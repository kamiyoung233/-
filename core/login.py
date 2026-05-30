#!/usr/bin/env python3
"""
核心逻辑层 - 校园网登录/注销/网络检测 (v2)
"""

import socket
import subprocess
import re
import time
import urllib.request
import urllib.error
from typing import Optional, Tuple

from core.config import Config
from api.portal import do_login as portal_login
from api.portal import do_logout as portal_logout
from core.logger import Logger

_TCP_PROBE_TIMEOUT = 3
_HTTP_PROBE_TIMEOUT = 3

_CAMPUS_IP_PREFIXES = ("10.", "172.16.", "172.17.")

_PORTAL_BASE = "10.10.102.50:801"

# ── Portal 状态查询的多组备用 URL ──
_PORTAL_STATUS_URLS = [
    f"http://{_PORTAL_BASE}/eportal/portal/status?callback=dr1000",
    f"http://{_PORTAL_BASE}/eportal/status?callback=dr1000",
    f"http://10.10.102.50/eportal/portal/status?callback=dr1000",
]


def _query_portal_for_ip() -> Optional[str]:
    """尝试通过 Portal 状态接口获取当前出口 IP（能穿透路由器）"""
    for url in _PORTAL_STATUS_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
            # 尝试多种字段名
            for field in ("v4ip", "ip", "client_ip", "wlan_user_ip"):
                m = re.search(r'"{field}":\s*"([^"]+)"'.replace("{field}", field), body)
                if m:
                    ip = m.group(1)
                    if ip:
                        return ip
            # 用最通用的模式: "ip":"数字.数字.数字.数字"
            m = re.search(r'"ip":\s*"(\d+\.\d+\.\d+\.\d+)"', body)
            if m:
                return m.group(1)
        except Exception:
            continue
    return None


def get_any_local_ip() -> Optional[str]:
    """获取本机任意网卡IPv4地址（不限于校园网段）"""
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            encoding="gbk",
            timeout=5,
        )
        for line in result.stdout.split("\n"):
            m = re.search(r"IPv4.*:\s*(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                ip = m.group(1)
                if not ip.startswith("127.") and not ip.startswith("169.254."):
                    return ip
    except Exception:
        pass
    return None


def get_campus_ip() -> Optional[str]:
    """
    获取校园网 IP 地址（如 10.x.x.x 段）。

    优先级：
      1. UDP 连接 Portal 探测（本地网卡IP，仅直连校园网有效）
      2. Portal 状态回调接口（可穿透路由器拿到出口IP）
      3. ipconfig 解析校园网段（后备）
      4. Portal 回调查任意 IP（最弱后备）
    """
    # 方法1：UDP 直连探测
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.10.102.50", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip.startswith(_CAMPUS_IP_PREFIXES):
            return ip
    except Exception:
        pass

    # 方法2：Portal 回调（可穿透路由器）
    portal_ip = _query_portal_for_ip()
    if portal_ip:
        # 如果 Portal 回的是任意 IP，先检查是不是校园网段
        if portal_ip.startswith(_CAMPUS_IP_PREFIXES):
            return portal_ip
        # 不是校园网段但有 IP → 路由器模式，存着备用
        # 当 retry 时往下继续尝试 ipconfig

    # 方法3：ipconfig 查校园网段
    try:
        result = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            encoding="gbk",
            timeout=5,
        )
        for line in result.stdout.split("\n"):
            m = re.search(r"IPv4.*:\s*((?:10\.|172\.(?:1[6-9]|2[0-9]|3[0-1]))\.\d+\.\d+)", line)
            if m:
                ip = m.group(1)
                return ip
    except Exception:
        pass

    # 方法4：Portal 回调如果有任意 IP 也返回（路由器模式）
    if portal_ip:
        return portal_ip

    return None


def detect_network_mode(local_ip: str = None, campus_ip: str = None) -> str:
    """
    检测当前网络模式。

    Returns:
        "direct"     - 直连校园网
        "router"     - 路由器模式（本地IP非校园网段）
        "no_network" - 无网络连接
        "unknown"    - 未知
    """
    if local_ip is None:
        local_ip = get_any_local_ip()
    if campus_ip is None:
        campus_ip = get_campus_ip()

    if local_ip is None and campus_ip is None:
        return "no_network"

    if campus_ip and campus_ip.startswith(_CAMPUS_IP_PREFIXES):
        return "direct"

    return "router"


def is_behind_router(campus_ip: str = None) -> bool:
    """
    检测当前设备是否在路由器后面（非校园网 IP 段）。
    即使 campus_ip 为 None，只要有本地 IP 且非校园网段就算路由器模式。
    """
    if campus_ip and campus_ip.startswith(_CAMPUS_IP_PREFIXES):
        return False

    # 拿不到校园网 IP：检查是不是有本地网络但不在校园网段
    local_ip = get_any_local_ip()
    if local_ip and not local_ip.startswith("127.") and not local_ip.startswith("169.254."):
        # 有本地 IP 但不是校园网 → 路由器或 VPN
        return True

    # 本地网络也没有 → 可能没插网线
    return False


ConnectivityResult = Tuple[bool, Optional[float], Optional[str]]


def check_connectivity(urls: list = None) -> ConnectivityResult:
    if urls is None:
        urls = [
            "http://www.baidu.com",
            "http://connect.rom.miui.com/generate_204",
        ]
    for url in urls:
        t1 = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=_HTTP_PROBE_TIMEOUT) as resp:
                t2 = time.time()
                latency_ms = round((t2 - t1) * 1000, 1)
                body = resp.read().decode("utf-8", errors="ignore")
                if "百度" in body or resp.status == 204:
                    return True, latency_ms, url
        except Exception:
            continue
    return False, None, None


# ── 错误码 ──
EC_NO_IP = "NO_IP"
EC_ALREADY_ONLINE = "ALREADY_ONLINE"
EC_PORTAL_UNREACHABLE = "PORTAL_UNREACHABLE"
EC_AUTH_FAILED = "AUTH_FAILED"
EC_NETWORK_ERROR = "NETWORK_ERROR"
EC_UNKNOWN = "UNKNOWN"

# 新增：路由器模式错误码
EC_ROUTER_MODE = "ROUTER_MODE"


class LoginEngine:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()

    def login(self, username: str, password: str, log: Optional[Logger] = None) -> Tuple[bool, str, Optional[str]]:
        logger = log or Logger()

        # 1. 检测网络模式
        network_mode = detect_network_mode()
        logger.info(f"网络模式: {network_mode}")

        # 2. 获取校园网 IP
        logger.info("正在获取校园网IP...")
        ip = get_campus_ip()

        # 3. 处理路由器模式
        if network_mode == "router":
            if ip and not ip.startswith(_CAMPUS_IP_PREFIXES):
                logger.warn(f"⚠ 检测到路由器模式：本机IP({get_any_local_ip()})，通过Portal查到的出口IP({ip})")
                logger.warn(f"   确保路由器已在网页手动登录过一次校园网，工具可帮助自动重连")
            elif ip is None:
                logger.warn(f"⚠ 检测到路由器模式，但无法获取校园网出口IP")
                logger.warn(f"   请尝试：① 在路由器管理界面登录一次校园网 ② 或直连校园网WiFi使用")
                return False, "路由器模式且无法获取校园网出口IP，请先在路由器管理页面登录校园网", EC_ROUTER_MODE

        # 4. 没有 IP 就报错退出
        if not ip:
            logger.error("无法获取校园网IP地址，请连接校园网WiFi")
            return False, "无法获取校园网IP，请连接校园网WiFi", EC_NO_IP

        logger.info(f"校园网IP: {ip}")

        # 5. 检查是否已在线
        logger.info("正在检测网络连通性...")
        online, lat, src = check_connectivity(self.config.connectivity_check_urls)
        if online:
            logger.info(f"网络已在线 (延迟: {lat}ms, 源: {src})")
            return True, f"已经在线 (IP: {ip})", EC_ALREADY_ONLINE

        # 6. 重试登录
        logger.info(f"开始登录，最多重试 {self.config.retry_count} 次")
        last_msg = ""
        last_code = EC_UNKNOWN
        for attempt in range(self.config.retry_count):
            logger.info(f"第 {attempt + 1}/{self.config.retry_count} 次尝试...")
            success, msg = portal_login(username, password, ip, timeout=self.config.login_timeout)

            if success:
                logger.info("登录成功")
                time.sleep(1)
                online_p, lat_p, src_p = check_connectivity(self.config.connectivity_check_urls)
                if online_p:
                    logger.info(f"外网连通性确认正常 (延迟: {lat_p}ms)")
                else:
                    logger.warn("登录成功但外网尚未连通（可能需要等待）")
                if "已经在线" in msg:
                    return True, msg, EC_ALREADY_ONLINE
                return True, msg, None

            if "HTTP错误" in msg or "无法连接" in msg:
                last_code = EC_PORTAL_UNREACHABLE
            elif "密码错误" in msg or "账号" in msg or "失败" in msg:
                last_code = EC_AUTH_FAILED
            else:
                last_code = EC_NETWORK_ERROR

            logger.warn(f"第 {attempt + 1} 次失败: {msg}")
            last_msg = msg
            if attempt < self.config.retry_count - 1:
                logger.info(f"等待 {self.config.retry_delay} 秒后重试...")
                time.sleep(self.config.retry_delay)

        logger.error(f"已重试 {self.config.retry_count} 次，登录失败")
        return False, last_msg, last_code

    def logout(self, log: Optional[Logger] = None) -> Tuple[bool, str, Optional[str]]:
        logger = log or Logger()
        logger.info("执行注销...")
        success, msg = portal_logout(timeout=self.config.login_timeout)
        if success:
            logger.info(msg)
            return True, msg, None
        else:
            logger.error(msg)
            return False, msg, EC_NETWORK_ERROR

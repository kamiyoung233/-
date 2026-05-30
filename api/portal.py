#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网络/API层 - 校园网 Portal HTTP 通信

职责：
  - 封装 Portal 登录/注销的 HTTP 请求
  - 不包含业务逻辑（重试、状态判断等）
  - 返回值统一为 (success: bool, message: str)

未来扩展：
  - 可在此层添加请求频率控制、代理支持
  - 可替换为异步 HTTP 客户端（httpx / aiohttp）
"""

import urllib.request
import urllib.parse
import random
import re
import json

# Portal 地址（天津科技大学深澜认证系统）
PORTAL_BASE = "http://10.10.102.50:801/eportal/portal/login"
LOGOUT_URL = "http://10.10.102.50:801/eportal/?c=ACSetting&a=Logout&ver=1.0"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 10


def _build_login_params(username: str, password: str, ip: str) -> dict:
    """构建登录请求参数"""
    callback_num = random.randint(1000, 9999)
    return {
        "callback": f"dr{callback_num}",
        "login_method": "1",
        "user_account": username,
        "user_password": password,
        "wlan_user_ip": ip,
        "wlan_user_ipv6": "",
        "wlan_user_mac": "000000000000",
        "wlan_ac_ip": "",
        "wlan_ac_name": "",
        "jsVersion": "4.1.3",
        "terminal_type": "1",
        "lang": "zh-cn",
        "v": str(callback_num),
    }


def do_login(username: str, password: str, ip: str, timeout: int = DEFAULT_TIMEOUT) -> tuple:
    """
    发送登录请求到 Portal。

    返回:
        (True, message)  - 登录成功或已在线
        (False, message) - 登录失败
    """
    params = _build_login_params(username, password, ip)
    url = f"{PORTAL_BASE}?{urllib.parse.urlencode(params)}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")

        # 解析响应
        if '"result":1' in body or '"result":"success"' in body or 'result":true' in body:
            return True, "登录成功"
        elif '"ret_code":2' in body or "已经在线" in body:
            return True, "已经在线，无需重复登录"
        elif '"result":0' in body:
            m = re.search(r'"msg":"([^"]+)"', body)
            msg = m.group(1) if m else "登录失败，请检查账号密码"
            return False, msg
        else:
            return False, "Portal 返回未知响应"

    except urllib.error.HTTPError as e:
        return False, f"HTTP错误 {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"无法连接 Portal ({e.reason})"
    except Exception as e:
        return False, f"请求异常: {str(e)}"


def do_logout(timeout: int = DEFAULT_TIMEOUT) -> tuple:
    """
    发送注销请求到 Portal。

    返回:
        (True, message)  - 注销成功
        (False, message) - 注销失败
    """
    try:
        req = urllib.request.Request(LOGOUT_URL, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="ignore")

        if "成功" in body or "logout" in body.lower():
            return True, "注销成功"
        elif "已经注销" in body or "not online" in body.lower():
            return True, "已经注销"
        else:
            return True, "注销请求已发送"

    except urllib.error.HTTPError as e:
        return False, f"注销HTTP错误 {e.code}"
    except urllib.error.URLError as e:
        return False, f"无法连接 Portal ({e.reason})"
    except Exception as e:
        return False, f"注销异常: {str(e)}"

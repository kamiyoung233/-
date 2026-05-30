#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心逻辑层 - 配置管理

职责：
  - 账号数据模型（AccountData）
  - 全局配置管理（Config），含持久化
  - 所有可调节行为参数集中管理

原则：
  - 不依赖任何 UI 或平台层
  - 纯数据层，可被任何场景复用（GUI / CLI / 后台）
"""

import json
import os
import sys

# ─── 项目路径 ───────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─── 默认网络检测目标 ───────────────────────────────
DEFAULT_CONNECTIVITY_URLS = [
    "http://www.baidu.com",
    "http://connect.rom.miui.com/generate_204",
]


# ─── 运营商配置 ──────────────────────────────────────
ISP_OPTIONS = [
    {"label": "校园网",        "prefix": ",0,", "suffix": ""},
    {"label": "中国联通",      "prefix": ",0,", "suffix": "@unicom"},
    {"label": "中国移动",      "prefix": ",0,", "suffix": "@cmcc"},
    {"label": "中国电信",      "prefix": ",0,", "suffix": "@dx"},
]


# ─── 账号数据模型 ────────────────────────────────────
class AccountData:
    """单个校园网账号数据（纯数据，无行为）"""

    def __init__(self, student_id: str = "", isp_index: int = 0, password: str = ""):
        self.student_id = student_id
        self.isp_index = isp_index if 0 <= isp_index < len(ISP_OPTIONS) else 0
        self.password = password

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "isp_index": self.isp_index,
            "password": self.password,
        }

    @staticmethod
    def from_dict(d: dict) -> "AccountData":
        return AccountData(
            student_id=d.get("student_id", ""),
            isp_index=d.get("isp_index", 0),
            password=d.get("password", ""),
        )


# ─── 全局配置 ────────────────────────────────────────
class Config:
    """
    全局配置，包含账号信息、行为参数、开关设置。
    所有可调节参数集中管理，不硬编码。

    默认值：
        retry_count : 3   （登录重试次数）
        retry_delay : 3   （重试间隔秒数）
    """

    # ── 默认行为参数 ──
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_RETRY_DELAY = 3
    DEFAULT_LOGIN_TIMEOUT = 10

    def __init__(self):
        # 账号
        self.account = AccountData()

        # 开关
        self.remember_account = False
        self.auto_start = False
        self.auto_login = False  # 测试功能

        # 行为参数（配置化，不硬编码）
        self.retry_count = self.DEFAULT_RETRY_COUNT
        self.retry_delay = self.DEFAULT_RETRY_DELAY
        self.login_timeout = self.DEFAULT_LOGIN_TIMEOUT
        self.connectivity_check_urls = list(DEFAULT_CONNECTIVITY_URLS)

        self.load()

    # ── 持久化 ──

    @property
    def config_path(self) -> str:
        return os.path.join(BASE_DIR, "config.json")

    def load(self):
        """从 JSON 文件加载配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return  # 文件不存在或损坏，使用默认值

        acct_data = data.get("account", {})
        self.account = AccountData.from_dict(acct_data)
        self.remember_account = data.get("remember_account", False)
        self.auto_start = data.get("auto_start", False)
        self.auto_login = data.get("auto_login", False)
        self.retry_count = data.get("retry_count", self.DEFAULT_RETRY_COUNT)
        self.retry_delay = data.get("retry_delay", self.DEFAULT_RETRY_DELAY)
        self.login_timeout = data.get("login_timeout", self.DEFAULT_LOGIN_TIMEOUT)
        self.connectivity_check_urls = data.get(
            "connectivity_check_urls",
            list(DEFAULT_CONNECTIVITY_URLS),
        )

    def save(self):
        """保存配置到 JSON 文件"""
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "account": self.account.to_dict(),
                    "remember_account": self.remember_account,
                    "auto_start": self.auto_start,
                    "auto_login": self.auto_login,
                    "retry_count": self.retry_count,
                    "retry_delay": self.retry_delay,
                    "login_timeout": self.login_timeout,
                    "connectivity_check_urls": self.connectivity_check_urls,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ── 辅助方法 ──

    def get_full_username(self) -> str:
        """构造完整的登录用户名（含运营商后缀）"""
        isp = ISP_OPTIONS[self.account.isp_index]
        return f"{isp['prefix']}{self.account.student_id}{isp['suffix']}"

    def validate_account(self) -> bool:
        """检查账号信息是否完整有效"""
        sid = self.account.student_id
        return bool(sid and sid.isdigit() and self.account.password)

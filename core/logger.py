#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心逻辑层 - 统一日志工具

职责：
  - 提供 info / warn / error / debug 分级日志
  - silent 模式：仅输出 WARN 及以上级别
  - callback 机制：UI 可注入日志回调，同时在控制台输出
  - 所有日志行统一格式，消除手动拼接差异

用法：
    # 控制台日志
    logger = Logger(silent=False)
    logger.info("开始登录")

    # 带 UI 回调
    logger = Logger(callback=lambda msg: text_widget.insert("end", msg))
    logger.warn("网络检测超时")

    # 静默模式（仅错误输出）
    logger = Logger(silent=True)
    logger.info("登录成功")     # 不输出
    logger.error("登录失败")    # 输出到 stderr
"""

import sys
import os
import time
from typing import Callable, Optional


# ─── 日志级别 ────────────────────────────────────────
LOG_LEVELS = {
    "DEBUG": 0,
    "INFO": 1,
    "WARN": 2,
    "ERROR": 3,
}


# ─── 默认日志路径（相对于 BASE_DIR） ────────────────
if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_LOG_FILE = os.path.join(_BASE, "campus_net.log")


# ─── Logger ───────────────────────────────────────────

LogCallback = Callable[[str], None]


class Logger:
    """统一日志工具

    Args:
        name: 日志来源名称（预留，未来用于模块区分）
        silent: True 时只输出 WARN/ERROR，INFO/DEBUG 静默
        level: 最小输出级别（"DEBUG"/"INFO"/"WARN"/"ERROR"）
        callback: 日志回调（UI 注入用），收到格式化后的行
    """

    def __init__(
        self,
        name: str = "",
        silent: bool = False,
        level: str = "INFO",
        callback: Optional[LogCallback] = None,
        log_file: Optional[str] = None,
    ):
        self.name = name
        self.silent = silent
        self._min_level = LOG_LEVELS.get(level.upper(), 1)  # 默认 INFO
        self.callback = callback
        self.log_file = log_file

    def _log(self, level: str, msg: str):
        """内部输出"""
        level_idx = LOG_LEVELS.get(level, 1)

        # 级别过滤
        if level_idx < self._min_level:
            return

        ts = time.strftime("%H:%M:%S")
        line = f"{ts} {level}: {msg}"

        # ── 文件日志（不受 silent/级别限制，always persist） ──
        if self.log_file:
            try:
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(f"{line}\n")
            except Exception:
                pass  # 文件写入失败不阻塞应用

        # silent 模式下跳过 DEBUG / INFO 的 console 输出
        if self.silent and level in ("DEBUG", "INFO"):
            return

        # 控制台输出
        if level == "ERROR":
            print(f"[FAIL] {msg}", file=sys.stderr)
        elif level == "WARN":
            print(f"[WARN] {msg}", file=sys.stderr)
        elif level == "INFO":
            print(f"[INFO] {msg}")

        # UI 回调
        if self.callback:
            self.callback(line)

    def debug(self, msg: str):
        """调试信息"""
        self._log("DEBUG", msg)

    def info(self, msg: str):
        """普通信息"""
        self._log("INFO", msg)

    def warn(self, msg: str):
        """警告"""
        self._log("WARN", msg)

    def error(self, msg: str):
        """错误"""
        self._log("ERROR", msg)

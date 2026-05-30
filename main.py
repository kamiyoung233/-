#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校园网络助手 - 测试版 v0.1
============================
天津科技大学校园网自动登录工具（测试版本）

用法:
    python main.py           # 启动 GUI
    python main.py --silent  # 静默模式（自动登录，成功不提示）

架构:
    - main.py        → 入口，处理 CLI 参数
    - ui/            → UI 层（Tkinter，可随时替换）
    - core/          → 核心逻辑层（登录引擎 + 配置 + 日志）
    - adapter/       → 平台适配层（开机启动等）
    - api/           → 网络/API 层（Portal 通信）

测试版原则:
    能稳定运行 > 功能多
    行为可观察 > 智能优化
    简单可靠 > 复杂自动化

变更记录:
    v0.1 (2026-05-09)
        - 初始测试版
        - 四层分离架构
        - 统一 Logger 日志
        - 返回结构标准化 (success, message, error_code)
        - 行为参数完全配置化
"""

import sys
import os

# ── 项目路径 ──────────────────────────────────────────
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

from core.config import Config
from core.login import LoginEngine, check_connectivity
from core.logger import Logger, DEFAULT_LOG_FILE


# ═══════════════════════════════════════════════════════
# GUI 模式
# ═══════════════════════════════════════════════════════

def run_gui():
    """启动图形界面（延迟加载 UI，silent 模式不引入 GUI 依赖）"""
    try:
        from ui.app import CampusNetUI
        import tkinter as tk

        root = tk.Tk()
        app = CampusNetUI(root)
        app.run()
    except Exception as e:
        print(f"[FAIL] GUI 启动失败: {e}", file=sys.stderr)
        print("[HINT] 请确认已安装 Python tkinter 支持", file=sys.stderr)
        print("       Windows: 通常已内置，若缺失需重装 Python", file=sys.stderr)
        print("       Linux: sudo apt install python3-tk", file=sys.stderr)
        print("[HINT] 也可使用 --silent 模式运行命令行版本", file=sys.stderr)
        sys.exit(1)


# ═══════════════════════════════════════════════════════
# 静默模式
# ═══════════════════════════════════════════════════════

def run_silent():
    """静默模式运行（后台自动登录）

    行为（通过 Logger 控制）:
        - Logger(silent=True): 成功 INFO 只写文件，不打印到控制台
        - 失败 ERROR 输出到 stderr + 写文件
        - 所有日志持久化到 campus_net.log
    """
    config = Config()
    logger = Logger(silent=True, log_file=DEFAULT_LOG_FILE)

    if not config.validate_account():
        logger.error("静默登录: 未配置账号信息")
        logger.error("请先运行 GUI 模式配置账号")
        sys.exit(1)

    # 检查是否已在线
    logger.info("正在检测网络状态...")
    online, lat, src = check_connectivity(config.connectivity_check_urls)
    if online:
        logger.info(f"网络已在线 (延迟: {lat}ms)，无需登录")
        return

    username = config.get_full_username()
    password = config.account.password

    engine = LoginEngine(config)
    success, msg, err_code = engine.login(username, password, log=logger)

    if success:
        # 成功：写文件，不打印
        logger.info(f"登录成功: {msg}")
        return
    else:
        # 失败：必须有输出（不可调试）
        logger.error(f"静默登录失败 [{err_code}]: {msg}")
        sys.exit(1)


# ═══════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("--silent", "-s"):
            run_silent()
            return
        elif arg in ("--help", "-h"):
            print(__doc__)
            return
        else:
            print(f"[WARN] 未知参数: {arg}", file=sys.stderr)
            print("[HINT] 使用 --help 查看帮助", file=sys.stderr)

    run_gui()


if __name__ == "__main__":
    main()

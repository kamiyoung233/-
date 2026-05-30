#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
校园网络助手 — PyInstaller 构建脚本

用法:
    pip install pyinstaller
    python build.py

输出:
    dist/CampusNetHelper/
    ├── CampusNetHelper.exe       ← 主程序（GUI / --silent 双模式）
    ├── *.pyd / *.dll             ← 依赖库
    ├── base_library.zip
    └── ...

测试:
    dist/CampusNetHelper/CampusNetHelper.exe               # GUI
    dist/CampusNetHelper/CampusNetHelper.exe --silent       # silent mode

注意:
    - 使用 onedir（单 exe 会释放到临时目录，路径难追踪）
    - 资源路径：sys.executable 同目录下生成 config.json / campus_net.log
    - --console 模式：保持 CLI 交互能力（--silent 可正常使用）
    - 管理员权限：schtasks 设置开机自启时需要，不内置请求（弹窗提示）
"""

import os
import sys
import shutil

# ── 确保 PyInstaller 已安装 ──────────────────────────
try:
    import PyInstaller.__main__
except ImportError:
    print("[FAIL] PyInstaller 未安装。请运行: pip install pyinstaller")
    sys.exit(1)

# ── 项目路径 ──────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT, "dist")
BUILD_DIR = os.path.join(ROOT, "build")
SPEC_FILE = os.path.join(ROOT, "campus_net_helper.spec")

# ── 清理旧构建 ────────────────────────────────────────
for d in [DIST_DIR, BUILD_DIR]:
    if os.path.exists(d):
        print(f"[INFO] 清理: {d}")
        shutil.rmtree(d, ignore_errors=True)
for f in [SPEC_FILE]:
    if os.path.exists(f):
        os.remove(f)

# ── 模块清单 ──────────────────────────────────────────
# PyInstaller 自动收集大部分依赖，但某些动态/隐式导入需要显式声明。
# 以下模块均为本项目实际使用但可能被 PyInstaller 遗漏的。
HIDDEN_IMPORTS = [
    # tkinter 组件
    "tkinter",         # UI 主框架（延迟加载，但 pyinstaller 需提前绑定）
    "tkinter.ttk",     # Combobox 组件
    "tkinter.messagebox",  # 弹窗
    # 标准库网络相关
    "urllib.request",
    "urllib.parse",
    "urllib.error",
    "socket",
    # 系统/平台相关
    "ctypes",          # DPI 感知
    "subprocess",      # ipconfig / schtasks
    "re",              # IP 地址正则提取
    "json",            # 配置持久化
    "threading",       # 异步登录
    "time",
    "random",
    "inspect",         # 类型检查（仅测试用，但保留安全）
]

# ── PyInstaller 参数 ──────────────────────────────────
# 原则：
#   1. 只用 onedir（拒绝 onefile — 临时目录路径不可控）
#   2. 明确声明所有依赖
#   3. --console 保留 CLI 能力
#   4. 不内置 UAC 请求（让用户右键管理员运行）

ARGS = [
    # 输出
    "--name=CampusNetHelper",
    "--distpath", DIST_DIR,
    "--workpath", BUILD_DIR,
    "--specpath", ROOT,
    # 构建模式
    "--onedir",                  # 唯一发布格式
    "--noconfirm",               # 覆盖已有输出
    "--clean",                   # 清理缓存
    # 日志
    "--log-level=INFO",
    # 控制台（保持 CLI 模式可用）
    "--console",
    # 隐式依赖
]
for mod in HIDDEN_IMPORTS:
    ARGS.append(f"--hidden-import={mod}")

# 入口文件（最后添加）
ARGS.append("main.py")


def build():
    """执行构建"""
    print("=" * 56)
    print("  校园网络助手 v0.1 — PyInstaller 构建")
    print("=" * 56)
    print(f"  输出: {DIST_DIR}")
    print(f"  格式: onedir (safest)")
    print(f"  入口: main.py")
    print(f"  隐式: {len(HIDDEN_IMPORTS)} modules")
    print()

    # 执行 PyInstaller
    PyInstaller.__main__.run(ARGS)

    # 验证构建
    output_dir = os.path.join(DIST_DIR, "CampusNetHelper")
    exe_path = os.path.join(output_dir, "CampusNetHelper.exe")

    if os.path.isfile(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        dir_items = len(os.listdir(output_dir))
        print(f"\n[OK] 构建成功")
        print(f"     主程序: {exe_path} ({size_mb:.1f} MB)")
        print(f"     目录: {output_dir}/ ({dir_items} items)")
    elif os.path.isdir(output_dir):
        print(f"[WARN] 目录存在但未找到 exe，请检查构建日志")
        print(f"      {output_dir}/")
    else:
        print(f"[FAIL] 构建失败，未找到输出")
        sys.exit(1)

    # 测试命令
    print()
    print("─" * 56)
    print("  测试命令:")
    print()
    print(f"    {exe_path}")
    print(f"    {exe_path} --silent")
    print(f"    {exe_path} --help")
    print()
    print("  传递新用户:")
    print("    直接把 dist/CampusNetHelper/ 整个目录压缩发过去")
    print("    对方双击 CampusNetHelper.exe 即可使用")
    print("─" * 56)


if __name__ == "__main__":
    build()

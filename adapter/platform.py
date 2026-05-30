#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台适配层 - 平台特定功能抽象

职责：
  - 定义平台适配器接口（PlatformAdapter）
  - 提供各平台实现（Windows / 未来 macOS / Linux / Android）
  - 所有与平台绑定的操作在此隔离

原则：
  - 上层（UI / Core）通过接口调用，不直接依赖平台代码
  - 未来新增平台只需新增 Adapter 子类
"""

import subprocess
import sys
import os
from typing import Optional

# ─── 启动文件夹辅助 ──────────────────────────────────

def _get_startup_path() -> str:
    """获取当前用户的 Windows 启动文件夹路径"""
    import ctypes
    from ctypes import wintypes

    CSIDL_STARTUP = 7
    buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_STARTUP, None, 0, buf)
    return buf.value


def _create_bat(python_exe: str, script_path: str, workdir: str, bat_name: str) -> bool:
    """
    创建启动用 .bat 批处理文件（带 BOM，防止乱码）。
    比 .lnk 快捷方式更可靠，不依赖 PowerShell COM。
    """
    startup = _get_startup_path()
    bat_path = os.path.join(startup, bat_name)

    content = (
        '@echo off\r\n'
        'chcp 65001 >nul\r\n'
        f'cd /d "{workdir}"\r\n'
        f'start "" /B "{python_exe}" "{script_path}"\r\n'
    )
    try:
        # UTF-8 with BOM
        with open(bat_path, 'wb') as f:
            f.write(b'\xef\xbb\xbf')
            f.write(content.encode('utf-8'))
        return True
    except Exception:
        return False


def _remove_bat(bat_name: str) -> bool:
    """删除启动文件夹中的 .bat 文件"""
    startup = _get_startup_path()
    bat_path = os.path.join(startup, bat_name)
    try:
        if os.path.exists(bat_path):
            os.remove(bat_path)
        return True
    except Exception:
        return False


class PlatformAdapter:
    """
    平台适配器基类。
    所有平台特定功能在此定义接口。
    """

    def set_startup(self, enabled: bool) -> bool:
        """启用/禁用开机自启，返回是否成功"""
        raise NotImplementedError

    def get_startup_status(self) -> bool:
        """查询开机自启是否已启用"""
        raise NotImplementedError


class WindowsAdapter(PlatformAdapter):
    """
    Windows 平台适配器（Startup 文件夹 .bat 实现）
    无需管理员权限！直接放批处理，编码可靠。
    """

    BAT_NAME = "CampusNetHelper.bat"

    def set_startup(self, enabled: bool) -> bool:
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(project_dir, "main.py")

        if enabled:
            return _create_bat(sys.executable, script_path, project_dir, self.BAT_NAME)
        else:
            return _remove_bat(self.BAT_NAME)

    def get_startup_status(self) -> bool:
        startup = _get_startup_path()
        bat = os.path.join(startup, self.BAT_NAME)
        return os.path.exists(bat)


# ─── 工厂函数 ────────────────────────────────────────

def get_platform_adapter() -> Optional[PlatformAdapter]:
    """获取当前平台的适配器实例。返回 None 表示当前平台暂无适配器。"""
    if sys.platform == "win32":
        return WindowsAdapter()
    return None

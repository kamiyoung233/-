#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI层 - 极简版校园网登录器界面（测试版）

设计原则：
  - 极简：首页只显示状态 + 一键登录 + 基本输入
  - 设置页只保留三个开关（记住账号/开机启动/自动登录）
  - 不做复杂功能页或 Pro 入口
  - 所有业务逻辑委托给 core 层处理

可观察性：
  - 登录开始/成功/失败日志实时展示
  - 网络检测日志
  - 所有错误信息都在日志区可见

容错：
  - UI 启动失败有明确的控制台错误提示
  - 不因 UI 问题导致用户不可用

日志解耦：
  - 使用 core.logger.Logger 统一日志格式
  - UI 通过 callback 接收日志，不同步阻塞
"""

import threading
import time

from core.config import Config, ISP_OPTIONS
from core.login import LoginEngine, get_campus_ip, check_connectivity, is_behind_router, detect_network_mode, get_any_local_ip
from core.logger import Logger
from adapter.platform import get_platform_adapter


class CampusNetUI:
    """校园网络助手 - 测试版 UI"""

    def __init__(self, root, config: Config = None):
        # 延迟导入 tkinter（解耦，silent 模式不引入 GUI 依赖）
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk

        self.root = root
        self.config = config or Config()
        self.engine = LoginEngine(self.config)
        self.adapter = get_platform_adapter()
        self.logging_in = False
        self._auto_save_id = None

        # UI 层 Logger（日志同时输出到控制台和 UI 日志区）
        self.logger = Logger(callback=self._log_to_ui)

        self._setup_window()
        self._build_ui()
        self._load_account()
        self._check_startup_status()

        # 延迟启动状态检测
        self.root.after(500, lambda: self.logger.info("启动网络检测..."))
        self.root.after(600, self._check_status)

    def _setup_window(self):
        """配置主窗口"""
        self.root.title("校园网络助手 - 测试版")
        self.root.resizable(False, False)
        self.root.geometry("480x620")
        self.root.configure(bg="#f0f4f8")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # DPI 适配
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    # ═══════════════════════════════════════════════════
    # UI 构建
    # ═══════════════════════════════════════════════════

    def _build_ui(self):
        """构建所有 UI 元素"""
        main = self.tk.Frame(self.root, bg="#f0f4f8", padx=24, pady=16)
        main.pack(fill="both", expand=True)

        self._build_header(main)
        self._build_status_card(main)
        self._build_login_form(main)
        self._build_login_button(main)
        self._build_log_area(main)
        self._build_footer(main)

    def _build_header(self, parent):
        """标题栏 + 设置入口"""
        frame = self.tk.Frame(parent, bg="#f0f4f8")
        frame.pack(fill="x", pady=(0, 8))

        self.tk.Label(frame, text="校园网络助手",
                      font=("Microsoft YaHei UI", 16, "bold"),
                      bg="#f0f4f8", fg="#1a1a2e").pack(side="left")

        settings_btn = self.tk.Label(frame, text="⚙ 设置",
                                     font=("Microsoft YaHei UI", 10),
                                     bg="#f0f4f8", fg="#4a6cf7", cursor="hand2")
        settings_btn.pack(side="right")
        settings_btn.bind("<Button-1>", lambda e: self._show_settings())

        self.tk.Label(parent, text="天津科技大学 · 深澜认证",
                      font=("Microsoft YaHei UI", 9),
                      bg="#f0f4f8", fg="#888", anchor="w").pack(fill="x", pady=(0, 12))

    def _build_status_card(self, parent):
        """网络状态卡片"""
        card = self.tk.Frame(parent, bg="#fff", relief="solid", bd=1,
                             highlightbackground="#e0e0e0")
        card.pack(fill="x", pady=(0, 14))

        row = self.tk.Frame(card, bg="#fff", padx=14, pady=10)
        row.pack(fill="x")

        # 状态指示灯
        self.status_dot = self.tk.Canvas(row, width=14, height=14,
                                         bg="#fff", highlightthickness=0)
        self.status_dot.pack(side="left", padx=(0, 8))
        self.dot = self.status_dot.create_oval(1, 1, 13, 13, fill="#999", outline="")

        # 状态文字
        self.status_label = self.tk.Label(row, text="检测中...",
                                          font=("Microsoft YaHei UI", 11, "bold"),
                                          bg="#fff", fg="#666")
        self.status_label.pack(side="left")

        # 稳定性提示
        self.stability_label = self.tk.Label(row, text="",
                                             font=("Microsoft YaHei UI", 9),
                                             bg="#fff", fg="#999")
        self.stability_label.pack(side="right")

        # IP 显示
        self.ip_label = self.tk.Label(card, text="",
                                      font=("Microsoft YaHei UI", 9),
                                      bg="#fff", fg="#aaa",
                                      padx=14, anchor="w")
        self.ip_label.pack(fill="x", pady=(0, 8))

    def _build_login_form(self, parent):
        """账号输入区"""
        # 学号
        self.tk.Label(parent, text="学号", font=("Microsoft YaHei UI", 10),
                      bg="#f0f4f8", fg="#444").pack(anchor="w")
        frame_sid = self.tk.Frame(parent, bg="#fff", relief="solid",
                                  bd=1, highlightbackground="#ccc")
        frame_sid.pack(fill="x", pady=(3, 8))
        self.sid_entry = self.tk.Entry(frame_sid, font=("Microsoft YaHei UI", 12),
                                       bd=0, highlightthickness=0)
        self.sid_entry.pack(fill="x", ipady=4, padx=8)
        self.sid_entry.bind("<KeyRelease>", self._on_input_change)

        # 密码
        self.tk.Label(parent, text="密码", font=("Microsoft YaHei UI", 10),
                      bg="#f0f4f8", fg="#444").pack(anchor="w")
        frame_pwd = self.tk.Frame(parent, bg="#fff", relief="solid",
                                  bd=1, highlightbackground="#ccc")
        frame_pwd.pack(fill="x", pady=(3, 8))
        self.pwd_entry = self.tk.Entry(frame_pwd, font=("Microsoft YaHei UI", 12),
                                       bd=0, highlightthickness=0, show="\u25cf")
        self.pwd_entry.pack(fill="x", ipady=4, padx=8)
        self.pwd_entry.bind("<KeyRelease>", self._on_input_change)

        # 运营商
        self.tk.Label(parent, text="运营商", font=("Microsoft YaHei UI", 10),
                      bg="#f0f4f8", fg="#444").pack(anchor="w")
        self.isp_combo = self.ttk.Combobox(
            parent,
            values=[o["label"] for o in ISP_OPTIONS],
            font=("Microsoft YaHei UI", 11),
            state="readonly",
        )
        self.isp_combo.current(0)
        self.isp_combo.pack(fill="x", ipady=2, pady=(3, 12))
        self.isp_combo.bind("<<ComboboxSelected>>", self._on_input_change)

    def _build_login_button(self, parent):
        """一键登录按钮"""
        self.login_btn = self.tk.Button(
            parent, text="一键登录",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg="#4a6cf7", fg="white",
            bd=0, pady=12, cursor="hand2",
            command=self._start_login,
        )
        self.login_btn.pack(fill="x", pady=(0, 10))

    def _build_log_area(self, parent):
        """运行日志区域"""
        self.tk.Label(parent, text="运行日志",
                      font=("Microsoft YaHei UI", 9, "bold"),
                      bg="#f0f4f8", fg="#555", anchor="w").pack(fill="x")

        log_frame = self.tk.Frame(parent, bg="#1a1a2e", relief="solid", bd=1)
        log_frame.pack(fill="both", expand=True)

        self.log_text = self.tk.Text(log_frame, font=("Consolas", 9),
                                     bg="#1a1a2e", fg="#a8d8ea",
                                     bd=0, padx=8, pady=6,
                                     height=8, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True)

        scrollbar = self.tk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _build_footer(self, parent):
        """底部信息（版本 + 免责声明）"""
        # ── 分隔线 ──
        sep = self.tk.Frame(parent, bg="#ddd", height=1)
        sep.pack(fill="x", pady=(4, 2))

        bottom = self.tk.Frame(parent, bg="#f0f4f8")
        bottom.pack(fill="x")

        self.tk.Label(bottom, text="v0.1-test",
                      font=("Microsoft YaHei UI", 8),
                      bg="#f0f4f8", fg="#aaa").pack(side="left")

        # ── 免责声明 ──
        inner = self.tk.Frame(parent, bg="#f0f4f8")
        inner.pack(fill="x", pady=(0, 2))
        disc = (
            "本工具仅用于校园网便捷登录，不修改/绕过认证系统。"
            "使用结果由用户自行承担。"
        )
        self.tk.Label(inner, text=disc,
                      font=("Microsoft YaHei UI", 7),
                      bg="#fff8e1", fg="#8d6e63",
                      wraplength=440, justify="center",
                      padx=8, pady=4).pack(fill="x")

    # ═══════════════════════════════════════════════════
    # 账号数据
    # ═══════════════════════════════════════════════════

    def _load_account(self):
        """加载已保存的账号信息到输入框"""
        acct = self.config.account
        self.sid_entry.delete(0, self.tk.END)
        self.sid_entry.insert(0, acct.student_id)
        if 0 <= acct.isp_index < len(ISP_OPTIONS):
            self.isp_combo.current(acct.isp_index)
        self.pwd_entry.delete(0, self.tk.END)
        if acct.password:
            self.pwd_entry.insert(0, acct.password)

    def _on_input_change(self, event=None):
        """输入变化，延迟自动保存"""
        if self._auto_save_id:
            self.root.after_cancel(self._auto_save_id)
        self._auto_save_id = self.root.after(500, self._save_current)

    def _save_current(self):
        """保存当前输入到配置"""
        sid = self.sid_entry.get().strip()
        isp_idx = self.isp_combo.current()
        if isp_idx < 0:
            isp_idx = 0
        pwd = self.pwd_entry.get()
        if sid and sid.isdigit():
            self.config.account.student_id = sid
            self.config.account.isp_index = isp_idx
            self.config.account.password = pwd
            self.config.save()

    # ═══════════════════════════════════════════════════
    # 日志
    # ═══════════════════════════════════════════════════

    def _log_to_ui(self, line: str):
        """
        Logger callback：将日志行追加到 UI 日志区。
        在主线程中执行（由 Logger 或 root.after 保障）。
        """
        def _do():
            self.log_text.config(state="normal")
            self.log_text.insert("end", f"{line}\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

        # 确保在 tkinter 主线程执行
        self.root.after(0, _do)

    # ═══════════════════════════════════════════════════
    # 状态显示
    # ═══════════════════════════════════════════════════

    def _set_status(self, text: str, connected: bool = None,
                    stability: str = None):
        """更新状态显示"""
        if connected is True:
            self.status_dot.itemconfig(self.dot, fill="#4caf50")
        elif connected is False:
            self.status_dot.itemconfig(self.dot, fill="#f44336")
        else:
            self.status_dot.itemconfig(self.dot, fill="#ff9800")
        self.status_label.config(text=text)
        if stability is not None:
            self.stability_label.config(text=stability)

    def _check_status(self):
        """异步检测网络状态"""
        self.logger.info("正在检测网络状态...")

        def _do():
            local_ip = get_any_local_ip()
            ip = get_campus_ip()
            network_mode = detect_network_mode(local_ip, ip)
            behind_router = (network_mode == "router")
            online, lat, src = check_connectivity(
                self.config.connectivity_check_urls
            )
            stability = ""
            if online and ip:
                stability = f"✓ {lat}ms"
            self.root.after(
                0, lambda: self._update_status(ip, online, lat, src, stability, behind_router, local_ip, network_mode)
            )

        threading.Thread(target=_do, daemon=True).start()

    def _update_status(self, ip, online, latency=None, source=None, stability="", behind_router=False, local_ip=None, network_mode=None):
        if online:
            self._set_status("已连接", True, stability)
            lat_str = f"延迟: {latency}ms" if latency else ""
            src_str = f"源: {source}" if source else ""
            msg = f"网络已连接 (IP: {ip}, {lat_str}, {src_str})"
            if behind_router:
                msg += " [路由器模式]"
            self.logger.info(msg)
        else:
            if network_mode == "router":
                self._set_status("路由器模式 ⚠", False)
                self.logger.warn("⚠ 检测到路由器模式：电脑通过路由器上网，无法直接获取校园网IP")
                self.logger.warn(f"   请先在路由器管理页面手动登录一次校园网，然后本工具可帮助自动重连")
                self.logger.warn(f"   或直连校园网WiFi使用（推荐）")
            elif ip:
                self._set_status("未连接", False)
                self.logger.info(f"校园网已连接 (IP: {ip})，外网未连通（需要登录）")
            elif local_ip:
                self._set_status("未连接", False)
                self.logger.warn(f"有网络连接({local_ip})但无法获取校园网IP")
                self.logger.warn("   请确认是否连接了校园网WiFi或网线")
            else:
                self._set_status("未连接", False)
                self.logger.warn("未检测到校园网连接")

        if network_mode == "router":
            ip_text = f"路由器模式"
            if local_ip:
                ip_text += f" (本地: {local_ip})"
            if ip:
                ip_text += f" 出口: {ip}"
        elif ip:
            ip_text = f"IP: {ip}"
        else:
            ip_text = "未连接校园网WiFi"
        self.ip_label.config(text=ip_text)

    def _check_startup_status(self):
        """同步开机自启状态到配置"""
        if self.adapter:
            self.config.auto_start = self.adapter.get_startup_status()

    # ═══════════════════════════════════════════════════
    # 登录操作
    # ═══════════════════════════════════════════════════

    def _start_login(self):
        """一键登录（异步）"""
        if self.logging_in:
            return

        sid = self.sid_entry.get().strip()
        pwd = self.pwd_entry.get()

        if not sid or not sid.isdigit():
            self.logger.warn("请输入正确的学号")
            return
        if not pwd:
            self.logger.warn("请输入密码")
            return

        self.logging_in = True
        self.login_btn.config(text="登录中...", state="disabled", bg="#999")
        self._save_current()

        # 构造完整用户名
        isp_idx = self.isp_combo.current()
        if isp_idx < 0:
            isp_idx = 0
        isp = ISP_OPTIONS[isp_idx]
        username = f"{isp['prefix']}{sid}{isp['suffix']}"

        self.logger.info("━━━ 开始登录 ━━━")
        self.logger.info(f"账号: {username}")

        def _thread():
            success, msg, err_code = self.engine.login(
                username, pwd, log=self.logger,
            )
            self.root.after(0, lambda: self._login_done(success, msg, err_code))

        threading.Thread(target=_thread, daemon=True).start()

    def _login_done(self, success: bool, msg: str, err_code: str = None):
        """登录完成后的 UI 更新"""
        self.logging_in = False
        self.login_btn.config(text="一键登录", state="normal", bg="#4a6cf7")

        if success:
            self._set_status("已连接", True)
        else:
            self._set_status("登录失败", False)

    # ═══════════════════════════════════════════════════
    # 设置
    # ═══════════════════════════════════════════════════

    def _show_settings(self):
        """弹出设置窗口"""
        from tkinter import messagebox

        dialog = self.tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.resizable(False, False)
        dialog.configure(bg="#f0f4f8")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("360x280")

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        dialog.geometry(f"360x280+{(sw-360)//2}+{(sh-280)//2}")

        main = self.tk.Frame(dialog, bg="#f0f4f8", padx=28, pady=24)
        main.pack(fill="both", expand=True)

        self.tk.Label(main, text="设置",
                      font=("Microsoft YaHei UI", 14, "bold"),
                      bg="#f0f4f8", fg="#333").pack(pady=(0, 18))

        # 记住账号
        remember_var = self.tk.BooleanVar(value=self.config.remember_account)
        self.tk.Checkbutton(
            main, text="记住账号", variable=remember_var,
            font=("Microsoft YaHei UI", 10),
            bg="#f0f4f8", fg="#444",
            selectcolor="#f0f4f8", cursor="hand2",
            command=lambda: self._toggle_setting(
                "remember_account", remember_var.get()),
        ).pack(anchor="w", pady=3)

        # 开机启动
        startup_var = self.tk.BooleanVar(value=self.config.auto_start)
        self.tk.Checkbutton(
            main, text="开机启动", variable=startup_var,
            font=("Microsoft YaHei UI", 10),
            bg="#f0f4f8", fg="#444",
            selectcolor="#f0f4f8", cursor="hand2",
            command=lambda: self._toggle_startup(startup_var.get()),
        ).pack(anchor="w", pady=3)

        # 自动登录（测试用）
        auto_login_var = self.tk.BooleanVar(value=self.config.auto_login)
        self.tk.Checkbutton(
            main, text="自动登录（测试功能）", variable=auto_login_var,
            font=("Microsoft YaHei UI", 10),
            bg="#f0f4f8", fg="#444",
            selectcolor="#f0f4f8", cursor="hand2",
            command=lambda: self._toggle_setting(
                "auto_login", auto_login_var.get()),
        ).pack(anchor="w", pady=3)

        self.tk.Label(main, text="", bg="#f0f4f8").pack(pady=(10, 0))

        self.tk.Button(
            main, text="关闭",
            font=("Microsoft YaHei UI", 11),
            bg="#4a6cf7", fg="white", bd=0, pady=8, cursor="hand2",
            command=dialog.destroy,
        ).pack(fill="x")

    def _toggle_setting(self, name: str, value: bool):
        """切换布尔设置并持久化"""
        setattr(self.config, name, value)
        self.config.save()

    def _toggle_startup(self, enabled: bool):
        """切换开机自启"""
        if not self.adapter:
            self.logger.warn("当前平台不支持开机自启设置")
            return

        ok = self.adapter.set_startup(enabled)
        if ok:
            self.config.auto_start = enabled
            self.config.save()
            self.logger.info(f"{'已设置' if enabled else '已取消'}开机自启")
        else:
            self.config.auto_start = False
            self.logger.error("设置开机自启失败（可能需要管理员权限）")

    # ═══════════════════════════════════════════════════
    # 生命周期
    # ═══════════════════════════════════════════════════

    def _on_close(self):
        """关闭窗口前保存配置"""
        self._save_current()
        self.root.destroy()

    def run(self):
        """启动主循环"""
        # 如果开启了自动登录且有有效账号，延迟后自动登录
        if self.config.auto_login and self.config.validate_account():
            self.logger.info("自动登录已开启，1秒后执行...")
            self.root.after(1000, self._start_login)
        self.root.mainloop()

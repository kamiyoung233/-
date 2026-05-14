# 校园网络助手 — 测试版 v0.1

天津科技大学校园网自动登录工具。基于深澜 Portal 认证系统。

## 功能

- **一键登录** — 输入学号密码，一键完成 Portal 认证
- **状态显示** — 实时显示校园网连接状态、IP 地址、延迟
- **运行日志** — 完整记录登录/检测过程，便于排查问题
- **静默模式** — 后台自动登录，成功不打扰，失败有提示
- **开机自启** — 支持通过 Windows 计划任务设置开机自动运行

## 用法

```bash
# 启动图形界面
python main.py

# 静默模式（自动登录，成功不提示，失败输出到 stderr）
python main.py --silent

# 查看帮助
python main.py --help
```

## 架构

```
test_version/
├── main.py        入口（CLI 解析 + 模式选择）
├── api/           网络/API 层 — Portal HTTP 通信
├── core/          核心逻辑层 — 登录引擎 + 配置 + 日志
├── adapter/       平台适配层 — 开机自启等系统行为
└── ui/            UI 层 — Tkinter 图形界面
```

**分层约束：**
- UI ❌ 不直接调用 API
- Core ❌ 不依赖 UI
- Adapter 只处理平台特定行为

## 打包为 exe

```bash
pip install pyinstaller
python build.py
```

生成的 exe 在 `dist/CampusNetHelper/` 目录。

## 配置

所有行为参数集中在 `config.json`（首次运行自动创建）：

- `retry_count` — 登录重试次数（默认 3）
- `retry_delay` — 重试间隔秒数（默认 3）
- `login_timeout` — Portal 请求超时（默认 10 秒）
- `connectivity_check_urls` — 外网连通性检测目标

## 日志

运行日志写入 `campus_net.log`（与程序同目录），自动轮转。

## 免责声明

> **本工具仅用于校园网络便捷登录。**
>
> - 工具模拟用户在浏览器中的手动登录操作，不修改、不绕过、不破解认证系统。
> - 使用本工具产生的任何后果由用户自行承担。
> - 请遵守天津科技大学校园网络使用规定。
> - 项目作者不对因使用本工具导致的任何直接或间接损失承担责任。

## 开发

```bash
# 环境要求
Python ≥ 3.8
tkinter（通常已内置）

# 验证安装
python -c "import tkinter; print('OK')"
```

## 许可

仅供学习研究使用。

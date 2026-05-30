# 校园网络助手 - v1.0.0-beta

天津科技大学校园网自动登录工具。基于深澜 Portal 认证系统。

## 下载

从 [Releases](https://github.com/kamiyoung233/CampusNetHelper/releases) 下载最新版压缩包，解压后即可使用。

国内下载慢的可以用 QQ 群文件或蓝奏云链接。

## 使用方法

### 安装
1. 解压压缩包到任意文件夹
2. 在 config.json 中填写学号和密码
3. 右键 install.ps1 -> 使用 PowerShell 运行（需要管理员权限）
4. 程序会自动开机启动并每 10 分钟保活

### 手动运行
双击 CampusNetHelper.exe 打开图形界面，点击登录。

### 卸载
右键 uninstall.ps1 -> 使用 PowerShell 运行（需要管理员权限）

## 功能
- 一键登录 / 静默后台运行
- 运行状态显示（IP、延迟、在线时长）
- 开机自启 + 每 10 分钟保活

## 注意事项
- 首次使用请填写 config.json 中的 username 和 password
- 如需修改配置，编辑 config.json 后重启程序
- 本工具仅适用于天津科技大学校园网（深澜 Portal 认证）

## 免责声明

本工具仅用于校园网络便捷登录。使用本工具产生的任何后果由用户自行承担。请遵守天津科技大学校园网络使用规定。

## 许可

仅供学习研究使用。

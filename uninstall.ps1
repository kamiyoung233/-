#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Uninstall CampusNetHelper startup + keepalive
.NOTES
    Run as Administrator!
#>
chcp 65001 > $null
$StartupDir = [Environment]::GetFolderPath("Startup")

# 删开机启动 bat
$BatPath = "$StartupDir\CampusNetHelper.bat"
if (Test-Path $BatPath) { Remove-Item $BatPath -Force; Write-Host "[OK] 已删除开机启动" }

# 删计划任务
schtasks /delete /tn "CampusNetHelperKeepalive" /f 2> $null
Write-Host "[OK] 已删除保活任务"
Write-Host "Uninstall complete."
pause

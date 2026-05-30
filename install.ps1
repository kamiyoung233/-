#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Install CampusNetHelper - startup + keepalive
.NOTES
    Run as Administrator!
#>
chcp 65001 > $null

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = "$ProjectDir\CampusNetHelper.exe"

if (-not (Test-Path $ExePath)) {
    Write-Host "[FAIL] 未找到 CampusNetHelper.exe" -ForegroundColor Red
    pause; exit 1
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   CampusNetHelper v1.0.0-beta - Install" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

$Esc = [char]34

Write-Host ">>> [1/3] 设置开机启动..." -ForegroundColor Cyan
$StartupDir = [Environment]::GetFolderPath("Startup")
$BatPath = "$StartupDir\CampusNetHelper.bat"
$BatText = "@echo off`r`nchcp 65001 >nul`r`nstart $Esc$Esc /B $Esc$ExePath$Esc --silent`r`n"
[System.IO.File]::WriteAllBytes($BatPath, [System.Text.Encoding]::UTF8.GetBytes($BatText))
Write-Host "  [OK] 开机启动已设置" -ForegroundColor Green

Write-Host ">>> [2/3] 创建保活任务（每10分钟）..." -ForegroundColor Cyan
schtasks /delete /tn "CampusNetHelperKeepalive" /f 2> $null
schtasks /create /tn "CampusNetHelperKeepalive" /tr "$Esc$ExePath$Esc --silent" /sc MINUTE /mo 10 /rl HIGHEST /f
if ($LASTEXITCODE -eq 0) { Write-Host "  [OK] 保活任务已创建" -ForegroundColor Green } else { Write-Host "  [WARN] 保活任务创建失败" -ForegroundColor Yellow }

Write-Host ">>> [3/3] 执行首次登录..." -ForegroundColor Cyan
Start-Process -WindowStyle Hidden -FilePath $ExePath -ArgumentList "--silent"
Write-Host "  [OK] 已启动 CampusNetHelper" -ForegroundColor Green

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Done!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
pause

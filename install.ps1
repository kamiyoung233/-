#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Install CampusNetHelper - startup + keepalive
.NOTES
    Run as Administrator!
#>

chcp 65001 > $null

# ── 自动检测当前目录 ──
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MainScript = "$ProjectDir\main.py"

# ── 找 Python ──
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    # 尝试常见路径
    $Candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:ProgramFiles\Python312\python.exe"
    )
    foreach ($c in $Candidates) {
        if (Test-Path $c) { $PythonExe = $c; break }
    }
}
if (-not $PythonExe) {
    Write-Host "[FAIL] 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    pause; exit 1
}

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   CampusNetHelper - Install" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Python : $PythonExe" -ForegroundColor Gray
Write-Host "   Project: $ProjectDir" -ForegroundColor Gray
Write-Host ""

# --- 1. 开机启动（Startup 文件夹 .bat）---
Write-Host ">>> [1/3] 设置开机启动..." -ForegroundColor Cyan
$StartupDir = [Environment]::GetFolderPath("Startup")
$BatPath = "$StartupDir\CampusNetHelper.bat"
$Esc = [char]34
$BatText = "@echo off`r`nchcp 65001 >nul`r`ncd /d $Esc$ProjectDir$Esc`r`nstart $Esc$Esc /B $Esc$PythonExe$Esc $Esc$MainScript$Esc --silent`r`n"
[System.IO.File]::WriteAllBytes($BatPath, [System.Text.Encoding]::UTF8.GetBytes($BatText))
Write-Host "  [OK] 开机启动已设置" -ForegroundColor Green

# --- 2. 保活计划任务 ---
Write-Host ">>> [2/3] 创建保活任务（每10分钟）..." -ForegroundColor Cyan
schtasks /delete /tn "CampusNetHelperKeepalive" /f 2> $null
schtasks /create /tn "CampusNetHelperKeepalive" `
    /tr "$Esc$PythonExe$Esc $Esc$MainScript$Esc --silent" `
    /sc MINUTE /mo 10 /rl HIGHEST /f
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] 保活任务已创建" -ForegroundColor Green
} else {
    Write-Host "  [WARN] 保活任务创建失败" -ForegroundColor Yellow
}

# --- 3. 立即登录 ---
Write-Host ">>> [3/3] 执行首次登录..." -ForegroundColor Cyan
& $PythonExe $MainScript --silent

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Done! 校园网已自动登录" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
pause

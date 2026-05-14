#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Uninstall CampusNetHelper startup + keepalive tasks
.NOTES
    Must run as Administrator!
#>

$PSDefaultParameterValues['*:Encoding'] = 'utf8'
chcp 65001 > $null

$StartupTask   = "CampusNetHelper"
$KeepaliveTask = "CampusNetHelperKeepalive"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   Uninstall CampusNetHelper - Tasks" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

Write-Host ">>> Removing startup task..." -ForegroundColor Cyan
schtasks /delete /tn $StartupTask /f
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Deleted" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Task not found or delete failed" -ForegroundColor Yellow
}

Write-Host ">>> Removing keepalive task..." -ForegroundColor Cyan
schtasks /delete /tn $KeepaliveTask /f
if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Deleted" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Task not found or delete failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Uninstall complete." -ForegroundColor Green
pause

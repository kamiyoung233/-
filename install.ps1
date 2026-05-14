chcp 65001 > $null

$ProjectDir = "C:\Users\Administrator\.openclaw\workspace\auto-login\test_version"
$PythonExe  = "C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
$MainScript = "$ProjectDir\main.py"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   CampusNetHelper - Install Startup" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

$StartupDir = [Environment]::GetFolderPath("Startup")

# --- 1. Remove old junk ---
Write-Host "" -ForegroundColor Cyan
Write-Host ">>> [1/3] Cleaning old startup files..." -ForegroundColor Cyan

$OldFiles = @(
    "$StartupDir\CampusNetHelper.lnk",
    "$StartupDir\login.bat",
    "$StartupDir\auto-login.ps1"
)
foreach ($f in $OldFiles) {
    if (Test-Path $f) {
        Remove-Item $f -Force
        Write-Host "  [DEL] $f" -ForegroundColor Gray
    }
}
Write-Host "  [OK] Cleaned old files" -ForegroundColor Green

# --- 2. Write .bat file directly with .NET ---
Write-Host "" -ForegroundColor Cyan
Write-Host ">>> [2/3] Creating startup .bat..." -ForegroundColor Cyan

$BatPath = "$StartupDir\CampusNetHelper.bat"
$Esc = [char]34  # double quote

# Build the bat content with explicit quoting
$Line1 = "@echo off"
$Line2 = "chcp 65001 >nul"
$Line3 = "cd /d " + $Esc + $ProjectDir + $Esc
$Line4 = "start " + $Esc + $Esc + " /B " + $Esc + $PythonExe + $Esc + " " + $Esc + $MainScript + $Esc
$BatText = $Line1 + "`r`n" + $Line2 + "`r`n" + $Line3 + "`r`n" + $Line4 + "`r`n"

$Utf8Bom = [System.Text.Encoding]::UTF8.GetBytes($BatText)
[System.IO.File]::WriteAllBytes($BatPath, $Utf8Bom)
Write-Host "  [OK] Created: $BatPath" -ForegroundColor Green

# --- 3. Keepalive task ---
Write-Host "" -ForegroundColor Cyan
Write-Host ">>> [3/3] Creating keepalive task..." -ForegroundColor Cyan

$KeepaliveTask = "CampusNetHelperKeepalive"
$CommandLine = $Esc + $PythonExe + $Esc + " " + $Esc + $MainScript + $Esc + " --silent"

schtasks /delete /tn $KeepaliveTask /f 2> $null
schtasks /create /tn $KeepaliveTask `
    /tr "$CommandLine" `
    /sc MINUTE /mo 10 /rl HIGHEST /f

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Keepalive task created" -ForegroundColor Green
} else {
    Write-Host "  [WARN] Keepalive task failed (code: $LASTEXITCODE)" -ForegroundColor Yellow
}

& $PythonExe $MainScript --silent
Write-Host "" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan
pause

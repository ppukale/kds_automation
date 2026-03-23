# Lists adb devices so you can copy serials (emulator-5554, etc.) into config/devices.yaml.
$adb = Get-Command adb -ErrorAction SilentlyContinue
if (-not $adb) {
    Write-Host "adb not found. Add Android SDK platform-tools to PATH, e.g.:" -ForegroundColor Yellow
    Write-Host '  $env:Path += ";$env:LOCALAPPDATA\Android\Sdk\platform-tools"' -ForegroundColor Gray
    exit 1
}
Write-Host "Connected devices (use serial as udid in config/devices.yaml):`n" -ForegroundColor Cyan
& adb devices -l

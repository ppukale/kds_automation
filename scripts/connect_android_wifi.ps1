param(
    [Parameter(Mandatory = $true)]
    [string]$DeviceIp,
    [int]$Port = 5555
)

$adbPath = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path $adbPath)) {
    Write-Host "adb not found at: $adbPath" -ForegroundColor Red
    exit 1
}

$target = "$DeviceIp`:$Port"
Write-Host "Connecting to $target ..." -ForegroundColor Cyan
& $adbPath connect $target

Write-Host "`nCurrent adb devices:" -ForegroundColor Cyan
& $adbPath devices -l

Write-Host "`nUse '$target' as udid in config/devices.yaml" -ForegroundColor Green

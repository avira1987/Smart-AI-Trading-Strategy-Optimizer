# اسکریپت به‌روزرسانی فرانت‌اند (نسخه ساده)
# این فایل اسکریپت اصلی را از پوشه scripts فراخوانی می‌کند

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$updateScript = Join-Path $scriptPath "scripts\update_frontend.ps1"

if (Test-Path $updateScript) {
    & $updateScript @args
} else {
    Write-Host "خطا: اسکریپت update_frontend.ps1 پیدا نشد!" -ForegroundColor Red
    exit 1
}


@echo off
REM اسکریپت به‌روزرسانی مبلغ هدیه ثبت‌نام
REM این اسکریپت مقدار registration_bonus را در SystemSettings به 39000 تومان به‌روزرسانی می‌کند

echo.
echo ========================================
echo به‌روزرسانی مبلغ هدیه ثبت‌نام
echo ========================================
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0update_registration_bonus.ps1" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ خطا در اجرای اسکریپت
    pause
    exit /b %ERRORLEVEL%
)

echo.
pause


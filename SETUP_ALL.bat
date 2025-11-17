@echo off
REM Script برای نصب و راه‌اندازی تمام وابستگی‌های پروژه
REM این فایل باید با دسترسی Administrator اجرا شود

echo =========================================
echo   نصب و راه‌اندازی وابستگی‌های پروژه
echo =========================================
echo.

REM بررسی دسترسی Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [خطا] این اسکریپت نیاز به دسترسی Administrator دارد!
    echo لطفا این فایل را با کلیک راست > Run as Administrator اجرا کنید.
    pause
    exit /b 1
)

echo [موفق] دسترسی Administrator تایید شد!
echo.

REM اجرای اسکریپت PowerShell
powershell -ExecutionPolicy Bypass -File "%~dp0setup_dependencies.ps1"

pause


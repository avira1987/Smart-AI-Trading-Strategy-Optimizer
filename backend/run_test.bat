@echo off
chcp 65001 >nul
cd /d %~dp0
python quick_test.py
if exist test_output.txt (
    echo.
    echo ========================================
    echo نتیجه تست:
    echo ========================================
    type test_output.txt
) else (
    echo فایل خروجی ایجاد نشد!
)
pause

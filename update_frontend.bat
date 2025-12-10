@echo off
REM اسکریپت به‌روزرسانی فرانت‌اند (Batch)
powershell -ExecutionPolicy Bypass -File "%~dp0update_frontend.ps1" %*


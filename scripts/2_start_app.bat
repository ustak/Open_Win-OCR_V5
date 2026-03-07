@echo off
setlocal
cd /d "%~dp0\.."

if not exist "python64\python.exe" (
    echo [错误] 未找到 python64 环境，请先运行 scripts\1_init_env.bat
    pause
    exit /b
)

echo Starting Win OCR V5 (Portable Mode)...
"python64\python.exe" main.py
set "APP_EXIT=%ERRORLEVEL%"
if %APP_EXIT% NEQ 0 (
    echo [ERROR] Win OCR exited with code %APP_EXIT%
    pause
)

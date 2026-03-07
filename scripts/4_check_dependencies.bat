@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo        Win OCR 第五代极速版 Dependency Check
echo ========================================================
echo.

if not exist "python64\python.exe" (
    echo [Error] python64 environment not found. Please run scripts\1_init_env.bat first.
    pause
    exit /b
)

echo [Check] Verifying Python Version...
for /f "delims=" %%i in ('"python64\python.exe" --version') do set PY_VER=%%i
echo Current Version: %PY_VER%
echo %PY_VER% | find "3.11" >nul
if %errorlevel% neq 0 (
    echo [Warning] Python version mismatch! Expected Python 3.11.x
) else (
    echo [OK] Python Version is valid.
)

echo.
echo [Check] Verifying Critical Libraries (V5 Support)...
"python64\python.exe" -c "import PySide6; import paddle; import paddleocr; import cv2; import numpy; print('[OK] All critical libraries (PySide6, paddle, paddleocr, cv2, numpy) imported successfully.')"
if %errorlevel% neq 0 (
    echo [Error] Some libraries are missing or incompatible!
    echo Please re-run scripts\1_init_env.bat to fix dependencies.
)

echo.
echo [Info] Listing installed packages in python64...
"python64\python.exe" -m pip list

echo.
echo ========================================================
echo [Success] Dependency check complete.
echo ========================================================
pause

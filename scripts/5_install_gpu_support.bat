@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo        Win OCR V5 GPU Component Installer
echo ========================================================
echo.
echo NOTE: GPU acceleration requires:
echo 1. An NVIDIA GPU (Intel/AMD not supported).
echo 2. CUDA Toolkit 11.x or 12.x properly configured.
echo.
pause

if not exist "python64\python.exe" (
    echo [ERROR] python64 environment not found. Please run 1_init_env.bat first.
    pause
    exit /b
)

echo.
echo [1/2] Uninstalling CPU version of PaddlePaddle...
"python64\python.exe" -m pip uninstall -y paddlepaddle

echo.
echo [2/2] Downloading and installing GPU version of PaddlePaddle (3.3.0 CUDA 12.9)...
echo This will download several GB of dependencies, please wait patiently.
set http_proxy=
set https_proxy=
"python64\python.exe" -m pip uninstall -y paddlepaddle-gpu >nul 2>nul
"python64\python.exe" -m pip install https://paddle-whl.bj.bcebos.com/stable/cu129/paddlepaddle-gpu/paddlepaddle_gpu-3.3.0-cp311-cp311-win_amd64.whl --trusted-host paddle-whl.bj.bcebos.com

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] GPU package installation failed.
    pause
    exit /b
)

echo.
echo ========================================================
echo [SUCCESS] GPU replacement completed!
echo ========================================================
echo Please enable GPU in settings and try again.
pause

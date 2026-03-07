@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo        Win OCR 第五代极速版 环境全自动初始化工具
echo ========================================================
echo.

set "PY_DIR=python64"
set "PY_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"
set "PIP_URL=https://bootstrap.pypa.io/get-pip.py"

:: 1. 检查环境变量
if exist "%PY_DIR%\python.exe" (
    echo [检查] %PY_DIR% 环境已存在，准备检查依赖...
    goto :FIX_PIP_CONFIG
)

:: 2. 下载 Python 嵌入版 (3.11.9 - 64bit)
echo [1/5] 正在下载 Python 3.11 (64-bit) 嵌入版...
powershell -Command "Invoke-WebRequest -Uri '%PY_URL%' -OutFile 'python64.zip'"
if not exist "python64.zip" (
    echo [错误] 下载失败，请检查网络。
    pause
    exit /b
)

:: 3. 解压
echo [2/5] 正在解压...
powershell -Command "Expand-Archive -Path 'python64.zip' -DestinationPath '%PY_DIR%' -Force"
del python64.zip

:FIX_PIP_CONFIG
:: 4. 修正 ._pth 文件以支持 pip
echo [3/5] 正在配置环境路径...
set "PTH_FILE=%PY_DIR%\python311._pth"
powershell -Command "if (Test-Path '%PTH_FILE%') { (Get-Content '%PTH_FILE%') -replace '#import site', 'import site' | Set-Content '%PTH_FILE%' } else { echo 'Warning: .pth file not found at %PTH_FILE%' }"

:: 5. 安装 pip
echo [4/5] 正在安装 pip...
if not exist "%PY_DIR%\Scripts\pip.exe" (
    powershell -Command "Invoke-WebRequest -Uri '%PIP_URL%' -OutFile 'get-pip.py'"
    "%PY_DIR%\python.exe" get-pip.py --no-warn-script-location --no-cache-dir
    del get-pip.py
)

:: 6. 安装依赖库，适配最新的 PP-OCRv5 和 PaddlePaddle 3.x
echo.
echo [5/5] 正在安装依赖库 (PySide6, PaddleOCR v3 等)...
if not exist "temp_install" mkdir "temp_install"
set TMP=%~dp0..\temp_install
set TEMP=%~dp0..\temp_install

:: Ensure portable build uses stable CPU runtime, not legacy beta GPU package.
"%PY_DIR%\python.exe" -m pip uninstall -y paddlepaddle-gpu >nul 2>nul

"%PY_DIR%\python.exe" -m pip install --no-cache-dir wheel setuptools -i https://pypi.tuna.tsinghua.edu.cn/simple
:: 安装 requirements.txt 中的包
if exist "requirements.txt" (
    "%PY_DIR%\python.exe" -m pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    echo [警告] 未找到 requirements.txt
)

:: 清理
cd /d "%~dp0\.."
rmdir /s /q "temp_install" 2>nul

echo.
echo ========================================================
echo [成功] 嵌入式环境部署完成！
echo ========================================================
pause

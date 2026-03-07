@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0\.."

echo ========================================================
echo        Win OCR 第五代极速版 便携版一键打包工具
echo ========================================================
echo.

if not exist "python64\python.exe" (
    echo [错误] 环境未初始化，请先运行 scripts\1_init_env.bat
    pause
    exit /b
)

echo [信息] 正在清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

:: 确保安装了 pyinstaller
"python64\python.exe" -m pip install pyinstaller

echo [信息] 开始针对 V5 引擎打包...
"python64\python.exe" -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --clean ^
    --name "Win_OCR_v5_Release" ^
    --collect-all "paddleocr" ^
    --collect-all "paddlex" ^
    --collect-all "paddle" ^
    --copy-metadata "paddlex" ^
    --copy-metadata "paddleocr" ^
    --copy-metadata "imagesize" ^
    --copy-metadata "opencv-contrib-python" ^
    --copy-metadata "pyclipper" ^
    --copy-metadata "pypdfium2" ^
    --copy-metadata "python-bidi" ^
    --copy-metadata "shapely" ^
    --add-data "python64\Lib\site-packages\paddle\libs;paddle\libs" ^
    --add-binary "python64\Lib\site-packages\nvidia\cuda_runtime\bin\*.dll;nvidia\cuda_runtime\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\cudnn\bin\*.dll;nvidia\cudnn\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\cublas\bin\*.dll;nvidia\cublas\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\cufft\bin\*.dll;nvidia\cufft\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\curand\bin\*.dll;nvidia\curand\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\cusolver\bin\*.dll;nvidia\cusolver\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\cusparse\bin\*.dll;nvidia\cusparse\bin" ^
    --add-binary "python64\Lib\site-packages\nvidia\nvjitlink\bin\*.dll;nvidia\nvjitlink\bin" ^
    --hidden-import "framework_pb2" ^
    --exclude-module "paddle.tensorrt" ^
    main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 打包完成！
    echo 可执行文件位于 dist 文件夹内。
    echo.
    start explorer dist
) else (
    echo [失败] 打包出错。
)
pause

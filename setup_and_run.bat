@echo off
chcp 65001 >nul
echo ========================================
echo   Anime Outfit Analyzer — 一键安装运行
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/3] 安装依赖...
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo [2/3] 首次运行会自动下载 AI 模型 (~600MB)，请耐心等待...
echo [3/3] 启动应用...
echo.

python main.py

pause

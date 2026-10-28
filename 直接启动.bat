@echo off
chcp 65001 >nul
title 🐾 西西工具包 · 直接启动 V4.1

:: 1. 自动向上寻址定位西西工具包根目录（严禁在 if 括号内使用 %CD%，彻底杜绝子目录变量展开失效）
cd /d "%~dp0"
if not exist "xixi_toolkit_launcher.py" if not exist "系统资源\xixi_toolkit_launcher.py" cd /d "%~dp0.."
set "XIXI_ROOT=%CD%\"
set "XIXI_TOOLKIT_ROOT=%CD%"

set "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"
if not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\xixi_toolkit_launcher.py"

if not exist "%XIXI_SCRIPT%" (
    echo [错误] 未在根目录或『系统资源\』下找到 xixi_toolkit_launcher.py！
    echo 当前探测目录: %XIXI_ROOT%
    pause
    exit /b 1
)

:: 2. 优先寻找真实安装的 Python，避开 WindowsApps 空壳商店别名
set "PY_CMD="
set "PYW_CMD="

for /f "delims=" %%i in ('where python 2^>nul') do (
    echo "%%i" | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        if not defined PY_CMD set "PY_CMD=%%i"
    )
)

for /f "delims=" %%i in ('where pythonw 2^>nul') do (
    echo "%%i" | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        if not defined PYW_CMD set "PYW_CMD=%%i"
    )
)

if not defined PY_CMD (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PY_CMD=%%D\python.exe"
        if exist "%%D\pythonw.exe" set "PYW_CMD=%%D\pythonw.exe"
    )
)

if not defined PY_CMD (
    echo [!] 未检测到 Python 环境，请确认已安装 Python 3.10+ 并勾选 Add Python to PATH。
    pause
    exit /b 1
)

:: 3. 检测 pywebview 是否已安装；若未安装则走清华源自动补齐
"%PY_CMD%" -c "import webview" >nul 2>&1
if errorlevel 1 (
    echo [西西工具包] 首次运行正在为您自动配置原生桌面窗口组件 pywebview ...
    "%PY_CMD%" -m pip install pywebview pillow pymupdf python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
)

:: 4. 优先无黑框启动；若返回非0则打印详细报错
if defined PYW_CMD (
    start "" "%PYW_CMD%" "%XIXI_SCRIPT%"
    exit /b 0
) else (
    "%PY_CMD%" "%XIXI_SCRIPT%"
    if errorlevel 1 (
        echo.
        echo [!] 启动遇到异常，请查看上方报错信息。
        pause
    )
)

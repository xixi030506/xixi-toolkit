@echo off
chcp 65001 >nul
title 🐾 西西工具包 · 一键生成总控 EXE (支持子文件夹调用 + 自动嵌入Q版图标)

:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%，彻底解决『工具\』子目录运行失效问题）
cd /d "%~dp0"
if not exist "xixi_toolkit_launcher.py" if not exist "系统资源\xixi_toolkit_launcher.py" cd /d "%~dp0.."
set "XIXI_ROOT=%CD%\"
set "XIXI_TOOLKIT_ROOT=%CD%"

set "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"
if not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\xixi_toolkit_launcher.py"

if not exist "%XIXI_SCRIPT%" (
    echo [错误] 未找到 xixi_toolkit_launcher.py！
    echo 请确保 xixi_toolkit_launcher.py 位于 %XIXI_ROOT% 或 %XIXI_ROOT%系统资源\ 下。
    pause
    exit /b 1
)

set "PY_CMD="
for /f "delims=" %%i in ('where python 2^>nul') do (
    echo "%%i" | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        if not defined PY_CMD set "PY_CMD=%%i"
    )
)
if not defined PY_CMD (
    for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
        if exist "%%D\python.exe" set "PY_CMD=%%D\python.exe"
    )
)
if not defined PY_CMD set "PY_CMD=python"

"%PY_CMD%" "%XIXI_SCRIPT%" --build-exe
echo.
pause

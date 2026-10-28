@echo off
chcp 65001 >nul
title 🔄 西西工具包 · 一键更新与版本回退助手 (支持『工具\』子目录直接运行)

:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%）
cd /d "%~dp0"
if not exist "xixi_toolkit_launcher.py" if not exist "系统资源\xixi_toolkit_launcher.py" cd /d "%~dp0.."
set "XIXI_ROOT=%CD%\"
set "XIXI_TOOLKIT_ROOT=%CD%"

:MENU
cls
echo ========================================================================
echo        🐾 西西工具包 · 热更新、本地版本回退与依赖自检中心 V4.1
echo        📍 当前锁定工具包根目录: %XIXI_ROOT%
echo ========================================================================
echo.
echo   [1] 🚀 一键拉取最新热更新 (git pull + 自动扫描『系统资源\requirements.txt』装库)
echo   [2] ⏪ 浏览本地 Git 历史版本并回退到任意旧版 (git log / checkout)
echo   [3] 📦 仅扫描并补齐所有插件所需 Python 依赖库 (清华镜像极速安装)
echo   [4] 🔧 一键修复/同步『工具\』与根目录下的全部辅助脚本
echo   [0] ❌ 退出助手
echo.
echo ========================================================================
set /p CHOICE="👉 请输入数字并按回车 [1/2/3/4/0]: "

if "%CHOICE%"=="1" goto DO_PULL
if "%CHOICE%"=="2" goto DO_ROLLBACK
if "%CHOICE%"=="3" goto DO_DEPS
if "%CHOICE%"=="4" goto DO_REPAIR
if "%CHOICE%"=="0" exit /b 0
goto MENU

:DO_PULL
echo.
echo [1/2] 正在同步远程仓库最新代码 (您的 缓存/、bak/、自定义样式/、自定义图片/ 均受保护)...
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo [提示] 当前仓库尚未绑定远程地址 origin，跳过云端拉取，直接为您切回本地最新 main 分支...
    git checkout main
) else (
    git fetch --all
    git checkout main 2>nul || git checkout master 2>nul
    git pull --ff-only
)
goto DO_DEPS

:DO_ROLLBACK
echo.
echo ---------------- 最近 15 个历史版本记录 (Hash ^| 时间 ^| 说明) ----------------
git log --all -n 15 --date=format:"%%Y-%%m-%%d %%H:%%M" --pretty=format:"  [%%h]  %%ad  ^|  %%s %%d"
echo.
echo ------------------------------------------------------------------------------
echo 💡 提示：输入上方中括号里的 7 位版本号（如 b027882）即可回退；输入 main 可回到最新版。
set /p TARGET_HASH="👉 请输入要切换/回退的目标版本号 (直接回车取消): "
if "%TARGET_HASH%"=="" goto MENU
git checkout -- .
git checkout -f %TARGET_HASH%
if %errorlevel% equ 0 (
    echo.
    echo ✅ 已成功切换至版本 [%TARGET_HASH%]！
) else (
    echo.
    echo ⚠️ 版本切换未成功，请检查输入的版本号是否正确。
)
pause
goto MENU

:DO_DEPS
echo.
echo [正在检索『系统资源\requirements.txt』及所有插件子目录的依赖库...]
if exist "%XIXI_ROOT%系统资源\requirements.txt" (
    echo   - 正在校验: 系统资源\requirements.txt
    python -m pip install -r "%XIXI_ROOT%系统资源\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
)
if exist "%XIXI_ROOT%requirements.txt" (
    echo   - 正在校验: requirements.txt
    python -m pip install -r "%XIXI_ROOT%requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
)
for /d %%D in ("%XIXI_ROOT%*") do (
    if exist "%%D\requirements.txt" (
        echo   - 正在校验子目录依赖: %%~nxD\requirements.txt
        python -m pip install -r "%%D\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
    )
)
echo.
echo 🎉 所有依赖库校验与补齐完成！
pause
goto MENU

:DO_REPAIR
echo.
set "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"
if not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\xixi_toolkit_launcher.py"
python "%XIXI_SCRIPT%" --repair-scripts
echo.
pause
goto MENU

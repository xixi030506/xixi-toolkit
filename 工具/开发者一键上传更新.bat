@echo off
chcp 65001 >nul
title 🚀 西西工具包 · 开发者一键归档与上传更新 (支持『工具\』子目录直接运行)

:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%）
cd /d "%~dp0"
if not exist "xixi_toolkit_launcher.py" if not exist "系统资源\xixi_toolkit_launcher.py" cd /d "%~dp0.."
set "XIXI_ROOT=%CD%\"
set "XIXI_TOOLKIT_ROOT=%CD%"

echo ========================================================================
echo   🚀 西西工具包 · 开发者一键 Git 本地归档 / 远程推送助手 V4.1
echo   📍 当前锁定工具包根目录: %XIXI_ROOT%
echo ========================================================================
echo.

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Git，请先安装 Git for Windows！
    pause
    exit /b 1
)

if not exist ".git" (
    echo [提示] 当前根目录尚未初始化 Git 仓库，正在为您执行 git init -b main ...
    git init -b main
)

echo [当前变动文件预览]:
git status -s
echo ------------------------------------------------------------------------
set /p COMMIT_MSG="✏️ 请输入本次更新说明 (直接回车默认使用当前时间戳归档): "
if "%COMMIT_MSG%"=="" set "COMMIT_MSG=feat(v4.1): 架构整理 + 四大系统子目录 + 隐藏收纳盒 + 跨文件夹脚本寻址修复 (%date:~0,10% %time:~0,5%)"

echo.
echo [1/3] 正在暂存所有源码与插件改动 (自动忽略 缓存/、bak/、自定义样式/、自定义图片/ 等私有数据)...
git add -A

echo [2/3] 正在提交到本地 Git 历史仓库...
git commit -m "%COMMIT_MSG%"

echo [3/3] 正在检查是否配置了远程仓库 (origin)...
git remote get-url origin >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ========================================================================
    echo   ✅ 本地 Git 归档提交已完成！
    echo   💡 当前尚未绑定远程云端仓库（或者 GitHub 暂未解封），您的所有版本历史
    echo      均已安全保存在本地 .git 仓库中，随时可在启动器『🔄 版本管理』回退！
    echo   💡 日后绑定 Gitee / GitHub 只需执行:
    echo      git remote add origin 您的仓库地址
    echo      git push -u origin main --tags
    echo ========================================================================
    pause
    exit /b 0
)

echo 正在推送到远程云端仓库...
git push
if %errorlevel% equ 0 (
    echo.
    echo ========================================================================
    echo   🎉 恭喜绮绮！本地归档与远程热更新推送全部成功！
    echo ========================================================================
) else (
    echo.
    echo [提示] 本地提交已成功保存！但推送到远程仓库未成功，请检查网络或远程仓库权限。
)
echo.
pause

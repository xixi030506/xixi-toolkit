#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🐾 西西工具包 · 轻量总控启动器 V4.0 (xixi_toolkit_launcher.py)
====================================================================================================
核心目录架构（V4.0 四大标准系统子夹 + 极简根目录 + 标志文件扫描 + 隐藏收纳盒）：
1. 【极简根目录与四大标准子文件夹】：
   - `工具/` (`D:\西西工具包\工具\`)：集中存放所有辅助批处理脚本（生成EXE、恢复出厂默认、Git上传/回退）与开发计划；
   - `bak/` (`D:\西西工具包\bak\`)：存放手动备份与一键快照备份压缩包；
   - `缓存/` (`D:\西西工具包\缓存\`)：存放启动器记忆配置 `launcher_memory.json`（含分类、隐藏列表、扫描模式、自定义路径）；
   - `系统资源/` (`D:\西西工具包\系统资源\`)：存放全局公用资源（`xixi_icon.ico`、`requirements.txt` 及启动器脚本备份）；
   - 根目录只保留各插件子文件夹、`西西工具包.exe`、`直接启动.bat`（`xixi_toolkit_launcher.py` 放根目录或 `系统资源/` 均可自动识别）。
2. 【双层插件过滤机制：`plugin.json` 标志文件 + 左侧 `🙈 隐藏收纳盒`】：
   - 绝不显示硬盘上不存在的虚空预设插件（如未创建的字数统计、重命名工具）；
   - 自动屏蔽 `工具`、`bak`、`缓存`、`系统资源`、`资源` 等系统辅助目录；
   - 支持切换「🏷️ 智能识别模式（含 `plugin.json` 标志文件或含可运行入口文件）」与「🔒 严格标志模式（仅显示含 `plugin.json` 的子文件夹）」；
   - 左侧分类栏底部常驻「🙈 隐藏收纳盒」，支持把任意卡片拖拽进去（或点卡片上的 `🙈` 按钮）一键隐藏，隐藏后绝不出现在全部工具或全部平铺中。
3. 【排版防折行与一键便捷工具】：
   - 全面加宽窗口与顶栏按钮 `whitespace-nowrap shrink-0`，彻底杜绝文字竖排折行；
   - 内置「🧹 一键整理根目录」、「📦 一键快照备份到 bak/」、「➕ 新建插件向导」与「🏷️ 插件信息/标志文件编辑」。
"""

import base64
import csv
import ctypes
import datetime
import hashlib
import http.server
import importlib.metadata
import importlib.util
import inspect
import io
import json
import math
import os
import random
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import urllib.request
import uuid
import webbrowser
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path

# 防止在 pythonw.exe 无黑框模式下 sys.stdout / sys.stderr 为 None 导致底层库打印日志时静默闪退
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except ImportError:
    tk = None
    filedialog = None
    messagebox = None


SYSTEM_SUPPORT_FOLDERS = {
    "工具",
    "小工具",
    "bak",
    "backup",
    "缓存",
    "历史缓存",
    "系统资源",
    "资源",
    "自定义样式",
    "自定义图片",
    "默认导出",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "_新插件标准模板_复制改名",
    "_回收站备份",
    "目录",
}


def get_base_dir() -> Path:
    """
    智能获取西西工具包根目录 `D:\\西西工具包\\`：
    兼容 `xixi_toolkit_launcher.py` 放在根目录、`系统资源/`、`工具/` 或 `西西工具包.exe` 启动。
    """
    env_root = os.environ.get("XIXI_TOOLKIT_ROOT", "").strip()
    if env_root:
        p = Path(env_root).resolve()
        if p.is_dir():
            return p
    if getattr(sys, "frozen", False):
        exe_parent = Path(sys.executable).resolve().parent
        if exe_parent.name in ("工具", "小工具", "系统资源", "资源", "缓存", "bak"):
            return exe_parent.parent
        return exe_parent
    if sys.argv and sys.argv[0]:
        argv0 = Path(sys.argv[0]).resolve()
        if argv0.is_file() and argv0.suffix.lower() == ".exe":
            if argv0.parent.name in ("工具", "小工具", "系统资源", "资源", "缓存", "bak"):
                return argv0.parent.parent
            return argv0.parent
    here = Path(__file__).resolve()
    parent = here.parent
    if parent.name in ("工具", "小工具", "系统资源", "资源", "缓存", "bak"):
        return parent.parent
    return parent


BASE_DIR = get_base_dir()

# 四大标准系统子目录
TOOLS_DIR = BASE_DIR / "工具"
BAK_DIR = BASE_DIR / "bak"
CACHE_DIR = BASE_DIR / "缓存"
SYS_RES_DIR = BASE_DIR / "系统资源"

# 启动器记忆文件存储在 `D:\西西工具包\缓存\launcher_memory.json`（兼容旧版 ~/.xixi_toolkit_user_config.json 自动迁移）
USER_CONFIG_PATH = CACHE_DIR / "launcher_memory.json"
LEGACY_USER_CONFIG_PATH = Path.home() / ".xixi_toolkit_user_config.json"

PLUGIN_MARKER_FILENAME = "plugin.json"
HIDDEN_CATEGORY_ID = "__hidden__"

HUB_WIDTH = 980
HUB_HEIGHT = 640
PLUGIN_WIDTH = 1400
PLUGIN_HEIGHT = 900

TSINGHUA_MIRROR = "https://pypi.tuna.tsinghua.edu.cn/simple"

DEFAULT_CATEGORIES = [
    {"id": "doc", "name": "📄 文档与办公"},
    {"id": "media", "name": "🎨 视觉与画布"},
    {"id": "disk", "name": "⚡ 批量与系统"},
    {"id": "custom", "name": "🧩 扩展插件"},
]

BUILTIN_PLUGINS = [
    {
        "id": "stamp_studio",
        "name": "西西盖章局",
        "subtitle": "PDF/Word 强力防删水印与印章工坊",
        "defaultCategory": "doc",
        "icon": "🌸",
        "color": "rose",
        "defaultFolder": "西西盖章局",
        "defaultRelPath": "西西盖章局/v5_pdf.html",
        "fallbackRelPath": "西西盖章局/v5_1pdf.html",
        "fingerprints": ["西西盖章局", "watermarkOverlayCanvas", "XixiWatermarkShape"],
        "keywords": ["盖章", "水印", "watermark", "stamp", "v5_pdf", "v5_1pdf"],
    },
    {
        "id": "word_counter",
        "name": "字数统计与排版",
        "subtitle": "中英文字数统计、敏感词排查与一键排版",
        "defaultCategory": "doc",
        "icon": "📝",
        "color": "amber",
        "defaultFolder": "字数统计与排版",
        "defaultRelPath": "字数统计与排版/word_counter.html",
        "fallbackRelPath": "字数统计与排版/index.html",
        "fingerprints": ["字数统计", "word_counter"],
        "keywords": ["字数", "排版", "word", "counter", "text"],
    },
    {
        "id": "batch_rename",
        "name": "批量重命名工具",
        "subtitle": "多文件前后缀替换、序号重排与扩展名修改",
        "defaultCategory": "disk",
        "icon": "⚡",
        "color": "indigo",
        "defaultFolder": "重命名工具",
        "defaultRelPath": "重命名工具/rename_tool.html",
        "fallbackRelPath": "重命名工具/main.py",
        "fingerprints": ["重命名", "batch_rename", "rename_tool"],
        "keywords": ["重命名", "改名", "rename", "batch"],
    },
]

IGNORED_DIRS = set(SYSTEM_SUPPORT_FOLDERS)
IGNORED_FILES = {
    "直接启动.bat",
    "xixi_toolkit_launcher.py",
    "stamp_studio_backend.py",
    "template_backend.py",
    "启动西西工具包.bat",
    "点我启动.bat",
    "开发者一键上传更新.bat",
    "一键更新与回退版本.bat",
    "一键生成西西工具包EXE.bat",
    "一键重置出厂默认_移入回收站.bat",
    "xixi_icon.ico",
    "一键打包总控EXE.bat",
    "西西工具包.exe",
    "xixi_toolkit_launcher.exe",
    "plugin.json",
    "requirements.txt",
    "计划.txt",
}
RUNNABLE_EXTS = {".html", ".htm", ".py", ".pyw", ".exe", ".bat"}


# ==================== 四大标准子目录初始化与根目录一键整理引擎 ====================


# ==================== 内置 V4.1 跨文件夹自适应批处理脚本与 .gitignore 自动修复模板 ====================

BAT_TPL_DIRECT_START = '@echo off\nchcp 65001 >nul\ntitle 🐾 西西工具包 · 直接启动 V4.1\n\n:: 1. 自动向上寻址定位西西工具包根目录（严禁在 if 括号内使用 %CD%，彻底杜绝子目录变量展开失效）\ncd /d "%~dp0"\nif not exist "xixi_toolkit_launcher.py" if not exist "系统资源\\xixi_toolkit_launcher.py" cd /d "%~dp0.."\nset "XIXI_ROOT=%CD%\\"\nset "XIXI_TOOLKIT_ROOT=%CD%"\n\nset "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"\nif not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\\xixi_toolkit_launcher.py"\n\nif not exist "%XIXI_SCRIPT%" (\n    echo [错误] 未在根目录或『系统资源\\』下找到 xixi_toolkit_launcher.py！\n    echo 当前探测目录: %XIXI_ROOT%\n    pause\n    exit /b 1\n)\n\n:: 2. 优先寻找真实安装的 Python，避开 WindowsApps 空壳商店别名\nset "PY_CMD="\nset "PYW_CMD="\n\nfor /f "delims=" %%i in (\'where python 2^>nul\') do (\n    echo "%%i" | findstr /i "WindowsApps" >nul\n    if errorlevel 1 (\n        if not defined PY_CMD set "PY_CMD=%%i"\n    )\n)\n\nfor /f "delims=" %%i in (\'where pythonw 2^>nul\') do (\n    echo "%%i" | findstr /i "WindowsApps" >nul\n    if errorlevel 1 (\n        if not defined PYW_CMD set "PYW_CMD=%%i"\n    )\n)\n\nif not defined PY_CMD (\n    for /d %%D in ("%LocalAppData%\\Programs\\Python\\Python3*") do (\n        if exist "%%D\\python.exe" set "PY_CMD=%%D\\python.exe"\n        if exist "%%D\\pythonw.exe" set "PYW_CMD=%%D\\pythonw.exe"\n    )\n)\n\nif not defined PY_CMD (\n    echo [!] 未检测到 Python 环境，请确认已安装 Python 3.10+ 并勾选 Add Python to PATH。\n    pause\n    exit /b 1\n)\n\n:: 3. 检测 pywebview 是否已安装；若未安装则走清华源自动补齐\n"%PY_CMD%" -c "import webview" >nul 2>&1\nif errorlevel 1 (\n    echo [西西工具包] 首次运行正在为您自动配置原生桌面窗口组件 pywebview ...\n    "%PY_CMD%" -m pip install pywebview pillow pymupdf python-docx -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn\n)\n\n:: 4. 优先无黑框启动；若返回非0则打印详细报错\nif defined PYW_CMD (\n    start "" "%PYW_CMD%" "%XIXI_SCRIPT%"\n    exit /b 0\n) else (\n    "%PY_CMD%" "%XIXI_SCRIPT%"\n    if errorlevel 1 (\n        echo.\n        echo [!] 启动遇到异常，请查看上方报错信息。\n        pause\n    )\n)\n'
BAT_TPL_BUILD_EXE = '@echo off\nchcp 65001 >nul\ntitle 🐾 西西工具包 · 一键生成总控 EXE (支持子文件夹调用 + 自动嵌入Q版图标)\n\n:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%，彻底解决『工具\\』子目录运行失效问题）\ncd /d "%~dp0"\nif not exist "xixi_toolkit_launcher.py" if not exist "系统资源\\xixi_toolkit_launcher.py" cd /d "%~dp0.."\nset "XIXI_ROOT=%CD%\\"\nset "XIXI_TOOLKIT_ROOT=%CD%"\n\nset "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"\nif not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\\xixi_toolkit_launcher.py"\n\nif not exist "%XIXI_SCRIPT%" (\n    echo [错误] 未找到 xixi_toolkit_launcher.py！\n    echo 请确保 xixi_toolkit_launcher.py 位于 %XIXI_ROOT% 或 %XIXI_ROOT%系统资源\\ 下。\n    pause\n    exit /b 1\n)\n\nset "PY_CMD="\nfor /f "delims=" %%i in (\'where python 2^>nul\') do (\n    echo "%%i" | findstr /i "WindowsApps" >nul\n    if errorlevel 1 (\n        if not defined PY_CMD set "PY_CMD=%%i"\n    )\n)\nif not defined PY_CMD (\n    for /d %%D in ("%LocalAppData%\\Programs\\Python\\Python3*") do (\n        if exist "%%D\\python.exe" set "PY_CMD=%%D\\python.exe"\n    )\n)\nif not defined PY_CMD set "PY_CMD=python"\n\n"%PY_CMD%" "%XIXI_SCRIPT%" --build-exe\necho.\npause\n'
BAT_TPL_FACTORY_RESET = '@echo off\nchcp 65001 >nul\ntitle 🧹 西西工具包 · 一键恢复出厂初始默认状态 (移入回收站)\n\n:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%，彻底解决『工具\\』子目录运行失效问题）\ncd /d "%~dp0"\nif not exist "xixi_toolkit_launcher.py" if not exist "系统资源\\xixi_toolkit_launcher.py" cd /d "%~dp0.."\nset "XIXI_ROOT=%CD%\\"\nset "XIXI_TOOLKIT_ROOT=%CD%"\n\nset "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"\nif not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\\xixi_toolkit_launcher.py"\n\nif not exist "%XIXI_SCRIPT%" (\n    echo [错误] 未找到 xixi_toolkit_launcher.py！\n    echo 请确保 xixi_toolkit_launcher.py 位于 %XIXI_ROOT% 或 %XIXI_ROOT%系统资源\\ 下。\n    pause\n    exit /b 1\n)\n\nset "PY_CMD="\nfor /f "delims=" %%i in (\'where python 2^>nul\') do (\n    echo "%%i" | findstr /i "WindowsApps" >nul\n    if errorlevel 1 (\n        if not defined PY_CMD set "PY_CMD=%%i"\n    )\n)\nif not defined PY_CMD (\n    for /d %%D in ("%LocalAppData%\\Programs\\Python\\Python3*") do (\n        if exist "%%D\\python.exe" set "PY_CMD=%%D\\python.exe"\n    )\n)\nif not defined PY_CMD set "PY_CMD=python"\n\n"%PY_CMD%" "%XIXI_SCRIPT%" --factory-reset\necho.\npause\n'
BAT_TPL_DEV_PUSH = '@echo off\nchcp 65001 >nul\ntitle 🚀 西西工具包 · 开发者一键归档与上传更新 (支持『工具\\』子目录直接运行)\n\n:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%）\ncd /d "%~dp0"\nif not exist "xixi_toolkit_launcher.py" if not exist "系统资源\\xixi_toolkit_launcher.py" cd /d "%~dp0.."\nset "XIXI_ROOT=%CD%\\"\nset "XIXI_TOOLKIT_ROOT=%CD%"\n\necho ========================================================================\necho   🚀 西西工具包 · 开发者一键 Git 本地归档 / 远程推送助手 V4.1\necho   📍 当前锁定工具包根目录: %XIXI_ROOT%\necho ========================================================================\necho.\n\nwhere git >nul 2>nul\nif %errorlevel% neq 0 (\n    echo [错误] 未检测到 Git，请先安装 Git for Windows！\n    pause\n    exit /b 1\n)\n\nif not exist ".git" (\n    echo [提示] 当前根目录尚未初始化 Git 仓库，正在为您执行 git init -b main ...\n    git init -b main\n)\n\necho [当前变动文件预览]:\ngit status -s\necho ------------------------------------------------------------------------\nset /p COMMIT_MSG="✏️ 请输入本次更新说明 (直接回车默认使用当前时间戳归档): "\nif "%COMMIT_MSG%"=="" set "COMMIT_MSG=feat(v4.1): 架构整理 + 四大系统子目录 + 隐藏收纳盒 + 跨文件夹脚本寻址修复 (%date:~0,10% %time:~0,5%)"\n\necho.\necho [1/3] 正在暂存所有源码与插件改动 (自动忽略 缓存/、bak/、自定义样式/、自定义图片/ 等私有数据)...\ngit add -A\n\necho [2/3] 正在提交到本地 Git 历史仓库...\ngit commit -m "%COMMIT_MSG%"\n\necho [3/3] 正在检查是否配置了远程仓库 (origin)...\ngit remote get-url origin >nul 2>nul\nif %errorlevel% neq 0 (\n    echo.\n    echo ========================================================================\n    echo   ✅ 本地 Git 归档提交已完成！\n    echo   💡 当前尚未绑定远程云端仓库（或者 GitHub 暂未解封），您的所有版本历史\n    echo      均已安全保存在本地 .git 仓库中，随时可在启动器『🔄 版本管理』回退！\n    echo   💡 日后绑定 Gitee / GitHub 只需执行:\n    echo      git remote add origin 您的仓库地址\n    echo      git push -u origin main --tags\n    echo ========================================================================\n    pause\n    exit /b 0\n)\n\necho 正在推送到远程云端仓库...\ngit push\nif %errorlevel% equ 0 (\n    echo.\n    echo ========================================================================\n    echo   🎉 恭喜绮绮！本地归档与远程热更新推送全部成功！\n    echo ========================================================================\n) else (\n    echo.\n    echo [提示] 本地提交已成功保存！但推送到远程仓库未成功，请检查网络或远程仓库权限。\n)\necho.\npause\n'
BAT_TPL_UPDATE_ROLLBACK = '@echo off\nchcp 65001 >nul\ntitle 🔄 西西工具包 · 一键更新与版本回退助手 (支持『工具\\』子目录直接运行)\n\n:: 1. 自动向上寻址定位西西工具包根目录（不在 if 括号内使用 %CD%）\ncd /d "%~dp0"\nif not exist "xixi_toolkit_launcher.py" if not exist "系统资源\\xixi_toolkit_launcher.py" cd /d "%~dp0.."\nset "XIXI_ROOT=%CD%\\"\nset "XIXI_TOOLKIT_ROOT=%CD%"\n\n:MENU\ncls\necho ========================================================================\necho        🐾 西西工具包 · 热更新、本地版本回退与依赖自检中心 V4.1\necho        📍 当前锁定工具包根目录: %XIXI_ROOT%\necho ========================================================================\necho.\necho   [1] 🚀 一键拉取最新热更新 (git pull + 自动扫描『系统资源\\requirements.txt』装库)\necho   [2] ⏪ 浏览本地 Git 历史版本并回退到任意旧版 (git log / checkout)\necho   [3] 📦 仅扫描并补齐所有插件所需 Python 依赖库 (清华镜像极速安装)\necho   [4] 🔧 一键修复/同步『工具\\』与根目录下的全部辅助脚本\necho   [0] ❌ 退出助手\necho.\necho ========================================================================\nset /p CHOICE="👉 请输入数字并按回车 [1/2/3/4/0]: "\n\nif "%CHOICE%"=="1" goto DO_PULL\nif "%CHOICE%"=="2" goto DO_ROLLBACK\nif "%CHOICE%"=="3" goto DO_DEPS\nif "%CHOICE%"=="4" goto DO_REPAIR\nif "%CHOICE%"=="0" exit /b 0\ngoto MENU\n\n:DO_PULL\necho.\necho [1/2] 正在同步远程仓库最新代码 (您的 缓存/、bak/、自定义样式/、自定义图片/ 均受保护)...\ngit remote get-url origin >nul 2>nul\nif %errorlevel% neq 0 (\n    echo [提示] 当前仓库尚未绑定远程地址 origin，跳过云端拉取，直接为您切回本地最新 main 分支...\n    git checkout main\n) else (\n    git fetch --all\n    git checkout main 2>nul || git checkout master 2>nul\n    git pull --ff-only\n)\ngoto DO_DEPS\n\n:DO_ROLLBACK\necho.\necho ---------------- 最近 15 个历史版本记录 (Hash ^| 时间 ^| 说明) ----------------\ngit log --all -n 15 --date=format:"%%Y-%%m-%%d %%H:%%M" --pretty=format:"  [%%h]  %%ad  ^|  %%s %%d"\necho.\necho ------------------------------------------------------------------------------\necho 💡 提示：输入上方中括号里的 7 位版本号（如 b027882）即可回退；输入 main 可回到最新版。\nset /p TARGET_HASH="👉 请输入要切换/回退的目标版本号 (直接回车取消): "\nif "%TARGET_HASH%"=="" goto MENU\ngit checkout -- .\ngit checkout -f %TARGET_HASH%\nif %errorlevel% equ 0 (\n    echo.\n    echo ✅ 已成功切换至版本 [%TARGET_HASH%]！\n) else (\n    echo.\n    echo ⚠️ 版本切换未成功，请检查输入的版本号是否正确。\n)\npause\ngoto MENU\n\n:DO_DEPS\necho.\necho [正在检索『系统资源\\requirements.txt』及所有插件子目录的依赖库...]\nif exist "%XIXI_ROOT%系统资源\\requirements.txt" (\n    echo   - 正在校验: 系统资源\\requirements.txt\n    python -m pip install -r "%XIXI_ROOT%系统资源\\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn\n)\nif exist "%XIXI_ROOT%requirements.txt" (\n    echo   - 正在校验: requirements.txt\n    python -m pip install -r "%XIXI_ROOT%requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn\n)\nfor /d %%D in ("%XIXI_ROOT%*") do (\n    if exist "%%D\\requirements.txt" (\n        echo   - 正在校验子目录依赖: %%~nxD\\requirements.txt\n        python -m pip install -r "%%D\\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn\n    )\n)\necho.\necho 🎉 所有依赖库校验与补齐完成！\npause\ngoto MENU\n\n:DO_REPAIR\necho.\nset "XIXI_SCRIPT=%XIXI_ROOT%xixi_toolkit_launcher.py"\nif not exist "%XIXI_SCRIPT%" set "XIXI_SCRIPT=%XIXI_ROOT%系统资源\\xixi_toolkit_launcher.py"\npython "%XIXI_SCRIPT%" --repair-scripts\necho.\npause\ngoto MENU\n'
GITIGNORE_TPL_V41 = '# ====================================================================\n# 🐾 西西工具包 V4.1 (.gitignore) - 保护用户私有数据与备份，仅版本化核心代码\n# ====================================================================\n\n# 1. 忽略 Python 编译缓存与打包临时文件\n__pycache__/\n*.py[cod]\n*$py.class\n*.spec\nbuild/\ndist/\n_xixi_launcher_stub.cs\n\n# 2. 忽略四大标准系统子目录中的『缓存/』与『bak/』(保留『工具/』与『系统资源/』入库)\n缓存/\nbak/\nbackup/\n_回收站备份/\n\n# 3. 忽略任意插件子文件夹（包含改名后的 1_西西盖章局/ 等）下的用户私有资源与导出文件\n**/自定义样式/\n**/自定义图片/\n**/历史缓存/\n**/默认导出/\n**/系统资源/save_dir_memory.json\n**/系统资源/save_dir_memory.js\n**/系统资源/reset_localstorage_token.js\n**/系统资源/prefs*.json\n\n# 4. 忽略操作系统临时文件与编辑器配置\n.DS_Store\nThumbs.db\nDesktop.ini\n.idea/\n.vscode/\n'


def _write_crlf_utf8_bom(target: Path, content: str):
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        crlf_bytes = b"\xef\xbb\xbf" + content.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
        if target.exists():
            try:
                if target.read_bytes() == crlf_bytes:
                    return False
            except Exception:
                pass
        target.write_bytes(crlf_bytes)
        return True
    except Exception:
        return False


def sync_and_repair_all_helper_scripts() -> list[str]:
    """
    自动将根目录下与『工具/』子文件夹内的所有 .bat 脚本及 .gitignore 升级为支持跨文件夹寻址的 V4.1 版本，
    并清理『工具/』下多余的旧版『直接启动.bat』，彻底解决脚本移入子文件夹后路径失效的问题。
    """
    updated = []
    # 1. 根目录保留最新的『直接启动.bat』与『.gitignore』
    if _write_crlf_utf8_bom(BASE_DIR / "直接启动.bat", BAT_TPL_DIRECT_START):
        updated.append("直接启动.bat (根目录)")
    try:
        gi_path = BASE_DIR / ".gitignore"
        gi_bytes = GITIGNORE_TPL_V41.replace("\r\n", "\n").encode("utf-8")
        if not gi_path.exists() or "V4.1" not in gi_path.read_text(encoding="utf-8", errors="ignore"):
            gi_path.write_bytes(gi_bytes)
            updated.append(".gitignore (根目录)")
    except Exception:
        pass

    # 2. 『工具/』子目录下自动同步四大辅助批处理脚本（支持在『工具/』内直接双击运行）
    tools_scripts = {
        "一键生成西西工具包EXE.bat": BAT_TPL_BUILD_EXE,
        "一键重置出厂默认_移入回收站.bat": BAT_TPL_FACTORY_RESET,
        "开发者一键上传更新.bat": BAT_TPL_DEV_PUSH,
        "一键更新与回退版本.bat": BAT_TPL_UPDATE_ROLLBACK,
    }
    for fname, tpl in tools_scripts.items():
        if _write_crlf_utf8_bom(TOOLS_DIR / fname, tpl):
            updated.append(f"工具/{fname}")

    # 3. 清理『工具/』下误放的旧版『直接启动.bat』或『点我启动.bat』，避免混淆
    for redundant in ("直接启动.bat", "点我启动.bat"):
        rp = TOOLS_DIR / redundant
        if rp.exists() and (BASE_DIR / "直接启动.bat").exists():
            try:
                rp.unlink()
                updated.append(f"已清理重复旧脚本: 工具/{redundant}")
            except Exception:
                pass

    return updated


def find_stamp_studio_dir() -> Path:
    """
    智能定位『西西盖章局』所在的真实子文件夹（兼容用户将其改名为『1_西西盖章局』等任意名称）。
    """
    exact = BASE_DIR / "西西盖章局"
    if exact.exists() and exact.is_dir():
        return exact
    try:
        for sub in sorted(BASE_DIR.iterdir()):
            if not sub.is_dir() or sub.name in SYSTEM_SUPPORT_FOLDERS or sub.name.startswith((".", "_")):
                continue
            if any((sub / fn).exists() for fn in ("stamp_studio_backend.py", "v5_pdf.html", "v5_1pdf.html", "水印盖章.html", "pdf_watermark_studio.html")):
                return sub
            marker = read_plugin_marker(sub)
            if marker and marker.get("id") == "stamp_studio":
                return sub
    except Exception:
        pass
    return exact


def ensure_standard_root_architecture(auto_migrate_files: bool = False) -> dict:
    """
    确保 `D:\\西西工具包\\` 下四大标准子文件夹存在：
    - `工具/`：放辅助 bat 脚本与计划文档
    - `bak/`：放手动备份与一键快照备份
    - `缓存/`：放启动器记忆 `launcher_memory.json`
    - `系统资源/`：放全局图标 `xixi_icon.ico`、`requirements.txt` 与启动器核心脚本备份
    同时自动为已存在的插件文件夹（如 `西西盖章局/`）补齐标准 `plugin.json` 标志文件。
    """
    moved_items = []
    for d in (TOOLS_DIR, BAK_DIR, CACHE_DIR, SYS_RES_DIR):
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    # 1. 自动迁移旧版「资源/」文件夹内的内容到「系统资源/」
    legacy_res_dir = BASE_DIR / "资源"
    if legacy_res_dir.exists() and legacy_res_dir.is_dir() and legacy_res_dir.resolve() != SYS_RES_DIR.resolve():
        try:
            for item in list(legacy_res_dir.iterdir()):
                dest = SYS_RES_DIR / item.name
                if not dest.exists():
                    shutil.move(str(item), str(dest))
                    moved_items.append(f"资源/{item.name} ➔ 系统资源/{item.name}")
            if not any(legacy_res_dir.iterdir()):
                legacy_res_dir.rmdir()
                moved_items.append("已合并清理空文件夹：资源/")
        except Exception:
            pass

    # 2. 自动将旧版用户主目录下的 ~/.xixi_toolkit_user_config.json 迁移至 缓存/launcher_memory.json
    if not USER_CONFIG_PATH.exists() and LEGACY_USER_CONFIG_PATH.exists():
        try:
            shutil.copy2(str(LEGACY_USER_CONFIG_PATH), str(USER_CONFIG_PATH))
            moved_items.append("已迁移启动器记忆至：缓存/launcher_memory.json")
        except Exception:
            pass

    # 3. 自动同步/修复『工具/』与根目录下的跨目录 .bat 脚本，并确保『西西盖章局』（含改名如 1_西西盖章局）的 plugin.json 存在
    repaired_scripts = sync_and_repair_all_helper_scripts()
    if auto_migrate_files and repaired_scripts:
        moved_items.extend([f"已升级跨目录脚本: {x}" for x in repaired_scripts])

    stamp_dir = find_stamp_studio_dir()
    if stamp_dir.exists() and stamp_dir.is_dir():
        marker_p = stamp_dir / PLUGIN_MARKER_FILENAME
        if not marker_p.exists():
            try:
                # 自动检测西西盖章局下的最佳 HTML 入口
                entry_name = "v5_pdf.html"
                for cand in ("v5_pdf.html", "v5_1pdf.html", "水印盖章.html", "pdf_watermark_studio.html"):
                    if (stamp_dir / cand).exists():
                        entry_name = cand
                        break
                marker_data = {
                    "id": "stamp_studio",
                    "name": "西西盖章局",
                    "subtitle": "PDF/Word 强力防删水印与印章工坊",
                    "icon": "🌸",
                    "color": "rose",
                    "category": "doc",
                    "entry": entry_name,
                    "enabled": True,
                }
                marker_p.write_text(json.dumps(marker_data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass

    tpl_dir = BASE_DIR / "_新插件标准模板_复制改名"
    if tpl_dir.exists() and tpl_dir.is_dir():
        tpl_marker = tpl_dir / PLUGIN_MARKER_FILENAME
        if not tpl_marker.exists():
            try:
                tpl_marker.write_text(
                    json.dumps(
                        {
                            "name": "我的新插件",
                            "subtitle": "复制此文件夹并改名即可被启动器自动识别",
                            "icon": "🧩",
                            "color": "emerald",
                            "category": "custom",
                            "entry": "index.html",
                            "enabled": True,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except Exception:
                pass

    # 4. 如果开启了 auto_migrate_files（或用户点击了「🧹 一键整理根目录」）：
    #    将根目录下散落的辅助 .bat、计划.txt 移入 `工具/`，将 xixi_icon.ico、requirements.txt 移入 `系统资源/`
    if auto_migrate_files:
        helper_files_to_tools = [
            "一键生成西西工具包EXE.bat",
            "一键重置出厂默认_移入回收站.bat",
            "开发者一键上传更新.bat",
            "一键更新与回退版本.bat",
            "点我启动.bat",
            "启动西西工具包.bat",
            "一键打包总控EXE.bat",
            "计划.txt",
        ]
        for fname in helper_files_to_tools:
            src = BASE_DIR / fname
            if src.exists() and src.is_file():
                dst = TOOLS_DIR / fname
                try:
                    if dst.exists():
                        dst.unlink()
                    shutil.move(str(src), str(dst))
                    moved_items.append(f"{fname} ➔ 工具/{fname}")
                except Exception:
                    pass

        res_files_to_sys = [
            "xixi_icon.ico",
            "requirements.txt",
        ]
        for fname in res_files_to_sys:
            src = BASE_DIR / fname
            if src.exists() and src.is_file():
                dst = SYS_RES_DIR / fname
                try:
                    shutil.copy2(str(src), str(dst))
                    src.unlink()
                    moved_items.append(f"{fname} ➔ 系统资源/{fname}")
                except Exception:
                    pass

        # 同步一份最新的 xixi_toolkit_launcher.py 到 系统资源/ 下备份
        this_py = Path(__file__).resolve()
        if this_py.exists() and this_py.name == "xixi_toolkit_launcher.py":
            sys_py = SYS_RES_DIR / "xixi_toolkit_launcher.py"
            try:
                if this_py.resolve() != sys_py.resolve():
                    shutil.copy2(str(this_py), str(sys_py))
            except Exception:
                pass

    return {
        "ok": True,
        "movedItems": moved_items,
        "msg": (
            f"🧹 整理完成！已自动归置 {len(moved_items)} 项文件到『工具/』与『系统资源/』。"
            if moved_items
            else "✅ 根目录非常干净整洁！四大系统子目录（工具 / bak / 缓存 / 系统资源）均已就绪。"
        ),
    }


def create_manual_snapshot_to_bak(note: str = "") -> dict:
    """一键将当前配置、插件代码与自定义样式/图片打包备份到 `bak/` 文件夹下"""
    try:
        BAK_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_note = re.sub(r'[\\/:*?"<>|]+', "_", (note or "").strip())
        zip_name = f"西西工具包备份_{stamp}{('_' + clean_note) if clean_note else ''}.zip"
        zip_path = BAK_DIR / zip_name

        skip_top_dirs = {"bak", "backup", ".git", "build", "dist", "__pycache__", "node_modules", "_回收站备份"}
        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root_dir, dirs, files in os.walk(BASE_DIR):
                rel_root = Path(root_dir).relative_to(BASE_DIR)
                if rel_root.parts and rel_root.parts[0] in skip_top_dirs:
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs if d not in skip_top_dirs and not d.startswith(".")]
                for fname in files:
                    if fname.endswith((".pyc", ".spec", ".cs")):
                        continue
                    fpath = Path(root_dir) / fname
                    try:
                        arcname = str(fpath.relative_to(BASE_DIR)).replace("\\", "/")
                        zf.write(fpath, arcname)
                        file_count += 1
                    except Exception:
                        pass

        size_kb = max(1, zip_path.stat().st_size // 1024)
        return {
            "ok": True,
            "zipName": zip_name,
            "zipPath": str(zip_path),
            "fileCount": file_count,
            "msg": f"📦 已成功备份 {file_count} 个文件至 bak/{zip_name} ({size_kb} KB)！",
        }
    except Exception as e:
        return {"ok": False, "msg": f"⚠️ 创建备份失败：{e}"}


# ==================== 依赖库 requirements.txt 自动检索与安装引擎 ====================

def parse_requirements_file(req_path: Path) -> list[dict]:
    """解析 requirements.txt，返回 [{'spec': 'pywebview>=4.0.0', 'pkg': 'pywebview'}, ...]"""
    if not req_path.exists() or not req_path.is_file():
        return []
    items = []
    try:
        for raw_line in req_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            m = re.match(r"^([A-Za-z0-9_.\-]+)", line)
            if m:
                pkg_name = m.group(1)
                items.append({"spec": line, "pkg": pkg_name, "source": str(req_path.parent.name or "系统资源")})
    except Exception:
        pass
    return items


def is_package_installed(pkg_name: str) -> bool:
    """检测指定包是否已安装在当前 Python 环境中"""
    norm = pkg_name.lower().replace("-", "_")
    import_alias = {
        "pywebview": "webview",
        "pillow": "PIL",
        "pymupdf": "fitz",
        "python_docx": "docx",
        "opencv_python": "cv2",
        "beautifulsoup4": "bs4",
    }
    try:
        importlib.metadata.distribution(pkg_name)
        return True
    except Exception:
        pass
    mod_name = import_alias.get(norm, norm)
    return importlib.util.find_spec(mod_name) is not None


def scan_all_requirements(target_dir: Path | None = None) -> dict:
    """检索 `系统资源/requirements.txt`、根目录 `requirements.txt` 及各插件子目录下的 `requirements.txt`"""
    req_files = []
    for cand_req in (SYS_RES_DIR / "requirements.txt", BASE_DIR / "requirements.txt"):
        if cand_req.exists() and cand_req not in req_files:
            req_files.append(cand_req)

    if target_dir and target_dir.exists():
        t_req = target_dir / "requirements.txt"
        if t_req.exists() and t_req not in req_files:
            req_files.append(t_req)
    else:
        try:
            for sub in sorted(BASE_DIR.iterdir()):
                if sub.is_dir() and sub.name not in IGNORED_DIRS and not sub.name.startswith((".", "_")):
                    s_req = sub / "requirements.txt"
                    if s_req.exists() and s_req not in req_files:
                        req_files.append(s_req)
        except Exception:
            pass

    seen = {}
    for rf in req_files:
        for item in parse_requirements_file(rf):
            key = item["pkg"].lower()
            if key not in seen:
                installed = is_package_installed(item["pkg"])
                seen[key] = {
                    "pkg": item["pkg"],
                    "spec": item["spec"],
                    "source": item["source"],
                    "installed": installed,
                }

    all_items = list(seen.values())
    missing = [x for x in all_items if not x["installed"]]
    return {
        "ok": True,
        "items": all_items,
        "missing": missing,
        "allInstalled": len(missing) == 0,
    }


def find_system_python(gui_mode: bool = False) -> str:
    if not getattr(sys, "frozen", False):
        if gui_mode and sys.executable.lower().endswith("python.exe"):
            pw = Path(sys.executable).with_name("pythonw.exe")
            if pw.exists():
                return str(pw)
        return sys.executable

    exe_names = ["pythonw.exe", "python.exe"] if gui_mode else ["python.exe", "py.exe"]
    for name in exe_names:
        found = shutil.which(name)
        if found:
            return found

    local_app = Path(os.environ.get("LOCALAPPDATA", ""))
    candidates = []
    if local_app.exists():
        candidates.extend(sorted(local_app.glob("Programs/Python/Python3*/python.exe"), reverse=True))
    for drive in ["C:/", "D:/"]:
        candidates.extend(sorted(Path(drive).glob("Python3*/python.exe"), reverse=True))
    for c in candidates:
        if c.exists():
            if gui_mode and c.with_name("pythonw.exe").exists():
                return str(c.with_name("pythonw.exe"))
            return str(c)
    return "python"


def install_missing_packages(specs: list[str]) -> dict:
    if not specs:
        return {"ok": True, "msg": "✅ 所有依赖库均已就绪，无需重复安装！"}
    py_bin = find_system_python(gui_mode=False)
    cmd = [
        py_bin,
        "-m",
        "pip",
        "install",
        *specs,
        "-i",
        TSINGHUA_MIRROR,
        "--trusted-host",
        "pypi.tuna.tsinghua.edu.cn",
    ]
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
        proc = subprocess.run(
            cmd,
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            creationflags=creation_flags,
        )
        if proc.returncode == 0:
            return {"ok": True, "msg": f"🎉 成功安装依赖库：{', '.join(specs)}", "log": proc.stdout[-600:]}
        return {"ok": False, "msg": f"⚠️ 安装遇到问题：{proc.stderr[-300:] or proc.stdout[-300:]}"}
    except Exception as e:
        return {"ok": False, "msg": f"⚠️ 调用 pip 安装失败：{e}"}


# ==================== Git 版本管理与热更新 / 安全回退引擎 ====================

def run_git_cmd(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
        proc = subprocess.run(
            ["git", *args],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=creation_flags,
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except FileNotFoundError:
        return -1, "", "当前电脑未安装 Git（或未加入环境变量 PATH）"
    except Exception as e:
        return -1, "", str(e)


def get_git_status_and_commits() -> dict:
    code, out, err = run_git_cmd(["rev-parse", "--is-inside-work-tree"])
    if code != 0:
        return {
            "ok": False,
            "hasGit": (code != -1 or "未安装 Git" not in err),
            "isRepo": False,
            "msg": err or "当前目录尚未初始化 Git 仓库",
            "commits": [],
        }

    _, branch, _ = run_git_cmd(["branch", "--show-current"])
    _, head_short, _ = run_git_cmd(["rev-parse", "--short", "HEAD"])
    _, remote_url, _ = run_git_cmd(["remote", "get-url", "origin"])
    _, status_porcelain, _ = run_git_cmd(["status", "--porcelain"])

    _, log_out, _ = run_git_cmd(
        ["log", "--all", "-n", "25", "--date=format:%Y-%m-%d %H:%M", "--pretty=format:%h|%ad|%s|%d"]
    )
    commits = []
    if log_out:
        for line in log_out.splitlines():
            parts = line.split("|", 3)
            if len(parts) >= 3:
                c_hash = parts[0].strip()
                c_date = parts[1].strip()
                c_msg = parts[2].strip()
                c_ref = parts[3].strip() if len(parts) > 3 else ""
                commits.append(
                    {
                        "hash": c_hash,
                        "date": c_date,
                        "message": c_msg,
                        "ref": c_ref,
                        "isCurrent": (c_hash == head_short),
                    }
                )

    return {
        "ok": True,
        "hasGit": True,
        "isRepo": True,
        "branch": branch or "分离头指针 (历史回退态)",
        "head": head_short,
        "remoteUrl": remote_url,
        "hasLocalChanges": bool(status_porcelain.strip()),
        "commits": commits,
    }


# ==================== 启动器记忆 `缓存/launcher_memory.json` 管理 ====================

def load_user_config() -> dict:
    """读取 `D:\\西西工具包\\缓存\\launcher_memory.json` 中的个性化配置"""
    default_cfg = {
        "categories": [dict(c) for c in DEFAULT_CATEGORIES],
        "pluginCategories": {},  # { plugin_id: category_id }
        "pluginPaths": {},       # { plugin_id: custom_rel_or_abs_path }
        "hiddenPlugins": [],     # [ plugin_id, ... ]
        "scanMode": "smart",     # "smart" (含 plugin.json 或含可运行文件) | "strict" (必须有 plugin.json 标志文件)
        "viewMode": "split",     # "split" | "tile"
    }
    target_cfg_path = USER_CONFIG_PATH if USER_CONFIG_PATH.exists() else (
        LEGACY_USER_CONFIG_PATH if LEGACY_USER_CONFIG_PATH.exists() else None
    )
    if target_cfg_path is None:
        return default_cfg
    try:
        data = json.loads(target_cfg_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return default_cfg
        cats = data.get("categories")
        if not isinstance(cats, list) or len(cats) == 0:
            cats = [dict(c) for c in DEFAULT_CATEGORIES]
        hidden_list = data.get("hiddenPlugins")
        if not isinstance(hidden_list, list):
            hidden_list = []
        scan_mode = data.get("scanMode", "smart")
        if scan_mode not in ("smart", "strict"):
            scan_mode = "smart"
        return {
            "categories": cats,
            "pluginCategories": data.get("pluginCategories") if isinstance(data.get("pluginCategories"), dict) else {},
            "pluginPaths": data.get("pluginPaths") if isinstance(data.get("pluginPaths"), dict) else {},
            "hiddenPlugins": [str(x) for x in hidden_list if x],
            "scanMode": scan_mode,
            "viewMode": data.get("viewMode", "split"),
        }
    except Exception:
        return default_cfg


def save_user_config(cfg: dict):
    """保存启动器记忆到 `D:\\西西工具包\\缓存\\launcher_memory.json`"""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        USER_CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def to_display_path(p: Path) -> str:
    try:
        return str(p.resolve().relative_to(BASE_DIR.resolve())).replace("\\", "/")
    except Exception:
        return str(p.resolve()).replace("\\", "/")


def resolve_path_str(path_str: str) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (BASE_DIR / path_str).resolve()


def read_plugin_marker(folder: Path) -> dict | None:
    """读取子文件夹内的 `plugin.json` 标志文件"""
    marker_file = folder / PLUGIN_MARKER_FILENAME
    if not marker_file.exists() or not marker_file.is_file():
        return None
    try:
        data = json.loads(marker_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return None


def write_plugin_marker(folder: Path, marker_data: dict) -> bool:
    """在子文件夹内写入或更新 `plugin.json` 标志文件"""
    try:
        folder.mkdir(parents=True, exist_ok=True)
        marker_file = folder / PLUGIN_MARKER_FILENAME
        marker_file.write_text(json.dumps(marker_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def score_runnable_candidate(file_path: Path, plugin_meta: dict | None = None) -> int:
    name_lower = file_path.name.lower()
    score = 0
    if name_lower in ("v5_pdf.html", "pdf_watermark_studio.html", "v5_1pdf.html", "水印盖章.html", "index.html", "main.py", "app.py", "app.html", "main.html"):
        score += 60
    if file_path.suffix.lower() == ".html":
        score += 25
    elif file_path.suffix.lower() in (".py", ".pyw"):
        score += 15
    elif file_path.suffix.lower() == ".exe":
        score += 10

    if plugin_meta:
        default_name = Path(plugin_meta.get("defaultRelPath", "")).name.lower()
        if default_name and name_lower == default_name:
            score += 100
        for kw in plugin_meta.get("keywords", []):
            if kw.lower() in name_lower or kw.lower() in file_path.parent.name.lower():
                score += 30
    return score


def sniff_plugin_by_fingerprint(plugin_meta: dict) -> Path | None:
    fingerprints = plugin_meta.get("fingerprints", [])
    keywords = plugin_meta.get("keywords", [])

    all_candidates = []
    try:
        for root_dir, dirs, files in os.walk(BASE_DIR):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith((".", "_"))]
            rel_depth = len(Path(root_dir).relative_to(BASE_DIR).parts)
            if rel_depth > 2:
                continue
            for fname in files:
                if fname in IGNORED_FILES or fname.startswith(".") or fname.endswith("_backend.py"):
                    continue
                fpath = Path(root_dir) / fname
                if fpath.suffix.lower() not in RUNNABLE_EXTS:
                    continue
                all_candidates.append(fpath)
    except Exception:
        pass

    if fingerprints:
        matched_fp = []
        for fpath in all_candidates:
            if fpath.suffix.lower() in (".html", ".htm", ".py", ".pyw"):
                try:
                    head_text = fpath.read_text(encoding="utf-8", errors="ignore")[:80000]
                    if any(fp in head_text for fp in fingerprints):
                        matched_fp.append(fpath)
                except Exception:
                    pass
        if matched_fp:
            matched_fp.sort(key=lambda p: (p.stat().st_mtime, score_runnable_candidate(p, plugin_meta)), reverse=True)
            return matched_fp[0]

    if keywords:
        matched = []
        for fpath in all_candidates:
            combined = f"{fpath.parent.name}/{fpath.name}".lower()
            if any(kw.lower() in combined for kw in keywords):
                matched.append(fpath)
        if matched:
            matched.sort(key=lambda p: score_runnable_candidate(p, plugin_meta), reverse=True)
            return matched[0]

    return None


def list_runnable_candidates_for_plugin(plugin_id: str, cfg: dict, folder_override: Path | None = None) -> list[dict]:
    builtin_map = {p["id"]: p for p in BUILTIN_PLUGINS}
    meta = builtin_map.get(plugin_id)

    search_dirs = []
    if folder_override and folder_override.exists() and folder_override.is_dir():
        search_dirs.append(folder_override)

    custom_p = cfg.get("pluginPaths", {}).get(plugin_id)
    if custom_p:
        cp = resolve_path_str(custom_p)
        if cp.parent.exists() and cp.parent != BASE_DIR and cp.parent not in search_dirs:
            search_dirs.append(cp.parent)

    if meta:
        def_dir = BASE_DIR / meta["defaultFolder"]
        if def_dir.exists() and def_dir.is_dir() and def_dir not in search_dirs:
            search_dirs.append(def_dir)
    elif plugin_id.startswith("custom_"):
        folder_name = plugin_id[len("custom_"):]
        c_dir = BASE_DIR / folder_name
        if c_dir.exists() and c_dir.is_dir() and c_dir not in search_dirs:
            search_dirs.append(c_dir)

    found_files = []
    seen_paths = set()
    for sdir in search_dirs:
        try:
            for item in sdir.iterdir():
                if item.is_file() and item.name not in IGNORED_FILES and not item.name.startswith(".") and not item.name.endswith("_backend.py"):
                    if item.suffix.lower() in RUNNABLE_EXTS:
                        rp = str(item.resolve())
                        if rp not in seen_paths:
                            seen_paths.add(rp)
                            found_files.append(item)
        except Exception:
            pass

    found_files.sort(key=lambda p: (score_runnable_candidate(p, meta), p.stat().st_mtime), reverse=True)

    result = []
    for f in found_files:
        disp = to_display_path(f)
        ext = f.suffix.lower()
        icon = "🌐" if ext in (".html", ".htm") else ("🐍" if ext in (".py", ".pyw") else "⚙️")
        result.append(
            {
                "name": f.name,
                "relPath": disp,
                "folder": f.parent.name,
                "icon": icon,
                "recommended": len(result) == 0,
            }
        )
    return result


def build_hub_state():
    """
    构建前端所需的完整状态（分类列表 + 插件列表 + 隐藏列表 + 扫描模式 + 四大系统文件夹状态）
    """
    ensure_standard_root_architecture(auto_migrate_files=False)
    cfg = load_user_config()
    categories = cfg.get("categories", [dict(c) for c in DEFAULT_CATEGORIES])
    valid_cat_ids = {c["id"] for c in categories}
    fallback_cat_id = categories[0]["id"] if categories else "doc"

    plugin_cats = cfg.get("pluginCategories", {})
    plugin_paths = cfg.get("pluginPaths", {})
    hidden_set = set(cfg.get("hiddenPlugins", []))
    scan_mode = cfg.get("scanMode", "smart")

    plugins_out = []
    claimed_dirs = set(IGNORED_DIRS)

    # 1. 扫描预设插件（仅当预设插件文件夹在硬盘上真实存在，或用户绑定了有效自定义路径时才加入，彻底告别不存在的幽灵待寻址卡片！）
    for item in BUILTIN_PLUGINS:
        pid = item["id"]
        def_folder = find_stamp_studio_dir() if pid == "stamp_studio" else (BASE_DIR / item["defaultFolder"])
        claimed_dirs.add(item["defaultFolder"])
        if def_folder.exists():
            claimed_dirs.add(def_folder.name)

        custom_path_str = plugin_paths.get(pid, "").strip()
        is_custom_path = False
        resolved_file = None

        if custom_path_str:
            cp = resolve_path_str(custom_path_str)
            if cp.exists() and cp.is_file():
                resolved_file = cp
                is_custom_path = True
                if cp.parent != BASE_DIR:
                    claimed_dirs.add(cp.parent.name)

        # 如果预设文件夹不存在且没有有效自定义路径：对于核心插件「西西盖章局」尝试特征码找回，其他未安装预设插件直接跳过不展示！
        if not def_folder.exists() and resolved_file is None:
            if pid == "stamp_studio":
                sniffed = sniff_plugin_by_fingerprint(item)
                if sniffed and sniffed.exists():
                    resolved_file = sniffed
                    if sniffed.parent != BASE_DIR:
                        claimed_dirs.add(sniffed.parent.name)
            if resolved_file is None and not def_folder.exists():
                continue

        target_folder = resolved_file.parent if (resolved_file and resolved_file.parent != BASE_DIR) else def_folder
        marker = read_plugin_marker(target_folder) if target_folder.exists() else None
        has_marker = marker is not None

        if scan_mode == "strict" and not has_marker:
            continue
        if marker and marker.get("enabled") is False:
            continue

        # 读取 plugin.json 里的入口或自动扫描最优 HTML
        if resolved_file is None and target_folder.exists() and target_folder.is_dir():
            if marker and marker.get("entry"):
                m_entry = target_folder / str(marker["entry"])
                if m_entry.exists() and m_entry.is_file():
                    resolved_file = m_entry

        if resolved_file is None and def_folder.exists() and def_folder.is_dir():
            html_in_folder = []
            try:
                html_in_folder = [
                    f for f in def_folder.iterdir()
                    if f.is_file() and f.suffix.lower() in (".html", ".htm") and not f.name.startswith(".")
                ]
            except Exception:
                pass
            if len(html_in_folder) > 1:
                def _html_priority(fp: Path):
                    ver_score = 0
                    try:
                        content = fp.read_text(encoding="utf-8", errors="ignore")
                        if "btnOpenHistoryDrawer" in content and "historyAndStorageModal" in content:
                            ver_score = 3
                        elif "ensure_system_resources" in content:
                            ver_score = 2
                        elif "firstTimeSaveDirModal" in content:
                            ver_score = 1
                    except Exception:
                        pass
                    return (ver_score, fp.stat().st_mtime)
                html_in_folder.sort(key=_html_priority, reverse=True)
                resolved_file = html_in_folder[0]
            elif len(html_in_folder) == 1:
                resolved_file = html_in_folder[0]
            else:
                p1 = BASE_DIR / item["defaultRelPath"]
                p2 = (BASE_DIR / item["fallbackRelPath"]) if item["fallbackRelPath"] else None
                if p1.exists() and p1.is_file():
                    resolved_file = p1
                elif p2 is not None and p2.exists() and p2.is_file():
                    resolved_file = p2
                else:
                    cands = list_runnable_candidates_for_plugin(pid, cfg, def_folder)
                    if cands:
                        cand_p = resolve_path_str(cands[0]["relPath"])
                        if cand_p.exists() and cand_p.is_file():
                            resolved_file = cand_p

        cat_id = plugin_cats.get(pid) or (marker.get("category") if marker else None) or item["defaultCategory"]
        if cat_id not in valid_cat_ids:
            cat_id = item["defaultCategory"] if item["defaultCategory"] in valid_cat_ids else fallback_cat_id

        actual_rel = to_display_path(resolved_file) if resolved_file else (custom_path_str or item["defaultRelPath"])
        folder_disp = target_folder.name if target_folder != BASE_DIR else item["defaultFolder"]

        plugins_out.append(
            {
                "id": pid,
                "name": (marker.get("name") if marker and marker.get("name") else item["name"]),
                "subtitle": (marker.get("subtitle") if marker and marker.get("subtitle") else item["subtitle"]),
                "category": cat_id,
                "defaultCategory": item["defaultCategory"],
                "icon": (marker.get("icon") if marker and marker.get("icon") else item["icon"]),
                "color": (marker.get("color") if marker and marker.get("color") else item["color"]),
                "defaultRelPath": item["defaultRelPath"],
                "actualRelPath": actual_rel,
                "folder": folder_disp,
                "ready": resolved_file is not None,
                "isCustomPath": is_custom_path,
                "isBuiltin": True,
                "hasMarker": has_marker,
                "hidden": (pid in hidden_set),
            }
        )

    # 2. 自动扫描根目录下未在预设列表中的其他子文件夹（排除四大系统目录与 _ / . 开头目录）
    try:
        for sub in sorted(BASE_DIR.iterdir()):
            if not sub.is_dir() or sub.name in claimed_dirs or sub.name.startswith((".", "_")):
                continue

            marker = read_plugin_marker(sub)
            has_marker = marker is not None
            if marker and marker.get("enabled") is False:
                continue

            pid = (marker.get("id") if marker and marker.get("id") else f"custom_{sub.name}")
            if any(p["id"] == pid for p in plugins_out):
                continue

            custom_path_str = plugin_paths.get(pid, "").strip()
            resolved_file = None
            is_custom_path = False
            if custom_path_str:
                cp = resolve_path_str(custom_path_str)
                if cp.exists() and cp.is_file():
                    resolved_file = cp
                    is_custom_path = True

            if resolved_file is None and marker and marker.get("entry"):
                m_entry = sub / str(marker["entry"])
                if m_entry.exists() and m_entry.is_file():
                    resolved_file = m_entry

            if resolved_file is None:
                cands = list_runnable_candidates_for_plugin(pid, cfg, sub)
                if cands:
                    resolved_file = resolve_path_str(cands[0]["relPath"])

            # 核心过滤规则：
            # - 若为 strict（严格标志模式）：没有 plugin.json 的文件夹一律不显示；
            # - 若为 smart（智能模式）：既没有 plugin.json 又没有任何可运行入口文件的普通杂物文件夹一律不显示！
            if scan_mode == "strict" and not has_marker:
                continue
            if scan_mode == "smart" and not has_marker and resolved_file is None:
                continue

            default_cat = (marker.get("category") if marker and marker.get("category") else "custom")
            cat_id = plugin_cats.get(pid, default_cat if default_cat in valid_cat_ids else fallback_cat_id)
            if cat_id not in valid_cat_ids:
                cat_id = fallback_cat_id

            actual_rel = to_display_path(resolved_file) if resolved_file else (custom_path_str or f"{sub.name}/index.html")
            plugins_out.append(
                {
                    "id": pid,
                    "name": (marker.get("name") if marker and marker.get("name") else sub.name),
                    "subtitle": (marker.get("subtitle") if marker and marker.get("subtitle") else f"扩展插件目录：{sub.name}/"),
                    "category": cat_id,
                    "defaultCategory": default_cat,
                    "icon": (marker.get("icon") if marker and marker.get("icon") else "🧩"),
                    "color": (marker.get("color") if marker and marker.get("color") else "emerald"),
                    "defaultRelPath": f"{sub.name}/index.html",
                    "actualRelPath": actual_rel,
                    "folder": sub.name,
                    "ready": resolved_file is not None,
                    "isCustomPath": is_custom_path,
                    "isBuiltin": False,
                    "hasMarker": has_marker,
                    "hidden": (pid in hidden_set),
                }
            )
    except Exception:
        pass

    # 检测根目录下是否还有未收纳的辅助文件（提示用户可一键整理）
    stray_root_helpers = []
    for fname in ("一键生成西西工具包EXE.bat", "一键重置出厂默认_移入回收站.bat", "开发者一键上传更新.bat", "一键更新与回退版本.bat", "点我启动.bat", "计划.txt", "xixi_icon.ico", "requirements.txt"):
        if (BASE_DIR / fname).exists():
            stray_root_helpers.append(fname)

    return {
        "categories": categories,
        "plugins": plugins_out,
        "viewMode": cfg.get("viewMode", "split"),
        "scanMode": scan_mode,
        "strayRootCount": len(stray_root_helpers),
        "strayRootFiles": stray_root_helpers,
        "rootDir": str(BASE_DIR),
    }


LAUNCHER_HUB_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>🐾 西西工具包</title>
  <script src="https://cdn.tailwindcss.com/3.4.17" async onerror="this.remove()"></script>
  <style>
    * { box-sizing: border-box; user-select: none; }
    input, textarea, select { user-select: text; }
    body {
      margin: 0;
      padding: 0;
      font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
      background-color: #FFFDF9;
      background-image:
        radial-gradient(#FBCFE8 1.2px, transparent 1.2px),
        radial-gradient(#FDE68A 1.2px, #FFFDF9 1.2px);
      background-size: 28px 28px;
      background-position: 0 0, 14px 14px;
      color: #4A353B;
      height: 100vh;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .cat-btn {
      transition: all 0.14s ease;
      border: 1.5px solid transparent;
    }
    .cat-btn.active {
      background: linear-gradient(135deg, #F43F5E 0%, #FB7185 100%);
      color: #FFFFFF;
      box-shadow: 0 3px 0 #E11D48;
      border-color: #E11D48;
    }
    .cat-btn.hidden-box-active {
      background: linear-gradient(135deg, #64748B 0%, #475569 100%);
      color: #FFFFFF;
      box-shadow: 0 3px 0 #334155;
      border-color: #334155;
    }
    .cat-btn.drag-over {
      background: #FFF1F2 !important;
      color: #BE123C !important;
      border: 2px dashed #F43F5E !important;
      transform: scale(1.02);
      box-shadow: 0 4px 12px rgba(244, 63, 94, 0.2);
    }
    .tool-item {
      background: rgba(255, 255, 255, 0.96);
      border: 2px solid #FBCFE8;
      box-shadow: 0 4px 0 #F9CBD6;
      transition: all 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    .tool-item:hover {
      transform: translateY(-2px);
      border-color: #FB7185;
      box-shadow: 0 6px 0 #FDA4AF, 0 8px 16px rgba(244, 63, 94, 0.12);
    }
    .tool-item:active {
      transform: translateY(1px);
      box-shadow: 0 2px 0 #FDA4AF;
    }
    .tool-item.dragging {
      opacity: 0.45;
      transform: scale(0.96);
      border-style: dashed;
    }
    .modal-backdrop {
      background: rgba(74, 53, 59, 0.42);
      backdrop-filter: blur(4px);
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-thumb { background: #F9A8D4; border-radius: 99px; }

    /* Built-in offline Tailwind utility fallback so UI is 100% styled even without internet */
    .hidden { display: none !important; }
    .flex { display: flex; }
    .grid { display: grid; }
    .block { display: block; }
    .flex-col { flex-direction: column; }
    .flex-1 { flex: 1 1 0%; }
    .shrink-0 { flex-shrink: 0; }
    .min-w-0 { min-width: 0px; }
    .w-full { width: 100%; }
    .w-52 { width: 13rem; }
    .w-12 { width: 3rem; }
    .h-12 { height: 3rem; }
    .w-10 { width: 2.5rem; }
    .h-10 { height: 2.5rem; }
    .w-8 { width: 2rem; }
    .h-8 { height: 2rem; }
    .w-7 { width: 1.75rem; }
    .h-7 { height: 1.75rem; }
    .w-6 { width: 1.5rem; }
    .h-6 { height: 1.5rem; }
    .h-52 { height: 13rem; }
    .max-w-lg { max-width: 32rem; }
    .max-w-xl { max-width: 36rem; }
    .max-w-md { max-width: 28rem; }
    .items-center { align-items: center; }
    .justify-between { justify-content: space-between; }
    .justify-center { justify-content: center; }
    .justify-end { justify-content: flex-end; }
    .gap-1 { gap: 0.25rem; }
    .gap-1\.5 { gap: 0.375rem; }
    .gap-2 { gap: 0.5rem; }
    .gap-2\.5 { gap: 0.625rem; }
    .gap-3 { gap: 0.75rem; }
    .gap-3\.5 { gap: 0.875rem; }
    .space-y-1 > * + * { margin-top: 0.25rem; }
    .space-y-1\.5 > * + * { margin-top: 0.375rem; }
    .space-y-2 > * + * { margin-top: 0.5rem; }
    .space-y-2\.5 > * + * { margin-top: 0.625rem; }
    .space-y-3 > * + * { margin-top: 0.75rem; }
    .space-y-3\.5 > * + * { margin-top: 0.875rem; }
    .space-y-4 > * + * { margin-top: 1rem; }
    .grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
    .grid-cols-2, .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .grid-cols-4, .sm\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
    .col-span-3 { grid-column: span 3 / span 3; }
    .p-0\.5 { padding: 0.125rem; }
    .p-1 { padding: 0.25rem; }
    .p-2 { padding: 0.5rem; }
    .p-2\.5 { padding: 0.625rem; }
    .p-3 { padding: 0.75rem; }
    .p-3\.5 { padding: 0.875rem; }
    .p-4 { padding: 1rem; }
    .p-5 { padding: 1.25rem; }
    .px-1\.5 { padding-left: 0.375rem; padding-right: 0.375rem; }
    .px-2 { padding-left: 0.5rem; padding-right: 0.5rem; }
    .px-2\.5 { padding-left: 0.625rem; padding-right: 0.625rem; }
    .px-3 { padding-left: 0.75rem; padding-right: 0.75rem; }
    .px-3\.5 { padding-left: 0.875rem; padding-right: 0.875rem; }
    .px-4 { padding-left: 1rem; padding-right: 1rem; }
    .py-0\.5 { padding-top: 0.125rem; padding-bottom: 0.125rem; }
    .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
    .py-1\.5 { padding-top: 0.375rem; padding-bottom: 0.375rem; }
    .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
    .py-2\.5 { padding-top: 0.625rem; padding-bottom: 0.625rem; }
    .pt-1 { padding-top: 0.25rem; }
    .pt-2 { padding-top: 0.5rem; }
    .pb-2\.5 { padding-bottom: 0.625rem; }
    .pr-0\.5 { padding-right: 0.125rem; }
    .pr-1 { padding-right: 0.25rem; }
    .mb-0\.5 { margin-bottom: 0.125rem; }
    .mb-1 { margin-bottom: 0.25rem; }
    .mb-1\.5 { margin-bottom: 0.375rem; }
    .mb-2 { margin-bottom: 0.5rem; }
    .mb-3 { margin-bottom: 0.75rem; }
    .mt-0\.5 { margin-top: 0.125rem; }
    .mt-1 { margin-top: 0.25rem; }
    .mt-2 { margin-top: 0.5rem; }
    .rounded { border-radius: 0.25rem; }
    .rounded-md { border-radius: 0.375rem; }
    .rounded-lg { border-radius: 0.5rem; }
    .rounded-xl { border-radius: 0.75rem; }
    .rounded-2xl { border-radius: 1rem; }
    .rounded-3xl { border-radius: 1.5rem; }
    .rounded-full { border-radius: 9999px; }
    .border { border-width: 1px; border-style: solid; }
    .border-2 { border-width: 2px; border-style: solid; }
    .border-b { border-bottom-width: 1px; border-bottom-style: solid; }
    .border-b-2 { border-bottom-width: 2px; border-bottom-style: solid; }
    .border-r-2 { border-right-width: 2px; border-right-style: solid; }
    .border-t { border-top-width: 1px; border-top-style: solid; }
    .border-dashed { border-style: dashed; }
    .border-rose-100 { border-color: #FFE4E6; }
    .border-rose-200, .border-rose-200\/80, .border-rose-200\/70 { border-color: #FECDD3; }
    .border-rose-300 { border-color: #FDA4AF; }
    .border-rose-400 { border-color: #FB7185; }
    .border-emerald-200 { border-color: #A7F3D0; }
    .border-emerald-300 { border-color: #6EE7B7; }
    .border-amber-200 { border-color: #FDE68A; }
    .border-amber-300 { border-color: #FCD34D; }
    .border-amber-500 { border-color: #F59E0B; }
    .border-indigo-200 { border-color: #C7D2FE; }
    .border-purple-200 { border-color: #E9D5FF; }
    .border-red-200 { border-color: #FECACA; }
    .border-red-300 { border-color: #FCA5A5; }
    .border-slate-200 { border-color: #E2E8F0; }
    .bg-white, .bg-white\/95, .bg-white\/90, .bg-white\/85, .bg-white\/70 { background-color: #FFFFFF; }
    .bg-rose-50, .bg-rose-50\/70, .bg-rose-50\/60, .bg-rose-50\/50 { background-color: #FFF1F2; }
    .bg-rose-100 { background-color: #FFE4E6; }
    .bg-rose-500 { background-color: #F43F5E; }
    .bg-emerald-50 { background-color: #ECFDF5; }
    .bg-emerald-100 { background-color: #D1FAE5; }
    .bg-emerald-500 { background-color: #10B981; }
    .bg-amber-50 { background-color: #FFFBEB; }
    .bg-amber-100 { background-color: #FEF3C7; }
    .bg-amber-400 { background-color: #FBBF24; }
    .bg-indigo-50 { background-color: #EEF2FF; }
    .bg-indigo-100 { background-color: #E0E7FF; }
    .bg-purple-50 { background-color: #FAF5FF; }
    .bg-red-50 { background-color: #FEF2F2; }
    .bg-slate-50, .bg-slate-100, .bg-slate-100\/80 { background-color: #F1F5F9; }
    .bg-slate-200 { background-color: #E2E8F0; }
    .bg-gradient-to-r.from-indigo-500.to-purple-500 { background: linear-gradient(90deg, #6366F1, #A855F7); }
    .text-white { color: #FFFFFF; }
    .text-rose-950 { color: #4C0519; }
    .text-rose-900 { color: #881337; }
    .text-rose-800 { color: #9F1239; }
    .text-rose-700 { color: #BE123C; }
    .text-rose-600, .text-rose-600\/90 { color: #E11D48; }
    .text-rose-500 { color: #F43F5E; }
    .text-rose-400 { color: #FB7185; }
    .text-emerald-800 { color: #065F46; }
    .text-emerald-700 { color: #047857; }
    .text-amber-950 { color: #451A03; }
    .text-amber-900 { color: #78350F; }
    .text-amber-800 { color: #92400E; }
    .text-amber-700 { color: #B45309; }
    .text-indigo-900 { color: #312E81; }
    .text-indigo-800 { color: #3730A3; }
    .text-indigo-700 { color: #4338CA; }
    .text-purple-900 { color: #581C87; }
    .text-red-700 { color: #B91C1C; }
    .text-slate-700 { color: #334155; }
    .text-slate-600 { color: #475569; }
    .text-\[9px\] { font-size: 9px; }
    .text-\[10px\] { font-size: 10px; }
    .text-\[11px\] { font-size: 11px; }
    .text-xs { font-size: 12px; }
    .text-sm { font-size: 14px; }
    .text-xl { font-size: 20px; }
    .text-2xl { font-size: 24px; }
    .text-3xl { font-size: 30px; }
    .font-medium { font-weight: 500; }
    .font-bold { font-weight: 700; }
    .font-extrabold { font-weight: 800; }
    .font-black { font-weight: 900; }
    .font-mono { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; }
    .whitespace-nowrap { white-space: nowrap; }
    .truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .text-center { text-align: center; }
    .text-left { text-align: left; }
    .overflow-hidden { overflow: hidden; }
    .overflow-y-auto { overflow-y: auto; }
    .overflow-x-auto { overflow-x: auto; }
    .relative { position: relative; }
    .absolute { position: absolute; }
    .fixed { position: fixed; }
    .inset-0 { top: 0; right: 0; bottom: 0; left: 0; }
    .top-2 { top: 0.5rem; }
    .right-2 { right: 0.5rem; }
    .bottom-3 { bottom: 0.75rem; }
    .right-3 { right: 0.75rem; }
    .z-50 { z-index: 50; }
    .cursor-pointer { cursor: pointer; }
    .opacity-0 { opacity: 0; }
    .group:hover .group-hover\\:opacity-100 { opacity: 1 !important; }
    .object-cover { object-fit: cover; }
    h1, h2, h3, p { margin: 0; }
    button { border: none; background: none; font-family: inherit; }

  </style>
</head>
<body>
  <!-- 顶部导航栏（全部按钮强制 whitespace-nowrap shrink-0，彻底杜绝文字折行） -->
  <header class="px-4 py-2.5 bg-white/95 border-b-2 border-rose-200 flex items-center justify-between gap-3 shrink-0">
    <div class="flex items-center gap-2.5 min-w-0">
      <img src="data:image/png;base64,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" alt="西西" class="w-10 h-10 rounded-xl border-2 border-rose-400 shadow-sm object-cover shrink-0" />
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <h1 class="text-sm font-black text-rose-950 whitespace-nowrap">西西工具包 V4.0</h1>
          <span class="px-2 py-0.5 rounded-full bg-rose-50 text-rose-600 border border-rose-200 text-[10px] font-extrabold whitespace-nowrap shrink-0">
            🏷️ 标志识别 · 🙈 隐藏收纳盒
          </span>
        </div>
        <p class="text-[11px] text-rose-500 font-medium truncate mt-0.5">
          卡片可拖入左侧分类或「🙈 隐藏收纳盒」· 记忆存于 <span class="font-mono text-rose-600">缓存/</span>
        </p>
      </div>
    </div>

    <!-- 右侧操作按钮组（严禁折行） -->
    <div class="flex items-center gap-1.5 shrink-0">
      <div class="flex items-center bg-rose-50 p-0.5 rounded-xl border border-rose-200 shrink-0">
        <button id="btnViewSplit" onclick="setViewMode('split')" class="px-2.5 py-1 rounded-lg text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer bg-rose-500 text-white shadow-2xs">
          📑 分类视图
        </button>
        <button id="btnViewTile" onclick="setViewMode('tile')" class="px-2.5 py-1 rounded-lg text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer text-rose-700 hover:bg-rose-100/60">
          🎛️ 全部平铺
        </button>
      </div>
      <button onclick="openNewPluginModal()" title="一键在根目录下新建带 plugin.json 标志文件的标准插件子夹" class="px-2.5 py-1.5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer">
        ➕ 新建插件
      </button>
      <button onclick="openUpdateCenterModal()" title="Git 版本更新、历史回退、开发者上传与依赖库检测" class="px-2.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-500 hover:from-indigo-600 hover:to-purple-600 text-white text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer shadow-xs">
        ☁️ 更新与回退
      </button>
      <button onclick="resetAllToDefault()" title="恢复默认分类、清空隐藏列表与路径绑定" class="px-2.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer">
        🔄 默认布局
      </button>
      <button onclick="triggerFactoryResetFromGui()" title="经过2次确认后，清空所有自定义样式/图片/缓存移入回收站" class="px-2.5 py-1.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer">
        🧹 出厂重置
      </button>
    </div>
  </header>

  <!-- 二级系统子目录快捷栏（工具 / bak / 缓存 / 系统资源 + 扫描模式切换 + 一键整理根目录） -->
  <div class="px-4 py-1.5 bg-rose-50/70 border-b border-rose-200/80 flex items-center justify-between gap-2 shrink-0 text-[11px]">
    <div class="flex items-center gap-1.5 overflow-hidden">
      <span class="font-extrabold text-rose-800 whitespace-nowrap">📁 系统目录直达：</span>
      <button onclick="openSystemSubfolder('root')" title="打开 D:\西西工具包 根目录" class="px-2 py-0.5 rounded-lg bg-white hover:bg-rose-100 text-rose-800 border border-rose-200 font-bold whitespace-nowrap shrink-0 cursor-pointer transition">
        🏠 根目录
      </button>
      <button onclick="openSystemSubfolder('tools')" title="打开 工具/ 文件夹（存放辅助 bat 脚本与计划）" class="px-2 py-0.5 rounded-lg bg-white hover:bg-amber-100 text-amber-900 border border-amber-200 font-bold whitespace-nowrap shrink-0 cursor-pointer transition">
        🛠️ 工具/
      </button>
      <button onclick="openSystemSubfolder('bak')" title="打开 bak/ 文件夹（存放手动备份与快照）" class="px-2 py-0.5 rounded-lg bg-white hover:bg-indigo-100 text-indigo-900 border border-indigo-200 font-bold whitespace-nowrap shrink-0 cursor-pointer transition">
        📦 bak/
      </button>
      <button onclick="openSystemSubfolder('cache')" title="打开 缓存/ 文件夹（存放启动器记忆 launcher_memory.json）" class="px-2 py-0.5 rounded-lg bg-white hover:bg-emerald-100 text-emerald-900 border border-emerald-200 font-bold whitespace-nowrap shrink-0 cursor-pointer transition">
        💾 缓存/
      </button>
      <button onclick="openSystemSubfolder('sys_res')" title="打开 系统资源/ 文件夹（存放全局图标 xixi_icon.ico 与公用资源）" class="px-2 py-0.5 rounded-lg bg-white hover:bg-purple-100 text-purple-900 border border-purple-200 font-bold whitespace-nowrap shrink-0 cursor-pointer transition">
        🎨 系统资源/
      </button>
    </div>

    <div class="flex items-center gap-1.5 shrink-0">
      <button id="btnScanModeToggle" onclick="toggleScanMode()" title="切换子文件夹扫描策略：智能模式（含 plugin.json 或可运行入口） / 严格标志模式（仅显示含 plugin.json 的文件夹）" class="px-2 py-0.5 rounded-lg bg-white hover:bg-rose-100 text-rose-700 border border-rose-200 font-extrabold whitespace-nowrap shrink-0 cursor-pointer transition">
        🏷️ 扫描：智能识别
      </button>
      <button onclick="createQuickBackup()" title="一键将当前工具包配置与插件打包备份到 bak/ 文件夹" class="px-2 py-0.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 font-extrabold whitespace-nowrap shrink-0 cursor-pointer transition">
        📦 备份到 bak
      </button>
      <button id="btnOrganizeRoot" onclick="organizeRootNow()" title="一键把根目录下散落的辅助 .bat 移入 工具/，把图标与 requirements.txt 移入 系统资源/" class="px-2 py-0.5 rounded-lg bg-amber-100 hover:bg-amber-200 text-amber-900 border border-amber-300 font-extrabold whitespace-nowrap shrink-0 cursor-pointer transition">
        🧹 一键整理根目录
      </button>
    </div>
  </div>

  <!-- 主体区：左侧分类与隐藏收纳盒 + 右侧工具卡片 -->
  <div class="flex-1 flex overflow-hidden">
    <!-- 左侧分类栏 -->
    <aside id="categorySidebar" class="w-52 bg-white/85 border-r-2 border-rose-100 p-3 flex flex-col justify-between shrink-0">
      <div class="space-y-1 overflow-y-auto pr-0.5">
        <div class="px-2 py-1 flex items-center justify-between">
          <span class="text-[10px] font-black text-rose-400 uppercase tracking-wider whitespace-nowrap">工具分类 (可拖入)</span>
          <button onclick="toggleAddCategoryBox()" title="新增自定义分类" class="px-1.5 py-0.5 rounded-md bg-rose-100 hover:bg-rose-200 text-rose-700 text-[10px] font-black transition whitespace-nowrap cursor-pointer">
            + 新增
          </button>
        </div>

        <!-- 内联新增分类输入框 -->
        <div id="addCategoryBox" class="hidden p-2 rounded-xl bg-rose-50/90 border border-rose-200 space-y-1.5 mb-1.5">
          <div class="flex items-center gap-1">
            <select id="newCatIconSelect" class="px-1 py-1 rounded-lg bg-white border border-rose-200 text-xs outline-none">
              <option value="📁">📁</option>
              <option value="🌸">🌸</option>
              <option value="✨">✨</option>
              <option value="🎨">🎨</option>
              <option value="📄">📄</option>
              <option value="⚡">⚡</option>
              <option value="🛠️">🛠️</option>
              <option value="💎">💎</option>
            </select>
            <input id="newCatNameInput" type="text" placeholder="分类名称..." class="w-full min-w-0 px-2 py-1 rounded-lg bg-white border border-rose-200 text-xs font-bold text-rose-950 outline-none focus:border-rose-400" />
          </div>
          <div class="flex items-center justify-end gap-1">
            <button type="button" onclick="toggleAddCategoryBox(false)" class="px-2 py-0.5 rounded-md bg-white text-rose-500 text-[10px] font-bold border border-rose-200 cursor-pointer">取消</button>
            <button type="button" onclick="confirmAddCategory()" class="px-2 py-0.5 rounded-md bg-rose-500 text-white text-[10px] font-extrabold cursor-pointer">添加</button>
          </div>
        </div>

        <div id="categoryList" class="space-y-1"></div>
      </div>

      <!-- 底部固定：🙈 隐藏收纳盒 + 操作提示 -->
      <div class="pt-2 border-t border-dashed border-rose-200 space-y-2">
        <div id="hiddenCategoryContainer"></div>
        <div class="p-2 rounded-xl bg-rose-50/70 border border-rose-200/70 text-[10px] text-rose-500 leading-relaxed">
          💡 <b>隐藏技巧</b>：将卡片拖入上方「🙈 隐藏收纳盒」或点卡片右上角「🙈」，即可从平铺和常规分类中隐藏！
        </div>
      </div>
    </aside>

    <!-- 右侧插件卡片展示区 -->
    <main class="flex-1 p-4 overflow-y-auto flex flex-col justify-between">
      <div>
        <!-- 当前分类标题栏 -->
        <div id="currentCategoryBanner" class="mb-3 px-3 py-2 rounded-xl bg-white/90 border border-rose-200 flex items-center justify-between">
          <div class="flex items-center gap-2 min-w-0">
            <span id="bannerCategoryTitle" class="text-xs font-black text-rose-950 whitespace-nowrap">🌟 全部工具</span>
            <span id="bannerCategorySub" class="text-[11px] text-rose-500 truncate">已自动过滤系统文件夹与隐藏插件</span>
          </div>
          <span id="bannerPluginCount" class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 text-[10px] font-extrabold whitespace-nowrap shrink-0">0 个插件</span>
        </div>

        <div id="toolsContainer"></div>
      </div>
    </main>
  </div>

  <!-- 弹窗 1：插件启动路径与标志文件 (`plugin.json`) 设置弹窗 -->
  <div id="pathModal" class="fixed inset-0 z-50 hidden items-center justify-center modal-backdrop p-4">
    <div class="bg-white rounded-3xl border-2 border-rose-300 shadow-xl w-full max-w-lg p-5 space-y-3.5 max-h-[90vh] flex flex-col">
      <div class="flex items-center justify-between border-b border-rose-100 pb-2.5 shrink-0">
        <div class="flex items-center gap-2 min-w-0">
          <span id="modalPluginIcon" class="text-xl">🌸</span>
          <div class="min-w-0">
            <h2 id="modalPluginTitle" class="text-sm font-black text-rose-950 truncate">插件设置与启动路径</h2>
            <p id="modalPluginCurrentPath" class="text-[10px] text-rose-500 font-mono truncate">当前指向：-</p>
          </div>
        </div>
        <button onclick="closePathModal()" class="w-7 h-7 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-600 font-black text-xs cursor-pointer shrink-0">✕</button>
      </div>

      <div class="overflow-y-auto space-y-3 pr-1 flex-1">
        <!-- 标志文件 plugin.json 快捷编辑区 -->
        <div class="p-3 rounded-2xl bg-rose-50/60 border border-rose-200 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-black text-rose-900">🏷️ 插件卡片展示信息 (同步写入子夹 <code class="font-mono text-rose-600">plugin.json</code> 标志文件)</span>
            <span id="modalMarkerBadge" class="px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-800">已含标志文件</span>
          </div>
          <div class="grid grid-cols-4 gap-2">
            <div>
              <label class="text-[10px] font-bold text-rose-600 block mb-0.5">图标</label>
              <input id="editPluginIcon" type="text" class="w-full px-2 py-1 rounded-lg bg-white border border-rose-200 text-xs font-bold text-center outline-none focus:border-rose-400" value="🌸" />
            </div>
            <div class="col-span-3">
              <label class="text-[10px] font-bold text-rose-600 block mb-0.5">显示名称</label>
              <input id="editPluginName" type="text" class="w-full px-2.5 py-1 rounded-lg bg-white border border-rose-200 text-xs font-bold text-rose-950 outline-none focus:border-rose-400" />
            </div>
          </div>
          <div>
            <label class="text-[10px] font-bold text-rose-600 block mb-0.5">副标题简介</label>
            <input id="editPluginSubtitle" type="text" class="w-full px-2.5 py-1 rounded-lg bg-white border border-rose-200 text-xs text-rose-950 outline-none focus:border-rose-400" />
          </div>
          <div class="flex items-center justify-between pt-1">
            <button type="button" id="btnModalToggleHide" onclick="handleModalToggleHidden()" class="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-extrabold cursor-pointer transition">
              🙈 移入隐藏收纳盒
            </button>
            <button type="button" onclick="handleSavePluginMarker()" class="px-3 py-1 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-[11px] font-extrabold cursor-pointer transition shadow-2xs">
              💾 保存信息并写入 plugin.json
            </button>
          </div>
        </div>

        <!-- 三种路径修复方式 -->
        <div class="space-y-2">
          <div class="text-xs font-black text-rose-900">🎯 启动文件寻址与绑定：</div>
          <button onclick="handleResetAndSniffPlugin()" class="w-full p-2.5 rounded-2xl border-2 border-rose-200 hover:border-rose-400 bg-rose-50/50 hover:bg-rose-50 text-left flex items-center gap-3 transition cursor-pointer">
            <div class="w-8 h-8 rounded-xl bg-rose-500 text-white flex items-center justify-center text-sm shrink-0 font-bold">a</div>
            <div class="min-w-0 flex-1">
              <div class="text-xs font-black text-rose-950">🔄 重置为默认路径（含防改名特征码嗅探）</div>
              <div class="text-[10px] text-rose-500">恢复默认文件名；若文件夹或文件曾被改名，自动扫描特征码找回</div>
            </div>
          </button>

          <button onclick="handleManualPickPluginFile()" class="w-full p-2.5 rounded-2xl border-2 border-amber-200 hover:border-amber-400 bg-amber-50/50 hover:bg-amber-50 text-left flex items-center gap-3 transition cursor-pointer">
            <div class="w-8 h-8 rounded-xl bg-amber-500 text-white flex items-center justify-center text-sm shrink-0 font-bold">b</div>
            <div class="min-w-0 flex-1">
              <div class="text-xs font-black text-amber-950">📂 自己手动指定启动文件</div>
              <div class="text-[10px] text-amber-700">弹出系统文件选择框，亲手选定任意 .html / .py / .exe 作为启动文件</div>
            </div>
          </button>

          <button onclick="handleAutoScanCandidates()" class="w-full p-2.5 rounded-2xl border-2 border-emerald-200 hover:border-emerald-400 bg-emerald-50/50 hover:bg-emerald-50 text-left flex items-center gap-3 transition cursor-pointer">
            <div class="w-8 h-8 rounded-xl bg-emerald-500 text-white flex items-center justify-center text-sm shrink-0 font-bold">c</div>
            <div class="min-w-0 flex-1">
              <div class="text-xs font-black text-emerald-950">🔍 自动扫描子夹内可运行文件并智能推荐</div>
              <div class="text-[10px] text-emerald-700">若子夹下只有1个可运行文件则自动锁定；若有多个则列出供点选</div>
            </div>
          </button>
        </div>

        <!-- 扫描出的候选可运行文件列表 -->
        <div id="candidatesWrap" class="hidden pt-1 border-t border-rose-100 space-y-1.5">
          <div id="candidatesTitle" class="text-[11px] font-black text-rose-800">📋 扫描到的可运行文件：</div>
          <div id="candidatesList" class="max-h-36 overflow-y-auto space-y-1.5 pr-1"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- 弹窗 2：➕ 新建插件向导弹窗 -->
  <div id="newPluginModal" class="fixed inset-0 z-50 hidden items-center justify-center modal-backdrop p-4">
    <div class="bg-white rounded-3xl border-2 border-emerald-300 shadow-xl w-full max-w-md p-5 space-y-3.5">
      <div class="flex items-center justify-between border-b border-emerald-100 pb-2.5">
        <div class="flex items-center gap-2">
          <span class="text-xl">➕</span>
          <div>
            <h2 class="text-sm font-black text-rose-950">一键新建标准插件子文件夹</h2>
            <p class="text-[10px] text-rose-500">自动创建子文件夹、<code class="font-mono">plugin.json</code> 标志文件与带返回按钮的脚手架</p>
          </div>
        </div>
        <button onclick="closeNewPluginModal()" class="w-7 h-7 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-600 font-black text-xs cursor-pointer">✕</button>
      </div>

      <div class="space-y-2.5 text-xs">
        <div class="grid grid-cols-4 gap-2">
          <div>
            <label class="text-[11px] font-extrabold text-rose-800 block mb-1">图标</label>
            <input id="npIconInput" type="text" value="✨" class="w-full px-2 py-1.5 rounded-xl bg-rose-50/50 border border-rose-200 text-center font-bold outline-none focus:border-emerald-400" />
          </div>
          <div class="col-span-3">
            <label class="text-[11px] font-extrabold text-rose-800 block mb-1">插件名称（同时作为子文件夹名）</label>
            <input id="npNameInput" type="text" placeholder="例如：图片格式转换器" class="w-full px-3 py-1.5 rounded-xl bg-rose-50/50 border border-rose-200 font-bold text-rose-950 outline-none focus:border-emerald-400" />
          </div>
        </div>
        <div>
          <label class="text-[11px] font-extrabold text-rose-800 block mb-1">副标题简介</label>
          <input id="npSubtitleInput" type="text" placeholder="一句话描述这个小工具的功能..." class="w-full px-3 py-1.5 rounded-xl bg-rose-50/50 border border-rose-200 text-rose-950 outline-none focus:border-emerald-400" />
        </div>
        <div>
          <label class="text-[11px] font-extrabold text-rose-800 block mb-1">所属分类</label>
          <select id="npCategorySelect" class="w-full px-3 py-1.5 rounded-xl bg-rose-50/50 border border-rose-200 font-bold text-rose-950 outline-none"></select>
        </div>
      </div>

      <div class="flex items-center justify-end gap-2 pt-2">
        <button onclick="closeNewPluginModal()" class="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-extrabold cursor-pointer">取消</button>
        <button onclick="confirmCreateNewPlugin()" class="px-4 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-black shadow-sm cursor-pointer transition">✨ 立即创建并打开文件夹</button>
      </div>
    </div>
  </div>

  <!-- 弹窗 3：☁️ Git 热更新 / 历史版本回退 / 开发者一键上传 / 依赖库自检中心 -->
  <div id="updateCenterModal" class="fixed inset-0 z-50 hidden items-center justify-center modal-backdrop p-4">
    <div class="bg-white rounded-3xl border-2 border-rose-300 shadow-2xl w-full max-w-xl p-5 space-y-3.5 max-h-[88vh] flex flex-col">
      <div class="flex items-center justify-between border-b border-rose-100 pb-2.5 shrink-0">
        <div class="flex items-center gap-2">
          <span class="text-xl">☁️</span>
          <div>
            <h2 class="text-sm font-black text-rose-950">版本热更新 · 历史版本回退 · 依赖环境中心</h2>
            <p class="text-[10px] text-rose-500">更新或回退代码时，您的自定义样式、自定义图片、缓存与 bak 备份 100% 安全保留</p>
          </div>
        </div>
        <button onclick="closeUpdateCenterModal()" class="w-7 h-7 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-600 font-black text-xs cursor-pointer">✕</button>
      </div>

      <div class="grid grid-cols-3 gap-1.5 bg-rose-50 p-1 rounded-2xl border border-rose-200 shrink-0">
        <button id="tabBtnUserUpdate" onclick="switchUpdateTab('user')" class="py-1.5 px-2 rounded-xl text-xs font-extrabold bg-rose-500 text-white shadow-2xs cursor-pointer">
          ⬇️ 更新与历史回退
        </button>
        <button id="tabBtnDevPush" onclick="switchUpdateTab('dev')" class="py-1.5 px-2 rounded-xl text-xs font-extrabold text-rose-800 hover:bg-rose-100 cursor-pointer">
          🚀 开发者一键上传
        </button>
        <button id="tabBtnDeps" onclick="switchUpdateTab('deps')" class="py-1.5 px-2 rounded-xl text-xs font-extrabold text-rose-800 hover:bg-rose-100 cursor-pointer">
          📦 所需库自动安装
        </button>
      </div>

      <div id="panelUserUpdate" class="flex-1 overflow-y-auto space-y-3 pr-1">
        <div class="p-3 rounded-2xl bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 flex items-center justify-between gap-3">
          <div>
            <div id="gitCurrentVerLabel" class="text-xs font-black text-indigo-950">正在读取 Git 仓库状态...</div>
            <div id="gitRemoteUrlLabel" class="text-[10px] text-indigo-600 font-mono truncate max-w-xs"></div>
          </div>
          <button onclick="triggerGitPullLatest()" class="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-black shadow-xs shrink-0 cursor-pointer">
            ⬇️ 一键同步最新版
          </button>
        </div>
        <div class="space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-black text-rose-900">⏪ 历史版本时光机（遇到 Bug 可随时回退到任意旧版）：</span>
            <button onclick="refreshUpdateCenterData()" class="text-[10px] font-extrabold text-rose-500 hover:text-rose-700 cursor-pointer">🔄 刷新列表</button>
          </div>
          <div id="gitCommitsList" class="space-y-1.5 max-h-56 overflow-y-auto pr-1"></div>
        </div>
      </div>

      <div id="panelDevPush" class="hidden flex-1 overflow-y-auto space-y-3 pr-1">
        <div class="p-3 rounded-2xl bg-rose-50/70 border border-rose-200 space-y-2.5">
          <div class="text-xs font-black text-rose-950">👩‍💻 开发者快速发布新版本 (git add + commit + push)</div>
          <p class="text-[11px] text-rose-600 leading-relaxed">
            当你修改了插件或新增了小工具后，在下方填写一句更新说明并点击推送，即可一键上传至远程仓库（自动忽略个人缓存与 bak 备份）。
          </p>
          <input id="devCommitMsgInput" type="text" placeholder="例如：✨ 优化根目录结构并新增隐藏收纳盒" class="w-full px-3 py-2 rounded-xl bg-white border border-rose-200 text-xs font-bold text-rose-950 outline-none focus:border-rose-400" />
          <button onclick="triggerDeveloperPush()" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-rose-500 to-pink-500 hover:from-rose-600 hover:to-pink-600 text-white text-xs font-black shadow-sm cursor-pointer">
            🚀 立即打包提交并推送到远程仓库 (Git Push)
          </button>
        </div>
        <div id="devPushLogBox" class="hidden p-2.5 rounded-xl bg-slate-900 text-emerald-300 font-mono text-[10px] whitespace-pre-wrap max-h-40 overflow-y-auto"></div>
      </div>

      <div id="panelDeps" class="hidden flex-1 overflow-y-auto space-y-3 pr-1">
        <div class="p-3 rounded-2xl bg-emerald-50/80 border border-emerald-200 flex items-center justify-between gap-3">
          <div>
            <div id="depsSummaryTitle" class="text-xs font-black text-emerald-950">正在扫描系统资源与各插件的 requirements.txt...</div>
            <div class="text-[10px] text-emerald-700">自动合并检索 <code class="font-mono">系统资源/requirements.txt</code> 与各子插件所需库</div>
          </div>
          <button onclick="triggerInstallAllDeps()" class="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-xs shrink-0 cursor-pointer">
            ⚡ 一键补齐全部库
          </button>
        </div>
        <div id="depsItemsList" class="space-y-1.5 max-h-56 overflow-y-auto pr-1"></div>
      </div>
    </div>
  </div>

  <!-- 弹窗 4：出厂重置 2次确认弹窗 -->
  <div id="factoryResetModal" class="hidden fixed inset-0 z-50 modal-backdrop flex items-center justify-center p-4">
    <div class="bg-white border-2 border-red-300 rounded-2xl shadow-2xl w-full max-w-md p-5 space-y-4">
      <div class="flex items-center justify-between border-b border-red-100 pb-2.5">
        <h3 id="factoryResetModalTitle" class="text-sm font-black text-red-700">⚠️ 第 1 / 2 次确认 · 恢复出厂初始默认</h3>
        <button onclick="closeFactoryResetModal()" class="w-6 h-6 rounded-lg bg-red-50 hover:bg-red-100 text-red-600 font-bold text-xs cursor-pointer">✕</button>
      </div>
      <div id="factoryResetModalBody" class="text-xs text-rose-950 leading-relaxed space-y-2 bg-red-50/60 p-3.5 rounded-xl border border-red-200"></div>
      <div class="flex items-center justify-end gap-2 pt-1">
        <button onclick="closeFactoryResetModal()" class="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-extrabold cursor-pointer">取消</button>
        <button id="btnFactoryResetNext" onclick="advanceFactoryResetStep()" class="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-600 text-white text-xs font-black shadow-sm cursor-pointer transition">继续第 2 次确认 ➔</button>
      </div>
    </div>
  </div>

  <!-- 轻提示 Toast -->
  <div id="hubToast" class="fixed bottom-3 right-3 z-50 hidden px-3.5 py-2 rounded-2xl bg-rose-500 text-white text-xs font-extrabold shadow-lg"></div>

  <script>
    const HIDDEN_CAT_ID = '__hidden__';
    let categories = [];
    let allPlugins = [];
    let currentCategory = 'all';
    let viewMode = 'split';
    let scanMode = 'smart';
    let strayRootCount = 0;
    let draggingPluginId = null;
    let activeModalPluginId = null;
    let toastTimer = null;

    function showHubToast(msg) {
      const el = document.getElementById('hubToast');
      el.textContent = msg;
      el.classList.remove('hidden');
      if (toastTimer) clearTimeout(toastTimer);
      toastTimer = setTimeout(() => el.classList.add('hidden'), 2800);
    }

    function applyHubState(stateObj) {
      if (!stateObj) return;
      categories = stateObj.categories || [];
      allPlugins = stateObj.plugins || [];
      if (stateObj.viewMode) viewMode = stateObj.viewMode;
      if (stateObj.scanMode) scanMode = stateObj.scanMode;
      strayRootCount = stateObj.strayRootCount || 0;

      if (currentCategory !== 'all' && currentCategory !== HIDDEN_CAT_ID && !categories.some(c => c.id === currentCategory)) {
        currentCategory = 'all';
      }
      syncViewModeUI();
      syncTopStatusButtons();
      renderCategories();
      renderTools();
    }

    function syncTopStatusButtons() {
      const scanBtn = document.getElementById('btnScanModeToggle');
      if (scanBtn) {
        if (scanMode === 'strict') {
          scanBtn.textContent = '🔒 扫描：仅标志文件 (plugin.json)';
          scanBtn.className = 'px-2 py-0.5 rounded-lg bg-rose-500 text-white border border-rose-600 font-extrabold whitespace-nowrap shrink-0 cursor-pointer transition';
        } else {
          scanBtn.textContent = '🏷️ 扫描：智能识别';
          scanBtn.className = 'px-2 py-0.5 rounded-lg bg-white hover:bg-rose-100 text-rose-700 border border-rose-200 font-extrabold whitespace-nowrap shrink-0 cursor-pointer transition';
        }
      }
      const orgBtn = document.getElementById('btnOrganizeRoot');
      if (orgBtn) {
        if (strayRootCount > 0) {
          orgBtn.textContent = `🧹 一键整理根目录 (${strayRootCount})`;
          orgBtn.className = 'px-2 py-0.5 rounded-lg bg-amber-400 hover:bg-amber-500 text-amber-950 border border-amber-500 font-black whitespace-nowrap shrink-0 cursor-pointer transition animate-pulse';
        } else {
          orgBtn.textContent = '🧹 根目录已整洁';
          orgBtn.className = 'px-2 py-0.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-200 font-extrabold whitespace-nowrap shrink-0 cursor-pointer transition';
        }
      }
    }

    function syncViewModeUI() {
      const sidebar = document.getElementById('categorySidebar');
      const btnSplit = document.getElementById('btnViewSplit');
      const btnTile = document.getElementById('btnViewTile');
      if (viewMode === 'tile') {
        sidebar.classList.add('hidden');
        btnTile.className = 'px-2.5 py-1 rounded-lg text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer bg-rose-500 text-white shadow-2xs';
        btnSplit.className = 'px-2.5 py-1 rounded-lg text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer text-rose-700 hover:bg-rose-100/60';
      } else {
        sidebar.classList.remove('hidden');
        btnSplit.className = 'px-2.5 py-1 rounded-lg text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer bg-rose-500 text-white shadow-2xs';
        btnTile.className = 'px-2.5 py-1 rounded-lg text-xs font-extrabold transition whitespace-nowrap shrink-0 cursor-pointer text-rose-700 hover:bg-rose-100/60';
      }
    }

    async function setViewMode(mode) {
      viewMode = mode;
      if (mode === 'tile' && currentCategory === HIDDEN_CAT_ID) {
        currentCategory = 'all';
      }
      syncViewModeUI();
      renderCategories();
      renderTools();
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.set_view_mode(mode);
      }
    }

    async function toggleScanMode() {
      const nextMode = scanMode === 'smart' ? 'strict' : 'smart';
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.set_scan_mode(nextMode);
        if (res && res.state) {
          applyHubState(res.state);
          showHubToast(res.msg || '已切换扫描模式');
        }
      } else {
        scanMode = nextMode;
        syncTopStatusButtons();
      }
    }

    async function organizeRootNow() {
      if (!window.pywebview || !window.pywebview.api) return;
      const res = await window.pywebview.api.organize_root_directory();
      if (res) {
        if (res.state) applyHubState(res.state);
        showHubToast(res.msg || '🧹 根目录整理完成！');
      }
    }

    async function createQuickBackup() {
      if (!window.pywebview || !window.pywebview.api) return;
      showHubToast('⏳ 正在打包当前配置与插件快照到 bak/ 文件夹...');
      const res = await window.pywebview.api.create_snapshot_backup('');
      if (res) {
        showHubToast(res.msg || '📦 备份完成！');
      }
    }

    async function openSystemSubfolder(targetKey) {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.open_system_subfolder(targetKey);
      }
    }

    function renderCategories() {
      const wrap = document.getElementById('categoryList');
      const hiddenWrap = document.getElementById('hiddenCategoryContainer');
      wrap.innerHTML = '';
      hiddenWrap.innerHTML = '';

      const visiblePlugins = allPlugins.filter(p => !p.hidden);
      const hiddenPlugins = allPlugins.filter(p => p.hidden);

      const allItems = [{ id: 'all', name: '🌟 全部工具', fixed: true }, ...categories];

      allItems.forEach(cat => {
        const count = cat.id === 'all'
          ? visiblePlugins.length
          : visiblePlugins.filter(p => p.category === cat.id).length;

        const row = document.createElement('div');
        row.className = `cat-btn group w-full px-2.5 py-2 rounded-xl text-left text-xs font-extrabold flex items-center justify-between cursor-pointer ${
          currentCategory === cat.id ? 'active' : 'text-rose-900 hover:bg-rose-100/60'
        }`;
        row.dataset.catId = cat.id;

        row.innerHTML = `
          <span class="truncate pr-1">${cat.name}</span>
          <div class="flex items-center gap-1 shrink-0">
            <span class="text-[10px] px-1.5 py-0.2 rounded-full ${
              currentCategory === cat.id ? 'bg-white/25 text-white' : 'bg-rose-100 text-rose-600'
            }">${count}</span>
            ${!cat.fixed ? `<button type="button" data-del-cat="${cat.id}" title="删除该分类" class="opacity-0 group-hover:opacity-100 px-1 rounded hover:bg-black/15 text-[11px] font-black transition">×</button>` : ''}
          </div>
        `;

        row.addEventListener('click', e => {
          const delBtn = e.target.closest('[data-del-cat]');
          if (delBtn) {
            e.stopPropagation();
            deleteCategory(delBtn.dataset.delCat);
            return;
          }
          currentCategory = cat.id;
          renderCategories();
          renderTools();
        });

        row.addEventListener('dragover', e => {
          e.preventDefault();
          row.classList.add('drag-over');
        });
        row.addEventListener('dragleave', () => {
          row.classList.remove('drag-over');
        });
        row.addEventListener('drop', async e => {
          e.preventDefault();
          row.classList.remove('drag-over');
          const pid = draggingPluginId || e.dataTransfer.getData('text/plain');
          if (!pid) return;
          if (cat.id === 'all') {
            await setPluginHidden(pid, false);
          } else {
            await movePluginToCategory(pid, cat.id, cat.name);
          }
        });

        wrap.appendChild(row);
      });

      // 渲染底部固定的「🙈 隐藏收纳盒」
      const hiddenRow = document.createElement('div');
      const isHiddenActive = currentCategory === HIDDEN_CAT_ID;
      hiddenRow.className = `cat-btn w-full px-2.5 py-2 rounded-xl text-left text-xs font-extrabold flex items-center justify-between cursor-pointer ${
        isHiddenActive ? 'hidden-box-active' : 'bg-slate-100/80 text-slate-700 hover:bg-slate-200/80 border border-slate-200'
      }`;
      hiddenRow.innerHTML = `
        <span class="truncate pr-1">🙈 隐藏收纳盒</span>
        <span class="text-[10px] px-1.5 py-0.2 rounded-full ${
          isHiddenActive ? 'bg-white/25 text-white' : 'bg-slate-200 text-slate-700'
        }">${hiddenPlugins.length}</span>
      `;
      hiddenRow.addEventListener('click', () => {
        currentCategory = HIDDEN_CAT_ID;
        renderCategories();
        renderTools();
      });
      hiddenRow.addEventListener('dragover', e => {
        e.preventDefault();
        hiddenRow.classList.add('drag-over');
      });
      hiddenRow.addEventListener('dragleave', () => {
        hiddenRow.classList.remove('drag-over');
      });
      hiddenRow.addEventListener('drop', async e => {
        e.preventDefault();
        hiddenRow.classList.remove('drag-over');
        const pid = draggingPluginId || e.dataTransfer.getData('text/plain');
        if (!pid) return;
        await setPluginHidden(pid, true);
      });
      hiddenWrap.appendChild(hiddenRow);
    }

    function toggleAddCategoryBox(forceState) {
      const box = document.getElementById('addCategoryBox');
      const input = document.getElementById('newCatNameInput');
      const show = typeof forceState === 'boolean' ? forceState : box.classList.contains('hidden');
      box.classList.toggle('hidden', !show);
      if (show) {
        input.value = '';
        input.focus();
      }
    }

    async function confirmAddCategory() {
      const icon = document.getElementById('newCatIconSelect').value || '📁';
      const rawName = (document.getElementById('newCatNameInput').value || '').trim();
      if (!rawName) {
        showHubToast('⚠️ 请输入新分类的名称哟！');
        return;
      }
      const fullName = `${icon} ${rawName}`;
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.add_category(fullName);
        if (res && res.state) {
          applyHubState(res.state);
          toggleAddCategoryBox(false);
          showHubToast(`✨ 已新增分类「${fullName}」`);
        }
      }
    }

    async function deleteCategory(catId) {
      if (categories.length <= 1) {
        showHubToast('⚠️ 至少需要保留 1 个工具分类哟！');
        return;
      }
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.delete_category(catId);
        if (res && res.state) {
          applyHubState(res.state);
          showHubToast('🗑️ 已删除该分类，原插件已自动归入默认分类');
        }
      }
    }

    async function movePluginToCategory(pluginId, targetCatId, targetCatName) {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.move_plugin_category(pluginId, targetCatId);
        if (res && res.state) {
          const pObj = allPlugins.find(p => p.id === pluginId);
          applyHubState(res.state);
          showHubToast(`✨ 已将「${pObj ? pObj.name : pluginId}」移入「${targetCatName}」！`);
        }
      }
    }

    async function setPluginHidden(pluginId, hideFlag) {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.toggle_plugin_hidden(pluginId, hideFlag);
        if (res && res.state) {
          applyHubState(res.state);
          showHubToast(res.msg || (hideFlag ? '🙈 已移入隐藏收纳盒' : '👁️ 已恢复显示'));
        }
      }
    }

    function renderTools() {
      const container = document.getElementById('toolsContainer');
      const bannerTitle = document.getElementById('bannerCategoryTitle');
      const bannerSub = document.getElementById('bannerCategorySub');
      const bannerCount = document.getElementById('bannerPluginCount');

      let filtered = [];
      if (viewMode === 'tile') {
        // 全部平铺模式下严格排除隐藏收纳盒中的插件！
        filtered = allPlugins.filter(p => !p.hidden);
        bannerTitle.textContent = '🎛️ 全部平铺视图';
        bannerSub.textContent = '展示所有未隐藏的可用插件（隐藏插件已自动过滤）';
      } else if (currentCategory === HIDDEN_CAT_ID) {
        filtered = allPlugins.filter(p => p.hidden);
        bannerTitle.textContent = '🙈 隐藏收纳盒';
        bannerSub.textContent = '以下插件不会在「全部工具」或「全部平铺」中显示，点「👁️」可随时恢复';
      } else if (currentCategory === 'all') {
        filtered = allPlugins.filter(p => !p.hidden);
        bannerTitle.textContent = '🌟 全部工具';
        bannerSub.textContent = scanMode === 'strict'
          ? '严格标志模式：仅展示含 plugin.json 标志文件的插件子夹'
          : '智能识别模式：自动识别含 plugin.json 或含可运行入口的插件子夹';
      } else {
        const catObj = categories.find(c => c.id === currentCategory);
        filtered = allPlugins.filter(p => !p.hidden && p.category === currentCategory);
        bannerTitle.textContent = catObj ? catObj.name : '工具分类';
        bannerSub.textContent = '可将卡片拖拽至左侧其他分类或底部「🙈 隐藏收纳盒」';
      }

      bannerCount.textContent = `${filtered.length} 个插件`;

      if (filtered.length === 0) {
        container.className = '';
        container.innerHTML = `
          <div class="h-52 rounded-2xl bg-white/70 border-2 border-dashed border-rose-200 flex flex-col items-center justify-center text-center text-rose-400 text-xs p-4">
            <div class="text-3xl mb-1.5">${currentCategory === HIDDEN_CAT_ID ? '🙈' : '📭'}</div>
            <div class="font-bold text-rose-700">${
              currentCategory === HIDDEN_CAT_ID
                ? '隐藏收纳盒目前是空的哟！'
                : '该分类下暂无插件'
            }</div>
            <div class="text-[11px] text-rose-400 mt-1">${
              currentCategory === HIDDEN_CAT_ID
                ? '你可以把暂时不想看到的插件卡片拖到这里，或点击卡片上的「🙈」按钮隐藏它'
                : '可从「🌟 全部工具」把卡片拖进来，或点击右上角「➕ 新建插件」创建新工具'
            }</div>
          </div>
        `;
        return;
      }

      const badgeColors = {
        rose: 'bg-rose-100 text-rose-700 border-rose-200',
        amber: 'bg-amber-100 text-amber-800 border-amber-200',
        indigo: 'bg-indigo-100 text-indigo-800 border-indigo-200',
        emerald: 'bg-emerald-100 text-emerald-800 border-emerald-200'
      };

      const getCatLabel = catId => {
        const found = categories.find(c => c.id === catId);
        return found ? found.name : '未分类';
      };

      if (viewMode === 'tile') {
        container.className = 'grid grid-cols-3 sm:grid-cols-4 gap-3';
        container.innerHTML = filtered.map(item => `
          <div
            draggable="true"
            data-plugin-id="${item.id}"
            onclick="handleCardClick('${item.id}')"
            class="tool-item relative p-3.5 rounded-2xl cursor-pointer flex flex-col items-center text-center justify-between group"
          >
            <div class="absolute top-2 right-2 flex items-center gap-1">
              <button
                type="button"
                onclick="event.stopPropagation(); setPluginHidden('${item.id}', ${!item.hidden})"
                title="${item.hidden ? '移出隐藏收纳盒' : '隐藏此插件（不显示在平铺和常规列表中）'}"
                class="w-6 h-6 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs flex items-center justify-center transition opacity-0 group-hover:opacity-100"
              >${item.hidden ? '👁️' : '🙈'}</button>
              <button
                type="button"
                onclick="event.stopPropagation(); openPathModal('${item.id}')"
                title="插件设置与标志文件管理"
                class="w-6 h-6 rounded-lg bg-rose-50 hover:bg-rose-200 text-rose-600 text-xs flex items-center justify-center transition"
              >⚙️</button>
            </div>
            <div class="w-12 h-12 rounded-2xl ${badgeColors[item.color] || badgeColors.rose} border flex items-center justify-center text-2xl mb-2 shadow-2xs">
              ${item.icon}
            </div>
            <div class="w-full">
              <div class="text-xs font-black text-rose-950 truncate">${item.name}</div>
              <div class="text-[10px] text-rose-500 truncate mt-0.5">${getCatLabel(item.category)}</div>
            </div>
            <span class="mt-2 px-2.5 py-0.5 rounded-full text-[10px] font-extrabold whitespace-nowrap ${
              item.ready ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
            }">
              ${item.ready ? '● 点击打开' : '🔧 配置路径'}
            </span>
          </div>
        `).join('');
      } else {
        container.className = 'grid grid-cols-1 sm:grid-cols-2 gap-3';
        container.innerHTML = filtered.map(item => `
          <div
            draggable="true"
            data-plugin-id="${item.id}"
            onclick="handleCardClick('${item.id}')"
            class="tool-item p-3.5 rounded-2xl cursor-pointer flex items-center gap-3.5 relative group"
            title="点击直接打开插件；按住可拖拽到左侧分类或底部「🙈 隐藏收纳盒」"
          >
            <div class="w-12 h-12 rounded-2xl ${badgeColors[item.color] || badgeColors.rose} border flex items-center justify-center text-2xl shrink-0 shadow-2xs">
              ${item.icon}
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center justify-between gap-1.5">
                <div class="flex items-center gap-1.5 min-w-0">
                  <span class="text-xs font-black text-rose-950 truncate">${item.name}</span>
                  ${item.hasMarker ? '<span title="该子文件夹包含标准 plugin.json 标志文件" class="px-1.5 py-0.2 rounded bg-rose-50 text-rose-600 border border-rose-200 text-[9px] font-extrabold whitespace-nowrap shrink-0">🏷️ 标志</span>' : ''}
                </div>
                <div class="flex items-center gap-1 shrink-0">
                  <span class="px-1.5 py-0.5 rounded-md text-[10px] font-extrabold whitespace-nowrap ${
                    item.ready ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                  }">${item.ready ? '已就绪' : '待寻址'}</span>
                  <button
                    type="button"
                    onclick="event.stopPropagation(); setPluginHidden('${item.id}', ${!item.hidden})"
                    title="${item.hidden ? '移出隐藏收纳盒（恢复显示）' : '移入左侧「🙈 隐藏收纳盒」'}"
                    class="w-6 h-6 rounded-lg ${item.hidden ? 'bg-indigo-100 text-indigo-700 border-indigo-200' : 'bg-slate-50 hover:bg-slate-200 text-slate-600 border-slate-200'} border text-xs flex items-center justify-center transition"
                  >${item.hidden ? '👁️' : '🙈'}</button>
                  <button
                    type="button"
                    onclick="event.stopPropagation(); openPathModal('${item.id}')"
                    title="插件名称/标志文件与启动路径设置"
                    class="w-6 h-6 rounded-lg bg-rose-50 hover:bg-rose-200 text-rose-700 border border-rose-200 text-xs flex items-center justify-center transition"
                  >⚙️</button>
                </div>
              </div>
              <div class="text-[11px] text-rose-600/90 truncate mt-1">${item.subtitle}</div>
              <div class="text-[10px] text-rose-400 font-mono truncate mt-0.5 flex items-center gap-1.5">
                <span>🎯 ${item.actualRelPath}</span>
              </div>
            </div>
          </div>
        `).join('');
      }

      container.querySelectorAll('[draggable="true"]').forEach(card => {
        card.addEventListener('dragstart', e => {
          draggingPluginId = card.dataset.pluginId;
          e.dataTransfer.setData('text/plain', draggingPluginId);
          card.classList.add('dragging');
          document.getElementById('categorySidebar').classList.remove('hidden');
        });
        card.addEventListener('dragend', () => {
          card.classList.remove('dragging');
          draggingPluginId = null;
          document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('drag-over'));
          syncViewModeUI();
        });
      });
    }

    async function handleCardClick(pluginId) {
      const item = allPlugins.find(p => p.id === pluginId);
      if (!item) return;
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.open_plugin_by_id(pluginId);
        if (res && !res.ok) {
          openPathModal(pluginId);
          if (res.msg) showHubToast(res.msg);
        }
      }
    }

    function openPathModal(pluginId) {
      activeModalPluginId = pluginId;
      const item = allPlugins.find(p => p.id === pluginId);
      if (!item) return;
      document.getElementById('modalPluginIcon').textContent = item.icon || '🌸';
      document.getElementById('modalPluginTitle').textContent = `「${item.name}」插件设置与标志文件`;
      document.getElementById('modalPluginCurrentPath').textContent = `当前指向：${item.actualRelPath} (${item.ready ? '✅文件存在' : '⚠️未找到该文件'})`;
      document.getElementById('editPluginIcon').value = item.icon || '🧩';
      document.getElementById('editPluginName').value = item.name || '';
      document.getElementById('editPluginSubtitle').value = item.subtitle || '';

      const markerBadge = document.getElementById('modalMarkerBadge');
      if (item.hasMarker) {
        markerBadge.textContent = '✅ 已含 plugin.json 标志文件';
        markerBadge.className = 'px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-100 text-emerald-800';
      } else {
        markerBadge.textContent = '⚪ 尚未生成 plugin.json (点下方保存即自动生成)';
        markerBadge.className = 'px-2 py-0.5 rounded-full text-[10px] font-extrabold bg-amber-100 text-amber-800';
      }

      const hideBtn = document.getElementById('btnModalToggleHide');
      if (item.hidden) {
        hideBtn.textContent = '👁️ 从隐藏收纳盒移出（恢复显示）';
      } else {
        hideBtn.textContent = '🙈 移入隐藏收纳盒';
      }

      document.getElementById('candidatesWrap').classList.add('hidden');
      const modal = document.getElementById('pathModal');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closePathModal() {
      const modal = document.getElementById('pathModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
      activeModalPluginId = null;
    }

    async function handleModalToggleHidden() {
      if (!activeModalPluginId) return;
      const item = allPlugins.find(p => p.id === activeModalPluginId);
      if (!item) return;
      await setPluginHidden(activeModalPluginId, !item.hidden);
      closePathModal();
    }

    async function handleSavePluginMarker() {
      if (!activeModalPluginId || !window.pywebview || !window.pywebview.api) return;
      const icon = (document.getElementById('editPluginIcon').value || '🧩').trim();
      const name = (document.getElementById('editPluginName').value || '').trim();
      const subtitle = (document.getElementById('editPluginSubtitle').value || '').trim();
      if (!name) {
        showHubToast('⚠️ 插件显示名称不能为空哟！');
        return;
      }
      const res = await window.pywebview.api.save_plugin_marker_info(activeModalPluginId, name, subtitle, icon);
      if (res && res.state) {
        applyHubState(res.state);
        showHubToast(res.msg || '✅ 已写入 plugin.json 标志文件！');
        closePathModal();
      }
    }

    // ==================== ➕ 新建插件向导 ====================
    function openNewPluginModal() {
      const sel = document.getElementById('npCategorySelect');
      sel.innerHTML = categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
      document.getElementById('npNameInput').value = '';
      document.getElementById('npSubtitleInput').value = '';
      const modal = document.getElementById('newPluginModal');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closeNewPluginModal() {
      const modal = document.getElementById('newPluginModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    async function confirmCreateNewPlugin() {
      const icon = (document.getElementById('npIconInput').value || '✨').trim();
      const name = (document.getElementById('npNameInput').value || '').trim();
      const subtitle = (document.getElementById('npSubtitleInput').value || '').trim();
      const catId = document.getElementById('npCategorySelect').value || 'custom';
      if (!name) {
        showHubToast('⚠️ 请先填写新插件的名称哟！');
        return;
      }
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.create_new_plugin_scaffold(name, subtitle, icon, catId);
        if (res) {
          if (res.state) applyHubState(res.state);
          showHubToast(res.msg || '✨ 新插件已创建！');
          if (res.ok) closeNewPluginModal();
        }
      }
    }

    async function handleResetAndSniffPlugin() {
      if (!activeModalPluginId || !window.pywebview) return;
      const res = await window.pywebview.api.reset_and_sniff_plugin(activeModalPluginId);
      if (res && res.state) {
        applyHubState(res.state);
        const updated = allPlugins.find(p => p.id === activeModalPluginId);
        if (updated) {
          document.getElementById('modalPluginCurrentPath').textContent = `当前指向：${updated.actualRelPath} (${updated.ready ? '✅已就绪' : '⚠️未找到'})`;
        }
        showHubToast(res.msg || '🔄 已重置插件路径');
        if (res.ok) setTimeout(closePathModal, 600);
      }
    }

    async function handleManualPickPluginFile() {
      if (!activeModalPluginId || !window.pywebview) return;
      const res = await window.pywebview.api.pick_plugin_entry_file(activeModalPluginId);
      if (res && res.state) {
        applyHubState(res.state);
        const updated = allPlugins.find(p => p.id === activeModalPluginId);
        if (updated) {
          document.getElementById('modalPluginCurrentPath').textContent = `当前指向：${updated.actualRelPath} (✅已就绪)`;
        }
        showHubToast(res.msg || '✅ 已绑定指定启动文件！');
        if (res.ok) setTimeout(closePathModal, 500);
      }
    }

    async function handleAutoScanCandidates() {
      if (!activeModalPluginId || !window.pywebview) return;
      const res = await window.pywebview.api.auto_scan_plugin_candidates(activeModalPluginId);
      if (!res) return;
      if (res.state) applyHubState(res.state);

      if (res.autoBound) {
        const updated = allPlugins.find(p => p.id === activeModalPluginId);
        if (updated) {
          document.getElementById('modalPluginCurrentPath').textContent = `当前指向：${updated.actualRelPath} (✅已自动锁定)`;
        }
        showHubToast(res.msg || '✅ 已自动选定启动文件！');
        setTimeout(closePathModal, 650);
        return;
      }

      const cands = res.candidates || [];
      const wrap = document.getElementById('candidatesWrap');
      const listEl = document.getElementById('candidatesList');
      const titleEl = document.getElementById('candidatesTitle');
      wrap.classList.remove('hidden');

      if (cands.length === 0) {
        titleEl.textContent = '⚠️ 未在目录下找到可运行文件 (.html / .py / .exe)：';
        listEl.innerHTML = `<div class="text-[11px] text-rose-500 py-2">请点击上方「📂 b. 自己手动指定启动文件」选择文件所在位置。</div>`;
        return;
      }

      titleEl.textContent = `📋 发现 ${cands.length} 个可运行文件，请点选一个作为主启动文件：`;
      listEl.innerHTML = cands.map(c => `
        <div class="p-2 rounded-xl bg-rose-50/70 border border-rose-200 flex items-center justify-between gap-2">
          <div class="min-w-0">
            <div class="text-xs font-extrabold text-rose-950 truncate flex items-center gap-1">
              <span>${c.icon} ${c.name}</span>
              ${c.recommended ? '<span class="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 text-[9px] font-black">智能推荐</span>' : ''}
            </div>
            <div class="text-[10px] text-rose-500 font-mono truncate">${c.relPath}</div>
          </div>
          <button
            type="button"
            onclick="selectCandidateFile('${c.relPath.replace(/'/g, "\\'")}')"
            class="px-2.5 py-1 rounded-lg bg-rose-500 hover:bg-rose-600 text-white text-[11px] font-extrabold shrink-0 cursor-pointer"
          >设为启动项</button>
        </div>
      `).join('');
    }

    async function selectCandidateFile(relPath) {
      if (!activeModalPluginId || !window.pywebview) return;
      const res = await window.pywebview.api.bind_plugin_candidate(activeModalPluginId, relPath);
      if (res && res.state) {
        applyHubState(res.state);
        showHubToast(res.msg || '✅ 已锁定该启动文件！');
        closePathModal();
      }
    }

    // ==================== ☁️ 版本更新 / 历史回退 / 开发者推送 / 依赖自检中心 ====================
    function switchUpdateTab(tab) {
      const tabs = ['user', 'dev', 'deps'];
      const btnMap = {
        user: document.getElementById('tabBtnUserUpdate'),
        dev: document.getElementById('tabBtnDevPush'),
        deps: document.getElementById('tabBtnDeps')
      };
      const panelMap = {
        user: document.getElementById('panelUserUpdate'),
        dev: document.getElementById('panelDevPush'),
        deps: document.getElementById('panelDeps')
      };
      tabs.forEach(t => {
        if (t === tab) {
          btnMap[t].className = 'py-1.5 px-2 rounded-xl text-xs font-extrabold bg-rose-500 text-white shadow-2xs cursor-pointer';
          panelMap[t].classList.remove('hidden');
        } else {
          btnMap[t].className = 'py-1.5 px-2 rounded-xl text-xs font-extrabold text-rose-800 hover:bg-rose-100 cursor-pointer';
          panelMap[t].classList.add('hidden');
        }
      });
    }

    async function openUpdateCenterModal() {
      const modal = document.getElementById('updateCenterModal');
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      await refreshUpdateCenterData();
    }

    function closeUpdateCenterModal() {
      const modal = document.getElementById('updateCenterModal');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    async function refreshUpdateCenterData() {
      if (!window.pywebview || !window.pywebview.api) return;
      const gitInfo = await window.pywebview.api.get_git_version_info();
      const verLabel = document.getElementById('gitCurrentVerLabel');
      const remoteLabel = document.getElementById('gitRemoteUrlLabel');
      const commitsList = document.getElementById('gitCommitsList');

      if (!gitInfo || !gitInfo.isRepo) {
        verLabel.textContent = '⚠️ 当前文件夹尚未关联 Git 仓库';
        remoteLabel.textContent = (gitInfo && gitInfo.msg) || '可随时使用「📦 备份到 bak」进行本地版本快照';
        commitsList.innerHTML = `<div class="p-3 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-800">尚未检测到 .git 历史记录。初始化 Git 仓库后，这里将展示所有历史版本供一键回退。</div>`;
      } else {
        verLabel.textContent = `当前版本：${gitInfo.head || '未知'} (${gitInfo.branch})`;
        remoteLabel.textContent = `远程地址：${gitInfo.remoteUrl || '未设置远程 origin'}`;
        const commits = gitInfo.commits || [];
        if (commits.length === 0) {
          commitsList.innerHTML = `<div class="p-3 rounded-xl bg-rose-50 text-xs text-rose-600">暂无提交记录</div>`;
        } else {
          commitsList.innerHTML = commits.map(c => `
            <div class="p-2.5 rounded-xl border ${c.isCurrent ? 'bg-indigo-50/90 border-indigo-300' : 'bg-rose-50/40 border-rose-200'} flex items-center justify-between gap-2">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5">
                  <span class="px-1.5 py-0.2 rounded bg-white border border-indigo-200 font-mono text-[10px] font-black text-indigo-800">${c.hash}</span>
                  <span class="text-xs font-extrabold text-rose-950 truncate">${c.message}</span>
                  ${c.isCurrent ? '<span class="px-1.5 py-0.2 rounded bg-emerald-500 text-white text-[9px] font-black shrink-0">当前版本</span>' : ''}
                </div>
                <div class="text-[10px] text-rose-400 mt-0.5">${c.date} ${c.ref ? '· ' + c.ref : ''}</div>
              </div>
              ${
                c.isCurrent
                  ? '<span class="text-[10px] font-bold text-emerald-700 shrink-0 px-2">使用中</span>'
                  : `<button onclick="triggerGitRollback('${c.hash}')" class="px-2.5 py-1 rounded-lg bg-white hover:bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-extrabold shrink-0 cursor-pointer">⏪ 回退到此版</button>`
              }
            </div>
          `).join('');
        }
      }

      const depInfo = await window.pywebview.api.check_requirements_status();
      const depTitle = document.getElementById('depsSummaryTitle');
      const depList = document.getElementById('depsItemsList');
      if (depInfo && depInfo.items) {
        const missingCount = (depInfo.missing || []).length;
        depTitle.textContent = missingCount === 0
          ? `✅ 全部 ${depInfo.items.length} 个所需库均已安装就绪！`
          : `⚠️ 发现 ${missingCount} 个缺失库待安装（共声明 ${depInfo.items.length} 个）`;
        depList.innerHTML = depInfo.items.map(d => `
          <div class="p-2.5 rounded-xl bg-white border border-rose-200 flex items-center justify-between gap-2">
            <div>
              <div class="text-xs font-extrabold text-rose-950">${d.spec}</div>
              <div class="text-[10px] text-rose-400">来源：${d.source}/requirements.txt</div>
            </div>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${
              d.installed ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
            }">${d.installed ? '✅ 已安装' : '⏳ 未安装'}</span>
          </div>
        `).join('');
      }
    }

    async function triggerGitPullLatest() {
      if (!window.pywebview || !window.pywebview.api) return;
      showHubToast('⏳ 正在从远程 Git 同步最新版本...');
      const res = await window.pywebview.api.git_pull_latest();
      if (res) {
        showHubToast(res.msg || (res.ok ? '🎉 已更新至最新版本！' : '⚠️ 更新失败'));
        if (res.state) applyHubState(res.state);
        await refreshUpdateCenterData();
      }
    }

    async function triggerGitRollback(commitHash) {
      if (!window.pywebview || !window.pywebview.api) return;
      showHubToast(`⏳ 正在安全回退至版本 ${commitHash}...`);
      const res = await window.pywebview.api.git_rollback_version(commitHash);
      if (res) {
        showHubToast(res.msg || (res.ok ? `✅ 已回退至版本 ${commitHash}` : '⚠️ 回退失败'));
        if (res.state) applyHubState(res.state);
        await refreshUpdateCenterData();
      }
    }

    async function triggerDeveloperPush() {
      if (!window.pywebview || !window.pywebview.api) return;
      const msg = (document.getElementById('devCommitMsgInput').value || '').trim();
      const logBox = document.getElementById('devPushLogBox');
      logBox.classList.remove('hidden');
      logBox.textContent = '⏳ 正在执行 git add -A -> git commit -> git push...';
      const res = await window.pywebview.api.git_developer_push(msg);
      if (res) {
        logBox.textContent = res.log || res.msg || '';
        showHubToast(res.msg || (res.ok ? '🚀 推送成功！' : '⚠️ 推送遇到问题'));
        if (res.ok) document.getElementById('devCommitMsgInput').value = '';
        await refreshUpdateCenterData();
      }
    }

    async function triggerInstallAllDeps() {
      if (!window.pywebview || !window.pywebview.api) return;
      showHubToast('⏳ 正在通过清华镜像源自动安装所需依赖库...');
      const res = await window.pywebview.api.install_all_requirements();
      if (res) {
        showHubToast(res.msg || '操作完成');
        await refreshUpdateCenterData();
      }
    }

    async function resetAllToDefault() {
      if (window.pywebview && window.pywebview.api) {
        const res = await window.pywebview.api.reset_all_to_default();
        if (res && res.state) {
          currentCategory = 'all';
          applyHubState(res.state);
          showHubToast('🔄 已重置默认分类、清空隐藏列表并恢复默认路径！');
        }
      }
    }

    let factoryResetStep = 0;

    function closeFactoryResetModal() {
      factoryResetStep = 0;
      const m = document.getElementById('factoryResetModal');
      if (m) m.classList.add('hidden');
    }

    function triggerFactoryResetFromGui() {
      factoryResetStep = 1;
      const m = document.getElementById('factoryResetModal');
      const t = document.getElementById('factoryResetModalTitle');
      const b = document.getElementById('factoryResetModalBody');
      const btn = document.getElementById('btnFactoryResetNext');
      if (!m || !t || !b || !btn) return;
      t.textContent = '⚠️ 第 1 / 2 次确认 · 恢复出厂初始默认';
      b.innerHTML = '<p class="font-extrabold text-red-800">即将重置所有文件夹内内容回归初始默认值：</p><p>• 清空所有自定义样式、自定义图片、历史缓存、默认导出及 <code class="font-mono">缓存/launcher_memory.json</code> 记忆</p><p>• <code class="font-mono">bak/</code> 手动备份文件夹完好保留，所有被清理文件均安全移入 Windows <b>【回收站】</b></p>';
      btn.textContent = '继续第 2 次确认 ➔';
      btn.className = 'px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-black shadow-sm cursor-pointer transition';
      m.classList.remove('hidden');
    }

    async function advanceFactoryResetStep() {
      const t = document.getElementById('factoryResetModalTitle');
      const b = document.getElementById('factoryResetModalBody');
      const btn = document.getElementById('btnFactoryResetNext');
      if (factoryResetStep === 1) {
        factoryResetStep = 2;
        if (t) t.textContent = '🚨 第 2 / 2 次确认 · 最终确认执行';
        if (b) b.innerHTML = '<p class="font-extrabold text-red-700">请再次确认：是否立即执行出厂重置？</p><p>• 确认后将立即把自定义内容与缓存移入系统回收站，并将所有子文件夹和大厅布局恢复为初始默认状态。</p>';
        if (btn) {
          btn.textContent = '🗑️ 立即移入回收站并重置 (2/2)';
          btn.className = 'px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-black shadow-sm cursor-pointer transition';
        }
        return;
      }
      closeFactoryResetModal();
      if (!window.pywebview || !window.pywebview.api) return;
      showHubToast('⏳ 正在将自定义数据与缓存安全移入回收站并恢复初始默认值...');
      const res = await window.pywebview.api.factory_reset_all_to_recycle_bin();
      if (res) {
        if (res.state) {
          currentCategory = 'all';
          applyHubState(res.state);
        }
        showHubToast(res.msg || '🎉 已完成出厂重置（原文件已放入回收站）！');
      }
    }

    async function initHub() {
      if (window.pywebview && window.pywebview.api) {
        const st = await window.pywebview.api.get_hub_state();
        applyHubState(st);
      } else {
        // 浏览器直接预览时的演示数据
        applyHubState({
          categories: [
            { id: 'doc', name: '📄 文档与办公' },
            { id: 'media', name: '🎨 视觉与画布' },
            { id: 'disk', name: '⚡ 批量与系统' },
            { id: 'custom', name: '🧩 扩展插件' }
          ],
          plugins: [
            {
              id: 'stamp_studio',
              name: '西西盖章局',
              subtitle: 'PDF/Word 强力防删水印与印章工坊',
              category: 'doc',
              icon: '🌸',
              color: 'rose',
              actualRelPath: '西西盖章局/v5_pdf.html',
              ready: true,
              hasMarker: true,
              hidden: false
            }
          ],
          viewMode: 'split',
          scanMode: 'smart',
          strayRootCount: 0
        });
      }
    }

    document.getElementById('newCatNameInput').addEventListener('keydown', e => {
      if (e.key === 'Enter') confirmAddCategory();
    });

    window.addEventListener('pywebviewready', initHub);
    window.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        if (allPlugins.length === 0) initHub();
      }, 120);
    });
  </script>
</body>
</html>
"""


AUTO_BACK_BUTTON_JS = r"""
(function() {
  if (document.title && document.title.indexOf('西西工具包') !== -1 && !location.href.startsWith('file:')) {
    return;
  }
  var existingBtn = document.getElementById('btnBackToHub');
  if (existingBtn) {
    existingBtn.classList.remove('hidden');
  } else if (!document.getElementById('xixiAutoBackBtn')) {
    var btn = document.createElement('button');
    btn.id = 'xixiAutoBackBtn';
    btn.innerHTML = '⬅️ 返回工具包';
    btn.title = '返回西西工具包选择其他插件';
    btn.style.cssText = 'position:fixed;top:12px;left:12px;z-index:999999;padding:6px 12px;border-radius:12px;background:#FFF1F2;color:#9F1239;border:2px solid #FDA4AF;border-bottom:3px solid #FB7185;font-family:"PingFang SC","Microsoft YaHei",sans-serif;font-size:12px;font-weight:800;cursor:pointer;box-shadow:0 4px 10px rgba(244,63,94,0.15);transition:all 0.15s ease;';
    btn.onmouseenter = function() { btn.style.transform = 'translateY(-1px)'; btn.style.background = '#FFE4E6'; };
    btn.onmouseleave = function() { btn.style.transform = 'none'; btn.style.background = '#FFF1F2'; };
    btn.onclick = function() {
      if (window.pywebview && window.pywebview.api && window.pywebview.api.go_home) {
        window.pywebview.api.go_home();
      }
    };
    document.body.appendChild(btn);
  }

  // ==================== 首次存储目录记忆守卫（仅第1次打开弹出，选过一次后永久记忆不再打扰） ====================
  async function syncSaveDirMemoryGuard() {
    if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_remembered_save_dir) return;
    try {
      var mem = await window.pywebview.api.get_remembered_save_dir();
      var modal = document.getElementById('firstTimeSaveDirModal');
      if (mem && mem.firstTimeCompleted) {
        try {
          localStorage.setItem('xixi_first_time_save_dir_done', '1');
          localStorage.setItem('xixi_has_chosen_save_dir', 'true');
          if (mem.defaultSaveDir) localStorage.setItem('xixi_default_save_dir', mem.defaultSaveDir);
          if (mem.defaultSaveMode) localStorage.setItem('xixi_default_save_mode', mem.defaultSaveMode);
        } catch (e) {}

        var hideFirstTimeModal = function() {
          var m = document.getElementById('firstTimeSaveDirModal');
          if (m && !m._xixiUserManualOpen) {
            m.classList.add('hidden');
            m.classList.remove('flex');
            m.style.display = 'none';
          }
        };
        hideFirstTimeModal();
        setTimeout(hideFirstTimeModal, 120);
        setTimeout(hideFirstTimeModal, 350);
        setTimeout(hideFirstTimeModal, 800);
      } else if (modal && !modal._xixiBoundFirstTimeHook) {
        modal._xixiBoundFirstTimeHook = true;
        modal.addEventListener('click', function(ev) {
          var btn = ev.target.closest('button');
          if (btn) {
            setTimeout(function() {
              if (modal.classList.contains('hidden') || modal.style.display === 'none') {
                window.pywebview.api.mark_first_time_save_dir_done();
              }
            }, 250);
          }
        });
      }
    } catch (e) {}
  }
  syncSaveDirMemoryGuard();
})();
"""


class XixiNativeBridge:
    """
    总控启动器桥接层 V4.0：
    1. 管理四大系统子文件夹（`工具/`、`bak/`、`缓存/`、`系统资源/`）、`plugin.json` 标志文件与 `🙈 隐藏收纳盒`；
    2. 动态加载并引用各插件文件夹内的专属后台模块（如 `西西盖章局/stamp_studio_backend.py` 或任意 `*_backend.py`）。
    """

    def __init__(self, window_getter):
        self._get_window = window_getter
        self._in_hub = True
        default_stamp_dir = find_stamp_studio_dir()
        self._active_plugin_dir = default_stamp_dir if default_stamp_dir.exists() else BASE_DIR
        self._plugin_backend = None
        self._load_plugin_backend(self._active_plugin_dir)

    def _load_plugin_backend(self, plugin_dir: Path):
        self._active_plugin_dir = Path(plugin_dir).resolve()

        backend_candidates = []
        if self._active_plugin_dir.exists() and self._active_plugin_dir.is_dir():
            backend_candidates.extend(sorted(self._active_plugin_dir.glob("*_backend.py")))
        fallback_stamp = find_stamp_studio_dir() / "stamp_studio_backend.py"
        if fallback_stamp.exists() and fallback_stamp not in backend_candidates:
            backend_candidates.append(fallback_stamp)

        for mod_path in backend_candidates:
            if mod_path.exists() and mod_path.is_file():
                try:
                    mod_name = f"xixi_plugin_{mod_path.stem}"
                    spec = importlib.util.spec_from_file_location(mod_name, str(mod_path))
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        for attr_name, attr_val in inspect.getmembers(mod, inspect.isclass):
                            if attr_name.endswith("Backend") and attr_val.__module__ == mod.__name__:
                                self._plugin_backend = attr_val(self._active_plugin_dir)
                                return self._plugin_backend
                except Exception:
                    pass
        return self._plugin_backend

    def _call_plugin(self, method_name: str, *args, **kwargs):
        backend = self._plugin_backend or self._load_plugin_backend(self._active_plugin_dir)
        if backend is None or not hasattr(backend, method_name):
            return {
                "ok": False,
                "msg": f"当前插件后台未实现接口 {method_name}，请检查插件文件夹内的 *_backend.py",
            }
        fn = getattr(backend, method_name)
        return fn(*args, **kwargs)

    # ==================== Git 版本热更新 / 回退 / 开发者推送接口 ====================

    def get_git_version_info(self):
        return get_git_status_and_commits()

    def git_pull_latest(self):
        info = get_git_status_and_commits()
        if not info.get("isRepo"):
            return {"ok": False, "msg": "⚠️ 当前目录尚未配置 Git 仓库，无法在线拉取"}

        branch = info.get("branch", "")
        if not branch or "分离头指针" in branch:
            for b_name in ("main", "master"):
                c, _, _ = run_git_cmd(["checkout", "-f", b_name])
                if c == 0:
                    branch = b_name
                    break

        run_git_cmd(["fetch", "--all"], timeout=45)
        run_git_cmd(["checkout", "--", "."])
        code, out, err = run_git_cmd(["pull", "--ff-only"], timeout=45)
        if code != 0 and branch:
            code, out, err = run_git_cmd(["reset", "--hard", f"origin/{branch}"], timeout=30)

        req_status = scan_all_requirements()
        if req_status["missing"]:
            install_missing_packages([x["spec"] for x in req_status["missing"]])

        if code == 0:
            return {
                "ok": True,
                "msg": "🎉 已成功同步至最新版本！（您的自定义样式、图片、缓存与 bak 均完好保留）",
                "state": build_hub_state(),
            }
        return {"ok": False, "msg": f"⚠️ 拉取更新遇到问题：{err or out}"}

    def git_rollback_version(self, target_hash: str):
        clean_hash = (target_hash or "").strip()
        if not clean_hash:
            return {"ok": False, "msg": "未指定要回退的版本号"}
        run_git_cmd(["checkout", "--", "."])
        code, out, err = run_git_cmd(["checkout", "-f", clean_hash])
        if code == 0:
            return {
                "ok": True,
                "msg": f"⏪ 已安全回退至历史版本 [{clean_hash}]！",
                "state": build_hub_state(),
            }
        return {"ok": False, "msg": f"⚠️ 回退失败：{err or out}"}

    def git_developer_push(self, commit_msg: str = ""):
        info = get_git_status_and_commits()
        if not info.get("isRepo"):
            return {"ok": False, "msg": "⚠️ 当前目录尚未初始化 Git 仓库"}

        msg = (commit_msg or "").strip()
        if not msg:
            msg = f"✨ 更新西西工具包 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M')})"

        logs = []
        c1, o1, e1 = run_git_cmd(["add", "-A"])
        logs.append(f"$ git add -A\n{o1 or e1 or '已暂存全部代码改动'}")

        c2, o2, e2 = run_git_cmd(["commit", "-m", msg])
        logs.append(f"$ git commit -m \"{msg}\"\n{o2 or e2}")

        c3, o3, e3 = run_git_cmd(["push"], timeout=60)
        logs.append(f"$ git push\n{o3 or e3 or '推送完成'}")

        if c3 == 0:
            return {
                "ok": True,
                "msg": "🚀 已成功提交并推送到远程 Git 仓库！",
                "log": "\n\n".join(logs),
            }
        return {
            "ok": False,
            "msg": f"⚠️ 推送至远程仓库未成功，请检查网络或远程分支设置：{e3 or o3}",
            "log": "\n\n".join(logs),
        }

    # ==================== 依赖库 requirements.txt 检索与安装接口 ====================

    def check_requirements_status(self):
        return scan_all_requirements()

    def install_all_requirements(self):
        status = scan_all_requirements()
        missing_specs = [x["spec"] for x in status.get("missing", [])]
        return install_missing_packages(missing_specs)

    # ==================== 启动器大厅管理接口（含四大系统子夹、隐藏收纳盒、标志文件、新建插件） ====================

    def get_hub_state(self):
        return build_hub_state()

    def set_view_mode(self, mode: str):
        cfg = load_user_config()
        cfg["viewMode"] = "tile" if mode == "tile" else "split"
        save_user_config(cfg)
        return {"ok": True}

    def set_scan_mode(self, mode: str):
        cfg = load_user_config()
        cfg["scanMode"] = "strict" if mode == "strict" else "smart"
        save_user_config(cfg)
        label = "🔒 严格标志模式（仅显示含 plugin.json 的子夹）" if cfg["scanMode"] == "strict" else "🏷️ 智能识别模式（含 plugin.json 或可运行文件）"
        return {"ok": True, "msg": f"✨ 已切换为：{label}", "state": build_hub_state()}

    def toggle_plugin_hidden(self, plugin_id: str, hide_flag: bool | None = None):
        cfg = load_user_config()
        hidden_list = list(cfg.get("hiddenPlugins", []))
        is_currently_hidden = plugin_id in hidden_list
        target_hide = (not is_currently_hidden) if hide_flag is None else bool(hide_flag)
        if target_hide and plugin_id not in hidden_list:
            hidden_list.append(plugin_id)
        elif not target_hide and plugin_id in hidden_list:
            hidden_list.remove(plugin_id)
        cfg["hiddenPlugins"] = hidden_list
        save_user_config(cfg)
        msg = "🙈 已移入左侧「隐藏收纳盒」（不再显示在常规列表与平铺中）" if target_hide else "👁️ 已从「隐藏收纳盒」恢复显示！"
        return {"ok": True, "hidden": target_hide, "msg": msg, "state": build_hub_state()}

    def save_plugin_marker_info(self, plugin_id: str, name: str, subtitle: str, icon: str):
        state_now = build_hub_state()
        p_obj = next((p for p in state_now["plugins"] if p["id"] == plugin_id), None)
        if not p_obj:
            return {"ok": False, "msg": "未找到该插件"}
        folder_path = BASE_DIR / p_obj["folder"]
        existing_marker = read_plugin_marker(folder_path) or {}
        entry_rel = Path(p_obj["actualRelPath"]).name if p_obj.get("actualRelPath") else "index.html"
        marker_data = {
            **existing_marker,
            "id": plugin_id,
            "name": name.strip() or p_obj["name"],
            "subtitle": subtitle.strip() or p_obj["subtitle"],
            "icon": icon.strip() or p_obj["icon"],
            "color": p_obj.get("color", "rose"),
            "category": p_obj.get("category", "custom"),
            "entry": existing_marker.get("entry") or entry_rel,
            "enabled": True,
        }
        write_plugin_marker(folder_path, marker_data)
        return {
            "ok": True,
            "msg": f"🏷️ 已保存插件信息并写入 {p_obj['folder']}/plugin.json！",
            "state": build_hub_state(),
        }

    def create_new_plugin_scaffold(self, name: str, subtitle: str, icon: str, category_id: str):
        clean_name = re.sub(r'[\\/:*?"<>|]+', "_", (name or "").strip())
        if not clean_name:
            return {"ok": False, "msg": "⚠️ 插件名称不能为空"}
        if clean_name in SYSTEM_SUPPORT_FOLDERS:
            return {"ok": False, "msg": f"⚠️ 「{clean_name}」是系统保留目录名，请换一个名字哟"}
        plugin_dir = BASE_DIR / clean_name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        pid = f"custom_{clean_name}"
        marker_data = {
            "id": pid,
            "name": clean_name,
            "subtitle": (subtitle or "").strip() or f"{clean_name} · 西西工具包扩展插件",
            "icon": (icon or "✨").strip(),
            "color": "emerald",
            "category": category_id or "custom",
            "entry": "index.html",
            "enabled": True,
        }
        write_plugin_marker(plugin_dir, marker_data)

        index_html = plugin_dir / "index.html"
        if not index_html.exists():
            starter_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>{clean_name}</title>
  <script src="https://cdn.tailwindcss.com/3.4.17" async onerror="this.remove()"></script>
</head>
<body class="min-h-screen bg-rose-50/40 text-rose-950 flex flex-col items-center justify-center p-6 font-sans">
  <button id="btnBackToHub" onclick="if(window.pywebview&&window.pywebview.api)window.pywebview.api.go_home();" class="fixed top-4 left-4 px-3.5 py-2 rounded-xl bg-white hover:bg-rose-50 text-rose-800 border-2 border-rose-300 font-extrabold text-xs shadow-sm cursor-pointer">
    ⬅️ 返回工具包
  </button>
  <div class="bg-white rounded-3xl border-2 border-rose-200 shadow-lg p-8 max-w-lg w-full text-center space-y-3">
    <div class="text-4xl">{marker_data['icon']}</div>
    <h1 class="text-lg font-black text-rose-950">{clean_name}</h1>
    <p class="text-xs text-rose-600">{marker_data['subtitle']}</p>
    <div class="p-3 rounded-xl bg-rose-50 border border-rose-200 text-[11px] text-left font-mono text-rose-800">
      📁 文件夹：{clean_name}/<br/>
      🏷️ 标志文件：{clean_name}/plugin.json<br/>
      🌐 入口文件：{clean_name}/index.html
    </div>
  </div>
</body>
</html>
"""
            index_html.write_text(starter_html, encoding="utf-8")

        cfg = load_user_config()
        cfg.setdefault("pluginCategories", {})[pid] = category_id or "custom"
        save_user_config(cfg)

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(plugin_dir))
        except Exception:
            pass

        return {
            "ok": True,
            "msg": f"✨ 已创建插件子文件夹「{clean_name}/」及 plugin.json 标志文件！",
            "state": build_hub_state(),
        }

    def organize_root_directory(self):
        res = ensure_standard_root_architecture(auto_migrate_files=True)
        res["state"] = build_hub_state()
        return res

    def create_snapshot_backup(self, note: str = ""):
        return create_manual_snapshot_to_bak(note)

    def open_system_subfolder(self, folder_key: str):
        ensure_standard_root_architecture(auto_migrate_files=False)
        mapping = {
            "root": BASE_DIR,
            "tools": TOOLS_DIR,
            "bak": BAK_DIR,
            "cache": CACHE_DIR,
            "sys_res": SYS_RES_DIR,
        }
        target = mapping.get(folder_key, BASE_DIR)
        target.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(target))
        except Exception:
            pass
        return {"ok": True, "path": str(target)}

    def add_category(self, name: str):
        clean_name = (name or "").strip()
        if not clean_name:
            return {"ok": False}
        cfg = load_user_config()
        cats = cfg.get("categories", [])
        new_id = f"cat_{int(datetime.datetime.now().timestamp() * 1000)}_{len(cats) + 1}"
        cats.append({"id": new_id, "name": clean_name})
        cfg["categories"] = cats
        save_user_config(cfg)
        return {"ok": True, "state": build_hub_state()}

    def delete_category(self, cat_id: str):
        cfg = load_user_config()
        cats = [c for c in cfg.get("categories", []) if c.get("id") != cat_id]
        if not cats:
            return {"ok": False}
        cfg["categories"] = cats
        fallback_id = cats[0]["id"]
        pcats = cfg.get("pluginCategories", {})
        for pid, cid in list(pcats.items()):
            if cid == cat_id:
                pcats[pid] = fallback_id
        cfg["pluginCategories"] = pcats
        save_user_config(cfg)
        return {"ok": True, "state": build_hub_state()}

    def move_plugin_category(self, plugin_id: str, target_cat_id: str):
        cfg = load_user_config()
        if target_cat_id == HIDDEN_CATEGORY_ID:
            return self.toggle_plugin_hidden(plugin_id, True)
        pcats = cfg.get("pluginCategories", {})
        pcats[plugin_id] = target_cat_id
        cfg["pluginCategories"] = pcats
        # 如果从隐藏收纳盒拖到普通分类，自动解除隐藏状态
        hidden_list = list(cfg.get("hiddenPlugins", []))
        if plugin_id in hidden_list:
            hidden_list.remove(plugin_id)
            cfg["hiddenPlugins"] = hidden_list
        save_user_config(cfg)
        return {"ok": True, "state": build_hub_state()}

    def reset_all_to_default(self):
        for p in (USER_CONFIG_PATH, LEGACY_USER_CONFIG_PATH):
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        return {"ok": True, "state": build_hub_state()}

    def reset_and_sniff_plugin(self, plugin_id: str):
        cfg = load_user_config()
        ppaths = cfg.get("pluginPaths", {})
        ppaths.pop(plugin_id, None)

        builtin_map = {p["id"]: p for p in BUILTIN_PLUGINS}
        meta = builtin_map.get(plugin_id)
        msg = "🔄 已重置为默认路径"
        ok = False

        if meta:
            def_p = BASE_DIR / meta["defaultRelPath"]
            alt_p = (BASE_DIR / meta["fallbackRelPath"]) if meta["fallbackRelPath"] else None
            if def_p.exists():
                ok = True
                msg = f"✅ 已恢复默认路径：{meta['defaultRelPath']}"
            elif alt_p and alt_p.exists():
                ok = True
                msg = f"✅ 已恢复默认路径：{meta['fallbackRelPath']}"
            else:
                sniffed = sniff_plugin_by_fingerprint(meta)
                if sniffed and sniffed.exists():
                    rel_str = to_display_path(sniffed)
                    ppaths[plugin_id] = rel_str
                    ok = True
                    msg = f"🎉 检测到插件曾被改名，已通过特征码自动找回：{rel_str}"
                else:
                    msg = "⚠️ 默认路径下未找到文件，请使用「b. 手动指定」或「c. 自动扫描」"

        cfg["pluginPaths"] = ppaths
        save_user_config(cfg)
        return {"ok": ok, "msg": msg, "state": build_hub_state()}

    def pick_plugin_entry_file(self, plugin_id: str):
        if not tk or not filedialog:
            return {"ok": False, "msg": "当前环境不支持文件对话框", "state": build_hub_state()}
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        picked = filedialog.askopenfilename(
            title="请指定该插件的启动文件 (.html / .py / .exe / .bat)",
            initialdir=str(BASE_DIR),
            filetypes=[
                ("可运行插件文件", "*.html *.htm *.py *.pyw *.exe *.bat"),
                ("网页插件 (.html)", "*.html *.htm"),
                ("Python 脚本 (.py)", "*.py *.pyw"),
                ("可执行程序 (.exe/.bat)", "*.exe *.bat"),
                ("所有文件", "*.*"),
            ],
        )
        root.destroy()
        if not picked:
            return {"ok": False, "msg": "已取消选择", "state": build_hub_state()}

        p = Path(picked).resolve()
        disp = to_display_path(p)
        cfg = load_user_config()
        ppaths = cfg.get("pluginPaths", {})
        ppaths[plugin_id] = disp
        cfg["pluginPaths"] = ppaths
        save_user_config(cfg)
        return {"ok": True, "msg": f"✅ 已绑定启动文件：{disp}", "state": build_hub_state()}

    def auto_scan_plugin_candidates(self, plugin_id: str):
        cfg = load_user_config()
        cands = list_runnable_candidates_for_plugin(plugin_id, cfg)
        if len(cands) == 1:
            chosen = cands[0]["relPath"]
            ppaths = cfg.get("pluginPaths", {})
            ppaths[plugin_id] = chosen
            cfg["pluginPaths"] = ppaths
            save_user_config(cfg)
            return {
                "ok": True,
                "autoBound": True,
                "msg": f"✅ 已自动锁定唯一可运行文件：{chosen}",
                "candidates": cands,
                "state": build_hub_state(),
            }
        return {
            "ok": True,
            "autoBound": False,
            "candidates": cands,
            "state": build_hub_state(),
        }

    def bind_plugin_candidate(self, plugin_id: str, rel_path: str):
        cfg = load_user_config()
        ppaths = cfg.get("pluginPaths", {})
        ppaths[plugin_id] = rel_path
        cfg["pluginPaths"] = ppaths
        save_user_config(cfg)
        return {"ok": True, "msg": f"✅ 已将「{rel_path}」设为启动项！", "state": build_hub_state()}

    def open_root_folder(self):
        try:
            os.startfile(str(BASE_DIR))
        except Exception:
            pass
        return {"ok": True}

    def go_home(self):
        self._in_hub = True
        win = self._get_window()
        if win:
            try:
                win.resize(HUB_WIDTH, HUB_HEIGHT)
            except Exception:
                pass
            win.set_title("🐾 西西工具包")
            win.load_html(LAUNCHER_HUB_HTML)
        return {"ok": True}

    def open_plugin_by_id(self, plugin_id: str):
        state_now = build_hub_state()
        plugin_obj = next((p for p in state_now["plugins"] if p["id"] == plugin_id), None)
        if not plugin_obj:
            return {"ok": False, "msg": "未找到该插件配置"}

        target = resolve_path_str(plugin_obj["actualRelPath"])
        if not target.exists() or not target.is_file():
            builtin_map = {p["id"]: p for p in BUILTIN_PLUGINS}
            meta = builtin_map.get(plugin_id)
            if meta:
                sniffed = sniff_plugin_by_fingerprint(meta)
                if sniffed and sniffed.exists():
                    cfg = load_user_config()
                    cfg.setdefault("pluginPaths", {})[plugin_id] = to_display_path(sniffed)
                    save_user_config(cfg)
                    target = sniffed

        if not target.exists() or not target.is_file():
            return {
                "ok": False,
                "msg": f"⚠️ 未找到启动文件「{plugin_obj['actualRelPath']}」，请在弹窗中一键重置、指定或自动扫描！",
            }

        return self._launch_target_file(target, plugin_obj["name"])

    def open_plugin(self, rel_path: str):
        target = resolve_path_str(rel_path)
        if not target.exists():
            alt = BASE_DIR / Path(rel_path).name
            if alt.exists():
                target = alt
            else:
                return {"ok": False, "msg": f"未找到插件文件：{target}"}
        return self._launch_target_file(target, target.parent.name)

    def _launch_target_file(self, target: Path, title_label: str):
        plugin_dir = target.parent.resolve()
        req_check = scan_all_requirements(plugin_dir)
        if req_check["missing"]:
            install_missing_packages([x["spec"] for x in req_check["missing"]])

        ext = target.suffix.lower()
        if ext in (".html", ".htm"):
            self._load_plugin_backend(plugin_dir)
            self._sync_save_dir_memory_js()
            self._auto_patch_plugin_html_first_time_memory(target)
            self._in_hub = False
            win = self._get_window()
            if win:
                try:
                    win.resize(PLUGIN_WIDTH, PLUGIN_HEIGHT)
                except Exception:
                    pass
                win.set_title(f"🐾 西西工具包 · {title_label}")
                win.load_url(target.as_uri())
                return {"ok": True}
        elif ext in (".py", ".pyw"):
            py_runner = find_system_python(gui_mode=(ext == ".pyw"))
            subprocess.Popen([py_runner, str(target)], cwd=str(plugin_dir))
            return {"ok": True, "msg": f"已启动 Python 工具：{target.name}"}
        elif ext in (".exe", ".bat"):
            subprocess.Popen([str(target)], cwd=str(plugin_dir), shell=(ext == ".bat"))
            return {"ok": True, "msg": f"已启动程序：{target.name}"}
        return {"ok": False, "msg": "暂不支持该插件文件类型"}

    # ==================== 子插件后台接口轻量转发 ====================

    def ensure_system_resources(self, demo_pdf_b64: str = "", mascot_svg: str = ""):
        return self._call_plugin("ensure_system_resources", demo_pdf_b64, mascot_svg)

    def _get_save_dir_memory_path(self) -> Path:
        sys_dir = self._active_plugin_dir / "系统资源"
        sys_dir.mkdir(parents=True, exist_ok=True)
        return sys_dir / "save_dir_memory.json"

    def _load_save_dir_memory(self) -> dict:
        p = self._get_save_dir_memory_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        for pname in ("prefs_config.json", "prefs.json"):
            legacy_prefs = self._active_plugin_dir / "历史缓存" / pname
            if legacy_prefs.exists():
                try:
                    lp = json.loads(legacy_prefs.read_text(encoding="utf-8"))
                    if isinstance(lp, dict) and (lp.get("firstRunCompleted") or lp.get("hasChosenSaveDir") or lp.get("firstTimeDone") or lp.get("firstTimeCompleted")):
                        mem = {
                            "firstTimeCompleted": True,
                            "defaultSaveMode": lp.get("defaultSaveMode", "plugin_export"),
                            "defaultSaveDir": lp.get("defaultSaveDir", ""),
                        }
                        self._write_save_dir_memory(mem)
                        return mem
                except Exception:
                    pass
        return {"firstTimeCompleted": False, "defaultSaveMode": "", "defaultSaveDir": ""}

    def _write_save_dir_memory(self, mem_dict: dict):
        try:
            p = self._get_save_dir_memory_path()
            p.write_text(json.dumps(mem_dict, ensure_ascii=False, indent=2), encoding="utf-8")
            # 同步备份一份到根目录 `缓存/stamp_save_dir_memory.json`
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            (CACHE_DIR / "stamp_save_dir_memory.json").write_text(
                json.dumps(mem_dict, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            self._sync_save_dir_memory_js(mem_dict)
        except Exception:
            pass

    def _sync_save_dir_memory_js(self, mem_dict: dict | None = None):
        try:
            if mem_dict is None:
                mem_dict = self._load_save_dir_memory()
            sys_dir = self._active_plugin_dir / "系统资源"
            sys_dir.mkdir(parents=True, exist_ok=True)
            js_path = sys_dir / "save_dir_memory.js"
            payload_json = json.dumps(mem_dict, ensure_ascii=False)
            js_code = (
                f"window.__XIXI_REMEMBERED_SAVE_DIR__ = {payload_json};\n"
                "try {\n"
                "  if (window.__XIXI_REMEMBERED_SAVE_DIR__ && window.__XIXI_REMEMBERED_SAVE_DIR__.firstTimeCompleted) {\n"
                "    localStorage.setItem('xixi_first_time_save_dir_done', '1');\n"
                "    localStorage.setItem('xixi_has_chosen_save_dir', 'true');\n"
                "    if (window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveDir) localStorage.setItem('xixi_default_save_dir', window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveDir);\n"
                "    if (window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveMode) localStorage.setItem('xixi_default_save_mode', window.__XIXI_REMEMBERED_SAVE_DIR__.defaultSaveMode);\n"
                "  }\n"
                "} catch(e) {}\n"
            )
            js_path.write_text(js_code, encoding="utf-8")
            token_js = sys_dir / "reset_localstorage_token.js"
            if not token_js.exists():
                token_js.write_text("// factory reset token placeholder\n", encoding="utf-8")
        except Exception:
            pass

    def _auto_patch_plugin_html_first_time_memory(self, html_path: Path):
        try:
            if not html_path.exists() or not html_path.is_file():
                return
            raw = html_path.read_text(encoding="utf-8", errors="ignore")
            if "西西盖章局" not in raw and "watermarkOverlayCanvas" not in raw:
                return
            modified = False
            if 'save_dir_memory.js' not in raw and "</head>" in raw:
                inject_head = (
                    '  <script>if(window.location.protocol==="file:"){["系统资源/save_dir_memory.js","系统资源/reset_localstorage_token.js"].forEach(function(p){var s=document.createElement("script");s.src=p;document.head.appendChild(s);});}</script>\n'
                    '  <style>body.xixi-remembered-save-dir #firstTimeSaveDirModal:not(.xixi-manual-open){display:none!important;}</style>\n'
                    '</head>'
                )
                raw = raw.replace("</head>", inject_head, 1)
                modified = True

            patch_marker = "/* __XIXI_HTML_INTERNAL_SAVE_DIR_MEMORY_PATCH_V37__ */"
            if patch_marker not in raw and "</body>" in raw:
                internal_patch = """<script>
/* __XIXI_HTML_INTERNAL_SAVE_DIR_MEMORY_PATCH_V37__ */
(function() {
  if (window.__XIXI_FACTORY_RESET_TOKEN__) {
    try {
      var lastTok = localStorage.getItem('xixi_last_factory_reset_token');
      if (lastTok !== String(window.__XIXI_FACTORY_RESET_TOKEN__)) {
        localStorage.clear();
        localStorage.setItem('xixi_last_factory_reset_token', String(window.__XIXI_FACTORY_RESET_TOKEN__));
      }
    } catch (e) {}
  }
  function isRememberedDone() {
    try {
      if (window.__XIXI_REMEMBERED_SAVE_DIR__ && window.__XIXI_REMEMBERED_SAVE_DIR__.firstTimeCompleted) return true;
      if (localStorage.getItem('xixi_first_time_save_dir_done') === '1') return true;
      if (localStorage.getItem('xixi_has_chosen_save_dir') === 'true') return true;
      if (localStorage.getItem('xixi_default_save_dir')) return true;
    } catch (e) {}
    return false;
  }
  function applyRememberedClass() {
    if (isRememberedDone() && document.body) {
      document.body.classList.add('xixi-remembered-save-dir');
      var m = document.getElementById('firstTimeSaveDirModal');
      if (m && !m.classList.contains('xixi-manual-open')) {
        m.classList.add('hidden');
        m.classList.remove('flex');
      }
    }
  }
  document.addEventListener('DOMContentLoaded', function() {
    applyRememberedClass();
    var m = document.getElementById('firstTimeSaveDirModal');
    if (m) {
      m.addEventListener('click', function(ev) {
        var b = ev.target.closest('button');
        if (b) {
          setTimeout(function() {
            if (m.classList.contains('hidden') || m.style.display === 'none') {
              m.classList.remove('xixi-manual-open');
              try {
                localStorage.setItem('xixi_first_time_save_dir_done', '1');
                localStorage.setItem('xixi_has_chosen_save_dir', 'true');
              } catch (e) {}
              if (window.pywebview && window.pywebview.api && window.pywebview.api.mark_first_time_save_dir_done) {
                window.pywebview.api.mark_first_time_save_dir_done();
              }
              applyRememberedClass();
            }
          }, 200);
        }
      });
    }
    document.addEventListener('click', function(ev) {
      var t = ev.target.closest('[id*="ChangeDefaultSaveDir"], [id*="changeSaveDir"], [onclick*="firstTimeSaveDirModal"]');
      if (t && m) {
        m.classList.add('xixi-manual-open');
        m.classList.remove('hidden');
        m.classList.add('flex');
      }
    });
  });
  applyRememberedClass();
})();
</script>
</body>"""
                raw = raw.replace("</body>", internal_patch, 1)
                modified = True

            if modified:
                html_path.write_text(raw, encoding="utf-8")
        except Exception:
            pass

    def get_remembered_save_dir(self):
        return self._load_save_dir_memory()

    def mark_first_time_save_dir_done(self, mode: str = "subfolder", custom_path: str = ""):
        mem = self._load_save_dir_memory()
        mem["firstTimeCompleted"] = True
        if mode:
            mem["defaultSaveMode"] = mode
        if custom_path:
            mem["defaultSaveDir"] = custom_path
        self._write_save_dir_memory(mem)
        return {"ok": True, "memory": mem}

    def get_plugin_init_data(self):
        res = self._call_plugin("get_plugin_init_data")
        mem = self._load_save_dir_memory()
        if isinstance(res, dict):
            if res.get("needsFirstTimeSetup") is False or (isinstance(res.get("prefs"), dict) and res["prefs"].get("firstRunCompleted")):
                if not mem.get("firstTimeCompleted"):
                    mem["firstTimeCompleted"] = True
                    mem["defaultSaveMode"] = res.get("defaultSaveMode") or "plugin_export"
                    mem["defaultSaveDir"] = res.get("defaultSaveDir") or ""
                    self._write_save_dir_memory(mem)
            if mem.get("firstTimeCompleted"):
                saved_mode = mem.get("defaultSaveMode") or "plugin_export"
                saved_dir = mem.get("defaultSaveDir") or ""
                try:
                    self._call_plugin("set_default_save_dir", saved_mode, saved_dir)
                except Exception:
                    pass
                res["firstRunCompleted"] = True
                res["firstTimeDone"] = True
                res["firstTimeCompleted"] = True
                res["hasChosenSaveDir"] = True
                res["needsFirstTimeSetup"] = False
                res["needFirstTimeSetup"] = False
                res["isFirstOpen"] = False
                if saved_mode:
                    res["defaultSaveMode"] = saved_mode
                if saved_dir:
                    res["defaultSaveDir"] = saved_dir
                if isinstance(res.get("prefs"), dict):
                    res["prefs"]["firstRunCompleted"] = True
                    res["prefs"]["firstTimeDone"] = True
                    res["prefs"]["hasChosenSaveDir"] = True
                    if saved_mode:
                        res["prefs"]["defaultSaveMode"] = saved_mode
                    if saved_dir:
                        res["prefs"]["defaultSaveDir"] = saved_dir
        return res

    def save_plugin_prefs(self, prefs_dict: dict):
        if isinstance(prefs_dict, dict):
            if prefs_dict.get("firstRunCompleted") or prefs_dict.get("hasChosenSaveDir") or prefs_dict.get("firstTimeDone"):
                mem = self._load_save_dir_memory()
                mem["firstTimeCompleted"] = True
                if prefs_dict.get("defaultSaveMode"):
                    mem["defaultSaveMode"] = prefs_dict["defaultSaveMode"]
                if prefs_dict.get("defaultSaveDir"):
                    mem["defaultSaveDir"] = prefs_dict["defaultSaveDir"]
                self._write_save_dir_memory(mem)
        return self._call_plugin("save_plugin_prefs", prefs_dict)

    def set_default_save_dir(self, mode: str, custom_path: str = ""):
        res = self._call_plugin("set_default_save_dir", mode, custom_path)
        mem = self._load_save_dir_memory()
        mem["firstTimeCompleted"] = True
        mem["defaultSaveMode"] = mode or "subfolder"
        if isinstance(res, dict) and res.get("defaultSaveDir"):
            mem["defaultSaveDir"] = res["defaultSaveDir"]
        elif custom_path:
            mem["defaultSaveDir"] = custom_path
        self._write_save_dir_memory(mem)
        return res

    def pick_default_save_dir(self):
        res = self._call_plugin("pick_default_save_dir")
        if isinstance(res, dict) and res.get("ok"):
            mem = self._load_save_dir_memory()
            mem["firstTimeCompleted"] = True
            mem["defaultSaveMode"] = res.get("defaultSaveMode", "custom")
            mem["defaultSaveDir"] = res.get("defaultSaveDir", "")
            self._write_save_dir_memory(mem)
        return res

    def list_subfolder_images(self):
        res = self._call_plugin("list_subfolder_images")
        return res if isinstance(res, list) else []

    def save_subfolder_image(self, file_name: str, b64_data: str):
        return self._call_plugin("save_subfolder_image", file_name, b64_data)

    def delete_subfolder_image(self, file_name: str):
        return self._call_plugin("delete_subfolder_image", file_name)

    def list_subfolder_styles(self):
        res = self._call_plugin("list_subfolder_styles")
        return res if isinstance(res, list) else []

    def save_subfolder_styles(self, stickers_list: list, single_sticker: dict | None = None):
        return self._call_plugin("save_subfolder_styles", stickers_list, single_sticker)

    def pick_input_files(self):
        res = self._call_plugin("pick_input_files")
        return res if isinstance(res, list) else []

    def save_batch_to_default_dir(self, items: list):
        return self._call_plugin("save_batch_to_default_dir", items)

    def save_batch_custom_dir(self, items: list):
        return self._call_plugin("save_batch_custom_dir", items)

    def save_single_dialog(self, source_path: str, suggested_name: str, b64_data: str, original_name: str = "", profile_label: str = ""):
        return self._call_plugin("save_single_dialog", source_path, suggested_name, b64_data, original_name, profile_label)

    def quick_save_to_source(self, items):
        return self._call_plugin("quick_save_to_source", items)

    def get_save_history(self):
        res = self._call_plugin("get_save_history")
        return res if isinstance(res, list) else []

    def reveal_in_explorer(self, target_path: str):
        return self._call_plugin("reveal_in_explorer", target_path)

    def open_folder(self, dir_path: str):
        return self._call_plugin("open_folder", dir_path)

    def revoke_history_item(self, record_id: str):
        return self._call_plugin("revoke_history_item", record_id)

    def restore_history_item(self, record_id: str):
        return self._call_plugin("restore_history_item", record_id)

    def delete_history_item(self, record_id: str):
        return self._call_plugin("delete_history_item", record_id)

    def clear_all_history(self):
        return self._call_plugin("clear_all_history")

    def factory_reset_all_to_recycle_bin(self):
        res = perform_factory_reset_to_recycle_bin(interactive=False)
        res["state"] = build_hub_state()
        return res


# ==================== 西西 2头身 Q版专属图标自动释放与 Win32 任务栏/文件图标刷新引擎 ====================

EMBEDDED_XIXI_ICO_ZLIB_B64 = "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"


def ensure_xixi_ico_exists() -> Path:
    """
    确保 `D:\\西西工具包\\系统资源\\xixi_icon.ico` 存在（若根目录原本存在 `xixi_icon.ico` 则同步复制到 `系统资源/`）。
    """
    SYS_RES_DIR.mkdir(parents=True, exist_ok=True)
    ico_path = SYS_RES_DIR / "xixi_icon.ico"
    root_ico = BASE_DIR / "xixi_icon.ico"
    if root_ico.exists() and root_ico.stat().st_size > 1000 and not ico_path.exists():
        try:
            shutil.copy2(str(root_ico), str(ico_path))
        except Exception:
            pass
    if ico_path.exists() and ico_path.stat().st_size > 1000:
        return ico_path
    try:
        raw_ico = zlib.decompress(base64.b64decode(EMBEDDED_XIXI_ICO_ZLIB_B64))
        ico_path.write_bytes(raw_ico)
    except Exception:
        pass
    return ico_path


def refresh_windows_icon_cache(exe_path: Path | None = None):
    if not sys.platform.startswith("win"):
        return
    try:
        if exe_path and exe_path.exists():
            now_ts = time.time()
            os.utime(str(exe_path), (now_ts, now_ts))
    except Exception:
        pass
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception:
        pass
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW
        subprocess.run(["ie4uinit.exe", "-show"], creationflags=creation_flags, timeout=5, capture_output=True)
        subprocess.run(["ie4uinit.exe", "-ClearIconCache"], creationflags=creation_flags, timeout=5, capture_output=True)
    except Exception:
        pass


def apply_win32_window_icon(window_title: str, ico_path: Path):
    if not sys.platform.startswith("win") or not ico_path.exists():
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("XixiToolkit.Launcher.V4.0")
    except Exception:
        pass

    def _worker():
        try:
            user32 = ctypes.windll.user32
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            LR_DEFAULTSIZE = 0x00000040
            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1

            hicon_big = user32.LoadImageW(None, str(ico_path), IMAGE_ICON, 64, 64, LR_LOADFROMFILE)
            hicon_small = user32.LoadImageW(None, str(ico_path), IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
            if not hicon_big:
                hicon_big = user32.LoadImageW(None, str(ico_path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)

            for _ in range(25):
                hwnd = user32.FindWindowW(None, window_title)
                if hwnd:
                    if hicon_big:
                        user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
                    if hicon_small:
                        user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
                    break
                time.sleep(0.15)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


# ==================== 一键恢复出厂初始默认值（清空所有自定义与缓存并安全移入 Windows 回收站） ====================

class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("wFunc", ctypes.c_uint),
        ("pFrom", ctypes.c_wchar_p),
        ("pTo", ctypes.c_wchar_p),
        ("fFlags", ctypes.c_ushort),
        ("fAnyOperationsAborted", ctypes.c_int),
        ("hNameMappings", ctypes.c_void_p),
        ("lpszProgressTitle", ctypes.c_wchar_p),
    ]


def send_paths_to_windows_recycle_bin(paths: list[Path]) -> tuple[int, list[str]]:
    valid_paths = [p.resolve() for p in paths if p.exists()]
    if not valid_paths:
        return 0, []

    moved_count = 0
    errors = []

    if sys.platform.startswith("win"):
        FO_DELETE = 3
        FOF_SILENT = 0x0004
        FOF_NOCONFIRMATION = 0x0010
        FOF_ALLOWUNDO = 0x0040
        FOF_NOERRORUI = 0x0400

        for p in valid_paths:
            try:
                from_buf = ctypes.create_unicode_buffer(str(p) + "\0\0")
                op = SHFILEOPSTRUCTW()
                op.hwnd = None
                op.wFunc = FO_DELETE
                op.pFrom = ctypes.cast(from_buf, ctypes.c_wchar_p)
                op.pTo = None
                op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
                ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
                if ret == 0 and not p.exists():
                    moved_count += 1
                    continue
            except Exception:
                pass

            try:
                is_dir = p.is_dir()
                ps_method = "DeleteDirectory" if is_dir else "DeleteFile"
                escaped = str(p).replace("'", "''")
                ps_cmd = (
                    "Add-Type -AssemblyName Microsoft.VisualBasic; "
                    f"[Microsoft.VisualBasic.FileIO.FileSystem]::{ps_method}('{escaped}', 'OnlyErrorDialogs', 'SendToRecycleBin')"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_cmd],
                    capture_output=True,
                    timeout=15,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                if not p.exists():
                    moved_count += 1
                else:
                    errors.append(str(p))
            except Exception as e:
                errors.append(f"{p}: {e}")
    else:
        trash_fallback = BASE_DIR / "_回收站备份" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        trash_fallback.mkdir(parents=True, exist_ok=True)
        for p in valid_paths:
            try:
                shutil.move(str(p), str(trash_fallback / p.name))
                moved_count += 1
            except Exception as e:
                errors.append(f"{p}: {e}")

    return moved_count, errors


def collect_custom_and_cache_targets() -> tuple[list[Path], list[Path]]:
    """
    扫描西西工具包根目录、`缓存/` 及所有插件子目录，收集所有需要移入回收站的自定义文件/缓存项
    （注意：`bak/` 手动备份文件夹与 `工具/` 辅助脚本夹受严格保护，绝不清理！）
    """
    target_folder_names = {"自定义样式", "自定义图片", "历史缓存", "默认导出"}
    items_to_recycle: list[Path] = []
    dirs_to_recreate: list[Path] = [CACHE_DIR]

    # 1. 收集根目录 `缓存/` 下的所有记忆文件
    if CACHE_DIR.exists() and CACHE_DIR.is_dir():
        try:
            for child in sorted(CACHE_DIR.iterdir()):
                items_to_recycle.append(child)
        except Exception:
            pass

    scan_roots = [BASE_DIR]
    try:
        for sub in sorted(BASE_DIR.iterdir()):
            if sub.is_dir() and not sub.name.startswith(".") and sub.name not in {".git", "__pycache__", "build", "dist", "bak", "backup", "工具", "小工具"}:
                scan_roots.append(sub)
    except Exception:
        pass

    seen_dirs = set()
    for root in scan_roots:
        for tname in target_folder_names:
            tdir = (root / tname).resolve()
            if str(tdir) in seen_dirs:
                continue
            seen_dirs.add(str(tdir))
            if tdir.exists() and tdir.is_dir():
                dirs_to_recreate.append(tdir)
                try:
                    for child in sorted(tdir.iterdir()):
                        items_to_recycle.append(child)
                except Exception:
                    pass
            elif root != BASE_DIR and (root / "v5_pdf.html").exists():
                dirs_to_recreate.append(tdir)

        sys_dir = root / "系统资源"
        if sys_dir.exists() and sys_dir.is_dir():
            for mem_name in ("save_dir_memory.json", "save_dir_memory.js", "reset_localstorage_token.js", "prefs_config.json", "prefs.json", "user_prefs.json"):
                mp = sys_dir / mem_name
                if mp.exists():
                    items_to_recycle.append(mp)

    if LEGACY_USER_CONFIG_PATH.exists():
        items_to_recycle.append(LEGACY_USER_CONFIG_PATH)

    return items_to_recycle, dirs_to_recreate


def perform_factory_reset_to_recycle_bin(interactive: bool = False) -> dict:
    items_to_recycle, dirs_to_recreate = collect_custom_and_cache_targets()
    moved_count, errors = send_paths_to_windows_recycle_bin(items_to_recycle)

    for d in dirs_to_recreate:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    reset_token = str(int(time.time() * 1000))
    scan_roots = [BASE_DIR] + [
        sub for sub in BASE_DIR.iterdir()
        if sub.is_dir() and not sub.name.startswith((".", "_")) and sub.name not in IGNORED_DIRS
    ]
    for r in scan_roots:
        if any((r / f).exists() for f in ("v5_pdf.html", "v5_1pdf.html", "水印盖章.html", "pdf_watermark_studio.html", "stamp_studio_backend.py")):
            sys_d = r / "系统资源"
            try:
                sys_d.mkdir(parents=True, exist_ok=True)
                (sys_d / "save_dir_memory.js").write_text(
                    "window.__XIXI_REMEMBERED_SAVE_DIR__ = {firstTimeCompleted: false, defaultSaveMode: '', defaultSaveDir: ''};",
                    encoding="utf-8",
                )
                (sys_d / "reset_localstorage_token.js").write_text(
                    f'window.__XIXI_FACTORY_RESET_TOKEN__ = "{reset_token}";\n',
                    encoding="utf-8",
                )
            except Exception:
                pass

    return {
        "ok": True,
        "movedCount": moved_count,
        "totalFound": len(items_to_recycle),
        "errors": errors,
        "msg": f"🎉 已恢复出厂默认状态！共将 {moved_count} 项自定义文件与缓存安全移入 Windows 回收站（bak/ 备份夹完好保留）。",
    }


def run_factory_reset_cli():
    print("=" * 72)
    print("  🧹 西西工具包 V4.0 · 一键恢复出厂初始默认状态 (安全移入 Windows 回收站)")
    print("=" * 72)
    print(f"  当前工具包根目录: {BASE_DIR}")
    items_to_recycle, _ = collect_custom_and_cache_targets()
    print("-" * 72)
    print("  即将清理并移入系统【回收站】的自定义内容与缓存范围：")
    print("    1. 缓存/            (启动器记忆 launcher_memory.json 等)")
    print("    2. 自定义样式/      (所有自建的水印样式 .json 文件)")
    print("    3. 自定义图片/      (所有导入的自定义印章/贴纸图片)")
    print("    4. 历史缓存/        (所有历史保存记录、撤回备份与偏好设置 prefs.json)")
    print("    5. 默认导出/        (默认导出目录中留存的测试或历史导出文件)")
    print("    6. 存储位置记忆     (save_dir_memory.json / 浏览器 localStorage 缓存)")
    print("    💡 保护项：bak/ 备份夹、工具/ 脚本夹、系统资源/ 静态图标与插件代码完好保留！")
    print("-" * 72)
    print(f"  📊 当前共扫描到 【{len(items_to_recycle)}】 项自定义文件/缓存待移入回收站。")
    if items_to_recycle:
        for idx, p in enumerate(items_to_recycle[:12], 1):
            try:
                rel = p.relative_to(BASE_DIR)
            except Exception:
                rel = p
            print(f"     - [{idx}] {rel}")
        if len(items_to_recycle) > 12:
            print(f"     ... 以及另外 {len(items_to_recycle) - 12} 个文件")
    print("=" * 72)

    try:
        ans1 = input("\n⚠️ 【第 1/2 次确认】确定要清空所有自定义内容与缓存并移入回收站吗？(输入 Y 回车继续，其他任意键取消): ").strip().upper()
    except Exception:
        ans1 = ""
    if ans1 != "Y":
        print("\n[已取消] 未做任何修改，您的所有自定义文件完好无损。")
        return

    print("\n" + "-" * 72)
    print("🚨 【第 2/2 次确认 · 最终确认】")
    print("   确认后，上述所有自定义样式、图片、缓存将立即移入 Windows 回收站，")
    print("   所有文件夹与首次打开存储位置提示都将回归最初始的出厂默认状态！")
    print("-" * 72)
    try:
        ans2 = input("👉 请输入 YES (或 Y) 并按回车执行最终重置: ").strip().upper()
    except Exception:
        ans2 = ""
    if ans2 not in ("Y", "YES"):
        print("\n[已取消] 未通过第二次确认，操作已安全中止。")
        return

    print("\n⏳ 正在将自定义内容与缓存安全移入 Windows 回收站并重建初始目录...")
    res = perform_factory_reset_to_recycle_bin(interactive=True)
    print("\n" + "=" * 72)
    print(f"  {res['msg']}")
    print("  💡 提示：如果误删了某张重要贴纸或样式，随时可以打开电脑桌面的【回收站】右键还原！")
    print("=" * 72)


CSHARP_NATIVE_STUB = r"""using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Windows.Forms;

[assembly: AssemblyTitle("西西工具包")]
[assembly: AssemblyProduct("西西工具包 Xixi Toolkit")]
[assembly: AssemblyDescription("西西工具包总控启动器 V4.0")]
[assembly: AssemblyVersion("4.0.0.0")]

class XixiLauncher {
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern int SetCurrentProcessExplicitAppUserModelID(string AppID);

    [STAThread]
    static void Main() {
        try {
            SetCurrentProcessExplicitAppUserModelID("XixiToolkit.Launcher.V4.0");
        } catch {}

        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string[] candidates = new string[] {
            Path.Combine(baseDir, "xixi_toolkit_launcher.py"),
            Path.Combine(baseDir, "系统资源", "xixi_toolkit_launcher.py"),
            Path.Combine(baseDir, "工具", "xixi_toolkit_launcher.py"),
            Path.Combine(baseDir, "资源", "xixi_toolkit_launcher.py")
        };

        string scriptPath = "";
        DateTime bestTime = DateTime.MinValue;
        foreach (string c in candidates) {
            if (File.Exists(c)) {
                DateTime t = File.GetLastWriteTimeUtc(c);
                if (scriptPath == "" || t > bestTime) {
                    scriptPath = c;
                    bestTime = t;
                }
            }
        }

        if (string.IsNullOrEmpty(scriptPath)) {
            MessageBox.Show("未在根目录或『系统资源/』下找到 xixi_toolkit_launcher.py！\n当前目录：" + baseDir, "🐾 西西工具包", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        string pyExe = FindPythonw();
        if (string.IsNullOrEmpty(pyExe)) {
            MessageBox.Show("未检测到 Python 环境！请先安装 Python 3.10+ 并勾选 Add Python to PATH。", "🐾 西西工具包", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = pyExe;
        psi.Arguments = "\"" + scriptPath + "\"";
        psi.WorkingDirectory = baseDir;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.EnvironmentVariables["XIXI_TOOLKIT_ROOT"] = baseDir;
        Process.Start(psi);
    }

    static string FindPythonw() {
        string[] names = new string[] { "pythonw.exe", "python.exe" };
        string pathEnv = Environment.GetEnvironmentVariable("PATH") ?? "";
        foreach (string p in pathEnv.Split(Path.PathSeparator)) {
            if (string.IsNullOrWhiteSpace(p)) continue;
            foreach (string n in names) {
                try {
                    string full = Path.Combine(p.Trim(), n);
                    if (File.Exists(full) && !full.Contains("WindowsApps")) return full;
                } catch {}
            }
        }
        string localApp = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
        string pyRoot = Path.Combine(localApp, "Programs", "Python");
        if (Directory.Exists(pyRoot)) {
            string[] dirs = Directory.GetDirectories(pyRoot, "Python3*");
            Array.Sort(dirs);
            Array.Reverse(dirs);
            foreach (string d in dirs) {
                string pw = Path.Combine(d, "pythonw.exe");
                if (File.Exists(pw)) return pw;
                string py = Path.Combine(d, "python.exe");
                if (File.Exists(py)) return py;
            }
        }
        return "pythonw.exe";
    }
}
"""


def silent_upgrade_native_exe_if_needed(ico_file: Path):
    """
    在 Windows 启动时，自动检测根目录下的 `西西工具包.exe` 是否已升级为支持多路径寻址的 V4.0 版本；
    若尚未升级且当前未占用，则调用系统自带 `csc.exe` 在后台 0.3 秒静默更新 `西西工具包.exe`。
    """
    if not sys.platform.startswith("win") or getattr(sys, "frozen", False):
        return
    ver_flag = SYS_RES_DIR / "exe_stub_version.txt"
    out_exe = BASE_DIR / "西西工具包.exe"
    if out_exe.exists() and ver_flag.exists():
        try:
            if ver_flag.read_text(encoding="utf-8").strip() == "4.0":
                return
        except Exception:
            pass
    try:
        sys_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
        csc_candidates = [
            sys_root / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe",
            sys_root / "Microsoft.NET" / "Framework" / "v4.0.30319" / "csc.exe",
        ]
        csc_path = next((p for p in csc_candidates if p.exists()), None)
        if not csc_path:
            return
        cs_file = CACHE_DIR / "_xixi_launcher_stub.cs"
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cs_file.write_text(CSHARP_NATIVE_STUB, encoding="utf-8-sig")
        cmd = [
            str(csc_path),
            "/nologo",
            "/target:winexe",
            f"/out:{out_exe}",
            "/r:System.Windows.Forms.dll",
            "/r:System.Drawing.dll",
            f"/win32icon:{ico_file.resolve()}",
            str(cs_file),
        ]
        proc = subprocess.run(cmd, cwd=str(BASE_DIR), capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
        cs_file.unlink(missing_ok=True)
        if proc.returncode == 0 and out_exe.exists():
            ver_flag.write_text("4.0", encoding="utf-8")
    except Exception:
        pass


def run_exe_builder_cli():
    ensure_standard_root_architecture(auto_migrate_files=False)
    ico_file = ensure_xixi_ico_exists()
    print("=" * 72)
    print("  🐾 西西工具包 · 一级目录总控 EXE 锻造台 V4.0 (支持根目录与系统资源双路径)")
    print("=" * 72)
    print(f"  工具包根目录: {BASE_DIR}")
    print(f"  专属图标路径: ✅ 系统资源/{ico_file.name} ({ico_file.stat().st_size // 1024} KB)")
    print("-" * 72)
    print("  [1] ⚡ 1秒生成【轻量原生版 西西工具包.exe】(自用首选：自动嵌 xixi_icon.ico 图标、0.05秒秒开)")
    print("  [2] 📦 PyInstaller 打包【独立环境版 西西工具包.exe】(分享首选：自动嵌 xixi_icon.ico 图标、免装Python)")
    print("-" * 72)

    clean_root_clutter()
    choice = "1"
    extra_args = [a for a in sys.argv[2:] if a in ("1", "2")]
    if extra_args:
        choice = extra_args[0]
    else:
        try:
            user_in = input("请输入数字 [1 或 2，直接回车默认选 1]: ").strip()
            if user_in in ("1", "2"):
                choice = user_in
        except Exception:
            choice = "1"

    out_exe = BASE_DIR / "西西工具包.exe"
    try:
        if out_exe.exists():
            out_exe.unlink()
    except Exception:
        pass

    if choice == "1":
        print("\n[1/3] 正在定位 Windows 系统自带 .NET 编译器 (csc.exe)...")
        sys_root = Path(os.environ.get("SystemRoot", "C:/Windows"))
        csc_candidates = [
            sys_root / "Microsoft.NET" / "Framework64" / "v4.0.30319" / "csc.exe",
            sys_root / "Microsoft.NET" / "Framework" / "v4.0.30319" / "csc.exe",
        ]
        csc_path = next((p for p in csc_candidates if p.exists()), None)
        if not csc_path:
            print("[!] 未找到 csc.exe，自动为您切换为模式 [2] PyInstaller 打包...")
            choice = "2"
        else:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cs_file = CACHE_DIR / "_xixi_launcher_stub.cs"
            cs_file.write_text(CSHARP_NATIVE_STUB, encoding="utf-8-sig")
            cmd = [
                str(csc_path),
                "/nologo",
                "/target:winexe",
                f"/out:{out_exe}",
                "/r:System.Windows.Forms.dll",
                "/r:System.Drawing.dll",
                f"/win32icon:{ico_file.resolve()}",
                str(cs_file),
            ]
            print(f"[2/3] 正在编译原生【西西工具包.exe】并嵌入图标 (系统资源/{ico_file.name})...")
            proc = subprocess.run(cmd, cwd=str(BASE_DIR))
            try:
                cs_file.unlink(missing_ok=True)
            except Exception:
                pass
            if proc.returncode == 0 and out_exe.exists():
                try:
                    (SYS_RES_DIR / "exe_stub_version.txt").write_text("4.0", encoding="utf-8")
                except Exception:
                    pass
                print("[3/3] 正在刷新 Windows 图标缓存...")
                refresh_windows_icon_cache(out_exe)
                print("\n" + "=" * 72)
                print("  🎉 恭喜绮绮！【西西工具包.exe】(V4.0 轻量原生版 + 西西Q版图标) 已在 1 秒内生成完毕！")
                print(f"  📍 路径: {out_exe}")
                print(f"  🎨 图标: {ico_file.resolve()}")
                print("=" * 72)
                return
            else:
                print("[!] csc.exe 编译未成功，自动切换为模式 [2] PyInstaller 打包...")
                choice = "2"

    if choice == "2":
        print("\n[1/3] 正在检测 PyInstaller 打包组件...")
        py_bin = find_system_python(gui_mode=False)
        chk = subprocess.run([py_bin, "-m", "PyInstaller", "--version"], capture_output=True)
        if chk.returncode != 0:
            print("      正在通过清华镜像源自动安装 pyinstaller...")
            subprocess.run([
                py_bin, "-m", "pip", "install", "pyinstaller", "pillow", "pywebview",
                "-i", TSINGHUA_MIRROR, "--trusted-host", "pypi.tuna.tsinghua.edu.cn"
            ])
        print(f"[2/3] 正在打包【西西工具包.exe】并嵌入图标 (系统资源/{ico_file.name})...")
        launcher_script = Path(__file__).resolve()
        cmd = [
            py_bin, "-m", "PyInstaller",
            "--noconfirm", "--clean", "--onefile", "--windowed",
            "--name", "西西工具包",
            f"--icon={ico_file.resolve()}",
            f"--add-data={ico_file.resolve()}{os.pathsep}.",
            "--distpath", str(BASE_DIR),
            "--workpath", str(Path(tempfile.gettempdir()) / "xixi_pyi_build" / "_work"),
            "--specpath", str(Path(tempfile.gettempdir()) / "xixi_pyi_build" / "_spec"),
            str(launcher_script),
        ]
        proc = subprocess.run(cmd, cwd=str(BASE_DIR))
        print("[3/3] 正在清理临时缓存目录并刷新 Windows 图标缓存...")
        shutil.rmtree(Path(tempfile.gettempdir()) / "xixi_pyi_build", ignore_errors=True)
        clean_root_clutter()
        refresh_windows_icon_cache(out_exe)
        if proc.returncode == 0 and out_exe.exists():
            print("\n" + "=" * 72)
            print("  🎉 恭喜绮绮！【西西工具包.exe】(独立环境版 + 西西Q版图标) 已打包完成！")
            print(f"  📍 路径: {out_exe}")
            print(f"  🎨 图标: {ico_file.resolve()}")
            print("=" * 72)


def clean_root_clutter():
    """清理根目录可能残留的 build 临时编译目录与 .cs/.spec 文件"""
    try:
        build_dir = BASE_DIR / "build"
        if build_dir.exists() and build_dir.is_dir():
            shutil.rmtree(build_dir, ignore_errors=True)
        for tmp_name in ("_xixi_launcher_stub.cs", "西西工具包.spec", "xixi_toolkit_launcher.spec"):
            tp = BASE_DIR / tmp_name
            if tp.exists() and tp.is_file():
                tp.unlink(missing_ok=True)
    except Exception:
        pass


def main():
    ensure_standard_root_architecture(auto_migrate_files=False)
    ico_file = ensure_xixi_ico_exists()
    silent_upgrade_native_exe_if_needed(ico_file)

    # 同步备份当前启动器脚本到 系统资源/xixi_toolkit_launcher.py，以便根目录或系统资源双路径均可启动
    try:
        cur_py = Path(__file__).resolve()
        sys_py = SYS_RES_DIR / "xixi_toolkit_launcher.py"
        if cur_py.exists() and cur_py.name == "xixi_toolkit_launcher.py" and cur_py != sys_py.resolve():
            shutil.copy2(str(cur_py), str(sys_py))
    except Exception:
        pass

    if sys.platform.startswith("win"):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("XixiToolkit.Launcher.V4.0")
        except Exception:
            pass

    try:
        import webview
    except ImportError:
        res = install_missing_packages(["pywebview>=4.0.0"])
        if res.get("ok"):
            try:
                import webview
            except ImportError:
                webview = None
        else:
            webview = None

        if webview is None:
            if tk and messagebox:
                root = tk.Tk()
                root.withdraw()
                messagebox.showerror(
                    "缺少依赖库 pywebview",
                    "自动安装 pywebview 失败，请双击运行「直接启动.bat」或在命令行执行：\n\npip install pywebview -i https://pypi.tuna.tsinghua.edu.cn/simple",
                )
            return

    window_holder = {"win": None}
    bridge = XixiNativeBridge(lambda: window_holder["win"])

    win = webview.create_window(
        "🐾 西西工具包",
        html=LAUNCHER_HUB_HTML,
        js_api=bridge,
        width=HUB_WIDTH,
        height=HUB_HEIGHT,
        min_size=(800, 520),
    )

    def on_page_loaded():
        apply_win32_window_icon(win.title if hasattr(win, "title") else "🐾 西西工具包", ico_file)
        if not bridge._in_hub:
            try:
                win.evaluate_js(AUTO_BACK_BUTTON_JS)
            except Exception:
                pass

    try:
        win.events.loaded += on_page_loaded
    except Exception:
        pass

    window_holder["win"] = win
    apply_win32_window_icon("🐾 西西工具包", ico_file)
    try:
        webview.start(debug=False, private_mode=False, icon=str(ico_file) if ico_file.exists() else None)
    except TypeError:
        try:
            webview.start(debug=False, private_mode=False)
        except TypeError:
            webview.start(debug=False)


def _boot_entry():
    clean_root_clutter()
    if "--build-exe" in sys.argv:
        run_exe_builder_cli()
        return

    if "--factory-reset" in sys.argv:
        run_factory_reset_cli()
        return

    if "--repair-scripts" in sys.argv:
        ensure_standard_root_architecture(auto_migrate_files=True)
        repaired = sync_and_repair_all_helper_scripts()
        print("✅ 已同步并修复所有跨文件夹 .bat 辅助脚本与 .gitignore！", repaired)
        return

    # 【核心黑科技：PyInstaller EXE 免重打热更新引擎（同时支持根目录与 系统资源/ 下的最新 .py）】
    if getattr(sys, "frozen", False) and not os.environ.get("XIXI_HOT_OVERRIDDEN"):
        candidates = [
            BASE_DIR / "xixi_toolkit_launcher.py",
            SYS_RES_DIR / "xixi_toolkit_launcher.py",
        ]
        existing_cands = [c for c in candidates if c.exists() and c.is_file()]
        if existing_cands:
            existing_cands.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            ext_py = existing_cands[0]
            try:
                os.environ["XIXI_HOT_OVERRIDDEN"] = "1"
                code_str = ext_py.read_text(encoding="utf-8")
                g_dict = dict(globals())
                g_dict["__file__"] = str(ext_py)
                g_dict["__name__"] = "__main__"
                exec(compile(code_str, str(ext_py), "exec"), g_dict)
                return
            except Exception:
                pass

    main()


if __name__ == "__main__":
    _boot_entry()
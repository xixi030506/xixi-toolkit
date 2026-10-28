#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧩 新插件专属后台标准模板 (template_backend.py)
================================================================================
使用方法：
1. 复制 `_新插件标准模板_复制改名` 文件夹，改名为你的新插件名（去掉开头的 `_`，例如 `西西图片工坊`）；
2. 总控启动器 `xixi_toolkit_launcher.py` 会在打开该插件时，自动扫描文件夹下的 `*_backend.py`，
   并自动加载其中以 `Backend` 结尾的类！
"""

from pathlib import Path


class TemplatePluginBackend:
    """新插件专属后台类（类名请保持以 Backend 结尾）"""

    def __init__(self, plugin_dir: Path):
        self._active_plugin_dir = Path(plugin_dir).resolve()
        self._ensure_subfolders()

    def set_plugin_dir(self, plugin_dir: Path):
        self._active_plugin_dir = Path(plugin_dir).resolve()
        self._ensure_subfolders()

    def _ensure_subfolders(self):
        for name in ("系统资源", "历史缓存", "默认导出"):
            (self._active_plugin_dir / name).mkdir(parents=True, exist_ok=True)

    def get_plugin_init_data(self):
        """前端页面加载时可通过 window.pywebview.api.get_plugin_init_data() 调用"""
        return {
            "ok": True,
            "pluginDir": str(self._active_plugin_dir),
            "message": "🎉 欢迎使用西西新插件标准模板！前后端已成功连通！",
        }

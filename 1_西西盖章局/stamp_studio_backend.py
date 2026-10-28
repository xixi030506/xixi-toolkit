#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌸 西西盖章局 · 专属后台服务模块 (stamp_studio_backend.py)
================================================================================
放置位置：请将本文件放在 `D:\\西西工具包\\西西盖章局\\` 文件夹内（与 `v5_pdf.html` 或 `pdf_watermark_studio.html` 同级）。
作用说明：
  由总控启动器 `xixi_toolkit_launcher.py` 动态加载引用，专门负责「西西盖章局」插件的：
  1. 同级五大固定子文件夹自动初始化与读写：
     - `系统资源/`：存放预设演示 PDF（《西西盖章局_功能说明与演示样板.pdf》）及内置印章矢量图标资源
     - `自定义图片/`：存放用户收藏的贴纸与印章图片
     - `自定义样式/`：存放本软件导出的专属水印样式文件 (.json)
     - `历史缓存/`：存放插件调教参数 (`prefs_config.json`)、历史记录 (`history.json`) 与防覆盖备份 (`backups/`)
     - `默认导出/`：同级默认导出目录选项
  2. 原生文件选择、零弹窗批量保存、资源管理器高亮直达 (`explorer /select`) 与历史撤回/恢复。
"""

import base64
import datetime
import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import filedialog
except ImportError:
    tk = None
    filedialog = None


DEFAULT_PAW_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120">
  <circle cx="60" cy="60" r="54" fill="none" stroke="#F43F5E" stroke-width="5" stroke-dasharray="8 5"/>
  <circle cx="60" cy="60" r="46" fill="#F43F5E" fill-opacity="0.14" stroke="#F43F5E" stroke-width="2.5"/>
  <ellipse cx="60" cy="72" rx="20" ry="16" fill="#F43F5E"/>
  <ellipse cx="36" cy="48" rx="8" ry="11" transform="rotate(-20 36 48)" fill="#F43F5E"/>
  <ellipse cx="51" cy="40" rx="8" ry="11" transform="rotate(-6 51 40)" fill="#F43F5E"/>
  <ellipse cx="69" cy="40" rx="8" ry="11" transform="rotate(6 69 40)" fill="#F43F5E"/>
  <ellipse cx="84" cy="48" rx="8" ry="11" transform="rotate(20 84 48)" fill="#F43F5E"/>
</svg>"""


class StampStudioBackend:
    """西西盖章局插件专属后台逻辑（与总控启动器彻底解耦）"""

    DEMO_PDF_FILENAME = "西西盖章局_功能说明与演示样板.pdf"

    def __init__(self, plugin_dir: Path):
        self._active_plugin_dir = Path(plugin_dir).resolve()
        self._last_source_dir = str(self._active_plugin_dir)
        self._ensure_plugin_subfolders()

    def set_plugin_dir(self, plugin_dir: Path):
        """切换或更新当前盖章局插件所在目录"""
        self._active_plugin_dir = Path(plugin_dir).resolve()
        self._ensure_plugin_subfolders()

    def _ensure_plugin_subfolders(self) -> dict[str, Path]:
        """
        确保西西盖章局同级目录下的 5 个标准固定子文件夹存在：
        - 系统资源/ (存放预设 PDF 演示文档与内置图标资源)
        - 自定义图片/
        - 自定义样式/
        - 历史缓存/ (含 backups/)
        - 默认导出/
        """
        pdir = self._active_plugin_dir
        res_dir = pdir / "系统资源"
        img_dir = pdir / "自定义图片"
        style_dir = pdir / "自定义样式"
        cache_dir = pdir / "历史缓存"
        backups_dir = cache_dir / "backups"
        export_dir = pdir / "默认导出"
        for d in (res_dir, img_dir, style_dir, cache_dir, backups_dir, export_dir):
            try:
                d.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        paw_file = res_dir / "默认猫爪章.svg"
        if not paw_file.exists():
            try:
                paw_file.write_text(DEFAULT_PAW_SVG, encoding="utf-8")
            except Exception:
                pass
        return {
            "plugin": pdir,
            "resources": res_dir,
            "images": img_dir,
            "styles": style_dir,
            "cache": cache_dir,
            "backups": backups_dir,
            "export": export_dir,
        }

    def _prefs_file(self) -> Path:
        return self._ensure_plugin_subfolders()["cache"] / "prefs_config.json"

    def _history_file(self) -> Path:
        return self._ensure_plugin_subfolders()["cache"] / "history.json"

    def _load_plugin_prefs_raw(self) -> dict:
        pf = self._prefs_file()
        if not pf.exists():
            return {}
        try:
            data = json.loads(pf.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _save_plugin_prefs_raw(self, data: dict):
        pf = self._prefs_file()
        try:
            pf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_history_list(self) -> list[dict]:
        hf = self._history_file()
        if not hf.exists():
            return []
        try:
            data = json.loads(hf.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def _save_history_list(self, records: list[dict]):
        hf = self._history_file()
        try:
            hf.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def ensure_system_resources(self, demo_pdf_b64: str = "", mascot_svg: str = ""):
        """
        将前端合成的高清 2 页版《西西盖章局_功能说明与演示样板.pdf》及内置图标同步写入同级 `系统资源/` 文件夹，
        方便随时在 `西西盖章局/系统资源/` 中查看或引用预设 PDF 与内置图像资源。
        """
        dirs = self._ensure_plugin_subfolders()
        res_dir = dirs["resources"]
        demo_pdf_path = res_dir / self.DEMO_PDF_FILENAME
        if demo_pdf_b64:
            try:
                demo_pdf_path.write_bytes(base64.b64decode(demo_pdf_b64))
            except Exception:
                pass
        if mascot_svg:
            mascot_path = res_dir / "吉祥物小猫.svg"
            if not mascot_path.exists():
                try:
                    mascot_path.write_text(mascot_svg, encoding="utf-8")
                except Exception:
                    pass
        return {
            "ok": True,
            "resourcesDir": str(res_dir.resolve()),
            "demoPdfPath": str(demo_pdf_path.resolve()) if demo_pdf_path.exists() else "",
        }

    def get_plugin_init_data(self):
        """
        插件启动时一次性拉取：
        - 同级固定子文件夹路径 (`系统资源`, `自定义图片`, `自定义样式`, `历史缓存`, `默认导出`)
        - `历史缓存/prefs_config.json` 中保存的所有插件参数与默认存储位置
        - 是否需要弹出初次进入的「选择默认保存位置」全屏引导框 (`needsFirstTimeSetup`)
        - `自定义图片/` 中的全部贴纸图片
        - `自定义样式/` 中的全部自定义样式
        - `历史缓存/history.json` 中的全部历史记录
        """
        dirs = self._ensure_plugin_subfolders()
        prefs = self._load_plugin_prefs_raw()

        default_export_dir = str(dirs["export"].resolve())
        default_save_dir = prefs.get("defaultSaveDir", "").strip()
        default_save_mode = prefs.get("defaultSaveMode", "")

        if default_save_mode == "downloads":
            default_save_mode = "plugin_export"
            default_save_dir = default_export_dir
            prefs["defaultSaveMode"] = default_save_mode
            prefs["defaultSaveDir"] = default_save_dir

        first_run_completed = bool(prefs.get("firstRunCompleted", False) and default_save_dir)

        demo_pdf_file = dirs["resources"] / self.DEMO_PDF_FILENAME
        demo_pdf_b64 = ""
        if demo_pdf_file.exists() and demo_pdf_file.is_file():
            try:
                demo_pdf_b64 = base64.b64encode(demo_pdf_file.read_bytes()).decode("ascii")
            except Exception:
                demo_pdf_b64 = ""

        return {
            "ok": True,
            "pluginDir": str(dirs["plugin"].resolve()),
            "resourcesSubfolder": str(dirs["resources"].resolve()),
            "imagesSubfolder": str(dirs["images"].resolve()),
            "stylesSubfolder": str(dirs["styles"].resolve()),
            "cacheSubfolder": str(dirs["cache"].resolve()),
            "defaultExportSubfolder": default_export_dir,
            "presetDemoPdfPath": str(demo_pdf_file.resolve()),
            "presetDemoPdfBase64": demo_pdf_b64,
            "needsFirstTimeSetup": not first_run_completed,
            "defaultSaveDir": default_save_dir or default_export_dir,
            "defaultSaveMode": default_save_mode or "plugin_export",
            "prefs": prefs,
            "images": self.list_subfolder_images(),
            "styles": self.list_subfolder_styles(),
            "history": self.get_save_history(),
        }

    def save_plugin_prefs(self, prefs_dict: dict):
        """将插件内的调教参数、方案①②③、后缀设置等实时写入 `历史缓存/prefs_config.json`"""
        if not isinstance(prefs_dict, dict):
            return {"ok": False}
        current = self._load_plugin_prefs_raw()
        current.update(prefs_dict)
        self._save_plugin_prefs_raw(current)
        return {"ok": True}

    def set_default_save_dir(self, mode: str, custom_path: str = ""):
        """
        设置默认保存位置并持久化到 `历史缓存/prefs_config.json`
        mode 取值（已移除不同电脑路径不一的 Downloads 项）：
        - 'custom_dir': 用户自选的具体文件夹路径
        - 'plugin_export': 同级「默认导出」子文件夹
        - 'source_dir': 各文件原所在目录（散落存回原文件旁）
        """
        dirs = self._ensure_plugin_subfolders()
        prefs = self._load_plugin_prefs_raw()

        if mode == "plugin_export":
            target_dir = str(dirs["export"].resolve())
        elif mode == "source_dir":
            target_dir = "@SOURCE_DIR"
        else:
            mode = "custom_dir"
            if custom_path:
                p = Path(custom_path).resolve()
                try:
                    p.mkdir(parents=True, exist_ok=True)
                except Exception:
                    pass
                target_dir = str(p)
            else:
                target_dir = str(dirs["export"].resolve())

        prefs["defaultSaveMode"] = mode
        prefs["defaultSaveDir"] = target_dir
        prefs["firstRunCompleted"] = True
        self._save_plugin_prefs_raw(prefs)
        return {
            "ok": True,
            "defaultSaveMode": mode,
            "defaultSaveDir": target_dir,
        }

    def pick_default_save_dir(self):
        """弹出 Windows 原生文件夹选择框，让用户自由挑选默认保存文件夹"""
        prefs = self._load_plugin_prefs_raw()
        cur_dir = prefs.get("defaultSaveDir", "")
        init_dir = str(self._active_plugin_dir)
        if cur_dir and cur_dir != "@SOURCE_DIR" and Path(cur_dir).exists():
            init_dir = cur_dir

        if not tk or not filedialog:
            return {"ok": False}

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen = filedialog.askdirectory(
            title="请选择默认保存文件夹（之后点快速保存将直接存到此目录）",
            initialdir=init_dir,
            mustexist=False,
        )
        root.destroy()
        if not chosen:
            return {"ok": False}

        p = Path(chosen).resolve()
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return self.set_default_save_dir("custom_dir", str(p))

    def list_subfolder_images(self) -> list[dict]:
        """直接读取同级固定子文件夹 `自定义图片/` 下的所有贴纸图片"""
        img_dir = self._ensure_plugin_subfolders()["images"]
        out = []
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".gif": "image/gif",
        }
        try:
            files = sorted(
                [f for f in img_dir.iterdir() if f.is_file() and f.suffix.lower() in mime_map],
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )
            for f in files:
                mime = mime_map[f.suffix.lower()]
                b64 = base64.b64encode(f.read_bytes()).decode("ascii")
                out.append(
                    {
                        "name": f.name,
                        "path": str(f.resolve()),
                        "dataUrl": f"data:{mime};base64,{b64}",
                    }
                )
        except Exception:
            pass
        return out

    def save_subfolder_image(self, file_name: str, b64_data: str):
        """直接将贴纸图片写入同级固定子文件夹 `自定义图片/`"""
        img_dir = self._ensure_plugin_subfolders()["images"]
        safe_name = Path(file_name or "西西贴纸.png").name
        if not any(safe_name.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg")):
            safe_name += ".png"
        out_path = img_dir / safe_name
        out_path.write_bytes(base64.b64decode(b64_data))
        return {
            "ok": True,
            "name": safe_name,
            "path": str(out_path.resolve()),
            "images": self.list_subfolder_images(),
        }

    def delete_subfolder_image(self, file_name: str):
        """从同级固定子文件夹 `自定义图片/` 中删除指定贴纸"""
        img_dir = self._ensure_plugin_subfolders()["images"]
        target = img_dir / Path(file_name).name
        try:
            if target.exists() and target.is_file():
                target.unlink()
        except Exception:
            pass
        return {"ok": True, "images": self.list_subfolder_images()}

    def list_subfolder_styles(self) -> list[dict]:
        """直接读取同级固定子文件夹 `自定义样式/` 下由本软件导出的 JSON 样式文件"""
        style_dir = self._ensure_plugin_subfolders()["styles"]
        loaded_map = {}
        lib_file = style_dir / "西西自定义样式库.json"
        if lib_file.exists():
            try:
                data = json.loads(lib_file.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("stickers"), list):
                    for st in data["stickers"]:
                        if isinstance(st, dict) and st.get("name") and isinstance(st.get("snapshot"), dict):
                            loaded_map[st["name"]] = st
            except Exception:
                pass
        try:
            files = sorted(
                [f for f in style_dir.iterdir() if f.is_file() and f.suffix.lower() == ".json" and f.name != "西西自定义样式库.json"],
                key=lambda x: x.stat().st_mtime,
                reverse=False,
            )
            for f in files:
                try:
                    parsed = json.loads(f.read_text(encoding="utf-8"))
                    if isinstance(parsed, dict) and isinstance(parsed.get("snapshot"), dict):
                        st_name = parsed.get("name") or f"📌 {f.stem}"
                        loaded_map[st_name] = {
                            "id": parsed.get("id") or f"stk_{f.stem}",
                            "name": st_name,
                            "snapshot": parsed["snapshot"],
                        }
                except Exception:
                    pass
        except Exception:
            pass
        return list(loaded_map.values())

    def save_subfolder_styles(self, stickers_list: list, single_sticker: dict | None = None):
        """
        当用户点击第二个按钮「💾 存到『自定义样式』夹」时，将样式写入同级固定子文件夹 `自定义样式/`。
        （注：界面上点击贴纸的 × 仅移除软件内当前会话的贴纸，绝不调用删除外部文件夹内样式的操作）
        """
        style_dir = self._ensure_plugin_subfolders()["styles"]
        lib_file = style_dir / "西西自定义样式库.json"
        try:
            existing_styles = {st["name"]: st for st in self.list_subfolder_styles() if isinstance(st, dict) and st.get("name")}
            if isinstance(stickers_list, list):
                for st in stickers_list:
                    if isinstance(st, dict) and st.get("name") and isinstance(st.get("snapshot"), dict):
                        existing_styles[st["name"]] = st
            if isinstance(single_sticker, dict) and single_sticker.get("name") and isinstance(single_sticker.get("snapshot"), dict):
                existing_styles[single_sticker["name"]] = single_sticker

            merged_list = list(existing_styles.values())
            lib_file.write_text(
                json.dumps(
                    {
                        "app": "西西盖章局 V5",
                        "format": "xixi_stamp_style_v5",
                        "updatedAt": datetime.datetime.now().isoformat(),
                        "stickers": merged_list,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            to_write = [single_sticker] if isinstance(single_sticker, dict) else (stickers_list if isinstance(stickers_list, list) else [])
            for st in to_write:
                if not isinstance(st, dict) or not st.get("snapshot"):
                    continue
                raw_name = str(st.get("name", "西西样式")).replace("📌", "").replace("✨", "").strip()
                safe_stem = "".join(c if c not in r'\/:*?"<>|' else "_" for c in raw_name) or "西西自定义样式"
                single_file = style_dir / (safe_stem if safe_stem.endswith(".json") else f"{safe_stem}.json")
                single_file.write_text(
                    json.dumps(
                        {
                            "app": "西西盖章局 V5",
                            "format": "xixi_stamp_style_v5",
                            "id": st.get("id", ""),
                            "name": st.get("name", safe_stem),
                            "snapshot": st.get("snapshot"),
                            "savedAt": datetime.datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
        except Exception as e:
            return {"ok": False, "msg": str(e)}
        return {"ok": True, "path": str(style_dir.resolve()), "styles": self.list_subfolder_styles()}

    def pick_input_files(self):
        """调用原生 Windows 文件选择框挑选 PDF / Word 文件，并连同真实绝对路径一并返回给前端"""
        if not tk or not filedialog:
            return []
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        file_paths = filedialog.askopenfilenames(
            title="选择要盖章的 PDF 或 Word (.docx) 文件",
            initialdir=self._last_source_dir,
            filetypes=[
                ("PDF 与 Word 文档", "*.pdf *.docx"),
                ("PDF 文档", "*.pdf"),
                ("Word 文档", "*.docx"),
            ],
        )
        root.destroy()
        if not file_paths:
            return []

        results = []
        for fp in file_paths:
            p = Path(fp)
            if p.exists() and p.is_file():
                self._last_source_dir = str(p.parent)
                raw_bytes = p.read_bytes()
                results.append(
                    {
                        "name": p.name,
                        "path": str(p.resolve()),
                        "base64": base64.b64encode(raw_bytes).decode("ascii"),
                    }
                )
        return results

    def _write_file_and_record_history(
        self,
        out_path: Path,
        raw_bytes: bytes,
        original_name: str = "",
        profile_label: str = "",
        is_zip: bool = False,
        save_mode_label: str = "",
    ) -> dict:
        """
        核心安全存盘函数：
        1. 若目标路径 `out_path` 已存在文件（例如开启了「🚫 无后缀」覆盖原文件），先将原文件备份到 `历史缓存/backups/orig_<id>_<name>`；
        2. 将本次生成的水印文件写入 `out_path`，同时在 `历史缓存/backups/gen_<id>_<name>` 保存一份缓存副本（供日后随时「🔄 恢复」）；
        3. 将记录追加到 `历史缓存/history.json` 并返回该条历史记录对象。
        """
        dirs = self._ensure_plugin_subfolders()
        backups_dir = dirs["backups"]
        out_path.parent.mkdir(parents=True, exist_ok=True)

        rec_id = f"his_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        safe_fname = out_path.name
        overwrote_orig_backup = ""

        if out_path.exists() and out_path.is_file():
            orig_backup_name = f"orig_{rec_id}_{safe_fname}"
            try:
                shutil.copy2(str(out_path), str(backups_dir / orig_backup_name))
                overwrote_orig_backup = orig_backup_name
            except Exception:
                pass

        out_path.write_bytes(raw_bytes)

        gen_backup_name = f"gen_{rec_id}_{safe_fname}"
        try:
            (backups_dir / gen_backup_name).write_bytes(raw_bytes)
        except Exception:
            gen_backup_name = ""

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "id": rec_id,
            "fileName": safe_fname,
            "originalName": original_name or safe_fname,
            "savedPath": str(out_path.resolve()),
            "dirPath": str(out_path.parent.resolve()),
            "timestamp": now_str,
            "status": "saved",
            "genBackupName": gen_backup_name,
            "origBackupName": overwrote_orig_backup,
            "profileLabel": profile_label,
            "isZip": bool(is_zip),
            "saveModeLabel": save_mode_label,
        }

        history = self._load_history_list()
        history.insert(0, record)
        self._save_history_list(history)
        return record

    def save_batch_to_default_dir(self, items: list):
        """
        【⚡ 快速保存 (默认文件夹)】：
        零弹窗！直接根据用户设定的默认存储位置（自定义默认目录 / 同级默认导出 / 原文件所在目录）批量写入文件，并记录到历史缓存。
        """
        if not items:
            return {"ok": False, "records": []}

        dirs = self._ensure_plugin_subfolders()
        prefs = self._load_plugin_prefs_raw()
        mode = prefs.get("defaultSaveMode", "plugin_export")
        default_dir_str = prefs.get("defaultSaveDir", str(dirs["export"].resolve()))

        created_records = []
        for item in items:
            file_name = item.get("fileName", "watermarked.pdf")
            orig_name = item.get("originalName", file_name)
            b64_data = item.get("base64", "")
            src_path = item.get("sourcePath", "")
            profile_label = item.get("profileLabel", "")
            is_zip = bool(item.get("isZip", False))

            if not b64_data:
                continue

            if mode == "source_dir" or default_dir_str == "@SOURCE_DIR":
                if src_path and Path(src_path).parent.exists():
                    target_dir = Path(src_path).parent
                elif self._last_source_dir and Path(self._last_source_dir).exists():
                    target_dir = Path(self._last_source_dir)
                else:
                    target_dir = dirs["export"]
            elif mode == "plugin_export":
                target_dir = dirs["export"]
            else:
                target_dir = Path(default_dir_str) if default_dir_str else dirs["export"]

            out_path = target_dir / file_name
            raw_bytes = base64.b64decode(b64_data)
            rec = self._write_file_and_record_history(
                out_path=out_path,
                raw_bytes=raw_bytes,
                original_name=orig_name,
                profile_label=profile_label,
                is_zip=is_zip,
                save_mode_label="快速保存(默认位置)",
            )
            created_records.append(rec)

        return {
            "ok": True,
            "records": created_records,
            "history": self.get_save_history(),
        }

    def save_batch_custom_dir(self, items: list):
        """
        【📂 自定义位置（批量保存）】：
        调用 Windows 原生文件夹选择框，将所有文件批量写入用户所选目录并记入历史缓存。
        """
        if not items or not tk or not filedialog:
            return {"ok": False, "records": []}

        prefs = self._load_plugin_prefs_raw()
        init_dir = prefs.get("defaultSaveDir", "")
        if not init_dir or init_dir == "@SOURCE_DIR" or not Path(init_dir).exists():
            init_dir = self._last_source_dir if Path(self._last_source_dir).exists() else str(self._active_plugin_dir)

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        chosen_dir = filedialog.askdirectory(
            title="选择批量保存的目标文件夹",
            initialdir=init_dir,
            mustexist=False,
        )
        root.destroy()
        if not chosen_dir:
            return {"ok": False, "cancelled": True}

        target_dir = Path(chosen_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        self._last_source_dir = str(target_dir)

        created_records = []
        for item in items:
            file_name = item.get("fileName", "watermarked.pdf")
            orig_name = item.get("originalName", file_name)
            b64_data = item.get("base64", "")
            profile_label = item.get("profileLabel", "")
            is_zip = bool(item.get("isZip", False))
            if not b64_data:
                continue
            out_path = target_dir / file_name
            raw_bytes = base64.b64decode(b64_data)
            rec = self._write_file_and_record_history(
                out_path=out_path,
                raw_bytes=raw_bytes,
                original_name=orig_name,
                profile_label=profile_label,
                is_zip=is_zip,
                save_mode_label="自定义位置保存",
            )
            created_records.append(rec)

        return {
            "ok": True,
            "dir": str(target_dir),
            "records": created_records,
            "history": self.get_save_history(),
        }

    def save_single_dialog(
        self,
        source_path: str,
        suggested_name: str,
        b64_data: str,
        original_name: str = "",
        profile_label: str = "",
    ):
        """
        【📂 单独保存 / ZIP 自定义位置另存为】：
        打开 Windows 原生文件保存窗口，保存后自动记入 `历史缓存/history.json`。
        """
        prefs = self._load_plugin_prefs_raw()
        default_dir = prefs.get("defaultSaveDir", "")
        if source_path and Path(source_path).parent.exists():
            init_dir = str(Path(source_path).parent)
        elif default_dir and default_dir != "@SOURCE_DIR" and Path(default_dir).exists():
            init_dir = default_dir
        elif self._last_source_dir and Path(self._last_source_dir).exists():
            init_dir = self._last_source_dir
        else:
            init_dir = str(self._active_plugin_dir)

        lower_name = suggested_name.lower()
        if lower_name.endswith(".docx"):
            def_ext = ".docx"
            filetypes = [("Word 文档 (.docx)", "*.docx"), ("所有文件", "*.*")]
        elif lower_name.endswith(".zip"):
            def_ext = ".zip"
            filetypes = [("ZIP 压缩包 (.zip)", "*.zip"), ("所有文件", "*.*")]
        else:
            def_ext = ".pdf"
            filetypes = [("PDF 文档 (.pdf)", "*.pdf"), ("所有文件", "*.*")]

        if not tk or not filedialog:
            return {"ok": False}

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        save_path = filedialog.asksaveasfilename(
            title="选择保存位置",
            initialdir=init_dir,
            initialfile=suggested_name,
            defaultextension=def_ext,
            filetypes=filetypes,
        )
        root.destroy()

        if not save_path:
            return {"ok": False, "cancelled": True}

        out_p = Path(save_path).resolve()
        raw_bytes = base64.b64decode(b64_data)
        self._last_source_dir = str(out_p.parent)

        rec = self._write_file_and_record_history(
            out_path=out_p,
            raw_bytes=raw_bytes,
            original_name=original_name or suggested_name,
            profile_label=profile_label,
            is_zip=lower_name.endswith(".zip"),
            save_mode_label="单独另存为",
        )
        return {
            "ok": True,
            "savedPath": str(out_p),
            "record": rec,
            "history": self.get_save_history(),
        }

    def quick_save_to_source(self, items):
        """兼容接口：转发至 save_batch_to_default_dir"""
        res = self.save_batch_to_default_dir(items)
        saved_paths = [r["savedPath"] for r in res.get("records", [])]
        return {
            "ok": res.get("ok", False),
            "count": len(saved_paths),
            "savedPaths": saved_paths,
            "records": res.get("records", []),
            "history": res.get("history", []),
        }

    def get_save_history(self) -> list[dict]:
        """获取全部持久化历史记录，并实时校验磁盘文件是否存在"""
        records = self._load_history_list()
        for rec in records:
            sp = rec.get("savedPath", "")
            rec["fileExists"] = bool(sp and Path(sp).exists())
        return records

    def reveal_in_explorer(self, target_path: str):
        """
        【📂 点击直达】：
        直接唤起真实的 Windows 资源管理器 (`explorer.exe /select,"路径"`) 并高亮选中该文件！
        """
        if not target_path:
            return {"ok": False, "msg": "路径为空"}
        p = Path(target_path)
        try:
            if sys.platform.startswith("win"):
                if p.exists() and p.is_file():
                    subprocess.Popen(["explorer", f"/select,{str(p.resolve())}"])
                    return {"ok": True}
                elif p.exists() and p.is_dir():
                    os.startfile(str(p.resolve()))
                    return {"ok": True}
                elif p.parent.exists():
                    os.startfile(str(p.parent.resolve()))
                    return {"ok": True, "msg": "该文件已被移动或撤回，已为您打开其所在文件夹"}
            else:
                target_dir = p if p.is_dir() else p.parent
                if target_dir.exists():
                    subprocess.Popen(["xdg-open", str(target_dir)])
                    return {"ok": True}
        except Exception as e:
            return {"ok": False, "msg": str(e)}
        return {"ok": False, "msg": "目标路径不存在"}

    def open_folder(self, dir_path: str):
        """在 Windows 资源管理器中打开指定文件夹"""
        return self.reveal_in_explorer(dir_path)

    def revoke_history_item(self, record_id: str):
        """
        【↩️ 撤回】：
        从磁盘物理删除该次导出的文件；
        如果当初保存时覆盖了同名原文件（例如开启了「🚫 无后缀」），自动从 `历史缓存/backups/` 将原文件完好还原。
        """
        dirs = self._ensure_plugin_subfolders()
        backups_dir = dirs["backups"]
        records = self._load_history_list()
        target_rec = next((r for r in records if r.get("id") == record_id), None)
        if not target_rec:
            return {"ok": False, "msg": "未找到该条历史记录", "history": self.get_save_history()}

        saved_path = Path(target_rec.get("savedPath", ""))
        orig_backup_name = target_rec.get("origBackupName", "")
        restored_orig = False

        try:
            if saved_path.exists() and saved_path.is_file():
                saved_path.unlink()
            if orig_backup_name:
                orig_backup_path = backups_dir / orig_backup_name
                if orig_backup_path.exists():
                    saved_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(orig_backup_path), str(saved_path))
                    restored_orig = True
        except Exception as e:
            return {"ok": False, "msg": f"撤回失败（请先关闭正在打开该文档的阅读器）：{e}", "history": self.get_save_history()}

        target_rec["status"] = "revoked"
        self._save_history_list(records)
        target_rec["fileExists"] = False
        msg = "↩️ 已撤回导出文件，并为您自动还原了覆盖前的原文件！" if restored_orig else f"↩️ 已从磁盘撤回并删除：{saved_path.name}"
        return {
            "ok": True,
            "msg": msg,
            "record": target_rec,
            "history": self.get_save_history(),
        }

    def restore_history_item(self, record_id: str):
        """
        【🔄 恢复】：
        将已撤回（或被误删）的文件从 `历史缓存/backups/` 重新写回原本的 `savedPath`。
        """
        dirs = self._ensure_plugin_subfolders()
        backups_dir = dirs["backups"]
        records = self._load_history_list()
        target_rec = next((r for r in records if r.get("id") == record_id), None)
        if not target_rec:
            return {"ok": False, "msg": "未找到该条历史记录", "history": self.get_save_history()}

        gen_backup_name = target_rec.get("genBackupName", "")
        if not gen_backup_name or not (backups_dir / gen_backup_name).exists():
            return {"ok": False, "msg": "缓存副本不存在，无法恢复", "history": self.get_save_history()}

        saved_path = Path(target_rec.get("savedPath", ""))
        try:
            saved_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(backups_dir / gen_backup_name), str(saved_path))
        except Exception as e:
            return {"ok": False, "msg": f"恢复写入失败：{e}", "history": self.get_save_history()}

        target_rec["status"] = "saved"
        self._save_history_list(records)
        target_rec["fileExists"] = True
        return {
            "ok": True,
            "msg": f"✅ 已从历史缓存恢复文件：{saved_path}",
            "record": target_rec,
            "history": self.get_save_history(),
        }

    def delete_history_item(self, record_id: str):
        """
        【✕ 删去记录】：
        从历史记录列表及 `历史缓存/backups/` 中彻底移除该条记录（保留磁盘上已保存的文件不动）。
        """
        dirs = self._ensure_plugin_subfolders()
        backups_dir = dirs["backups"]
        records = self._load_history_list()
        kept = []
        for rec in records:
            if rec.get("id") == record_id:
                for b_key in ("genBackupName", "origBackupName"):
                    b_name = rec.get(b_key, "")
                    if b_name:
                        bp = backups_dir / b_name
                        try:
                            if bp.exists():
                                bp.unlink()
                        except Exception:
                            pass
            else:
                kept.append(rec)

        self._save_history_list(kept)
        return {"ok": True, "history": self.get_save_history()}

    def clear_all_history(self):
        """一键清空全部历史记录与缓存副本（不影响已保存在外面的正常文件）"""
        dirs = self._ensure_plugin_subfolders()
        backups_dir = dirs["backups"]
        try:
            for f in backups_dir.iterdir():
                if f.is_file():
                    f.unlink()
        except Exception:
            pass
        self._save_history_list([])
        return {"ok": True, "history": []}
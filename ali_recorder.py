import os
import sys
import io
import gc
import re
import math
import json
import time
import wave
import array
import ctypes
from ctypes import wintypes
import tempfile
import threading
import subprocess
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import winreg
except Exception:
    winreg = None

import mss
import pyaudiowpatch as pyaudio
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageTk, ImageFilter, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_PERSIAN = True
except Exception:
    HAS_PERSIAN = False

try:
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl
    HAS_WGC = True
except Exception:
    HAS_WGC = False

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

APP_TITLE = "Mocap"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".mocap_config.json")
LOG_PATH = os.path.join(os.path.expanduser("~"), ".mocap_debug.log")
RUN_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

QUALITY_MAP = {
    "low": {"fps": 15, "crf": "32"},
    "medium": {"fps": 25, "crf": "25"},
    "high": {"fps": 30, "crf": "19"},
    "ultra": {"fps": 45, "crf": "15"},
}

STRINGS = {
    "fa": {
        "nav_audio": "🎵   ضبط صدای سیستم",
        "nav_video": "🎬   ضبط ویدیو و صفحه",
        "nav_convert": "🔄   تبدیل ویدیو به صدا",
        "nav_shot": "📸   اسکرین‌شات و ادیتور",
        "nav_help": "📖   راهنما و گزارش خطا",
        "theme_lbl": "🎨 انتخاب تم ظاهری",
        "lang_lbl": "🌐 زبان نرم‌افزار",
        "settings_btn": "⚙  تنظیمات و استارتاپ",
        "title_audio": "ضبط صدای سیستم",
        "title_video": "ضبط ویدیو و صفحه",
        "title_convert": "تبدیل ویدیو به صدا",
        "title_shot": "اسکرین‌شات و ادیتور تصویر",
        "title_help": "راهنما و گزارش خطا",
        "badge_audio": "● آماده ضبط صدا",
        "badge_video": "● آماده ضبط ویدیو",
        "badge_convert": "● مبدل آماده",
        "badge_shot": "● آماده عکاسی",
        "badge_help": "● راهنما",
        "badge_rec_aud": "● در حال ضبط صدا...",
        "badge_rec_vid": "● در حال ضبط ویدیو...",
        "badge_paused": "❚❚ متوقف شده",
        "badge_saving": "● در حال ذخیره...",
        "badge_saved": "✔ ذخیره شد",
        "badge_canceled": "● ذخیره لغو شد",
        "badge_err": "● خطا",
        "btn_fullscreen": "🖥 کل صفحه",
        "btn_region": "✂ محدوده خاص",
        "btn_window": "🪟 پنجره خاص",
        "btn_win_crop": "✂ محدوده مشخص از این پنجره",
        "btn_win_full": "⬜ پنجره کامل",
        "src_fullscreen": "\u200fمنبع تصویر: کل صفحه\u200f",
        "src_region": "\u200fمنبع تصویر: محدوده {w}×{h}\u200f",
        "src_win_full": "\u200fپنجره انتخابی: {t} (کامل)\u200f",
        "src_win_crop": "\u200fپنجره انتخابی: {t} (برش {w}×{h})\u200f",
        "quality_lbl": "\u200fکیفیت ویدیو:\u200f",
        "q_low": "پایین (حجم کم)",
        "q_medium": "متوسط (استاندارد)",
        "q_high": "بالا (باکیفیت)",
        "q_ultra": "عالی (حداکثر)",
        "with_audio": "همراه با صدا",
        "show_cursor": "نمایش نشانگر ماوس",
        "flip_rtl": "اصلاح تصوير برعکس(مرورگر داراي منوي فارسي)",
        "vol_lbl": "🔊 شدت صدا",
        "spd_lbl": "⏩ سرعت پخش",
        "auto_name_hint": "نام فایل به‌صورت خودکار از ویدیوی در حال پخش خوانده می‌شود",
        "file_name_lbl": "\u200fنام فایل: {name}\u200f",
        "btn_rec": "ضبط",
        "btn_pause": "ایستادن",
        "btn_resume": "ادامه",
        "btn_stop": "اتمام",
        "win_tip": (
            "\u200fراهنمای ضبط پنجره خاص:\u200f\n"
            "\u200f• پنجره انتخاب‌شده را کوچک نکنید.\u200f\n"
            "\u200f• اگر تصویر کروم یا فایرفاکس سفید یا متوقف شد، بخش راهنما را ببینید.\u200f\n"
            "\u200f• پس از اتمام ضبط، منبع تصویر خودکار به کل صفحه برمی‌گردد.\u200f"
        ),
        "win_pick_title": "انتخاب پنجره خاص",
        "win_pick_lbl": "\u200fپنجره مورد نظر خود را انتخاب کنید:\u200f",
        "win_pick_ok": "تایید و انتخاب این پنجره",
        "conv_desc": "فایل ویدیویی را انتخاب کنید تا صدای آن استخراج شود",
        "conv_pick": "📂 انتخاب فایل ویدیویی",
        "conv_none": "هنوز فایلی انتخاب نشده است",
        "conv_start": "▶ شروع تبدیل به صدا",
        "conv_working": "در حال تبدیل ویدیو به صدا...",
        "conv_done": "✔ تبدیل با موفقیت انجام شد",
        "shot_desc": "\u202b کلید \u202aPrtSc\u202c برای اسکرین شات از محدوده مشخص و \u202aShift+PrtSc\u202c برای اسکرین شات از کل صفحه\u202c",
        "shot_full": "🖥   عکس از کل صفحه و باز کردن ادیتور",
        "shot_region": "✂   عکس از محدوده خاص و باز کردن ادیتور",
        "shot_open": "📂   باز کردن یک عکس موجود در ادیتور",
        "help_title": "\u200f💡 راهنماي ضبط  :\u200f",
        "bug_title": "\u200f🐞 گزارش فنی و خطاها:\u200f",
        "bug_copy": "📋 کپی گزارش",
        "bug_refresh": "🔄 بروزرسانی",
        "bug_copied": "✔ گزارش کپی شد",
        "set_title": "تنظیمات نرم‌افزار",
        "set_folder": "\u200fپوشه پیش‌فرض ذخیره فایل‌ها:\u200f",
        "set_browse": "انتخاب پوشه",
        "set_ask": "آیا هر بار پس از اتمام، محل ذخیره فایل پرسیده شود؟",
        "set_startup": "اجرای خودکار نرم‌افزار هنگام روشن شدن ویندوز",
        "set_save": "ذخیره تنظیمات",
        "region_prompt": "با ماوس محدوده مورد نظر را بکشید  (کلید لغو برای انصراف)",
        "ed_title": "ادیتور تصویر",
        "ed_save": "💾 ذخیره",
        "ed_copy": "📋 کپی",
        "ed_undo": "↩ برگشت",
        "ed_color": "\u200fرنگ:\u200f",
        "ed_size": "\u200fضخامت و فونت:\u200f",
        "ed_copied": "✔ تصویر در حافظه کپی شد",
        "ed_saved": "✔ تصویر ذخیره شد",
        "ed_undone": "↩ یک مرحله به عقب برگشت",
        "ed_text_title": "وارد کردن متن",
        "ed_text_lbl": "\u200fمتن مورد نظر خود را بنویسید:\u200f",
        "ed_text_ok": "تایید و درج متن",
        "ed_text_cancel": "انصراف",
        "tools": {
            "arrow": "↗ فلش", "double_arrow": "↔ دوسر", "rect": "⬜ کادر",
            "oval": "⭕ دایره", "highlight": "🖍 هایلایتر", "number": "① شماره",
            "pen": "✏ قلم", "blur": "▒ مات", "text": "T متن", "crop": "✂ برش",
        },
    },
    "en": {
        "nav_audio": "🎵   System Audio",
        "nav_video": "🎬   Screen & Video",
        "nav_convert": "🔄   Video to MP3",
        "nav_shot": "📸   Screenshot Editor",
        "nav_help": "📖   Guide & Bug Report",
        "theme_lbl": "🎨 Theme",
        "lang_lbl": "🌐 Language",
        "settings_btn": "⚙  Settings & Startup",
        "title_audio": "System Audio Recorder (MP3)",
        "title_video": "Screen & Video Recorder (MP4)",
        "title_convert": "Convert Video to MP3",
        "title_shot": "Screenshot & Image Editor",
        "title_help": "User Guide & Bug Report",
        "badge_audio": "● Ready (Audio)",
        "badge_video": "● Ready (Video)",
        "badge_convert": "● Converter Ready",
        "badge_shot": "● Ready (Capture)",
        "badge_help": "● Guide",
        "badge_rec_aud": "● Recording Audio...",
        "badge_rec_vid": "● Recording Video...",
        "badge_paused": "❚❚ Paused",
        "badge_saving": "● Saving...",
        "badge_saved": "✔ Saved",
        "badge_canceled": "● Canceled",
        "badge_err": "● Error",
        "btn_fullscreen": "🖥 Full Screen",
        "btn_region": "✂ Custom Region",
        "btn_window": "🪟 Specific Window",
        "btn_win_crop": "✂ Crop Inside Window",
        "btn_win_full": "⬜ Full Window",
        "src_fullscreen": "Source: Full Screen",
        "src_region": "Source: Region {w}×{h}",
        "src_win_full": "Window: {t} (Full)",
        "src_win_crop": "Window: {t} (Crop {w}×{h})",
        "quality_lbl": "Video Quality:",
        "q_low": "Low (Small size)",
        "q_medium": "Medium (Standard)",
        "q_high": "High (Sharp)",
        "q_ultra": "Ultra (Max)",
        "with_audio": "Include Audio",
        "show_cursor": "Show Mouse Cursor",
        "flip_rtl": "Fix Mirrored (RTL UI)",
        "vol_lbl": "🔊 Volume",
        "spd_lbl": "⏩ Speed",
        "auto_name_hint": "Output filename is automatically detected from playing media",
        "file_name_lbl": "File: {name}",
        "btn_rec": "Record",
        "btn_pause": "Pause",
        "btn_resume": "Resume",
        "btn_stop": "Stop",
        "win_tip": (
            "Specific Window Tips:\n"
            "• Do NOT minimize the target window.\n"
            "• See Guide if browser video turns white or freezes.\n"
            "• Source automatically resets to Full Screen after stopping."
        ),
        "win_pick_title": "Select Window",
        "win_pick_lbl": "Choose the target window:",
        "win_pick_ok": "Confirm Window",
        "conv_desc": "Select a video file to extract its audio as MP3",
        "conv_pick": "📂 Choose Video File",
        "conv_none": "No file selected",
        "conv_start": "▶ Convert to MP3",
        "conv_working": "Converting video to MP3...",
        "conv_done": "✔ Conversion completed",
        "shot_desc": "Global Hotkeys: PrtSc (Region) | Shift+PrtSc (Full Screen)",
        "shot_full": "🖥   Full Screen Capture & Edit",
        "shot_region": "✂   Region Capture & Edit",
        "shot_open": "📂   Open Existing Image in Editor",
        "help_title": "💡 Quick Tips for Best Recording Quality:",
        "bug_title": "🐞 Technical Log & Bug Report:",
        "bug_copy": "📋 Copy Report",
        "bug_refresh": "🔄 Refresh",
        "bug_copied": "✔ Copied",
        "set_title": "Settings & Startup",
        "set_folder": "Default Save Folder:",
        "set_browse": "Browse",
        "set_ask": "Ask where to save every time after recording?",
        "set_startup": "Start Mocap automatically with Windows",
        "set_save": "Save Settings",
        "region_prompt": "Drag to select region  (Press ESC to cancel)",
        "ed_title": "Image Editor",
        "ed_save": "💾 Save",
        "ed_copy": "📋 Copy",
        "ed_undo": "↩ Undo",
        "ed_color": "Color:",
        "ed_size": "Size:",
        "ed_copied": "✔ Copied to clipboard",
        "ed_saved": "✔ Image saved",
        "ed_undone": "↩ Undone",
        "ed_text_title": "Insert Text",
        "ed_text_lbl": "Enter your text:",
        "ed_text_ok": "Insert Text",
        "ed_text_cancel": "Cancel",
        "tools": {
            "arrow": "↗ Arrow", "double_arrow": "↔ 2-Way", "rect": "⬜ Box",
            "oval": "⭕ Oval", "highlight": "🖍 Highlight", "number": "① Step",
            "pen": "✏ Pen", "blur": "▒ Blur", "text": "T Text", "crop": "✂ Crop",
        },
    },
}

THEMES = {
    "شب نئونی": {
        "bg": "#0F172A", "sidebar": "#111827", "card": "#1E293B", "card_alt": "#263349",
        "border": "#334155", "text": "#F8FAFC", "muted": "#94A3B8", "accent": "#6366F1",
        "accent_hover": "#818CF8", "accent_fg": "#FFFFFF", "cyan": "#06B6D4", "pink": "#EC4899",
        "amber": "#F59E0B", "green": "#10B981", "record": "#F43F5E", "record_hover": "#FB7185",
        "pause": "#F59E0B", "pause_hover": "#FBBF24", "stop": "#10B981", "stop_hover": "#34D399",
        "disabled": "#334155", "canvas_bg": "#090D16",
    },
    "تیره استودیویی": {
        "bg": "#121212", "sidebar": "#181818", "card": "#1E1E1E", "card_alt": "#2A2A2A",
        "border": "#333333", "text": "#F3F4F6", "muted": "#9CA3AF", "accent": "#D97706",
        "accent_hover": "#F59E0B", "accent_fg": "#FFFFFF", "cyan": "#14B8A6", "pink": "#F43F5E",
        "amber": "#F59E0B", "green": "#22C55E", "record": "#EF4444", "record_hover": "#F87171",
        "pause": "#EAB308", "pause_hover": "#FACC15", "stop": "#10B981", "stop_hover": "#34D399",
        "disabled": "#3F3F46", "canvas_bg": "#0A0A0A",
    },
    "روشن مدرن": {
        "bg": "#F1F5F9", "sidebar": "#FFFFFF", "card": "#FFFFFF", "card_alt": "#E2E8F0",
        "border": "#CBD5E1", "text": "#0F172A", "muted": "#475569", "accent": "#2563EB",
        "accent_hover": "#3B82F6", "accent_fg": "#FFFFFF", "cyan": "#0891B2", "pink": "#DB2777",
        "amber": "#D97706", "green": "#059669", "record": "#E11D48", "record_hover": "#F43F5E",
        "pause": "#D97706", "pause_hover": "#F59E0B", "stop": "#059669", "stop_hover": "#10B981",
        "disabled": "#CBD5E1", "canvas_bg": "#E2E8F0",
    },
    "بنفش حرفه‌ای": {
        "bg": "#13111C", "sidebar": "#181426", "card": "#211C35", "card_alt": "#2D2647",
        "border": "#3B325E", "text": "#F5F3FF", "muted": "#A78BFA", "accent": "#8B5CF6",
        "accent_hover": "#A78BFA", "accent_fg": "#FFFFFF", "cyan": "#22D3EE", "pink": "#F472B6",
        "amber": "#FBBF24", "green": "#34D399", "record": "#FB7185", "record_hover": "#FDA4AF",
        "pause": "#FBBF24", "pause_hover": "#FCD34D", "stop": "#34D399", "stop_hover": "#6EE7B7",
        "disabled": "#3B325E", "canvas_bg": "#0B0912",
    },
}

DEBUG_LOGS = []


def log_event(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    DEBUG_LOGS.append(line)
    if len(DEBUG_LOGS) > 150:
        DEBUG_LOGS.pop(0)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def is_frame_mostly_black(raw_bytes: bytes) -> bool:
    n = len(raw_bytes)
    if n < 400:
        return True
    step = max(4, n // 120)
    non_zero = 0
    for i in range(0, n - 3, step):
        if raw_bytes[i] > 8 or raw_bytes[i + 1] > 8 or raw_bytes[i + 2] > 8:
            non_zero += 1
            if non_zero >= 3:
                return False
    return True


def is_window_rtl(hwnd) -> bool:
    try:
        ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        return bool(ex_style & 0x00400000)
    except Exception:
        return False


def set_windows_startup(enable: bool):
    if not winreg:
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_PATH, 0, winreg.KEY_SET_VALUE)
        if enable:
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}" --minimized'
            else:
                cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" --minimized'
            winreg.SetValueEx(key, APP_TITLE, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_TITLE)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        log_event(f"Startup registry error: {e}")


def get_resource_path(candidates):
    dirs = []
    if hasattr(sys, "_MEIPASS"):
        dirs.append(sys._MEIPASS)
    dirs.append(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)))
    dirs.append(os.getcwd())
    for d in dirs:
        for name in candidates:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def _run_wgc_subprocess_worker(cfg_path: str):
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    fps, crf = cfg["fps"], cfg["crf"]
    stop_flag, pause_flag, result_path = cfg["stop_flag"], cfg["pause_flag"], cfg["result_path"]

    state = {
        "w": 0, "h": 0, "latest_bytes": None, "lock": threading.Lock(),
        "proc": None, "frames_written": 0, "black_skipped": 0, "error": "",
    }

    try:
        capture = WindowsCapture(
            cursor_capture=bool(cfg.get("cursor_capture", False)),
            draw_border=None,
            window_name=cfg["window_title"],
        )

        @capture.event
        def on_frame_arrived(frame: Frame, capture_control: InternalCaptureControl):
            if os.path.exists(stop_flag):
                _safe_call(capture_control.stop)
                return
            if os.path.exists(pause_flag):
                return

            buf = frame.frame_buffer
            fh, fw = buf.shape[0], buf.shape[1]
            if fw < 16 or fh < 16:
                return

            with state["lock"]:
                if state["proc"] is None:
                    ew, eh = fw - (fw % 2), fh - (fh % 2)
                    state["w"], state["h"] = ew, eh
                    vfilters = []
                    if cfg.get("hflip"):
                        vfilters.append("hflip")
                    crop = cfg.get("crop")
                    if crop:
                        cw = min(crop["w"], ew - crop["x"])
                        ch = min(crop["h"], eh - crop["y"])
                        cw -= cw % 2
                        ch -= ch % 2
                        if cw >= 40 and ch >= 40:
                            cx = (ew - crop["x"] - cw) if cfg.get("hflip") else crop["x"]
                            vfilters.append(f"crop={cw}:{ch}:{max(0, cx)}:{crop['y']}")
                    vf_args = ["-vf", ",".join(vfilters)] if vfilters else []

                    cmd = [
                        ffmpeg_exe, "-y",
                        "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{ew}x{eh}", "-r", str(fps),
                        "-i", "-",
                    ] + vf_args + [
                        "-c:v", "libx264", "-preset", "ultrafast", "-crf", crf,
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                        cfg["output_path"],
                    ]
                    state["proc"] = subprocess.Popen(
                        cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, creationflags=creationflags,
                    )

                tw, th = state["w"], state["h"]
                if fw >= tw and fh >= th:
                    raw = buf[:th, :tw, :].tobytes()
                else:
                    pil_f = Image.frombuffer("RGBA", (fw, fh), buf.tobytes(), "raw", "BGRA", 0, 1)
                    pil_f = pil_f.resize((tw, th), Image.Resampling.BILINEAR)
                    r, g, b, a = pil_f.split()
                    raw = Image.merge("RGBA", (b, g, r, a)).tobytes()

                if state["latest_bytes"] is not None and is_frame_mostly_black(raw):
                    state["black_skipped"] += 1
                else:
                    state["latest_bytes"] = raw

        @capture.event
        def on_closed():
            pass

        control = capture.start_free_threaded() if hasattr(capture, "start_free_threaded") else None
        if control is None:
            threading.Thread(target=capture.start, daemon=True).start()

        frame_interval = 1.0 / fps
        next_t = time.perf_counter()

        while not os.path.exists(stop_flag):
            if os.path.exists(pause_flag):
                time.sleep(0.05)
                next_t = time.perf_counter()
                continue
            with state["lock"]:
                data = state["latest_bytes"]
                proc = state["proc"]
            if data and proc and proc.stdin:
                try:
                    proc.stdin.write(data)
                    state["frames_written"] += 1
                except Exception:
                    break
            next_t += frame_interval
            sl = next_t - time.perf_counter()
            if sl > 0:
                time.sleep(sl)
            else:
                next_t = time.perf_counter()

        if control is not None:
            t_stop = threading.Thread(target=lambda: _safe_call(control.stop), daemon=True)
            t_stop.start()
            t_stop.join(timeout=0.8)
    except Exception as e:
        state["error"] = str(e)
    finally:
        if state["proc"]:
            try:
                if state["proc"].stdin:
                    state["proc"].stdin.close()
                state["proc"].wait(timeout=8)
            except Exception:
                _safe_call(state["proc"].kill)
        try:
            with open(result_path, "w", encoding="utf-8") as rf:
                json.dump({
                    "frames": state["frames_written"],
                    "black_skipped": state["black_skipped"],
                    "error": state["error"],
                }, rf)
        except Exception:
            pass
    os._exit(0)


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


class HoverTooltip:
    def __init__(self, widget, text: str, theme: dict, is_rtl: bool = True):
        self.widget, self.text, self.theme, self.is_rtl = widget, text, theme, is_rtl
        self.tip_win = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tip_win:
            return
        x = self.widget.winfo_rootx() - (220 if self.is_rtl else 0)
        y = self.widget.winfo_rooty() + 28
        self.tip_win = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{max(10, x)}+{y}")
        tw.attributes("-topmost", True)
        frame = tk.Frame(tw, bg=self.theme["card"], padx=12, pady=10, highlightbackground=self.theme["accent"], highlightthickness=1)
        frame.pack()
        tk.Label(frame, text=self.text, bg=self.theme["card"], fg=self.theme["text"], font=("Tahoma", 8),
                 justify="right" if self.is_rtl else "left", wraplength=290).pack()

    def hide(self, _event=None):
        if self.tip_win:
            self.tip_win.destroy()
            self.tip_win = None


def fix_persian_text(text: str) -> str:
    if not HAS_PERSIAN:
        return text
    return "\n".join(get_display(arabic_reshaper.reshape(line)) for line in text.splitlines())


def hex_to_rgba(hex_color: str, alpha: int = 255):
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha)


def copy_image_to_clipboard(pil_image: Image.Image):
    output = io.BytesIO()
    pil_image.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    h_global = kernel32.GlobalAlloc(0x0002, len(data))
    if not h_global:
        raise RuntimeError("Clipboard allocation failed")
    p_global = kernel32.GlobalLock(h_global)
    ctypes.memmove(p_global, data, len(data))
    kernel32.GlobalUnlock(h_global)
    if not user32.OpenClipboard(0):
        kernel32.GlobalFree(h_global)
        raise RuntimeError("Cannot open clipboard")
    user32.EmptyClipboard()
    user32.SetClipboardData(8, h_global)
    user32.CloseClipboard()


def list_open_windows():
    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    windows = []

    def foreach(hwnd, _lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value.strip()
                if title and APP_TITLE not in title and title not in ("Program Manager", "Settings"):
                    rect = wintypes.RECT()
                    user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    if (rect.right - rect.left) >= 100 and (rect.bottom - rect.top) >= 100:
                        windows.append((hwnd, title))
        return True

    user32.EnumWindows(EnumWindowsProc(foreach), 0)
    return windows


def capture_window_bgra_fallback(hwnd, width, height):
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    hwnd_dc = user32.GetWindowDC(hwnd)
    if not hwnd_dc:
        return None
    mfc_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, width, height)
    old_obj = gdi32.SelectObject(mfc_dc, bitmap)
    user32.PrintWindow(hwnd, mfc_dc, 2)
    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth, bmi.bmiHeader.biHeight = width, -height
    bmi.bmiHeader.biPlanes, bmi.bmiHeader.biBitCount, bmi.bmiHeader.biCompression = 1, 32, 0
    buf = ctypes.create_string_buffer(width * height * 4)
    gdi32.GetDIBits(mfc_dc, bitmap, 0, height, buf, ctypes.byref(bmi), 0)
    gdi32.SelectObject(mfc_dc, old_obj)
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mfc_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)
    return buf.raw


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\r\n\t]+', " ", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name[:120] if name else ""


def detect_playing_media_name(target_title: str = "") -> str:
    titles = [target_title] if target_title else [t for _, t in list_open_windows()]
    player_suffixes = [
        " - VLC media player", " - PotPlayer", " - PotPlayerMini64", " - PotPlayer64",
        " - KMPlayer", " - The KMPlayer", " - Media Player Classic", " - MPC-HC",
        " - MPC-BE", " - Media Player", " - Windows Media Player", " - GOM Player", " - mpv",
    ]
    video_exts = (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".ts", ".mp3", ".wav")
    for title in titles:
        for suffix in player_suffixes:
            if title.lower().endswith(suffix.lower()):
                clean = title[: -len(suffix)].strip()
                for ext in video_exts:
                    if clean.lower().endswith(ext):
                        clean = clean[: -len(ext)]
                        break
                clean = sanitize_filename(clean)
                if clean:
                    return clean
    for title in titles:
        lower = title.lower()
        for ext in video_exts:
            if ext in lower:
                clean = sanitize_filename(title[: lower.rfind(ext)])
                if clean:
                    return clean
    browser_suffixes = [
        " - YouTube - Google Chrome", " - YouTube - Microsoft Edge", " - YouTube — Mozilla Firefox",
        " - Google Chrome", " - Microsoft Edge", " — Mozilla Firefox", " - Opera", " - Brave",
    ]
    for title in titles:
        for suffix in browser_suffixes:
            if title.endswith(suffix):
                clean = sanitize_filename(re.sub(r"^\(\d+\)\s*", "", title[: -len(suffix)].strip()))
                if clean and clean.lower() not in ("new tab", "youtube", "google"):
                    return clean
    if target_title:
        clean = sanitize_filename(target_title)
        if clean:
            return clean
    return f"Mocap_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"


def build_atempo_chain(speed: float) -> str:
    filters, remaining = [], speed
    while remaining > 2.0:
        filters.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5:
        filters.append("atempo=0.5")
        remaining /= 0.5
    filters.append(f"atempo={remaining:.4f}")
    return ",".join(filters)


class RegionSelector:
    def __init__(self, parent, callback, prompt_text, restore_parent=True):
        self.parent, self.callback, self.restore_parent = parent, callback, restore_parent
        self.start_x = self.start_y = 0
        self.rect_id = None

        self.parent.withdraw()
        time.sleep(0.2)

        self.overlay = tk.Toplevel()
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-alpha", 0.30)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="#000000", cursor="crosshair")

        self.canvas = tk.Canvas(self.overlay, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(self.overlay.winfo_screenwidth() // 2, 45, text=prompt_text, fill="#FFFFFF", font=("Tahoma", 13, "bold"))

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.overlay.bind("<Escape>", self._on_cancel)

    def _on_press(self, event):
        self.start_x, self.start_y = event.x_root, event.y_root
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#06B6D4", width=3, fill="#1E293B")

    def _on_drag(self, event):
        if self.rect_id:
            self.canvas.coords(self.rect_id, self.start_x - self.overlay.winfo_rootx(), self.start_y - self.overlay.winfo_rooty(), event.x, event.y)

    def _on_release(self, event):
        end_x, end_y = event.x_root, event.y_root
        left, top = min(self.start_x, end_x), min(self.start_y, end_y)
        width, height = abs(end_x - self.start_x), abs(end_y - self.start_y)
        width -= width % 2
        height -= height % 2
        self.overlay.destroy()
        if self.restore_parent:
            self.parent.deiconify()
        if width >= 20 and height >= 20:
            self.callback({"left": left, "top": top, "width": width, "height": height})
        elif not self.restore_parent:
            self.parent.deiconify()

    def _on_cancel(self, _event):
        self.overlay.destroy()
        self.parent.deiconify()


class ScreenshotEditor(tk.Toplevel):
    def __init__(self, parent, pil_image: Image.Image, save_folder: str, theme: dict, tr: dict):
        super().__init__(parent)
        self.theme, self.tr, self.save_folder = theme, tr, save_folder
        self.title(f"{tr['ed_title']} — {APP_TITLE}")
        self.configure(bg=theme["bg"])

        self.image = pil_image.convert("RGB")
        self.history, self.step_counter = [], 1
        self.current_tool, self.current_color = "arrow", "#FF3B30"
        self.thickness_var = tk.IntVar(value=5)
        self.start_xy = self.preview_id = self.tk_img = None
        self.pen_points = []

        self._calc_display_size()
        self._build_toolbar()
        self._build_canvas()
        self._refresh_canvas()

        self.bind("<BackSpace>", lambda _e: self.undo())
        self.bind("<Escape>", lambda _e: self.undo())
        self.bind("<Control-z>", lambda _e: self.undo())
        self.bind("<Control-Z>", lambda _e: self.undo())
        self.lift()
        self.focus_force()

    def _calc_display_size(self):
        max_w = min(1150, self.winfo_screenwidth() - 120)
        max_h = min(650, self.winfo_screenheight() - 220)
        img_w, img_h = self.image.size
        self.scale = min(1.0, max_w / img_w, max_h / img_h)
        self.disp_w, self.disp_h = max(1, int(img_w * self.scale)), max(1, int(img_h * self.scale))

    def _build_toolbar(self):
        t, tr = self.theme, self.tr
        bar1 = tk.Frame(self, bg=t["card"], pady=9, padx=10, highlightbackground=t["border"], highlightthickness=1)
        bar1.pack(fill="x")
        self.tool_buttons = {}
        for key, label in tr["tools"].items():
            btn = tk.Button(bar1, text=label, bg=t["card_alt"], fg=t["text"], relief="flat",
                            font=("Tahoma", 8, "bold"), padx=8, pady=5, cursor="hand2", command=lambda k=key: self.select_tool(k))
            btn.pack(side="right", padx=2)
            self.tool_buttons[key] = btn

        tk.Button(bar1, text=tr["ed_save"], bg=t["stop"], fg="#FFFFFF", relief="flat", font=("Tahoma", 8, "bold"), padx=11, pady=5, cursor="hand2", command=self.save_image).pack(side="left", padx=2)
        tk.Button(bar1, text=tr["ed_copy"], bg=t["cyan"], fg="#FFFFFF", relief="flat", font=("Tahoma", 8, "bold"), padx=11, pady=5, cursor="hand2", command=self.copy_image).pack(side="left", padx=2)
        tk.Button(bar1, text=tr["ed_undo"], bg=t["pause"], fg="#111827", relief="flat", font=("Tahoma", 8, "bold"), padx=9, pady=5, cursor="hand2", command=self.undo).pack(side="left", padx=2)

        bar2 = tk.Frame(self, bg=t["bg"], pady=7, padx=12)
        bar2.pack(fill="x")
        tk.Label(bar2, text=tr["ed_color"], bg=t["bg"], fg=t["text"], font=("Tahoma", 9, "bold")).pack(side="right", padx=(6, 4))
        self.color_btns = {}
        for col in ("#FF3B30", "#FFCC00", "#06B6D4", "#22C55E", "#A855F7", "#FFFFFF", "#000000"):
            cb = tk.Button(bar2, bg=col, width=3, height=1, relief="flat", cursor="hand2", command=lambda c=col: self.select_color(c))
            cb.pack(side="right", padx=2)
            self.color_btns[col] = cb
        tk.Label(bar2, text=tr["ed_size"], bg=t["bg"], fg=t["text"], font=("Tahoma", 9, "bold")).pack(side="right", padx=(16, 6))
        tk.Scale(bar2, from_=2, to=20, orient="horizontal", variable=self.thickness_var, bg=t["bg"], fg=t["text"], troughcolor=t["card_alt"], highlightthickness=0, length=120).pack(side="right")
        self.info_lbl = tk.Label(bar2, text="", bg=t["bg"], fg=t["accent"], font=("Tahoma", 8, "bold"))
        self.info_lbl.pack(side="left", padx=6)
        self.select_tool("arrow")
        self.select_color("#FF3B30")

    def _build_canvas(self):
        t = self.theme
        frame = tk.Frame(self, bg=t["canvas_bg"], padx=10, pady=10)
        frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(frame, width=self.disp_w, height=self.disp_h, bg=t["canvas_bg"], highlightthickness=1, highlightbackground=t["border"], cursor="crosshair")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def select_tool(self, tool_key: str):
        t = self.theme
        self.current_tool = tool_key
        for k, btn in self.tool_buttons.items():
            btn.config(bg=t["accent"] if k == tool_key else t["card_alt"], fg=t["accent_fg"] if k == tool_key else t["text"])
        self.info_lbl.config(text=self.tr["tools"].get(tool_key, ""), fg=t["accent"])

    def select_color(self, color_hex: str):
        self.current_color = color_hex
        for c, btn in self.color_btns.items():
            btn.config(bd=3 if c == color_hex else 0, relief="solid" if c == color_hex else "flat")

    def _push_history(self):
        self.history.append((self.image.copy(), self.step_counter))
        if len(self.history) > 30:
            self.history.pop(0)

    def undo(self):
        if self.history:
            self.image, self.step_counter = self.history.pop()
            self._calc_display_size()
            self.canvas.config(width=self.disp_w, height=self.disp_h)
            self._refresh_canvas()
            self.info_lbl.config(text=self.tr["ed_undone"], fg=self.theme["pause"])

    def _refresh_canvas(self):
        self.tk_img = ImageTk.PhotoImage(self.image.resize((self.disp_w, self.disp_h), Image.Resampling.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def _to_img_coords(self, x, y):
        return int(x / self.scale), int(y / self.scale)

    def _draw_arrowhead(self, draw: ImageDraw.ImageDraw, x1, y1, x2, y2, size, color):
        angle, head_len, spread = math.atan2(y2 - y1, x2 - x1), max(14, size * 4), math.pi / 6
        draw.polygon([
            (x2, y2),
            (x2 - head_len * math.cos(angle - spread), y2 - head_len * math.sin(angle - spread)),
            (x2 - head_len * math.cos(angle + spread), y2 - head_len * math.sin(angle + spread)),
        ], fill=color)

    def _ask_multiline_text(self) -> str:
        t, tr = self.theme, self.tr
        dlg = tk.Toplevel(self)
        dlg.title(tr["ed_text_title"])
        dlg.geometry("390x195")
        dlg.resizable(False, False)
        dlg.configure(bg=t["bg"])
        dlg.transient(self)
        dlg.grab_set()
        tk.Label(dlg, text=tr["ed_text_lbl"], bg=t["bg"], fg=t["accent"], font=("Tahoma", 9, "bold")).pack(pady=(12, 6))
        txt_box = tk.Text(dlg, height=4, bg=t["card"], fg=t["text"], insertbackground=t["text"], font=("Tahoma", 10),
                          relief="flat", padx=8, pady=6, highlightbackground=t["border"], highlightthickness=1)
        txt_box.pack(fill="x", padx=16)
        txt_box.focus_set()
        result = {"text": ""}

        def on_ok(_e=None):
            result["text"] = txt_box.get("1.0", "end-1c").strip()
            dlg.destroy()

        btn_row = tk.Frame(dlg, bg=t["bg"])
        btn_row.pack(pady=10)
        tk.Button(btn_row, text=tr["ed_text_ok"], bg=t["stop"], fg="#FFFFFF", relief="flat", font=("Tahoma", 9, "bold"), padx=16, pady=5, cursor="hand2", command=on_ok).pack(side="left", padx=6)
        tk.Button(btn_row, text=tr["ed_text_cancel"], bg=t["card_alt"], fg=t["text"], relief="flat", font=("Tahoma", 9), padx=12, pady=5, cursor="hand2", command=dlg.destroy).pack(side="left", padx=6)
        dlg.bind("<Control-Return>", on_ok)
        self.wait_window(dlg)
        self.focus_set()
        return result["text"]

    def _on_press(self, event):
        if self.current_tool == "number":
            self._push_history()
            ix, iy = self._to_img_coords(event.x, event.y)
            r = max(14, int(self.thickness_var.get() * 2.5 / self.scale))
            draw = ImageDraw.Draw(self.image)
            draw.ellipse([ix - r, iy - r, ix + r, iy + r], fill=self.current_color, outline="#FFFFFF", width=2)
            try:
                font = ImageFont.truetype("tahoma.ttf", int(r * 1.15))
            except Exception:
                font = ImageFont.load_default()
            num_str = str(self.step_counter)
            bbox = draw.textbbox((0, 0), num_str, font=font)
            txt_col = "#000000" if self.current_color in ("#FFFFFF", "#FFCC00") else "#FFFFFF"
            draw.text((ix - (bbox[2] - bbox[0]) / 2, iy - (bbox[3] - bbox[1]) / 2 - bbox[1] / 2), num_str, fill=txt_col, font=font)
            self.step_counter += 1
            self._refresh_canvas()
            return
        self.start_xy = (event.x, event.y)
        self.pen_points = [(event.x, event.y)]

    def _on_drag(self, event):
        if not self.start_xy:
            return
        x0, y0, x1, y1 = self.start_xy[0], self.start_xy[1], event.x, event.y
        if self.current_tool == "pen":
            self.pen_points.append((x1, y1))
            self.canvas.create_line(self.pen_points[-2][0], self.pen_points[-2][1], x1, y1, fill=self.current_color, width=self.thickness_var.get(), capstyle="round")
            return
        if self.preview_id:
            self.canvas.delete(self.preview_id)
        if self.current_tool in ("arrow", "double_arrow"):
            self.preview_id = self.canvas.create_line(x0, y0, x1, y1, fill=self.current_color, width=self.thickness_var.get(), arrow=tk.LAST if self.current_tool == "arrow" else tk.BOTH)
        elif self.current_tool == "rect":
            self.preview_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline=self.current_color, width=self.thickness_var.get())
        elif self.current_tool == "oval":
            self.preview_id = self.canvas.create_oval(x0, y0, x1, y1, outline=self.current_color, width=self.thickness_var.get())
        elif self.current_tool in ("blur", "text", "crop", "highlight"):
            self.preview_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline="#FFCC00" if self.current_tool == "highlight" else "#06B6D4", width=2, dash=(4, 4))

    def _on_release(self, event):
        if not self.start_xy:
            return
        x0, y0, x1, y1 = self.start_xy[0], self.start_xy[1], event.x, event.y
        self.start_xy = None
        if self.preview_id:
            self.canvas.delete(self.preview_id)
            self.preview_id = None

        ix0, iy0 = self._to_img_coords(x0, y0)
        ix1, iy1 = self._to_img_coords(x1, y1)
        left, right = max(0, min(ix0, ix1)), min(self.image.width, max(ix0, ix1))
        top, bottom = max(0, min(iy0, iy1)), min(self.image.height, max(iy0, iy1))
        thick = max(2, int(self.thickness_var.get() / self.scale))

        if self.current_tool == "text":
            if (right - left) < 15 or (bottom - top) < 15:
                right, bottom = min(self.image.width, left + 250), min(self.image.height, top + 80)
            raw_txt = self._ask_multiline_text()
            if not raw_txt:
                return
            self._push_history()
            shaped = fix_persian_text(raw_txt)
            draw = ImageDraw.Draw(self.image)
            try:
                font = ImageFont.truetype("tahoma.ttf", max(16, int(self.thickness_var.get() * 4.5 / self.scale)))
            except Exception:
                font = ImageFont.load_default()
            bbox = draw.multiline_textbbox((0, 0), shaped, font=font)
            draw.multiline_text((max(left, right - (bbox[2] - bbox[0]) - 6), top + 4), shaped, fill=self.current_color, font=font, align="right")
            self._refresh_canvas()
            return

        if self.current_tool == "crop":
            if (right - left) >= 20 and (bottom - top) >= 20:
                self._push_history()
                self.image = self.image.crop((left, top, right, bottom))
                self._calc_display_size()
                self.canvas.config(width=self.disp_w, height=self.disp_h)
                self._refresh_canvas()
            return

        self._push_history()
        draw = ImageDraw.Draw(self.image)
        if self.current_tool == "pen" and len(self.pen_points) > 1:
            draw.line([self._to_img_coords(px, py) for px, py in self.pen_points], fill=self.current_color, width=thick, joint="curve")
        elif self.current_tool == "arrow":
            draw.line([(ix0, iy0), (ix1, iy1)], fill=self.current_color, width=thick)
            self._draw_arrowhead(draw, ix0, iy0, ix1, iy1, thick, self.current_color)
        elif self.current_tool == "double_arrow":
            draw.line([(ix0, iy0), (ix1, iy1)], fill=self.current_color, width=thick)
            self._draw_arrowhead(draw, ix0, iy0, ix1, iy1, thick, self.current_color)
            self._draw_arrowhead(draw, ix1, iy1, ix0, iy0, thick, self.current_color)
        elif self.current_tool == "rect":
            draw.rectangle([left, top, right, bottom], outline=self.current_color, width=thick)
        elif self.current_tool == "oval":
            draw.ellipse([left, top, right, bottom], outline=self.current_color, width=thick)
        elif self.current_tool == "highlight" and (right - left) >= 4 and (bottom - top) >= 4:
            overlay = Image.new("RGBA", self.image.size, (0, 0, 0, 0))
            ImageDraw.Draw(overlay).rectangle([left, top, right, bottom], fill=hex_to_rgba(self.current_color, 95))
            self.image = Image.alpha_composite(self.image.convert("RGBA"), overlay).convert("RGB")
        elif self.current_tool == "blur" and (right - left) >= 4 and (bottom - top) >= 4:
            self.image.paste(self.image.crop((left, top, right, bottom)).filter(ImageFilter.GaussianBlur(radius=14)), (left, top))
        self._refresh_canvas()

    def copy_image(self):
        try:
            copy_image_to_clipboard(self.image)
            self.info_lbl.config(text=self.tr["ed_copied"], fg=self.theme["stop"])
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    def save_image(self):
        path = filedialog.asksaveasfilename(
            parent=self, initialdir=self.save_folder,
            initialfile=f"Mocap_Shot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.png",
            defaultextension=".png", filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")],
        )
        if path:
            self.image.save(path)
            self.info_lbl.config(text=self.tr["ed_saved"], fg=self.theme["stop"])
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])


class CircleButton(tk.Canvas):
    def __init__(self, parent, size, bg_color, hover_color, disabled_color, canvas_bg, text_color, muted_color, symbol, label_text, command, **kwargs):
        super().__init__(parent, width=size, height=size + 28, bg=canvas_bg, highlightthickness=0, cursor="hand2", **kwargs)
        self.bg_color, self.hover_color, self.disabled_color = bg_color, hover_color, disabled_color
        self.text_color, self.muted_color, self.command, self.enabled = text_color, muted_color, command, True
        pad = 4
        self.circle = self.create_oval(pad, pad, size - pad, size - pad, fill=bg_color, outline="")
        self.icon_text = self.create_text(size / 2, size / 2, text=symbol, fill="#FFFFFF", font=("Segoe UI Symbol", 20, "bold"))
        self.caption = self.create_text(size / 2, size + 14, text=label_text, fill=text_color, font=("Tahoma", 9, "bold"))
        self.bind("<Enter>", lambda _e: self.enabled and self.itemconfig(self.circle, fill=self.hover_color))
        self.bind("<Leave>", lambda _e: self.enabled and self.itemconfig(self.circle, fill=self.bg_color))
        self.bind("<Button-1>", lambda _e: self.enabled and self.command and self.command())

    def set_enabled(self, state: bool):
        self.enabled = state
        self.itemconfig(self.circle, fill=self.bg_color if state else self.disabled_color)
        self.itemconfig(self.caption, fill=self.text_color if state else self.muted_color)
        self.config(cursor="hand2" if state else "arrow")

    def set_symbol_and_label(self, symbol: str, label_text: str):
        self.itemconfig(self.icon_text, text=symbol)
        self.itemconfig(self.caption, text=label_text)


class MocapApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("800x690")
        self.root.resizable(False, False)

        self.settings = self.load_settings()
        theme_name = self.settings.get("theme", "شب نئونی")
        self.theme_name = tk.StringVar(value=theme_name if theme_name in THEMES else "شب نئونی")
        self.theme = THEMES[self.theme_name.get()]

        self.lang = self.settings.get("lang", "fa")
        if self.lang not in STRINGS:
            self.lang = "fa"
        self.tr = STRINGS[self.lang]

        self.mode, self.capture_source = "audio", "fullscreen"
        self.selected_region = self.selected_window_hwnd = self.window_crop = None
        self.selected_window_title = self.convert_video_path = ""

        self.record_audio_with_video = tk.BooleanVar(value=True)
        self.show_cursor_var = tk.BooleanVar(value=False)
        self.flip_rtl_var = tk.BooleanVar(value=False)
        self.quality_key = "medium"
        self.quality_var = tk.StringVar(value=self.tr["q_medium"])
        self.volume_var = tk.DoubleVar(value=1.0)
        self.speed_var = tk.DoubleVar(value=1.0)

        self.is_recording = self.is_paused = False
        self.stop_event = threading.Event()
        self.recorded_frames = []
        self.sample_rate, self.channels = 48000, 2
        self.elapsed_seconds = self.last_tick = 0.0
        self.detected_name = ""

        self.audio_thread = self.video_thread = self.wgc_proc = None
        self.wgc_stop_flag = self.wgc_pause_flag = self.temp_video_path = self.temp_audio_path = None

        log_event(f"Mocap started | WGC={HAS_WGC} | Persian={HAS_PERSIAN} | lang={self.lang}")
        self._build_ui()
        self._start_global_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if "--minimized" in sys.argv:
            self.root.iconify()

    def _start_global_hotkeys(self):
        def listener():
            user32 = ctypes.windll.user32
            r1 = user32.RegisterHotKey(None, 1, 0, 0x2C)
            r2 = user32.RegisterHotKey(None, 2, 0x0004, 0x2C)
            log_event(f"Hotkeys registered | PrtSc={bool(r1)} | Shift+PrtSc={bool(r2)}")
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                if msg.message == 0x0312:
                    if msg.wParam == 1:
                        self.root.after(0, self.take_region_shot)
                    elif msg.wParam == 2:
                        self.root.after(0, self.take_fullscreen_shot)
            user32.UnregisterHotKey(None, 1)
            user32.UnregisterHotKey(None, 2)

        threading.Thread(target=listener, daemon=True).start()

    def load_settings(self):
        default_dir = os.path.join(os.path.expanduser("~"), "Music")
        if not os.path.isdir(default_dir):
            default_dir = os.path.expanduser("~")
        defaults = {"save_folder": default_dir, "ask_every_time": True, "theme": "شب نئونی", "lang": "fa", "start_with_windows": False}
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    defaults.update(json.load(f))
            except Exception:
                pass
        return defaults

    def save_settings(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def change_theme(self, new_theme_name: str):
        if self.is_recording or new_theme_name not in THEMES:
            return
        self.theme_name.set(new_theme_name)
        self.theme = THEMES[new_theme_name]
        self.settings["theme"] = new_theme_name
        self.save_settings()
        self._build_ui()

    def change_language(self, new_lang: str):
        if self.is_recording or new_lang not in STRINGS:
            return
        self.lang, self.tr = new_lang, STRINGS[new_lang]
        self.settings["lang"] = new_lang
        self.save_settings()
        self.quality_var.set(self.tr[f"q_{self.quality_key}"])
        self._build_ui()

    def _get_selected_quality_preset(self):
        val = self.quality_var.get()
        for k in ("low", "medium", "high", "ultra"):
            if val == self.tr[f"q_{k}"]:
                self.quality_key = k
                return QUALITY_MAP[k]
        return QUALITY_MAP["medium"]

    def _draw_mocap_logo(self, parent):
        t = self.theme
        logo_canvas = tk.Canvas(parent, width=196, height=76, bg=t["sidebar"], highlightthickness=0)
        logo_canvas.pack(pady=(10, 4))

        ico_path = get_resource_path(["mocap.ico"])
        if ico_path:
            _safe_call(lambda: self.root.iconbitmap(ico_path))

        logo_path = get_resource_path(["mocap_logo.png", "mocap_logo.jpg", "mocap_logo.jpeg"])
        if logo_path:
            try:
                raw = Image.open(logo_path).convert("RGB")
                w, h = raw.size
                raw = raw.crop((int(w * 0.13), int(h * 0.13), int(w * 0.87), int(h * 0.87))).resize((54, 54), Image.Resampling.LANCZOS)
                bg_rgb = hex_to_rgba(t["card_alt"])[:3]
                acc_rgb = hex_to_rgba(t["accent"])[:3]
                cyn_rgb = hex_to_rgba(t["cyan"])[:3]

                new_pixels = []
                for r, g, b in raw.getdata():
                    mx = max(r, g, b)
                    if mx < 65:
                        new_pixels.append(bg_rgb)
                    else:
                        alpha = min(1.0, (mx - 65) / 140.0)
                        fg = cyn_rgb if (g > r + 25) else acc_rgb
                        new_pixels.append((
                            int(bg_rgb[0] * (1 - alpha) + fg[0] * alpha),
                            int(bg_rgb[1] * (1 - alpha) + fg[1] * alpha),
                            int(bg_rgb[2] * (1 - alpha) + fg[2] * alpha),
                        ))
                recolored = Image.new("RGB", (54, 54))
                recolored.putdata(new_pixels)
                recolored = recolored.convert("RGBA")
                mask = Image.new("L", (54, 54), 0)
                ImageDraw.Draw(mask).rounded_rectangle([0, 0, 54, 54], radius=12, fill=255)
                recolored.putalpha(mask)
                self._logo_tk = ImageTk.PhotoImage(recolored)
                logo_canvas.create_image(158, 38, image=self._logo_tk)
            except Exception as e:
                log_event(f"Logo load error: {e}")

        logo_canvas.create_text(64, 30, text="Mocap", fill=t["text"], font=("Segoe UI", 19, "bold"))
        logo_canvas.create_text(64, 53, text="MEDIA STUDIO", fill=t["muted"], font=("Segoe UI", 7, "bold"))

    def _make_card(self, parent, pady=(0, 12), padx=0):
        t = self.theme
        frame = tk.Frame(parent, bg=t["card"], padx=16, pady=12, highlightbackground=t["border"], highlightthickness=1)
        frame.pack(fill="x", pady=pady, padx=padx)
        return frame

    def _build_ui(self):
        for w in self.root.winfo_children():
            w.destroy()

        t, tr = self.theme, self.tr
        is_rtl = (self.lang == "fa")
        anchor_main = "e" if is_rtl else "w"
        side_primary = "right" if is_rtl else "left"
        side_secondary = "left" if is_rtl else "right"

        self.root.configure(bg=t["bg"])
        container = tk.Frame(self.root, bg=t["bg"])
        container.pack(fill="both", expand=True)

        # --- منوی کناری ---
        sidebar = tk.Frame(container, bg=t["sidebar"], width=215, highlightbackground=t["border"], highlightthickness=1)
        sidebar.pack(side=side_primary, fill="y")
        sidebar.pack_propagate(False)
        self._draw_mocap_logo(sidebar)
        tk.Frame(sidebar, bg=t["border"], height=1).pack(fill="x", padx=14, pady=(2, 6))

        nav_frame = tk.Frame(sidebar, bg=t["sidebar"], padx=10, pady=2)
        nav_frame.pack(fill="x")
        self.nav_buttons = {}
        for key, text in (("audio", tr["nav_audio"]), ("video", tr["nav_video"]), ("convert", tr["nav_convert"]), ("screenshot", tr["nav_shot"]), ("help", tr["nav_help"])):
            btn = tk.Button(nav_frame, text=text, bg=t["sidebar"], fg=t["text"], activebackground=t["card_alt"], activeforeground=t["text"],
                            relief="flat", font=("Tahoma", 9, "bold"), anchor=anchor_main, padx=12, pady=8, cursor="hand2", command=lambda k=key: self.set_mode(k))
            btn.pack(fill="x", pady=3)
            self.nav_buttons[key] = btn

        bottom_side = tk.Frame(sidebar, bg=t["sidebar"], padx=12, pady=10)
        bottom_side.pack(side="bottom", fill="x")
        tk.Frame(bottom_side, bg=t["border"], height=1).pack(fill="x", pady=(0, 8))

        tk.Label(bottom_side, text=tr["lang_lbl"], bg=t["sidebar"], fg=t["muted"], font=("Tahoma", 8, "bold"), anchor=anchor_main).pack(fill="x", pady=(0, 4))
        lang_row = tk.Frame(bottom_side, bg=t["sidebar"])
        lang_row.pack(fill="x", pady=(0, 8))
        for code, lbl in (("fa", "فارسی"), ("en", "English")):
            active = (self.lang == code)
            tk.Button(lang_row, text=lbl, bg=t["accent"] if active else t["card_alt"], fg=t["accent_fg"] if active else t["text"],
                      relief="flat", font=("Tahoma", 8, "bold"), pady=4, cursor="hand2", command=lambda c=code: self.change_language(c)).pack(side="left", fill="x", expand=True, padx=2)

        tk.Label(bottom_side, text=tr["theme_lbl"], bg=t["sidebar"], fg=t["muted"], font=("Tahoma", 8, "bold"), anchor=anchor_main).pack(fill="x", pady=(0, 4))
        theme_grid = tk.Frame(bottom_side, bg=t["sidebar"])
        theme_grid.pack(fill="x", pady=(0, 8))
        for idx, tname in enumerate(THEMES.keys()):
            is_active = (tname == self.theme_name.get())
            tk.Button(theme_grid, text=tname, bg=t["accent"] if is_active else t["card_alt"], fg=t["accent_fg"] if is_active else t["text"],
                      relief="flat", font=("Tahoma", 7, "bold"), pady=4, cursor="hand2", command=lambda name=tname: self.change_theme(name)).grid(row=idx // 2, column=idx % 2, sticky="ew", padx=2, pady=2)
        theme_grid.columnconfigure(0, weight=1)
        theme_grid.columnconfigure(1, weight=1)

        tk.Button(bottom_side, text=tr["settings_btn"], bg=t["card_alt"], fg=t["text"], activebackground=t["accent"], activeforeground=t["accent_fg"],
                  relief="flat", font=("Tahoma", 8, "bold"), pady=7, cursor="hand2", command=self.open_settings_menu).pack(fill="x")

        # --- فضای کار اصلی ---
        self.main_area = tk.Frame(container, bg=t["bg"], padx=20, pady=16)
        self.main_area.pack(side=side_secondary, fill="both", expand=True)

        top_header = tk.Frame(self.main_area, bg=t["bg"])
        top_header.pack(fill="x", pady=(0, 12))
        self.page_title_lbl = tk.Label(top_header, text=tr["title_audio"], bg=t["bg"], fg=t["text"], font=("Tahoma", 12, "bold"))
        self.page_title_lbl.pack(side=side_primary)
        self.badge_lbl = tk.Label(top_header, text=tr["badge_audio"], bg=t["card"], fg=t["cyan"], font=("Tahoma", 8, "bold"), padx=10, pady=4, highlightbackground=t["border"], highlightthickness=1)
        self.badge_lbl.pack(side=side_secondary)

        # --- کارت تنظیمات ویدیو ---
        self.video_opts_frame = tk.Frame(self.main_area, bg=t["card"], padx=14, pady=10, highlightbackground=t["border"], highlightthickness=1)
        src_row = tk.Frame(self.video_opts_frame, bg=t["card"])
        src_row.pack(fill="x")
        tk.Button(src_row, text=tr["btn_fullscreen"], bg=t["card_alt"], fg=t["text"], relief="flat", font=("Tahoma", 8, "bold"), padx=10, pady=5, cursor="hand2", command=self.reset_to_fullscreen).pack(side=side_primary)
        tk.Button(src_row, text=tr["btn_region"], bg=t["accent"], fg=t["accent_fg"], relief="flat", font=("Tahoma", 8, "bold"), padx=10, pady=5, cursor="hand2", command=self.choose_region).pack(side=side_primary, padx=6)
        tk.Button(src_row, text=tr["btn_window"], bg=t["pink"], fg="#FFFFFF", relief="flat", font=("Tahoma", 8, "bold"), padx=10, pady=5, cursor="hand2", command=self.open_window_picker).pack(side=side_primary)

        info_icon = tk.Label(src_row, text="ⓘ", bg=t["card"], fg=t["cyan"], font=("Segoe UI", 12, "bold"), cursor="question_arrow", padx=5)
        info_icon.pack(side=side_primary, padx=4)
        HoverTooltip(info_icon, tr["win_tip"], t, is_rtl=is_rtl)

        self.win_size_row = tk.Frame(self.video_opts_frame, bg=t["card"])
        tk.Button(self.win_size_row, text=tr["btn_win_crop"], bg=t["cyan"], fg="#FFFFFF", relief="flat", font=("Tahoma", 8, "bold"), padx=8, pady=3, cursor="hand2", command=self.choose_window_crop).pack(side=side_primary)
        tk.Button(self.win_size_row, text=tr["btn_win_full"], bg=t["card_alt"], fg=t["text"], relief="flat", font=("Tahoma", 8, "bold"), padx=8, pady=3, cursor="hand2", command=self.reset_window_crop).pack(side=side_primary, padx=6)

        self.region_lbl = tk.Label(self.video_opts_frame, text=tr["src_fullscreen"], bg=t["card"], fg=t["cyan"], font=("Tahoma", 8, "bold"), anchor=anchor_main)
        self.region_lbl.pack(fill="x", pady=(6, 4))

        qual_row = tk.Frame(self.video_opts_frame, bg=t["card"])
        qual_row.pack(fill="x", pady=(2, 2))
        tk.Label(qual_row, text=tr["quality_lbl"], bg=t["card"], fg=t["text"], font=("Tahoma", 8, "bold")).pack(side=side_primary, padx=6)
        ttk.Combobox(qual_row, textvariable=self.quality_var, values=[tr["q_low"], tr["q_medium"], tr["q_high"], tr["q_ultra"]], state="readonly", width=19, font=("Tahoma", 8)).pack(side=side_primary)
        tk.Checkbutton(qual_row, text=tr["with_audio"], variable=self.record_audio_with_video, bg=t["card"], fg=t["text"], selectcolor=t["card_alt"], activebackground=t["card"], activeforeground=t["text"], font=("Tahoma", 8), cursor="hand2").pack(side=side_secondary, padx=(4, 0))
        tk.Checkbutton(qual_row, text=tr["show_cursor"], variable=self.show_cursor_var, bg=t["card"], fg=t["text"], selectcolor=t["card_alt"], activebackground=t["card"], activeforeground=t["text"], font=("Tahoma", 8), cursor="hand2").pack(side=side_secondary, padx=4)

        extra_row = tk.Frame(self.video_opts_frame, bg=t["card"])
        extra_row.pack(fill="x", pady=(4, 0))
        tk.Checkbutton(extra_row, text=tr["flip_rtl"], variable=self.flip_rtl_var, bg=t["card"], fg=t["text"], selectcolor=t["card_alt"], activebackground=t["card"], activeforeground=t["text"], font=("Tahoma", 8), cursor="hand2").pack(side=side_primary)

        # --- کارت اسلایدرها ---
        self.fx_frame = tk.Frame(self.main_area, bg=t["card"], padx=14, pady=10, highlightbackground=t["border"], highlightthickness=1)
        vol_row = tk.Frame(self.fx_frame, bg=t["card"])
        vol_row.pack(fill="x", pady=(0, 6))
        tk.Button(vol_row, text="↺", bg=t["card_alt"], fg=t["muted"], relief="flat", font=("Segoe UI", 8, "bold"), width=2, cursor="hand2", command=lambda: self._reset_slider("vol")).pack(side="left", padx=(0, 4))
        self.vol_val_lbl = tk.Label(vol_row, text=f"{self.volume_var.get():.2f}x", bg=t["card"], fg=t["cyan"], font=("Consolas", 10, "bold"), width=6, anchor="w")
        self.vol_val_lbl.pack(side="left")
        tk.Scale(vol_row, from_=0.33, to=3.0, resolution=0.05, orient="horizontal", variable=self.volume_var, showvalue=False, bg=t["card"], fg=t["text"], troughcolor=t["card_alt"], highlightthickness=0, activebackground=t["cyan"], command=self._on_vol_change).pack(side="left", fill="x", expand=True, padx=8)
        tk.Label(vol_row, text=tr["vol_lbl"], bg=t["card"], fg=t["text"], font=("Tahoma", 9, "bold"), width=11, anchor="e").pack(side="right")

        spd_row = tk.Frame(self.fx_frame, bg=t["card"])
        spd_row.pack(fill="x")
        tk.Button(spd_row, text="↺", bg=t["card_alt"], fg=t["muted"], relief="flat", font=("Segoe UI", 8, "bold"), width=2, cursor="hand2", command=lambda: self._reset_slider("spd")).pack(side="left", padx=(0, 4))
        self.spd_val_lbl = tk.Label(spd_row, text=f"{self.speed_var.get():.1f}x", bg=t["card"], fg=t["pink"], font=("Consolas", 10, "bold"), width=6, anchor="w")
        self.spd_val_lbl.pack(side="left")
        tk.Scale(spd_row, from_=0.2, to=5.0, resolution=0.1, orient="horizontal", variable=self.speed_var, showvalue=False, bg=t["card"], fg=t["text"], troughcolor=t["card_alt"], highlightthickness=0, activebackground=t["pink"], command=self._on_spd_change).pack(side="left", fill="x", expand=True, padx=8)
        tk.Label(spd_row, text=tr["spd_lbl"], bg=t["card"], fg=t["text"], font=("Tahoma", 9, "bold"), width=11, anchor="e").pack(side="right")

        # --- بخش ضبط ---
        self.recorder_section = tk.Frame(self.main_area, bg=t["bg"])
        self.card = self._make_card(self.recorder_section, pady=(10, 12))
        self.timer_lbl = tk.Label(self.card, text="00:00:00", bg=t["card"], fg=t["text"], font=("Consolas", 36, "bold"))
        self.timer_lbl.pack(pady=(4, 4))
        self.file_lbl = tk.Label(self.card, text=tr["auto_name_hint"], bg=t["card"], fg=t["muted"], font=("Tahoma", 8), wraplength=470, justify="center")
        self.file_lbl.pack(pady=(0, 4))

        btn_frame = tk.Frame(self.recorder_section, bg=t["bg"])
        btn_frame.pack(pady=(4, 4))
        self.stop_btn = CircleButton(btn_frame, 68, t["stop"], t["stop_hover"], t["disabled"], t["bg"], t["text"], t["muted"], "■", tr["btn_stop"], self.stop_recording)
        self.stop_btn.pack(side="left", padx=18)
        self.pause_btn = CircleButton(btn_frame, 68, t["pause"], t["pause_hover"], t["disabled"], t["bg"], t["text"], t["muted"], "❚❚", tr["btn_pause"], self.toggle_pause)
        self.pause_btn.pack(side="left", padx=18)
        self.record_btn = CircleButton(btn_frame, 78, t["record"], t["record_hover"], t["disabled"], t["bg"], t["text"], t["muted"], "●", tr["btn_rec"], self.start_recording)
        self.record_btn.pack(side="left", padx=18)
        self.pause_btn.set_enabled(False)
        self.stop_btn.set_enabled(False)

        # --- کارت مبدل ---
        self.convert_frame = tk.Frame(self.main_area, bg=t["card"], padx=18, pady=22, highlightbackground=t["border"], highlightthickness=1)
        tk.Label(self.convert_frame, text=tr["conv_desc"], bg=t["card"], fg=t["amber"], font=("Tahoma", 9, "bold")).pack(pady=(0, 14))
        tk.Button(self.convert_frame, text=tr["conv_pick"], bg=t["accent"], fg=t["accent_fg"], relief="flat", font=("Tahoma", 9, "bold"), padx=18, pady=8, cursor="hand2", command=self.choose_video_to_convert).pack()
        file_txt = os.path.basename(self.convert_video_path) if self.convert_video_path else tr["conv_none"]
        self.convert_file_lbl = tk.Label(self.convert_frame, text=file_txt, bg=t["card"], fg=t["muted"], font=("Tahoma", 8), wraplength=440, justify="center")
        self.convert_file_lbl.pack(pady=(10, 14))
        self.convert_start_btn = tk.Button(self.convert_frame, text=tr["conv_start"], bg=t["stop"], fg="#FFFFFF", relief="flat", font=("Tahoma", 10, "bold"), padx=24, pady=9, cursor="hand2", command=self.start_video_conversion)
        self.convert_start_btn.pack()
        self.convert_status_lbl = tk.Label(self.convert_frame, text="", bg=t["card"], fg=t["cyan"], font=("Tahoma", 9, "bold"))
        self.convert_status_lbl.pack(pady=(10, 0))

        # --- کارت اسکرین‌شات ---
        self.screenshot_frame = tk.Frame(self.main_area, bg=t["card"], padx=20, pady=24, highlightbackground=t["border"], highlightthickness=1)
        tk.Label(self.screenshot_frame, text=tr["shot_desc"], bg=t["card"], fg=t["green"], font=("Tahoma", 8, "bold"), wraplength=460).pack(pady=(0, 18))
        tk.Button(self.screenshot_frame, text=tr["shot_full"], bg=t["cyan"], fg="#FFFFFF", relief="flat", font=("Tahoma", 10, "bold"), pady=12, cursor="hand2", command=self.take_fullscreen_shot).pack(fill="x", pady=(0, 12))
        tk.Button(self.screenshot_frame, text=tr["shot_region"], bg=t["pink"], fg="#FFFFFF", relief="flat", font=("Tahoma", 10, "bold"), pady=12, cursor="hand2", command=self.take_region_shot).pack(fill="x", pady=(0, 12))
        tk.Button(self.screenshot_frame, text=tr["shot_open"], bg=t["accent"], fg=t["accent_fg"], relief="flat", font=("Tahoma", 9, "bold"), pady=10, cursor="hand2", command=self.open_existing_image_in_editor).pack(fill="x")

        # --- بخش راهنما و گزارش خطا ---
        self.help_frame = tk.Frame(self.main_area, bg=t["bg"])
        guide_card = tk.Frame(self.help_frame, bg=t["card"], padx=14, pady=10, highlightbackground=t["border"], highlightthickness=1)
        guide_card.pack(fill="x", pady=(0, 10))
        tk.Label(guide_card, text=tr["help_title"], bg=t["card"], fg=t["cyan"], font=("Tahoma", 9, "bold"), anchor=anchor_main).pack(fill="x", pady=(0, 6))

        guide_box = tk.Text(guide_card, height=11, bg=t["card"], fg=t["text"], font=("Tahoma", 8), relief="flat", highlightthickness=0, wrap="word", padx=4, pady=2)
        guide_box.pack(fill="x")
        guide_box.tag_configure("rtl", justify="right", font=("Tahoma", 8))
        guide_box.tag_configure("cmd", justify="left", font=("Consolas", 8), foreground=t["cyan"])

        if self.lang == "fa":
            lines = [
                ("rtl", "\u202b▪ در حالت پنجره خاص، پنجره انتخاب‌شده را کوچک نکنید.\u202c\n"),
                ("rtl", "\u202b▪ اگر منوی مرورگر شما فارسی است و تصویر برعکس ضبط می‌شود، تیک اصلاح تصویر برعکس را بزنید.\u202c\n"),
                ("rtl", "\u202b▪ برای رفع سفید شدن ویدیو در کروم، وارد آدرس زیر شوید و شتاب‌دهنده گرافیکی را خاموش کنید:\u202c\n"),
                ("cmd", "chrome://settings/system\n"),
                ("rtl", "\u202b▪ برای رفع سیاه شدن کروم (دسکتاپ یا تسکبار)، روی آیکون کروم راست‌کلیک کرده و وارد تنظیمات میانبر شوید و با یک فاصله این عبارت را به انتهای مسیر هدف اضافه کنید:\u202c\n"),
                ("cmd", "--disable-features=CalculateNativeWinOcclusion\n"),
                ("rtl", "\u202b▪ برای رفع توقف ویدیو در فایرفاکس، وارد تنظیمات پیشرفته زیر شوید و مقدار گزینه بعدی را خاموش کنید:\u202c\n"),
                ("cmd", "about:config  ->  widget.windows.window_occlusion_tracking.enabled = false\n"),
                ("rtl", "\u202b▪ کلید میانبر اسکرین‌شات محدوده (\u202aPrtSc\u202c) و کل صفحه (\u202aShift+PrtSc\u202c) در تمام برنامه‌ها فعال است.\u202c\n"),
            ]
        else:
            lines = [
                ("cmd", "• Keep the target window un-minimized in Specific Window mode.\n"),
                ("cmd", "• Enable 'Fix Mirrored' if capturing a Right-to-Left browser UI.\n"),
                ("cmd", "• Chrome white video fix: Disable Graphics Acceleration in chrome://settings/system\n"),
                ("cmd", "• Chrome black screen fix (Taskbar/Desktop): Append to Shortcut Target:\n"),
                ("cmd", "  --disable-features=CalculateNativeWinOcclusion\n"),
                ("cmd", "• Firefox freeze fix: about:config -> widget.windows.window_occlusion_tracking.enabled = false\n"),
                ("cmd", "• Hotkeys: PrtSc (Region) | Shift+PrtSc (Full Screen).\n"),
            ]
        for tag, text in lines:
            guide_box.insert("end", text, tag)
        guide_box.config(state="disabled")

        bug_card = tk.Frame(self.help_frame, bg=t["card"], padx=14, pady=10, highlightbackground=t["border"], highlightthickness=1)
        bug_card.pack(fill="both", expand=True)
        bug_top = tk.Frame(bug_card, bg=t["card"])
        bug_top.pack(fill="x", pady=(0, 6))
        tk.Label(bug_top, text=tr["bug_title"], bg=t["card"], fg=t["amber"], font=("Tahoma", 9, "bold")).pack(side=side_primary)
        tk.Button(bug_top, text=tr["bug_copy"], bg=t["accent"], fg=t["accent_fg"], relief="flat", font=("Tahoma", 8, "bold"), padx=10, pady=3, cursor="hand2", command=self.copy_bug_report).pack(side=side_secondary)
        tk.Button(bug_top, text=tr["bug_refresh"], bg=t["card_alt"], fg=t["text"], relief="flat", font=("Tahoma", 8, "bold"), padx=8, pady=3, cursor="hand2", command=self.refresh_bug_log_view).pack(side=side_secondary, padx=6)

        self.log_text = tk.Text(bug_card, height=8, bg=t["canvas_bg"], fg=t["muted"], font=("Consolas", 8), relief="flat", padx=8, pady=6, highlightbackground=t["border"], highlightthickness=1)
        self.log_text.pack(fill="both", expand=True)

        if self.capture_source == "window" and self.selected_window_hwnd:
            self.win_size_row.pack(fill="x", pady=(6, 0), before=self.region_lbl)
            self._update_window_label()
        elif self.capture_source == "region" and self.selected_region:
            r = self.selected_region
            self.region_lbl.config(text=tr["src_region"].format(w=r["width"], h=r["height"]))

        self.set_mode(self.mode)

    def refresh_bug_log_view(self):
        if hasattr(self, "log_text"):
            self.log_text.config(state="normal")
            self.log_text.delete("1.0", "end")
            self.log_text.insert("1.0", "\n".join(DEBUG_LOGS) or "No logs yet.")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

    def copy_bug_report(self):
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(DEBUG_LOGS) or "No logs.")
        self.badge_lbl.config(text=self.tr["bug_copied"], fg=self.theme["stop"])

    def _reset_slider(self, which: str):
        if which == "vol":
            self.volume_var.set(1.0)
            self.vol_val_lbl.config(text="1.00x")
        else:
            self.speed_var.set(1.0)
            self.spd_val_lbl.config(text="1.0x")

    def _on_vol_change(self, val):
        self.vol_val_lbl.config(text=f"{float(val):.2f}x")

    def _on_spd_change(self, val):
        self.spd_val_lbl.config(text=f"{float(val):.1f}x")

    def set_mode(self, new_mode: str):
        if self.is_recording:
            return
        t, tr = self.theme, self.tr
        self.mode = new_mode
        for k, btn in self.nav_buttons.items():
            btn.config(bg=t["accent"] if k == new_mode else t["sidebar"], fg=t["accent_fg"] if k == new_mode else t["text"])
        for f in (self.video_opts_frame, self.fx_frame, self.recorder_section, self.convert_frame, self.screenshot_frame, self.help_frame):
            f.pack_forget()

        if new_mode == "audio":
            self.page_title_lbl.config(text=tr["title_audio"])
            self.badge_lbl.config(text=tr["badge_audio"], fg=t["cyan"])
            self.fx_frame.pack(fill="x", pady=(0, 10))
            self.recorder_section.pack(fill="both", expand=True)
        elif new_mode == "video":
            self.page_title_lbl.config(text=tr["title_video"])
            self.badge_lbl.config(text=tr["badge_video"], fg=t["pink"])
            self.video_opts_frame.pack(fill="x", pady=(0, 10))
            self.fx_frame.pack(fill="x", pady=(0, 10))
            self.recorder_section.pack(fill="both", expand=True)
        elif new_mode == "convert":
            self.page_title_lbl.config(text=tr["title_convert"])
            self.badge_lbl.config(text=tr["badge_convert"], fg=t["amber"])
            self.fx_frame.pack(fill="x", pady=(0, 12))
            self.convert_frame.pack(fill="x")
        elif new_mode == "screenshot":
            self.page_title_lbl.config(text=tr["title_shot"])
            self.badge_lbl.config(text=tr["badge_shot"], fg=t["green"])
            self.screenshot_frame.pack(fill="x", pady=(8, 0))
        elif new_mode == "help":
            self.page_title_lbl.config(text=tr["title_help"])
            self.badge_lbl.config(text=tr["badge_help"], fg=t["accent"])
            self.help_frame.pack(fill="both", expand=True)
            self.refresh_bug_log_view()

    def take_fullscreen_shot(self):
        self.root.withdraw()
        self.root.update()
        time.sleep(0.25)
        with mss.mss() as sct:
            sct_img = sct.grab(sct.monitors[1])
            pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        self.root.deiconify()
        ScreenshotEditor(self.root, pil_img, self.settings["save_folder"], self.theme, self.tr)

    def take_region_shot(self):
        RegionSelector(self.root, self._on_shot_region_selected, self.tr["region_prompt"], restore_parent=False)

    def _on_shot_region_selected(self, region):
        time.sleep(0.2)
        with mss.mss() as sct:
            sct_img = sct.grab(region)
            pil_img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        self.root.deiconify()
        ScreenshotEditor(self.root, pil_img, self.settings["save_folder"], self.theme, self.tr)

    def open_existing_image_in_editor(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if path:
            ScreenshotEditor(self.root, Image.open(path), self.settings["save_folder"], self.theme, self.tr)

    def choose_video_to_convert(self):
        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm *.m4v *.ts"), ("All", "*.*")])
        if path:
            self.convert_video_path = path
            self.convert_file_lbl.config(text=os.path.basename(path), fg=self.theme["text"])
            self.convert_status_lbl.config(text="")

    def start_video_conversion(self):
        if not self.convert_video_path or not os.path.isfile(self.convert_video_path):
            return
        base_name = sanitize_filename(os.path.splitext(os.path.basename(self.convert_video_path))[0]) or "audio_output"
        save_dir = self.settings["save_folder"] if os.path.isdir(self.settings["save_folder"]) else os.path.dirname(self.convert_video_path)
        if self.settings["ask_every_time"]:
            final_path = filedialog.asksaveasfilename(initialdir=save_dir, initialfile=f"{base_name}.mp3", defaultextension=".mp3", filetypes=[("MP3", "*.mp3")])
            if not final_path:
                return
        else:
            final_path = self._get_unique_path(save_dir, base_name, ".mp3")
        self.convert_start_btn.config(state="disabled")
        self.convert_status_lbl.config(text=self.tr["conv_working"], fg=self.theme["cyan"])
        threading.Thread(target=self._convert_worker, args=(self.convert_video_path, final_path), daemon=True).start()

    def _convert_worker(self, input_video: str, output_mp3: str):
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            vol, spd = round(float(self.volume_var.get()), 2), round(float(self.speed_var.get()), 2)
            afilters = []
            if abs(vol - 1.0) >= 0.04:
                afilters.append(f"volume={vol}")
            if abs(spd - 1.0) >= 0.05:
                afilters.append(build_atempo_chain(spd))
            cmd = [ffmpeg_exe, "-y", "-i", input_video, "-vn"] + (["-af", ",".join(afilters)] if afilters else []) + ["-c:a", "libmp3lame", "-b:a", "192k", output_mp3]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.root.after(0, lambda: self._on_convert_done(True, output_mp3))
        except Exception as e:
            log_event(f"Convert error: {e}")
            self.root.after(0, lambda err=e: self._on_convert_done(False, str(err)))

    def _on_convert_done(self, success: bool, info: str):
        self.convert_start_btn.config(state="normal")
        if success:
            self.convert_status_lbl.config(text=self.tr["conv_done"], fg=self.theme["stop"])
            subprocess.Popen(["explorer", "/select,", os.path.normpath(info)])
        else:
            self.convert_status_lbl.config(text=self.tr["badge_err"], fg=self.theme["record"])
            messagebox.showerror("Error", info)

    def open_window_picker(self):
        if self.is_recording:
            return
        t, tr = self.theme, self.tr
        win = tk.Toplevel(self.root)
        win.title(tr["win_pick_title"])
        win.geometry("460x350")
        win.configure(bg=t["bg"])
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text=tr["win_pick_lbl"], bg=t["bg"], fg=t["cyan"], font=("Tahoma", 9, "bold"), anchor="e" if self.lang == "fa" else "w").pack(fill="x", padx=14, pady=(12, 8))
        listbox = tk.Listbox(win, bg=t["card"], fg=t["text"], selectbackground=t["accent"], selectforeground=t["accent_fg"], font=("Tahoma", 9), relief="flat", highlightbackground=t["border"], highlightthickness=1)
        listbox.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        windows = list_open_windows()
        for _hwnd, title in windows:
            listbox.insert("end", title)

        def confirm():
            sel = listbox.curselection()
            if not sel:
                return
            hwnd, title = windows[sel[0]]
            self.capture_source, self.selected_window_hwnd, self.selected_window_title, self.window_crop = "window", hwnd, title, None
            self.win_size_row.pack(fill="x", pady=(6, 0), before=self.region_lbl)
            self._update_window_label()
            log_event(f"Selected window: {title[:60]} | RTL={is_window_rtl(hwnd)}")
            win.destroy()

        tk.Button(win, text=tr["win_pick_ok"], bg=t["stop"], fg="#FFFFFF", relief="flat", font=("Tahoma", 9, "bold"), padx=18, pady=7, cursor="hand2", command=confirm).pack(pady=(0, 12))

    def _update_window_label(self):
        short = self.selected_window_title[:30] + "..." if len(self.selected_window_title) > 30 else self.selected_window_title
        if self.window_crop:
            c = self.window_crop
            self.region_lbl.config(text=self.tr["src_win_crop"].format(t=short, w=c["w"], h=c["h"]))
        else:
            self.region_lbl.config(text=self.tr["src_win_full"].format(t=short))

    def choose_window_crop(self):
        if self.is_recording or not self.selected_window_hwnd:
            return
        user32 = ctypes.windll.user32
        if not user32.IsWindow(self.selected_window_hwnd):
            self.reset_to_fullscreen()
            return
        if user32.IsIconic(self.selected_window_hwnd):
            user32.ShowWindow(self.selected_window_hwnd, 9)
        user32.SetForegroundWindow(self.selected_window_hwnd)
        time.sleep(0.2)
        RegionSelector(self.root, self._on_window_crop_selected, self.tr["region_prompt"])

    def _on_window_crop_selected(self, region):
        rect = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(self.selected_window_hwnd, ctypes.byref(rect))
        rx, ry = max(0, region["left"] - rect.left), max(0, region["top"] - rect.top)
        cw = min(region["width"], (rect.right - rect.left) - rx)
        ch = min(region["height"], (rect.bottom - rect.top) - ry)
        cw -= cw % 2
        ch -= ch % 2
        if cw >= 40 and ch >= 40:
            self.window_crop = {"x": rx, "y": ry, "w": cw, "h": ch}
            self._update_window_label()

    def reset_window_crop(self):
        if not self.is_recording and self.capture_source == "window":
            self.window_crop = None
            self._update_window_label()

    def choose_region(self):
        if not self.is_recording:
            RegionSelector(self.root, self._on_region_selected, self.tr["region_prompt"])

    def _on_region_selected(self, region):
        self.capture_source, self.selected_region = "region", region
        self.selected_window_hwnd = self.window_crop = None
        self.selected_window_title = ""
        self.win_size_row.pack_forget()
        self.region_lbl.config(text=self.tr["src_region"].format(w=region["width"], h=region["height"]))

    def reset_to_fullscreen(self):
        self.capture_source = "fullscreen"
        self.selected_region = self.selected_window_hwnd = self.window_crop = None
        self.selected_window_title = ""
        self.win_size_row.pack_forget()
        self.region_lbl.config(text=self.tr["src_fullscreen"])

    def open_settings_menu(self):
        t, tr = self.theme, self.tr
        anchor_main = "e" if self.lang == "fa" else "w"
        win = tk.Toplevel(self.root)
        win.title(f"{tr['set_title']} — {APP_TITLE}")
        win.geometry("460x310")
        win.resizable(False, False)
        win.configure(bg=t["bg"])
        win.transient(self.root)
        win.grab_set()

        top_bar = tk.Frame(win, bg=t["accent"], height=46)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text=tr["set_title"], bg=t["accent"], fg=t["accent_fg"], font=("Tahoma", 10, "bold")).pack(side="right" if self.lang == "fa" else "left", padx=14, pady=10)

        body = tk.Frame(win, bg=t["bg"], padx=18, pady=14)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=tr["set_folder"], bg=t["bg"], fg=t["text"], font=("Tahoma", 9, "bold"), anchor=anchor_main).pack(fill="x", pady=(0, 6))
        path_frame = tk.Frame(body, bg=t["bg"])
        path_frame.pack(fill="x", pady=(0, 12))

        folder_var = tk.StringVar(value=self.settings["save_folder"])
        tk.Button(path_frame, text=tr["set_browse"], bg=t["accent"], fg=t["accent_fg"], relief="flat", font=("Tahoma", 9, "bold"), padx=10, pady=4, cursor="hand2",
                  command=lambda: (lambda p: p and folder_var.set(p))(filedialog.askdirectory(initialdir=folder_var.get()))).pack(side="left", padx=(0, 8))
        tk.Entry(path_frame, textvariable=folder_var, bg=t["card"], fg=t["text"], insertbackground=t["text"], relief="flat", font=("Segoe UI", 9), highlightbackground=t["border"], highlightthickness=1).pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 4))

        ask_var = tk.BooleanVar(value=self.settings["ask_every_time"])
        startup_var = tk.BooleanVar(value=self.settings.get("start_with_windows", False))
        chk_card = tk.Frame(body, bg=t["card"], padx=12, pady=10, highlightbackground=t["border"], highlightthickness=1)
        chk_card.pack(fill="x", pady=(0, 14))
        tk.Checkbutton(chk_card, text=tr["set_ask"], variable=ask_var, bg=t["card"], fg=t["text"], selectcolor=t["card_alt"], activebackground=t["card"], activeforeground=t["text"], font=("Tahoma", 8), anchor=anchor_main, cursor="hand2").pack(fill="x", pady=(0, 6))
        tk.Checkbutton(chk_card, text=tr["set_startup"], variable=startup_var, bg=t["card"], fg=t["text"], selectcolor=t["card_alt"], activebackground=t["card"], activeforeground=t["text"], font=("Tahoma", 8), anchor=anchor_main, cursor="hand2").pack(fill="x")

        def save_and_close():
            chosen = folder_var.get().strip()
            if not chosen or not os.path.isdir(chosen):
                return
            self.settings["save_folder"], self.settings["ask_every_time"], self.settings["start_with_windows"] = chosen, ask_var.get(), startup_var.get()
            set_windows_startup(startup_var.get())
            self.save_settings()
            win.destroy()

        tk.Button(body, text=tr["set_save"], bg=t["stop"], fg="#FFFFFF", relief="flat", font=("Tahoma", 10, "bold"), padx=22, pady=6, cursor="hand2", command=save_and_close).pack()

    def start_recording(self):
        if self.is_recording:
            return
        if self.mode == "video" and self.capture_source == "window":
            if not self.selected_window_hwnd or not ctypes.windll.user32.IsWindow(self.selected_window_hwnd):
                self.reset_to_fullscreen()
                return
            if ctypes.windll.user32.IsIconic(self.selected_window_hwnd):
                messagebox.showwarning(APP_TITLE, self.tr["win_tip"])
                return

        target_t = self.selected_window_title if (self.mode == "video" and self.capture_source == "window") else ""
        self.detected_name = detect_playing_media_name(target_t)
        self.recorded_frames, self.elapsed_seconds = [], 0.0
        self.stop_event.clear()
        self.is_recording, self.is_paused, self.last_tick = True, False, time.time()

        self.record_btn.set_enabled(False)
        self.pause_btn.set_enabled(True)
        self.stop_btn.set_enabled(True)
        self.pause_btn.set_symbol_and_label("❚❚", self.tr["btn_pause"])

        ext = ".mp3" if self.mode == "audio" else ".mp4"
        self.file_lbl.config(text=self.detected_name)
        log_event(f"Start recording | mode={self.mode} | source={self.capture_source}")

        if (self.mode == "audio") or self.record_audio_with_video.get():
            self.audio_thread = threading.Thread(target=self._audio_worker, daemon=True)
            self.audio_thread.start()

        if self.mode == "video":
            self.badge_lbl.config(text=self.tr["badge_rec_vid"], fg=self.theme["record"])
            self.temp_video_path = os.path.join(tempfile.gettempdir(), f"mocap_vid_{int(time.time())}.mp4")
            if self.capture_source != "window":
                self.root.iconify()
                self.root.update()
                time.sleep(0.25)
            self.video_thread = threading.Thread(target=self._video_worker, daemon=True)
            self.video_thread.start()
        else:
            self.badge_lbl.config(text=self.tr["badge_rec_aud"], fg=self.theme["record"])
        self._update_timer()

    def _audio_worker(self):
        p = stream = None
        try:
            p = pyaudio.PyAudio()
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
            self.channels, self.sample_rate = int(default_speakers["maxInputChannels"]), int(default_speakers["defaultSampleRate"])
            stream = p.open(format=pyaudio.paInt16, channels=self.channels, rate=self.sample_rate, frames_per_buffer=1024, input=True, input_device_index=default_speakers["index"])
            while self.is_recording and not self.stop_event.is_set():
                data = stream.read(1024, exception_on_overflow=False)
                if not self.is_paused:
                    self.recorded_frames.append(data)
        except Exception as e:
            log_event(f"Audio error: {e}")
            self.is_recording = False
            self.root.after(0, lambda err=e: self._handle_error(str(err)))
        finally:
            if stream:
                _safe_call(stream.stop_stream)
                _safe_call(stream.close)
            if p:
                _safe_call(p.terminate)

    def _run_wgc_in_subprocess(self, fps, crf):
        stamp, tmp = str(int(time.time() * 1000)), tempfile.gettempdir()
        cfg_path = os.path.join(tmp, f"mocap_cfg_{stamp}.json")
        self.wgc_stop_flag = os.path.join(tmp, f"mocap_stop_{stamp}.flag")
        self.wgc_pause_flag = os.path.join(tmp, f"mocap_pause_{stamp}.flag")
        res_path = os.path.join(tmp, f"mocap_res_{stamp}.json")

        cfg = {
            "window_title": self.selected_window_title, "output_path": self.temp_video_path,
            "fps": fps, "crf": crf, "cursor_capture": self.show_cursor_var.get(),
            "crop": self.window_crop,
            "hflip": self.flip_rtl_var.get() or is_window_rtl(self.selected_window_hwnd),
            "stop_flag": self.wgc_stop_flag, "pause_flag": self.wgc_pause_flag, "result_path": res_path,
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False)

        cmd = [sys.executable, "--wgc-worker", cfg_path] if getattr(sys, "frozen", False) else [sys.executable, os.path.abspath(__file__), "--wgc-worker", cfg_path]
        self.wgc_proc = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

        while self.wgc_proc.poll() is None and not self.stop_event.is_set():
            time.sleep(0.1)

        if self.wgc_proc.poll() is None:
            try:
                open(self.wgc_stop_flag, "w").close()
                self.wgc_proc.wait(timeout=4.0)
            except Exception:
                _safe_call(self.wgc_proc.kill)

        if os.path.exists(res_path):
            try:
                with open(res_path, "r", encoding="utf-8") as rf:
                    res = json.load(rf)
                log_event(f"WGC worker finished | frames={res.get('frames', 0)} | black_skipped={res.get('black_skipped', 0)} | err={res.get('error', '')}")
            except Exception:
                pass

        for p in (cfg_path, self.wgc_stop_flag, self.wgc_pause_flag, res_path):
            if p and os.path.exists(p):
                _safe_call(lambda path=p: os.remove(path))
        self.wgc_proc = self.wgc_stop_flag = self.wgc_pause_flag = None

    def _video_worker(self):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        preset = self._get_selected_quality_preset()
        fps, crf = preset["fps"], preset["crf"]

        if self.capture_source == "window" and HAS_WGC:
            try:
                self._run_wgc_in_subprocess(fps, crf)
                if self.temp_video_path and os.path.exists(self.temp_video_path) and os.path.getsize(self.temp_video_path) > 1024:
                    return
            except Exception as e:
                log_event(f"WGC subprocess error: {e}")

        proc = None
        try:
            vf_args = []
            if self.capture_source == "window":
                rect = wintypes.RECT()
                ctypes.windll.user32.GetWindowRect(self.selected_window_hwnd, ctypes.byref(rect))
                w = (rect.right - rect.left) - ((rect.right - rect.left) % 2)
                h = (rect.bottom - rect.top) - ((rect.bottom - rect.top) % 2)
                monitor = None
                if self.window_crop:
                    c = self.window_crop
                    cw, ch = min(c["w"], w - c["x"]), min(c["h"], h - c["y"])
                    cw -= cw % 2
                    ch -= ch % 2
                    if cw >= 40 and ch >= 40:
                        vf_args = ["-vf", f"crop={cw}:{ch}:{c['x']}:{c['y']}"]
            else:
                sct_init = mss.mss()
                if self.capture_source == "region" and self.selected_region:
                    monitor = dict(self.selected_region)
                else:
                    mon = sct_init.monitors[1]
                    monitor = {"left": mon["left"], "top": mon["top"], "width": mon["width"] - (mon["width"] % 2), "height": mon["height"] - (mon["height"] % 2)}
                w, h = monitor["width"], monitor["height"]
                sct_init.close()

            cmd = [ffmpeg_exe, "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-"] + vf_args + ["-c:v", "libx264", "-preset", "ultrafast", "-crf", crf, "-pix_fmt", "yuv420p", "-movflags", "+faststart", self.temp_video_path]
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            frame_interval, next_frame_time = 1.0 / fps, time.perf_counter()
            with mss.mss() as sct:
                while self.is_recording and not self.stop_event.is_set():
                    if self.is_paused:
                        time.sleep(0.05)
                        next_frame_time = time.perf_counter()
                        continue
                    frame_bytes = capture_window_bgra_fallback(self.selected_window_hwnd, w, h) if self.capture_source == "window" else sct.grab(monitor).bgra
                    if frame_bytes and proc.stdin:
                        proc.stdin.write(frame_bytes)
                    next_frame_time += frame_interval
                    sl = next_frame_time - time.perf_counter()
                    if sl > 0:
                        time.sleep(sl)
                    else:
                        next_frame_time = time.perf_counter()
        except Exception as e:
            log_event(f"Video worker error: {e}")
            self.is_recording = False
            self.root.after(0, lambda err=e: self._handle_error(str(err)))
        finally:
            if proc:
                try:
                    if proc.stdin:
                        proc.stdin.close()
                    proc.wait(timeout=10)
                except Exception:
                    _safe_call(proc.kill)

    def _handle_error(self, msg: str):
        self.record_btn.set_enabled(True)
        self.pause_btn.set_enabled(False)
        self.stop_btn.set_enabled(False)
        self.badge_lbl.config(text=self.tr["badge_err"], fg=self.theme["record"])
        messagebox.showerror("Error", msg)

    def toggle_pause(self):
        if not self.is_recording:
            return
        self.is_paused = not self.is_paused
        if self.wgc_pause_flag:
            if self.is_paused:
                _safe_call(lambda: open(self.wgc_pause_flag, "w").close())
            elif os.path.exists(self.wgc_pause_flag):
                _safe_call(lambda: os.remove(self.wgc_pause_flag))
        if self.is_paused:
            self.pause_btn.set_symbol_and_label("▶", self.tr["btn_resume"])
            self.badge_lbl.config(text=self.tr["badge_paused"], fg=self.theme["pause"])
        else:
            self.last_tick = time.time()
            self.pause_btn.set_symbol_and_label("❚❚", self.tr["btn_pause"])
            self.badge_lbl.config(text=self.tr["badge_rec_vid"] if self.mode == "video" else self.tr["badge_rec_aud"], fg=self.theme["record"])

    def _update_timer(self):
        if self.is_recording:
            now = time.time()
            if not self.is_paused:
                self.elapsed_seconds += now - self.last_tick
            self.last_tick = now
            hrs, rem = divmod(int(self.elapsed_seconds), 3600)
            mins, secs = divmod(rem, 60)
            self.timer_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
            self.root.after(200, self._update_timer)

    def stop_recording(self):
        if not self.is_recording:
            return
        was_window_capture = (self.mode == "video" and self.capture_source == "window")
        self.is_recording = self.is_paused = False
        self.stop_event.set()
        if self.wgc_stop_flag:
            _safe_call(lambda: open(self.wgc_stop_flag, "w").close())
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.5)
        if self.video_thread and self.video_thread.is_alive():
            self.video_thread.join(timeout=6.0)
        self.audio_thread = self.video_thread = None

        self.record_btn.set_enabled(True)
        self.pause_btn.set_enabled(False)
        self.stop_btn.set_enabled(False)
        self.pause_btn.set_symbol_and_label("❚❚", self.tr["btn_pause"])

        if was_window_capture:
            self.reset_to_fullscreen()
            gc.collect()
            log_event("Window capture state cleared and reset to fullscreen")

        if self.mode == "audio" and not self.recorded_frames:
            return
        if self.mode == "video" and (not self.temp_video_path or not os.path.exists(self.temp_video_path)):
            return

        self.badge_lbl.config(text=self.tr["badge_saving"], fg=self.theme["cyan"])
        self.root.update_idletasks()

        ext = ".mp3" if self.mode == "audio" else ".mp4"
        save_dir = self.settings["save_folder"] if os.path.isdir(self.settings["save_folder"]) else os.path.expanduser("~")
        if self.settings["ask_every_time"]:
            final_path = filedialog.asksaveasfilename(initialdir=save_dir, initialfile=f"{self.detected_name}{ext}", defaultextension=ext, filetypes=[(ext.upper(), f"*{ext}")])
            if not final_path:
                self._cleanup_temp_files()
                self.recorded_frames = []
                gc.collect()
                self.badge_lbl.config(text=self.tr["badge_canceled"], fg=self.theme["muted"])
                return
        else:
            final_path = self._get_unique_path(save_dir, self.detected_name, ext)

        try:
            self._save_as_mp3(final_path) if self.mode == "audio" else self._save_as_mp4(final_path)
            self.badge_lbl.config(text=self.tr["badge_saved"], fg=self.theme["stop"])
            self.timer_lbl.config(text="00:00:00")
            log_event(f"Saved successfully: {os.path.basename(final_path)}")
            subprocess.Popen(["explorer", "/select,", os.path.normpath(final_path)])
        except Exception as e:
            log_event(f"Save error: {e}")
            self.badge_lbl.config(text=self.tr["badge_err"], fg=self.theme["record"])
            messagebox.showerror("Error", str(e))
        finally:
            self._cleanup_temp_files()
            self.recorded_frames = []
            gc.collect()

    def _get_unique_path(self, folder: str, base_name: str, ext: str) -> str:
        candidate, counter = os.path.join(folder, f"{base_name}{ext}"), 1
        while os.path.exists(candidate):
            candidate = os.path.join(folder, f"{base_name} ({counter}){ext}")
            counter += 1
        return candidate

    def _write_temp_wav(self) -> str:
        raw_pcm, channels = b"".join(self.recorded_frames), self.channels
        if channels > 2:
            samples, stereo = array.array("h"), array.array("h")
            samples.frombytes(raw_pcm)
            for i in range(0, len(samples) - channels + 1, channels):
                stereo.append(samples[i])
                stereo.append(samples[i + 1])
            raw_pcm, channels = stereo.tobytes(), 2
        wav_path = os.path.join(tempfile.gettempdir(), f"mocap_aud_{int(time.time())}.wav")
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(raw_pcm)
        self.temp_audio_path = wav_path
        return wav_path

    def _save_as_mp3(self, filepath: str):
        ffmpeg_exe, wav_path = imageio_ffmpeg.get_ffmpeg_exe(), self._write_temp_wav()
        vol, spd = round(float(self.volume_var.get()), 2), round(float(self.speed_var.get()), 2)
        afilters = []
        if abs(vol - 1.0) >= 0.04:
            afilters.append(f"volume={vol}")
        if abs(spd - 1.0) >= 0.05:
            afilters.append(build_atempo_chain(spd))
        cmd = [ffmpeg_exe, "-y", "-i", wav_path] + (["-af", ",".join(afilters)] if afilters else []) + ["-c:a", "libmp3lame", "-b:a", "192k", filepath]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def _save_as_mp4(self, filepath: str):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        vol, spd = round(float(self.volume_var.get()), 2), round(float(self.speed_var.get()), 2)
        has_audio = self.record_audio_with_video.get() and bool(self.recorded_frames)
        speed_changed, vol_changed = abs(spd - 1.0) >= 0.05, abs(vol - 1.0) >= 0.04

        if not has_audio and not speed_changed:
            if os.path.exists(filepath):
                os.remove(filepath)
            os.replace(self.temp_video_path, filepath)
            self.temp_video_path = None
            return

        cmd = [ffmpeg_exe, "-y", "-i", self.temp_video_path]
        if has_audio:
            cmd += ["-i", self._write_temp_wav()]
        cmd += (["-vf", f"setpts={1.0 / spd:.4f}*PTS", "-c:v", "libx264", "-preset", "veryfast"] if speed_changed else ["-c:v", "copy"])
        if has_audio:
            afilters = []
            if vol_changed:
                afilters.append(f"volume={vol}")
            if speed_changed:
                afilters.append(build_atempo_chain(spd))
            if afilters:
                cmd += ["-af", ",".join(afilters)]
            cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
        cmd += ["-movflags", "+faststart", filepath]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)

    def _cleanup_temp_files(self):
        for path in (self.temp_video_path, self.temp_audio_path):
            if path and os.path.exists(path):
                _safe_call(lambda p=path: os.remove(p))
        self.temp_video_path = self.temp_audio_path = None

    def _on_close(self):
        self.is_recording = False
        self.stop_event.set()
        if self.wgc_proc and self.wgc_proc.poll() is None:
            _safe_call(self.wgc_proc.kill)
        self._cleanup_temp_files()
        self.root.destroy()


def _safe_call(fn):
    try:
        fn()
    except Exception:
        pass


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--wgc-worker":
        _run_wgc_subprocess_worker(sys.argv[2])
    else:
        root = tk.Tk()
        app = MocapApp(root)
        root.mainloop()

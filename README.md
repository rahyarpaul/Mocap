# Mocap — Media Studio

ابزار سبک و کاربردی ویندوز برای ضبط صدای سیستم، ضبط صفحه و پنجره، تبدیل ویدیو به MP3، اسکرین‌شات با کلید میانبر سراسری و ویرایشگر تصویر.

A lightweight Windows utility for system audio capture, full-screen/region/window recording, video-to-MP3 conversion, global hotkey screenshots, and built-in image annotation.

---

## فارسی

### امکانات اصلی
* **ضبط صدای سیستم:** ضبط صدای داخلی ویندوز با امکان تنظیم شدت صدا و سرعت پخش و ذخیره به‌صورت MP3.
* **ضبط ویدیو و صفحه:** ضبط کل صفحه، محدوده دلخواه یا پنجره خاص (با پشتیبانی از Windows Graphics Capture در پروسس مجزا)، همراه با تنظیم کیفیت، نمایش ماوس، ضبط صدا و گزینه اصلاح تصویر آینه‌ای برای منوهای راست‌به‌چپ.
* **تبدیل ویدیو به صدا:** استخراج سریع صدای فایل‌های ویدیویی به فرمت MP3 با امکان تغییر حجم صدا و سرعت.
* **اسکرین‌شات و ادیتور تصویر:**
  * `PrtSc` : عکس از محدوده انتخابی و باز شدن ادیتور
  * `Shift + PrtSc` : عکس از کل صفحه و باز شدن ادیتور
  * ابزارهای فلش، کادر، دایره، هایلایتر، شماره‌گذاری، قلم، مات کردن، متن و برش با قابلیت کپی به کلیپ‌بورد و ذخیره.
* **شخصی‌سازی:** پشتیبانی از زبان فارسی و انگلیسی، چند تم ظاهری و اجرای خودکار با ویندوز.

### نکات مهم ضبط
* در حالت **پنجره خاص**، پنجره هدف را کوچک نکنید.
* اگر تصویر کروم سفید یا در فایرفاکس متوقف شد، شتاب‌دهنده گرافیکی مرورگر را بررسی کنید یا گزینه `widget.windows.window_occlusion_tracking.enabled` را در `about:config` فایرفاکس روی `false` بگذارید.
* در صورت برعکس افتادن تصویر در مرورگرهای دارای منوی فارسی، تیک **اصلاح تصویر برعکس (منوی فارسی)** را فعال کنید.

### دانلود و ساخت
* نسخه آماده ویندوز را می‌توانید از بخش **Releases** همین مخزن دریافت کنید.
* برای اجرا یا بیلد محلی با پایتون:
  ```bash
  pip install pyinstaller mss pyaudiowpatch imageio-ffmpeg pillow arabic-reshaper python-bidi windows-capture
  python ali_recorder.py
  ```

---

## English

### Key Features
* **System Audio Recorder:** Captures system playback audio with volume and speed adjustments, exporting to MP3.
* **Screen & Window Recorder:** Records full screen, custom regions, or specific windows (using a subprocess Windows Graphics Capture worker) with quality presets, cursor toggle, optional system audio, and mirrored RTL UI flip support.
* **Video to MP3 Converter:** Extracts audio tracks from video files into MP3 with optional volume and tempo adjustments.
* **Screenshots & Image Editor:**
  * `PrtSc`: Region capture directly into the editor
  * `Shift + PrtSc`: Full-screen capture directly into the editor
  * Includes arrows, shapes, highlights, step numbers, pen, blur, text, crop, clipboard copy, and image export.
* **Customization:** Bilingual UI (Persian / English), multiple color themes, and optional Windows startup.

### Recording Notes
* Keep the target window un-minimized when using **Specific Window** capture.
* If browser capture appears white or frozen, check hardware/graphics acceleration settings or set `widget.windows.window_occlusion_tracking.enabled` to `false` in Firefox `about:config`.
* Use **Fix Mirrored (RTL UI)** if a right-to-left browser interface appears horizontally flipped.

### Download & Build
* Grab the packaged Windows executable from the **Releases** tab of this repository.
* To run or build locally from source:
  ```bash
  pip install pyinstaller mss pyaudiowpatch imageio-ffmpeg pillow arabic-reshaper python-bidi windows-capture
  python ali_recorder.py
  ```

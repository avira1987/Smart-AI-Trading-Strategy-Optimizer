#!/usr/bin/env python3
"""
اسکریپت ساخت ویدیو معرفی برای Smart AI Trading Strategy Optimizer
این اسکریپت از MoviePy برای ساخت ویدیو استفاده می‌کند.

نصب وابستگی‌ها:
pip install moviepy pillow numpy

نکته: این اسکریپت یک نمونه پایه است. برای ویدیو حرفه‌ای‌تر، 
پیشنهاد می‌شود از Adobe After Effects یا ابزارهای تخصصی استفاده شود.
"""

from moviepy.editor import (
    VideoFileClip, ImageClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, AudioFileClip, ColorClip
)
from moviepy.video.fx import resize, fadein, fadeout
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
from pathlib import Path

# تنظیمات
OUTPUT_DIR = Path("frontend/public")
OUTPUT_FILE = OUTPUT_DIR / "pro_vid.mp4"
FPS = 30
DURATION = 35  # طول کل ویدیو به ثانیه
RESOLUTION = (1920, 1080)

# رنگ‌های برند
COLORS = {
    "bg_dark": "#111827",      # gray-900
    "bg_card": "#1F2937",      # gray-800
    "primary": "#2563EB",      # blue-600
    "success": "#16A34A",      # green-600
    "warning": "#CA8A04",      # yellow-600
    "text": "#FFFFFF",         # white
    "text_secondary": "#D1D5DB" # gray-300
}

def create_text_clip(text, fontsize=60, color="white", duration=5, position=("center", "center")):
    """ایجاد یک TextClip با تنظیمات فارسی"""
    try:
        # استفاده از فونت فارسی (اگر موجود باشد)
        # در ویندوز: 'Arial' یا 'Tahoma' معمولاً از فارسی پشتیبانی می‌کنند
        txt_clip = TextClip(
            text,
            fontsize=fontsize,
            color=color,
            font='Arial',  # یا 'Tahoma' برای فارسی بهتر
            method='caption',
            size=(RESOLUTION[0] * 0.8, None),
            align='center'
        ).set_duration(duration).set_position(position)
        return txt_clip
    except Exception as e:
        print(f"خطا در ایجاد TextClip: {e}")
        # Fallback به فونت پیش‌فرض
        return TextClip(
            text,
            fontsize=fontsize,
            color=color,
            method='caption',
            size=(RESOLUTION[0] * 0.8, None),
            align='center'
        ).set_duration(duration).set_position(position)

def create_section_background(color, duration):
    """ایجاد پس‌زمینه رنگی برای یک بخش"""
    return ColorClip(size=RESOLUTION, color=color, duration=duration)

def create_logo_animation(duration=3):
    """ایجاد انیمیشن لوگو (placeholder - باید لوگوی واقعی جایگزین شود)"""
    # ایجاد یک تصویر ساده برای لوگو
    logo_img = Image.new('RGBA', (400, 200), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo_img)
    
    # رسم یک لوگوی ساده
    draw.rectangle([50, 50, 350, 150], fill=COLORS["primary"], outline=COLORS["text"], width=3)
    draw.text((200, 100), "AI Trading", fill=COLORS["text"], anchor="mm")
    
    logo_path = OUTPUT_DIR / "temp_logo.png"
    logo_img.save(logo_path)
    
    logo_clip = ImageClip(str(logo_path)).set_duration(duration)
    logo_clip = logo_clip.resize(height=200).set_position(("center", "center"))
    return logo_clip

def create_section_1():
    """بخش 1: معرفی و جلب توجه (0-5 ثانیه)"""
    duration = 5
    
    # پس‌زمینه با گرادیان
    bg = create_section_background(COLORS["bg_dark"], duration)
    
    # لوگو
    logo = create_logo_animation(duration).set_start(0)
    
    # متن
    title = create_text_clip(
        "Smart AI Trading Strategy Optimizer",
        fontsize=70,
        color=COLORS["text"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.3)
    )
    
    subtitle = create_text_clip(
        "ترید با هوش مصنوعی",
        fontsize=50,
        color=COLORS["primary"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.5)
    )
    
    return CompositeVideoClip([bg, logo, title, subtitle], size=RESOLUTION)

def create_section_2():
    """بخش 2: معرفی ویژگی اصلی (5-12 ثانیه)"""
    duration = 7
    
    bg = create_section_background(COLORS["bg_card"], duration)
    
    title = create_text_clip(
        "✨ تحلیل هوشمند با AI",
        fontsize=60,
        color=COLORS["text"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.3)
    )
    
    subtitle = create_text_clip(
        "آپلود استراتژی → تبدیل خودکار به کد",
        fontsize=45,
        color=COLORS["text_secondary"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.5)
    )
    
    return CompositeVideoClip([bg, title, subtitle], size=RESOLUTION)

def create_section_3():
    """بخش 3: بک‌تست و تست (12-20 ثانیه)"""
    duration = 8
    
    bg = create_section_background(COLORS["bg_dark"], duration)
    
    title = create_text_clip(
        "📊 بک‌تست حرفه‌ای",
        fontsize=60,
        color=COLORS["success"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.3)
    )
    
    subtitle = create_text_clip(
        "تست با داده‌های واقعی بازار",
        fontsize=45,
        color=COLORS["text_secondary"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.5)
    )
    
    return CompositeVideoClip([bg, title, subtitle], size=RESOLUTION)

def create_section_4():
    """بخش 4: بهینه‌سازی و معاملات خودکار (20-28 ثانیه)"""
    duration = 8
    
    bg = create_section_background(COLORS["bg_card"], duration)
    
    title = create_text_clip(
        "🚀 بهینه‌سازی خودکار",
        fontsize=60,
        color=COLORS["primary"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.3)
    )
    
    subtitle = create_text_clip(
        "معاملات 24/7 با MetaTrader 5",
        fontsize=45,
        color=COLORS["text_secondary"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.5)
    )
    
    return CompositeVideoClip([bg, title, subtitle], size=RESOLUTION)

def create_section_5():
    """بخش 5: فراخوان به عمل (CTA) (28-35 ثانیه)"""
    duration = 7
    
    bg = create_section_background(COLORS["bg_dark"], duration)
    
    title = create_text_clip(
        "🎁 حساب دمو رایگان: 10,000 دلار",
        fontsize=55,
        color=COLORS["success"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.3)
    )
    
    subtitle = create_text_clip(
        "شروع کنید - بدون نیاز به برنامه‌نویسی",
        fontsize=45,
        color=COLORS["text"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.5)
    )
    
    return CompositeVideoClip([bg, title, subtitle], size=RESOLUTION)

def create_section_6():
    """بخش 6: پایان (35-40 ثانیه)"""
    duration = 5
    
    bg = create_section_background(COLORS["bg_card"], duration)
    
    title = create_text_clip(
        "Smart AI Trading Strategy Optimizer",
        fontsize=50,
        color=COLORS["text"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.4)
    )
    
    url = create_text_clip(
        "myaibaz.ir",
        fontsize=40,
        color=COLORS["primary"],
        duration=duration,
        position=("center", RESOLUTION[1] * 0.6)
    )
    
    return CompositeVideoClip([bg, title, url], size=RESOLUTION)

def create_video():
    """ساخت ویدیو کامل"""
    print("🎬 شروع ساخت ویدیو...")
    
    # ایجاد دایرکتوری خروجی
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # ساخت بخش‌ها
    print("📹 ساخت بخش‌های ویدیو...")
    section1 = create_section_1()
    section2 = create_section_2()
    section3 = create_section_3()
    section4 = create_section_4()
    section5 = create_section_5()
    section6 = create_section_6()
    
    # اضافه کردن fade effects
    section1 = section1.fadein(0.5).fadeout(0.5)
    section2 = section2.fadein(0.5).fadeout(0.5)
    section3 = section3.fadein(0.5).fadeout(0.5)
    section4 = section4.fadein(0.5).fadeout(0.5)
    section5 = section5.fadein(0.5).fadeout(0.5)
    section6 = section6.fadein(0.5).fadeout(0.5)
    
    # اتصال بخش‌ها
    print("🔗 اتصال بخش‌ها...")
    final_video = concatenate_videoclips(
        [section1, section2, section3, section4, section5, section6],
        method="compose"
    )
    
    # اضافه کردن موسیقی (اگر فایل موسیقی موجود باشد)
    music_path = OUTPUT_DIR / "background_music.mp3"
    if music_path.exists():
        print("🎵 اضافه کردن موسیقی...")
        audio = AudioFileClip(str(music_path))
        if audio.duration > final_video.duration:
            audio = audio.subclip(0, final_video.duration)
        audio = audio.volumex(0.3)  # کاهش حجم صدا
        final_video = final_video.set_audio(audio)
    else:
        print("⚠️  فایل موسیقی یافت نشد. ویدیو بدون موسیقی ساخته می‌شود.")
        print(f"   برای اضافه کردن موسیقی، فایل را در {music_path} قرار دهید.")
    
    # ذخیره ویدیو
    print(f"💾 ذخیره ویدیو در {OUTPUT_FILE}...")
    final_video.write_videofile(
        str(OUTPUT_FILE),
        fps=FPS,
        codec='libx264',
        audio_codec='aac',
        bitrate='8000k',
        preset='medium'
    )
    
    print(f"✅ ویدیو با موفقیت ساخته شد: {OUTPUT_FILE}")
    print(f"📊 طول ویدیو: {final_video.duration:.2f} ثانیه")
    print(f"📐 رزولوشن: {RESOLUTION[0]}x{RESOLUTION[1]}")
    
    # پاک کردن فایل‌های موقت
    temp_logo = OUTPUT_DIR / "temp_logo.png"
    if temp_logo.exists():
        temp_logo.unlink()
    
    return final_video

if __name__ == "__main__":
    try:
        create_video()
    except Exception as e:
        print(f"❌ خطا در ساخت ویدیو: {e}")
        import traceback
        traceback.print_exc()


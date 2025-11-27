"""
تست سریع برای تشخیص مشکل Timeout در GapGPT
این تست برای اجرای سریع و تشخیص مشکل timeout طراحی شده است.
"""

import os
import sys
import django
import time

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from ai_module.gapgpt_client import convert_strategy_with_gapgpt, get_gapgpt_api_key


def test_timeout_quick():
    """تست سریع برای تشخیص مشکل timeout"""
    print("=" * 80)
    print("🔍 تست سریع تشخیص مشکل Timeout در GapGPT")
    print("=" * 80)
    
    # 1. بررسی API key
    print("\n[1] بررسی API Key...")
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_user(username='test', password='test')
    
    api_key = get_gapgpt_api_key(user=user)
    if not api_key:
        print("❌ GapGPT API key تنظیم نشده است!")
        print("   لطفاً در تنظیمات > پیکربندی API، کلید GapGPT را اضافه کنید.")
        return False
    print("✓ API Key موجود است")
    
    # 2. بررسی timeout پیش‌فرض
    print("\n[2] بررسی Timeout پیش‌فرض...")
    import inspect
    from ai_module.gapgpt_client import convert_strategy_with_gapgpt
    sig = inspect.signature(convert_strategy_with_gapgpt)
    timeout_param = sig.parameters.get('timeout')
    
    if timeout_param:
        default_timeout = timeout_param.default
        print(f"   Timeout پیش‌فرض: {default_timeout} ثانیه")
        if default_timeout < 60:
            print(f"   ⚠ هشدار: Timeout خیلی کوتاه است! (کمتر از 60 ثانیه)")
            print(f"   پیشنهاد: timeout را به 120 ثانیه افزایش دهید")
        elif default_timeout < 120:
            print(f"   ⚠ هشدار: Timeout ممکن است برای استراتژی‌های طولانی کافی نباشد")
            print(f"   پیشنهاد: timeout را به 120 ثانیه افزایش دهید")
        else:
            print(f"   ✓ Timeout مناسب است (>= 120 ثانیه)")
    else:
        print("   ❌ پارامتر timeout در تابع وجود ندارد!")
        return False
    
    # 3. تست واقعی با timeout
    print("\n[3] تست واقعی تبدیل استراتژی...")
    strategy_text = """
    استراتژی RSI:
    - ورود: RSI < 30
    - خروج: RSI > 70
    - حد ضرر: 50 پیپ
    - حد سود: 100 پیپ
    """
    
    print("   در حال ارسال درخواست...")
    start_time = time.time()
    
    try:
        result = convert_strategy_with_gapgpt(
            strategy_text=strategy_text,
            user=user,
            timeout=120  # استفاده از timeout مناسب
        )
        
        elapsed = time.time() - start_time
        print(f"   ✓ درخواست در {elapsed:.2f} ثانیه تکمیل شد")
        
        if result.get('success'):
            print("   ✓ تبدیل موفق بود!")
            print(f"   مدل استفاده شده: {result.get('model_used', 'N/A')}")
            print(f"   توکن‌های استفاده شده: {result.get('tokens_used', 0)}")
            print(f"   زمان پاسخ: {result.get('latency_ms', 0):.0f}ms")
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"   ❌ خطا: {error}")
            
            # بررسی نوع خطا
            if 'timeout' in error.lower() or 'زمان' in error.lower():
                print("\n   🔴 مشکل Timeout تشخیص داده شد!")
                print("   راه‌حل:")
                print("   1. بررسی کنید که timeout در backend >= 120 ثانیه باشد")
                print("   2. بررسی کنید که timeout در frontend >= 120000ms باشد")
                print("   3. بررسی کنید که از gapGPTClient در frontend استفاده می‌شود")
            elif 'api key' in error.lower() or 'کلید' in error.lower():
                print("\n   🔴 مشکل API Key!")
                print("   لطفاً API key را در تنظیمات بررسی کنید")
            else:
                print(f"\n   ⚠ خطای دیگر: {error}")
            
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"   ❌ Exception بعد از {elapsed:.2f} ثانیه: {e}")
        
        if elapsed >= 10:
            print("\n   🔴 احتمالاً مشکل Timeout است!")
            print("   درخواست بیش از 10 ثانیه طول کشید")
            print("   راه‌حل:")
            print("   1. بررسی timeout در frontend (باید >= 120000ms باشد)")
            print("   2. بررسی timeout در backend (باید >= 120 ثانیه باشد)")
        
        import traceback
        traceback.print_exc()
        return False


def check_frontend_config():
    """بررسی تنظیمات frontend (نیاز به بررسی دستی)"""
    print("\n" + "=" * 80)
    print("📋 بررسی تنظیمات Frontend (نیاز به بررسی دستی)")
    print("=" * 80)
    
    client_file = "frontend/src/api/client.ts"
    
    checks = [
        ("gapGPTClient با timeout >= 120000 تعریف شده است", False),
        ("gapGPTClient.interceptors.request.use تنظیم شده است", False),
        ("gapGPTClient.interceptors.response.use تنظیم شده است", False),
        ("getGapGPTModels از gapGPTClient استفاده می‌کند", False),
        ("convertStrategyWithGapGPT از gapGPTClient استفاده می‌کند", False),
        ("compareModelsWithGapGPT از gapGPTClient استفاده می‌کند", False),
    ]
    
    print("\nلطفاً فایل frontend/src/api/client.ts را بررسی کنید:")
    for i, (check, _) in enumerate(checks, 1):
        print(f"  {i}. {check}")
    
    print("\nاگر همه موارد بالا درست هستند، مشکل timeout باید حل شده باشد.")


def main():
    """اجرای تست اصلی"""
    print("\n" + "=" * 80)
    print("🚀 شروع تست سریع تشخیص مشکل Timeout")
    print("=" * 80)
    
    # اجرای تست
    success = test_timeout_quick()
    
    # بررسی تنظیمات frontend
    check_frontend_config()
    
    # خلاصه
    print("\n" + "=" * 80)
    print("📊 خلاصه")
    print("=" * 80)
    
    if success:
        print("✓ تست موفق بود!")
        print("  اگر هنوز مشکل timeout دارید:")
        print("  1. بررسی کنید که frontend از gapGPTClient استفاده می‌کند")
        print("  2. بررسی کنید که timeout در frontend >= 120000ms است")
        print("  3. بررسی کنید که timeout در backend >= 120 ثانیه است")
    else:
        print("❌ تست ناموفق بود!")
        print("  لطفاً:")
        print("  1. API key را بررسی کنید")
        print("  2. اتصال اینترنت را بررسی کنید")
        print("  3. تنظیمات timeout را بررسی کنید")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


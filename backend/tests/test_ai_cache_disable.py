"""
تست برای بررسی غیرفعال شدن کش AI
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import SystemSettings
from ai_module.gemini_client import _call_gemini, _load_cache, _hash_text
from unittest.mock import patch, MagicMock
import json


def test_cache_disabled():
    """تست که بررسی می‌کند وقتی use_ai_cache=False است، کش استفاده نمی‌شود"""
    print("\n" + "="*60)
    print("تست غیرفعال شدن کش AI")
    print("="*60)
    
    # 1. تنظیمات را به False تغییر می‌دهیم
    settings = SystemSettings.load()
    original_value = settings.use_ai_cache
    print(f"\n1. مقدار قبلی use_ai_cache: {original_value}")
    
    try:
        settings.use_ai_cache = False
        settings.save()
        print(f"   ✓ use_ai_cache به False تغییر یافت")
        
        # 2. بررسی می‌کنیم که تنظیمات ذخیره شده
        settings_reload = SystemSettings.load()
        assert settings_reload.use_ai_cache == False, "تنظیمات ذخیره نشده!"
        print(f"   ✓ تنظیمات در دیتابیس ذخیره شد: {settings_reload.use_ai_cache}")
        
        # 3. یک cache key می‌سازیم
        test_cache_key = "test_cache_key_for_disable_test"
        test_namespace = "test"
        digest = _hash_text(test_cache_key)
        
        # 4. یک cache fake می‌سازیم (اگر وجود داشته باشد)
        from pathlib import Path
        from django.conf import settings as django_settings
        cache_dir = Path(getattr(django_settings, 'CACHE_DIR', Path(__file__).parent.parent / 'cache' / 'gemini'))
        cache_file = cache_dir / test_namespace / f"{digest}.json"
        
        # 5. یک cache fake می‌سازیم
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        fake_cache_data = {
            "timestamp": 9999999999,  # زمان آینده (هرگز expire نشود)
            "payload": {
                "ai_status": "ok",
                "message": "This is from cache",
                "test": True
            }
        }
        cache_file.write_text(json.dumps(fake_cache_data, ensure_ascii=False), encoding='utf-8')
        print(f"\n2. یک cache fake ایجاد شد: {cache_file}")
        
        # 6. بررسی می‌کنیم که cache وجود دارد
        cached = _load_cache(test_namespace, digest)
        assert cached is not None, "Cache باید وجود داشته باشد!"
        print(f"   ✓ Cache موجود است: {cached.get('message')}")
        
        # 7. حالا _call_gemini را با use_ai_cache=False فراخوانی می‌کنیم
        # باید از cache استفاده نکند
        print(f"\n3. فراخوانی _call_gemini با use_ai_cache=False...")
        
        # Mock کردن provider manager تا خطا ندهد
        with patch('ai_module.gemini_client.get_provider_manager') as mock_manager:
            mock_provider = MagicMock()
            mock_provider.has_available_provider.return_value = False
            mock_manager.return_value = mock_provider
            
            result = _call_gemini(
                prompt="test prompt",
                cache_namespace=test_namespace,
                cache_key=test_cache_key,
                generation_config={},
                response_parser=lambda x: {"ai_status": "ok", "message": x},
                user=None
            )
            
            # بررسی می‌کنیم که از cache استفاده نشده
            if result.get("message") == "This is from cache":
                print(f"   ✗ خطا: از cache استفاده شده است!")
                print(f"   نتیجه: {result}")
                return False
            else:
                print(f"   ✓ از cache استفاده نشده است")
                print(f"   نتیجه: {result.get('ai_status')}")
                return True
        
    except Exception as e:
        print(f"\n✗ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # بازگرداندن مقدار قبلی
        settings.use_ai_cache = original_value
        settings.save()
        print(f"\n4. مقدار use_ai_cache به {original_value} بازگردانده شد")
        
        # پاک کردن cache fake
        if cache_file.exists():
            cache_file.unlink()
            print(f"   ✓ Cache fake پاک شد")


def test_cache_enabled():
    """تست که بررسی می‌کند وقتی use_ai_cache=True است، کش استفاده می‌شود"""
    print("\n" + "="*60)
    print("تست فعال بودن کش AI")
    print("="*60)
    
    settings = SystemSettings.load()
    original_value = settings.use_ai_cache
    
    try:
        settings.use_ai_cache = True
        settings.save()
        print(f"\n1. use_ai_cache به True تنظیم شد")
        
        test_cache_key = "test_cache_key_for_enable_test"
        test_namespace = "test"
        digest = _hash_text(test_cache_key)
        
        from pathlib import Path
        from django.conf import settings as django_settings
        cache_dir = Path(getattr(django_settings, 'CACHE_DIR', Path(__file__).parent.parent / 'cache' / 'gemini'))
        cache_file = cache_dir / test_namespace / f"{digest}.json"
        
        # ایجاد cache
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        fake_cache_data = {
            "timestamp": 9999999999,
            "payload": {
                "ai_status": "ok",
                "message": "This is from cache (enabled test)",
                "test": True
            }
        }
        cache_file.write_text(json.dumps(fake_cache_data, ensure_ascii=False), encoding='utf-8')
        print(f"2. Cache ایجاد شد")
        
        # فراخوانی _call_gemini
        with patch('ai_module.gemini_client.get_provider_manager') as mock_manager:
            mock_provider = MagicMock()
            mock_provider.has_available_provider.return_value = False
            mock_manager.return_value = mock_provider
            
            result = _call_gemini(
                prompt="test prompt",
                cache_namespace=test_namespace,
                cache_key=test_cache_key,
                generation_config={},
                response_parser=lambda x: {"ai_status": "ok", "message": x},
                user=None
            )
            
            if result.get("message") == "This is from cache (enabled test)":
                print(f"   ✓ از cache استفاده شده است")
                return True
            else:
                print(f"   ✗ از cache استفاده نشده است!")
                print(f"   نتیجه: {result}")
                return False
        
    except Exception as e:
        print(f"\n✗ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        settings.use_ai_cache = original_value
        settings.save()
        if cache_file.exists():
            cache_file.unlink()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("شروع تست‌های کش AI")
    print("="*60)
    
    result1 = test_cache_enabled()
    result2 = test_cache_disabled()
    
    print("\n" + "="*60)
    print("نتیجه تست‌ها:")
    print(f"  تست فعال بودن کش: {'✓ موفق' if result1 else '✗ ناموفق'}")
    print(f"  تست غیرفعال بودن کش: {'✓ موفق' if result2 else '✗ ناموفق'}")
    print("="*60)


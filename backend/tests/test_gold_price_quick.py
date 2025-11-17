"""
تست سریع و ساده سیستم دریافت قیمت لحظه‌ای طلا
برای استفاده در توسعه و debug
"""

import sys
import io
import os
import time

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.gold_price_providers import GoldPriceManager, MT5GoldPriceProvider, FreeAPIProvider


def test_provider(provider_name, provider_func):
    """تست یک provider خاص"""
    print(f"\n{'='*60}")
    print(f"تست {provider_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        if isinstance(provider_func, tuple):
            # برای FreeAPIProvider که tuple برمی‌گرداند
            price, error = provider_func[1]()
        else:
            # برای MT5 که dict برمی‌گرداند
            price_data, error = provider_func.get_price()
            price = price_data['last'] if price_data else None
        
        elapsed = time.time() - start_time
        
        if price:
            print(f"✅ موفق - قیمت: {price}")
            if isinstance(price_data, dict) and 'bid' in price_data:
                print(f"   Bid: {price_data['bid']}, Ask: {price_data['ask']}")
                print(f"   Spread: {price_data.get('spread', 'N/A')}")
            print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")
        else:
            print(f"❌ ناموفق - خطا: {error}")
            print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ خطا - {str(e)}")
        print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")


def test_all_providers():
    """تست تمام providers به صورت جداگانه"""
    print("\n" + "="*70)
    print("تست جداگانه Providers")
    print("="*70)
    
    # تست MT5
    mt5_provider = MT5GoldPriceProvider()
    test_provider("MT5", mt5_provider)
    
    # تست Free APIs
    free_providers = [
        ('ExchangeRate-API', FreeAPIProvider.get_from_exchangerate_api),
        ('MetalsAPI', FreeAPIProvider.get_from_metalsapi_free),
        ('Fixer.io', FreeAPIProvider.get_from_fixer_io),
        ('OpenExchangeRates', FreeAPIProvider.get_from_openexchangerates),
    ]
    
    for name, func in free_providers:
        test_provider(name, (name, func))


def test_manager():
    """تست GoldPriceManager"""
    print("\n" + "="*70)
    print("تست GoldPriceManager")
    print("="*70)
    
    manager = GoldPriceManager()
    
    # تست 1: بدون اولویت MT5
    print("\n[TEST 1] بدون اولویت MT5 (fallback به API های رایگان)")
    print("-" * 60)
    start_time = time.time()
    result = manager.get_price(prefer_mt5=False)
    elapsed = time.time() - start_time
    
    if result['success']:
        print(f"✅ موفق")
        print(f"   منبع: {result['source']}")
        print(f"   قیمت: {result['price']}")
        print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")
    else:
        print(f"❌ ناموفق - {result.get('error', 'Unknown error')}")
        print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")
    
    # تست 2: با اولویت MT5
    print("\n[TEST 2] با اولویت MT5")
    print("-" * 60)
    start_time = time.time()
    result = manager.get_price(prefer_mt5=True)
    elapsed = time.time() - start_time
    
    if result['success']:
        print(f"✅ موفق")
        print(f"   منبع: {result['source']}")
        print(f"   قیمت: {result['price']}")
        if result.get('data') and isinstance(result['data'], dict):
            if 'bid' in result['data']:
                print(f"   Bid: {result['data']['bid']}")
                print(f"   Ask: {result['data']['ask']}")
        print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")
    else:
        print(f"❌ ناموفق - {result.get('error', 'Unknown error')}")
        print(f"   زمان پاسخ: {elapsed:.3f} ثانیه")
    
    # تست 3: بررسی دسترسی MT5
    print("\n[TEST 3] بررسی دسترسی MT5")
    print("-" * 60)
    mt5_available = manager.is_mt5_available()
    print(f"MT5 در دسترس: {'✅ بله' if mt5_available else '❌ خیر'}")


def test_multiple_requests():
    """تست چندین درخواست متوالی"""
    print("\n" + "="*70)
    print("تست چندین درخواست متوالی (Performance)")
    print("="*70)
    
    manager = GoldPriceManager()
    num_requests = 5
    
    print(f"\nانجام {num_requests} درخواست متوالی...")
    times = []
    successes = 0
    
    for i in range(num_requests):
        start_time = time.time()
        result = manager.get_price(prefer_mt5=False)
        elapsed = time.time() - start_time
        times.append(elapsed)
        
        if result['success']:
            successes += 1
            print(f"  درخواست {i+1}: ✅ ({result['source']}) - {elapsed:.3f}s")
        else:
            print(f"  درخواست {i+1}: ❌ - {elapsed:.3f}s")
        
        time.sleep(0.1)  # کمی تاخیر بین درخواست‌ها
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n📊 آمار:")
    print(f"   موفق: {successes}/{num_requests}")
    print(f"   میانگین زمان: {avg_time:.3f} ثانیه")
    print(f"   حداقل: {min_time:.3f} ثانیه")
    print(f"   حداکثر: {max_time:.3f} ثانیه")


def main():
    """اجرای تمام تست‌ها"""
    print("="*70)
    print("تست سریع سیستم دریافت قیمت لحظه‌ای طلا")
    print("="*70)
    
    try:
        # تست جداگانه providers
        test_all_providers()
        
        # تست manager
        test_manager()
        
        # تست performance
        test_multiple_requests()
        
        print("\n" + "="*70)
        print("✅ تست تمام شد")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n❌ تست توسط کاربر متوقف شد")
    except Exception as e:
        print(f"\n\n❌ خطای غیرمنتظره: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


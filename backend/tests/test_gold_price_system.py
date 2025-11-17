"""
تست سیستم دریافت قیمت طلا
"""

import sys
import io
import os

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.gold_price_providers import GoldPriceManager, MT5GoldPriceProvider, FreeAPIProvider

def test_gold_price_manager():
    """تست GoldPriceManager"""
    print("=" * 70)
    print("[TEST] تست GoldPriceManager")
    print("=" * 70)
    
    manager = GoldPriceManager()
    
    # تست بدون اولویت MT5
    print("\n[TEST 1] تست بدون اولویت MT5 (اول API های جایگزین)")
    result = manager.get_price(prefer_mt5=False)
    print(f"Success: {result['success']}")
    print(f"Source: {result['source']}")
    print(f"Price: {result['price']}")
    print(f"Error: {result.get('error')}")
    if result['data']:
        print(f"Data: {result['data']}")
    
    # تست با اولویت MT5
    print("\n[TEST 2] تست با اولویت MT5")
    result = manager.get_price(prefer_mt5=True)
    print(f"Success: {result['success']}")
    print(f"Source: {result['source']}")
    print(f"Price: {result['price']}")
    print(f"Error: {result.get('error')}")
    if result['data']:
        print(f"Data: {result['data']}")
    
    # بررسی دسترسی MT5
    print("\n[TEST 3] بررسی دسترسی MT5")
    mt5_available = manager.is_mt5_available()
    print(f"MT5 Available: {mt5_available}")


def test_free_apis():
    """تست API های رایگان"""
    print("\n" + "=" * 70)
    print("[TEST] تست API های رایگان")
    print("=" * 70)
    
    providers = [
        ('ExchangeRate-API', FreeAPIProvider.get_from_exchangerate_api),
        ('MetalsAPI', FreeAPIProvider.get_from_metalsapi_free),
        ('Fixer.io', FreeAPIProvider.get_from_fixer_io),
        ('OpenExchangeRates', FreeAPIProvider.get_from_openexchangerates),
    ]
    
    for name, provider_func in providers:
        print(f"\n[TEST] {name}")
        price, error = provider_func()
        if price:
            print(f"   [OK] Price: {price}")
        else:
            print(f"   [FAILED] Error: {error}")


def test_mt5_directly():
    """تست مستقیم MT5"""
    print("\n" + "=" * 70)
    print("[TEST] تست مستقیم MT5")
    print("=" * 70)
    
    provider = MT5GoldPriceProvider()
    price_data, error = provider.get_price()
    
    if price_data:
        print(f"[OK] MT5 کار می‌کند!")
        print(f"Bid: {price_data['bid']}")
        print(f"Ask: {price_data['ask']}")
        print(f"Last: {price_data['last']}")
        print(f"Spread: {price_data['spread']}")
        print(f"Symbol: {price_data['symbol']}")
    else:
        print(f"[FAILED] MT5 در دسترس نیست: {error}")


def main():
    print("=" * 70)
    print("[COMPREHENSIVE TEST] تست جامع سیستم قیمت طلا")
    print("=" * 70)
    
    test_free_apis()
    test_mt5_directly()
    test_gold_price_manager()
    
    print("\n" + "=" * 70)
    print("[SUMMARY] تست تمام شد")
    print("=" * 70)


if __name__ == "__main__":
    main()


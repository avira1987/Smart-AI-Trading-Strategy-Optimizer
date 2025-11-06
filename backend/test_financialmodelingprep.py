"""
تست Financial Modeling Prep API
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

from api.gold_price_providers import FinancialModelingPrepProvider, GoldPriceManager

def test_financialmodelingprep():
    """تست Financial Modeling Prep Provider"""
    print("=" * 70)
    print("تست Financial Modeling Prep Provider")
    print("=" * 70)
    
    # تنظیم API key
    api_key = "CrFA9qczl3MRwERIiCGcmqloOilqkOBY"
    os.environ['FINANCIALMODELINGPREP_API_KEY'] = api_key
    
    provider = FinancialModelingPrepProvider()
    
    print("\n[TEST] دریافت قیمت از Financial Modeling Prep...")
    price_data, error = provider.get_price()
    
    if price_data:
        print("✅ موفق!")
        print(f"   قیمت: {price_data['last']}")
        print(f"   Bid: {price_data['bid']}")
        print(f"   Ask: {price_data['ask']}")
        print(f"   Spread: {price_data['spread']}")
        if 'volume' in price_data:
            print(f"   Volume: {price_data['volume']}")
        if 'high' in price_data:
            print(f"   High: {price_data['high']}")
        if 'low' in price_data:
            print(f"   Low: {price_data['low']}")
    else:
        print(f"❌ ناموفق: {error}")


def test_gold_price_manager():
    """تست GoldPriceManager با Financial Modeling Prep"""
    print("\n" + "=" * 70)
    print("تست GoldPriceManager با Financial Modeling Prep")
    print("=" * 70)
    
    # تنظیم API key
    api_key = "CrFA9qczl3MRwERIiCGcmqloOilqkOBY"
    os.environ['FINANCIALMODELINGPREP_API_KEY'] = api_key
    
    manager = GoldPriceManager()
    
    print("\n[TEST 1] با اولویت Financial Modeling Prep")
    result = manager.get_price(prefer_fmp=True)
    
    if result['success']:
        print(f"✅ موفق - منبع: {result['source']}")
        print(f"   قیمت: {result['price']}")
    else:
        print(f"❌ ناموفق: {result.get('error')}")
    
    print("\n[TEST 2] بدون اولویت (پیش‌فرض)")
    result = manager.get_price()
    
    if result['success']:
        print(f"✅ موفق - منبع: {result['source']}")
        print(f"   قیمت: {result['price']}")
    else:
        print(f"❌ ناموفق: {result.get('error')}")


if __name__ == "__main__":
    print("=" * 70)
    print("تست Financial Modeling Prep API")
    print("=" * 70)
    
    test_financialmodelingprep()
    test_gold_price_manager()
    
    print("\n" + "=" * 70)
    print("✅ تست تمام شد")
    print("=" * 70)


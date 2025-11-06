"""
تست بک‌تست بدون MT5
برای کاربران موبایل و ویندوز بدون MT5
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

from api.data_providers import DataProviderManager, FinancialModelingPrepProvider
from api.gold_price_providers import GoldPriceManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_data_providers():
    """تست ارائه‌دهندگان داده"""
    print("=" * 70)
    print("تست ارائه‌دهندگان داده (بدون MT5)")
    print("=" * 70)
    
    # تنظیم API key پیش‌فرض
    if not os.getenv('FINANCIALMODELINGPREP_API_KEY'):
        os.environ['FINANCIALMODELINGPREP_API_KEY'] = 'CrFA9qczl3MRwERIiCGcmqloOilqkOBY'
        print("\n✅ API key پیش‌فرض تنظیم شد")
    
    manager = DataProviderManager()
    available = manager.get_available_providers()
    
    print(f"\n📊 ارائه‌دهندگان موجود: {available}")
    
    if not available:
        print("\n❌ هیچ ارائه‌دهنده‌ای در دسترس نیست!")
        return False
    
    # تست Financial Modeling Prep
    print("\n" + "-" * 70)
    print("تست Financial Modeling Prep")
    print("-" * 70)
    
    provider = FinancialModelingPrepProvider()
    print(f"API Key: {'تنظیم شده' if provider.api_key else 'تنظیم نشده'}")
    
    # تست دریافت داده
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    end_date = timezone.now().strftime('%Y-%m-%d')
    start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"\nدریافت داده برای XAU/USD از {start_date} تا {end_date}...")
    
    try:
        data = provider.get_historical_data('XAU/USD', start_date, end_date)
        if not data.empty:
            print(f"✅ موفق! تعداد ردیف‌ها: {len(data)}")
            print(f"   اولین تاریخ: {data.index[0]}")
            print(f"   آخرین تاریخ: {data.index[-1]}")
            print(f"   ستون‌ها: {list(data.columns)}")
            return True
        else:
            print("❌ داده خالی است")
            return False
    except Exception as e:
        print(f"❌ خطا: {str(e)}")
        return False


def test_gold_price():
    """تست دریافت قیمت لحظه‌ای طلا"""
    print("\n" + "=" * 70)
    print("تست دریافت قیمت لحظه‌ای طلا")
    print("=" * 70)
    
    # تنظیم API key پیش‌فرض
    if not os.getenv('FINANCIALMODELINGPREP_API_KEY'):
        os.environ['FINANCIALMODELINGPREP_API_KEY'] = 'CrFA9qczl3MRwERIiCGcmqloOilqkOBY'
    
    manager = GoldPriceManager()
    
    print("\n[TEST 1] دریافت قیمت با اولویت Financial Modeling Prep")
    result = manager.get_price(prefer_fmp=True)
    
    if result['success']:
        print(f"✅ موفق - منبع: {result['source']}")
        print(f"   قیمت: {result['price']}")
        if result.get('data'):
            data = result['data']
            if 'bid' in data:
                print(f"   Bid: {data['bid']}")
                print(f"   Ask: {data['ask']}")
        return True
    else:
        print(f"❌ ناموفق: {result.get('error')}")
        return False


def test_full_backtest_flow():
    """تست کامل جریان بک‌تست"""
    print("\n" + "=" * 70)
    print("تست جریان کامل بک‌تست (بدون MT5)")
    print("=" * 70)
    
    # تنظیم API key پیش‌فرض
    if not os.getenv('FINANCIALMODELINGPREP_API_KEY'):
        os.environ['FINANCIALMODELINGPREP_API_KEY'] = 'CrFA9qczl3MRwERIiCGcmqloOilqkOBY'
    
    manager = DataProviderManager()
    
    # تست دریافت داده
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    symbol = 'XAU/USD'
    end_date = timezone.now().strftime('%Y-%m-%d')
    start_date = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"\nدریافت داده برای {symbol}...")
    data, provider_used = manager.get_data_from_any_provider(symbol, start_date, end_date)
    
    if not data.empty:
        print(f"✅ موفق! داده از {provider_used} دریافت شد")
        print(f"   تعداد ردیف‌ها: {len(data)}")
        print(f"   بازه زمانی: {data.index[0]} تا {data.index[-1]}")
        return True
    else:
        print(f"❌ ناموفق - هیچ provider داده برنگرداند")
        return False


def main():
    """اجرای تمام تست‌ها"""
    print("=" * 70)
    print("تست سیستم بک‌تست بدون MT5")
    print("برای کاربران موبایل و ویندوز بدون MT5")
    print("=" * 70)
    
    results = []
    
    # تست 1: ارائه‌دهندگان داده
    results.append(("ارائه‌دهندگان داده", test_data_providers()))
    
    # تست 2: قیمت لحظه‌ای
    results.append(("قیمت لحظه‌ای طلا", test_gold_price()))
    
    # تست 3: جریان کامل بک‌تست
    results.append(("جریان کامل بک‌تست", test_full_backtest_flow()))
    
    # خلاصه
    print("\n" + "=" * 70)
    print("خلاصه نتایج")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ موفق" if result else "❌ ناموفق"
        print(f"{name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ همه تست‌ها موفق بودند!")
        print("سیستم آماده استفاده برای کاربران موبایل و بدون MT5 است.")
    else:
        print("⚠️ برخی تست‌ها ناموفق بودند.")
        print("لطفاً API keys را بررسی کنید.")
    print("=" * 70)


if __name__ == "__main__":
    main()


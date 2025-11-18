"""
تست بررسی استفاده از API های خارجی در بک‌تست
این تست بررسی می‌کند که آیا واقعاً از API های خارجی استفاده می‌شود یا از MT5
"""

import sys
import io
import os

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

import logging
from datetime import datetime, timedelta
from django.utils import timezone
from api.data_providers import DataProviderManager
from api.mt5_client import is_mt5_available
from core.models import TradingStrategy, Job, Result, APIConfiguration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_api_keys():
    """بررسی API key های تنظیم شده"""
    print("\n" + "=" * 80)
    print("بررسی API Key های تنظیم شده")
    print("=" * 80)
    
    api_keys_status = {}
    
    # بررسی از environment variables
    env_keys = {
        'FINANCIALMODELINGPREP_API_KEY': os.getenv('FINANCIALMODELINGPREP_API_KEY'),
        'TWELVEDATA_API_KEY': os.getenv('TWELVEDATA_API_KEY'),
        'ALPHAVANTAGE_API_KEY': os.getenv('ALPHAVANTAGE_API_KEY'),
        'OANDA_API_KEY': os.getenv('OANDA_API_KEY'),
        'METALSAPI_API_KEY': os.getenv('METALSAPI_API_KEY'),
    }
    
    for key_name, key_value in env_keys.items():
        if key_value:
            # فقط 4 کاراکتر اول و آخر را نمایش بده
            masked = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
            api_keys_status[key_name] = {'source': 'Environment', 'status': '✅ تنظیم شده', 'masked': masked}
            print(f"✅ {key_name}: تنظیم شده (از Environment) - {masked}")
        else:
            api_keys_status[key_name] = {'source': 'Environment', 'status': '❌ تنظیم نشده'}
            print(f"❌ {key_name}: تنظیم نشده (از Environment)")
    
    # بررسی از Database (APIConfiguration)
    try:
        db_configs = APIConfiguration.objects.filter(is_active=True, user__isnull=True)
        if db_configs.exists():
            print("\n--- API Keys از Database ---")
            for config in db_configs:
                provider = config.provider
                masked = config.api_key[:4] + "..." + config.api_key[-4:] if len(config.api_key) > 8 else "***"
                api_keys_status[f'{provider}_DB'] = {'source': 'Database', 'status': '✅ تنظیم شده', 'masked': masked}
                print(f"✅ {provider}: تنظیم شده (از Database) - {masked}")
    except Exception as e:
        print(f"⚠️ خطا در بررسی Database: {e}")
    
    return api_keys_status


def check_available_providers():
    """بررسی ارائه‌دهندگان در دسترس"""
    print("\n" + "=" * 80)
    print("بررسی ارائه‌دهندگان در دسترس")
    print("=" * 80)
    
    data_manager = DataProviderManager()
    available_providers = data_manager.get_available_providers()
    
    provider_names = {
        'financialmodelingprep': 'Financial Modeling Prep',
        'twelvedata': 'TwelveData',
        'alphavantage': 'Alpha Vantage',
        'oanda': 'OANDA',
        'metalsapi': 'MetalsAPI',
    }
    
    if available_providers:
        print(f"✅ تعداد ارائه‌دهندگان در دسترس: {len(available_providers)}")
        for provider in available_providers:
            display_name = provider_names.get(provider, provider)
            print(f"  - {display_name} ({provider})")
    else:
        print("❌ هیچ ارائه‌دهنده API خارجی در دسترس نیست!")
    
    # بررسی MT5
    mt5_ok, mt5_msg = is_mt5_available()
    if mt5_ok:
        print(f"⚠️ MT5 در دسترس است: {mt5_msg}")
    else:
        print(f"ℹ️ MT5 در دسترس نیست: {mt5_msg}")
    
    return available_providers, mt5_ok


def test_data_fetching(symbol='XAU/USD', days=30):
    """تست دریافت داده از ارائه‌دهندگان"""
    print("\n" + "=" * 80)
    print(f"تست دریافت داده برای نماد: {symbol} (آخرین {days} روز)")
    print("=" * 80)
    
    data_manager = DataProviderManager()
    available_providers = data_manager.get_available_providers()
    
    if not available_providers:
        print("❌ هیچ ارائه‌دهنده API خارجی در دسترس نیست!")
        return None, None
    
    # محاسبه تاریخ‌ها
    end_date = timezone.now().strftime('%Y-%m-%d')
    start_date = (timezone.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    print(f"بازه زمانی: {start_date} تا {end_date}")
    print(f"در حال تلاش برای دریافت داده از ارائه‌دهندگان...")
    
    # تست دریافت داده
    data, provider_used = data_manager.get_data_from_any_provider(
        symbol, start_date, end_date, user=None
    )
    
    if not data.empty:
        print(f"\n✅ داده با موفقیت دریافت شد!")
        print(f"  - ارائه‌دهنده استفاده شده: {provider_used}")
        print(f"  - تعداد ردیف‌ها: {len(data):,}")
        print(f"  - محدوده داده: {data.index[0]} تا {data.index[-1]}")
        print(f"  - نمونه داده (5 ردیف اول):")
        print(data.head().to_string())
        
        # بررسی اینکه آیا داده واقعی است یا نه
        if data['close'].std() == 0:
            print("\n⚠️ هشدار: داده flat است (همه قیمت‌ها یکسان)!")
        else:
            print(f"\n✅ داده واقعی است (انحراف معیار: {data['close'].std():.2f})")
        
        return data, provider_used
    else:
        print("\n❌ هیچ داده‌ای دریافت نشد!")
        return None, None


def test_backtest_with_provider_check():
    """تست بک‌تست کامل با بررسی provider"""
    print("\n" + "=" * 80)
    print("تست بک‌تست کامل")
    print("=" * 80)
    
    # ایجاد یک استراتژی ساده برای تست
    strategy_text = """
    استراتژی تست:
    - نماد: XAU/USD
    - تایم‌فریم: M15
    - شرایط ورود: RSI < 30
    - شرایط خروج: RSI > 70
    - اندیکاتورها: RSI
    """
    
    try:
        # ایجاد یا پیدا کردن استراتژی تست
        strategy, created = TradingStrategy.objects.get_or_create(
            name='تست Provider Verification',
            defaults={
                'strategy_text': strategy_text,
                'user': None,
            }
        )
        
        if created:
            print(f"✅ استراتژی تست ایجاد شد (ID: {strategy.id})")
        else:
            print(f"ℹ️ استراتژی تست موجود است (ID: {strategy.id})")
        
        # ایجاد Job
        job = Job.objects.create(
            strategy=strategy,
            job_type='backtest',
            status='pending',
            timeframe_days=30,
            symbol_override='XAU/USD',
            initial_capital=10000,
        )
        
        print(f"✅ Job ایجاد شد (ID: {job.id})")
        print(f"در حال اجرای بک‌تست...")
        
        # اجرای بک‌تست
        from api.tasks import run_backtest_task
        result = run_backtest_task(job.id, timeframe_days=30, symbol_override='XAU/USD', initial_capital=10000)
        
        # بررسی نتایج
        job.refresh_from_db()
        
        print("\n" + "=" * 80)
        print("نتایج بک‌تست")
        print("=" * 80)
        
        if job.status == 'completed' and job.result:
            result_obj = job.result
            print(f"✅ بک‌تست با موفقیت انجام شد!")
            print(f"\n📊 نتایج:")
            print(f"  - بازده کل: {result_obj.total_return:.2f}%")
            print(f"  - تعداد معاملات: {result_obj.total_trades}")
            print(f"  - معاملات برنده: {result_obj.winning_trades}")
            print(f"  - معاملات بازنده: {result_obj.losing_trades}")
            print(f"  - نرخ برد: {result_obj.win_rate:.2f}%")
            print(f"  - حداکثر افت: {result_obj.max_drawdown:.2f}%")
            
            # بررسی provider استفاده شده
            if result_obj.data_sources:
                provider = result_obj.data_sources.get('provider', 'unknown')
                available_providers = result_obj.data_sources.get('available_providers', [])
                
                print(f"\n📡 اطلاعات Provider:")
                print(f"  - Provider استفاده شده: {provider}")
                print(f"  - ارائه‌دهندگان در دسترس: {available_providers}")
                
                provider_names = {
                    'financialmodelingprep': 'Financial Modeling Prep',
                    'twelvedata': 'TwelveData',
                    'alphavantage': 'Alpha Vantage',
                    'oanda': 'OANDA',
                    'metalsapi': 'MetalsAPI',
                    'mt5': 'MetaTrader 5',
                }
                
                provider_display = provider_names.get(provider, provider)
                print(f"  - نام نمایشی: {provider_display}")
                
                if provider == 'mt5':
                    print(f"\n⚠️ هشدار: از MT5 استفاده شده است (داده محلی، نه از API های خارجی)")
                else:
                    print(f"\n✅ از API خارجی استفاده شده است: {provider_display}")
                
                # نمایش توضیحات
                if result_obj.description:
                    print(f"\n📝 توضیحات:")
                    # فقط بخش منابع داده را نمایش بده
                    if 'منابع داده استفاده شده' in result_obj.description:
                        parts = result_obj.description.split('منابع داده استفاده شده')
                        if len(parts) > 1:
                            print(parts[1][:500])  # فقط 500 کاراکتر اول
            
            return True
        else:
            print(f"❌ بک‌تست ناموفق بود!")
            print(f"  - وضعیت: {job.status}")
            if job.error_message:
                print(f"  - خطا: {job.error_message}")
            return False
            
    except Exception as e:
        print(f"❌ خطا در اجرای بک‌تست: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """تابع اصلی"""
    print("\n" + "=" * 80)
    print("تست بررسی استفاده از API های خارجی در بک‌تست")
    print("=" * 80)
    print(f"زمان شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # مرحله 1: بررسی API Keys
    api_keys_status = check_api_keys()
    
    # مرحله 2: بررسی ارائه‌دهندگان در دسترس
    available_providers, mt5_ok = check_available_providers()
    
    # مرحله 3: تست دریافت داده
    data, provider_used = test_data_fetching(symbol='XAU/USD', days=30)
    
    # مرحله 4: تست بک‌تست کامل
    backtest_success = test_backtest_with_provider_check()
    
    # خلاصه نتایج
    print("\n" + "=" * 80)
    print("خلاصه نتایج")
    print("=" * 80)
    
    api_keys_count = sum(1 for k, v in api_keys_status.items() if '✅' in v.get('status', ''))
    print(f"✅ API Keys تنظیم شده: {api_keys_count}")
    print(f"✅ ارائه‌دهندگان در دسترس: {len(available_providers) if available_providers else 0}")
    print(f"✅ MT5 در دسترس: {'بله' if mt5_ok else 'خیر'}")
    
    if data is not None:
        print(f"✅ دریافت داده: موفق (از {provider_used})")
        if provider_used == 'mt5':
            print("⚠️ هشدار: از MT5 استفاده شده است!")
        else:
            print("✅ از API خارجی استفاده شده است!")
    else:
        print("❌ دریافت داده: ناموفق")
    
    if backtest_success:
        print("✅ بک‌تست: موفق")
    else:
        print("❌ بک‌تست: ناموفق")
    
    print("\n" + "=" * 80)
    print("تست به پایان رسید")
    print("=" * 80)


if __name__ == '__main__':
    main()


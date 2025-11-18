"""
Management command برای تست بررسی استفاده از API های خارجی
"""

from django.core.management.base import BaseCommand
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from api.data_providers import DataProviderManager
from api.mt5_client import is_mt5_available
from core.models import TradingStrategy, Job, APIConfiguration
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'تست بررسی استفاده از API های خارجی در بک‌تست'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("تست بررسی استفاده از API های خارجی در بک‌تست")
        self.stdout.write("=" * 80)
        self.stdout.write(f"زمان شروع: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # مرحله 1: بررسی API Keys
        self.check_api_keys()
        
        # مرحله 2: بررسی ارائه‌دهندگان در دسترس
        available_providers, mt5_ok = self.check_available_providers()
        
        # مرحله 3: تست دریافت داده
        data, provider_used = self.test_data_fetching(symbol='XAU/USD', days=30)
        
        # خلاصه نتایج
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("خلاصه نتایج")
        self.stdout.write("=" * 80)
        
        api_keys_count = len([k for k in ['FINANCIALMODELINGPREP_API_KEY', 'TWELVEDATA_API_KEY', 
                                          'ALPHAVANTAGE_API_KEY', 'OANDA_API_KEY', 'METALSAPI_API_KEY'] 
                             if os.getenv(k)])
        self.stdout.write(f"✅ API Keys تنظیم شده: {api_keys_count}")
        self.stdout.write(f"✅ ارائه‌دهندگان در دسترس: {len(available_providers) if available_providers else 0}")
        self.stdout.write(f"✅ MT5 در دسترس: {'بله' if mt5_ok else 'خیر'}")
        
        if data is not None:
            self.stdout.write(f"✅ دریافت داده: موفق (از {provider_used})")
            if provider_used == 'mt5':
                self.stdout.write(self.style.WARNING("⚠️ هشدار: از MT5 استفاده شده است!"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ از API خارجی استفاده شده است!"))
        else:
            self.stdout.write(self.style.ERROR("❌ دریافت داده: ناموفق"))
        
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("تست به پایان رسید")
        self.stdout.write("=" * 80)

    def check_api_keys(self):
        """بررسی API key های تنظیم شده"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("بررسی API Key های تنظیم شده")
        self.stdout.write("=" * 80)
        
        env_keys = {
            'FINANCIALMODELINGPREP_API_KEY': os.getenv('FINANCIALMODELINGPREP_API_KEY'),
            'TWELVEDATA_API_KEY': os.getenv('TWELVEDATA_API_KEY'),
            'ALPHAVANTAGE_API_KEY': os.getenv('ALPHAVANTAGE_API_KEY'),
            'OANDA_API_KEY': os.getenv('OANDA_API_KEY'),
            'METALSAPI_API_KEY': os.getenv('METALSAPI_API_KEY'),
        }
        
        for key_name, key_value in env_keys.items():
            if key_value:
                masked = key_value[:4] + "..." + key_value[-4:] if len(key_value) > 8 else "***"
                self.stdout.write(self.style.SUCCESS(f"✅ {key_name}: تنظیم شده - {masked}"))
            else:
                self.stdout.write(self.style.ERROR(f"❌ {key_name}: تنظیم نشده"))
        
        # بررسی از Database
        try:
            db_configs = APIConfiguration.objects.filter(is_active=True, user__isnull=True)
            if db_configs.exists():
                self.stdout.write("\n--- API Keys از Database ---")
                for config in db_configs:
                    masked = config.api_key[:4] + "..." + config.api_key[-4:] if len(config.api_key) > 8 else "***"
                    self.stdout.write(self.style.SUCCESS(f"✅ {config.provider}: تنظیم شده (از Database) - {masked}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ خطا در بررسی Database: {e}"))

    def check_available_providers(self):
        """بررسی ارائه‌دهندگان در دسترس"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("بررسی ارائه‌دهندگان در دسترس")
        self.stdout.write("=" * 80)
        
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
            self.stdout.write(self.style.SUCCESS(f"✅ تعداد ارائه‌دهندگان در دسترس: {len(available_providers)}"))
            for provider in available_providers:
                display_name = provider_names.get(provider, provider)
                self.stdout.write(f"  - {display_name} ({provider})")
        else:
            self.stdout.write(self.style.ERROR("❌ هیچ ارائه‌دهنده API خارجی در دسترس نیست!"))
        
        # بررسی MT5
        mt5_ok, mt5_msg = is_mt5_available()
        if mt5_ok:
            self.stdout.write(self.style.WARNING(f"⚠️ MT5 در دسترس است: {mt5_msg}"))
        else:
            self.stdout.write(f"ℹ️ MT5 در دسترس نیست: {mt5_msg}")
        
        return available_providers, mt5_ok

    def test_data_fetching(self, symbol='XAU/USD', days=30):
        """تست دریافت داده از ارائه‌دهندگان"""
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(f"تست دریافت داده برای نماد: {symbol} (آخرین {days} روز)")
        self.stdout.write("=" * 80)
        
        data_manager = DataProviderManager()
        available_providers = data_manager.get_available_providers()
        
        if not available_providers:
            self.stdout.write(self.style.ERROR("❌ هیچ ارائه‌دهنده API خارجی در دسترس نیست!"))
            return None, None
        
        # محاسبه تاریخ‌ها
        end_date = timezone.now().strftime('%Y-%m-%d')
        start_date = (timezone.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        self.stdout.write(f"بازه زمانی: {start_date} تا {end_date}")
        self.stdout.write("در حال تلاش برای دریافت داده از ارائه‌دهندگان...")
        
        # تست دریافت داده
        data, provider_used = data_manager.get_data_from_any_provider(
            symbol, start_date, end_date, user=None
        )
        
        if not data.empty:
            self.stdout.write(self.style.SUCCESS("\n✅ داده با موفقیت دریافت شد!"))
            self.stdout.write(f"  - ارائه‌دهنده استفاده شده: {provider_used}")
            self.stdout.write(f"  - تعداد ردیف‌ها: {len(data):,}")
            self.stdout.write(f"  - محدوده داده: {data.index[0]} تا {data.index[-1]}")
            self.stdout.write(f"  - نمونه داده (5 ردیف اول):")
            self.stdout.write(str(data.head()))
            
            # بررسی اینکه آیا داده واقعی است یا نه
            if data['close'].std() == 0:
                self.stdout.write(self.style.WARNING("\n⚠️ هشدار: داده flat است (همه قیمت‌ها یکسان)!"))
            else:
                self.stdout.write(self.style.SUCCESS(f"\n✅ داده واقعی است (انحراف معیار: {data['close'].std():.2f})"))
            
            return data, provider_used
        else:
            self.stdout.write(self.style.ERROR("\n❌ هیچ داده‌ای دریافت نشد!"))
            return None, None


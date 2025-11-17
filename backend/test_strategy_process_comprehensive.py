#!/usr/bin/env python
"""
تست جامع برای پردازش استراتژی - شناسایی خطاها
این تست تمام خطاهای احتمالی در زمان پردازش استراتژی را شناسایی می‌کند
"""
import os
import sys
import django
import traceback
import logging
from datetime import datetime

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import TradingStrategy, User
from api.views import TradingStrategyViewSet
from rest_framework.test import APIRequestFactory
from rest_framework import status
from django.contrib.auth.models import AnonymousUser
from django.conf import settings

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/strategy_process_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_strategy_process():
    """تست کامل پردازش استراتژی"""
    # اضافه کردن testserver به ALLOWED_HOSTS برای تست
    if 'testserver' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('testserver')
    if 'localhost' not in settings.ALLOWED_HOSTS:
        settings.ALLOWED_HOSTS.append('localhost')
    
    print("\n" + "="*80)
    print("تست جامع پردازش استراتژی - شناسایی خطاها")
    print("="*80 + "\n")
    
    # دریافت اولین استراتژی
    strategy = TradingStrategy.objects.first()
    if not strategy:
        print("❌ هیچ استراتژی یافت نشد!")
        print("لطفاً ابتدا یک استراتژی آپلود کنید.")
        return False
    
    print(f"✅ استراتژی پیدا شد:")
    print(f"   ID: {strategy.id}")
    print(f"   نام: {strategy.name}")
    print(f"   کاربر: {strategy.user.username if strategy.user else 'None'}")
    print(f"   وضعیت پردازش: {strategy.processing_status}")
    print(f"   فایل دارد: {bool(strategy.strategy_file)}")
    
    if strategy.strategy_file:
        file_path = strategy.strategy_file.path
        file_exists = os.path.exists(file_path)
        print(f"   مسیر فایل: {file_path}")
        print(f"   فایل وجود دارد: {file_exists}")
        if file_exists:
            file_size = os.path.getsize(file_path)
            print(f"   اندازه فایل: {file_size} بایت")
        else:
            print("   ⚠️ فایل استراتژی یافت نشد!")
    else:
        print("   ⚠️ استراتژی فایل ندارد!")
        return False
    
    # ایجاد request factory
    factory = APIRequestFactory()
    
    # تست با کاربر احراز هویت شده
    user = strategy.user if strategy.user else User.objects.first()
    if not user:
        print("\n❌ هیچ کاربری یافت نشد!")
        return False
    
    print(f"\n📝 تست با کاربر: {user.username}")
    
    # ایجاد request
    request = factory.post(f'/api/strategies/{strategy.id}/process/')
    request.user = user
    
    # ایجاد viewset instance
    viewset = TradingStrategyViewSet()
    viewset.kwargs = {'pk': strategy.id}
    viewset.request = request
    
    # ذخیره وضعیت اولیه
    initial_status = strategy.processing_status
    initial_error = strategy.processing_error
    
    print(f"\n🔄 وضعیت اولیه:")
    print(f"   processing_status: {initial_status}")
    print(f"   processing_error: {initial_error[:100] if initial_error else 'None'}")
    
    # اجرای تست
    print("\n" + "-"*80)
    print("شروع پردازش استراتژی...")
    print("-"*80 + "\n")
    
    start_time = datetime.now()
    errors_caught = []
    warnings_caught = []
    
    try:
        # لاگ تمام خطاهای احتمالی
        import sys
        original_excepthook = sys.excepthook
        
        def custom_excepthook(exc_type, exc_value, exc_traceback):
            """جمع‌آوری تمام خطاها"""
            error_info = {
                'type': exc_type.__name__,
                'message': str(exc_value),
                'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            }
            errors_caught.append(error_info)
            logger.error(f"خطا شناسایی شد: {error_info['type']}: {error_info['message']}")
            original_excepthook(exc_type, exc_value, exc_traceback)
        
        sys.excepthook = custom_excepthook
        
        # فراخوانی متد process
        response = viewset.process(request, pk=strategy.id)
        
        # بازگرداندن excepthook اصلی
        sys.excepthook = original_excepthook
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n✅ پردازش تکمیل شد در {duration:.2f} ثانیه")
        print(f"\n📊 نتیجه:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Type: {type(response)}")
        
        if hasattr(response, 'data'):
            response_data = response.data
            print(f"\n📦 داده‌های پاسخ:")
            
            if isinstance(response_data, dict):
                for key, value in response_data.items():
                    if key == 'parsed_data' and isinstance(value, dict):
                        print(f"   {key}:")
                        print(f"      - confidence_score: {value.get('confidence_score', 'N/A')}")
                        print(f"      - symbol: {value.get('symbol', 'N/A')}")
                        print(f"      - timeframe: {value.get('timeframe', 'N/A')}")
                        print(f"      - has_analysis: {bool(value.get('analysis'))}")
                        print(f"      - has_genetic_optimization: {bool(value.get('genetic_optimization'))}")
                    elif key == 'analysis_sources' and isinstance(value, dict):
                        print(f"   {key}:")
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, (str, int, float, bool, type(None))):
                                print(f"      - {sub_key}: {sub_value}")
                            elif isinstance(sub_value, dict):
                                print(f"      - {sub_key}: (dict with {len(sub_value)} keys)")
                            elif isinstance(sub_value, list):
                                print(f"      - {sub_key}: (list with {len(sub_value)} items)")
                            else:
                                print(f"      - {sub_key}: {type(sub_value).__name__}")
                    else:
                        if isinstance(value, (str, int, float, bool, type(None))):
                            print(f"   {key}: {value}")
                        elif isinstance(value, dict):
                            print(f"   {key}: (dict with {len(value)} keys)")
                        elif isinstance(value, list):
                            print(f"   {key}: (list with {len(value)} items)")
                        else:
                            print(f"   {key}: {type(value).__name__}")
            else:
                print(f"   Response data type: {type(response_data)}")
                print(f"   Response data: {str(response_data)[:500]}")
        
        # بررسی وضعیت نهایی استراتژی
        strategy.refresh_from_db()
        print(f"\n📈 وضعیت نهایی استراتژی:")
        print(f"   processing_status: {strategy.processing_status}")
        print(f"   processed_at: {strategy.processed_at}")
        if strategy.processing_error:
            print(f"   ⚠️ processing_error: {strategy.processing_error[:200]}")
        if strategy.parsed_strategy_data:
            print(f"   ✅ parsed_strategy_data موجود است")
            if isinstance(strategy.parsed_strategy_data, dict):
                print(f"      - confidence_score: {strategy.parsed_strategy_data.get('confidence_score', 'N/A')}")
        
        # بررسی خطاها
        if errors_caught:
            print(f"\n⚠️ {len(errors_caught)} خطا در طول پردازش شناسایی شد:")
            for i, error in enumerate(errors_caught, 1):
                print(f"\n   خطا {i}:")
                print(f"      نوع: {error['type']}")
                print(f"      پیام: {error['message'][:200]}")
        else:
            print("\n✅ هیچ خطایی در طول پردازش شناسایی نشد")
        
        # بررسی هشدارها
        if warnings_caught:
            print(f"\n⚠️ {len(warnings_caught)} هشدار در طول پردازش شناسایی شد:")
            for i, warning in enumerate(warnings_caught, 1):
                print(f"   {i}. {warning}")
        
        # بررسی موفقیت
        if response.status_code == status.HTTP_200_OK:
            if isinstance(response.data, dict) and response.data.get('status') == 'success':
                print("\n✅ پردازش با موفقیت انجام شد!")
                return True
            else:
                print("\n⚠️ پاسخ 200 اما status != 'success'")
                return False
        else:
            print(f"\n❌ پردازش ناموفق بود (Status: {response.status_code})")
            if hasattr(response, 'data') and isinstance(response.data, dict):
                error_msg = response.data.get('message', response.data.get('error', 'Unknown error'))
                print(f"   پیام خطا: {error_msg}")
            return False
            
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        error_type = type(e).__name__
        error_message = str(e)
        error_traceback = traceback.format_exc()
        
        print(f"\n❌ خطای غیرمنتظره در طول تست:")
        print(f"   نوع: {error_type}")
        print(f"   پیام: {error_message}")
        print(f"   مدت زمان تا خطا: {duration:.2f} ثانیه")
        print(f"\n📋 Traceback کامل:")
        print(error_traceback)
        
        # بررسی وضعیت استراتژی بعد از خطا
        try:
            strategy.refresh_from_db()
            print(f"\n📈 وضعیت استراتژی بعد از خطا:")
            print(f"   processing_status: {strategy.processing_status}")
            if strategy.processing_error:
                print(f"   processing_error: {strategy.processing_error[:300]}")
        except Exception as refresh_error:
            print(f"\n⚠️ خطا در بررسی وضعیت استراتژی: {refresh_error}")
        
        return False

def test_all_strategies():
    """تست تمام استراتژی‌ها"""
    strategies = TradingStrategy.objects.all()[:5]  # حداکثر 5 استراتژی
    if not strategies:
        print("❌ هیچ استراتژی یافت نشد!")
        return
    
    print(f"\n📋 تست {len(strategies)} استراتژی...\n")
    
    results = []
    for strategy in strategies:
        print(f"\n{'='*80}")
        print(f"تست استراتژی: {strategy.name} (ID: {strategy.id})")
        print('='*80)
        
        try:
            success = test_strategy_process()
            results.append({
                'strategy_id': strategy.id,
                'strategy_name': strategy.name,
                'success': success
            })
        except Exception as e:
            print(f"\n❌ خطا در تست استراتژی {strategy.id}: {e}")
            results.append({
                'strategy_id': strategy.id,
                'strategy_name': strategy.name,
                'success': False,
                'error': str(e)
            })
    
    # خلاصه نتایج
    print("\n" + "="*80)
    print("خلاصه نتایج:")
    print("="*80)
    successful = sum(1 for r in results if r.get('success'))
    failed = len(results) - successful
    print(f"✅ موفق: {successful}")
    print(f"❌ ناموفق: {failed}")
    print("\nجزئیات:")
    for result in results:
        status_icon = "✅" if result.get('success') else "❌"
        print(f"   {status_icon} {result['strategy_name']} (ID: {result['strategy_id']})")
        if 'error' in result:
            print(f"      خطا: {result['error']}")

if __name__ == '__main__':
    # ایجاد دایرکتوری لاگ
    os.makedirs('logs', exist_ok=True)
    
    # تست یک استراتژی
    print("\n" + "="*80)
    print("شروع تست پردازش استراتژی")
    print("="*80)
    
    try:
        # تست اولین استراتژی
        success = test_strategy_process()
        
        if success:
            print("\n✅ تست با موفقیت انجام شد!")
            sys.exit(0)
        else:
            print("\n❌ تست ناموفق بود!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ تست توسط کاربر متوقف شد")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        traceback.print_exc()
        sys.exit(1)


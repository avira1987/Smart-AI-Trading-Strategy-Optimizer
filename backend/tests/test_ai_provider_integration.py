"""
تست‌های جامع برای بررسی مکانیزم API keys و استفاده از OpenAI برای پردازش استراتژی
این تست‌ها کل فرآیند از ذخیره API key تا استفاده در پردازش را بررسی می‌کنند
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import APIConfiguration
from ai_module.provider_manager import get_provider_manager
from ai_module.gemini_client import analyze_strategy_with_gemini, _providers_available
from ai_module.providers import _get_api_key
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_key_retrieval():
    """تست بررسی خواندن API key از دیتابیس"""
    print("\n" + "="*60)
    print("تست 1: بررسی خواندن API key از دیتابیس")
    print("="*60)
    
    # 1. بررسی API configهای موجود در دیتابیس
    print("\n1.1. بررسی API configهای موجود:")
    all_configs = APIConfiguration.objects.filter(is_active=True).all()
    print(f"   تعداد configهای active: {all_configs.count()}")
    
    for config in all_configs:
        print(f"   - Provider: {config.provider}, User: {config.user_id if config.user else 'System'}, "
              f"Active: {config.is_active}, Key Length: {len(config.api_key) if config.api_key else 0}")
    
    # 2. تست خواندن API key برای OpenAI
    print("\n1.2. تست خواندن API key برای OpenAI:")
    openai_key = _get_api_key('openai', 'OPENAI_API_KEY', user=None)
    print(f"   API Key (user=None): {'✅ پیدا شد' if openai_key else '❌ پیدا نشد'}, "
          f"طول: {len(openai_key) if openai_key else 0}")
    
    # 3. تست خواندن API key برای OpenAI با user
    test_user = User.objects.filter(is_staff=True).first()
    if test_user:
        print(f"\n1.3. تست خواندن API key با user (id={test_user.id}):")
        openai_key_user = _get_api_key('openai', 'OPENAI_API_KEY', user=test_user)
        print(f"   API Key (user={test_user.id}): {'✅ پیدا شد' if openai_key_user else '❌ پیدا نشد'}, "
              f"طول: {len(openai_key_user) if openai_key_user else 0}")
    else:
        print("\n1.3. تست خواندن API key با user: ❌ کاربر admin پیدا نشد")
    
    # 4. تست خواندن API key برای Gemini
    print("\n1.4. تست خواندن API key برای Gemini:")
    gemini_key = _get_api_key('gemini', 'GEMINI_API_KEY', user=None)
    print(f"   API Key (user=None): {'✅ پیدا شد' if gemini_key else '❌ پیدا نشد'}, "
          f"طول: {len(gemini_key) if gemini_key else 0}")
    
    return {
        'openai_key': openai_key,
        'gemini_key': gemini_key,
        'configs_count': all_configs.count()
    }

def test_provider_manager():
    """تست بررسی ProviderManager"""
    print("\n" + "="*60)
    print("تست 2: بررسی ProviderManager")
    print("="*60)
    
    # 1. تست بدون user
    print("\n2.1. تست ProviderManager بدون user:")
    manager_no_user = get_provider_manager(user=None)
    has_provider_no_user = manager_no_user.has_available_provider()
    print(f"   has_available_provider: {'✅ بله' if has_provider_no_user else '❌ خیر'}")
    print(f"   Providers: {list(manager_no_user.providers.keys())}")
    
    # 2. تست با user
    test_user = User.objects.filter(is_staff=True).first()
    if test_user:
        print(f"\n2.2. تست ProviderManager با user (id={test_user.id}):")
        manager_user = get_provider_manager(user=test_user)
        has_provider_user = manager_user.has_available_provider()
        print(f"   has_available_provider: {'✅ بله' if has_provider_user else '❌ خیر'}")
        print(f"   Providers: {list(manager_user.providers.keys())}")
    else:
        print("\n2.2. تست ProviderManager با user: ❌ کاربر admin پیدا نشد")
    
    return {
        'has_provider_no_user': has_provider_no_user,
        'has_provider_user': has_provider_user if test_user else None
    }

def test_providers_available():
    """تست بررسی تابع _providers_available"""
    print("\n" + "="*60)
    print("تست 3: بررسی تابع _providers_available")
    print("="*60)
    
    # 1. تست بدون user
    print("\n3.1. تست _providers_available بدون user:")
    available_no_user = _providers_available(user=None)
    print(f"   _providers_available: {'✅ بله' if available_no_user else '❌ خیر'}")
    
    # 2. تست با user
    test_user = User.objects.filter(is_staff=True).first()
    if test_user:
        print(f"\n3.2. تست _providers_available با user (id={test_user.id}):")
        available_user = _providers_available(user=test_user)
        print(f"   _providers_available: {'✅ بله' if available_user else '❌ خیر'}")
    else:
        print("\n3.2. تست _providers_available با user: ❌ کاربر admin پیدا نشد")
    
    return {
        'available_no_user': available_no_user,
        'available_user': available_user if test_user else None
    }

def test_strategy_analysis():
    """تست پردازش استراتژی با OpenAI"""
    print("\n" + "="*60)
    print("تست 4: تست پردازش استراتژی با OpenAI")
    print("="*60)
    
    # ایجاد یک استراتژی نمونه
    parsed_strategy = {
        'entry_conditions': ['RSI < 30', 'Price crosses above MA'],
        'exit_conditions': ['Take profit at 50 pips', 'Stop loss at 30 pips'],
        'risk_management': {'stop_loss': 30, 'take_profit': 50},
        'indicators': ['RSI', 'MA'],
        'symbol': 'EURUSD',
        'timeframe': '1h'
    }
    
    raw_text = """
    استراتژی معاملاتی:
    ورود: وقتی RSI زیر 30 باشد و قیمت از MA عبور کند
    خروج: سود 50 پیپ یا ضرر 30 پیپ
    """
    
    test_user = User.objects.filter(is_staff=True).first()
    
    print("\n4.1. بررسی در دسترس بودن provider قبل از تحلیل:")
    available = _providers_available(user=test_user)
    print(f"   Provider available: {'✅ بله' if available else '❌ خیر'}")
    
    if not available:
        print("\n   ⚠️ هیچ provider در دسترس نیست، نمی‌توان تحلیل را انجام داد")
        return None
    
    print("\n4.2. اجرای تحلیل استراتژی:")
    try:
        result = analyze_strategy_with_gemini(parsed_strategy, raw_text, user=test_user)
        
        ai_status = result.get('ai_status')
        message = result.get('message', '')
        error = result.get('error', '')
        provider = result.get('ai_provider') or result.get('provider', 'unknown')
        
        print(f"   AI Status: {ai_status}")
        print(f"   Provider: {provider}")
        print(f"   Message: {message[:100]}...")
        if error:
            print(f"   Error: {error[:200]}...")
        
        if ai_status == 'ok':
            print("\n   ✅ تحلیل با موفقیت انجام شد")
        elif ai_status == 'error':
            print("\n   ❌ خطا در تحلیل:")
            print(f"      {message}")
            if error:
                print(f"      {error}")
        elif ai_status == 'disabled':
            print("\n   ⚠️ تحلیل غیرفعال است:")
            print(f"      {message}")
        
        return result
        
    except Exception as e:
        print(f"\n   ❌ خطا در اجرای تست: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_provider_priority():
    """تست بررسی اولویت providerها"""
    print("\n" + "="*60)
    print("تست 5: بررسی اولویت providerها")
    print("="*60)
    
    from django.conf import settings
    priority_config = getattr(settings, 'AI_PROVIDER_PRIORITY', [])
    print(f"\n5.1. تنظیمات اولویت از settings:")
    print(f"   AI_PROVIDER_PRIORITY: {priority_config}")
    
    manager = get_provider_manager(user=None)
    priority_list = manager._get_priority_list()
    print(f"\n5.2. لیست اولویت نهایی:")
    for i, provider in enumerate(priority_list, 1):
        provider_obj = manager.providers.get(provider)
        if provider_obj:
            api_key = provider_obj.get_api_key()
            is_available = provider_obj.is_available()
            print(f"   {i}. {provider}: {'✅ Available' if is_available else '❌ Not Available'} "
                  f"(API Key Length: {len(api_key) if api_key else 0})")
        else:
            print(f"   {i}. {provider}: ❌ Not Found")
    
    return priority_list

def main():
    """اجرای همه تست‌ها"""
    print("\n" + "="*60)
    print("شروع تست‌های جامع API Provider و پردازش استراتژی")
    print("="*60)
    
    results = {}
    
    try:
        # تست 1: بررسی خواندن API key
        results['api_key'] = test_api_key_retrieval()
        
        # تست 2: بررسی ProviderManager
        results['provider_manager'] = test_provider_manager()
        
        # تست 3: بررسی _providers_available
        results['providers_available'] = test_providers_available()
        
        # تست 4: بررسی اولویت providerها
        results['priority'] = test_provider_priority()
        
        # تست 5: تست پردازش استراتژی
        results['analysis'] = test_strategy_analysis()
        
        # خلاصه نتایج
        print("\n" + "="*60)
        print("خلاصه نتایج:")
        print("="*60)
        print(f"\n✅ API Configs در DB: {results['api_key']['configs_count']}")
        print(f"✅ OpenAI Key: {'✅ پیدا شد' if results['api_key']['openai_key'] else '❌ پیدا نشد'}")
        print(f"✅ Gemini Key: {'✅ پیدا شد' if results['api_key']['gemini_key'] else '❌ پیدا نشد'}")
        print(f"✅ Provider Available (no user): {'✅ بله' if results['provider_manager']['has_provider_no_user'] else '❌ خیر'}")
        print(f"✅ _providers_available (no user): {'✅ بله' if results['providers_available']['available_no_user'] else '❌ خیر'}")
        
        if results['analysis']:
            ai_status = results['analysis'].get('ai_status')
            if ai_status == 'ok':
                print(f"✅ تحلیل استراتژی: ✅ موفق")
            else:
                print(f"⚠️ تحلیل استراتژی: ❌ {ai_status}")
                print(f"   Message: {results['analysis'].get('message', '')[:100]}")
        
    except Exception as e:
        print(f"\n❌ خطا در اجرای تست‌ها: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("پایان تست‌ها")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()


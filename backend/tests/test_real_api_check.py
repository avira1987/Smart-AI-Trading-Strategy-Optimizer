"""
تست واقعی و دقیق برای بررسی API key و پردازش استراتژی
این تست واقعاً API را فراخوانی می‌کند و صحت را بررسی می‌کند
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
from ai_module.providers import _get_api_key, get_registered_providers
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def check_api_keys_in_db():
    """بررسی دقیق API keys در دیتابیس"""
    print("\n" + "="*70)
    print("بررسی دقیق API keys در دیتابیس")
    print("="*70)
    
    all_configs = APIConfiguration.objects.filter(is_active=True).all()
    print(f"\nتعداد configهای active: {all_configs.count()}")
    
    for config in all_configs:
        print(f"\n{'='*70}")
        print(f"Config ID: {config.id}")
        print(f"Provider: {config.provider}")
        print(f"User ID: {config.user_id if config.user else 'System (None)'}")
        print(f"Is Active: {config.is_active}")
        print(f"API Key Length: {len(config.api_key) if config.api_key else 0}")
        
        # نمایش 20 کاراکتر اول کلید (برای تشخیص placeholder)
        if config.api_key:
            key_preview = config.api_key[:20] + "..." if len(config.api_key) > 20 else config.api_key
            print(f"API Key Preview: {key_preview}")
            
            # بررسی placeholder patterns
            key_lower = config.api_key.lower()
            placeholder_patterns = ['your-', 'placeholder', 'dummy', 'test-', 'example']
            found_patterns = [p for p in placeholder_patterns if p in key_lower]
            if found_patterns:
                print(f"⚠️ WARNING: Key looks like placeholder (contains: {', '.join(found_patterns)})")
            else:
                print("✅ Key doesn't look like placeholder")
            
            # بررسی فرمت OpenAI
            if config.provider == 'openai':
                if config.api_key.startswith('sk-'):
                    print("✅ OpenAI key format looks correct (starts with 'sk-')")
                else:
                    print(f"❌ OpenAI key format incorrect (should start with 'sk-', but starts with: {config.api_key[:5]})")
                if len(config.api_key) >= 20:
                    print(f"✅ OpenAI key length looks reasonable ({len(config.api_key)} chars)")
                else:
                    print(f"⚠️ OpenAI key seems short ({len(config.api_key)} chars, expected 50+)")
        
        print(f"{'='*70}")
    
    return all_configs

def test_api_key_retrieval_detailed():
    """تست دقیق خواندن API key"""
    print("\n" + "="*70)
    print("تست دقیق خواندن API key")
    print("="*70)
    
    # تست 1: بدون user
    print("\n1. تست بدون user (user=None):")
    openai_key = _get_api_key('openai', 'OPENAI_API_KEY', user=None)
    print(f"   Result: {openai_key[:20] + '...' if openai_key and len(openai_key) > 20 else openai_key}")
    print(f"   Length: {len(openai_key) if openai_key else 0}")
    print(f"   Found: {'✅ بله' if openai_key else '❌ خیر'}")
    
    # تست 2: با user
    test_user = User.objects.filter(is_staff=True).first()
    if test_user:
        print(f"\n2. تست با user (id={test_user.id}, username={test_user.username}):")
        openai_key_user = _get_api_key('openai', 'OPENAI_API_KEY', user=test_user)
        print(f"   Result: {openai_key_user[:20] + '...' if openai_key_user and len(openai_key_user) > 20 else openai_key_user}")
        print(f"   Length: {len(openai_key_user) if openai_key_user else 0}")
        print(f"   Found: {'✅ بله' if openai_key_user else '❌ خیر'}")
        
        # بررسی اینکه آیا کلید برای این user است یا system
        user_config = APIConfiguration.objects.filter(
            provider='openai',
            is_active=True,
            user=test_user
        ).first()
        if user_config:
            print(f"   Source: User-specific config (ID: {user_config.id})")
        else:
            system_config = APIConfiguration.objects.filter(
                provider='openai',
                is_active=True,
                user__isnull=True
            ).first()
            if system_config:
                print(f"   Source: System config (ID: {system_config.id})")
            else:
                admin_config = APIConfiguration.objects.filter(
                    provider='openai',
                    is_active=True
                ).first()
                if admin_config:
                    print(f"   Source: Admin config (ID: {admin_config.id}, User ID: {admin_config.user_id})")
    else:
        print("\n2. تست با user: ❌ کاربر admin پیدا نشد")
    
    return {
        'openai_key_no_user': openai_key,
        'openai_key_with_user': openai_key_user if test_user else None,
        'test_user': test_user
    }

def test_provider_is_available():
    """تست دقیق is_available برای provider"""
    print("\n" + "="*70)
    print("تست دقیق is_available برای Provider")
    print("="*70)
    
    providers = get_registered_providers()
    openai_provider = providers.get('openai')
    
    if not openai_provider:
        print("❌ OpenAI provider not found in registered providers")
        return
    
    # تست بدون user context
    print("\n1. تست بدون user context:")
    openai_provider.set_user_context(None)
    api_key = openai_provider.get_api_key()
    is_avail = openai_provider.is_available()
    
    print(f"   API Key: {api_key[:20] + '...' if api_key and len(api_key) > 20 else api_key}")
    print(f"   Key Length: {len(api_key) if api_key else 0}")
    print(f"   is_available(): {'✅ True' if is_avail else '❌ False'}")
    
    # تست با user context
    test_user = User.objects.filter(is_staff=True).first()
    if test_user:
        print(f"\n2. تست با user context (id={test_user.id}):")
        openai_provider.set_user_context(test_user)
        api_key_user = openai_provider.get_api_key()
        is_avail_user = openai_provider.is_available()
        
        print(f"   API Key: {api_key_user[:20] + '...' if api_key_user and len(api_key_user) > 20 else api_key_user}")
        print(f"   Key Length: {len(api_key_user) if api_key_user else 0}")
        print(f"   is_available(): {'✅ True' if is_avail_user else '❌ False'}")
    
    return {
        'is_available_no_user': is_avail,
        'is_available_with_user': is_avail_user if test_user else None
    }

def test_provider_manager_detailed():
    """تست دقیق ProviderManager"""
    print("\n" + "="*70)
    print("تست دقیق ProviderManager")
    print("="*70)
    
    test_user = User.objects.filter(is_staff=True).first()
    
    # تست بدون user
    print("\n1. تست بدون user:")
    manager_no_user = get_provider_manager(user=None)
    has_provider_no_user = manager_no_user.has_available_provider()
    
    print(f"   has_available_provider(): {'✅ True' if has_provider_no_user else '❌ False'}")
    
    # تست با user
    if test_user:
        print(f"\n2. تست با user (id={test_user.id}):")
        manager_user = get_provider_manager(user=test_user)
        has_provider_user = manager_user.has_available_provider()
        
        print(f"   has_available_provider(): {'✅ True' if has_provider_user else '❌ False'}")
    
    return {
        'has_provider_no_user': has_provider_no_user,
        'has_provider_user': has_provider_user if test_user else None
    }

def test_real_api_call():
    """تست واقعی فراخوانی API"""
    print("\n" + "="*70)
    print("تست واقعی فراخوانی API (نه فقط بررسی کلید)")
    print("="*70)
    
    test_user = User.objects.filter(is_staff=True).first()
    
    # بررسی اولیه
    print("\n1. بررسی در دسترس بودن provider:")
    available = _providers_available(user=test_user)
    print(f"   _providers_available(): {'✅ True' if available else '❌ False'}")
    
    if not available:
        print("\n   ⚠️ Provider در دسترس نیست، نمی‌توان تست واقعی را انجام داد")
        return None
    
    # تست واقعی با یک prompt ساده
    print("\n2. تست واقعی با prompt ساده:")
    providers = get_registered_providers()
    openai_provider = providers.get('openai')
    openai_provider.set_user_context(test_user)
    
    try:
        result = openai_provider.generate(
            prompt='Say "test" and return {"status": "ok"}.',
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 50,
            },
            metadata={'system_prompt': 'You must respond with valid JSON only.'}
        )
        
        print(f"   Success: {'✅ True' if result.success else '❌ False'}")
        print(f"   Provider: {result.provider}")
        if result.error:
            print(f"   Error: {result.error}")
        if result.text:
            print(f"   Response: {result.text[:100]}...")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """اجرای همه تست‌های دقیق"""
    print("\n" + "="*70)
    print("تست‌های واقعی و دقیق برای بررسی API Provider")
    print("="*70)
    
    try:
        # 1. بررسی API keys در دیتابیس
        db_configs = check_api_keys_in_db()
        
        # 2. تست خواندن API key
        key_results = test_api_key_retrieval_detailed()
        
        # 3. تست is_available
        availability_results = test_provider_is_available()
        
        # 4. تست ProviderManager
        manager_results = test_provider_manager_detailed()
        
        # 5. تست واقعی API call
        api_call_result = test_real_api_call()
        
        # خلاصه
        print("\n" + "="*70)
        print("خلاصه نتایج:")
        print("="*70)
        
        print(f"\n✅ Configs در DB: {db_configs.count()}")
        
        openai_key = key_results.get('openai_key_no_user') or key_results.get('openai_key_with_user')
        print(f"✅ API Key خوانده شده: {'✅ بله' if openai_key else '❌ خیر'}")
        if openai_key:
            print(f"   طول: {len(openai_key)}")
            print(f"   شروع: {openai_key[:10]}...")
        
        is_avail = availability_results.get('is_available_no_user') or availability_results.get('is_available_with_user')
        print(f"✅ is_available(): {'✅ True' if is_avail else '❌ False'}")
        
        has_provider = manager_results.get('has_provider_no_user') or manager_results.get('has_provider_user')
        print(f"✅ has_available_provider(): {'✅ True' if has_provider else '❌ False'}")
        
        if api_call_result:
            print(f"✅ تست واقعی API: {'✅ موفق' if api_call_result.success else '❌ ناموفق'}")
            if api_call_result.error:
                print(f"   خطا: {api_call_result.error}")
        else:
            print(f"✅ تست واقعی API: ⚠️ انجام نشد (provider در دسترس نبود)")
        
    except Exception as e:
        print(f"\n❌ خطا در اجرای تست‌ها: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("پایان تست‌ها")
    print("="*70 + "\n")

if __name__ == '__main__':
    main()


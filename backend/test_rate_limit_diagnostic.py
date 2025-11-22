"""
اسکریپت تست برای تشخیص منبع خطای Rate Limit
این اسکریپت بررسی می‌کند که آیا خطای Rate Limit از OpenAI API می‌آید یا از منطق برنامه
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import logging
from ai_module.provider_manager import get_provider_manager
from ai_module.gemini_client import JSON_ONLY_SYSTEM_PROMPT
from django.contrib.auth.models import User

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

def test_rate_limit_diagnostic():
    """تست تشخیص منبع خطای Rate Limit"""
    print("=" * 80)
    print("تست تشخیص منبع خطای Rate Limit")
    print("=" * 80)
    
    # Get a test user (use first user or create one)
    try:
        user = User.objects.first()
        if not user:
            print("❌ هیچ کاربری در پایگاه داده نیست")
            return
        print(f"✓ کاربر تست: {user.username}")
    except Exception as e:
        print(f"❌ خطا در دریافت کاربر: {e}")
        return
    
    # Create provider manager
    provider_manager = get_provider_manager(user=user)
    
    # Test with a simple prompt
    test_prompt = 'Return {"status": "test"} as compact JSON.'
    
    print("\n" + "=" * 80)
    print("در حال ارسال درخواست به OpenAI API...")
    print("=" * 80)
    
    try:
        generation_config = {
            'temperature': 0.3,
            'max_output_tokens': 128,
        }
        
        result = provider_manager.generate(
            prompt=test_prompt,
            generation_config=generation_config,
            metadata={'system_prompt': JSON_ONLY_SYSTEM_PROMPT}
        )
        
        print("\n" + "=" * 80)
        print("نتایج:")
        print("=" * 80)
        print(f"✓ Success: {result.success}")
        print(f"✓ Status Code: {result.status_code}")
        print(f"✓ Error: {result.error}")
        print(f"✓ Provider: {result.provider}")
        
        if result.attempts:
            print(f"\n✓ تعداد تلاش‌ها: {len(result.attempts)}")
            for i, attempt in enumerate(result.attempts, 1):
                print(f"\n  تلاش {i}:")
                print(f"    - Provider: {attempt.provider}")
                print(f"    - Success: {attempt.success}")
                print(f"    - Status Code: {attempt.status_code}")
                print(f"    - Error: {attempt.error}")
                print(f"    - Latency: {attempt.latency_ms}ms")
                
                # بررسی دقیق‌تر
                if attempt.status_code == 429:
                    print(f"\n    ⚠️  خطای 429 تشخیص داده شد!")
                    print(f"    ⚠️  این خطا از OpenAI API آمده است (واقعی)")
                    
                    # بررسی raw response اگر وجود دارد
                    if hasattr(result, 'raw_response'):
                        print(f"    - Raw Response: {result.raw_response}")
                        
        print("\n" + "=" * 80)
        print("تحلیل:")
        print("=" * 80)
        
        if result.success:
            print("✓ درخواست موفق بود - هیچ خطای Rate Limit وجود ندارد")
        else:
            if result.status_code == 429:
                print("⚠️  خطای 429 از OpenAI API دریافت شد")
                print("   این یعنی OpenAI واقعاً محدودیت نرخ اعمال کرده است")
                print("   راه‌حل: صبر کنید یا به حساب OpenAI خود برای افزایش محدودیت مراجعه کنید")
            elif result.status_code:
                print(f"⚠️  خطای HTTP {result.status_code} دریافت شد")
                if "rate limit" in (result.error or "").lower():
                    print("   پیام خطا شامل 'rate limit' است")
                print(f"   خطا: {result.error}")
            else:
                print("⚠️  خطا بدون status code (ممکن است از منطق برنامه باشد)")
                print(f"   خطا: {result.error}")
                
    except Exception as e:
        print(f"\n❌ خطا در اجرای تست: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_rate_limit_diagnostic()

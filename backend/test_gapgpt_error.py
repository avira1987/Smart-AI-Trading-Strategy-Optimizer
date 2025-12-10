"""
اسکریپت تست برای بررسی خطای واقعی GapGPT
این اسکریپت مستقیماً API را فراخوانی می‌کند و خطای دقیق را نمایش می‌دهد
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
import json
from ai_module.gapgpt_client import get_gapgpt_api_key
from ai_module.provider_manager import get_provider_manager
from ai_module.gemini_client import parse_with_gemini
from core.models import User

def test_gapgpt_api_directly():
    """تست مستقیم API GapGPT"""
    print("=" * 80)
    print("تست مستقیم API GapGPT")
    print("=" * 80)
    
    # دریافت API key
    api_key = get_gapgpt_api_key()
    if not api_key:
        print("❌ کلید API GapGPT یافت نشد!")
        return
    
    print(f"✅ کلید API یافت شد: {api_key[:20]}...")
    
    # تست ساده
    endpoint = "https://api.gapgpt.app/v1/chat/completions"
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test' and return {\"status\": \"ok\"} as JSON."}
        ],
        "temperature": 0.3,
        "max_tokens": 50,
        "response_format": {"type": "json_object"}
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("\n📤 ارسال درخواست به GapGPT API...")
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        
        print(f"\n📥 Status Code: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ درخواست موفق بود!")
            print(f"📄 Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ خطا دریافت شد: {response.status_code}")
            
            # خواندن خطا با encoding صحیح
            try:
                response.encoding = 'utf-8'
                error_data = response.json()
                print(f"\n📄 Error Response (JSON):")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
                
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_message = error_detail.get('message', '')
                    error_code = error_detail.get('code', '')
                    error_type = error_detail.get('type', '')
                    print(f"\n🔍 Error Details:")
                    print(f"   Message: {error_message}")
                    print(f"   Code: {error_code}")
                    print(f"   Type: {error_type}")
                elif isinstance(error_detail, str):
                    print(f"\n🔍 Error Message: {error_detail}")
            except:
                print(f"\n📄 Error Response (Text):")
                print(response.text[:500])
                
    except requests.exceptions.Timeout:
        print("❌ Timeout: درخواست بیش از 30 ثانیه طول کشید")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()


def test_provider_manager():
    """تست Provider Manager"""
    print("\n" + "=" * 80)
    print("تست Provider Manager")
    print("=" * 80)
    
    # دریافت کاربر اول
    user = User.objects.first()
    if user:
        print(f"👤 استفاده از کاربر: {user.username} (ID: {user.id})")
    else:
        print("⚠️  کاربری یافت نشد، استفاده از None")
        user = None
    
    manager = get_provider_manager(user=user)
    
    print(f"\n📋 Providers موجود: {list(manager.providers.keys())}")
    print(f"📋 Priority List: {manager._get_priority_list()}")
    print(f"📋 Has Available Provider: {manager.has_available_provider()}")
    
    # بررسی GapGPT
    gapgpt_provider = manager.providers.get('gapgpt')
    if gapgpt_provider:
        print(f"\n🔍 GapGPT Provider:")
        print(f"   Available: {gapgpt_provider.is_available()}")
        api_key = gapgpt_provider.get_api_key()
        if api_key:
            print(f"   API Key: {api_key[:20]}... (length: {len(api_key)})")
        else:
            print(f"   API Key: None")
    
    # تست generate
    print(f"\n🧪 تست generate با prompt ساده...")
    test_prompt = "Say 'test' and return {\"status\": \"ok\"} as JSON."
    
    try:
        result = manager.generate(
            test_prompt,
            {
                'temperature': 0.3,
                'max_output_tokens': 50,
                'response_format': {'type': 'json_object'}
            },
            metadata={'use_json_response_format': True}
        )
        
        print(f"\n📊 Result:")
        print(f"   Success: {result.success}")
        print(f"   Provider: {result.provider}")
        print(f"   Status Code: {result.status_code}")
        print(f"   Tokens Used: {result.tokens_used}")
        
        if result.success:
            print(f"   Text: {result.text[:200]}")
        else:
            print(f"   Error: {result.error}")
            print(f"   Attempts: {len(result.attempts)}")
            for i, attempt in enumerate(result.attempts, 1):
                print(f"\n   Attempt {i}:")
                print(f"      Provider: {attempt.provider}")
                print(f"      Success: {attempt.success}")
                print(f"      Status Code: {attempt.status_code}")
                print(f"      Error: {attempt.error}")
                print(f"      Latency: {attempt.latency_ms}ms")
                
    except Exception as e:
        print(f"❌ Error in generate: {e}")
        import traceback
        traceback.print_exc()


def test_parse_with_gemini():
    """تست parse_with_gemini"""
    print("\n" + "=" * 80)
    print("تست parse_with_gemini (که از provider manager استفاده می‌کند)")
    print("=" * 80)
    
    user = User.objects.first()
    if user:
        print(f"👤 استفاده از کاربر: {user.username} (ID: {user.id})")
    else:
        print("⚠️  کاربری یافت نشد، استفاده از None")
        user = None
    
    test_text = """
    استراتژی معاملاتی:
    - ورود: وقتی RSI زیر 30 باشد
    - خروج: وقتی RSI بالای 70 باشد
    - Stop Loss: 50 پیپ
    - Take Profit: 100 پیپ
    - نماد: EURUSD
    - تایم‌فریم: H1
    """
    
    print(f"\n🧪 تست parse_with_gemini...")
    try:
        result = parse_with_gemini(test_text, user=user)
        
        print(f"\n📊 Result:")
        print(f"   AI Status: {result.get('ai_status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   Provider: {result.get('provider')}")
        print(f"   Status Code: {result.get('status_code')}")
        
        if result.get('ai_status') == 'ok':
            print(f"   ✅ موفق بود!")
            print(f"   Entry Conditions: {result.get('entry_conditions', [])}")
            print(f"   Exit Conditions: {result.get('exit_conditions', [])}")
        else:
            print(f"   ❌ خطا:")
            print(f"   Error: {result.get('error')}")
            print(f"   Provider Attempts: {len(result.get('provider_attempts', []))}")
            
            for i, attempt in enumerate(result.get('provider_attempts', []), 1):
                print(f"\n   Attempt {i}:")
                if isinstance(attempt, dict):
                    print(f"      Provider: {attempt.get('provider')}")
                    print(f"      Success: {attempt.get('success')}")
                    print(f"      Status Code: {attempt.get('status_code')}")
                    print(f"      Error: {attempt.get('error')}")
                    print(f"      Latency: {attempt.get('latency_ms')}ms")
                else:
                    print(f"      {attempt}")
                    
    except Exception as e:
        print(f"❌ Error in parse_with_gemini: {e}")
        import traceback
        traceback.print_exc()


def main():
    """اجرای تمام تست‌ها"""
    print("\n" + "=" * 80)
    print("🧪 شروع تست‌های GapGPT")
    print("=" * 80)
    
    # تست 1: تست مستقیم API
    test_gapgpt_api_directly()
    
    # تست 2: تست Provider Manager
    test_provider_manager()
    
    # تست 3: تست parse_with_gemini
    test_parse_with_gemini()
    
    print("\n" + "=" * 80)
    print("✅ تست‌ها کامل شدند")
    print("=" * 80)


if __name__ == '__main__':
    main()

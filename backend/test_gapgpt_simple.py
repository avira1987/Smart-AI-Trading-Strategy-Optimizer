#!/usr/bin/env python
"""تست ساده برای بررسی خطای GapGPT"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    print("✅ Django setup successful")
except Exception as e:
    print(f"❌ Django setup failed: {e}")
    sys.exit(1)

import requests
import json
from ai_module.gapgpt_client import get_gapgpt_api_key

def main():
    print("\n" + "=" * 80)
    print("🧪 تست GapGPT API")
    print("=" * 80)
    
    # دریافت API key
    api_key = get_gapgpt_api_key()
    if not api_key:
        print("❌ کلید API GapGPT یافت نشد!")
        print("   بررسی کنید که کلید در دیتابیس یا environment variable تنظیم شده باشد.")
        return
    
    print(f"✅ کلید API یافت شد: {api_key[:20]}... (طول: {len(api_key)})")
    
    # تست ساده
    endpoint = "https://api.gapgpt.app/v1/chat/completions"
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'test'"}
        ],
        "temperature": 0.3,
        "max_tokens": 50
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n📤 ارسال درخواست به: {endpoint}")
    print(f"📤 Model: {payload['model']}")
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        
        print(f"\n📥 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ درخواست موفق بود!")
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                print(f"📄 Response: {content}")
        else:
            print(f"❌ خطا دریافت شد: {response.status_code}")
            
            # خواندن خطا
            try:
                response.encoding = 'utf-8'
                error_data = response.json()
                print(f"\n📄 Error Response:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
                
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_message = error_detail.get('message', '')
                    error_code = error_detail.get('code', '')
                    error_type = error_detail.get('type', '')
                    print(f"\n🔍 جزئیات خطا:")
                    print(f"   Message: {error_message}")
                    print(f"   Code: {error_code}")
                    print(f"   Type: {error_type}")
                    
                    # بررسی quota error
                    if any(char in error_message for char in ['预扣费', '额度', '剩余额度', '需要']):
                        print("\n⚠️  این خطا مربوط به QUOTA است!")
                    elif '额度' in error_message or 'quota' in error_message.lower():
                        print("\n⚠️  این خطا مربوط به QUOTA است!")
                    else:
                        print("\n⚠️  این خطا مربوط به QUOTA نیست!")
                        print("   احتمالاً مشکل دیگری است (مدل، دسترسی، و غیره)")
                        
                elif isinstance(error_detail, str):
                    print(f"\n🔍 Error Message: {error_detail}")
            except Exception as e:
                print(f"\n📄 Error Response (Text):")
                print(response.text[:500])
                print(f"\n⚠️  خطا در خواندن JSON: {e}")
                
    except requests.exceptions.Timeout:
        print("❌ Timeout: درخواست بیش از 30 ثانیه طول کشید")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

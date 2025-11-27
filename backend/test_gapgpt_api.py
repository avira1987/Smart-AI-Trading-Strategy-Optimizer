"""
تست اتصال به GapGPT API
این فایل برای تست اولیه API GapGPT استفاده می‌شود
"""

import os
import sys
import django
import requests
import json

# تنظیم Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# کلید API GapGPT
GAPGPT_API_KEY = "sk-kIXLQoKiiryl775Y0YRzcNEAvW84WSGaBWurzapLaUJ29MJG"
GAPGPT_API_BASE_URL = "https://api.gapgpt.app"  # فرض می‌کنیم این endpoint است


def test_gapgpt_connection():
    """تست اولیه اتصال به GapGPT API"""
    print("=" * 80)
    print("تست اتصال به GapGPT API")
    print("=" * 80)
    
    # تست 1: دریافت لیست مدل‌ها
    print("\n[تست 1] دریافت لیست مدل‌ها...")
    try:
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/models"
        headers = {
            "Authorization": f"Bearer {GAPGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(endpoint, headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ موفق! لیست مدل‌ها دریافت شد:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        else:
            print(f"✗ خطا: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ خطا: Timeout - اتصال به API طول کشید")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ خطا: Connection Error - {e}")
        return False
    except Exception as e:
        print(f"✗ خطا غیرمنتظره: {e}")
        return False


def test_gapgpt_chat_completion():
    """تست ارسال درخواست chat completion"""
    print("\n" + "=" * 80)
    print("تست ارسال درخواست Chat Completion")
    print("=" * 80)
    
    try:
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/chat/completions"
        
        # استفاده از مدل‌هایی که در لیست موجود هستند
        # امتحان با gpt-4o که در لیست موجود است
        payload = {
            "model": "gpt-4o",  # تغییر به مدل موجود
            "messages": [
                {
                    "role": "system",
                    "content": "شما یک دستیار فارسی هستید. پاسخ‌ها را مختصر و مفید بدهید."
                },
                {
                    "role": "user",
                    "content": "سلام! لطفاً یک جمله کوتاه فارسی بگو."
                }
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        headers = {
            "Authorization": f"Bearer {GAPGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"\nEndpoint: {endpoint}")
        print(f"Model: {payload['model']}")
        print("Sending request...")
        
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ موفق! پاسخ دریافت شد:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # استخراج متن پاسخ
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                print(f"\n📝 پاسخ مدل: {content}")
            
            # اطلاعات استفاده
            if 'usage' in data:
                usage = data['usage']
                print(f"\n📊 استفاده از توکن‌ها: {usage}")
            
            return True
        else:
            print(f"✗ خطا: {response.status_code}")
            print(f"Response Text:\n{response.text}")
            
            # تلاش برای پارس کردن خطا
            try:
                error_data = response.json()
                print(f"\nError Details:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                pass
            
            return False
            
    except requests.exceptions.Timeout:
        print("✗ خطا: Timeout - درخواست بیش از 30 ثانیه طول کشید")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ خطا: Connection Error - {e}")
        return False
    except Exception as e:
        print(f"✗ خطا غیرمنتظره: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gapgpt_strategy_conversion():
    """تست تبدیل استراتژی"""
    print("\n" + "=" * 80)
    print("تست تبدیل استراتژی معاملاتی")
    print("=" * 80)
    
    strategy_text = """
    استراتژی RSI:
    - وقتی RSI کمتر از 30 باشد، خرید کن
    - وقتی RSI بیشتر از 70 باشد، بفروش
    - حد ضرر: 50 پیپ
    - حد سود: 100 پیپ
    """
    
    try:
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/chat/completions"
        
        prompt = f"""این یک استراتژی معاملاتی است. لطفاً آن را به JSON تبدیل کن:

{strategy_text}

خروجی باید JSON باشد با ساختار:
{{
    "entry_conditions": ["..."],
    "exit_conditions": ["..."],
    "risk_management": {{"stop_loss": 50, "take_profit": 100}}
}}
"""
        
        payload = {
            "model": "gpt-4o",  # تغییر به مدل موجود
            "messages": [
                {
                    "role": "system",
                    "content": "شما یک متخصص تبدیل استراتژی معاملاتی هستید. همیشه JSON معتبر برگردانید."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {GAPGPT_API_KEY}",
            "Content-Type": "application/json"
        }
        
        print(f"\nSending strategy conversion request...")
        
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✓ موفق! استراتژی تبدیل شد:")
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0].get('message', {}).get('content', '')
                print(f"\n📝 پاسخ خام:\n{content}")
                
                # تلاش برای پارس کردن JSON
                try:
                    strategy_json = json.loads(content)
                    print(f"\n✓ JSON معتبر است!")
                    print(json.dumps(strategy_json, indent=2, ensure_ascii=False))
                except json.JSONDecodeError as e:
                    print(f"\n⚠ هشدار: نتوانست JSON را پارس کند: {e}")
            
            return True
        else:
            print(f"✗ خطا: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ خطا: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_endpoints():
    """تست endpointهای مختلف احتمالی"""
    print("\n" + "=" * 80)
    print("تست endpointهای مختلف")
    print("=" * 80)
    
    possible_endpoints = [
        "https://api.gapgpt.app/v1/models",
        "https://api.gapgpt.app/v1/chat/completions",
        "https://gapgpt.app/api/v1/models",
        "https://gapgpt.app/api/v1/chat/completions",
        "https://api.gapgpt.app/models",
        "https://api.gapgpt.app/chat/completions",
    ]
    
    headers = {
        "Authorization": f"Bearer {GAPGPT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    working_endpoints = []
    
    for endpoint in possible_endpoints:
        print(f"\n[تست] {endpoint}")
        try:
            if "models" in endpoint:
                response = requests.get(endpoint, headers=headers, timeout=5)
            else:
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json={"model": "gpt-4", "messages": [{"role": "user", "content": "test"}]},
                    timeout=5
                )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 401, 403]:  # حتی خطاهای auth نشان می‌دهد endpoint معتبر است
                print(f"  ✓ Endpoint معتبر است!")
                working_endpoints.append((endpoint, response.status_code))
            else:
                print(f"  ✗ Status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error: {type(e).__name__}")
        except Exception as e:
            print(f"  ✗ Unexpected: {e}")
    
    if working_endpoints:
        print(f"\n✓ Endpointهای معتبر پیدا شد:")
        for endpoint, status in working_endpoints:
            print(f"  - {endpoint} (Status: {status})")
    else:
        print("\n✗ هیچ endpoint معتبری پیدا نشد")
    
    return working_endpoints


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🔍 تست کامل GapGPT API")
    print("=" * 80)
    print(f"\nAPI Key: {GAPGPT_API_KEY[:20]}...")
    print(f"Base URL: {GAPGPT_API_BASE_URL}\n")
    
    results = {}
    
    # تست 1: بررسی endpointهای مختلف
    results['endpoints'] = test_different_endpoints()
    
    # تست 2: اتصال به API
    results['models'] = test_gapgpt_connection()
    
    # تست 3: Chat completion
    if results.get('models') or results.get('endpoints'):
        results['chat'] = test_gapgpt_chat_completion()
    
    # تست 4: تبدیل استراتژی
    if results.get('chat'):
        results['strategy'] = test_gapgpt_strategy_conversion()
    
    # خلاصه نتایج
    print("\n" + "=" * 80)
    print("📊 خلاصه نتایج تست")
    print("=" * 80)
    for test_name, result in results.items():
        status = "✓ موفق" if result else "✗ ناموفق"
        print(f"{test_name}: {status}")
    
    # پیشنهادات
    print("\n" + "=" * 80)
    print("💡 پیشنهادات")
    print("=" * 80)
    
    if not any(results.values()):
        print("⚠ هیچ یک از تست‌ها موفق نبود.")
        print("لطفاً بررسی کنید:")
        print("  1. کلید API معتبر است؟")
        print("  2. Endpoint صحیح است؟")
        print("  3. اتصال اینترنت برقرار است؟")
        print("  4. مستندات GapGPT را بررسی کنید: https://gapgpt.app/platform/quickstart")
    elif results.get('chat'):
        print("✓ API به درستی کار می‌کند!")
        print("می‌توانید به سراغ توسعه کامل بروید.")
    else:
        print("⚠ برخی تست‌ها ناموفق بودند.")
        print("لطفاً endpoint و فرمت درخواست را بررسی کنید.")


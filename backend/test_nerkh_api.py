"""
تست API نرخ (nerkh.io) با استفاده از Proxy
برای استفاده از IP محلی کلاینت
"""

import requests
import os
import sys
from typing import Optional, Tuple

# تنظیم encoding برای Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# کلید API
# API key should be set via environment variable
# For testing, set NERKH_API_KEY in your .env file
import os
API_KEY = os.getenv('NERKH_API_KEY', '')
if not API_KEY:
    print("⚠️  Warning: NERKH_API_KEY not set. Please set it in your .env file.")

# آدرس Proxy (IP محلی کلاینت)
# مثال: http://192.168.100.9:8080 یا socks5://192.168.100.9:1080
PROXY = os.getenv('NERKH_PROXY', 'http://192.168.100.9:8080')  # تغییر به IP کلاینت

# Base URL
BASE_URL = "https://nerkh.io/api"

# Endpoint های محتمل برای طلا
GOLD_ENDPOINTS = [
    "/gold/24k",
    "/gold/18k", 
    "/metal/gold",
    "/price/gold",
    "/v1/gold",
    "/api/gold",
    "/gold",
    "/metals/gold",
    "/price/24k",
    "/latest/gold",
]

def test_without_proxy():
    """تست بدون proxy (برای مقایسه)"""
    print("=" * 60)
    print("[TEST] تست بدون Proxy (از VPS مستقیم)")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    try:
        # تست endpoint اصلی
        response = requests.get(
            f"{BASE_URL}/gold",
            headers=headers,
            timeout=10,
            verify=True
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        
        if response.status_code == 200:
            print("[OK] موفق - بدون proxy کار کرد!")
            return True, response.json()
        else:
            print(f"[ERROR] خطا: {response.status_code}")
            return False, None
            
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] خطای اتصال: {e}")
        print("[TIP] احتمالاً از IP ایران قابل دسترسی نیست")
        return False, None
    except Exception as e:
        print(f"[ERROR] خطا: {e}")
        return False, None


def test_with_proxy(endpoint: str = "/gold"):
    """تست با proxy"""
    print("=" * 60)
    print(f"[TEST] تست با Proxy: {PROXY}")
    print(f"[ENDPOINT] Endpoint: {BASE_URL}{endpoint}")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    proxies = {
        'http': PROXY,
        'https': PROXY,
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=headers,
            proxies=proxies,
            timeout=15,
            verify=True
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n[OK] موفق! داده دریافت شد:")
                print(f"Data: {data}")
                return True, data
            except:
                print(f"\n[OK] موفق! اما پاسخ JSON نیست")
                return True, response.text
        else:
            print(f"[ERROR] خطا: HTTP {response.status_code}")
            return False, None
            
    except requests.exceptions.ProxyError as e:
        print(f"[ERROR] خطای Proxy: {e}")
        print("\n[TIP] راهنمایی:")
        print("   1. مطمئن شوید proxy روی کلاینت در حال اجرا است")
        print(f"   2. IP و Port صحیح است: {PROXY}")
        print("   3. Proxy از نوع HTTP یا SOCKS5 است")
        return False, None
    except requests.exceptions.ConnectionError as e:
        print(f"[ERROR] خطای اتصال: {e}")
        print("[TIP] احتمالاً proxy در دسترس نیست")
        return False, None
    except Exception as e:
        print(f"[ERROR] خطای ناشناخته: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_multiple_endpoints():
    """تست چند endpoint مختلف"""
    print("\n" + "=" * 60)
    print("[TEST] تست چندین Endpoint مختلف")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json',
    }
    
    proxies = {
        'http': PROXY,
        'https': PROXY,
    }
    
    successful_endpoints = []
    
    for endpoint in GOLD_ENDPOINTS:
        print(f"\n📡 تست: {endpoint}")
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                proxies=proxies,
                timeout=10,
                verify=True
            )
            
            if response.status_code == 200:
                print(f"   [OK] موفق! Status: {response.status_code}")
                successful_endpoints.append(endpoint)
                try:
                    data = response.json()
                    print(f"   [DATA] Data: {str(data)[:100]}")
                except:
                    print(f"   [TEXT] Response: {response.text[:100]}")
            else:
                print(f"   [WARN] Status: {response.status_code}")
                
        except Exception as e:
            print(f"   [ERROR] خطا: {str(e)[:50]}")
    
    return successful_endpoints


def test_api_info():
    """تست اطلاعات API"""
    print("\n" + "=" * 60)
    print("[TEST] تست Endpoint های عمومی")
    print("=" * 60)
    
    proxies = {
        'http': PROXY,
        'https': PROXY,
    }
    
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json',
    }
    
    # Endpoint های محتمل
    info_endpoints = [
        "/",
        "/info",
        "/status",
        "/health",
        "/v1",
        "/api",
    ]
    
    for endpoint in info_endpoints:
        try:
            response = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers,
                proxies=proxies,
                timeout=5,
                verify=True
            )
            print(f"{endpoint}: Status {response.status_code}")
            if response.status_code == 200:
                print(f"   Response: {response.text[:100]}")
        except:
            pass


def main():
    """تابع اصلی"""
    print("\n" + "[START] شروع تست API نرخ (nerkh.io)")
    print("=" * 60)
    print(f"API Key: {API_KEY[:20]}...")
    print(f"Proxy: {PROXY}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 60)
    
    # 1. تست بدون proxy
    print("\n[1] تست بدون Proxy")
    success_no_proxy, data_no_proxy = test_without_proxy()
    
    # 2. تست با proxy
    print("\n[2] تست با Proxy")
    success_with_proxy, data_with_proxy = test_with_proxy()
    
    # 3. تست endpoint های مختلف
    print("\n[3] تست Endpoint های مختلف")
    successful_endpoints = test_multiple_endpoints()
    
    # 4. تست endpoint های عمومی
    test_api_info()
    
    # نتیجه نهایی
    print("\n" + "=" * 60)
    print("[SUMMARY] خلاصه نتایج")
    print("=" * 60)
    print(f"[RESULT] بدون Proxy: {'موفق' if success_no_proxy else 'ناموفق'}")
    print(f"[RESULT] با Proxy: {'موفق' if success_with_proxy else 'ناموفق'}")
    print(f"[RESULT] Endpoint های موفق: {len(successful_endpoints)}")
    if successful_endpoints:
        print(f"   - {', '.join(successful_endpoints)}")
    
    print("\n[TIP] توصیه:")
    if success_with_proxy:
        print("   [OK] Proxy کار می‌کند! می‌توانید از این روش استفاده کنید.")
    else:
        print("   [ERROR] Proxy کار نکرد. بررسی کنید:")
        print("      1. Proxy روی کلاینت در حال اجرا است؟")
        print("      2. IP و Port صحیح است؟")
        print("      3. Firewall مسدود نمی‌کند؟")
        print("      4. از VPN کلاینت مطمئن شوید proxy از IP ایران استفاده می‌کند")


if __name__ == "__main__":
    # امکان تنظیم proxy از command line
    if len(sys.argv) > 1:
        PROXY = sys.argv[1]
        print(f"[CONFIG] Proxy از command line تنظیم شد: {PROXY}")
    
    main()


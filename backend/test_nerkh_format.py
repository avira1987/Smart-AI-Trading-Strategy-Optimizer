"""
تست فرمت‌های مختلف درخواست به nerkh.io
"""

import requests
import sys
import io
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "KKpWyVfgSpg8cu5dbDiENhvTtcpLgCL-uenJG24M1_c="
BASE_URL = "https://nerkh.io"

def test_with_token_in_url():
    """تست با token در URL"""
    print("\n[TEST 1] تست با token در URL (query parameter)")
    print("=" * 70)
    
    endpoints = [
        "/api",
        "/api/gold",
        "/api/price",
        "/api/rates",
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}?token={API_KEY}"
        try:
            response = requests.get(url, timeout=5)
            print(f"{endpoint}?token=... -> Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   [OK] Success! {response.text[:100]}")
            elif response.status_code != 404:
                print(f"   [INTERESTING] {response.text[:100]}")
        except Exception as e:
            print(f"{endpoint} -> Error: {str(e)[:50]}")


def test_with_apikey_header():
    """تست با X-API-Key header"""
    print("\n[TEST 2] تست با X-API-Key header")
    print("=" * 70)
    
    endpoints = [
        "/api",
        "/api/gold",
        "/api/price",
        "/api/rates",
    ]
    
    for endpoint in endpoints:
        headers = {
            'X-API-Key': API_KEY,
            'Accept': 'application/json',
        }
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            print(f"{endpoint} -> Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   [OK] Success! {response.text[:100]}")
            elif response.status_code != 404:
                print(f"   [INTERESTING] {response.text[:100]}")
        except Exception as e:
            print(f"{endpoint} -> Error: {str(e)[:50]}")


def test_with_bearer_token():
    """تست با Bearer token"""
    print("\n[TEST 3] تست با Bearer token (Authorization header)")
    print("=" * 70)
    
    endpoints = [
        "/api",
        "/api/gold",
        "/api/price",
        "/api/rates",
        "/api/v1/gold",
    ]
    
    for endpoint in endpoints:
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Accept': 'application/json',
        }
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            print(f"{endpoint} -> Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   [OK] Success! {response.text[:100]}")
            elif response.status_code != 404:
                print(f"   [INTERESTING] {response.text[:100]}")
        except Exception as e:
            print(f"{endpoint} -> Error: {str(e)[:50]}")


def test_without_auth():
    """تست بدون authentication"""
    print("\n[TEST 4] تست بدون authentication (برای دیدن endpoint اصلی)")
    print("=" * 70)
    
    endpoints = [
        "/",
        "/api",
        "/api/docs",
        "/api/documentation",
        "/api/help",
        "/docs",
        "/documentation",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"{endpoint} -> Status: {response.status_code}")
            if response.status_code == 200:
                # بررسی آیا مستندات یا endpoint list دارد
                text = response.text.lower()
                if 'api' in text or 'endpoint' in text or 'documentation' in text:
                    print(f"   [INTERESTING] ممکن است مستندات باشد")
                    print(f"   Content: {response.text[:200]}")
        except Exception as e:
            print(f"{endpoint} -> Error: {str(e)[:50]}")


def test_root_page():
    """بررسی صفحه اصلی برای پیدا کردن endpoint"""
    print("\n[TEST 5] بررسی صفحه اصلی برای پیدا کردن اطلاعات API")
    print("=" * 70)
    
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            text = response.text
            # جستجو برای endpoint های API
            import re
            api_patterns = [
                r'/api/[^"\s]+',
                r'api/[^"\s]+',
                r'endpoint[^"\s]+',
            ]
            
            found_endpoints = set()
            for pattern in api_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                found_endpoints.update(matches)
            
            if found_endpoints:
                print("[FOUND] Endpoint های پیدا شده در صفحه اصلی:")
                for ep in sorted(found_endpoints)[:20]:  # فقط 20 اول
                    print(f"   - {ep}")
            else:
                print("[INFO] endpoint خاصی در صفحه اصلی پیدا نشد")
    except Exception as e:
        print(f"[ERROR] {e}")


def main():
    print("=" * 70)
    print("[TEST] تست فرمت‌های مختلف درخواست به nerkh.io")
    print("=" * 70)
    print(f"API Key: {API_KEY[:30]}...")
    print(f"Base URL: {BASE_URL}")
    
    test_root_page()
    test_without_auth()
    test_with_token_in_url()
    test_with_apikey_header()
    test_with_bearer_token()
    
    print("\n" + "=" * 70)
    print("[SUMMARY] تست تمام شد")
    print("=" * 70)


if __name__ == "__main__":
    main()


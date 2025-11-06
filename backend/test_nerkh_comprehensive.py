"""
تست جامع برای پیدا کردن endpoint صحیح nerkh.io
"""

import requests
import sys
import io
import json

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_KEY = "KKpWyVfgSpg8cu5dbDiENhvTtcpLgCL-uenJG24M1_c="

def test_docs_page():
    """بررسی صفحه مستندات"""
    print("[TEST] بررسی صفحه مستندات")
    print("=" * 70)
    
    docs_urls = [
        "https://docs.nerkh.io",
        "https://nerkh.io/docs",
        "https://nerkh.io/documentation",
        "https://nerkh.io/api/docs",
        "https://nerkh.io/wiki",
        "https://wiki.nerkh.io",
    ]
    
    for url in docs_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[OK] {url} - Status: 200")
                # جستجو برای endpoint
                if 'api' in response.text.lower() or 'endpoint' in response.text.lower():
                    print(f"   [FOUND] ممکن است مستندات باشد")
                    # استخراج endpoint های احتمالی
                    import re
                    endpoints = re.findall(r'/api/[^"\s\)]+', response.text)
                    if endpoints:
                        print(f"   Endpoints found: {set(endpoints[:10])}")
            else:
                print(f"[INFO] {url} - Status: {response.status_code}")
        except:
            pass


def test_common_api_patterns():
    """تست الگوهای رایج API"""
    print("\n[TEST] تست الگوهای رایج API")
    print("=" * 70)
    
    # الگوهای مختلف
    patterns = [
        # با token در query
        ("https://nerkh.io/api/gold", {"token": API_KEY}),
        ("https://nerkh.io/api/price/gold", {"token": API_KEY}),
        ("https://nerkh.io/api/rates/gold", {"token": API_KEY}),
        ("https://nerkh.io/api/forex/XAUUSD", {"token": API_KEY}),
        # با key در query
        ("https://nerkh.io/api/gold", {"key": API_KEY}),
        ("https://nerkh.io/api/gold", {"api_key": API_KEY}),
        ("https://nerkh.io/api/gold", {"apikey": API_KEY}),
        # با header
        ("https://nerkh.io/api/gold", None, {"X-API-Key": API_KEY}),
        ("https://nerkh.io/api/gold", None, {"Authorization": f"Bearer {API_KEY}"}),
        ("https://nerkh.io/api/gold", None, {"Authorization": f"Token {API_KEY}"}),
        ("https://nerkh.io/api/gold", None, {"X-Auth-Token": API_KEY}),
    ]
    
    successful = []
    
    for pattern in patterns:
        url = pattern[0]
        params = pattern[1] if len(pattern) > 1 and pattern[1] else {}
        headers = pattern[2] if len(pattern) > 2 else {}
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"[OK] {url} - Status: 200")
                print(f"   Params: {params}")
                print(f"   Headers: {list(headers.keys())}")
                print(f"   Response: {response.text[:150]}")
                successful.append((url, params, headers, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text))
            elif response.status_code in [401, 403]:
                print(f"[INTERESTING] {url} - Status: {response.status_code} (Auth needed)")
            elif response.status_code != 404:
                print(f"[OTHER] {url} - Status: {response.status_code}")
        except Exception as e:
            pass
    
    return successful


def main():
    print("=" * 70)
    print("[COMPREHENSIVE TEST] تست جامع nerkh.io API")
    print("=" * 70)
    
    test_docs_page()
    successful = test_common_api_patterns()
    
    print("\n" + "=" * 70)
    print("[SUMMARY] خلاصه")
    print("=" * 70)
    
    if successful:
        print(f"[SUCCESS] {len(successful)} endpoint موفق پیدا شد!")
        for url, params, headers, data in successful:
            print(f"\n✅ {url}")
            print(f"   Params: {params}")
            print(f"   Headers: {headers}")
            print(f"   Data: {str(data)[:200]}")
    else:
        print("[FAILED] هیچ endpoint موفقی پیدا نشد")
        print("\n[RECOMMENDATION] پیشنهاد:")
        print("   1. از API های جایگزین استفاده کنید")
        print("   2. از MT5 برای قیمت لحظه‌ای استفاده کنید")


if __name__ == "__main__":
    main()


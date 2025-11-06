"""
تست endpoint های مختلف nerkh.io برای پیدا کردن endpoint صحیح
"""

import requests
import sys
import io

# تنظیم encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# API key should be set via environment variable
# For testing, set NERKH_API_KEY in your .env file
import os
API_KEY = os.getenv('NERKH_API_KEY', '')
if not API_KEY:
    print("⚠️  Warning: NERKH_API_KEY not set. Please set it in your .env file.")
BASE_URL = "https://nerkh.io"

# Endpoint های محتمل بر اساس مستندات nerkh.io
ENDPOINTS = [
    "/api/v1/gold",
    "/api/v1/price/gold",
    "/api/v1/metal/gold",
    "/api/gold",
    "/api/price/gold",
    "/api/metal/gold",
    "/api/v1/gold/24k",
    "/api/v1/gold/18k",
    "/api/gold/24k",
    "/api/gold/18k",
    "/api/latest/gold",
    "/api/current/gold",
    "/api/rates/gold",
    "/api/currency/gold",
    "/api/forex/gold",
    "/api/forex/XAUUSD",
    "/api/forex/XAU/USD",
    "/api/forex/xauusd",
    "/api/forex/xau-usd",
    "/api/forex/xau_usd",
    "/api/forex/gold-usd",
    "/api/forex/gold_usd",
    "/api/forex/gold/usd",
    "/api/metals/gold",
    "/api/metals/XAU",
    "/api/metals/XAUUSD",
    "/api/commodities/gold",
    "/api/commodities/XAU",
    "/api/prices/gold",
    "/api/prices/XAU",
    "/api/prices/XAUUSD",
    "/api/spot/gold",
    "/api/spot/XAU",
    "/api/spot/XAUUSD",
    "/api/realtime/gold",
    "/api/realtime/XAU",
    "/api/realtime/XAUUSD",
    "/api/ws/gold",
    "/api/ws/XAU",
    "/api/ws/XAUUSD",
    "/api/rest/gold",
    "/api/rest/XAU",
    "/api/rest/XAUUSD",
    "/gold",
    "/price/gold",
    "/metal/gold",
    "/metals/gold",
    "/forex/gold",
    "/forex/XAUUSD",
    "/rates/gold",
    "/currency/gold",
    "/commodities/gold",
    "/spot/gold",
    "/realtime/gold",
    "/ws/gold",
    "/rest/gold",
    "/v1/gold",
    "/v1/price/gold",
    "/v1/metal/gold",
    "/v1/metals/gold",
    "/v1/forex/gold",
    "/v1/forex/XAUUSD",
    "/v1/rates/gold",
    "/v1/currency/gold",
    "/v1/commodities/gold",
    "/v1/spot/gold",
    "/v1/realtime/gold",
]

def test_endpoint(endpoint):
    """تست یک endpoint"""
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, timeout=5, verify=True)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return True, data, response.status_code
            except:
                # اگر JSON نیست، بررسی کنیم آیا حاوی اطلاعات مفید است
                text = response.text.lower()
                if 'gold' in text or 'xau' in text or 'price' in text or 'rate' in text:
                    return True, response.text[:200], response.status_code
                return False, None, response.status_code
        elif response.status_code == 401:
            return False, "Unauthorized - API key مشکل دارد", response.status_code
        elif response.status_code == 403:
            return False, "Forbidden - دسترسی ندارید", response.status_code
        else:
            return False, None, response.status_code
            
    except requests.exceptions.ConnectionError:
        return False, "Connection Error", None
    except Exception as e:
        return False, str(e)[:50], None


def main():
    print("=" * 70)
    print("[TEST] تست Endpoint های مختلف nerkh.io")
    print("=" * 70)
    print(f"API Key: {API_KEY[:30]}...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 70)
    
    successful = []
    interesting = []  # پاسخ‌های جالب (مثلاً 401, 403)
    
    for i, endpoint in enumerate(ENDPOINTS, 1):
        success, data, status = test_endpoint(endpoint)
        
        if success:
            print(f"\n[{i}/{len(ENDPOINTS)}] {endpoint}")
            print(f"   [OK] Status: {status}")
            print(f"   [DATA] {str(data)[:150]}")
            successful.append((endpoint, data, status))
        elif status in [401, 403]:
            print(f"\n[{i}/{len(ENDPOINTS)}] {endpoint}")
            print(f"   [INTERESTING] Status: {status} - {data}")
            interesting.append((endpoint, data, status))
        elif status and status != 404:
            print(f"\n[{i}/{len(ENDPOINTS)}] {endpoint}")
            print(f"   [OTHER] Status: {status}")
        else:
            # فقط برای endpoint های اولیه نمایش بده
            if i <= 10:
                print(f"[{i}/{len(ENDPOINTS)}] {endpoint} - 404")
    
    # خلاصه
    print("\n" + "=" * 70)
    print("[SUMMARY] خلاصه نتایج")
    print("=" * 70)
    print(f"[SUCCESS] Endpoint های موفق: {len(successful)}")
    if successful:
        print("\n✅ Endpoint های موفق:")
        for endpoint, data, status in successful:
            print(f"   - {endpoint} (Status: {status})")
            print(f"     Data: {str(data)[:100]}")
    
    print(f"\n[INTERESTING] Endpoint های جالب (401/403): {len(interesting)}")
    if interesting:
        print("\n⚠️  Endpoint هایی که authentication نیاز دارند:")
        for endpoint, data, status in interesting:
            print(f"   - {endpoint} (Status: {status})")
            print(f"     Message: {data}")
    
    if not successful and not interesting:
        print("\n❌ هیچ endpoint موفقی پیدا نشد!")
        print("\n💡 پیشنهاد:")
        print("   1. مستندات API را از docs.nerkh.io بررسی کنید")
        print("   2. فرمت Authorization header را بررسی کنید")
        print("   3. ممکن است نیاز به استفاده از query parameters باشد")


if __name__ == "__main__":
    main()


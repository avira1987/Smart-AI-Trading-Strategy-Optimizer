"""
تست ارسال پیامک OTP با استفاده از متد Lookup کاوه نگار
این تست پیامک ورود را به شماره مشخص شده ارسال می‌کند
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.sms_service import send_otp_sms, get_kavenegar_api_key, get_kavenegar_template_name
import secrets


def test_send_otp_sms():
    """
    تست ارسال پیامک OTP به شماره 09112732986
    """
    # شماره تلفن تست
    phone_number = '09112732986'
    
    # تولید کد OTP تصادفی 4 رقمی
    otp_code = ''.join([str(secrets.randbelow(10)) for _ in range(4)])
    
    print("=" * 80)
    print("🧪 تست ارسال پیامک OTP")
    print("=" * 80)
    print(f"📱 شماره گیرنده: {phone_number}")
    print(f"🔐 کد OTP: {otp_code}")
    
    # بررسی تنظیمات
    api_key = get_kavenegar_api_key()
    template_name = get_kavenegar_template_name()
    
    print(f"🔑 API Key تنظیم شده: {'✅ بله' if api_key else '❌ خیر'}")
    print(f"📋 نام تمپلیت: {template_name}")
    print("-" * 80)
    
    if not api_key:
        print("⚠️  هشدار: API Key تنظیم نشده است!")
        print("لطفا در فایل .env یا تنظیمات API، KAVENEGAR_API_KEY را تنظیم کنید.")
        return False
    
    # ارسال پیامک
    print("📤 در حال ارسال پیامک...")
    try:
        result = send_otp_sms(phone_number, otp_code, template_name)
        
        print("-" * 80)
        if result['success']:
            print("✅ پیامک با موفقیت ارسال شد!")
            print(f"📨 پیام: {result.get('message', 'N/A')}")
            if 'response' in result:
                print(f"📊 پاسخ API: {result['response']}")
            return True
        else:
            print("❌ ارسال پیامک ناموفق بود!")
            print(f"📨 پیام خطا: {result.get('message', 'خطای نامشخص')}")
            if 'error_type' in result:
                print(f"🔍 نوع خطا: {result['error_type']}")
            return False
            
    except Exception as e:
        print("-" * 80)
        print(f"❌ خطا در ارسال پیامک: {str(e)}")
        import traceback
        print("جزئیات خطا:")
        print(traceback.format_exc())
        return False
    
    finally:
        print("=" * 80)


if __name__ == '__main__':
    print("\n")
    success = test_send_otp_sms()
    print("\n")
    
    if success:
        print("✅ تست با موفقیت انجام شد!")
        sys.exit(0)
    else:
        print("❌ تست ناموفق بود!")
        sys.exit(1)


"""
اسکریپت تست ارسال پیامک با Kavenegar
"""
import os
import sys
import django

# خواندن فایل .env و تنظیم environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # حذف کوتیشن‌ها اگر وجود داشته باشند
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                # تنظیم environment variable (حتی اگر خالی باشد)
                if key not in os.environ:
                    os.environ[key] = value

# تنظیم مسیر Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.sms_service import send_otp_sms, get_kavenegar_api_key, get_kavenegar_sender, SMS_ENABLED
import json

def test_sms_configuration():
    """بررسی تنظیمات SMS"""
    print("=" * 60)
    print("بررسی تنظیمات Kavenegar SMS")
    print("=" * 60)
    
    # بررسی نصب ماژول
    print(f"\n✓ ماژول Kavenegar: {'نصب شده' if SMS_ENABLED else '❌ نصب نشده'}")
    
    # بررسی API Key
    api_key = get_kavenegar_api_key()
    if api_key:
        print(f"✓ API Key: تنظیم شده (طول: {len(api_key)} کاراکتر)")
        # نمایش 4 کاراکتر اول و آخر برای اطمینان
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        print(f"  (نمایش جزئی: {masked_key})")
    else:
        print("❌ API Key: تنظیم نشده")
        return False
    
    # بررسی Sender
    sender = get_kavenegar_sender()
    if sender:
        print(f"✓ شماره فرستنده: {sender}")
    else:
        print("⚠ شماره فرستنده: تنظیم نشده (استفاده از پیش‌فرض)")
    
    return True

def test_send_sms(phone_number: str):
    """تست ارسال پیامک"""
    print("\n" + "=" * 60)
    print("تست ارسال پیامک")
    print("=" * 60)
    
    if not phone_number:
        print("❌ شماره موبایل وارد نشده است")
        return False
    
    # بررسی فرمت شماره
    if not phone_number.startswith('09') or len(phone_number) != 11:
        print(f"❌ شماره موبایل نامعتبر: {phone_number}")
        print("   فرمت صحیح: 09123456789")
        return False
    
    print(f"\n📱 شماره موبایل: {phone_number}")
    print("📤 در حال ارسال پیامک...")
    
    # ارسال پیامک تستی
    test_otp = "123456"
    result = send_otp_sms(phone_number, test_otp)
    
    print("\n" + "-" * 60)
    print("نتیجه ارسال:")
    print("-" * 60)
    
    if result.get('success'):
        print("✅ پیامک با موفقیت ارسال شد!")
        print(f"   پیام: {result.get('message', '')}")
        print(f"   کد تست: {test_otp}")
        if 'response' in result:
            print(f"   پاسخ API: {json.dumps(result['response'], indent=2, ensure_ascii=False)}")
        return True
    else:
        print("❌ خطا در ارسال پیامک")
        print(f"   پیام خطا: {result.get('message', 'خطای نامشخص')}")
        if 'error_type' in result:
            print(f"   نوع خطا: {result.get('error_type')}")
        return False

def main():
    """تابع اصلی"""
    print("\n" + "=" * 60)
    print("تست سیستم ارسال پیامک Kavenegar")
    print("=" * 60)
    
    # بررسی تنظیمات
    if not test_sms_configuration():
        print("\n❌ تنظیمات کامل نیست. لطفا API Key را در فایل .env تنظیم کنید.")
        return
    
    # دریافت شماره موبایل از argument یا input
    phone_number = None
    if len(sys.argv) > 1:
        phone_number = sys.argv[1].strip()
    else:
        print("\n" + "-" * 60)
        phone_number = input("لطفا شماره موبایل خود را وارد کنید (مثلاً 09123456789): ").strip()
    
    if not phone_number:
        print("❌ شماره موبایل وارد نشده است")
        print("   استفاده: python test_sms.py <شماره_موبایل>")
        return
    
    # تست ارسال
    success = test_send_sms(phone_number)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ تست با موفقیت انجام شد!")
    else:
        print("❌ تست ناموفق بود. لطفا تنظیمات را بررسی کنید.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ تست توسط کاربر متوقف شد")
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()


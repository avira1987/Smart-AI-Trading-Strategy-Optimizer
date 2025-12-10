"""
Test script to check user login issue for phone number 09129742504
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, OTPCode, Wallet, Device
from decimal import Decimal

phone_number = '09129742504'

print("=" * 80)
print("🔍 بررسی وضعیت کاربر و OTP")
print("=" * 80)
print(f"📱 شماره موبایل: {phone_number}")
print()

# Check if user exists
try:
    user = User.objects.get(username=phone_number)
    print(f"✅ کاربر با username={phone_number} پیدا شد")
    print(f"   ID: {user.id}")
    print(f"   Email: {user.email}")
    print(f"   Date Joined: {user.date_joined}")
except User.DoesNotExist:
    print(f"❌ کاربر با username={phone_number} پیدا نشد")
    
    # Check if user exists with different username but same phone
    try:
        profile = UserProfile.objects.get(phone_number=phone_number)
        user = profile.user
        print(f"⚠️  کاربر با phone_number={phone_number} پیدا شد اما username متفاوت است")
        print(f"   User ID: {user.id}")
        print(f"   Username: {user.username}")
        print(f"   Phone in profile: {profile.phone_number}")
    except UserProfile.DoesNotExist:
        print(f"❌ هیچ کاربری با phone_number={phone_number} پیدا نشد")
        user = None

print()

# Check OTP codes
print("🔐 بررسی کدهای OTP:")
otp_codes = OTPCode.objects.filter(phone_number=phone_number).order_by('-created_at')[:5]
if otp_codes:
    print(f"   تعداد OTP های موجود: {otp_codes.count()}")
    for otp in otp_codes:
        status = "✅ Valid" if otp.is_valid() else "❌ Invalid/Used"
        print(f"   - Code: {otp.code}, Created: {otp.created_at}, Status: {status}, Attempts: {otp.attempts}")
else:
    print("   ❌ هیچ کد OTP یافت نشد")

print()

# Check wallet
if user:
    try:
        wallet = Wallet.objects.get(user=user)
        print(f"💰 کیف پول:")
        print(f"   موجودی: {wallet.balance:,.0f} تومان")
    except Wallet.DoesNotExist:
        print("   ❌ کیف پول یافت نشد")

print()

# Check devices
if user:
    devices = Device.objects.filter(user=user)
    if devices:
        print(f"📱 دستگاه‌ها ({devices.count()}):")
        for device in devices:
            print(f"   - {device.device_name} (Active: {device.is_active}, Last Login: {device.last_login})")
    else:
        print("   ❌ هیچ دستگاهی ثبت نشده است")

print()
print("=" * 80)

# Test creating OTP
print("\n🧪 تست ایجاد OTP جدید:")
try:
    otp = OTPCode.create_otp(phone_number)
    print(f"✅ OTP ایجاد شد: {otp.code}")
    print(f"   Expires at: {otp.expires_at}")
    print(f"   Is valid: {otp.is_valid()}")
except Exception as e:
    print(f"❌ خطا در ایجاد OTP: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)


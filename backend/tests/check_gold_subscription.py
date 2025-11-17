"""
بررسی سریع جدول GoldPriceSubscription
"""

import os
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.models import GoldPriceSubscription, User

print("=" * 70)
print("[CHECK] بررسی جدول GoldPriceSubscription")
print("=" * 70)

# تعداد رکوردها
count = GoldPriceSubscription.objects.count()
print(f"\n[INFO] تعداد اشتراک‌ها: {count}")

if count > 0:
    print("\n[SUBSCRIPTIONS] لیست اشتراک‌ها:")
    for sub in GoldPriceSubscription.objects.all():
        print(f"   - User: {sub.user.username} (ID: {sub.user.id})")
        print(f"     Active: {sub.is_active}")
        print(f"     Valid: {sub.is_valid()}")
        print(f"     Start: {sub.start_date}")
        print(f"     End: {sub.end_date}")
        print(f"     Price: {sub.monthly_price:,} تومان")
else:
    print("\n[INFO] هیچ اشتراکی در دیتابیس نیست")
    print("[TIP] برای ایجاد اشتراک:")
    print("   1. از پنل ادمین: /admin/core/goldpricesubscription/")
    print("   2. از API: POST /api/gold-price-subscription/")
    print("   3. از shell: python test_gold_subscription.py")

# بررسی کاربران
users_count = User.objects.count()
print(f"\n[INFO] تعداد کاربران: {users_count}")

if users_count > 0:
    print("\n[USERS] کاربران موجود:")
    for user in User.objects.all()[:5]:  # فقط 5 کاربر اول
        has_sub = GoldPriceSubscription.objects.filter(user=user).exists()
        print(f"   - {user.username} (ID: {user.id}) - Subscription: {'Yes' if has_sub else 'No'}")

print("\n" + "=" * 70)
print("[DONE] بررسی تمام شد")
print("=" * 70)


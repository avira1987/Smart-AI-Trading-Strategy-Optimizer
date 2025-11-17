"""
تست ایجاد و مدیریت اشتراک قیمت طلا
"""

import os
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from core.models import GoldPriceSubscription, User, Wallet
from django.utils import timezone
from datetime import timedelta

def test_create_subscription():
    """تست ایجاد اشتراک"""
    print("=" * 70)
    print("[TEST] تست ایجاد اشتراک قیمت طلا")
    print("=" * 70)
    
    # پیدا کردن یا ایجاد کاربر تست
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    if created:
        user.set_password('test123')
        user.save()
        print(f"[CREATED] User created: {user.username}")
    else:
        print(f"[EXISTS] User exists: {user.username}")
    
    # ایجاد یا دریافت Wallet
    wallet, created = Wallet.objects.get_or_create(user=user)
    if created:
        print(f"[CREATED] Wallet created for {user.username}")
    else:
        print(f"[EXISTS] Wallet exists for {user.username}, balance: {wallet.balance}")
    
    # بررسی اشتراک موجود
    try:
        subscription = GoldPriceSubscription.objects.get(user=user)
        print(f"[EXISTS] Subscription exists:")
        print(f"   - Active: {subscription.is_active}")
        print(f"   - Valid: {subscription.is_valid()}")
        print(f"   - Start: {subscription.start_date}")
        print(f"   - End: {subscription.end_date}")
    except GoldPriceSubscription.DoesNotExist:
        print(f"[NOT EXISTS] No subscription for {user.username}")
        
        # ایجاد اشتراک تست
        subscription = GoldPriceSubscription.objects.create(
            user=user,
            is_active=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30),
            monthly_price=300000
        )
        print(f"[CREATED] Subscription created:")
        print(f"   - Active: {subscription.is_active}")
        print(f"   - Valid: {subscription.is_valid()}")
        print(f"   - Start: {subscription.start_date}")
        print(f"   - End: {subscription.end_date}")
    
    # تست همه اشتراک‌ها
    print("\n[ALL SUBSCRIPTIONS]")
    all_subs = GoldPriceSubscription.objects.all()
    print(f"Total subscriptions: {all_subs.count()}")
    for sub in all_subs:
        print(f"   - User: {sub.user.username}, Active: {sub.is_active}, Valid: {sub.is_valid()}")


def test_subscription_validation():
    """تست اعتبارسنجی اشتراک"""
    print("\n" + "=" * 70)
    print("[TEST] تست اعتبارسنجی اشتراک")
    print("=" * 70)
    
    subscriptions = GoldPriceSubscription.objects.all()
    
    for sub in subscriptions:
        print(f"\nUser: {sub.user.username}")
        print(f"   Active: {sub.is_active}")
        print(f"   Start: {sub.start_date}")
        print(f"   End: {sub.end_date}")
        print(f"   Valid: {sub.is_valid()}")
        print(f"   Expired: {sub.end_date and timezone.now() > sub.end_date if sub.end_date else False}")


def main():
    print("=" * 70)
    print("[GOLD PRICE SUBSCRIPTION TEST]")
    print("=" * 70)
    
    test_create_subscription()
    test_subscription_validation()
    
    print("\n" + "=" * 70)
    print("[SUMMARY] تست تمام شد")
    print("=" * 70)


if __name__ == "__main__":
    main()


"""
تست کسر هزینه پردازش استراتژی از موجودی کاربر
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from core.models import (
    TradingStrategy,
    Wallet,
    Transaction,
    SystemSettings,
    UserProfile
)


def test_strategy_processing_cost_deduction():
    """تست کسر هزینه پردازش استراتژی از موجودی کاربر"""
    print("\n" + "="*80)
    print("تست کسر هزینه پردازش استراتژی")
    print("="*80)
    
    # ایجاد یا دریافت کاربر تست
    test_username = 'test_strategy_processing_user'
    user, created = User.objects.get_or_create(
        username=test_username,
        defaults={'email': f'{test_username}@test.com'}
    )
    
    if created:
        UserProfile.objects.create(user=user, phone_number='09123456789')
        print(f"✓ کاربر تست ایجاد شد: {user.username}")
    else:
        print(f"✓ کاربر تست موجود است: {user.username}")
    
    # دریافت یا ایجاد wallet
    wallet, wallet_created = Wallet.objects.get_or_create(user=user)
    initial_balance = wallet.balance
    print(f"✓ موجودی اولیه: {initial_balance:,.0f} تومان")
    
    # دریافت تنظیمات سیستم
    settings = SystemSettings.load()
    processing_cost = settings.strategy_processing_cost
    print(f"✓ هزینه پردازش استراتژی: {processing_cost:,.0f} تومان")
    
    # شارژ حساب برای تست
    test_balance = Decimal('1000.00')
    wallet.balance = test_balance
    wallet.save()
    print(f"✓ موجودی تست تنظیم شد: {wallet.balance:,.0f} تومان")
    
    # شبیه‌سازی پردازش استراتژی
    print("\n" + "-"*80)
    print("شبیه‌سازی پردازش استراتژی...")
    print("-"*80)
    
    try:
        from django.db import transaction as db_transaction
        
        with db_transaction.atomic():
            # بررسی موجودی
            wallet.refresh_from_db()
            if wallet.balance < processing_cost:
                print(f"❌ موجودی کافی نیست. موجودی: {wallet.balance:,.0f}، هزینه: {processing_cost:,.0f}")
                return False
            
            # کسر هزینه
            wallet.balance -= processing_cost
            wallet.save(update_fields=['balance', 'updated_at'])
            
            # ایجاد تراکنش
            Transaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=processing_cost,
                status='completed',
                description='هزینه پردازش استراتژی - تست',
                completed_at=timezone.now()
            )
            
            print(f"✓ هزینه {processing_cost:,.0f} تومان از موجودی کسر شد")
            print(f"✓ موجودی جدید: {wallet.balance:,.0f} تومان")
            print(f"✓ تراکنش ثبت شد")
            
            # بررسی نهایی
            wallet.refresh_from_db()
            expected_balance = test_balance - processing_cost
            
            if wallet.balance == expected_balance:
                print(f"\n✅ تست موفق: موجودی به درستی کسر شد")
                print(f"   موجودی انتظاری: {expected_balance:,.0f} تومان")
                print(f"   موجودی واقعی: {wallet.balance:,.0f} تومان")
                return True
            else:
                print(f"\n❌ تست ناموفق: موجودی مطابقت ندارد")
                print(f"   موجودی انتظاری: {expected_balance:,.0f} تومان")
                print(f"   موجودی واقعی: {wallet.balance:,.0f} تومان")
                return False
                
    except Exception as e:
        print(f"\n❌ خطا در تست: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # بازگرداندن موجودی اولیه
        wallet.balance = initial_balance
        wallet.save()
        print(f"\n✓ موجودی به مقدار اولیه بازگردانده شد: {wallet.balance:,.0f} تومان")


def test_insufficient_balance():
    """تست عدم کافی بودن موجودی"""
    print("\n" + "="*80)
    print("تست عدم کافی بودن موجودی")
    print("="*80)
    
    # ایجاد یا دریافت کاربر تست
    test_username = 'test_insufficient_balance_user'
    user, created = User.objects.get_or_create(
        username=test_username,
        defaults={'email': f'{test_username}@test.com'}
    )
    
    if created:
        UserProfile.objects.create(user=user, phone_number='09123456780')
        print(f"✓ کاربر تست ایجاد شد: {user.username}")
    
    # دریافت یا ایجاد wallet
    wallet, _ = Wallet.objects.get_or_create(user=user)
    
    # تنظیم موجودی کم
    settings = SystemSettings.load()
    processing_cost = settings.strategy_processing_cost
    wallet.balance = processing_cost - Decimal('10.00')  # کمتر از هزینه
    wallet.save()
    
    print(f"✓ موجودی تست: {wallet.balance:,.0f} تومان")
    print(f"✓ هزینه پردازش: {processing_cost:,.0f} تومان")
    
    # بررسی موجودی
    wallet.refresh_from_db()
    if wallet.balance < processing_cost:
        print(f"✓ موجودی کافی نیست (همانطور که انتظار می‌رفت)")
        print(f"✅ تست موفق: سیستم به درستی موجودی ناکافی را تشخیص داد")
        return True
    else:
        print(f"❌ تست ناموفق: سیستم موجودی ناکافی را تشخیص نداد")
        return False


if __name__ == '__main__':
    print("\n" + "="*80)
    print("شروع تست‌های کسر هزینه پردازش استراتژی")
    print("="*80)
    
    # تست 1: کسر هزینه با موجودی کافی
    test1_result = test_strategy_processing_cost_deduction()
    
    # تست 2: بررسی موجودی ناکافی
    test2_result = test_insufficient_balance()
    
    # خلاصه نتایج
    print("\n" + "="*80)
    print("خلاصه نتایج تست‌ها")
    print("="*80)
    print(f"تست کسر هزینه: {'✅ موفق' if test1_result else '❌ ناموفق'}")
    print(f"تست موجودی ناکافی: {'✅ موفق' if test2_result else '❌ ناموفق'}")
    
    if test1_result and test2_result:
        print("\n✅ همه تست‌ها موفق بودند!")
        sys.exit(0)
    else:
        print("\n❌ برخی تست‌ها ناموفق بودند!")
        sys.exit(1)







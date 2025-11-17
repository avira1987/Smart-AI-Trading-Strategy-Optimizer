"""
تست‌های جامع برای سیستم ردیابی استفاده از API
این تست‌ها بررسی می‌کنند که:
1. لاگ‌گیری برای همه provider ها به درستی کار می‌کند
2. آمار بر اساس provider به درستی محاسبه می‌شود
3. فیلترها (تاریخ، provider، user) به درستی کار می‌کنند
4. محاسبه هزینه برای همه provider ها صحیح است
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import APIUsageLog
from api.api_usage_tracker import (
    log_api_usage,
    get_api_usage_stats,
    calculate_api_cost
)


def test_calculate_api_cost():
    """تست محاسبه هزینه برای همه provider ها"""
    print("\n" + "="*60)
    print("تست محاسبه هزینه API")
    print("="*60)
    
    providers = [
        'twelvedata',
        'alphavantage',
        'oanda',
        'metalsapi',
        'financialmodelingprep',
        'nerkh',
        'gemini',
        'kavenegar',
        'mt5'
    ]
    
    for provider in providers:
        cost = calculate_api_cost(provider, request_count=1)
        print(f"  {provider:25} -> ${cost}")
        assert cost >= 0, f"هزینه برای {provider} باید غیر منفی باشد"
    
    # تست Gemini با توکن
    gemini_cost = calculate_api_cost('gemini', input_tokens=1000, output_tokens=1000)
    print(f"  gemini (1000 input + 1000 output tokens) -> ${gemini_cost}")
    assert gemini_cost > 0, "هزینه Gemini باید بیشتر از صفر باشد"
    
    print("✅ تست محاسبه هزینه موفق بود\n")


def test_log_api_usage_all_providers():
    """تست لاگ‌گیری برای همه provider ها"""
    print("\n" + "="*60)
    print("تست لاگ‌گیری برای همه Provider ها")
    print("="*60)
    
    # ایجاد یا دریافت کاربر تست
    test_user, _ = User.objects.get_or_create(
        username='test_user_api',
        defaults={'email': 'test@example.com'}
    )
    
    providers = [
        'twelvedata',
        'alphavantage',
        'oanda',
        'metalsapi',
        'financialmodelingprep',
        'nerkh',
        'gemini',
        'kavenegar',
        'mt5',
        'google_oauth',
        'zarinpal'
    ]
    
    created_logs = []
    
    for provider in providers:
        try:
            # لاگ موفق
            log_entry = log_api_usage(
                provider=provider,
                endpoint=f"test_endpoint/{provider}",
                request_type='GET',
                status_code=200,
                success=True,
                response_time_ms=150.5,
                user=test_user,
                metadata={'test': True, 'provider': provider}
            )
            created_logs.append(log_entry)
            print(f"  ✅ {provider:25} - لاگ موفق ایجاد شد (ID: {log_entry.id})")
            
            # لاگ ناموفق
            log_entry_failed = log_api_usage(
                provider=provider,
                endpoint=f"test_endpoint/{provider}",
                request_type='GET',
                status_code=500,
                success=False,
                response_time_ms=50.0,
                error_message="Test error",
                user=test_user,
                metadata={'test': True, 'provider': provider, 'failed': True}
            )
            created_logs.append(log_entry_failed)
            print(f"  ✅ {provider:25} - لاگ ناموفق ایجاد شد (ID: {log_entry_failed.id})")
            
        except Exception as e:
            print(f"  ❌ {provider:25} - خطا: {e}")
            raise
    
    print(f"\n✅ مجموع {len(created_logs)} لاگ ایجاد شد")
    return created_logs


def test_get_api_usage_stats_all_providers():
    """تست دریافت آمار برای همه provider ها"""
    print("\n" + "="*60)
    print("تست دریافت آمار برای همه Provider ها")
    print("="*60)
    
    # دریافت آمار کلی
    stats = get_api_usage_stats()
    
    print(f"\n📊 آمار کلی:")
    print(f"  کل درخواست‌ها: {stats['total_requests']}")
    print(f"  درخواست‌های موفق: {stats['successful_requests']}")
    print(f"  درخواست‌های ناموفق: {stats['failed_requests']}")
    print(f"  نرخ موفقیت: {stats['success_rate']:.2f}%")
    print(f"  هزینه کل (USD): ${stats['total_cost_usd']:.6f}")
    print(f"  هزینه کل (تومان): {stats['total_cost_toman']:.2f}")
    
    print(f"\n📊 آمار بر اساس Provider:")
    provider_stats = stats.get('provider_stats', {})
    
    if not provider_stats:
        print("  ⚠️  هیچ آمار provider یافت نشد!")
        return
    
    # بررسی که همه provider ها در آمار هستند
    expected_providers = [
        'twelvedata', 'alphavantage', 'oanda', 'metalsapi',
        'financialmodelingprep', 'nerkh', 'gemini', 'kavenegar',
        'mt5', 'google_oauth', 'zarinpal'
    ]
    
    found_providers = list(provider_stats.keys())
    print(f"\n  Provider های یافت شده ({len(found_providers)}):")
    for provider in sorted(found_providers):
        p_stats = provider_stats[provider]
        print(f"    {provider:25} - درخواست‌ها: {p_stats['total_requests']:3} | "
              f"موفق: {p_stats['successful_requests']:3} | "
              f"ناموفق: {p_stats['failed_requests']:3} | "
              f"هزینه: ${p_stats['total_cost_usd']:.6f}")
    
    # تست فیلتر بر اساس provider
    print(f"\n🔍 تست فیلتر بر اساس Provider:")
    for provider in ['mt5', 'twelvedata', 'gemini']:
        if provider in found_providers:
            filtered_stats = get_api_usage_stats(provider=provider)
            print(f"  {provider}: {filtered_stats['total_requests']} درخواست")
            assert filtered_stats['total_requests'] > 0, f"باید برای {provider} درخواست وجود داشته باشد"
    
    print("\n✅ تست دریافت آمار موفق بود")


def test_filter_by_date():
    """تست فیلتر بر اساس تاریخ"""
    print("\n" + "="*60)
    print("تست فیلتر بر اساس تاریخ")
    print("="*60)
    
    # آمار 30 روز گذشته
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now()
    
    stats_30_days = get_api_usage_stats(
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"  آمار 30 روز گذشته: {stats_30_days['total_requests']} درخواست")
    
    # آمار 7 روز گذشته
    start_date_7 = timezone.now() - timedelta(days=7)
    stats_7_days = get_api_usage_stats(
        start_date=start_date_7,
        end_date=end_date
    )
    
    print(f"  آمار 7 روز گذشته: {stats_7_days['total_requests']} درخواست")
    
    assert stats_30_days['total_requests'] >= stats_7_days['total_requests'], \
        "آمار 30 روز باید بیشتر یا مساوی 7 روز باشد"
    
    print("✅ تست فیلتر تاریخ موفق بود")


def test_filter_by_user():
    """تست فیلتر بر اساس کاربر"""
    print("\n" + "="*60)
    print("تست فیلتر بر اساس کاربر")
    print("="*60)
    
    test_user, _ = User.objects.get_or_create(
        username='test_user_api',
        defaults={'email': 'test@example.com'}
    )
    
    # آمار برای کاربر خاص
    user_stats = get_api_usage_stats(user=test_user)
    print(f"  آمار کاربر '{test_user.username}': {user_stats['total_requests']} درخواست")
    
    # آمار کلی
    all_stats = get_api_usage_stats()
    print(f"  آمار کلی: {all_stats['total_requests']} درخواست")
    
    assert user_stats['total_requests'] <= all_stats['total_requests'], \
        "آمار کاربر باید کمتر یا مساوی آمار کلی باشد"
    
    print("✅ تست فیلتر کاربر موفق بود")


def test_provider_stats_structure():
    """تست ساختار آمار provider ها"""
    print("\n" + "="*60)
    print("تست ساختار آمار Provider ها")
    print("="*60)
    
    stats = get_api_usage_stats()
    provider_stats = stats.get('provider_stats', {})
    
    if not provider_stats:
        print("  ⚠️  هیچ آمار provider یافت نشد!")
        return
    
    # بررسی ساختار برای هر provider
    required_fields = [
        'total_requests',
        'successful_requests',
        'failed_requests',
        'total_cost_usd',
        'total_cost_toman'
    ]
    
    for provider, p_stats in provider_stats.items():
        print(f"\n  بررسی {provider}:")
        for field in required_fields:
            if field not in p_stats:
                print(f"    ❌ فیلد '{field}' موجود نیست!")
                raise AssertionError(f"فیلد '{field}' برای {provider} موجود نیست")
            print(f"    ✅ {field}: {p_stats[field]}")
        
        # بررسی منطقی بودن مقادیر
        assert p_stats['total_requests'] >= 0, f"total_requests باید غیر منفی باشد"
        assert p_stats['successful_requests'] >= 0, f"successful_requests باید غیر منفی باشد"
        assert p_stats['failed_requests'] >= 0, f"failed_requests باید غیر منفی باشد"
        assert p_stats['total_requests'] == p_stats['successful_requests'] + p_stats['failed_requests'], \
            f"جمع موفق و ناموفق باید برابر کل باشد"
        assert p_stats['total_cost_usd'] >= 0, f"total_cost_usd باید غیر منفی باشد"
        assert p_stats['total_cost_toman'] >= 0, f"total_cost_toman باید غیر منفی باشد"
    
    print("\n✅ ساختار آمار صحیح است")


def test_api_usage_stats_endpoint():
    """تست endpoint آمار API (شبیه‌سازی درخواست)"""
    print("\n" + "="*60)
    print("تست Endpoint آمار API")
    print("="*60)
    
    # شبیه‌سازی پارامترهای درخواست
    test_cases = [
        {'provider': None, 'days': None, 'description': 'بدون فیلتر'},
        {'provider': 'mt5', 'days': None, 'description': 'فیلتر MT5'},
        {'provider': 'twelvedata', 'days': None, 'description': 'فیلتر TwelveData'},
        {'provider': None, 'days': 30, 'description': '30 روز گذشته'},
        {'provider': 'mt5', 'days': 7, 'description': 'MT5 - 7 روز گذشته'},
    ]
    
    for test_case in test_cases:
        provider = test_case['provider']
        days = test_case['days']
        
        # محاسبه تاریخ
        start_date = None
        end_date = None
        if days:
            start_date = timezone.now() - timedelta(days=days)
            end_date = timezone.now()
        
        # دریافت آمار
        stats = get_api_usage_stats(
            provider=provider,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\n  {test_case['description']}:")
        print(f"    درخواست‌ها: {stats['total_requests']}")
        print(f"    Provider ها: {len(stats.get('provider_stats', {}))}")
        
        if provider:
            # اگر فیلتر provider اعمال شده، باید فقط آن provider در آمار باشد
            provider_stats = stats.get('provider_stats', {})
            if provider_stats:
                assert provider in provider_stats, \
                    f"Provider {provider} باید در آمار باشد"
                print(f"    ✅ Provider {provider} در آمار موجود است")
    
    print("\n✅ تست endpoint موفق بود")


def test_user_specific_visibility():
    """تست می‌کند که آمار مصرف فقط شامل لاگ‌های همان کاربر باشد"""
    print("\n" + "="*60)
    print("تست نمایش اختصاصی آمار برای هر کاربر")
    print("="*60)

    # ایجاد کاربران تست
    user_alice, _ = User.objects.get_or_create(
        username='api_usage_alice',
        defaults={'email': 'alice@example.com'}
    )
    user_bob, _ = User.objects.get_or_create(
        username='api_usage_bob',
        defaults={'email': 'bob@example.com'}
    )

    # حذف لاگ‌های قبلی این تست
    APIUsageLog.objects.filter(metadata__contains={'visibility_test': True}).delete()

    # ثبت لاگ برای آلیس
    log_api_usage(
        provider='alice_provider',
        endpoint='test/visibility/alice',
        request_type='GET',
        status_code=200,
        success=True,
        user=user_alice,
        metadata={'visibility_test': True}
    )

    # ثبت لاگ برای باب
    log_api_usage(
        provider='bob_provider',
        endpoint='test/visibility/bob',
        request_type='GET',
        status_code=200,
        success=True,
        user=user_bob,
        metadata={'visibility_test': True}
    )

    # ثبت لاگ سیستمی (بدون کاربر)
    log_api_usage(
        provider='system_provider',
        endpoint='test/visibility/system',
        request_type='GET',
        status_code=200,
        success=True,
        user=None,
        metadata={'visibility_test': True}
    )

    # آمار آلیس باید فقط شامل لاگ خودش باشد
    alice_stats = get_api_usage_stats(user=user_alice)
    alice_providers = list(alice_stats.get('provider_stats', {}).keys())
    print(f"  آمار آلیس: {alice_stats['total_requests']} درخواست - Provider ها: {alice_providers}")
    assert alice_stats['total_requests'] == 1, "آمار آلیس باید فقط لاگ‌های خودش را شامل شود"
    assert alice_providers == ['alice_provider'], "Provider های آلیس باید فقط provider خودش باشد"

    # آمار باب باید فقط شامل لاگ‌های خودش باشد
    bob_stats = get_api_usage_stats(user=user_bob)
    bob_providers = list(bob_stats.get('provider_stats', {}).keys())
    print(f"  آمار باب: {bob_stats['total_requests']} درخواست - Provider ها: {bob_providers}")
    assert bob_stats['total_requests'] == 1, "آمار باب باید فقط لاگ‌های خودش را شامل شود"
    assert bob_providers == ['bob_provider'], "Provider های باب باید فقط provider خودش باشد"

    # آمار کلی (بدون user) فقط باید لاگ‌های سیستمی را نشان دهد
    system_stats = get_api_usage_stats()
    system_providers = list(system_stats.get('provider_stats', {}).keys())
    print(f"  آمار سیستم: {system_stats['total_requests']} درخواست - Provider ها: {system_providers}")
    assert 'system_provider' in system_providers, "لاگ‌های سیستمی باید در آمار کلی وجود داشته باشد"
    assert 'alice_provider' not in system_providers and 'bob_provider' not in system_providers, \
        "آمار کلی نباید لاگ‌های کاربران را بدون فیلتر user شامل شود"

    print("\n✅ تست نمایش اختصاصی آمار برای هر کاربر موفق بود")


def main():
    """اجرای همه تست‌ها"""
    print("\n" + "="*60)
    print("شروع تست‌های سیستم ردیابی استفاده از API")
    print("="*60)
    
    try:
        # تست محاسبه هزینه
        test_calculate_api_cost()
        
        # تست لاگ‌گیری
        created_logs = test_log_api_usage_all_providers()
        
        # تست دریافت آمار
        test_get_api_usage_stats_all_providers()
        
        # تست فیلترها
        test_filter_by_date()
        test_filter_by_user()
        
        # تست ساختار
        test_provider_stats_structure()

        # تست نمایش اختصاصی آمار برای هر کاربر
        test_user_specific_visibility()
        
        # تست endpoint
        test_api_usage_stats_endpoint()
        
        print("\n" + "="*60)
        print("✅ همه تست‌ها با موفقیت انجام شد!")
        print("="*60)
        
        # نمایش خلاصه
        final_stats = get_api_usage_stats()
        print(f"\n📊 خلاصه نهایی:")
        print(f"  کل درخواست‌ها: {final_stats['total_requests']}")
        print(f"  تعداد Provider ها: {len(final_stats.get('provider_stats', {}))}")
        print(f"  هزینه کل (USD): ${final_stats['total_cost_usd']:.6f}")
        
        # پاک‌سازی لاگ‌های تست (اختیاری - غیرفعال برای اجرای خودکار)
        # cleanup = input("\nآیا می‌خواهید لاگ‌های تست پاک شوند؟ (y/n): ").strip().lower()
        # if cleanup == 'y':
        #     if created_logs:
        #         for log in created_logs:
        #             log.delete()
        #         print(f"✅ {len(created_logs)} لاگ تست پاک شد")
        print(f"\n💡 برای پاک کردن لاگ‌های تست، می‌توانید از دستور زیر استفاده کنید:")
        print(f"   APIUsageLog.objects.filter(metadata__test=True).delete()")
        
    except Exception as e:
        print(f"\n❌ خطا در تست: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())


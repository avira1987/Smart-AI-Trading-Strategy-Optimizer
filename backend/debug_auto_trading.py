"""
اسکریپت دیباگ برای بررسی وضعیت ترید خودکار
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import AutoTradingSettings, UserProfile, TradingStrategy, LiveTrade
from api.mt5_client import is_market_open
from api.auto_trader import check_strategy_signals
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("بررسی وضعیت ترید خودکار")
print("=" * 60)

# 1. بررسی تنظیمات فعال
print("\n1. بررسی تنظیمات فعال:")
settings = AutoTradingSettings.objects.filter(is_enabled=True).select_related('strategy', 'user', 'deployed_result')
print(f"   تعداد تنظیمات فعال: {settings.count()}")

if settings.count() == 0:
    print("\n   ⚠️ هیچ تنظیمات فعالی یافت نشد!")
    print("   بررسی تنظیمات غیرفعال:")
    all_settings = AutoTradingSettings.objects.all().select_related('strategy', 'user', 'deployed_result')
    print(f"   تعداد کل تنظیمات: {all_settings.count()}")
    for s in all_settings:
        print(f"   - ID: {s.id}, Strategy: {s.strategy.name}, Enabled: {s.is_enabled}")

for s in settings:
    print(f"\n   تنظیمات ID: {s.id}")
    print(f"   - استراتژی: {s.strategy.name} (ID: {s.strategy.id})")
    print(f"   - کاربر: {s.user.username if s.user else 'None'} (ID: {s.user.id if s.user else 'None'})")
    print(f"   - فعال: {s.is_enabled}")
    print(f"   - استراتژی فعال: {s.strategy.is_active}")
    print(f"   - وضعیت پردازش: {s.strategy.processing_status}")
    print(f"   - deployed_result: {s.deployed_result.id if s.deployed_result else 'None (⚠️ مشکل!)'}")
    print(f"   - نماد: {s.symbol}")
    print(f"   - تایم‌فریم: {s.timeframe}")
    print(f"   - حداکثر معاملات باز: {s.max_open_trades}")
    print(f"   - فاصله بررسی (دقیقه): {s.check_interval_minutes}")
    
    # بررسی مجوز
    user = s.user or s.strategy.user
    try:
        profile = UserProfile.objects.get(user=user)
        can_use = profile.can_use_auto_trading
        print(f"   - can_use_auto_trading: {can_use} {'✅' if can_use else '❌ (⚠️ مشکل!)'}")
    except UserProfile.DoesNotExist:
        print(f"   - can_use_auto_trading: ❌ (⚠️ پروفایل کاربر یافت نشد!)")
    
    # بررسی زمان آخرین چک
    if s.last_check_time:
        time_diff = timezone.now() - s.last_check_time
        minutes_ago = time_diff.total_seconds() / 60
        print(f"   - آخرین بررسی: {s.last_check_time} ({minutes_ago:.1f} دقیقه پیش)")
        if minutes_ago > s.check_interval_minutes:
            print(f"   - ⚠️ زمان بررسی گذشته است! باید {s.check_interval_minutes} دقیقه بین بررسی‌ها باشد")
    else:
        print(f"   - آخرین بررسی: هرگز (اولین بار)")
    
    # بررسی معاملات باز
    open_trades = LiveTrade.objects.filter(
        user=user,
        strategy=s.strategy,
        status='open',
        symbol=s.symbol
    )
    print(f"   - معاملات باز: {open_trades.count()}/{s.max_open_trades}")
    
    # بررسی بازار
    try:
        market_open, market_msg = is_market_open()
        print(f"   - بازار باز: {market_open} {'✅' if market_open else '❌'} ({market_msg})")
    except Exception as e:
        print(f"   - بازار: ❌ خطا در بررسی - {str(e)}")
    
    # تست سیگنال
    if s.deployed_result and s.strategy.parsed_strategy_data:
        try:
            symbol = s.symbol or 'XAUUSD'
            timeframe = s.timeframe or 'M15'
            print(f"   - تست سیگنال برای {symbol} در {timeframe}...")
            signal = check_strategy_signals(s.strategy, symbol, timeframe=timeframe)
            print(f"   - سیگنال فعلی: {signal['signal']} (اعتماد: {signal['confidence']:.2f})")
            print(f"   - دلیل: {signal['reason']}")
            if signal['signal'] == 'hold':
                print(f"   - ⚠️ سیگنال hold است - معامله‌ای باز نمی‌شود")
        except Exception as e:
            print(f"   - ❌ خطا در تست سیگنال: {str(e)}")
    else:
        if not s.deployed_result:
            print(f"   - ❌ deployed_result تنظیم نشده است!")
        if not s.strategy.parsed_strategy_data:
            print(f"   - ❌ استراتژی پردازش نشده است!")

# 2. بررسی Celery
print("\n" + "=" * 60)
print("2. بررسی Celery:")
print("   (لطفاً دستی بررسی کنید که Celery Worker و Beat در حال اجرا هستند)")

# 3. بررسی MT5
print("\n" + "=" * 60)
print("3. بررسی MT5:")
try:
    from api.mt5_client import mt5
    if mt5.initialize():
        print("   ✅ MT5 متصل است")
        account_info = mt5.account_info()
        if account_info:
            print(f"   - حساب: {account_info.login}")
            print(f"   - سرور: {account_info.server}")
            print(f"   - موجودی: {account_info.balance}")
    else:
        print("   ❌ MT5 متصل نیست!")
        print(f"   - خطا: {mt5.last_error()}")
except Exception as e:
    print(f"   ❌ خطا در بررسی MT5: {str(e)}")

# 4. بررسی لاگ‌های اخیر
print("\n" + "=" * 60)
print("4. بررسی معاملات اخیر:")
recent_trades = LiveTrade.objects.filter(
    opened_at__gte=timezone.now() - timedelta(days=1)
).order_by('-opened_at')[:10]
print(f"   تعداد معاملات در 24 ساعت گذشته: {recent_trades.count()}")
for trade in recent_trades:
    print(f"   - {trade.symbol} {trade.trade_type} | Ticket: {trade.mt5_ticket} | Status: {trade.status} | Opened: {trade.opened_at}")

print("\n" + "=" * 60)
print("پایان بررسی")
print("=" * 60)


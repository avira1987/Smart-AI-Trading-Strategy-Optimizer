"""
سیستم معاملات دمو برای کاربرانی که MT5 ندارند
استفاده از Twelve Data برای قیمت‌های لحظه‌ای
"""

import logging
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import DemoAccount, DemoTrade, TradingStrategy, LiveTrade
from api.gold_price_providers import GoldPriceManager

User = get_user_model()
logger = logging.getLogger(__name__)


def get_or_create_demo_account(user) -> DemoAccount:
    """دریافت یا ایجاد حساب دمو برای کاربر"""
    account, created = DemoAccount.objects.get_or_create(
        user=user,
        defaults={
            'balance': 10000.0,
            'equity': 10000.0,
            'free_margin': 10000.0,
        }
    )
    return account


def calculate_margin_required(volume: float, price: float, leverage: int = 100) -> Decimal:
    """محاسبه مارجین مورد نیاز"""
    # برای طلا: مارجین = (حجم * قیمت * 100) / اهرم
    # حجم به لات است، پس باید به اونس تبدیل کنیم
    margin = (Decimal(str(volume)) * Decimal(str(price)) * Decimal('100')) / Decimal(str(leverage))
    return margin


def open_demo_trade(
    user,
    trade_type: str,
    symbol: str,
    volume: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    strategy: Optional[TradingStrategy] = None
) -> Tuple[Optional[DemoTrade], Optional[str]]:
    """
    باز کردن معامله دمو
    
    Returns:
        (trade, error) - trade در صورت موفقیت، None در صورت خطا
    """
    try:
        # دریافت یا ایجاد حساب دمو
        account = get_or_create_demo_account(user)
        
        if not account.is_active:
            return None, "حساب دمو غیرفعال است"
        
        # دریافت قیمت لحظه‌ای
        price_manager = GoldPriceManager()
        # اولویت: Financial Modeling Prep > Twelve Data > MT5
        price_result = price_manager.get_price(prefer_fmp=True, prefer_twelvedata=True)
        
        if not price_result['success']:
            return None, f"خطا در دریافت قیمت: {price_result.get('error', 'Unknown error')}"
        
        price_data = price_result['data']
        
        # تعیین قیمت باز شدن
        if trade_type.lower() == 'buy':
            open_price = price_data.get('ask', price_data.get('last', 0))
        elif trade_type.lower() == 'sell':
            open_price = price_data.get('bid', price_data.get('last', 0))
        else:
            return None, "نوع معامله باید 'buy' یا 'sell' باشد"
        
        if open_price == 0:
            return None, "قیمت معتبر نیست"
        
        # محاسبه مارجین
        margin_required = calculate_margin_required(volume, open_price, account.leverage)
        
        # بررسی موجودی کافی
        if account.free_margin < margin_required:
            return None, f"موجودی کافی نیست. مارجین مورد نیاز: ${margin_required:.2f}"
        
        # محاسبه کمیسیون (معمولاً برای هر لات $7)
        commission = volume * 7.0
        
        # ایجاد معامله
        trade = DemoTrade.objects.create(
            account=account,
            strategy=strategy,
            trade_type=trade_type.lower(),
            symbol=symbol,
            volume=volume,
            open_price=open_price,
            current_price=open_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            commission=commission,
            margin_used=margin_required,
        )
        
        # به‌روزرسانی حساب
        account.margin += margin_required
        account.free_margin -= margin_required
        account.save(update_fields=['margin', 'free_margin'])
        
        # ایجاد LiveTrade برای نمایش در سیستم
        live_trade = LiveTrade.objects.create(
            strategy=strategy,
            symbol=symbol,
            trade_type=trade_type.lower(),
            volume=volume,
            open_price=open_price,
            current_price=open_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            commission=commission,
            status='open',
            is_demo=True,
            demo_trade=trade,
        )
        
        logger.info(f"Demo trade opened: {trade.id} - {symbol} {trade_type} {volume} @ {open_price}")
        
        return trade, None
        
    except Exception as e:
        logger.exception(f"Error opening demo trade: {e}")
        return None, str(e)


def close_demo_trade(trade_id: int, user) -> Tuple[Optional[DemoTrade], Optional[str]]:
    """
    بستن معامله دمو
    
    Returns:
        (trade, error)
    """
    try:
        trade = DemoTrade.objects.get(id=trade_id, account__user=user)
        
        if trade.status != 'open':
            return None, "معامله قبلاً بسته شده است"
        
        # دریافت قیمت لحظه‌ای
        price_manager = GoldPriceManager()
        # اولویت: Financial Modeling Prep > Twelve Data > MT5
        price_result = price_manager.get_price(prefer_fmp=True, prefer_twelvedata=True)
        
        if not price_result['success']:
            return None, f"خطا در دریافت قیمت: {price_result.get('error')}"
        
        price_data = price_result['data']
        
        # تعیین قیمت بسته شدن
        if trade.trade_type == 'buy':
            close_price = price_data.get('bid', price_data.get('last', trade.open_price))
        else:  # sell
            close_price = price_data.get('ask', price_data.get('last', trade.open_price))
        
        # بستن معامله
        trade.close_trade(close_price, "بسته شده توسط کاربر")
        
        # به‌روزرسانی LiveTrade
        try:
            live_trade = LiveTrade.objects.get(demo_trade=trade)
            live_trade.status = 'closed'
            live_trade.close_price = close_price
            live_trade.closed_at = timezone.now()
            live_trade.close_reason = "بسته شده توسط کاربر"
            live_trade.profit = trade.profit
            live_trade.save()
        except LiveTrade.DoesNotExist:
            pass
        
        logger.info(f"Demo trade closed: {trade.id} @ {close_price}, Profit: {trade.profit}")
        
        return trade, None
        
    except DemoTrade.DoesNotExist:
        return None, "معامله پیدا نشد"
    except Exception as e:
        logger.exception(f"Error closing demo trade: {e}")
        return None, str(e)


def update_demo_trades_prices():
    """
    به‌روزرسانی قیمت‌های معاملات باز دمو
    این تابع باید به صورت دوره‌ای (مثلاً هر ثانیه) اجرا شود
    """
    try:
        # دریافت تمام معاملات باز
        open_trades = DemoTrade.objects.filter(status='open')
        
        if not open_trades.exists():
            return {'updated': 0, 'closed': 0, 'errors': 0}
        
        # دریافت قیمت لحظه‌ای
        price_manager = GoldPriceManager()
        # اولویت: Financial Modeling Prep > Twelve Data > MT5
        price_result = price_manager.get_price(prefer_fmp=True, prefer_twelvedata=True)
        
        if not price_result['success']:
            logger.warning(f"Failed to get price for demo trades update: {price_result.get('error')}")
            return {'updated': 0, 'closed': 0, 'errors': 1}
        
        price_data = price_result['data']
        current_price = price_data.get('last', 0)
        
        if current_price == 0:
            return {'updated': 0, 'closed': 0, 'errors': 1}
        
        updated = 0
        closed = 0
        
        for trade in open_trades:
            try:
                # تعیین قیمت فعلی بر اساس نوع معامله
                if trade.trade_type == 'buy':
                    # برای خرید از bid استفاده می‌کنیم (قیمت فروش)
                    trade_price = price_data.get('bid', current_price)
                else:  # sell
                    # برای فروش از ask استفاده می‌کنیم (قیمت خرید)
                    trade_price = price_data.get('ask', current_price)
                
                # به‌روزرسانی قیمت
                trade.update_current_price(trade_price)
                
                # بررسی stop loss و take profit
                if trade.check_stop_loss_take_profit():
                    closed += 1
                    # به‌روزرسانی LiveTrade
                    try:
                        live_trade = LiveTrade.objects.get(demo_trade=trade)
                        live_trade.status = 'closed'
                        live_trade.close_price = trade.close_price
                        live_trade.closed_at = trade.closed_at
                        live_trade.close_reason = trade.close_reason
                        live_trade.profit = trade.profit
                        live_trade.save()
                    except LiveTrade.DoesNotExist:
                        pass
                else:
                    updated += 1
                    # به‌روزرسانی LiveTrade
                    try:
                        live_trade = LiveTrade.objects.get(demo_trade=trade)
                        live_trade.current_price = trade_price
                        live_trade.profit = trade.profit
                        live_trade.save()
                    except LiveTrade.DoesNotExist:
                        pass
                
                # به‌روزرسانی equity حساب
                trade.account.update_equity()
                
            except Exception as e:
                logger.error(f"Error updating demo trade {trade.id}: {e}")
        
        return {
            'updated': updated,
            'closed': closed,
            'errors': 0
        }
        
    except Exception as e:
        logger.exception(f"Error in update_demo_trades_prices: {e}")
        return {'updated': 0, 'closed': 0, 'errors': 1}


def get_demo_account_info(user) -> Dict[str, Any]:
    """دریافت اطلاعات حساب دمو"""
    account = get_or_create_demo_account(user)
    
    # شمارش معاملات باز
    open_trades_count = DemoTrade.objects.filter(account=account, status='open').count()
    
    # به‌روزرسانی equity
    account.update_equity()
    
    return {
        'balance': float(account.balance),
        'equity': float(account.equity),
        'margin': float(account.margin),
        'free_margin': float(account.free_margin),
        'profit': float(account.profit),
        'leverage': account.leverage,
        'open_trades': open_trades_count,
        'is_active': account.is_active,
    }


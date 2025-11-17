"""
Automatic trading system that monitors strategies and executes trades
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from core.models import TradingStrategy, LiveTrade, AutoTradingSettings
from api.mt5_client import (
    fetch_mt5_candles, is_market_open, open_mt5_trade,
    get_mt5_positions, close_mt5_trade
)
from ai_module.backtest_engine import BacktestEngine
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


def check_strategy_signals(strategy: TradingStrategy, symbol: str) -> Dict[str, Any]:
    """
    Check if strategy generates buy/sell signals based on current market data.
    
    For live trading, we check the last few completed candles (not just the last one,
    which might still be forming) to find the most recent valid signal.
    
    Returns:
        {
            'signal': 'buy' | 'sell' | 'hold',
            'confidence': float,
            'reason': str
        }
    """
    try:
        # Get parsed strategy data
        if not strategy.parsed_strategy_data:
            logger.warning(f"Strategy {strategy.id} has no parsed data")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': 'استراتژی پردازش نشده است'
            }
        
        parsed_data = strategy.parsed_strategy_data
        
        # Fetch recent candles from MT5
        df, error = fetch_mt5_candles(symbol, timeframe='M15', count=500)
        if df.empty or error:
            logger.warning(f"Could not fetch data for {symbol}: {error}")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': f'خطا در دریافت داده: {error}'
            }
        
        logger.info(f"Fetched {len(df)} candles for {symbol}, last candle time: {df.index[-1]}")
        
        # Use backtest engine to generate signals
        engine = BacktestEngine()
        
        # Get all signals for the dataframe
        signals, reasons = engine._generate_signals(df, parsed_data)
        
        if signals.empty:
            logger.warning(f"No signals generated for strategy {strategy.id} on {symbol}")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': 'هیچ سیگنالی تولید نشد'
            }
        
        # For live trading, check the last few completed candles (not just the last one)
        # The last candle might still be forming, so we look at the last 3-5 completed candles
        # to find the most recent valid signal
        lookback_candles = min(5, len(signals))
        
        # Reverse iterate through the last few candles to find the most recent non-hold signal
        signal_map = {
            1: 'buy',
            -1: 'sell',
            0: 'hold'
        }
        
        # Check signals from most recent backwards
        for i in range(1, lookback_candles + 1):
            idx = -i
            signal_value = signals.iloc[idx]
            signal_index = signals.index[idx]
            
            signal_type = signal_map.get(signal_value, 'hold')
            
            # If we find a non-hold signal in the last few candles, use it
            if signal_type != 'hold':
                reason_dict = reasons.get(signal_index, {})
                logger.info(f"Found {signal_type} signal for strategy {strategy.id} at {signal_index} (candle {i} from end)")
                return {
                    'signal': signal_type,
                    'confidence': abs(float(signal_value)),
                    'reason': reason_dict.get('entry_reason_fa', reason_dict.get('entry_reason', 'سیگنال از استراتژی')),
                    'timestamp': signal_index.isoformat() if hasattr(signal_index, 'isoformat') else str(signal_index)
                }
        
        # If no non-hold signal found in recent candles, return hold
        # But still check the last signal for logging purposes
        last_signal = signals.iloc[-1]
        last_index = signals.index[-1]
        reason_dict = reasons.get(last_index, {})
        signal_type = signal_map.get(last_signal, 'hold')
        
        logger.debug(f"Strategy {strategy.id} on {symbol}: Last signal is {signal_type} at {last_index}")
        
        return {
            'signal': signal_type,
            'confidence': abs(float(last_signal)),
            'reason': reason_dict.get('entry_reason_fa', reason_dict.get('entry_reason', 'هیچ سیگنال فعالی در شمع‌های اخیر')),
            'timestamp': last_index.isoformat() if hasattr(last_index, 'isoformat') else str(last_index)
        }
        
    except Exception as e:
        logger.exception(f"Error checking signals for strategy {strategy.id}: {e}")
        return {
            'signal': 'hold',
            'confidence': 0.0,
            'reason': f'خطا: {str(e)}'
        }


def should_open_trade(strategy: TradingStrategy, settings: AutoTradingSettings, signal: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if a new trade should be opened based on current conditions.
    
    Returns:
        (should_open: bool, reason: str)
    """
    # Check if signal is valid
    if signal['signal'] == 'hold' or signal['confidence'] < 0.5:
        return False, 'سیگنال مناسب نیست'
    
    # Check market status
    market_open, market_msg = is_market_open()
    if not market_open:
        return False, f'بازار بسته است: {market_msg}'
    
    # Check max open trades limit
    open_trades = LiveTrade.objects.filter(
        strategy=strategy,
        status='open',
        symbol=settings.symbol
    ).count()
    
    if open_trades >= settings.max_open_trades:
        return False, f'حداکثر تعداد معاملات باز ({settings.max_open_trades}) رسیده است'
    
    # Check if there's already a similar open position
    existing_trade = LiveTrade.objects.filter(
        strategy=strategy,
        status='open',
        symbol=settings.symbol,
        trade_type=signal['signal']
    ).first()
    
    if existing_trade:
        return False, 'معامله مشابه در حال باز است'
    
    return True, 'شرایط مناسب است'


def calculate_stop_loss_take_profit(
    entry_price: float,
    trade_type: str,
    stop_loss_pips: float,
    take_profit_pips: float,
    symbol: str
) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate stop loss and take profit prices based on pips.
    
    Note: For XAUUSD, pip value is typically 0.01 per dollar move.
    For other symbols, pip calculation may vary.
    """
    # For XAUUSD (Gold), price moves in 0.01 increments (pip = 0.01)
    # For other forex pairs, pip is usually 0.0001 (except JPY pairs)
    
    if 'XAU' in symbol or 'GOLD' in symbol.upper():
        pip_value = 0.01
    elif 'JPY' in symbol:
        pip_value = 0.01
    else:
        pip_value = 0.0001
    
    if trade_type == 'buy':
        stop_loss = entry_price - (stop_loss_pips * pip_value)
        take_profit = entry_price + (take_profit_pips * pip_value)
    else:  # sell
        stop_loss = entry_price + (stop_loss_pips * pip_value)
        take_profit = entry_price - (take_profit_pips * pip_value)
    
    return stop_loss, take_profit


def execute_auto_trade(settings: AutoTradingSettings) -> Dict[str, Any]:
    """
    Main function to execute automatic trading for a strategy.
    Called periodically by Celery task.
    """
    try:
        strategy = settings.strategy
        
        # Check if auto trading is enabled
        if not settings.is_enabled:
            return {
                'status': 'skipped',
                'message': 'معامله خودکار غیرفعال است'
            }
        
        # Check if strategy is active
        if not strategy.is_active:
            return {
                'status': 'skipped',
                'message': 'استراتژی غیرفعال است'
            }
        
        # Check if strategy is processed
        if strategy.processing_status != 'processed':
            return {
                'status': 'skipped',
                'message': 'استراتژی پردازش نشده است'
            }
        
        # Check strategy signals
        signal_result = check_strategy_signals(strategy, settings.symbol)
        
        logger.info(f"Strategy {strategy.id} signal: {signal_result}")
        
        # Determine if we should open a trade
        should_open, reason = should_open_trade(strategy, settings, signal_result)
        
        if not should_open:
            return {
                'status': 'skipped',
                'message': reason,
                'signal': signal_result
            }
        
        # Open trade
        trade_type = signal_result['signal']
        
        # Auto-detect correct symbol based on account type
        from api.mt5_client import get_symbol_for_account
        symbol = settings.symbol
        if '_' not in symbol or (not symbol.endswith('_o') and not symbol.endswith('_l')):
            # Base symbol provided, auto-detect correct variant
            symbol = get_symbol_for_account(symbol)
            logger.info(f"Auto-detected symbol for auto-trading: {settings.symbol} -> {symbol}")
        
        # Calculate stop loss and take profit
        # We need current price first
        from api.mt5_client import get_mt5_account_info
        account_info, _ = get_mt5_account_info()
        if not account_info:
            # Try to get price from MT5
            df, _ = fetch_mt5_candles(symbol, 'M1', 1)
            if df.empty:
                return {
                    'status': 'error',
                    'message': 'نمی‌توان قیمت فعلی را دریافت کرد'
                }
            current_price = float(df['close'].iloc[-1])
        else:
            # Get price from tick
            df, _ = fetch_mt5_candles(symbol, 'M1', 1)
            if df.empty:
                return {
                    'status': 'error',
                    'message': 'نمی‌توان قیمت فعلی را دریافت کرد'
                }
            current_price = float(df['close'].iloc[-1])
        
        stop_loss = None
        take_profit = None
        
        if settings.use_stop_loss:
            stop_loss, _ = calculate_stop_loss_take_profit(
                current_price, trade_type, settings.stop_loss_pips, 0, settings.symbol
            )
        
        if settings.use_take_profit:
            _, take_profit = calculate_stop_loss_take_profit(
                current_price, trade_type, 0, settings.take_profit_pips, settings.symbol
            )

        # Safety clamp: ensure SL/TP are on the correct side of current price to satisfy MT5 validation
        # Determine pip value for symbol (match calculate_stop_loss_take_profit logic)
        if 'XAU' in settings.symbol or 'GOLD' in settings.symbol.upper():
            _pip = 0.01
        elif 'JPY' in settings.symbol:
            _pip = 0.01
        else:
            _pip = 0.0001

        if trade_type == 'buy':
            if stop_loss is not None and stop_loss >= current_price:
                stop_loss = current_price - _pip
            if take_profit is not None and take_profit <= current_price:
                take_profit = current_price + _pip
        else:
            if stop_loss is not None and stop_loss <= current_price:
                stop_loss = current_price + _pip
            if take_profit is not None and take_profit >= current_price:
                take_profit = current_price - _pip
        
        # Determine order volume: use risk-based sizing if configured and SL available
        order_volume = settings.volume
        try:
            if settings.use_stop_loss and settings.risk_per_trade_percent and settings.risk_per_trade_percent > 0:
                # Compute entry/SL prices based on current price and pips
                sl_price, _tp_dummy = calculate_stop_loss_take_profit(
                    current_price, trade_type, settings.stop_loss_pips, 0, settings.symbol
                )
                if sl_price is not None:
                    from api.mt5_client import compute_volume_for_risk
                    vol, vol_err = compute_volume_for_risk(symbol, current_price, sl_price, settings.risk_te_percent if False else settings.risk_per_trade_percent)
                    if vol_err is None and vol is not None:
                        order_volume = float(vol)
                        logger.info(f"Risk-based sizing: equity%={settings.risk_per_trade_percent} -> volume={order_volume}")
        except Exception as _e:
            logger.warning(f"Risk sizing failed, fallback to fixed volume: {settings.volume}: {_e}")

        # Open trade in MT5
        result, error = open_mt5_trade(
            symbol=symbol,  # Use auto-detected symbol
            trade_type=trade_type,
            volume=order_volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=f'AutoTrade: {strategy.name}'
        )
        
        if error:
            return {
                'status': 'error',
                'message': error,
                'signal': signal_result
            }
        
        # Save to database
        live_trade = LiveTrade.objects.create(
            strategy=strategy,
            mt5_ticket=result['ticket'],
            symbol=result['symbol'],
            trade_type=result['type'],
            volume=result['volume'],
            open_price=result['price_open'],
            current_price=result.get('price_current'),
            stop_loss=result.get('stop_loss'),
            take_profit=result.get('take_profit'),
            profit=result.get('profit', 0.0),
            swap=result.get('swap', 0.0),
            commission=result.get('commission', 0.0),
            status='open'
        )
        
        logger.info(f"Auto trade opened: {live_trade.mt5_ticket} - {symbol} {trade_type}")
        
        # Update last check time
        settings.last_check_time = django_timezone.now()
        settings.save(update_fields=['last_check_time'])
        
        return {
            'status': 'success',
            'message': 'معامله با موفقیت باز شد',
            'trade_id': live_trade.id,
            'ticket': live_trade.mt5_ticket,
            'signal': signal_result
        }
        
    except Exception as e:
        logger.exception(f"Error in execute_auto_trade for settings {settings.id}: {e}")
        return {
            'status': 'error',
            'message': f'خطا: {str(e)}'
        }


def manage_open_trades() -> Dict[str, Any]:
    """
    Manage existing open trades - update prices, check exit conditions.
    """
    try:
        open_trades = LiveTrade.objects.filter(status='open')
        
        updated_count = 0
        closed_count = 0
        
        # Sync with MT5 positions
        mt5_positions, error = get_mt5_positions()
        if error:
            return {
                'status': 'error',
                'message': f'خطا در دریافت موقعیت‌های MT5: {error}'
            }
        
        mt5_tickets = {p['ticket'] for p in mt5_positions}
        
        for trade in open_trades:
            # Update if position still exists in MT5
            mt5_position = next((p for p in mt5_positions if p['ticket'] == trade.mt5_ticket), None)
            
            if mt5_position:
                trade.current_price = mt5_position['price_current']
                trade.profit = mt5_position['profit']
                trade.swap = mt5_position['swap']
                trade.commission = mt5_position['commission']
                trade.save()
                updated_count += 1
            else:
                # Position closed in MT5 but not in DB
                trade.status = 'closed'
                trade.closed_at = django_timezone.now()
                trade.close_reason = 'موقعیت در MT5 بسته شد'
                trade.save()
                closed_count += 1
        
        # Mark trades as closed if they don't exist in MT5
        db_tickets = {t.mt5_ticket for t in open_trades}
        missing_tickets = db_tickets - mt5_tickets
        
        if missing_tickets:
            LiveTrade.objects.filter(
                mt5_ticket__in=missing_tickets,
                status='open'
            ).update(
                status='closed',
                closed_at=django_timezone.now(),
                close_reason='موقعیت در MT5 بسته شد'
            )
            closed_count += len(missing_tickets)
        
        return {
            'status': 'success',
            'updated': updated_count,
            'closed': closed_count,
            'total_open': open_trades.count() - closed_count
        }
        
    except Exception as e:
        logger.exception(f"Error in manage_open_trades: {e}")
        return {
            'status': 'error',
            'message': f'خطا: {str(e)}'
        }


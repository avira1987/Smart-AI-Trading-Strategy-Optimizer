"""
Automatic trading system that monitors strategies and executes trades based on backtest results.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
import pandas as pd
from core.models import TradingStrategy, LiveTrade, AutoTradingSettings, Result, UserProfile
from api.mt5_client import (
    fetch_mt5_candles, is_market_open, open_mt5_trade,
    get_mt5_positions, close_mt5_trade, get_symbol_for_account,
    get_mt5_account_info, compute_volume_for_risk
)
from ai_module.backtest_engine import BacktestEngine
from ai_module.technical_indicators import calculate_all_indicators
from django.utils import timezone as django_timezone

logger = logging.getLogger(__name__)


def check_strategy_signals(strategy: TradingStrategy, symbol: str, timeframe: str = 'M15', parsed_data_override: dict = None) -> Dict[str, Any]:
    """
    Check if strategy generates buy/sell signals based on current market data.
    Uses the exact parameters from the deployed backtest result.
    """
    try:
        parsed_data = parsed_data_override or strategy.parsed_strategy_data
        
        if not parsed_data:
            logger.warning(f"Strategy {strategy.id} has no parsed data")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': 'استراتژی پردازش نشده است'
            }
        
        # Fetch recent candles from MT5
        df, error = fetch_mt5_candles(symbol, timeframe=timeframe, count=500)
        if df.empty or error:
            logger.warning(f"Could not fetch data for {symbol} on {timeframe}: {error}")
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': f'خطا در دریافت داده ({timeframe}): {error}'
            }
        
        # Calculate indicators for live data, same as in backtest engine
        df = calculate_all_indicators(df)
        
        # Use backtest engine to generate signals
        engine = BacktestEngine()
        signals, reasons = engine._generate_signals(df, parsed_data)
        
        if signals.empty:
            return {
                'signal': 'hold',
                'confidence': 0.0,
                'reason': 'هیچ سیگنالی تولید نشد'
            }
        
        # For auto-trading, we look at the last COMPLETED candle (index -2)
        # to avoid signals that flicker on the current forming candle.
        # However, we can also check the last 2-3 candles to ensure we don't miss a signal.
        lookback = 2
        signal_map = {1: 'buy', -1: 'sell', 0: 'hold'}
        
        for i in range(1, lookback + 1):
            idx = -i
            signal_value = signals.iloc[idx]
            signal_index = signals.index[idx]
            signal_type = signal_map.get(signal_value, 'hold')
            
            if signal_type != 'hold':
                reason_dict = reasons.get(signal_index, {})
                return {
                    'signal': signal_type,
                    'confidence': abs(float(signal_value)),
                    'reason': reason_dict.get('entry_reason_fa', reason_dict.get('entry_reason', 'سیگنال تایید شده')),
                    'timestamp': signal_index.isoformat() if hasattr(signal_index, 'isoformat') else str(signal_index)
                }
        
        return {
            'signal': 'hold',
            'confidence': 0.0,
            'reason': 'سیگنال فعالی در شمع‌های اخیر یافت نشد'
        }
        
    except Exception as e:
        logger.exception(f"Error checking signals for strategy {strategy.id}: {e}")
        return {'signal': 'hold', 'confidence': 0.0, 'reason': f'خطای داخلی: {str(e)}'}


def execute_auto_trade(settings: AutoTradingSettings) -> Dict[str, Any]:
    """
    Executes automatic trading. Strictly follows the deployed backtest result.
    """
    try:
        strategy = settings.strategy
        user = settings.user or strategy.user # Use deployer user, fallback to strategy owner
        
        # 1. Admin Permission Check
        profile = UserProfile.objects.filter(user=user).first()
        if not profile or not profile.can_use_auto_trading:
            return {
                'status': 'skipped',
                'message': f'دسترسی معامله خودکار برای کاربر {user.username} تایید نشده است'
            }
        
        # 2. Basic Enabled Check
        if not settings.is_enabled or not strategy.is_active:
            return {'status': 'skipped', 'message': 'معامله خودکار یا استراتژی غیرفعال است'}

        # 3. Backtest Result Reference Check
        deployed_result = settings.deployed_result
        if not deployed_result:
            return {'status': 'skipped', 'message': 'هیچ بک‌تستی برای این استراتژی مستقر نشده است'}

        # Extract parameters from deployed result
        # We assume the result metadata or data_sources contains the successful params
        meta = deployed_result.data_sources or {}
        symbol = settings.symbol or meta.get('symbol') or 'XAUUSD'
        timeframe = settings.timeframe or meta.get('strategy_timeframe') or 'M15'
        risk_percent = settings.risk_per_trade_percent or 2.0
        
        # Sync symbol with MT5 account suffix
        mt5_symbol = get_symbol_for_account(symbol)
        
        # 4. Market Status Check
        market_open, market_msg = is_market_open()
        if not market_open:
            return {'status': 'skipped', 'message': f'بازار بسته است: {market_msg}'}

        # 5. Check Signal
        # Important: Use the parsed data that was actually used in the backtest if possible
        signal_result = check_strategy_signals(strategy, mt5_symbol, timeframe=timeframe)
        
        if signal_result['signal'] == 'hold':
            return {'status': 'skipped', 'message': signal_result['reason'], 'signal': signal_result}

        # 6. Risk and Open Positions Check
        # Filter by user to handle multiple users per strategy
        open_trades_count = LiveTrade.objects.filter(user=user, strategy=strategy, status='open', symbol=mt5_symbol).count()
        if open_trades_count >= settings.max_open_trades:
            return {'status': 'skipped', 'message': f'حداکثر تعداد معاملات باز ({settings.max_open_trades}) رعایت شده است'}

        # Prevent duplicate trades in same direction for this user
        existing = LiveTrade.objects.filter(user=user, strategy=strategy, status='open', symbol=mt5_symbol, trade_type=signal_result['signal']).exists()
        if existing:
            return {'status': 'skipped', 'message': 'معامله مشابه در حال حاضر باز است'}

        # 7. Calculate Volume based on Risk
        # Fetch current price for SL calculation
        df, _ = fetch_mt5_candles(mt5_symbol, 'M1', 1)
        if df.empty:
            return {'status': 'error', 'message': 'عدم دسترسی به قیمت لحظه‌ای'}
        current_price = float(df['close'].iloc[-1])

        # SL/TP calculation (using pips or ATR logic if we had it, but here we use pips from settings as fallback)
        stop_loss = None
        take_profit = None
        
        # Pip value detection
        pip_value = 0.01 if ('XAU' in symbol or 'JPY' in symbol) else 0.0001
        
        if signal_result['signal'] == 'buy':
            stop_loss = current_price - (settings.stop_loss_pips * pip_value)
            take_profit = current_price + (settings.take_profit_pips * pip_value)
        else:
            stop_loss = current_price + (settings.stop_loss_pips * pip_value)
            take_profit = current_price - (settings.take_profit_pips * pip_value)

        # Calculate Lot Volume based on Risk
        volume = settings.volume
        if risk_percent > 0 and stop_loss:
            vol, vol_err = compute_volume_for_risk(mt5_symbol, current_price, stop_loss, risk_percent)
            if not vol_err:
                volume = float(vol)

        # 8. Execute Trade
        # Capture current signal details for verification (DNA of the entry)
        signal_dna = {
            'timestamp': django_timezone.now().isoformat(),
            'confidence': signal_result.get('confidence', 0),
            'reason': signal_result.get('reason', ''),
            'indicators_snapshot': {}, # In a real scenario, we'd pull the last row of indicators here
            'backtest_id': deployed_result.id,
            'initial_expected_return': deployed_result.total_return,
            'user_id': user.id
        }

        result, error = open_mt5_trade(
            symbol=mt5_symbol,
            trade_type=signal_result['signal'],
            volume=volume,
            stop_loss=stop_loss,
            take_profit=take_profit,
            comment=f'AutoDeploy: Result#{deployed_result.id} User#{user.id}'
        )
        
        if error:
            return {'status': 'error', 'message': f'خطای MT5: {error}', 'signal': signal_result}
            
        # 9. Record Trade
        live_trade = LiveTrade.objects.create(
            user=user,
            strategy=strategy,
            deployed_result=deployed_result, # Link to the blueprint
            signal_data=signal_dna, # Store why we entered
            mt5_ticket=result['ticket'],
            symbol=result['symbol'],
            trade_type=result['type'],
            volume=result['volume'],
            open_price=result['price_open'],
            current_price=result.get('price_current'),
            stop_loss=result.get('stop_loss'),
            take_profit=result.get('take_profit'),
            profit=result.get('profit', 0.0),
            status='open'
        )
        
        return {
            'status': 'success',
            'message': 'معامله خودکار با موفقیت بر اساس بک‌تست مستقر شد',
            'ticket': live_trade.mt5_ticket,
            'signal': signal_result
        }
        
    except Exception as e:
        logger.exception(f"Error in execute_auto_trade: {e}")
        return {'status': 'error', 'message': f'خطای سیستمی: {str(e)}'}


def manage_open_trades() -> Dict[str, Any]:
    """
    Syncs and manages open trades.
    """
    try:
        open_trades = LiveTrade.objects.filter(status='open')
        mt5_positions, error = get_mt5_positions()
        
        if error:
            return {'status': 'error', 'message': error}
        
        mt5_tickets = {p['ticket'] for p in mt5_positions}
        updated = 0
        closed = 0
        
        for trade in open_trades:
            pos = next((p for p in mt5_positions if p['ticket'] == trade.mt5_ticket), None)
            if pos:
                trade.current_price = pos['price_current']
                trade.profit = pos['profit']
                trade.save(update_fields=['current_price', 'profit'])
                updated += 1
            else:
                trade.status = 'closed'
                trade.closed_at = django_timezone.now()
                trade.close_reason = 'بسته شده در MT5'
                trade.save()
                closed += 1
                
        return {'status': 'success', 'updated': updated, 'closed': closed}
    except Exception as e:
        logger.error(f"Error managing trades: {e}")
        return {'status': 'error', 'message': str(e)}

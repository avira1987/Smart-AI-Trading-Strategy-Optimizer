import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)


def fetch_mt5_m1_candles(symbol: str, count: int = 500) -> pd.DataFrame:
    """Fetch recent M1 candles from a locally installed MetaTrader 5 terminal.

    Requirements:
    - MT5 terminal installed on this machine and logged in
    - Python package MetaTrader5 installed
    """
    initialized = False
    try:
        if not mt5.initialize():
            return pd.DataFrame()
        initialized = True

        # Ensure the symbol is selected in Market Watch
        mt5.symbol_select(symbol, True)

        now = datetime.now()
        # Copy last N M1 rates
        rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M1, now, count)
        if rates is None or len(rates) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        if df.empty:
            return df
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        df = df.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'tick_volume': 'volume'})
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        df = df.sort_values('datetime')
        df.set_index('datetime', inplace=True)
        return df
    finally:
        if initialized:
            mt5.shutdown()


# --- Enhanced helper with timeframe and better diagnostics ---

TIMEFRAME_MAP = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'M30': mt5.TIMEFRAME_M30,
    'H1': mt5.TIMEFRAME_H1,
}


def _generate_symbol_variants(symbol: str) -> List[str]:
    base = symbol.strip()
    candidates = [base]
    # Common broker suffixes (omit '.i' to avoid confusion like XAUUSD_I.i)
    for suf in ['.', '.m']:
        candidates.append(base + suf)
    return list(dict.fromkeys(candidates))


def fetch_mt5_candles(symbol: str, timeframe: str = 'M1', count: int = 500) -> Tuple[pd.DataFrame, Optional[str]]:
    """Fetch recent candles with timeframe and better error reporting.

    Returns: (DataFrame, error_message)
    """
    initialized = False
    logger.info(f"[MT5] fetch_mt5_candles start symbol={symbol} tf={timeframe} count={count}")
    try:
        if not mt5.initialize():
            logger.error("[MT5] initialize() failed")
            return pd.DataFrame(), 'Failed to initialize MT5 terminal'
        initialized = True

        tf = TIMEFRAME_MAP.get(timeframe.upper(), mt5.TIMEFRAME_M1)

        candidate = symbol.strip()
        try:
            logger.info(f"[MT5] selecting symbol: {candidate}")
            selected_symbol = candidate
            if not mt5.symbol_select(candidate, True):
                # Collect suggestions from available symbols and try the first one automatically
                try:
                    all_symbols = mt5.symbols_get()
                    wanted = candidate.upper()
                    suggestions = [s.name for s in all_symbols or [] if wanted in s.name.upper()]
                    logger.warning(f"[MT5] symbol_select failed for {candidate}, suggestions={suggestions[:10]}")
                    if suggestions:
                        fallback = suggestions[0]
                        logger.info(f"[MT5] retrying with suggested symbol: {fallback}")
                        if not mt5.symbol_select(fallback, True):
                            return pd.DataFrame(), f"Symbol not available: {candidate}. Suggested {fallback} also not selectable."
                        selected_symbol = fallback
                    else:
                        return pd.DataFrame(), f'Symbol not available: {candidate}'
                except Exception as e:
                    logger.exception(f"[MT5] error while building suggestions: {e}")
                    return pd.DataFrame(), f'Symbol not available: {candidate}'
            now = datetime.now()
            logger.info(f"[MT5] copy_rates_from {selected_symbol} tf={timeframe} now={now} count={count}")
            rates = mt5.copy_rates_from(selected_symbol, tf, now, count)
            if rates is None or len(rates) == 0:
                logger.warning("[MT5] copy_rates_from returned no data, trying copy_rates_from_pos")
                # Try from position as fallback
                rates = mt5.copy_rates_from_pos(selected_symbol, tf, 0, count)
            if rates is None or len(rates) == 0:
                logger.error("[MT5] no rates after both methods")
                return pd.DataFrame(), f'No rates for symbol: {selected_symbol}'

            df = pd.DataFrame(rates)
            logger.info(f"[MT5] received rates: len={len(df)} head_time={df['time'].iloc[0] if not df.empty else 'NA'} tail_time={df['time'].iloc[-1] if not df.empty else 'NA'}")
            if df.empty:
                logger.error("[MT5] dataframe empty after converting rates")
                return pd.DataFrame(), f'Empty dataframe for symbol'
            df['datetime'] = pd.to_datetime(df['time'], unit='s')
            df = df.rename(columns={'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close', 'tick_volume': 'volume'})
            df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('datetime')
            df.set_index('datetime', inplace=True)
            logger.info(f"[MT5] final df shape={df.shape} first={df.index[0] if not df.empty else 'NA'} last={df.index[-1] if not df.empty else 'NA'}")
            return df, None
        except Exception as e:
            logger.exception(f"[MT5] exception during fetch for {candidate}: {e}")
            return pd.DataFrame(), f'Error for {candidate}: {e}'
    finally:
        if initialized:
            mt5.shutdown()
            logger.info("[MT5] shutdown()")


def extract_timeframe_minutes(timeframe: str) -> Optional[int]:
    """
    Extract minutes from timeframe string.
    
    Examples:
        "77m" -> 77
        "77min" -> 77
        "77 دقیقه" -> 77
        "M15" -> 15
        "H1" -> 60
        "1h" -> 60
    
    Returns:
        Minutes as integer, or None if cannot be determined
    """
    if not timeframe:
        return None
    
    import re
    timeframe_upper = str(timeframe).upper().strip()
    
    # Direct MT5 format mappings
    mt5_mapping = {
        'M1': 1,
        'M5': 5,
        'M15': 15,
        'M30': 30,
        'H1': 60,
        'H4': 240,
        'D1': 1440,
    }
    if timeframe_upper in mt5_mapping:
        return mt5_mapping[timeframe_upper]
    
    # Pattern: "77m", "77min", "77 minute", "77 دقیقه"
    minute_match = re.search(r'(\d+)\s*(?:m|min|minute|دقیقه)', timeframe_upper)
    if minute_match:
        return int(minute_match.group(1))
    
    # Pattern: "1h", "1 hour", "1 ساعت"
    hour_match = re.search(r'(\d+)\s*(?:h|hour|ساعت)', timeframe_upper)
    if hour_match:
        return int(hour_match.group(1)) * 60
    
    # Pattern: "1d", "1 day", "1 روز"
    day_match = re.search(r'(\d+)\s*(?:d|day|روز)', timeframe_upper)
    if day_match:
        return int(day_match.group(1)) * 1440
    
    return None


def aggregate_m1_candles_to_timeframe(m1_df: pd.DataFrame, target_minutes: int) -> pd.DataFrame:
    """
    Aggregate M1 candles to a custom timeframe.
    
    Args:
        m1_df: DataFrame with M1 candles (must have datetime index and OHLCV columns)
        target_minutes: Target timeframe in minutes (e.g., 77 for 77-minute candles)
    
    Returns:
        DataFrame with aggregated candles
    """
    if m1_df.empty:
        return m1_df
    
    if target_minutes <= 1:
        return m1_df.copy()
    
    # Ensure datetime index
    if not isinstance(m1_df.index, pd.DatetimeIndex):
        if 'datetime' in m1_df.columns:
            m1_df = m1_df.set_index('datetime')
        else:
            logger.error("Cannot aggregate: DataFrame must have datetime index")
            return m1_df
    
    # Create a copy to avoid modifying original
    df = m1_df.copy()
    
    # Resample to target timeframe
    # Use 'T' for minutes in pandas
    rule = f'{target_minutes}T'
    
    # Aggregate OHLCV
    aggregated = pd.DataFrame()
    aggregated['open'] = df['open'].resample(rule).first()
    aggregated['high'] = df['high'].resample(rule).max()
    aggregated['low'] = df['low'].resample(rule).min()
    aggregated['close'] = df['close'].resample(rule).last()
    
    # Sum volume if available
    if 'volume' in df.columns:
        aggregated['volume'] = df['volume'].resample(rule).sum()
    elif 'tick_volume' in df.columns:
        aggregated['volume'] = df['tick_volume'].resample(rule).sum()
    
    # Drop rows with NaN (incomplete candles at the end)
    aggregated = aggregated.dropna()
    
    logger.info(f"Aggregated {len(m1_df)} M1 candles to {len(aggregated)} {target_minutes}-minute candles")
    
    return aggregated


def fetch_mt5_candles_aggregated(symbol: str, target_timeframe: str, count: int = 500) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Fetch candles from MT5 by always using M1 and aggregating to target timeframe.
    
    This ensures accurate backtesting for custom timeframes (e.g., 77 minutes).
    
    Args:
        symbol: Trading symbol
        target_timeframe: Target timeframe string (e.g., "77m", "M15", "H1")
        count: Number of target candles needed (will fetch more M1 candles to aggregate)
    
    Returns:
        (DataFrame with aggregated candles, error_message)
    """
    # Extract minutes from target timeframe
    target_minutes = extract_timeframe_minutes(target_timeframe)
    
    if target_minutes is None:
        # Fallback to standard MT5 timeframe
        logger.warning(f"Could not extract minutes from timeframe '{target_timeframe}', using standard MT5 fetch")
        return fetch_mt5_candles(symbol, target_timeframe, count)
    
    # If target is 1 minute, use standard M1 fetch
    if target_minutes == 1:
        return fetch_mt5_candles(symbol, 'M1', count)
    
    # Calculate how many M1 candles we need
    # Add 20% buffer to ensure we have enough data after aggregation
    m1_count = int(count * target_minutes * 1.2)
    
    logger.info(f"Fetching {m1_count} M1 candles to aggregate to {target_minutes}-minute candles (need {count} candles)")
    
    # Fetch M1 candles
    m1_df, error = fetch_mt5_candles(symbol, 'M1', m1_count)
    
    if error or m1_df.empty:
        return m1_df, error
    
    # Aggregate to target timeframe
    aggregated_df = aggregate_m1_candles_to_timeframe(m1_df, target_minutes)
    
    # Limit to requested count (most recent candles)
    if len(aggregated_df) > count:
        aggregated_df = aggregated_df.tail(count)
    
    return aggregated_df, None


def is_mt5_available() -> Tuple[bool, Optional[str]]:
    """Quick availability check for a locally installed and logged-in MT5 terminal."""
    try:
        if not mt5.initialize():
            return False, 'Failed to initialize MT5 terminal'
        return True, None
    except Exception as e:
        return False, f'MT5 error: {e}'
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass


def get_mt5_account_info():
    """Get account information from MT5."""
    initialized = False
    try:
        if not mt5.initialize():
            return None, 'Failed to initialize MT5 terminal'
        initialized = True
        
        account_info = mt5.account_info()
        if account_info is None:
            return None, 'Failed to get account info'
        
        # Determine if account is demo or real
        # MT5 typically marks demo accounts with specific server names or trade_mode
        is_demo = account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO
        # Also check server name for common demo patterns
        server_lower = account_info.server.lower() if account_info.server else ''
        if 'demo' in server_lower or 'test' in server_lower:
            is_demo = True
        elif 'real' in server_lower or 'live' in server_lower:
            is_demo = False
        
        return {
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'free_margin': account_info.margin_free,
            'margin_level': account_info.margin_level,
            'currency': account_info.currency,
            'server': account_info.server,
            'login': account_info.login,
            'name': account_info.name,
            'leverage': account_info.leverage,
            'is_demo': is_demo,
            'trade_mode': account_info.trade_mode,
        }, None
    except Exception as e:
        logger.exception(f"[MT5] Error getting account info: {e}")
        return None, f'Error: {e}'
    finally:
        if initialized:
            mt5.shutdown()


def get_mt5_positions(symbol: str = None):
    """Get open positions from MT5."""
    initialized = False
    try:
        if not mt5.initialize():
            return [], 'Failed to initialize MT5 terminal'
        initialized = True
        
        positions = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        if positions is None:
            # No positions or error
            error_code = mt5.last_error()
            if error_code[0] == mt5.RES_S_OK:
                return [], None  # No positions
            return [], f'Error getting positions: {error_code}'
        
        positions_list = []
        for pos in positions:
            positions_list.append({
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'profit': pos.profit,
                'swap': pos.swap,
                'commission': pos.commission,
                'time': datetime.fromtimestamp(pos.time),
                'stop_loss': pos.sl,
                'take_profit': pos.tp,
                'comment': pos.comment or '',
            })
        
        return positions_list, None
    except Exception as e:
        logger.exception(f"[MT5] Error getting positions: {e}")
        return [], f'Error: {e}'
    finally:
        if initialized:
            mt5.shutdown()


def compute_volume_for_risk(symbol: str, entry_price: float, stop_loss_price: float, risk_percent: float) -> tuple:
    """
    Compute MT5 order volume (lots) to risk approximately `risk_percent` of account equity
    based on distance between entry and stop loss using MT5 tick size/value.

    Returns: (volume, error) where volume is float or None if error.
    """
    initialized = False
    try:
        if not mt5.initialize():
            return None, 'Failed to initialize MT5 terminal'
        initialized = True

        account = mt5.account_info()
        if account is None:
            return None, 'Failed to get account info for risk sizing'

        sym = symbol.strip()
        if not mt5.symbol_select(sym, True):
            # try fallback to available symbol containing name
            all_symbols = mt5.symbols_get()
            wanted = sym.upper()
            cand = next((s.name for s in all_symbols or [] if wanted in s.name.upper()), None)
            if not cand or not mt5.symbol_select(cand, True):
                return None, f'Cannot select symbol {symbol} for risk sizing'
            sym = cand

        info = mt5.symbol_info(sym)
        if info is None:
            return None, f'Cannot get symbol info for {sym}'

        tick_size = float(getattr(info, 'trade_tick_size', 0.0) or getattr(info, 'point', 0.0) or 0.0)
        tick_value = float(getattr(info, 'trade_tick_value', 0.0))
        vol_min = float(getattr(info, 'volume_min', 0.01))
        vol_max = float(getattr(info, 'volume_max', 100.0))
        vol_step = float(getattr(info, 'volume_step', 0.01))

        if tick_size <= 0 or tick_value <= 0:
            return None, 'Invalid symbol tick parameters for risk sizing'

        price_delta = abs(entry_price - stop_loss_price)
        if price_delta <= 0:
            return None, 'Stop loss equals entry price'

        ticks_to_sl = max(1.0, price_delta / tick_size)
        risk_amount = float(account.equity) * (float(risk_percent) / 100.0)
        # volume = risk / (ticks * tick_value)
        raw_vol = risk_amount / (ticks_to_sl * tick_value)

        # snap to step and bounds
        def snap(v, step):
            steps = max(1, int(round(v / step)))
            return round(steps * step, 2)

        vol = max(vol_min, min(vol_max, snap(max(raw_vol, 0.0), vol_step)))
        if vol <= 0:
            return None, 'Computed volume is zero; check risk_percent/SL'
        return vol, None
    except Exception as e:
        logger.exception(f"[MT5] Error computing risk volume: {e}")
        return None, f'Error computing volume: {e}'
    finally:
        if initialized:
            try:
                mt5.shutdown()
            except Exception:
                pass

def open_mt5_trade(symbol: str, trade_type: str, volume: float, 
                   stop_loss: float = None, take_profit: float = None,
                   deviation: int = 20, comment: str = 'Strategy Trade'):
    """
    Open a trade in MT5.
    
    Args:
        symbol: Trading symbol (e.g., 'XAUUSD')
        trade_type: 'buy' or 'sell'
        volume: Trade volume in lots
        stop_loss: Stop loss price (optional)
        take_profit: Take profit price (optional)
        deviation: Maximum price deviation from current price in points
        comment: Trade comment
    
    Returns:
        (result_dict, error_message)
    """
    initialized = False
    try:
        if not mt5.initialize():
            return None, 'Failed to initialize MT5 terminal'
        initialized = True
        
        # Normalize symbol (preserve case for broker-specific suffixes like _o/_l)
        base_symbol = symbol.strip()
        # Try selecting as-is first
        candidate = base_symbol
        if not mt5.symbol_select(candidate, True):
            # Try variants: uppercase, with .m, without USD
            variants = [
                base_symbol.upper(),
                f'{base_symbol}.m',
                base_symbol.replace('USD', ''),
                (base_symbol.upper().replace('USD', '')),
            ]
            selected = False
            for variant in variants:
                if mt5.symbol_select(variant, True):
                    candidate = variant
                    selected = True
                    break
            if not selected:
                # As a last resort, try suggestions from available symbols
                try:
                    all_symbols = mt5.symbols_get()
                    wanted = base_symbol.upper()
                    suggestions = [s.name for s in all_symbols or [] if wanted in s.name.upper()]
                    if suggestions and mt5.symbol_select(suggestions[0], True):
                        candidate = suggestions[0]
                    else:
                        return None, f'Symbol {base_symbol} not available in MT5'
                except Exception:
                    return None, f'Symbol {base_symbol} not available in MT5'
        
        # Get symbol info
        symbol_info = mt5.symbol_info(candidate)
        if symbol_info is None:
            return None, f'Could not get symbol info for {candidate}'
        
        if not symbol_info.visible:
            if not mt5.symbol_select(candidate, True):
                return None, f'Could not select symbol {candidate}'
        
        # Get current price
        tick = mt5.symbol_info_tick(candidate)
        if tick is None:
            return None, f'Could not get tick data for {candidate}'
        
        # Determine order type
        if trade_type.lower() == 'buy':
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            # Auto-adjust SL/TP to valid side if needed
            if 'XAU' in candidate or 'GOLD' in candidate.upper() or 'JPY' in candidate:
                _pip = 0.01
            else:
                _pip = 0.0001
            if stop_loss is not None and stop_loss >= price:
                stop_loss = price - _pip
            if take_profit is not None and take_profit <= price:
                take_profit = price + _pip
        elif trade_type.lower() == 'sell':
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            if 'XAU' in candidate or 'GOLD' in candidate.upper() or 'JPY' in candidate:
                _pip = 0.01
            else:
                _pip = 0.0001
            if stop_loss is not None and stop_loss <= price:
                stop_loss = price + _pip
            if take_profit is not None and take_profit >= price:
                take_profit = price - _pip
        else:
            return None, f'Invalid trade_type: {trade_type}. Must be "buy" or "sell"'
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": candidate,
            "volume": float(volume),
            "type": order_type,
            "price": price,
            "deviation": deviation,
            "magic": 234000,  # Magic number for strategy identification
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add stop loss and take profit if provided
        if stop_loss is not None:
            request["sl"] = float(stop_loss)
        if take_profit is not None:
            request["tp"] = float(take_profit)
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            return None, f'Order send failed: {error}'
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return None, f'Order failed: {result.retcode} - {result.comment}'
        
        # Get the opened position
        position = mt5.positions_get(ticket=result.order)
        if position and len(position) > 0:
            pos = position[0]
            return {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': 'buy' if pos.type == mt5.ORDER_TYPE_BUY else 'sell',
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'profit': pos.profit,
                'swap': pos.swap,
                'commission': pos.commission,
                'stop_loss': pos.sl,
                'take_profit': pos.tp,
                'comment': pos.comment or '',
                'time': datetime.fromtimestamp(pos.time).isoformat(),
            }, None
        else:
            # Order was filled but position not found immediately
            return {
                'ticket': result.order,
                'symbol': candidate,
                'type': trade_type,
                'volume': volume,
                'price_open': price,
                'comment': comment,
            }, None
            
    except Exception as e:
        logger.exception(f"[MT5] Error opening trade: {e}")
        return None, f'Error: {e}'
    finally:
        if initialized:
            mt5.shutdown()


def close_mt5_trade(ticket: int, volume: float = None):
    """
    Close a position in MT5.
    
    Args:
        ticket: Position ticket number
        volume: Volume to close (None to close entire position)
    
    Returns:
        (result_dict, error_message)
    """
    initialized = False
    try:
        if not mt5.initialize():
            return None, 'Failed to initialize MT5 terminal'
        initialized = True
        
        # Get position
        positions = mt5.positions_get(ticket=ticket)
        if positions is None or len(positions) == 0:
            return None, f'Position with ticket {ticket} not found'
        
        position = positions[0]
        
        # Get current price
        tick = mt5.symbol_info_tick(position.symbol)
        if tick is None:
            return None, f'Could not get tick data for {position.symbol}'
        
        # Determine close type and price
        if position.type == mt5.ORDER_TYPE_BUY:
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        
        # Use provided volume or position volume
        close_volume = volume if volume else position.volume
        
        # Prepare request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": float(close_volume),
            "type": order_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "Strategy Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result is None:
            error = mt5.last_error()
            return None, f'Close order failed: {error}'
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return None, f'Close order failed: {result.retcode} - {result.comment}'
        
        return {
            'ticket': ticket,
            'closed': True,
            'close_price': price,
            'profit': position.profit,
            'comment': result.comment,
        }, None
        
    except Exception as e:
        logger.exception(f"[MT5] Error closing trade: {e}")
        return None, f'Error: {e}'
    finally:
        if initialized:
            mt5.shutdown()


def is_market_open():
    """Check if forex market is currently open (24/5 excluding weekends)."""
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    weekday = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Forex market is closed on weekends (Saturday and Sunday)
    if weekday >= 5:  # Saturday = 5, Sunday = 6
        return False, 'Market is closed (weekend)'
    
    # Market is open 24/5 during weekdays
    return True, 'Market is open'


def get_symbol_for_account(base_symbol: str = 'XAUUSD') -> str:
    """
    Get the correct symbol variant based on account type (demo or real).
    - Demo accounts: XAUUSD_o
    - Real accounts: XAUUSD_l
    
    Args:
        base_symbol: Base symbol without suffix (default: 'XAUUSD')
    
    Returns:
        Symbol with appropriate suffix based on account type
    """
    account_info, error = get_mt5_account_info()
    if error or not account_info:
        # If we can't determine account type, try to detect from available symbols
        logger.warning(f"Could not get account info, trying to detect symbol: {error}")
        return _detect_symbol_from_available(base_symbol)
    
    is_demo = account_info.get('is_demo', False)
    
    if is_demo:
        symbol = f"{base_symbol}_o"
        logger.info(f"Demo account detected, using symbol: {symbol}")
    else:
        symbol = f"{base_symbol}_l"
        logger.info(f"Real account detected, using symbol: {symbol}")
    
    # Verify symbol exists in MT5
    initialized = False
    try:
        if not mt5.initialize():
            return symbol  # Return what we determined, even if we can't verify
        initialized = True
        
        # Try to select the symbol to verify it exists
        if mt5.symbol_select(symbol, True):
            return symbol
        else:
            # If our determined symbol doesn't exist, try alternatives
            logger.warning(f"Symbol {symbol} not available, trying alternatives")
            return _detect_symbol_from_available(base_symbol)
    finally:
        if initialized:
            mt5.shutdown()
    
    return symbol


def _detect_symbol_from_available(base_symbol: str) -> str:
    """
    Detect correct symbol variant by checking available symbols in MT5.
    Tries both _o (demo) and _l (real) variants.
    
    Args:
        base_symbol: Base symbol without suffix
    
    Returns:
        Available symbol variant or base symbol if neither found
    """
    initialized = False
    try:
        if not mt5.initialize():
            return base_symbol
        initialized = True
        
        # Get all available symbols
        symbols = mt5.symbols_get()
        if symbols is None:
            return base_symbol
        
        # Try demo variant first (_o)
        demo_symbol = f"{base_symbol}_o"
        real_symbol = f"{base_symbol}_l"
        
        symbol_names = [s.name for s in symbols]
        
        if demo_symbol in symbol_names:
            logger.info(f"Detected demo symbol: {demo_symbol}")
            return demo_symbol
        elif real_symbol in symbol_names:
            logger.info(f"Detected real symbol: {real_symbol}")
            return real_symbol
        elif base_symbol in symbol_names:
            logger.info(f"Using base symbol: {base_symbol}")
            return base_symbol
        else:
            # Try case-insensitive search
            base_upper = base_symbol.upper()
            for sym_name in symbol_names:
                if base_upper in sym_name.upper():
                    logger.info(f"Found similar symbol: {sym_name}")
                    return sym_name
            
            logger.warning(f"Could not find symbol variant for {base_symbol}, using base")
            return base_symbol
            
    except Exception as e:
        logger.exception(f"Error detecting symbol: {e}")
        return base_symbol
    finally:
        if initialized:
            mt5.shutdown()


def get_available_mt5_symbols() -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Get all available symbols from MT5 and test if they are actually selectable.
    
    Returns:
        (list of symbol dictionaries with 'name' and 'is_available' status, error_message)
    """
    initialized = False
    available_symbols = []
    
    try:
        if not mt5.initialize():
            return [], 'Failed to initialize MT5 terminal'
        initialized = True
        
        # Get all symbols
        symbols = mt5.symbols_get()
        if symbols is None:
            return [], 'Failed to get symbols from MT5'
        
        logger.info(f"Found {len(symbols)} symbols in MT5, testing availability...")
        
        # Test each symbol to see if it's actually selectable
        for symbol_info in symbols:
            symbol_name = symbol_info.name
            is_selectable = False
            
            try:
                # Try to select the symbol
                is_selectable = mt5.symbol_select(symbol_name, True)
            except Exception as e:
                logger.debug(f"Error selecting symbol {symbol_name}: {e}")
                is_selectable = False
            
            available_symbols.append({
                'name': symbol_name,
                'is_available': is_selectable,
                'description': symbol_info.description if hasattr(symbol_info, 'description') else '',
                'currency_base': symbol_info.currency_base if hasattr(symbol_info, 'currency_base') else '',
                'currency_profit': symbol_info.currency_profit if hasattr(symbol_info, 'currency_profit') else '',
                'currency_margin': symbol_info.currency_margin if hasattr(symbol_info, 'currency_margin') else '',
            })
        
        # Filter to only available symbols and sort
        available_count = sum(1 for s in available_symbols if s['is_available'])
        logger.info(f"Tested {len(available_symbols)} symbols, {available_count} are available")
        
        return available_symbols, None
        
    except Exception as e:
        logger.exception(f"Error getting MT5 symbols: {e}")
        return [], f'Error: {e}'
    finally:
        if initialized:
            mt5.shutdown()


def map_user_symbol_to_server_symbol(user_symbol: str, for_backtest: bool = True) -> str:
    """
    Map user-selected symbol to the appropriate server symbol.
    For backtesting, prefer XAUUSD_l for gold symbols.
    
    Args:
        user_symbol: Symbol selected by user (e.g., 'XAUUSD')
        for_backtest: Whether this is for backtesting (default: True)
    
    Returns:
        Server symbol (e.g., 'XAUUSD_l' for XAUUSD in backtest mode)
    """
    user_symbol = user_symbol.strip().upper()
    
    # For backtesting with gold symbols, prefer _l (live) variant
    if for_backtest:
        # Special handling for gold symbols
        if user_symbol == 'XAUUSD' or user_symbol.startswith('XAU'):
            # Try to detect available variant
            server_symbol = _detect_symbol_from_available('XAUUSD')
            # If detected symbol is base, prefer _l for backtest
            if server_symbol == 'XAUUSD':
                # Check if _l exists
                initialized = False
                try:
                    if mt5.initialize():
                        initialized = True
                        if mt5.symbol_select('XAUUSD_l', True):
                            return 'XAUUSD_l'
                        elif mt5.symbol_select('XAUUSD_o', True):
                            return 'XAUUSD_o'
                except Exception:
                    pass
                finally:
                    if initialized:
                        mt5.shutdown()
            return server_symbol
        
        # For other symbols, try to get the appropriate variant
        server_symbol = _detect_symbol_from_available(user_symbol)
        return server_symbol
    
    # For live trading, use the mapping function based on account type
    return get_symbol_for_account(user_symbol)



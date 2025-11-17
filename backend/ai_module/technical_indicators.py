import pandas as pd
import numpy as np
from typing import Tuple, List
import logging

logger = logging.getLogger(__name__)

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logger.error(f"Error calculating RSI: {e}")
        return pd.Series(index=prices.index, dtype=float)

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD indicator"""
    try:
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    except Exception as e:
        logger.error(f"Error calculating MACD: {e}")
        empty_series = pd.Series(index=prices.index, dtype=float)
        return empty_series, empty_series, empty_series

def calculate_moving_average(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    try:
        return prices.rolling(window=period).mean()
    except Exception as e:
        logger.error(f"Error calculating Moving Average: {e}")
        return pd.Series(index=prices.index, dtype=float)

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    try:
        return prices.ewm(span=period).mean()
    except Exception as e:
        logger.error(f"Error calculating EMA: {e}")
        return pd.Series(index=prices.index, dtype=float)

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands"""
    try:
        sma = calculate_moving_average(prices, period)
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands: {e}")
        empty_series = pd.Series(index=prices.index, dtype=float)
        return empty_series, empty_series, empty_series

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator"""
    try:
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    except Exception as e:
        logger.error(f"Error calculating Stochastic: {e}")
        empty_series = pd.Series(index=close.index, dtype=float)
        return empty_series, empty_series

def calculate_williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Williams %R"""
    try:
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return williams_r
    except Exception as e:
        logger.error(f"Error calculating Williams %R: {e}")
        return pd.Series(index=close.index, dtype=float)

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    try:
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    except Exception as e:
        logger.error(f"Error calculating ATR: {e}")
        return pd.Series(index=close.index, dtype=float)

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Average Directional Index"""
    try:
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        dm_plus = high.diff()
        dm_minus = -low.diff()
        
        dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
        dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)
        
        # Calculate smoothed values
        tr_smooth = tr.rolling(window=period).mean()
        dm_plus_smooth = dm_plus.rolling(window=period).mean()
        dm_minus_smooth = dm_minus.rolling(window=period).mean()
        
        # Calculate DI
        di_plus = 100 * (dm_plus_smooth / tr_smooth)
        di_minus = 100 * (dm_minus_smooth / tr_smooth)
        
        # Calculate ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return adx
    except Exception as e:
        logger.error(f"Error calculating ADX: {e}")
        return pd.Series(index=close.index, dtype=float)

def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> pd.Series:
    """Calculate Commodity Channel Index"""
    try:
        typical_price = (high + low + close) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical_price - sma_tp) / (0.015 * mad)
        return cci
    except Exception as e:
        logger.error(f"Error calculating CCI: {e}")
        return pd.Series(index=close.index, dtype=float)

def calculate_all_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators for the given data"""
    try:
        df = data.copy()
        
        # Ensure we have the required columns
        required_columns = ['open', 'high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return df
        
        # RSI
        df['rsi'] = calculate_rsi(df['close'])
        
        # MACD
        macd, macd_signal, macd_hist = calculate_macd(df['close'])
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_histogram'] = macd_hist
        
        # Moving Averages
        df['sma_20'] = calculate_moving_average(df['close'], 20)
        df['sma_50'] = calculate_moving_average(df['close'], 50)
        df['ema_12'] = calculate_ema(df['close'], 12)
        df['ema_26'] = calculate_ema(df['close'], 26)
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df['close'])
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        # Stochastic
        stoch_k, stoch_d = calculate_stochastic(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch_k
        df['stoch_d'] = stoch_d
        
        # Williams %R
        df['williams_r'] = calculate_williams_r(df['high'], df['low'], df['close'])
        
        # ATR
        df['atr'] = calculate_atr(df['high'], df['low'], df['close'])
        
        # ADX
        df['adx'] = calculate_adx(df['high'], df['low'], df['close'])
        
        # CCI
        df['cci'] = calculate_cci(df['high'], df['low'], df['close'])
        
        logger.info(f"Successfully calculated indicators for {len(df)} data points")
        return df
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return data

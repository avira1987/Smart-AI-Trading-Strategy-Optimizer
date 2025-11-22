import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import os
import time
from django.conf import settings
import logging
from dataclasses import dataclass
from api.mt5_client import fetch_mt5_candles, is_mt5_available

logger = logging.getLogger(__name__)

# Import APIConfiguration to load API keys from database
try:
    from core.models import APIConfiguration
except ImportError:
    APIConfiguration = None

_ADMIN_ALERT_COOLDOWN_SECONDS = 3600  # 1 hour
_provider_alert_history: Dict[str, float] = {}


def _notify_admin_api_issue(provider_name: str, message: str) -> None:
    """Send SMS notification to admins when a data provider fails or quota expires."""
    admin_phones = getattr(settings, 'ADMIN_NOTIFICATION_PHONES', [])
    if not admin_phones:
        return

    now = time.time()
    last_notified = _provider_alert_history.get(provider_name)
    if last_notified and now - last_notified < _ADMIN_ALERT_COOLDOWN_SECONDS:
        return

    _provider_alert_history[provider_name] = now

    alert_message = (
        f"هشدار سرویس داده ({provider_name}):\n"
        f"{message}\n"
        "لطفاً وضعیت کلید API یا اعتبار سرویس را بررسی کنید."
    )

    try:
        from .sms_service import send_sms
    except Exception:
        send_sms = None

    if send_sms:
        for phone in admin_phones:
            try:
                result = send_sms(phone, alert_message)
                if not result.get('success', False):
                    logger.error(
                        "Failed to send admin notification SMS for %s to %s: %s",
                        provider_name,
                        phone,
                        result.get('message', 'unknown error')
                    )
            except Exception as sms_error:
                logger.exception(
                    "Unexpected error while sending admin notification for %s: %s",
                    provider_name,
                    sms_error
                )
    else:
        logger.warning(
            "SMS service unavailable while notifying admins about %s issue: %s",
            provider_name,
            message
        )


class MT5DataProvider:
    """MetaTrader 5 based market data provider."""

    def __init__(self):
        self.api_key = None  # For compatibility with legacy interfaces

    def get_historical_data(self, symbol: str, timeframe: str = 'M15', count: int = 2000) -> pd.DataFrame:
        df, error = fetch_mt5_candles(symbol, timeframe, count)
        if df is None or df.empty:
            raise RuntimeError(error or "MT5 returned no data")
        return df

    def test_connection(self) -> Dict[str, Any]:
        available, error = is_mt5_available()
        if not available:
            raise RuntimeError(error or "MT5 terminal is not available")
        return {"status": "success", "message": "MetaTrader 5 connection is healthy"}


class TwelveDataProvider:
    """TwelveData API provider for historical data"""
    
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        self.base_url = 'https://api.twelvedata.com'
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1day') -> pd.DataFrame:
        """Get historical data from TwelveData"""
        if not self.api_key:
            logger.warning("TwelveData API key not found")
            _notify_admin_api_issue("TwelveData", "کلید TwelveData تنظیم نشده است یا از حساب حذف شده است.")
            return pd.DataFrame()
            
        url = f"{self.base_url}/time_series"
        params = {
            'symbol': symbol,
            'interval': interval,
            'start_date': start_date,
            'end_date': end_date,
            'apikey': self.api_key,
            'format': 'JSON'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'values' in data:
                df = pd.DataFrame(data['values'])
                # Normalize column names and dtypes
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                        except Exception:
                            pass
                df['datetime'] = pd.to_datetime(df['datetime'])
                df = df.sort_values('datetime')
                # Keep only expected OHLCV columns if present
                keep_cols = [c for c in ['datetime','open','high','low','close','volume'] if c in df.columns]
                df = df[keep_cols]
                df.set_index('datetime', inplace=True)
                return df
            else:
                logger.error(f"TwelveData API Error: {data}")
                error_info = data.get('message') or data
                _notify_admin_api_issue("TwelveData", f"پاسخ نامعتبر از TwelveData: {error_info}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"TwelveData API Error: {e}")
            _notify_admin_api_issue("TwelveData", f"خطای ارتباط با TwelveData: {e}")
            return pd.DataFrame()

class AlphaVantageProvider:
    """Alpha Vantage API provider"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data from Alpha Vantage"""
        if not self.api_key:
            logger.warning("Alpha Vantage API key not found")
            _notify_admin_api_issue("AlphaVantage", "کلید Alpha Vantage تنظیم نشده است یا در دسترس نیست.")
            raise Exception("Alpha Vantage API key not found")
        
        url = self.base_url
        params = {
            'function': 'FX_DAILY',
            'from_symbol': symbol.split('/')[0],
            'to_symbol': symbol.split('/')[1],
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Accept all main AlphaVantage FX keys
            time_series_keys = [
                'Time Series FX (Daily)',
                'Time Series (FX)',
                'Time Series FX (5min)',
                'Time Series FX (15min)',
                'Time Series FX (30min)',
                'Time Series FX (60min)'
            ]
            found_key = next((k for k in time_series_keys if k in data), None)
            if found_key:
                ts_data = data[found_key]
                df = pd.DataFrame(ts_data).T
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                # The column keys can vary, but commonly are:
                # '1. open', '2. high', '3. low', '4. close'
                if set(['1. open', '2. high', '3. low', '4. close']).issubset(df.columns):
                    df = df[['1. open', '2. high', '3. low', '4. close']].copy()
                    df.columns = ['open', 'high', 'low', 'close']
                    df = df.astype(float)
                return df
            else:
                err_msg = data.get('Error Message') or data.get('Note') or str(data)
                logger.error(f"Alpha Vantage API Error: {err_msg}")
                _notify_admin_api_issue("AlphaVantage", f"پاسخ خطا از Alpha Vantage: {err_msg}")
                raise Exception(f"Alpha Vantage API Error: {err_msg}")
        except Exception as e:
            logger.error(f"Alpha Vantage API Error: {e}")
            _notify_admin_api_issue("AlphaVantage", f"خطای ارتباط با Alpha Vantage: {e}")
            raise Exception(f"Alpha Vantage API Exception: {e}")

class OANDAProvider:
    """OANDA API provider"""
    
    def __init__(self):
        self.api_key = os.getenv('OANDA_API_KEY')
        self.base_url = 'https://api-fxpractice.oanda.com'
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data from OANDA"""
        if not self.api_key:
            logger.warning("OANDA API key not found")
            _notify_admin_api_issue("OANDA", "کلید OANDA تنظیم نشده است یا از حساب حذف شده است.")
            return pd.DataFrame()
            
        url = f"{self.base_url}/v3/instruments/{symbol}/candles"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        params = {
            'from': start_date,
            'to': end_date,
            'granularity': 'D'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'candles' in data:
                candles = []
                for candle in data['candles']:
                    if candle['complete']:
                        candles.append({
                            'datetime': candle['time'],
                            'open': float(candle['mid']['o']),
                            'high': float(candle['mid']['h']),
                            'low': float(candle['mid']['l']),
                            'close': float(candle['mid']['c'])
                        })
                
                df = pd.DataFrame(candles)
                df['datetime'] = pd.to_datetime(df['datetime'])
                df.set_index('datetime', inplace=True)
                return df
            else:
                logger.error(f"OANDA API Error: {data}")
                error_info = data.get('errorMessage') or data
                _notify_admin_api_issue("OANDA", f"پاسخ خطا از OANDA: {error_info}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"OANDA API Error: {e}")
            _notify_admin_api_issue("OANDA", f"خطای ارتباط با OANDA: {e}")
            return pd.DataFrame()

class MetalsAPIProvider:
    """MetalsAPI provider (metals-api.com)"""
    
    def __init__(self):
        # Supports either METALS_API_KEY or METALSAPI_API_KEY
        self.api_key = os.getenv('METALS_API_KEY') or os.getenv('METALSAPI_API_KEY')
        # Use only correct .com API url
        self.base_urls = ['https://metals-api.com/api']
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data for metals. Expects symbols like XAU/USD."""
        if not self.api_key:
            logger.warning("MetalsAPI API key not found")
            _notify_admin_api_issue("MetalsAPI", "کلید MetalsAPI تنظیم نشده است یا اعتبار آن به پایان رسیده است.")
            raise Exception("MetalsAPI API key not found")
        
        try:
            base, quote = symbol.replace('-', '/').split('/')
        except Exception:
            base, quote = 'XAU', 'USD'
        
        # Prefer timeseries if available; otherwise fall back to daily by-date loop
        # Try only the first reachable base to avoid long hangs
        for base_url in self.base_urls[:1]:
            url = f"{base_url}/timeseries"
            params = {
                'access_key': self.api_key,
                'base': base,
                'symbols': quote,
                'start_date': start_date,
                'end_date': end_date,
            }
            try:
                response = requests.get(url, params=params, timeout=8)
                response.raise_for_status()
                data = response.json()
                
                # Expected structure: { success: true, base: 'XAU', rates: { 'YYYY-MM-DD': { 'USD': 1234.56 } } }
                rates = data.get('rates') or {}
                if not rates:
                    err_msg = data.get('error', {}).get('info') or str(data)
                    logger.warning(f"MetalsAPI timeseries returned no rates: {err_msg}")
                    _notify_admin_api_issue("MetalsAPI", f"پاسخ نامعتبر از MetalsAPI: {err_msg}")
                    raise Exception(f"MetalsAPI timeseries error: {err_msg}")
                rows = []
                for date_str, quote_map in rates.items():
                    # If base is XAU and quote is USD, USD value is USD per 1 XAU directly
                    price = quote_map.get(quote)
                    if price is None:
                        continue
                    rows.append({
                        'datetime': pd.to_datetime(date_str),
                        'open': float(price),
                        'high': float(price),
                        'low': float(price),
                        'close': float(price),
                    })
                if not rows:
                    continue
                df = pd.DataFrame(rows)
                df.set_index('datetime', inplace=True)
                return df
            except Exception as e:
                logger.warning(f"MetalsAPI timeseries error on {base_url}: {e}")
                _notify_admin_api_issue("MetalsAPI", f"خطای timeseries در MetalsAPI: {e}")
                raise Exception(f"MetalsAPI timeseries exception: {e}")
        
        return pd.DataFrame()

    def _extract_usdxau_from_latest(self, data: Dict[str, Any]) -> Optional[float]:
        rates = data.get('rates') or {}
        if not isinstance(rates, dict):
            return None
        usdxau = rates.get('USDXAU')
        if usdxau is not None:
            try:
                return float(usdxau)
            except Exception:
                return None
        # If only XAU exists under base USD, invert
        xau_rate = rates.get('XAU')
        try:
            if xau_rate and float(xau_rate) != 0:
                return 1.0 / float(xau_rate)
        except Exception:
            return None
        return None

    def get_latest_usdxau(self) -> pd.DataFrame:
        """Fetch latest USD to main metals prices using base=USD and metals symbols."""
        if not self.api_key:
            logger.warning("MetalsAPI API key not found")
            _notify_admin_api_issue("MetalsAPI", "کلید MetalsAPI تنظیم نشده است یا از حساب حذف شده است.")
            raise Exception("MetalsAPI API key not found")
        
        param_keys = ['access_key']  # prefer standard key
        symbols = 'XAU,XAG,XPD,XPT'
        for base_url in self.base_urls[:1]:
            for key_name in param_keys:
                url = f"{base_url}/latest"
                params = {
                    key_name: self.api_key,
                    'base': 'USD',
                    'symbols': symbols,
                }
                try:
                    response = requests.get(url, params=params, timeout=8)
                    response.raise_for_status()
                    data = response.json()
                    if data.get('success') is False:
                        err_msg = data.get('error', {}).get('info') or str(data)
                        logger.warning(f"MetalsAPI latest error: {err_msg}")
                        _notify_admin_api_issue("MetalsAPI", f"پاسخ خطا از MetalsAPI (latest): {err_msg}")
                        raise Exception(f"MetalsAPI latest error: {err_msg}")
                    # Try to extract USDXAU or main metals rates, otherwise pass to old extract method
                    if 'rates' in data and 'USDXAU' in data['rates']:
                        usdxau = data['rates']['USDXAU']
                    elif 'rates' in data and 'XAU' in data['rates'] and data['rates']['XAU'] != 0:
                        # Calculate USD/XAU from XAU per USD
                        usdxau = 1 / float(data['rates']['XAU'])
                    else:
                        usdxau = self._extract_usdxau_from_latest(data)
                    if usdxau is None:
                        raise Exception("Could not extract USD/XAU value from MetalsAPI response")
                    df = pd.DataFrame([{
                        'datetime': pd.to_datetime(data.get('date') or pd.Timestamp.utcnow().date()),
                        'open': float(usdxau),
                        'high': float(usdxau),
                        'low': float(usdxau),
                        'close': float(usdxau),
                    }])
                    df.set_index('datetime', inplace=True)
                    return df
                except Exception as e:
                    logger.warning(f"MetalsAPI latest error on {base_url} with {key_name}: {e}")
                    _notify_admin_api_issue("MetalsAPI", f"خطای latest در MetalsAPI: {e}")
                    raise Exception(f"MetalsAPI latest exception: {e}")
        return pd.DataFrame()

class FinancialModelingPrepProvider:
    """Financial Modeling Prep API provider for historical data"""
    
    def __init__(self):
        # Get API key from environment variable (optional - can be set later via APIConfiguration)
        self.api_key = os.getenv('FINANCIALMODELINGPREP_API_KEY')
        if not self.api_key:
            logger.warning("FINANCIALMODELINGPREP_API_KEY not set. Please set it via environment variable or APIConfiguration model.")
        self.base_url = 'https://financialmodelingprep.com/api/v3'
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data from Financial Modeling Prep"""
        if not self.api_key:
            logger.warning("Financial Modeling Prep API key not found")
            _notify_admin_api_issue(
                "FinancialModelingPrep",
                "کلید Financial Modeling Prep تنظیم نشده است یا در دسترس نیست."
            )
            return pd.DataFrame()
        
        # Financial Modeling Prep uses different endpoints for different asset types
        # For forex/metals: /historical-chart/interval/{symbol}
        # For stocks: /historical-price-full/{symbol}
        
        # Try forex/metals endpoint first (XAU/USD -> XAUUSD)
        formatted_symbol = symbol.replace('/', '').upper()
        
        # Try daily historical data
        url = f"{self.base_url}/historical-price-full/{formatted_symbol}"
        params = {
            'apikey': self.api_key,
            'from': start_date,
            'to': end_date,
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                
                # Check if we have historical data
                if 'historical' in data and isinstance(data['historical'], list):
                    df = pd.DataFrame(data['historical'])
                    if not df.empty:
                        # Convert date column
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        
                        # Rename columns to match expected format
                        column_map = {
                            'open': 'open',
                            'high': 'high',
                            'low': 'low',
                            'close': 'close',
                            'volume': 'volume'
                        }
                        df = df.rename(columns={col: col for col in column_map.keys() if col in df.columns})
                        
                        # Keep only required columns
                        keep_cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
                        df = df[keep_cols]
                        df = df.sort_index()
                        return df
                
                # If no historical data, try alternative endpoint
                return self._try_alternative_endpoint(formatted_symbol, start_date, end_date)
            
            elif response.status_code == 403:
                logger.warning("Financial Modeling Prep API key invalid or expired")
                _notify_admin_api_issue(
                    "FinancialModelingPrep",
                    "کلید Financial Modeling Prep نامعتبر است یا اعتبار رایگان آن به پایان رسیده است."
                )
                return pd.DataFrame()
            else:
                logger.warning(f"Financial Modeling Prep returned status {response.status_code}")
                if response.status_code in (401, 402, 403, 429):
                    _notify_admin_api_issue(
                        "FinancialModelingPrep",
                        f"پاسخ خطا ({response.status_code}) از Financial Modeling Prep دریافت شد."
                    )
                return self._try_alternative_endpoint(formatted_symbol, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Financial Modeling Prep API Error: {e}")
            _notify_admin_api_issue(
                "FinancialModelingPrep",
                f"خطای ارتباط با Financial Modeling Prep: {e}"
            )
            return self._try_alternative_endpoint(formatted_symbol, start_date, end_date)
    
    def _try_alternative_endpoint(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Try alternative endpoint for historical data"""
        try:
            # Try 1day interval historical chart
            url = f"{self.base_url}/historical-chart/1day/{symbol}"
            params = {
                'apikey': self.api_key,
            }
            
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame(data)
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        
                        # Filter by date range
                        start = pd.to_datetime(start_date)
                        end = pd.to_datetime(end_date)
                        df = df[(df.index >= start) & (df.index <= end)]
                        
                        # Rename columns
                        column_map = {
                            'open': 'open',
                            'high': 'high',
                            'low': 'low',
                            'close': 'close',
                            'volume': 'volume'
                        }
                        df = df.rename(columns={col: col for col in column_map.keys() if col in df.columns})
                        
                        # Keep only required columns
                        keep_cols = [c for c in ['open', 'high', 'low', 'close', 'volume'] if c in df.columns]
                        df = df[keep_cols]
                        df = df.sort_index()
                        return df
            else:
                if response.status_code in (401, 402, 403, 429):
                    _notify_admin_api_issue(
                        "FinancialModelingPrep",
                        f"پاسخ خطا ({response.status_code}) از endpoint جایگزین Financial Modeling Prep دریافت شد."
                    )
        except Exception as e:
            logger.warning(f"Financial Modeling Prep alternative endpoint error: {e}")
            _notify_admin_api_issue(
                "FinancialModelingPrep",
                f"خطای ارتباط با endpoint جایگزین Financial Modeling Prep: {e}"
            )
        
        return pd.DataFrame()


class DataProviderManager:
    """Manager for all data providers"""
    
    def __init__(self, user=None):
        # نگهداری کاربر برای تشخیص کلیدهای اختصاصی
        self.user = user if user and getattr(user, "is_authenticated", False) else None
        self.providers = {
            'mt5': MT5DataProvider(),
        }
        # Load API keys from APIConfiguration if available
        self._load_api_keys_from_db()
    
    def _apply_api_configs(self, configs, *, override=False, source_label="system"):
        for api_config in configs:
            provider_name = api_config.provider
            provider_instance = self.providers.get(provider_name)
            if not provider_instance or not hasattr(provider_instance, 'api_key'):
                continue
            
            current_value = getattr(provider_instance, 'api_key', None)
            if override or not current_value:
                provider_instance.api_key = api_config.api_key
                logger.info(
                    "Loaded %s API key for %s from APIConfiguration (override=%s)",
                    source_label,
                    provider_name,
                    override,
                )
            else:
                logger.debug(
                    "Skipped loading %s API key for %s because provider already has a key",
                    source_label,
                    provider_name,
                )

    def _load_api_keys_from_db(self):
        """Load API keys from APIConfiguration model"""
        if not APIConfiguration:
            return
        
        user_id = None
        if self.user:
            user_id = getattr(self.user, "pk", None) or getattr(self.user, "id", None)
        
        try:
            # Load system-wide keys first (user=None)
            system_configs = APIConfiguration.objects.filter(
                is_active=True,
                user__isnull=True,
            ).order_by('-updated_at', '-created_at')
            
            # Load user-specific keys if a user is provided
            user_configs = []
            if user_id is not None:
                user_configs = APIConfiguration.objects.filter(
                    is_active=True,
                    user_id=user_id,
                ).order_by('-updated_at', '-created_at')
        except Exception as e:
            logger.warning(f"Failed to load API keys from database: {e}")
            return
        
        self._apply_api_configs(system_configs, override=False, source_label="system")
        
        if user_configs:
            # User keys should override system/env keys for that user session
            self._apply_api_configs(user_configs, override=True, source_label=f"user:{user_id}")

    def get_data(self, provider: str, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get data from specified provider"""
        if provider != 'mt5':
            raise ValueError(f"Provider {provider} not supported")
        try:
            timeframe_days = max(
                1,
                (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days or 1,
            )
        except Exception:
            timeframe_days = 30
        return self.get_historical_data(symbol, timeframe_days=timeframe_days)
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers with API keys"""
        available = []
        mt5_ok, _ = is_mt5_available()
        if mt5_ok:
            available.append('mt5')
        return available

    def _normalize_symbol(self, symbol: str) -> str:
        if not symbol:
            return "XAU/USD"
        normalized = symbol.strip().upper().replace("-", "/")
        if normalized == "XAUUSD":
            normalized = "XAU/USD"
        elif normalized == "USDXAU":
            normalized = "USD/XAU"
        return normalized

    def _format_symbol_for_mt5(self, symbol: str) -> str:
        if not symbol:
            return "XAUUSD"
        candidate = symbol.strip()
        if "/" in candidate:
            candidate = candidate.replace("/", "")
        if "-" in candidate:
            candidate = candidate.replace("-", "")
        return candidate or "XAUUSD"

    def _estimate_mt5_count(self, timeframe_days: int, interval: str) -> int:
        interval = (interval or "").lower()
        bars_per_day_map = {
            'm1': 1440,
            'm5': 288,
            'm15': 96,
            'm30': 48,
            'h1': 24,
            '4h': 6,
            '1day': 1,
            'daily': 1,
        }
        bars_per_day = bars_per_day_map.get(interval, 96)
        return max(200, min(5000, bars_per_day * max(1, timeframe_days)))

    def get_historical_data(
        self,
        symbol: str,
        timeframe_days: int = 365,
        *,
        interval: str = "1day",
        prefer_provider: Optional[str] = None,
        include_latest: bool = True,
        user=None,
        return_provider: bool = False,
    ) -> Any:
        """
        Fetch historical data exclusively from MetaTrader 5.
        """
        normalized_symbol = self._normalize_symbol(symbol)
        mt5_symbol = self._format_symbol_for_mt5(normalized_symbol)
        provider = self.providers.get('mt5')
        if provider is None:
            raise RuntimeError("MT5 provider is not initialized")

        mt5_timeframe = 'M15'
        count = self._estimate_mt5_count(timeframe_days, interval)
        try:
            data = provider.get_historical_data(mt5_symbol, timeframe=mt5_timeframe, count=count)
            provider_used = 'mt5'
        except Exception as mt5_error:
            logger.error("Failed to fetch data from MT5 for %s: %s", mt5_symbol, mt5_error)
            data = pd.DataFrame()
            provider_used = None

        if data is None:
            data = pd.DataFrame()

        if return_provider:
            return data, provider_used
        return data
    
    def get_data_from_any_provider(self, symbol: str, start_date: str, end_date: str, user=None) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        Try to get data from any available provider
        Returns: (dataframe, provider_name) or (empty_df, None) if all fail
        """
        try:
            timeframe_days = max(
                1,
                (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days or 1,
            )
        except Exception:
            timeframe_days = 30
        data = self.get_historical_data(symbol, timeframe_days=timeframe_days, return_provider=False)
        provider = 'mt5' if data is not None and not data.empty else None
        if provider is None:
            logger.error(f"MT5 provider failed to get data for {symbol}")
        return data, provider
    
    def test_provider(self, provider: str) -> Dict[str, Any]:
        """Test if provider is working"""
        if provider != 'mt5':
            return {'status': 'error', 'message': 'Provider not supported'}

        try:
            test_result = self.providers['mt5'].test_connection()
            test_symbol = 'XAUUSD'
            data = self.providers['mt5'].get_historical_data(test_symbol, timeframe='M15', count=500)
            if data is not None and not data.empty:
                test_result['data_points'] = len(data)
            else:
                test_result['status'] = 'error'
                test_result['message'] = 'MT5 returned no data for XAUUSD'
            return test_result
        except Exception as exc:
            return {'status': 'error', 'message': f'MT5 test failed: {exc}'}

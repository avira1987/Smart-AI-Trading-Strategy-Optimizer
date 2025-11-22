"""
ارائه‌دهندگان قیمت لحظه‌ای طلا (XAU/USD)
اولویت: 1) nerkh.io (با proxy)، 2) API های جایگزین، 3) MT5
"""

import requests
import os
import logging
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Import APIConfiguration to load API keys from database
try:
    from core.models import APIConfiguration
except ImportError:
    APIConfiguration = None

try:
    import MetaTrader5 as mt5  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - handled at runtime
    mt5 = None  # type: ignore[assignment]

try:
    from api.mt5_client import get_symbol_for_account, _detect_symbol_from_available
except ImportError:  # pragma: no cover - handled when MT5 client not available
    get_symbol_for_account = None  # type: ignore[assignment]
    _detect_symbol_from_available = None  # type: ignore[assignment]


class NerkhProvider:
    """ارائه‌دهنده قیمت از nerkh.io (نیاز به IP ایران)"""
    
    def __init__(self, api_key: str, proxy: Optional[str] = None):
        self.api_key = api_key
        self.proxy = proxy or os.getenv('NERKH_PROXY')
        self.base_url = "https://nerkh.io"
        
    def get_price(self) -> Tuple[Optional[float], Optional[str]]:
        """دریافت قیمت طلا"""
        # TODO: وقتی endpoint صحیح پیدا شد، اینجا پیاده می‌شود
        return None, "Endpoint not found yet"


class TwelveDataProvider:
    """ارائه‌دهنده قیمت از Twelve Data API"""
    
    @staticmethod
    def get_price(api_key: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت لحظه‌ای طلا از Twelve Data"""
        try:
            api_key = api_key or os.getenv('TWELVEDATA_API_KEY')
            if not api_key:
                return None, "TwelveData API key not configured"
            
            # Twelve Data برای طلا از symbol XAU/USD استفاده می‌کند
            url = 'https://api.twelvedata.com/price'
            params = {
                'symbol': 'XAU/USD',
                'apikey': api_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # بررسی ساختار پاسخ Twelve Data
                if 'price' in data:
                    price = float(data['price'])
                    # برای bid/ask، spread معمولی برای طلا را در نظر می‌گیریم
                    spread = 0.5  # spread معمولی برای طلا
                    bid = price - spread / 2
                    ask = price + spread / 2
                    
                    price_data = {
                        'bid': bid,
                        'ask': ask,
                        'last': price,
                        'spread': spread,
                        'time': datetime.now(),
                        'symbol': 'XAU/USD',
                        'volume': 0,
                    }
                    return price_data, None
                elif 'code' in data:
                    # خطای API
                    error_msg = data.get('message', 'Unknown error from Twelve Data')
                    return None, f"TwelveData API error: {error_msg}"
            
            return None, f"TwelveData API returned status {response.status_code}"
            
        except requests.exceptions.Timeout:
            return None, "TwelveData API timeout"
        except requests.exceptions.RequestException as e:
            return None, f"TwelveData API request error: {str(e)}"
        except Exception as e:
            logger.error(f"TwelveData error: {e}")
            return None, str(e)
    
    @staticmethod
    def get_realtime_quote(api_key: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت quote لحظه‌ای با جزئیات بیشتر"""
        try:
            api_key = api_key or os.getenv('TWELVEDATA_API_KEY')
            if not api_key:
                return None, "TwelveData API key not configured"
            
            url = 'https://api.twelvedata.com/quote'
            params = {
                'symbol': 'XAU/USD',
                'apikey': api_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'close' in data or 'price' in data:
                    price = float(data.get('close') or data.get('price', 0))
                    bid = float(data.get('bid', price - 0.25))
                    ask = float(data.get('ask', price + 0.25))
                    
                    price_data = {
                        'bid': bid,
                        'ask': ask,
                        'last': price,
                        'spread': ask - bid,
                        'time': datetime.now(),
                        'symbol': 'XAU/USD',
                        'volume': float(data.get('volume', 0)),
                        'high': float(data.get('high', price)),
                        'low': float(data.get('low', price)),
                        'open': float(data.get('open', price)),
                        'change': float(data.get('change', 0)),
                        'percent_change': float(data.get('percent_change', 0)),
                    }
                    return price_data, None
                elif 'code' in data:
                    error_msg = data.get('message', 'Unknown error')
                    return None, f"TwelveData API error: {error_msg}"
            
            return None, f"TwelveData API returned status {response.status_code}"
            
        except Exception as e:
            logger.error(f"TwelveData quote error: {e}")
            return None, str(e)


class FinancialModelingPrepProvider:
    """ارائه‌دهنده قیمت از Financial Modeling Prep API"""
    
    @staticmethod
    def get_price(api_key: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت لحظه‌ای طلا از Financial Modeling Prep"""
        try:
            # Get API key from environment variable (optional - can be set via APIConfiguration for data providers)
            api_key = api_key or os.getenv('FINANCIALMODELINGPREP_API_KEY')
            if not api_key:
                return None, "Financial Modeling Prep API key not configured. Please set FINANCIALMODELINGPREP_API_KEY environment variable."
            
            # Financial Modeling Prep برای طلا از endpoint commodities استفاده می‌کند
            # یا از quote endpoint برای XAU/USD
            url = 'https://financialmodelingprep.com/api/v3/quote/XAUUSD'
            params = {
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # بررسی ساختار پاسخ
                if isinstance(data, list) and len(data) > 0:
                    quote = data[0]
                    price = quote.get('price') or quote.get('close') or quote.get('last')
                    
                    if price:
                        price = float(price)
                        # برای bid/ask، spread معمولی را در نظر می‌گیریم
                        spread = 0.5
                        bid = price - spread / 2
                        ask = price + spread / 2
                        
                        price_data = {
                            'bid': bid,
                            'ask': ask,
                            'last': price,
                            'spread': spread,
                            'time': datetime.now(),
                            'symbol': 'XAU/USD',
                            'volume': float(quote.get('volume', 0)),
                            'high': float(quote.get('dayHigh', price)),
                            'low': float(quote.get('dayLow', price)),
                            'open': float(quote.get('open', price)),
                            'change': float(quote.get('change', 0)),
                            'percent_change': float(quote.get('changesPercentage', 0)),
                        }
                        return price_data, None
                
                # اگر ساختار متفاوت بود، سعی کنیم از endpoint دیگر استفاده کنیم
                return FinancialModelingPrepProvider.get_from_commodities(api_key)
            
            elif response.status_code == 403:
                return None, "Financial Modeling Prep API key invalid or expired"
            elif response.status_code == 429:
                return None, "Financial Modeling Prep API rate limit exceeded"
            
            return None, f"Financial Modeling Prep API returned status {response.status_code}"
            
        except requests.exceptions.Timeout:
            return None, "Financial Modeling Prep API timeout"
        except requests.exceptions.RequestException as e:
            return None, f"Financial Modeling Prep API request error: {str(e)}"
        except Exception as e:
            logger.error(f"Financial Modeling Prep error: {e}")
            return None, str(e)
    
    @staticmethod
    def get_from_commodities(api_key: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت طلا از endpoint commodities"""
        try:
            # Get API key from environment variable (optional - can be set via APIConfiguration for data providers)
            api_key = api_key or os.getenv('FINANCIALMODELINGPREP_API_KEY')
            if not api_key:
                return None, "Financial Modeling Prep API key not configured. Please set FINANCIALMODELINGPREP_API_KEY environment variable."
            
            # برخی از plan ها از endpoint commodities استفاده می‌کنند
            url = 'https://financialmodelingprep.com/api/v3/commodities'
            params = {
                'apikey': api_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # جستجوی طلا در لیست کالاها
                if isinstance(data, list):
                    for commodity in data:
                        symbol = commodity.get('symbol', '').upper()
                        name = commodity.get('name', '').upper()
                        
                        if 'XAU' in symbol or 'GOLD' in name or 'GOLD' in symbol:
                            price = commodity.get('price') or commodity.get('last')
                            if price:
                                price = float(price)
                                spread = 0.5
                                bid = price - spread / 2
                                ask = price + spread / 2
                                
                                price_data = {
                                    'bid': bid,
                                    'ask': ask,
                                    'last': price,
                                    'spread': spread,
                                    'time': datetime.now(),
                                    'symbol': 'XAU/USD',
                                    'volume': 0,
                                }
                                return price_data, None
            
            return None, "Gold not found in commodities list"
            
        except Exception as e:
            logger.error(f"Financial Modeling Prep commodities error: {e}")
            return None, str(e)


class FreeAPIProvider:
    """ارائه‌دهندگان API رایگان جایگزین"""
    
    @staticmethod
    def get_from_fixer_io() -> Tuple[Optional[float], Optional[str]]:
        """دریافت از Fixer.io (رایگان - محدود)"""
        try:
            api_key = os.getenv('FIXER_API_KEY')
            if not api_key:
                return None, "Fixer API key not configured"
            
            # Fixer.io معمولاً XAU را پشتیبانی نمی‌کند، اما می‌توانیم تست کنیم
            response = requests.get(
                'http://data.fixer.io/api/latest',
                params={
                    'access_key': api_key,
                    'symbols': 'XAU',  # اگر پشتیبانی کند
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'rates' in data:
                    xau_rate = data['rates'].get('XAU')
                    if xau_rate:
                        # تبدیل به USD/XAU (معکوس)
                        return 1.0 / float(xau_rate), None
            
            return None, "XAU not supported by Fixer.io"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_from_exchangerate_api() -> Tuple[Optional[float], Optional[str]]:
        """دریافت از ExchangeRate-API (رایگان)"""
        try:
            # ExchangeRate-API رایگان
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/XAU',
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'USD' in data['rates']:
                    return float(data['rates']['USD']), None
            
            return None, "ExchangeRate-API doesn't support XAU"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_from_metalsapi_free() -> Tuple[Optional[float], Optional[str]]:
        """دریافت از MetalsAPI (رایگان - محدود)"""
        try:
            api_key = os.getenv('METALS_API_KEY')
            if not api_key:
                return None, "MetalsAPI key not configured"
            
            response = requests.get(
                'https://metals-api.com/api/latest',
                params={
                    'access_key': api_key,
                    'base': 'XAU',
                    'symbols': 'USD',
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'rates' in data:
                    usd_rate = data['rates'].get('USD')
                    if usd_rate:
                        return float(usd_rate), None
            
            return None, "MetalsAPI error"
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_from_openexchangerates() -> Tuple[Optional[float], Optional[str]]:
        """دریافت از OpenExchangeRates (رایگان - محدود)"""
        try:
            api_key = os.getenv('OPENEXCHANGERATES_API_KEY')
            if not api_key:
                return None, "OpenExchangeRates key not configured"
            
            # OpenExchangeRates معمولاً XAU را پشتیبانی نمی‌کند
            response = requests.get(
                'https://openexchangerates.org/api/latest.json',
                params={'app_id': api_key},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # بررسی آیا XAU در rates هست
                if 'rates' in data and 'XAU' in data['rates']:
                    return float(data['rates']['XAU']), None
            
            return None, "OpenExchangeRates doesn't support XAU"
        except Exception as e:
            return None, str(e)


class MT5GoldPriceProvider:
    """ارائه‌دهنده قیمت لحظه‌ای طلا از MT5"""
    
    def __init__(self):
        self.symbol = 'XAUUSD'
    
    def get_price(self) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت لحظه‌ای طلا از MT5"""
        try:
            global mt5  # ensure module-level reference updated when available
            module_mt5 = mt5
            if module_mt5 is None:
                try:
                    import MetaTrader5 as module_mt5  # type: ignore[import-untyped]
                    mt5 = module_mt5
                except ImportError:
                    return None, 'MetaTrader5 package not installed'

            initialized = False
            try:
                if not module_mt5.initialize():
                    return None, 'Failed to initialize MT5 terminal'
                initialized = True
                
                symbol_getter = get_symbol_for_account
                symbol_detector = _detect_symbol_from_available
                if symbol_getter is None or symbol_detector is None:
                    from api.mt5_client import get_symbol_for_account as symbol_getter, _detect_symbol_from_available as symbol_detector  # type: ignore
                
                # اول سعی کنیم با get_symbol_for_account
                actual_symbol = symbol_getter(self.symbol) if symbol_getter else self.symbol
                
                # اگر symbol انتخاب نشد، سعی کنیم نمادهای مختلف را امتحان کنیم
                if not actual_symbol:
                    actual_symbol = self.symbol
                if not module_mt5.symbol_select(actual_symbol, True):
                    # نمادهای محتمل
                    possible_symbols = [
                        'XAUUSD',
                        'XAUUSD_o',
                        'XAUUSD_l',
                        'GOLD',
                        'GOLDUSD',
                        'XAU/USD',
                    ]
                    
                    for sym in possible_symbols:
                        if module_mt5.symbol_select(sym, True):
                            actual_symbol = sym
                            logger.info(f"Found gold symbol: {sym}")
                            break
                    else:
                        # آخرین تلاش: از _detect_symbol_from_available
                        if symbol_detector:
                            actual_symbol = symbol_detector(self.symbol)
                
                # Select symbol
                if not module_mt5.symbol_select(actual_symbol, True):
                    return None, f'Symbol {actual_symbol} not available in MT5'
                
                # Get current tick
                tick = module_mt5.symbol_info_tick(actual_symbol)
                if tick is None:
                    return None, f'Could not get tick data for {actual_symbol}'
                
                price_data = {
                    'bid': float(tick.bid),
                    'ask': float(tick.ask),
                    'last': float(tick.last),
                    'spread': float(tick.ask - tick.bid),
                    'time': datetime.fromtimestamp(tick.time),
                    'symbol': actual_symbol,
                    'volume': int(tick.volume) if hasattr(tick, 'volume') else 0,
                }
                
                return price_data, None
                
            finally:
                if initialized:
                    module_mt5.shutdown()
                    
        except ImportError:
            return None, 'MetaTrader5 package not installed'
        except Exception as e:
            logger.error(f"MT5 error: {e}")
            return None, str(e)


class GoldPriceManager:
    """مدیریت دریافت قیمت طلا از منابع مختلف"""
    
    def __init__(self):
        self.mt5_provider = MT5GoldPriceProvider()
    
    def get_price(self, prefer_mt5: bool = True, prefer_twelvedata: bool = False, prefer_fmp: bool = False) -> Dict[str, Any]:
        """
        دریافت قیمت طلا فقط از MetaTrader 5
        """
        result = {
            'success': False,
            'price': None,
            'source': None,
            'data': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        price_data, error = self.mt5_provider.get_price()
        if price_data:
            result['success'] = True
            result['price'] = price_data['last']
            result['source'] = 'mt5'
            result['data'] = price_data
            return result
        
        result['error'] = error or "MT5 price provider unavailable"
        return result
    
    def is_mt5_available(self) -> bool:
        """بررسی آیا MT5 در دسترس است"""
        price_data, _ = self.mt5_provider.get_price()
        return price_data is not None

    def get_price_for_user(self, provider: str, api_key: str) -> Dict[str, Any]:
        """دریافت قیمت با استفاده از API اختصاصی کاربر"""
        result = {
            'success': False,
            'price': None,
            'source': None,
            'data': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        provider_key = (provider or '').strip().lower()
        api_key = (api_key or '').strip()
        
        if not provider_key or not api_key:
            result['error'] = 'missing_credentials'
            return result
        
        price_data = None
        error = None
        
        if provider_key in ['mt5', 'meta_trader', 'metatrader5']:
            price_data, error = self.mt5_provider.get_price()
            provider_slug = 'mt5'
        else:
            result['error'] = 'unsupported_provider'
            return result
        
        if price_data:
            result['success'] = True
            result['price'] = price_data.get('last')
            result['source'] = provider_slug
            result['data'] = price_data
            return result
        
        result['error'] = error or 'provider_error'
        return result


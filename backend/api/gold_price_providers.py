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
    def get_price() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت لحظه‌ای طلا از Twelve Data"""
        try:
            api_key = os.getenv('TWELVEDATA_API_KEY')
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
    def get_realtime_quote() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت quote لحظه‌ای با جزئیات بیشتر"""
        try:
            api_key = os.getenv('TWELVEDATA_API_KEY')
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
    def get_price() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت لحظه‌ای طلا از Financial Modeling Prep"""
        try:
            # Try environment variable first, then default key
            api_key = os.getenv('FINANCIALMODELINGPREP_API_KEY') or 'CrFA9qczl3MRwERIiCGcmqloOilqkOBY'
            if not api_key:
                return None, "Financial Modeling Prep API key not configured"
            
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
                return FinancialModelingPrepProvider.get_from_commodities()
            
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
    def get_from_commodities() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """دریافت قیمت طلا از endpoint commodities"""
        try:
            # Try environment variable first, then default key
            api_key = os.getenv('FINANCIALMODELINGPREP_API_KEY') or 'CrFA9qczl3MRwERIiCGcmqloOilqkOBY'
            if not api_key:
                return None, "Financial Modeling Prep API key not configured"
            
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
            import MetaTrader5 as mt5
            
            initialized = False
            try:
                if not mt5.initialize():
                    return None, 'Failed to initialize MT5 terminal'
                initialized = True
                
                # پیدا کردن symbol صحیح
                from api.mt5_client import get_symbol_for_account, _detect_symbol_from_available
                
                # اول سعی کنیم با get_symbol_for_account
                actual_symbol = get_symbol_for_account(self.symbol)
                
                # اگر symbol انتخاب نشد، سعی کنیم نمادهای مختلف را امتحان کنیم
                if not mt5.symbol_select(actual_symbol, True):
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
                        if mt5.symbol_select(sym, True):
                            actual_symbol = sym
                            logger.info(f"Found gold symbol: {sym}")
                            break
                    else:
                        # آخرین تلاش: از _detect_symbol_from_available
                        actual_symbol = _detect_symbol_from_available(self.symbol)
                
                # Select symbol
                if not mt5.symbol_select(actual_symbol, True):
                    return None, f'Symbol {actual_symbol} not available in MT5'
                
                # Get current tick
                tick = mt5.symbol_info_tick(actual_symbol)
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
                    mt5.shutdown()
                    
        except ImportError:
            return None, 'MetaTrader5 package not installed'
        except Exception as e:
            logger.error(f"MT5 error: {e}")
            return None, str(e)


class GoldPriceManager:
    """مدیریت دریافت قیمت طلا از منابع مختلف"""
    
    def __init__(self):
        self.nerkh_provider = None
        self.mt5_provider = MT5GoldPriceProvider()
        self.twelvedata_provider = TwelveDataProvider()
        self.financialmodelingprep_provider = FinancialModelingPrepProvider()
        
        # سعی کنیم nerkh را تنظیم کنیم
        nerkh_key = os.getenv('NERKH_API_KEY')
        if nerkh_key:
            self.nerkh_provider = NerkhProvider(nerkh_key)
    
    def get_price(self, prefer_mt5: bool = False, prefer_twelvedata: bool = False, prefer_fmp: bool = False) -> Dict[str, Any]:
        """
        دریافت قیمت طلا با اولویت:
        1. Financial Modeling Prep (اگر prefer_fmp=True و API key تنظیم شده)
        2. Twelve Data (اگر prefer_twelvedata=True و API key تنظیم شده)
        3. MT5 (اگر prefer_mt5=True یا MT5 در دسترس باشد)
        4. Financial Modeling Prep (به صورت پیش‌فرض قبل از Twelve Data)
        5. Twelve Data (به صورت پیش‌فرض)
        6. API های رایگان جایگزین
        7. nerkh.io (اگر endpoint پیدا شد)
        
        Returns:
            {
                'success': bool,
                'price': float (bid, ask, last),
                'source': str,
                'data': dict,
                'error': str
            }
        """
        result = {
            'success': False,
            'price': None,
            'source': None,
            'data': None,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. اول Financial Modeling Prep را چک کنیم (اگر prefer_fmp=True)
        if prefer_fmp:
            price_data, error = self.financialmodelingprep_provider.get_price()
            if price_data:
                result['success'] = True
                result['price'] = price_data['last']
                result['source'] = 'financialmodelingprep'
                result['data'] = price_data
                return result
            elif prefer_fmp:
                result['error'] = f"Financial Modeling Prep not available: {error}"
                return result
        
        # 2. Twelve Data را چک کنیم (اگر prefer_twelvedata=True)
        if prefer_twelvedata:
            price_data, error = self.twelvedata_provider.get_realtime_quote()
            if price_data:
                result['success'] = True
                result['price'] = price_data['last']
                result['source'] = 'twelvedata'
                result['data'] = price_data
                return result
            elif prefer_twelvedata:
                result['error'] = f"TwelveData not available: {error}"
                return result
        
        # 3. MT5 را چک کنیم (اگر prefer_mt5)
        if prefer_mt5:
            price_data, error = self.mt5_provider.get_price()
            if price_data:
                result['success'] = True
                result['price'] = price_data['last']
                result['source'] = 'mt5'
                result['data'] = price_data
                return result
            else:
                result['error'] = f"MT5 not available: {error}"
                # به fallback ادامه می‌دهیم
        
        # 4. Financial Modeling Prep (به صورت پیش‌فرض)
        if not prefer_mt5:
            price_data, error = self.financialmodelingprep_provider.get_price()
            if price_data:
                result['success'] = True
                result['price'] = price_data['last']
                result['source'] = 'financialmodelingprep'
                result['data'] = price_data
                return result
        
        # 5. Twelve Data (به صورت پیش‌فرض)
        if not prefer_mt5:
            price_data, error = self.twelvedata_provider.get_realtime_quote()
            if price_data:
                result['success'] = True
                result['price'] = price_data['last']
                result['source'] = 'twelvedata'
                result['data'] = price_data
                return result
        
        # 6. API های جایگزین رایگان
        free_providers = [
            ('ExchangeRate-API', FreeAPIProvider.get_from_exchangerate_api),
            ('MetalsAPI', FreeAPIProvider.get_from_metalsapi_free),
            ('Fixer.io', FreeAPIProvider.get_from_fixer_io),
            ('OpenExchangeRates', FreeAPIProvider.get_from_openexchangerates),
        ]
        
        for name, provider_func in free_providers:
            price, error = provider_func()
            if price:
                result['success'] = True
                result['price'] = price
                result['source'] = name.lower().replace('.', '').replace('-', '_')
                result['data'] = {'price': price}
                return result
        
        # 7. nerkh.io (اگر endpoint پیدا شد)
        if self.nerkh_provider:
            price, error = self.nerkh_provider.get_price()
            if price:
                result['success'] = True
                result['price'] = price
                result['source'] = 'nerkh'
                result['data'] = {'price': price}
                return result
        
        # 8. در نهایت MT5 را امتحان کنیم (اگر هنوز امتحان نشده)
        if not prefer_mt5:
            price_data, error = self.mt5_provider.get_price()
            if price_data:
                result['success'] = True
                result['price'] = price_data['last']
                result['source'] = 'mt5'
                result['data'] = price_data
                return result
        
        # همه منابع ناموفق
        result['error'] = "All price providers failed"
        return result
    
    def is_mt5_available(self) -> bool:
        """بررسی آیا MT5 در دسترس است"""
        price_data, _ = self.mt5_provider.get_price()
        return price_data is not None


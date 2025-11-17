"""
تست جامع سیستم دریافت قیمت لحظه‌ای طلا
این تست شامل:
- Unit tests برای هر provider
- Integration tests برای GoldPriceManager
- API endpoint tests
- Error handling tests
- Fallback mechanism tests
"""

import sys
import io
import os
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
import uuid

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.gold_price_providers import (
    GoldPriceManager,
    MT5GoldPriceProvider,
    FreeAPIProvider,
    NerkhProvider
)
from api.gold_price_views import GoldPriceView
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import UserGoldAPIAccess

User = get_user_model()


class TestFreeAPIProvider(unittest.TestCase):
    """تست API های رایگان"""
    
    @patch('api.gold_price_providers.requests.get')
    def test_exchangerate_api_success(self, mock_get):
        """تست موفقیت ExchangeRate-API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rates': {'USD': 2050.50}
        }
        mock_get.return_value = mock_response
        
        price, error = FreeAPIProvider.get_from_exchangerate_api()
        
        self.assertIsNotNone(price)
        self.assertEqual(price, 2050.50)
        self.assertIsNone(error)
        mock_get.assert_called_once()
    
    @patch('api.gold_price_providers.requests.get')
    def test_exchangerate_api_failure(self, mock_get):
        """تست شکست ExchangeRate-API"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        price, error = FreeAPIProvider.get_from_exchangerate_api()
        
        self.assertIsNone(price)
        self.assertIsNotNone(error)
    
    @patch('api.gold_price_providers.requests.get')
    def test_exchangerate_api_timeout(self, mock_get):
        """تست timeout در ExchangeRate-API"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")
        
        price, error = FreeAPIProvider.get_from_exchangerate_api()
        
        self.assertIsNone(price)
        self.assertIsNotNone(error)
    
    @patch('api.gold_price_providers.requests.get')
    @patch.dict(os.environ, {'METALS_API_KEY': 'test_key'})
    def test_metalsapi_success(self, mock_get):
        """تست موفقیت MetalsAPI"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'success': True,
            'rates': {'USD': 2048.75}
        }
        mock_get.return_value = mock_response
        
        price, error = FreeAPIProvider.get_from_metalsapi_free()
        
        self.assertIsNotNone(price)
        self.assertEqual(price, 2048.75)
        self.assertIsNone(error)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_metalsapi_no_key(self):
        """تست MetalsAPI بدون API key"""
        price, error = FreeAPIProvider.get_from_metalsapi_free()
        
        self.assertIsNone(price)
        self.assertIn('not configured', error)


class TestMT5GoldPriceProvider(unittest.TestCase):
    """تست MT5 Provider"""
    
    @patch('api.gold_price_providers.mt5')
    @patch('api.gold_price_providers.get_symbol_for_account')
    def test_mt5_success(self, mock_get_symbol, mock_mt5):
        """تست موفقیت دریافت قیمت از MT5"""
        # Mock MT5 initialization
        mock_mt5.initialize.return_value = True
        mock_mt5.symbol_select.return_value = True
        
        # Mock symbol info
        mock_tick = Mock()
        mock_tick.bid = 2050.00
        mock_tick.ask = 2050.50
        mock_tick.last = 2050.25
        mock_tick.time = datetime.now().timestamp()
        mock_tick.volume = 100
        
        mock_mt5.symbol_info_tick.return_value = mock_tick
        mock_get_symbol.return_value = 'XAUUSD'
        
        provider = MT5GoldPriceProvider()
        price_data, error = provider.get_price()
        
        self.assertIsNotNone(price_data)
        self.assertEqual(price_data['bid'], 2050.00)
        self.assertEqual(price_data['ask'], 2050.50)
        self.assertEqual(price_data['last'], 2050.25)
        self.assertEqual(price_data['spread'], 0.50)
        self.assertIsNone(error)
        mock_mt5.shutdown.assert_called_once()
    
    @patch('api.gold_price_providers.mt5')
    def test_mt5_not_initialized(self, mock_mt5):
        """تست شکست initialization MT5"""
        mock_mt5.initialize.return_value = False
        
        provider = MT5GoldPriceProvider()
        price_data, error = provider.get_price()
        
        self.assertIsNone(price_data)
        self.assertIsNotNone(error)
        self.assertIn('initialize', error.lower())
    
    @patch('api.gold_price_providers.mt5')
    @patch('api.gold_price_providers.get_symbol_for_account')
    def test_mt5_symbol_not_found(self, mock_get_symbol, mock_mt5):
        """تست پیدا نشدن symbol"""
        mock_mt5.initialize.return_value = True
        mock_get_symbol.return_value = 'XAUUSD'
        mock_mt5.symbol_select.return_value = False
        
        # Mock symbol detection
        with patch('api.gold_price_providers._detect_symbol_from_available') as mock_detect:
            mock_detect.return_value = None
            provider = MT5GoldPriceProvider()
            price_data, error = provider.get_price()
            
            self.assertIsNone(price_data)
            self.assertIsNotNone(error)
    
    def test_mt5_not_installed(self):
        """تست عدم نصب MetaTrader5"""
        with patch.dict('sys.modules', {'MetaTrader5': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'MetaTrader5'")):
                provider = MT5GoldPriceProvider()
                price_data, error = provider.get_price()
                
                self.assertIsNone(price_data)
                self.assertIsNotNone(error)


class TestNerkhProvider(unittest.TestCase):
    """تست Nerkh Provider"""
    
    def test_nerkh_not_implemented(self):
        """تست Nerkh که هنوز پیاده نشده"""
        provider = NerkhProvider('test_key')
        price, error = provider.get_price()
        
        self.assertIsNone(price)
        self.assertIn('not found', error.lower())


class TestGoldPriceManager(unittest.TestCase):
    """تست GoldPriceManager - مدیریت fallback"""
    
    def setUp(self):
        """Setup برای هر تست"""
        self.manager = GoldPriceManager()
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    def test_prefer_mt5_success(self, mock_mt5_get):
        """تست اولویت MT5 با موفقیت"""
        mock_mt5_get.return_value = ({
            'bid': 2050.0,
            'ask': 2050.5,
            'last': 2050.25,
            'spread': 0.5,
            'symbol': 'XAUUSD'
        }, None)
        
        result = self.manager.get_price(prefer_mt5=True)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['source'], 'mt5')
        self.assertEqual(result['price'], 2050.25)
        self.assertIsNotNone(result['data'])
        mock_mt5_get.assert_called_once()
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    @patch.object(FreeAPIProvider, 'get_from_exchangerate_api')
    def test_fallback_to_free_api(self, mock_free_api, mock_mt5_get):
        """تست fallback به API رایگان وقتی MT5 شکست می‌خورد"""
        mock_mt5_get.return_value = (None, 'MT5 not available')
        mock_free_api.return_value = (2051.00, None)
        
        result = self.manager.get_price(prefer_mt5=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['source'], 'exchangerate_api')
        self.assertEqual(result['price'], 2051.00)
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    @patch.object(FreeAPIProvider, 'get_from_exchangerate_api')
    @patch.object(FreeAPIProvider, 'get_from_metalsapi_free')
    def test_multiple_fallback(self, mock_metals, mock_exchange, mock_mt5_get):
        """تست fallback به چندین provider"""
        mock_mt5_get.return_value = (None, 'MT5 failed')
        mock_exchange.return_value = (None, 'ExchangeRate failed')
        mock_metals.return_value = (2049.50, None)
        
        result = self.manager.get_price(prefer_mt5=False)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['source'], 'metalsapi')
        self.assertEqual(result['price'], 2049.50)
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    @patch.object(FreeAPIProvider, 'get_from_exchangerate_api')
    @patch.object(FreeAPIProvider, 'get_from_metalsapi_free')
    @patch.object(FreeAPIProvider, 'get_from_fixer_io')
    @patch.object(FreeAPIProvider, 'get_from_openexchangerates')
    def test_all_providers_fail(self, mock_open, mock_fixer, mock_metals, 
                                mock_exchange, mock_mt5_get):
        """تست وقتی همه providers شکست می‌خورند"""
        mock_mt5_get.return_value = (None, 'MT5 failed')
        mock_exchange.return_value = (None, 'ExchangeRate failed')
        mock_metals.return_value = (None, 'MetalsAPI failed')
        mock_fixer.return_value = (None, 'Fixer failed')
        mock_open.return_value = (None, 'OpenExchange failed')
        
        result = self.manager.get_price(prefer_mt5=False)
        
        self.assertFalse(result['success'])
        self.assertIsNone(result['price'])
        self.assertIsNotNone(result['error'])
        self.assertIn('failed', result['error'].lower())
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    def test_is_mt5_available_true(self, mock_mt5_get):
        """تست بررسی دسترسی MT5 - موفق"""
        mock_mt5_get.return_value = ({'last': 2050.0}, None)
        
        result = self.manager.is_mt5_available()
        
        self.assertTrue(result)
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    def test_is_mt5_available_false(self, mock_mt5_get):
        """تست بررسی دسترسی MT5 - ناموفق"""
        mock_mt5_get.return_value = (None, 'MT5 not available')
        
        result = self.manager.is_mt5_available()
        
        self.assertFalse(result)
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    @patch.object(FreeAPIProvider, 'get_from_exchangerate_api')
    def test_timestamp_in_result(self, mock_free_api, mock_mt5_get):
        """تست وجود timestamp در نتیجه"""
        mock_mt5_get.return_value = (None, 'MT5 failed')
        mock_free_api.return_value = (2050.0, None)
        
        result = self.manager.get_price(prefer_mt5=False)
        
        self.assertIn('timestamp', result)
        self.assertIsNotNone(result['timestamp'])
        # بررسی فرمت ISO
        try:
            datetime.fromisoformat(result['timestamp'])
        except ValueError:
            self.fail("Timestamp is not in ISO format")


class TestGoldPriceView(unittest.TestCase):
    """تست API View"""
    
    def setUp(self):
        """Setup برای هر تست"""
        self.factory = APIRequestFactory()
        self.view = GoldPriceView.as_view()
    
    @patch('api.gold_price_views.gold_price_manager')
    def test_admin_access_success(self, mock_manager):
        """ادمین باید بتواند قیمت را دریافت کند"""
        admin_user = User.objects.create_user(
            username=f'admin_user_{uuid.uuid4().hex}',
            email=f'admin_{uuid.uuid4().hex}@example.com',
            password='testpass123',
            is_staff=True
        )
        
        mock_manager.get_price.return_value = {
            'success': True,
            'price': 2050.25,
            'source': 'mt5',
            'data': {'bid': 2050.0, 'ask': 2050.5, 'last': 2050.25},
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = admin_user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['access_type'], 'admin')
        self.assertTrue(response.data.get('allow_mt5_access'))
        mock_manager.get_price.assert_called_once()
    
    @patch('api.gold_price_views.gold_price_manager')
    def test_admin_access_error(self, mock_manager):
        """اگر دریافت قیمت برای ادمین شکست بخورد باید 500 برگردد"""
        admin_user = User.objects.create_user(
            username=f'admin_error_{uuid.uuid4().hex}',
            email=f'admin_error_{uuid.uuid4().hex}@example.com',
            password='testpass123',
            is_staff=True
        )
        
        mock_manager.get_price.return_value = {
            'success': False,
            'error': 'All providers failed',
            'price': None,
            'source': None,
            'data': None,
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = admin_user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'price_fetch_error')
    
    def test_user_without_credentials(self):
        """کاربر عادی بدون API باید 403 دریافت کند"""
        user = User.objects.create_user(
            username=f'normal_user_{uuid.uuid4().hex}',
            email=f'normal_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'admin_only')
        self.assertFalse(response.data.get('allow_mt5_access', True))
    
    @patch('api.gold_price_views.gold_price_manager')
    def test_user_with_credentials_success(self, mock_manager):
        """کاربر با API شخصی باید بتواند قیمت دریافت کند"""
        user = User.objects.create_user(
            username=f'api_user_{uuid.uuid4().hex}',
            email=f'api_user_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        UserGoldAPIAccess.objects.create(
            user=user,
            provider='twelvedata',
            api_key='test-key',
            is_active=True
        )
        
        mock_manager.get_price_for_user.return_value = {
            'success': True,
            'price': 2049.5,
            'source': 'twelvedata',
            'data': {'last': 2049.5},
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['access_type'], 'user_api')
        self.assertEqual(response.data['provider'], 'twelvedata')
        self.assertFalse(response.data.get('allow_mt5_access', True))
        mock_manager.get_price_for_user.assert_called_once_with('twelvedata', 'test-key')
    
    @patch('api.gold_price_views.gold_price_manager')
    def test_user_with_credentials_error(self, mock_manager):
        """اگر دریافت قیمت با API کاربر شکست بخورد باید خطا برگردد"""
        user = User.objects.create_user(
            username=f'api_user_error_{uuid.uuid4().hex}',
            email=f'api_user_error_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        UserGoldAPIAccess.objects.create(
            user=user,
            provider='twelvedata',
            api_key='test-key',
            is_active=True
        )
        
        mock_manager.get_price_for_user.return_value = {
            'success': False,
            'error': 'provider_error',
            'price': None,
            'source': None,
            'data': None,
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'user_api_error')
        self.assertFalse(response.data.get('allow_mt5_access', True))

    @patch('api.gold_price_views.gold_price_manager')
    def test_user_with_mt5_delegate_success(self, mock_manager):
        """کاربری که توسط ادمین مجاز شده باید بتواند قیمت MT5 را دریافت کند"""
        user = User.objects.create_user(
            username=f'mt5_delegate_{uuid.uuid4().hex}',
            email=f'mt5_delegate_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        UserGoldAPIAccess.objects.create(
            user=user,
            provider='',
            api_key='',
            allow_mt5_access=True,
            is_active=True
        )

        mock_manager.get_price.return_value = {
            'success': True,
            'price': 2051.0,
            'source': 'mt5',
            'data': {'last': 2051.0},
            'timestamp': datetime.now().isoformat()
        }

        request = self.factory.get('/api/gold-price/')
        request.user = user

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['access_type'], 'mt5_delegate')
        self.assertTrue(response.data.get('allow_mt5_access'))
        self.assertTrue(response.data.get('mt5_used'))
        self.assertFalse(response.data.get('has_credentials'))
        self.assertEqual(mock_manager.get_price.call_count, 1)
        first_call_kwargs = mock_manager.get_price.call_args_list[0].kwargs
        self.assertTrue(first_call_kwargs.get('prefer_mt5'))

    @patch('api.gold_price_views.gold_price_manager')
    def test_user_with_mt5_delegate_fallback(self, mock_manager):
        """اگر دسترسی MT5 شکست بخورد باید fallback اجرا شود"""
        user = User.objects.create_user(
            username=f'mt5_delegate_fallback_{uuid.uuid4().hex}',
            email=f'mt5_delegate_fallback_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        UserGoldAPIAccess.objects.create(
            user=user,
            provider='',
            api_key='',
            allow_mt5_access=True,
            is_active=True
        )

        mock_manager.get_price.side_effect = [
            {
                'success': False,
                'price': None,
                'source': None,
                'data': None,
                'error': 'mt5_down',
                'timestamp': datetime.now().isoformat()
            },
            {
                'success': True,
                'price': 2048.5,
                'source': 'financialmodelingprep',
                'data': {'last': 2048.5},
                'timestamp': datetime.now().isoformat()
            },
        ]

        request = self.factory.get('/api/gold-price/')
        request.user = user

        response = self.view(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['access_type'], 'mt5_delegate')
        self.assertTrue(response.data.get('allow_mt5_access'))
        self.assertFalse(response.data.get('mt5_used'))
        self.assertEqual(mock_manager.get_price.call_count, 2)
        first_call_kwargs = mock_manager.get_price.call_args_list[0].kwargs
        second_call_kwargs = mock_manager.get_price.call_args_list[1].kwargs
        self.assertTrue(first_call_kwargs.get('prefer_mt5'))
        self.assertEqual(second_call_kwargs, {})


class TestMarketDataView(unittest.TestCase):
    """تست محدودیت‌های دسترسی به داده‌های MT5"""

    def setUp(self):
        from api.views import MarketDataView  # noqa: WPS433 - imported lazily after Django setup
        self.view = MarketDataView.as_view()
        self.client = APIClient()
        self.market_url = '/api/market/mt5_candles/?source=mt5_candles'
        self.host_kwargs = {'HTTP_HOST': 'localhost'}

    def tearDown(self):
        # Ensure client authentication state is cleared between tests
        self.client.force_authenticate(user=None)

    def test_mt5_requires_authentication(self):
        response = self.client.get(self.market_url, **self.host_kwargs)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    @patch('api.views.fetch_mt5_candles')
    def test_mt5_denied_for_regular_user(self, mock_fetch):
        user = User.objects.create_user(
            username=f'mt5_user_{uuid.uuid4().hex}',
            email=f'mt5_user_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        response = self.client.get(self.market_url, **self.host_kwargs)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('MetaTrader 5', response.data.get('message', ''))
        mock_fetch.assert_not_called()

    @patch('api.views.fetch_mt5_candles')
    def test_mt5_allowed_for_delegate_user(self, mock_fetch):
        user = User.objects.create_user(
            username=f'mt5_delegate_{uuid.uuid4().hex}',
            email=f'mt5_delegate_{uuid.uuid4().hex}@example.com',
            password='testpass123'
        )
        UserGoldAPIAccess.objects.create(
            user=user,
            provider='financialmodelingprep',
            api_key='dummy',
            allow_mt5_access=True,
            is_active=True
        )
        mock_df = MagicMock()
        mock_df.empty = False
        now = datetime.now()
        mock_df.iterrows.return_value = [
            (now, {'open': 2000.0, 'high': 2005.0, 'low': 1995.0, 'close': 2002.5, 'volume': 150.0})
        ]
        mock_fetch.return_value = (mock_df, None)

        self.client.force_authenticate(user=user)
        response = self.client.get(self.market_url, **self.host_kwargs)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['source'], 'mt5')
        self.assertEqual(response.data['count'], 1)
        mock_fetch.assert_called_once()

    @patch('api.views.fetch_mt5_candles')
    def test_mt5_allowed_for_admin(self, mock_fetch):
        admin_user = User.objects.create_user(
            username=f'mt5_admin_{uuid.uuid4().hex}',
            email=f'mt5_admin_{uuid.uuid4().hex}@example.com',
            password='testpass123',
            is_staff=True
        )
        mock_df = MagicMock()
        mock_df.empty = False
        now = datetime.now()
        mock_df.iterrows.return_value = [
            (now, {'open': 2001.0, 'high': 2006.0, 'low': 1996.0, 'close': 2003.0, 'volume': 160.0})
        ]
        mock_fetch.return_value = (mock_df, None)

        self.client.force_authenticate(user=admin_user)
        response = self.client.get(self.market_url, **self.host_kwargs)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['source'], 'mt5')
        mock_fetch.assert_called_once()


class TestPerformance(unittest.TestCase):
    """تست عملکرد و performance"""
    
    @patch.object(MT5GoldPriceProvider, 'get_price')
    def test_response_time(self, mock_mt5_get):
        """تست زمان پاسخ (باید سریع باشد)"""
        import time
        
        mock_mt5_get.return_value = ({
            'last': 2050.0
        }, None)
        
        manager = GoldPriceManager()
        
        start_time = time.time()
        result = manager.get_price(prefer_mt5=True)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertTrue(result['success'])
        # باید در کمتر از 1 ثانیه پاسخ دهد
        self.assertLess(response_time, 1.0, 
                       f"Response time too slow: {response_time:.3f}s")
    
    @patch.object(FreeAPIProvider, 'get_from_exchangerate_api')
    def test_concurrent_requests(self, mock_api):
        """تست درخواست‌های همزمان"""
        import threading
        
        mock_api.return_value = (2050.0, None)
        
        results = []
        errors = []
        
        def make_request():
            try:
                manager = GoldPriceManager()
                result = manager.get_price(prefer_mt5=False)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        for result in results:
            self.assertTrue(result['success'])


def run_tests():
    """اجرای تمام تست‌ها"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # اضافه کردن تمام تست کلاس‌ها
    suite.addTests(loader.loadTestsFromTestCase(TestFreeAPIProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestMT5GoldPriceProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestNerkhProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestGoldPriceManager))
    suite.addTests(loader.loadTestsFromTestCase(TestGoldPriceView))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("[COMPREHENSIVE GOLD PRICE TESTS]")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print(f"[SUMMARY]")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("=" * 70)
    
    if result.failures:
        print("\n[FAILURES]")
        for test, traceback in result.failures:
            print(f"\n{test}:")
            print(traceback)
    
    if result.errors:
        print("\n[ERRORS]")
        for test, traceback in result.errors:
            print(f"\n{test}:")
            print(traceback)


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
from rest_framework.test import APIRequestFactory
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import GoldPriceSubscription

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
    
    @patch('api.gold_price_views.is_mt5_available')
    @patch('api.gold_price_views.gold_price_manager')
    def test_view_with_mt5_access(self, mock_manager, mock_mt5_avail):
        """تست view با دسترسی MT5"""
        # ایجاد کاربر تست
        user = User.objects.create_user(
            username='test_mt5_user',
            email='test_mt5@example.com',
            password='testpass123'
        )
        
        # Mock MT5
        mock_mt5_avail.return_value = (True, None)
        mock_manager.get_price.return_value = {
            'success': True,
            'price': 2050.25,
            'source': 'mt5',
            'data': {'bid': 2050.0, 'ask': 2050.5, 'last': 2050.25},
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['access_type'], 'mt5')
        self.assertTrue(response.data['has_mt5'])
    
    @patch('api.gold_price_views.is_mt5_available')
    @patch('api.gold_price_views.gold_price_manager')
    def test_view_with_subscription(self, mock_manager, mock_mt5_avail):
        """تست view با اشتراک فعال"""
        from django.utils import timezone
        from datetime import timedelta
        
        user = User.objects.create_user(
            username='test_sub_user',
            email='test_sub@example.com',
            password='testpass123'
        )
        
        # ایجاد اشتراک فعال
        subscription = GoldPriceSubscription.objects.create(
            user=user,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=29)
        )
        
        mock_mt5_avail.return_value = (False, 'MT5 not available')
        mock_manager.get_price.return_value = {
            'success': True,
            'price': 2049.50,
            'source': 'exchangerate_api',
            'data': {'price': 2049.50},
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['access_type'], 'subscription')
        self.assertTrue(response.data['has_subscription'])
    
    @patch('api.gold_price_views.is_mt5_available')
    def test_view_no_access(self, mock_mt5_avail):
        """تست view بدون دسترسی (نه MT5 و نه اشتراک)"""
        user = User.objects.create_user(
            username='test_no_access',
            email='test_noaccess@example.com',
            password='testpass123'
        )
        
        mock_mt5_avail.return_value = (False, 'MT5 not available')
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'access_denied')
    
    @patch('api.gold_price_views.is_mt5_available')
    @patch('api.gold_price_views.gold_price_manager')
    def test_view_price_fetch_error(self, mock_manager, mock_mt5_avail):
        """تست view وقتی دریافت قیمت شکست می‌خورد"""
        user = User.objects.create_user(
            username='test_error',
            email='test_error@example.com',
            password='testpass123'
        )
        
        mock_mt5_avail.return_value = (True, None)
        mock_manager.get_price.return_value = {
            'success': False,
            'error': 'All providers failed',
            'price': None,
            'source': None,
            'data': None,
            'timestamp': datetime.now().isoformat()
        }
        
        request = self.factory.get('/api/gold-price/')
        request.user = user
        
        response = self.view(request)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error'], 'price_fetch_error')


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


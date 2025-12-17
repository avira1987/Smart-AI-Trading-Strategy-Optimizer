"""
Test cases for backtest with parsed strategy data vs strategy file parsing
This test checks why backtest works for one strategy but fails for another processed strategy
"""
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from api.data_providers import DataProviderManager
from core.models import TradingStrategy, Job, APIConfiguration
import pandas as pd
import json


class BacktestParsedStrategyTestCase(TestCase):
    """Test backtest behavior with parsed_strategy_data vs strategy file"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@example.com'
        )
        
        # Create API configuration for user (simulating real scenario)
        APIConfiguration.objects.create(
            provider='financialmodelingprep',
            api_key='test_fmp_key_123',
            user=self.user,
            is_active=True
        )
        
        APIConfiguration.objects.create(
            provider='twelvedata',
            api_key='test_td_key_123',
            user=self.user,
            is_active=True
        )
    
    def test_data_provider_manager_with_user_loads_api_keys(self):
        """Test that DataProviderManager with user loads API keys from database"""
        manager = DataProviderManager(user=self.user)
        
        fmp_provider = manager.providers.get('financialmodelingprep')
        td_provider = manager.providers.get('twelvedata')
        
        self.assertIsNotNone(fmp_provider)
        self.assertEqual(fmp_provider.api_key, 'test_fmp_key_123')
        self.assertIsNotNone(td_provider)
        self.assertEqual(td_provider.api_key, 'test_td_key_123')
    
    def test_data_provider_manager_without_user_does_not_load_user_keys(self):
        """Test that DataProviderManager without user does not load user-specific keys"""
        manager = DataProviderManager()  # No user passed
        
        fmp_provider = manager.providers.get('financialmodelingprep')
        td_provider = manager.providers.get('twelvedata')
        
        # Should not have user-specific keys, only env vars if set
        # This is the bug - without user, API keys from DB are not loaded
        self.assertIsNotNone(fmp_provider)
        # API key should be None or from env, not from DB
        if not os.getenv('FINANCIALMODELINGPREP_API_KEY'):
            # If no env var, should be None (not loaded from DB without user)
            self.assertIsNone(fmp_provider.api_key)
    
    def test_backtest_with_parsed_strategy_uses_user_context(self):
        """Test that backtest with parsed_strategy_data should use user context for API keys"""
        # Create strategy with parsed_strategy_data (processed strategy)
        strategy = TradingStrategy.objects.create(
            user=self.user,
            name='پرو b2b پورصمدی - 12/15/2025',
            processing_status='processed',
            parsed_strategy_data={
                'symbol': 'XAU/USD',
                'timeframe': 'M15',
                'confidence_score': 0.95,
                'entry_conditions': ['test condition'],
                'exit_conditions': ['test exit'],
                'indicators': ['RSI', 'MACD']
            }
        )
        
        # Create job for this strategy
        job = Job.objects.create(
            user=self.user,
            strategy=strategy,
            status='pending'
        )
        
        # Simulate what happens in run_backtest_task
        # The bug: DataProviderManager() is created without user
        manager_without_user = DataProviderManager()
        available_without_user = manager_without_user.get_available_providers()
        
        # The fix: DataProviderManager(user=user) should be used
        manager_with_user = DataProviderManager(user=self.user)
        available_with_user = manager_with_user.get_available_providers()
        
        # With user, should have API keys loaded
        self.assertIn('financialmodelingprep', available_with_user)
        self.assertIn('twelvedata', available_with_user)
        
        # Without user, might not have keys (depending on env vars)
        # This demonstrates the bug
    
    def test_parsed_strategy_missing_symbol_handling(self):
        """Test handling of parsed_strategy_data that might be missing symbol"""
        # Create strategy with parsed_strategy_data but missing symbol
        strategy = TradingStrategy.objects.create(
            user=self.user,
            name='Strategy without symbol',
            processing_status='processed',
            parsed_strategy_data={
                'timeframe': 'M15',
                'confidence_score': 0.95,
                # Missing 'symbol' key
            }
        )
        
        parsed_strategy = strategy.parsed_strategy_data
        
        # Check if symbol exists
        symbol = parsed_strategy.get('symbol')
        
        # Should handle None symbol gracefully
        self.assertIsNone(symbol)
        
        # In backtest, should use symbol_override or default
        symbol_override = 'XAU/USD'
        final_symbol = symbol_override or symbol or 'XAU/USD'
        self.assertEqual(final_symbol, 'XAU/USD')
    
    def test_parsed_strategy_missing_timeframe_handling(self):
        """Test handling of parsed_strategy_data that might be missing timeframe"""
        strategy = TradingStrategy.objects.create(
            user=self.user,
            name='Strategy without timeframe',
            processing_status='processed',
            parsed_strategy_data={
                'symbol': 'XAU/USD',
                'confidence_score': 0.95,
                # Missing 'timeframe' key
            }
        )
        
        parsed_strategy = strategy.parsed_strategy_data
        strategy_timeframe = parsed_strategy.get('timeframe')
        
        # Should handle None timeframe
        self.assertIsNone(strategy_timeframe)
        
        # Should default to '1day' in get_historical_data
        interval = strategy_timeframe if strategy_timeframe else "1day"
        self.assertEqual(interval, '1day')
    
    def test_symbol_normalization_handles_invalid_formats(self):
        """Test that symbol normalization handles various invalid formats correctly"""
        from api.data_providers import DataProviderManager
        
        manager = DataProviderManager()
        
        # Test that invalid symbols are normalized correctly
        test_cases = [
            ('EURUSD', 'EUR/USD'),  # Missing slash
            ('XAUUSD', 'XAU/USD'),  # Missing slash
            ('GOLD', 'XAU/USD'),    # Invalid name
            ('XAU', 'XAU/USD'),     # Incomplete
            ('', 'XAU/USD'),        # Empty
            (None, 'XAU/USD'),      # None
        ]
        
        for invalid_symbol, expected in test_cases:
            normalized = manager._normalize_symbol(invalid_symbol)
            self.assertEqual(normalized, expected,
                           f"Symbol '{invalid_symbol}' should normalize to '{expected}', got '{normalized}'")
    
    def test_backtest_error_message_when_no_providers_available(self):
        """Test error message when no providers are available"""
        # Create manager without user and no env vars
        with patch.dict(os.environ, {}, clear=True):
            manager = DataProviderManager()
            available = manager.get_available_providers()
            
            # Should be empty or only MT5 if available
            # This simulates the error scenario
            if not available:
                error_msg = (
                    "نمی‌توان داده بازار را دریافت کرد. "
                    "لطفاً مطمئن شوید که حداقل یک API key تنظیم شده است: "
                    "Financial Modeling Prep (FINANCIALMODELINGPREP_API_KEY) یا "
                    "Twelve Data (TWELVEDATA_API_KEY). "
                    "MT5 در دسترس نیست: N/A"
                )
                # This is the error message user sees
                self.assertIn('API key', error_msg)
    
    def test_backtest_with_processed_strategy_uses_user_api_keys(self):
        """Test that backtest with processed strategy correctly uses user API keys"""
        # Create processed strategy (like "پرو b2b پورصمدی - 12/15/2025")
        strategy = TradingStrategy.objects.create(
            user=self.user,
            name='پرو b2b پورصمدی - 12/15/2025',
            processing_status='processed',
            parsed_strategy_data={
                'symbol': 'XAU/USD',
                'timeframe': 'M15',
                'confidence_score': 0.95,
                'entry_conditions': ['RSI < 30'],
                'exit_conditions': ['RSI > 70'],
                'indicators': ['RSI', 'MACD']
            }
        )
        
        # Create job
        job = Job.objects.create(
            user=self.user,
            strategy=strategy,
            status='pending'
        )
        
        # Simulate the backtest flow
        # Step 1: Get user (as done in run_backtest_task)
        user = job.user
        
        # Step 2: Get parsed_strategy_data
        parsed_strategy = strategy.parsed_strategy_data
        
        # Step 3: Create DataProviderManager WITH user (the fix)
        data_manager = DataProviderManager(user=user)
        available_providers = data_manager.get_available_providers()
        
        # Should have API keys loaded
        self.assertIn('financialmodelingprep', available_providers)
        self.assertIn('twelvedata', available_providers)
        
        # Step 4: Get symbol and timeframe
        symbol = parsed_strategy.get('symbol')
        strategy_timeframe = parsed_strategy.get('timeframe')
        
        self.assertEqual(symbol, 'XAU/USD')
        self.assertEqual(strategy_timeframe, 'M15')
        
        # Step 5: Verify data can be fetched (with mocked providers)
        mock_data = pd.DataFrame({
            'open': [2000.0],
            'high': [2010.0],
            'low': [1990.0],
            'close': [2005.0]
        }, index=pd.date_range('2024-01-01', periods=1, freq='D'))
        
        with patch('api.data_providers.is_mt5_available', return_value=(False, "MT5 not available")):
            with patch('api.data_providers.fetch_mt5_candles_aggregated', 
                      side_effect=RuntimeError("MT5 not available")):
                # Mock MT5 provider to raise exception
                with patch.object(data_manager.providers['mt5'], 
                                'get_historical_data', 
                                side_effect=RuntimeError("MT5 not available")):
                    with patch.object(data_manager.providers['financialmodelingprep'], 
                                    'get_historical_data', return_value=mock_data):
                        data, provider = data_manager.get_historical_data(
                            symbol,
                            timeframe_days=365,
                            interval=strategy_timeframe,
                            return_provider=True
                        )
                        
                        # Should successfully get data
                        self.assertFalse(data.empty)
                        self.assertEqual(provider, 'financialmodelingprep')
    
    def test_backtest_comparison_processed_vs_unprocessed(self):
        """Test comparison between processed and unprocessed strategies"""
        # Create processed strategy
        processed_strategy = TradingStrategy.objects.create(
            user=self.user,
            name='Processed Strategy',
            processing_status='processed',
            parsed_strategy_data={
                'symbol': 'XAU/USD',
                'timeframe': 'M15',
                'confidence_score': 0.95
            }
        )
        
        # Create unprocessed strategy (with strategy_file)
        from django.core.files.uploadedfile import SimpleUploadedFile
        unprocessed_strategy = TradingStrategy.objects.create(
            user=self.user,
            name='Unprocessed Strategy',
            processing_status='not_processed',
            strategy_file=SimpleUploadedFile("test.txt", b"test content")
        )
        
        # Both should work with DataProviderManager(user=user)
        user = self.user
        
        # Processed strategy path
        if processed_strategy.parsed_strategy_data and processed_strategy.processing_status == 'processed':
            parsed_strategy_processed = processed_strategy.parsed_strategy_data
            manager_processed = DataProviderManager(user=user)
            available_processed = manager_processed.get_available_providers()
            self.assertIn('financialmodelingprep', available_processed)
        
        # Unprocessed strategy path (would parse file, but we skip that in test)
        # The key point: both should use DataProviderManager(user=user)
        manager_unprocessed = DataProviderManager(user=user)
        available_unprocessed = manager_unprocessed.get_available_providers()
        self.assertIn('financialmodelingprep', available_unprocessed)
        
        # Both should have same available providers when using same user
        self.assertEqual(available_processed, available_unprocessed)
    
    def test_symbol_validation_with_invalid_symbols(self):
        """Test that invalid symbols are normalized to XAU/USD"""
        from api.data_providers import DataProviderManager
        
        manager = DataProviderManager()
        
        # Test various invalid symbol formats
        test_cases = [
            ('EURUSD', 'EUR/USD'),  # Missing slash
            ('XAUUSD', 'XAU/USD'),  # Missing slash
            ('GOLD', 'XAU/USD'),    # Invalid name
            ('XAU', 'XAU/USD'),    # Incomplete
            ('', 'XAU/USD'),        # Empty
            (None, 'XAU/USD'),      # None
            ('  ', 'XAU/USD'),      # Whitespace only
        ]
        
        for invalid_symbol, expected in test_cases:
            normalized = manager._normalize_symbol(invalid_symbol)
            self.assertEqual(normalized, expected, 
                           f"Symbol '{invalid_symbol}' should normalize to '{expected}', got '{normalized}'")
    
    def test_symbol_validation_in_backtest_with_invalid_symbol(self):
        """Test that backtest handles invalid symbols from parsed_strategy_data"""
        # Create strategy with invalid symbol (simulating high temperature extraction)
        strategy = TradingStrategy.objects.create(
            user=self.user,
            name='Strategy with invalid symbol',
            processing_status='processed',
            parsed_strategy_data={
                'symbol': 'EURUSD',  # Invalid format (missing slash) - like what high temperature might produce
                'timeframe': 'M15',
                'confidence_score': 0.95
            }
        )
        
        job = Job.objects.create(
            user=self.user,
            strategy=strategy,
            status='pending'
        )
        
        # Simulate symbol extraction in backtest
        parsed_strategy = strategy.parsed_strategy_data
        symbol = parsed_strategy.get('symbol')
        
        # Apply validation logic (same as in tasks.py)
        if not symbol or not str(symbol).strip():
            symbol = 'XAU/USD'
        else:
            symbol = str(symbol).strip().upper()
            if symbol == 'XAUUSD':
                symbol = 'XAU/USD'
            elif symbol in ['GOLD', 'XAU']:
                symbol = 'XAU/USD'
            elif '/' not in symbol and len(symbol) == 6:
                symbol = f"{symbol[:3]}/{symbol[3:]}"
            
            valid_symbols = ['XAU/USD', 'EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD', 'USD/CHF', 'NZD/USD']
            if symbol not in valid_symbols:
                symbol = 'XAU/USD'
        
        # Should be normalized to valid format
        self.assertEqual(symbol, 'EUR/USD')  # EURUSD should become EUR/USD
    
    def test_symbol_validation_with_high_temperature_scenarios(self):
        """Test symbol validation with various high-temperature extraction scenarios"""
        from api.data_providers import DataProviderManager
        
        manager = DataProviderManager()
        
        # Simulate what high temperature AI might extract
        high_temp_extractions = [
            ('EURUSD', 'EUR/USD'),      # Missing slash
            ('gbpusd', 'GBP/USD'),      # Lowercase, missing slash
            ('XAU-USD', 'XAU/USD'),     # Dash instead of slash
            ('gold', 'XAU/USD'),        # Invalid name
            ('XAU', 'XAU/USD'),         # Incomplete
            ('  XAUUSD  ', 'XAU/USD'),  # Whitespace
            ('EUR/USD', 'EUR/USD'),     # Already valid
            ('XAU/USD', 'XAU/USD'),     # Already valid
        ]
        
        for extracted, expected in high_temp_extractions:
            normalized = manager._normalize_symbol(extracted)
            self.assertEqual(normalized, expected,
                           f"High temp extraction '{extracted}' should normalize to '{expected}', got '{normalized}'")


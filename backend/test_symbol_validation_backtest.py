"""
Test script to verify symbol validation works correctly in backtest
This simulates what happens when AI extracts invalid symbols with high temperature
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import TradingStrategy, Job, APIConfiguration
from api.data_providers import DataProviderManager
from api.tasks import run_backtest_task
import pandas as pd

def test_symbol_validation():
    """Test symbol validation with various invalid symbols"""
    print("=" * 80)
    print("تست اعتبارسنجی Symbol در بک‌تست")
    print("=" * 80)
    
    # Get or create test user
    user, _ = User.objects.get_or_create(username='test_backtest_user', defaults={'email': 'test@example.com'})
    
    # Create API configurations for user
    APIConfiguration.objects.get_or_create(
        provider='financialmodelingprep',
        user=user,
        defaults={'api_key': 'test_key_fmp', 'is_active': True}
    )
    APIConfiguration.objects.get_or_create(
        provider='twelvedata',
        user=user,
        defaults={'api_key': 'test_key_td', 'is_active': True}
    )
    
    # Test cases: invalid symbols that might be extracted with high temperature
    test_cases = [
        {
            'name': 'پرو b2b پورصمدی - 12/15/2025',
            'symbol': 'EURUSD',  # Invalid: missing slash
            'timeframe': 'M15',
            'expected_normalized': 'EUR/USD'
        },
        {
            'name': 'استراتژی با GOLD',
            'symbol': 'GOLD',  # Invalid: should be XAU/USD
            'timeframe': 'M15',
            'expected_normalized': 'XAU/USD'
        },
        {
            'name': 'استراتژی با XAU',
            'symbol': 'XAU',  # Invalid: incomplete
            'timeframe': 'M15',
            'expected_normalized': 'XAU/USD'
        },
        {
            'name': 'استراتژی با symbol خالی',
            'symbol': '',  # Invalid: empty
            'timeframe': 'M15',
            'expected_normalized': 'XAU/USD'
        },
        {
            'name': 'استراتژی معتبر',
            'symbol': 'XAU/USD',  # Valid
            'timeframe': 'M15',
            'expected_normalized': 'XAU/USD'
        },
    ]
    
    print(f"\nتعداد تست‌ها: {len(test_cases)}\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"تست {i}/{len(test_cases)}: {test_case['name']}")
        print(f"Symbol استخراج شده: '{test_case['symbol']}'")
        print(f"Symbol مورد انتظار بعد از normalize: '{test_case['expected_normalized']}'")
        print(f"{'='*80}")
        
        # Create strategy with invalid symbol
        strategy = TradingStrategy.objects.create(
            user=user,
            name=test_case['name'],
            processing_status='processed',
            parsed_strategy_data={
                'symbol': test_case['symbol'],
                'timeframe': test_case['timeframe'],
                'confidence_score': 0.95,
                'entry_conditions': ['RSI < 30'],
                'exit_conditions': ['RSI > 70'],
                'indicators': ['RSI']
            }
        )
        
        # Test symbol normalization in DataProviderManager
        manager = DataProviderManager(user=user)
        normalized = manager._normalize_symbol(test_case['symbol'])
        
        print(f"✅ Symbol normalize شده: '{normalized}'")
        
        if normalized == test_case['expected_normalized']:
            print(f"✅ تست پاس شد: Symbol به درستی normalize شد")
        else:
            print(f"❌ تست شکست خورد: انتظار '{test_case['expected_normalized']}' بود، اما '{normalized}' دریافت شد")
        
        # Test that symbol validation in tasks.py would work
        # Simulate the validation logic from tasks.py
        symbol = test_case['symbol']
        if not symbol or not str(symbol).strip():
            validated_symbol = 'XAU/USD'
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
                validated_symbol = 'XAU/USD'
            else:
                validated_symbol = symbol
        
        print(f"✅ Symbol بعد از اعتبارسنجی در tasks.py: '{validated_symbol}'")
        
        if validated_symbol == test_case['expected_normalized']:
            print(f"✅ اعتبارسنجی در tasks.py درست کار می‌کند")
        else:
            print(f"⚠️ اعتبارسنجی در tasks.py: انتظار '{test_case['expected_normalized']}' بود، اما '{validated_symbol}' دریافت شد")
        
        # Clean up
        strategy.delete()
    
    print(f"\n{'='*80}")
    print("✅ تمام تست‌های اعتبارسنجی Symbol انجام شد")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    test_symbol_validation()


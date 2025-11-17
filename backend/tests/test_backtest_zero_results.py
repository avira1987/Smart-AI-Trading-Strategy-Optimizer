"""
Test file to diagnose why backtests return zero results
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ai_module.backtest_engine import BacktestEngine
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_data(n_days=365):
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=n_days, freq='D')
    
    # Generate realistic price data
    np.random.seed(42)
    base_price = 1.1000
    returns = np.random.randn(n_days) * 0.01
    prices = [base_price]
    
    for ret in returns:
        prices.append(prices[-1] * (1 + ret))
    
    prices = prices[1:]
    
    data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(n_days) * 0.002),
        'high': prices * (1 + abs(np.random.randn(n_days)) * 0.005),
        'low': prices * (1 - abs(np.random.randn(n_days)) * 0.005),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n_days)
    }, index=dates)
    
    return data

def test_basic_strategy():
    """Test with a simple RSI-based strategy"""
    logger.info("=" * 80)
    logger.info("Test 1: Basic RSI Strategy")
    logger.info("=" * 80)
    
    data = create_sample_data(365)
    
    # Create a simple strategy
    strategy = {
        'entry_conditions': ['RSI below 30'],
        'exit_conditions': ['RSI above 70'],
        'indicators': ['rsi'],
        'raw_excerpt': 'Buy when RSI is below 30, sell when RSI is above 70'
    }
    
    engine = BacktestEngine(initial_capital=10000)
    result = engine.run_backtest(data, strategy, 'EUR/USD')
    
    logger.info(f"Result: {result}")
    logger.info(f"Total trades: {result.get('total_trades', 0)}")
    logger.info(f"Total return: {result.get('total_return', 0):.2f}%")
    logger.info(f"Trades list: {len(result.get('trades', []))}")
    
    assert result.get('total_trades', 0) > 0, "Expected at least one trade, got 0"
    logger.info("✅ Test 1 PASSED")
    return result

def test_signals_generation():
    """Test signal generation separately"""
    logger.info("=" * 80)
    logger.info("Test 2: Signal Generation")
    logger.info("=" * 80)
    
    from ai_module.technical_indicators import calculate_all_indicators
    
    data = create_sample_data(365)
    data = calculate_all_indicators(data)
    
    strategy = {
        'entry_conditions': ['RSI below 30'],
        'exit_conditions': ['RSI above 70'],
        'indicators': ['rsi'],
        'raw_excerpt': 'Buy when RSI is below 30, sell when RSI is above 70'
    }
    
    engine = BacktestEngine(initial_capital=10000)
    signals, signal_reasons = engine._generate_signals(data, strategy)
    
    buy_signals = int((signals == 1).sum())
    sell_signals = int((signals == -1).sum())
    
    logger.info(f"Buy signals: {buy_signals}")
    logger.info(f"Sell signals: {sell_signals}")
    logger.info(f"Total signals: {buy_signals + sell_signals}")
    logger.info(f"Signal reasons: {len(signal_reasons)}")
    
    assert buy_signals > 0 or sell_signals > 0, f"Expected signals, got buys={buy_signals}, sells={sell_signals}"
    logger.info("✅ Test 2 PASSED")
    return signals, signal_reasons

def test_trade_execution():
    """Test trade execution separately"""
    logger.info("=" * 80)
    logger.info("Test 3: Trade Execution")
    logger.info("=" * 80)
    
    from ai_module.technical_indicators import calculate_all_indicators
    
    data = create_sample_data(365)
    data = calculate_all_indicators(data)
    
    strategy = {
        'entry_conditions': ['RSI below 30'],
        'exit_conditions': ['RSI above 70'],
        'indicators': ['rsi'],
        'raw_excerpt': 'Buy when RSI is below 30, sell when RSI is above 70'
    }
    
    engine = BacktestEngine(initial_capital=10000)
    signals, signal_reasons = engine._generate_signals(data, strategy)
    
    logger.info(f"Generated signals: buys={(signals==1).sum()}, sells={(signals==-1).sum()}")
    
    engine._execute_trades(data, signals, signal_reasons)
    
    logger.info(f"Trades executed: {len(engine.trades)}")
    logger.info(f"Final capital: {engine.current_capital:.2f}")
    
    if len(engine.trades) > 0:
        logger.info(f"First trade: {engine.trades[0]}")
    
    assert len(engine.trades) > 0, f"Expected trades, got {len(engine.trades)}"
    logger.info("✅ Test 3 PASSED")
    return engine.trades

def test_metrics_calculation():
    """Test metrics calculation separately"""
    logger.info("=" * 80)
    logger.info("Test 4: Metrics Calculation")
    logger.info("=" * 80)
    
    engine = BacktestEngine(initial_capital=10000)
    
    # Manually add some trades
    engine.trades = [
        {
            'entry_date': '2023-01-01 00:00:00',
            'exit_date': '2023-01-10 00:00:00',
            'entry_price': 1.1000,
            'exit_price': 1.1100,
            'pnl': 0.01,
            'pnl_percent': 1.0,
            'duration_days': 9,
            'entry_reason_fa': 'Test entry',
            'exit_reason_fa': 'Test exit'
        },
        {
            'entry_date': '2023-01-15 00:00:00',
            'exit_date': '2023-01-25 00:00:00',
            'entry_price': 1.1100,
            'exit_price': 1.1050,
            'pnl': -0.0045,
            'pnl_percent': -0.45,
            'duration_days': 10,
            'entry_reason_fa': 'Test entry',
            'exit_reason_fa': 'Test exit'
        }
    ]
    engine.current_capital = 10050.0
    
    metrics = engine._calculate_metrics()
    
    logger.info(f"Metrics: {metrics}")
    assert metrics['total_trades'] == 2, f"Expected 2 trades, got {metrics['total_trades']}"
    assert metrics['winning_trades'] == 1, f"Expected 1 winning trade, got {metrics['winning_trades']}"
    assert metrics['losing_trades'] == 1, f"Expected 1 losing trade, got {metrics['losing_trades']}"
    assert metrics['total_return'] > 0, f"Expected positive return, got {metrics['total_return']}"
    
    logger.info("✅ Test 4 PASSED")
    return metrics

def test_with_selected_indicators():
    """Test with selected indicators"""
    logger.info("=" * 80)
    logger.info("Test 5: Strategy with Selected Indicators")
    logger.info("=" * 80)
    
    data = create_sample_data(365)
    
    strategy = {
        'entry_conditions': ['Buy signal'],
        'exit_conditions': ['Sell signal'],
        'selected_indicators': ['rsi'],
        'raw_excerpt': 'Use RSI indicator'
    }
    
    engine = BacktestEngine(initial_capital=10000)
    result = engine.run_backtest(data, strategy, 'EUR/USD')
    
    logger.info(f"Result: {result}")
    logger.info(f"Total trades: {result.get('total_trades', 0)}")
    logger.info(f"Total return: {result.get('total_return', 0):.2f}%")
    
    # This might return 0 if AND logic is too strict
    logger.info(f"⚠️ Test 5: Got {result.get('total_trades', 0)} trades (might be 0 due to AND logic)")
    return result

def test_index_alignment():
    """Test index alignment between data and signals"""
    logger.info("=" * 80)
    logger.info("Test 6: Index Alignment")
    logger.info("=" * 80)
    
    data = create_sample_data(100)
    from ai_module.technical_indicators import calculate_all_indicators
    data = calculate_all_indicators(data)
    
    strategy = {
        'entry_conditions': ['RSI below 30'],
        'exit_conditions': ['RSI above 70'],
        'indicators': ['rsi'],
    }
    
    engine = BacktestEngine(initial_capital=10000)
    signals, signal_reasons = engine._generate_signals(data, strategy)
    
    logger.info(f"Data index length: {len(data.index)}")
    logger.info(f"Signals index length: {len(signals.index)}")
    logger.info(f"Index match: {data.index.equals(signals.index)}")
    
    if not data.index.equals(signals.index):
        logger.warning("⚠️ Index mismatch detected!")
        logger.info(f"Data index sample: {data.index[:5]}")
        logger.info(f"Signals index sample: {signals.index[:5]}")
    
    # Test execution
    engine._execute_trades(data, signals, signal_reasons)
    logger.info(f"Trades after execution: {len(engine.trades)}")
    
    logger.info("✅ Test 6 PASSED")
    return signals

if __name__ == '__main__':
    logger.info("Starting backtest diagnostic tests...")
    
    try:
        # Run all tests
        test_basic_strategy()
        test_signals_generation()
        test_trade_execution()
        test_metrics_calculation()
        test_with_selected_indicators()
        test_index_alignment()
        
        logger.info("=" * 80)
        logger.info("✅ All tests completed!")
        logger.info("=" * 80)
    except AssertionError as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

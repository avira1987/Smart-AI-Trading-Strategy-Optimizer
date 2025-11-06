"""
Debug test to find why backtests return zero results
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
from datetime import datetime
from ai_module.backtest_engine import BacktestEngine
from ai_module.technical_indicators import calculate_all_indicators
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

def test_strategy_with_entry_exit_conditions():
    """Test with explicit entry and exit conditions"""
    logger.info("=" * 80)
    logger.info("Test: Strategy with entry and exit conditions")
    logger.info("=" * 80)
    
    data = create_sample_data(365)
    data = calculate_all_indicators(data)
    
    # Strategy with explicit conditions
    strategy = {
        'entry_conditions': ['RSI below 30', 'Buy signal'],
        'exit_conditions': ['RSI above 70', 'Sell signal'],
        'indicators': ['rsi'],
        'raw_excerpt': 'Buy when RSI is below 30, sell when RSI is above 70',
        'selected_indicators': []
    }
    
    engine = BacktestEngine(initial_capital=10000)
    
    # Test signal generation
    logger.info("Testing signal generation...")
    signals, signal_reasons = engine._generate_signals(data, strategy)
    
    buy_signals = int((signals == 1).sum())
    sell_signals = int((signals == -1).sum())
    total_signals = buy_signals + sell_signals
    
    logger.info(f"Buy signals: {buy_signals}")
    logger.info(f"Sell signals: {sell_signals}")
    logger.info(f"Total signals: {total_signals}")
    logger.info(f"Signal reasons count: {len(signal_reasons)}")
    
    if total_signals == 0:
        logger.error("❌ NO SIGNALS GENERATED!")
        logger.error(f"Available columns: {list(data.columns)[:20]}")
        logger.error(f"RSI column exists: {'rsi' in data.columns}")
        if 'rsi' in data.columns:
            logger.error(f"RSI min: {data['rsi'].min()}, max: {data['rsi'].max()}, mean: {data['rsi'].mean()}")
            logger.error(f"RSI < 30 count: {(data['rsi'] < 30).sum()}")
            logger.error(f"RSI > 70 count: {(data['rsi'] > 70).sum()}")
        return False
    
    # Test trade execution
    logger.info("Testing trade execution...")
    engine._execute_trades(data, signals, signal_reasons)
    
    logger.info(f"Trades executed: {len(engine.trades)}")
    if len(engine.trades) > 0:
        logger.info(f"First trade: {engine.trades[0]}")
    
    # Test full backtest
    logger.info("Testing full backtest...")
    result = engine.run_backtest(data, strategy, 'EUR/USD')
    
    logger.info(f"Result - Total trades: {result.get('total_trades', 0)}")
    logger.info(f"Result - Total return: {result.get('total_return', 0):.2f}%")
    
    if result.get('total_trades', 0) == 0:
        logger.error("❌ NO TRADES IN RESULT!")
        return False
    
    logger.info("✅ Test PASSED")
    return True

def test_strategy_with_selected_indicators():
    """Test with selected indicators"""
    logger.info("=" * 80)
    logger.info("Test: Strategy with selected indicators")
    logger.info("=" * 80)
    
    data = create_sample_data(365)
    data = calculate_all_indicators(data)
    
    # Strategy with selected indicators only (no text strategy)
    strategy = {
        'entry_conditions': [],
        'exit_conditions': [],
        'indicators': [],
        'raw_excerpt': '',
        'selected_indicators': ['rsi']
    }
    
    engine = BacktestEngine(initial_capital=10000)
    
    # Test signal generation
    logger.info("Testing signal generation...")
    signals, signal_reasons = engine._generate_signals(data, strategy)
    
    buy_signals = int((signals == 1).sum())
    sell_signals = int((signals == -1).sum())
    total_signals = buy_signals + sell_signals
    
    logger.info(f"Buy signals: {buy_signals}")
    logger.info(f"Sell signals: {sell_signals}")
    logger.info(f"Total signals: {total_signals}")
    
    if total_signals == 0:
        logger.error("❌ NO SIGNALS GENERATED!")
        return False
    
    # Test full backtest
    logger.info("Testing full backtest...")
    result = engine.run_backtest(data, strategy, 'EUR/USD')
    
    logger.info(f"Result - Total trades: {result.get('total_trades', 0)}")
    logger.info(f"Result - Total return: {result.get('total_return', 0):.2f}%")
    
    if result.get('total_trades', 0) == 0:
        logger.error("❌ NO TRADES IN RESULT!")
        return False
    
    logger.info("✅ Test PASSED")
    return True

def test_strategy_with_text_and_selected_indicators():
    """Test with both text strategy and selected indicators"""
    logger.info("=" * 80)
    logger.info("Test: Strategy with text AND selected indicators")
    logger.info("=" * 80)
    
    data = create_sample_data(365)
    data = calculate_all_indicators(data)
    
    # Strategy with both text and selected indicators
    strategy = {
        'entry_conditions': ['Buy signal'],
        'exit_conditions': ['Sell signal'],
        'indicators': ['rsi'],
        'raw_excerpt': 'Use RSI',
        'selected_indicators': ['rsi']
    }
    
    engine = BacktestEngine(initial_capital=10000)
    
    # Test signal generation
    logger.info("Testing signal generation...")
    signals, signal_reasons = engine._generate_signals(data, strategy)
    
    buy_signals = int((signals == 1).sum())
    sell_signals = int((signals == -1).sum())
    total_signals = buy_signals + sell_signals
    
    logger.info(f"Buy signals: {buy_signals}")
    logger.info(f"Sell signals: {sell_signals}")
    logger.info(f"Total signals: {total_signals}")
    
    if total_signals == 0:
        logger.error("❌ NO SIGNALS GENERATED!")
        logger.error("This might be due to AND logic being too strict")
        return False
    
    # Test full backtest
    logger.info("Testing full backtest...")
    result = engine.run_backtest(data, strategy, 'EUR/USD')
    
    logger.info(f"Result - Total trades: {result.get('total_trades', 0)}")
    logger.info(f"Result - Total return: {result.get('total_return', 0):.2f}%")
    
    if result.get('total_trades', 0) == 0:
        logger.error("❌ NO TRADES IN RESULT!")
        return False
    
    logger.info("✅ Test PASSED")
    return True

if __name__ == '__main__':
    logger.info("Starting backtest signals debug tests...")
    
    results = []
    
    try:
        results.append(("Entry/Exit Conditions", test_strategy_with_entry_exit_conditions()))
        results.append(("Selected Indicators Only", test_strategy_with_selected_indicators()))
        results.append(("Text + Selected Indicators", test_strategy_with_text_and_selected_indicators()))
        
        logger.info("=" * 80)
        logger.info("Test Summary:")
        logger.info("=" * 80)
        
        for test_name, passed in results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            logger.info(f"{test_name}: {status}")
        
        all_passed = all(result[1] for result in results)
        if all_passed:
            logger.info("=" * 80)
            logger.info("✅ All tests passed!")
            logger.info("=" * 80)
        else:
            logger.error("=" * 80)
            logger.error("❌ Some tests failed!")
            logger.error("=" * 80)
            
    except Exception as e:
        logger.error(f"❌ Test error: {e}", exc_info=True)
        import traceback
        traceback.print_exc()

"""
تست جامع برای بررسی علت صفر بودن نتایج بک‌تست
این تست تمام مراحل بک‌تست را بررسی می‌کند و مشکل را شناسایی می‌کند
"""

import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import TradingStrategy, Job, Result
from ai_module.backtest_engine import BacktestEngine
from ai_module.nlp_parser import parse_strategy_text
from api.data_providers import DataProviderManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('test_backtest_debug.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def create_sample_data(days=90, symbol='EURUSD'):
    """ایجاد داده‌های نمونه برای تست"""
    logger.info("=" * 80)
    logger.info("مرحله 1: ایجاد داده‌های نمونه")
    logger.info("=" * 80)
    
    # ایجاد تاریخ‌ها
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='15min')
    
    # ایجاد داده‌های OHLC با نوسان واقعی
    np.random.seed(42)
    n = len(dates)
    
    # قیمت پایه
    base_price = 1.1000 if 'EUR' in symbol else 2500.0
    
    # ایجاد قیمت‌ها با روند و نوسان
    returns = np.random.normal(0, 0.001, n)
    prices = base_price * (1 + returns).cumprod()
    
    # ایجاد OHLC
    data = pd.DataFrame({
        'open': prices,
        'high': prices * (1 + np.abs(np.random.normal(0, 0.002, n))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.002, n))),
        'close': prices * (1 + np.random.normal(0, 0.0005, n)),
        'volume': np.random.randint(1000, 10000, n)
    }, index=dates)
    
    # اطمینان از اینکه high >= low و ...
    data['high'] = data[['open', 'high', 'close']].max(axis=1)
    data['low'] = data[['open', 'low', 'close']].min(axis=1)
    
    logger.info(f"✅ داده‌های نمونه ایجاد شد: {len(data)} ردیف")
    logger.info(f"   - بازه زمانی: {data.index[0]} تا {data.index[-1]}")
    logger.info(f"   - قیمت اول: {data.iloc[0]['close']:.4f}")
    logger.info(f"   - قیمت آخر: {data.iloc[-1]['close']:.4f}")
    
    return data


def test_strategy_extraction():
    """تست استخراج استراتژی"""
    logger.info("=" * 80)
    logger.info("مرحله 2: تست استخراج استراتژی")
    logger.info("=" * 80)
    
    # استراتژی نمونه با شرایط ورود و خروج
    strategy_text = """
    استراتژی معاملاتی:
    
    شرایط ورود:
    1. RSI زیر 30 باشد
    2. قیمت بالاتر از SMA 20 باشد
    3. MACD از خط سیگنال بالاتر باشد
    
    شرایط خروج:
    1. RSI بالای 70 باشد
    2. قیمت زیر SMA 20 باشد
    3. MACD از خط سیگنال پایین‌تر باشد
    """
    
    logger.info("متن استراتژی:")
    logger.info(strategy_text)
    
    parsed = parse_strategy_text(strategy_text)
    
    logger.info("=" * 80)
    logger.info("نتایج استخراج استراتژی:")
    logger.info("=" * 80)
    logger.info(f"  - شرط‌های ورود: {len(parsed.get('entry_conditions', []))}")
    for i, cond in enumerate(parsed.get('entry_conditions', []), 1):
        logger.info(f"    {i}. {cond[:100]}...")
    
    logger.info(f"  - شرط‌های خروج: {len(parsed.get('exit_conditions', []))}")
    for i, cond in enumerate(parsed.get('exit_conditions', []), 1):
        logger.info(f"    {i}. {cond[:100]}...")
    
    logger.info(f"  - اندیکاتورها: {parsed.get('indicators', [])}")
    logger.info(f"  - Confidence Score: {parsed.get('confidence_score', 0):.2f}")
    
    return parsed


def test_signal_generation(data, strategy):
    """تست تولید سیگنال‌ها"""
    logger.info("=" * 80)
    logger.info("مرحله 3: تست تولید سیگنال‌ها")
    logger.info("=" * 80)
    
    engine = BacktestEngine(initial_capital=10000)
    
    # محاسبه اندیکاتورها
    from ai_module.technical_indicators import calculate_all_indicators
    data_with_indicators = calculate_all_indicators(data.copy())
    
    logger.info(f"داده‌ها بعد از محاسبه اندیکاتورها: {data_with_indicators.shape}")
    logger.info(f"ستون‌های موجود: {list(data_with_indicators.columns)[:15]}...")
    
    # تولید سیگنال‌ها
    signals, reasons = engine._generate_signals(data_with_indicators, strategy)
    
    buy_signals = int((signals == 1).sum())
    sell_signals = int((signals == -1).sum())
    total_signals = buy_signals + sell_signals
    
    logger.info("=" * 80)
    logger.info("نتایج تولید سیگنال:")
    logger.info("=" * 80)
    logger.info(f"  - سیگنال خرید: {buy_signals}")
    logger.info(f"  - سیگنال فروش: {sell_signals}")
    logger.info(f"  - کل سیگنال‌ها: {total_signals}")
    logger.info(f"  - کل ردیف‌ها: {len(signals)}")
    
    if total_signals == 0:
        logger.error("❌ مشکل: هیچ سیگنالی تولید نشد!")
        logger.error("   دلایل احتمالی:")
        logger.error("   1. شرط‌های ورود استخراج نشده‌اند")
        logger.error("   2. شرط‌ها قابل پارس نیستند")
        logger.error("   3. شرط‌ها با داده‌ها مطابقت ندارند")
        
        # بررسی شرط‌های ورود
        entry_conditions = strategy.get('entry_conditions', [])
        if not entry_conditions:
            logger.error("   ⚠️ هیچ شرط ورودی استخراج نشده است!")
        else:
            logger.error(f"   ⚠️ {len(entry_conditions)} شرط ورود استخراج شده اما هیچ سیگنالی تولید نشد")
            logger.error("   بررسی کنید که شرط‌ها قابل پارس باشند")
    else:
        logger.info("✅ سیگنال‌ها با موفقیت تولید شدند")
    
    # نمایش نمونه سیگنال‌ها
    if buy_signals > 0:
        buy_indices = signals[signals == 1].index[:5]
        logger.info("\nنمونه سیگنال‌های خرید:")
        for idx in buy_indices:
            reason = reasons.get(idx, {}).get('entry_reason_fa', 'بدون دلیل')
            logger.info(f"  - {idx}: {reason[:80]}...")
    
    if sell_signals > 0:
        sell_indices = signals[signals == -1].index[:5]
        logger.info("\nنمونه سیگنال‌های فروش:")
        for idx in sell_indices:
            reason = reasons.get(idx, {}).get('exit_reason_fa', 'بدون دلیل')
            logger.info(f"  - {idx}: {reason[:80]}...")
    
    return signals, reasons, data_with_indicators


def test_trade_execution(data, signals, signal_reasons):
    """تست اجرای معاملات"""
    logger.info("=" * 80)
    logger.info("مرحله 4: تست اجرای معاملات")
    logger.info("=" * 80)
    
    engine = BacktestEngine(initial_capital=10000)
    
    # اجرای معاملات
    engine._execute_trades(data, signals, signal_reasons)
    
    total_trades = len(engine.trades)
    
    logger.info("=" * 80)
    logger.info("نتایج اجرای معاملات:")
    logger.info("=" * 80)
    logger.info(f"  - تعداد معاملات: {total_trades}")
    logger.info(f"  - سرمایه اولیه: {engine.initial_capital:.2f}")
    logger.info(f"  - سرمایه نهایی: {engine.current_capital:.2f}")
    
    if total_trades == 0:
        logger.error("❌ مشکل: هیچ معامله‌ای اجرا نشد!")
        buy_signals = int((signals == 1).sum())
        sell_signals = int((signals == -1).sum())
        logger.error(f"   - سیگنال خرید: {buy_signals}")
        logger.error(f"   - سیگنال فروش: {sell_signals}")
        logger.error("   ⚠️ برای اجرای معامله، نیاز به سیگنال خرید و سپس سیگنال فروش است")
    else:
        logger.info("✅ معاملات با موفقیت اجرا شدند")
        
        # نمایش نمونه معاملات
        logger.info("\nنمونه معاملات (5 معامله اول):")
        for i, trade in enumerate(engine.trades[:5], 1):
            logger.info(f"  معامله {i}:")
            logger.info(f"    - ورود: {trade.get('entry_date', 'N/A')}")
            logger.info(f"    - خروج: {trade.get('exit_date', 'N/A')}")
            logger.info(f"    - قیمت ورود: {trade.get('entry_price', 0):.4f}")
            logger.info(f"    - قیمت خروج: {trade.get('exit_price', 0):.4f}")
            logger.info(f"    - سود/زیان: {trade.get('pnl_percent', 0):.2f}%")
    
    return engine


def test_metrics_calculation(engine):
    """تست محاسبه متریک‌ها"""
    logger.info("=" * 80)
    logger.info("مرحله 5: تست محاسبه متریک‌ها")
    logger.info("=" * 80)
    
    metrics = engine._calculate_metrics()
    
    logger.info("=" * 80)
    logger.info("نتایج محاسبه متریک‌ها:")
    logger.info("=" * 80)
    logger.info(f"  - Total Return: {metrics.get('total_return', 0):.2f}%")
    logger.info(f"  - Total Trades: {metrics.get('total_trades', 0)}")
    logger.info(f"  - Winning Trades: {metrics.get('winning_trades', 0)}")
    logger.info(f"  - Losing Trades: {metrics.get('losing_trades', 0)}")
    logger.info(f"  - Win Rate: {metrics.get('win_rate', 0):.2f}%")
    logger.info(f"  - Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
    logger.info(f"  - Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
    logger.info(f"  - Profit Factor: {metrics.get('profit_factor', 0):.4f}")
    
    if metrics.get('total_trades', 0) == 0:
        logger.error("❌ مشکل: تعداد معاملات صفر است!")
        logger.error("   این باعث می‌شود تمام متریک‌ها صفر باشند")
    
    return metrics


def test_full_backtest():
    """تست کامل بک‌تست"""
    logger.info("=" * 80)
    logger.info("=" * 80)
    logger.info("تست کامل بک‌تست - بررسی علت صفر بودن نتایج")
    logger.info("=" * 80)
    logger.info("=" * 80)
    
    try:
        # مرحله 1: ایجاد داده‌ها
        data = create_sample_data(days=90, symbol='EURUSD')
        
        # مرحله 2: استخراج استراتژی
        strategy = test_strategy_extraction()
        
        # مرحله 3: تولید سیگنال‌ها
        signals, reasons, data_with_indicators = test_signal_generation(data, strategy)
        
        # مرحله 4: اجرای معاملات
        engine = test_trade_execution(data_with_indicators, signals, reasons)
        
        # مرحله 5: محاسبه متریک‌ها
        metrics = test_metrics_calculation(engine)
        
        # مرحله 6: اجرای بک‌تست کامل
        logger.info("=" * 80)
        logger.info("مرحله 6: اجرای بک‌تست کامل")
        logger.info("=" * 80)
        
        engine_full = BacktestEngine(initial_capital=10000)
        result_data = engine_full.run_backtest(data_with_indicators, strategy, 'EURUSD')
        
        logger.info("=" * 80)
        logger.info("نتایج نهایی بک‌تست:")
        logger.info("=" * 80)
        logger.info(f"  - Total Return: {result_data.get('total_return', 0):.2f}%")
        logger.info(f"  - Total Trades: {result_data.get('total_trades', 0)}")
        logger.info(f"  - Winning Trades: {result_data.get('winning_trades', 0)}")
        logger.info(f"  - Losing Trades: {result_data.get('losing_trades', 0)}")
        logger.info(f"  - Win Rate: {result_data.get('win_rate', 0):.2f}%")
        logger.info(f"  - Max Drawdown: {result_data.get('max_drawdown', 0):.2f}%")
        
        if result_data.get('error'):
            logger.error(f"  - خطا: {result_data.get('error')}")
        
        # خلاصه مشکلات
        logger.info("=" * 80)
        logger.info("=" * 80)
        logger.info("خلاصه مشکلات شناسایی شده:")
        logger.info("=" * 80)
        logger.info("=" * 80)
        
        problems = []
        
        if len(strategy.get('entry_conditions', [])) == 0:
            problems.append("❌ هیچ شرط ورودی از استراتژی استخراج نشده است")
        
        buy_signals = int((signals == 1).sum())
        if buy_signals == 0:
            problems.append("❌ هیچ سیگنال خریدی تولید نشده است")
        
        if len(engine.trades) == 0:
            problems.append("❌ هیچ معامله‌ای اجرا نشده است")
        
        if result_data.get('total_trades', 0) == 0:
            problems.append("❌ تعداد معاملات در نتایج صفر است")
        
        if result_data.get('total_return', 0) == 0 and result_data.get('total_trades', 0) == 0:
            problems.append("❌ تمام نتایج صفر هستند")
        
        if problems:
            logger.error("\nمشکلات شناسایی شده:")
            for i, problem in enumerate(problems, 1):
                logger.error(f"  {i}. {problem}")
        else:
            logger.info("✅ هیچ مشکلی شناسایی نشد - بک‌تست به درستی کار می‌کند")
        
        logger.info("=" * 80)
        logger.info("=" * 80)
        
        return result_data
        
    except Exception as e:
        logger.error("=" * 80)
        logger.error("خطا در تست:")
        logger.error("=" * 80)
        logger.error(f"نوع خطا: {type(e).__name__}")
        logger.error(f"پیام خطا: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("شروع تست بک‌تست - بررسی علت صفر بودن نتایج")
    print("=" * 80 + "\n")
    
    result = test_full_backtest()
    
    print("\n" + "=" * 80)
    print("تست کامل شد. نتایج در فایل test_backtest_debug.log ذخیره شد.")
    print("=" * 80 + "\n")


"""Tests for live trading signal generation to ensure indicators are calculated.

این تست‌ها بررسی می‌کنند که در تابع check_strategy_signals هنگام معاملات زنده،
قبل از تولید سیگنال، اندیکاتورها محاسبه می‌شوند (هماهنگ با منطق بک‌تست).
"""

import unittest
from unittest.mock import patch, MagicMock

import pandas as pd

from api.auto_trader import check_strategy_signals


class DummyStrategy:
    """Simple dummy TradingStrategy-like object for unit testing.

    We only need .parsed_strategy_data and .id attributes for check_strategy_signals.
    """

    def __init__(self, parsed_strategy_data=None, sid=1):
        self.parsed_strategy_data = parsed_strategy_data or {}
        self.id = sid


class LiveTradingIndicatorsTestCase(unittest.TestCase):
    """Unit tests for live trading signal checks.

    Note: These tests do not hit the database or MT5; everything is mocked.
    """

    def _make_df(self, rows: int = 100) -> pd.DataFrame:
        index = pd.date_range("2024-01-01", periods=rows, freq="15min")
        data = {
            "open": [2000 + i * 0.1 for i in range(rows)],
            "high": [2000 + i * 0.1 + 0.5 for i in range(rows)],
            "low": [2000 + i * 0.1 - 0.5 for i in range(rows)],
            "close": [2000 + i * 0.1 for i in range(rows)],
        }
        return pd.DataFrame(data, index=index)

    @patch("api.auto_trader.calculate_all_indicators")
    @patch("api.auto_trader.fetch_mt5_candles")
    @patch("ai_module.backtest_engine.BacktestEngine._generate_signals")
    def test_indicators_are_calculated_before_signals(
        self,
        mock_generate_signals,
        mock_fetch_candles,
        mock_calc_indicators,
    ):
        """Ensure calculate_all_indicators is called on fetched data before _generate_signals.

        This is the core bug you reported: backtest had indicators, but live trading did not.
        """
        raw_df = self._make_df()
        df_with_indicators = raw_df.copy()
        df_with_indicators["rsi"] = 30  # dummy indicator column

        # fetch_mt5_candles returns raw data
        mock_fetch_candles.return_value = (raw_df, None)
        # calculate_all_indicators should be called and return enriched data
        mock_calc_indicators.return_value = df_with_indicators

        # _generate_signals returns a simple buy signal at the last candle
        signals = pd.Series(0, index=df_with_indicators.index)
        signals.iloc[-1] = 1
        mock_generate_signals.return_value = (signals, {})

        strategy = DummyStrategy(parsed_strategy_data={"entry_conditions": ["RSI < 30"]})

        result = check_strategy_signals(strategy, "XAUUSD", timeframe="M15")

        # 1) Indicators must be calculated once
        mock_calc_indicators.assert_called_once()
        # It must be called with the dataframe returned from fetch_mt5_candles
        called_df = mock_calc_indicators.call_args[0][0]
        assert called_df is raw_df

        # 2) _generate_signals must receive the enriched dataframe
        called_args, _ = mock_generate_signals.call_args
        # called_args[0] is self (BacktestEngine instance), called_args[1] is df, called_args[2] is strategy dict
        passed_df_to_generate = called_args[1]
        assert passed_df_to_generate is df_with_indicators

        # 3) And the function should return a non-hold signal as mocked
        assert result["signal"] in ("buy", "sell")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

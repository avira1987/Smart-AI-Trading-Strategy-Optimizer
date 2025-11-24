"""
Integration-style test ensuring preprocessed strategies are used directly
during backtests without re-parsing the original uploaded file.
"""
import os
import sys
import uuid
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402

from core.models import TradingStrategy, Job  # noqa: E402
from api.tasks import run_backtest_task  # noqa: E402


def _sample_market_data(rows: int = 256) -> pd.DataFrame:
    """Build deterministic OHLCV data for mocks."""
    rng = np.random.default_rng(42)
    index = pd.date_range(end=datetime.utcnow(), periods=rows, freq="h")
    base = 1900 + rng.normal(scale=1.0, size=rows).cumsum()
    data = pd.DataFrame(
        {
            "open": base + rng.normal(scale=0.3, size=rows),
            "high": base + abs(rng.normal(scale=0.6, size=rows)),
            "low": base - abs(rng.normal(scale=0.6, size=rows)),
            "close": base + rng.normal(scale=0.3, size=rows),
            "volume": rng.integers(100_000, 200_000, size=rows),
        },
        index=index,
    )
    return data


def test_run_backtest_uses_generated_strategy(monkeypatch):
    """
    Verify run_backtest_task consumes TradingStrategy.parsed_strategy_data
    (produced by AI pipeline) instead of re-parsing the uploaded file.
    """

    market_data = _sample_market_data()

    class DummyDataProviderManager:
        def __init__(self, *args, **kwargs):
            self._data = market_data

        def get_available_providers(self):
            return ["dummy"]

        def get_historical_data(
            self,
            symbol,
            timeframe_days=365,
            *,
            interval="1day",
            include_latest=True,
            user=None,
            return_provider=False,
            **kwargs,
        ):
            df = self._data.copy()
            if return_provider:
                return df, "dummy"
            return df

        def get_data_from_any_provider(self, *args, **kwargs):
            return self._data.copy(), "dummy"

    def _fail_parse_strategy(*args, **kwargs):
        raise AssertionError("parse_strategy_file should not be called")

    captured = {}

    class FakeBacktestEngine:
        def __init__(self, initial_capital):
            self.initial_capital = initial_capital

        def run_backtest(self, data, strategy, symbol):
            captured["data_length"] = len(data)
            captured["strategy"] = strategy
            captured["symbol"] = symbol
            return {
                "total_return": 7.5,
                "total_trades": 4,
                "winning_trades": 2,
                "losing_trades": 2,
                "win_rate": 50.0,
                "max_drawdown": 2.1,
                "equity_curve_data": [self.initial_capital, self.initial_capital * 1.075],
                "trades": [
                    {"entry_date": "2024-01-01", "exit_date": "2024-01-02"}
                ],
                "description_fa": "نتایج نمونه",
                "sharpe_ratio": 1.23,
                "profit_factor": 1.45,
            }

    monkeypatch.setattr("api.tasks.DataProviderManager", DummyDataProviderManager)
    monkeypatch.setattr("api.tasks.parse_strategy_file", _fail_parse_strategy)
    monkeypatch.setattr("api.tasks.BacktestEngine", FakeBacktestEngine)
    monkeypatch.setattr("api.tasks.is_mt5_available", lambda: (False, "mt5 disabled"))
    monkeypatch.setattr(
        "core.gamification.award_backtest_points",
        lambda user, result: {
            "points_awarded": 0,
            "total_points": 0,
            "level": 1,
            "new_achievements": [],
        },
        raising=False,
    )
    monkeypatch.setattr(
        "ai_module.gemini_client.analyze_backtest_trades_with_ai",
        lambda *args, **kwargs: {"ai_status": "ok", "analysis_text": "mock analysis"},
    )
    monkeypatch.setattr(
        "ai_module.gemini_client.generate_basic_backtest_analysis",
        lambda *args, **kwargs: "basic analysis fallback",
    )

    User = get_user_model()
    username = f"strategy-owner-{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password="test123")
    dummy_file = SimpleUploadedFile("strategy.txt", b"placeholder")
    parsed_strategy = {
        "symbol": "XAU/USD",
        "timeframe": "M15",
        "entry_conditions": ["RSI below 30"],
        "exit_conditions": ["RSI above 70"],
        "indicators": ["rsi"],
        "raw_excerpt": "خرید وقتی RSI زیر 30 باشد",
        "confidence_score": 0.82,
        "conversion_source": "unit-test",
    }

    strategy = TradingStrategy.objects.create(
        user=user,
        name="Generated Strategy",
        description="AI generated strategy",
        strategy_file=dummy_file,
        processing_status="processed",
        parsed_strategy_data=parsed_strategy,
    )
    job = Job.objects.create(user=user, strategy=strategy, job_type="backtest")

    response = run_backtest_task(
        job.id,
        timeframe_days=14,
        initial_capital=12_000,
        ai_provider=None,
    )

    job.refresh_from_db()
    strategy.refresh_from_db()

    assert response.startswith("Backtest completed")
    assert job.status == "completed"
    assert job.result is not None
    assert captured["strategy"]["conversion_source"] == "unit-test"
    assert captured["strategy"]["raw_excerpt"] == parsed_strategy["raw_excerpt"]
    assert captured["strategy"]["selected_indicators"] == []
    assert captured["symbol"] == "XAU/USD"
    assert captured["data_length"] == len(market_data)


def test_backtest_fetches_mt5_timeframe_for_stored_strategy(monkeypatch):
    """
    Ensure run_backtest_task requests MT5 data using the strategy's timeframe metadata.
    """

    mt5_capture = {}

    def fake_fetch(symbol, timeframe, count):
        mt5_capture["symbol"] = symbol
        mt5_capture["timeframe"] = timeframe
        mt5_capture["count"] = count
        data = _sample_market_data(rows=min(count, 1024))
        return data, None

    monkeypatch.setattr("api.data_providers.fetch_mt5_candles", fake_fetch)
    monkeypatch.setattr("api.tasks.fetch_mt5_candles", fake_fetch)
    monkeypatch.setattr("api.data_providers.is_mt5_available", lambda: (True, None))
    monkeypatch.setattr("api.tasks.is_mt5_available", lambda: (True, None))

    def _fail_parse_strategy(*args, **kwargs):
        raise AssertionError("parse_strategy_file should not be called")

    monkeypatch.setattr("api.tasks.parse_strategy_file", _fail_parse_strategy)

    captured = {}

    class FakeBacktestEngine:
        def __init__(self, initial_capital):
            self.initial_capital = initial_capital

        def run_backtest(self, data, strategy, symbol):
            captured["data_length"] = len(data)
            captured["symbol"] = symbol
            return {
                "total_return": 11.3,
                "total_trades": 6,
                "winning_trades": 3,
                "losing_trades": 3,
                "win_rate": 50.0,
                "max_drawdown": 3.0,
                "equity_curve_data": [self.initial_capital, self.initial_capital * 1.1],
                "trades": [{"entry_date": "2024-02-01", "exit_date": "2024-02-03"}],
                "description_fa": "نتایج تست MT5",
                "sharpe_ratio": 1.11,
                "profit_factor": 1.3,
            }

    monkeypatch.setattr("api.tasks.BacktestEngine", FakeBacktestEngine)
    monkeypatch.setattr(
        "core.gamification.award_backtest_points",
        lambda user, result: {
            "points_awarded": 0,
            "total_points": 0,
            "level": 1,
            "new_achievements": [],
        },
        raising=False,
    )
    monkeypatch.setattr(
        "ai_module.gemini_client.analyze_backtest_trades_with_ai",
        lambda *args, **kwargs: {"ai_status": "ok", "analysis_text": "mock analysis"},
    )
    monkeypatch.setattr(
        "ai_module.gemini_client.generate_basic_backtest_analysis",
        lambda *args, **kwargs: "basic analysis fallback",
    )

    User = get_user_model()
    username = f"mt5-owner-{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password="test123")
    dummy_file = SimpleUploadedFile("strategy.txt", b"placeholder")
    parsed_strategy = {
        "symbol": "XAU/USD",
        "timeframe": "M5",
        "entry_conditions": ["Breakout"],
        "exit_conditions": ["Stop loss"],
        "indicators": ["ema"],
        "raw_excerpt": "نمونه استراتژی کوتاه‌مدت",
        "confidence_score": 0.9,
    }

    strategy = TradingStrategy.objects.create(
        user=user,
        name="MT5 Strategy",
        description="MT5 timeframe test",
        strategy_file=dummy_file,
        processing_status="processed",
        parsed_strategy_data=parsed_strategy,
    )
    job = Job.objects.create(user=user, strategy=strategy, job_type="backtest")

    response = run_backtest_task(
        job.id,
        timeframe_days=10,
        initial_capital=8_000,
        selected_indicators=None,
        ai_provider=None,
    )

    job.refresh_from_db()

    assert response.startswith("Backtest completed")
    assert job.status == "completed"
    assert job.result is not None
    assert mt5_capture["symbol"] == "XAUUSD"
    assert mt5_capture["timeframe"] == "M5"
    assert mt5_capture["count"] >= 200
    assert captured["data_length"] > 0
    assert captured["symbol"] == "XAU/USD"
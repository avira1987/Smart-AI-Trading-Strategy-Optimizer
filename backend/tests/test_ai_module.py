import os
import sys
import json
from unittest.mock import Mock, patch

import pytest

import django
import pandas as pd
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
django.setup()

from django.test import override_settings

from backend.ai_module import gemini_client, provider_manager
from backend.ai_module.providers import ProviderAttempt, ProviderResult, GeminiProvider


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Ensure rate limit queue is cleared between tests."""
    gemini_client._request_timestamps.clear()
    yield
    gemini_client._request_timestamps.clear()


@pytest.fixture(autouse=True)
def reset_provider_cache():
    provider_manager._PROVIDER_MANAGERS.clear()
    yield
    provider_manager._PROVIDER_MANAGERS.clear()


class _DummyManagerDisabled:
    providers = {}

    def has_available_provider(self):
        return False

    def generate(self, *args, **kwargs):
        return ProviderResult(success=False, error="no_provider", attempts=[])


class _DummyManagerSuccess:
    providers = {}

    def has_available_provider(self):
        return True

    def generate(self, prompt, generation_config, metadata=None):
        text = json.dumps(
            {
                "entry_conditions": ["RSI < 30"],
                "exit_conditions": ["RSI > 60"],
                "risk_management": {"stop_loss": 50, "take_profit": 100},
            }
        )
        attempts = [
            ProviderAttempt(
                provider="test-provider",
                success=True,
                status_code=200,
                error=None,
                latency_ms=12.0,
                tokens_used=123,
            )
        ]
        return ProviderResult(
            success=True,
            text=text,
            provider="test-provider",
            raw_response={"choices": []},
            attempts=attempts,
            tokens_used=123,
        )


@patch("backend.ai_module.gemini_client.get_provider_manager")
def test_call_gemini_analyzer_disabled(mock_manager):
    mock_manager.return_value = _DummyManagerDisabled()
    result = gemini_client.call_gemini_analyzer("Sample strategy text")
    assert result["ai_status"] == "disabled"
    assert "AI analysis unavailable" in result["message"]
    assert result["entry_conditions"] == []
    assert result["exit_conditions"] == []


@patch("backend.ai_module.gemini_client.get_provider_manager")
def test_mocked_ai_response(mock_manager):
    mock_manager.return_value = _DummyManagerSuccess()
    result = gemini_client.call_gemini_analyzer("Sample strategy text for Gemini call")

    assert result["ai_status"] == "ok"
    assert "RSI < 30" in result["entry_conditions"]
    assert result["risk_management"]["stop_loss"] == 50
    assert result.get("ai_provider") == "test-provider"


def test_registered_providers_include_chatgpt_alias():
    providers = provider_manager.get_registered_providers()
    assert "openai" in providers
    assert "chatgpt" in providers
    assert providers["chatgpt"] is providers["openai"]


def test_priority_preserves_order_with_openai_first():
    with override_settings(AI_PROVIDER_PRIORITY=["openai", "gemini", "cohere"]):
        manager = provider_manager.AIProviderManager()
        assert manager._get_priority_list() == ["openai", "gemini", "cohere"]


def test_priority_normalizes_alias_but_keeps_rest():
    with override_settings(AI_PROVIDER_PRIORITY=["chatgpt", "gemini", "cohere"]):
        manager = provider_manager.AIProviderManager()
        assert manager._get_priority_list() == ["openai", "gemini", "cohere"]


def test_priority_keeps_non_openai_when_missing():
    with override_settings(AI_PROVIDER_PRIORITY=["gemini", "cohere"]):
        manager = provider_manager.AIProviderManager()
        assert manager._get_priority_list() == ["gemini", "cohere"]


def test_data_provider_manager_prefers_requested_provider(monkeypatch):
    from backend.api.data_providers import DataProviderManager

    manager = DataProviderManager()
    dummy_df = pd.DataFrame(
        {"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0]},
        index=[pd.Timestamp("2024-01-01")],
    )

    monkeypatch.setattr(
        manager.providers["metalsapi"],
        "get_historical_data",
        lambda symbol, start, end: dummy_df,
    )

    data, provider_used = manager.get_historical_data(
        "XAU/USD",
        timeframe_days=5,
        prefer_provider="metalsapi",
        include_latest=False,
        return_provider=True,
    )

    assert not data.empty
    assert provider_used == "metalsapi"


def test_data_provider_manager_falls_back_to_any_provider(monkeypatch):
    from backend.api.data_providers import DataProviderManager

    manager = DataProviderManager()

    def fake_get_data_from_any_provider(symbol, start, end, user=None):
        df = pd.DataFrame(
            {"open": [1900.0], "high": [1910.0], "low": [1890.0], "close": [1905.0]},
            index=[pd.Timestamp("2024-02-01")],
        )
        return df, "financialmodelingprep"

    monkeypatch.setattr(
        manager,
        "get_data_from_any_provider",
        fake_get_data_from_any_provider,
    )

    data, provider_used = manager.get_historical_data(
        "XAUUSD",
        timeframe_days=10,
        prefer_provider=None,
        include_latest=False,
        return_provider=True,
    )

    assert not data.empty
    assert provider_used == "financialmodelingprep"


def test_gemini_provider_handles_single_candidate_success(monkeypatch):
    provider = GeminiProvider()

    class _DummyResponse:
        def __init__(self, text: str) -> None:
            self.text = text
            self.usage_metadata = type("Usage", (), {"total_token_count": 42})()

        def to_dict(self):
            return {"text": self.text}

    dummy_response = _DummyResponse('{"entry_conditions": []}')

    class _DummyModel:
        def generate_content(self, prompt, generation_config):
            assert prompt == "prompt"
            assert "max_output_tokens" in generation_config
            return dummy_response

    class _DummyGenAI:
        def GenerativeModel(self, name):
            assert name == "gemini-1.5-flash-latest"
            return _DummyModel()

    monkeypatch.setattr(provider, "_configure", lambda: _DummyGenAI())
    monkeypatch.setattr(provider, "_resolve_model_candidates", lambda: ["gemini-1.5-flash-latest"])

    result = provider.generate("prompt", {"temperature": 0.1}, metadata=None)

    assert result.success is True
    assert result.text == dummy_response.text
    assert result.tokens_used == 42


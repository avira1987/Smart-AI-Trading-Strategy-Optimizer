"""
Test that BacktestPrecheckView uses cached parsed_strategy_data instead of re-parsing files.
This ensures precheck is fast and doesn't cause timeout errors.
"""
import os
import sys
import uuid
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from core.models import TradingStrategy  # noqa: E402


def test_precheck_uses_parsed_strategy_data():
    """Verify that precheck uses parsed_strategy_data instead of re-parsing files."""
    User = get_user_model()
    username = f"precheck-user-{uuid.uuid4().hex[:8]}"
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
        name="Precheck Test Strategy",
        description="Test strategy for precheck",
        strategy_file=dummy_file,
        processing_status="processed",
        parsed_strategy_data=parsed_strategy,
    )
    
    # Mock parse_strategy_file to fail if called (should not be called)
    parse_called = []
    
    def mock_parse_strategy_file(*args, **kwargs):
        parse_called.append(True)
        raise AssertionError("parse_strategy_file should not be called when parsed_strategy_data exists")
    
    # Monkey patch parse_strategy_file to detect if it's called
    from ai_module import nlp_parser
    original_parse = nlp_parser.parse_strategy_file
    nlp_parser.parse_strategy_file = mock_parse_strategy_file
    
    try:
        # Test precheck using APIClient
        client = APIClient()
        client.force_authenticate(user=user)
        
        start_time = time.time()
        response = client.post('/api/precheck/backtest/', {'strategy': strategy.id}, format='json')
        elapsed = time.time() - start_time
        
        # Restore original function
        nlp_parser.parse_strategy_file = original_parse
        
        # Verify response is successful
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data if hasattr(response, 'data') else 'No data'}"
        assert response.data['status'] in ['ready', 'ready_with_fallback'], f"Expected ready status, got {response.data['status']}"
        
        # Verify parse_strategy_file was NOT called
        assert len(parse_called) == 0, "parse_strategy_file should not be called when parsed_strategy_data exists"
        
        # Verify precheck is fast (should complete in less than 2 seconds)
        assert elapsed < 2.0, f"Precheck took {elapsed:.2f} seconds, should be < 2 seconds"
        
        # Verify symbol is extracted from parsed_strategy_data
        assert response.data['details']['symbol'] == "XAU/USD", "Symbol should be extracted from parsed_strategy_data"
        
    except Exception as e:
        # Restore original function on error
        nlp_parser.parse_strategy_file = original_parse
        raise


def test_precheck_fallback_to_parse_when_no_parsed_data():
    """Verify that precheck falls back to parsing when parsed_strategy_data doesn't exist."""
    User = get_user_model()
    username = f"precheck-fallback-{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password="test123")
    
    dummy_file = SimpleUploadedFile("strategy.txt", b"placeholder")
    
    strategy = TradingStrategy.objects.create(
        user=user,
        name="Precheck Fallback Strategy",
        description="Test strategy without parsed data",
        strategy_file=dummy_file,
        processing_status="not_processed",
        parsed_strategy_data=None,
    )
    
    # Test precheck using APIClient
    client = APIClient()
    client.force_authenticate(user=user)
    
    # This should work (fallback to parsing), but we expect it to be slower
    # We don't mock parse_strategy_file here because we want to test the fallback path
    response = client.post('/api/precheck/backtest/', {'strategy': strategy.id}, format='json')
    
    # Should still return a response (even if error due to missing file content)
    assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}"


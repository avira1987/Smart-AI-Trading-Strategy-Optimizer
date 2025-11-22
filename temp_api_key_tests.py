import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR / "backend"))

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.utils import timezone  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402
from unittest.mock import patch  # noqa: E402

from ai_module import provider_manager  # noqa: E402
from ai_module.provider_manager import get_provider_manager  # noqa: E402
from api.gold_price_views import GoldPriceView  # noqa: E402
from core.models import APIConfiguration, UserGoldAPIAccess  # noqa: E402


def reset_manager_cache():
    provider_manager._PROVIDER_MANAGERS.clear()


def main():
    User = get_user_model()
    admin = User.objects.get(username="09035760718")
    regular = User.objects.get(username="09338882080")

    APIConfiguration.objects.all().delete()

    print("=== Test 1: Regular user without personal key uses admin key ===")
    admin_key = APIConfiguration.objects.create(
        provider="openai",
        api_key="admin-shared-key",
        user=admin,
        is_active=True,
    )
    reset_manager_cache()
    provider = get_provider_manager(user=regular).providers["openai"]
    print("Resolved key:", provider.get_api_key())

    print("\n=== Test 2: Regular user with personal key takes priority ===")
    user_key = APIConfiguration.objects.create(
        provider="openai",
        api_key="user-personal-key",
        user=regular,
        is_active=True,
    )
    reset_manager_cache()
    provider = get_provider_manager(user=regular).providers["openai"]
    print("Resolved key:", provider.get_api_key())

    print("\n=== Test 3: GoldPriceView without user key falls back to MT5 ===")
    user_key.delete()
    reset_manager_cache()

    factory = APIRequestFactory()
    request = factory.get("/api/gold-price/")
    force_authenticate(request, user=regular)

    fake_mt5_result = {
        "success": True,
        "data": {"price": 1800},
        "price": 1800,
        "source": "mt5",
        "timestamp": timezone.now().isoformat(),
    }

    with patch("api.gold_price_views.gold_price_manager.get_price", return_value=fake_mt5_result) as mock_price, patch(
        "api.gold_price_views.gold_price_manager.get_price_for_user", return_value=fake_mt5_result
    ) as mock_user_price:
        response = GoldPriceView.as_view()(request)
        print("response status:", response.status_code)
        print("response data:", response.data)
        print("get_price called:", mock_price.call_count)
        print("get_price_for_user called:", mock_user_price.call_count)

    print("\n=== Test 4: GoldPriceView with user key uses user provider ===")
    # Delete any existing access first
    UserGoldAPIAccess.objects.filter(user=regular).delete()
    
    user_access = UserGoldAPIAccess.objects.create(
        user=regular,
        provider="twelvedata",
        api_key="user-gold-key",
        is_active=True,
    )
    
    # Verify has_credentials works
    print(f"User access created: provider={user_access.provider}, api_key={user_access.api_key[:10]}..., has_credentials={user_access.has_credentials}")

    reset_manager_cache()
    request = factory.get("/api/gold-price/")
    force_authenticate(request, user=regular)

    fake_user_result = {
        "success": True,
        "data": {"price": 1850},
        "price": 1850,
        "source": "twelvedata",
        "timestamp": timezone.now().isoformat(),
    }

    with patch("api.gold_price_views.gold_price_manager.get_price_for_user", return_value=fake_user_result) as mock_user_price, patch(
        "api.gold_price_views.gold_price_manager.get_price", return_value=fake_mt5_result
    ) as mock_price:
        response = GoldPriceView.as_view()(request)
        print("response status:", response.status_code)
        print("response data:", response.data)
        print("get_price_for_user called:", mock_user_price.call_count)
        print("get_price called:", mock_price.call_count)
        if mock_user_price.call_count > 0:
            print("✅ Test 4 PASSED: User key was used")
        else:
            print("❌ Test 4 FAILED: User key was not used")

    user_access.delete()
    APIConfiguration.objects.all().delete()
    reset_manager_cache()


if __name__ == "__main__":
    main()


"""
Tests for API key priority and MT5 fallback access
"""
import os
import django
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch, MagicMock
from django.utils import timezone

from core.models import APIConfiguration, UserGoldAPIAccess
from ai_module.provider_manager import get_provider_manager
from api.gold_price_views import GoldPriceView
from ai_module import provider_manager

User = get_user_model()


class APIKeyPriorityTests(TestCase):
    """Test API key resolution priority"""

    def setUp(self):
        """Set up test data"""
        # Get or create admin user (phone: 09035760718)
        self.admin = User.objects.get_or_create(
            username="09035760718",
            defaults={"is_staff": True, "is_superuser": True}
        )[0]
        
        # Get or create regular user
        self.regular = User.objects.get_or_create(
            username="test_user_regular",
            defaults={"is_staff": False, "is_superuser": False}
        )[0]
        
        # Clear all API configurations
        APIConfiguration.objects.all().delete()
        UserGoldAPIAccess.objects.all().delete()
        provider_manager._PROVIDER_MANAGERS.clear()

    def test_1_user_without_key_uses_admin_key(self):
        """Test that user without personal key uses admin key"""
        print("\n=== Test 1: User without personal key uses admin key ===")
        
        # Create admin key
        admin_key = APIConfiguration.objects.create(
            provider="openai",
            api_key="admin-shared-key",
            user=self.admin,
            is_active=True,
        )
        
        provider_manager._PROVIDER_MANAGERS.clear()
        provider = get_provider_manager(user=self.regular).providers["openai"]
        resolved_key = provider.get_api_key()
        
        self.assertEqual(resolved_key, "admin-shared-key", 
                        "User should use admin key when no personal key exists")
        print(f"✅ PASSED: Resolved key = {resolved_key}")

    def test_2_user_with_personal_key_takes_priority(self):
        """Test that user's personal key takes priority over admin key"""
        print("\n=== Test 2: User with personal key takes priority ===")
        
        # Create admin key
        admin_key = APIConfiguration.objects.create(
            provider="openai",
            api_key="admin-shared-key",
            user=self.admin,
            is_active=True,
        )
        
        # Create user's personal key
        user_key = APIConfiguration.objects.create(
            provider="openai",
            api_key="user-personal-key",
            user=self.regular,
            is_active=True,
        )
        
        provider_manager._PROVIDER_MANAGERS.clear()
        provider = get_provider_manager(user=self.regular).providers["openai"]
        resolved_key = provider.get_api_key()
        
        self.assertEqual(resolved_key, "user-personal-key",
                        "User's personal key should take priority")
        print(f"✅ PASSED: Resolved key = {resolved_key}")

    def test_3_gold_price_without_user_key_falls_back_to_mt5(self):
        """Test that GoldPriceView falls back to MT5 when user has no API key"""
        print("\n=== Test 3: GoldPriceView without user key falls back to MT5 ===")
        
        factory = APIRequestFactory()
        request = factory.get("/api/gold-price/")
        force_authenticate(request, user=self.regular)
        
        fake_mt5_result = {
            "success": True,
            "data": {"price": 1800},
            "price": 1800,
            "source": "mt5",
            "timestamp": timezone.now().isoformat(),
        }
        
        with patch("api.gold_price_views.gold_price_manager.get_price", 
                  return_value=fake_mt5_result) as mock_price, \
             patch("api.gold_price_views.gold_price_manager.get_price_for_user", 
                  return_value=fake_mt5_result) as mock_user_price:
            
            response = GoldPriceView.as_view()(request)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data.get('success'))
            self.assertEqual(response.data.get('access_type'), 'mt5_delegate')
            self.assertTrue(response.data.get('allow_mt5_access'))
            self.assertEqual(mock_price.call_count, 1)
            self.assertEqual(mock_user_price.call_count, 0)
            
            print(f"✅ PASSED: MT5 fallback used, get_price called {mock_price.call_count} times")

    def test_4_gold_price_with_user_key_uses_user_provider(self):
        """Test that GoldPriceView uses user's API key when available"""
        print("\n=== Test 4: GoldPriceView with user key uses user provider ===")
        
        # Create user's gold API access
        user_access = UserGoldAPIAccess.objects.create(
            user=self.regular,
            provider="twelvedata",
            api_key="user-gold-key",
            is_active=True,
        )
        
        # Verify has_credentials
        self.assertTrue(user_access.has_credentials, 
                       "User access should have valid credentials")
        print(f"User access: provider={user_access.provider}, "
              f"has_credentials={user_access.has_credentials}")
        
        factory = APIRequestFactory()
        request = factory.get("/api/gold-price/")
        force_authenticate(request, user=self.regular)
        
        fake_user_result = {
            "success": True,
            "data": {"price": 1850},
            "price": 1850,
            "source": "twelvedata",
            "timestamp": timezone.now().isoformat(),
        }
        
        fake_mt5_result = {
            "success": True,
            "data": {"price": 1800},
            "price": 1800,
            "source": "mt5",
            "timestamp": timezone.now().isoformat(),
        }
        
        with patch("api.gold_price_views.gold_price_manager.get_price_for_user", 
                  return_value=fake_user_result) as mock_user_price, \
             patch("api.gold_price_views.gold_price_manager.get_price", 
                  return_value=fake_mt5_result) as mock_price:
            
            response = GoldPriceView.as_view()(request)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data.get('success'))
            self.assertEqual(mock_user_price.call_count, 1,
                           "get_price_for_user should be called when user has credentials")
            self.assertEqual(mock_price.call_count, 0,
                           "get_price should not be called when user has credentials")
            self.assertEqual(response.data.get('access_type'), 'user_api')
            self.assertEqual(response.data.get('source'), 'twelvedata')
            
            print(f"✅ PASSED: User key used, get_price_for_user called {mock_user_price.call_count} times")

    def test_5_admin_keys_hidden_from_regular_users(self):
        """Test that admin API keys are hidden in serializer"""
        print("\n=== Test 5: Admin keys hidden from regular users ===")
        
        from api.serializers import APIConfigurationSerializer
        from rest_framework.test import APIRequestFactory
        
        # Create admin key
        admin_key = APIConfiguration.objects.create(
            provider="openai",
            api_key="admin-secret-key",
            user=self.admin,
            is_active=True,
        )
        
        factory = APIRequestFactory()
        request = factory.get("/api/api-configurations/")
        force_authenticate(request, user=self.regular)
        
        serializer = APIConfigurationSerializer(
            admin_key,
            context={'request': request}
        )
        data = serializer.data
        
        # Regular user should not see admin's API key
        self.assertIsNone(data.get('api_key'),
                         "Regular user should not see admin's API key")
        print(f"✅ PASSED: Admin key hidden (api_key={data.get('api_key')})")
        
        # Admin should see their own key
        force_authenticate(request, user=self.admin)
        serializer = APIConfigurationSerializer(
            admin_key,
            context={'request': request}
        )
        data = serializer.data
        self.assertEqual(data.get('api_key'), "admin-secret-key",
                        "Admin should see their own API key")
        print(f"✅ PASSED: Admin can see their own key")


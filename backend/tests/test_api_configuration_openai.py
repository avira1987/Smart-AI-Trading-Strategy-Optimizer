from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import APIConfiguration
from ai_module.providers import OpenAIProvider, ProviderResult


class _DummyOpenAIProvider(OpenAIProvider):
    """Helper provider that returns a predefined result."""

    def __init__(self, result: ProviderResult, should_raise: bool = False) -> None:
        super().__init__()
        self._result = result
        self._should_raise = should_raise

    def generate(self, prompt, generation_config, metadata=None):  # type: ignore[override]
        if self._should_raise:
            raise RuntimeError(self._result.error or "boom")
        return self._result


class APIConfigurationOpenAITest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="tester", email="tester@example.com", password="pass12345"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.config = APIConfiguration.objects.create(
            provider="openai",
            api_key="sk-test",
            is_active=True,
            user=self.user,
        )

    def _url(self) -> str:
        return reverse("api-test", kwargs={"pk": self.config.pk})

    def test_openai_invalid_key_returns_user_friendly_message(self):
        provider_result = ProviderResult(
            success=False,
            error="openai error: invalid_api_key",
            status_code=401,
            raw_response={"error": {"message": "Invalid API key"}},
        )
        dummy_provider = _DummyOpenAIProvider(provider_result)

        with patch("api.views.get_registered_providers", return_value={"openai": dummy_provider}):
            response = self.client.post(self._url())

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["provider"], "openai")
        self.assertEqual(body["status"], "error")
        self.assertIn("Authentication failed", body["message"])
        self.assertEqual(body["status_code"], 401)

    def test_openai_exception_converted_to_error_response(self):
        provider_result = ProviderResult(
            success=False,
            error="timeout",
        )
        dummy_provider = _DummyOpenAIProvider(provider_result, should_raise=True)

        with patch("api.views.get_registered_providers", return_value={"openai": dummy_provider}):
            response = self.client.post(self._url())

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["provider"], "openai")
        self.assertEqual(body["status"], "error")
        self.assertIn("AI provider test failed", body["message"])


class APIConfigurationChatGPTAliasTest(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="chatgpt-user", email="chatgpt@example.com", password="pass12345"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_can_create_chatgpt_configuration_via_api(self):
        payload = {
            "provider": "chatgpt",
            "api_key": "sk-live-chatgpt-1234567890abcdef123456",
            "is_active": True,
        }
        response = self.client.post(reverse("api-list"), payload, format="json")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            APIConfiguration.objects.filter(provider="chatgpt", user=self.user).exists()
        )

    @patch("api.views.get_registered_providers")
    def test_chatgpt_alias_uses_openai_provider_in_test_endpoint(self, mock_providers):
        provider_result = ProviderResult(
            success=True,
            text='{"status":"ok"}',
            raw_response={"choices": []},
        )
        dummy_provider = _DummyOpenAIProvider(provider_result)
        mock_providers.return_value = {
            "openai": dummy_provider,
            "chatgpt": dummy_provider,
        }

        config = APIConfiguration.objects.create(
            provider="chatgpt",
            api_key="sk-live-chatgpt-abcdef1234567890",
            is_active=True,
            user=self.user,
        )

        response = self.client.post(reverse("api-test", kwargs={"pk": config.pk}))

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["provider"], "chatgpt")
        self.assertEqual(body["status"], "success")
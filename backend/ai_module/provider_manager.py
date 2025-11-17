import logging
import time
from typing import Any, Dict, List, Optional

from django.conf import settings

from .providers import ProviderAttempt, ProviderResult, get_registered_providers


LOGGER = logging.getLogger("ai.provider_manager")


class AIProviderManager:
    """
    Coordinates requests across multiple AI providers with fallback logic.
    """

    def __init__(self) -> None:
        self.providers = get_registered_providers()

    @staticmethod
    def _normalize_provider_name(provider: str) -> Optional[str]:
        if not provider:
            return None

        normalized = provider.strip().lower()
        alias_map = {
            "chatgpt": "openai",
            "gpt": "openai",
            "gpt-4": "openai",
            "gpt4": "openai",
        }
        resolved = alias_map.get(normalized, normalized)
        return resolved if resolved else None

    def _get_priority_list(self) -> List[str]:
        priority_config = getattr(settings, "AI_PROVIDER_PRIORITY", [])
        if isinstance(priority_config, str):
            priority = [priority_config]
        else:
            priority = list(priority_config) if priority_config else []

        normalized: List[str] = []
        seen: set[str] = set()

        for provider_name in priority:
            resolved = self._normalize_provider_name(provider_name)
            if not resolved:
                continue
            if resolved not in self.providers:
                continue
            if resolved not in seen:
                normalized.append(resolved)
                seen.add(resolved)

        if "openai" in seen:
            return ["openai"]

        if not normalized:
            fallback_priority = ["openai"]
            normalized = [
                name for name in fallback_priority if name in self.providers
            ]

        if not normalized:
            normalized = [
                name
                for name in ["gemini", "cohere", "openrouter", "together_ai", "deepinfra", "groq"]
                if name in self.providers
            ]

        return normalized

    def _log_attempt(self, attempt: ProviderAttempt) -> None:
        if getattr(settings, "AI_PROVIDER_ENABLE_LOGGING", True):
            LOGGER.info(
                "AI provider attempt",
                extra={
                    "provider": attempt.provider,
                    "success": attempt.success,
                    "error": attempt.error,
                    "status_code": attempt.status_code,
                    "latency_ms": attempt.latency_ms,
                    "tokens_used": attempt.tokens_used,
                },
            )

    def generate(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        attempts: List[ProviderAttempt] = []
        providers_tried = 0

        for provider_name in self._get_priority_list():
            provider = self.providers.get(provider_name)
            if not provider:
                continue

            providers_tried += 1

            if not provider.is_available():
                attempt = ProviderAttempt(
                    provider=provider_name,
                    success=False,
                    error="missing_api_key",
                    status_code=None,
                    latency_ms=None,
                )
                attempts.append(attempt)
                self._log_attempt(attempt)
                continue

            start_time = time.perf_counter()
            result = provider.generate(prompt, generation_config, metadata=metadata)
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            if not result.attempts:
                attempt = ProviderAttempt(
                    provider=provider_name,
                    success=result.success,
                    error=result.error,
                    status_code=result.status_code,
                    latency_ms=latency_ms,
                    tokens_used=result.tokens_used,
                )
                attempts.append(attempt)
                self._log_attempt(attempt)
            else:
                for attempt in result.attempts:
                    if attempt.latency_ms is None:
                        attempt.latency_ms = latency_ms
                    attempts.append(attempt)
                    self._log_attempt(attempt)

            if result.success and result.text:
                result.provider = provider_name
                result.attempts = attempts
                return result

        error_message = (
            "All AI providers failed"
            if providers_tried
            else "No AI providers configured or enabled"
        )
        failure = ProviderResult(success=False, error=error_message, attempts=attempts)
        return failure

    def has_available_provider(self) -> bool:
        for provider_name in self._get_priority_list():
            provider = self.providers.get(provider_name)
            if provider and provider.is_available():
                return True
        return False


_PROVIDER_MANAGER: Optional[AIProviderManager] = None


def get_provider_manager() -> AIProviderManager:
    global _PROVIDER_MANAGER
    if _PROVIDER_MANAGER is None:
        _PROVIDER_MANAGER = AIProviderManager()
    return _PROVIDER_MANAGER


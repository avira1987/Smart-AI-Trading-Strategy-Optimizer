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

    def __init__(self, user=None) -> None:
        self.providers = get_registered_providers()
        self.user = user
        self._apply_user_context(user)

    def _apply_user_context(self, user) -> None:
        for provider in self.providers.values():
            set_context = getattr(provider, "set_user_context", None)
            if callable(set_context):
                set_context(user)

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
        # Ensure user context is always fresh before generating
        self._apply_user_context(self.user)
        
        user_id = None
        if self.user and getattr(self.user, "is_authenticated", False):
            user_id = getattr(self.user, "pk", None) or getattr(self.user, "id", None)
        
        LOGGER.info(
            f"AIProviderManager.generate called (user_id={user_id}, prompt_length={len(prompt)})"
        )
        
        attempts: List[ProviderAttempt] = []
        providers_tried = 0
        priority_list = self._get_priority_list()
        LOGGER.info(f"Provider priority list: {priority_list}")

        for provider_name in priority_list:
            provider = self.providers.get(provider_name)
            if not provider:
                LOGGER.warning(f"Provider {provider_name} not found in providers dict")
                continue

            providers_tried += 1
            LOGGER.info(f"Trying provider {provider_name} (attempt {providers_tried})")

            if not provider.is_available():
                api_key = provider.get_api_key()
                error_msg = f"Provider {provider_name} not available - missing API key"
                LOGGER.warning(
                    f"Provider {provider_name} not available (user_id={user_id}, "
                    f"has_api_key={bool(api_key)}, api_key_length={len(api_key) if api_key else 0})"
                )
                attempt = ProviderAttempt(
                    provider=provider_name,
                    success=False,
                    error=error_msg,
                    status_code=None,
                    latency_ms=None,
                )
                attempts.append(attempt)
                self._log_attempt(attempt)
                continue

            start_time = time.perf_counter()
            LOGGER.info(f"Calling provider {provider_name}.generate()")
            result = provider.generate(prompt, generation_config, metadata=metadata)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            LOGGER.info(
                f"Provider {provider_name} returned: success={result.success}, "
                f"error={result.error}, latency={latency_ms:.2f}ms"
            )

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
        LOGGER.error(
            f"All providers failed (user_id={user_id}, providers_tried={providers_tried}, "
            f"attempts={len(attempts)}): {error_message}"
        )
        if attempts:
            for attempt in attempts:
                LOGGER.error(
                    f"  Provider {attempt.provider}: success={attempt.success}, "
                    f"error={attempt.error}, status_code={attempt.status_code}"
                )
        failure = ProviderResult(success=False, error=error_message, attempts=attempts)
        return failure

    def has_available_provider(self) -> bool:
        # Ensure user context is always fresh before checking availability
        self._apply_user_context(self.user)
        
        user_id = None
        if self.user and getattr(self.user, "is_authenticated", False):
            user_id = getattr(self.user, "pk", None) or getattr(self.user, "id", None)
        
        for provider_name in self._get_priority_list():
            provider = self.providers.get(provider_name)
            if provider:
                is_available = provider.is_available()
                if is_available:
                    LOGGER.info(
                        f"Found available provider: {provider_name} (user_id={user_id})"
                    )
                    return True
                else:
                    api_key = provider.get_api_key()
                    LOGGER.debug(
                        f"Provider {provider_name} not available (user_id={user_id}, "
                        f"has_api_key={bool(api_key)})"
                    )
        LOGGER.warning(f"No available providers found (user_id={user_id})")
        return False


_PROVIDER_MANAGERS: Dict[str, AIProviderManager] = {}


def _manager_cache_key(user) -> str:
    if user and getattr(user, "is_authenticated", False):
        user_id = getattr(user, "pk", None) or getattr(user, "id", None)
        if user_id is not None:
            return f"user:{user_id}"
    return "anonymous"


def get_provider_manager(user=None) -> AIProviderManager:
    key = _manager_cache_key(user)
    manager = _PROVIDER_MANAGERS.get(key)
    if manager is None:
        manager = AIProviderManager(user=user)
        _PROVIDER_MANAGERS[key] = manager
    else:
        manager.user = user
        manager._apply_user_context(user)
    return manager


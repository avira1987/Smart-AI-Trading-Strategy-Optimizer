import logging
import time
from typing import Any, Dict, List, Optional

from django.conf import settings

from .providers import ProviderAttempt, ProviderResult, get_registered_providers
from .rate_limiter import get_rate_limiter
from .token_monitor import get_token_monitor


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
        """
        Force ChatGPT/OpenAI to be the sole provider for strategy processing.
        Any configured fallback providers are ignored intentionally.
        """
        if "openai" in self.providers:
            return ["openai"]
        return []

    def _log_attempt(self, attempt: ProviderAttempt) -> None:
        if getattr(settings, "AI_PROVIDER_ENABLE_LOGGING", True):
            LOGGER.debug(
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
        
        LOGGER.debug(
            f"AIProviderManager.generate called (user_id={user_id}, prompt_length={len(prompt)})"
        )
        
        attempts: List[ProviderAttempt] = []
        providers_tried = 0
        priority_list = self._get_priority_list()
        LOGGER.debug(f"Provider priority list: {priority_list}")

        for provider_name in priority_list:
            provider = self.providers.get(provider_name)
            if not provider:
                LOGGER.warning(f"Provider {provider_name} not found in providers dict")
                continue

            providers_tried += 1
            LOGGER.debug(f"Trying provider {provider_name} (attempt {providers_tried})")

            if not provider.is_available():
                api_key = provider.get_api_key()
                if not api_key or not api_key.strip():
                    error_msg = "کلید ChatGPT (OpenAI) تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید OpenAI را اضافه کنید."
                elif len(api_key) < 20:
                    error_msg = "کلید ChatGPT (OpenAI) نامعتبر است. لطفاً کلید معتبر OpenAI را در تنظیمات > پیکربندی API وارد کنید."
                else:
                    error_msg = f"ارائه‌دهنده {provider_name} در دسترس نیست. لطفاً کلید API را بررسی کنید."
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

            # Rate limiting and token monitoring
            rate_limiter = get_rate_limiter()
            token_monitor = get_token_monitor()
            
            # Estimate tokens for rate limiting
            estimated_tokens = token_monitor.estimate_tokens(prompt) + 100  # Add buffer for response
            
            # Check rate limit before making request
            if not rate_limiter.acquire(estimated_tokens, timeout=300):
                error_msg = "Rate limit: Cannot acquire capacity for request. Please try again later."
                LOGGER.warning(f"[PROVIDER_MANAGER] Rate limit exceeded (user_id={user_id})")
                attempt = ProviderAttempt(
                    provider=provider_name,
                    success=False,
                    error=error_msg,
                    status_code=429,
                    latency_ms=None,
                )
                attempts.append(attempt)
                self._log_attempt(attempt)
                continue
            
            start_time = time.perf_counter()
            LOGGER.info(f"[PROVIDER_MANAGER] Calling provider {provider_name}.generate() (user_id={user_id})")
            LOGGER.debug(f"[PROVIDER_MANAGER] Prompt length: {len(prompt)}, Config: {generation_config}")
            result = provider.generate(prompt, generation_config, metadata=metadata)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            
            # Handle 429 errors with rate limiter
            if result.status_code == 429:
                rate_limiter.handle_429_error()
            
            # Record token usage
            if result.tokens_used:
                rate_limiter.record_tokens(result.tokens_used)
                token_monitor.log_request(
                    prompt=prompt,
                    response_text=result.text if result.success else "",
                    tokens_used=result.tokens_used,
                    provider=provider_name,
                    user_id=user_id
                )
            LOGGER.info(
                f"[PROVIDER_MANAGER] Provider {provider_name} returned: success={result.success}, "
                f"status_code={result.status_code}, latency={latency_ms:.2f}ms"
            )
            if not result.success:
                # Log provider failure - but use appropriate log level
                if result.status_code == 429:
                    # Rate Limit - log once with summary (detailed error is in provider response)
                    LOGGER.warning(f"[PROVIDER_MANAGER] Provider {provider_name} failed: Rate Limit (429)")
                    # Detailed error info available in result.error if needed for debugging
                    LOGGER.debug(f"[PROVIDER_MANAGER] Rate Limit details: {result.error[:200] if result.error else 'N/A'}")
                else:
                    # Other errors - log warning with error summary
                    LOGGER.warning(f"[PROVIDER_MANAGER] Provider {provider_name} failed: {result.error[:100] if result.error else 'Unknown error'}...")

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

        # Build a more helpful error message
        if not providers_tried:
            error_message = "کلید ChatGPT (OpenAI) تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید OpenAI را اضافه کنید."
        elif attempts:
            # Get the first error message from attempts
            first_error = attempts[0].error if attempts else None
            first_status_code = attempts[0].status_code if attempts else None
            
            # Handle Rate Limit (429) specifically
            if first_status_code == 429:
                # Log Rate Limit error once with summary (details are logged at provider level)
                LOGGER.warning(f"[PROVIDER_MANAGER] Rate Limit (429) from OpenAI API - Provider: {attempts[0].provider}")
                # Detailed error info is already logged at provider level, no need to repeat
                error_message = "محدودیت نرخ استفاده از ChatGPT (Rate Limit) رسیده است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید. برای افزایش محدودیت، به حساب OpenAI خود مراجعه کنید."
            elif first_status_code and first_status_code != 429:
                # Log non-429 errors for diagnosis
                LOGGER.warning(f"[PROVIDER_MANAGER] Non-429 error detected: status_code={first_status_code}, error={first_error}")
            # Handle Invalid API key (401)
            elif first_status_code == 401:
                error_message = "کلید ChatGPT (OpenAI) نامعتبر است. لطفاً کلید معتبر OpenAI را در تنظیمات > پیکربندی API وارد کنید."
            # Handle other errors
            elif first_error and ("کلید" in first_error or "API" in first_error or "ChatGPT" in first_error or "OpenAI" in first_error):
                error_message = first_error
            elif first_error and ("Rate limit" in first_error or "rate limit" in first_error):
                error_message = "محدودیت نرخ استفاده از ChatGPT (Rate Limit) رسیده است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید."
            else:
                error_message = f"خطا در استفاده از ChatGPT: {first_error or 'خطای نامشخص'}"
        else:
            error_message = "کلید ChatGPT (OpenAI) تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید OpenAI را اضافه کنید."
        
        # Log error summary in English only - avoid [FA] spam in console
        # Extract error type from Persian message for console logging
        error_type = "unknown_error"
        if attempts:
            first_status_code = attempts[0].status_code
            if first_status_code == 429:
                error_type = "RateLimit (429)"
            elif first_status_code == 401:
                error_type = "InvalidAPIKey (401)"
            elif first_status_code:
                error_type = f"Error ({first_status_code})"
        
        # Log summary in English - full details are in error_message (for files) and attempt details (for debugging)
        LOGGER.warning(
            f"All providers failed (user_id={user_id}, providers_tried={providers_tried}, attempts={len(attempts)}): {error_type}"
        )
        # Log attempt details only in debug mode to reduce console spam
        if attempts:
            for attempt in attempts:
                # Extract error type from error message (in English if possible)
                error_detail = attempt.error or "unknown"
                error_type_from_msg = error_detail
                if "Rate limit" in error_detail or "429" in str(attempt.status_code):
                    error_type_from_msg = "RateLimit (429)"
                elif "Invalid API key" in error_detail or "401" in str(attempt.status_code):
                    error_type_from_msg = "InvalidAPIKey (401)"
                elif len(error_detail) > 100:
                    error_type_from_msg = error_detail[:100] + "..."
                
                LOGGER.debug(
                    f"  Provider {attempt.provider}: success={attempt.success}, "
                    f"error={error_type_from_msg}, status_code={attempt.status_code}"
                )
        # Return clean error JSON without crashing
        failure = ProviderResult(success=False, error=error_message, attempts=attempts)
        
        # Log final failure summary
        LOGGER.warning(
            f"All providers failed after retries (user_id={user_id}, "
            f"providers_tried={providers_tried}, total_attempts={len(attempts)})"
        )
        
        return failure

    def has_available_provider(self) -> bool:
        # Ensure user context is always fresh before checking availability
        self._apply_user_context(self.user)
        
        user_id = None
        if self.user and getattr(self.user, "is_authenticated", False):
            user_id = getattr(self.user, "pk", None) or getattr(self.user, "id", None)
        
        priority_list = self._get_priority_list()
        LOGGER.debug(
            f"Checking provider availability (user_id={user_id}, priority_list={priority_list}, "
            f"providers={list(self.providers.keys())})"
        )
        
        for provider_name in priority_list:
            provider = self.providers.get(provider_name)
            if provider:
                api_key = provider.get_api_key()
                is_available = provider.is_available()
                LOGGER.debug(
                    f"Provider {provider_name}: is_available={is_available}, "
                    f"has_api_key={bool(api_key)}, api_key_length={len(api_key) if api_key else 0} (user_id={user_id})"
                )
                if is_available:
                    LOGGER.debug(
                        f"Found available provider: {provider_name} (user_id={user_id})"
                    )
                    return True
            else:
                LOGGER.warning(f"Provider {provider_name} not found in providers dict (available providers: {list(self.providers.keys())})")
        
        LOGGER.warning(f"No available providers found (user_id={user_id}, checked providers: {priority_list})")
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


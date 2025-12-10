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
        Prioritize GapGPT for strategy processing, but fallback to other providers if GapGPT is not available.
        """
        # Check if GapGPT is available first
        if "gapgpt" in self.providers:
            gapgpt_provider = self.providers.get("gapgpt")
            if gapgpt_provider and gapgpt_provider.is_available():
                return ["gapgpt"]
        
        # Fallback to other available providers if GapGPT is not available
        fallback_providers = []
        # Priority order for fallback: OpenAI, Gemini, then others
        preferred_fallback = ["openai", "gemini", "cohere", "openrouter", "together_ai", "deepinfra", "groq"]
        
        # Add all available preferred providers (they will be tried in order)
        for provider_name in preferred_fallback:
            if provider_name in self.providers:
                provider = self.providers.get(provider_name)
                if provider and provider.is_available():
                    fallback_providers.append(provider_name)
        
        # If no preferred providers are available, try any other available provider
        if not fallback_providers:
            for provider_name, provider in self.providers.items():
                if provider_name not in preferred_fallback and provider_name != "gapgpt":
                    if provider and provider.is_available():
                        fallback_providers.append(provider_name)
                        # Only add the first available non-preferred provider to avoid too many fallbacks
                        break
        
        return fallback_providers if fallback_providers else []

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
                    if provider_name == "gapgpt":
                        error_msg = "کلید GapGPT تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید GapGPT را اضافه کنید."
                    else:
                        error_msg = "کلید ChatGPT (OpenAI) تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید OpenAI را اضافه کنید."
                elif len(api_key) < 20:
                    if provider_name == "gapgpt":
                        error_msg = "کلید GapGPT نامعتبر است. لطفاً کلید معتبر GapGPT را در تنظیمات > پیکربندی API وارد کنید."
                    else:
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
            # Check if GapGPT exists but is not available
            if "gapgpt" in self.providers:
                gapgpt_provider = self.providers.get("gapgpt")
                if gapgpt_provider and not gapgpt_provider.is_available():
                    error_message = "کلید GapGPT تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید GapGPT را اضافه کنید. یا می‌توانید از ارائه‌دهنده‌های دیگر مانند OpenAI یا Gemini استفاده کنید."
                else:
                    error_message = "هیچ ارائه‌دهنده AI در دسترس نیست. لطفاً در تنظیمات > پیکربندی API، حداقل یک کلید API (GapGPT، OpenAI، یا Gemini) را اضافه کنید."
            else:
                error_message = "هیچ ارائه‌دهنده AI در دسترس نیست. لطفاً در تنظیمات > پیکربندی API، حداقل یک کلید API (GapGPT، OpenAI، یا Gemini) را اضافه کنید."
        elif attempts:
            # Get the first error message from attempts
            first_error = attempts[0].error if attempts else None
            first_status_code = attempts[0].status_code if attempts else None
            
            # Handle Rate Limit (429) specifically
            if first_status_code == 429:
                # Log Rate Limit error once with summary (details are logged at provider level)
                provider_name_for_log = attempts[0].provider if attempts else "unknown"
                LOGGER.warning(f"[PROVIDER_MANAGER] Rate Limit (429) from {provider_name_for_log} API - Provider: {provider_name_for_log}")
                # Detailed error info is already logged at provider level, no need to repeat
                if provider_name_for_log == "gapgpt":
                    error_message = "محدودیت نرخ استفاده از GapGPT (Rate Limit) رسیده است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید."
                else:
                    error_message = "محدودیت نرخ استفاده از ChatGPT (Rate Limit) رسیده است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید. برای افزایش محدودیت، به حساب OpenAI خود مراجعه کنید."
            # Handle Invalid API key (401)
            elif first_status_code == 401:
                provider_name_for_log = attempts[0].provider if attempts else "unknown"
                if provider_name_for_log == "gapgpt":
                    error_message = "کلید GapGPT نامعتبر است. لطفاً کلید معتبر GapGPT را در تنظیمات > پیکربندی API وارد کنید."
                elif provider_name_for_log == "openai":
                    error_message = "کلید OpenAI نامعتبر است. لطفاً کلید معتبر OpenAI را در تنظیمات > پیکربندی API وارد کنید."
                else:
                    error_message = f"کلید API برای {provider_name_for_log} نامعتبر است. لطفاً کلید معتبر را در تنظیمات > پیکربندی API وارد کنید."
            # Handle Forbidden (403) - API key might be invalid or account suspended
            elif first_status_code == 403:
                provider_name_for_log = attempts[0].provider if attempts else "unknown"
                LOGGER.warning(
                    f"[PROVIDER_MANAGER] Forbidden (403) error detected: "
                    f"provider={provider_name_for_log}, status_code={first_status_code}, "
                    f"error='{first_error[:200] if first_error else None}'"
                )
                
                # بررسی و ترجمه خطاهای چینی مربوط به اعتبار
                is_quota_error = False
                remaining = 'نامشخص'
                required = 'نامشخص'
                
                # بررسی خطاهای quota (چینی و انگلیسی) - فقط در صورت وجود شواهد مشخص
                import re
                if first_error:
                    first_error_lower = first_error.lower()
                    # بررسی برای پیام‌های چینی - باید هم 剩余额度 یا 需要 باشد
                    has_chinese_quota_indicators = any(char in first_error for char in ['预扣费', '剩余额度', '需要额度'])
                    # بررسی برای پیام‌های انگلیسی - باید هم quota و هم remain/need باشد
                    has_english_quota_indicators = (
                        ('quota' in first_error_lower) and 
                        (('remain' in first_error_lower) or ('remaining' in first_error_lower) or ('need' in first_error_lower) or ('insufficient' in first_error_lower))
                    )
                    
                    if has_chinese_quota_indicators:
                        is_quota_error = True
                        remaining_match = re.search(r'剩余额度[：:]\s*\$?([\d.]+)', first_error)
                        required_match = re.search(r'需要[^：:]*[：:]\s*\$?([\d.]+)', first_error)
                        
                        remaining = remaining_match.group(1) if remaining_match else 'نامشخص'
                        required = required_match.group(1) if required_match else 'نامشخص'
                    elif has_english_quota_indicators:
                        is_quota_error = True
                        # استخراج مقادیر از پیام انگلیسی
                        remaining_match = re.search(r'(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)', first_error, re.IGNORECASE)
                        required_match = re.search(r'need[\s_]?quota[：:\s]*\$?\??([\d.]+)', first_error, re.IGNORECASE)
                        
                        if remaining_match:
                            remaining = remaining_match.group(1)
                        if required_match:
                            required = required_match.group(1)
                
                # ارسال پیامک به ادمین در صورت اتمام اعتبار
                if is_quota_error:
                    try:
                        from ai_module.gapgpt_client import _notify_admin_gapgpt_quota_exhausted
                        _notify_admin_gapgpt_quota_exhausted(remaining, required)
                    except Exception as e:
                        LOGGER.warning(f"Failed to notify admin about GapGPT quota: {e}")
                
                # پیام دقیق‌تر برای کاربران
                if is_quota_error:
                    # Only show quota message if it's actually a quota error
                    error_message = "سرویس پردازش هوش مصنوعی موقتاً در دسترس نیست. لطفاً چند دقیقه دیگر دوباره تلاش کنید."
                elif first_error:
                    # Show the actual error message from the provider
                    error_lower = first_error.lower()
                    if 'model' in error_lower and ('not found' in error_lower or 'unavailable' in error_lower):
                        error_message = f"مدل انتخابی در دسترس نیست. لطفاً مدل دیگری انتخاب کنید."
                    elif 'permission' in error_lower or 'forbidden' in error_lower:
                        error_message = f"دسترسی رد شد. لطفاً کلید API و وضعیت حساب را بررسی کنید."
                    elif 'group' in error_lower or '分组' in first_error:
                        error_message = f"مدل در گروه فعلی در دسترس نیست. لطفاً مدل دیگری امتحان کنید."
                    elif "کلید" in first_error or "API" in first_error or "GapGPT" in first_error or "gapgpt" in first_error.lower():
                        error_message = first_error
                    else:
                        # Show the actual error message
                        error_message = f"خطا در استفاده از سرویس: {first_error}"
                else:
                    # Fallback if no error message
                    error_message = "دسترسی رد شد (403). لطفاً کلید API و وضعیت حساب را بررسی کنید."
            # Handle other status codes
            elif first_status_code and first_status_code != 429 and first_status_code != 401 and first_status_code != 403:
                # Log non-standard errors for diagnosis
                LOGGER.warning(f"[PROVIDER_MANAGER] Non-standard error detected: status_code={first_status_code}, error={first_error}")
                if first_error and ("کلید" in first_error or "API" in first_error or "GapGPT" in first_error or "gapgpt" in first_error.lower()):
                    error_message = first_error
                else:
                    error_message = f"خطا در استفاده از GapGPT (کد خطا: {first_status_code}): {first_error or 'خطای نامشخص'}"
            # Handle error message patterns when status_code is None or not set
            elif first_error and ("کلید" in first_error or "API" in first_error or "GapGPT" in first_error or "gapgpt" in first_error.lower()):
                error_message = first_error
            elif first_error and ("Rate limit" in first_error or "rate limit" in first_error):
                error_message = "محدودیت نرخ استفاده از GapGPT (Rate Limit) رسیده است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید."
            else:
                error_message = f"خطا در استفاده از GapGPT: {first_error or 'خطای نامشخص'}"
        else:
            error_message = "کلید GapGPT تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید GapGPT را اضافه کنید."
        
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


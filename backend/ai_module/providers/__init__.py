import json
import logging
import os
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

try:
    from core.models import APIConfiguration, UserProfile  # type: ignore
except Exception:  # pragma: no cover - during migrations/tests without db
    APIConfiguration = None
    UserProfile = None


LOGGER = logging.getLogger("ai.providers")


@dataclass
class ProviderAttempt:
    provider: str
    success: bool
    error: Optional[str] = None
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    tokens_used: Optional[int] = None


@dataclass
class ProviderResult:
    success: bool
    text: str = ""
    provider: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    tokens_used: Optional[int] = None
    raw_response: Optional[Any] = None
    attempts: List[ProviderAttempt] = field(default_factory=list)


def _get_api_key(provider_name: str, env_key: Optional[str], user=None) -> str:
    """
    Get API key from database first, then fallback to environment variables.
    Priority:
    1. User-specific key from DB
    2. System-wide key from DB (user=None)
    3. Admin key from DB
    4. Any active key from DB
    5. Environment variable (as fallback)
    """
    # First, try to get from database
    provider_candidates: List[str] = [provider_name] if provider_name else []
    provider_alias_map = getattr(settings, "AI_PROVIDER_NAME_ALIASES", {})
    
    # Add direct aliases
    provider_candidates.extend(provider_alias_map.get(provider_name, []))
    
    # Build reverse alias map
    reverse_alias_map: Dict[str, str] = {}
    for main_provider, aliases in provider_alias_map.items():
        for alias in aliases:
            reverse_alias_map[alias] = main_provider
            if provider_name == alias and main_provider not in provider_candidates:
                provider_candidates.append(main_provider)
    
    # Remove duplicates
    seen = set()
    unique_candidates = []
    for candidate in provider_candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            unique_candidates.append(candidate)
    provider_candidates = unique_candidates

    if provider_candidates and APIConfiguration is not None:
        try:
            # 1. User-specific API key (if request user provided)
            if user is not None and getattr(user, "is_authenticated", False):
                user_config = (
                    APIConfiguration.objects.filter(
                        provider__in=provider_candidates,
                        is_active=True,
                        user=user,
                    )
                    .order_by("-updated_at", "-created_at")
                    .first()
                )
                if user_config and user_config.api_key:
                    # Log only in debug mode - too many logs in console
                    LOGGER.debug(f"Found user-specific API key for provider={provider_name}, user_id={user.id}, provider_in_db={user_config.provider}")
                    return user_config.api_key.strip()

            # 2. System-wide API key (user=None)
            system_config = (
                APIConfiguration.objects.filter(
                    provider__in=provider_candidates,
                    is_active=True,
                    user__isnull=True,
                )
                .order_by("-updated_at", "-created_at")
                .first()
            )
            if system_config and system_config.api_key:
                # Log only in debug mode - too many logs in console
                LOGGER.debug(f"Found system-wide API key for provider={provider_name}, provider_in_db={system_config.provider}")
                return system_config.api_key.strip()

            # 3. Admin-provided API keys
            admin_phone = getattr(settings, "ADMIN_PHONE_NUMBER", "09035760718")
            admin_user_ids: List[int] = []
            if admin_phone and UserProfile is not None:
                try:
                    admin_user_ids = list(
                        UserProfile.objects.filter(phone=admin_phone).values_list("user_id", flat=True)
                    )
                except Exception:
                    admin_user_ids = []
            
            if admin_user_ids:
                admin_config = (
                    APIConfiguration.objects.filter(
                        provider__in=provider_candidates,
                        is_active=True,
                        user_id__in=admin_user_ids,
                    )
                    .order_by("-updated_at", "-created_at")
                    .first()
                )
                if admin_config and admin_config.api_key:
                    LOGGER.info(f"Found admin API key for provider={provider_name}, admin_user_ids={admin_user_ids}, provider_in_db={admin_config.provider}")
                    return admin_config.api_key.strip()

            # 4. Fallback to any active key
            config = (
                APIConfiguration.objects.filter(
                    provider__in=provider_candidates,
                    is_active=True,
                )
                .order_by("-updated_at", "-created_at")
                .first()
            )
            if config and config.api_key:
                LOGGER.info(f"Found fallback API key for provider={provider_name}, provider_in_db={config.provider}")
                return config.api_key.strip()
                
        except Exception as db_error:
            LOGGER.warning(f"Error fetching API key from database: {db_error}")
    
    # Fallback to environment variable if no DB key found
    env_candidates: List[str] = []
    if env_key:
        env_candidates.append(env_key)
        env_alias_map = getattr(settings, "AI_ENV_KEY_ALIASES", {})
        env_candidates.extend(env_alias_map.get(env_key, []))

    for candidate in env_candidates:
        key = os.environ.get(candidate, "").strip()
        if key:
            LOGGER.debug(f"Using environment variable API key for {provider_name} (from {candidate})")
            return key
    
    # Log if no key found
    LOGGER.warning(
        f"No API key found for provider={provider_name} (searched candidates={provider_candidates}, "
        f"user={user.id if user and hasattr(user, 'id') else None})"
    )
    # Also log available API configs for debugging
    try:
        if APIConfiguration is not None:
            all_configs = APIConfiguration.objects.filter(is_active=True).values('provider', 'user_id', 'is_active')
            LOGGER.info(f"Available API configs in DB: {list(all_configs)}")
    except Exception as e:
        LOGGER.debug(f"Could not query API configs: {e}")
    
    return ""


class BaseProvider:
    name: str = ""
    env_key: Optional[str] = None
    default_model: Optional[str] = None

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"ai.providers.{self.name or 'unknown'}")
        self._user_context = None

    def set_user_context(self, user) -> None:
        """Attach current request user for API key resolution."""
        self._user_context = user

    def get_api_key(self) -> str:
        return _get_api_key(self.name, self.env_key, user=self._user_context)

    def is_available(self) -> bool:
        """Check if provider is available (has a valid-looking API key)"""
        api_key = self.get_api_key()
        if not api_key or not api_key.strip():
            return False
        
        # Validate that the key doesn't look like a placeholder/dummy
        api_key_lower = api_key.lower().strip()
        
        # Common placeholder patterns to reject
        placeholder_patterns = [
            'your-',
            'your_',
            'placeholder',
            'dummy',
            'test-',
            'test_',
            'example',
            'xxxxx',
            '*****',
            'sk-test',
            'sk-dummy',
            'api-key-here',
            'enter-your',
            'paste-your',
        ]
        
        # Check if key looks like a placeholder
        for pattern in placeholder_patterns:
            if pattern in api_key_lower:
                self.logger.warning(
                    f"API key for {self.name} looks like a placeholder (contains '{pattern}')"
                )
                return False
        
        # For OpenAI, check that it starts with 'sk-' and has reasonable length
        if self.name == 'openai':
            if not api_key.startswith('sk-'):
                self.logger.warning(
                    f"OpenAI API key doesn't start with 'sk-': {api_key[:10]}..."
                )
                return False
            if len(api_key) < 20:  # OpenAI keys are typically 50+ characters
                self.logger.warning(
                    f"OpenAI API key seems too short (length: {len(api_key)})"
                )
                return False
        
        # For Gemini, check that it has reasonable length
        if self.name == 'gemini':
            if len(api_key) < 20:  # Gemini keys are typically 30+ characters
                self.logger.warning(
                    f"Gemini API key seems too short (length: {len(api_key)})"
                )
                return False
        
        return True

    def get_model(self) -> Optional[str]:
        model_map = getattr(settings, "AI_PROVIDER_DEFAULT_MODELS", {})
        if self.name in model_map and model_map[self.name]:
            return model_map[self.name]
        return self.default_model

    def get_temperature(self) -> float:
        return float(getattr(settings, "AI_PROVIDER_DEFAULT_TEMPERATURE", 0.3))

    def get_timeout(self) -> float:
        return float(getattr(settings, "AI_PROVIDER_HTTP_TIMEOUT", 30))

    def build_system_prompt(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        base_prompt = (
            "You are an AI assistant that must strictly return valid, compact JSON with double quoted keys."
        )
        if metadata and metadata.get("system_prompt"):
            base_prompt = metadata["system_prompt"]
        return base_prompt

    def format_messages(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        system_prompt = self.build_system_prompt(metadata)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

    def generate(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        raise NotImplementedError

    def _extract_tokens(self, payload: Dict[str, Any]) -> Optional[int]:
        usage = payload.get("usage") if isinstance(payload, dict) else None
        if isinstance(usage, dict):
            for key in ("total_tokens", "output_tokens", "completion_tokens"):
                value = usage.get(key)
                if isinstance(value, int):
                    return value
            try:
                output = usage.get("output", usage.get("output_tokens"))
                if isinstance(output, (int, float)):
                    return int(output)
            except Exception:
                pass
        return None


class GeminiProvider(BaseProvider):
    name = "gemini"
    env_key = "GEMINI_API_KEY"
    default_model = "gemini-1.5-flash-latest"

    def __init__(self) -> None:
        super().__init__()
        self._genai = None

    def _resolve_model_candidates(self) -> List[str]:
        candidates: List[str] = []
        configured = self.get_model()
        if configured:
            candidates.append(configured.strip())
        fallback_models = getattr(settings, "GEMINI_FALLBACK_MODELS", [])
        if isinstance(fallback_models, (list, tuple)):
            candidates.extend([str(model).strip() for model in fallback_models if str(model).strip()])
        elif isinstance(fallback_models, str) and fallback_models.strip():
            candidates.append(fallback_models.strip())

        # Ensure uniqueness while preserving order
        unique_candidates: List[str] = []
        seen = set()
        for model_name in candidates:
            if not model_name:
                continue
            if model_name not in seen:
                seen.add(model_name)
                unique_candidates.append(model_name)
        return unique_candidates

    def _discover_available_models(self, genai_module: Any) -> List[str]:
        discovered: List[str] = []
        try:
            models = genai_module.list_models()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Unable to list Gemini models: %s", exc)
            return discovered

        for model in models:
            try:
                name = getattr(model, "name", "")
                methods = getattr(model, "supported_generation_methods", [])
                if name and (not methods or "generateContent" in methods):
                    discovered.append(str(name))
            except Exception:
                continue
        return discovered

    def _configure(self) -> Optional[Any]:
        if self._genai is not None:
            return self._genai

        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            self.logger.warning("google-generativeai library not installed.")
            return None

        api_key = self.get_api_key()
        if not api_key:
            return None

        try:
            genai.configure(api_key=api_key)
            self._genai = genai
        except Exception as exc:
            self.logger.exception("Failed to configure Gemini client: %s", exc)
            return None
        return self._genai

    def is_available(self) -> bool:
        if not getattr(settings, "GEMINI_ENABLED", True):
            return False
        return super().is_available()

    def generate(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        genai = self._configure()
        if genai is None:
            return ProviderResult(success=False, error="Gemini client not available")

        initial_candidates = self._resolve_model_candidates()
        if not initial_candidates:
            return ProviderResult(success=False, error="Gemini model not configured")

        try:
            from google.api_core import exceptions as google_exceptions  # type: ignore
        except Exception:
            google_exceptions = None  # type: ignore

        last_error: Optional[Exception] = None
        discovery_attempted = False

        model_candidates = deque(initial_candidates)
        primary_model = initial_candidates[0] if initial_candidates else None
        seen_candidates = set(initial_candidates)

        while model_candidates:
            candidate = model_candidates.popleft()
            try:
                model = genai.GenerativeModel(candidate)
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": generation_config.get("temperature", self.get_temperature()),
                        "max_output_tokens": generation_config.get(
                            "max_output_tokens", settings.GEMINI_MAX_OUTPUT_TOKENS
                        ),
                        "response_mime_type": generation_config.get("response_mime_type"),
                    },
                )
                raw_text = getattr(response, "text", None)
                if not raw_text and hasattr(response, "candidates"):
                    try:
                        raw_text = response.candidates[0].content.parts[0].text  # type: ignore[attr-defined]
                    except Exception:
                        raw_text = None

                if not raw_text:
                    return ProviderResult(
                        success=False,
                        error="Gemini response empty",
                        raw_response=getattr(response, "to_dict", lambda: None)(),
                    )

                tokens_used = None
                try:
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        tokens_used = response.usage_metadata.total_token_count
                except Exception:
                    tokens_used = None

                if primary_model and candidate != primary_model:
                    self.logger.info("Gemini fallback model selected: %s", candidate)

                return ProviderResult(
                    success=True,
                    text=raw_text,
                    tokens_used=tokens_used,
                    raw_response=getattr(response, "to_dict", lambda: None)(),
                    provider=candidate,
                )
            except Exception as exc:  # noqa: BLE001 - we want to inspect provider-specific errors
                last_error = exc
                if google_exceptions and isinstance(exc, google_exceptions.NotFound):
                    self.logger.warning("Gemini model %s not available: %s", candidate, exc)
                    if not discovery_attempted:
                        discovery_attempted = True
                        for discovered_model in self._discover_available_models(genai):
                            if discovered_model not in seen_candidates:
                                seen_candidates.add(discovered_model)
                                model_candidates.append(discovered_model)
                    continue
                self.logger.exception("Gemini request failed for model %s: %s", candidate, exc)
                break

        error_message = str(last_error) if last_error else "Gemini request failed"
        return ProviderResult(success=False, error=error_message)


class CohereProvider(BaseProvider):
    name = "cohere"
    env_key = "COHERE_API_KEY"
    default_model = "command-r-plus"
    endpoint = "https://api.cohere.com/v1/generate"

    def generate(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        api_key = self.get_api_key()
        if not api_key:
            return ProviderResult(success=False, error="Cohere API key not configured")

        payload = {
            "model": self.get_model(),
            "prompt": prompt,
            "temperature": generation_config.get("temperature", self.get_temperature()),
            "max_tokens": generation_config.get("max_output_tokens", settings.GEMINI_MAX_OUTPUT_TOKENS),
            "k": 0,
            "stop_sequences": [],
            "return_likelihoods": "NONE",
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.get_timeout(),
            )
            status_code = response.status_code
            data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}

            if status_code == 200:
                generations = data.get("generations") or []
                if not generations:
                    return ProviderResult(
                        success=False,
                        error="Cohere returned no generations",
                        status_code=status_code,
                        raw_response=data,
                    )
                text = generations[0].get("text", "")
                tokens = None
                meta = data.get("meta", {})
                if isinstance(meta, dict):
                    tokens = meta.get("tokens", {}).get("output", None)
                    if tokens is not None:
                        try:
                            tokens = int(tokens)
                        except Exception:
                            tokens = None
                return ProviderResult(
                    success=True,
                    text=text,
                    tokens_used=tokens,
                    status_code=status_code,
                    raw_response=data,
                )

            error_message = data.get("message") if isinstance(data, dict) else response.text
            return ProviderResult(
                success=False,
                error=f"Cohere error: {error_message}",
                status_code=status_code,
                raw_response=data or response.text,
            )
        except Exception as exc:
            self.logger.exception("Cohere request failed: %s", exc)
            return ProviderResult(success=False, error=str(exc))


class ChatCompletionProvider(BaseProvider):
    endpoint: str = ""
    auth_header: str = "Authorization"

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        headers = {
            self.auth_header: f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        return headers

    def _prepare_payload(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": self.get_model(),
            "messages": self.format_messages(prompt, metadata),
            "temperature": generation_config.get("temperature", self.get_temperature()),
            "max_tokens": generation_config.get("max_output_tokens", settings.GEMINI_MAX_OUTPUT_TOKENS),
        }
        if metadata and isinstance(metadata, dict):
            for key in ("top_p", "presence_penalty", "frequency_penalty", "stop", "logit_bias"):
                if key in metadata:
                    payload[key] = metadata[key]
            response_format = metadata.get("response_format")
            if response_format:
                payload["response_format"] = response_format
            extra_payload = metadata.get("extra_payload")
            if isinstance(extra_payload, dict):
                payload.update(extra_payload)
        return payload

    def _extract_text(self, data: Dict[str, Any]) -> str:
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message", {})
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, list):
                # Some providers return list of dict with type/content
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        parts.append(item.get("text") or item.get("content") or "")
                    else:
                        parts.append(str(item))
                return "".join(parts)
            if content:
                return str(content)
        text = first.get("text")
        if text:
            return str(text)
        return ""

    def _make_request_with_retry(
        self,
        endpoint: str,
        headers: Dict[str, str],
        payload: Dict[str, Any],
        timeout: float,
    ) -> ProviderResult:
        """
        Make API request with retry logic and exponential backoff.
        Max 5 attempts with backoff: 3s, 6s, 9s, 12s, 15s
        """
        max_attempts = getattr(settings, 'AI_RETRY_ATTEMPTS', 5)
        backoff_times = [3, 6, 9, 12, 15]  # Exponential backoff in seconds
        
        last_error = None
        last_status_code = None
        attempts = []
        
        for attempt_num in range(1, max_attempts + 1):
            try:
                start_time = time.perf_counter()
                response = requests.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                
                status_code = response.status_code
                data: Any
                if response.headers.get("content-type", "").startswith("application/json"):
                    data = response.json()
                else:
                    data = {}

                if status_code in (200, 201):
                    text = self._extract_text(data if isinstance(data, dict) else {})
                    if not text:
                        result = ProviderResult(
                            success=False,
                            error="Empty response content",
                            status_code=status_code,
                            raw_response=data,
                        )
                    else:
                        tokens = self._extract_tokens(data if isinstance(data, dict) else {})
                        result = ProviderResult(
                            success=True,
                            text=text,
                            status_code=status_code,
                            tokens_used=tokens,
                            raw_response=data,
                        )
                    
                    # Add attempt record
                    attempt = ProviderAttempt(
                        provider=self.name,
                        success=result.success,
                        error=result.error,
                        status_code=status_code,
                        latency_ms=latency_ms,
                        tokens_used=tokens if result.success else None,
                    )
                    attempts.append(attempt)
                    result.attempts = attempts
                    return result

                # Handle error responses
                raw_text = response.text
                error_message = None
                error_type = None
                if isinstance(data, dict):
                    error = data.get("error")
                    if isinstance(error, dict):
                        error_message = error.get("message") or error.get("code")
                        error_type = error.get("type")
                    elif isinstance(error, str):
                        error_message = error
                
                # Provide more detailed error messages for common OpenAI errors
                if status_code == 401:
                    error_message = error_message or "Invalid API key. Please check your OpenAI API key."
                elif status_code == 429:
                    error_message = error_message or "Rate limit exceeded. Please try again later."
                elif status_code == 400:
                    model_name = payload.get("model", "unknown")
                    error_message = error_message or f"Invalid request. Model '{model_name}' may not be available or request format is incorrect."
                elif status_code == 404:
                    model_name = payload.get("model", "unknown")
                    error_message = error_message or f"Model '{model_name}' not found. Please check the model name."
                
                if not error_message:
                    error_message = raw_text or f"HTTP {status_code} error"

                full_error = f"{self.name} error: {error_message}"
                if error_type:
                    full_error += f" (type: {error_type})"
                
                last_error = full_error
                last_status_code = status_code
                
                # Record attempt
                attempt = ProviderAttempt(
                    provider=self.name,
                    success=False,
                    error=full_error,
                    status_code=status_code,
                    latency_ms=latency_ms,
                    tokens_used=None,
                )
                attempts.append(attempt)
                
                # Don't retry on 401 (invalid API key) or 400 (bad request)
                if status_code in (401, 400):
                    self.logger.warning(
                        f"{self.name} API call failed (non-retryable): status={status_code}, error={error_message}, "
                        f"model={payload.get('model', 'unknown')}"
                    )
                    result = ProviderResult(
                        success=False,
                        error=full_error,
                        status_code=status_code,
                        raw_response=data or raw_text,
                        attempts=attempts,
                    )
                    return result
                
                # For 429 and other retryable errors, apply backoff
                if attempt_num < max_attempts:
                    backoff_time = backoff_times[min(attempt_num - 1, len(backoff_times) - 1)]
                    self.logger.warning(
                        f"{self.name} API call failed (attempt {attempt_num}/{max_attempts}): "
                        f"status={status_code}, error={error_message}, "
                        f"retrying in {backoff_time}s"
                    )
                    time.sleep(backoff_time)
                else:
                    self.logger.warning(
                        f"{self.name} API call failed after {max_attempts} attempts: "
                        f"status={status_code}, error={error_message}, "
                        f"model={payload.get('model', 'unknown')}"
                    )
                    
            except requests.exceptions.Timeout as exc:
                last_error = f"{self.name} request timed out after {timeout}s"
                self.logger.warning(f"{self.name} request timed out (attempt {attempt_num}/{max_attempts}): {exc}")
                
                attempt = ProviderAttempt(
                    provider=self.name,
                    success=False,
                    error=last_error,
                    status_code=None,
                    latency_ms=None,
                    tokens_used=None,
                )
                attempts.append(attempt)
                
                if attempt_num < max_attempts:
                    backoff_time = backoff_times[min(attempt_num - 1, len(backoff_times) - 1)]
                    time.sleep(backoff_time)
                    
            except requests.exceptions.RequestException as exc:
                last_error = f"{self.name} network error: {str(exc)}"
                self.logger.warning(f"{self.name} network error (attempt {attempt_num}/{max_attempts}): {exc}")
                
                attempt = ProviderAttempt(
                    provider=self.name,
                    success=False,
                    error=last_error,
                    status_code=None,
                    latency_ms=None,
                    tokens_used=None,
                )
                attempts.append(attempt)
                
                if attempt_num < max_attempts:
                    backoff_time = backoff_times[min(attempt_num - 1, len(backoff_times) - 1)]
                    time.sleep(backoff_time)
                    
            except Exception as exc:
                last_error = f"{self.name} error: {str(exc)}"
                self.logger.exception(f"{self.name} request failed (attempt {attempt_num}/{max_attempts}): {exc}")
                
                attempt = ProviderAttempt(
                    provider=self.name,
                    success=False,
                    error=last_error,
                    status_code=None,
                    latency_ms=None,
                    tokens_used=None,
                )
                attempts.append(attempt)
                
                if attempt_num < max_attempts:
                    backoff_time = backoff_times[min(attempt_num - 1, len(backoff_times) - 1)]
                    time.sleep(backoff_time)
        
        # All attempts failed
        return ProviderResult(
            success=False,
            error=last_error or f"{self.name} request failed after {max_attempts} attempts",
            status_code=last_status_code,
            attempts=attempts,
        )

    def generate(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ProviderResult:
        api_key = self.get_api_key()
        if not api_key:
            return ProviderResult(success=False, error=f"{self.name} API key not configured")

        payload = self._prepare_payload(prompt, generation_config, metadata)
        headers = self._build_headers(api_key)

        return self._make_request_with_retry(
            self.endpoint,
            headers,
            payload,
            self.get_timeout(),
        )


class OpenRouterProvider(ChatCompletionProvider):
    name = "openrouter"
    env_key = "OPENROUTER_API_KEY"
    default_model = "openrouter/anthropic/claude-3-haiku"
    endpoint = "https://openrouter.ai/api/v1/chat/completions"

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        headers = super()._build_headers(api_key)
        referer = getattr(settings, "FRONTEND_URL", None)
        if referer:
            headers["HTTP-Referer"] = referer
            headers["X-Title"] = "Smart AI Trading Strategy Optimizer"
        return headers


class TogetherAIProvider(ChatCompletionProvider):
    name = "together_ai"
    env_key = "TOGETHER_API_KEY"
    default_model = "togethercomputer/llama-3-70b-instruct"
    endpoint = "https://api.together.xyz/v1/chat/completions"


class DeepInfraProvider(ChatCompletionProvider):
    name = "deepinfra"
    env_key = "DEEPINFRA_API_KEY"
    default_model = "meta-llama/Llama-3.1-70B-Instruct"
    endpoint = "https://api.deepinfra.com/v1/openai/chat/completions"

class GroqProvider(ChatCompletionProvider):
    name = "groq"
    env_key = "GROQ_API_KEY"
    default_model = "llama3-70b-8192"
    endpoint = "https://api.groq.com/openai/v1/chat/completions"


class OpenAIProvider(ChatCompletionProvider):
    name = "openai"
    env_key = "OPENAI_API_KEY"
    default_model = "gpt-4o-mini"  # Fixed: was "gpt-4.1-mini" which is invalid
    endpoint = "https://api.openai.com/v1/chat/completions"

    def _build_headers(self, api_key: str) -> Dict[str, str]:
        headers = super()._build_headers(api_key)
        organization = getattr(settings, "OPENAI_ORG_ID", None)
        if organization:
            headers["OpenAI-Organization"] = organization
        project = getattr(settings, "OPENAI_PROJECT_ID", None)
        if project:
            headers["OpenAI-Project"] = project
        return headers

    def _prepare_payload(
        self,
        prompt: str,
        generation_config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        payload = super()._prepare_payload(prompt, generation_config, metadata)
        if metadata and isinstance(metadata, dict):
            if metadata.get("use_json_response_format"):
                payload["response_format"] = {"type": "json_object"}
            if metadata.get("stream"):
                payload["stream"] = True
        return payload


def get_registered_providers() -> Dict[str, BaseProvider]:
    openai_provider = OpenAIProvider()
    providers: List[BaseProvider] = [
        GeminiProvider(),
        CohereProvider(),
        openai_provider,
        OpenRouterProvider(),
        TogetherAIProvider(),
        DeepInfraProvider(),
        GroqProvider(),
    ]
    provider_map = {provider.name: provider for provider in providers}
    for alias in ("chatgpt", "gpt", "gpt4", "gpt-4"):
        provider_map[alias] = openai_provider
    return provider_map


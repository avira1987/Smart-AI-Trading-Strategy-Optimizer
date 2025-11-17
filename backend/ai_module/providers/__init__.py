import json
import logging
import os
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from django.conf import settings

try:
    from core.models import APIConfiguration  # type: ignore
except Exception:  # pragma: no cover - during migrations/tests without db
    APIConfiguration = None


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


def _get_api_key(provider_name: str, env_key: Optional[str]) -> str:
    env_candidates: List[str] = []
    if env_key:
        env_candidates.append(env_key)
        env_alias_map = getattr(settings, "AI_ENV_KEY_ALIASES", {})
        env_candidates.extend(env_alias_map.get(env_key, []))

    for candidate in env_candidates:
        key = os.environ.get(candidate, "").strip()
        if key:
            return key

    provider_candidates: List[str] = [provider_name] if provider_name else []
    provider_alias_map = getattr(settings, "AI_PROVIDER_NAME_ALIASES", {})
    provider_candidates.extend(provider_alias_map.get(provider_name, []))
    provider_candidates = [name for name in provider_candidates if name]

    if not provider_candidates:
        return ""

    if APIConfiguration is None:
        return ""

    try:
        # First try to get system-wide API key (user=None)
        config = (
            APIConfiguration.objects.filter(
                provider__in=provider_candidates,
                is_active=True,
                user__isnull=True,
            )
            .order_by("-updated_at", "-created_at")
            .first()
        )
        if config and config.api_key:
            return config.api_key.strip()
        
        # If no system key found, try to get any active user key
        # This allows users to use their own API keys for AI providers
        config = (
            APIConfiguration.objects.filter(
                provider__in=provider_candidates,
                is_active=True,
            )
            .order_by("-updated_at", "-created_at")
            .first()
        )
        if config and config.api_key:
            return config.api_key.strip()
    except Exception:  # pragma: no cover - database errors should not break provider discovery
        LOGGER.exception("Failed to fetch API key for provider %s from database", provider_name)
    return ""


class BaseProvider:
    name: str = ""
    env_key: Optional[str] = None
    default_model: Optional[str] = None

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"ai.providers.{self.name or 'unknown'}")

    def get_api_key(self) -> str:
        return _get_api_key(self.name, self.env_key)

    def is_available(self) -> bool:
        return bool(self.get_api_key())

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

                if candidate != model_candidates[0]:
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

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=self.get_timeout(),
            )
            status_code = response.status_code
            data: Any
            if response.headers.get("content-type", "").startswith("application/json"):
                data = response.json()
            else:
                data = {}

            if status_code in (200, 201):
                text = self._extract_text(data if isinstance(data, dict) else {})
                if not text:
                    return ProviderResult(
                        success=False,
                        error="Empty response content",
                        status_code=status_code,
                        raw_response=data,
                    )
                tokens = self._extract_tokens(data if isinstance(data, dict) else {})
                return ProviderResult(
                    success=True,
                    text=text,
                    status_code=status_code,
                    tokens_used=tokens,
                    raw_response=data,
                )

            raw_text = response.text
            error_message = None
            if isinstance(data, dict):
                error = data.get("error")
                if isinstance(error, dict):
                    error_message = error.get("message") or error.get("code")
                elif isinstance(error, str):
                    error_message = error
            if not error_message:
                error_message = raw_text

            return ProviderResult(
                success=False,
                error=f"{self.name} error: {error_message}",
                status_code=status_code,
                raw_response=data or raw_text,
            )
        except Exception as exc:
            self.logger.exception("%s request failed: %s", self.name, exc)
            return ProviderResult(success=False, error=str(exc))


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
    default_model = "gpt-4.1-mini"
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


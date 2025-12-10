"""
Google Gemini AI client for strategy analysis and parsing
"""

import json
import hashlib
import logging
import time
from collections import deque
from threading import Lock
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

from .provider_manager import get_provider_manager
from .text_chunker import get_chunker

# Constants & configuration defaults
CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours
RATE_LIMIT_CALLS_PER_MINUTE = 60
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_INPUT_TOKENS = 32000
MAX_OUTPUT_TOKENS = 8000
DISABLED_MESSAGE = "AI analysis unavailable. Please configure your AI provider (OpenAI ChatGPT or Gemini) in Settings."
PROVIDERS_FAILED_MESSAGE = "کلید ChatGPT (OpenAI) تنظیم نشده یا نامعتبر است. لطفاً در تنظیمات > پیکربندی API، کلید معتبر OpenAI را وارد کنید."
SERVICE_UNAVAILABLE_MESSAGE = "سرویس هوش مصنوعی موقتاً در دسترس نیست."
JSON_ONLY_SYSTEM_PROMPT = (
    "You are an assistant that must respond with strictly valid JSON output. "
    "Do not include explanations, markdown fences, or any text outside the JSON."
)

_rate_lock = Lock()
_request_timestamps: deque[float] = deque()

# Cache directory
_CACHE_DIR = Path(getattr(settings, 'CACHE_DIR', Path(__file__).parent.parent / 'cache' / 'gemini'))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# System instructions
ANALYSIS_SYSTEM_INSTRUCTIONS = (
    "شما یک تحلیلگر حرفه‌ای استراتژی معاملاتی هستید. بر اساس اطلاعات استراتژی که دریافت می‌کنید، "
    "یک تحلیل جامع به فارسی ارائه دهید که شامل موارد زیر باشد:\n"
    "1. خلاصه کلی استراتژی\n"
    "2. نقاط قوت استراتژی (لیست)\n"
    "3. نقاط ضعف استراتژی (لیست)\n"
    "4. ارزیابی ریسک\n"
    "5. پیشنهادات برای بهبود (لیست)\n"
    "6. امتیاز کیفیت (0-100)\n\n"
    "خروجی باید یک JSON با ساختار زیر باشد:\n"
    '{"summary": "...", "strengths": [...], "weaknesses": [...], '
    '"risk_assessment": "...", "recommendations": [...], "quality_score": عدد}'
)

BACKTEST_ANALYSIS_SYSTEM_INSTRUCTIONS = (
    "شما یک تحلیلگر حرفه‌ای نتایج بک‌تست معاملاتی هستید. بر اساس نتایج بک‌تست و معاملات انجام شده، "
    "یک تحلیل جامع و مفصل به فارسی ارائه دهید.\n\n"
    "تحلیل باید شامل موارد زیر باشد:\n"
    "1. تحلیل عملکرد کلی استراتژی: چقدر سود یا ضرر کرده است؟\n"
    "2. تحلیل معاملات: چند معامله برنده/بازنده داشت؟ نرخ برد چقدر است؟\n"
    "3. تحلیل هر استراتژی: برای هر شرط ورود/خروج که در استراتژی استفاده شده، بگو که:\n"
    "   - این شرط چند بار فعال شده است؟\n"
    "   - چقدر سودآور بوده است؟\n"
    "   - آیا نیاز به بهبود دارد؟\n"
    "4. نقاط قوت و ضعف استراتژی بر اساس نتایج واقعی\n"
    "5. پیشنهادات برای بهبود عملکرد\n\n"
    "تحلیل باید دقیق، جامع و به فارسی باشد."
)


def _hash_text(text: str) -> str:
    """Create hash for caching"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def truncate_text(text: str, max_tokens: int = MAX_INPUT_TOKENS) -> str:
    """Truncate text to approximate token limit (4 chars ≈ 1 token)."""
    if not text:
        return text
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    logger.debug("Truncating text from %s to %s characters", len(text), max_chars)
    return text[:max_chars]


def _clean_response_text(response_text: str) -> str:
    """Remove code fences and trim whitespace from LLM responses."""
    if not response_text:
        return ""
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        parts = cleaned.split('\n', 1)
        cleaned = parts[1] if len(parts) > 1 else parts[0]
    return cleaned.strip()


def _providers_available(user=None) -> bool:
    manager = get_provider_manager(user=user)
    return manager.has_available_provider()


def _build_base_response(
    ai_status: str,
    message: str,
    *,
    raw_output: str = "",
    extra: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized response payload."""
    payload: Dict[str, Any] = {
        "entry_conditions": [],
        "exit_conditions": [],
        "risk_management": {},
        "ai_status": ai_status,
        "message": message,
        "raw_output": raw_output or "",
    }
    if extra:
        for key, value in extra.items():
            payload[key] = value
    return payload


def _resolve_provider_from_attempts(attempts: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    """Best-effort extraction of provider name from serialized attempts."""
    if not attempts:
        return None

    for attempt in attempts:
        provider = attempt.get("provider")
        if provider and attempt.get("success"):
            return provider

    for attempt in attempts:
        provider = attempt.get("provider")
        if provider:
            return provider

    return None


def resolve_ai_provider(result_payload: Dict[str, Any]) -> Optional[str]:
    """
    Determine the most accurate provider label from an AI result payload.

    Preference order:
        1. Explicit ai_provider / provider fields
        2. Successful provider_attempts entries
        3. Any provider entry in attempts
    """
    provider = result_payload.get("ai_provider") or result_payload.get("provider")
    if provider:
        return provider

    attempts = result_payload.get("provider_attempts")
    if isinstance(attempts, list):
        return _resolve_provider_from_attempts(attempts)

    return None


def _translate_ai_error_message(error_message: Optional[str]) -> str:
    if not error_message:
        return SERVICE_UNAVAILABLE_MESSAGE

    message = error_message.strip()
    lowered = message.lower()

    if "user location is not supported" in lowered:
        return "سرویس Gemini در موقعیت مکانی فعلی شما در دسترس نیست. لطفاً از VPN یا ارائه‌دهنده جایگزین استفاده کنید."
    if "location" in lowered and "not supported" in lowered:
        return "سرویس هوش مصنوعی برای این موقعیت جغرافیایی فعال نیست."
    if "api key" in lowered and "invalid" in lowered:
        return "کلید Gemini نامعتبر است. لطفاً کلید جدید وارد کنید."
    if "permission" in lowered and "denied" in lowered:
        return "دسترسی لازم برای استفاده از سرویس Gemini فراهم نشده است."
    if "quota" in lowered or "exceeded" in lowered or "rate limit" in lowered:
        return "محدودیت مصرف سرویس Gemini تمام شده است. کمی بعد دوباره تلاش کنید."
    if "model" in lowered and "not found" in lowered:
        return "مدل انتخابی Gemini در دسترس نیست. لطفاً تنظیمات مدل را به‌روزرسانی کنید."

    return message


def _cache_file(namespace: str, digest: str) -> Path:
    """Return cache file path for a given namespace and digest."""
    namespace_dir = _CACHE_DIR / namespace
    namespace_dir.mkdir(parents=True, exist_ok=True)
    return namespace_dir / f"{digest}.json"


def _load_cache(namespace: str, digest: str) -> Optional[Dict[str, Any]]:
    """Load cached response if still within TTL."""
    path = _cache_file(namespace, digest)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        timestamp = data.get("timestamp")
        payload = data.get("payload")
        if not timestamp or payload is None:
            return None
        if time.time() - float(timestamp) > CACHE_TTL_SECONDS:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
            return None
        return payload
    except Exception as exc:
        logger.debug("Failed to load AI cache: %s", exc, exc_info=True)
        return None


def _write_cache(namespace: str, digest: str, payload: Dict[str, Any]) -> None:
    """Write payload to cache with timestamp."""
    path = _cache_file(namespace, digest)
    try:
        path.write_text(
            json.dumps({"timestamp": time.time(), "payload": payload}, ensure_ascii=False),
            encoding='utf-8'
        )
    except Exception as exc:
        logger.debug("Failed to write AI cache: %s", exc, exc_info=True)


def _enforce_rate_limit() -> Optional[Dict[str, Any]]:
    """Enforce per-minute rate limit. Returns error response if limit exceeded."""
    if RATE_LIMIT_CALLS_PER_MINUTE <= 0:
        return None

    now = time.time()
    with _rate_lock:
        while _request_timestamps and now - _request_timestamps[0] > RATE_LIMIT_WINDOW_SECONDS:
            _request_timestamps.popleft()
        if len(_request_timestamps) >= RATE_LIMIT_CALLS_PER_MINUTE:
            logger.warning("AI provider rate limit exceeded (%s per minute)", RATE_LIMIT_CALLS_PER_MINUTE)
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output="",
                extra={"error": "Rate limit exceeded"}
            )
        _request_timestamps.append(now)
    return None


def _get_gemini_api_key(user=None) -> Optional[str]:
    """Compatibility helper to fetch Gemini API key."""
    provider = get_provider_manager(user=user).providers.get("gemini")
    if provider:
        key = provider.get_api_key()
        if key:
            return key
    return getattr(settings, 'GEMINI_API_KEY', '') or ''


def _call_gemini(
    prompt: str,
    *,
    cache_namespace: str,
    cache_key: str,
    generation_config: Optional[Dict[str, Any]],
    response_parser: Callable[[str], Dict[str, Any]],
    user=None,
) -> Dict[str, Any]:
    """Execute AI provider call with caching, rate limiting, and standardized responses."""
    user_id = None
    if user and getattr(user, "is_authenticated", False):
        user_id = getattr(user, "pk", None) or getattr(user, "id", None)
    
    # Reduced logging - too many logs in console
    logger.debug(
        f"_call_gemini called (cache_namespace={cache_namespace}, user_id={user_id}, "
        f"prompt_length={len(prompt)}, cache_key_length={len(cache_key)})"
    )
    
    manager = get_provider_manager(user=user)
    digest = _hash_text(cache_key)
    
    # Check if cache is enabled in system settings
    # Always read directly from DB to get the latest value (bypass any ORM cache)
    try:
        from core.models import SystemSettings
        # Read directly from database, not from cache
        system_settings = SystemSettings.objects.get(pk=1)
        use_cache = system_settings.use_ai_cache
        logger.debug(f"SystemSettings.use_ai_cache = {use_cache} (user_id={user_id}, cache_namespace={cache_namespace})")
    except SystemSettings.DoesNotExist:
        # If settings don't exist, create with default (cache enabled)
        system_settings = SystemSettings.objects.create(pk=1, use_ai_cache=True)
        use_cache = True
        logger.info(f"SystemSettings created with default use_ai_cache=True (user_id={user_id})")
    except Exception as e:
        logger.warning(f"Failed to load SystemSettings, defaulting to cache enabled: {e}")
        use_cache = True
    
    # Only use cache if enabled in settings
    if use_cache:
        cached = _load_cache(cache_namespace, digest)
        if cached:
            logger.info(f"Cache hit for {cache_namespace} (user_id={user_id}) - returning cached result")
            return cached
        logger.debug(f"Cache miss for {cache_namespace} (user_id={user_id})")
    else:
        logger.debug(f"Cache disabled for {cache_namespace} (user_id={user_id})")
        # Delete cache file if it exists (to ensure fresh API calls)
        cache_path = _cache_file(cache_namespace, digest)
        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.debug(f"Deleted existing cache file for {cache_namespace} (user_id={user_id})")
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_path}: {e}")

    logger.debug(f"Checking provider availability for {cache_namespace} (user_id={user_id})")
    if not manager.has_available_provider():
        logger.warning(f"No available providers (user_id={user_id}, cache_namespace={cache_namespace})")
        return _build_base_response(
            ai_status="disabled",
            message=DISABLED_MESSAGE,
            extra={"error": "no_provider_available"}
        )

    rate_limit_error = _enforce_rate_limit()
    if rate_limit_error:
        logger.warning(f"Rate limit enforced (user_id={user_id})")
        return rate_limit_error

    config = dict(generation_config or {})
    configured_max_tokens = getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', MAX_OUTPUT_TOKENS)
    config.setdefault('max_output_tokens', min(configured_max_tokens, MAX_OUTPUT_TOKENS))
    metadata = config.pop('provider_metadata', None) or {}

    # Validate prompt is not empty
    if not prompt or not prompt.strip():
        logger.error(f"Empty prompt provided (user_id={user_id}, cache_namespace={cache_namespace})")
        return _build_base_response(
            ai_status="error",
            message="Prompt cannot be empty",
            extra={"error": "empty_prompt"}
        )
    
    # Check if prompt needs chunking
    chunker = get_chunker()
    if chunker and chunker.should_chunk(prompt):
        logger.info(f"Prompt exceeds token limit, chunking into smaller pieces (user_id={user_id}, cache_namespace={cache_namespace})")
        chunks = chunker.chunk_text(prompt)
        logger.info(f"Prompt chunked into {len(chunks)} pieces (user_id={user_id})")
        
        # Process each chunk separately
        chunk_results = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)} (user_id={user_id})")
            chunk_result = manager.generate(chunk, config, metadata=metadata)
            
            if not chunk_result.success:
                # If any chunk fails, return error
                logger.warning(f"Chunk {i+1} failed: {chunk_result.error} (user_id={user_id})")
                attempts_serialized = [
                    {
                        "provider": attempt.provider,
                        "success": attempt.success,
                        "error": attempt.error,
                        "status_code": attempt.status_code,
                        "latency_ms": attempt.latency_ms,
                        "tokens_used": attempt.tokens_used,
                    }
                    for attempt in chunk_result.attempts
                ]
                return _build_base_response(
                    ai_status="error",
                    message=chunk_result.error or "AI processing failed for chunk",
                    raw_output="",
                    extra={
                        "error": "chunk_processing_failed",
                        "chunk_number": i + 1,
                        "total_chunks": len(chunks),
                        "provider_attempts": attempts_serialized
                    }
                )
            
            chunk_results.append(chunk_result.text)
        
        # Merge chunked responses
        merged_text = chunker.merge_chunked_responses(chunk_results)
        
        # Parse the merged response
        try:
            parsed_result = response_parser(merged_text)
            parsed_result["ai_status"] = "ok"
            parsed_result["message"] = "Success"
            parsed_result["raw_output"] = merged_text
            
            # Write to cache if enabled
            if use_cache:
                _write_cache(cache_namespace, digest, parsed_result)
            
            logger.info(f"Chunked processing completed successfully (user_id={user_id}, cache_namespace={cache_namespace})")
            return parsed_result
        except Exception as parse_exc:
            logger.error(f"Error parsing merged chunked response: {parse_exc} (user_id={user_id})")
            return _build_base_response(
                ai_status="error",
                message=f"Error parsing merged response: {str(parse_exc)}",
                raw_output=merged_text,
                extra={"error": "parse_error", "chunks_processed": len(chunks)}
            )
    
    logger.debug(f"Calling manager.generate() (user_id={user_id}, cache_namespace={cache_namespace})")
    result = manager.generate(prompt, config, metadata=metadata)
    # Don't log error message here if failed - already logged in provider_manager
    # Log only success cases or error type (in English) to avoid [FA] spam
    if result.success:
        logger.info(f"manager.generate() succeeded: provider={result.provider} (user_id={user_id})")
    else:
        # Extract error type in English only
        error_type = "Error"
        if result.status_code == 429:
            error_type = "RateLimit (429)"
        elif result.status_code == 401:
            error_type = "InvalidAPIKey (401)"
        elif result.status_code:
            error_type = f"Error ({result.status_code})"
        logger.debug(f"manager.generate() failed: {error_type}, provider={result.provider} (user_id={user_id})")

    attempts_serialized = [
        {
            "provider": attempt.provider,
            "success": attempt.success,
            "error": attempt.error,
            "status_code": attempt.status_code,
            "latency_ms": attempt.latency_ms,
            "tokens_used": attempt.tokens_used,
        }
        for attempt in result.attempts
    ]

    if not result.success or not result.text:
        # Log error type in English only - detailed errors are logged in provider_manager
        # This avoids [FA] spam in console (Persian messages are replaced with [FA] by SafeUnicodeStreamHandler)
        error_type = "unknown_error"
        status_code = result.status_code
        
        # Extract error type from error message (use English messages only)
        error_msg = result.error or ""
        if status_code == 429 or "Rate limit" in error_msg or "429" in str(error_msg):
            error_type = "RateLimit (429)"
        elif status_code == 401 or "Invalid API key" in error_msg or "401" in str(error_msg):
            error_type = "InvalidAPIKey (401)"
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            error_type = "Timeout"
        elif status_code:
            error_type = f"Error ({status_code})"
        else:
            error_type = "Error"
        
        # Log only error type in English to avoid [FA] in console
        # Full error details are already logged in provider_manager and will be in log files
        logger.warning(
            "AI providers failed: %s",
            error_type,
        )
        error_text = result.error or SERVICE_UNAVAILABLE_MESSAGE
        
        # Use the error message from provider_manager if it's already in Persian
        # Otherwise, use the default message
        if error_text and ("کلید" in error_text or "ChatGPT" in error_text or "OpenAI" in error_text):
            user_message = error_text
        elif "All AI providers failed" in error_text or "No AI providers" in error_text:
            user_message = PROVIDERS_FAILED_MESSAGE
        else:
            user_message = _translate_ai_error_message(error_text)
            # Translate to Persian if needed
            if "All AI providers failed" in user_message or "Please check your API keys" in user_message:
                user_message = PROVIDERS_FAILED_MESSAGE
        
        extra = {
            "error": error_text,
            "translated_error": user_message,
            "provider_attempts": attempts_serialized,
        }
        return _build_base_response(
            ai_status="error",
            message=user_message,
            extra=extra,
        )

    raw_output = result.text

    cleaned_output = _clean_response_text(raw_output)

    try:
        parsed_response = response_parser(cleaned_output)
    except Exception as exc:
        logger.warning("AI response parsing failed: %s", exc, exc_info=True)
        parsed_response = _build_base_response(
            ai_status="error",
            message=SERVICE_UNAVAILABLE_MESSAGE,
            raw_output=cleaned_output,
            extra={"error": str(exc)}
        )

    if "raw_output" not in parsed_response:
        parsed_response["raw_output"] = cleaned_output
    parsed_response.setdefault("provider_attempts", attempts_serialized)
    if result.provider:
        parsed_response.setdefault("provider", result.provider)
        parsed_response.setdefault("ai_provider", result.provider)
    if result.tokens_used is not None:
        parsed_response.setdefault("tokens_used", result.tokens_used)

    if parsed_response.get("ai_status") == "ok" and use_cache:
        _write_cache(cache_namespace, digest, parsed_response)

    return parsed_response


def parse_with_gemini(text: str, user=None) -> Dict[str, Any]:
    """Parse strategy text using AI providers with standardized response."""
    truncated_text = truncate_text(text or "")
    cache_key = truncated_text or "empty"

    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"error": "empty_response"}
            )

        try:
            data = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode AI parse response: %s", exc)
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"error": str(exc)}
            )

        entry_conditions = data.get("entry_conditions") or []
        exit_conditions = data.get("exit_conditions") or []
        risk_management = data.get("risk_management") or {}

        return _build_base_response(
            ai_status="ok",
            message="AI parsing successful.",
            raw_output=raw_output,
            extra={
                "entry_conditions": entry_conditions,
                "exit_conditions": exit_conditions,
                "risk_management": risk_management,
                "indicators": data.get("indicators", []),
                "timeframe": data.get("timeframe"),
                "symbol": data.get("symbol"),
                "confidence": data.get("confidence"),
                "source": "llm",
            }
        )

    prompt = f"""
    این یک استراتژی معاملاتی است که به فارسی یا انگلیسی نوشته شده است. 
    لطفاً آن را تحلیل کنید و اطلاعات زیر را استخراج کنید:
    
    {truncated_text}
    
    خروجی باید JSON با این ساختار باشد:
    {{
        "entry_conditions": ["شرط 1", "شرط 2"],
        "exit_conditions": ["شرط 1", "شرط 2"],
        "indicators": ["RSI", "MACD"],
        "risk_management": {{"stop_loss": 50, "take_profit": 100}},
        "timeframe": "H1",
        "symbol": "EURUSD"
    }}
    
    فقط JSON برگردانید.
    """

    return _call_gemini(
        prompt,
        cache_namespace="parse",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.3,
            'response_mime_type': 'application/json',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )


def call_gemini_analyzer(text: str, user=None) -> Dict[str, Any]:
    """Public helper used by tests to parse strategy text via Gemini."""
    return parse_with_gemini(text, user=user)


def analyze_strategy_with_gemini(parsed_strategy: Dict[str, Any], raw_text: str = None, user=None) -> Dict[str, Any]:
    """Generate comprehensive analysis of a trading strategy using Gemini AI."""
    # Create a text description of the strategy for analysis
    strategy_description = f"""
اطلاعات استراتژی:
- شرایط ورود: {', '.join(parsed_strategy.get('entry_conditions', []))}
- شرایط خروج: {', '.join(parsed_strategy.get('exit_conditions', []))}
- مدیریت ریسک: {parsed_strategy.get('risk_management', {})}
- اندیکاتورها: {', '.join(parsed_strategy.get('indicators', []))}
- نماد: {parsed_strategy.get('symbol', 'تعیین نشده')}
- تایم‌فریم: {parsed_strategy.get('timeframe', 'تعیین نشده')}
- امتیاز اعتماد: {parsed_strategy.get('confidence_score', 0.0) * 100:.0f}%
"""

    if raw_text:
        strategy_description += f"\nمتن اصلی استراتژی:\n{truncate_text(raw_text, max_tokens=8000)[:8000*4]}"

    cache_key = strategy_description

    prompt = (
        f"{ANALYSIS_SYSTEM_INSTRUCTIONS}\n\n"
        f"{strategy_description}\n\n"
        f"لطفاً تحلیل جامعی ارائه دهید."
    )

    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"error": "empty_response"}
            )

        try:
            data: Dict[str, Any] = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode Gemini strategy analysis response: %s", exc)
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"error": str(exc)}
            )

        strengths = data.get('strengths') or []
        weaknesses = data.get('weaknesses') or []
        recommendations = data.get('recommendations') or []
        risk_assessment = data.get('risk_assessment') or 'ارزیابی ریسک در دسترس نیست.'
        summary = data.get('summary') or 'تحلیل در دسترس نیست.'
        quality_score = data.get('quality_score', 50)

        if isinstance(quality_score, (int, float)):
            if quality_score > 1:
                quality_score = float(quality_score) / 100.0
        else:
            quality_score = 0.5

        analysis_payload = {
            "summary": summary,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "quality_score": quality_score,
            "is_basic": False,
            "source": "llm",
        }

        return _build_base_response(
            ai_status="ok",
            message="AI analysis successful.",
            raw_output=raw_output,
            extra=analysis_payload
        )

    result = _call_gemini(
        prompt,
        cache_namespace="analysis",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.7,
            'response_mime_type': 'application/json',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )

    provider_name = resolve_ai_provider(result)

    if result.get("ai_status") == "ok" and provider_name:
        try:
            from api.api_usage_tracker import log_api_usage

            input_tokens_approx = len(prompt) // 4
            output_tokens_approx = len(result.get("raw_output", "")) // 4
            total_tokens = input_tokens_approx + output_tokens_approx

            metadata = {
                'function': 'analyze_strategy_with_gemini',
                'input_tokens_approx': input_tokens_approx,
                'output_tokens_approx': output_tokens_approx,
                'total_tokens_approx': total_tokens,
                'provider_attempts': result.get("provider_attempts"),
            }

            log_api_usage(
                provider=provider_name,
                endpoint='analyze_strategy_with_gemini',
                request_type='POST',
                status_code=200,
                success=True,
                tokens=total_tokens,
                user=user,
                metadata=metadata,
            )
        except Exception as log_error:
            logger.warning("Failed to log AI usage: %s", log_error)
    elif result.get("ai_status") == "error" and provider_name:
        try:
            from api.api_usage_tracker import log_api_usage
            metadata = {
                'function': 'analyze_strategy_with_gemini',
                'error': result.get("error"),
                'provider_attempts': result.get("provider_attempts"),
            }
            log_api_usage(
                provider=provider_name,
                endpoint='analyze_strategy_with_gemini',
                request_type='POST',
                status_code=500,
                success=False,
                error_message=result.get("error"),
                user=user,
                metadata=metadata,
            )
        except Exception:
            pass

    return result


def generate_strategy_questions(
    parsed_strategy: Dict[str, Any],
    raw_text: str,
    existing_answers: Dict[str, Any] = None,
    user=None,
) -> Dict[str, Any]:
    """Generate intelligent follow-up questions for completing a strategy."""
    logger.info("Starting question generation...")

    existing_answers = existing_answers or {}

    summary = (
        f"شرایط ورود استخراج شده: {len(parsed_strategy.get('entry_conditions', []))} شرط\n"
        f"شرایط خروج استخراج شده: {len(parsed_strategy.get('exit_conditions', []))} شرط\n"
        f"اندیکاتورها: {', '.join(parsed_strategy.get('indicators', []))}\n"
        f"امتیاز اعتماد: {parsed_strategy.get('confidence_score', 0) * 100:.0f}%"
    )

    if existing_answers:
        summary += f"\nجواب‌های قبلی کاربر:\n{json.dumps(existing_answers, ensure_ascii=False, indent=2)}"

    truncated_text = truncate_text(raw_text or "", max_tokens=MAX_INPUT_TOKENS // 2)
    cache_key = f"{summary}\n{truncated_text}"

    prompt = f"""
    شما یک تحلیلگر حرفه‌ای استراتژی معاملاتی هستید. بر اساس استراتژی که دریافت می‌کنید، باید سوالات هوشمندانه و هدفمند تولید کنید که به کاربر کمک کند استراتژی را کامل‌تر و دقیق‌تر تعریف کند.
    
    استراتژی:
    {summary}
    
    متن اصلی استراتژی (قسمت اول):
    {truncated_text}
    
    **قوانین مهم برای تولید سوالات:**
    
    1. قبل از تولید هر سوال، بررسی کنید که آیا پاسخ آن سوال در متن استراتژی موجود است یا نه.
       - اگر پاسخ سوال به طور واضح و کامل در متن استراتژی آمده است، آن سوال را تولید نکنید.
       - فقط سوالاتی را تولید کنید که پاسخشان در متن موجود نیست یا به طور مبهم بیان شده است.
    
    2. هدف شما: تولید 3 تا 5 سوال هوشمند که:
       - نقاط مبهم و ناقص استراتژی را شناسایی کنند.
       - شرایط ورود/خروج را دقیق‌تر کنند اگر مبهم است.
       - پارامترهای مهم (حد ضرر، حد سود، تایم‌فریم) را مشخص کنند اگر ذکر نشده.
       - اندیکاتورها و تنظیمات آنها را مشخص کنند اگر ذکر نشده.
    
    3. مثال:
       - اگر در متن نوشته شده «حد ضرر 50 پیپ است»، سوال «حد ضرر چقدر است؟» را تولید نکنید.
       - اگر نوشته شده «از اندیکاتور RSI استفاده می‌کنیم»، سوال «کدام اندیکاتور استفاده می‌شود؟» را تولید نکنید.
    
    خروجی باید JSON با این ساختار باشد:
    {{
      "questions": [
        {{
          "question_text": "متن سوال به فارسی",
          "question_type": "text|number|choice|multiple_choice|boolean",
          "options": ["گزینه 1", "گزینه 2"],
          "order": 1,
          "context": {{
            "section": "entry|exit|risk|indicator",
            "related_text": "بخشی از متن که مربوط به این سوال است"
          }}
        }}
      ]
    }}
    
    فقط JSON بازگردانید و از توضیحات اضافه خودداری کنید.
    """

    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"questions": []}
            )

        try:
            data: Dict[str, Any] = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse questions JSON: %s", exc)
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"questions": [], "error": str(exc)}
            )

        questions = data.get("questions") or []
        if not isinstance(questions, list):
            logger.warning("Gemini questions response missing list, got %s", type(questions))
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"questions": [], "error": "invalid_structure"}
            )

        return _build_base_response(
            ai_status="ok",
            message="AI question generation successful.",
            raw_output=raw_output,
            extra={
                "questions": questions,
                "questions_count": len(questions)
            }
        )

    result = _call_gemini(
        prompt,
        cache_namespace="questions",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.7,
            'response_mime_type': 'application/json',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )

    logger.info("Question generation completed with status: %s", result.get("ai_status"))
    return result


def analyze_converted_strategy_ambiguities(
    converted_strategy: Dict[str, Any],
    existing_answers: Dict[str, Any] = None,
    user=None,
) -> Dict[str, Any]:
    """Analyze ambiguities in a converted strategy (from GapGPT) and generate questions."""
    logger.info("Starting ambiguity analysis for converted strategy...")

    existing_answers = existing_answers or {}

    # Convert converted strategy to a readable format for analysis
    strategy_summary = json.dumps(converted_strategy, ensure_ascii=False, indent=2)
    
    # Truncate if too long
    strategy_summary = truncate_text(strategy_summary, max_tokens=MAX_INPUT_TOKENS // 2)

    if existing_answers:
        answers_text = f"\nجواب‌های قبلی کاربر:\n{json.dumps(existing_answers, ensure_ascii=False, indent=2)}"
    else:
        answers_text = ""

    cache_key = f"converted_ambiguity_{hashlib.sha256(strategy_summary.encode()).hexdigest()}"

    prompt = f"""
    شما یک تحلیلگر حرفه‌ای استراتژی معاملاتی هستید. یک استراتژی تبدیل شده (JSON) دریافت کرده‌اید که از GapGPT آمده است.
    وظیفه شما این است که ابهامات و نقاط ناقص این استراتژی را شناسایی کنید و سوالات هوشمندانه تولید کنید.
    
    استراتژی تبدیل شده (JSON):
    {strategy_summary}
    {answers_text}
    
    **قوانین مهم برای تولید سوالات:**
    
    1. استراتژی تبدیل شده را به دقت بررسی کنید و نقاط مبهم را شناسایی کنید:
       - پارامترهای نامشخص یا ناقص (مثلاً دوره‌های اندیکاتورها، مقادیر حد ضرر/سود)
       - شرایط ورود/خروج که به طور کامل تعریف نشده‌اند
       - منطق معاملاتی که نیاز به توضیح بیشتر دارد
       - تنظیمات مدیریت ریسک که ناقص هستند
    
    2. هدف شما: تولید 3 تا 7 سوال هوشمند که:
       - نقاط مبهم و ناقص استراتژی تبدیل شده را شناسایی کنند
       - به کاربر کمک کنند استراتژی را کامل‌تر و دقیق‌تر کنند
       - پارامترهای مهم را مشخص کنند
       - منطق معاملاتی را واضح‌تر کنند
    
    3. اگر استراتژی کامل و واضح است، سوالات کمتری تولید کنید (مثلاً 2-3 سوال)
       اگر استراتژی مبهم یا ناقص است، سوالات بیشتری تولید کنید (مثلاً 5-7 سوال)
    
    4. سوالات باید متناسب با ساختار JSON استراتژی باشند:
       - اگر entry_conditions وجود دارد، سوالات مربوط به شرایط ورود
       - اگر exit_conditions وجود دارد، سوالات مربوط به شرایط خروج
       - اگر indicators وجود دارد، سوالات مربوط به تنظیمات اندیکاتورها
       - اگر risk_management وجود دارد، سوالات مربوط به مدیریت ریسک
    
    خروجی باید JSON با این ساختار باشد:
    {{
      "questions": [
        {{
          "question_text": "متن سوال به فارسی",
          "question_type": "text|number|choice|multiple_choice|boolean",
          "options": ["گزینه 1", "گزینه 2"],
          "order": 1,
          "context": {{
            "section": "entry|exit|risk|indicator|general",
            "related_text": "بخشی از استراتژی که مربوط به این سوال است"
          }}
        }}
      ]
    }}
    
    فقط JSON بازگردانید و از توضیحات اضافه خودداری کنید.
    """

    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"questions": []}
            )

        try:
            data: Dict[str, Any] = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse ambiguity analysis JSON: %s", exc)
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"questions": [], "error": str(exc)}
            )

        questions = data.get("questions") or []
        if not isinstance(questions, list):
            logger.warning("Ambiguity analysis response missing list, got %s", type(questions))
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"questions": [], "error": "invalid_structure"}
            )

        return _build_base_response(
            ai_status="ok",
            message="AI ambiguity analysis successful.",
            raw_output=raw_output,
            extra={
                "questions": questions,
                "questions_count": len(questions)
            }
        )

    result = _call_gemini(
        prompt,
        cache_namespace="converted_ambiguity",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.7,
            'response_mime_type': 'application/json',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )

    logger.info("Ambiguity analysis completed with status: %s", result.get("ai_status"))
    return result


def parse_strategy_with_answers(
    parsed_strategy: Dict[str, Any],
    raw_text: str,
    answers: Dict[str, Any],
    user=None,
) -> Dict[str, Any]:
    """تبدیل استراتژی به مدل قابل اجرا با استفاده از جواب‌های کاربر و Gemini"""
    if not _providers_available(user=user):
        logger.warning("AI provider not available for strategy conversion")
        return parsed_strategy
    
    # آماده‌سازی اطلاعات برای Gemini
    strategy_info = f"""
    شرایط ورود استخراج شده:
    {chr(10).join(f'- {c}' for c in parsed_strategy.get('entry_conditions', []))}
    
    شرایط خروج استخراج شده:
    {chr(10).join(f'- {c}' for c in parsed_strategy.get('exit_conditions', []))}
    
    اندیکاتورها: {', '.join(parsed_strategy.get('indicators', []))}
    مدیریت ریسک: {json.dumps(parsed_strategy.get('risk_management', {}), ensure_ascii=False)}
    """
    
    answers_text = f"""
    جواب‌های کاربر:
    {json.dumps(answers, ensure_ascii=False, indent=2)}
    """
    
    # Create cache key from strategy content and answers
    cache_key = f"{raw_text[:1000]}_{json.dumps(answers, sort_keys=True)}"
    
    prompt = f"""
    شما یک مبدل حرفه‌ای استراتژی معاملاتی هستید. باید یک استراتژی متنی (فارسی/انگلیسی) را به یک مدل قابل اجرا تبدیل کنید.
    
    اطلاعات استراتژی:
    {strategy_info}
    
    {answers_text}
    
    متن اصلی استراتژی:
    {raw_text[:4000]}
    
    هدف: تبدیل استراتژی به یک ساختار JSON کامل و قابل اجرا که شامل:
    1. شرایط ورود دقیق و قابل اجرا
    2. شرایط خروج دقیق و قابل اجرا
    3. اندیکاتورها با پارامترهای دقیق
    4. مدیریت ریسک کامل
    5. یک مدل اجرایی که برنامه بتواند با آن ترید کند
    
    خروجی باید JSON با این ساختار باشد:
    {{
      "entry_conditions": [
        {{
          "condition": "شرط به صورت متن",
          "type": "indicator|price_action|pattern|custom",
          "params": {{}},
          "code_snippet": "کد Python قابل اجرا (اختیاری)"
        }}
      ],
      "exit_conditions": [...],
      "indicators": {{
        "rsi": {{"period": 14}},
        "macd": {{"fast": 12, "slow": 26, "signal": 9}}
      }},
      "risk_management": {{
        "stop_loss": {{"type": "pips|percentage|price", "value": 50}},
        "take_profit": {{"type": "pips|percentage|price", "value": 100}},
        "risk_per_trade": 2
      }},
      "executable_model": {{
        "entry_logic": "منطق ورود به صورت قابل اجرا",
        "exit_logic": "منطق خروج به صورت قابل اجرا"
      }}
    }}
    
    فقط JSON برگردانید.
    """
    
    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return {
                "ai_status": "error",
                "message": SERVICE_UNAVAILABLE_MESSAGE,
                "raw_output": raw_output,
                "error": "empty_response",
            }

        cleaned = _clean_response_text(raw_output)
        try:
            enhanced_strategy: Dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to decode strategy conversion response: %s", exc)
            return {
                "ai_status": "error",
                "message": SERVICE_UNAVAILABLE_MESSAGE,
                "raw_output": cleaned,
                "error": str(exc),
            }

        return {
            "ai_status": "ok",
            "message": "Strategy conversion successful.",
            "raw_output": cleaned,
            "enhanced_strategy": enhanced_strategy,
        }

    result = _call_gemini(
        prompt,
        cache_namespace="strategy_conversion",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.3,
            'response_mime_type': 'application/json',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )

    # استخراج اطلاعات توکن‌ها
    tokens_used = result.get("tokens_used")
    input_tokens_approx = len(prompt) // 4
    output_tokens_approx = len(result.get("raw_output", "")) // 4
    total_tokens_approx = input_tokens_approx + output_tokens_approx
    
    # اگر tokens_used از API موجود باشد، از آن استفاده کن
    if tokens_used is not None:
        total_tokens_approx = tokens_used
    
    # لاگ استفاده از API
    provider_name = resolve_ai_provider(result)
    if result.get("ai_status") == "ok" and provider_name:
        try:
            from api.api_usage_tracker import log_api_usage
            log_api_usage(
                provider=provider_name,
                endpoint='parse_strategy_with_answers',
                request_type='POST',
                status_code=200,
                success=True,
                tokens=total_tokens_approx,
                user=user,
                metadata={
                    'function': 'parse_strategy_with_answers',
                    'input_tokens_approx': input_tokens_approx,
                    'output_tokens_approx': output_tokens_approx,
                    'total_tokens_approx': total_tokens_approx,
                    'tokens_used': tokens_used,
                    'provider_attempts': result.get("provider_attempts"),
                }
            )
        except Exception as log_error:
            logger.warning("Failed to log AI usage: %s", log_error)

    if result.get("ai_status") == "ok":
        enhanced = result.get("enhanced_strategy") or {}
        if isinstance(enhanced, dict):
            merged = dict(parsed_strategy)
            merged.update(enhanced)
            # اضافه کردن اطلاعات توکن به نتیجه
            merged['_token_info'] = {
                'total_tokens': total_tokens_approx,
                'input_tokens': input_tokens_approx,
                'output_tokens': output_tokens_approx,
                'tokens_used': tokens_used,
                'provider': provider_name,
            }
            return merged

    # حتی در صورت خطا، اطلاعات توکن را برگردان
    parsed_strategy['_token_info'] = {
        'total_tokens': total_tokens_approx,
        'input_tokens': input_tokens_approx,
        'output_tokens': output_tokens_approx,
        'tokens_used': tokens_used,
        'provider': provider_name,
    }
    return parsed_strategy


def analyze_backtest_trades_with_ai(
    backtest_results: Dict[str, Any],
    strategy: Dict[str, Any],
    symbol: str,
    data_provider: str = None,
    data_points: int = 0,
    date_range: str = None,
    user=None
) -> Dict[str, Any]:
    """Analyze backtest trades using AI (Gemini) and return structured analysis."""
    # Prepare comprehensive backtest data for analysis
    analysis_data = {
        "total_trades": backtest_results.get('total_trades', 0),
        "winning_trades": backtest_results.get('winning_trades', 0),
        "losing_trades": backtest_results.get('losing_trades', 0),
        "win_rate": backtest_results.get('win_rate', 0.0),
        "total_return": backtest_results.get('total_return', 0.0),
        "max_drawdown": backtest_results.get('max_drawdown', 0.0),
        "sharpe_ratio": backtest_results.get('sharpe_ratio', 0.0),
        "profit_factor": backtest_results.get('profit_factor', 0.0),
        "entry_conditions": strategy.get('entry_conditions', []),
        "exit_conditions": strategy.get('exit_conditions', []),
        "risk_management": strategy.get('risk_management', {}),
        "symbol": symbol,
        "sample_trades": (backtest_results.get('trades') or [])[:10],
    }

    if data_provider:
        analysis_data["data_provider"] = data_provider
    if data_points > 0:
        analysis_data["data_points"] = data_points
    if date_range:
        analysis_data["date_range"] = date_range

    cache_key = json.dumps(analysis_data, ensure_ascii=False, sort_keys=True)

    prompt = (
        f"{BACKTEST_ANALYSIS_SYSTEM_INSTRUCTIONS}\n\n"
        f"نتایج بک‌تست:\n{json.dumps(analysis_data, ensure_ascii=False, indent=2)}\n\n"
        f"لطفاً تحلیل جامعی ارائه دهید."
    )

    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"analysis_text": ""}
            )

        return _build_base_response(
            ai_status="ok",
            message="Gemini backtest analysis successful.",
            raw_output=raw_output,
            extra={
                "analysis_text": raw_output,
                "analysis_segments": [segment.strip() for segment in raw_output.split("\n\n") if segment.strip()],
                "is_basic": False,
                "source": "llm"
            }
        )

    result = _call_gemini(
        prompt,
        cache_namespace="backtest_analysis",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.7,
            'response_mime_type': 'text/plain',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )

    provider_name = resolve_ai_provider(result)

    if result.get("ai_status") == "ok" and provider_name:
        try:
            from api.api_usage_tracker import log_api_usage

            input_tokens_approx = len(prompt) // 4
            output_tokens_approx = len(result.get("raw_output", "")) // 4
            total_tokens = input_tokens_approx + output_tokens_approx

            log_api_usage(
                provider=provider_name,
                endpoint='analyze_backtest_trades_with_ai',
                request_type='POST',
                status_code=200,
                success=True,
                tokens=total_tokens,
                user=user,
                metadata={
                    'function': 'analyze_backtest_trades_with_ai',
                    'symbol': symbol,
                    'input_tokens_approx': input_tokens_approx,
                    'output_tokens_approx': output_tokens_approx,
                    'total_tokens_approx': total_tokens,
                    'provider_attempts': result.get("provider_attempts"),
                }
            )
        except Exception as log_error:
            logger.warning("Failed to log AI usage: %s", log_error)
    elif result.get("ai_status") == "error" and provider_name:
        try:
            from api.api_usage_tracker import log_api_usage
            log_api_usage(
                provider=provider_name,
                endpoint='analyze_backtest_trades_with_ai',
                request_type='POST',
                status_code=500,
                success=False,
                error_message=result.get("error"),
                user=user,
                metadata={
                    'function': 'analyze_backtest_trades_with_ai',
                    'error': result.get("error"),
                    'provider_attempts': result.get("provider_attempts"),
                }
            )
        except Exception:
            pass

    return result


def generate_basic_backtest_analysis(
    backtest_results: Dict[str, Any], 
    strategy: Dict[str, Any], 
    symbol: str,
    data_provider: str = None,
    data_points: int = 0,
    date_range: str = None
) -> str:
    """Generate a basic backtest analysis without AI - fallback when Gemini is not available"""
    total_trades = backtest_results.get('total_trades', 0)
    winning_trades = backtest_results.get('winning_trades', 0)
    losing_trades = backtest_results.get('losing_trades', 0)
    total_return = backtest_results.get('total_return', 0.0)
    win_rate = backtest_results.get('win_rate', 0.0)
    max_drawdown = backtest_results.get('max_drawdown', 0.0)
    
    entry_conditions = strategy.get('entry_conditions', [])
    exit_conditions = strategy.get('exit_conditions', [])
    
    analysis = f"📊 تحلیل نتایج بک‌تست برای {symbol}\n\n"
    
    # Add data source information at the beginning
    if data_provider or data_points > 0 or date_range:
        analysis += "📊 منابع داده استفاده شده:\n"
        if data_provider:
            analysis += f"• ارائه‌دهنده داده: {data_provider}\n"
        if date_range:
            analysis += f"• بازه زمانی: {date_range}\n"
        if data_points > 0:
            analysis += f"• تعداد نقاط داده: {data_points:,}\n"
        analysis += "\n"
    
    analysis += "=" * 80 + "\n\n"
    
    if total_trades > 0:
        analysis += f"📈 آمار کلی:\n"
        analysis += f"- تعداد کل معاملات: {total_trades}\n"
        analysis += f"- معاملات برنده: {winning_trades}\n"
        analysis += f"- معاملات بازنده: {losing_trades}\n"
        analysis += f"- نرخ برد: {win_rate:.2f}%\n\n"
        
        if winning_trades > losing_trades:
            analysis += f"✅ استراتژی عملکرد مثبتی داشته است. {winning_trades} معامله برنده در مقابل {losing_trades} معامله بازنده.\n\n"
        elif losing_trades > winning_trades:
            analysis += f"⚠️ استراتژی نیاز به بهبود دارد. {losing_trades} معامله بازنده در مقابل {winning_trades} معامله برنده.\n\n"
        else:
            analysis += f"📊 تعداد معاملات برنده و بازنده برابر است.\n\n"
        
        if total_return > 0:
            analysis += f"💹 با استفاده از این استراتژی، سرمایه شما {total_return:.2f}% افزایش یافته است.\n\n"
        elif total_return < 0:
            analysis += f"📉 متأسفانه با این استراتژی، سرمایه شما {abs(total_return):.2f}% کاهش یافته است.\n\n"
        else:
            analysis += f"➡️ این استراتژی در این بازه زمانی سود یا ضرر خاصی نداشته است.\n\n"
    else:
        analysis += "⚠️ هیچ معامله‌ای در این بک‌تست انجام نشده است. ممکن است شرایط ورود یا خروج با داده‌های موجود همخوانی نداشته باشند.\n\n"
    
    # Strategy analysis
    if entry_conditions or exit_conditions:
        analysis += f"📋 تحلیل استراتژی:\n"
        analysis += f"- تعداد شرایط ورود: {len(entry_conditions)}\n"
        analysis += f"- تعداد شرایط خروج: {len(exit_conditions)}\n\n"
        
        if entry_conditions:
            analysis += "شرایط ورود:\n"
            for idx, cond in enumerate(entry_conditions[:5], 1):
                analysis += f"  {idx}. {cond[:100]}...\n"
            analysis += "\n"
        
        if exit_conditions:
            analysis += "شرایط خروج:\n"
            for idx, cond in enumerate(exit_conditions[:5], 1):
                analysis += f"  {idx}. {cond[:100]}...\n"
            analysis += "\n"
    
    # Trade analysis if available
    trades = backtest_results.get('trades', [])
    if trades:
        profits = [t.get('profit', 0) for t in trades if t.get('profit', 0) > 0]
        losses = [t.get('profit', 0) for t in trades if t.get('profit', 0) < 0]
        
        if profits:
            avg_profit = sum(profits) / len(profits)
            analysis += f"💰 متوسط سود هر معامله برنده: {avg_profit:.2f}\n"
        
        if losses:
            avg_loss = abs(sum(losses) / len(losses))
            analysis += f"📉 متوسط ضرر هر معامله بازنده: {avg_loss:.2f}\n"
    
    analysis += "\n" + "=" * 80
    analysis += "\n\n💡 توصیه: برای تحلیل دقیق‌تر هر شرط ورود/خروج، از تحلیل هوش مصنوعی استفاده کنید."
    
    return analysis


def generate_ai_recommendations(
    parsed_strategy: Dict[str, Any],
    raw_text: str = None,
    analysis: Dict[str, Any] = None,
    user=None,
) -> Dict[str, Any]:
    """
    Generate AI recommendations for improving the strategy
    Each recommendation costs 150,000 Toman
    """
    # Prepare strategy information
    strategy_info = f"""
    استراتژی معاملاتی:
    - شرایط ورود: {', '.join(parsed_strategy.get('entry_conditions', []))}
    - شرایط خروج: {', '.join(parsed_strategy.get('exit_conditions', []))}
    - مدیریت ریسک: {json.dumps(parsed_strategy.get('risk_management', {}), ensure_ascii=False)}
    - اندیکاتورها: {', '.join(parsed_strategy.get('indicators', []))}
    - نماد: {parsed_strategy.get('symbol', 'تعیین نشده')}
    - تایم‌فریم: {parsed_strategy.get('timeframe', 'تعیین نشده')}
    """
    
    if raw_text:
        strategy_info += f"\nمتن اصلی استراتژی:\n{raw_text[:2000]}"
    
    if analysis:
        strategy_info += f"\n\nتحلیل فعلی استراتژی:\n{json.dumps(analysis, ensure_ascii=False)}"
    
    prompt = f"""
    شما یک مشاور حرفه‌ای معاملاتی هستید. بر اساس استراتژی زیر، 3-5 پیشنهاد عملی و قابل اجرا برای بهبود استراتژی ارائه دهید.
    
    {strategy_info}
    
    هر پیشنهاد باید:
    1. یک عنوان واضح و کاربردی داشته باشد
    2. توضیح کاملی از پیشنهاد ارائه دهد
    3. نوع پیشنهاد را مشخص کند (entry_condition, exit_condition, risk_management, indicator, parameter, general)
    4. داده‌های قابل اجرا برای اعمال پیشنهاد داشته باشد
    
    خروجی باید JSON با این ساختار باشد:
    {{
      "recommendations": [
        {{
          "title": "عنوان پیشنهاد",
          "description": "توضیح کامل پیشنهاد",
          "type": "entry_condition|exit_condition|risk_management|indicator|parameter|general",
          "data": {{
            "suggested_value": "مقدار پیشنهادی",
            "implementation": "روش پیاده‌سازی",
            "expected_improvement": "بهبود مورد انتظار"
          }}
        }}
      ]
    }}
    
    فقط JSON برگردانید، بدون توضیحات اضافی.
    """
    
    cache_key = f"{strategy_info}\n{analysis}"

    def _parse_response(raw_output: str) -> Dict[str, Any]:
        if not raw_output:
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"recommendations": []}
            )
        try:
            data: Dict[str, Any] = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            logger.error("Error parsing AI recommendations JSON: %s", exc)
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"recommendations": [], "error": str(exc)}
            )

        recommendations = data.get("recommendations") or []
        if not isinstance(recommendations, list):
            return _build_base_response(
                ai_status="error",
                message=SERVICE_UNAVAILABLE_MESSAGE,
                raw_output=raw_output,
                extra={"recommendations": [], "error": "invalid_structure"}
            )

        return _build_base_response(
            ai_status="ok",
            message="AI recommendations generated.",
            raw_output=raw_output,
            extra={
                "recommendations": recommendations,
                "recommendations_count": len(recommendations),
                "is_basic": False
            }
        )

    return _call_gemini(
        prompt,
        cache_namespace="recommendations",
        cache_key=cache_key,
        generation_config={
            'temperature': 0.8,
            'response_mime_type': 'application/json',
            'provider_metadata': {'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
        },
        response_parser=_parse_response,
        user=user,
    )

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

# Constants & configuration defaults
CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours
RATE_LIMIT_CALLS_PER_MINUTE = 60
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_INPUT_TOKENS = 32000
MAX_OUTPUT_TOKENS = 8000
DISABLED_MESSAGE = "AI analysis unavailable. Please configure your AI provider (OpenAI ChatGPT or Gemini) in Settings."
SERVICE_UNAVAILABLE_MESSAGE = "AI service temporarily unavailable."
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


def _providers_available() -> bool:
    manager = get_provider_manager()
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


def _get_gemini_api_key() -> Optional[str]:
    """Compatibility helper to fetch Gemini API key."""
    provider = get_provider_manager().providers.get("gemini")
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
    response_parser: Callable[[str], Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute AI provider call with caching, rate limiting, and standardized responses."""
    manager = get_provider_manager()
    digest = _hash_text(cache_key)
    cached = _load_cache(cache_namespace, digest)
    if cached:
        return cached

    if not manager.has_available_provider():
        return _build_base_response(
            ai_status="disabled",
            message=DISABLED_MESSAGE,
            extra={"error": "no_provider_available"}
        )

    rate_limit_error = _enforce_rate_limit()
    if rate_limit_error:
        return rate_limit_error

    config = dict(generation_config or {})
    configured_max_tokens = getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', MAX_OUTPUT_TOKENS)
    config.setdefault('max_output_tokens', min(configured_max_tokens, MAX_OUTPUT_TOKENS))
    metadata = config.pop('provider_metadata', None) or {}

    result = manager.generate(prompt, config, metadata=metadata)

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
        logger.warning(
            "AI providers failed to generate response: %s",
            result.error or "unknown_error",
        )
        error_text = result.error or SERVICE_UNAVAILABLE_MESSAGE
        user_message = _translate_ai_error_message(error_text)
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

    if parsed_response.get("ai_status") == "ok":
        _write_cache(cache_namespace, digest, parsed_response)

    return parsed_response


def parse_with_gemini(text: str) -> Dict[str, Any]:
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
        response_parser=_parse_response
    )


def call_gemini_analyzer(text: str) -> Dict[str, Any]:
    """Public helper used by tests to parse strategy text via Gemini."""
    return parse_with_gemini(text)


def generate_basic_analysis(parsed_strategy: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a basic analysis without AI - fallback when Gemini is not available"""
    entry_conditions = parsed_strategy.get('entry_conditions', [])
    exit_conditions = parsed_strategy.get('exit_conditions', [])
    risk_management = parsed_strategy.get('risk_management', {})
    indicators = parsed_strategy.get('indicators', [])
    
    summary = f"استراتژی شامل {len(entry_conditions)} شرط ورود و {len(exit_conditions)} شرط خروج است."
    if indicators:
        summary += f" از اندیکاتورهای {', '.join(indicators)} استفاده می‌کند."
    
    strengths = []
    if entry_conditions:
        strengths.append("دارای شرایط ورود مشخص است")
    if exit_conditions:
        strengths.append("دارای شرایط خروج مشخص است")
    if risk_management:
        strengths.append("مدیریت ریسک تعریف شده است")
    
    weaknesses = []
    if not entry_conditions:
        weaknesses.append("شرایط ورود مشخص نیست")
    if not exit_conditions:
        weaknesses.append("شرایط خروج مشخص نیست")
    if not risk_management:
        weaknesses.append("مدیریت ریسک کامل نیست")
    
    risk_assessment = "ریسک متوسط"
    if not risk_management.get('stop_loss'):
        risk_assessment = "ریسک بالا - حد ضرر تعریف نشده است"
    
    recommendations = []
    if not risk_management.get('stop_loss'):
        recommendations.append("تعریف حد ضرر برای مدیریت ریسک")
    if len(entry_conditions) < 2:
        recommendations.append("افزودن شرایط ورود بیشتر برای افزایش دقت")
    
    quality_score = 50
    if entry_conditions and exit_conditions and risk_management:
        quality_score = 70
    if len(entry_conditions) > 2 and len(exit_conditions) > 1:
        quality_score = 80
    
    return {
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "risk_assessment": risk_assessment,
        "recommendations": recommendations,
        "quality_score": quality_score / 100.0,
        "is_basic": True
    }


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
        response_parser=_parse_response
    )

    provider_name = result.get("ai_provider") or result.get("provider") or "ai"

    if result.get("ai_status") == "ok":
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
    elif result.get("ai_status") == "error":
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
    existing_answers: Dict[str, Any] = None
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
        response_parser=_parse_response
    )

    logger.info("Question generation completed with status: %s", result.get("ai_status"))
    return result


def parse_strategy_with_answers(
    parsed_strategy: Dict[str, Any],
    raw_text: str,
    answers: Dict[str, Any]
) -> Dict[str, Any]:
    """تبدیل استراتژی به مدل قابل اجرا با استفاده از جواب‌های کاربر و Gemini"""
    if not _providers_available():
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
        response_parser=_parse_response
    )

    if result.get("ai_status") == "ok":
        enhanced = result.get("enhanced_strategy") or {}
        if isinstance(enhanced, dict):
            merged = dict(parsed_strategy)
            merged.update(enhanced)
            return merged

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
        response_parser=_parse_response
    )

    provider_name = result.get("ai_provider") or result.get("provider") or "ai"

    if result.get("ai_status") == "ok":
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
    elif result.get("ai_status") == "error":
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
    analysis: Dict[str, Any] = None
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
        response_parser=_parse_response
    )

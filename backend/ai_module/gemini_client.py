"""
Google Gemini AI client for strategy analysis and parsing
"""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

# Try to import google-generativeai
try:
    import google.generativeai as genai
except ImportError:
    genai = None
    logger.warning("google-generativeai not installed. Gemini features will be disabled.")

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


def _get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from database or settings"""
    from core.models import APIConfiguration
    
    try:
        api_config = APIConfiguration.objects.filter(
            provider='gemini',
            is_active=True
        ).first()
        
        if api_config and api_config.api_key:
            return api_config.api_key.strip()
    except Exception as e:
        logger.warning(f"Error getting API key from database: {e}")
    
    # Fallback to settings
    return getattr(settings, 'GEMINI_API_KEY', '')


def _init_client():
    """Initialize Gemini client"""
    if genai is None:
        return None
    
    api_key = _get_gemini_api_key()
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.0-flash')
        return genai.GenerativeModel(model_name)
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {e}")
        return None


def _client_ready() -> bool:
    """Check if Gemini client is ready"""
    if genai is None:
        return False
    
    gemini_enabled = getattr(settings, 'GEMINI_ENABLED', True)
    if not gemini_enabled:
        return False
    
    api_key = _get_gemini_api_key()
    if not api_key:
        return False
    
    return True


def parse_with_gemini(text: str) -> Optional[Dict[str, Any]]:
    """Parse strategy text using Gemini"""
    if not _client_ready():
        return None
    
    # Hash for caching
    digest = _hash_text(text[:4000])
    cache_file = _CACHE_DIR / f"parse_{digest}.json"
    
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding='utf-8'))
        except Exception:
            pass
    
    client = _init_client()
    if client is None:
        return None
    
    prompt = f"""
    این یک استراتژی معاملاتی است که به فارسی یا انگلیسی نوشته شده است. 
    لطفاً آن را تحلیل کنید و اطلاعات زیر را استخراج کنید:
    
    {text[:4000]}
    
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
    
    try:
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 1024),
                'response_mime_type': 'application/json',
            },
        )
        
        content = response.text if hasattr(response, 'text') else None
        if not content:
            return None
        
        content_str = content.strip()
        if content_str.startswith('```'):
            content_str = content_str.strip('`')
            parts = content_str.split('\n', 1)
            content_str = parts[1] if len(parts) > 1 else parts[0]
        
        data = json.loads(content_str)
        
        # Cache result
        try:
            cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass
        
        return data
    except Exception as e:
        logger.warning(f"Gemini parsing failed: {e}")
        return None


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


def analyze_strategy_with_gemini(parsed_strategy: Dict[str, Any], raw_text: str = None) -> Optional[Dict[str, Any]]:
    """Generate comprehensive analysis of a trading strategy using Gemini AI"""
    if not _client_ready():
        logger.warning("Gemini not available for strategy analysis")
        return None

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
        strategy_description += f"\nمتن اصلی استراتژی:\n{raw_text[:2000]}"

    # Hash for caching
    digest = _hash_text(strategy_description)
    cache_file = _CACHE_DIR / f"analysis_{digest}.json"

    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding='utf-8'))
        except Exception:
            pass

    client = _init_client()
    if client is None:
        return None

    prompt = (
        f"{ANALYSIS_SYSTEM_INSTRUCTIONS}\n\n"
        f"{strategy_description}\n\n"
        f"لطفاً تحلیل جامعی ارائه دهید."
    )

    try:
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 2048),
                'response_mime_type': 'application/json',
            },
        )

        content = response.text if hasattr(response, 'text') else None
        if not content:
            return None

        # Parse JSON response
        content_str = content.strip()
        if content_str.startswith('```'):
            content_str = content_str.strip('`')
            parts = content_str.split('\n', 1)
            content_str = parts[1] if len(parts) > 1 else parts[0]

        data: Dict[str, Any] = json.loads(content_str)

        # Validate structure
        if not isinstance(data, dict):
            return None

        # Ensure all required fields exist
        if 'strengths' not in data:
            data['strengths'] = []
        if 'weaknesses' not in data:
            data['weaknesses'] = []
        if 'risk_assessment' not in data:
            data['risk_assessment'] = 'ارزیابی ریسک در دسترس نیست.'
        if 'recommendations' not in data:
            data['recommendations'] = []
        if 'summary' not in data:
            data['summary'] = 'تحلیل در دسترس نیست.'
        if 'quality_score' not in data:
            data['quality_score'] = 50
        
        # Convert quality_score to float if it's an integer
        if isinstance(data['quality_score'], int):
            data['quality_score'] = data['quality_score'] / 100.0
        elif isinstance(data['quality_score'], float) and data['quality_score'] > 1.0:
            data['quality_score'] = data['quality_score'] / 100.0

        try:
            cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass

        return data
    except Exception as e:
        logger.warning("Gemini strategy analysis failed: %s", e)
        return None


def generate_strategy_questions(
    parsed_strategy: Dict[str, Any],
    raw_text: str,
    existing_answers: Dict[str, Any] = None
) -> Optional[List[Dict[str, Any]]]:
    """تولید سوالات هوشمند برای تکمیل استراتژی با استفاده از Gemini"""
    logger.info("Starting question generation...")
    
    if not _client_ready():
        api_key = _get_gemini_api_key()
        if not api_key:
            logger.error("Gemini API key not found")
        if genai is None:
            logger.error("google-generativeai library not installed")
        logger.warning("Gemini not available for question generation")
        return None
    
    existing_answers = existing_answers or {}
    
    # آماده‌سازی متن استراتژی
    strategy_summary = f"""
    شرایط ورود استخراج شده: {len(parsed_strategy.get('entry_conditions', []))} شرط
    شرایط خروج استخراج شده: {len(parsed_strategy.get('exit_conditions', []))} شرط
    اندیکاتورها: {', '.join(parsed_strategy.get('indicators', []))}
    امتیاز اعتماد: {parsed_strategy.get('confidence_score', 0) * 100:.0f}%
    """
    
    if existing_answers:
        strategy_summary += f"\nجواب‌های قبلی کاربر:\n{json.dumps(existing_answers, ensure_ascii=False, indent=2)}"
    
    prompt = f"""
    شما یک تحلیلگر حرفه‌ای استراتژی معاملاتی هستید. بر اساس استراتژی که دریافت می‌کنید، باید سوالات هوشمندانه و هدفمند تولید کنید که به کاربر کمک کند استراتژی را کامل‌تر و دقیق‌تر تعریف کند.
    
    استراتژی:
    {strategy_summary}
    
    متن اصلی استراتژی (قسمت اول):
    {raw_text[:3000]}
    
    **قوانین مهم برای تولید سوالات:**
    
    1. **قبل از تولید هر سوال، ابتدا بررسی کنید که آیا پاسخ آن سوال در متن استراتژی موجود است یا نه**
       - اگر پاسخ سوال به طور واضح و کامل در متن استراتژی آمده است، آن سوال را تولید نکنید
       - فقط سوالاتی را تولید کنید که پاسخشان در متن موجود نیست یا به طور مبهم بیان شده است
    
    2. **هدف شما: تولید 3-5 سوال هوشمند که:**
       - نقاط مبهم و ناقص استراتژی را شناسایی کنند (نه چیزهایی که در متن واضح هستند)
       - به کاربر کمک کنند شرایط ورود/خروج را دقیق‌تر تعریف کنند (فقط اگر در متن مبهم است)
       - پارامترهای مهم (مثل حد ضرر، حد سود، تایم فریم) را مشخص کنند (فقط اگر در متن مشخص نشده)
       - اندیکاتورها و تنظیمات آنها را مشخص کنند (فقط اگر در متن مشخص نشده)
    
    3. **مثال:**
       - اگر در متن استراتژی نوشته شده "حد ضرر 50 پیپ است"، سوال "حد ضرر چقدر است؟" را تولید نکنید
       - اگر در متن نوشته شده "از اندیکاتور RSI استفاده می‌کنیم"، سوال "کدام اندیکاتور استفاده می‌شود؟" را تولید نکنید
       - فقط سوالاتی تولید کنید که پاسخشان در متن موجود نیست
    
    خروجی باید یک JSON با این ساختار باشد:
    {{
      "questions": [
        {{
          "question_text": "متن سوال به فارسی",
          "question_type": "text|number|choice|multiple_choice|boolean",
          "options": ["گزینه 1", "گزینه 2"] (فقط برای choice و multiple_choice),
          "order": 1,
          "context": {{
            "section": "entry|exit|risk|indicator",
            "related_text": "بخشی از متن که مربوط به این سوال است"
          }}
        }}
      ]
    }}
    
    نکات مهم:
    - سوالات باید به فارسی و واضح باشند
    - برای سوالات عددی (مثل حد ضرر، حد سود) از نوع "number" استفاده کنید
    - برای سوالات بله/خیر از نوع "boolean" استفاده کنید
    - برای انتخاب از چند گزینه از "choice" استفاده کنید
    - ترتیب سوالات مهم است (از مهم‌ترین شروع کنید)
    - اگر جواب‌های قبلی وجود دارد، سوالات جدید نباید تکراری باشند
    - **مهم: فقط سوالاتی تولید کنید که پاسخشان در متن موجود نیست**
    
    فقط JSON برگردانید، بدون توضیحات اضافی.
    """
    
    client = _init_client()
    if client is None:
        logger.error("Failed to initialize Gemini client")
        return None
    
    try:
        logger.info("Sending request to Gemini API...")
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 2048),
                'response_mime_type': 'application/json',
            },
        )
        
        logger.info("Received response from Gemini API")
        content = response.text if hasattr(response, 'text') else None
        if not content:
            logger.error("Gemini API returned empty response")
            return None
        
        # Parse JSON
        content_str = content.strip()
        if content_str.startswith('```'):
            content_str = content_str.strip('`')
            parts = content_str.split('\n', 1)
            content_str = parts[1] if len(parts) > 1 else parts[0]
        
        try:
            data: Dict[str, Any] = json.loads(content_str)
        except json.JSONDecodeError as json_error:
            logger.error(f"Failed to parse JSON response: {json_error}")
            logger.error(f"Response content: {content_str[:500]}")
            return None
        
        if not isinstance(data, dict) or 'questions' not in data:
            logger.error(f"Invalid response structure. Expected 'questions' key. Got: {list(data.keys()) if isinstance(data, dict) else type(data)}")
            return None
        
        questions = data['questions']
        if not isinstance(questions, list):
            logger.error(f"Questions is not a list. Got: {type(questions)}")
            return None
        
        if len(questions) == 0:
            logger.warning("Gemini returned empty questions list")
            return None
        
        logger.info(f"Successfully generated {len(questions)} questions")
        return questions
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Gemini question generation failed: {str(e)}\n{error_trace}")
        return None


def parse_strategy_with_answers(
    parsed_strategy: Dict[str, Any],
    raw_text: str,
    answers: Dict[str, Any]
) -> Dict[str, Any]:
    """تبدیل استراتژی به مدل قابل اجرا با استفاده از جواب‌های کاربر و Gemini"""
    if not _client_ready():
        logger.warning("Gemini not available for strategy conversion")
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
    
    client = _init_client()
    if client is None:
        return parsed_strategy
    
    try:
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 4096),
                'response_mime_type': 'application/json',
            },
        )
        
        content = response.text if hasattr(response, 'text') else None
        if not content:
            return parsed_strategy
        
        content_str = content.strip()
        if content_str.startswith('```'):
            content_str = content_str.strip('`')
            parts = content_str.split('\n', 1)
            content_str = parts[1] if len(parts) > 1 else parts[0]
        
        enhanced_strategy: Dict[str, Any] = json.loads(content_str)
        
        # Merge with original parsed strategy
        merged = dict(parsed_strategy)
        merged.update(enhanced_strategy)
        
        return merged
        
    except Exception as e:
        logger.warning(f"Gemini strategy conversion failed: {e}")
        return parsed_strategy


def analyze_backtest_trades_with_ai(
    backtest_results: Dict[str, Any],
    strategy: Dict[str, Any],
    symbol: str
) -> Optional[str]:
    """Analyze backtest trades using AI (Gemini) and return Persian text analysis."""
    if not _client_ready():
        logger.warning("Gemini not available for backtest analysis")
        return None
    
    # Prepare comprehensive backtest data for analysis
    total_trades = backtest_results.get('total_trades', 0)
    winning_trades = backtest_results.get('winning_trades', 0)
    losing_trades = backtest_results.get('losing_trades', 0)
    total_return = backtest_results.get('total_return', 0.0)
    win_rate = backtest_results.get('win_rate', 0.0)
    max_drawdown = backtest_results.get('max_drawdown', 0.0)
    sharpe_ratio = backtest_results.get('sharpe_ratio', 0.0)
    profit_factor = backtest_results.get('profit_factor', 0.0)
    
    trades = backtest_results.get('trades', [])
    
    # Strategy info
    entry_conditions = strategy.get('entry_conditions', [])
    exit_conditions = strategy.get('exit_conditions', [])
    risk_management = strategy.get('risk_management', {})
    
    # Create analysis data
    analysis_data = {
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "total_return": total_return,
        "max_drawdown": max_drawdown,
        "sharpe_ratio": sharpe_ratio,
        "profit_factor": profit_factor,
        "entry_conditions": entry_conditions,
        "exit_conditions": exit_conditions,
        "risk_management": risk_management,
        "symbol": symbol,
        "sample_trades": trades[:10] if trades else []
    }
    
    # Hash for caching
    digest = _hash_text(json.dumps(analysis_data, sort_keys=True))
    cache_file = _CACHE_DIR / f"backtest_analysis_{digest}.txt"
    
    if cache_file.exists():
        try:
            return cache_file.read_text(encoding='utf-8')
        except Exception:
            pass
    
    prompt = (
        f"{BACKTEST_ANALYSIS_SYSTEM_INSTRUCTIONS}\n\n"
        f"نتایج بک‌تست:\n{json.dumps(analysis_data, ensure_ascii=False, indent=2)}\n\n"
        f"لطفاً تحلیل جامعی ارائه دهید."
    )
    
    client = _init_client()
    if client is None:
        return None
    
    try:
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.7,
                'max_output_tokens': getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 4096),
            },
        )
        
        analysis_text = response.text if hasattr(response, 'text') else None
        if not analysis_text:
            return None
        
        analysis_text = analysis_text.strip()
        if analysis_text.startswith('```'):
            analysis_text = analysis_text.strip('`')
            parts = analysis_text.split('\n', 1)
            analysis_text = parts[1] if len(parts) > 1 else parts[0]
        
        # Cache result
        try:
            cache_file.write_text(analysis_text, encoding='utf-8')
        except Exception:
            pass
        
        return analysis_text
    except Exception as e:
        logger.warning("Gemini backtest analysis failed: %s", e)
        return None


def generate_basic_backtest_analysis(backtest_results: Dict[str, Any], strategy: Dict[str, Any], symbol: str) -> str:
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
) -> Optional[List[Dict[str, Any]]]:
    """
    Generate AI recommendations for improving the strategy
    Each recommendation costs 150,000 Toman
    """
    if not _client_ready():
        logger.warning("Gemini not available for recommendations generation")
        return None
    
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
    
    client = _init_client()
    if client is None:
        return None
    
    try:
        response = client.generate_content(
            prompt,
            generation_config={
                'temperature': 0.8,
                'max_output_tokens': getattr(settings, 'GEMINI_MAX_OUTPUT_TOKENS', 4096),
                'response_mime_type': 'application/json',
            },
        )
        
        content = response.text if hasattr(response, 'text') else None
        if not content:
            return None
        
        content_str = content.strip()
        if content_str.startswith('```'):
            content_str = content_str.strip('`')
            parts = content_str.split('\n', 1)
            content_str = parts[1] if len(parts) > 1 else parts[0]
        
        data: Dict[str, Any] = json.loads(content_str)
        
        if not isinstance(data, dict) or 'recommendations' not in data:
            return None
        
        recommendations = data['recommendations']
        if not isinstance(recommendations, list):
            return None
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {str(e)}")
        return None

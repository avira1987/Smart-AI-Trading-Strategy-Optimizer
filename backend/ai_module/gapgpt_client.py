"""
GapGPT API Client for strategy conversion and analysis
مستندات: https://gapgpt.app/platform/quickstart

این کلاینت برای تبدیل متن استراتژی‌های معاملاتی به مدل‌های AI مختلف استفاده می‌شود.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, List
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# GapGPT API Configuration
GAPGPT_API_BASE_URL = "https://api.gapgpt.app"
GAPGPT_DEFAULT_MODEL = "gpt-4o"  # مدل پیش‌فرض که در تست موفق بود


def get_gapgpt_api_key(user=None) -> Optional[str]:
    """
    دریافت کلید API GapGPT از دیتابیس یا environment variable
    
    اولویت:
    1. کلید کاربری از دیتابیس
    2. کلید سیستمی از دیتابیس
    3. Environment variable
    
    Returns:
        کلید API یا None در صورت عدم وجود
    """
    try:
        from core.models import APIConfiguration
        
        # 1. کلید کاربری
        if user and hasattr(user, 'is_authenticated') and user.is_authenticated:
            config = APIConfiguration.objects.filter(
                provider='gapgpt',
                is_active=True,
                user=user
            ).order_by('-updated_at').first()
            
            if config and config.api_key and config.api_key.strip():
                api_key = config.api_key.strip()
                # اعتبارسنجی کلید
                if api_key.startswith('sk-') and len(api_key) > 20:
                    logger.debug(f"Found user-specific GapGPT API key for user {user.id}")
                    return api_key
        
        # 2. کلید سیستمی
        config = APIConfiguration.objects.filter(
            provider='gapgpt',
            is_active=True,
            user__isnull=True
        ).order_by('-updated_at').first()
        
        if config and config.api_key and config.api_key.strip():
            api_key = config.api_key.strip()
            if api_key.startswith('sk-') and len(api_key) > 20:
                logger.debug("Found system-wide GapGPT API key")
                return api_key
                
    except Exception as e:
        logger.warning(f"Error fetching GapGPT API key from DB: {e}")
    
    # 3. Environment variable
    api_key = getattr(settings, 'GAPGPT_API_KEY', None)
    if api_key and api_key.strip() and api_key.startswith('sk-'):
        logger.debug("Found GapGPT API key from environment")
        return api_key.strip()
    
    return None


def test_gapgpt_api_key(api_key: str, user=None) -> Dict[str, Any]:
    """
    تست اعتبار کلید API GapGPT
    
    Args:
        api_key: کلید API برای تست
        user: کاربر فعلی (اختیاری)
    
    Returns:
        Dict شامل:
        - success: bool - آیا تست موفق بود؟
        - message: str - پیام نتیجه
        - available_models: int - تعداد مدل‌های در دسترس
        - model_used: str - مدل استفاده شده در تست
        - tokens_used: int - تعداد توکن‌های استفاده شده
        - error: str - پیام خطا در صورت وجود
    """
    if not api_key or not api_key.strip():
        return {
            'success': False,
            'message': 'کلید API خالی است',
            'error': 'API key is empty'
        }
    
    api_key = api_key.strip()
    
    # Test 1: Try to get available models
    try:
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/models"
        response = requests.get(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('data', [])
            
            if models and len(models) > 0:
                # If we got models, test is successful
                return {
                    'success': True,
                    'message': f'کلید API معتبر است. {len(models)} مدل در دسترس است.',
                    'available_models': len(models),
                    'models': [m.get('id', m.get('name', '')) for m in models[:5]]
                }
            else:
                # If no models, try a simple conversion test
                logger.warning("GapGPT models list was empty, trying conversion test")
        
        elif response.status_code == 401:
            return {
                'success': False,
                'message': 'کلید API نامعتبر است. لطفاً کلید صحیح را وارد کنید.',
                'error': 'Invalid API key',
                'status_code': 401
            }
        elif response.status_code == 403:
            return {
                'success': False,
                'message': 'دسترسی رد شد. لطفاً کلید API را بررسی کنید.',
                'error': 'Permission denied',
                'status_code': 403
            }
        elif response.status_code == 429:
            return {
                'success': False,
                'message': 'محدودیت نرخ استفاده از GapGPT رسیده است. لطفاً چند لحظه صبر کنید.',
                'error': 'Rate limit exceeded',
                'status_code': 429
            }
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get('message', error_msg)
                elif isinstance(error_detail, str):
                    error_msg = error_detail
            except:
                error_msg = response.text[:200] if response.text else error_msg
            
            logger.warning(f"GapGPT models API returned {response.status_code}: {error_msg}")
            # Continue to conversion test
    
    except requests.exceptions.Timeout:
        logger.warning("Timeout fetching GapGPT models, trying conversion test")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching GapGPT models: {e}, trying conversion test")
    except Exception as e:
        logger.warning(f"Unexpected error fetching GapGPT models: {e}, trying conversion test")
    
    # Test 2: Try a simple conversion
    try:
        model_id = GAPGPT_DEFAULT_MODEL
        prompt = "Say 'test' and return {\"status\": \"ok\"} as JSON."
        
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/chat/completions"
        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "You must respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 50,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=15
        )
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            choices = data.get('choices', [])
            usage = data.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            
            if choices:
                return {
                    'success': True,
                    'message': f'کلید API معتبر است. تست تبدیل با موفقیت انجام شد.',
                    'available_models': 0,  # Couldn't get models count
                    'model_used': model_id,
                    'tokens_used': tokens_used,
                    'latency_ms': latency_ms
                }
            else:
                return {
                    'success': False,
                    'message': 'پاسخ نامعتبر از GapGPT API',
                    'error': 'Invalid response format',
                    'status_code': 200
                }
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get('message', error_msg)
                elif isinstance(error_detail, str):
                    error_msg = error_detail
            except:
                error_msg = response.text[:200] if response.text else error_msg
            
            if response.status_code == 401:
                error_msg = 'کلید API GapGPT نامعتبر است. لطفاً کلید صحیح را وارد کنید.'
            elif response.status_code == 429:
                error_msg = 'محدودیت نرخ استفاده از GapGPT رسیده است. لطفاً چند لحظه صبر کنید.'
            elif response.status_code == 404:
                error_msg = 'مدل انتخابی در دسترس نیست. لطفاً مدل دیگری انتخاب کنید.'
            
            return {
                'success': False,
                'message': error_msg,
                'error': error_msg,
                'status_code': response.status_code,
                'latency_ms': latency_ms
            }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'message': 'زمان اتصال به GapGPT API تمام شد. لطفاً اتصال اینترنت خود را بررسی کنید.',
            'error': 'Connection timeout'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'success': False,
            'message': 'خطا در اتصال به GapGPT API. لطفاً اتصال اینترنت خود را بررسی کنید.',
            'error': f'Connection error: {str(e)}'
        }
    except Exception as e:
        logger.exception(f"Unexpected error testing GapGPT API: {e}")
        return {
            'success': False,
            'message': f'خطای غیرمنتظره در تست API: {str(e)}',
            'error': str(e)
        }


def get_available_models(user=None, filter_chat_models=True) -> List[Dict[str, Any]]:
    """
    دریافت لیست مدل‌های موجود در GapGPT
    
    Args:
        user: کاربر فعلی (برای دریافت API key)
        filter_chat_models: اگر True باشد، فقط مدل‌های چت را برمی‌گرداند
    
    Returns:
        لیست دیکشنری‌ها شامل id, name, description برای هر مدل
    """
    api_key = get_gapgpt_api_key(user)
    if not api_key:
        logger.warning("GapGPT API key not found, returning default models")
        return _get_default_models()
    
    try:
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/models"
        
        response = requests.get(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # فرمت پاسخ GapGPT
            if isinstance(data, dict) and 'data' in data:
                models = data['data']
            elif isinstance(data, list):
                models = data
            else:
                models = []
            
            result = []
            for model in models:
                if not isinstance(model, dict):
                    continue
                    
                model_id = model.get('id')
                if not model_id:
                    continue
                
                # فیلتر کردن مدل‌های چت (حذف image-generation, tts, etc)
                if filter_chat_models:
                    supported_types = model.get('supported_endpoint_types', [])
                    if 'openai' not in supported_types or 'image-generation' in supported_types:
                        continue
                
                # نام مناسب برای نمایش
                name = model_id
                if '/' in model_id:
                    name = model_id.split('/')[-1]
                
                result.append({
                    'id': model_id,
                    'name': name.replace('-', ' ').replace('_', ' ').title(),
                    'description': f"{model.get('owned_by', 'unknown').title()} Model",
                    'owned_by': model.get('owned_by', 'unknown'),
                    'endpoint_types': model.get('supported_endpoint_types', [])
                })
            
            # مرتب‌سازی: مدل‌های GPT اول، سپس بقیه
            def sort_key(m):
                id_lower = m['id'].lower()
                if 'gpt-4' in id_lower or 'gpt-5' in id_lower:
                    return (0, m['id'])
                elif 'claude' in id_lower:
                    return (1, m['id'])
                elif 'gemini' in id_lower:
                    return (2, m['id'])
                else:
                    return (3, m['id'])
            
            result.sort(key=sort_key)
            
            if result:
                logger.info(f"Retrieved {len(result)} GapGPT models")
                return result
                
    except requests.exceptions.Timeout:
        logger.warning("Timeout fetching GapGPT models, using defaults")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching GapGPT models: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error fetching GapGPT models: {e}", exc_info=True)
    
    # Fallback به مدل‌های پیش‌فرض
    return _get_default_models()


def _get_default_models() -> List[Dict[str, Any]]:
    """مدل‌های پیش‌فرض GapGPT (در صورت عدم دسترسی به API)"""
    return [
        {
            'id': 'gpt-4o',
            'name': 'GPT-4o',
            'description': 'OpenAI GPT-4o Model via GapGPT',
            'owned_by': 'openai',
            'endpoint_types': ['openai']
        },
        {
            'id': 'gpt-5',
            'name': 'GPT-5',
            'description': 'OpenAI GPT-5 Model via GapGPT',
            'owned_by': 'openai',
            'endpoint_types': ['openai']
        },
        {
            'id': 'gpt-4o-mini',
            'name': 'GPT-4o Mini',
            'description': 'OpenAI GPT-4o Mini Model via GapGPT',
            'owned_by': 'openai',
            'endpoint_types': ['openai']
        },
        {
            'id': 'claude-3-5-sonnet-20241022',
            'name': 'Claude 3.5 Sonnet',
            'description': 'Anthropic Claude 3.5 Sonnet via GapGPT',
            'owned_by': 'vertex-ai',
            'endpoint_types': ['anthropic', 'openai']
        },
        {
            'id': 'gemini-1.5-pro',
            'name': 'Gemini 1.5 Pro',
            'description': 'Google Gemini 1.5 Pro via GapGPT',
            'owned_by': 'vertex-ai',
            'endpoint_types': ['gemini', 'openai']
        },
    ]


def convert_strategy_with_gapgpt(
    strategy_text: str,
    model_id: str = None,
    user=None,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    json_response: bool = True,
    timeout: int = 60,
    **kwargs
) -> Dict[str, Any]:
    """
    تبدیل متن استراتژی به مدل AI با استفاده از GapGPT
    
    Args:
        strategy_text: متن استراتژی معاملاتی
        model_id: ID مدل AI (اگر None باشد، از مدل پیش‌فرض استفاده می‌شود)
        user: کاربر فعلی (برای دریافت API key)
        temperature: دما برای تولید متن (0.0 تا 2.0)
        max_tokens: حداکثر تعداد توکن برای پاسخ
        json_response: آیا پاسخ باید JSON باشد؟
        timeout: تایم‌اوت برای درخواست (ثانیه)
        **kwargs: پارامترهای اضافی
    
    Returns:
        Dict شامل:
        - success: bool - آیا درخواست موفق بود؟
        - converted_strategy: dict یا str - استراتژی تبدیل شده
        - model_used: str - مدل استفاده شده
        - tokens_used: int - تعداد توکن‌های استفاده شده
        - latency_ms: float - زمان پاسخ (میلی‌ثانیه)
        - error: str - پیام خطا در صورت وجود
        - raw_response: str - پاسخ خام از API
    """
    # دریافت API key
    api_key = get_gapgpt_api_key(user)
    if not api_key:
        return {
            'success': False,
            'error': 'کلید API GapGPT تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید GapGPT را اضافه کنید.',
            'converted_strategy': None,
            'model_used': model_id or GAPGPT_DEFAULT_MODEL,
            'tokens_used': 0,
            'latency_ms': 0
        }
    
    # تعیین مدل
    model = model_id or GAPGPT_DEFAULT_MODEL
    
    # آماده‌سازی prompt
    prompt = f"""شما یک متخصص حرفه‌ای تبدیل استراتژی معاملاتی هستید. 

لطفاً استراتژی زیر را تحلیل کرده و آن را به یک مدل قابل اجرا و بهینه تبدیل کنید.

**استراتژی:**
{strategy_text[:8000]}

**خروجی مورد انتظار:**
یک JSON کامل که شامل موارد زیر باشد:

1. **entry_conditions**: لیست شرایط ورود دقیق و قابل اجرا
2. **exit_conditions**: لیست شرایط خروج دقیق و قابل اجرا  
3. **indicators**: دیکشنری اندیکاتورها با پارامترهای دقیق (مثلاً: {{"rsi": {{"period": 14}}, "macd": {{"fast": 12, "slow": 26}}}})
4. **risk_management**: مدیریت ریسک کامل شامل stop_loss، take_profit، risk_per_trade
5. **timeframe**: تایم‌فریم معاملاتی (مثلاً: H1, M15, D1)
6. **symbol**: نماد معاملاتی (مثلاً: EURUSD, XAUUSD)
7. **executable_model**: مدل قابل اجرا که شامل منطق ورود و خروج باشد

**ساختار JSON:**
{{
    "entry_conditions": [
        "شرط 1 به صورت دقیق",
        "شرط 2 به صورت دقیق"
    ],
    "exit_conditions": [
        "شرط خروج 1",
        "شرط خروج 2"
    ],
    "indicators": {{
        "rsi": {{"period": 14, "overbought": 70, "oversold": 30}},
        "macd": {{"fast": 12, "slow": 26, "signal": 9}}
    }},
    "risk_management": {{
        "stop_loss": {{"type": "pips", "value": 50}},
        "take_profit": {{"type": "pips", "value": 100}},
        "risk_per_trade": 2
    }},
    "timeframe": "H1",
    "symbol": "EURUSD",
    "executable_model": {{
        "entry_logic": "منطق ورود قابل اجرا",
        "exit_logic": "منطق خروج قابل اجرا"
    }}
}}

فقط JSON برگردانید، بدون توضیحات اضافی."""
    
    try:
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/chat/completions"
        
        # آماده‌سازی payload
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "شما یک متخصص تبدیل استراتژی معاملاتی هستید. همیشه پاسخ را به صورت JSON معتبر برگردانید."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        # اضافه کردن response_format برای JSON
        if json_response:
            payload["response_format"] = {"type": "json_object"}
        
        # اضافه کردن پارامترهای اضافی از kwargs
        for key in ['top_p', 'frequency_penalty', 'presence_penalty', 'stop']:
            if key in kwargs:
                payload[key] = kwargs[key]
        
        # آماده‌سازی headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"[GapGPT] Calling API with model: {model}, prompt_length: {len(prompt)}")
        start_time = time.time()
        
        # ارسال درخواست
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # بررسی پاسخ
        if response.status_code == 200:
            data = response.json()
            
            # استخراج متن پاسخ
            choices = data.get('choices', [])
            if not choices:
                return {
                    'success': False,
                    'error': 'پاسخ نامعتبر از GapGPT API - no choices',
                    'converted_strategy': None,
                    'model_used': model,
                    'tokens_used': 0,
                    'latency_ms': latency_ms,
                    'raw_response': json.dumps(data)
                }
            
            message = choices[0].get('message', {})
            content = message.get('content', '')
            
            if not content:
                return {
                    'success': False,
                    'error': 'پاسخ خالی از GapGPT API',
                    'converted_strategy': None,
                    'model_used': model,
                    'tokens_used': 0,
                    'latency_ms': latency_ms,
                    'raw_response': json.dumps(data)
                }
            
            # استخراج اطلاعات استفاده
            usage = data.get('usage', {})
            tokens_used = usage.get('total_tokens', 0)
            
            # تلاش برای پارس کردن JSON
            converted_strategy = None
            try:
                # پاک کردن markdown code blocks اگر وجود داشته باشد
                cleaned_content = content.strip()
                if cleaned_content.startswith('```'):
                    # حذف ```json و ``` از ابتدا و انتها
                    lines = cleaned_content.split('\n')
                    if len(lines) > 1:
                        cleaned_content = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
                
                converted_strategy = json.loads(cleaned_content)
                logger.info(f"[GapGPT] Successfully parsed JSON response from model {model}")
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse GapGPT response as JSON: {e}")
                # اگر JSON نبود، متن خام را برمی‌گردانیم
                converted_strategy = content
            
            return {
                'success': True,
                'converted_strategy': converted_strategy,
                'model_used': model,
                'tokens_used': tokens_used,
                'latency_ms': latency_ms,
                'raw_response': content,
                'error': None
            }
        
        else:
            # خطای HTTP
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get('message', error_msg)
                    error_code = error_detail.get('code', '')
                    
                    # ترجمه خطاهای رایج
                    if error_code == 'model_not_found':
                        error_msg = f"مدل '{model}' در دسترس نیست. لطفاً مدل دیگری انتخاب کنید."
                    elif '分组' in error_msg or 'distributor' in error_msg.lower():
                        error_msg = f"مدل '{model}' در گروه فعلی در دسترس نیست. لطفاً مدل دیگری امتحان کنید."
                elif isinstance(error_detail, str):
                    error_msg = error_detail
            except:
                error_msg = response.text[:200] if response.text else error_msg
            
            logger.error(f"[GapGPT] API error: {response.status_code} - {error_msg}")
            
            # ترجمه خطاهای رایج
            if response.status_code == 401:
                error_msg = "کلید API GapGPT نامعتبر است. لطفاً کلید صحیح را وارد کنید."
            elif response.status_code == 429:
                error_msg = "محدودیت نرخ استفاده از GapGPT رسیده است. لطفاً چند لحظه صبر کنید."
            elif response.status_code == 503:
                if 'model' in error_msg.lower():
                    error_msg = f"مدل '{model}' موقتاً در دسترس نیست. لطفاً مدل دیگری انتخاب کنید."
                else:
                    error_msg = "سرویس GapGPT موقتاً در دسترس نیست. لطفاً دوباره تلاش کنید."
            
            return {
                'success': False,
                'error': error_msg,
                'converted_strategy': None,
                'model_used': model,
                'tokens_used': 0,
                'latency_ms': latency_ms,
                'status_code': response.status_code
            }
            
    except requests.exceptions.Timeout:
        logger.error(f"[GapGPT] Request timeout after {timeout}s")
        return {
            'success': False,
            'error': f'زمان اتصال به GapGPT API تمام شد ({timeout} ثانیه). لطفاً دوباره تلاش کنید.',
            'converted_strategy': None,
            'model_used': model,
            'tokens_used': 0
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[GapGPT] Connection error: {e}")
        return {
            'success': False,
            'error': 'خطا در اتصال به GapGPT API. لطفاً اتصال اینترنت خود را بررسی کنید.',
            'converted_strategy': None,
            'model_used': model,
            'tokens_used': 0
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"[GapGPT] Request error: {e}")
        return {
            'success': False,
            'error': f'خطا در ارسال درخواست به GapGPT API: {str(e)}',
            'converted_strategy': None,
            'model_used': model,
            'tokens_used': 0
        }
    except Exception as e:
        logger.error(f"[GapGPT] Unexpected error: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'خطای غیرمنتظره: {str(e)}',
            'converted_strategy': None,
            'model_used': model,
            'tokens_used': 0
        }


def analyze_strategy_with_multiple_models(
    strategy_text: str,
    models: List[str] = None,
    user=None,
    **kwargs
) -> Dict[str, Any]:
    """
    تبدیل استراتژی با چندین مدل مختلف و مقایسه نتایج برای پیدا کردن بهترین
    
    Args:
        strategy_text: متن استراتژی
        models: لیست مدل‌ها برای تست (اگر None باشد، از مدل‌های پیش‌فرض استفاده می‌شود)
        user: کاربر فعلی
        **kwargs: پارامترهای اضافی (temperature, max_tokens, etc.)
    
    Returns:
        Dict شامل:
        - all_results: نتایج تمام مدل‌ها
        - best_result: بهترین نتیجه بر اساس امتیاز
        - models_tested: لیست مدل‌های تست شده
        - summary: خلاصه نتایج
    """
    if models is None:
        available_models = get_available_models(user, filter_chat_models=True)
        # انتخاب 5 مدل محبوب
        popular_models = ['gpt-4o', 'gpt-5', 'gpt-4o-mini', 'claude-3-5-sonnet-20241022', 'gemini-1.5-pro']
        models = [m['id'] for m in available_models if m['id'] in popular_models]
        if len(models) < 3:  # اگر مدل‌های محبوب موجود نبودند، از 3 مدل اول استفاده کنیم
            models = [m['id'] for m in available_models[:3]]
    
    results = {}
    best_result = None
    best_score = -1
    successful_count = 0
    
    logger.info(f"[GapGPT] Analyzing strategy with {len(models)} models: {models}")
    
    for model_id in models:
        logger.info(f"[GapGPT] Testing model: {model_id}")
        
        result = convert_strategy_with_gapgpt(
            strategy_text=strategy_text,
            model_id=model_id,
            user=user,
            **kwargs
        )
        
        results[model_id] = result
        
        # محاسبه امتیاز برای مقایسه
        if result['success']:
            successful_count += 1
            score = _calculate_strategy_score(result['converted_strategy'])
            
            result['score'] = score
            
            if score > best_score:
                best_score = score
                best_result = {
                    'model_id': model_id,
                    'result': result,
                    'score': score
                }
        else:
            result['score'] = 0
    
    # آماده‌سازی خلاصه
    summary = {
        'total_models': len(models),
        'successful_models': successful_count,
        'failed_models': len(models) - successful_count,
        'best_model_id': best_result['model_id'] if best_result else None,
        'best_score': best_score,
    }
    
    return {
        'all_results': results,
        'best_result': best_result,
        'models_tested': list(models),
        'summary': summary
    }


def _calculate_strategy_score(strategy: Any) -> float:
    """
    محاسبه امتیاز کیفیت استراتژی تبدیل شده
    
    هر بخش کامل +1 امتیاز (حداکثر 7 امتیاز)
    """
    if not isinstance(strategy, dict):
        return 0.0
    
    score = 0.0
    
    # بررسی entry_conditions
    if strategy.get('entry_conditions'):
        if isinstance(strategy['entry_conditions'], list) and len(strategy['entry_conditions']) > 0:
            score += 1.0
    
    # بررسی exit_conditions
    if strategy.get('exit_conditions'):
        if isinstance(strategy['exit_conditions'], list) and len(strategy['exit_conditions']) > 0:
            score += 1.0
    
    # بررسی indicators
    if strategy.get('indicators'):
        if isinstance(strategy['indicators'], dict) and len(strategy['indicators']) > 0:
            score += 1.0
    
    # بررسی risk_management
    risk_mgmt = strategy.get('risk_management')
    if risk_mgmt:
        if isinstance(risk_mgmt, dict):
            if risk_mgmt.get('stop_loss'):
                score += 0.5
            if risk_mgmt.get('take_profit'):
                score += 0.5
    
    # بررسی timeframe
    if strategy.get('timeframe'):
        score += 0.5
    
    # بررسی symbol
    if strategy.get('symbol'):
        score += 0.5
    
    # بررسی executable_model
    if strategy.get('executable_model'):
        if isinstance(strategy['executable_model'], dict):
            if strategy['executable_model'].get('entry_logic'):
                score += 1.0
            if strategy['executable_model'].get('exit_logic'):
                score += 1.0
    
    return min(score, 7.0)  # حداکثر 7 امتیاز


def analyze_backtest_trades_with_gapgpt(
    backtest_results: Dict[str, Any],
    strategy: Dict[str, Any],
    symbol: str,
    data_provider: str = None,
    data_points: int = 0,
    date_range: str = None,
    user=None,
    model_id: str = None
) -> Dict[str, Any]:
    """
    تحلیل نتایج بک تست با استفاده از GapGPT
    
    Args:
        backtest_results: نتایج بک تست
        strategy: استراتژی معاملاتی
        symbol: نماد معاملاتی
        data_provider: ارائه‌دهنده داده
        data_points: تعداد نقاط داده
        date_range: بازه زمانی
        user: کاربر فعلی
        model_id: ID مدل GapGPT (اختیاری)
    
    Returns:
        Dict شامل:
        - ai_status: 'ok' یا 'error'
        - analysis_text: متن تحلیل
        - message: پیام نتیجه
        - raw_output: خروجی خام
    """
    api_key = get_gapgpt_api_key(user)
    if not api_key:
        return {
            'ai_status': 'error',
            'message': 'کلید API GapGPT تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید GapGPT را اضافه کنید.',
            'analysis_text': '',
            'raw_output': ''
        }
    
    # آماده‌سازی داده‌های تحلیل
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
        "indicators": strategy.get('indicators', {}),
        "symbol": symbol,
        "sample_trades": (backtest_results.get('trades') or [])[:10],
    }
    
    if data_provider:
        analysis_data["data_provider"] = data_provider
    if data_points > 0:
        analysis_data["data_points"] = data_points
    if date_range:
        analysis_data["date_range"] = date_range
    
    # ساخت prompt برای تحلیل
    system_prompt = """شما یک تحلیلگر حرفه‌ای استراتژی معاملاتی هستید. بر اساس نتایج بک تست که دریافت می‌کنید، یک تحلیل جامع به فارسی ارائه دهید که شامل موارد زیر باشد:
1. خلاصه کلی نتایج بک تست
2. نقاط قوت استراتژی (لیست)
3. نقاط ضعف استراتژی (لیست)
4. ارزیابی ریسک
5. پیشنهادات برای بهبود (لیست)
6. امتیاز کیفیت (0-100)

تحلیل باید دقیق، کاربردی و قابل فهم باشد."""
    
    user_prompt = f"""نتایج بک تست:
{json.dumps(analysis_data, ensure_ascii=False, indent=2)}

لطفاً تحلیل جامعی ارائه دهید."""
    
    try:
        model = model_id or GAPGPT_DEFAULT_MODEL
        endpoint = f"{GAPGPT_API_BASE_URL}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"[GapGPT] Analyzing backtest with model: {model}")
        start_time = time.time()
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=60
        )
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            choices = data.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                content = message.get('content', '')
                usage = data.get('usage', {})
                tokens_used = usage.get('total_tokens', 0)
                
                if content:
                    logger.info(f"[GapGPT] Backtest analysis completed: {tokens_used} tokens, {latency_ms:.0f}ms")
                    return {
                        'ai_status': 'ok',
                        'analysis_text': content,
                        'message': 'تحلیل با موفقیت انجام شد',
                        'raw_output': content,
                        'model_used': model,
                        'tokens_used': tokens_used,
                        'latency_ms': latency_ms
                    }
                else:
                    return {
                        'ai_status': 'error',
                        'message': 'پاسخ خالی از GapGPT API',
                        'analysis_text': '',
                        'raw_output': ''
                    }
            else:
                return {
                    'ai_status': 'error',
                    'message': 'پاسخ نامعتبر از GapGPT API',
                    'analysis_text': '',
                    'raw_output': ''
                }
        else:
            error_msg = f"HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_msg = error_detail.get('message', error_msg)
                elif isinstance(error_detail, str):
                    error_msg = error_detail
            except:
                error_msg = response.text[:200] if response.text else error_msg
            
            logger.error(f"[GapGPT] Backtest analysis error: {response.status_code} - {error_msg}")
            
            if response.status_code == 401:
                error_msg = "کلید API GapGPT نامعتبر است. لطفاً کلید صحیح را وارد کنید."
            elif response.status_code == 429:
                error_msg = "محدودیت نرخ استفاده از GapGPT رسیده است. لطفاً چند لحظه صبر کنید."
            
            return {
                'ai_status': 'error',
                'message': error_msg,
                'analysis_text': '',
                'raw_output': ''
            }
    
    except requests.exceptions.Timeout:
        logger.error(f"[GapGPT] Backtest analysis timeout")
        return {
            'ai_status': 'error',
            'message': 'زمان اتصال به GapGPT API تمام شد. لطفاً دوباره تلاش کنید.',
            'analysis_text': '',
            'raw_output': ''
        }
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[GapGPT] Backtest analysis connection error: {e}")
        return {
            'ai_status': 'error',
            'message': 'خطا در اتصال به GapGPT API. لطفاً اتصال اینترنت خود را بررسی کنید.',
            'analysis_text': '',
            'raw_output': ''
        }
    except Exception as e:
        logger.exception(f"[GapGPT] Unexpected error in backtest analysis: {e}")
        return {
            'ai_status': 'error',
            'message': f'خطای غیرمنتظره: {str(e)}',
            'analysis_text': '',
            'raw_output': ''
        }


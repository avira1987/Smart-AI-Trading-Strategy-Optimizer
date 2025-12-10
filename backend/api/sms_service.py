"""
SMS Service using Kavenegar API
"""
import logging
import os

logger = logging.getLogger(__name__)

# Try to import requests for direct REST API calls
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("Warning: requests module not found. Will try to use Kavenegar library methods only.")

# Try to import Kavenegar
try:
    from kavenegar import *
    SMS_ENABLED = True
except ImportError:
    SMS_ENABLED = False
    logger.warning("Warning: Kavenegar module not found. SMS notifications disabled.")

# Get API key from environment or APIConfiguration
def get_kavenegar_api_key():
    """Get Kavenegar API key from environment variable or APIConfiguration"""
    # First try environment variable
    api_key = os.environ.get('KAVENEGAR_API_KEY', '')
    if api_key and api_key.strip():
        return api_key.strip()
    
    # Then try APIConfiguration model
    try:
        from core.models import APIConfiguration
        api_config = APIConfiguration.objects.filter(
            provider='kavenegar',
            is_active=True,
            user__isnull=True,
        ).first()
        if api_config and api_config.api_key:
            api_key_value = api_config.api_key.strip()
            if api_key_value:
                return api_key_value
    except Exception as e:
        # Log debug message - might fail during migrations or if database not ready
        logger.debug(f"Could not get API key from database: {e}")
        pass
    
    return ''

# Get template name from environment
def get_kavenegar_template_name():
    """Get Kavenegar template name from environment variable"""
    template = os.environ.get('KAVENEGAR_TEMPLATE', 'codeToken')
    return template.strip() if template else 'codeToken'


def _send_lookup_via_rest(api_key: str, phone_number: str, template_name: str, token: str) -> dict:
    """
    Send Lookup SMS via direct REST API call
    
    Args:
        api_key: Kavenegar API key
        phone_number: Phone number
        template_name: Template name
        token: OTP token
        
    Returns:
        dict: Response from API
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests module is required for REST API calls")
    
    url = f'https://api.kavenegar.com/v1/{api_key}/verify/lookup.json'
    params = {
        'receptor': phone_number,
        'template': template_name,
        'token': token
    }
    
    response = requests.post(url, data=params, timeout=10)
    response.raise_for_status()
    return response.json()


def send_otp_sms(phone_number: str, otp_code: str, template_name: str = None) -> dict:
    """
    Send OTP code via SMS using Kavenegar Lookup method
    
    Args:
        phone_number: Phone number in format '09123456789' (without +)
        otp_code: OTP code to send
        template_name: Template name defined in Kavenegar panel (optional)
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not SMS_ENABLED:
        logger.error("SMS service is not enabled. Kavenegar module not installed.")
        return {
            'success': False,
            'message': 'سرویس پیامک فعال نیست'
        }
    
    # Get API key dynamically
    api_key = get_kavenegar_api_key()
    if not api_key:
        logger.error("Kavenegar API key is not configured")
        return {
            'success': False,
            'message': 'کلید API پیامک تنظیم نشده است. لطفا در تنظیمات API، کلید Kavenegar را وارد کنید.'
        }
    
    # Get template name from environment or use provided one
    if not template_name:
        template_name = get_kavenegar_template_name()
    
    try:
        # Log API key status (without showing the actual key)
        logger.info(f"Attempting to send OTP via Lookup to {phone_number} (template: {template_name})")
        
        # Initialize Kavenegar API
        api = KavenegarAPI(api_key)
        
        # Use Lookup method for verification SMS
        # Parameters: receptor, template, token
        params = {
            'receptor': phone_number,
            'template': template_name,
            'token': otp_code
        }
        
        logger.debug(f"Sending OTP via Lookup with params: receptor={phone_number}, template={template_name}")
        logger.info(f"📤 Lookup params: receptor={phone_number}, template={template_name}, token_length={len(otp_code)}")
        
        # Try to use verify_lookup method, fallback to direct REST API if not available
        try:
            # Check if verify_lookup method exists
            if hasattr(api, 'verify_lookup'):
                response = api.verify_lookup(params)
            else:
                # Fallback to direct REST API call
                logger.info("verify_lookup method not found, using direct REST API")
                response = _send_lookup_via_rest(api_key, phone_number, template_name, otp_code)
        except AttributeError:
            # If verify_lookup doesn't exist, use REST API
            logger.info("verify_lookup method not available, using direct REST API")
            response = _send_lookup_via_rest(api_key, phone_number, template_name, otp_code)
        
        logger.info(f"✅ OTP sent successfully via Lookup to {phone_number}")
        logger.debug(f"Lookup response: {response}")
        return {
            'success': True,
            'message': 'کد یکبار مصرف به شماره موبایل شما ارسال شد',
            'response': response
        }
        
    except Exception as e:
        import traceback
        error_str = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ Lookup SMS failed: {error_type} - {error_str}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Check for specific Kavenegar error codes
        error_lower = error_str.lower()
        
        # Check if error is about invalid API key
        if '401' in error_str or 'api' in error_lower and ('key' in error_lower or 'کلید' in error_str):
            return {
                'success': False,
                'message': 'کلید API نامعتبر است. لطفا کلید API خود را در تنظیمات بررسی کنید.'
            }
        
        # Check if error is about invalid template (404 or 424)
        if 'template' in error_lower or 'الگو' in error_str or '404' in error_str or '424' in error_str or '404' in str(e) or '424' in str(e):
            return {
                'success': False,
                'message': f'الگوی "{template_name}" در پنل کاوه نگار یافت نشد یا هنوز تأیید نشده است. لطفا:\n1. نام الگو را در پنل کاوه نگار بررسی کنید\n2. مطمئن شوید الگو تأیید شده است\n3. نام دقیق الگو را در متغیر KAVENEGAR_TEMPLATE تنظیم کنید'
            }
        
        # Check if error is about insufficient credit
        if '402' in error_str or 'credit' in error_lower or 'اعتبار' in error_str:
            return {
                'success': False,
                'message': 'اعتبار حساب Kavenegar شما کافی نیست. لطفا حساب خود را شارژ کنید.'
            }
        
        # Generic error
        return {
            'success': False,
            'message': f'خطا در ارسال پیامک: {error_str}',
            'error_type': error_type
        }


def send_sms(phone_number: str, message: str) -> dict:
    """
    Send custom SMS message
    
    Args:
        phone_number: Phone number in format '09123456789'
        message: Message text
        
    Returns:
        dict: {'success': bool, 'message': str}
    """
    if not SMS_ENABLED:
        logger.error("SMS service is not enabled.")
        return {
            'success': False,
            'message': 'سرویس پیامک فعال نیست'
        }
    
    # Get API key dynamically
    api_key = get_kavenegar_api_key()
    if not api_key:
        logger.error("Kavenegar API key is not configured")
        return {
            'success': False,
            'message': 'کلید API پیامک تنظیم نشده است. لطفا در تنظیمات API، کلید Kavenegar را وارد کنید.'
        }
    
    try:
        # Log API key status (without showing the actual key)
        logger.info(f"Attempting to send SMS to {phone_number} (API key configured: {'Yes' if api_key else 'No'})")
        
        api = KavenegarAPI(api_key)
        
        params = {
            'receptor': phone_number,
            'message': message
        }
        
        logger.debug(f"Sending SMS with params: {params}")
        logger.info(f"📤 SMS params (no sender): receptor={phone_number}, message_length={len(message)}")
        
        response = api.sms_send(params)
        
        logger.info(f"✅ SMS sent successfully to {phone_number}")
        logger.debug(f"SMS response: {response}")
        return {
            'success': True,
            'message': 'پیامک با موفقیت ارسال شد',
            'response': response
        }
        
    except Exception as e:
        import traceback
        error_str = str(e)
        error_type = type(e).__name__
        logger.error(f"❌ SMS failed: {error_type} - {error_str}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Check for specific Kavenegar error codes
        error_lower = error_str.lower()
        
        # Check if error is about invalid API key
        if '401' in error_str or 'api' in error_lower and ('key' in error_lower or 'کلید' in error_str):
            return {
                'success': False,
                'message': 'کلید API نامعتبر است. لطفا کلید API خود را در تنظیمات بررسی کنید.'
            }
        
        # Check if error is about invalid sender
        if '412' in error_str or 'ارسال کننده' in error_str or 'نامعتبر' in error_str or 'sender' in error_lower:
            return {
                'success': False,
                'message': 'شماره فرستنده نامعتبر است. لطفا در فایل .env متغیر KAVENEGAR_SENDER را با شماره معتبر خود تنظیم کنید یا آن را خالی بگذارید.'
            }
        
        # Check if error is about insufficient credit
        if '402' in error_str or 'credit' in error_lower or 'اعتبار' in error_str:
            return {
                'success': False,
                'message': 'اعتبار حساب Kavenegar شما کافی نیست. لطفا حساب خود را شارژ کنید.'
            }
        
        # Generic error
        return {
            'success': False,
            'message': f'خطا در ارسال پیامک: {error_str}',
            'error_type': error_type
        }


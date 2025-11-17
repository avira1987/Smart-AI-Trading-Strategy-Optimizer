"""
SMS Service using Kavenegar API
"""
import logging
import os

logger = logging.getLogger(__name__)

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

# Get sender number from environment (optional - if not set, will try without sender)
def get_kavenegar_sender():
    """Get Kavenegar sender number from environment"""
    sender = os.environ.get('KAVENEGAR_SENDER', '')
    return sender.strip() if sender else None


def send_otp_sms(phone_number: str, otp_code: str) -> dict:
    """
    Send OTP code via SMS using Kavenegar
    
    Args:
        phone_number: Phone number in format '09123456789' (without +)
        otp_code: OTP code to send
        
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
    
    try:
        # Log API key status (without showing the actual key)
        logger.info(f"Attempting to send SMS to {phone_number} (API key configured: {'Yes' if api_key else 'No'})")
        
        # Initialize Kavenegar API
        api = KavenegarAPI(api_key)
        
        # Format message
        message = f'{otp_code}. اعتبار این کد 5 دقیقه.'
        
        # Send SMS - only include sender if it's configured
        params = {
            'receptor': phone_number,
            'message': message
        }
        
        # Add sender only if configured
        sender = get_kavenegar_sender()
        if sender:
            params['sender'] = sender
            logger.debug(f"Using sender: {sender}")
        else:
            logger.debug("No sender configured, using default")
        
        logger.debug(f"Sending SMS with params: receptor={phone_number}, sender={'configured' if sender else 'default'}")
        
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
        
        # Add sender only if configured
        sender = get_kavenegar_sender()
        if sender:
            params['sender'] = sender
            logger.debug(f"Using sender: {sender}")
        else:
            logger.debug("No sender configured, using default")
        
        logger.debug(f"Sending SMS with params: receptor={phone_number}, sender={'configured' if sender else 'default'}")
        
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


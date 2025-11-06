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
    if api_key:
        return api_key
    
    # Then try APIConfiguration model
    try:
        from core.models import APIConfiguration
        api_config = APIConfiguration.objects.filter(provider='kavenegar', is_active=True).first()
        if api_config:
            return api_config.api_key
    except Exception:
        pass
    
    return ''

KAVENEGAR_API_KEY = get_kavenegar_api_key()

# Get sender number from environment (optional - if not set, will try without sender)
KAVENEGAR_SENDER = os.environ.get('KAVENEGAR_SENDER', None)


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
    
    try:
        # Initialize Kavenegar API
        api = KavenegarAPI(KAVENEGAR_API_KEY)
        
        # Format message
        message = f'کد ورود شما: {otp_code}\n\nاین کد تا 5 دقیقه معتبر است.'
        
        # Send SMS - only include sender if it's configured
        params = {
            'receptor': phone_number,
            'message': message
        }
        
        # Add sender only if configured
        if KAVENEGAR_SENDER:
            params['sender'] = KAVENEGAR_SENDER
        
        response = api.sms_send(params)
        
        logger.info(f"✅ SMS sent successfully to {phone_number}")
        return {
            'success': True,
            'message': 'پیامک با موفقیت ارسال شد',
            'response': response
        }
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"❌ SMS failed: {error_str}")
        
        # Check if error is about invalid sender
        if '412' in error_str or 'ارسال کننده' in error_str or 'نامعتبر' in error_str:
            return {
                'success': False,
                'message': 'شماره فرستنده نامعتبر است. لطفا در فایل .env متغیر KAVENEGAR_SENDER را با شماره معتبر خود تنظیم کنید.'
            }
        
        return {
            'success': False,
            'message': f'خطا در ارسال پیامک: {error_str}'
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
    
    try:
        api = KavenegarAPI(KAVENEGAR_API_KEY)
        
        params = {
            'receptor': phone_number,
            'message': message
        }
        
        # Add sender only if configured
        if KAVENEGAR_SENDER:
            params['sender'] = KAVENEGAR_SENDER
        
        response = api.sms_send(params)
        
        logger.info(f"✅ SMS sent successfully to {phone_number}")
        return {
            'success': True,
            'message': 'پیامک با موفقیت ارسال شد',
            'response': response
        }
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"❌ SMS failed: {error_str}")
        
        # Check if error is about invalid sender
        if '412' in error_str or 'ارسال کننده' in error_str or 'نامعتبر' in error_str:
            return {
                'success': False,
                'message': 'شماره فرستنده نامعتبر است. لطفا در فایل .env متغیر KAVENEGAR_SENDER را با شماره معتبر خود تنظیم کنید.'
            }
        
        return {
            'success': False,
            'message': f'خطا در ارسال پیامک: {error_str}'
        }


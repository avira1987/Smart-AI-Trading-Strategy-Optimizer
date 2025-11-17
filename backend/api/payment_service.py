"""
Payment service for Zarinpal integration
"""

import requests
import logging
import os
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Zarinpal API endpoints
ZARINPAL_SANDBOX_URL = "https://sandbox.zarinpal.com/pg/v4"
ZARINPAL_PRODUCTION_URL = "https://api.zarinpal.com/pg/v4"

ZARINPAL_REQUEST_URL = "/payment/request.json"
ZARINPAL_VERIFY_URL = "/payment/verify.json"
ZARINPAL_START_PAY_URL = "https://sandbox.zarinpal.com/pg/StartPay/"
ZARINPAL_START_PAY_PRODUCTION = "https://www.zarinpal.com/pg/StartPay/"


class ZarinpalPaymentService:
    """Service for handling Zarinpal payments"""
    
    def __init__(self):
        # Don't cache merchant_id - read from DB each time to get latest value
        self.sandbox_mode = getattr(settings, 'ZARINPAL_SANDBOX', True)
        self.base_url = ZARINPAL_SANDBOX_URL if self.sandbox_mode else ZARINPAL_PRODUCTION_URL
        self.start_pay_url = ZARINPAL_START_PAY_URL if self.sandbox_mode else ZARINPAL_START_PAY_PRODUCTION
    
    def _get_merchant_id(self) -> str:
        """Get Zarinpal Merchant ID from database or settings (always fresh)"""
        # First try environment variable
        merchant_id = os.environ.get('ZARINPAL_MERCHANT_ID', '')
        if merchant_id:
            return merchant_id
        
        # Then try APIConfiguration model (always read fresh from DB)
        try:
            from core.models import APIConfiguration
            api_config = APIConfiguration.objects.filter(
                provider='zarinpal',
                is_active=True,
                user__isnull=True,
            ).first()
            if api_config and api_config.api_key:
                return api_config.api_key.strip()
        except Exception as e:
            logger.warning(f"Error getting Zarinpal Merchant ID from database: {e}")
        
        # Fallback to settings (may be outdated)
        return getattr(settings, 'ZARINPAL_MERCHANT_ID', '')
    
    def create_payment_request(
        self,
        amount: int,
        description: str,
        callback_url: str,
        email: str = None,
        mobile: str = None
    ) -> Dict[str, Any]:
        """
        Create a payment request in Zarinpal
        
        Args:
            amount: Amount in Toman (will be converted to Rials for Zarinpal API)
            description: Payment description
            callback_url: URL to redirect after payment
            email: User email (optional)
            mobile: User mobile (optional)
            
        Returns:
            Dict with 'status', 'authority', 'start_pay_url' or 'error'
        """
        merchant_id = self._get_merchant_id()
        if not merchant_id:
            logger.error("Zarinpal merchant ID not configured")
            return {
                'status': 'error',
                'error': 'زرین‌پال تنظیم نشده است. لطفاً Merchant ID را در بخش تنظیمات API اضافه کنید.'
            }
        
        # Convert Toman to Rial (1 Toman = 10 Rials)
        # Handle both int and float/Decimal types
        amount_in_rials = int(float(amount) * 10)
        
        url = f"{self.base_url}{ZARINPAL_REQUEST_URL}"
        
        payload = {
            "merchant_id": merchant_id,
            "amount": amount_in_rials,
            "description": description,
            "callback_url": callback_url,
        }
        
        if email:
            payload["email"] = email
        if mobile:
            payload["mobile"] = mobile
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and data['data'].get('code') == 100:
                authority = data['data']['authority']
                start_pay_url = f"{self.start_pay_url}{authority}"
                
                logger.info(f"Payment request created: authority={authority}, amount={amount} Toman ({amount_in_rials} Rials)")
                
                return {
                    'status': 'success',
                    'authority': authority,
                    'start_pay_url': start_pay_url
                }
            else:
                # Handle different error codes from Zarinpal API v4
                error_code = data.get('data', {}).get('code', 0)
                error_message = self._get_error_message(error_code)
                if not error_message:
                    error_message = data.get('errors', {}).get('message', 'خطا در ایجاد درخواست پرداخت')
                logger.error(f"Zarinpal payment request failed: code={error_code}, message={error_message}")
                return {
                    'status': 'error',
                    'error': error_message,
                    'error_code': error_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Zarinpal API request failed: {str(e)}")
            return {
                'status': 'error',
                'error': f'خطا در ارتباط با زرین‌پال: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error in payment request: {str(e)}")
            return {
                'status': 'error',
                'error': f'خطای غیرمنتظره: {str(e)}'
            }
    
    def verify_payment(self, authority: str, amount: int) -> Dict[str, Any]:
        """
        Verify a payment with Zarinpal
        
        Args:
            authority: Payment authority from callback
            amount: Original amount in Toman (will be converted to Rials for Zarinpal API)
            
        Returns:
            Dict with 'status', 'ref_id' or 'error'
        """
        merchant_id = self._get_merchant_id()
        if not merchant_id:
            logger.error("Zarinpal merchant ID not configured")
            return {
                'status': 'error',
                'error': 'زرین‌پال تنظیم نشده است. لطفاً Merchant ID را در بخش تنظیمات API اضافه کنید.'
            }
        
        # Convert Toman to Rial (1 Toman = 10 Rials)
        # Handle both int and float/Decimal types
        amount_in_rials = int(float(amount) * 10)
        
        url = f"{self.base_url}{ZARINPAL_VERIFY_URL}"
        
        payload = {
            "merchant_id": merchant_id,
            "amount": amount_in_rials,
            "authority": authority
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data') and data['data'].get('code') == 100:
                ref_id = data['data']['ref_id']
                
                logger.info(f"Payment verified: authority={authority}, ref_id={ref_id}, amount={amount} Toman ({amount_in_rials} Rials)")
                
                return {
                    'status': 'success',
                    'ref_id': str(ref_id)
                }
            else:
                error_code = data.get('data', {}).get('code', 'unknown')
                error_message = self._get_error_message(error_code)
                logger.error(f"Zarinpal payment verification failed: code={error_code}")
                return {
                    'status': 'error',
                    'error': error_message,
                    'error_code': error_code
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Zarinpal verification request failed: {str(e)}")
            return {
                'status': 'error',
                'error': f'خطا در ارتباط با زرین‌پال: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error in payment verification: {str(e)}")
            return {
                'status': 'error',
                'error': f'خطای غیرمنتظره: {str(e)}'
            }
    
    def _get_error_message(self, error_code: int) -> str:
        """Get Persian error message for Zarinpal error codes"""
        error_messages = {
            -9: 'خطای اعتبارسنجی',
            -10: 'IP یا مرچنت کد صحیح نیست',
            -11: 'مرچنت کد فعال نیست',
            -12: 'تلاش بیش از حد در یک بازه زمانی کوتاه',
            -15: 'ترمینال شما به حالت تعلیق در آمده است',
            -16: 'سطح تایید پذیرنده پایین‌تر از سطح نقره‌ای است',
            -30: 'اجازه دسترسی به تسویه اشتراکی شناور ندارید',
            -31: 'حساب بانکی تسویه را به پنل اضافه کنید',
            -32: 'مبلغ از حد مجاز حساب شما بیشتر است',
            -33: 'مبلغ از حد مجاز سطح شما بیشتر است',
            -34: 'مبلغ از حد مجاز تراکنش بیشتر است',
            -35: 'تعداد تراکنش‌ها از حد مجاز بیشتر است',
            -40: 'پارامترهای ارسال شده صحیح نیست',
            -50: 'مبلغ پرداخت شده با مبلغ وریفای شده مطابقت ندارد',
            -51: 'پرداخت ناموفق',
            -52: 'خطای غیرمنتظره',
            -53: 'اتوریتی نامعتبر',
            -54: 'اتوریتی منقضی شده است',
        }
        return error_messages.get(error_code, f'خطای نامشخص (کد: {error_code})')


# Singleton instance
_zarinpal_service = None

def get_zarinpal_service() -> ZarinpalPaymentService:
    """Get Zarinpal service instance (always returns fresh instance to get latest Merchant ID)"""
    global _zarinpal_service
    # Always create new instance to ensure we get latest Merchant ID from DB
    # This is lightweight since we're not caching merchant_id anymore
    _zarinpal_service = ZarinpalPaymentService()
    return _zarinpal_service


"""
Self-managed CAPTCHA system
Lightweight, no external dependencies
"""
import secrets
import hashlib
import time
import json
import logging
from typing import Dict, Optional, Tuple
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# CAPTCHA settings
CAPTCHA_EXPIRY = 300  # 5 minutes
CAPTCHA_CACHE_PREFIX = 'captcha:'
CAPTCHA_MIN_TIME = 0.5  # Minimum seconds between page load and submit (reduced for better UX)
CAPTCHA_MAX_TIME = 600  # Maximum seconds (10 minutes)


def generate_math_challenge() -> Tuple[str, int]:
    """
    Generate a simple math challenge with only numbers (no operators visible)
    
    Returns:
        Tuple of (question_string, answer)
    """
    import random
    
    # Very simple addition only (1-10 range for easier calculation)
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    answer = num1 + num2
    
    # Display only the numbers, user needs to add them
    # Format: "عدد اول + عدد دوم" or just show numbers
    question = f"{num1} + {num2}"
    
    return question, answer


def generate_captcha_token(action: str = 'default') -> Dict[str, str]:
    """
    Generate a CAPTCHA challenge token
    
    Args:
        action: Action name (e.g., 'login', 'send_otp')
        
    Returns:
        Dict with 'token' and 'challenge' (math question)
    """
    # Generate unique token
    token = secrets.token_urlsafe(32)
    
    # Generate math challenge
    question, answer = generate_math_challenge()
    
    # Store answer in cache with token
    cache_key = f"{CAPTCHA_CACHE_PREFIX}{token}"
    cache.set(cache_key, {
        'answer': answer,
        'action': action,
        'created_at': time.time()
    }, CAPTCHA_EXPIRY)
    
    return {
        'token': token,
        'challenge': question,
        'type': 'math'
    }


def verify_captcha(
    token: str,
    answer: Optional[int] = None,
    page_load_time: Optional[float] = None,
    honeypot: Optional[str] = None
) -> Dict[str, any]:
    """
    Verify CAPTCHA response
    
    Args:
        token: CAPTCHA token from frontend
        answer: User's answer to math challenge
        page_load_time: Timestamp when page was loaded (for time-based check)
        honeypot: Honeypot field value (should be empty)
        
    Returns:
        Dict with 'success' (bool) and 'message' (str)
    """
    if not token:
        return {
            'success': False,
            'message': 'CAPTCHA token missing',
            'error': 'missing_token'
        }
    
    # Get stored challenge from cache
    cache_key = f"{CAPTCHA_CACHE_PREFIX}{token}"
    stored_data = cache.get(cache_key)
    
    if not stored_data:
        logger.warning(f"CAPTCHA token not found or expired: {token[:20]}")
        return {
            'success': False,
            'message': 'CAPTCHA منقضی شده است. لطفا صفحه را رفرش کنید.',
            'error': 'expired_token'
        }
    
    # Check honeypot (should be empty)
    if honeypot and honeypot.strip():
        logger.warning(f"Honeypot field filled - likely bot: {token[:20]}")
        cache.delete(cache_key)  # Delete token to prevent reuse
        return {
            'success': False,
            'message': 'درخواست نامعتبر',
            'error': 'honeypot_triggered'
        }
    
    # Check time-based validation
    # Skip time validation if page_load_time is not provided (allows for first-time page loads)
    if page_load_time and page_load_time > 0:
        elapsed_time = time.time() - page_load_time
        
        # Too fast (likely bot) - but allow if it's a reasonable time (at least 0.5 seconds)
        # This prevents accidental fast submissions while allowing normal use
        if elapsed_time < CAPTCHA_MIN_TIME and elapsed_time > 0:
            # Only block if it's suspiciously fast (less than 0.5 seconds)
            # This allows for quick but legitimate submissions
            logger.warning(f"Form submitted too quickly: {elapsed_time:.2f}s")
            cache.delete(cache_key)
            return {
                'success': False,
                'message': 'درخواست شما خیلی سریع ارسال شد. لطفا چند ثانیه صبر کنید و دوباره تلاش کنید.',
                'error': 'too_fast'
            }
        
        # Too slow (expired)
        if elapsed_time > CAPTCHA_MAX_TIME:
            logger.warning(f"Form submitted too slowly: {elapsed_time:.2f}s")
            cache.delete(cache_key)
            return {
                'success': False,
                'message': 'زمان شما به پایان رسیده است. لطفا صفحه را رفرش کنید.',
                'error': 'too_slow'
            }
    
    # Verify math answer
    if answer is None:
        cache.delete(cache_key)
        return {
            'success': False,
            'message': 'پاسخ CAPTCHA ارسال نشده است',
            'error': 'missing_answer'
        }
    
    correct_answer = stored_data.get('answer')
    
    if int(answer) != correct_answer:
        logger.warning(f"Wrong CAPTCHA answer: {answer} != {correct_answer}")
        cache.delete(cache_key)  # Delete token to prevent brute force
        return {
            'success': False,
            'message': 'پاسخ CAPTCHA اشتباه است',
            'error': 'wrong_answer'
        }
    
    # Success - delete token to prevent reuse
    cache.delete(cache_key)
    
    logger.debug(f"CAPTCHA verified successfully for action: {stored_data.get('action')}")
    
    return {
        'success': True,
        'message': 'CAPTCHA verified',
        'action': stored_data.get('action')
    }


def get_client_ip(request) -> str:
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


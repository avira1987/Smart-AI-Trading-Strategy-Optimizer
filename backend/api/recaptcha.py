"""
reCAPTCHA v3 verification utility
Lightweight implementation for bot protection
"""
import requests
import logging
from django.conf import settings
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def verify_recaptcha(token: str, remote_ip: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify reCAPTCHA v3 token with Google's API
    
    Args:
        token: reCAPTCHA token from frontend
        remote_ip: Optional client IP address
        
    Returns:
        Dict with 'success' (bool) and 'score' (float, 0.0-1.0) and 'action' (str)
    """
    recaptcha_secret_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', '')
    
    if not recaptcha_secret_key:
        logger.warning("RECAPTCHA_SECRET_KEY not configured, skipping verification")
        return {
            'success': True,  # Allow in development if not configured
            'score': 1.0,
            'action': 'unknown',
            'message': 'reCAPTCHA not configured'
        }
    
    if not token:
        return {
            'success': False,
            'score': 0.0,
            'action': 'unknown',
            'message': 'reCAPTCHA token missing'
        }
    
    try:
        # Verify with Google reCAPTCHA API
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        data = {
            'secret': recaptcha_secret_key,
            'response': token,
        }
        
        if remote_ip:
            data['remoteip'] = remote_ip
        
        response = requests.post(verify_url, data=data, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        success = result.get('success', False)
        score = result.get('score', 0.0)  # 0.0 (bot) to 1.0 (human)
        action = result.get('action', 'unknown')
        
        if not success:
            error_codes = result.get('error-codes', [])
            logger.warning(f"reCAPTCHA verification failed: {error_codes}")
            return {
                'success': False,
                'score': 0.0,
                'action': action,
                'error_codes': error_codes,
                'message': f'reCAPTCHA verification failed: {error_codes}'
            }
        
        logger.debug(f"reCAPTCHA verified: score={score}, action={action}")
        
        return {
            'success': True,
            'score': score,
            'action': action,
            'challenge_ts': result.get('challenge_ts'),
            'hostname': result.get('hostname')
        }
        
    except requests.RequestException as e:
        logger.error(f"Error verifying reCAPTCHA: {e}")
        # In case of network error, allow the request but log it
        return {
            'success': True,  # Fail open for network errors
            'score': 0.5,  # Medium score
            'action': 'unknown',
            'message': f'Network error: {str(e)}'
        }
    except Exception as e:
        logger.error(f"Unexpected error verifying reCAPTCHA: {e}")
        return {
            'success': False,
            'score': 0.0,
            'action': 'unknown',
            'message': f'Unexpected error: {str(e)}'
        }


def is_human(score: float, threshold: float = 0.5) -> bool:
    """
    Check if the score indicates a human user
    
    Args:
        score: reCAPTCHA score (0.0 to 1.0)
        threshold: Minimum score to consider human (default 0.5)
        
    Returns:
        True if score >= threshold
    """
    return score >= threshold


def get_client_ip(request) -> str:
    """
    Get client IP address from request
    
    Args:
        request: Django request object
        
    Returns:
        Client IP address as string
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


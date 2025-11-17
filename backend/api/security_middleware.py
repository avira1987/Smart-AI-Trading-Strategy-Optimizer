"""
Security middleware for bot detection and protection
"""
import re
import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from typing import Optional

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware to detect and block suspicious requests
    """
    
    # Suspicious user agents (common bot patterns)
    SUSPICIOUS_USER_AGENTS = [
        r'bot', r'crawler', r'spider', r'scraper',
        r'curl', r'wget', r'python-requests',
        r'postman', r'insomnia', r'httpie',
        r'^$',  # Empty user agent
    ]
    
    # Suspicious patterns in headers
    SUSPICIOUS_HEADER_PATTERNS = [
        (r'HTTP_X_FORWARDED_FOR', r'^[\d\.]+$'),  # Only IP, no other info
    ]
    
    # Paths that need extra security
    PROTECTED_PATHS = [
        '/api/auth/',
        '/api/demo/',
        '/api/gold-price/',
    ]
    
    def process_request(self, request):
        """Check for suspicious activity"""
        path = request.path
        
        # Only check protected paths
        if not any(path.startswith(protected) for protected in self.PROTECTED_PATHS):
            return None
        
        # Check user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Block suspicious user agents
        for pattern in self.SUSPICIOUS_USER_AGENTS:
            if re.search(pattern, user_agent, re.IGNORECASE):
                logger.warning(f"Suspicious user agent blocked: {user_agent} from {self._get_client_ip(request)}")
                return JsonResponse(
                    {
                        'success': False,
                        'message': 'درخواست نامعتبر',
                        'error': 'suspicious_request'
                    },
                    status=403
                )
        
        # Check for missing or suspicious headers
        if not user_agent:
            logger.warning(f"Request with no user agent from {self._get_client_ip(request)}")
            return JsonResponse(
                {
                    'success': False,
                    'message': 'درخواست نامعتبر',
                    'error': 'invalid_request'
                },
                status=403
            )
        
        # Check referer for API requests (optional, can be disabled for mobile apps)
        # This is commented out as it might block legitimate requests
        # referer = request.META.get('HTTP_REFERER', '')
        # if referer and not any(allowed in referer for allowed in ['localhost', '127.0.0.1', 'yourdomain.com']):
        #     logger.warning(f"Suspicious referer: {referer}")
        #     return JsonResponse({'success': False, 'message': 'Invalid request'}, status=403)
        
        return None
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def process_response(self, request, response):
        """Add security headers to response"""
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Only add CSP in production
        # response['Content-Security-Policy'] = "default-src 'self'"
        
        return response


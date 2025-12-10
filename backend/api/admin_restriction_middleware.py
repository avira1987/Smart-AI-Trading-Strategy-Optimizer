"""
Middleware to restrict Django admin access to localhost only
"""
import logging
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class AdminRestrictionMiddleware(MiddlewareMixin):
    """
    Middleware to restrict Django admin panel access to localhost only.
    This prevents access to Django admin from the internet.
    """
    
    def process_request(self, request):
        """Check if request is to Django admin and restrict to localhost"""
        path = request.path
        
        # Only check Django admin paths (not API admin endpoints)
        if path.startswith('/admin/') and not path.startswith('/admin/users') and not path.startswith('/admin/security') and not path.startswith('/admin/settings'):
            # Get client IP address
            client_ip = self._get_client_ip(request)
            
            # Check if request is from localhost
            if client_ip not in ['127.0.0.1', 'localhost', '::1']:
                # Check if Host header is localhost (nginx might set this)
                host = request.META.get('HTTP_HOST', '').lower()
                if 'localhost' not in host and '127.0.0.1' not in host:
                    logger.warning(
                        f"Django admin access blocked from {client_ip} (Host: {host}) for path: {path}"
                    )
                    return HttpResponseForbidden(
                        "<h1>403 Forbidden</h1>"
                        "<p>Django admin panel is only accessible from localhost.</p>"
                        "<p>Please access it directly from the server.</p>"
                    )
        
        return None
    
    def _get_client_ip(self, request):
        """Get the real client IP address"""
        # Check X-Real-IP header (set by nginx)
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        
        # Check X-Forwarded-For header
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            ip = x_forwarded_for.split(',')[0].strip()
            return ip
        
        # Fallback to REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', 'unknown')


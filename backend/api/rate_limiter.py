"""
Rate limiting middleware for bot protection
Lightweight in-memory rate limiting (can be upgraded to Redis later)
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, consider using Redis-based rate limiting
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}  # IP -> unblock time
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
    
    def is_allowed(
        self, 
        identifier: str, 
        max_requests: int = 10, 
        window_seconds: int = 60,
        block_duration: int = 300
    ) -> Tuple[bool, str]:
        """
        Check if request is allowed
        
        Args:
            identifier: Unique identifier (IP address, user ID, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            block_duration: How long to block after exceeding limit (seconds)
            
        Returns:
            Tuple of (is_allowed, message)
        """
        current_time = time.time()
        
        # Cleanup old entries periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup(current_time)
            self.last_cleanup = current_time
        
        # Check if IP is blocked
        if identifier in self.blocked_ips:
            unblock_time = self.blocked_ips[identifier]
            if current_time < unblock_time:
                remaining = int(unblock_time - current_time)
                return False, f"Too many requests. Please try again in {remaining} seconds."
            else:
                # Unblock expired IP
                del self.blocked_ips[identifier]
        
        # Get request history for this identifier
        request_times = self.requests[identifier]
        
        # Remove old requests outside the window
        cutoff_time = current_time - window_seconds
        request_times[:] = [t for t in request_times if t > cutoff_time]
        
        # Check if limit exceeded
        if len(request_times) >= max_requests:
            # Block the IP
            self.blocked_ips[identifier] = current_time + block_duration
            logger.warning(f"Rate limit exceeded for {identifier}. Blocked for {block_duration} seconds.")
            return False, f"Too many requests. Please try again in {block_duration} seconds."
        
        # Add current request
        request_times.append(current_time)
        
        return True, "OK"
    
    def _cleanup(self, current_time: float):
        """Remove old entries to prevent memory leaks"""
        # Remove expired blocks
        expired_ips = [
            ip for ip, unblock_time in self.blocked_ips.items()
            if current_time >= unblock_time
        ]
        for ip in expired_ips:
            del self.blocked_ips[ip]
        
        # Remove old request histories (older than 1 hour)
        cutoff = current_time - 3600
        for identifier in list(self.requests.keys()):
            self.requests[identifier] = [
                t for t in self.requests[identifier] if t > cutoff
            ]
            # Remove empty histories
            if not self.requests[identifier]:
                del self.requests[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(MiddlewareMixin):
    """
    Middleware to rate limit requests based on IP address
    """
    
    # Endpoints that should be rate limited
    RATE_LIMITED_PATHS = [
        '/api/auth/send-otp/',
        '/api/auth/verify-otp/',
        '/api/auth/google/',
        '/api/gold-price/',
        '/api/demo/trades/',
    ]
    
    # Different limits for different endpoints
    RATE_LIMITS = {
        '/api/auth/send-otp/': (5, 300),  # 5 requests per 5 minutes
        '/api/auth/verify-otp/': (10, 60),  # 10 requests per minute
        '/api/auth/google/': (5, 60),  # 5 requests per minute
        '/api/gold-price/': (30, 60),  # 30 requests per minute
        '/api/demo/trades/': (20, 60),  # 20 requests per minute
    }
    
    def process_request(self, request):
        """Check rate limit before processing request"""
        path = request.path
        
        # Check if this path should be rate limited
        if not any(path.startswith(limited_path) for limited_path in self.RATE_LIMITED_PATHS):
            return None
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        # Get rate limit settings for this path
        max_requests, window_seconds = (10, 60)  # Default
        for limited_path, limits in self.RATE_LIMITS.items():
            if path.startswith(limited_path):
                max_requests, window_seconds = limits
                break
        
        # Check rate limit
        is_allowed, message = rate_limiter.is_allowed(
            identifier=ip,
            max_requests=max_requests,
            window_seconds=window_seconds,
            block_duration=300  # Block for 5 minutes
        )
        
        if not is_allowed:
            logger.warning(f"Rate limit exceeded for IP {ip} on path {path}")
            return JsonResponse(
                {
                    'success': False,
                    'message': message,
                    'error': 'rate_limit_exceeded'
                },
                status=429  # Too Many Requests
            )
        
        return None


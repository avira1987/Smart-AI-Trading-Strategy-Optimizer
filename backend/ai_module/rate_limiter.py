"""
Global rate limiter for OpenAI API calls with TPM (Tokens Per Minute) tracking.
Implements queue for simultaneous requests and exponential backoff after 429 errors.
"""

import time
import logging
import threading
from collections import deque
from typing import Optional, Callable, Any
from queue import Queue, Empty
from django.conf import settings

logger = logging.getLogger("ai.rate_limiter")


class RateLimiter:
    """
    Global rate limiter that tracks tokens per minute (TPM) and manages request queue.
    """
    
    def __init__(self, max_tpm: int = None):
        self.max_tpm = max_tpm or getattr(settings, 'AI_MAX_TPM', 70000)
        self._lock = threading.Lock()
        self._token_usage: deque = deque()  # List of (timestamp, tokens) tuples
        self._request_queue: Queue = Queue()
        self._processing = False
        self._last_429_time: float = 0
        self._backoff_base: float = 3.0  # Base backoff time in seconds
        
    def _clean_old_tokens(self, now: float):
        """Remove token usage records older than 60 seconds."""
        while self._token_usage and now - self._token_usage[0][0] > 60:
            self._token_usage.popleft()
    
    def _get_current_tpm(self) -> int:
        """Calculate current tokens used in the last minute."""
        now = time.time()
        with self._lock:
            self._clean_old_tokens(now)
            return sum(tokens for _, tokens in self._token_usage)
    
    def _wait_for_capacity(self, required_tokens: int, timeout: float = 300) -> bool:
        """
        Wait until there's capacity for the required tokens.
        Returns True if capacity is available, False if timeout.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_tpm = self._get_current_tpm()
            if current_tpm + required_tokens <= self.max_tpm:
                return True
            # Wait a bit before checking again
            time.sleep(0.5)
        return False
    
    def _apply_429_backoff(self):
        """Apply exponential backoff after 429 error."""
        now = time.time()
        time_since_last_429 = now - self._last_429_time
        
        # If last 429 was less than 60 seconds ago, apply backoff
        if time_since_last_429 < 60:
            backoff_time = self._backoff_base * (2 ** min(3, int(time_since_last_429 / 10)))
            logger.warning(f"Applying {backoff_time:.1f}s backoff after 429 error")
            time.sleep(backoff_time)
        
        self._last_429_time = time.time()
    
    def record_tokens(self, tokens: int):
        """Record token usage for TPM tracking."""
        now = time.time()
        with self._lock:
            self._token_usage.append((now, tokens))
            self._clean_old_tokens(now)
    
    def acquire(self, estimated_tokens: int, timeout: float = 300) -> bool:
        """
        Acquire permission to make a request with estimated token usage.
        Returns True if permission granted, False if timeout.
        """
        # Check if we need to wait for capacity
        if not self._wait_for_capacity(estimated_tokens, timeout):
            logger.warning(f"Rate limit timeout: cannot acquire capacity for {estimated_tokens} tokens")
            return False
        
        # Check if we need to apply 429 backoff
        if self._last_429_time > 0:
            time_since_last_429 = time.time() - self._last_429_time
            if time_since_last_429 < 60:
                self._apply_429_backoff()
        
        return True
    
    def handle_429_error(self):
        """Handle 429 rate limit error by applying backoff."""
        self._apply_429_backoff()
    
    def get_current_usage(self) -> dict:
        """Get current rate limit usage statistics."""
        current_tpm = self._get_current_tpm()
        return {
            'current_tpm': current_tpm,
            'max_tpm': self.max_tpm,
            'available_tpm': max(0, self.max_tpm - current_tpm),
            'usage_percent': (current_tpm / self.max_tpm * 100) if self.max_tpm > 0 else 0
        }


# Global rate limiter instance
_global_rate_limiter: Optional[RateLimiter] = None
_limiter_lock = threading.Lock()


def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        with _limiter_lock:
            if _global_rate_limiter is None:
                max_tpm = getattr(settings, 'AI_MAX_TPM', 70000)
                _global_rate_limiter = RateLimiter(max_tpm=max_tpm)
                logger.info(f"Initialized global rate limiter with max_tpm={max_tpm}")
    return _global_rate_limiter


def rate_limit_wrapper(func: Callable) -> Callable:
    """
    Decorator to wrap OpenAI API calls with rate limiting.
    """
    def wrapper(*args, **kwargs):
        limiter = get_rate_limiter()
        
        # Estimate tokens (rough approximation: 4 chars = 1 token)
        prompt = kwargs.get('prompt', '') or (args[0] if args else '')
        estimated_tokens = len(str(prompt)) // 4 + 100  # Add buffer for response
        
        # Acquire permission
        if not limiter.acquire(estimated_tokens):
            raise Exception("Rate limit: Cannot acquire capacity for request")
        
        try:
            result = func(*args, **kwargs)
            
            # Record actual token usage if available
            if hasattr(result, 'tokens_used') and result.tokens_used:
                limiter.record_tokens(result.tokens_used)
            elif isinstance(result, dict) and 'tokens_used' in result:
                limiter.record_tokens(result['tokens_used'])
            
            return result
        except Exception as e:
            # Handle 429 errors
            error_str = str(e)
            if '429' in error_str or 'rate limit' in error_str.lower():
                limiter.handle_429_error()
            raise
    
    return wrapper


"""
Token usage monitoring for AI API calls.
Tracks tokens sent, received, and total per request.
"""

import logging
import time
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger("ai.token_monitor")


class TokenMonitor:
    """
    Monitors token usage for AI API calls.
    """
    
    def __init__(self):
        self.max_tpm = getattr(settings, 'AI_MAX_TPM', 70000)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count from text (rough approximation: 4 chars = 1 token).
        """
        return len(text) // 4
    
    def log_request(
        self,
        prompt: str,
        response_text: str = "",
        tokens_used: Optional[int] = None,
        provider: str = "unknown",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Log token usage for a request.
        Returns token usage information.
        """
        input_tokens = self.estimate_tokens(prompt)
        output_tokens = self.estimate_tokens(response_text) if response_text else 0
        
        # Use actual tokens if provided, otherwise use estimates
        if tokens_used is not None:
            total_tokens = tokens_used
            # If we have actual tokens, try to split input/output
            # Most APIs return total, so we estimate split
            if output_tokens == 0:
                output_tokens = max(0, total_tokens - input_tokens)
        else:
            total_tokens = input_tokens + output_tokens
        
        usage_info = {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': total_tokens,
            'provider': provider,
            'timestamp': time.time(),
            'user_id': user_id
        }
        
        # Log token usage
        logger.info(
            f"[TOKEN_MONITOR] Request tokens - "
            f"provider={provider}, "
            f"input={input_tokens}, "
            f"output={output_tokens}, "
            f"total={total_tokens}, "
            f"user_id={user_id}"
        )
        
        return usage_info
    
    def check_tpm_limit(self, estimated_tokens: int, current_tpm: int = None) -> tuple[bool, Optional[float]]:
        """
        Check if request would exceed TPM limit.
        Returns (can_proceed, delay_seconds).
        """
        if current_tpm is None:
            # We can't check without current TPM, so we'll assume it's okay
            # The rate limiter will handle the actual checking
            return True, None
        
        if current_tpm + estimated_tokens > self.max_tpm:
            # Calculate delay needed
            # Estimate that tokens will free up at rate of max_tpm per minute
            excess_tokens = (current_tpm + estimated_tokens) - self.max_tpm
            delay_seconds = (excess_tokens / self.max_tpm) * 60
            delay_seconds = min(delay_seconds, 300)  # Cap at 5 minutes
            
            logger.warning(
                f"[TOKEN_MONITOR] TPM limit would be exceeded. "
                f"Current: {current_tpm}, Required: {estimated_tokens}, "
                f"Max: {self.max_tpm}, Delay needed: {delay_seconds:.1f}s"
            )
            return False, delay_seconds
        
        return True, None


# Global token monitor instance
_global_token_monitor: Optional[TokenMonitor] = None


def get_token_monitor() -> TokenMonitor:
    """Get or create the global token monitor instance."""
    global _global_token_monitor
    if _global_token_monitor is None:
        _global_token_monitor = TokenMonitor()
    return _global_token_monitor


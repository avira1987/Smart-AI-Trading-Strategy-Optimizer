"""
ماژول ردیابی استفاده از API و محاسبه هزینه
"""
import time
from decimal import Decimal
from typing import Optional, Dict, Any
from django.utils import timezone
from django.db.models import Sum
from core.models import APIUsageLog
import logging

logger = logging.getLogger(__name__)

# نرخ تبدیل دلار به تومان (می‌تواند از تنظیمات یا API دریافت شود)
USD_TO_TOMAN_RATE = Decimal('42000')  # نرخ تقریبی

# تعریف هزینه هر API call بر اساس provider
API_COSTS = {
    'twelvedata': {
        'per_request': Decimal('0.001'),  # $0.001 per request
        'free_tier': 800,  # 800 requests per day free
    },
    'alphavantage': {
        'per_request': Decimal('0.0005'),  # $0.0005 per request
        'free_tier': 5,  # 5 requests per minute, 500 per day free
    },
    'oanda': {
        'per_request': Decimal('0'),  # Free for practice account
        'free_tier': float('inf'),
    },
    'metalsapi': {
        'per_request': Decimal('0.002'),  # $0.002 per request
        'free_tier': 50,  # 50 requests per month free
    },
    'financialmodelingprep': {
        'per_request': Decimal('0.0015'),  # $0.0015 per request
        'free_tier': 250,  # 250 requests per day free
    },
    'nerkh': {
        'per_request': Decimal('0'),  # Free
        'free_tier': float('inf'),
    },
    'gemini': {
        'per_request': Decimal('0.0001'),  # $0.0001 per 1K tokens (approximate)
        'free_tier': 15000,  # 15 requests per minute free
    },
    'kavenegar': {
        'per_request': Decimal('0.0005'),  # ~200 تومان per SMS
        'free_tier': 0,
    },
}


def calculate_api_cost(provider: str, request_count: int = 1, tokens: Optional[int] = None) -> Decimal:
    """
    محاسبه هزینه API بر اساس provider
    
    Args:
        provider: نام ارائه‌دهنده API
        request_count: تعداد درخواست‌ها
        tokens: تعداد توکن‌ها (برای Gemini)
    
    Returns:
        هزینه به دلار
    """
    if provider not in API_COSTS:
        return Decimal('0')
    
    cost_config = API_COSTS[provider]
    base_cost = cost_config.get('per_request', Decimal('0'))
    
    # برای Gemini هزینه بر اساس توکن محاسبه می‌شود
    if provider == 'gemini' and tokens:
        # تقریباً $0.0001 per 1K tokens
        cost = (Decimal(tokens) / Decimal('1000')) * Decimal('0.0001')
    else:
        cost = base_cost * Decimal(str(request_count))
    
    return cost


def log_api_usage(
    provider: str,
    endpoint: str = '',
    request_type: str = 'GET',
    status_code: Optional[int] = None,
    success: bool = True,
    response_time_ms: Optional[float] = None,
    error_message: str = '',
    cost: Optional[Decimal] = None,
    tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> APIUsageLog:
    """
    ثبت لاگ استفاده از API
    
    Args:
        provider: نام ارائه‌دهنده API
        endpoint: آدرس endpoint
        request_type: نوع درخواست
        status_code: کد وضعیت HTTP
        success: آیا درخواست موفق بود
        response_time_ms: زمان پاسخ به میلی‌ثانیه
        error_message: پیام خطا
        cost: هزینه (اگر محاسبه شده باشد)
        tokens: تعداد توکن‌ها (برای Gemini)
        metadata: اطلاعات اضافی
    
    Returns:
        APIUsageLog instance
    """
    try:
        # محاسبه هزینه اگر داده نشده باشد
        if cost is None:
            cost = calculate_api_cost(provider, tokens=tokens)
        
        # تبدیل به تومان
        cost_toman = cost * USD_TO_TOMAN_RATE
        
        # ایجاد لاگ
        log_entry = APIUsageLog.objects.create(
            provider=provider,
            endpoint=endpoint,
            request_type=request_type,
            status_code=status_code,
            success=success,
            cost=cost,
            cost_toman=cost_toman,
            response_time_ms=response_time_ms,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        return log_entry
    except Exception as e:
        logger.error(f"Error logging API usage: {e}")
        # در صورت خطا، لاگ نمی‌کنیم اما خطا را برمی‌گردانیم
        raise


def get_api_usage_stats(
    provider: Optional[str] = None,
    start_date: Optional[timezone.datetime] = None,
    end_date: Optional[timezone.datetime] = None
) -> Dict[str, Any]:
    """
    دریافت آمار استفاده از API
    
    Args:
        provider: فیلتر بر اساس provider (اختیاری)
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
    
    Returns:
        دیکشنری شامل آمار
    """
    queryset = APIUsageLog.objects.all()
    
    # فیلتر بر اساس provider
    if provider:
        queryset = queryset.filter(provider=provider)
    
    # فیلتر بر اساس تاریخ
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    # محاسبه آمار کلی
    total_requests = queryset.count()
    successful_requests = queryset.filter(success=True).count()
    failed_requests = queryset.filter(success=False).count()
    
    # محاسبه هزینه کل
    total_cost_usd = queryset.aggregate(
        total=Sum('cost')
    )['total'] or Decimal('0')
    
    total_cost_toman = queryset.aggregate(
        total=Sum('cost_toman')
    )['total'] or Decimal('0')
    
    # آمار بر اساس provider
    provider_stats = {}
    for provider_name in queryset.values_list('provider', flat=True).distinct():
        provider_queryset = queryset.filter(provider=provider_name)
        provider_total = provider_queryset.count()
        provider_cost_usd = provider_queryset.aggregate(
            total=Sum('cost')
        )['total'] or Decimal('0')
        provider_cost_toman = provider_queryset.aggregate(
            total=Sum('cost_toman')
        )['total'] or Decimal('0')
        
        provider_stats[provider_name] = {
            'total_requests': provider_total,
            'successful_requests': provider_queryset.filter(success=True).count(),
            'failed_requests': provider_queryset.filter(success=False).count(),
            'total_cost_usd': float(provider_cost_usd),
            'total_cost_toman': float(provider_cost_toman),
        }
    
    return {
        'total_requests': total_requests,
        'successful_requests': successful_requests,
        'failed_requests': failed_requests,
        'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
        'total_cost_usd': float(total_cost_usd),
        'total_cost_toman': float(total_cost_toman),
        'provider_stats': provider_stats,
    }


# Decorator برای ردیابی استفاده از API
def track_api_usage(provider: str):
    """
    Decorator برای ردیابی استفاده از API
    
    Usage:
        @track_api_usage('twelvedata')
        def fetch_data():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            status_code = None
            error_message = ''
            tokens = None
            
            try:
                result = func(*args, **kwargs)
                
                # اگر نتیجه یک response object باشد، status_code را استخراج کن
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                    success = status_code < 400
                
                # برای Gemini، تعداد توکن‌ها را از metadata استخراج کن
                if provider == 'gemini' and isinstance(result, dict):
                    tokens = result.get('tokens', None)
                
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time = (time.time() - start_time) * 1000  # به میلی‌ثانیه
                
                # ثبت لاگ
                try:
                    log_api_usage(
                        provider=provider,
                        endpoint=func.__name__,
                        request_type='GET',
                        status_code=status_code,
                        success=success,
                        response_time_ms=response_time,
                        error_message=error_message,
                        tokens=tokens
                    )
                except Exception as log_error:
                    logger.error(f"Error logging API usage: {log_error}")
        
        return wrapper
    return decorator


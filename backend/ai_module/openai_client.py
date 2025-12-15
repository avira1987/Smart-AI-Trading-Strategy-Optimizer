"""
ماژول برای بررسی موجودی و آمار استفاده از OpenAI
"""
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q
from core.models import APIUsageLog
from config.settings import get_api_key_from_db_or_env
import logging

logger = logging.getLogger(__name__)

def get_openai_api_key(user=None) -> Optional[str]:
    """دریافت کلید API OpenAI از دیتابیس یا environment"""
    return get_api_key_from_db_or_env('openai', 'OPENAI_API_KEY', user=user)


def check_openai_account_balance(user=None) -> Dict[str, Any]:
    """
    بررسی موجودی حساب OpenAI
    
    از آنجایی که OpenAI API مستقیم برای بررسی موجودی ندارد،
    از آمار استفاده و لاگ‌های ذخیره شده استفاده می‌کنیم.
    
    Args:
        user: کاربر فعلی (برای دریافت API key)
    
    Returns:
        Dict شامل:
        - success: bool - آیا بررسی موفق بود؟
        - balance: str - وضعیت موجودی (بر اساس آمار)
        - balance_formatted: str - موجودی فرمت شده
        - currency: str - واحد پول ($)
        - message: str - پیام توضیحی
        - usage_stats: dict - آمار استفاده
        - last_checked: str - زمان آخرین بررسی
    """
    api_key = get_openai_api_key(user)
    if not api_key:
        return {
            'success': False,
            'error': 'کلید API OpenAI تنظیم نشده است. لطفاً در تنظیمات > پیکربندی API، کلید OpenAI را اضافه کنید.',
            'balance': None,
            'balance_formatted': 'نامشخص',
            'currency': '$',
            'message': '',
            'last_checked': datetime.now().isoformat()
        }
    
    try:
        # محاسبه آمار استفاده از OpenAI در 30 روز گذشته
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # فیلتر لاگ‌های OpenAI (openai, chatgpt, gpt)
        openai_logs = APIUsageLog.objects.filter(
            Q(provider='openai') | Q(provider='chatgpt') | Q(provider='gpt'),
            created_at__gte=thirty_days_ago
        )
        
        # آمار کلی
        total_requests = openai_logs.count()
        successful_requests = openai_logs.filter(success=True).count()
        failed_requests = openai_logs.filter(success=False).count()
        
        # محاسبه هزینه کل
        cost_stats = openai_logs.aggregate(
            total_cost_usd=Sum('cost'),
            total_cost_toman=Sum('cost_toman')
        )
        
        total_cost_usd = float(cost_stats['total_cost_usd'] or 0)
        total_cost_toman = float(cost_stats['total_cost_toman'] or 0)
        
        # آمار توکن‌ها
        total_tokens = 0
        input_tokens = 0
        output_tokens = 0
        
        for log in openai_logs.filter(success=True):
            metadata = log.metadata or {}
            if 'tokens_used' in metadata:
                total_tokens += metadata['tokens_used']
            if 'input_tokens' in metadata:
                input_tokens += metadata['input_tokens']
            if 'output_tokens' in metadata:
                output_tokens += metadata['output_tokens']
        
        # آمار امروز
        today = timezone.now().date()
        today_logs = openai_logs.filter(created_at__date=today)
        today_requests = today_logs.count()
        today_cost_usd = float(today_logs.aggregate(total=Sum('cost'))['total'] or 0)
        
        # تست اتصال با یک درخواست کوچک
        test_success = False
        latency_ms = None
        test_error = None
        
        try:
            endpoint = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
                "temperature": 0.1
            }
            
            start_time = time.time()
            response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                test_success = True
            elif response.status_code == 401:
                test_error = "کلید API نامعتبر است"
            elif response.status_code == 429:
                test_error = "محدودیت نرخ استفاده (Rate Limit)"
            elif response.status_code == 402:
                test_error = "موجودی حساب کافی نیست"
            else:
                test_error = f"خطا: {response.status_code}"
        except requests.exceptions.Timeout:
            test_error = "Timeout - اتصال به OpenAI برقرار نشد"
        except Exception as e:
            test_error = f"خطا در تست اتصال: {str(e)}"
        
        # تعیین وضعیت موجودی بر اساس تست و آمار
        if test_success:
            balance_status = "فعال"
            balance_formatted = "حساب فعال است"
        elif test_error and "402" in test_error:
            balance_status = "ناکافی"
            balance_formatted = "موجودی کافی نیست"
        elif test_error and "401" in test_error:
            balance_status = "نامعتبر"
            balance_formatted = "کلید API نامعتبر"
        else:
            balance_status = "نامشخص"
            balance_formatted = "وضعیت نامشخص"
        
        usage_stats = {
            'total_requests_30d': total_requests,
            'successful_requests_30d': successful_requests,
            'failed_requests_30d': failed_requests,
            'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            'total_cost_usd_30d': total_cost_usd,
            'total_cost_toman_30d': total_cost_toman,
            'total_tokens_30d': total_tokens,
            'input_tokens_30d': input_tokens,
            'output_tokens_30d': output_tokens,
            'today_requests': today_requests,
            'today_cost_usd': today_cost_usd,
        }
        
        return {
            'success': test_success,
            'balance': balance_status,
            'balance_formatted': balance_formatted,
            'currency': '$',
            'message': test_error or 'حساب OpenAI فعال است',
            'error': test_error if not test_success else None,
            'usage_stats': usage_stats,
            'last_checked': datetime.now().isoformat(),
            'latency_ms': latency_ms,
            'test_success': test_success
        }
        
    except Exception as e:
        logger.error(f"Error checking OpenAI account balance: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'خطا در بررسی موجودی: {str(e)}',
            'balance': None,
            'balance_formatted': 'خطا در بررسی',
            'currency': '$',
            'message': '',
            'last_checked': datetime.now().isoformat()
        }


def get_openai_request_logs(user=None, limit=100, start_date=None, end_date=None, success_only=None) -> Dict[str, Any]:
    """
    دریافت لاگ‌های درخواست‌های OpenAI
    
    Args:
        user: کاربر برای فیلتر (اختیاری)
        limit: تعداد لاگ‌های برگشتی
        start_date: تاریخ شروع (اختیاری)
        end_date: تاریخ پایان (اختیاری)
        success_only: فقط درخواست‌های موفق (اختیاری)
    
    Returns:
        Dict شامل لیست لاگ‌ها و آمار
    """
    try:
        # فیلتر لاگ‌های OpenAI
        logs_query = APIUsageLog.objects.filter(
            Q(provider='openai') | Q(provider='chatgpt') | Q(provider='gpt')
        ).order_by('-created_at')
        
        if user:
            logs_query = logs_query.filter(user=user)
        
        if start_date:
            logs_query = logs_query.filter(created_at__gte=start_date)
        
        if end_date:
            logs_query = logs_query.filter(created_at__lte=end_date)
        
        if success_only is not None:
            logs_query = logs_query.filter(success=success_only)
        
        total_count = logs_query.count()
        logs = logs_query[:limit]
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'user': log.user.username if log.user else 'سیستم',
                'user_id': log.user.id if log.user else None,
                'endpoint': log.endpoint,
                'request_type': log.request_type,
                'status_code': log.status_code,
                'success': log.success,
                'cost_usd': float(log.cost),
                'cost_toman': float(log.cost_toman),
                'response_time_ms': log.response_time_ms,
                'error_message': log.error_message,
                'metadata': log.metadata,
                'created_at': log.created_at.isoformat(),
            })
        
        return {
            'success': True,
            'logs': logs_data,
            'total': total_count,
            'returned': len(logs_data)
        }
    except Exception as e:
        logger.error(f"Error getting OpenAI request logs: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'logs': [],
            'total': 0,
            'returned': 0
        }


def get_openai_usage_report(start_date=None, end_date=None, group_by='day') -> Dict[str, Any]:
    """
    دریافت گزارش پیشرفته استفاده از OpenAI
    
    Args:
        start_date: تاریخ شروع
        end_date: تاریخ پایان
        group_by: گروه‌بندی بر اساس 'day', 'hour', 'user'
    
    Returns:
        Dict شامل گزارش تفصیلی
    """
    try:
        logs_query = APIUsageLog.objects.filter(
            Q(provider='openai') | Q(provider='chatgpt') | Q(provider='gpt')
        )
        
        if start_date:
            logs_query = logs_query.filter(created_at__gte=start_date)
        
        if end_date:
            logs_query = logs_query.filter(created_at__lte=end_date)
        
        # آمار کلی
        total_requests = logs_query.count()
        successful_requests = logs_query.filter(success=True).count()
        failed_requests = logs_query.filter(success=False).count()
        
        # هزینه‌ها
        cost_stats = logs_query.aggregate(
            total_cost_usd=Sum('cost'),
            total_cost_toman=Sum('cost_toman'),
            avg_response_time=Sum('response_time_ms') / Count('id')
        )
        
        # آمار بر اساس کاربر
        user_stats = {}
        for log in logs_query.select_related('user'):
            username = log.user.username if log.user else 'سیستم'
            if username not in user_stats:
                user_stats[username] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'total_cost_usd': 0,
                    'total_cost_toman': 0,
                }
            
            user_stats[username]['total_requests'] += 1
            if log.success:
                user_stats[username]['successful_requests'] += 1
            else:
                user_stats[username]['failed_requests'] += 1
            user_stats[username]['total_cost_usd'] += float(log.cost)
            user_stats[username]['total_cost_toman'] += float(log.cost_toman)
        
        # آمار بر اساس روز
        daily_stats = {}
        for log in logs_query:
            date_key = log.created_at.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'date': date_key,
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'total_cost_usd': 0,
                }
            
            daily_stats[date_key]['total_requests'] += 1
            if log.success:
                daily_stats[date_key]['successful_requests'] += 1
            else:
                daily_stats[date_key]['failed_requests'] += 1
            daily_stats[date_key]['total_cost_usd'] += float(log.cost)
        
        return {
            'success': True,
            'summary': {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0,
                'total_cost_usd': float(cost_stats['total_cost_usd'] or 0),
                'total_cost_toman': float(cost_stats['total_cost_toman'] or 0),
                'avg_response_time_ms': float(cost_stats['avg_response_time'] or 0),
            },
            'by_user': user_stats,
            'by_day': list(daily_stats.values()),
            'period': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
            }
        }
    except Exception as e:
        logger.error(f"Error generating OpenAI usage report: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'summary': {},
            'by_user': {},
            'by_day': []
        }


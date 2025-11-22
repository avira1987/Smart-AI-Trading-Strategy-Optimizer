"""
Admin security management views
برای مدیریت مسائل حساس امنیتی توسط ادمین
"""
import time
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminOrStaff
from .rate_limiter import rate_limiter
import logging

logger = logging.getLogger(__name__)


class SecurityManagementView(APIView):
    """
    View برای مدیریت مسائل امنیتی توسط ادمین
    """
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    
    def get(self, request):
        """
        دریافت اطلاعات امنیتی:
        - لیست IP های مسدود شده
        - آمار Rate Limiting
        - تنظیمات Rate Limit
        """
        try:
            # لیست IP های مسدود شده (با محدود کردن خروجی برای کارایی)
            blocked_snapshot, total_blocked = rate_limiter.get_blocked_snapshot(limit=200)
            blocked_ips = [
                {
                    'ip': entry['ip'],
                    'blocked_until': datetime.fromtimestamp(entry['blocked_until']).isoformat(),
                    'remaining_seconds': entry['remaining_seconds'],
                    'remaining_minutes': entry['remaining_seconds'] // 60,
                }
                for entry in blocked_snapshot
            ]
            
            # آمار Rate Limiting (خلاصه بر اساس پنجره ۵ دقیقه‌ای)
            stats_snapshot, total_tracked = rate_limiter.get_recent_activity_snapshot(
                window_seconds=300,
                limit=200,
            )
            rate_limit_stats = {
                entry['ip']: {
                    'ip': entry['ip'],
                    'requests_count': entry['requests_count'],
                    'last_request': datetime.fromtimestamp(entry['last_request']).isoformat(),
                    'first_request': datetime.fromtimestamp(entry['first_request']).isoformat(),
                }
                for entry in stats_snapshot
            }
            
            # تنظیمات Rate Limit
            from .rate_limiter import RateLimitMiddleware
            rate_limit_config = {
                'limits': RateLimitMiddleware.RATE_LIMITS,
                'protected_paths': RateLimitMiddleware.RATE_LIMITED_PATHS,
            }
            
            return Response({
                'success': True,
                'blocked_ips': blocked_ips,
                'rate_limit_stats': rate_limit_stats,
                'rate_limit_config': rate_limit_config,
                'total_blocked': total_blocked,
                'total_tracked_ips': total_tracked,
            })
            
        except Exception as e:
            logger.error(f"Error in SecurityManagementView.get: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'خطا در دریافت اطلاعات امنیتی: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        عملیات مدیریت امنیتی:
        - آزاد کردن IP مسدود شده
        - پاک کردن تاریخچه Rate Limit
        """
        action_type = request.data.get('action')
        
        if action_type == 'unblock_ip':
            ip = request.data.get('ip')
            if not ip:
                return Response({
                    'success': False,
                    'message': 'IP address is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # آزاد کردن IP
            if ip in rate_limiter.blocked_ips:
                del rate_limiter.blocked_ips[ip]
                logger.info(f"Admin {request.user.username} unblocked IP: {ip}")
                return Response({
                    'success': True,
                    'message': f'IP {ip} آزاد شد'
                })
            else:
                return Response({
                    'success': False,
                    'message': f'IP {ip} در لیست مسدود شده‌ها نیست'
                }, status=status.HTTP_404_NOT_FOUND)
        
        elif action_type == 'clear_rate_limit_history':
            ip = request.data.get('ip')
            if ip:
                # پاک کردن تاریخچه یک IP خاص
                if ip in rate_limiter.requests:
                    del rate_limiter.requests[ip]
                    logger.info(f"Admin {request.user.username} cleared rate limit history for IP: {ip}")
                    return Response({
                        'success': True,
                        'message': f'تاریخچه Rate Limit برای IP {ip} پاک شد'
                    })
                else:
                    return Response({
                        'success': False,
                        'message': f'تاریخچه‌ای برای IP {ip} یافت نشد'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # پاک کردن همه تاریخچه‌ها
                rate_limiter.requests.clear()
                logger.info(f"Admin {request.user.username} cleared all rate limit history")
                return Response({
                    'success': True,
                    'message': 'همه تاریخچه‌های Rate Limit پاک شدند'
                })
        
        elif action_type == 'unblock_all':
            # آزاد کردن همه IP ها
            count = len(rate_limiter.blocked_ips)
            rate_limiter.blocked_ips.clear()
            logger.info(f"Admin {request.user.username} unblocked all IPs ({count} IPs)")
            return Response({
                'success': True,
                'message': f'{count} IP آزاد شدند'
            })
        
        else:
            return Response({
                'success': False,
                'message': f'عملیات نامعتبر: {action_type}'
            }, status=status.HTTP_400_BAD_REQUEST)


class SecurityLogsView(APIView):
    """
    View برای مشاهده لاگ‌های امنیتی
    """
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    
    def get(self, request):
        """
        دریافت لاگ‌های امنیتی از logger
        """
        try:
            # در اینجا می‌توانید لاگ‌های امنیتی را از فایل یا دیتابیس بخوانید
            # برای سادگی، یک نمونه ساختاری برمی‌گردانیم
            
            # می‌توانید از logging.handlers.RotatingFileHandler استفاده کنید
            # و لاگ‌ها را در فایل ذخیره کنید
            
            logs = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'WARNING',
                    'message': 'Rate limit exceeded',
                    'ip': '192.168.1.1',
                    'path': '/api/auth/send-otp/',
                }
            ]
            
            return Response({
                'success': True,
                'logs': logs,
                'note': 'برای مشاهده لاگ‌های کامل، فایل logs/api.log را بررسی کنید'
            })
            
        except Exception as e:
            logger.error(f"Error in SecurityLogsView.get: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'خطا در دریافت لاگ‌ها: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


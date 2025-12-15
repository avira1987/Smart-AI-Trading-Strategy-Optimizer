"""
API Views برای Analytics - Google Analytics و Database Analytics
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Max, Min, Q
from django.db.models.functions import TruncDate, TruncHour
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User

from api.permissions import IsAdminOrStaff
from core.models import UserSession, PageVisit, Device, UserProfile

logger = logging.getLogger(__name__)


# ==================== Google Analytics API ====================

def get_google_analytics_client():
    """ایجاد کلاینت Google Analytics"""
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.oauth2 import service_account
        
        SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE', '')
        if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
            return None
        
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        return BetaAnalyticsDataClient(credentials=credentials)
    except Exception as e:
        logger.error(f"Error creating Google Analytics client: {e}")
        return None


class GoogleAnalyticsStatsView(APIView):
    """دریافت آمار از Google Analytics API"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت آمار کلی از Google Analytics"""
        PROPERTY_ID = os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID', '')
        if not PROPERTY_ID:
            return Response({
                'success': False,
                'message': 'Google Analytics Property ID تنظیم نشده است',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        client = get_google_analytics_client()
        if not client:
            return Response({
                'success': False,
                'message': 'خطا در اتصال به Google Analytics',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # دریافت پارامترها
        days = int(request.query_params.get('days', 7))
        start_date = f"{days}daysAgo"
        end_date = "today"
        
        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric,
            )
            
            # درخواست آمار کلی
            request_obj = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="newUsers"),
                    Metric(name="sessions"),
                    Metric(name="screenPageViews"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="bounceRate"),
                ],
            )
            
            response = client.run_report(request_obj)
            
            if response.row_count == 0:
                return Response({
                    'success': True,
                    'message': 'داده‌ای دریافت نشد',
                    'data': {
                        'activeUsers': 0,
                        'newUsers': 0,
                        'sessions': 0,
                        'screenPageViews': 0,
                        'averageSessionDuration': 0,
                        'bounceRate': 0,
                    }
                })
            
            row = response.rows[0]
            metrics = row.metric_values
            
            data = {
                'activeUsers': int(metrics[0].value) if metrics[0].value else 0,
                'newUsers': int(metrics[1].value) if metrics[1].value else 0,
                'sessions': int(metrics[2].value) if metrics[2].value else 0,
                'screenPageViews': int(metrics[3].value) if metrics[3].value else 0,
                'averageSessionDuration': float(metrics[4].value) if metrics[4].value else 0,
                'bounceRate': float(metrics[5].value) if metrics[5].value else 0,
            }
            
            return Response({
                'success': True,
                'message': 'آمار با موفقیت دریافت شد',
                'data': data
            })
            
        except Exception as e:
            logger.error(f"Error fetching Google Analytics data: {e}")
            return Response({
                'success': False,
                'message': f'خطا در دریافت داده: {str(e)}',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAnalyticsPagesView(APIView):
    """دریافت صفحات پربازدید از Google Analytics"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت صفحات پربازدید"""
        PROPERTY_ID = os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID', '')
        if not PROPERTY_ID:
            return Response({
                'success': False,
                'message': 'Google Analytics Property ID تنظیم نشده است',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        client = get_google_analytics_client()
        if not client:
            return Response({
                'success': False,
                'message': 'خطا در اتصال به Google Analytics',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        start_date = f"{days}daysAgo"
        end_date = "today"
        
        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric,
            )
            
            request_obj = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[
                    Dimension(name="pagePath"),
                    Dimension(name="pageTitle"),
                ],
                metrics=[
                    Metric(name="screenPageViews"),
                    Metric(name="activeUsers"),
                    Metric(name="averageSessionDuration"),
                ],
                order_bys=[{"metric": {"metric_name": "screenPageViews"}, "desc": True}],
                limit=limit
            )
            
            response = client.run_report(request_obj)
            
            pages = []
            for row in response.rows:
                pages.append({
                    'path': row.dimension_values[0].value,
                    'title': row.dimension_values[1].value,
                    'views': int(row.metric_values[0].value) if row.metric_values[0].value else 0,
                    'users': int(row.metric_values[1].value) if row.metric_values[1].value else 0,
                    'avgDuration': float(row.metric_values[2].value) if row.metric_values[2].value else 0,
                })
            
            return Response({
                'success': True,
                'message': 'صفحات با موفقیت دریافت شدند',
                'data': pages
            })
            
        except Exception as e:
            logger.error(f"Error fetching Google Analytics pages: {e}")
            return Response({
                'success': False,
                'message': f'خطا در دریافت صفحات: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAnalyticsTimeSeriesView(APIView):
    """دریافت سری زمانی از Google Analytics"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت سری زمانی"""
        PROPERTY_ID = os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID', '')
        if not PROPERTY_ID:
            return Response({
                'success': False,
                'message': 'Google Analytics Property ID تنظیم نشده است',
                'data': []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        client = get_google_analytics_client()
        if not client:
            return Response({
                'success': False,
                'message': 'خطا در اتصال به Google Analytics',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        days = int(request.query_params.get('days', 7))
        start_date = f"{days}daysAgo"
        end_date = "today"
        
        try:
            from google.analytics.data_v1beta.types import (
                RunReportRequest,
                DateRange,
                Dimension,
                Metric,
            )
            
            request_obj = RunReportRequest(
                property=f"properties/{PROPERTY_ID}",
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimensions=[Dimension(name="date")],
                metrics=[
                    Metric(name="activeUsers"),
                    Metric(name="sessions"),
                    Metric(name="screenPageViews"),
                ],
                order_bys=[{"dimension": {"dimension_name": "date"}}],
            )
            
            response = client.run_report(request_obj)
            
            time_series = []
            for row in response.rows:
                date_str = row.dimension_values[0].value
                try:
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                    date_formatted = date_obj.strftime("%Y-%m-%d")
                except:
                    date_formatted = date_str
                
                time_series.append({
                    'date': date_formatted,
                    'users': int(row.metric_values[0].value) if row.metric_values[0].value else 0,
                    'sessions': int(row.metric_values[1].value) if row.metric_values[1].value else 0,
                    'views': int(row.metric_values[2].value) if row.metric_values[2].value else 0,
                })
            
            return Response({
                'success': True,
                'message': 'سری زمانی با موفقیت دریافت شد',
                'data': time_series
            })
            
        except Exception as e:
            logger.error(f"Error fetching Google Analytics time series: {e}")
            return Response({
                'success': False,
                'message': f'خطا در دریافت سری زمانی: {str(e)}',
                'data': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Database Analytics API ====================

class DatabaseAnalyticsStatsView(APIView):
    """دریافت آمار از Database (کاربران لاگین شده)"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت آمار کلی از Database"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # آمار جلسات
        total_sessions = UserSession.objects.filter(login_time__gte=start_date).count()
        active_sessions = UserSession.objects.filter(
            login_time__gte=start_date,
            is_active=True
        ).count()
        completed_sessions = UserSession.objects.filter(
            login_time__gte=start_date,
            is_active=False
        ).count()
        
        # آمار بازدید صفحات
        total_page_visits = PageVisit.objects.filter(visit_time__gte=start_date).count()
        unique_pages = PageVisit.objects.filter(
            visit_time__gte=start_date
        ).values('page_path').distinct().count()
        
        # آمار کاربران
        # کاربران منحصر به فرد که در بازه زمانی لاگین کرده‌اند
        unique_users = UserSession.objects.filter(
            login_time__gte=start_date
        ).values('user').distinct().count()
        
        # کل کاربران ثبت‌نام شده (دارای شماره موبایل)
        total_registered_users = UserProfile.objects.count()
        
        # کاربران ثبت‌نام شده در بازه زمانی
        registered_users_in_period = UserProfile.objects.filter(
            created_at__gte=start_date
        ).count()
        
        # شماره موبایل‌های منحصر به فرد (باید با total_registered_users برابر باشد)
        unique_phone_numbers = UserProfile.objects.values('phone_number').distinct().count()
        
        # میانگین مدت جلسه
        avg_session_duration = UserSession.objects.filter(
            login_time__gte=start_date,
            is_active=False
        ).aggregate(avg=Avg('total_duration'))['avg'] or 0
        
        # میانگین مدت بازدید صفحه
        avg_page_duration = PageVisit.objects.filter(
            visit_time__gte=start_date,
            is_active=False
        ).aggregate(avg=Avg('duration'))['avg'] or 0
        
        data = {
            'totalSessions': total_sessions,
            'activeSessions': active_sessions,
            'completedSessions': completed_sessions,
            'totalPageVisits': total_page_visits,
            'uniquePages': unique_pages,
            'uniqueUsers': unique_users,  # کاربران لاگین شده در بازه زمانی
            'totalRegisteredUsers': total_registered_users,  # کل کاربران ثبت‌نام شده
            'registeredUsersInPeriod': registered_users_in_period,  # کاربران ثبت‌نام شده در بازه زمانی
            'uniquePhoneNumbers': unique_phone_numbers,  # شماره موبایل‌های منحصر به فرد
            'avgSessionDuration': int(avg_session_duration),
            'avgPageDuration': int(avg_page_duration),
        }
        
        return Response({
            'success': True,
            'message': 'آمار با موفقیت دریافت شد',
            'data': data
        })


class DatabaseAnalyticsPagesView(APIView):
    """دریافت صفحات پربازدید از Database"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت صفحات پربازدید"""
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))
        start_date = timezone.now() - timedelta(days=days)
        
        pages = PageVisit.objects.filter(
            visit_time__gte=start_date
        ).values(
            'page_path',
            'page_title'
        ).annotate(
            views=Count('id'),
            users=Count('user', distinct=True),
            avgDuration=Avg('duration')
        ).order_by('-views')[:limit]
        
        result = []
        for page in pages:
            result.append({
                'path': page['page_path'],
                'title': page['page_title'] or page['page_path'],
                'views': page['views'],
                'users': page['users'],
                'avgDuration': int(page['avgDuration'] or 0),
            })
        
        return Response({
            'success': True,
            'message': 'صفحات با موفقیت دریافت شدند',
            'data': result
        })


class DatabaseAnalyticsUsersView(APIView):
    """دریافت آمار کاربران"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت آمار کاربران"""
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 20))
        start_date = timezone.now() - timedelta(days=days)
        
        users = UserSession.objects.filter(
            login_time__gte=start_date
        ).values(
            'user__id',
            'user__username',
            'user__email'
        ).annotate(
            sessions=Count('id'),
            totalDuration=Sum('total_duration'),
            lastLogin=Max('login_time'),
            pageVisits=Count('visits')
        ).order_by('-sessions')[:limit]
        
        result = []
        for user in users:
            result.append({
                'userId': user['user__id'],
                'username': user['user__username'],
                'email': user['user__email'],
                'sessions': user['sessions'],
                'totalDuration': int(user['totalDuration'] or 0),
                'lastLogin': user['lastLogin'].isoformat() if user['lastLogin'] else None,
                'pageVisits': user['pageVisits'],
            })
        
        return Response({
            'success': True,
            'message': 'آمار کاربران با موفقیت دریافت شد',
            'data': result
        })


class DatabaseAnalyticsTimeSeriesView(APIView):
    """دریافت سری زمانی از Database"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت سری زمانی"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)
        
        # آمار روزانه جلسات
        sessions_by_date = UserSession.objects.filter(
            login_time__gte=start_date
        ).annotate(
            date=TruncDate('login_time')
        ).values('date').annotate(
            sessions=Count('id'),
            users=Count('user', distinct=True)
        ).order_by('date')
        
        # آمار روزانه بازدید صفحات
        visits_by_date = PageVisit.objects.filter(
            visit_time__gte=start_date
        ).annotate(
            date=TruncDate('visit_time')
        ).values('date').annotate(
            visits=Count('id')
        ).order_by('date')
        
        # ترکیب داده‌ها
        time_series = {}
        for item in sessions_by_date:
            date_str = item['date'].strftime('%Y-%m-%d')
            time_series[date_str] = {
                'date': date_str,
                'sessions': item['sessions'],
                'users': item['users'],
                'visits': 0,
            }
        
        for item in visits_by_date:
            date_str = item['date'].strftime('%Y-%m-%d')
            if date_str not in time_series:
                time_series[date_str] = {
                    'date': date_str,
                    'sessions': 0,
                    'users': 0,
                    'visits': 0,
                }
            time_series[date_str]['visits'] = item['visits']
        
        result = list(time_series.values())
        result.sort(key=lambda x: x['date'])
        
        return Response({
            'success': True,
            'message': 'سری زمانی با موفقیت دریافت شد',
            'data': result
        })


# ==================== Track API (برای Frontend) ====================

class TrackSessionView(APIView):
    """ثبت جلسه کاربر"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """شروع جلسه"""
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({
                'success': False,
                'message': 'session_id الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # بررسی وجود جلسه فعال
        existing_session = UserSession.objects.filter(
            user=request.user,
            session_id=session_id,
            is_active=True
        ).first()
        
        if existing_session:
            return Response({
                'success': True,
                'message': 'جلسه از قبل وجود دارد',
                'session_id': session_id
            })
        
        # ایجاد جلسه جدید
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        device_id = request.data.get('device_id', '')
        
        session = UserSession.objects.create(
            user=request.user,
            session_id=session_id,
            login_time=timezone.now(),
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            is_active=True
        )
        
        return Response({
            'success': True,
            'message': 'جلسه با موفقیت ثبت شد',
            'session_id': session_id
        })


class TrackPageVisitView(APIView):
    """ثبت بازدید صفحه"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """ثبت بازدید صفحه"""
        session_id = request.data.get('session_id')
        page_path = request.data.get('page_path')
        page_title = request.data.get('page_title', '')
        referrer = request.data.get('referrer', '')
        
        if not session_id or not page_path:
            return Response({
                'success': False,
                'message': 'session_id و page_path الزامی هستند'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # پیدا کردن جلسه
        session = UserSession.objects.filter(
            user=request.user,
            session_id=session_id,
            is_active=True
        ).first()
        
        if not session:
            return Response({
                'success': False,
                'message': 'جلسه پیدا نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ایجاد بازدید
        visit = PageVisit.objects.create(
            session=session,
            user=request.user,
            page_path=page_path,
            page_title=page_title,
            visit_time=timezone.now(),
            referrer=referrer,
            is_active=True
        )
        
        return Response({
            'success': True,
            'message': 'بازدید با موفقیت ثبت شد',
            'visit_id': visit.id
        })


class EndPageVisitView(APIView):
    """پایان بازدید صفحه"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """پایان بازدید صفحه"""
        visit_id = request.data.get('visit_id')
        if not visit_id:
            return Response({
                'success': False,
                'message': 'visit_id الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            visit = PageVisit.objects.get(
                id=visit_id,
                user=request.user,
                is_active=True
            )
            visit.end_visit()
            return Response({
                'success': True,
                'message': 'بازدید با موفقیت به پایان رسید',
                'duration': visit.duration
            })
        except PageVisit.DoesNotExist:
            return Response({
                'success': False,
                'message': 'بازدید پیدا نشد'
            }, status=status.HTTP_404_NOT_FOUND)


class EndSessionView(APIView):
    """پایان جلسه"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """پایان جلسه"""
        session_id = request.data.get('session_id')
        if not session_id:
            return Response({
                'success': False,
                'message': 'session_id الزامی است'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            session = UserSession.objects.get(
                user=request.user,
                session_id=session_id,
                is_active=True
            )
            
            # پایان دادن به همه بازدیدهای فعال
            PageVisit.objects.filter(
                session=session,
                is_active=True
            ).update(
                exit_time=timezone.now(),
                is_active=False
            )
            
            # پایان دادن به جلسه
            session.end_session()
            
            return Response({
                'success': True,
                'message': 'جلسه با موفقیت به پایان رسید',
                'duration': session.total_duration
            })
        except UserSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'جلسه پیدا نشد'
            }, status=status.HTTP_404_NOT_FOUND)


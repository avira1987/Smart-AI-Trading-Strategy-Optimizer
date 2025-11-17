"""
Views برای دریافت قیمت لحظه‌ای طلا
"""

from decimal import Decimal

import logging
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .gold_price_providers import GoldPriceManager
from core.models import UserGoldAPIAccess, GoldAPIAccessRequest

logger = logging.getLogger(__name__)

gold_price_manager = GoldPriceManager()


def _get_assistance_price_value() -> int:
    price_setting = getattr(settings, 'GOLD_API_ASSISTANCE_PRICE', 450000)
    try:
        return int(Decimal(str(price_setting)).quantize(Decimal('1')))
    except Exception:
        return 450000


class GoldPriceView(APIView):
    """دریافت قیمت لحظه‌ای طلا (XAU/USD)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        is_admin = user.is_staff or user.is_superuser
        assistance_price = _get_assistance_price_value()
        guide_url = getattr(settings, 'FREE_GOLD_API_GUIDE_URL', '/guides/free-gold-api')
        
        if is_admin:
            result = gold_price_manager.get_price(prefer_mt5=True, prefer_fmp=True, prefer_twelvedata=True)
            if result['success']:
                return Response({
                    'success': True,
                    'data': result['data'],
                    'price': result['price'],
                    'source': result['source'],
                    'access_type': 'admin',
                    'allow_mt5_access': True,
                    'timestamp': result['timestamp'],
                })
            return Response({
                'success': False,
                'error': 'price_fetch_error',
                'message': result.get('error', 'Could not fetch price'),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        access = getattr(user, 'gold_api_access', None)  # type: UserGoldAPIAccess | None
        has_credentials = bool(access and access.has_credentials)
        allow_mt5_access = bool(access and access.allow_mt5_access and access.is_active)
        
        if has_credentials:
            result = gold_price_manager.get_price_for_user(access.provider, access.api_key)
            if result['success']:
                return Response({
                    'success': True,
                    'data': result['data'],
                    'price': result['price'],
                    'source': result['source'],
                    'access_type': 'user_api',
                    'provider': access.provider,
                    'allow_mt5_access': allow_mt5_access,
                    'timestamp': result['timestamp'],
                })
            else:
                logger.warning(
                    "User %s has gold API credentials but fetch failed: %s",
                    user.username,
                    result.get('error')
                )
                return Response({
                    'success': False,
                    'error': 'user_api_error',
                    'message': result.get('error', 'خطا در استفاده از API ثبت شده'),
                    'provider': access.provider,
                    'allow_mt5_access': allow_mt5_access,
                }, status=status.HTTP_502_BAD_GATEWAY)
        
        if allow_mt5_access:
            result = gold_price_manager.get_price(prefer_mt5=True)
            if not result['success']:
                fallback_result = gold_price_manager.get_price()
                if fallback_result['success']:
                    result = fallback_result
            if result['success']:
                return Response({
                    'success': True,
                    'data': result['data'],
                    'price': result['price'],
                    'source': result['source'],
                    'access_type': 'mt5_delegate',
                    'allow_mt5_access': True,
                    'has_credentials': has_credentials,
                    'mt5_used': result.get('source') == 'mt5',
                    'timestamp': result['timestamp'],
                })
            return Response({
                'success': False,
                'error': 'price_fetch_error',
                'message': result.get('error', 'عدم موفقیت در دریافت قیمت از منابع مجاز'),
                'allow_mt5_access': True,
                'has_credentials': has_credentials,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        active_request = GoldAPIAccessRequest.objects.filter(
            user=user,
            status__in=['pending_payment', 'awaiting_admin']
        ).order_by('-created_at').first()
        
        return Response({
            'success': False,
            'error': 'admin_only',
            'message': 'دریافت قیمت لحظه‌ای طلا فقط برای ادمین فعال است. لطفاً مطابق آموزش API شخصی تهیه کنید یا درخواست پشتیبانی ارسال نمایید.',
            'guide_url': guide_url,
            'assistance_price': assistance_price,
            'has_active_request': bool(active_request),
            'active_request_status': active_request.status if active_request else None,
            'active_request_id': active_request.id if active_request else None,
            'has_credentials': False,
            'assigned_by_admin': False,
            'allow_mt5_access': allow_mt5_access,
        }, status=status.HTTP_403_FORBIDDEN)


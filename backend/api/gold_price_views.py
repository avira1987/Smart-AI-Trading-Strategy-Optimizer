"""
Views برای دریافت قیمت لحظه‌ای طلا
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .gold_price_providers import GoldPriceManager
from core.models import GoldPriceSubscription
from api.mt5_client import is_mt5_available
import logging

logger = logging.getLogger(__name__)

gold_price_manager = GoldPriceManager()


class GoldPriceView(APIView):
    """دریافت قیمت لحظه‌ای طلا (XAU/USD)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # بررسی دسترسی: MT5 یا اشتراک فعال
        has_mt5_access = False
        has_subscription = False
        
        # 1. بررسی MT5
        mt5_available, mt5_error = is_mt5_available()
        if mt5_available:
            has_mt5_access = True
        
        # 2. بررسی اشتراک
        try:
            subscription = GoldPriceSubscription.objects.get(user=user)
            if subscription.is_valid():
                has_subscription = True
        except GoldPriceSubscription.DoesNotExist:
            pass
        
        # اگر هیچ دسترسی نداشته باشد
        if not has_mt5_access and not has_subscription:
            return Response({
                'success': False,
                'error': 'access_denied',
                'message': 'برای دریافت قیمت لحظه‌ای طلا، باید MetaTrader 5 روی سیستم شما نصب باشد و اجرا شود، یا اشتراک ماهانه خریداری کنید.',
                'subscription_price': 300000,
                'has_mt5': False,
                'has_subscription': False,
            }, status=status.HTTP_403_FORBIDDEN)
        
        # دریافت قیمت
        # اولویت: اگر MT5 داریم از MT5، وگرنه از Financial Modeling Prep > Twelve Data
        prefer_mt5 = has_mt5_access  # اگر MT5 داریم، از آن استفاده کنیم
        prefer_fmp = not has_mt5_access  # اگر MT5 نداریم، از Financial Modeling Prep استفاده کنیم
        prefer_twelvedata = not has_mt5_access  # اگر MT5 نداریم، از Twelve Data استفاده کنیم
        result = gold_price_manager.get_price(prefer_mt5=prefer_mt5, prefer_fmp=prefer_fmp, prefer_twelvedata=prefer_twelvedata)
        
        if result['success']:
            return Response({
                'success': True,
                'data': result['data'],
                'price': result['price'],
                'source': result['source'],
                'access_type': 'mt5' if has_mt5_access else 'subscription',
                'has_mt5': has_mt5_access,
                'has_subscription': has_subscription,
                'timestamp': result['timestamp'],
            })
        else:
            return Response({
                'success': False,
                'error': 'price_fetch_error',
                'message': result.get('error', 'Could not fetch price'),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


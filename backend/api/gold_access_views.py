import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import UserGoldAPIAccess, GoldAPIAccessRequest, Wallet, Transaction
from .permissions import IsAdminOrStaff
from .serializers import (
    UserGoldAPIAccessSerializer,
    GoldAPIAccessRequestSerializer,
    AdminGoldAPIAccessRequestSerializer,
)
from .sms_service import send_sms
from .payment_service import get_zarinpal_service


logger = logging.getLogger(__name__)


def _get_assistance_price() -> Decimal:
    price_setting = getattr(settings, 'GOLD_API_ASSISTANCE_PRICE', 450000)
    try:
        return Decimal(str(price_setting))
    except Exception:
        return Decimal('450000')


def notify_admins_gold_api_request(request_obj: GoldAPIAccessRequest):
    admin_phones = getattr(settings, 'ADMIN_NOTIFICATION_PHONES', [])
    if not admin_phones:
        return
    
    message = (
        f"درخواست جدید API طلا #{request_obj.id}\n"
        f"کاربر: {request_obj.user.username}\n"
        f"وضعیت: {request_obj.get_status_display()}"
    )
    
    for phone in admin_phones:
        try:
            result = send_sms(phone, message)
            if not result.get('success', False):
                logger.error("Failed to send gold API request SMS to %s: %s", phone, result.get('message'))
        except Exception:
            logger.exception("Unexpected error sending gold API request SMS to %s", phone)


class UserGoldAPIAccessView(APIView):
    """مدیریت تنظیمات API طلا برای کاربر فعلی"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        access, _ = UserGoldAPIAccess.objects.get_or_create(
            user=request.user,
            defaults={'source': 'user'}
        )
        serializer = UserGoldAPIAccessSerializer(access)
        return Response(serializer.data)
    
    def put(self, request):
        access, _ = UserGoldAPIAccess.objects.get_or_create(
            user=request.user,
            defaults={'source': 'user'}
        )
        
        provider = (request.data.get('provider') or '').strip()
        api_key = (request.data.get('api_key') or '').strip()
        notes = (request.data.get('notes') or '').strip()
        
        # Update fields
        access.provider = provider
        access.api_key = api_key
        access.notes = notes
        access.source = 'user'
        access.assigned_by_admin = False
        
        if provider and api_key:
            access.is_active = True
            access.assigned_at = timezone.now()
        else:
            access.is_active = False
            access.assigned_at = None
        
        access.save()
        serializer = UserGoldAPIAccessSerializer(access)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GoldAPIAccessRequestViewSet(viewsets.ModelViewSet):
    """مدیریت درخواست‌های API طلا"""
    queryset = GoldAPIAccessRequest.objects.all()
    serializer_class = GoldAPIAccessRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = GoldAPIAccessRequest.objects.select_related('user', 'assigned_by', 'transaction')
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(user=user)
    
    def get_serializer_class(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return AdminGoldAPIAccessRequestSerializer
        return GoldAPIAccessRequestSerializer
    
    def create(self, request, *args, **kwargs):
        user = request.user
        if GoldAPIAccessRequest.objects.filter(
            user=user,
            status__in=['pending_payment', 'awaiting_admin']
        ).exists():
            return Response(
                {'detail': 'شما یک درخواست فعال دارید که هنوز تکمیل نشده است.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preferred_provider = (request.data.get('preferred_provider') or '').strip()
        user_notes = (request.data.get('user_notes') or '').strip()
        price_amount = _get_assistance_price()
        
        try:
            with db_transaction.atomic():
                access_request = GoldAPIAccessRequest.objects.create(
                    user=user,
                    status='pending_payment',
                    preferred_provider=preferred_provider,
                    user_notes=user_notes,
                    price_amount=price_amount,
                )
                
                wallet, _ = Wallet.objects.select_for_update().get_or_create(
                    user=user,
                    defaults={'balance': Decimal('0.00')}
                )
                
                transaction = Transaction.objects.create(
                    wallet=wallet,
                    transaction_type='gold_api_request',
                    amount=price_amount,
                    status='pending',
                    description=f'درخواست دریافت API طلا - #{access_request.id}'
                )
                
                access_request.transaction = transaction
                access_request.save(update_fields=['transaction'])
                
                payment_service = get_zarinpal_service()
                callback_url = request.build_absolute_uri(
                    f'/api/payments/callback/?transaction_id={transaction.id}'
                )
                amount_for_gateway = int(price_amount.quantize(Decimal('1')))
                payment_result = payment_service.create_payment_request(
                    amount=amount_for_gateway,
                    description=f'هزینه تامین API طلا برای کاربر {user.username}',
                    callback_url=callback_url,
                    email=user.email if user.email else None,
                    mobile=getattr(user.profile, 'phone_number', None) if hasattr(user, 'profile') else None
                )
                
                if payment_result['status'] == 'success':
                    transaction.zarinpal_authority = payment_result['authority']
                    transaction.save(update_fields=['zarinpal_authority'])
                    serializer = self.get_serializer(access_request)
                    data = serializer.data
                    data['payment_url'] = payment_result['start_pay_url']
                    return Response(data, status=status.HTTP_201_CREATED)
                
                transaction.status = 'failed'
                transaction.save(update_fields=['status'])
                access_request.status = 'cancelled'
                access_request.admin_notes = 'ایجاد پرداخت ناموفق بود'
                access_request.save(update_fields=['status', 'admin_notes'])
                
                return Response(
                    {'detail': payment_result.get('error', 'خطا در ایجاد درخواست پرداخت')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as exc:
            return Response(
                {'detail': f'خطا در ایجاد درخواست: {exc}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'ویرایش مستقیم درخواست مجاز نیست.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
    
    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        access_request = self.get_object()
        if access_request.user != request.user and not (request.user.is_staff or request.user.is_superuser):
            return Response({'detail': 'دسترسی مجاز نیست'}, status=status.HTTP_403_FORBIDDEN)
        
        if access_request.status != 'pending_payment':
            return Response({'detail': 'این درخواست قابل لغو نیست.'}, status=status.HTTP_400_BAD_REQUEST)
        
        access_request.status = 'cancelled'
        access_request.save(update_fields=['status'])
        
        if access_request.transaction and access_request.transaction.status == 'pending':
            access_request.transaction.status = 'cancelled'
            access_request.transaction.save(update_fields=['status'])
        
        return Response({'detail': 'درخواست لغو شد.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdminOrStaff])
    def assign(self, request, pk=None):
        access_request = self.get_object()
        if access_request.status not in ['awaiting_admin', 'completed']:
            return Response(
                {'detail': 'درخواست هنوز تایید پرداخت نشده یا قبلاً تکمیل شده است.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        provider = (request.data.get('provider') or '').strip()
        api_key = (request.data.get('api_key') or '').strip()
        notes = (request.data.get('admin_notes') or '').strip()
        is_active = request.data.get('is_active', True)
        
        if not provider or not api_key:
            return Response(
                {'detail': 'وارد کردن ارائه‌دهنده و کلید API الزامی است.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_access, _ = UserGoldAPIAccess.objects.get_or_create(
            user=access_request.user,
            defaults={'source': 'admin'}
        )
        allow_mt5_raw = request.data.get('allow_mt5_access', None)
        if allow_mt5_raw is None:
            allow_mt5_access = bool(user_access.allow_mt5_access)
        else:
            if isinstance(allow_mt5_raw, bool):
                allow_mt5_access = allow_mt5_raw
            else:
                allow_mt5_access = str(allow_mt5_raw).strip().lower() in ['1', 'true', 'yes', 'on']
        
        now = timezone.now()
        access_request.assigned_provider = provider
        access_request.assigned_api_key = api_key
        access_request.assigned_at = now
        access_request.assigned_by = request.user
        access_request.admin_notes = notes
        access_request.status = 'completed'
        access_request.save()
        
        user_access.provider = provider
        user_access.api_key = api_key
        user_access.notes = notes
        user_access.source = 'admin'
        user_access.assigned_by_admin = True
        user_access.allow_mt5_access = allow_mt5_access
        user_access.assigned_at = now
        user_access.is_active = bool(is_active)
        user_access.save()
        
        serializer = self.get_serializer(access_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


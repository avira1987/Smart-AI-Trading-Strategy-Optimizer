"""
Authentication views for phone-based OTP login
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from core.models import UserProfile, OTPCode, Device, SystemSettings, UserActivityLog
from .serializers import PhoneNumberSerializer, OTPVerificationSerializer, UserSerializer
from .sms_service import send_otp_sms
from .self_captcha import verify_captcha, get_client_ip
import logging
import os
import hashlib
import requests

logger = logging.getLogger(__name__)


class SendOTPView(APIView):
    """
    Send OTP code to phone number
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for this endpoint
    
    def post(self, request):
        # Verify self-managed CAPTCHA
        captcha_token = request.data.get('captcha_token', '')
        captcha_answer = request.data.get('captcha_answer')
        page_load_time = request.data.get('page_load_time')
        honeypot = request.data.get('website', '')  # Honeypot field
        
        # Convert page_load_time to float if it's a string
        if page_load_time and isinstance(page_load_time, str):
            try:
                page_load_time = float(page_load_time)
            except (ValueError, TypeError):
                page_load_time = None
        
        captcha_result = verify_captcha(
            token=captcha_token,
            answer=captcha_answer,
            page_load_time=page_load_time,
            honeypot=honeypot
        )
        
        if not captcha_result['success']:
            logger.warning(f"CAPTCHA verification failed: {captcha_result.get('message', 'Unknown error')}")
            return Response(
                {
                    'success': False,
                    'message': captcha_result.get('message', 'تایید امنیتی ناموفق بود. لطفا دوباره تلاش کنید.'),
                    'error': captcha_result.get('error', 'captcha_failed')
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PhoneNumberSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone_number = serializer.validated_data['phone_number']
        
        try:
            # Create or get OTP
            otp = OTPCode.create_otp(phone_number)
            
            # Send SMS
            sms_result = send_otp_sms(phone_number, otp.code)
            
            if not sms_result['success']:
                logger.error(f"Failed to send SMS to {phone_number}: {sms_result['message']}")
                return Response(
                    {
                        'success': False,
                        'message': 'خطا در ارسال پیامک. لطفا دوباره تلاش کنید.',
                        'error': sms_result['message']
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            logger.info(f"OTP sent successfully to {phone_number}")
            
            return Response({
                'success': True,
                'message': 'کد یکبار مصرف به شماره موبایل شما ارسال شد',
                'expires_in': 300  # 5 minutes in seconds
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error sending OTP: {e}")
            return Response(
                {
                    'success': False,
                    'message': 'خطا در ارسال کد. لطفا دوباره تلاش کنید.',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyOTPView(APIView):
    """
    Verify OTP code and login user
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for this endpoint
    
    def post(self, request):
        """
        Verify OTP code and login user
        """
        # Verify self-managed CAPTCHA (optional for OTP verification, but recommended)
        captcha_token = request.data.get('captcha_token', '')
        captcha_answer = request.data.get('captcha_answer')
        page_load_time = request.data.get('page_load_time')
        honeypot = request.data.get('website', '')
        
        if captcha_token:
            if page_load_time and isinstance(page_load_time, str):
                try:
                    page_load_time = float(page_load_time)
                except (ValueError, TypeError):
                    page_load_time = None
            
            captcha_result = verify_captcha(
                token=captcha_token,
                answer=captcha_answer,
                page_load_time=page_load_time,
                honeypot=honeypot
            )
            
            if not captcha_result['success']:
                logger.warning(f"CAPTCHA verification failed for OTP verification")
                return Response(
                    {
                        'success': False,
                        'message': captcha_result.get('message', 'تایید امنیتی ناموفق بود. لطفا دوباره تلاش کنید.'),
                        'error': captcha_result.get('error', 'captcha_failed')
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = OTPVerificationSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        
        try:
            # Find valid OTP
            otp = OTPCode.objects.filter(
                phone_number=phone_number,
                code=otp_code,
                is_used=False
            ).order_by('-created_at').first()
            
            if not otp:
                return Response(
                    {
                        'success': False,
                        'message': 'کد وارد شده اشتباه است'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if OTP is expired
            if not otp.is_valid():
                otp.increment_attempts()
                return Response(
                    {
                        'success': False,
                        'message': 'کد منقضی شده است. لطفا کد جدید درخواست کنید'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check attempts (max 5 attempts)
            if otp.attempts >= 5:
                otp.mark_as_used()
                return Response(
                    {
                        'success': False,
                        'message': 'تعداد تلاش‌های ناموفق بیش از حد مجاز است. لطفا کد جدید درخواست کنید'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark OTP as used
            otp.mark_as_used()
            
            # Get or create user
            user, created = User.objects.get_or_create(
                username=phone_number,
                defaults={
                    'email': f'{phone_number}@example.com',
                    'first_name': '',
                    'last_name': ''
                }
            )
            
            # Get or create user profile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'phone_number': phone_number}
            )
            
            if profile_created or profile.phone_number != phone_number:
                profile.phone_number = phone_number
                profile.save()
            
            # Give registration bonus to new users
            if created:
                from core.models import Wallet, SystemSettings, Transaction
                from decimal import Decimal
                wallet, wallet_created = Wallet.objects.get_or_create(user=user)
                if wallet_created:
                    # Get registration bonus from system settings
                    settings = SystemSettings.load()
                    bonus_amount = Decimal(str(settings.registration_bonus))
                    wallet.charge(float(bonus_amount))
                    # Create transaction record
                    Transaction.objects.create(
                        wallet=wallet,
                        transaction_type='charge',
                        amount=bonus_amount,
                        status='completed',
                        description=f'هدیه ثبت‌نام ({bonus_amount:,.0f} تومان)',
                        completed_at=timezone.now()
                    )
                    logger.info(f"Registration bonus of {bonus_amount} Toman given to new user {user.username}")
            
            # Generate device ID
            device_id = Device.generate_device_id(request)
            device_name = request.META.get('HTTP_USER_AGENT', 'Unknown Device')[:255]
            
            # Get or create device
            device, device_created = Device.objects.get_or_create(
                user=user,
                device_id=device_id,
                defaults={'device_name': device_name}
            )
            
            # Update device last login
            device.update_last_login()
            device.is_active = True
            device.save()
            
            # Login user
            login(request, user)
            
            # Serialize user data
            user_serializer = UserSerializer(user)
            
            logger.info(f"User {user.username} logged in successfully from device {device_id[:20]}")
            
            # Check if user is new (just created)
            is_new_user = created
            
            return Response({
                'success': True,
                'message': 'ورود با موفقیت انجام شد',
                'user': user_serializer.data,
                'device_id': device_id,
                'is_new_device': device_created,
                'is_new_user': is_new_user
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return Response(
                {
                    'success': False,
                    'message': 'خطا در تایید کد. لطفا دوباره تلاش کنید.',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_auth(request):
    """
    Check if user is authenticated and device is valid
    """
    user = request.user
    
    try:
        # Get device ID from request
        device_id = Device.generate_device_id(request)
        
        # Check if device exists for this user
        device = Device.objects.filter(
            user=user,
            device_id=device_id,
            is_active=True
        ).first()
        
        if not device:
            # Device not found - user needs to login again
            return Response(
                {
                    'success': False,
                    'authenticated': False,
                    'message': 'دستگاه شما شناسایی نشد. لطفا مجددا وارد شوید'
                },
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Update last login
        device.update_last_login()
        
        # Serialize user data
        user_serializer = UserSerializer(user)
        
        return Response({
            'success': True,
            'authenticated': True,
            'user': user_serializer.data,
            'device_id': device_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking auth: {e}")
        return Response(
            {
                'success': False,
                'authenticated': False,
                'message': 'خطا در بررسی وضعیت ورود',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Get CSRF token for frontend
    """
    token = get_token(request)
    return Response({'csrfToken': token})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_profile_completion(request):
    """
    Check if user profile is complete (has real email and phone number)
    """
    user = request.user
    
    try:
        # Check if email is valid (not placeholder like phone@example.com)
        email_valid = user.email and not user.email.endswith('@example.com')
        
        # Check if phone number is valid (not placeholder like google_xxx)
        phone_valid = False
        try:
            profile = getattr(user, 'profile', None)
            if profile:
                phone_number = getattr(profile, 'phone_number', None)
                if phone_number:
                    # Valid phone should start with 09 and be 11 digits
                    phone_valid = phone_number.startswith('09') and len(phone_number) == 11 and phone_number.isdigit()
        except Exception as profile_error:
            logger.warning(f"Error accessing user profile: {profile_error}")
            phone_valid = False
        
        is_complete = email_valid and phone_valid
        
        # Get preferred symbol from profile
        preferred_symbol = 'XAUUSD'  # default
        try:
            profile = getattr(user, 'profile', None)
            if profile and hasattr(profile, 'preferred_symbol') and profile.preferred_symbol:
                preferred_symbol = profile.preferred_symbol
        except Exception:
            pass
        
        return Response({
            'success': True,
            'is_complete': is_complete,
            'has_valid_email': email_valid,
            'has_valid_phone': phone_valid,
            'preferred_symbol': preferred_symbol
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking profile completion: {e}")
        return Response(
            {
                'success': False,
                'message': 'خطا در بررسی پروفایل',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Update user profile (email and phone number)
    """
    user = request.user
    
    try:
        email = request.data.get('email', '').strip()
        phone_number = request.data.get('phone_number', '').strip()
        preferred_symbol = request.data.get('preferred_symbol', '').strip()
        nickname_raw = request.data.get('nickname', None)
        nickname = None
        if nickname_raw is not None:
            nickname = nickname_raw.strip()
            if not nickname:
                errors = {'nickname': 'نیک‌نیم نمی‌تواند خالی باشد'}
                return Response({
                    'success': False,
                    'message': 'خطا در به‌روزرسانی پروفایل',
                    'errors': errors
                }, status=status.HTTP_400_BAD_REQUEST)
            if len(nickname) < 3:
                return Response({
                    'success': False,
                    'message': 'نیک‌نیم باید حداقل ۳ کاراکتر باشد',
                    'errors': {'nickname': 'نیک‌نیم باید حداقل ۳ کاراکتر باشد'}
                }, status=status.HTTP_400_BAD_REQUEST)
            if UserProfile.objects.filter(nickname__iexact=nickname).exclude(user=user).exists():
                return Response({
                    'success': False,
                    'message': 'این نیک‌نیم قبلاً استفاده شده است',
                    'errors': {'nickname': 'این نیک‌نیم قبلاً استفاده شده است'}
                }, status=status.HTTP_400_BAD_REQUEST)
        
        errors = {}
        
        # Validate email
        if email:
            if '@' not in email or '.' not in email.split('@')[1]:
                errors['email'] = 'ایمیل معتبر نیست'
            else:
                # Check if email is already used by another user
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    errors['email'] = 'این ایمیل قبلا استفاده شده است'
                else:
                    user.email = email
                    user.save()
        
        # Get or create profile
        profile = getattr(user, 'profile', None)
        if not profile:
            # Only create profile if we have a phone number (required field)
            if phone_number:
                if not phone_number.startswith('09') or len(phone_number) != 11 or not phone_number.isdigit():
                    errors['phone_number'] = 'شماره موبایل باید 11 رقم و با 09 شروع شود'
                else:
                    if UserProfile.objects.filter(phone_number=phone_number).exists():
                        errors['phone_number'] = 'این شماره موبایل قبلا استفاده شده است'
                    else:
                        # Create profile with phone number and preferred symbol
                        profile = UserProfile.objects.create(
                            user=user,
                            phone_number=phone_number,
                        preferred_symbol=preferred_symbol if preferred_symbol else 'XAUUSD',
                        nickname=nickname if nickname else None
                        )
            # If no phone number and no profile exists, we can't create profile yet
            # The symbol will be saved when profile is created with phone number
        else:
            # Validate and update phone number
            if phone_number:
                if not phone_number.startswith('09') or len(phone_number) != 11 or not phone_number.isdigit():
                    errors['phone_number'] = 'شماره موبایل باید 11 رقم و با 09 شروع شود'
                else:
                    if UserProfile.objects.filter(phone_number=phone_number).exclude(user=user).exists():
                        errors['phone_number'] = 'این شماره موبایل قبلا استفاده شده است'
                    else:
                        profile.phone_number = phone_number
            
            # Update preferred symbol if provided
            if preferred_symbol:
                profile.preferred_symbol = preferred_symbol

            if nickname is not None:
                profile.nickname = nickname
            
            profile.save()
        if nickname is not None and not profile:
            # If user provided nickname but profile creation wasn't possible (e.g. missing phone)
            errors['nickname'] = 'برای ثبت نیک‌نیم ابتدا باید شماره موبایل معتبر ثبت شود'
        
        if errors:
            return Response({
                'success': False,
                'message': 'خطا در به‌روزرسانی پروفایل',
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Serialize updated user
        user_serializer = UserSerializer(user)
        
        logger.info(f"User {user.username} updated profile")
        
        return Response({
            'success': True,
            'message': 'پروفایل با موفقیت به‌روزرسانی شد',
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return Response(
            {
                'success': False,
                'message': 'خطا در به‌روزرسانی پروفایل',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user and optionally deactivate device
    """
    user = request.user
    
    try:
        # Get device ID
        device_id = Device.generate_device_id(request)
        
        # Deactivate device (optional - comment out if you want to keep device active)
        Device.objects.filter(
            user=user,
            device_id=device_id
        ).update(is_active=False)
        
        # Logout user
        from django.contrib.auth import logout
        logout(request)
        
        logger.info(f"User {user.username} logged out from device {device_id[:20]}")
        
        return Response({
            'success': True,
            'message': 'خروج با موفقیت انجام شد'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error logging out: {e}")
        return Response(
            {
                'success': False,
                'message': 'خطا در خروج',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def check_ip_location(request):
    """
    Check IP location to determine if it's from Iran
    """
    try:
        # Get client IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Use ipapi.co to check IP location
        try:
            response = requests.get(f'https://ipapi.co/{ip}/json/', timeout=5)
            response.raise_for_status()
            data = response.json()
            
            country_code = data.get('country_code', '')
            is_iran = country_code == 'IR'
            
            return Response({
                'success': True,
                'is_iran': is_iran,
                'country_code': country_code,
                'country_name': data.get('country_name', ''),
                'ip': ip
            }, status=status.HTTP_200_OK)
        except requests.RequestException as e:
            logger.error(f"Error fetching IP location: {e}")
            # Fallback: try to get country from request headers
            return Response({
                'success': False,
                'message': 'خطا در بررسی موقعیت IP',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        logger.error(f"Error in check_ip_location: {e}")
        return Response({
            'success': False,
            'message': 'خطا در بررسی IP',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_activity_logs(request):
    """
    دریافت لاگ فعالیت‌های کاربر
    """
    try:
        user = request.user
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # دریافت لاگ‌های کاربر
        logs = UserActivityLog.objects.filter(user=user).order_by('-created_at')[offset:offset+limit]
        
        # تبدیل به فرمت JSON
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'action_type': log.action_type,
                'action_type_display': log.get_action_type_display(),
                'action_description': log.action_description,
                'metadata': log.metadata,
                'created_at': log.created_at.isoformat(),
            })
        
        total_count = UserActivityLog.objects.filter(user=user).count()
        
        return Response({
            'success': True,
            'logs': logs_data,
            'total_count': total_count,
            'limit': limit,
            'offset': offset,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting user activity logs: {e}")
        return Response({
            'success': False,
            'message': 'خطا در دریافت لاگ فعالیت‌ها',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
from core.models import UserProfile, OTPCode, Device, SystemSettings
from .serializers import PhoneNumberSerializer, OTPVerificationSerializer, UserSerializer
from .sms_service import send_otp_sms
import logging
import os
import hashlib
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests

logger = logging.getLogger(__name__)


class SendOTPView(APIView):
    """
    Send OTP code to phone number
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for this endpoint
    
    def post(self, request):
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
            
            return Response({
                'success': True,
                'message': 'ورود با موفقیت انجام شد',
                'user': user_serializer.data,
                'device_id': device_id,
                'is_new_device': device_created
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


class GoogleOAuthView(APIView):
    """
    Authenticate user with Google OAuth ID token
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication for this endpoint
    
    def post(self, request):
        """
        Verify Google ID token and login/create user
        """
        # بررسی اینکه Google Auth فعال است یا نه
        settings = SystemSettings.load()
        if not settings.google_auth_enabled:
            return Response(
                {
                    'success': False,
                    'message': 'ورود با گوگل در حال حاضر غیرفعال است'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        id_token_string = request.data.get('id_token')
        
        if not id_token_string:
            return Response(
                {
                    'success': False,
                    'message': 'توکن گوگل ارسال نشده است'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get Google Client ID from environment
            GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
            
            if not GOOGLE_CLIENT_ID:
                logger.error("GOOGLE_CLIENT_ID not configured in environment")
                return Response(
                    {
                        'success': False,
                        'message': 'تنظیمات احراز هویت گوگل کامل نیست'
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Verify the token
            try:
                idinfo = id_token.verify_oauth2_token(
                    id_token_string, 
                    google_requests.Request(), 
                    GOOGLE_CLIENT_ID
                )
            except ValueError as e:
                logger.error(f"Invalid Google token: {e}")
                return Response(
                    {
                        'success': False,
                        'message': 'توکن گوگل نامعتبر است'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract user information
            google_id = idinfo.get('sub')
            email = idinfo.get('email')
            name = idinfo.get('name', '')
            given_name = idinfo.get('given_name', '')
            family_name = idinfo.get('family_name', '')
            picture = idinfo.get('picture', '')
            
            if not email:
                return Response(
                    {
                        'success': False,
                        'message': 'ایمیل از گوگل دریافت نشد'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create user
            # Use email as username, or create unique username if email already exists
            username = email.split('@')[0]
            base_username = username
            
            # Ensure unique username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': given_name or name.split()[0] if name else '',
                    'last_name': family_name or ' '.join(name.split()[1:]) if name and len(name.split()) > 1 else '',
                }
            )
            
            # Update user info if needed
            if not created:
                if given_name and not user.first_name:
                    user.first_name = given_name
                if family_name and not user.last_name:
                    user.last_name = family_name
                if user.username != username and not User.objects.filter(username=username).exists():
                    user.username = username
                user.save()
            
            # Get or create user profile
            # For Google users, use a unique placeholder since phone_number is unique
            # Format: google_{email_hash} to ensure uniqueness
            email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
            google_phone_placeholder = f'google_{email_hash}'
            
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'phone_number': google_phone_placeholder}
            )
            
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
            
            logger.info(f"User {user.username} logged in via Google OAuth from device {device_id[:20]}")
            
            return Response({
                'success': True,
                'message': 'ورود با گوگل با موفقیت انجام شد',
                'user': user_serializer.data,
                'device_id': device_id,
                'is_new_user': created,
                'is_new_device': device_created
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error verifying Google OAuth: {e}")
            return Response(
                {
                    'success': False,
                    'message': 'خطا در ورود با گوگل. لطفا دوباره تلاش کنید.',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
        profile = getattr(user, 'profile', None)
        phone_valid = False
        if profile:
            phone_number = profile.phone_number
            # Valid phone should start with 09 and be 11 digits
            phone_valid = phone_number and phone_number.startswith('09') and len(phone_number) == 11 and phone_number.isdigit()
        
        is_complete = email_valid and phone_valid
        
        return Response({
            'success': True,
            'is_complete': is_complete,
            'has_valid_email': email_valid,
            'has_valid_phone': phone_valid
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
        
        # Validate phone number
        if phone_number:
            if not phone_number.startswith('09') or len(phone_number) != 11 or not phone_number.isdigit():
                errors['phone_number'] = 'شماره موبایل باید 11 رقم و با 09 شروع شود'
            else:
                # Check if phone is already used by another user
                profile = getattr(user, 'profile', None)
                if not profile:
                    profile = UserProfile.objects.create(user=user, phone_number=phone_number)
                else:
                    if UserProfile.objects.filter(phone_number=phone_number).exclude(user=user).exists():
                        errors['phone_number'] = 'این شماره موبایل قبلا استفاده شده است'
                    else:
                        profile.phone_number = phone_number
                        profile.save()
        
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
@permission_classes([AllowAny])
def check_google_auth_status(request):
    """
    بررسی وضعیت فعال/غیرفعال بودن ورود با گوگل
    """
    try:
        settings = SystemSettings.load()
        return Response({
            'success': True,
            'google_auth_enabled': settings.google_auth_enabled
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error checking Google Auth status: {e}")
        return Response(
            {
                'success': False,
                'message': 'خطا در بررسی وضعیت',
                'google_auth_enabled': False
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


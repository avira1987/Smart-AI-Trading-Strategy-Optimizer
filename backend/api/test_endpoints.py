"""
Test endpoints for debugging SMS and Google OAuth
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .sms_service import send_otp_sms, get_kavenegar_api_key, get_kavenegar_sender, SMS_ENABLED
import logging
import os

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def test_sms(request):
    """
    Test SMS sending functionality
    """
    phone_number = request.data.get('phone_number')
    
    if not phone_number:
        return Response(
            {
                'success': False,
                'message': 'شماره موبایل ارسال نشده است'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Test OTP code
    test_otp = '123456'
    
    try:
        result = send_otp_sms(phone_number, test_otp)
        
        return Response(
            {
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'test_otp': test_otp,
                'phone_number': phone_number,
                'details': result
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error testing SMS: {e}")
        return Response(
            {
                'success': False,
                'message': f'خطا در تست SMS: {str(e)}',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def test_google_oauth_config(request):
    """
    Test Google OAuth configuration
    """
    import os
    
    google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
    frontend_client_id = request.GET.get('frontend_client_id', '')
    
    config_status = {
        'backend_google_client_id': '✅ تنظیم شده' if google_client_id else '❌ تنظیم نشده',
        'frontend_client_id_received': '✅ دریافت شد' if frontend_client_id else '❌ دریافت نشد',
        'current_origin': request.META.get('HTTP_ORIGIN', ''),
        'current_host': request.get_host(),
    }
    
    # Check if origins match
    if frontend_client_id:
        config_status['client_ids_match'] = '✅ مطابقت دارد' if google_client_id == frontend_client_id else '❌ مطابقت ندارد'
    
    return Response(
        {
            'success': True,
            'message': 'وضعیت تنظیمات Google OAuth',
            'config': config_status,
            'recommendations': [
                'مطمئن شوید که GOOGLE_CLIENT_ID در فایل .env تنظیم شده است',
                'مطمئن شوید که VITE_GOOGLE_CLIENT_ID در frontend/.env.local تنظیم شده است',
                f'Origin فعلی ({config_status["current_origin"]}) باید در Google Cloud Console ثبت شود',
            ]
        },
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def test_kavenegar_config(request):
    """
    Test Kavenegar SMS configuration and API key status
    """
    try:
        # Get API key from different sources
        api_key_env = os.environ.get('KAVENEGAR_API_KEY', '')
        api_key_dynamic = get_kavenegar_api_key()
        sender = get_kavenegar_sender()
        
        # Check database configuration
        db_config = None
        try:
            from core.models import APIConfiguration
            api_config = APIConfiguration.objects.filter(
                provider='kavenegar',
                is_active=True,
                user__isnull=True,
            ).first()
            if api_config:
                db_config = {
                    'exists': True,
                    'has_api_key': bool(api_config.api_key),
                    'api_key_length': len(api_config.api_key) if api_config.api_key else 0,
                    'is_active': api_config.is_active
                }
            else:
                db_config = {'exists': False}
        except Exception as e:
            db_config = {'error': str(e)}
        
        config_status = {
            'sms_enabled': SMS_ENABLED,
            'api_key_from_env': '✅ تنظیم شده' if api_key_env else '❌ تنظیم نشده',
            'api_key_from_dynamic': '✅ تنظیم شده' if api_key_dynamic else '❌ تنظیم نشده',
            'api_key_length_env': len(api_key_env) if api_key_env else 0,
            'api_key_length_dynamic': len(api_key_dynamic) if api_key_dynamic else 0,
            'sender_configured': '✅ تنظیم شده' if sender else '❌ تنظیم نشده (استفاده از پیش‌فرض)',
            'sender_value': sender if sender else None,
            'database_config': db_config,
            'api_key_matches': api_key_env == api_key_dynamic if (api_key_env and api_key_dynamic) else False
        }
        
        return Response(
            {
                'success': True,
                'message': 'وضعیت تنظیمات Kavenegar SMS',
                'config': config_status,
                'recommendations': [
                    'اگر API key تنظیم نشده است، آن را در فایل .env یا در تنظیمات API وارد کنید',
                    'اگر sender تنظیم نشده است، می‌توانید آن را خالی بگذارید تا از پیش‌فرض استفاده شود',
                    'مطمئن شوید که ماژول kavenegar نصب شده است: pip install kavenegar',
                ]
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error checking Kavenegar config: {e}")
        return Response(
            {
                'success': False,
                'message': f'خطا در بررسی تنظیمات: {str(e)}',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def emergency_set_kavenegar_api_key(request):
    """
    Emergency endpoint to set Kavenegar API key (for recovery when SMS is not working)
    WARNING: This should be disabled in production or protected with additional security
    """
    try:
        api_key = request.data.get('api_key', '').strip()
        secret_token = request.data.get('secret_token', '')
        
        # Simple security check - in production, use a more secure method
        # For now, we'll use a simple token check
        expected_token = os.environ.get('EMERGENCY_API_KEY_TOKEN', 'EMERGENCY_RECOVERY_2024')
        
        if secret_token != expected_token:
            logger.warning("Unauthorized attempt to set API key")
            return Response(
                {
                    'success': False,
                    'message': 'دسترسی غیرمجاز. لطفا از management command استفاده کنید.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not api_key:
            return Response(
                {
                    'success': False,
                    'message': 'API key ارسال نشده است'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set API key in database
        from core.models import APIConfiguration
        api_config, created = APIConfiguration.objects.get_or_create(
            provider='kavenegar',
            user=None,
            defaults={
                'api_key': api_key,
                'is_active': True
            }
        )
        
        if not created:
            api_config.api_key = api_key
            api_config.is_active = True
            api_config.save()
        
        logger.info(f"Kavenegar API key {'created' if created else 'updated'} via emergency endpoint")
        
        return Response(
            {
                'success': True,
                'message': f'API key با موفقیت {"ایجاد" if created else "به‌روزرسانی"} شد',
                'created': created
            },
            status=status.HTTP_200_OK
        )
        
    except Exception as e:
        logger.error(f"Error setting API key via emergency endpoint: {e}")
        return Response(
            {
                'success': False,
                'message': f'خطا در تنظیم API key: {str(e)}',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def test_backend_status(request):
    """
    Test backend status and configuration
    """
    import os
    import socket
    
    # Get local IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Get all network interfaces
    import subprocess
    network_ips = []
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=2)
            for line in result.stdout.split('\n'):
                if 'IPv4' in line or 'IP Address' in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip.startswith(('192.168.', '10.', '172.')):
                        network_ips.append(ip)
        else:  # Linux/Mac
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                network_ips = result.stdout.strip().split()
    except Exception:
        pass
    
    config = {
        'backend_running': True,
        'hostname': hostname,
        'local_ip': local_ip,
        'network_ips': network_ips,
        'current_host': request.get_host(),
        'current_origin': request.META.get('HTTP_ORIGIN', ''),
        'google_client_id_configured': bool(os.environ.get('GOOGLE_CLIENT_ID', '')),
        'kavenegar_api_key_configured': bool(os.environ.get('KAVENEGAR_API_KEY', '')),
        'kavenegar_sender_configured': bool(os.environ.get('KAVENEGAR_SENDER', '')),
    }
    
    return Response(
        {
            'success': True,
            'message': 'وضعیت Backend',
            'config': config,
            'timestamp': str(__import__('django.utils.timezone').timezone.now())
        },
        status=status.HTTP_200_OK
    )


"""
Test endpoints for debugging SMS and Google OAuth
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .sms_service import send_otp_sms
import logging

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


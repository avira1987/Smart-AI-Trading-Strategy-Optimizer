"""
API views for self-managed CAPTCHA
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .self_captcha import generate_captcha_token
import logging

logger = logging.getLogger(__name__)


class GetCaptchaView(APIView):
    """
    Get a new CAPTCHA challenge
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        """
        Generate and return a new CAPTCHA challenge
        """
        action = request.data.get('action', 'default')
        
        try:
            captcha_data = generate_captcha_token(action)
            
            return Response({
                'success': True,
                'token': captcha_data['token'],
                'challenge': captcha_data['challenge'],
                'type': captcha_data['type']
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating CAPTCHA: {e}")
            return Response(
                {
                    'success': False,
                    'message': 'خطا در تولید CAPTCHA',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


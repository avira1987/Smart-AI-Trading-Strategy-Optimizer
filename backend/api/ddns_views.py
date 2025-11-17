"""
DDNS Management Views (Admin only)
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminOrStaff
from core.models import DDNSConfiguration
from .serializers import DDNSConfigurationSerializer
from .ddns_service import update_ddns, test_ddns_config, get_public_ip
import logging

logger = logging.getLogger(__name__)


class DDNSConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing DDNS configurations (Admin only)
    """
    queryset = DDNSConfiguration.objects.all()
    serializer_class = DDNSConfigurationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrStaff]
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        Test DDNS configuration
        """
        config = self.get_object()
        result = test_ddns_config(config.id)
        
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def update_now(self, request):
        """
        Manually trigger DDNS update for all active configurations
        """
        try:
            update_ddns()
            return Response(
                {
                    'success': True,
                    'message': 'به‌روزرسانی DDNS انجام شد'
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            logger.error(f"Error updating DDNS: {e}")
            return Response(
                {
                    'success': False,
                    'message': f'خطا در به‌روزرسانی: {str(e)}'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def get_public_ip(self, request):
        """
        Get current public IP address
        """
        ip = get_public_ip()
        if ip:
            return Response(
                {
                    'success': True,
                    'ip': ip
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    'success': False,
                    'message': 'نمی‌توان IP عمومی را دریافت کرد'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        """
        When creating a new DDNS config, disable others if this one is enabled
        """
        instance = serializer.save()
        if instance.is_enabled:
            # Disable other configurations
            DDNSConfiguration.objects.filter(is_enabled=True).exclude(id=instance.id).update(is_enabled=False)
    
    def perform_update(self, serializer):
        """
        When updating, disable others if this one is being enabled
        """
        instance = serializer.save()
        if instance.is_enabled:
            # Disable other configurations
            DDNSConfiguration.objects.filter(is_enabled=True).exclude(id=instance.id).update(is_enabled=False)


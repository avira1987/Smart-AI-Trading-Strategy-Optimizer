"""
Custom permissions for device-based authentication
"""
from rest_framework import permissions
from core.models import Device
import logging

logger = logging.getLogger(__name__)


class IsAuthenticatedDevice(permissions.BasePermission):
    """
    Permission class that checks if user is authenticated AND device is valid
    """
    
    def has_permission(self, request, view):
        # First check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            # Generate device ID from request
            device_id = Device.generate_device_id(request)
            
            # Check if device exists and is active
            device = Device.objects.filter(
                user=request.user,
                device_id=device_id,
                is_active=True
            ).first()
            
            if not device:
                logger.warning(f"Device {device_id[:20]} not found for user {request.user.username}")
                return False
            
            # Update last login time
            device.update_last_login()
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking device permission: {e}")
            return False


class IsAdminOrStaff(permissions.BasePermission):
    """
    Permission class that checks if user is admin or staff
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)

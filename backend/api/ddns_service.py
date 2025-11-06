"""
DDNS Service for updating dynamic DNS records
"""
import logging
import requests
import socket
from django.utils import timezone
from datetime import timedelta
from core.models import DDNSConfiguration

logger = logging.getLogger(__name__)


def get_public_ip():
    """
    Get the current public IP address
    """
    try:
        # Try multiple services for reliability
        services = [
            'https://api.ipify.org?format=json',
            'https://api.myip.com',
            'https://ifconfig.me/ip',
            'https://icanhazip.com',
        ]
        
        for service in services:
            try:
                if 'json' in service:
                    response = requests.get(service, timeout=5)
                    data = response.json()
                    ip = data.get('ip') or data.get('query')
                else:
                    response = requests.get(service, timeout=5)
                    ip = response.text.strip()
                
                if ip and _is_valid_ip(ip):
                    logger.info(f"Public IP obtained: {ip} from {service}")
                    return ip
            except Exception as e:
                logger.debug(f"Failed to get IP from {service}: {e}")
                continue
        
        logger.error("Failed to get public IP from all services")
        return None
    except Exception as e:
        logger.error(f"Error getting public IP: {e}")
        return None


def _is_valid_ip(ip):
    """Validate IP address format"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except socket.error:
            return False


def update_ddns():
    """
    Update DDNS for all active configurations
    """
    active_configs = DDNSConfiguration.objects.filter(is_enabled=True)
    
    if not active_configs.exists():
        logger.debug("No active DDNS configurations found")
        return
    
    current_ip = get_public_ip()
    if not current_ip:
        logger.error("Could not get public IP, skipping DDNS update")
        return
    
    for config in active_configs:
        try:
            # Check if update is needed (IP changed or interval passed)
            needs_update = False
            if not config.last_ip or config.last_ip != current_ip:
                needs_update = True
                logger.info(f"IP changed from {config.last_ip} to {current_ip}")
            
            if not needs_update and config.last_update:
                next_update = config.last_update + timedelta(minutes=config.update_interval_minutes)
                if timezone.now() > next_update:
                    needs_update = True
                    logger.info(f"Update interval passed for {config.domain}")
            
            if not needs_update:
                logger.debug(f"Skipping update for {config.domain} - no change needed")
                continue
            
            # Get update URL
            update_url = config.get_update_url()
            if not update_url:
                logger.error(f"No update URL for provider {config.provider}")
                continue
            
            # Add IP to URL if needed
            if 'ip=' in update_url or 'myip=' in update_url:
                if 'ip=' in update_url:
                    update_url = update_url.replace('ip=', f'ip={current_ip}')
                if 'myip=' in update_url:
                    update_url = update_url.replace('myip=', f'myip={current_ip}')
            elif config.provider not in ['noip', 'freedns']:
                # Most providers accept IP as parameter
                separator = '&' if '?' in update_url else '?'
                update_url = f"{update_url}{separator}ip={current_ip}"
            
            # Make update request
            logger.info(f"Updating DDNS for {config.domain} via {update_url[:50]}...")
            response = requests.get(update_url, timeout=10)
            
            # Check response
            response_text = response.text.strip().lower()
            
            if response.status_code == 200:
                # Check for success indicators
                success_indicators = ['ok', 'good', 'nochg', 'updated', 'success']
                if any(indicator in response_text for indicator in success_indicators):
                    config.last_update = timezone.now()
                    config.last_ip = current_ip
                    config.save()
                    logger.info(f"✅ DDNS updated successfully for {config.domain}: {current_ip}")
                else:
                    logger.warning(f"⚠️ DDNS update response unclear for {config.domain}: {response_text}")
            else:
                logger.error(f"❌ DDNS update failed for {config.domain}: HTTP {response.status_code} - {response_text}")
                
        except Exception as e:
            logger.error(f"❌ Error updating DDNS for {config.domain}: {e}")


def test_ddns_config(config_id):
    """
    Test a DDNS configuration
    """
    try:
        config = DDNSConfiguration.objects.get(id=config_id)
        
        current_ip = get_public_ip()
        if not current_ip:
            return {
                'success': False,
                'message': 'نمی‌توان IP عمومی را دریافت کرد'
            }
        
        update_url = config.get_update_url()
        if not update_url:
            return {
                'success': False,
                'message': 'URL به‌روزرسانی معتبر نیست'
            }
        
        # Add IP to URL
        if 'ip=' in update_url or 'myip=' in update_url:
            if 'ip=' in update_url:
                update_url = update_url.replace('ip=', f'ip={current_ip}')
            if 'myip=' in update_url:
                update_url = update_url.replace('myip=', f'myip={current_ip}')
        else:
            separator = '&' if '?' in update_url else '?'
            update_url = f"{update_url}{separator}ip={current_ip}"
        
        # Make test request
        response = requests.get(update_url, timeout=10)
        response_text = response.text.strip()
        
        if response.status_code == 200:
            success_indicators = ['ok', 'good', 'nochg', 'updated', 'success']
            if any(indicator in response_text.lower() for indicator in success_indicators):
                config.last_update = timezone.now()
                config.last_ip = current_ip
                config.save()
                return {
                    'success': True,
                    'message': f'تست موفق بود. IP: {current_ip}',
                    'response': response_text
                }
            else:
                return {
                    'success': False,
                    'message': f'پاسخ نامعتبر: {response_text}',
                    'response': response_text
                }
        else:
            return {
                'success': False,
                'message': f'خطا در به‌روزرسانی: HTTP {response.status_code}',
                'response': response_text
            }
            
    except DDNSConfiguration.DoesNotExist:
        return {
            'success': False,
            'message': 'تنظیمات DDNS یافت نشد'
        }
    except Exception as e:
        logger.error(f"Error testing DDNS: {e}")
        return {
            'success': False,
            'message': f'خطا: {str(e)}'
        }


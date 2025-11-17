"""
Management command to set Kavenegar API key in database

Usage:
    python manage.py set_kavenegar_api_key --api-key YOUR_API_KEY
    python manage.py set_kavenegar_api_key --api-key YOUR_API_KEY --sender 10008663
"""
from django.core.management.base import BaseCommand
from core.models import APIConfiguration


class Command(BaseCommand):
    help = 'Set Kavenegar API key in database'

    def add_arguments(self, parser):
        parser.add_argument('--api-key', type=str, help='Kavenegar API key', required=True)
        parser.add_argument('--sender', type=str, help='Kavenegar sender number (optional)')

    def handle(self, *args, **options):
        api_key = options.get('api_key')
        sender = options.get('sender')
        
        if not api_key:
            self.stdout.write(self.style.ERROR('API key is required'))
            return
        
        try:
            # Get or create API configuration
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
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ Kavenegar API key {"created" if created else "updated"} successfully'
            ))
            self.stdout.write(f'   Provider: kavenegar')
            self.stdout.write(f'   API Key: {api_key[:10]}...{api_key[-4:]} (hidden)')
            self.stdout.write(f'   Active: {api_config.is_active}')
            
            if sender:
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Note: Sender number should be set in .env file as KAVENEGAR_SENDER={sender}'
                ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error setting API key: {str(e)}'))


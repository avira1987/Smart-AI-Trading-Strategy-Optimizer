"""
Management command to update registration bonus amount in SystemSettings
"""
from django.core.management.base import BaseCommand
from core.models import SystemSettings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Update registration bonus amount in SystemSettings to 45000 Toman'

    def add_arguments(self, parser):
        parser.add_argument(
            '--amount',
            type=float,
            default=45000.0,
            help='Registration bonus amount in Toman (default: 45000)'
        )

    def handle(self, *args, **options):
        amount = options.get('amount', 45000.0)
        
        try:
            # Load or create SystemSettings (singleton pattern)
            settings = SystemSettings.load()
            
            # Get current value
            current_amount = float(settings.registration_bonus)
            
            # Update to new amount
            settings.registration_bonus = Decimal(str(amount))
            settings.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Registration bonus updated successfully!\n'
                    f'   Previous amount: {current_amount:,.0f} تومان\n'
                    f'   New amount: {amount:,.0f} تومان'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error updating registration bonus: {str(e)}')
            )


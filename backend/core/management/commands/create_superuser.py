"""
Management command to create a superuser using phone number
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile
import getpass


class Command(BaseCommand):
    help = 'Create a superuser with phone number'

    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, help='Phone number (e.g., 09123456789)')
        parser.add_argument('--username', type=str, help='Username (optional, defaults to phone number)')
        parser.add_argument('--email', type=str, help='Email address (optional)')
        parser.add_argument('--password', type=str, help='Password (optional, will prompt if not provided)')

    def handle(self, *args, **options):
        phone_number = options.get('phone')
        username = options.get('username')
        email = options.get('email')
        password = options.get('password')

        # Prompt for phone number if not provided
        if not phone_number:
            phone_number = input('Phone number (e.g., 09123456789): ').strip()
        
        # Validate phone number format
        if not phone_number.startswith('09') or len(phone_number) != 11 or not phone_number.isdigit():
            self.stdout.write(self.style.ERROR('Invalid phone number format. Must be 11 digits starting with 09'))
            return

        # Use phone number as username if not provided
        if not username:
            username = phone_number

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'User with username "{username}" already exists'))
            return

        # Prompt for password if not provided
        if not password:
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                return

        # Prompt for email if not provided
        if not email:
            email = input('Email address (optional): ').strip()
            if not email:
                email = f'{phone_number}@example.com'

        try:
            # Create superuser
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_staff=True,
                is_superuser=True
            )

            # Create or update user profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'phone_number': phone_number}
            )
            
            if not created:
                profile.phone_number = phone_number
                profile.save()

            self.stdout.write(self.style.SUCCESS(
                f'Superuser "{username}" created successfully with phone number "{phone_number}"'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {str(e)}'))


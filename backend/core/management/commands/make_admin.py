"""
Management command to make a user admin (staff and superuser)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Make a user admin by username or phone number'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to make admin')
        parser.add_argument('--phone', type=str, help='Phone number to make admin (e.g., 09035760718)')

    def handle(self, *args, **options):
        username = options.get('username')
        phone_number = options.get('phone')

        user = None

        # Find user by phone number if provided
        if phone_number:
            try:
                profile = UserProfile.objects.get(phone_number=phone_number)
                user = profile.user
                self.stdout.write(self.style.SUCCESS(f'Found user by phone number: {user.username}'))
            except UserProfile.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No user found with phone number: {phone_number}'))
                return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error finding user by phone: {str(e)}'))
                return

        # Find user by username if provided
        elif username:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(self.style.SUCCESS(f'Found user by username: {user.username}'))
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'No user found with username: {username}'))
                return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error finding user by username: {str(e)}'))
                return
        else:
            self.stdout.write(self.style.ERROR('Please provide either --username or --phone'))
            return

        # Make user admin
        try:
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            phone_info = ""
            if hasattr(user, 'profile') and user.profile.phone_number:
                phone_info = f" (Phone: {user.profile.phone_number})"
            
            self.stdout.write(self.style.SUCCESS(
                f'User "{user.username}"{phone_info} is now admin (staff and superuser)'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error making user admin: {str(e)}'))


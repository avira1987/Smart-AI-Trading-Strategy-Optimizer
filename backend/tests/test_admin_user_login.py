"""
Test for admin-created user login functionality
This test verifies that users created by admin can successfully login via OTP
"""
import os
import django
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import UserProfile, OTPCode, Wallet, SystemSettings, Transaction
from decimal import Decimal
from unittest.mock import patch


class AdminUserLoginTestCase(TestCase):
    """Test cases for admin-created user login"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Set up system settings
        SystemSettings.objects.create(
            registration_bonus=Decimal('10000.00')
        )
    
    def test_admin_create_user_and_login(self):
        """Test that admin can create a user and the user can login via OTP"""
        phone_number = '09123456789'
        
        # Step 1: Admin creates a new user via PUT request
        create_url = reverse('admin_user_management')
        create_response = self.client.put(
            create_url,
            {
                'phone_number': phone_number,
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'send_otp': True
            },
            format='json'
        )
        
        # Verify user was created
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(create_response.data['success'])
        self.assertEqual(create_response.data['user']['phone_number'], phone_number)
        self.assertEqual(create_response.data['user']['username'], phone_number)
        
        # Verify user exists in database
        user = User.objects.get(username=phone_number)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'test@example.com')
        
        # Verify profile exists
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone_number, phone_number)
        
        # Verify wallet was created
        wallet = Wallet.objects.get(user=user)
        self.assertIsNotNone(wallet)
        
        # Verify OTP was created
        otp = OTPCode.objects.filter(phone_number=phone_number, is_used=False).first()
        self.assertIsNotNone(otp, "OTP should be created when admin creates user")
        
        # Step 2: User tries to login with OTP
        # Get the OTP that was created when admin created the user
        # (or create a new one if send_otp was False)
        latest_otp = OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False
        ).order_by('-created_at').first()
        
        # If no OTP exists, create one manually for testing
        if not latest_otp:
            latest_otp = OTPCode.create_otp(phone_number)
        
        self.assertIsNotNone(latest_otp, "OTP should be available for login")
        otp_code = latest_otp.code
        
        # Step 3: Verify OTP and login (mock CAPTCHA verification)
        user_client = APIClient()
        with patch('api.auth_views.verify_captcha') as mock_captcha:
            mock_captcha.return_value = {'success': True, 'message': 'CAPTCHA verified'}
            verify_response = user_client.post(
                '/api/auth/verify-otp/',
                {
                    'phone_number': phone_number,
                    'otp_code': otp_code,
                    'captcha_token': 'test_token',
                    'captcha_answer': '5678',
                    'page_load_time': '2000'
                },
                format='json',
                HTTP_USER_AGENT='Mozilla/5.0 (Test)'
            )
        
        # Verify login was successful
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['success'])
        self.assertEqual(verify_response.data['user']['username'], phone_number)
        self.assertFalse(verify_response.data['is_new_user'], "User should not be marked as new since it was created by admin")
    
    def test_user_created_with_different_username_can_login(self):
        """Test that if a user exists with different username but same phone, they can still login"""
        phone_number = '09111111111'
        
        # Create a user manually (simulating admin creating user with custom username)
        # This simulates the old bug where username might not match phone_number
        custom_username = 'custom_user_123'
        user = User.objects.create_user(
            username=custom_username,
            email='custom@example.com',
            password=None
        )
        
        # Create profile with phone_number
        profile = UserProfile.objects.create(
            user=user,
            phone_number=phone_number
        )
        
        # Create wallet
        wallet = Wallet.objects.get_or_create(user=user)[0]
        
        # Now try to login with OTP
        # Create OTP directly for testing (bypassing CAPTCHA)
        from core.models import OTPCode
        latest_otp = OTPCode.create_otp(phone_number)
        otp_code = latest_otp.code
        
        # Verify OTP and login (mock CAPTCHA verification)
        user_client = APIClient()
        # Set user agent to avoid security middleware blocking
        user_client.defaults['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Test)'
        with patch('api.auth_views.verify_captcha') as mock_captcha:
            mock_captcha.return_value = {'success': True, 'message': 'CAPTCHA verified'}
            verify_response = user_client.post(
                '/api/auth/verify-otp/',
                {
                    'phone_number': phone_number,
                    'otp_code': otp_code,
                    'captcha_token': 'test_token',
                    'captcha_answer': '5678',
                    'page_load_time': '2000'
                },
                format='json',
                HTTP_USER_AGENT='Mozilla/5.0 (Test)'
            )
        
        # Verify login was successful
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['success'])
        
        # Verify username was updated to match phone_number
        user.refresh_from_db()
        self.assertEqual(user.username, phone_number, "Username should be updated to match phone number")
        
        # Verify we're logging in as the same user (not a new one)
        self.assertEqual(verify_response.data['user']['id'], user.id)
        self.assertFalse(verify_response.data['is_new_user'])
    
    def test_admin_cannot_create_duplicate_user(self):
        """Test that admin cannot create a user with existing phone number"""
        phone_number = '09222222222'
        
        # Create first user
        user1 = User.objects.create_user(
            username=phone_number,
            email='user1@example.com'
        )
        UserProfile.objects.create(user=user1, phone_number=phone_number)
        
        # Try to create duplicate user
        create_url = reverse('admin_user_management')
        create_response = self.client.put(
            create_url,
            {
                'phone_number': phone_number,
                'email': 'user2@example.com'
            },
            format='json'
        )
        
        # Should fail
        self.assertEqual(create_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', create_response.data)


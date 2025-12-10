"""
End-to-end test for new user registration and login
This simulates the real user flow
"""
import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from core.models import UserProfile, OTPCode, Wallet, SystemSettings, Transaction, Device
from decimal import Decimal
from unittest.mock import patch, MagicMock


class NewUserRegistrationTestCase(TestCase):
    """Test new user registration flow"""
    
    def setUp(self):
        """Set up test data"""
        # Create system settings
        SystemSettings.objects.create(
            registration_bonus=Decimal('45000.00')
        )
        
        # Create API client
        self.client = APIClient()
    
    def test_new_user_complete_registration_flow(self):
        """Test complete registration flow for a new user"""
        phone_number = '09129999999'
        
        # Step 1: Send OTP (simulate user requesting OTP)
        with patch('api.auth_views.verify_captcha') as mock_captcha, \
             patch('api.sms_service.send_otp_sms') as mock_sms:
            
            mock_captcha.return_value = {'success': True, 'message': 'CAPTCHA verified'}
            mock_sms.return_value = {'success': True, 'message': 'SMS sent'}
            
            send_otp_response = self.client.post(
                '/api/auth/send-otp/',
                {
                    'phone_number': phone_number,
                    'captcha_token': 'test_token',
                    'captcha_answer': '1234',
                    'page_load_time': '1000'
                },
                format='json',
                HTTP_USER_AGENT='Mozilla/5.0 (Test)'
            )
            
            # Verify OTP was sent
            self.assertEqual(send_otp_response.status_code, status.HTTP_200_OK)
            self.assertTrue(send_otp_response.data['success'])
        
        # Step 2: Get the OTP code that was created
        otp = OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False
        ).order_by('-created_at').first()
        
        self.assertIsNotNone(otp, "OTP should be created")
        otp_code = otp.code
        
        # Step 3: Verify OTP and complete registration
        with patch('api.auth_views.verify_captcha') as mock_captcha:
            mock_captcha.return_value = {'success': True, 'message': 'CAPTCHA verified'}
            
            verify_response = self.client.post(
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
            
            # Verify registration was successful
            self.assertEqual(verify_response.status_code, status.HTTP_200_OK, 
                           f"Response: {verify_response.data}")
            self.assertTrue(verify_response.data['success'], 
                          f"Response data: {verify_response.data}")
            self.assertTrue(verify_response.data['is_new_user'], 
                          "User should be marked as new")
            
            # Verify user was created
            user = User.objects.get(username=phone_number)
            self.assertIsNotNone(user)
            
            # Verify profile was created
            profile = UserProfile.objects.get(user=user)
            self.assertEqual(profile.phone_number, phone_number)
            
            # Verify wallet was created and bonus was given
            wallet = Wallet.objects.get(user=user)
            self.assertIsNotNone(wallet)
            self.assertGreater(wallet.balance, 0, "Registration bonus should be given")
            
            # Verify transaction was created
            transaction = Transaction.objects.filter(
                wallet=wallet,
                transaction_type='charge',
                description__icontains='هدیه ثبت‌نام'
            ).first()
            self.assertIsNotNone(transaction, "Registration bonus transaction should exist")
            
            # Verify device was created
            device = Device.objects.filter(user=user).first()
            self.assertIsNotNone(device, "Device should be created")
            self.assertTrue(device.is_active, "Device should be active")
    
    def test_new_user_registration_with_existing_phone_but_no_user(self):
        """Test case where phone number exists in OTP but user doesn't exist yet"""
        phone_number = '09128888888'
        
        # Create OTP directly (simulating SMS sent)
        otp = OTPCode.create_otp(phone_number)
        otp_code = otp.code
        
        # Verify OTP (this should create the user)
        with patch('api.auth_views.verify_captcha') as mock_captcha:
            mock_captcha.return_value = {'success': True, 'message': 'CAPTCHA verified'}
            
            verify_response = self.client.post(
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
            
            # Should succeed
            self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
            self.assertTrue(verify_response.data['success'])
            self.assertTrue(verify_response.data['is_new_user'])
            
            # User should be created
            user = User.objects.get(username=phone_number)
            self.assertIsNotNone(user)
            
            # Wallet should have bonus
            wallet = Wallet.objects.get(user=user)
            self.assertGreater(wallet.balance, 0)


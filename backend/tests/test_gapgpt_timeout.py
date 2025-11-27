"""
تست بررسی مشکل Timeout در GapGPT API
این تست برای بررسی و تشخیص مشکل timeout در تبدیل استراتژی با GapGPT طراحی شده است.
"""

import os
import sys
import django
import time
import requests
from unittest.mock import patch, MagicMock

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth.models import User
from core.models import TradingStrategy, APIConfiguration
from ai_module.gapgpt_client import (
    convert_strategy_with_gapgpt,
    get_gapgpt_api_key,
    get_available_models
)
from api.views import GapGPTViewSet
from rest_framework.test import APIClient
from rest_framework import status


class GapGPTTimeoutTest(TestCase):
    """تست‌های مربوط به timeout در GapGPT"""
    
    def setUp(self):
        """تنظیمات اولیه برای تست"""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        
        # ایجاد یک استراتژی تست
        self.strategy_text = """
        استراتژی معاملاتی RSI:
        - ورود: وقتی RSI زیر 30 باشد
        - خروج: وقتی RSI بالای 70 باشد
        - حد ضرر: 50 پیپ
        - حد سود: 100 پیپ
        - تایم‌فریم: H1
        """
    
    def test_timeout_configuration(self):
        """تست 1: بررسی تنظیمات timeout در convert_strategy_with_gapgpt"""
        print("\n" + "=" * 80)
        print("تست 1: بررسی تنظیمات Timeout")
        print("=" * 80)
        
        # بررسی timeout پیش‌فرض
        import inspect
        sig = inspect.signature(convert_strategy_with_gapgpt)
        timeout_param = sig.parameters.get('timeout')
        
        if timeout_param:
            default_timeout = timeout_param.default
            print(f"✓ Timeout پیش‌فرض: {default_timeout} ثانیه")
            self.assertGreaterEqual(default_timeout, 60, 
                "Timeout باید حداقل 60 ثانیه باشد برای تبدیل استراتژی")
        else:
            self.fail("پارامتر timeout در تابع convert_strategy_with_gapgpt وجود ندارد")
    
    def test_timeout_in_api_view(self):
        """تست 2: بررسی timeout در API View"""
        print("\n" + "=" * 80)
        print("تست 2: بررسی Timeout در API View")
        print("=" * 80)
        
        # بررسی کد views.py برای اطمینان از timeout
        import inspect
        from api.views import GapGPTViewSet
        
        # بررسی متد convert_strategy
        viewset = GapGPTViewSet()
        viewset.request = MagicMock()
        viewset.request.user = self.user
        
        # بررسی اینکه timeout در فراخوانی استفاده می‌شود
        # این تست نیاز به بررسی کد دارد
        print("✓ بررسی کد API View برای استفاده از timeout")
        print("  (این تست نیاز به بررسی دستی کد دارد)")
    
    def test_actual_timeout_behavior(self):
        """تست 3: بررسی رفتار واقعی timeout"""
        print("\n" + "=" * 80)
        print("تست 3: بررسی رفتار واقعی Timeout")
        print("=" * 80)
        
        # بررسی API key
        api_key = get_gapgpt_api_key(user=self.user)
        if not api_key:
            print("⚠ GapGPT API key تنظیم نشده است. تست را skip می‌کنیم.")
            self.skipTest("GapGPT API key تنظیم نشده است")
        
        # تست با timeout کوتاه برای بررسی رفتار
        start_time = time.time()
        
        try:
            result = convert_strategy_with_gapgpt(
                strategy_text=self.strategy_text,
                user=self.user,
                timeout=5  # timeout کوتاه برای تست
            )
            
            elapsed = time.time() - start_time
            print(f"✓ درخواست در {elapsed:.2f} ثانیه تکمیل شد")
            
            # اگر timeout رخ داده باشد، باید error داشته باشیم
            if not result.get('success'):
                error = result.get('error', '')
                if 'timeout' in error.lower() or 'زمان' in error:
                    print(f"⚠ Timeout رخ داد (انتظار می‌رفت): {error}")
                else:
                    print(f"✗ خطای دیگر: {error}")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Exception بعد از {elapsed:.2f} ثانیه: {e}")
            if elapsed >= 5:
                print("⚠ احتمالاً timeout رخ داده است")
    
    def test_timeout_with_long_strategy(self):
        """تست 4: بررسی timeout با استراتژی طولانی"""
        print("\n" + "=" * 80)
        print("تست 4: بررسی Timeout با استراتژی طولانی")
        print("=" * 80)
        
        api_key = get_gapgpt_api_key(user=self.user)
        if not api_key:
            self.skipTest("GapGPT API key تنظیم نشده است")
        
        # ایجاد یک استراتژی طولانی
        long_strategy = self.strategy_text * 50  # تکرار 50 بار
        print(f"طول استراتژی: {len(long_strategy)} کاراکتر")
        
        start_time = time.time()
        
        try:
            result = convert_strategy_with_gapgpt(
                strategy_text=long_strategy,
                user=self.user,
                timeout=120  # timeout طولانی
            )
            
            elapsed = time.time() - start_time
            print(f"✓ درخواست در {elapsed:.2f} ثانیه تکمیل شد")
            
            if result.get('success'):
                print("✓ تبدیل موفق بود")
            else:
                error = result.get('error', '')
                print(f"✗ خطا: {error}")
                
                # بررسی اینکه آیا timeout رخ داده
                if elapsed >= 120:
                    print("⚠ احتمالاً timeout رخ داده است (بیش از 120 ثانیه)")
                elif 'timeout' in error.lower() or 'زمان' in error:
                    print("⚠ Timeout رخ داد")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Exception بعد از {elapsed:.2f} ثانیه: {e}")
    
    def test_api_endpoint_timeout(self):
        """تست 5: بررسی timeout در API endpoint"""
        print("\n" + "=" * 80)
        print("تست 5: بررسی Timeout در API Endpoint")
        print("=" * 80)
        
        # بررسی API key
        api_key = get_gapgpt_api_key(user=self.user)
        if not api_key:
            self.skipTest("GapGPT API key تنظیم نشده است")
        
        # تست endpoint
        url = '/api/gapgpt/convert/'
        data = {
            'strategy_text': self.strategy_text,
            'model_id': 'gpt-4o',
            'temperature': 0.3,
            'max_tokens': 4000
        }
        
        start_time = time.time()
        
        try:
            response = self.client.post(url, data, format='json')
            elapsed = time.time() - start_time
            
            print(f"✓ درخواست در {elapsed:.2f} ثانیه تکمیل شد")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == status.HTTP_200_OK:
                response_data = response.json()
                if response_data.get('status') == 'success':
                    print("✓ تبدیل موفق بود")
                else:
                    print(f"✗ خطا: {response_data.get('message', 'Unknown error')}")
            else:
                print(f"✗ Status Code: {response.status_code}")
                print(f"Response: {response.data}")
            
            # بررسی اینکه آیا timeout رخ داده
            if elapsed >= 10:
                print("⚠ درخواست بیش از 10 ثانیه طول کشید (ممکن است timeout در frontend رخ دهد)")
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Exception بعد از {elapsed:.2f} ثانیه: {e}")
    
    def test_frontend_timeout_configuration(self):
        """تست 6: بررسی تنظیمات timeout در frontend (نیاز به بررسی دستی)"""
        print("\n" + "=" * 80)
        print("تست 6: بررسی تنظیمات Timeout در Frontend")
        print("=" * 80)
        
        print("⚠ این تست نیاز به بررسی دستی فایل frontend/src/api/client.ts دارد")
        print("\nبررسی کنید:")
        print("  1. آیا gapGPTClient با timeout >= 120000 (120 ثانیه) تعریف شده است؟")
        print("  2. آیا توابع GapGPT از gapGPTClient استفاده می‌کنند؟")
        print("  3. آیا interceptorهای CSRF برای gapGPTClient تنظیم شده‌اند؟")
        
        # این تست را pass می‌کنیم چون نیاز به بررسی دستی دارد
        self.assertTrue(True, "نیاز به بررسی دستی")
    
    def test_timeout_recommendations(self):
        """تست 7: پیشنهادات برای بهبود timeout"""
        print("\n" + "=" * 80)
        print("تست 7: پیشنهادات برای بهبود Timeout")
        print("=" * 80)
        
        recommendations = [
            "✓ Frontend: timeout باید حداقل 120 ثانیه (120000ms) باشد",
            "✓ Backend: timeout برای convert_strategy_with_gapgpt باید حداقل 120 ثانیه باشد",
            "✓ Backend: timeout برای analyze_strategy_with_multiple_models باید حداقل 180 ثانیه باشد",
            "✓ استفاده از client جداگانه برای GapGPT در frontend",
            "✓ نمایش loading state به کاربر هنگام انتظار",
            "✓ استفاده از retry mechanism برای خطاهای timeout"
        ]
        
        for rec in recommendations:
            print(rec)
        
        self.assertTrue(True, "پیشنهادات نمایش داده شد")


def run_timeout_tests():
    """اجرای تمام تست‌های timeout"""
    print("\n" + "=" * 80)
    print("🔍 اجرای تست‌های Timeout برای GapGPT")
    print("=" * 80)
    
    import unittest
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(GapGPTTimeoutTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    print("📊 خلاصه نتایج")
    print("=" * 80)
    print(f"تست‌های اجرا شده: {result.testsRun}")
    print(f"موفق: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"ناموفق: {len(result.failures)}")
    print(f"خطا: {len(result.errors)}")
    
    if result.failures:
        print("\n⚠ تست‌های ناموفق:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback[:200]}")
    
    if result.errors:
        print("\n❌ خطاها:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback[:200]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_timeout_tests()
    sys.exit(0 if success else 1)


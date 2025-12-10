"""
تست‌های endpoint گیمیفیکیشن
این تست‌ها بررسی می‌کنند که endpoint /api/gamification/scores/me/ به درستی کار می‌کند
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from core.models import UserScore


class GamificationEndpointTest(TestCase):
    """تست‌های endpoint گیمیفیکیشن"""
    
    def setUp(self):
        """تنظیمات اولیه برای تست‌ها"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_gamification_scores_me_endpoint_exists(self):
        """تست وجود endpoint /api/gamification/scores/me/"""
        response = self.client.get('/api/gamification/scores/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_gamification_scores_me_returns_user_score(self):
        """تست بازگشت امتیاز کاربر از endpoint"""
        response = self.client.get('/api/gamification/scores/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_points', response.data)
        self.assertIn('level', response.data)
        self.assertIn('rank', response.data)
        self.assertIn('backtests_completed', response.data)
        self.assertIn('best_return', response.data)
    
    def test_gamification_scores_me_creates_score_if_not_exists(self):
        """تست ایجاد امتیاز در صورت عدم وجود"""
        # حذف امتیاز در صورت وجود
        UserScore.objects.filter(user=self.user).delete()
        
        # درخواست endpoint
        response = self.client.get('/api/gamification/scores/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # بررسی اینکه امتیاز ایجاد شده است
        self.assertTrue(UserScore.objects.filter(user=self.user).exists())
    
    def test_gamification_scores_me_requires_authentication(self):
        """تست نیاز به احراز هویت برای endpoint"""
        # ایجاد کلاینت بدون احراز هویت
        unauthenticated_client = APIClient()
        response = unauthenticated_client.get('/api/gamification/scores/me/')
        
        # Django REST Framework با IsAuthenticated، 403 Forbidden برمی‌گرداند نه 401
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
                     "Endpoint should require authentication (401 or 403)")
    
    def test_gamification_scores_me_url_not_doubled(self):
        """تست عدم وجود /api/api در URL"""
        # این تست بررسی می‌کند که URL به درستی ساخته می‌شود
        # و مشکل /api/api وجود ندارد
        response = self.client.get('/api/gamification/scores/me/')
        
        # اگر endpoint وجود داشته باشد، باید 200 برگرداند
        # اگر /api/api باشد، 404 برمی‌گرداند
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND, 
                          "Endpoint should not return 404 - check for double /api/api in URL")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


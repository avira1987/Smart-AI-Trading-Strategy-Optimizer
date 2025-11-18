"""
تست دستور مدیریت make_admin
برای اجرا: python manage.py test tests.test_make_admin_command
"""

import sys
import io
import os
import unittest
from io import StringIO

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# تنظیم Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from core.models import UserProfile


class TestMakeAdminCommand(TestCase):
    """تست دستور مدیریت make_admin"""

    def setUp(self):
        """تنظیمات اولیه برای هر تست"""
        # ایجاد کاربر معمولی برای تست
        self.normal_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.normal_user.is_staff = False
        self.normal_user.is_superuser = False
        self.normal_user.save()

        # ایجاد کاربر با پروفایل (شماره موبایل)
        self.user_with_phone = User.objects.create_user(
            username='phoneuser',
            email='phone@example.com',
            password='testpass123'
        )
        self.user_with_phone.is_staff = False
        self.user_with_phone.is_superuser = False
        self.user_with_phone.save()

        # ایجاد پروفایل با شماره موبایل
        UserProfile.objects.create(
            user=self.user_with_phone,
            phone_number='09123456789'
        )

    def test_make_admin_by_username(self):
        """تست ادمین کردن کاربر با استفاده از username"""
        # بررسی اولیه - کاربر نباید ادمین باشد
        self.assertFalse(self.normal_user.is_staff)
        self.assertFalse(self.normal_user.is_superuser)

        # اجرای دستور
        out = StringIO()
        call_command('make_admin', '--username', 'testuser', stdout=out)

        # بارگذاری مجدد کاربر از دیتابیس
        self.normal_user.refresh_from_db()

        # بررسی نتیجه
        self.assertTrue(self.normal_user.is_staff)
        self.assertTrue(self.normal_user.is_superuser)

        # بررسی پیام خروجی
        output = out.getvalue()
        self.assertIn('Found user by username: testuser', output)
        self.assertIn('is now admin', output)

    def test_make_admin_by_phone(self):
        """تست ادمین کردن کاربر با استفاده از شماره موبایل"""
        # بررسی اولیه - کاربر نباید ادمین باشد
        self.assertFalse(self.user_with_phone.is_staff)
        self.assertFalse(self.user_with_phone.is_superuser)

        # اجرای دستور
        out = StringIO()
        call_command('make_admin', '--phone', '09123456789', stdout=out)

        # بارگذاری مجدد کاربر از دیتابیس
        self.user_with_phone.refresh_from_db()

        # بررسی نتیجه
        self.assertTrue(self.user_with_phone.is_staff)
        self.assertTrue(self.user_with_phone.is_superuser)

        # بررسی پیام خروجی
        output = out.getvalue()
        self.assertIn('Found user by phone number: phoneuser', output)
        self.assertIn('is now admin', output)
        self.assertIn('09123456789', output)

    def test_make_admin_nonexistent_username(self):
        """تست خطا برای username وجود نداشته باشد"""
        out = StringIO()
        err = StringIO()

        try:
            call_command('make_admin', '--username', 'nonexistent', stdout=out, stderr=err)
        except Exception:
            pass  # ممکن است exception رخ دهد یا نه

        output = out.getvalue()
        error_output = err.getvalue()
        
        # باید پیام خطا نمایش داده شود
        combined_output = output + error_output
        self.assertIn('No user found', combined_output)

    def test_make_admin_nonexistent_phone(self):
        """تست خطا برای شماره موبایل وجود نداشته باشد"""
        out = StringIO()
        err = StringIO()

        try:
            call_command('make_admin', '--phone', '09999999999', stdout=out, stderr=err)
        except Exception:
            pass  # ممکن است exception رخ دهد یا نه

        output = out.getvalue()
        error_output = err.getvalue()
        
        # باید پیام خطا نمایش داده شود
        combined_output = output + error_output
        self.assertIn('No user found', combined_output)

    def test_make_admin_no_arguments(self):
        """تست خطا وقتی هیچ argumentی ارسال نشده باشد"""
        out = StringIO()
        err = StringIO()

        try:
            call_command('make_admin', stdout=out, stderr=err)
        except Exception:
            pass  # ممکن است exception رخ دهد یا نه

        output = out.getvalue()
        error_output = err.getvalue()
        
        # باید پیام خطا نمایش داده شود
        combined_output = output + error_output
        self.assertIn('--username or --phone', combined_output)

    def test_make_admin_already_admin(self):
        """تست ادمین کردن کاربری که از قبل ادمین است"""
        # تبدیل کاربر به ادمین
        self.normal_user.is_staff = True
        self.normal_user.is_superuser = True
        self.normal_user.save()

        # اجرای مجدد دستور
        out = StringIO()
        call_command('make_admin', '--username', 'testuser', stdout=out)

        # بارگذاری مجدد کاربر از دیتابیس
        self.normal_user.refresh_from_db()

        # باید همچنان ادمین باشد
        self.assertTrue(self.normal_user.is_staff)
        self.assertTrue(self.normal_user.is_superuser)

        # بررسی پیام خروجی
        output = out.getvalue()
        self.assertIn('is now admin', output)

    def test_make_admin_only_staff(self):
        """تست ادمین کردن کاربری که فقط staff است"""
        # تبدیل کاربر به staff (نه superuser)
        self.normal_user.is_staff = True
        self.normal_user.is_superuser = False
        self.normal_user.save()

        # اجرای دستور
        out = StringIO()
        call_command('make_admin', '--username', 'testuser', stdout=out)

        # بارگذاری مجدد کاربر از دیتابیس
        self.normal_user.refresh_from_db()

        # باید اکنون هم staff و هم superuser باشد
        self.assertTrue(self.normal_user.is_staff)
        self.assertTrue(self.normal_user.is_superuser)

    def test_make_admin_multiple_users(self):
        """تست ادمین کردن چند کاربر"""
        # ایجاد کاربر دوم
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        user2.is_staff = False
        user2.is_superuser = False
        user2.save()

        # ادمین کردن کاربر اول
        call_command('make_admin', '--username', 'testuser', stdout=StringIO())
        self.normal_user.refresh_from_db()
        self.assertTrue(self.normal_user.is_staff)
        self.assertTrue(self.normal_user.is_superuser)

        # ادمین کردن کاربر دوم با شماره موبایل
        UserProfile.objects.create(
            user=user2,
            phone_number='09234567890'
        )
        call_command('make_admin', '--phone', '09234567890', stdout=StringIO())
        user2.refresh_from_db()
        self.assertTrue(user2.is_staff)
        self.assertTrue(user2.is_superuser)

        # بررسی که هر دو کاربر ادمین هستند
        admin_users = User.objects.filter(is_staff=True, is_superuser=True)
        self.assertGreaterEqual(admin_users.count(), 2)


def run_tests():
    """اجرای تمام تست‌ها"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # اضافه کردن تمام تست کلاس
    suite.addTests(loader.loadTestsFromTestCase(TestMakeAdminCommand))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("=" * 70)
    print("[TEST] تست دستور مدیریت make_admin")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    if result.wasSuccessful():
        print("\n" + "=" * 70)
        print("[SUCCESS] تمام تست‌ها با موفقیت پاس شدند!")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("[FAILURE] برخی تست‌ها ناموفق بودند!")
        print("=" * 70)
        sys.exit(1)


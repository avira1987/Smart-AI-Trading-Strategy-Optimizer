"""
اسکریپت تست دریافت داده‌های رایگان از Google Analytics API
این اسکریپت بررسی می‌کند چه اطلاعاتی به صورت رایگان در دسترس است
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any

# اضافه کردن مسیر backend
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

def print_section(title: str):
    """چاپ عنوان بخش"""
    print("\n" + "="*70)
    print(f"📊 {title}")
    print("="*70)

def print_result(success: bool, message: str, data: Any = None):
    """چاپ نتیجه تست"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if data and success:
        if isinstance(data, (dict, list)):
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"   {data}")

def test_library_installation():
    """تست نصب کتابخانه‌ها"""
    print_section("تست نصب کتابخانه‌های Google Analytics")
    
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            RunReportRequest,
            DateRange,
            Dimension,
            Metric,
            FilterExpression,
            DimensionExpression,
        )
        from google.oauth2 import service_account
        print_result(True, "همه کتابخانه‌ها نصب شده است")
        return True
    except ImportError as e:
        print_result(False, f"کتابخانه نصب نشده: {e}")
        print("\n💡 برای نصب اجرا کنید:")
        print("   pip install google-analytics-data google-auth")
        return False

def get_available_dimensions():
    """لیست Dimension های قابل دسترس"""
    return [
        "date",                    # تاریخ
        "year",                    # سال
        "month",                   # ماه
        "week",                    # هفته
        "day",                     # روز
        "hour",                    # ساعت
        "minute",                  # دقیقه
        "country",                 # کشور
        "region",                  # منطقه
        "city",                    # شهر
        "continent",               # قاره
        "subContinent",            # زیرقاره
        "metro",                   # مترو
        "deviceCategory",          # نوع دستگاه (desktop, mobile, tablet)
        "mobileDeviceInfo",        # اطلاعات موبایل
        "operatingSystem",         # سیستم عامل
        "operatingSystemVersion",  # نسخه سیستم عامل
        "browser",                 # مرورگر
        "browserVersion",          # نسخه مرورگر
        "screenResolution",        # رزولوشن صفحه
        "language",                # زبان
        "pagePath",                # مسیر صفحه
        "pageTitle",               # عنوان صفحه
        "pageLocation",            # آدرس کامل صفحه
        "hostName",                # نام هاست
        "source",                  # منبع (source)
        "medium",                  # رسانه (medium)
        "campaign",                # کمپین
        "sessionSource",           # منبع جلسه
        "sessionMedium",           # رسانه جلسه
        "sessionCampaign",         # کمپین جلسه
        "sessionDefaultChannelGroup",  # گروه کانال پیش‌فرض
        "userAgeBracket",          # گروه سنی
        "userGender",              # جنسیت
        "newVsReturning",          # کاربر جدید/بازگشتی
        "sessionId",              # شناسه جلسه
        "clientId",                # شناسه کلاینت
        "userId",                  # شناسه کاربر (اگر تنظیم شده باشد)
    ]

def get_available_metrics():
    """لیست Metric های قابل دسترس"""
    return [
        "activeUsers",             # کاربران فعال
        "newUsers",                # کاربران جدید
        "totalUsers",              # کل کاربران
        "sessions",                # جلسات
        "screenPageViews",         # بازدید صفحات
        "pageViews",               # بازدید صفحات (مشابه)
        "averageSessionDuration",  # میانگین مدت جلسه (ثانیه)
        "bounceRate",             # نرخ پرش
        "engagementRate",         # نرخ تعامل
        "engagedSessions",        # جلسات تعاملی
        "eventCount",             # تعداد رویدادها
        "conversions",            # تبدیل‌ها
        "totalRevenue",           # کل درآمد
        "purchaseRevenue",        # درآمد خرید
        "transactions",           # تراکنش‌ها
        "itemsPurchased",         # آیتم‌های خریداری شده
    ]

def test_connection(client, property_id: str) -> bool:
    """تست اتصال به Google Analytics"""
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(start_date="today", end_date="today")],
            dimensions=[Dimension(name="date")],
            metrics=[Metric(name="activeUsers")],
            limit=1
        )
        response = client.run_report(request)
        return True
    except Exception as e:
        print(f"❌ خطا در اتصال: {e}")
        return False

def test_basic_metrics(client, property_id: str, days: int = 7) -> Dict[str, Any]:
    """تست دریافت Metric های پایه"""
    print_section(f"Metric های پایه ({days} روز گذشته)")
    
    results = {}
    
    metrics_to_test = [
        ("activeUsers", "کاربران فعال"),
        ("newUsers", "کاربران جدید"),
        ("totalUsers", "کل کاربران"),
        ("sessions", "جلسات"),
        ("screenPageViews", "بازدید صفحات"),
        ("averageSessionDuration", "میانگین مدت جلسه (ثانیه)"),
        ("bounceRate", "نرخ پرش"),
        ("engagementRate", "نرخ تعامل"),
    ]
    
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            metrics=[Metric(name=metric) for metric, _ in metrics_to_test],
        )
        
        response = client.run_report(request)
        
        if response.row_count > 0:
            row = response.rows[0]
            for i, (metric, label) in enumerate(metrics_to_test):
                value = row.metric_values[i].value
                results[metric] = {
                    "label": label,
                    "value": value,
                    "type": "number"
                }
                print_result(True, f"{label}: {value}")
        else:
            print_result(False, "داده‌ای دریافت نشد")
            
    except Exception as e:
        print_result(False, f"خطا در دریافت Metric ها: {e}")
    
    return results

def test_page_analytics(client, property_id: str, days: int = 7) -> List[Dict]:
    """تست دریافت آمار صفحات"""
    print_section(f"آمار صفحات ({days} روز گذشته)")
    
    results = []
    
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[
                Dimension(name="pagePath"),
                Dimension(name="pageTitle"),
            ],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="averageSessionDuration"),
            ],
            order_bys=[
                {"metric": {"metric_name": "screenPageViews"}, "desc": True}
            ],
            limit=10
        )
        
        response = client.run_report(request)
        
        if response.row_count > 0:
            print(f"✅ {response.row_count} صفحه پیدا شد:\n")
            for row in response.rows:
                page_path = row.dimension_values[0].value
                page_title = row.dimension_values[1].value
                views = row.metric_values[0].value
                users = row.metric_values[1].value
                duration = row.metric_values[2].value
                
                result = {
                    "path": page_path,
                    "title": page_title,
                    "views": views,
                    "users": users,
                    "avg_duration": duration
                }
                results.append(result)
                
                print(f"   📄 {page_title}")
                print(f"      مسیر: {page_path}")
                print(f"      بازدید: {views} | کاربران: {users} | مدت: {duration}ثانیه")
                print()
        else:
            print_result(False, "داده‌ای برای صفحات دریافت نشد")
            
    except Exception as e:
        print_result(False, f"خطا در دریافت آمار صفحات: {e}")
    
    return results

def test_user_demographics(client, property_id: str, days: int = 7) -> Dict[str, Any]:
    """تست دریافت اطلاعات دموگرافیک"""
    print_section(f"اطلاعات دموگرافیک ({days} روز گذشته)")
    
    results = {}
    
    # تست کشور
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[Dimension(name="country")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[{"metric": {"metric_name": "activeUsers"}, "desc": True}],
            limit=10
        )
        
        response = client.run_report(request)
        if response.row_count > 0:
            countries = []
            for row in response.rows:
                country = row.dimension_values[0].value
                users = row.metric_values[0].value
                countries.append({"country": country, "users": users})
                print(f"   🌍 {country}: {users} کاربر")
            results["countries"] = countries
    except Exception as e:
        print_result(False, f"خطا در دریافت اطلاعات کشور: {e}")
    
    # تست دستگاه
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[Dimension(name="deviceCategory")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[{"metric": {"metric_name": "activeUsers"}, "desc": True}],
        )
        
        response = client.run_report(request)
        if response.row_count > 0:
            devices = []
            for row in response.rows:
                device = row.dimension_values[0].value
                users = row.metric_values[0].value
                devices.append({"device": device, "users": users})
                print(f"   📱 {device}: {users} کاربر")
            results["devices"] = devices
    except Exception as e:
        print_result(False, f"خطا در دریافت اطلاعات دستگاه: {e}")
    
    # تست مرورگر
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[Dimension(name="browser")],
            metrics=[Metric(name="activeUsers")],
            order_bys=[{"metric": {"metric_name": "activeUsers"}, "desc": True}],
            limit=5
        )
        
        response = client.run_report(request)
        if response.row_count > 0:
            browsers = []
            for row in response.rows:
                browser = row.dimension_values[0].value
                users = row.metric_values[0].value
                browsers.append({"browser": browser, "users": users})
                print(f"   🌐 {browser}: {users} کاربر")
            results["browsers"] = browsers
    except Exception as e:
        print_result(False, f"خطا در دریافت اطلاعات مرورگر: {e}")
    
    return results

def test_traffic_sources(client, property_id: str, days: int = 7) -> Dict[str, Any]:
    """تست دریافت منابع ترافیک"""
    print_section(f"منابع ترافیک ({days} روز گذشته)")
    
    results = {}
    
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
                Dimension(name="sessionDefaultChannelGroup"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="activeUsers"),
            ],
            order_bys=[{"metric": {"metric_name": "sessions"}, "desc": True}],
            limit=10
        )
        
        response = client.run_report(request)
        
        if response.row_count > 0:
            sources = []
            print(f"✅ {response.row_count} منبع ترافیک پیدا شد:\n")
            for row in response.rows:
                source = row.dimension_values[0].value
                medium = row.dimension_values[1].value
                channel = row.dimension_values[2].value
                sessions = row.metric_values[0].value
                users = row.metric_values[1].value
                
                source_data = {
                    "source": source,
                    "medium": medium,
                    "channel": channel,
                    "sessions": sessions,
                    "users": users
                }
                sources.append(source_data)
                
                print(f"   🔗 {channel}")
                print(f"      منبع: {source} | رسانه: {medium}")
                print(f"      جلسات: {sessions} | کاربران: {users}")
                print()
            
            results["sources"] = sources
        else:
            print_result(False, "داده‌ای برای منابع ترافیک دریافت نشد")
            
    except Exception as e:
        print_result(False, f"خطا در دریافت منابع ترافیک: {e}")
    
    return results

def test_time_series(client, property_id: str, days: int = 7) -> List[Dict]:
    """تست دریافت داده‌های سری زمانی"""
    print_section(f"داده‌های سری زمانی ({days} روز گذشته)")
    
    results = []
    
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
                Metric(name="screenPageViews"),
            ],
            order_bys=[{"dimension": {"dimension_name": "date"}}],
        )
        
        response = client.run_report(request)
        
        if response.row_count > 0:
            print(f"✅ {response.row_count} روز داده دریافت شد:\n")
            for row in response.rows:
                date_str = row.dimension_values[0].value
                users = row.metric_values[0].value
                sessions = row.metric_values[1].value
                views = row.metric_values[2].value
                
                result = {
                    "date": date_str,
                    "users": users,
                    "sessions": sessions,
                    "views": views
                }
                results.append(result)
                
                # تبدیل تاریخ به فرمت خوانا
                try:
                    date_obj = datetime.strptime(date_str, "%Y%m%d")
                    date_formatted = date_obj.strftime("%Y-%m-%d")
                    print(f"   📅 {date_formatted}: {users} کاربر | {sessions} جلسه | {views} بازدید")
                except:
                    print(f"   📅 {date_str}: {users} کاربر | {sessions} جلسه | {views} بازدید")
        else:
            print_result(False, "داده‌ای برای سری زمانی دریافت نشد")
            
    except Exception as e:
        print_result(False, f"خطا در دریافت سری زمانی: {e}")
    
    return results

def test_user_behavior(client, property_id: str, days: int = 7) -> Dict[str, Any]:
    """تست دریافت رفتار کاربران"""
    print_section(f"رفتار کاربران ({days} روز گذشته)")
    
    results = {}
    
    # کاربران جدید vs بازگشتی
    try:
        request = RunReportRequest(
            property=f"properties/{property_id}",
            date_ranges=[DateRange(
                start_date=f"{days}daysAgo",
                end_date="today"
            )],
            dimensions=[Dimension(name="newVsReturning")],
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="sessions"),
            ],
        )
        
        response = client.run_report(request)
        if response.row_count > 0:
            behavior = []
            for row in response.rows:
                user_type = row.dimension_values[0].value
                users = row.metric_values[0].value
                sessions = row.metric_values[1].value
                behavior.append({
                    "type": user_type,
                    "users": users,
                    "sessions": sessions
                })
                print(f"   👤 {user_type}: {users} کاربر | {sessions} جلسه")
            results["user_types"] = behavior
    except Exception as e:
        print_result(False, f"خطا در دریافت رفتار کاربران: {e}")
    
    return results

def generate_summary_report(all_results: Dict[str, Any]):
    """تولید گزارش خلاصه"""
    print_section("📋 گزارش خلاصه داده‌های قابل دسترس")
    
    print("\n✅ داده‌هایی که به صورت رایگان در دسترس هستند:\n")
    
    categories = {
        "Metric های پایه": [
            "کاربران فعال (activeUsers)",
            "کاربران جدید (newUsers)",
            "کل کاربران (totalUsers)",
            "جلسات (sessions)",
            "بازدید صفحات (screenPageViews)",
            "میانگین مدت جلسه (averageSessionDuration)",
            "نرخ پرش (bounceRate)",
            "نرخ تعامل (engagementRate)",
        ],
        "اطلاعات صفحات": [
            "مسیر صفحات (pagePath)",
            "عنوان صفحات (pageTitle)",
            "آمار بازدید هر صفحه",
            "کاربران هر صفحه",
            "مدت زمان در هر صفحه",
        ],
        "اطلاعات جغرافیایی": [
            "کشور کاربران",
            "منطقه/استان",
            "شهر",
            "قاره",
        ],
        "اطلاعات دستگاه": [
            "نوع دستگاه (desktop, mobile, tablet)",
            "سیستم عامل",
            "نسخه سیستم عامل",
            "مرورگر",
            "نسخه مرورگر",
            "رزولوشن صفحه",
        ],
        "منابع ترافیک": [
            "منبع (source)",
            "رسانه (medium)",
            "کمپین (campaign)",
            "گروه کانال (channel group)",
        ],
        "داده‌های زمانی": [
            "آمار روزانه",
            "آمار هفتگی",
            "آمار ماهانه",
            "سری زمانی کامل",
        ],
        "رفتار کاربران": [
            "کاربران جدید vs بازگشتی",
            "جلسات تعاملی",
            "رویدادها",
        ],
    }
    
    for category, items in categories.items():
        print(f"\n📌 {category}:")
        for item in items:
            print(f"   • {item}")
    
    print("\n" + "="*70)
    print("💡 نکات مهم:")
    print("="*70)
    print("""
1. ✅ Google Analytics Data API به صورت رایگان است (تا 10 میلیون درخواست در ماه)
2. ✅ تمام این داده‌ها بدون هزینه در دسترس هستند
3. ✅ محدودیت Rate Limit: 10 درخواست در ثانیه
4. ✅ داده‌های Real-time در دسترس هستند
5. ✅ می‌توانید داده‌های تاریخی تا 14 ماه گذشته را دریافت کنید
6. ⚠️  برای دریافت داده‌های کاربران خاص، باید userId را تنظیم کنید
7. ⚠️  برخی Metric ها نیاز به تنظیمات خاص دارند (مثل conversions)
    """)

def main():
    """تابع اصلی"""
    print("="*70)
    print("🚀 تست دریافت داده‌های رایگان از Google Analytics API")
    print("="*70)
    
    # تست نصب
    if not test_library_installation():
        print("\n❌ لطفا ابتدا کتابخانه‌ها را نصب کنید:")
        print("   pip install google-analytics-data google-auth")
        return
    
    # بررسی تنظیمات
    SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE', '')
    PROPERTY_ID = os.environ.get('GOOGLE_ANALYTICS_PROPERTY_ID', '')
    
    if not SERVICE_ACCOUNT_FILE:
        print("\n⚠️  متغیر GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE تنظیم نشده")
        print("\n📝 برای تست:")
        print("   1. Service Account در Google Cloud Console ایجاد کنید")
        print("   2. Google Analytics Data API را فعال کنید")
        print("   3. JSON Key File را دانلود کنید")
        print("   4. متغیر را تنظیم کنید:")
        print("      export GOOGLE_ANALYTICS_SERVICE_ACCOUNT_FILE=path/to/key.json")
        print("      export GOOGLE_ANALYTICS_PROPERTY_ID=123456789")
        return
    
    if not PROPERTY_ID:
        print("\n⚠️  متغیر GOOGLE_ANALYTICS_PROPERTY_ID تنظیم نشده")
        print("   Property ID را از Google Analytics > Admin > Property Settings دریافت کنید")
        return
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"\n❌ فایل Service Account پیدا نشد: {SERVICE_ACCOUNT_FILE}")
        return
    
    # ایجاد کلاینت
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import RunReportRequest, DateRange, Dimension, Metric
        from google.oauth2 import service_account
        
        print_section("اتصال به Google Analytics")
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        client = BetaAnalyticsDataClient(credentials=credentials)
        print_result(True, "اتصال برقرار شد")
        
        # تست اتصال
        if not test_connection(client, PROPERTY_ID):
            print("\n❌ اتصال به Property ناموفق بود")
            return
        
        # جمع‌آوری نتایج
        all_results = {}
        
        # تست‌های مختلف
        all_results["basic_metrics"] = test_basic_metrics(client, PROPERTY_ID, 7)
        all_results["pages"] = test_page_analytics(client, PROPERTY_ID, 7)
        all_results["demographics"] = test_user_demographics(client, PROPERTY_ID, 7)
        all_results["traffic_sources"] = test_traffic_sources(client, PROPERTY_ID, 7)
        all_results["time_series"] = test_time_series(client, PROPERTY_ID, 7)
        all_results["user_behavior"] = test_user_behavior(client, PROPERTY_ID, 7)
        
        # گزارش خلاصه
        generate_summary_report(all_results)
        
        # ذخیره نتایج
        output_file = Path(__file__).parent / "google_analytics_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 نتایج در فایل ذخیره شد: {output_file}")
        
    except Exception as e:
        print(f"\n❌ خطا: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()


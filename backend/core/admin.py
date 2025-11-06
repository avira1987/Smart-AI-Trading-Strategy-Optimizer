from django.contrib import admin
from .models import APIConfiguration, TradingStrategy, Job, Result, LiveTrade, AutoTradingSettings
from .models import UserProfile, OTPCode, Device, Ticket, TicketMessage, StrategyOptimization
from .models import Wallet, Transaction, AIRecommendation, DDNSConfiguration, SystemSettings, GoldPriceSubscription


@admin.register(APIConfiguration)
class APIConfigurationAdmin(admin.ModelAdmin):
    list_display = ['provider', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active']
    search_fields = ['provider']


@admin.register(TradingStrategy)
class TradingStrategyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'uploaded_at']
    search_fields = ['name', 'description']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'job_type', 'status', 'created_at', 'completed_at']
    list_filter = ['job_type', 'status']
    search_fields = ['strategy__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['job', 'total_return', 'total_trades', 'win_rate', 'created_at']
    list_filter = ['created_at']
    readonly_fields = ['created_at']


@admin.register(LiveTrade)
class LiveTradeAdmin(admin.ModelAdmin):
    list_display = ['mt5_ticket', 'symbol', 'trade_type', 'volume', 'open_price', 'profit', 'status', 'opened_at']
    list_filter = ['status', 'trade_type', 'symbol', 'strategy']
    search_fields = ['mt5_ticket', 'symbol', 'strategy__name']
    readonly_fields = ['mt5_ticket', 'opened_at', 'closed_at']


@admin.register(AutoTradingSettings)
class AutoTradingSettingsAdmin(admin.ModelAdmin):
    list_display = ['strategy', 'is_enabled', 'symbol', 'volume', 'max_open_trades', 'check_interval_minutes', 'last_check_time']
    list_filter = ['is_enabled', 'symbol']
    search_fields = ['strategy__name']
    readonly_fields = ['last_check_time', 'created_at', 'updated_at']


@admin.register(DDNSConfiguration)
class DDNSConfigurationAdmin(admin.ModelAdmin):
    list_display = ['provider', 'domain', 'is_enabled', 'last_update', 'last_ip', 'created_at']
    list_filter = ['provider', 'is_enabled']
    search_fields = ['domain', 'provider']
    readonly_fields = ['last_update', 'last_ip', 'created_at', 'updated_at']
    fieldsets = (
        ('تنظیمات اصلی', {
            'fields': ('provider', 'domain', 'is_enabled', 'update_interval_minutes')
        }),
        ('اطلاعات احراز هویت', {
            'fields': ('token', 'username', 'password', 'update_url'),
            'description': 'برای DuckDNS: فقط token نیاز است. برای No-IP و Dynu: username و password. برای سرویس سفارشی: update_url'
        }),
        ('اطلاعات سیستم', {
            'fields': ('last_update', 'last_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'created_at']
    search_fields = ['phone_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'code', 'is_used', 'created_at', 'expires_at', 'attempts']
    list_filter = ['is_used', 'created_at']
    search_fields = ['phone_number', 'code']
    readonly_fields = ['created_at', 'expires_at']
    ordering = ['-created_at']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_id', 'device_name', 'is_active', 'last_login', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'device_id', 'device_name']
    readonly_fields = ['created_at', 'last_login']
    ordering = ['-last_login']


class TicketMessageInline(admin.TabularInline):
    """Inline admin for ticket messages"""
    model = TicketMessage
    extra = 0
    readonly_fields = ['created_at']
    fields = ['user', 'message', 'is_admin', 'created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'category', 'priority', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'priority', 'category', 'created_at']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at']
    inlines = [TicketMessageInline]
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('user', 'title', 'description', 'category', 'priority', 'status')
        }),
        ('پاسخ ادمین', {
            'fields': ('admin_user', 'admin_response', 'resolved_at')
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']


@admin.register(TicketMessage)
class TicketMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'user', 'is_admin', 'created_at']
    list_filter = ['is_admin', 'created_at']
    search_fields = ['message', 'ticket__title', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(StrategyOptimization)
class StrategyOptimizationAdmin(admin.ModelAdmin):
    list_display = ['id', 'strategy', 'method', 'optimizer_type', 'objective', 'status', 'best_score', 'improvement_percent', 'created_at']
    list_filter = ['method', 'optimizer_type', 'objective', 'status', 'created_at']
    search_fields = ['strategy__name']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'best_score', 'improvement_percent']
    ordering = ['-created_at']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('strategy', 'method', 'optimizer_type', 'objective', 'status')
        }),
        ('نتایج', {
            'fields': ('original_params', 'optimized_params', 'best_score', 'original_score', 'improvement_percent', 'optimization_history')
        }),
        ('تنظیمات', {
            'fields': ('optimization_settings',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('خطا', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'wallet', 'transaction_type', 'amount', 'status', 'ai_recommendation', 'created_at', 'completed_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['wallet__user__username', 'zarinpal_authority', 'zarinpal_ref_id', 'description']
    readonly_fields = ['created_at', 'completed_at']
    ordering = ['-created_at']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('wallet', 'transaction_type', 'amount', 'status', 'description')
        }),
        ('زرین‌پال', {
            'fields': ('zarinpal_authority', 'zarinpal_ref_id')
        }),
        ('پیشنهاد AI', {
            'fields': ('ai_recommendation',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ['id', 'strategy', 'title', 'recommendation_type', 'price', 'status', 'purchased_by', 'created_at']
    list_filter = ['recommendation_type', 'status', 'created_at']
    search_fields = ['title', 'description', 'strategy__name', 'purchased_by__username']
    readonly_fields = ['created_at', 'purchased_at', 'applied_at']
    ordering = ['-created_at']
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('strategy', 'recommendation_type', 'title', 'description', 'price', 'status')
        }),
        ('داده‌های پیشنهاد', {
            'fields': ('recommendation_data',)
        }),
        ('خرید', {
            'fields': ('purchased_by', 'purchased_at')
        }),
        ('اعمال', {
            'fields': ('applied_to_strategy', 'applied_at')
        }),
        ('زمان', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(GoldPriceSubscription)
class GoldPriceSubscriptionAdmin(admin.ModelAdmin):
    """Admin برای اشتراک قیمت طلا"""
    list_display = ['user', 'is_active', 'start_date', 'end_date', 'monthly_price', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('وضعیت اشتراک', {
            'fields': ('is_active', 'start_date', 'end_date', 'monthly_price')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """برای ویرایش، created_at فقط خواندنی"""
        return ['created_at', 'updated_at']


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """Admin برای تنظیمات سیستم"""
    list_display = ['id', 'google_auth_enabled', 'updated_at']
    list_filter = ['google_auth_enabled']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # فقط یک رکورد داشته باشیم
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # جلوگیری از حذف
        return False
    
    fieldsets = (
        ('تنظیمات احراز هویت', {
            'fields': ('google_auth_enabled',),
            'description': 'فعال یا غیرفعال کردن ویژگی‌های احراز هویت مختلف'
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def changelist_view(self, request, extra_context=None):
        # اگر رکوردی وجود ندارد، آن را ایجاد کنیم
        SystemSettings.load()
        return super().changelist_view(request, extra_context)


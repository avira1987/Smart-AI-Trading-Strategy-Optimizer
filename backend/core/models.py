from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import secrets
import hashlib


class APIConfiguration(models.Model):
    """Configuration for external API connections"""
    
    PROVIDER_CHOICES = [
        ('twelvedata', 'TwelveData'),
        ('alphavantage', 'Alpha Vantage'),
        ('oanda', 'OANDA'),
        ('metalsapi', 'MetalsAPI'),
        ('financialmodelingprep', 'Financial Modeling Prep'),
        ('nerkh', 'Nerkh.io (قیمت طلا)'),
        ('gemini', 'Gemini AI (Google AI Studio)'),
        ('kavenegar', 'Kavenegar (SMS)'),
        ('google_oauth', 'Google OAuth (Client ID)'),
        ('zarinpal', 'Zarinpal (Merchant ID)'),
    ]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "API Configuration"
        verbose_name_plural = "API Configurations"
        # Remove unique constraint to allow multiple API keys per provider
        # unique_together = ['provider']
    
    def __str__(self):
        return f"{self.get_provider_display()} - {self.is_active}"


class TradingStrategy(models.Model):
    """Trading strategy uploaded by user"""
    
    PROCESSING_STATUS_CHOICES = [
        ('not_processed', 'Not Processed'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    strategy_file = models.FileField(upload_to='strategies/')
    is_active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_strategy_data = models.JSONField(null=True, blank=True, help_text="Parsed strategy data from NLP processing")
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='not_processed')
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True, help_text="Error message if processing failed")
    
    class Meta:
        verbose_name = "Trading Strategy"
        verbose_name_plural = "Trading Strategies"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.name}"


class StrategyQuestion(models.Model):
    """سوالات و جواب‌های تعاملی برای تکمیل استراتژی"""
    
    QUESTION_STATUS_CHOICES = [
        ('pending', 'در انتظار جواب'),
        ('answered', 'پاسخ داده شده'),
        ('skipped', 'رد شده'),
    ]
    
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(help_text="متن سوال")
    question_type = models.CharField(
        max_length=50,
        help_text="نوع سوال: text, number, choice, multiple_choice, boolean"
    )
    options = models.JSONField(
        null=True, 
        blank=True, 
        help_text="گزینه‌های انتخابی برای سوالات choice"
    )
    answer = models.TextField(null=True, blank=True, help_text="جواب کاربر")
    status = models.CharField(max_length=20, choices=QUESTION_STATUS_CHOICES, default='pending')
    order = models.IntegerField(default=0, help_text="ترتیب نمایش سوال")
    created_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    context = models.JSONField(
        null=True, 
        blank=True, 
        help_text="اطلاعات اضافی برای سوال (مثلاً بخشی از متن که نیاز به توضیح دارد)"
    )
    
    class Meta:
        verbose_name = "Strategy Question"
        verbose_name_plural = "Strategy Questions"
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}... ({self.strategy.name})"


class Job(models.Model):
    """Jobs for backtesting or demo trading"""
    
    JOB_TYPES = [
        ('backtest', 'Backtest'),
        ('demo_trade', 'Demo Trade'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.ForeignKey('Result', null=True, blank=True, on_delete=models.SET_NULL, related_name='job_set')
    error_message = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_job_type_display()} - {self.strategy.name} - {self.status}"


class Result(models.Model):
    """Results from backtesting or demo trading"""
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='results')
    total_return = models.FloatField(default=0.0)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)
    max_drawdown = models.FloatField(default=0.0)
    equity_curve_data = models.JSONField(default=list, blank=True)
    description = models.TextField(blank=True)
    trades_details = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Result for {self.job} - Return: {self.total_return:.2f}%"


class DemoAccount(models.Model):
    """حساب دمو برای کاربرانی که MT5 ندارند"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='demo_account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.0, help_text="موجودی اولیه حساب دمو (USD)")
    equity = models.DecimalField(max_digits=12, decimal_places=2, default=10000.0, help_text="ارزش فعلی حساب")
    margin = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="مارجین استفاده شده")
    free_margin = models.DecimalField(max_digits=12, decimal_places=2, default=10000.0, help_text="مارجین آزاد")
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="سود/زیان کل")
    leverage = models.IntegerField(default=100, help_text="اهرم حساب")
    is_active = models.BooleanField(default=True, help_text="آیا حساب فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "حساب دمو"
        verbose_name_plural = "حساب‌های دمو"
    
    def __str__(self):
        return f"Demo Account - {self.user.username} - Balance: ${self.balance}"
    
    def update_equity(self):
        """به‌روزرسانی equity بر اساس معاملات باز"""
        from django.db.models import Sum
        from django.db.models import Q
        
        # محاسبه سود/زیان معاملات باز
        open_trades = DemoTrade.objects.filter(
            account=self,
            status='open'
        )
        
        total_profit = sum(trade.get_current_profit() for trade in open_trades)
        
        self.profit = total_profit
        self.equity = self.balance + total_profit
        self.free_margin = self.equity - self.margin
        self.save(update_fields=['equity', 'profit', 'free_margin', 'updated_at'])
    
    def reset_account(self):
        """بازنشانی حساب به مقدار اولیه"""
        self.balance = 10000.0
        self.equity = 10000.0
        self.margin = 0.0
        self.free_margin = 10000.0
        self.profit = 0.0
        # بستن تمام معاملات باز
        DemoTrade.objects.filter(account=self, status='open').update(status='closed')
        self.save()


class DemoTrade(models.Model):
    """معاملات دمو که در دیتابیس ثبت می‌شوند"""
    
    TRADE_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pending', 'Pending'),
    ]
    
    account = models.ForeignKey(DemoAccount, on_delete=models.CASCADE, related_name='trades')
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.SET_NULL, null=True, blank=True)
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPE_CHOICES)
    symbol = models.CharField(max_length=50, default='XAU/USD')
    volume = models.FloatField(help_text="حجم معامله")
    open_price = models.FloatField(help_text="قیمت باز شدن")
    current_price = models.FloatField(null=True, blank=True, help_text="قیمت فعلی")
    stop_loss = models.FloatField(null=True, blank=True)
    take_profit = models.FloatField(null=True, blank=True)
    profit = models.FloatField(default=0.0, help_text="سود/زیان فعلی")
    commission = models.FloatField(default=0.0, help_text="کمیسیون")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    close_price = models.FloatField(null=True, blank=True)
    close_reason = models.TextField(blank=True)
    margin_used = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="مارجین استفاده شده")
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = "معامله دمو"
        verbose_name_plural = "معاملات دمو"
        indexes = [
            models.Index(fields=['account', 'status']),
            models.Index(fields=['status', 'opened_at']),
        ]
    
    def __str__(self):
        return f"{self.symbol} {self.get_trade_type_display()} - {self.account.user.username}"
    
    def get_current_profit(self) -> float:
        """محاسبه سود/زیان فعلی معامله"""
        if self.status != 'open' or not self.current_price:
            return float(self.profit)
        
        # محاسبه سود/زیان
        if self.trade_type == 'buy':
            # برای خرید: سود = (قیمت فعلی - قیمت باز) * حجم
            profit = (self.current_price - self.open_price) * self.volume * 100  # 100 برای تبدیل لات
        else:  # sell
            # برای فروش: سود = (قیمت باز - قیمت فعلی) * حجم
            profit = (self.open_price - self.current_price) * self.volume * 100
        
        # کسر کمیسیون
        profit -= self.commission
        
        return profit
    
    def update_current_price(self, price: float):
        """به‌روزرسانی قیمت فعلی و محاسبه سود/زیان"""
        self.current_price = price
        self.profit = self.get_current_profit()
        self.save(update_fields=['current_price', 'profit'])
    
    def check_stop_loss_take_profit(self) -> bool:
        """بررسی آیا stop loss یا take profit فعال شده است"""
        if self.status != 'open' or not self.current_price:
            return False
        
        should_close = False
        reason = ""
        
        if self.trade_type == 'buy':
            if self.stop_loss and self.current_price <= self.stop_loss:
                should_close = True
                reason = f"Stop Loss triggered at {self.stop_loss}"
            elif self.take_profit and self.current_price >= self.take_profit:
                should_close = True
                reason = f"Take Profit triggered at {self.take_profit}"
        else:  # sell
            if self.stop_loss and self.current_price >= self.stop_loss:
                should_close = True
                reason = f"Stop Loss triggered at {self.stop_loss}"
            elif self.take_profit and self.current_price <= self.take_profit:
                should_close = True
                reason = f"Take Profit triggered at {self.take_profit}"
        
        if should_close:
            self.close_trade(self.current_price, reason)
        
        return should_close
    
    def close_trade(self, close_price: float, reason: str = ""):
        """بستن معامله"""
        if self.status != 'open':
            return
        
        self.status = 'closed'
        self.close_price = close_price
        self.closed_at = timezone.now()
        self.close_reason = reason
        self.current_price = close_price
        self.profit = self.get_current_profit()
        
        # به‌روزرسانی موجودی حساب
        self.account.balance += self.profit
        self.account.margin -= self.margin_used
        
        self.save()
        self.account.update_equity()


class LiveTrade(models.Model):
    """Live trading positions opened via MT5"""
    
    TRADE_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('pending', 'Pending'),
    ]
    
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.SET_NULL, null=True, blank=True)
    mt5_ticket = models.BigIntegerField(unique=True, null=True, blank=True, help_text="MT5 position ticket number")
    symbol = models.CharField(max_length=50, default='XAUUSD')
    trade_type = models.CharField(max_length=10, choices=TRADE_TYPE_CHOICES)
    volume = models.FloatField()
    open_price = models.FloatField()
    current_price = models.FloatField(null=True, blank=True)
    stop_loss = models.FloatField(null=True, blank=True)
    take_profit = models.FloatField(null=True, blank=True)
    profit = models.FloatField(default=0.0)
    swap = models.FloatField(default=0.0)
    commission = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    close_price = models.FloatField(null=True, blank=True)
    close_reason = models.TextField(blank=True)
    is_demo = models.BooleanField(default=False, help_text="آیا این معامله دمو است؟")
    demo_trade = models.ForeignKey(DemoTrade, on_delete=models.SET_NULL, null=True, blank=True, related_name='live_trade')
    
    class Meta:
        ordering = ['-opened_at']
        verbose_name = "Live Trade"
        verbose_name_plural = "Live Trades"
    
    def __str__(self):
        ticket = self.mt5_ticket or self.id
        return f"{self.symbol} {self.get_trade_type_display()} - Ticket: {ticket}"


class AutoTradingSettings(models.Model):
    """Settings for automatic trading based on strategies"""
    
    strategy = models.OneToOneField(TradingStrategy, on_delete=models.CASCADE, related_name='auto_trading_settings')
    is_enabled = models.BooleanField(default=False, help_text="فعال/غیرفعال کردن معامله خودکار")
    symbol = models.CharField(max_length=50, default='XAUUSD', help_text="نماد معاملاتی")
    volume = models.FloatField(default=0.01, help_text="حجم معامله به لات")
    max_open_trades = models.IntegerField(default=3, help_text="حداکثر تعداد معاملات باز همزمان")
    check_interval_minutes = models.IntegerField(default=5, help_text="فاصله زمانی بررسی سیگنال (دقیقه)")
    use_stop_loss = models.BooleanField(default=True, help_text="استفاده از حد ضرر")
    use_take_profit = models.BooleanField(default=True, help_text="استفاده از حد سود")
    stop_loss_pips = models.FloatField(default=50.0, help_text="حد ضرر به پیپ")
    take_profit_pips = models.FloatField(default=100.0, help_text="حد سود به پیپ")
    risk_per_trade_percent = models.FloatField(default=2.0, help_text="ریسک به درصد سرمایه در هر معامله")
    last_check_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Auto Trading Settings"
        verbose_name_plural = "Auto Trading Settings"
    
    def __str__(self):
        status = "فعال" if self.is_enabled else "غیرفعال"
        return f"{self.strategy.name} - {status}"


class DDNSConfiguration(models.Model):
    """DDNS Configuration for making server accessible via public domain"""
    
    PROVIDER_CHOICES = [
        ('duckdns', 'DuckDNS (رایگان)'),
        ('noip', 'No-IP (رایگان)'),
        ('dynu', 'Dynu (رایگان)'),
        ('freedns', 'FreeDNS (رایگان)'),
        ('custom', 'سرویس سفارشی'),
    ]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='duckdns', help_text="سرویس DDNS")
    domain = models.CharField(max_length=255, help_text="دامنه (مثلاً: mydomain.duckdns.org)")
    token = models.CharField(max_length=255, help_text="توکن یا رمز عبور DDNS", blank=True)
    username = models.CharField(max_length=255, help_text="نام کاربری (برای No-IP و Dynu)", blank=True)
    password = models.CharField(max_length=255, help_text="رمز عبور (برای No-IP و Dynu)", blank=True)
    update_url = models.URLField(max_length=500, help_text="URL به‌روزرسانی (برای سرویس سفارشی)", blank=True)
    is_enabled = models.BooleanField(default=False, help_text="فعال/غیرفعال کردن DDNS")
    update_interval_minutes = models.IntegerField(default=5, help_text="فاصله زمانی به‌روزرسانی (دقیقه)")
    last_update = models.DateTimeField(null=True, blank=True, help_text="آخرین به‌روزرسانی")
    last_ip = models.CharField(max_length=45, blank=True, help_text="آخرین IP ثبت شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "DDNS Configuration"
        verbose_name_plural = "DDNS Configurations"
        # Only one active DDNS configuration at a time
        constraints = [
            models.UniqueConstraint(
                fields=['is_enabled'],
                condition=models.Q(is_enabled=True),
                name='unique_active_ddns'
            )
        ]
    
    def __str__(self):
        status = "فعال" if self.is_enabled else "غیرفعال"
        return f"{self.get_provider_display()} - {self.domain} ({status})"
    
    def get_update_url(self):
        """Get the update URL based on provider"""
        if self.provider == 'duckdns':
            return f"https://www.duckdns.org/update?domains={self.domain}&token={self.token}&ip="
        elif self.provider == 'noip':
            return f"https://dynupdate.no-ip.com/nic/update?hostname={self.domain}&username={self.username}&password={self.password}"
        elif self.provider == 'dynu':
            return f"https://api.dynu.com/nic/update?hostname={self.domain}&username={self.username}&password={self.password}&myip="
        elif self.provider == 'freedns':
            return f"https://freedns.afraid.org/dynamic/update.php?{self.token}"
        elif self.provider == 'custom':
            return self.update_url
        return None


class UserProfile(models.Model):
    """Extended user profile with phone number"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, unique=True, help_text="شماره موبایل به فرمت 09123456789")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"{self.user.username} - {self.phone_number}"


class OTPCode(models.Model):
    """One-time password codes for phone authentication"""
    phone_number = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0, help_text="تعداد تلاش‌های ناموفق")
    
    class Meta:
        verbose_name = "OTP Code"
        verbose_name_plural = "OTP Codes"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'is_used']),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone_number} - {self.code}"
    
    def is_valid(self):
        """Check if OTP is still valid"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.is_used = True
        self.save()
    
    def increment_attempts(self):
        """Increment failed attempts"""
        self.attempts += 1
        self.save()
    
    @staticmethod
    def generate_code():
        """Generate a 4-digit OTP code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(4)])
    
    @staticmethod
    def create_otp(phone_number: str):
        """Create a new OTP code"""
        # Invalidate previous unused OTPs for this phone
        OTPCode.objects.filter(
            phone_number=phone_number,
            is_used=False,
            expires_at__gt=timezone.now()
        ).update(is_used=True)
        
        # Generate new OTP
        code = OTPCode.generate_code()
        expires_at = timezone.now() + timedelta(minutes=5)
        
        otp = OTPCode.objects.create(
            phone_number=phone_number,
            code=code,
            expires_at=expires_at
        )
        
        return otp


class Device(models.Model):
    """Track user devices for persistent login"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_id = models.CharField(max_length=255, db_index=True, help_text="Unique device identifier (fingerprint)")
    device_name = models.CharField(max_length=255, blank=True, help_text="Device name or browser info")
    last_login = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        unique_together = ['user', 'device_id']
        ordering = ['-last_login']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_id[:20]}"
    
    @staticmethod
    def generate_device_id(request):
        """Generate device fingerprint from request"""
        # Combine user agent, IP, and accept language
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = request.META.get('REMOTE_ADDR', '')
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        
        # Create a hash
        fingerprint_string = f"{user_agent}|{ip_address}|{accept_language}"
        device_id = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        return device_id
    
    def update_last_login(self):
        """Update last login time"""
        self.last_login = timezone.now()
        self.save()


class Ticket(models.Model):
    """سیستم تیکت برای کاربران لاگین شده"""
    
    PRIORITY_CHOICES = [
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'بالا'),
        ('urgent', 'فوری'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'باز'),
        ('in_progress', 'در حال بررسی'),
        ('resolved', 'حل شده'),
        ('closed', 'بسته شده'),
    ]
    
    CATEGORY_CHOICES = [
        ('technical', 'مسئله فنی'),
        ('feature', 'درخواست ویژگی'),
        ('bug', 'گزارش باگ'),
        ('question', 'سوال'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets', help_text="کاربر ایجاد کننده تیکت")
    title = models.CharField(max_length=255, help_text="عنوان تیکت")
    description = models.TextField(help_text="توضیحات تیکت")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', help_text="دسته‌بندی تیکت")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', help_text="اولویت تیکت")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', help_text="وضعیت تیکت")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    admin_response = models.TextField(blank=True, help_text="پاسخ ادمین")
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='admin_tickets',
        help_text="ادمین پاسخ دهنده"
    )
    
    class Meta:
        verbose_name = "تیکت"
        verbose_name_plural = "تیکت‌ها"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'priority']),
        ]
    
    def __str__(self):
        return f"تیکت #{self.id} - {self.title} - {self.user.username}"
    
    def mark_as_resolved(self, admin_user=None, response=''):
        """علامت‌گذاری تیکت به عنوان حل شده"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if admin_user:
            self.admin_user = admin_user
        if response:
            self.admin_response = response
        self.save()
    
    def close_ticket(self):
        """بستن تیکت"""
        self.status = 'closed'
        self.save()


class TicketMessage(models.Model):
    """پیام‌های تیکت (برای مکالمه)"""
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='messages', help_text="تیکت مربوطه")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_messages', help_text="ارسال کننده پیام")
    message = models.TextField(help_text="متن پیام")
    is_admin = models.BooleanField(default=False, help_text="آیا پیام از طرف ادمین است؟")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "پیام تیکت"
        verbose_name_plural = "پیام‌های تیکت"
        ordering = ['created_at']
    
    def __str__(self):
        sender = "ادمین" if self.is_admin else "کاربر"
        return f"پیام از {sender} - تیکت #{self.ticket.id}"


class StrategyOptimization(models.Model):
    """نتایج بهینه‌سازی استراتژی با استفاده از ML/DL"""
    
    OPTIMIZATION_METHOD_CHOICES = [
        ('ml', 'Machine Learning'),
        ('dl', 'Deep Learning'),
        ('hybrid', 'Hybrid (ML + DL)'),
        ('auto', 'Auto'),
    ]
    
    OPTIMIZATION_STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('running', 'در حال اجرا'),
        ('completed', 'تکمیل شده'),
        ('failed', 'خطا'),
        ('cancelled', 'لغو شده'),
    ]
    
    OBJECTIVE_CHOICES = [
        ('sharpe_ratio', 'Sharpe Ratio'),
        ('total_return', 'Total Return'),
        ('win_rate', 'Win Rate'),
        ('profit_factor', 'Profit Factor'),
        ('combined', 'Combined'),
    ]
    
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE, related_name='optimizations')
    method = models.CharField(max_length=20, choices=OPTIMIZATION_METHOD_CHOICES, default='auto')
    optimizer_type = models.CharField(max_length=20, default='ml', help_text="ml or dl")
    objective = models.CharField(max_length=20, choices=OBJECTIVE_CHOICES, default='sharpe_ratio')
    status = models.CharField(max_length=20, choices=OPTIMIZATION_STATUS_CHOICES, default='pending')
    
    # Original parameters (before optimization)
    original_params = models.JSONField(null=True, blank=True, help_text="پارامترهای اولیه استراتژی")
    
    # Optimized parameters
    optimized_params = models.JSONField(null=True, blank=True, help_text="پارامترهای بهینه شده")
    
    # Results
    best_score = models.FloatField(null=True, blank=True, help_text="بهترین امتیاز بدست آمده")
    optimization_history = models.JSONField(default=list, blank=True, help_text="تاریخچه بهینه‌سازی")
    
    # Comparison with original
    original_score = models.FloatField(null=True, blank=True, help_text="امتیاز استراتژی اولیه")
    improvement_percent = models.FloatField(null=True, blank=True, help_text="درصد بهبود")
    
    # Optimization settings
    optimization_settings = models.JSONField(default=dict, blank=True, help_text="تنظیمات بهینه‌سازی")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, help_text="پیام خطا در صورت شکست")
    
    class Meta:
        verbose_name = "Strategy Optimization"
        verbose_name_plural = "Strategy Optimizations"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['strategy', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Optimization for {self.strategy.name} - {self.get_method_display()} - {self.status}"
    
    def calculate_improvement(self):
        """محاسبه درصد بهبود"""
        if self.original_score is not None and self.best_score is not None:
            if self.original_score != 0:
                self.improvement_percent = ((self.best_score - self.original_score) / abs(self.original_score)) * 100
            else:
                self.improvement_percent = 100.0 if self.best_score > 0 else 0.0
            self.save(update_fields=['improvement_percent'])


class Wallet(models.Model):
    """کیف پول کاربر برای پرداخت پیشنهادات AI"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="موجودی به تومان")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "کیف پول"
        verbose_name_plural = "کیف پول‌ها"
    
    def __str__(self):
        return f"کیف پول {self.user.username} - {self.balance:,} تومان"
    
    def charge(self, amount: float):
        """شارژ حساب"""
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
    
    def deduct(self, amount: float) -> bool:
        """کسر از موجودی - فقط در صورت کافی بودن موجودی"""
        if self.balance >= amount:
            self.balance -= amount
            self.save(update_fields=['balance', 'updated_at'])
            return True
        return False


class GoldPriceSubscription(models.Model):
    """اشتراک دریافت قیمت لحظه‌ای طلا"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gold_price_subscription')
    is_active = models.BooleanField(default=False, help_text="وضعیت اشتراک")
    start_date = models.DateTimeField(null=True, blank=True, help_text="تاریخ شروع اشتراک")
    end_date = models.DateTimeField(null=True, blank=True, help_text="تاریخ پایان اشتراک")
    monthly_price = models.DecimalField(max_digits=12, decimal_places=2, default=300000, help_text="قیمت ماهانه به تومان")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "اشتراک قیمت طلا"
        verbose_name_plural = "اشتراک‌های قیمت طلا"
    
    def __str__(self):
        return f"اشتراک {self.user.username} - {'فعال' if self.is_active else 'غیرفعال'}"
    
    def is_valid(self):
        """بررسی معتبر بودن اشتراک"""
        if not self.is_active:
            return False
        if self.end_date and timezone.now() > self.end_date:
            self.is_active = False
            self.save()
            return False
        return True
    
    def extend_subscription(self, months: int = 1):
        """تمدید اشتراک"""
        if self.end_date and self.end_date > timezone.now():
            self.end_date += timedelta(days=30 * months)
        else:
            self.start_date = timezone.now()
            self.end_date = timezone.now() + timedelta(days=30 * months)
        self.is_active = True
        self.save()


class Transaction(models.Model):
    """تراکنش‌های مالی"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('charge', 'شارژ'),
        ('payment', 'پرداخت'),
        ('refund', 'بازگشت وجه'),
        ('subscription_purchase', 'خرید اشتراک'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'در انتظار'),
        ('completed', 'تکمیل شده'),
        ('failed', 'ناموفق'),
        ('cancelled', 'لغو شده'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=25, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="مبلغ به تومان")
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    description = models.TextField(blank=True, help_text="توضیحات تراکنش")
    
    # زرین‌پال
    zarinpal_authority = models.CharField(max_length=255, blank=True, help_text="Authority از زرین‌پال")
    zarinpal_ref_id = models.CharField(max_length=255, blank=True, help_text="Ref ID از زرین‌پال")
    
    # ارتباط با پیشنهاد AI
    ai_recommendation = models.ForeignKey('AIRecommendation', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount:,} تومان - {self.get_status_display()}"


class AIRecommendation(models.Model):
    """پیشنهادات هوش مصنوعی برای بهبود استراتژی"""
    
    RECOMMENDATION_TYPE_CHOICES = [
        ('entry_condition', 'شرط ورود'),
        ('exit_condition', 'شرط خروج'),
        ('risk_management', 'مدیریت ریسک'),
        ('indicator', 'اندیکاتور'),
        ('parameter', 'پارامتر'),
        ('general', 'عمومی'),
    ]
    
    STATUS_CHOICES = [
        ('generated', 'تولید شده'),
        ('purchased', 'خریداری شده'),
        ('applied', 'اعمال شده'),
    ]
    
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE, related_name='ai_recommendations')
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
    title = models.CharField(max_length=255, help_text="عنوان پیشنهاد")
    description = models.TextField(help_text="توضیحات پیشنهاد")
    recommendation_data = models.JSONField(default=dict, help_text="داده‌های پیشنهاد (JSON)")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=150000, help_text="قیمت به تومان")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generated')
    
    # کاربری که خرید کرده
    purchased_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchased_recommendations')
    purchased_at = models.DateTimeField(null=True, blank=True)
    
    # آیا به استراتژی اعمال شده
    applied_to_strategy = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "پیشنهاد AI"
        verbose_name_plural = "پیشنهادات AI"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.strategy.name}"


class SystemSettings(models.Model):
    """تنظیمات سیستم برای مدیریت ویژگی‌های مختلف"""
    
    # استفاده از Singleton pattern - فقط یک رکورد داشته باشیم
    class Meta:
        verbose_name = "تنظیمات سیستم"
        verbose_name_plural = "تنظیمات سیستم"
    
    # Google Authentication
    google_auth_enabled = models.BooleanField(
        default=False, 
        help_text="فعال/غیرفعال کردن ورود با گوگل"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # فقط یک رکورد داشته باشیم
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # جلوگیری از حذف - فقط reset می‌کنیم
        pass
    
    @classmethod
    def load(cls):
        """بارگذاری تنظیمات سیستم (Singleton)"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return "تنظیمات سیستم"


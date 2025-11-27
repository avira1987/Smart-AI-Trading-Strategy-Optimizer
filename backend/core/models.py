from django.db import models, transaction
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
        ('openai', 'OpenAI (ChatGPT)'),
        # Explicit aliases for OpenAI so users can pick the label they expect in the dashboard
        ('chatgpt', 'ChatGPT (alias of OpenAI)'),
        ('gpt', 'GPT (alias of OpenAI)'),
        ('gpt4', 'GPT-4 (alias of OpenAI)'),
        ('gpt-4', 'GPT-4 (alias of OpenAI)'),
        ('cohere', 'Cohere AI'),
        ('openrouter', 'OpenRouter'),
        ('together_ai', 'Together AI'),
        ('deepinfra', 'DeepInfra'),
        ('groq', 'GroqCloud'),
        ('gapgpt', 'GapGPT'),
        ('kavenegar', 'Kavenegar (SMS)'),
        ('zarinpal', 'Zarinpal (Merchant ID)'),
        ('recaptcha', 'reCAPTCHA v3 (Site Key & Secret Key)'),
    ]
    
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='api_configurations',
        null=True,
        blank=True,
        help_text="مالک کلید API؛ اگر خالی باشد کلید سیستمی است"
    )
    
    class Meta:
        verbose_name = "API Configuration"
        verbose_name_plural = "API Configurations"
        # Remove unique constraint to allow multiple API keys per provider
        # unique_together = ['provider']
        indexes = [
            models.Index(fields=['provider', 'user']),
        ]
    
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
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='strategies',
        null=True,
        blank=True,
        help_text="کاربر صاحب استراتژی"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    strategy_file = models.FileField(upload_to='strategies/')
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False, help_text="استراتژی اصلی کاربر در داشبورد")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    parsed_strategy_data = models.JSONField(null=True, blank=True, help_text="Parsed strategy data from NLP processing")
    processing_status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='not_processed')
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True, help_text="Error message if processing failed")
    # منابع تحلیل استفاده شده
    analysis_sources = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="اطلاعات منابع تحلیل استفاده شده (مثلاً: ai_model, nlp_parser, analysis_method)"
    )
    
    class Meta:
        verbose_name = "Trading Strategy"
        verbose_name_plural = "Trading Strategies"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'uploaded_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_strategy'
            )
        ]
    
    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_primary:
                base_queryset = TradingStrategy.objects.filter(is_primary=True)
                if self.pk:
                    base_queryset = base_queryset.exclude(pk=self.pk)
                base_queryset.update(is_primary=False)
            super().save(*args, **kwargs)


class StrategyMarketplaceListing(models.Model):
    """اطلاعات استراتژی‌هایی که در مارکت‌پلیس منتشر می‌شوند."""

    strategy = models.OneToOneField(
        TradingStrategy,
        on_delete=models.CASCADE,
        related_name='marketplace_entry',
        help_text="استراتژی اصلی که منتشر می‌شود"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='strategy_listings',
        help_text="کاربر منتشرکننده"
    )
    title = models.CharField(max_length=255, help_text="عنوان قابل نمایش در مارکت‌پلیس")
    headline = models.CharField(max_length=500, blank=True, help_text="خلاصه کوتاه برای جذب مخاطب")
    description = models.TextField(blank=True, help_text="توضیحات کامل مارکت‌پلیس")
    shared_text = models.TextField(blank=True, help_text="نسخه متنی/پارامترهای استراتژی برای مطالعه کاربران")
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="هزینه اجاره به تومان")
    billing_cycle_days = models.PositiveIntegerField(default=30, help_text="مدت دوره اجاره پس از پرداخت (روز)")
    trial_days = models.PositiveIntegerField(default=9, help_text="طول دوره آزمایشی رایگان (روز)")
    trial_backtest_limit = models.PositiveIntegerField(
        default=3,
        help_text="حداکثر تعداد بک‌تست مجاز در دوره آزمایشی"
    )
    performance_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="خلاصه نتایج تست‌های مالک (بازده، دراودان و ...)"
    )
    sample_results = models.JSONField(
        default=list,
        blank=True,
        help_text="لیست نتایج نمونه بک‌تست‌ها برای نمایش عمومی"
    )
    supported_symbols = models.JSONField(
        default=list,
        blank=True,
        help_text="نمادها/بازارهای پیشنهادی برای این استراتژی"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="برچسب‌ها برای جست‌وجو در مارکت‌پلیس"
    )
    source_result = models.ForeignKey(
        'Result',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='marketplace_listings',
        help_text="نتیجه بک‌تست مورد استفاده برای این لیست"
    )
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Strategy Marketplace Listing"
        verbose_name_plural = "Strategy Marketplace Listings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_published', 'published_at']),
            models.Index(fields=['owner', 'is_published']),
        ]

    def __str__(self):
        return f"{self.title} (#{self.id})"

    def mark_published(self):
        """انتشار لیست استراتژی در مارکت‌پلیس."""
        if not self.is_published:
            self.is_published = True
            self.published_at = timezone.now()
            self.save(update_fields=['is_published', 'published_at', 'updated_at'])

    def mark_unpublished(self):
        """لغو انتشار استراتژی در مارکت‌پلیس."""
        if self.is_published:
            self.is_published = False
            self.save(update_fields=['is_published', 'updated_at'])


class StrategyListingAccess(models.Model):
    """دسترسی کاربران به استراتژی‌های مارکت‌پلیس (آزمایشی یا پولی)."""

    STATUS_CHOICES = [
        ('trial', 'دوره آزمایشی'),
        ('active', 'فعال'),
        ('expired', 'منقضی شده'),
        ('cancelled', 'لغو شده'),
    ]

    listing = models.ForeignKey(
        StrategyMarketplaceListing,
        on_delete=models.CASCADE,
        related_name='accesses',
        help_text="استراتژی مارکت‌پلیس"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='strategy_accesses',
        help_text="کاربر دریافت‌کننده دسترسی"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    trial_started_at = models.DateTimeField(null=True, blank=True)
    trial_expires_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_payment_transaction = models.ForeignKey(
        'Transaction',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='listing_accesses'
    )
    total_backtests_run = models.PositiveIntegerField(default=0, help_text="تعداد کل بک‌تست‌های اجرا شده")
    last_backtest_at = models.DateTimeField(null=True, blank=True)
    last_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="مبلغ آخرین پرداخت شده")
    platform_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10.0, help_text="درصد سهم پلتفرم")
    platform_fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="مبلغ سهم پلتفرم")
    owner_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="مبلغ سهم صاحب استراتژی")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Strategy Listing Access"
        verbose_name_plural = "Strategy Listing Accesses"
        unique_together = ('listing', 'user')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['listing', 'status']),
        ]

    def __str__(self):
        return f"Access {self.user.username} -> {self.listing.title} ({self.status})"

    def ensure_status(self, save: bool = True) -> str:
        """به‌روزرسانی وضعیت دسترسی بر اساس تاریخ انقضا."""
        now = timezone.now()
        new_status = self.status
        if self.status == 'trial' and self.trial_expires_at and self.trial_expires_at < now:
            new_status = 'expired'
        elif self.status == 'active' and self.expires_at and self.expires_at < now:
            new_status = 'expired'

        if new_status != self.status:
            self.status = new_status
            if save:
                self.save(update_fields=['status', 'updated_at'])
        return self.status

    def has_active_access(self) -> bool:
        """بررسی فعال بودن دسترسی (آزمایشی یا پولی)."""
        self.ensure_status()
        now = timezone.now()
        if self.status == 'trial' and self.trial_expires_at and self.trial_expires_at >= now:
            return True
        if self.status == 'active' and (self.expires_at is None or self.expires_at >= now):
            return True
        return False

    def is_trial_active(self) -> bool:
        """آیا دوره آزمایشی هنوز فعال است؟"""
        self.ensure_status()
        return self.status == 'trial'

    def remaining_trial_seconds(self) -> int:
        """بازمانده دوره آزمایشی به ثانیه."""
        if not self.trial_expires_at:
            return 0
        delta = self.trial_expires_at - timezone.now()
        return max(int(delta.total_seconds()), 0)

    def remaining_active_seconds(self) -> int:
        """بازمانده اشتراک فعال به ثانیه."""
        if not self.expires_at:
            return 0
        delta = self.expires_at - timezone.now()
        return max(int(delta.total_seconds()), 0)

    def increment_backtests(self, amount: int = 1, save: bool = True):
        self.total_backtests_run += amount
        self.last_backtest_at = timezone.now()
        if save:
            self.save(update_fields=['total_backtests_run', 'last_backtest_at', 'updated_at'])


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

    MARKETPLACE_ORIGIN_CHOICES = [
        ('direct', 'مستقیم'),
        ('marketplace_trial', 'مارکت‌پلیس - دوره آزمایشی'),
        ('marketplace_active', 'مارکت‌پلیس - اشتراک فعال'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='jobs',
        help_text="کاربری که job را ایجاد کرده است"
    )
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    result = models.ForeignKey('Result', null=True, blank=True, on_delete=models.SET_NULL, related_name='job_set')
    error_message = models.TextField(blank=True)
    marketplace_access = models.ForeignKey(
        StrategyListingAccess,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='jobs',
        help_text="اگر job از طریق مارکت‌پلیس ایجاد شده باشد"
    )
    origin = models.CharField(max_length=30, choices=MARKETPLACE_ORIGIN_CHOICES, default='direct')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['origin', 'created_at']),
        ]
    
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
    # منابع داده استفاده شده
    data_sources = models.JSONField(
        default=dict, 
        blank=True, 
        help_text="اطلاعات منابع داده استفاده شده در بک‌تست (مثلاً: provider, symbol, date_range)"
    )
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


class UserProfile(models.Model):
    """Extended user profile with phone number"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=15, unique=True, help_text="شماره موبایل به فرمت 09123456789")
    nickname = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="نیک‌نیم قابل نمایش در مارکت‌پلیس")
    preferred_symbol = models.CharField(max_length=50, null=True, blank=True, default='XAUUSD', help_text="نماد معاملاتی ترجیحی کاربر")
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


class UserGoldAPIAccess(models.Model):
    """تنظیمات دسترسی کاربر به API قیمت طلا"""
    
    SOURCE_CHOICES = [
        ('user', 'ثبت توسط کاربر'),
        ('admin', 'ثبت توسط ادمین'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gold_api_access')
    provider = models.CharField(max_length=100, blank=True, help_text="نام ارائه‌دهنده API (مثلاً: TwelveData, FinancialModelingPrep)")
    api_key = models.CharField(max_length=255, blank=True, help_text="کلید API اختصاصی کاربر")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='user', help_text="منبع ثبت اطلاعات")
    assigned_by_admin = models.BooleanField(default=False, help_text="آیا این دسترسی توسط ادمین ثبت شده است؟")
    allow_mt5_access = models.BooleanField(
        default=False,
        help_text="اجازه دریافت قیمت طلا از MetaTrader 5 توسط این کاربر (تعیین شده توسط ادمین)"
    )
    assigned_at = models.DateTimeField(null=True, blank=True, help_text="تاریخ ثبت/تخصیص دسترسی فعال")
    notes = models.TextField(blank=True, help_text="توضیحات تکمیلی برای کاربر یا ادمین")
    is_active = models.BooleanField(default=True, help_text="وضعیت فعال بودن دسترسی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "دسترسی API طلا"
        verbose_name_plural = "دسترسی‌های API طلا"
    
    def __str__(self):
        return f"{self.user.username} - {self.provider or 'بدون ارائه‌دهنده'}"
    
    @property
    def has_credentials(self) -> bool:
        return bool(self.provider and self.api_key and self.is_active)


class GoldAPIAccessRequest(models.Model):
    """درخواست کاربران برای دریافت API قیمت طلا توسط ادمین"""
    
    STATUS_CHOICES = [
        ('pending_payment', 'در انتظار پرداخت'),
        ('awaiting_admin', 'در انتظار اقدام ادمین'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gold_api_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    preferred_provider = models.CharField(max_length=100, blank=True, help_text="ارائه‌دهنده پیشنهادی از سمت کاربر")
    user_notes = models.TextField(blank=True, help_text="توضیحات کاربر هنگام ثبت درخواست")
    admin_notes = models.TextField(blank=True, help_text="توضیحات ادمین")
    price_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="مبلغ پرداخت شده برای این درخواست")
    transaction = models.OneToOneField(
        'Transaction',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='gold_api_access_request',
        help_text="تراکنش مربوط به این درخواست"
    )
    payment_confirmed_at = models.DateTimeField(null=True, blank=True, help_text="تاریخ تایید پرداخت")
    assigned_provider = models.CharField(max_length=100, blank=True, help_text="ارائه‌دهنده اختصاص داده شده توسط ادمین")
    assigned_api_key = models.CharField(max_length=255, blank=True, help_text="کلید API اختصاص داده شده")
    assigned_at = models.DateTimeField(null=True, blank=True, help_text="تاریخ ثبت API توسط ادمین")
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_gold_api_requests',
        help_text="ادمینی که API را ثبت کرده است"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "درخواست API طلا"
        verbose_name_plural = "درخواست‌های API طلا"
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=models.Q(status__in=['pending_payment', 'awaiting_admin']),
                name='unique_active_gold_api_request_per_user'
            )
        ]
    
    def __str__(self):
        return f"درخواست API طلا #{self.id} - {self.user.username} - {self.get_status_display()}"
    
    @property
    def is_pending_admin(self) -> bool:
        return self.status in ['pending_payment', 'awaiting_admin']


class Transaction(models.Model):
    """تراکنش‌های مالی"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('charge', 'شارژ'),
        ('payment', 'پرداخت'),
        ('refund', 'بازگشت وجه'),
        ('subscription_purchase', 'خرید اشتراک'),
        ('gold_api_request', 'درخواست API طلا'),
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

    # Feature flags
    live_trading_enabled = models.BooleanField(
        default=False,
        help_text="فعال/غیرفعال کردن نمایش بخش معاملات زنده در وب‌سایت"
    )
    
    use_ai_cache = models.BooleanField(
        default=True,
        help_text="استفاده از کش برای پردازش تبدیل متن انسانی به مدل هوش مصنوعی. اگر غیرفعال شود، همیشه از API استفاده می‌شود."
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


class APIUsageLog(models.Model):
    """ردیابی استفاده از API ها و محاسبه هزینه"""
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='api_usage_logs',
        help_text="کاربری که از API استفاده کرده است"
    )
    provider = models.CharField(max_length=50, help_text="نام ارائه‌دهنده API")
    endpoint = models.CharField(max_length=255, blank=True, help_text="آدرس endpoint فراخوانی شده")
    request_type = models.CharField(max_length=10, default='GET', help_text="نوع درخواست (GET, POST, etc.)")
    status_code = models.IntegerField(null=True, blank=True, help_text="کد وضعیت پاسخ")
    success = models.BooleanField(default=True, help_text="آیا درخواست موفق بود؟")
    cost = models.DecimalField(max_digits=12, decimal_places=6, default=0.0, help_text="هزینه به دلار")
    cost_toman = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="هزینه به تومان")
    response_time_ms = models.FloatField(null=True, blank=True, help_text="زمان پاسخ به میلی‌ثانیه")
    error_message = models.TextField(blank=True, help_text="پیام خطا در صورت وجود")
    metadata = models.JSONField(default=dict, blank=True, help_text="اطلاعات اضافی")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "لاگ استفاده از API"
        verbose_name_plural = "لاگ‌های استفاده از API"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'provider', 'created_at']),
            models.Index(fields=['provider', 'created_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['provider', 'success']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        status = "موفق" if self.success else "ناموفق"
        username = self.user.username if self.user else "سیستم"
        return f"{username} - {self.provider} - {status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class UserActivityLog(models.Model):
    """لاگ فعالیت‌های کاربر برای نمایش در پروفایل"""
    
    ACTION_TYPE_CHOICES = [
        ('strategy_processed', 'پردازش استراتژی'),
        ('strategy_created', 'ایجاد استراتژی'),
        ('strategy_deleted', 'حذف استراتژی'),
        ('backtest_run', 'اجرای بک‌تست'),
        ('trade_opened', 'باز کردن معامله'),
        ('trade_closed', 'بستن معامله'),
        ('api_key_added', 'افزودن کلید API'),
        ('api_key_removed', 'حذف کلید API'),
        ('wallet_charged', 'شارژ کیف پول'),
        ('profile_updated', 'به‌روزرسانی پروفایل'),
        ('other', 'سایر'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        help_text="کاربری که این فعالیت را انجام داده است"
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPE_CHOICES,
        help_text="نوع فعالیت"
    )
    action_description = models.TextField(
        help_text="توضیحات فعالیت"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="اطلاعات اضافی (مثل تعداد توکن‌ها، نام استراتژی، و غیره)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "لاگ فعالیت کاربر"
        verbose_name_plural = "لاگ‌های فعالیت کاربران"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class UserScore(models.Model):
    """سیستم امتیازدهی کاربران برای گیمیفیکیشن"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_score')
    total_points = models.IntegerField(default=0, help_text="مجموع امتیازات کاربر")
    level = models.IntegerField(default=1, help_text="سطح کاربر (بر اساس امتیاز)")
    backtests_completed = models.IntegerField(default=0, help_text="تعداد بک‌تست‌های انجام شده")
    strategies_created = models.IntegerField(default=0, help_text="تعداد استراتژی‌های ایجاد شده")
    optimizations_completed = models.IntegerField(default=0, help_text="تعداد بهینه‌سازی‌های انجام شده")
    best_return = models.FloatField(default=0.0, help_text="بهترین بازدهی در بک‌تست")
    total_trades = models.IntegerField(default=0, help_text="مجموع معاملات انجام شده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "امتیاز کاربر"
        verbose_name_plural = "امتیازات کاربران"
        ordering = ['-total_points']
    
    def __str__(self):
        return f"{self.user.username} - {self.total_points} امتیاز - سطح {self.level}"
    
    def calculate_level(self):
        """محاسبه سطح بر اساس امتیاز"""
        if self.total_points < 100:
            return 1
        elif self.total_points < 500:
            return 2
        elif self.total_points < 1000:
            return 3
        elif self.total_points < 2500:
            return 4
        elif self.total_points < 5000:
            return 5
        elif self.total_points < 10000:
            return 6
        elif self.total_points < 25000:
            return 7
        elif self.total_points < 50000:
            return 8
        elif self.total_points < 100000:
            return 9
        else:
            return 10
    
    def add_points(self, points: int, reason: str = ""):
        """افزودن امتیاز به کاربر"""
        self.total_points += points
        old_level = self.level
        self.level = self.calculate_level()
        self.save(update_fields=['total_points', 'level', 'updated_at'])
        
        # اگر سطح افزایش یافت، یک دستاورد ایجاد می‌کنیم
        if self.level > old_level:
            achievement, _ = Achievement.objects.get_or_create(
                code=f'level_{self.level}',
                defaults={
                    'name': f'سطح {self.level}',
                    'description': f'رسیدن به سطح {self.level}',
                    'icon': '⭐',
                    'points_reward': 0,
                    'category': 'level',
                    'condition_type': 'level',
                    'condition_value': float(self.level)
                }
            )
            UserAchievement.objects.get_or_create(
                user=self.user,
                achievement=achievement,
                defaults={'unlocked_at': timezone.now()}
            )
        
        return self.level > old_level


class Achievement(models.Model):
    """دستاوردهای قابل دریافت"""
    code = models.CharField(max_length=100, unique=True, help_text="کد یکتا برای دستاورد")
    name = models.CharField(max_length=200, help_text="نام دستاورد")
    description = models.TextField(help_text="توضیحات دستاورد")
    icon = models.CharField(max_length=10, default='🏆', help_text="آیکون دستاورد")
    points_reward = models.IntegerField(default=0, help_text="امتیاز جایزه")
    category = models.CharField(
        max_length=50,
        choices=[
            ('backtest', 'بک‌تست'),
            ('strategy', 'استراتژی'),
            ('optimization', 'بهینه‌سازی'),
            ('trading', 'معاملات'),
            ('social', 'اجتماعی'),
            ('level', 'سطح'),
        ],
        default='backtest',
        help_text="دسته‌بندی دستاورد"
    )
    condition_type = models.CharField(
        max_length=50,
        choices=[
            ('backtest_count', 'تعداد بک‌تست'),
            ('return_threshold', 'آستانه بازدهی'),
            ('win_rate_threshold', 'آستانه نرخ برد'),
            ('trades_count', 'تعداد معاملات'),
            ('strategy_count', 'تعداد استراتژی'),
            ('optimization_count', 'تعداد بهینه‌سازی'),
            ('level', 'سطح'),
        ],
        help_text="نوع شرط برای دریافت دستاورد"
    )
    condition_value = models.FloatField(help_text="مقدار شرط")
    is_active = models.BooleanField(default=True, help_text="آیا دستاورد فعال است")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "دستاورد"
        verbose_name_plural = "دستاوردها"
        ordering = ['category', 'points_reward']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class UserAchievement(models.Model):
    """دستاوردهای دریافت شده توسط کاربران"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "دستاورد کاربر"
        verbose_name_plural = "دستاوردهای کاربران"
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
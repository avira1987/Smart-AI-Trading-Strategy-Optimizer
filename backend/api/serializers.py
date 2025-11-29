from rest_framework import serializers
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from core.models import (
    APIConfiguration,
    TradingStrategy,
    Job,
    Result,
    LiveTrade,
    AutoTradingSettings,
    StrategyMarketplaceListing,
    StrategyListingAccess,
)
from core.models import (
    UserProfile,
    OTPCode,
    Device,
    StrategyQuestion,
    Ticket,
    TicketMessage,
    StrategyOptimization,
)
from core.models import Wallet, Transaction, AIRecommendation, SystemSettings, UserGoldAPIAccess, GoldAPIAccessRequest
from core.models import UserScore, Achievement, UserAchievement
from django.contrib.auth.models import User
import re


class APIConfigurationSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_username = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = APIConfiguration
        fields = [
            'id',
            'provider',
            'api_key',
            'is_active',
            'created_at',
            'updated_at',
            'user',
            'owner_username',
            'is_owner',
        ]
        read_only_fields = ['created_at', 'updated_at', 'user', 'owner_username', 'is_owner']
    
    def validate_api_key(self, value):
        """Validate API key is not empty and has reasonable length"""
        if not value or not value.strip():
            raise serializers.ValidationError('کلید API نمی‌تواند خالی باشد')
        
        # Check length (max 255 as per model, but warn if too short for some providers)
        if len(value.strip()) < 3:
            raise serializers.ValidationError('کلید API خیلی کوتاه است')
        
        return value.strip()

    def get_owner_username(self, obj):
        if obj.user:
            return obj.user.get_username()
        return None

    def get_is_owner(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user_id == request.user.id
    
    def validate(self, data):
        """Validate the entire object"""
        provider = data.get('provider', '')
        api_key = data.get('api_key', '')
        
        # Specific validation for Zarinpal Merchant ID
        if provider == 'zarinpal':
            if not api_key or not api_key.strip():
                raise serializers.ValidationError({
                    'api_key': 'Merchant ID زرین‌پال نمی‌تواند خالی باشد'
                })
            
            merchant_id = api_key.strip()
            
            # Check length (max 255 as per model)
            if len(merchant_id) > 255:
                raise serializers.ValidationError({
                    'api_key': 'Merchant ID زرین‌پال خیلی طولانی است (حداکثر 255 کاراکتر)'
                })
            
            # Check minimum length (Merchant IDs are usually at least 10 characters)
            if len(merchant_id) < 10:
                raise serializers.ValidationError({
                    'api_key': 'Merchant ID زرین‌پال خیلی کوتاه است (حداقل 10 کاراکتر)'
                })
            
            # Basic format check - should contain at least some alphanumeric characters
            # Allow alphanumeric, dashes, underscores, and dots (common in UUIDs and IDs)
            if not any(c.isalnum() for c in merchant_id):
                raise serializers.ValidationError({
                    'api_key': 'فرمت Merchant ID زرین‌پال نامعتبر است. باید شامل حداقل یک حرف یا عدد باشد'
                })
        
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')

        if not request or not request.user or not request.user.is_authenticated:
            data['api_key'] = None
            return data

        # Staff/admin users can view full keys
        if request.user.is_staff or request.user.is_superuser:
            return data

        # Owners can view their own keys
        if instance.user_id == request.user.id:
            return data

        # Hide keys that belong to system/admin accounts
        if self._belongs_to_admin(instance):
            data['api_key'] = None
        else:
            data['api_key'] = None
        return data

    @staticmethod
    def _belongs_to_admin(instance) -> bool:
        admin_phone = getattr(settings, "ADMIN_PHONE_NUMBER", "09035760718")
        if not admin_phone:
            return False
        user = getattr(instance, "user", None)
        if user is None:
            return True
        profile = getattr(user, "userprofile", None)
        user_phone = getattr(profile, "phone", None)
        return str(user_phone) == str(admin_phone)


class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['live_trading_enabled', 'use_ai_cache', 'token_cost_per_1000', 'backtest_cost', 'strategy_processing_cost', 'registration_bonus']


class PublicSystemSettingsSerializer(serializers.Serializer):
    live_trading_enabled = serializers.BooleanField()


class TradingStrategySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    questions_count = serializers.SerializerMethodField()
    analysis_sources_display = serializers.SerializerMethodField()
    marketplace_listing_id = serializers.SerializerMethodField()
    marketplace_listing_status = serializers.SerializerMethodField()
    
    class Meta:
        model = TradingStrategy
        fields = ['id', 'user', 'name', 'description', 'strategy_file', 'is_active', 'is_primary', 'uploaded_at',
                  'parsed_strategy_data', 'processing_status', 'processed_at', 'processing_error', 
                  'questions_count', 'analysis_sources', 'analysis_sources_display',
                  'marketplace_listing_id', 'marketplace_listing_status']
        read_only_fields = ['user', 'uploaded_at', 'parsed_strategy_data', 'processing_status', 'processed_at', 
                           'processing_error', 'questions_count', 'analysis_sources', 'analysis_sources_display']
    
    def get_questions_count(self, obj):
        return obj.questions.count()
    
    def get_analysis_sources_display(self, obj):
        """تبدیل اطلاعات منابع تحلیل به فرمت قابل نمایش"""
        if not obj.analysis_sources:
            return {}
        
        method_names = {
            'gemini_ai': 'هوش مصنوعی Gemini',
            'openai_ai': 'هوش مصنوعی OpenAI (ChatGPT)',
            'basic_analysis': 'تحلیل پایه',
            'failed': 'ناموفق',
            None: 'نامشخص'
        }
        
        ai_model_names = {
            'gemini': 'Google Gemini AI',
            'openai': 'OpenAI (ChatGPT)',
            None: 'هیچکدام'
        }
        
        provider_names = {
            'financialmodelingprep': 'Financial Modeling Prep',
            'twelvedata': 'TwelveData',
            'alphavantage': 'Alpha Vantage',
            'oanda': 'OANDA',
            'metalsapi': 'MetalsAPI',
            'mt5': 'MetaTrader 5',
            'openai': 'OpenAI (ChatGPT)',
            'gemini': 'Google Gemini AI',
            'unknown': 'نامشخص'
        }
        
        data = obj.analysis_sources.copy()
        method = data.get('analysis_method')
        ai_model = data.get('ai_model')
        
        data['analysis_method_display'] = method_names.get(method, method)
        data['ai_model_display'] = ai_model_names.get(ai_model, ai_model)
        ai_status = data.get('ai_status')
        if ai_status:
            status_map = {
                'ok': 'موفق',
                'error': 'خطا',
                'disabled': 'غیرفعال',
                'unavailable': 'در دسترس نیست',
            }
            data['ai_status_display'] = status_map.get(ai_status, ai_status)
        data['nlp_parser_display'] = 'Parser NLP' if data.get('nlp_parser') else None

        duration_seconds = data.get('processing_duration_seconds')
        if (
            'processing_duration_display' not in data
            and isinstance(duration_seconds, (int, float))
        ):
            data['processing_duration_display'] = f"{duration_seconds:.2f} ثانیه"

        for timestamp_key in ('processing_started_at', 'processing_completed_at'):
            human_key = f"{timestamp_key}_display"
            timestamp_val = data.get(timestamp_key)
            if timestamp_val and human_key not in data:
                try:
                    normalized_value = (
                        timestamp_val.replace('Z', '+00:00')
                        if isinstance(timestamp_val, str)
                        else timestamp_val
                    )
                    parsed_dt = datetime.fromisoformat(normalized_value)
                    if timezone.is_naive(parsed_dt):
                        parsed_dt = timezone.make_aware(parsed_dt, timezone=timezone.utc)
                    local_dt = timezone.localtime(parsed_dt)
                    data[human_key] = local_dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    # If parsing fails, skip adding human readable value
                    continue

        if data.get('ai_fallback_reason') and 'ai_fallback_reason_display' not in data:
            data['ai_fallback_reason_display'] = data['ai_fallback_reason']

        if data.get('ai_message') and 'ai_message_display' not in data:
            data['ai_message_display'] = data['ai_message']

        attempts = data.get('ai_attempts')
        if attempts and isinstance(attempts, list):
            formatted_attempts = []
            for attempt in attempts:
                if not isinstance(attempt, dict):
                    continue
                provider_name = attempt.get('provider')
                formatted_attempts.append({
                    'provider': provider_names.get(provider_name, provider_name),
                    'success': attempt.get('success'),
                    'error': attempt.get('error'),
                    'status_code': attempt.get('status_code'),
                    'latency_ms': attempt.get('latency_ms'),
                })
            data['ai_attempts_display'] = formatted_attempts
        
        # پردازش و نمایش اطلاعات منابع داده در تحلیل
        if 'data_sources' in data and data['data_sources']:
            data_sources = data['data_sources'].copy()
            
            # تبدیل نام ارائه‌دهندگان به نام‌های قابل نمایش
            available_providers = data_sources.get('available_providers', [])
            if available_providers:
                data_sources['available_providers_display'] = [
                    provider_names.get(provider, provider) 
                    for provider in available_providers
                ]
                data_sources['available_providers_names_fa'] = [
                    provider_names.get(provider, provider) 
                    for provider in available_providers
                ]
            
            # اضافه کردن اطلاعات خلاصه
            if data_sources.get('strategy_symbol'):
                data_sources['has_symbol'] = True
            if data_sources.get('strategy_timeframe'):
                data_sources['has_timeframe'] = True
            if data_sources.get('indicators_mentioned'):
                data_sources['indicators_count'] = len(data_sources.get('indicators_mentioned', []))
            
            data['data_sources_display'] = data_sources
        else:
            data['data_sources_display'] = {}

        genetic_info = data.get('genetic_optimization')
        if isinstance(genetic_info, dict):
            status_map = {
                'completed': 'تکمیل شد',
                'error': 'خطا',
                'no_data': 'داده در دسترس نیست',
            }
            genetic_display = {
                'status_display': status_map.get(genetic_info.get('status'), genetic_info.get('status')),
                'best_score': genetic_info.get('best_score'),
                'episodes': genetic_info.get('episodes'),
                'provider_display': provider_names.get(genetic_info.get('provider'), genetic_info.get('provider')),
                'data_points': genetic_info.get('data_points'),
                'message': genetic_info.get('message'),
            }
            data['genetic_optimization_display'] = genetic_display
        else:
            data['genetic_optimization_display'] = None
        
        return data

    def get_marketplace_listing_id(self, obj):
        entry = getattr(obj, 'marketplace_entry', None)
        return entry.id if entry else None

    def get_marketplace_listing_status(self, obj):
        entry = getattr(obj, 'marketplace_entry', None)
        if not entry:
            return None
        return 'published' if entry.is_published else 'draft'


class StrategyListingAccessSerializer(serializers.ModelSerializer):
    listing_id = serializers.IntegerField(source='listing.id', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_trial_active = serializers.SerializerMethodField()
    has_active_access = serializers.SerializerMethodField()
    remaining_trial_seconds = serializers.SerializerMethodField()
    remaining_active_seconds = serializers.SerializerMethodField()
    owner_username = serializers.CharField(source='listing.owner.username', read_only=True)
    trial_backtest_limit = serializers.IntegerField(source='listing.trial_backtest_limit', read_only=True)
    price = serializers.DecimalField(source='listing.price', read_only=True, max_digits=12, decimal_places=2)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    owner_display_name = serializers.SerializerMethodField()

    class Meta:
        model = StrategyListingAccess
        fields = [
            'id',
            'listing_id',
            'listing_title',
            'user_id',
            'username',
            'owner_display_name',
            'status',
            'status_display',
            'trial_started_at',
            'trial_expires_at',
            'activated_at',
            'expires_at',
            'total_backtests_run',
            'last_backtest_at',
            'is_trial_active',
            'has_active_access',
            'remaining_trial_seconds',
            'remaining_active_seconds',
            'owner_username',
            'trial_backtest_limit',
            'price',
            'last_price',
            'platform_fee_percent',
            'platform_fee_amount',
            'owner_amount',
        ]
        read_only_fields = [
            'status',
            'trial_started_at',
            'trial_expires_at',
            'activated_at',
            'expires_at',
            'total_backtests_run',
            'last_backtest_at',
            'last_price',
            'platform_fee_percent',
            'platform_fee_amount',
            'owner_amount',
        ]

    def get_is_trial_active(self, obj):
        return obj.is_trial_active()

    def get_has_active_access(self, obj):
        return obj.has_active_access()

    def get_remaining_trial_seconds(self, obj):
        return obj.remaining_trial_seconds()

    def get_remaining_active_seconds(self, obj):
        return obj.remaining_active_seconds()

    def get_owner_display_name(self, obj):
        profile = getattr(obj.listing.owner, 'profile', None)
        if profile and profile.nickname:
            return profile.nickname
        return obj.listing.owner.username


class StrategyMarketplaceListingWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyMarketplaceListing
        fields = [
            'id',
            'strategy',
            'title',
            'headline',
            'description',
            'shared_text',
            'price',
            'billing_cycle_days',
            'trial_days',
            'trial_backtest_limit',
            'supported_symbols',
            'tags',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            strategy = attrs.get('strategy')
            if strategy and strategy.user_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
                raise serializers.ValidationError({'strategy': 'شما مالک این استراتژی نیستید.'})
            if strategy:
                queryset = StrategyMarketplaceListing.objects.filter(strategy=strategy)
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({'strategy': 'برای این استراتژی قبلاً لیست دیگری ایجاد شده است.'})
        price = attrs.get('price')
        if price is not None and price < 0:
            raise serializers.ValidationError({'price': 'قیمت نمی‌تواند منفی باشد.'})
        return attrs


class StrategyMarketplaceListingSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    strategy_id = serializers.IntegerField(source='strategy.id', read_only=True)
    current_user_access = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    can_start_trial = serializers.SerializerMethodField()
    can_purchase = serializers.SerializerMethodField()
    owner_display_name = serializers.SerializerMethodField()
    source_result_id = serializers.IntegerField(source='source_result.id', read_only=True)

    class Meta:
        model = StrategyMarketplaceListing
        fields = [
            'id',
            'strategy_id',
            'strategy_name',
            'owner_id',
            'owner_username',
            'owner_display_name',
            'title',
            'headline',
            'description',
            'shared_text',
            'price',
            'billing_cycle_days',
            'trial_days',
            'trial_backtest_limit',
            'performance_snapshot',
            'sample_results',
            'supported_symbols',
            'tags',
            'is_published',
            'published_at',
            'created_at',
            'updated_at',
            'current_user_access',
            'is_owner',
            'can_start_trial',
            'can_purchase',
            'source_result_id',
        ]
        read_only_fields = [
            'strategy_id',
            'strategy_name',
            'owner_id',
            'owner_username',
            'owner_display_name',
            'performance_snapshot',
            'sample_results',
            'is_published',
            'published_at',
            'created_at',
            'updated_at',
            'current_user_access',
            'is_owner',
            'can_start_trial',
            'can_purchase',
            'source_result_id',
        ]

    def get_current_user_access(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        try:
            access = obj.accesses.get(user=user)
        except StrategyListingAccess.DoesNotExist:
            return None
        return StrategyListingAccessSerializer(access, context=self.context).data

    def get_is_owner(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and user.id == obj.owner_id)

    def get_owner_display_name(self, obj):
        profile = getattr(obj.owner, 'profile', None)
        if profile and profile.nickname:
            return profile.nickname
        return obj.owner.username

    def _get_access_for_user(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        try:
            return obj.accesses.get(user=user)
        except StrategyListingAccess.DoesNotExist:
            return None

    def get_can_start_trial(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not obj.is_published:
            return False
        if user.id == obj.owner_id:
            return False
        if obj.trial_days <= 0:
            return False
        access = self._get_access_for_user(obj)
        if not access:
            return True
        if access.trial_started_at:
            access.ensure_status(save=False)
            return False
        return True

    def get_can_purchase(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not obj.is_published:
            return False
        if user.id == obj.owner_id:
            return False
        access = self._get_access_for_user(obj)
        if not access:
            return True
        access.ensure_status(save=False)
        if access.status == 'active' and access.has_active_access():
            return False
        return True


class StrategyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyQuestion
        fields = ['id', 'strategy', 'question_text', 'question_type', 'options', 
                  'answer', 'status', 'order', 'created_at', 'answered_at', 'context']
        read_only_fields = ['created_at', 'answered_at']


class ResultSerializer(serializers.ModelSerializer):
    data_sources_display = serializers.SerializerMethodField()
    strategy_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Result
        fields = ['id', 'job', 'strategy_name', 'total_return', 'total_trades', 'winning_trades', 
                  'losing_trades', 'win_rate', 'max_drawdown', 'equity_curve_data',
                  'description', 'trades_details', 'data_sources', 'data_sources_display', 'created_at']
        read_only_fields = ['created_at', 'data_sources', 'data_sources_display', 'strategy_name']
    
    def get_strategy_name(self, obj):
        """Get strategy name from the related job"""
        if obj.job and obj.job.strategy:
            return obj.job.strategy.name
        return None
    
    def get_data_sources_display(self, obj):
        """تبدیل اطلاعات منابع داده به فرمت قابل نمایش"""
        if not obj.data_sources:
            return {}
        
        provider_names = {
            'financialmodelingprep': 'Financial Modeling Prep',
            'twelvedata': 'TwelveData',
            'alphavantage': 'Alpha Vantage',
            'oanda': 'OANDA',
            'metalsapi': 'MetalsAPI',
            'mt5': 'MetaTrader 5',
            'unknown': 'نامشخص'
        }
        
        data = obj.data_sources.copy()
        provider = data.get('provider', 'unknown')
        data['provider_display'] = provider_names.get(provider, provider)
        data['provider_name_fa'] = provider_names.get(provider, provider)
        
        return data


class JobSerializer(serializers.ModelSerializer):
    result = ResultSerializer(read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    marketplace_access = StrategyListingAccessSerializer(read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'strategy', 'strategy_name', 'job_type', 'status', 'created_at', 
                  'started_at', 'completed_at', 'result', 'error_message', 'origin', 'marketplace_access']
        read_only_fields = ['created_at', 'started_at', 'completed_at', 'status', 'result', 'error_message', 'origin', 'marketplace_access']


class JobCreateSerializer(serializers.Serializer):
    ai_provider = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="AI provider for backtest analysis (gapgpt, gemini, openai, or auto)")
    strategy = serializers.IntegerField()
    job_type = serializers.ChoiceField(choices=['backtest', 'demo_trade'])
    timeframe_days = serializers.IntegerField(required=False, min_value=1, default=365)
    symbol = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    initial_capital = serializers.FloatField(required=False, min_value=0, default=10000)
    selected_indicators = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    
    def validate(self, data):
        """Validate that symbol is required for backtest jobs"""
        job_type = data.get('job_type')
        symbol = data.get('symbol')
        
        if job_type == 'backtest':
            if not symbol or (isinstance(symbol, str) and not symbol.strip()):
                raise serializers.ValidationError({
                    'symbol': 'انتخاب جفت ارز برای بک‌تست اجباری است.'
                })
        
        return data


class LiveTradeSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = LiveTrade
        fields = ['id', 'strategy', 'strategy_name', 'mt5_ticket', 'symbol', 'trade_type',
                  'volume', 'open_price', 'current_price', 'stop_loss', 'take_profit',
                  'profit', 'swap', 'commission', 'status', 'opened_at', 'closed_at',
                  'close_price', 'close_reason']
        read_only_fields = ['mt5_ticket', 'opened_at', 'closed_at', 'current_price', 'profit']


class AutoTradingSettingsSerializer(serializers.ModelSerializer):
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = AutoTradingSettings
        fields = ['id', 'strategy', 'strategy_name', 'is_enabled', 'symbol', 'volume',
                  'max_open_trades', 'check_interval_minutes', 'use_stop_loss',
                  'use_take_profit', 'stop_loss_pips', 'take_profit_pips',
                  'risk_per_trade_percent', 'last_check_time', 'created_at', 'updated_at']
        read_only_fields = ['last_check_time', 'created_at', 'updated_at']


# Authentication Serializers
class PhoneNumberSerializer(serializers.Serializer):
    """Serializer for phone number input"""
    phone_number = serializers.CharField(max_length=15)
    
    def validate_phone_number(self, value):
        """Validate phone number format (Iranian format)"""
        # Remove spaces and dashes
        phone = re.sub(r'[\s\-]', '', value)
        
        # Check if starts with 0 or +98
        if phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif phone.startswith('0098'):
            phone = '0' + phone[4:]
        elif not phone.startswith('0'):
            phone = '0' + phone
        
        # Validate Iranian mobile format (09xxxxxxxxx)
        if not re.match(r'^09\d{9}$', phone):
            raise serializers.ValidationError('شماره موبایل معتبر نیست. فرمت صحیح: 09123456789')
        
        return phone


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    phone_number = serializers.CharField(max_length=15)
    otp_code = serializers.CharField(max_length=4, min_length=4)
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        phone = re.sub(r'[\s\-]', '', value)
        if phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif phone.startswith('0098'):
            phone = '0' + phone[4:]
        elif not phone.startswith('0'):
            phone = '0' + phone
        
        if not re.match(r'^09\d{9}$', phone):
            raise serializers.ValidationError('شماره موبایل معتبر نیست')
        
        return phone
    
    def validate_otp_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError('کد باید فقط عدد باشد')
        return value


class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile info"""
    phone_number = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    gold_api_access = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'phone_number',
            'nickname',
            'first_name',
            'last_name',
            'date_joined',
            'is_staff',
            'is_superuser',
            'gold_api_access',
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'is_staff', 'is_superuser', 'gold_api_access']
    
    def get_phone_number(self, obj):
        """Get phone number from profile, return empty string if profile doesn't exist"""
        try:
            profile = getattr(obj, 'profile', None)
            if profile:
                return profile.phone_number
            return ''
        except Exception:
            return ''
    
    def get_nickname(self, obj):
        try:
            profile = getattr(obj, 'profile', None)
            if profile and profile.nickname:
                return profile.nickname
            return ''
        except Exception:
            return ''
    
    def get_gold_api_access(self, obj):
        try:
            access = getattr(obj, 'gold_api_access', None)
            if not access:
                return {
                    'has_credentials': False,
                    'provider': '',
                    'api_key': '',
                    'source': None,
                    'assigned_by_admin': False,
                    'allow_mt5_access': False,
                    'is_active': False,
                    'assigned_at': None,
                    'updated_at': None,
                    'notes': '',
                }
            return {
                'has_credentials': access.has_credentials,
                'provider': access.provider or '',
                'api_key': access.api_key or '',
                'source': access.source,
                'assigned_by_admin': access.assigned_by_admin,
                'allow_mt5_access': access.allow_mt5_access,
                'is_active': access.is_active,
                'assigned_at': access.assigned_at.isoformat() if access.assigned_at else None,
                'updated_at': access.updated_at.isoformat() if access.updated_at else None,
                'notes': access.notes,
            }
        except Exception:
            return {
                'has_credentials': False,
                'provider': '',
                'api_key': '',
                'source': None,
                'assigned_by_admin': False,
                'allow_mt5_access': False,
                'is_active': False,
                'assigned_at': None,
                'updated_at': None,
                'notes': '',
            }


class DeviceSerializer(serializers.ModelSerializer):
    """Device serializer"""
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'device_name', 'last_login', 'created_at', 'is_active']
        read_only_fields = ['id', 'device_id', 'last_login', 'created_at']


class TicketMessageSerializer(serializers.ModelSerializer):
    """Serializer for ticket messages"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TicketMessage
        fields = ['id', 'ticket', 'user', 'user_name', 'message', 'is_admin', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer for tickets"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    admin_name = serializers.CharField(source='admin_user.username', read_only=True, allow_null=True)
    messages_count = serializers.SerializerMethodField()
    messages = TicketMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'user', 'user_name', 'title', 'description', 'category', 
            'priority', 'status', 'created_at', 'updated_at', 'resolved_at',
            'admin_response', 'admin_user', 'admin_name', 'messages_count', 'messages'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'resolved_at', 'admin_user']
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class TicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating tickets"""
    class Meta:
        model = Ticket
        fields = ['title', 'description', 'category', 'priority']
    
    def validate_priority(self, value):
        """Validate priority value"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        if value not in valid_priorities:
            raise serializers.ValidationError('اولویت نامعتبر است')
        return value
    
    def validate_category(self, value):
        """Validate category value"""
        valid_categories = ['technical', 'feature', 'bug', 'question', 'other']
        if value not in valid_categories:
            raise serializers.ValidationError('دسته‌بندی نامعتبر است')
        return value


class UserGoldAPIAccessSerializer(serializers.ModelSerializer):
    """Serializer for user gold API access configuration"""
    has_credentials = serializers.SerializerMethodField()
    
    class Meta:
        model = UserGoldAPIAccess
        fields = [
            'provider',
            'api_key',
            'source',
            'assigned_by_admin',
            'allow_mt5_access',
            'is_active',
            'assigned_at',
            'updated_at',
            'notes',
            'has_credentials',
        ]
        read_only_fields = ['source', 'assigned_by_admin', 'allow_mt5_access', 'assigned_at', 'updated_at', 'has_credentials']
        extra_kwargs = {
            'provider': {'allow_blank': True, 'required': False},
            'api_key': {'allow_blank': True, 'required': False},
            'notes': {'allow_blank': True, 'required': False},
        }
    
    def get_has_credentials(self, obj):
        return obj.has_credentials


class GoldAPIAccessRequestSerializer(serializers.ModelSerializer):
    """Serializer for gold API access requests (user view)"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = GoldAPIAccessRequest
        fields = [
            'id',
            'status',
            'status_display',
            'preferred_provider',
            'user_notes',
            'admin_notes',
            'price_amount',
            'transaction_id',
            'payment_confirmed_at',
            'assigned_provider',
            'assigned_api_key',
            'assigned_at',
            'assigned_by',
            'assigned_by_username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'status',
            'status_display',
            'admin_notes',
            'price_amount',
            'transaction_id',
            'payment_confirmed_at',
            'assigned_provider',
            'assigned_api_key',
            'assigned_at',
            'assigned_by',
            'assigned_by_username',
            'created_at',
            'updated_at',
        ]
    
    transaction_id = serializers.IntegerField(source='transaction.id', read_only=True, allow_null=True)


class AdminGoldAPIAccessRequestSerializer(GoldAPIAccessRequestSerializer):
    """Serializer for admin view of gold API access requests"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_phone = serializers.SerializerMethodField()
    user_has_gold_access = serializers.SerializerMethodField()
    user_allow_mt5_access = serializers.SerializerMethodField()
    
    class Meta(GoldAPIAccessRequestSerializer.Meta):
        fields = GoldAPIAccessRequestSerializer.Meta.fields + [
            'user_id',
            'username',
            'user_email',
            'user_phone',
            'user_has_gold_access',
            'user_allow_mt5_access',
        ]
    
    def get_user_phone(self, obj):
        profile = getattr(obj.user, 'profile', None)
        return profile.phone_number if profile else ''
    
    def get_user_has_gold_access(self, obj):
        access = getattr(obj.user, 'gold_api_access', None)
        return access.has_credentials if access else False

    def get_user_allow_mt5_access(self, obj):
        access = getattr(obj.user, 'gold_api_access', None)
        return access.allow_mt5_access if access else False


class StrategyOptimizationSerializer(serializers.ModelSerializer):
    """Serializer for strategy optimization results"""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = StrategyOptimization
        fields = [
            'id', 'strategy', 'strategy_name', 'method', 'optimizer_type', 'objective',
            'status', 'original_params', 'optimized_params', 'best_score', 
            'optimization_history', 'original_score', 'improvement_percent',
            'optimization_settings', 'created_at', 'started_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'created_at', 'started_at', 'completed_at', 'status', 'error_message',
            'best_score', 'optimization_history', 'improvement_percent'
        ]


class StrategyOptimizationCreateSerializer(serializers.Serializer):
    """Serializer for creating optimization job"""
    strategy = serializers.IntegerField()
    method = serializers.ChoiceField(
        choices=['ml', 'dl', 'hybrid', 'auto'],
        default='auto'
    )
    optimizer_type = serializers.ChoiceField(
        choices=['ml', 'dl'],
        default='ml',
        required=False
    )
    objective = serializers.ChoiceField(
        choices=['sharpe_ratio', 'total_return', 'win_rate', 'profit_factor', 'combined'],
        default='sharpe_ratio',
        required=False
    )
    n_trials = serializers.IntegerField(default=50, min_value=10, max_value=500, required=False)
    n_episodes = serializers.IntegerField(default=50, min_value=10, max_value=500, required=False)
    ml_method = serializers.ChoiceField(
        choices=['bayesian', 'random_search', 'grid_search'],
        default='bayesian',
        required=False
    )
    dl_method = serializers.ChoiceField(
        choices=['reinforcement_learning', 'neural_evolution', 'gan'],
        default='reinforcement_learning',
        required=False
    )
    timeframe_days = serializers.IntegerField(default=365, min_value=30, max_value=3650, required=False)
    symbol = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for user wallet"""
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for transactions"""
    recommendation_title = serializers.CharField(source='ai_recommendation.title', read_only=True, allow_null=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'transaction_type', 'amount', 'status', 'description',
            'zarinpal_authority', 'zarinpal_ref_id', 'ai_recommendation', 'recommendation_title',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at', 'completed_at', 'zarinpal_ref_id']


class AIRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for AI recommendations"""
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    is_purchased = serializers.SerializerMethodField()
    
    class Meta:
        model = AIRecommendation
        fields = [
            'id', 'strategy', 'strategy_name', 'recommendation_type', 'title', 'description',
            'recommendation_data', 'price', 'status', 'purchased_by', 'purchased_at',
            'applied_to_strategy', 'applied_at', 'created_at', 'is_purchased'
        ]
        read_only_fields = [
            'id', 'created_at', 'purchased_at', 'applied_at', 'status'
        ]
    
    def get_is_purchased(self, obj):
        """Check if current user has purchased this recommendation"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.purchased_by == request.user
        return False


class UserScoreSerializer(serializers.ModelSerializer):
    """Serializer for user scores"""
    username = serializers.CharField(source='user.username', read_only=True)
    rank = serializers.SerializerMethodField()
    
    class Meta:
        model = UserScore
        fields = [
            'id', 'user', 'username', 'total_points', 'level', 'backtests_completed',
            'strategies_created', 'optimizations_completed', 'best_return', 'total_trades',
            'rank', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_rank(self, obj):
        """Calculate user rank"""
        from core.gamification import get_user_rank
        return get_user_rank(obj.user)


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for achievements"""
    is_unlocked = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id', 'code', 'name', 'description', 'icon', 'points_reward',
            'category', 'condition_type', 'condition_value', 'is_active',
            'is_unlocked', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_is_unlocked(self, obj):
        """Check if current user has unlocked this achievement"""
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return UserAchievement.objects.filter(user=request.user, achievement=obj).exists()
        return False


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for user achievements"""
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'user', 'achievement', 'unlocked_at']
        read_only_fields = ['id', 'unlocked_at']

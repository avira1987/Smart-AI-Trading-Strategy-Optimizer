from rest_framework import serializers
from core.models import APIConfiguration, TradingStrategy, Job, Result, LiveTrade, AutoTradingSettings
from core.models import UserProfile, OTPCode, Device, StrategyQuestion, Ticket, TicketMessage, StrategyOptimization
from core.models import Wallet, Transaction, AIRecommendation, DDNSConfiguration
from django.contrib.auth.models import User
import re


class APIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIConfiguration
        fields = ['id', 'provider', 'api_key', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class TradingStrategySerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TradingStrategy
        fields = ['id', 'name', 'description', 'strategy_file', 'is_active', 'uploaded_at',
                  'parsed_strategy_data', 'processing_status', 'processed_at', 'processing_error', 'questions_count']
        read_only_fields = ['uploaded_at', 'parsed_strategy_data', 'processing_status', 'processed_at', 'processing_error', 'questions_count']
    
    def get_questions_count(self, obj):
        return obj.questions.count()


class StrategyQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StrategyQuestion
        fields = ['id', 'strategy', 'question_text', 'question_type', 'options', 
                  'answer', 'status', 'order', 'created_at', 'answered_at', 'context']
        read_only_fields = ['created_at', 'answered_at']


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = ['id', 'job', 'total_return', 'total_trades', 'winning_trades', 
                  'losing_trades', 'win_rate', 'max_drawdown', 'equity_curve_data',
                  'description', 'trades_details', 'created_at']
        read_only_fields = ['created_at']


class JobSerializer(serializers.ModelSerializer):
    result = ResultSerializer(read_only=True)
    strategy_name = serializers.CharField(source='strategy.name', read_only=True)
    
    class Meta:
        model = Job
        fields = ['id', 'strategy', 'strategy_name', 'job_type', 'status', 'created_at', 
                  'started_at', 'completed_at', 'result', 'error_message']
        read_only_fields = ['created_at', 'started_at', 'completed_at', 'status', 'result', 'error_message']


class JobCreateSerializer(serializers.Serializer):
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
    phone_number = serializers.CharField(source='profile.phone_number', read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 'last_name', 'date_joined', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'username', 'date_joined', 'is_staff', 'is_superuser']


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


class DDNSConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for DDNS Configuration (Admin only)"""
    
    class Meta:
        model = DDNSConfiguration
        fields = [
            'id', 'provider', 'domain', 'token', 'username', 'password', 
            'update_url', 'is_enabled', 'update_interval_minutes', 
            'last_update', 'last_ip', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_update', 'last_ip', 'created_at', 'updated_at']
        extra_kwargs = {
            'token': {'write_only': True},
            'password': {'write_only': True},
        }

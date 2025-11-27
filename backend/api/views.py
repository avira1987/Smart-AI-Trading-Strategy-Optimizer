from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.serializers import ValidationError
from django.shortcuts import get_object_or_404
from django.http import Http404, FileResponse
import os
import mimetypes
from urllib.parse import quote
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import User
from django.conf import settings
from ai_module.gemini_client import JSON_ONLY_SYSTEM_PROMPT, resolve_ai_provider
from ai_module.providers import get_registered_providers
from .permissions import IsAdminOrStaff
from .api_usage_tracker import get_api_usage_stats
from core.models import (
    APIConfiguration,
    TradingStrategy,
    Job,
    Result,
    LiveTrade,
    AutoTradingSettings,
    Ticket,
    TicketMessage,
    StrategyOptimization,
    StrategyMarketplaceListing,
    StrategyListingAccess,
    SystemSettings,
)
from core.models import Wallet, Transaction, AIRecommendation
from core.models import UserScore, Achievement, UserAchievement
from core.gamification import (
    get_or_create_user_score,
    award_backtest_points,
    check_and_award_achievements,
    get_user_rank,
    get_leaderboard,
    initialize_default_achievements
)
from .serializers import (
    APIConfigurationSerializer,
    TradingStrategySerializer,
    JobSerializer,
    JobCreateSerializer,
    ResultSerializer,
    LiveTradeSerializer,
    AutoTradingSettingsSerializer,
    TicketSerializer,
    TicketCreateSerializer,
    TicketMessageSerializer,
    StrategyOptimizationSerializer,
    StrategyOptimizationCreateSerializer,
    WalletSerializer,
    TransactionSerializer,
    AIRecommendationSerializer,
    StrategyMarketplaceListingSerializer,
    StrategyMarketplaceListingWriteSerializer,
    StrategyListingAccessSerializer,
    SystemSettingsSerializer,
    PublicSystemSettingsSerializer,
    UserScoreSerializer,
    AchievementSerializer,
    UserAchievementSerializer,
)
from .data_providers import DataProviderManager
from .tasks import run_backtest_task, run_demo_trade_task, run_auto_trading
from .mt5_client import (
    fetch_mt5_m1_candles, fetch_mt5_candles, is_mt5_available,
    get_mt5_account_info, get_mt5_positions, open_mt5_trade, 
    close_mt5_trade, is_market_open
)
import logging
import types
import time
import redis
from redis.exceptions import RedisError


CELERY_CHECK_CACHE = {
    'timestamp': 0.0,
    'available': False,
}
CELERY_CHECK_TTL_SECONDS = 30

MT5_CHECK_CACHE = {
    'timestamp': 0.0,
    'available': False,
    'message': None,
}
MT5_CHECK_TTL_SECONDS = 30


def _is_celery_available_quick():
    """Determine Celery availability with a very fast broker probe.
    
    The previous implementation attempted to establish a full Celery connection
    on every request, which could block for long periods when Redis/broker was
    down. That delay surfaced in the UI as a timeout when starting a backtest.
    """
    now = time.monotonic()
    if now - CELERY_CHECK_CACHE['timestamp'] < CELERY_CHECK_TTL_SECONDS:
        return CELERY_CHECK_CACHE['available']
    
    available = False
    try:
        from celery import current_app
        
        if getattr(current_app.conf, 'task_always_eager', False):
            available = False
        else:
            broker_url = getattr(current_app.conf, 'broker_url', None) or getattr(settings, 'CELERY_BROKER_URL', None)
            if not broker_url:
                available = False
            elif broker_url.startswith(('redis://', 'rediss://')):
                try:
                    redis_client = redis.Redis.from_url(
                        broker_url,
                        socket_connect_timeout=1.0,
                        socket_timeout=1.0,
                    )
                    redis_client.ping()
                    available = True
                except RedisError as redis_error:
                    logger.warning("Redis broker unreachable: %s", redis_error)
                    available = False
            else:
                try:
                    from kombu import Connection
                    conn = Connection(broker_url, connect_timeout=1.0)
                    conn.connect()
                    conn.release()
                    available = True
                except Exception as kombu_error:
                    logger.warning("Celery broker unreachable: %s", kombu_error)
                    available = False
    except Exception as e:
        logger.warning("Celery availability check error: %s", e)
        available = False
    
    CELERY_CHECK_CACHE['timestamp'] = now
    CELERY_CHECK_CACHE['available'] = available
    return available


def _is_mt5_available_cached():
    """Check MT5 availability with caching to avoid slow initialization on every request."""
    now = time.monotonic()
    if now - MT5_CHECK_CACHE['timestamp'] < MT5_CHECK_TTL_SECONDS:
        return MT5_CHECK_CACHE['available'], MT5_CHECK_CACHE['message']
    
    from .mt5_client import is_mt5_available
    available, message = is_mt5_available()
    
    MT5_CHECK_CACHE['timestamp'] = now
    MT5_CHECK_CACHE['available'] = available
    MT5_CHECK_CACHE['message'] = message
    return available, message

import time
from .utils import get_user_friendly_api_error_message, get_user_strategy_or_404  # توابع کمکی مدیریت پیام خطا
from .sms_service import send_sms

logger = logging.getLogger(__name__)

class SystemSettingsView(APIView):
    """Endpoint برای مشاهده و به‌روزرسانی تنظیمات سیستم"""
    permission_classes = [AllowAny]

    def get(self, request):
        settings = SystemSettings.load()

        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            serializer = SystemSettingsSerializer(settings)
            return Response(serializer.data)

        serializer = PublicSystemSettingsSerializer({
            'live_trading_enabled': settings.live_trading_enabled,
        })
        return Response(serializer.data)

    def patch(self, request):
        if not request.user.is_authenticated:
            return Response({'detail': 'برای تغییر تنظیمات وارد شوید'}, status=status.HTTP_401_UNAUTHORIZED)

        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'detail': 'فقط ادمین می‌تواند تنظیمات را تغییر دهد'}, status=status.HTTP_403_FORBIDDEN)

        settings = SystemSettings.load()
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class ClearAICacheView(APIView):
    """Endpoint برای پاک کردن کش AI (فقط ادمین)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        if not (request.user.is_staff or request.user.is_superuser):
            return Response({'detail': 'فقط ادمین می‌تواند کش را پاک کند'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            from pathlib import Path
            from ai_module.gemini_client import _CACHE_DIR
            
            cache_dir = _CACHE_DIR
            deleted_count = 0
            
            if cache_dir.exists():
                for cache_file in cache_dir.rglob("*.json"):
                    try:
                        cache_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete cache file {cache_file}: {e}")
            
            logger.info(f"Admin {request.user.username} cleared {deleted_count} AI cache files")
            return Response({
                'status': 'success',
                'message': f'{deleted_count} فایل کش پاک شد',
                'deleted_count': deleted_count
            })
        except Exception as e:
            logger.error(f"Error clearing AI cache: {e}")
            return Response({
                'status': 'error',
                'message': f'خطا در پاک کردن کش: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing API configurations"""
    queryset = APIConfiguration.objects.all()
    serializer_class = APIConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    # Backend/system providers that require admin access
    BACKEND_PROVIDERS = ['kavenegar', 'zarinpal']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Regular users only see their own API keys
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(user=user).exclude(provider__in=self.BACKEND_PROVIDERS)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Override create to check admin permission for backend providers"""
        provider = request.data.get('provider', '')
        
        # Check if user is trying to create a backend provider
        if provider in self.BACKEND_PROVIDERS:
            if not (request.user and (request.user.is_staff or request.user.is_superuser)):
                return Response(
                    {'detail': 'فقط ادمین می‌تواند تنظیمات بک‌اند را اضافه کند'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except ValidationError as e:
            # Return validation errors in a user-friendly format
            logger.error(f"Validation error creating API configuration: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error creating API configuration: {e}")
            return Response(
                {'detail': f'خطا در ایجاد تنظیمات API: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """Override update to check admin permission for backend providers"""
        instance = self.get_object()
        provider = request.data.get('provider', instance.provider)
        
        # Check if user is trying to update a backend provider
        if provider in self.BACKEND_PROVIDERS or instance.provider in self.BACKEND_PROVIDERS:
            if not (request.user and (request.user.is_staff or request.user.is_superuser)):
                return Response(
                    {'detail': 'فقط ادمین می‌تواند تنظیمات بک‌اند را ویرایش کند'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        try:
            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except ValidationError as e:
            # Return validation errors in a user-friendly format
            logger.error(f"Validation error updating API configuration: {e.detail}")
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Error updating API configuration: {e}")
            return Response(
                {'detail': f'خطا در به‌روزرسانی تنظیمات API: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """Override destroy to check admin permission for backend providers"""
        instance = self.get_object()
        
        # Check if user is trying to delete a backend provider
        if instance.provider in self.BACKEND_PROVIDERS:
            if not (request.user and (request.user.is_staff or request.user.is_superuser)):
                return Response(
                    {'detail': 'فقط ادمین می‌تواند تنظیمات بک‌اند را حذف کند'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        return super().destroy(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        provider = serializer.validated_data.get('provider')
        request_user = self.request.user if self.request.user.is_authenticated else None
        assign_system_owner = self._should_assign_system_owner(
            provider=provider,
            request_user=request_user,
            current_owner=None,
        )
        owner = None if assign_system_owner else request_user
        serializer.save(user=owner)

    def perform_update(self, serializer):
        provider = serializer.validated_data.get('provider', serializer.instance.provider)
        request_user = self.request.user if self.request.user.is_authenticated else None
        current_owner = serializer.instance.user
        assign_system_owner = self._should_assign_system_owner(
            provider=provider,
            request_user=request_user,
            current_owner=current_owner,
        )
        owner = None if assign_system_owner else current_owner
        serializer.save(user=owner)

    def _should_assign_system_owner(self, provider, request_user, current_owner):
        """
        Determine whether the API key should be saved as a system-wide key (user=None).
        Admin-created keys for AI providers should be system-wide unless the admin explicitly
        edits another user's key. Backend providers are always system-owned.
        """
        if provider in self.BACKEND_PROVIDERS:
            return True

        if not request_user or not request_user.is_authenticated:
            return False

        if not (request_user.is_staff or request_user.is_superuser):
            return False

        # Admin-created keys (no current owner) should be system-wide.
        if current_owner is None:
            return True

        # Allow admins to keep their own personal keys if they edit someone else's.
        return current_owner.id == request_user.id if hasattr(current_owner, "id") else False
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test API connection"""
        api_config = self.get_object()
        
        logger.info("API test initiated for provider %s (config id=%s)", api_config.provider, api_config.id)

        # Special handling for Gemini AI API
        if api_config.provider == 'gemini':
            try:
                # Check if google-generativeai is installed
                try:
                    import google.generativeai as genai
                except ImportError as import_err:
                    logger.error(f"Gemini import failed: {import_err}")
                    return Response({
                        'status': 'error',
                        'message': 'Google Generative AI library not installed. Please install it: pip install google-generativeai',
                        'provider': 'gemini'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if genai is None:
                    return Response({
                        'status': 'error',
                        'message': 'Google Generative AI library not available',
                        'provider': 'gemini'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Test Gemini API with the key from this config
                if not api_config.api_key or not api_config.api_key.strip():
                    return Response({
                        'status': 'error',
                        'message': 'API key is empty',
                        'provider': 'gemini'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    # Configure genai with the test key
                    genai.configure(api_key=api_config.api_key.strip())
                    model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')
                    
                    # First, try to get list of available models
                    available_models = []
                    try:
                        logger.info("Fetching list of available Gemini models...")
                        for model in genai.list_models():
                            if 'generateContent' in model.supported_generation_methods:
                                model_display_name = model.display_name or model.name
                                model_name_short = model.name.split('/')[-1] if '/' in model.name else model.name
                                available_models.append({
                                    'full_name': model.name,
                                    'short_name': model_name_short,
                                    'display_name': model_display_name
                                })
                                logger.info(f"Found available model: {model.name}")
                    except Exception as list_error:
                        logger.warning(f"Could not list models: {str(list_error)}")
                        # Continue with default models if listing fails
                    
                    # Build list of models to try
                    model_names_to_try = []
                    
                    # Add configured model first
                    if model_name:
                        model_names_to_try.append(model_name)
                    
                    # Add models from available_models list
                    if available_models:
                        for model_info in available_models:
                            # Try both full name and short name
                            if model_info['full_name'] not in model_names_to_try:
                                model_names_to_try.append(model_info['full_name'])
                            if model_info['short_name'] not in model_names_to_try and model_info['short_name'] != model_info['full_name']:
                                model_names_to_try.append(model_info['short_name'])
                    
                    # Add fallback models if no models found from API
                    if not model_names_to_try:
                        model_names_to_try = [
                            'gemini-2.0-flash',
                            'gemini-2.5-flash',
                            'gemini-2.0-flash-001',
                            'gemini-2.5-pro',
                            'gemini-pro-latest',
                            'models/gemini-2.0-flash',
                            'models/gemini-2.5-flash',
                            'models/gemini-pro-latest',
                        ]
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    model_names_to_try = [x for x in model_names_to_try if not (x in seen or seen.add(x))]
                    
                    logger.info(f"Models to try: {model_names_to_try}")
                    
                    last_error = None
                    successful_model = None
                    
                    for try_model_name in model_names_to_try:
                        try:
                            logger.info(f"Trying Gemini model: {try_model_name}")
                            model = genai.GenerativeModel(try_model_name)
                            
                            # Try a simple test call to verify the API key works
                            test_response = model.generate_content(
                                "Say 'test'",
                                generation_config={'max_output_tokens': 10}
                            )
                            
                            # Check if response is valid
                            if hasattr(test_response, 'text') or hasattr(test_response, 'candidates'):
                                successful_model = try_model_name
                                success_msg = f'Gemini API connection successful using model: {try_model_name}'
                                if try_model_name != model_name:
                                    success_msg += f' (configured model "{model_name}" was not available, used "{try_model_name}" instead)'
                                
                                return Response({
                                    'status': 'success',
                                    'message': success_msg,
                                    'provider': 'gemini',
                                    'data_points': 0
                                })
                        except Exception as model_error:
                            last_error = model_error
                            logger.warning(f"Model {try_model_name} failed: {str(model_error)}")
                            continue
                    
                    # If all models failed, return detailed error
                    if last_error:
                        error_msg = str(last_error)
                        logger.error(f"Gemini API test error with all models: {error_msg}")
                        
                        # Build detailed error message
                        if available_models:
                            available_model_names = [m['short_name'] for m in available_models[:5]]
                            error_details = f'\n\nAvailable models found: {", ".join(available_model_names)}'
                            if len(available_models) > 5:
                                error_details += f' (and {len(available_models) - 5} more)'
                        else:
                            available_model_names = []
                            error_details = '\n\nCould not fetch list of available models from API.'
                        
                        # Provide user-friendly error messages
                        if 'API_KEY_INVALID' in error_msg or 'Invalid API key' in error_msg or 'INVALID_API_KEY' in error_msg:
                            error_msg = f'Invalid API key. Please check your Gemini API key from Google AI Studio.{error_details}'
                        elif 'PERMISSION_DENIED' in error_msg or 'Permission denied' in error_msg:
                            error_msg = f'Permission denied. Please check your API key permissions in Google AI Studio.{error_details}'
                        elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower() or 'QUOTA_EXCEEDED' in error_msg:
                            error_msg = f'API quota exceeded. Please check your usage limits in Google AI Studio.{error_details}'
                        elif '404' in error_msg or 'NOT_FOUND' in error_msg or 'Model not found' in error_msg or 'is not found for API version' in error_msg:
                            error_msg = f'Models not found for API version. This usually means:\n1. The API version changed or models were renamed\n2. Your API key does not have access to these models\n3. You need to update the model names\n\nFull error: {error_msg}{error_details}\n\nTried models: {", ".join(model_names_to_try[:5])}'
                        elif '401' in error_msg or 'UNAUTHENTICATED' in error_msg:
                            error_msg = f'Authentication failed. Please verify your API key.{error_details}'
                        elif '429' in error_msg:
                            error_msg = f'Rate limit exceeded. Please try again later.{error_details}'
                        else:
                            # Include full error message for debugging
                            error_msg = f'{error_msg}{error_details}\n\nTried models: {", ".join(model_names_to_try[:5])}'
                        
                        return Response({
                            'status': 'error',
                            'message': f'Gemini API test failed: {error_msg}',
                            'provider': 'gemini'
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # This should not happen, but just in case
                    return Response({
                        'status': 'error',
                        'message': 'Gemini API test failed: No models were attempted.',
                        'provider': 'gemini'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
                except Exception as api_error:
                    error_msg = str(api_error)
                    logger.exception(f"Gemini API test unexpected error: {error_msg}")
                    
                    # Provide user-friendly error messages
                    if 'API_KEY_INVALID' in error_msg or 'Invalid API key' in error_msg or 'INVALID_API_KEY' in error_msg:
                        error_msg = 'Invalid API key. Please check your Gemini API key from Google AI Studio.'
                    elif 'PERMISSION_DENIED' in error_msg or 'Permission denied' in error_msg:
                        error_msg = 'Permission denied. Please check your API key permissions in Google AI Studio.'
                    elif 'quota' in error_msg.lower() or 'limit' in error_msg.lower() or 'QUOTA_EXCEEDED' in error_msg:
                        error_msg = 'API quota exceeded. Please check your usage limits in Google AI Studio.'
                    elif '404' in error_msg or 'NOT_FOUND' in error_msg:
                        error_msg = 'Model not found. Please check GEMINI_MODEL setting.'
                    elif '401' in error_msg or 'UNAUTHENTICATED' in error_msg:
                        error_msg = 'Authentication failed. Please verify your API key.'
                    elif '429' in error_msg:
                        error_msg = 'Rate limit exceeded. Please try again later.'
                    
                    return Response({
                        'status': 'error',
                        'message': f'Gemini API test failed: {error_msg}',
                        'provider': 'gemini'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
            except Exception as e:
                logger.exception(f"Gemini API test failed with exception: {e}")
                user_message = get_user_friendly_api_error_message(str(e))
                return Response({
                    'status': 'error',
                    'message': user_message,
                    'provider': 'gemini'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif api_config.provider == 'gapgpt':
            # Special handling for GapGPT API
            try:
                test_key = (api_config.api_key or "").strip()
                if not test_key:
                    return Response({
                        'status': 'error',
                        'message': 'کلید API خالی است',
                        'provider': 'gapgpt'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Import GapGPT test function
                from ai_module.gapgpt_client import test_gapgpt_api_key
                
                # Run the test
                test_result = test_gapgpt_api_key(test_key, user=request.user if request.user.is_authenticated else None)
                
                if test_result.get('success'):
                    response_data = {
                        'status': 'success',
                        'message': test_result.get('message', 'GapGPT API connection successful.'),
                        'provider': 'gapgpt',
                        'data_points': test_result.get('available_models', 0)
                    }
                    # Add optional fields if available
                    if 'model_used' in test_result:
                        response_data['model_used'] = test_result['model_used']
                    if 'tokens_used' in test_result:
                        response_data['tokens_used'] = test_result['tokens_used']
                    if 'models' in test_result:
                        response_data['available_models'] = test_result['models']
                    
                    return Response(response_data)
                else:
                    error_msg = test_result.get('message', test_result.get('error', 'Unknown error'))
                    status_code = test_result.get('status_code', status.HTTP_400_BAD_REQUEST)
                    
                    return Response({
                        'status': 'error',
                        'message': error_msg,
                        'provider': 'gapgpt',
                        'details': test_result.get('error')
                    }, status=status_code)
            
            except Exception as e:
                logger.exception(f"GapGPT API test failed with exception: {e}")
                return Response({
                    'status': 'error',
                    'message': f'GapGPT API test failed: {str(e)}',
                    'provider': 'gapgpt'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        elif api_config.provider in {'openai', 'chatgpt', 'gpt', 'gpt4', 'gpt-4', 'cohere', 'openrouter', 'together_ai', 'deepinfra', 'groq'}:
            try:
                test_key = (api_config.api_key or "").strip()
                if not test_key:
                    return Response({
                        'status': 'error',
                        'message': 'API key is empty',
                        'provider': api_config.provider
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    provider_map = get_registered_providers()
                except Exception as provider_error:
                    logger.exception("Failed to build provider map for test: %s", provider_error)
                    return Response({
                        'status': 'error',
                        'message': 'AI provider test failed: could not initialize provider.',
                        'provider': api_config.provider
                    }, status=status.HTTP_400_BAD_REQUEST)

                template_instance = provider_map.get(api_config.provider)
                if not template_instance:
                    return Response({
                        'status': 'error',
                        'message': 'Provider not supported',
                        'provider': api_config.provider
                    }, status=status.HTTP_400_BAD_REQUEST)

                try:
                    provider = template_instance.__class__()
                except Exception as init_error:
                    logger.exception("Failed to instantiate provider %s: %s", api_config.provider, init_error)
                    return Response({
                        'status': 'error',
                        'message': 'AI provider test failed: could not create provider instance.',
                        'provider': api_config.provider
                    }, status=status.HTTP_400_BAD_REQUEST)

                def _test_key_override(self):
                    return test_key

                provider.get_api_key = types.MethodType(_test_key_override, provider)  # type: ignore[assignment]

                generation_config = {
                    'temperature': getattr(settings, 'AI_PROVIDER_DEFAULT_TEMPERATURE', 0.3),
                    'max_output_tokens': 128,
                }

                try:
                    result = provider.generate(
                        prompt='Return {"status": "ok"} as compact JSON.',
                        generation_config=generation_config,
                        metadata={'system_prompt': JSON_ONLY_SYSTEM_PROMPT},
                    )
                except Exception as exc:
                    logger.exception("AI provider test failed: %s", exc)
                    return Response({
                        'status': 'error',
                        'message': f"AI provider test failed: {exc}",
                        'provider': api_config.provider
                    }, status=status.HTTP_400_BAD_REQUEST)

                if result.success:
                    return Response({
                        'status': 'success',
                        'message': 'AI provider responded successfully.',
                        'provider': api_config.provider
                    })

                error_message = result.error or 'Provider returned error'
                if result.status_code == 401:
                    error_message = 'Authentication failed. لطفاً کلید OpenAI را بررسی کنید.'
                elif result.status_code == 403:
                    error_message = 'دسترسی رد شد. مطمئن شوید کلید به پروژه‌ی صحیح متصل است.'
                elif result.status_code == 404:
                    error_message = 'مدل پیدا نشد. لطفاً نام مدل پیش‌فرض را بررسی کنید.'
                elif result.status_code == 429:
                    error_message = 'محدودیت نرخ فراخوانی (Rate Limit). بعداً دوباره تلاش کنید.'

                raw_details = result.raw_response
                if not isinstance(raw_details, (dict, list, str, int, float, bool)) and raw_details is not None:
                    raw_details = str(raw_details)

                return Response({
                    'status': 'error',
                    'message': error_message,
                    'details': raw_details,
                    'provider': api_config.provider,
                    'status_code': result.status_code,
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as unexpected_exc:
                logger.exception("Unhandled error during AI provider test for %s: %s", api_config.provider, unexpected_exc)
                return Response({
                    'status': 'error',
                    'message': f'AI provider test failed with unexpected error: {unexpected_exc}',
                    'provider': api_config.provider
                }, status=status.HTTP_400_BAD_REQUEST)

        # Original code for data providers
        try:
            data_manager = DataProviderManager(user=request.user)
            # Override provider key with the key stored in DB for this config
            if api_config.provider in data_manager.providers:
                provider_instance = data_manager.providers[api_config.provider]
                if hasattr(provider_instance, 'api_key'):
                    provider_instance.api_key = api_config.api_key
            test_result = data_manager.test_provider(api_config.provider)
            
            return Response({
                'status': test_result['status'],
                'message': test_result['message'],
                'provider': api_config.provider,
                'data_points': test_result.get('data_points', 0)
            })
        except Exception as e:
            logger.error(f"API test failed for {api_config.provider}: {e}")
            user_message = get_user_friendly_api_error_message(str(e))
            return Response({
                'status': 'error',
                'message': user_message,
                'provider': api_config.provider
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def available_providers(self, request):
        """Get list of available data providers"""
        try:
            data_manager = DataProviderManager(user=request.user)
            providers = data_manager.get_available_providers()
            
            return Response({
                'available_providers': providers,
                'total_count': len(providers)
            })
        except Exception as e:
            logger.error(f"Error getting available providers: {e}")
            return Response({
                'error': str(e),
                'available_providers': [],
                'total_count': 0
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def test_mt5(self, request):
        """Test MetaTrader 5 connection on Windows"""
        try:
            available, error_msg = is_mt5_available()
            
            if available:
                # Try to get account info for more detailed test
                account_info, account_error = get_mt5_account_info()
                if account_info:
                    return Response({
                        'status': 'success',
                        'message': f'اتصال به MetaTrader 5 با موفقیت برقرار شد. حساب: {account_info.get("login", "N/A")} ({account_info.get("server", "N/A")})',
                        'provider': 'mt5',
                        'account_info': {
                            'login': account_info.get('login'),
                            'server': account_info.get('server'),
                            'balance': account_info.get('balance'),
                            'equity': account_info.get('equity'),
                            'currency': account_info.get('currency'),
                            'is_demo': account_info.get('is_demo', False)
                        }
                    })
                else:
                    return Response({
                        'status': 'success',
                        'message': 'اتصال به MetaTrader 5 برقرار شد. (نمی‌توان اطلاعات حساب را دریافت کرد)',
                        'provider': 'mt5',
                        'warning': account_error
                    })
            else:
                return Response({
                    'status': 'error',
                    'message': f'خطا در اتصال به MetaTrader 5: {error_msg or "MT5 terminal راه‌اندازی نشده یا لاگین نیست"}',
                    'provider': 'mt5'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"MT5 test error: {e}")
            return Response({
                'status': 'error',
                'message': f'خطا در تست اتصال MetaTrader 5: {str(e)}',
                'provider': 'mt5'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView


class MarketDataView(APIView):
    """Endpoints for market data integrations (e.g., MT5)."""
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _has_mt5_access(user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return True

    def get(self, request, *args, **kwargs):
        source = request.query_params.get('source')
        if source == 'mt5_candles':
            if not self._has_mt5_access(request.user):
                return Response(
                    {
                        'status': 'error',
                        'message': 'دسترسی به داده‌های MetaTrader 5 فقط برای ادمین یا کاربران مجاز فعال است.',
                        'allow_mt5_access': False,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            symbol = request.query_params.get('symbol', 'XAUUSD_l')
            timeframe = request.query_params.get('timeframe', 'M1')
            try:
                count = int(request.query_params.get('count', '500'))
            except Exception:
                count = 500
            logger.info(f"[API] /market/mt5_candles symbol={symbol} tf={timeframe} count={count}")
            df, err = fetch_mt5_candles(symbol, timeframe, count)
            if df.empty:
                logger.warning(f"[API] mt5_candles error symbol={symbol}: {err}")
                return Response({'status': 'error', 'message': err or 'No data returned from MT5'}, status=status.HTTP_400_BAD_REQUEST)
            candles = [
                {
                    'datetime': idx.isoformat(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row.get('volume', 0.0)),
                }
                for idx, row in df.iterrows()
            ]
            logger.info(f"[API] mt5_candles success symbol={symbol} rows={len(candles)} first={candles[0]['datetime']} last={candles[-1]['datetime']}")
            return Response({'status': 'success', 'source': 'mt5', 'symbol': symbol, 'timeframe': timeframe, 'count': len(candles), 'candles': candles})
        elif source == 'mt5_symbols':
            # Get available MT5 symbols
            if not self._has_mt5_access(request.user):
                return Response(
                    {
                        'status': 'error',
                        'message': 'دسترسی به داده‌های MetaTrader 5 فقط برای ادمین یا کاربران مجاز فعال است.',
                        'allow_mt5_access': False,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
            from .mt5_client import get_available_mt5_symbols
            symbols, error = get_available_mt5_symbols()
            if error:
                return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)
            
            # Filter to only available symbols if requested
            only_available = request.query_params.get('only_available', 'false').lower() == 'true'
            if only_available:
                symbols = [s for s in symbols if s.get('is_available', False)]
            
            return Response({
                'status': 'success',
                'symbols': symbols,
                'total_count': len(symbols),
                'available_count': sum(1 for s in symbols if s.get('is_available', False))
            })

        return Response({'status': 'error', 'message': 'Unknown market data source'}, status=status.HTTP_400_BAD_REQUEST)


class BacktestPrecheckView(APIView):
    """Validate data availability for a strategy before running backtest."""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            strategy_id = request.data.get('strategy')
            if not strategy_id:
                return Response({'status': 'error', 'message': 'strategy is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                strategy = get_user_strategy_or_404(request.user, id=strategy_id)
            except Http404:
                # Check if it's a marketplace strategy
                marketplace_access = (
                    StrategyListingAccess.objects.select_related('listing', 'listing__strategy')
                    .filter(listing__strategy_id=strategy_id, user=request.user)
                    .first()
                )
                
                if not marketplace_access or not marketplace_access.has_active_access():
                    return Response({
                        'status': 'error', 
                        'message': 'به این استراتژی دسترسی ندارید.'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                strategy = marketplace_access.listing.strategy

            # Use pre-processed strategy data if available, otherwise parse on the fly
            # IMPORTANT: If parsed_strategy_data exists and processing_status is 'processed',
            # we don't need to parse the file again. This avoids slow re-parsing on every precheck.
            if strategy.parsed_strategy_data and strategy.processing_status == 'processed':
                parsed = strategy.parsed_strategy_data
                logger.debug(f"Precheck: Using pre-processed strategy data for strategy {strategy.id}")
            else:
                # Parse strategy file on the fly (backward compatibility)
                from ai_module.nlp_parser import parse_strategy_file
                if not strategy.strategy_file:
                    return Response({
                        'status': 'error', 
                        'message': 'استراتژی انتخاب شده فایل ندارد. لطفاً ابتدا استراتژی را آپلود کنید.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                parsed = parse_strategy_file(strategy.strategy_file.path, user=request.user)
            
            # Default to XAU/USD (Gold) as it's the primary symbol for this trading system
            symbol = parsed.get('symbol') or 'XAU/USD'

            data_manager = DataProviderManager(user=request.user)
            available = data_manager.get_available_providers()
            
            # If no providers found, API key should be set via environment variable or APIConfiguration
            # Do not set default API keys here for security reasons
            if not available:
                pass  # Provider configuration should be done via APIConfiguration model

            details = {
                'symbol': symbol,
                'available_providers': available,
                'provider_checks': [],
                'mt5': {'available': False, 'message': None},
            }

            # If provider(s) exist, test the first one and attempt a tiny fetch window
            if available:
                provider = available[0]
                try:
                    provider_test = data_manager.test_provider(provider)
                    details['provider_checks'].append({'provider': provider, **provider_test})
                except Exception as e:
                    details['provider_checks'].append({'provider': provider, 'status': 'error', 'message': str(e)})

            # Probe MT5 availability regardless, as a fallback option (with caching)
            mt5_ok, mt5_msg = _is_mt5_available_cached()
            details['mt5'] = {'available': mt5_ok, 'message': mt5_msg}

            # Decide readiness and user-facing guidance
            if available:
                # At least one provider configured; consider ready, but surface provider test result
                ready = True
                provider_status = details['provider_checks'][0].get('status') if details['provider_checks'] else 'unknown'
                if provider_status == 'success':
                    message = '✅ ارائه‌دهنده داده تنظیم شده و در دسترس است. می‌توانید بک‌تست را اجرا کنید.'
                else:
                    message = '⚠️ ارائه‌دهنده داده تنظیم شده است. در صورت نیاز به MT5 نصب کنید (اختیاری).'
                return Response({'status': 'ready' if ready else 'not_ready', 'message': message, 'details': details})
            else:
                # No providers; fall back to MT5 if available, else block
                if mt5_ok:
                    return Response({
                        'status': 'ready_with_fallback', 
                        'message': '⚠️ هیچ ارائه‌دهنده API تنظیم نشده است. MT5 به عنوان راه جایگزین در دسترس است.', 
                        'details': details
                    })
                # Clear error message for mobile users
                error_message = (
                    '❌ برای اجرای بک‌تست، لطفاً حداقل یک API key تنظیم کنید:\n'
                    '• Financial Modeling Prep: FINANCIALMODELINGPREP_API_KEY\n'
                    '• Twelve Data: TWELVEDATA_API_KEY\n\n'
                    'یا MetaTrader 5 را نصب و اجرا کنید (فقط برای Windows).'
                )
                return Response({
                    'status': 'not_ready', 
                    'message': error_message, 
                    'details': details
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Precheck error: {e}")
            return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TradingStrategyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trading strategies"""
    serializer_class = TradingStrategySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    pagination_class = None  # Disable pagination for strategies - return all results

    def get_queryset(self):
        """Limit strategies to the authenticated user unless staff"""
        user = self.request.user
        if not user or not user.is_authenticated:
            return TradingStrategy.objects.none()
        if user.is_staff or user.is_superuser:
            return TradingStrategy.objects.all()
        return TradingStrategy.objects.filter(user=user)

    def create(self, request):
        """Upload new strategy"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, is_active=True)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle strategy active status"""
        strategy = self.get_object()
        strategy.is_active = not strategy.is_active
        strategy.save()
        return Response({
            'is_active': strategy.is_active,
            'message': f'Strategy {"activated" if strategy.is_active else "deactivated"}'
        })

    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, pk=None):
        """Set the selected strategy as the user's primary strategy"""
        strategy = self.get_object()
        was_primary = strategy.is_primary
        strategy.is_primary = not strategy.is_primary
        strategy.save(update_fields=['is_primary'])

        message = (
            'Primary strategy unset successfully'
            if was_primary
            else 'Primary strategy updated successfully'
        )

        return Response({
            'status': 'success',
            'strategy_id': strategy.id,
            'is_primary': strategy.is_primary,
            'message': message
        })
    
    @action(detail=True, methods=['post'], url_path='save-gapgpt-conversion')
    def save_gapgpt_conversion(self, request, pk=None):
        """
        ذخیره استراتژی تبدیل شده با GapGPT
        
        Body:
        - converted_strategy: استراتژی تبدیل شده (JSON)
        - model_used: مدل استفاده شده (optional)
        - tokens_used: تعداد توکن‌های استفاده شده (optional)
        
        Returns:
            استراتژی به‌روز شده
        """
        strategy = self.get_object()
        
        # بررسی دسترسی
        if not (request.user.is_staff or request.user.is_superuser or strategy.user == request.user):
            return Response({
                'status': 'error',
                'message': 'شما دسترسی به این استراتژی ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            converted_strategy = request.data.get('converted_strategy')
            if not converted_strategy:
                return Response({
                    'status': 'error',
                    'message': 'استراتژی تبدیل شده (converted_strategy) الزامی است'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # اگر converted_strategy یک string JSON است، آن را parse کن
            if isinstance(converted_strategy, str):
                import json
                try:
                    converted_strategy = json.loads(converted_strategy)
                except json.JSONDecodeError:
                    return Response({
                        'status': 'error',
                        'message': 'فرمت استراتژی تبدیل شده نامعتبر است'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # ذخیره استراتژی تبدیل شده در parsed_strategy_data
            from django.utils import timezone
            from time import time
            
            # اضافه کردن metadata
            if not isinstance(converted_strategy, dict):
                converted_strategy = {'data': converted_strategy}
            
            # اضافه کردن اطلاعات GapGPT
            converted_strategy['conversion_source'] = 'gapgpt'
            converted_strategy['converted_at'] = timezone.now().isoformat()
            converted_strategy['model_used'] = request.data.get('model_used', 'unknown')
            converted_strategy['tokens_used'] = request.data.get('tokens_used', 0)
            
            # اضافه کردن confidence_score در صورت عدم وجود
            if 'confidence_score' not in converted_strategy:
                # محاسبه confidence score بر اساس کامل بودن استراتژی
                score = 0.0
                if converted_strategy.get('entry_conditions'):
                    score += 0.3
                if converted_strategy.get('exit_conditions'):
                    score += 0.3
                if converted_strategy.get('indicators'):
                    score += 0.2
                if converted_strategy.get('risk_management'):
                    score += 0.2
                converted_strategy['confidence_score'] = min(score, 1.0)
            
            # ذخیره
            strategy.parsed_strategy_data = converted_strategy
            strategy.processing_status = 'processed'
            strategy.processed_at = timezone.now()
            strategy.processing_error = ''
            strategy.save()
            
            logger.info(f"Saved GapGPT conversion for strategy {strategy.id}")
            
            return Response({
                'status': 'success',
                'message': 'استراتژی تبدیل شده با موفقیت ذخیره شد',
                'strategy': TradingStrategySerializer(strategy).data
            })
            
        except Exception as e:
            logger.error(f"Error saving GapGPT conversion: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'خطا در ذخیره استراتژی: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='file-content')
    def get_file_content(self, request, pk=None):
        """
        دریافت محتوای فایل استراتژی
        
        Returns:
            محتوای فایل استراتژی به صورت متن
        """
        strategy = self.get_object()
        
        # بررسی دسترسی
        if not (request.user.is_staff or request.user.is_superuser or strategy.user == request.user):
            return Response({
                'status': 'error',
                'message': 'شما دسترسی به این استراتژی ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if not strategy.strategy_file:
            return Response({
                'status': 'error',
                'message': 'فایل استراتژی یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            from ai_module.nlp_parser import extract_text_from_file
            import os
            
            strategy_file_path = strategy.strategy_file.path
            if not os.path.exists(strategy_file_path):
                return Response({
                    'status': 'error',
                    'message': f'فایل در مسیر یافت نشد: {strategy_file_path}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            file_content = extract_text_from_file(strategy_file_path)
            
            return Response({
                'status': 'success',
                'content': file_content,
                'file_name': os.path.basename(strategy.strategy_file.name),
                'file_size': len(file_content)
            })
            
        except Exception as e:
            logger.error(f"Error reading strategy file content: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'خطا در خواندن فایل: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process strategy file to extract and parse strategy data"""
        from django.utils import timezone
        from django.core.cache import cache
        from ai_module.nlp_parser import parse_strategy_file, extract_text_from_file
        from ai_module.gemini_client import analyze_strategy_with_gemini
        
        strategy = self.get_object()
        
        if not strategy.strategy_file:
            return Response({
                'status': 'error',
                'message': 'No strategy file found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            process_started_at = timezone.now()
            process_started_perf = time.perf_counter()
            # Set processing status
            strategy.processing_status = 'processing'
            strategy.processing_error = ''
            strategy.save()
            
            # Initialize progress tracking
            progress_key = f'strategy_process_progress_{strategy.id}'
            cache.set(progress_key, {
                'progress': 0,
                'stage': 'شروع پردازش',
                'message': 'در حال آماده‌سازی...'
            }, 600)  # 10 minutes TTL
            
            # Parse strategy file
            strategy_file_path = strategy.strategy_file.path
            
            # Check if file exists
            import os
            if not os.path.exists(strategy_file_path):
                strategy.processing_status = 'failed'
                strategy.processing_error = f'Strategy file not found: {strategy_file_path}'
                strategy.save()
                return Response({
                    'status': 'error',
                    'message': f'Strategy file not found: {strategy_file_path}',
                    'error': 'FileNotFoundError'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"[STRATEGY PROCESS] Starting parse_strategy_file for strategy {strategy.id}, file: {strategy_file_path}")
            logger.info(f"[STRATEGY PROCESS] User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
            
            # Update progress: Parsing stage
            cache.set(progress_key, {
                'progress': 20,
                'stage': 'تجزیه فایل',
                'message': 'در حال تجزیه فایل استراتژی...'
            }, 600)
            
            try:
                parsed_data = parse_strategy_file(strategy_file_path, user=request.user)
                logger.debug(f"[STRATEGY PROCESS] parse_strategy_file completed for strategy {strategy.id}")
                logger.debug(f"[STRATEGY PROCESS] Parsing result: method={parsed_data.get('parsing_method')}, has_error={'error' in parsed_data}")
                
                # Update progress: Parsing completed
                cache.set(progress_key, {
                    'progress': 40,
                    'stage': 'تجزیه کامل شد',
                    'message': 'فایل استراتژی با موفقیت تجزیه شد'
                }, 600)
            except Exception as parse_error:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"[STRATEGY PROCESS] Error in parse_strategy_file for {strategy_file_path}: {str(parse_error)}\n{error_trace}")
                strategy.processing_status = 'failed'
                strategy.processing_error = f'Parse error: {str(parse_error)}'
                strategy.save()
                return Response({
                    'status': 'error',
                    'message': f'Error parsing strategy file: {str(parse_error)}',
                    'error': str(parse_error),
                    'error_type': type(parse_error).__name__
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Check if parsing was successful
            if 'error' in parsed_data and parsed_data.get('error'):
                error_message = parsed_data['error']
                
                # Check if this is a Rate Limit error
                is_rate_limit = False
                status_code = parsed_data.get('status_code')
                
                # Check status code from provider attempts
                if status_code == 429:
                    is_rate_limit = True
                
                # Check error message for rate limit
                error_lower = error_message.lower()
                if 'rate limit' in error_lower or 'rate_limit' in error_lower or '429' in str(error_message):
                    is_rate_limit = True
                
                # Check provider attempts
                provider_attempts = parsed_data.get('provider_attempts', [])
                if provider_attempts and len(provider_attempts) > 0:
                    attempt_status_code = provider_attempts[0].get('status_code')
                    if attempt_status_code == 429:
                        is_rate_limit = True
                
                # Update progress: Error
                from django.core.cache import cache
                progress_key = f'strategy_process_progress_{strategy.id}'
                cache.set(progress_key, {
                    'progress': 0,
                    'stage': 'خطا',
                    'message': f'خطا در تجزیه: {error_message[:100]}'
                }, 600)
                
                strategy.processing_status = 'failed'
                strategy.processing_error = error_message
                strategy.save()
                
                # Return appropriate response based on error type
                if is_rate_limit:
                    # Log in English only - avoid [FA] spam in console
                    logger.warning(
                        f"Rate Limit detected in parsing for Strategy {strategy.id}: status_code={status_code}"
                    )
                    return Response({
                        'status': 'error',
                        'message': error_message,
                        'error': 'rate_limit',
                        'error_type': 'RateLimitError',
                        'strategy': {
                            'id': strategy.id,
                            'name': strategy.name,
                            'processing_status': 'failed',
                            'processing_error': error_message
                        },
                        'suggestion': 'لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید. یا از ارائه‌دهنده AI دیگری استفاده کنید.'
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    return Response({
                        'status': 'failed',
                        'message': f'Error parsing strategy: {error_message}',
                        'parsed_data': parsed_data
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate strategy analysis - try Gemini first, fallback to basic analysis
            analysis = None
            analysis_sources_info = {
                'nlp_parser': 'nlp_parser',
                'analysis_method': None,
                'ai_model': None,
                'data_sources': {},  # اطلاعات منابع داده استفاده شده در تحلیل
            }
            
            # جمع‌آوری اطلاعات منابع داده از parsed_data
            strategy_symbol = parsed_data.get('symbol')
            strategy_timeframe = parsed_data.get('timeframe')
            strategy_indicators = parsed_data.get('indicators', [])
            
            # اضافه کردن اطلاعات استخراج شده از استراتژی
            if strategy_symbol:
                analysis_sources_info['data_sources']['strategy_symbol'] = strategy_symbol
            if strategy_timeframe:
                analysis_sources_info['data_sources']['strategy_timeframe'] = strategy_timeframe
            if strategy_indicators:
                analysis_sources_info['data_sources']['indicators_mentioned'] = strategy_indicators
            
            # دریافت لیست ارائه‌دهندگان داده در دسترس
            try:
                from api.data_providers import DataProviderManager
                data_manager = DataProviderManager(user=request.user)
                available_providers = data_manager.get_available_providers()
                analysis_sources_info['data_sources']['available_providers'] = available_providers
                analysis_sources_info['data_sources']['providers_count'] = len(available_providers)
                logger.info(f"Available data providers for analysis: {available_providers}")
            except Exception as provider_error:
                logger.warning(f"Could not get available providers info: {str(provider_error)}")
                analysis_sources_info['data_sources']['available_providers'] = []
                analysis_sources_info['data_sources']['providers_error'] = str(provider_error)
            
            from ai_module.gemini_client import analyze_strategy_with_gemini
            from ai_module.nlp_parser import extract_text_from_file

            # Update progress: Analysis stage
            cache.set(progress_key, {
                'progress': 50,
                'stage': 'تحلیل هوش مصنوعی',
                'message': 'در حال تحلیل استراتژی با هوش مصنوعی...'
            }, 600)
            
            logger.info(f"Starting analysis generation for strategy {strategy.id}")
            raw_text = extract_text_from_file(strategy_file_path)
            logger.info(f"Extracted {len(raw_text)} characters for analysis")
            analysis_sources_info['text_length'] = len(raw_text)
            analysis_sources_info['data_sources']['source_file_length'] = len(raw_text)

            user = request.user if request.user and request.user.is_authenticated else None
            analysis_result = analyze_strategy_with_gemini(parsed_data, raw_text, user=user)
            
            # Update progress: Analysis completed
            cache.set(progress_key, {
                'progress': 80,
                'stage': 'تحلیل کامل شد',
                'message': 'تحلیل هوش مصنوعی با موفقیت انجام شد'
            }, 600)

            ai_status = analysis_result.get('ai_status')
            analysis_sources_info['ai_status'] = ai_status
            provider_attempts = analysis_result.get('provider_attempts')
            if provider_attempts:
                analysis_sources_info['ai_attempts'] = provider_attempts

            resolved_ai_provider = resolve_ai_provider(analysis_result)
            if resolved_ai_provider:
                analysis_sources_info['ai_provider'] = resolved_ai_provider
            if analysis_result.get('provider'):
                analysis_sources_info['ai_provider_raw'] = analysis_result.get('provider')
            if analysis_result.get('error'):
                analysis_sources_info['ai_error'] = analysis_result.get('error')
            if analysis_result.get('message'):
                analysis_sources_info['ai_message'] = analysis_result.get('message')

            if ai_status != 'ok':
                message = analysis_result.get(
                    'message',
                    "AI analysis unavailable. لطفاً کلید ChatGPT را بررسی کنید."
                )
                
                # Diagnostic logging for Rate Limit errors
                provider_attempts = analysis_result.get('provider_attempts', [])
                status_code_from_api = None
                raw_error_from_api = None
                
                # Extract actual status code and error from API response
                if provider_attempts:
                    for attempt in provider_attempts:
                        if isinstance(attempt, dict):
                            status_code_from_api = attempt.get('status_code')
                            raw_error_from_api = attempt.get('error')
                        elif hasattr(attempt, 'status_code'):
                            status_code_from_api = attempt.status_code
                            raw_error_from_api = attempt.error
                        if status_code_from_api:
                            break
                
                # Log detailed diagnostic information
                logger.error("=" * 80)
                logger.error(f"❌ AI Analysis Failed for Strategy {strategy.id}")
                logger.error(f"Message: {message}")
                logger.error(f"Status Code from API: {status_code_from_api}")
                logger.error(f"Raw Error from API: {raw_error_from_api}")
                logger.error(f"Provider Attempts: {provider_attempts}")
                logger.error(f"Analysis Result Keys: {list(analysis_result.keys())}")
                logger.error(f"Status Code from result: {analysis_result.get('status_code')}")
                logger.error("=" * 80)
                
                # Handle Rate Limit errors more gracefully
                # Check multiple sources to determine if it's really a rate limit error
                is_rate_limit = False
                rate_limit_sources = []
                
                if status_code_from_api == 429:
                    is_rate_limit = True
                    rate_limit_sources.append(f"API status_code={status_code_from_api}")
                
                if analysis_result.get('status_code') == 429:
                    is_rate_limit = True
                    rate_limit_sources.append(f"result.status_code=429")
                
                message_lower = message.lower()
                if 'rate limit' in message_lower or 'rate_limit' in message_lower or '429' in str(message):
                    is_rate_limit = True
                    rate_limit_sources.append(f"message contains rate limit")
                
                if raw_error_from_api and ('rate limit' in str(raw_error_from_api).lower() or '429' in str(raw_error_from_api)):
                    is_rate_limit = True
                    rate_limit_sources.append(f"raw_error contains rate limit")
                
                logger.warning(
                    f"Rate Limit Detection for Strategy {strategy.id}: "
                    f"is_rate_limit={is_rate_limit}, sources={rate_limit_sources}, "
                    f"api_status_code={status_code_from_api}, "
                    f"message='{message[:100]}'"
                )
                
                # Update progress: Error
                from django.core.cache import cache
                progress_key = f'strategy_process_progress_{strategy.id}'
                cache.set(progress_key, {
                    'progress': 0,
                    'stage': 'خطا',
                    'message': f'خطا در تحلیل: {message[:100]}'
                }, 600)
                
                # Save parsed data without analysis (basic processing)
                strategy.processing_status = 'failed'
                strategy.processing_error = message
                strategy.parsed_strategy_data = parsed_data
                strategy.analysis_sources = analysis_sources_info
                strategy.save()
                
                logger.warning(
                    f"Strategy {strategy.id} processing failed due to AI analysis error: {message}"
                )
                
                # Return appropriate response based on error type
                if is_rate_limit:
                    return Response({
                        'status': 'error',
                        'message': message,
                        'error': 'rate_limit',
                        'error_type': 'RateLimitError',
                        'strategy': {
                            'id': strategy.id,
                            'name': strategy.name,
                            'processing_status': 'failed',
                            'processing_error': message
                        },
                        'analysis_sources': analysis_sources_info,
                        'suggestion': 'لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید. یا از ارائه‌دهنده AI دیگری استفاده کنید.'
                    }, status=status.HTTP_429_TOO_MANY_REQUESTS)
                else:
                    return Response({
                        'status': 'error',
                        'message': message,
                        'error': 'ai_analysis_failed',
                        'error_type': 'AIAnalysisError',
                        'strategy': {
                            'id': strategy.id,
                            'name': strategy.name,
                            'processing_status': 'failed',
                            'processing_error': message
                        },
                        'analysis_sources': analysis_sources_info
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            analysis = analysis_result
            provider_name = resolved_ai_provider or 'openai'
            analysis_sources_info['analysis_method'] = f'{provider_name}_ai'
            analysis_sources_info['ai_model'] = provider_name
            analysis_sources_info.pop('ai_fallback_reason', None)
            parsed_data['analysis'] = analysis
            logger.info(f"AI analysis added to parsed_data for strategy {strategy.id}")
            
            # Run genetic optimization with ChatGPT-backed analysis and backtest on gold
            optimization_summary = {}
            try:
                from copy import deepcopy
                from ai_module.strategy_optimizer import OptimizationEngine
                from ai_module.backtest_engine import BacktestEngine
                from api.data_providers import DataProviderManager

                data_manager = DataProviderManager(user=request.user)
                default_symbol = strategy_symbol or "XAU/USD"
                timeframe_days = 365
                # استفاده از تایم‌فریم دقیق از استراتژی پردازش شده
                strategy_timeframe = parsed_data.get('timeframe')
                historical_data, historical_provider = data_manager.get_historical_data(
                    default_symbol,
                    timeframe_days=timeframe_days,
                    include_latest=True,
                    user=request.user if request.user.is_authenticated else None,
                    return_provider=True,
                    strategy_timeframe=strategy_timeframe,  # تایم‌فریم دقیق از استراتژی
                )

                if historical_data is not None and not historical_data.empty:
                    analysis_sources_info['data_sources']['historical_provider'] = historical_provider
                    analysis_sources_info['data_sources']['historical_rows'] = int(len(historical_data))
                    analysis_sources_info['data_sources']['historical_timeframe_days'] = timeframe_days

                    base_strategy = deepcopy(parsed_data)
                    backtest_engine = BacktestEngine()
                    baseline_results = backtest_engine.run_backtest(
                        historical_data,
                        base_strategy,
                        symbol=default_symbol,
                    )

                    optimizer_engine = OptimizationEngine(deepcopy(parsed_data), historical_data)
                    ga_result = optimizer_engine.optimize(
                        method='dl',
                        objective='sharpe_ratio',
                        dl_method='neural_evolution',
                        n_episodes=25,
                    )

                    def _clean_json(obj):
                        try:
                            import numpy as np  # type: ignore
                            numpy_types = (np.floating, np.integer)
                        except Exception:  # pragma: no cover
                            numpy_types = tuple()

                        if isinstance(obj, dict):
                            return {k: _clean_json(v) for k, v in obj.items()}
                        if isinstance(obj, list):
                            return [_clean_json(item) for item in obj]
                        if isinstance(obj, numpy_types):
                            return float(obj)
                        if isinstance(obj, (float, int, str, bool)) or obj is None:
                            return obj
                        if hasattr(obj, "tolist"):
                            try:
                                return obj.tolist()
                            except Exception:
                                return str(obj)
                        return obj

                    optimization_history = ga_result.get('optimization_history', [])
                    best_params = _clean_json(ga_result.get('best_params', {}))
                    best_score = float(ga_result.get('best_score') or 0.0)
                    history_tail = _clean_json(optimization_history[-5:])

                    optimized_results = None
                    if optimization_history:
                        best_entry = max(
                            optimization_history,
                            key=lambda entry: entry.get('score', float('-inf')),
                        )
                        optimized_results = _clean_json(best_entry.get('results', {}))
                    else:
                        optimized_strategy = optimizer_engine.dl_optimizer._apply_params_to_strategy(  # type: ignore[attr-defined]
                            ga_result.get('best_params', {})
                        )
                        optimized_results = backtest_engine.run_backtest(
                            historical_data,
                            optimized_strategy,
                            symbol=default_symbol,
                        )
                        optimized_results = _clean_json(optimized_results)

                    optimization_summary = {
                        'objective': 'sharpe_ratio',
                        'best_score': best_score,
                        'best_params': best_params,
                        'history_tail': history_tail,
                        'episodes': ga_result.get('n_episodes', 25),
                        'provider': historical_provider,
                        'data_points': int(len(historical_data)),
                        'baseline': _clean_json(baseline_results),
                        'optimized': optimized_results,
                    }

                    parsed_data['genetic_optimization'] = optimization_summary
                    analysis_sources_info['genetic_optimization'] = {
                        'status': 'completed',
                        'best_score': best_score,
                        'episodes': ga_result.get('n_episodes', 25),
                        'provider': historical_provider,
                        'data_points': int(len(historical_data)),
                    }
                else:
                    analysis_sources_info['genetic_optimization'] = {
                        'status': 'no_data',
                        'message': 'Historical gold price data unavailable for optimization.',
                    }
            except Exception as optimization_error:
                logger.warning(
                    "Genetic optimization skipped for strategy %s: %s",
                    strategy.id,
                    optimization_error,
                )
                analysis_sources_info['genetic_optimization'] = {
                    'status': 'error',
                    'message': str(optimization_error),
                }
            
            # استخراج اطلاعات توکن از تحلیل AI
            token_info = {}
            if analysis and isinstance(analysis, dict):
                provider_for_tokens = resolve_ai_provider(analysis)
                tokens_used = analysis.get('tokens_used')
                if tokens_used:
                    token_info = {
                        'total_tokens': tokens_used,
                        'provider': provider_for_tokens,
                    }
                # همچنین بررسی metadata در analysis_sources_info
                if analysis_sources_info.get('ai_provider'):
                    # استخراج از API usage log
                    try:
                        from core.models import APIUsageLog
                        latest_log = APIUsageLog.objects.filter(
                            user=user,
                            provider=analysis_sources_info.get('ai_provider'),
                            endpoint='analyze_strategy_with_gemini',
                            success=True
                        ).order_by('-created_at').first()
                        if latest_log and latest_log.metadata:
                            meta = latest_log.metadata
                            if meta.get('total_tokens_approx'):
                                token_info = {
                                    'total_tokens': meta.get('total_tokens_approx'),
                                    'input_tokens': meta.get('input_tokens_approx'),
                                    'output_tokens': meta.get('output_tokens_approx'),
                                    'provider': analysis_sources_info.get('ai_provider'),
                                }
                    except Exception:
                        pass
            
            # ثبت لاگ فعالیت
            if user and user.is_authenticated:
                try:
                    from core.models import UserActivityLog
                    UserActivityLog.objects.create(
                        user=user,
                        action_type='strategy_processed',
                        action_description=f'پردازش استراتژی «{strategy.name}»',
                        metadata={
                            'strategy_id': strategy.id,
                            'strategy_name': strategy.name,
                            'token_info': token_info,
                            'analysis_method': analysis_sources_info.get('analysis_method'),
                            'ai_provider': analysis_sources_info.get('ai_provider'),
                        }
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log user activity: {log_error}")
            
            # Update progress: Finalizing
            cache.set(progress_key, {
                'progress': 90,
                'stage': 'ذخیره نتایج',
                'message': 'در حال ذخیره نتایج پردازش...'
            }, 600)
            
            # Save parsed data (with or without analysis)
            process_completed_at = timezone.now()
            duration_seconds = max(time.perf_counter() - process_started_perf, 0.0)
            analysis_sources_info['processing_started_at'] = process_started_at.isoformat()
            analysis_sources_info['processing_completed_at'] = process_completed_at.isoformat()
            analysis_sources_info['processing_duration_seconds'] = round(duration_seconds, 2)
            analysis_sources_info['processing_duration_display'] = f"{duration_seconds:.2f} ثانیه"
            strategy.parsed_strategy_data = parsed_data
            strategy.processing_status = 'processed'
            strategy.processed_at = process_completed_at
            strategy.processing_error = ''
            strategy.analysis_sources = analysis_sources_info
            strategy.save()
            
            # Update progress: Completed
            cache.set(progress_key, {
                'progress': 100,
                'stage': 'پردازش کامل شد',
                'message': 'پردازش استراتژی با موفقیت انجام شد'
            }, 600)
            
            logger.info(f"Strategy {strategy.id} processed successfully with confidence {parsed_data.get('confidence_score', 0):.2f}")
            
            serializer = TradingStrategySerializer(strategy, context={'request': request})
            return Response({
                'status': 'success',
                'message': 'Strategy processed successfully',
                'parsed_data': parsed_data,
                'confidence_score': parsed_data.get('confidence_score', 0.0),
                'analysis_generated': analysis is not None,
                'analysis_sources': strategy.analysis_sources,
                'analysis_sources_display': serializer.data.get('analysis_sources_display'),
                'token_info': token_info,  # بازگرداندن اطلاعات توکن
            })
            
        except Exception as e:
            import traceback
            from django.core.cache import cache
            error_trace = traceback.format_exc()
            logger.error(f"Error processing strategy {strategy.id}: {str(e)}\n{error_trace}")
            
            # Update progress: Error
            progress_key = f'strategy_process_progress_{strategy.id}'
            cache.set(progress_key, {
                'progress': 0,
                'stage': 'خطا',
                'message': f'خطا در پردازش: {str(e)[:100]}'
            }, 600)
            
            strategy.processing_status = 'failed'
            strategy.processing_error = f"{str(e)}\n{error_trace[:500]}"  # Limit error length
            strategy.save()
            return Response({
                'status': 'error',
                'message': f'Error processing strategy: {str(e)}',
                'error': str(e),
                'error_type': type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get processing progress for a strategy"""
        from django.core.cache import cache
        
        strategy = self.get_object()
        progress_key = f'strategy_process_progress_{strategy.id}'
        progress_data = cache.get(progress_key)
        
        if progress_data:
            return Response({
                'status': 'processing',
                'progress': progress_data.get('progress', 0),
                'stage': progress_data.get('stage', ''),
                'message': progress_data.get('message', ''),
                'processing_status': strategy.processing_status
            })
        else:
            # No progress data, return current status
            return Response({
                'status': strategy.processing_status,
                'progress': 100 if strategy.processing_status == 'processed' else 0,
                'stage': 'پردازش نشده' if strategy.processing_status == 'not_processed' else 'نامشخص',
                'message': 'اطلاعات پیشرفت در دسترس نیست',
                'processing_status': strategy.processing_status
            })
    
    @action(detail=True, methods=['post'])
    def generate_questions(self, request, pk=None):
        """تولید سوالات هوشمند برای تکمیل استراتژی"""
        from ai_module.nlp_parser import extract_text_from_file
        from ai_module.gemini_client import generate_strategy_questions
        from ai_module.provider_manager import get_provider_manager
        from core.models import StrategyQuestion
        from django.utils import timezone
        
        strategy = self.get_object()
        
        if not strategy.strategy_file:
            return Response({
                'status': 'error',
                'message': 'فایل استراتژی یافت نشد. لطفاً ابتدا استراتژی را آپلود کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if strategy has been processed
        if not strategy.parsed_strategy_data:
            return Response({
                'status': 'error',
                'message': 'استراتژی هنوز پردازش نشده است. لطفاً ابتدا روی دکمه "پردازش" کلیک کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        manager = get_provider_manager(user=request.user)
        available_providers = [
            name for name, provider in manager.providers.items() if provider.is_available()
        ]
        if not available_providers:
            logger.error("No AI providers configured for question generation")
            return Response({
                'status': 'error',
                'message': 'هیچ کلید معتبری برای ارائه‌دهندگان هوش مصنوعی ثبت نشده است. لطفاً در بخش تنظیمات API یکی از سرویس‌های Cohere، OpenRouter، Together AI، DeepInfra، GroqCloud یا Gemini را فعال کنید.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Get parsed data and raw text
            parsed_data = strategy.parsed_strategy_data or {}
            strategy_file_path = strategy.strategy_file.path
            raw_text = extract_text_from_file(strategy_file_path)
            
            if not raw_text or len(raw_text.strip()) == 0:
                return Response({
                    'status': 'error',
                    'message': 'فایل استراتژی خالی است یا قابل خواندن نیست.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get existing answers
            existing_questions = StrategyQuestion.objects.filter(strategy=strategy, status='answered')
            existing_answers = {
                q.question_text: q.answer for q in existing_questions if q.answer
            }
            
            logger.info(f"Generating questions for strategy {strategy.id}, parsed_data keys: {list(parsed_data.keys())}, raw_text length: {len(raw_text)}")
            
            # Generate questions using Gemini
            questions_result = generate_strategy_questions(parsed_data, raw_text, existing_answers, user=request.user)
            if questions_result.get('ai_status') != 'ok':
                message = questions_result.get(
                    'message',
                    "AI analysis unavailable. لطفاً کلید یکی از ارائه‌دهندگان هوش مصنوعی را در تنظیمات وارد و فعال کنید."
                )
                logger.warning(
                    "AI question generation unavailable for strategy %s: %s",
                    strategy.id,
                    message
                )
                return Response({
                    'status': 'error',
                    'message': message
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            questions = questions_result.get('questions', [])
            if not isinstance(questions, list) or len(questions) == 0:
                logger.warning(f"generate_strategy_questions returned empty list for strategy {strategy.id}")
                return Response({
                    'status': 'error',
                    'message': 'هیچ سوالی تولید نشد. لطفاً استراتژی را کامل‌تر تعریف کنید.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Delete old pending questions
            StrategyQuestion.objects.filter(strategy=strategy, status='pending').delete()
            
            # Create new questions
            created_questions = []
            for q_data in questions:
                try:
                    question = StrategyQuestion.objects.create(
                        strategy=strategy,
                        question_text=q_data.get('question_text', ''),
                        question_type=q_data.get('question_type', 'text'),
                        options=q_data.get('options'),
                        order=q_data.get('order', 0),
                        context=q_data.get('context', {})
                    )
                    created_questions.append(question)
                except Exception as create_error:
                    logger.error(f"Error creating question: {str(create_error)}, data: {q_data}")
                    continue
            
            if len(created_questions) == 0:
                return Response({
                    'status': 'error',
                    'message': 'خطا در ایجاد سوالات در پایگاه داده.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            from api.serializers import StrategyQuestionSerializer
            serializer = StrategyQuestionSerializer(created_questions, many=True)
            
            logger.info(f"Successfully generated {len(created_questions)} questions for strategy {strategy.id}")
            
            return Response({
                'status': 'success',
                'message': f'{len(created_questions)} سوال با موفقیت تولید شد.',
                'questions': serializer.data
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error generating questions for strategy {strategy.id}: {str(e)}\n{error_trace}")
            return Response({
                'status': 'error',
                'message': f'خطا در تولید سوالات: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def process_with_answers(self, request, pk=None):
        """پردازش استراتژی با استفاده از جواب‌های کاربر"""
        from django.utils import timezone
        from ai_module.nlp_parser import extract_text_from_file
        from ai_module.gemini_client import parse_strategy_with_answers
        from core.models import StrategyQuestion
        
        strategy = self.get_object()
        
        if not strategy.strategy_file:
            return Response({
                'status': 'error',
                'message': 'No strategy file found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get all answered questions
            answered_questions = StrategyQuestion.objects.filter(
                strategy=strategy,
                status='answered'
            ).order_by('order')
            
            if not answered_questions.exists():
                return Response({
                    'status': 'error',
                    'message': 'No answers provided. Please answer questions first.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Build answers dictionary
            answers = {}
            for q in answered_questions:
                answers[q.question_text] = q.answer
            
            # Get parsed data and raw text
            parsed_data = strategy.parsed_strategy_data or {}
            strategy_file_path = strategy.strategy_file.path
            raw_text = extract_text_from_file(strategy_file_path)
            
            # Convert strategy with answers
            enhanced_strategy = parse_strategy_with_answers(parsed_data, raw_text, answers, user=request.user)
            
            # استخراج اطلاعات توکن
            token_info = enhanced_strategy.get('_token_info', {})
            
            # ثبت لاگ فعالیت
            try:
                from core.models import UserActivityLog
                UserActivityLog.objects.create(
                    user=request.user,
                    action_type='strategy_processed',
                    action_description=f'پردازش استراتژی «{strategy.name}» با استفاده از هوش مصنوعی',
                    metadata={
                        'strategy_id': strategy.id,
                        'strategy_name': strategy.name,
                        'token_info': token_info,
                    }
                )
            except Exception as log_error:
                logger.warning(f"Failed to log user activity: {log_error}")
            
            # حذف _token_info از parsed_data قبل از ذخیره
            enhanced_strategy_for_save = dict(enhanced_strategy)
            enhanced_strategy_for_save.pop('_token_info', None)
            
            # Update strategy
            strategy.parsed_strategy_data = enhanced_strategy_for_save
            strategy.processing_status = 'processed'
            strategy.processed_at = timezone.now()
            strategy.processing_error = ''
            strategy.save()
            
            logger.info(f"Strategy {strategy.id} processed with answers successfully")
            
            return Response({
                'status': 'success',
                'message': 'Strategy processed successfully with answers',
                'parsed_data': enhanced_strategy_for_save,
                'confidence_score': enhanced_strategy.get('confidence_score', 0.0),
                'token_info': token_info,  # بازگرداندن اطلاعات توکن
            })
            
        except Exception as e:
            logger.error(f"Error processing strategy with answers {strategy.id}: {str(e)}")
            strategy.processing_status = 'failed'
            strategy.processing_error = str(e)
            strategy.save()
            return Response({
                'status': 'error',
                'message': f'Error processing strategy: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='download')
    def download(self, request, pk=None):
        """دانلود فایل استراتژی - همان فایل آپلود شده"""
        strategy = self.get_object()
        
        # بررسی دسترسی
        if not (request.user.is_staff or request.user.is_superuser or strategy.user == request.user):
            return Response({
                'status': 'error',
                'message': 'شما دسترسی به این استراتژی ندارید'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # بررسی وجود فایل
        if not strategy.strategy_file:
            return Response({
                'status': 'error',
                'message': 'فایل استراتژی یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            file_path = strategy.strategy_file.path
            if not os.path.exists(file_path):
                return Response({
                    'status': 'error',
                    'message': 'فایل در سرور یافت نشد'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # دریافت نام فایل اصلی (همان نام آپلود شده) با حفظ پسوند کامل
            original_filename = os.path.basename(strategy.strategy_file.name)
            
            # تعیین Content-Type بر اساس پسوند فایل
            # برای فایل‌های Word (.docx) باید content type درست باشد
            content_type, _ = mimetypes.guess_type(original_filename)
            if not content_type:
                # Fallback برای انواع فایل‌های رایج
                file_ext = os.path.splitext(original_filename)[1].lower()
                content_type_map = {
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.doc': 'application/msword',
                    '.pdf': 'application/pdf',
                    '.txt': 'text/plain',
                    '.md': 'text/markdown',
                }
                content_type = content_type_map.get(file_ext, 'application/octet-stream')
            
            # باز کردن فایل و ارسال آن (همان فایل آپلود شده - باینری)
            file = open(file_path, 'rb')
            response = FileResponse(file, content_type=content_type, as_attachment=True)
            
            # Encode کردن نام فایل برای پشتیبانی از کاراکترهای فارسی و خاص
            # استفاده از RFC 2231 برای پشتیبانی بهتر از کاراکترهای غیر ASCII
            encoded_filename = quote(original_filename, safe='')
            # استفاده از هر دو فرمت برای سازگاری بیشتر با مرورگرها
            response['Content-Disposition'] = f'attachment; filename="{original_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            
            return response
        except Exception as e:
            logger.error(f"Error downloading strategy file {strategy.id}: {str(e)}")
            return Response({
                'status': 'error',
                'message': f'خطا در دانلود فایل: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StrategyMarketplaceViewSet(viewsets.ModelViewSet):
    """مدیریت مارکت‌پلیس استراتژی‌ها."""

    permission_classes = [IsAuthenticated]
    pagination_class = None
    PLATFORM_FEE_PERCENT = Decimal('10.0')

    @staticmethod
    def _require_owner_nickname(user):
        profile = getattr(user, 'profile', None)
        nickname = (profile.nickname or '').strip() if profile and getattr(profile, 'nickname', None) else ''
        if not nickname:
            raise ValidationError({'nickname': 'برای انتشار استراتژی در مارکت‌پلیس لازم است ابتدا نیک‌نیم خود را در پروفایل تکمیل کنید.'})

    @staticmethod
    def _get_latest_result(strategy, owner):
        return Result.objects.filter(
            job__strategy=strategy,
            job__user=owner,
            job__job_type='backtest',
            job__status='completed'
        ).order_by('-created_at').first()

    @staticmethod
    def _build_metrics(result: Result):
        snapshot = {
            'total_return_percent': round(result.total_return or 0.0, 4),
            'win_rate_percent': round(result.win_rate or 0.0, 4),
            'max_drawdown_percent': round(result.max_drawdown or 0.0, 4),
            'total_trades': result.total_trades,
            'winning_trades': result.winning_trades,
            'losing_trades': result.losing_trades,
            'generated_at': result.created_at.isoformat() if result.created_at else None,
            'job_id': result.job_id,
        }

        trades = result.trades_details or []
        sample_trades = []
        for trade in trades[:10]:
            sample_trades.append({
                'entry_date': trade.get('entry_date'),
                'exit_date': trade.get('exit_date'),
                'entry_price': trade.get('entry_price'),
                'exit_price': trade.get('exit_price'),
                'pnl': trade.get('pnl'),
                'pnl_percent': trade.get('pnl_percent'),
                'duration_days': trade.get('duration_days'),
                'entry_reason_fa': trade.get('entry_reason_fa'),
                'exit_reason_fa': trade.get('exit_reason_fa'),
            })

        equity_curve = result.equity_curve_data or []
        snapshot['equity_curve_preview'] = equity_curve[-50:]

        return snapshot, sample_trades

    @staticmethod
    def _quantize(amount):
        if amount is None:
            amount = Decimal('0')
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def get_queryset(self):
        user = self.request.user
        action = getattr(self, 'action', None)
        qs = StrategyMarketplaceListing.objects.select_related('strategy', 'owner')

        if user.is_staff or user.is_superuser:
            return qs

        if action in ['publish', 'unpublish', 'update', 'partial_update', 'destroy', 'accesses']:
            return qs.filter(owner=user)

        if action in ['retrieve', 'start_trial', 'purchase', 'access_info']:
            return qs.filter(
                Q(is_published=True) | Q(owner=user) | Q(accesses__user=user)
            ).distinct()

        return qs.filter(Q(is_published=True) | Q(owner=user)).distinct()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return StrategyMarketplaceListingWriteSerializer
        return StrategyMarketplaceListingSerializer

    def perform_create(self, serializer):
        strategy = serializer.validated_data['strategy']
        user = self.request.user
        if strategy.user_id != user.id and not (user.is_staff or user.is_superuser):
            raise ValidationError({'strategy': 'مجوز انتشار این استراتژی را ندارید.'})
        if hasattr(strategy, 'marketplace_entry'):
            raise ValidationError({'strategy': 'برای این استراتژی قبلاً لیست مارکت‌پلیس ساخته شده است.'})

        self._require_owner_nickname(user)
        latest_result = self._get_latest_result(strategy, user)
        if not latest_result:
            raise ValidationError({'detail': 'برای انتشار استراتژی ابتدا باید حداقل یک بک‌تست موفق انجام دهید.'})

        performance_snapshot, sample_trades = self._build_metrics(latest_result)

        serializer.save(
            owner=user,
            performance_snapshot=performance_snapshot,
            sample_results=sample_trades,
            source_result=latest_result
        )

    def perform_update(self, serializer):
        listing = self.get_object()
        user = self.request.user
        if listing.owner_id != user.id and not (user.is_staff or user.is_superuser):
            raise ValidationError({'detail': 'مجوز ویرایش این استراتژی را ندارید.'})

        self._require_owner_nickname(listing.owner)
        latest_result = self._get_latest_result(listing.strategy, listing.owner)
        if not latest_result:
            raise ValidationError({'detail': 'برای ویرایش این استراتژی لازم است ابتدا یک بک‌تست موفق داشته باشید.'})

        performance_snapshot, sample_trades = self._build_metrics(latest_result)

        serializer.save(
            performance_snapshot=performance_snapshot,
            sample_results=sample_trades,
            source_result=latest_result
        )

    def destroy(self, request, *args, **kwargs):
        listing = self.get_object()
        user = request.user
        if listing.owner_id != user.id and not (user.is_staff or user.is_superuser):
            return Response({'error': 'مجوز حذف این استراتژی را ندارید.'}, status=status.HTTP_403_FORBIDDEN)
        if listing.is_published:
            listing.mark_unpublished()
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        listing = self.get_object()
        if listing.owner_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'مجوز انتشار ندارید.'}, status=status.HTTP_403_FORBIDDEN)
        listing.mark_published()
        return Response(StrategyMarketplaceListingSerializer(listing, context={'request': request}).data)

    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        listing = self.get_object()
        if listing.owner_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'مجوز لغو انتشار ندارید.'}, status=status.HTTP_403_FORBIDDEN)
        listing.mark_unpublished()
        return Response(StrategyMarketplaceListingSerializer(listing, context={'request': request}).data)

    @action(detail=False, methods=['get'], url_path='strategy-summary')
    def strategy_summary(self, request):
        strategy_id = request.query_params.get('strategy')
        if not strategy_id:
            return Response({'error': 'پارامتر strategy الزامی است.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            strategy = get_user_strategy_or_404(request.user, id=strategy_id)
        except Http404:
            return Response({'error': 'استراتژی پیدا نشد یا دسترسی ندارید.'}, status=status.HTTP_404_NOT_FOUND)

        latest_result = self._get_latest_result(strategy, request.user)
        if not latest_result:
            return Response({
                'has_result': False,
                'strategy_id': strategy.id,
                'strategy_name': strategy.name,
                'message': 'برای این استراتژی هنوز بک‌تست موفقی ثبت نشده است.'
            }, status=status.HTTP_200_OK)

        performance_snapshot, sample_trades = self._build_metrics(latest_result)

        return Response({
            'has_result': True,
            'strategy_id': strategy.id,
            'strategy_name': strategy.name,
            'result_id': latest_result.id,
            'metrics': performance_snapshot,
            'sample_trades': sample_trades,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-listings')
    def my_listings(self, request):
        listings = StrategyMarketplaceListing.objects.select_related('strategy', 'owner').filter(owner=request.user)
        serializer = StrategyMarketplaceListingSerializer(listings, many=True, context={'request': request})
        return Response({'results': serializer.data})

    @action(detail=False, methods=['get'], url_path='my-accesses')
    def my_accesses(self, request):
        accesses = StrategyListingAccess.objects.select_related('listing', 'listing__owner').filter(user=request.user)
        serializer = StrategyListingAccessSerializer(accesses, many=True, context={'request': request})
        return Response({'results': serializer.data})

    @action(detail=True, methods=['get'], url_path='access')
    def access_info(self, request, pk=None):
        listing = self.get_object()
        try:
            access = listing.accesses.get(user=request.user)
        except StrategyListingAccess.DoesNotExist:
            return Response({'access': None})
        return Response({'access': StrategyListingAccessSerializer(access, context={'request': request}).data})

    @action(detail=True, methods=['get'], url_path='accesses')
    def accesses(self, request, pk=None):
        listing = self.get_object()
        if listing.owner_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
            return Response({'error': 'دسترسی مجاز نیست.'}, status=status.HTTP_403_FORBIDDEN)
        accesses = listing.accesses.select_related('user').all()
        serializer = StrategyListingAccessSerializer(accesses, many=True, context={'request': request})
        return Response({'results': serializer.data})

    @action(detail=True, methods=['post'], url_path='start-trial')
    def start_trial(self, request, pk=None):
        listing = self.get_object()
        user = request.user

        if listing.owner_id == user.id:
            return Response({'error': 'مالک استراتژی نیازی به دوره آزمایشی ندارد.'}, status=status.HTTP_400_BAD_REQUEST)
        if not listing.is_published:
            return Response({'error': 'این استراتژی هنوز منتشر نشده است.'}, status=status.HTTP_400_BAD_REQUEST)

        access, created = StrategyListingAccess.objects.get_or_create(
            listing=listing,
            user=user,
            defaults={
                'status': 'trial',
                'trial_started_at': timezone.now(),
                'trial_expires_at': timezone.now() + timedelta(days=listing.trial_days or 9),
                'total_backtests_run': 0,
                'last_price': self._quantize(0),
                'platform_fee_percent': self.PLATFORM_FEE_PERCENT,
                'platform_fee_amount': self._quantize(0),
                'owner_amount': self._quantize(0),
            }
        )

        if not created:
            access.ensure_status()
            if access.trial_started_at:
                if access.is_trial_active():
                    return Response({
                        'message': 'دوره آزمایشی فعال است.',
                        'access': StrategyListingAccessSerializer(access, context={'request': request}).data
                    })
                return Response({'error': 'شما قبلاً از دوره آزمایشی استفاده کرده‌اید.'}, status=status.HTTP_400_BAD_REQUEST)

            access.status = 'trial'
            access.trial_started_at = timezone.now()
            access.trial_expires_at = timezone.now() + timedelta(days=listing.trial_days or 9)
            access.total_backtests_run = 0
            access.last_backtest_at = None
            access.last_price = self._quantize(0)
            access.platform_fee_percent = self.PLATFORM_FEE_PERCENT
            access.platform_fee_amount = self._quantize(0)
            access.owner_amount = self._quantize(0)
            access.save(update_fields=['status', 'trial_started_at', 'trial_expires_at', 'total_backtests_run', 'last_backtest_at', 'last_price', 'platform_fee_percent', 'platform_fee_amount', 'owner_amount', 'updated_at'])

        data = StrategyListingAccessSerializer(access, context={'request': request}).data
        return Response({'access': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        listing = self.get_object()
        user = request.user

        if listing.owner_id == user.id:
            return Response({'error': 'مالک استراتژی نیازی به خرید ندارد.'}, status=status.HTTP_400_BAD_REQUEST)
        if not listing.is_published:
            return Response({'error': 'این استراتژی منتشر نشده است.'}, status=status.HTTP_400_BAD_REQUEST)

        price = listing.price or Decimal('0')
        price = self._quantize(price)
        if price < 0:
            return Response({'error': 'قیمت نامعتبر است.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user, defaults={'balance': Decimal('0.00')})

            if wallet.balance < price:
                return Response({'error': 'موجودی کیف پول کافی نیست.'}, status=status.HTTP_400_BAD_REQUEST)

            wallet.balance -= price
            wallet.save(update_fields=['balance', 'updated_at'])

            now = timezone.now()

            transaction_obj = Transaction.objects.create(
                wallet=wallet,
                transaction_type='subscription_purchase',
                amount=price,
                status='completed',
                description=f'خرید اشتراک استراتژی مارکت‌پلیس: {listing.title}',
                completed_at=now
            )

            access, _ = StrategyListingAccess.objects.select_for_update().get_or_create(
                listing=listing,
                user=user,
                defaults={'status': 'active'}
            )

            access.status = 'active'
            access.activated_at = now
            access.expires_at = now + timedelta(days=listing.billing_cycle_days or 30)
            access.last_payment_transaction = transaction_obj
            platform_amount = self._quantize(price * self.PLATFORM_FEE_PERCENT / Decimal('100'))
            owner_amount = self._quantize(price - platform_amount)
            remainder = price - (platform_amount + owner_amount)
            if remainder != 0:
                owner_amount = self._quantize(owner_amount + remainder)

            access.last_price = price
            access.platform_fee_percent = self.PLATFORM_FEE_PERCENT
            access.platform_fee_amount = platform_amount
            access.owner_amount = owner_amount
            access.save(update_fields=['status', 'activated_at', 'expires_at', 'last_payment_transaction', 'last_price', 'platform_fee_percent', 'platform_fee_amount', 'owner_amount', 'updated_at'])

            admin_user = User.objects.filter(is_superuser=True).order_by('id').first()
            if admin_user:
                admin_wallet, _ = Wallet.objects.select_for_update().get_or_create(user=admin_user, defaults={'balance': Decimal('0.00')})
                admin_wallet.balance += platform_amount
                admin_wallet.save(update_fields=['balance', 'updated_at'])
                Transaction.objects.create(
                    wallet=admin_wallet,
                    transaction_type='payment',
                    amount=platform_amount,
                    status='completed',
                    description=f'سهم پلتفرم از اشتراک استراتژی: {listing.title}',
                    completed_at=now
                )

            owner_wallet, _ = Wallet.objects.select_for_update().get_or_create(user=listing.owner, defaults={'balance': Decimal('0.00')})
            owner_wallet.balance += owner_amount
            owner_wallet.save(update_fields=['balance', 'updated_at'])
            Transaction.objects.create(
                wallet=owner_wallet,
                transaction_type='payment',
                amount=owner_amount,
                status='completed',
                description=f'درآمد صاحب استراتژی از اشتراک: {listing.title}',
                completed_at=now
            )

        access.refresh_from_db()
        data = StrategyListingAccessSerializer(access, context={'request': request}).data
        return Response({'access': data}, status=status.HTTP_200_OK)


class StrategyQuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy questions"""
    serializer_class = None  # Will be set in __init__
    permission_classes = [IsAuthenticated]
    filterset_fields = ['strategy', 'status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from api.serializers import StrategyQuestionSerializer
        self.serializer_class = StrategyQuestionSerializer
    
    def get_queryset(self):
        from core.models import StrategyQuestion
        user = self.request.user
        queryset = StrategyQuestion.objects.all()
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(strategy__user=user)
        strategy_id = self.request.query_params.get('strategy', None)
        if strategy_id:
            queryset = queryset.filter(strategy_id=strategy_id)
        return queryset.order_by('order', 'created_at')
    
    def update(self, request, *args, **kwargs):
        """Update question answer"""
        from django.utils import timezone
        from core.models import StrategyQuestion
        
        question = self.get_object()
        answer = request.data.get('answer', '')
        status = request.data.get('status', 'answered')
        
        question.answer = answer
        question.status = status
        if status == 'answered' and answer:
            question.answered_at = timezone.now()
        question.save()
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing jobs"""
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Job.objects.select_related(
            'strategy',
            'result',
            'marketplace_access',
            'marketplace_access__listing',
            'marketplace_access__listing__owner',
        )
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(user=user)
        return queryset
    
    def create(self, request):
        """Create new job (backtest or demo trade)"""
        serializer = JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        strategy_id = serializer.validated_data['strategy']
        job_type = serializer.validated_data['job_type']
        timeframe_days = serializer.validated_data.get('timeframe_days', 365)
        symbol_override = serializer.validated_data.get('symbol')
        initial_capital = serializer.validated_data.get('initial_capital', 10000)
        selected_indicators = serializer.validated_data.get('selected_indicators', [])
        ai_provider = serializer.validated_data.get('ai_provider', None)
        
        user = request.user
        marketplace_access = None
        origin = 'direct'

        try:
            strategy = get_user_strategy_or_404(user, id=strategy_id)
        except Http404:
            marketplace_access = (
                StrategyListingAccess.objects.select_related('listing', 'listing__strategy')
                .filter(listing__strategy_id=strategy_id, user=user)
                .first()
            )

            if not marketplace_access:
                return Response({'error': 'به این استراتژی دسترسی ندارید.'}, status=status.HTTP_403_FORBIDDEN)

            marketplace_access.ensure_status()

            if not marketplace_access.has_active_access():
                return Response({'error': 'دسترسی شما منقضی شده است.'}, status=status.HTTP_403_FORBIDDEN)

            listing = marketplace_access.listing
            if marketplace_access.is_trial_active() and listing.trial_backtest_limit is not None:
                if marketplace_access.total_backtests_run >= listing.trial_backtest_limit:
                    return Response({'error': 'حداکثر تعداد بک‌تست در دوره آزمایشی مصرف شده است.'}, status=status.HTTP_403_FORBIDDEN)

            strategy = listing.strategy
            origin = 'marketplace_trial' if marketplace_access.is_trial_active() else 'marketplace_active'

        if marketplace_access and job_type != 'backtest':
            return Response({'error': 'برای استراتژی‌های مارکت‌پلیس تنها امکان اجرای بک‌تست وجود دارد.'}, status=status.HTTP_400_BAD_REQUEST)

        if job_type == 'backtest':
            # فقط برای استراتژی‌های کاربر (نه مارکت‌پلیس) بررسی می‌کنیم که آیا حداقل یک استراتژی وجود دارد
            # اما اجازه می‌دهیم هر استراتژی کاربر برای بک‌تست استفاده شود، نه فقط استراتژی اصلی
            if not marketplace_access:
                # برای استراتژی‌های کاربر، بررسی می‌کنیم که استراتژی متعلق به کاربر باشد
                if strategy.user != user:
                    return Response(
                        {'error': 'شما به این استراتژی دسترسی ندارید.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                # بررسی می‌کنیم که استراتژی فایل داشته باشد
                if not strategy.strategy_file:
                    return Response(
                        {'error': 'استراتژی انتخاب شده فایل ندارد. لطفاً ابتدا استراتژی را آپلود کنید.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Create job
        job = Job.objects.create(
            user=user,
            strategy=strategy,
            job_type=job_type,
            status='pending',
            marketplace_access=marketplace_access,
            origin=origin
        )

        if marketplace_access and job_type == 'backtest':
            marketplace_access.increment_backtests(save=True)
        
        # Try to run task asynchronously if Celery is available
        celery_available = _is_celery_available_quick()
        
        if celery_available:
            # Run task asynchronously using Celery
            try:
                if job_type == 'backtest':
                    logger.info(f"Starting async backtest task for job {job.id}, strategy {strategy_id}, timeframe {timeframe_days} days, ai_provider={ai_provider}")
                    run_backtest_task.delay(
                        job.id,
                        timeframe_days=timeframe_days,
                        symbol_override=symbol_override,
                        initial_capital=initial_capital,
                        selected_indicators=selected_indicators,
                        ai_provider=ai_provider
                    )
                else:
                    logger.info(f"Starting async demo trade task for job {job.id}")
                    run_demo_trade_task.delay(job.id)
                
                logger.info(f"Job {job.id} queued successfully. Status: {job.status}")
                # Return immediately - task will run in background
                return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                logger.warning(f"Failed to queue async task for job {job.id}: {e}. Falling back to synchronous execution.")
                celery_available = False  # Fallback to sync
        
        # Fallback: Run synchronously if Celery is not available
        # اما برای جلوگیری از timeout، حتی در حالت sync هم job را ایجاد می‌کنیم و در background اجرا می‌کنیم
        if not celery_available:
            logger.warning(
                f"Celery/Redis is not available. For backtest jobs, we'll create the job and return immediately. "
                "The task will run in a separate thread to avoid timeout. Please start Redis and Celery worker for better performance."
            )
            
            # برای بک تست، حتی اگر Celery در دسترس نباشد، job را ایجاد می‌کنیم و در background اجرا می‌کنیم
            if job_type == 'backtest':
                import threading
                def run_backtest_in_thread():
                    try:
                        logger.info(f"Starting synchronous backtest in thread for job {job.id}, strategy {strategy_id}, timeframe {timeframe_days} days, ai_provider={ai_provider}")
                        run_backtest_task(job.id, timeframe_days=timeframe_days, symbol_override=symbol_override, initial_capital=initial_capital, selected_indicators=selected_indicators, ai_provider=ai_provider)
                        job.refresh_from_db()
                        logger.info(f"Backtest task completed in thread for job {job.id}, status: {job.status}, result_id: {job.result_id}")
                    except Exception as e:
                        logger.error(f"Error executing backtest task in thread for job {job.id}: {e}", exc_info=True)
                        job.refresh_from_db()
                        job.status = 'failed'
                        job.error_message = str(e)
                        job.save()
                
                # اجرای بک تست در thread جداگانه
                thread = threading.Thread(target=run_backtest_in_thread, daemon=True)
                thread.start()
                
                # فوراً response را برمی‌گردانیم
                logger.info(f"Job {job.id} created and backtest started in background thread. Returning immediately.")
                return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
            else:
                # برای demo trade، sync اجرا می‌کنیم
                try:
                    logger.info(f"Starting synchronous demo trade for job {job.id}")
                    run_demo_trade_task(job.id)
                    job.refresh_from_db()
                except Exception as e:
                    logger.error(f"Error executing demo trade task synchronously for job {job.id}: {e}", exc_info=True)
                    job.refresh_from_db()
        
        return Response(JobSerializer(job).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get job status"""
        job = self.get_object()
        payload = {
            'status': job.status,
            'error_message': job.error_message,
        }
        if job.result_id:
            payload['result_id'] = job.result_id
        return Response(payload)


class ResultViewSet(viewsets.ModelViewSet):
    """ViewSet for managing results (list, retrieve, delete)."""
    serializer_class = ResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Result.objects.select_related(
            'job',
            'job__strategy',
            'job__user',
        )
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(job__user=user)
        job_id = self.request.query_params.get('job')
        if job_id:
            qs = qs.filter(job_id=job_id)
        return qs

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all results or filtered by job."""
        results = self.get_queryset()
        count = results.count()
        return Response({
            'total_results': count,
            'average_return': (sum(r.total_return for r in results) / count) if count > 0 else 0,
            'total_trades': sum(r.total_trades for r in results),
        })

    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Delete all results, optionally filtered by ?job=<id>."""
        results = self.get_queryset()
        deleted_count = results.count()
        results.delete()
        return Response({'deleted': deleted_count})


class LiveTradeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing live trades."""
    serializer_class = LiveTradeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['symbol', 'status', 'strategy']
    pagination_class = None  # Disable pagination for trades - return all results
    
    def get_queryset(self):
        user = self.request.user
        queryset = LiveTrade.objects.select_related('strategy', 'strategy__user')
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(strategy__user=user)
        return queryset
    
    @action(detail=False, methods=['get'])
    def account_info(self, request):
        """Get MT5 account information."""
        from .mt5_client import get_symbol_for_account
        
        account_info, error = get_mt5_account_info()
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get recommended symbol based on account type
        recommended_symbol = get_symbol_for_account('XAUUSD')
        
        response_data = {
            'status': 'success',
            'account': account_info,
            'recommended_symbol': recommended_symbol,
            'is_demo': account_info.get('is_demo', False)
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def mt5_positions(self, request):
        """Get all open positions from MT5."""
        symbol = request.query_params.get('symbol')
        positions, error = get_mt5_positions(symbol)
        if error:
            return Response({'status': 'error', 'message': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': 'success', 'positions': positions})
    
    @action(detail=False, methods=['get'])
    def market_status(self, request):
        """Check if market is open."""
        is_open, message = is_market_open()
        return Response({
            'status': 'success',
            'market_open': is_open,
            'message': message
        })
    
    @action(detail=False, methods=['post'])
    def open_trade(self, request):
        """Open a new trade based on strategy."""
        from django.utils import timezone
        
        strategy_id = request.data.get('strategy_id')
        symbol_input = request.data.get('symbol', 'XAUUSD')
        trade_type = request.data.get('trade_type')  # 'buy' or 'sell'
        volume = request.data.get('volume', 0.01)
        stop_loss = request.data.get('stop_loss')
        take_profit = request.data.get('take_profit')
        
        # Auto-detect correct symbol based on account type if base symbol provided
        from .mt5_client import get_symbol_for_account
        if '_' not in symbol_input or (not symbol_input.endswith('_o') and not symbol_input.endswith('_l')):
            # User provided base symbol without suffix, auto-detect
            symbol = get_symbol_for_account(symbol_input)
            logger.info(f"Auto-detected symbol: {symbol_input} -> {symbol}")
        else:
            # User provided specific symbol, use it
            symbol = symbol_input
        
        # Validate inputs
        if not strategy_id:
            return Response({
                'status': 'error',
                'message': 'strategy_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if trade_type not in ['buy', 'sell']:
            return Response({
                'status': 'error',
                'message': 'trade_type must be "buy" or "sell"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if market is open
        market_open, market_msg = is_market_open()
        if not market_open:
            return Response({
                'status': 'error',
                'message': f'Cannot open trade: {market_msg}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            strategy = get_user_strategy_or_404(request.user, id=strategy_id)
        except Http404:
            return Response({
                'status': 'error',
                'message': 'استراتژی پیدا نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # هشدار اگر استراتژی غیرفعال باشد
        if not strategy.is_active:
            logger.warning(f"Attempting to open trade with inactive strategy {strategy_id}")
        
        # Open trade in MT5
        result, error = open_mt5_trade(
            symbol=symbol,
            trade_type=trade_type,
            volume=float(volume),
            stop_loss=float(stop_loss) if stop_loss else None,
            take_profit=float(take_profit) if take_profit else None,
            comment=f'Strategy: {strategy.name}'
        )
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save to database
        try:
            live_trade = LiveTrade.objects.create(
                strategy=strategy,
                mt5_ticket=result['ticket'],
                symbol=result['symbol'],
                trade_type=result['type'],
                volume=result['volume'],
                open_price=result['price_open'],
                current_price=result.get('price_current'),
                stop_loss=result.get('stop_loss'),
                take_profit=result.get('take_profit'),
                profit=result.get('profit', 0.0),
                swap=result.get('swap', 0.0),
                commission=result.get('commission', 0.0),
                status='open'
            )
            
            logger.info(f"Trade opened: {live_trade.mt5_ticket} - {symbol} {trade_type} {volume}")
            
            return Response({
                'status': 'success',
                'message': 'Trade opened successfully',
                'trade': LiveTradeSerializer(live_trade).data
            })
        except Exception as e:
            logger.exception(f"Error saving trade to database: {e}")
            return Response({
                'status': 'error',
                'message': f'Trade opened in MT5 but failed to save: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def close_trade(self, request, pk=None):
        """Close a trade."""
        from django.utils import timezone
        
        live_trade = self.get_object()
        
        if live_trade.status != 'open':
            return Response({
                'status': 'error',
                'message': f'Trade is already {live_trade.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        volume = request.data.get('volume')  # Optional partial close
        
        # Close in MT5
        result, error = close_mt5_trade(live_trade.mt5_ticket, float(volume) if volume else None)
        
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update in database
        live_trade.status = 'closed'
        live_trade.closed_at = timezone.now()
        live_trade.close_price = result.get('close_price')
        live_trade.profit = result.get('profit', live_trade.profit)
        live_trade.close_reason = result.get('comment', 'Manual close')
        live_trade.save()
        
        logger.info(f"Trade closed: {live_trade.mt5_ticket}")
        
        return Response({
            'status': 'success',
            'message': 'Trade closed successfully',
            'trade': LiveTradeSerializer(live_trade).data
        })
    
    @action(detail=False, methods=['post'])
    def sync_positions(self, request):
        """Sync MT5 positions with database."""
        from django.utils import timezone
        
        # Get all positions from MT5
        positions, error = get_mt5_positions()
        if error:
            return Response({
                'status': 'error',
                'message': error
            }, status=status.HTTP_400_BAD_REQUEST)
        
        synced_count = 0
        updated_count = 0
        
        for pos in positions:
            try:
                live_trade, created = LiveTrade.objects.get_or_create(
                    mt5_ticket=pos['ticket'],
                    defaults={
                        'symbol': pos['symbol'],
                        'trade_type': pos['type'],
                        'volume': pos['volume'],
                        'open_price': pos['price_open'],
                        'current_price': pos['price_current'],
                        'profit': pos['profit'],
                        'swap': pos['swap'],
                        'commission': pos['commission'],
                        'stop_loss': pos['stop_loss'],
                        'take_profit': pos['take_profit'],
                        'status': 'open',
                    }
                )
                
                if created:
                    synced_count += 1
                else:
                    # Update existing
                    if live_trade.status == 'open':
                        live_trade.current_price = pos['price_current']
                        live_trade.profit = pos['profit']
                        live_trade.save()
                        updated_count += 1
            except Exception as e:
                logger.error(f"Error syncing position {pos['ticket']}: {e}")
        
        # Mark closed positions that no longer exist in MT5
        mt5_tickets = {p['ticket'] for p in positions}
        closed_trades = self.get_queryset().filter(
            status='open'
        ).exclude(mt5_ticket__in=mt5_tickets)
        
        closed_count = closed_trades.count()
        closed_trades.update(
            status='closed',
            closed_at=timezone.now(),
            close_reason='Position closed in MT5'
        )
        
        return Response({
            'status': 'success',
            'synced': synced_count,
            'updated': updated_count,
            'closed': closed_count,
            'total_positions': len(positions)
        })


class AutoTradingSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for managing auto trading settings"""
    queryset = AutoTradingSettings.objects.all()
    serializer_class = AutoTradingSettingsSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for settings - return all results
    
    def get_queryset(self):
        user = self.request.user
        qs = AutoTradingSettings.objects.select_related('strategy', 'strategy__user')
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(strategy__user=user)
        strategy_id = self.request.query_params.get('strategy')
        if strategy_id:
            qs = qs.filter(strategy_id=strategy_id)
        return qs
    
    @action(detail=False, methods=['post'])
    def create_or_update_for_strategy(self, request):
        """Create or update auto trading settings for a strategy"""
        strategy_id = request.data.get('strategy_id')
        if not strategy_id:
            return Response({
                'status': 'error',
                'message': 'strategy_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            strategy = get_user_strategy_or_404(request.user, id=strategy_id)
        except Http404:
            return Response({
                'status': 'error',
                'message': 'Strategy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        settings, created = AutoTradingSettings.objects.get_or_create(
            strategy=strategy,
            defaults={
                'symbol': request.data.get('symbol', 'XAUUSD'),
                'volume': float(request.data.get('volume', 0.01)),
                'max_open_trades': int(request.data.get('max_open_trades', 3)),
                'check_interval_minutes': int(request.data.get('check_interval_minutes', 5)),
                'use_stop_loss': request.data.get('use_stop_loss', True),
                'use_take_profit': request.data.get('use_take_profit', True),
                'stop_loss_pips': float(request.data.get('stop_loss_pips', 50.0)),
                'take_profit_pips': float(request.data.get('take_profit_pips', 100.0)),
                'risk_per_trade_percent': float(request.data.get('risk_per_trade_percent', 2.0)),
                'is_enabled': request.data.get('is_enabled', False),
            }
        )
        
        if not created:
            # Update existing
            for field in ['symbol', 'volume', 'max_open_trades', 'check_interval_minutes',
                         'use_stop_loss', 'use_take_profit', 'stop_loss_pips',
                         'take_profit_pips', 'risk_per_trade_percent', 'is_enabled']:
                if field in request.data:
                    setattr(settings, field, request.data[field])
            settings.save()
        
        return Response({
            'status': 'success',
            'message': 'Settings saved successfully',
            'settings': AutoTradingSettingsSerializer(settings).data
        })
    
    @action(detail=True, methods=['post'])
    def toggle_enabled(self, request, pk=None):
        """Toggle auto trading on/off"""
        settings = self.get_object()
        settings.is_enabled = not settings.is_enabled
        settings.save()
        
        return Response({
            'status': 'success',
            'is_enabled': settings.is_enabled,
            'message': f'Auto trading {"enabled" if settings.is_enabled else "disabled"}'
        })
    
    @action(detail=False, methods=['post'])
    def test_auto_trade(self, request):
        """Test auto trading for a strategy (dry run)"""
        from api.auto_trader import check_strategy_signals
        
        strategy_id = request.data.get('strategy_id')
        symbol = request.data.get('symbol', 'XAUUSD')
        
        if not strategy_id:
            return Response({
                'status': 'error',
                'message': 'strategy_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            strategy = get_user_strategy_or_404(request.user, id=strategy_id)
        except Http404:
            return Response({
                'status': 'error',
                'message': 'Strategy not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        signal_result = check_strategy_signals(strategy, symbol)
        
        return Response({
            'status': 'success',
            'signal': signal_result
        })
    
    @action(detail=False, methods=['post'])
    def trigger_auto_trading(self, request):
        """Manually trigger the auto trading cycle (for testing/debugging)"""
        from celery import current_app
        
        try:
            # Check if Celery is available
            if current_app.conf.task_always_eager:
                # Running synchronously (e.g., in tests)
                result = run_auto_trading()
            else:
                # Running asynchronously
                task = run_auto_trading.delay()
                result = task.get(timeout=120)  # Wait up to 2 minutes
            
            return Response({
                'status': 'success',
                'message': 'Auto trading cycle completed',
                'result': result
            })
        except Exception as e:
            logger.exception(f"Error triggering auto trading: {e}")
            return Response({
                'status': 'error',
                'message': f'خطا در اجرای معاملات خودکار: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TicketViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tickets for logged-in users"""
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return tickets for the current user only"""
        if self.request.user.is_staff or self.request.user.is_superuser:
            queryset = Ticket.objects.all().prefetch_related('messages', 'user')
        else:
            queryset = Ticket.objects.filter(user=self.request.user).prefetch_related('messages')
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by category if provided
        category_param = self.request.query_params.get('category', None)
        if category_param:
            queryset = queryset.filter(category=category_param)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializer for create action"""
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new ticket with proper error handling"""
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"Ticket validation errors: {serializer.errors}")
            return Response(
                {
                    'error': 'خطا در اعتبارسنجی داده‌ها',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create ticket with user
            ticket = serializer.save(user=request.user)
            
            # Notify admins if configured
            if not (request.user.is_staff or request.user.is_superuser):
                self._notify_admin_new_ticket(ticket)

            # Return full ticket data
            response_serializer = TicketSerializer(ticket)
            logger.info(f"Ticket created: {ticket.id} by user {request.user.username}")
            
            response_data = response_serializer.data

            if not (request.user.is_staff or request.user.is_superuser):
                redirect_url = getattr(settings, 'USER_PANEL_HOME_URL', '/')
                if redirect_url:
                    response_data['redirect_url'] = redirect_url

            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Error creating ticket: {e}")
            return Response(
                {
                    'error': 'خطا در ایجاد تیکت',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _notify_admin_new_ticket(self, ticket):
        """Send SMS notification to configured admins about new ticket"""
        admin_phones = getattr(settings, 'ADMIN_NOTIFICATION_PHONES', [])

        if not admin_phones:
            logger.debug("No admin phone numbers configured for ticket notifications.")
            return

        message = (
            f"تیکت جدید #{ticket.id} توسط {ticket.user.username} ثبت شد.\n"
            f"عنوان: {ticket.title}"
        )

        for phone in admin_phones:
            try:
                result = send_sms(phone, message)
                if not result.get('success', False):
                    logger.error(
                        "Failed to send ticket notification SMS to %s: %s",
                        phone,
                        result.get('message', 'Unknown error')
                    )
            except Exception:
                logger.exception(
                    "Unexpected error while sending ticket notification SMS to %s",
                    phone
                )
    
    def list(self, request, *args, **kwargs):
        """List tickets with proper serialization"""
        queryset = self.filter_queryset(self.get_queryset())
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a single ticket with messages"""
        instance = self.get_object()
        
        # Check if ticket belongs to user or user is admin/staff
        is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        
        if not is_admin and instance.user != request.user:
            return Response(
                {'error': 'شما دسترسی به این تیکت ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_message(self, request, pk=None):
        """Add a message to a ticket (user or admin)"""
        ticket = self.get_object()
        
        # Check if user is admin/staff
        is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        
        # Check if ticket belongs to user or user is admin
        if not is_admin and ticket.user != request.user:
            return Response(
                {'error': 'شما دسترسی به این تیکت ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message_text = request.data.get('message', '').strip()
        if not message_text:
            return Response(
                {'error': 'پیام نمی‌تواند خالی باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create message
            message = TicketMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=message_text,
                is_admin=is_admin
            )
            
            # If admin is responding, update ticket
            if is_admin:
                # Update admin_response field
                ticket.admin_response = message_text
                ticket.admin_user = request.user
                
                # Update status if needed
                if ticket.status == 'open':
                    ticket.status = 'in_progress'
                elif ticket.status == 'closed':
                    ticket.status = 'open'
                
                ticket.save()
            else:
                # If user is responding and ticket was closed, reopen it
                if ticket.status == 'closed':
                    ticket.status = 'open'
                    ticket.save()
            
            serializer = TicketMessageSerializer(message)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.exception(f"Error adding message to ticket {ticket.id}: {e}")
            return Response(
                {'error': 'خطا در ارسال پیام', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close a ticket (user or admin)"""
        ticket = self.get_object()
        
        # Check if user is admin/staff
        is_admin = request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)
        
        # Check if ticket belongs to user or user is admin
        if not is_admin and ticket.user != request.user:
            return Response(
                {'error': 'شما دسترسی به این تیکت ندارید'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            ticket.close_ticket()
            serializer = self.get_serializer(ticket)
            return Response(serializer.data)
        except Exception as e:
            logger.exception(f"Error closing ticket {ticket.id}: {e}")
            return Response(
                {'error': 'خطا در بستن تیکت', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminOrStaff])
    def all_tickets(self, request):
        """Get all tickets (admin only)"""
        queryset = Ticket.objects.all().prefetch_related('messages', 'user')
        
        # Filter by status if provided
        status_param = request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by category if provided
        category_param = request.query_params.get('category', None)
        if category_param:
            queryset = queryset.filter(category=category_param)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrStaff])
    def admin_response(self, request, pk=None):
        """Admin response to ticket (sets admin_response and updates status)"""
        ticket = self.get_object()
        
        response_text = request.data.get('response', '').strip()
        new_status = request.data.get('status', None)
        
        if not response_text:
            return Response(
                {'error': 'پاسخ نمی‌تواند خالی باشد'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update ticket
            ticket.admin_response = response_text
            ticket.admin_user = request.user
            
            if new_status and new_status in ['open', 'in_progress', 'resolved', 'closed']:
                ticket.status = new_status
                if new_status == 'resolved':
                    from django.utils import timezone
                    ticket.resolved_at = timezone.now()
            
            ticket.save()
            
            # Also create a message
            message = TicketMessage.objects.create(
                ticket=ticket,
                user=request.user,
                message=response_text,
                is_admin=True
            )
            
            serializer = self.get_serializer(ticket)
            return Response(serializer)
        except Exception as e:
            logger.exception(f"Error adding admin response to ticket {ticket.id}: {e}")
            return Response(
                {'error': 'خطا در ثبت پاسخ', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrStaff])
    def update_status(self, request, pk=None):
        """Update ticket status (admin only)"""
        ticket = self.get_object()
        
        new_status = request.data.get('status', None)
        
        if not new_status or new_status not in ['open', 'in_progress', 'resolved', 'closed']:
            return Response(
                {'error': 'وضعیت نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ticket.status = new_status
            if new_status == 'resolved':
                from django.utils import timezone
                ticket.resolved_at = timezone.now()
                ticket.admin_user = request.user
            
            ticket.save()
            serializer = self.get_serializer(ticket)
            return Response(serializer)
        except Exception as e:
            logger.exception(f"Error updating ticket status {ticket.id}: {e}")
            return Response(
                {'error': 'خطا در به‌روزرسانی وضعیت', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user wallet"""
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)
    
    def get_object(self):
        wallet, created = Wallet.objects.get_or_create(user=self.request.user)
        return wallet
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get current wallet balance"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        return Response({
            'balance': float(wallet.balance),
            'balance_formatted': f"{wallet.balance:,.0f} تومان"
        })

    @action(detail=False, methods=['post'])
    def charge(self, request):
        """Create payment request for wallet charge"""
        from django.utils import timezone
        from api.payment_service import get_zarinpal_service
        
        amount = request.data.get('amount')
        if not amount:
            return Response(
                {'error': 'مبلغ شارژ الزامی است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount = float(amount)
            if amount <= 0:
                return Response(
                    {'error': 'مبلغ باید بیشتر از صفر باشد'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': 'مبلغ معتبر نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        
        # Create transaction record
        transaction = Transaction.objects.create(
            wallet=wallet,
            transaction_type='charge',
            amount=amount,
            status='pending',
            description=f'شارژ کیف پول به مبلغ {amount:,.0f} تومان'
        )
        
        # Create payment request
        payment_service = get_zarinpal_service()
        callback_url = request.build_absolute_uri(f'/api/payments/callback/?transaction_id={transaction.id}')
        payment_result = payment_service.create_payment_request(
            amount=int(amount),
            description=f'شارژ کیف پول به مبلغ {amount:,.0f} تومان',
            callback_url=callback_url,
            email=request.user.email if request.user.email else None,
            mobile=getattr(request.user, 'phone_number', None) if hasattr(request.user, 'phone_number') else None
        )
        
        if payment_result['status'] == 'success':
            transaction.zarinpal_authority = payment_result['authority']
            transaction.save()
            
            return Response({
                'status': 'success',
                'payment_url': payment_result['start_pay_url'],
                'message': 'لطفاً به صفحه پرداخت هدایت می‌شوید',
                'transaction_id': transaction.id
            })
        else:
            transaction.status = 'failed'
            transaction.save()
            return Response(
                {'error': payment_result.get('error', 'خطا در ایجاد درخواست پرداخت')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIRecommendationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing AI recommendations"""
    serializer_class = AIRecommendationSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['strategy', 'status', 'recommendation_type']
    
    def get_queryset(self):
        queryset = AIRecommendation.objects.all()
        strategy_id = self.request.query_params.get('strategy', None)
        if strategy_id:
            queryset = queryset.filter(strategy_id=strategy_id)
        return queryset.order_by('-created_at')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'])
    def generate(self, request, pk=None):
        """Generate AI recommendations for a strategy"""
        from ai_module.gemini_client import generate_ai_recommendations
        from ai_module.nlp_parser import extract_text_from_file
        from django.utils import timezone
        
        strategy = self.get_object()
        
        if not strategy.parsed_strategy_data:
            return Response(
                {'error': 'استراتژی باید ابتدا پردازش شود'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get raw text
            raw_text = ''
            if strategy.strategy_file:
                raw_text = extract_text_from_file(strategy.strategy_file.path)
            
            # Get analysis if available
            analysis = strategy.parsed_strategy_data.get('analysis')
            
            # Generate recommendations
            recommendations_result = generate_ai_recommendations(
                strategy.parsed_strategy_data,
                raw_text,
                analysis,
                user=request.user
            )
            
            if recommendations_result.get('ai_status') != 'ok':
                message = recommendations_result.get(
                    'message',
                    "AI analysis unavailable. Please configure your AI provider (OpenAI ChatGPT or Gemini) in Settings."
                )
                return Response(
                    {'error': message},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            recommendations_data = recommendations_result.get('recommendations', [])
            if not recommendations_data:
                return Response(
                    {'error': 'هیچ پیشنهادی تولید نشد. لطفاً استراتژی را دقیق‌تر بررسی کنید.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create recommendation records
            created_recommendations = []
            for rec_data in recommendations_data:
                recommendation = AIRecommendation.objects.create(
                    strategy=strategy,
                    recommendation_type=rec_data.get('type', 'general'),
                    title=rec_data.get('title', 'پیشنهاد بهبود'),
                    description=rec_data.get('description', ''),
                    recommendation_data=rec_data.get('data', {}),
                    price=150000,  # 150,000 Toman
                    status='generated'
                )
                created_recommendations.append(recommendation)
            
            serializer = self.get_serializer(created_recommendations, many=True)
            return Response({
                'status': 'success',
                'count': len(created_recommendations),
                'recommendations': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return Response(
                {'error': f'خطا در تولید پیشنهادات: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        """Purchase an AI recommendation"""
        from django.utils import timezone
        from api.payment_service import get_zarinpal_service
        
        recommendation = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'برای خرید باید وارد حساب کاربری شوید'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if already purchased
        if recommendation.status == 'purchased' and recommendation.purchased_by == user:
            return Response({
                'status': 'already_purchased',
                'message': 'این پیشنهاد قبلاً خریداری شده است'
            })
        
        # Get or create wallet
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        # Check balance
        if wallet.balance < recommendation.price:
            # Need to charge - create payment request
            payment_service = get_zarinpal_service()
            
            # Create transaction record
            transaction = Transaction.objects.create(
                wallet=wallet,
                transaction_type='charge',
                amount=recommendation.price,
                status='pending',
                description=f'شارژ برای خرید پیشنهاد: {recommendation.title}',
                ai_recommendation=recommendation
            )
            
            # Create payment request
            callback_url = request.build_absolute_uri(f'/api/payments/callback/?transaction_id={transaction.id}')
            payment_result = payment_service.create_payment_request(
                amount=int(recommendation.price),
                description=f'شارژ کیف پول برای خرید پیشنهاد AI: {recommendation.title}',
                callback_url=callback_url,
                email=user.email if user.email else None,
                mobile=getattr(user.profile, 'phone_number', None) if hasattr(user, 'profile') else None
            )
            
            if payment_result['status'] == 'success':
                transaction.zarinpal_authority = payment_result['authority']
                transaction.save()
                
                return Response({
                    'status': 'payment_required',
                    'payment_url': payment_result['start_pay_url'],
                    'message': 'لطفاً برای شارژ حساب و خرید پیشنهاد، به صفحه پرداخت بروید',
                    'transaction_id': transaction.id
                })
            else:
                return Response(
                    {'error': payment_result.get('error', 'خطا در ایجاد درخواست پرداخت')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        # User has enough balance - deduct and purchase
        if wallet.deduct(recommendation.price):
            # Create payment transaction
            transaction = Transaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=recommendation.price,
                status='completed',
                description=f'خرید پیشنهاد: {recommendation.title}',
                ai_recommendation=recommendation,
                completed_at=timezone.now()
            )
            
            # Update recommendation
            recommendation.status = 'purchased'
            recommendation.purchased_by = user
            recommendation.purchased_at = timezone.now()
            recommendation.save()
            
            return Response({
                'status': 'success',
                'message': 'پیشنهاد با موفقیت خریداری شد',
                'remaining_balance': float(wallet.balance),
                'transaction_id': transaction.id
            })
        else:
            return Response(
                {'error': 'موجودی کافی نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentViewSet(viewsets.ViewSet):
    """ViewSet for payment callbacks"""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'], url_path='callback')
    def payment_callback(self, request):
        """Handle Zarinpal payment callback"""
        from django.utils import timezone
        from api.payment_service import get_zarinpal_service
        from django.shortcuts import redirect
        from django.conf import settings
        
        authority = request.query_params.get('Authority')
        status = request.query_params.get('Status')
        transaction_id = request.query_params.get('transaction_id')
        
        # Get frontend URL from settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        
        if not authority or not transaction_id:
            return redirect(f'{frontend_url}/?payment_error=missing_params')
        
        try:
            transaction = Transaction.objects.get(id=transaction_id, zarinpal_authority=authority)
        except Transaction.DoesNotExist:
            return redirect(f'{frontend_url}/?payment_error=transaction_not_found')
        
        if transaction.status != 'pending':
            return redirect(f'{frontend_url}/?payment_error=already_processed')
        
        # Verify payment
        if status == 'OK':
            payment_service = get_zarinpal_service()
            verify_result = payment_service.verify_payment(
                authority=authority,
                amount=int(transaction.amount)
            )
            
            if verify_result['status'] == 'success':
                # Payment successful - charge wallet
                transaction.wallet.charge(transaction.amount)
                transaction.status = 'completed'
                transaction.zarinpal_ref_id = verify_result['ref_id']
                transaction.completed_at = timezone.now()
                transaction.save()
                
                # If this was for a recommendation purchase, complete the purchase
                if transaction.ai_recommendation:
                    recommendation = transaction.ai_recommendation
                    # Deduct again for the purchase
                    if transaction.wallet.deduct(recommendation.price):
                        purchase_transaction = Transaction.objects.create(
                            wallet=transaction.wallet,
                            transaction_type='payment',
                            amount=recommendation.price,
                            status='completed',
                            description=f'خرید پیشنهاد: {recommendation.title}',
                            ai_recommendation=recommendation,
                            completed_at=timezone.now()
                        )
                        
                        recommendation.status = 'purchased'
                        recommendation.purchased_by = transaction.wallet.user
                        recommendation.purchased_at = timezone.now()
                        recommendation.save()
                
                return redirect(f'{frontend_url}/?payment_success=1&transaction_id={transaction.id}')
            else:
                transaction.status = 'failed'
                transaction.save()
                return redirect(f'{frontend_url}/?payment_error=verify_failed&error={verify_result.get("error", "")}')
        else:
            transaction.status = 'cancelled'
            transaction.save()
            return redirect(f'{frontend_url}/?payment_error=cancelled')
    
    @action(detail=False, methods=['get'], url_path='check')
    def check_payment(self, request):
        """Check payment status"""
        transaction_id = request.query_params.get('transaction_id')
        if not transaction_id:
            return Response({'error': 'transaction_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            return Response({
                'status': transaction.status,
                'amount': float(transaction.amount),
                'description': transaction.description
            })
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)


class StrategyOptimizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy optimizations"""
    queryset = StrategyOptimization.objects.all()
    serializer_class = StrategyOptimizationSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['strategy', 'status', 'method']
    
    def get_queryset(self):
        user = self.request.user
        queryset = StrategyOptimization.objects.all()
        if not (user.is_staff or user.is_superuser):
            queryset = queryset.filter(strategy__user=user)
        strategy_id = self.request.query_params.get('strategy', None)
        if strategy_id:
            queryset = queryset.filter(strategy_id=strategy_id)
        return queryset.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        """Create and start optimization job"""
        from django.utils import timezone
        from api.tasks import run_optimization_task
        from ai_module.backtest_engine import BacktestEngine
        from api.data_providers import DataProviderManager
        
        serializer = StrategyOptimizationCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        strategy_id = data['strategy']
        
        try:
            strategy = get_user_strategy_or_404(request.user, id=strategy_id)
        except Http404:
            return Response(
                {'error': 'استراتژی یافت نشد'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not strategy.parsed_strategy_data:
            return Response(
                {'error': 'استراتژی باید ابتدا پردازش شود'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create optimization record
        optimization = StrategyOptimization.objects.create(
            strategy=strategy,
            method=data.get('method', 'auto'),
            optimizer_type=data.get('optimizer_type', 'ml'),
            objective=data.get('objective', 'sharpe_ratio'),
            status='pending',
            original_params=strategy.parsed_strategy_data.get('risk_management', {}),
            optimization_settings={
                'n_trials': data.get('n_trials', 50),
                'n_episodes': data.get('n_episodes', 50),
                'ml_method': data.get('ml_method', 'bayesian'),
                'dl_method': data.get('dl_method', 'reinforcement_learning'),
                'timeframe_days': data.get('timeframe_days', 365),
                'symbol': data.get('symbol'),
            }
        )
        
        # Calculate original score
        try:
            # Get historical data
            # Default to XAU/USD (Gold) as it's the primary symbol for this trading system
            symbol = data.get('symbol') or strategy.parsed_strategy_data.get('symbol') or 'XAU/USD'
            timeframe_days = data.get('timeframe_days', 365)
            
            data_provider = DataProviderManager(user=request.user)
            historical_data = data_provider.get_historical_data(
                symbol=symbol,
                timeframe_days=timeframe_days
            )
            
            if historical_data is not None and not historical_data.empty:
                # Run backtest with original strategy
                engine = BacktestEngine()
                original_results = engine.run_backtest(
                    historical_data,
                    strategy.parsed_strategy_data,
                    symbol=symbol
                )
                
                # Calculate original score based on objective
                objective = data.get('objective', 'sharpe_ratio')
                if objective == 'sharpe_ratio':
                    original_score = original_results.get('sharpe_ratio', 0.0)
                elif objective == 'total_return':
                    original_score = original_results.get('total_return', 0.0)
                elif objective == 'win_rate':
                    original_score = original_results.get('win_rate', 0.0)
                elif objective == 'profit_factor':
                    original_score = original_results.get('profit_factor', 0.0)
                else:
                    original_score = original_results.get('total_return', 0.0)
                
                optimization.original_score = original_score
                optimization.save(update_fields=['original_score'])
        except Exception as e:
            logger.warning(f"Could not calculate original score: {str(e)}")
        
        # Start optimization task asynchronously
        try:
            run_optimization_task.delay(optimization.id)
            optimization.status = 'running'
            optimization.started_at = timezone.now()
            optimization.save(update_fields=['status', 'started_at'])
        except Exception as e:
            logger.error(f"Failed to start optimization task: {str(e)}")
            optimization.status = 'failed'
            optimization.error_message = str(e)
            optimization.save(update_fields=['status', 'error_message'])
            return Response(
                {'error': f'خطا در شروع بهینه‌سازی: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        serializer = StrategyOptimizationSerializer(optimization)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get optimization status"""
        optimization = self.get_object()
        return Response({
            'id': optimization.id,
            'status': optimization.status,
            'best_score': optimization.best_score,
            'improvement_percent': optimization.improvement_percent,
            'progress': self._calculate_progress(optimization)
        })
    
    def _calculate_progress(self, optimization):
        """Calculate optimization progress percentage"""
        if optimization.status == 'completed':
            return 100
        elif optimization.status == 'failed' or optimization.status == 'cancelled':
            return 0
        elif optimization.status == 'running':
            # Estimate based on history length
            settings = optimization.optimization_settings or {}
            n_trials = settings.get('n_trials', 50) or settings.get('n_episodes', 50)
            history_len = len(optimization.optimization_history or [])
            if n_trials > 0:
                return min(100, int((history_len / n_trials) * 100))
        return 0
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a running optimization"""
        from django.utils import timezone
        
        optimization = self.get_object()
        
        if optimization.status not in ['pending', 'running']:
            return Response(
                {'error': 'فقط بهینه‌سازی‌های در انتظار یا در حال اجرا قابل لغو هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Mark as cancelled
        optimization.status = 'cancelled'
        optimization.completed_at = timezone.now()
        optimization.error_message = 'بهینه‌سازی توسط کاربر لغو شد'
        optimization.save(update_fields=['status', 'completed_at', 'error_message'])
        
        # Stop polling for this optimization
        # Note: The actual Celery task will check status and stop itself
        
        serializer = StrategyOptimizationSerializer(optimization)
        return Response({
            'status': 'cancelled',
            'message': 'بهینه‌سازی با موفقیت لغو شد',
            'optimization': serializer.data
        })
    
    def update(self, request, *args, **kwargs):
        """Update optimization settings (only if pending, failed, or cancelled)"""
        optimization = self.get_object()
        
        if optimization.status not in ['pending', 'failed', 'cancelled']:
            return Response(
                {'error': 'فقط بهینه‌سازی‌های در انتظار، خطا یا لغو شده قابل ویرایش هستند'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Only allow updating settings for pending optimizations
        if optimization.status == 'pending':
            # Get serializer for validation
            serializer = StrategyOptimizationCreateSerializer(data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            # Update optimization settings
            settings = optimization.optimization_settings or {}
            validated_data = serializer.validated_data
            
            if 'n_trials' in validated_data:
                settings['n_trials'] = validated_data['n_trials']
            if 'n_episodes' in validated_data:
                settings['n_episodes'] = validated_data['n_episodes']
            if 'ml_method' in validated_data:
                settings['ml_method'] = validated_data['ml_method']
            if 'dl_method' in validated_data:
                settings['dl_method'] = validated_data['dl_method']
            if 'timeframe_days' in validated_data:
                settings['timeframe_days'] = validated_data['timeframe_days']
            if 'symbol' in validated_data:
                settings['symbol'] = validated_data['symbol']
            
            # Update direct fields
            if 'objective' in validated_data:
                optimization.objective = validated_data['objective']
            if 'method' in validated_data:
                optimization.method = validated_data['method']
            if 'optimizer_type' in validated_data:
                optimization.optimizer_type = validated_data['optimizer_type']
            
            optimization.optimization_settings = settings
            optimization.save()
            
            serializer = StrategyOptimizationSerializer(optimization)
            return Response(serializer.data)
        
        return Response(
            {'error': 'این بهینه‌سازی قابل ویرایش نیست'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete optimization (only if not running)"""
        optimization = self.get_object()
        
        if optimization.status == 'running':
            return Response(
                {'error': 'بهینه‌سازی در حال اجرا است. لطفاً ابتدا آن را متوقف کنید.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class APIUsageStatsView(APIView):
    """View برای نمایش آمار استفاده از API و هزینه"""
    permission_classes = [IsAdminOrStaff]
    
    def get(self, request):
        """دریافت آمار استفاده از API (برای ادمین - همه کاربران)"""
        # دریافت پارامترهای فیلتر
        provider = request.query_params.get('provider', None)
        days = request.query_params.get('days', None)
        user_id = request.query_params.get('user_id', None)  # برای فیلتر بر اساس کاربر خاص
        
        # محاسبه تاریخ شروع و پایان
        start_date = None
        end_date = None
        
        if days:
            try:
                days = int(days)
                start_date = timezone.now() - timedelta(days=days)
                end_date = timezone.now()
            except ValueError:
                pass
        
        # اگر user_id مشخص شده باشد، فیلتر بر اساس آن
        user_filter = None
        if user_id:
            try:
                from django.contrib.auth.models import User
                user_filter = User.objects.get(id=int(user_id))
            except (User.DoesNotExist, ValueError):
                pass
        
        # دریافت آمار
        stats = get_api_usage_stats(
            provider=provider,
            start_date=start_date,
            end_date=end_date,
            user=user_filter
        )
        
        return Response(stats)


class UserAPIUsageStatsView(APIView):
    """View برای نمایش آمار استفاده از API برای کاربران معمولی (فقط آمار خودشان)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """دریافت آمار استفاده از API کاربر فعلی"""
        # دریافت پارامترهای فیلتر
        provider = request.query_params.get('provider', None)
        days = request.query_params.get('days', 30)  # پیش‌فرض 30 روز
        
        # محاسبه تاریخ شروع و پایان
        start_date = None
        end_date = None
        
        if days:
            try:
                days = int(days)
                start_date = timezone.now() - timedelta(days=days)
                end_date = timezone.now()
            except ValueError:
                pass
        
        # دریافت آمار فقط برای کاربر فعلی
        stats = get_api_usage_stats(
            provider=provider,
            start_date=start_date,
            end_date=end_date,
            user=request.user
        )
        
        return Response(stats)


class UserScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user scores"""
    serializer_class = UserScoreSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return UserScore.objects.all()
        return UserScore.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's score"""
        score = get_or_create_user_score(request.user)
        serializer = self.get_serializer(score)
        rank = get_user_rank(request.user)
        data = serializer.data
        data['rank'] = rank
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard"""
        limit = int(request.query_params.get('limit', 10))
        leaderboard = get_leaderboard(limit)
        return Response(leaderboard)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for achievements"""
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Achievement.objects.filter(is_active=True)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class UserAchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user achievements"""
    serializer_class = UserAchievementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return UserAchievement.objects.all()
        return UserAchievement.objects.filter(user=user)
    
    @action(detail=False, methods=['get'])
    def my_achievements(self, request):
        """Get current user's achievements"""
        achievements = UserAchievement.objects.filter(user=request.user).select_related('achievement')
        serializer = self.get_serializer(achievements, many=True)
        return Response(serializer.data)


class GapGPTViewSet(viewsets.ViewSet):
    """
    ViewSet for GapGPT API operations
    مستندات: https://gapgpt.app/platform/quickstart
    
    این ViewSet برای تبدیل متن استراتژی‌های معاملاتی به مدل‌های AI مختلف استفاده می‌شود.
    """
    
    @action(detail=False, methods=['get'], url_path='models', permission_classes=[AllowAny])
    def list_models(self, request):
        """
        لیست مدل‌های موجود در GapGPT
        
        Returns:
            لیست مدل‌های قابل استفاده
        """
        try:
            from ai_module.gapgpt_client import get_available_models
            
            user = request.user if request.user.is_authenticated else None
            models = get_available_models(user=user, filter_chat_models=True)
            
            return Response({
                'status': 'success',
                'models': models,
                'count': len(models)
            })
        except Exception as e:
            logger.error(f"Error listing GapGPT models: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'خطا در دریافت لیست مدل‌ها: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='convert', permission_classes=[AllowAny])
    def convert_strategy(self, request):
        """
        تبدیل استراتژی با استفاده از GapGPT
        
        Body:
        - strategy_text: متن استراتژی (required)
        - model_id: ID مدل (optional, default: gpt-4o)
        - temperature: دما (optional, default: 0.3)
        - max_tokens: حداکثر توکن (optional, default: 4000)
        
        Returns:
            استراتژی تبدیل شده
        """
        try:
            from ai_module.gapgpt_client import convert_strategy_with_gapgpt
            
            strategy_text = request.data.get('strategy_text')
            model_id = request.data.get('model_id', None)
            temperature = float(request.data.get('temperature', 0.3))
            max_tokens = int(request.data.get('max_tokens', 4000))
            
            if not strategy_text:
                return Response({
                    'status': 'error',
                    'message': 'متن استراتژی (strategy_text) الزامی است'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user if request.user.is_authenticated else None
            
            # افزایش timeout برای تبدیل استراتژی (ممکن است طول بکشد)
            result = convert_strategy_with_gapgpt(
                strategy_text=strategy_text,
                model_id=model_id,
                user=user,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=120  # 120 ثانیه timeout برای تبدیل استراتژی
            )
            
            if result['success']:
                return Response({
                    'status': 'success',
                    'data': result
                })
            else:
                return Response({
                    'status': 'error',
                    'message': result.get('error', 'خطای نامشخص'),
                    'data': result
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': f'پارامتر نامعتبر: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error converting strategy with GapGPT: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'خطا در تبدیل استراتژی: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='compare-models', permission_classes=[AllowAny])
    def compare_models(self, request):
        """
        تبدیل استراتژی با چندین مدل و مقایسه نتایج برای پیدا کردن بهترین
        
        Body:
        - strategy_text: متن استراتژی (required)
        - models: لیست ID مدل‌ها (optional, اگر نباشد از مدل‌های پیش‌فرض استفاده می‌شود)
        
        Returns:
            نتایج تمام مدل‌ها و بهترین نتیجه
        """
        try:
            from ai_module.gapgpt_client import analyze_strategy_with_multiple_models
            
            strategy_text = request.data.get('strategy_text')
            models = request.data.get('models', None)
            temperature = float(request.data.get('temperature', 0.3))
            max_tokens = int(request.data.get('max_tokens', 4000))
            
            if not strategy_text:
                return Response({
                    'status': 'error',
                    'message': 'متن استراتژی (strategy_text) الزامی است'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = request.user if request.user.is_authenticated else None
            
            # افزایش timeout برای مقایسه مدل‌ها (ممکن است بیشتر طول بکشد)
            result = analyze_strategy_with_multiple_models(
                strategy_text=strategy_text,
                models=models,
                user=user,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=180  # 180 ثانیه (3 دقیقه) برای مقایسه چند مدل
            )
            
            return Response({
                'status': 'success',
                'data': result
            })
                
        except ValueError as e:
            return Response({
                'status': 'error',
                'message': f'پارامتر نامعتبر: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error comparing models with GapGPT: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'خطا در مقایسه مدل‌ها: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

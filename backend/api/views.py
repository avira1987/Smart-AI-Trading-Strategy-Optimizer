from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .permissions import IsAdminOrStaff
from core.models import APIConfiguration, TradingStrategy, Job, Result, LiveTrade, AutoTradingSettings, Ticket, TicketMessage, StrategyOptimization
from core.models import Wallet, Transaction, AIRecommendation, DDNSConfiguration
from .serializers import (
    APIConfigurationSerializer, TradingStrategySerializer, 
    JobSerializer, JobCreateSerializer, ResultSerializer, LiveTradeSerializer,
    AutoTradingSettingsSerializer, TicketSerializer, TicketCreateSerializer, TicketMessageSerializer,
    StrategyOptimizationSerializer, StrategyOptimizationCreateSerializer,
    WalletSerializer, TransactionSerializer, AIRecommendationSerializer, DDNSConfigurationSerializer
)
from .data_providers import DataProviderManager
from .tasks import run_backtest_task, run_demo_trade_task, run_auto_trading
from .mt5_client import (
    fetch_mt5_m1_candles, fetch_mt5_candles, is_mt5_available,
    get_mt5_account_info, get_mt5_positions, open_mt5_trade, 
    close_mt5_trade, is_market_open
)
import logging
from .utils import get_user_friendly_api_error_message  # توابع کمکی مدیریت پیام خطا

logger = logging.getLogger(__name__)


class APIConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing API configurations"""
    queryset = APIConfiguration.objects.all()
    serializer_class = APIConfigurationSerializer
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test API connection"""
        api_config = self.get_object()
        
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
                
                from django.conf import settings
                
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
        
        # Original code for data providers
        try:
            data_manager = DataProviderManager()
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
            data_manager = DataProviderManager()
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
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later

    def get(self, request, *args, **kwargs):
        source = request.query_params.get('source')
        if source == 'mt5_candles':
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

        return Response({'status': 'error', 'message': 'Unknown market data source'}, status=status.HTTP_400_BAD_REQUEST)


class BacktestPrecheckView(APIView):
    """Validate data availability for a strategy before running backtest."""
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later

    def post(self, request, *args, **kwargs):
        try:
            strategy_id = request.data.get('strategy')
            if not strategy_id:
                return Response({'status': 'error', 'message': 'strategy is required'}, status=status.HTTP_400_BAD_REQUEST)

            strategy = get_object_or_404(TradingStrategy, id=strategy_id)

            # Parse strategy file to extract requirements (symbol at minimum)
            from ai_module.nlp_parser import parse_strategy_file
            parsed = parse_strategy_file(strategy.strategy_file.path) if strategy.strategy_file else {}
            symbol = parsed.get('symbol', 'EUR/USD')

            data_manager = DataProviderManager()
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

            # Probe MT5 availability regardless, as a fallback option
            mt5_ok, mt5_msg = is_mt5_available()
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
    queryset = TradingStrategy.objects.all()
    serializer_class = TradingStrategySerializer
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    pagination_class = None  # Disable pagination for strategies - return all results
    
    def create(self, request):
        """Upload new strategy"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
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
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process strategy file to extract and parse strategy data"""
        from django.utils import timezone
        from ai_module.nlp_parser import parse_strategy_file, extract_text_from_file
        from ai_module.gemini_client import analyze_strategy_with_gemini
        
        strategy = self.get_object()
        
        if not strategy.strategy_file:
            return Response({
                'status': 'error',
                'message': 'No strategy file found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Set processing status
            strategy.processing_status = 'processing'
            strategy.processing_error = ''
            strategy.save()
            
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
            
            try:
                parsed_data = parse_strategy_file(strategy_file_path)
            except Exception as parse_error:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Error in parse_strategy_file for {strategy_file_path}: {str(parse_error)}\n{error_trace}")
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
                strategy.processing_status = 'failed'
                strategy.processing_error = parsed_data['error']
                strategy.save()
                return Response({
                    'status': 'failed',
                    'message': f'Error parsing strategy: {parsed_data["error"]}',
                    'parsed_data': parsed_data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate strategy analysis - try Gemini first, fallback to basic analysis
            analysis = None
            try:
                from ai_module.gemini_client import generate_basic_analysis, analyze_strategy_with_gemini
                from ai_module.nlp_parser import extract_text_from_file
                
                logger.info(f"Starting analysis generation for strategy {strategy.id}")
                raw_text = extract_text_from_file(strategy_file_path)
                logger.info(f"Extracted {len(raw_text)} characters for analysis")
                
                # Try Gemini AI analysis first
                try:
                    analysis = analyze_strategy_with_gemini(parsed_data, raw_text)
                    if analysis:
                        logger.info(f"Generated AI strategy analysis for strategy {strategy.id}")
                    else:
                        logger.info(f"Gemini analysis returned None, using basic analysis")
                except Exception as gemini_error:
                    logger.warning(f"Gemini analysis failed: {str(gemini_error)}, using basic analysis")
                    analysis = None
                
                # If Gemini is not available or failed, use basic analysis
                if not analysis:
                    analysis = generate_basic_analysis(parsed_data)
                    logger.info(f"Generated basic strategy analysis for strategy {strategy.id}")
                
                # Always add analysis (either AI or basic)
                if analysis:
                    parsed_data['analysis'] = analysis
                    logger.info(f"Analysis added to parsed_data for strategy {strategy.id}")
                else:
                    logger.warning(f"No analysis generated for strategy {strategy.id}")
                    
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Error generating strategy analysis: {str(e)}\n{error_trace}")
                # Try basic analysis as fallback
                try:
                    from ai_module.gemini_client import generate_basic_analysis
                    analysis = generate_basic_analysis(parsed_data)
                    parsed_data['analysis'] = analysis
                    logger.info(f"Used basic analysis fallback after error for strategy {strategy.id}")
                except Exception as e2:
                    import traceback
                    error_trace2 = traceback.format_exc()
                    logger.error(f"Even basic analysis failed: {str(e2)}\n{error_trace2}")
                    # Don't fail the whole process if analysis fails completely
                    # Just continue without analysis
            
            # Save parsed data (with or without analysis)
            strategy.parsed_strategy_data = parsed_data
            strategy.processing_status = 'processed'
            strategy.processed_at = timezone.now()
            strategy.processing_error = ''
            strategy.save()
            
            logger.info(f"Strategy {strategy.id} processed successfully with confidence {parsed_data.get('confidence_score', 0):.2f}")
            
            return Response({
                'status': 'success',
                'message': 'Strategy processed successfully',
                'parsed_data': parsed_data,
                'confidence_score': parsed_data.get('confidence_score', 0.0),
                'analysis_generated': analysis is not None
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            logger.error(f"Error processing strategy {strategy.id}: {str(e)}\n{error_trace}")
            strategy.processing_status = 'failed'
            strategy.processing_error = f"{str(e)}\n{error_trace[:500]}"  # Limit error length
            strategy.save()
            return Response({
                'status': 'error',
                'message': f'Error processing strategy: {str(e)}',
                'error': str(e),
                'error_type': type(e).__name__
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def generate_questions(self, request, pk=None):
        """تولید سوالات هوشمند برای تکمیل استراتژی"""
        from ai_module.nlp_parser import extract_text_from_file
        from ai_module.gemini_client import generate_strategy_questions, _client_ready, _get_gemini_api_key
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
        
        # Check if Gemini API is configured
        api_key = _get_gemini_api_key()
        if not api_key:
            # Check if there's an inactive API key in database
            from core.models import APIConfiguration
            inactive_key = APIConfiguration.objects.filter(provider='gemini', is_active=False).first()
            if inactive_key:
                logger.warning(f"Found inactive Gemini API key for strategy {strategy.id}")
                return Response({
                    'status': 'error',
                    'message': 'کلید Gemini API یافت شد اما غیرفعال است. لطفاً در بخش تنظیمات API، کلید Gemini را فعال کنید.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error(f"Gemini API key not found for strategy {strategy.id}")
                return Response({
                    'status': 'error',
                    'message': 'Gemini API Key یافت نشد. لطفاً در بخش "تنظیمات API" یک کلید Gemini اضافه و فعال کنید.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if genai library is available
        try:
            import google.generativeai as genai
            if genai is None:
                return Response({
                    'status': 'error',
                    'message': 'کتابخانه google-generativeai نصب نشده است. لطفاً آن را نصب کنید: pip install google-generativeai'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ImportError as import_err:
            logger.error(f"google-generativeai import failed: {import_err}")
            return Response({
                'status': 'error',
                'message': f'کتابخانه google-generativeai نصب نشده است: {str(import_err)}. لطفاً آن را نصب کنید: pip install google-generativeai'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Detailed check for client readiness
        from django.conf import settings as django_settings
        gemini_enabled = getattr(django_settings, 'GEMINI_ENABLED', True)
        
        if not gemini_enabled:
            logger.error(f"Gemini is disabled in settings for strategy {strategy.id}")
            return Response({
                'status': 'error',
                'message': 'Gemini API در تنظیمات غیرفعال است. لطفاً GEMINI_ENABLED را در تنظیمات فعال کنید.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Check if genai library is installed
        try:
            import google.generativeai as genai_check
            if genai_check is None:
                return Response({
                    'status': 'error',
                    'message': 'کتابخانه google-generativeai نصب نشده است. لطفاً آن را نصب کنید: pip install google-generativeai'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ImportError as import_err:
            logger.error(f"google-generativeai import failed: {import_err}")
            return Response({
                'status': 'error',
                'message': f'کتابخانه google-generativeai نصب نشده است: {str(import_err)}. لطفاً آن را نصب کنید: pip install google-generativeai'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not _client_ready():
            # Final check - this should not happen if above checks pass
            logger.error(f"Gemini client not ready for strategy {strategy.id}, API key exists: {bool(api_key)}, gemini_enabled: {gemini_enabled}")
            return Response({
                'status': 'error',
                'message': 'Gemini API آماده نیست. لطفاً مطمئن شوید که:\n1. API Key معتبر است\n2. کتابخانه google-generativeai نصب شده است\n3. اینترنت متصل است'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        try:
            # Log API key status for debugging (without showing the actual key)
            logger.info(f"API key exists: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
            if api_key:
                logger.info(f"API key starts with: {api_key[:10]}...")
            
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
            questions = generate_strategy_questions(parsed_data, raw_text, existing_answers)
            
            if not questions:
                logger.warning(f"generate_strategy_questions returned None for strategy {strategy.id}")
                return Response({
                    'status': 'error',
                    'message': 'امکان تولید سوالات وجود ندارد. لطفاً مطمئن شوید که:\n1. Gemini API Key معتبر است\n2. اینترنت متصل است\n3. استراتژی دارای محتوای کافی است'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
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
            enhanced_strategy = parse_strategy_with_answers(parsed_data, raw_text, answers)
            
            # Update strategy
            strategy.parsed_strategy_data = enhanced_strategy
            strategy.processing_status = 'processed'
            strategy.processed_at = timezone.now()
            strategy.processing_error = ''
            strategy.save()
            
            logger.info(f"Strategy {strategy.id} processed with answers successfully")
            
            return Response({
                'status': 'success',
                'message': 'Strategy processed successfully with answers',
                'parsed_data': enhanced_strategy,
                'confidence_score': enhanced_strategy.get('confidence_score', 0.0)
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


class StrategyQuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy questions"""
    serializer_class = None  # Will be set in __init__
    permission_classes = [AllowAny]
    filterset_fields = ['strategy', 'status']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from api.serializers import StrategyQuestionSerializer
        self.serializer_class = StrategyQuestionSerializer
    
    def get_queryset(self):
        from core.models import StrategyQuestion
        queryset = StrategyQuestion.objects.all()
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
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later
    
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
        
        strategy = get_object_or_404(TradingStrategy, id=strategy_id)
        
        # Create job
        job = Job.objects.create(
            strategy=strategy,
            job_type=job_type,
            status='pending'
        )
        
        # Run async task (placeholder - requires Redis/Celery)
        # if job_type == 'backtest':
        #     run_backtest_task.delay(job.id)
        # else:
        #     run_demo_trade_task.delay(job.id)
        
        # For now, run sync as fallback
        # Note: We call the task synchronously, but we need to refresh the job after execution
        # to get the updated status and result
        try:
            if job_type == 'backtest':
                logger.info(f"Starting synchronous backtest for job {job.id}, strategy {strategy_id}, timeframe {timeframe_days} days")
                run_backtest_task(job.id, timeframe_days=timeframe_days, symbol_override=symbol_override, initial_capital=initial_capital, selected_indicators=selected_indicators)
            else:
                run_demo_trade_task(job.id)
            
            # Refresh job from database to get updated status and result
            job.refresh_from_db()
            logger.info(f"Backtest task completed for job {job.id}, status: {job.status}, result_id: {job.result_id}")
        except Exception as e:
            logger.error(f"Error executing backtest task for job {job.id}: {e}", exc_info=True)
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
    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later

    def get_queryset(self):
        qs = super().get_queryset()
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
    queryset = LiveTrade.objects.all()
    serializer_class = LiveTradeSerializer
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later
    filterset_fields = ['symbol', 'status', 'strategy']
    pagination_class = None  # Disable pagination for trades - return all results
    
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
            strategy = TradingStrategy.objects.get(id=strategy_id)
        except TradingStrategy.DoesNotExist:
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
        closed_trades = LiveTrade.objects.filter(
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
    permission_classes = [AllowAny]  # Keep AllowAny for now, can change to IsAuthenticated later
    pagination_class = None  # Disable pagination for settings - return all results
    
    def get_queryset(self):
        qs = super().get_queryset()
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
            strategy = TradingStrategy.objects.get(id=strategy_id)
        except TradingStrategy.DoesNotExist:
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
            strategy = TradingStrategy.objects.get(id=strategy_id)
        except TradingStrategy.DoesNotExist:
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
            
            # Return full ticket data
            response_serializer = TicketSerializer(ticket)
            logger.info(f"Ticket created: {ticket.id} by user {request.user.username}")
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Error creating ticket: {e}")
            return Response(
                {
                    'error': 'خطا در ایجاد تیکت',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            return Response(serializer, status=status.HTTP_201_CREATED)
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
            return Response(serializer)
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
        
        strategy = get_object_or_404(TradingStrategy, id=pk)
        
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
            recommendations_data = generate_ai_recommendations(
                strategy.parsed_strategy_data,
                raw_text,
                analysis
            )
            
            if not recommendations_data:
                return Response(
                    {'error': 'خطا در تولید پیشنهادات. لطفاً Gemini API را بررسی کنید.'},
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
    serializer_class = StrategyOptimizationSerializer
    permission_classes = [AllowAny]
    filterset_fields = ['strategy', 'status', 'method']
    
    def get_queryset(self):
        from core.models import StrategyOptimization
        queryset = StrategyOptimization.objects.all()
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
            strategy = TradingStrategy.objects.get(id=strategy_id)
        except TradingStrategy.DoesNotExist:
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
            symbol = data.get('symbol') or strategy.parsed_strategy_data.get('symbol', 'EURUSD')
            timeframe_days = data.get('timeframe_days', 365)
            
            data_provider = DataProviderManager()
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


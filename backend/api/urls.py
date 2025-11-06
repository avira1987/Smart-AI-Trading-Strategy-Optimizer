from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    APIConfigurationViewSet, TradingStrategyViewSet, JobViewSet, 
    ResultViewSet, MarketDataView, BacktestPrecheckView, LiveTradeViewSet,
    AutoTradingSettingsViewSet, StrategyQuestionViewSet, TicketViewSet,
    WalletViewSet, AIRecommendationViewSet, PaymentViewSet, StrategyOptimizationViewSet
)
from .ddns_views import DDNSConfigurationViewSet
from .auth_views import SendOTPView, VerifyOTPView, GoogleOAuthView, check_auth, logout, get_csrf_token, check_profile_completion, update_profile, check_ip_location, check_google_auth_status
from .test_endpoints import test_sms, test_google_oauth_config, test_backend_status
from .gold_price_views import GoldPriceView
from .demo_trading_views import (
    DemoAccountView, DemoTradeView, DemoCloseTradeView, DemoUpdatePricesView
)

router = DefaultRouter()
router.register(r'apis', APIConfigurationViewSet, basename='api')
router.register(r'strategies', TradingStrategyViewSet, basename='strategy')
router.register(r'strategy-questions', StrategyQuestionViewSet, basename='strategy-question')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'results', ResultViewSet, basename='result')
router.register(r'trades', LiveTradeViewSet, basename='trade')
router.register(r'auto-trading-settings', AutoTradingSettingsViewSet, basename='auto-trading')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'ai-recommendations', AIRecommendationViewSet, basename='ai-recommendation')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'strategy-optimizations', StrategyOptimizationViewSet, basename='strategy-optimization')
router.register(r'ddns-configurations', DDNSConfigurationViewSet, basename='ddns-configuration')

urlpatterns = [
    path('', include(router.urls)),
    path('market/mt5_candles/', MarketDataView.as_view()),
    path('precheck/backtest/', BacktestPrecheckView.as_view()),
    # Authentication endpoints
    path('auth/send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('auth/google/', GoogleOAuthView.as_view(), name='google_oauth'),
    path('auth/check/', check_auth, name='check_auth'),
    path('auth/logout/', logout, name='logout'),
    path('auth/csrf-token/', get_csrf_token, name='get_csrf_token'),
    path('auth/profile/check/', check_profile_completion, name='check_profile_completion'),
    path('auth/profile/update/', update_profile, name='update_profile'),
    path('auth/check-ip/', check_ip_location, name='check_ip_location'),
    path('auth/google-status/', check_google_auth_status, name='check_google_auth_status'),
    # Test endpoints
    path('test/sms/', test_sms, name='test_sms'),
    path('test/google-oauth/', test_google_oauth_config, name='test_google_oauth'),
    path('test/backend-status/', test_backend_status, name='test_backend_status'),
    # Gold price endpoints
    path('gold-price/', GoldPriceView.as_view(), name='gold_price'),
    # Demo trading endpoints
    path('demo/account/', DemoAccountView.as_view(), name='demo_account'),
    path('demo/trades/', DemoTradeView.as_view(), name='demo_trades'),
    path('demo/trades/<int:trade_id>/close/', DemoCloseTradeView.as_view(), name='demo_close_trade'),
    path('demo/update-prices/', DemoUpdatePricesView.as_view(), name='demo_update_prices'),
]


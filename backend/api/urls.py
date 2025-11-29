from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    APIConfigurationViewSet,
    TradingStrategyViewSet,
    StrategyMarketplaceViewSet,
    JobViewSet,
    ResultViewSet,
    MarketDataView,
    BacktestPrecheckView,
    LiveTradeViewSet,
    AutoTradingSettingsViewSet,
    StrategyQuestionViewSet,
    TicketViewSet,
    WalletViewSet,
    AIRecommendationViewSet,
    PaymentViewSet,
    StrategyOptimizationViewSet,
    APIUsageStatsView,
    UserAPIUsageStatsView,
    SystemSettingsView,
    ClearAICacheView,
    UserScoreViewSet,
    AchievementViewSet,
    UserAchievementViewSet,
    GapGPTViewSet,
    AdminUserManagementView,
)
from .auth_views import SendOTPView, VerifyOTPView, check_auth, logout, get_csrf_token, check_profile_completion, update_profile, check_ip_location, get_user_activity_logs
from .captcha_views import GetCaptchaView
from .test_endpoints import test_sms, test_backend_status, test_kavenegar_config, emergency_set_kavenegar_api_key
from .gold_price_views import GoldPriceView
from .gold_access_views import GoldAPIAccessRequestViewSet, UserGoldAPIAccessView
from .demo_trading_views import (
    DemoAccountView, DemoTradeView, DemoCloseTradeView, DemoUpdatePricesView
)
from .security_views import SecurityManagementView, SecurityLogsView

router = DefaultRouter()
router.register(r'apis', APIConfigurationViewSet, basename='api')
router.register(r'strategies', TradingStrategyViewSet, basename='strategy')
router.register(r'marketplace/listings', StrategyMarketplaceViewSet, basename='strategy-marketplace')
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
router.register(r'gold-access/requests', GoldAPIAccessRequestViewSet, basename='gold-access-request')
router.register(r'gamification/scores', UserScoreViewSet, basename='user-score')
router.register(r'gamification/achievements', AchievementViewSet, basename='achievement')
router.register(r'gamification/user-achievements', UserAchievementViewSet, basename='user-achievement')
router.register(r'gapgpt', GapGPTViewSet, basename='gapgpt')

urlpatterns = [
    path('', include(router.urls)),
    path('market/mt5_candles/', MarketDataView.as_view()),
    path('precheck/backtest/', BacktestPrecheckView.as_view()),
    # CAPTCHA endpoint
    path('captcha/get/', GetCaptchaView.as_view(), name='get_captcha'),
    # Authentication endpoints
    path('auth/send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('auth/check/', check_auth, name='check_auth'),
    path('auth/logout/', logout, name='logout'),
    path('auth/csrf-token/', get_csrf_token, name='get_csrf_token'),
    path('auth/profile/check/', check_profile_completion, name='check_profile_completion'),
    path('auth/profile/update/', update_profile, name='update_profile'),
    path('auth/activity-logs/', get_user_activity_logs, name='get_user_activity_logs'),
    path('auth/check-ip/', check_ip_location, name='check_ip_location'),
    # System settings
    path('system-settings/', SystemSettingsView.as_view(), name='system_settings'),
    path('admin/clear-ai-cache/', ClearAICacheView.as_view(), name='clear_ai_cache'),
    # Test endpoints
    path('test/sms/', test_sms, name='test_sms'),
    path('test/backend-status/', test_backend_status, name='test_backend_status'),
    path('test/kavenegar-config/', test_kavenegar_config, name='test_kavenegar_config'),
    path('emergency/set-kavenegar-api-key/', emergency_set_kavenegar_api_key, name='emergency_set_kavenegar_api_key'),
    # Gold price endpoints
    path('gold-price/', GoldPriceView.as_view(), name='gold_price'),
    path('gold-access/self/', UserGoldAPIAccessView.as_view(), name='gold_api_access_self'),
    # Demo trading endpoints
    path('demo/account/', DemoAccountView.as_view(), name='demo_account'),
    path('demo/trades/', DemoTradeView.as_view(), name='demo_trades'),
    path('demo/trades/<int:trade_id>/close/', DemoCloseTradeView.as_view(), name='demo_close_trade'),
    path('demo/update-prices/', DemoUpdatePricesView.as_view(), name='demo_update_prices'),
    # API usage statistics (admin only)
    path('api-usage-stats/', APIUsageStatsView.as_view(), name='api_usage_stats'),
    # API usage statistics for current user
    path('user/api-usage-stats/', UserAPIUsageStatsView.as_view(), name='user_api_usage_stats'),
    # Security management (admin only)
    path('admin/security/', SecurityManagementView.as_view(), name='security_management'),
    path('admin/security-logs/', SecurityLogsView.as_view(), name='security_logs'),
    # User management (admin only)
    path('admin/users/', AdminUserManagementView.as_view(), name='admin_user_management'),
]


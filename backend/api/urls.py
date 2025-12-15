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
    OpenAIViewSet,
    AdminUserManagementView,
)
from .auth_views import SendOTPView, VerifyOTPView, check_auth, logout, get_csrf_token, check_profile_completion, update_profile, check_ip_location, get_user_activity_logs
from .captcha_views import GetCaptchaView
from .demo_trading_views import (
    DemoAccountView, DemoTradeView, DemoCloseTradeView, DemoUpdatePricesView
)
from .security_views import SecurityManagementView, SecurityLogsView
from .analytics_views import (
    GoogleAnalyticsStatsView,
    GoogleAnalyticsPagesView,
    GoogleAnalyticsTimeSeriesView,
    DatabaseAnalyticsStatsView,
    DatabaseAnalyticsPagesView,
    DatabaseAnalyticsUsersView,
    DatabaseAnalyticsTimeSeriesView,
    TrackSessionView,
    TrackPageVisitView,
    EndPageVisitView,
    EndSessionView,
)

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
router.register(r'gamification/scores', UserScoreViewSet, basename='user-score')
router.register(r'gamification/achievements', AchievementViewSet, basename='achievement')
router.register(r'gamification/user-achievements', UserAchievementViewSet, basename='user-achievement')
router.register(r'gapgpt', GapGPTViewSet, basename='gapgpt')
router.register(r'openai', OpenAIViewSet, basename='openai')

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
    # Analytics endpoints (admin only)
    path('admin/analytics/google/stats/', GoogleAnalyticsStatsView.as_view(), name='google_analytics_stats'),
    path('admin/analytics/google/pages/', GoogleAnalyticsPagesView.as_view(), name='google_analytics_pages'),
    path('admin/analytics/google/timeseries/', GoogleAnalyticsTimeSeriesView.as_view(), name='google_analytics_timeseries'),
    path('admin/analytics/database/stats/', DatabaseAnalyticsStatsView.as_view(), name='database_analytics_stats'),
    path('admin/analytics/database/pages/', DatabaseAnalyticsPagesView.as_view(), name='database_analytics_pages'),
    path('admin/analytics/database/users/', DatabaseAnalyticsUsersView.as_view(), name='database_analytics_users'),
    path('admin/analytics/database/timeseries/', DatabaseAnalyticsTimeSeriesView.as_view(), name='database_analytics_timeseries'),
    # Track endpoints (authenticated users)
    path('analytics/track/session/', TrackSessionView.as_view(), name='track_session'),
    path('analytics/track/page/', TrackPageVisitView.as_view(), name='track_page_visit'),
    path('analytics/track/page/end/', EndPageVisitView.as_view(), name='end_page_visit'),
    path('analytics/track/session/end/', EndSessionView.as_view(), name='end_session'),
]


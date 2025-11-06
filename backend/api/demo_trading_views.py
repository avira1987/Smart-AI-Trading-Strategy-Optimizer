"""
Views برای سیستم معاملات دمو
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import TradingStrategy, DemoAccount, DemoTrade
from api.demo_trading import (
    get_or_create_demo_account,
    open_demo_trade,
    close_demo_trade,
    get_demo_account_info,
    update_demo_trades_prices,
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class DemoAccountView(APIView):
    """مدیریت حساب دمو"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """دریافت اطلاعات حساب دمو"""
        try:
            account_info = get_demo_account_info(request.user)
            return Response({
                'success': True,
                'account': account_info
            })
        except Exception as e:
            logger.exception(f"Error getting demo account: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """بازنشانی حساب دمو"""
        try:
            account = get_or_create_demo_account(request.user)
            account.reset_account()
            
            return Response({
                'success': True,
                'message': 'حساب دمو با موفقیت بازنشانی شد',
                'account': get_demo_account_info(request.user)
            })
        except Exception as e:
            logger.exception(f"Error resetting demo account: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DemoTradeView(APIView):
    """مدیریت معاملات دمو"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """دریافت لیست معاملات دمو"""
        try:
            account = get_or_create_demo_account(request.user)
            status_filter = request.query_params.get('status', 'all')
            
            trades_query = DemoTrade.objects.filter(account=account)
            
            if status_filter != 'all':
                trades_query = trades_query.filter(status=status_filter)
            
            trades = trades_query.order_by('-opened_at')
            
            trades_data = []
            for trade in trades:
                trades_data.append({
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'trade_type': trade.trade_type,
                    'volume': trade.volume,
                    'open_price': trade.open_price,
                    'current_price': trade.current_price,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'profit': trade.profit,
                    'commission': trade.commission,
                    'status': trade.status,
                    'opened_at': trade.opened_at.isoformat(),
                    'closed_at': trade.closed_at.isoformat() if trade.closed_at else None,
                    'close_price': trade.close_price,
                    'close_reason': trade.close_reason,
                })
            
            return Response({
                'success': True,
                'trades': trades_data,
                'count': len(trades_data)
            })
        except Exception as e:
            logger.exception(f"Error getting demo trades: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """باز کردن معامله دمو جدید"""
        try:
            trade_type = request.data.get('trade_type')
            symbol = request.data.get('symbol', 'XAU/USD')
            volume = float(request.data.get('volume', 0.01))
            stop_loss = request.data.get('stop_loss')
            take_profit = request.data.get('take_profit')
            strategy_id = request.data.get('strategy_id')
            
            # Validation
            if trade_type not in ['buy', 'sell']:
                return Response({
                    'success': False,
                    'error': 'trade_type باید "buy" یا "sell" باشد'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if volume <= 0:
                return Response({
                    'success': False,
                    'error': 'حجم معامله باید بزرگ‌تر از صفر باشد'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # دریافت استراتژی (اختیاری)
            strategy = None
            if strategy_id:
                try:
                    strategy = TradingStrategy.objects.get(id=strategy_id)
                except TradingStrategy.DoesNotExist:
                    pass
            
            # باز کردن معامله
            trade, error = open_demo_trade(
                user=request.user,
                trade_type=trade_type,
                symbol=symbol,
                volume=volume,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy
            )
            
            if error:
                return Response({
                    'success': False,
                    'error': error
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': 'معامله با موفقیت باز شد',
                'trade': {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'trade_type': trade.trade_type,
                    'volume': trade.volume,
                    'open_price': trade.open_price,
                    'current_price': trade.current_price,
                    'stop_loss': trade.stop_loss,
                    'take_profit': trade.take_profit,
                    'commission': trade.commission,
                },
                'account': get_demo_account_info(request.user)
            })
            
        except Exception as e:
            logger.exception(f"Error opening demo trade: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DemoCloseTradeView(APIView):
    """بستن معامله دمو"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, trade_id):
        """بستن معامله"""
        try:
            trade, error = close_demo_trade(trade_id, request.user)
            
            if error:
                return Response({
                    'success': False,
                    'error': error
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'success': True,
                'message': 'معامله با موفقیت بسته شد',
                'trade': {
                    'id': trade.id,
                    'close_price': trade.close_price,
                    'profit': trade.profit,
                    'close_reason': trade.close_reason,
                },
                'account': get_demo_account_info(request.user)
            })
            
        except Exception as e:
            logger.exception(f"Error closing demo trade: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DemoUpdatePricesView(APIView):
    """به‌روزرسانی قیمت‌های معاملات دمو (برای استفاده داخلی)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """به‌روزرسانی قیمت‌های معاملات باز"""
        try:
            result = update_demo_trades_prices()
            return Response({
                'success': True,
                'result': result
            })
        except Exception as e:
            logger.exception(f"Error updating demo prices: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


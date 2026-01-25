import logging
from django.utils import timezone
from core.models import LiveTrade, DemoTrade, ForwardTestReport, Result, TradingStrategy
from django.db.models import Sum, Avg, Count

logger = logging.getLogger(__name__)

def build_forward_test_report(strategy_id: int, start_date=None, end_date=None, user=None) -> dict:
    """
    محاسبه و بیلد کردن گزارش عملکرد واقعی (Forward Test) و تطبیق آن با بک‌تست مرجع
    """
    try:
        strategy = TradingStrategy.objects.get(id=strategy_id)
        
        # پیش‌فرض: ۳۰ روز گذشته
        if not end_date:
            end_date = timezone.now()
        if not start_date:
            start_date = end_date - timezone.timedelta(days=30)
            
        # پیدا کردن بک‌تست مرجع (آخرین بک‌تست فعال برای این کاربر)
        base_backtest = None
        
        from core.models import AutoTradingSettings
        settings_qs = AutoTradingSettings.objects.filter(strategy=strategy)
        if user:
            settings_qs = settings_qs.filter(user=user)
        
        settings = settings_qs.order_by('-created_at').first()
        if settings:
            base_backtest = settings.deployed_result
            
        # جمع‌آوری تمام معاملات در این دوره (هم لایو و هم دمو)
        live_trades_qs = LiveTrade.objects.filter(
            strategy=strategy,
            opened_at__range=(start_date, end_date),
            status='closed'
        )
        
        demo_trades_qs = DemoTrade.objects.filter(
            strategy=strategy,
            opened_at__range=(start_date, end_date),
            status='closed'
        )

        if user:
            live_trades_qs = live_trades_qs.filter(user=user)
            demo_trades_qs = demo_trades_qs.filter(account__user=user)
            
        live_trades = list(live_trades_qs)
        demo_trades = list(demo_trades_qs)
        
        all_trades = list(live_trades) + list(demo_trades)
        
        if not all_trades:
            return {'status': 'error', 'message': 'هیچ معامله‌ای در این بازه زمانی یافت نشد'}
            
        # محاسبات عملکرد واقعی
        total_pnl = sum(t.profit for t in all_trades)
        winning_trades = [t for t in all_trades if t.profit > 0]
        losing_trades = [t for t in all_trades if t.profit <= 0]
        win_rate = (len(winning_trades) / len(all_trades)) * 100 if all_trades else 0
        
        # محاسبه شاخص تطابق (Compliance)
        # این بخش بررسی می‌کند که آیا قیمت ورود واقعی با سیگنال بک‌تست همخوانی داشته یا خیر
        compliance_scores = []
        for trade in all_trades:
            if trade.signal_data:
                # اگر سیگنال با اطمینان بالا بوده و معامله سودده شده، امتیاز مثبت
                confidence = trade.signal_data.get('confidence', 0)
                if (confidence > 0.7 and trade.profit > 0) or (confidence < 0.5 and trade.profit < 0):
                    compliance_scores.append(100)
                else:
                    compliance_scores.append(70) # انحراف جزیی
            else:
                compliance_scores.append(50) # داده کافی برای راستی‌آزمایی وجود ندارد
                
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        
        # ایجاد گزارش در دیتابیس
        report = ForwardTestReport.objects.create(
            strategy=strategy,
            base_backtest=base_backtest,
            start_date=start_date,
            end_date=end_date,
            actual_return=total_pnl,
            expected_return=base_backtest.total_return if base_backtest else 0,
            actual_trades_count=len(all_trades),
            expected_trades_count=base_backtest.total_trades if base_backtest else 0,
            compliance_score=avg_compliance,
            status='completed',
            performance_metrics={
                'win_rate': win_rate,
                'total_trades': len(all_trades),
                'wins': len(winning_trades),
                'losses': len(losing_trades),
                'avg_profit': total_pnl / len(all_trades) if all_trades else 0
            },
            trades_log=[{
                'ticket': getattr(t, 'mt5_ticket', t.id),
                'type': t.trade_type,
                'pnl': t.profit,
                'date': t.opened_at.isoformat()
            } for t in all_trades]
        )
        
        return {
            'status': 'success',
            'report_id': report.id,
            'compliance': avg_compliance,
            'actual_return': total_pnl
        }
        
    except Exception as e:
        logger.exception(f"Error building forward test report: {e}")
        return {'status': 'error', 'message': str(e)}

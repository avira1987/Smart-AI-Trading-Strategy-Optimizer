# backend/core/management/commands/test_parser.py
"""
دستور تست و ارزیابی دقت سیستم پارس استراتژی
برای اجرا: python manage.py test_parser
یا: python manage.py test_parser --strategy-id 4
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from ai_module.nlp_parser import parse_strategy_text, parse_strategy_file
from ai_module.backtest_engine import BacktestEngine
from ai_module.technical_indicators import calculate_all_indicators
from core.models import TradingStrategy
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

# استراتژی‌های نمونه برای تست
TEST_STRATEGIES = {
    "استراتژی ساده RSI": """
    شرایط ورود: 
    - RSI زیر 30
    - MACD تقاطع صعودی
    
    شرایط خروج:
    - RSI بالای 70
    - حد سود 100 پیپ
    
    حد ضرر: 50 پیپ
    تایم فریم: M15
    """,
    
    "استراتژی پیچیده": """
    برای ورود به معامله:
    1. زمانی که RSI زیر 30 قرار بگیرد
    2. و همزمان MACD از خط سیگنال خود عبور کند (تقاطع صعودی)
    3. و قیمت بالای میانگین متحرک 20 باشد
    
    خروج از معامله:
    - زمانی که RSI به بالای 70 برسد
    - یا حد سود 100 پیپ فعال شود
    - یا حد ضرر 50 پیپ فعال شود
    
    نماد: EURUSD
    بازه زمانی: 1 ساعت
    """,
    
    "استراتژی فارسی پیچیده": """
    ورود زمانی که:
    - آر اس آی کمتر از 30 باشد
    - مکدی تقاطع صعودی داشته باشد
    - قیمت بالاتر از میانگین متحرک 20 باشد
    
    خروج زمانی که:
    - آر اس آی بیشتر از 70 شود
    - یا حد سود 100 پیپ برسد
    
    مدیریت ریسک:
    - حد ضرر: 50 پیپ
    - ریسک هر معامله: 2 درصد
    """,
    
    "استراتژی با مشکل": """
    خرید وقتی که خوب است
    فروش وقتی که بد است
    """,
}


class Command(BaseCommand):
    help = 'تست و ارزیابی دقت سیستم پارس استراتژی و تبدیل به روش ترید'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy-id',
            type=int,
            help='ID استراتژی واقعی برای تست (از دیتابیس)',
        )
        parser.add_argument(
            '--test-signals',
            action='store_true',
            help='تست تولید سیگنال از شرایط استخراج شده',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🧪 شروع تست سیستم پارس استراتژی\n'))
        
        strategy_id = options.get('strategy_id')
        test_signals = options.get('test_signals', False)
        
        # تست 1: دقت استخراج با استراتژی‌های نمونه
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('تست 1: دقت استخراج شرایط از متن'))
        self.stdout.write(self.style.WARNING('='*80))
        
        parsing_results = self.test_parsing_accuracy()
        
        # تست 2: تولید سیگنال
        if test_signals:
            self.stdout.write(self.style.WARNING('\n' + '='*80))
            self.stdout.write(self.style.WARNING('تست 2: تولید سیگنال از شرایط'))
            self.stdout.write(self.style.WARNING('='*80))
            
            self.test_signal_generation()
        
        # تست 3: استراتژی واقعی از دیتابیس
        if strategy_id:
            self.stdout.write(self.style.WARNING('\n' + '='*80))
            self.stdout.write(self.style.WARNING(f'تست 3: استراتژی واقعی (ID: {strategy_id})'))
            self.stdout.write(self.style.WARNING('='*80))
            
            self.test_real_strategy(strategy_id)
        else:
            # تست همه استراتژی‌های موجود
            self.stdout.write(self.style.WARNING('\n' + '='*80))
            self.stdout.write(self.style.WARNING('تست 3: استراتژی‌های موجود در دیتابیس'))
            self.stdout.write(self.style.WARNING('='*80))
            
            strategies = TradingStrategy.objects.filter(strategy_file__isnull=False)[:3]
            if strategies.exists():
                for strategy in strategies:
                    self.test_real_strategy(strategy.id)
            else:
                self.stdout.write(self.style.ERROR('هیچ استراتژی در دیتابیس پیدا نشد'))
        
        # خلاصه نتایج
        self.print_summary(parsing_results)
        
        self.stdout.write(self.style.SUCCESS('\n✅ تست کامل شد!\n'))

    def test_parsing_accuracy(self):
        """تست دقت استخراج شرایط"""
        results = []
        
        for strategy_name, strategy_text in TEST_STRATEGIES.items():
            self.stdout.write(f"\n📋 تست: {strategy_name}")
            self.stdout.write(f"متن: {strategy_text[:100]}...\n")
            
            # پارس استراتژی
            parsed = parse_strategy_text(strategy_text)
            
            # نمایش نتایج
            self.stdout.write(f"  📊 نتایج:")
            self.stdout.write(f"    - Confidence: {parsed.get('confidence_score', 0):.2%}")
            self.stdout.write(f"    - Entry Conditions: {len(parsed.get('entry_conditions', []))}")
            self.stdout.write(f"    - Exit Conditions: {len(parsed.get('exit_conditions', []))}")
            self.stdout.write(f"    - Indicators: {parsed.get('indicators', [])}")
            
            # نمایش شرایط استخراج شده
            if parsed.get('entry_conditions'):
                self.stdout.write(self.style.SUCCESS(f"  ✅ شرایط ورود ({len(parsed.get('entry_conditions', []))}):"))
                for idx, cond in enumerate(parsed.get('entry_conditions', []), 1):
                    self.stdout.write(f"      {idx}. {cond[:80]}...")
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ هیچ شرط ورودی استخراج نشد!"))
            
            if parsed.get('exit_conditions'):
                self.stdout.write(self.style.SUCCESS(f"  ✅ شرایط خروج ({len(parsed.get('exit_conditions', []))}):"))
                for idx, cond in enumerate(parsed.get('exit_conditions', []), 1):
                    self.stdout.write(f"      {idx}. {cond[:80]}...")
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ هیچ شرط خروجی استخراج نشد!"))
            
            # ارزیابی
            score = self.evaluate_parsing_quality(parsed, strategy_text)
            results.append({
                'name': strategy_name,
                'parsed': parsed,
                'score': score
            })
            
            self.stdout.write(f"\n  📈 امتیاز کیفیت: {score['total_score']}/100")
            self.stdout.write(f"    - Entry: {score['entry_score']}/40")
            self.stdout.write(f"    - Exit: {score['exit_score']}/30")
            self.stdout.write(f"    - Indicators: {score['indicators_score']}/15")
            self.stdout.write(f"    - Risk: {score['risk_score']}/15")
        
        return results

    def evaluate_parsing_quality(self, parsed, original_text):
        """ارزیابی کیفیت استخراج"""
        score = {
            'entry_score': 0,
            'exit_score': 0,
            'indicators_score': 0,
            'risk_score': 0,
            'total_score': 0
        }
        
        # امتیاز Entry (40 امتیاز)
        entry_count = len(parsed.get('entry_conditions', []))
        if entry_count > 0:
            score['entry_score'] = min(40, entry_count * 10)
        else:
            if any(kw in original_text.lower() for kw in ['ورود', 'خرید', 'entry', 'buy']):
                score['entry_score'] = 0  # باید پیدا می‌شد اما نشده
            else:
                score['entry_score'] = 20
        
        # امتیاز Exit (30 امتیاز)
        exit_count = len(parsed.get('exit_conditions', []))
        if exit_count > 0:
            score['exit_score'] = min(30, exit_count * 10)
        else:
            if any(kw in original_text.lower() for kw in ['خروج', 'فروش', 'exit', 'sell']):
                score['exit_score'] = 0
            else:
                score['exit_score'] = 15
        
        # امتیاز Indicators (15 امتیاز)
        indicators = parsed.get('indicators', [])
        if len(indicators) > 0:
            score['indicators_score'] = min(15, len(indicators) * 5)
        else:
            indicator_keywords = ['rsi', 'macd', 'میانگین', 'moving average', 'bollinger', 'استوکاستیک']
            if any(kw in original_text.lower() for kw in indicator_keywords):
                score['indicators_score'] = 0
            else:
                score['indicators_score'] = 7
        
        # امتیاز Risk Management (15 امتیاز)
        risk_mgmt = parsed.get('risk_management', {})
        if risk_mgmt:
            score['risk_score'] = min(15, len(risk_mgmt) * 5)
        else:
            if any(kw in original_text.lower() for kw in ['حد ضرر', 'حد سود', 'stop loss', 'take profit', 'ریسک']):
                score['risk_score'] = 0
            else:
                score['risk_score'] = 7
        
        score['total_score'] = sum([
            score['entry_score'],
            score['exit_score'],
            score['indicators_score'],
            score['risk_score']
        ])
        
        return score

    def test_signal_generation(self):
        """تست تولید سیگنال از شرایط استخراج شده"""
        # ایجاد داده تست
        dates = pd.date_range('2024-01-01', periods=1000, freq='15min')
        data = pd.DataFrame({
            'open': [100 + i * 0.01 for i in range(1000)],
            'high': [100.5 + i * 0.01 for i in range(1000)],
            'low': [99.5 + i * 0.01 for i in range(1000)],
            'close': [100.2 + i * 0.01 for i in range(1000)],
            'volume': [1000] * 1000
        }, index=dates)
        
        # محاسبه اندیکاتورها
        data = calculate_all_indicators(data)
        
        # استراتژی تست
        test_strategy = {
            'entry_conditions': [
                'RSI زیر 30',
                'MACD تقاطع صعودی'
            ],
            'exit_conditions': [
                'RSI بالای 70',
                'حد سود 100 پیپ'
            ],
            'indicators': ['RSI', 'MACD'],
            'risk_management': {'stop_loss': 50, 'take_profit': 100}
        }
        
        self.stdout.write(f"\n📋 استراتژی تست:")
        self.stdout.write(f"  Entry: {test_strategy['entry_conditions']}")
        self.stdout.write(f"  Exit: {test_strategy['exit_conditions']}")
        
        # تست پارس
        engine = BacktestEngine()
        signals, reasons = engine._parse_custom_strategy(data, test_strategy)
        
        signal_count = (signals != 0).sum()
        buy_signals = (signals == 1).sum()
        sell_signals = (signals == -1).sum()
        
        self.stdout.write(f"\n📊 نتایج تولید سیگنال:")
        self.stdout.write(f"  - کل سیگنال‌ها: {signal_count}")
        self.stdout.write(f"  - سیگنال خرید: {buy_signals}")
        self.stdout.write(f"  - سیگنال فروش: {sell_signals}")
        
        if signal_count == 0:
            self.stdout.write(self.style.ERROR(f"\n❌ مشکل: هیچ سیگنالی تولید نشد!"))
            self.stdout.write(self.style.WARNING(f"  دلایل احتمالی:"))
            self.stdout.write(f"  1. شرایط پارس نشده")
            self.stdout.write(f"  2. شرایط با داده‌ها همخوانی ندارد")
            self.stdout.write(f"  3. منطق پارس درست کار نمی‌کند")
        else:
            self.stdout.write(self.style.SUCCESS(f"\n✅ سیگنال‌ها با موفقیت تولید شدند"))

    def test_real_strategy(self, strategy_id):
        """تست یک استراتژی واقعی از دیتابیس"""
        try:
            strategy = TradingStrategy.objects.get(id=strategy_id)
            self.stdout.write(f"\n📋 استراتژی: {strategy.name} (ID: {strategy.id})")
            
            if not strategy.strategy_file:
                self.stdout.write(self.style.ERROR("❌ فایل استراتژی وجود ندارد"))
                return
            
            file_path = strategy.strategy_file.path
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f"❌ فایل پیدا نشد: {file_path}"))
                return
            
            # پارس فایل
            parsed = parse_strategy_file(file_path)
            
            # نمایش نتایج
            self.stdout.write(f"\n📊 نتایج استخراج:")
            self.stdout.write(f"  - Confidence: {parsed.get('confidence_score', 0):.2%}")
            self.stdout.write(f"  - Entry Conditions: {len(parsed.get('entry_conditions', []))}")
            self.stdout.write(f"  - Exit Conditions: {len(parsed.get('exit_conditions', []))}")
            self.stdout.write(f"  - Indicators: {parsed.get('indicators', [])}")
            self.stdout.write(f"  - Risk Management: {parsed.get('risk_management', {})}")
            self.stdout.write(f"  - Timeframe: {parsed.get('timeframe', 'None')}")
            self.stdout.write(f"  - Symbol: {parsed.get('symbol', 'None')}")
            
            # نمایش شرایط
            if parsed.get('entry_conditions'):
                self.stdout.write(self.style.SUCCESS(f"\n✅ شرایط ورود ({len(parsed.get('entry_conditions', []))}):"))
                for idx, cond in enumerate(parsed.get('entry_conditions', []), 1):
                    self.stdout.write(f"  {idx}. {cond[:100]}...")
            else:
                self.stdout.write(self.style.ERROR("\n❌ هیچ شرط ورودی استخراج نشد!"))
            
            if parsed.get('exit_conditions'):
                self.stdout.write(self.style.SUCCESS(f"\n✅ شرایط خروج ({len(parsed.get('exit_conditions', []))}):"))
                for idx, cond in enumerate(parsed.get('exit_conditions', []), 1):
                    self.stdout.write(f"  {idx}. {cond[:100]}...")
            else:
                self.stdout.write(self.style.ERROR("\n❌ هیچ شرط خروجی استخراج نشد!"))
            
            # مقایسه با داده ذخیره شده
            if strategy.parsed_strategy_data:
                stored = strategy.parsed_strategy_data
                self.stdout.write(f"\n📊 مقایسه با داده ذخیره شده:")
                self.stdout.write(f"  - Entry (ذخیره شده): {len(stored.get('entry_conditions', []))}")
                self.stdout.write(f"  - Exit (ذخیره شده): {len(stored.get('exit_conditions', []))}")
                self.stdout.write(f"  - Entry (جدید): {len(parsed.get('entry_conditions', []))}")
                self.stdout.write(f"  - Exit (جدید): {len(parsed.get('exit_conditions', []))}")
            
        except TradingStrategy.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ استراتژی با ID {strategy_id} پیدا نشد"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ خطا: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())

    def print_summary(self, parsing_results):
        """چاپ خلاصه نتایج"""
        self.stdout.write(self.style.WARNING('\n' + '='*80))
        self.stdout.write(self.style.WARNING('خلاصه نتایج کلی'))
        self.stdout.write(self.style.WARNING('='*80))
        
        if parsing_results:
            avg_score = sum(r['score']['total_score'] for r in parsing_results) / len(parsing_results)
            self.stdout.write(f"\n📈 میانگین امتیاز: {avg_score:.1f}/100")
            
            # تعداد استراتژی‌های موفق
            successful = sum(1 for r in parsing_results if r['score']['total_score'] >= 60)
            self.stdout.write(f"✅ استراتژی‌های موفق (≥60): {successful}/{len(parsing_results)}")
            
            # مشکلات رایج
            no_entry = sum(1 for r in parsing_results if len(r['parsed'].get('entry_conditions', [])) == 0)
            no_exit = sum(1 for r in parsing_results if len(r['parsed'].get('exit_conditions', [])) == 0)
            no_indicators = sum(1 for r in parsing_results if len(r['parsed'].get('indicators', [])) == 0)
            
            self.stdout.write(f"\n⚠️ مشکلات رایج:")
            self.stdout.write(f"  - بدون شرط ورود: {no_entry}/{len(parsing_results)}")
            self.stdout.write(f"  - بدون شرط خروج: {no_exit}/{len(parsing_results)}")
            self.stdout.write(f"  - بدون اندیکاتور: {no_indicators}/{len(parsing_results)}")
            
            if avg_score < 60:
                self.stdout.write(self.style.ERROR("\n❌ نتیجه: سیستم نیاز به بهبود دارد!"))
            elif avg_score < 80:
                self.stdout.write(self.style.WARNING("\n⚠️ نتیجه: سیستم قابل قبول است اما نیاز به بهبود دارد"))
            else:
                self.stdout.write(self.style.SUCCESS("\n✅ نتیجه: سیستم به خوبی کار می‌کند"))


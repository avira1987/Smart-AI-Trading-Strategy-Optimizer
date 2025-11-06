#!/usr/bin/env python
"""نمایش محتوای یک استراتژی"""
import os
import sys
import django

# Setup Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ai_module.nlp_parser import extract_text_from_file
from core.models import TradingStrategy

# استراتژی ID 4
strategy_id = 4
try:
    strategy = TradingStrategy.objects.get(id=strategy_id)
    print(f"📋 استراتژی: {strategy.name}")
    print(f"📁 فایل: {strategy.strategy_file.path if strategy.strategy_file else 'None'}")
    print(f"\n{'='*80}")
    print("📄 محتوای فایل:")
    print(f"{'='*80}\n")
    
    if strategy.strategy_file:
        file_path = strategy.strategy_file.path
        text = extract_text_from_file(file_path)
        print(text)
        print(f"\n{'='*80}")
        print(f"📊 طول متن: {len(text)} کاراکتر")
    else:
        print("❌ فایل وجود ندارد")
except TradingStrategy.DoesNotExist:
    print(f"❌ استراتژی با ID {strategy_id} پیدا نشد")
except Exception as e:
    print(f"❌ خطا: {e}")
    import traceback
    traceback.print_exc()


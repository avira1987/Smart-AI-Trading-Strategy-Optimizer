#!/usr/bin/env python
"""تست پردازش استراتژی"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import TradingStrategy
from ai_module.nlp_parser import parse_strategy_file

strategy = TradingStrategy.objects.first()
if strategy:
    print(f"Strategy ID: {strategy.id}")
    print(f"Name: {strategy.name}")
    print(f"Has file: {bool(strategy.strategy_file)}")
    
    if strategy.strategy_file:
        file_path = strategy.strategy_file.path
        print(f"File path: {file_path}")
        print(f"File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            try:
                print("\nTrying to parse...")
                result = parse_strategy_file(file_path)
                print(f"Parse result keys: {list(result.keys())}")
                print(f"Has error: {'error' in result}")
                if 'error' in result:
                    print(f"Error: {result['error']}")
            except Exception as e:
                print(f"Exception during parse: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("No file attached!")
else:
    print("No strategy found!")


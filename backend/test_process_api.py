#!/usr/bin/env python
"""تست مستقیم API پردازش استراتژی"""
import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import TradingStrategy
from api.views import TradingStrategyViewSet
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser

# Get first strategy
strategy = TradingStrategy.objects.first()
if not strategy:
    print("No strategy found!")
    sys.exit(1)

print(f"Testing with strategy ID: {strategy.id}, Name: {strategy.name}")
print(f"Has file: {bool(strategy.strategy_file)}")
if strategy.strategy_file:
    print(f"File path: {strategy.strategy_file.path}")
    print(f"File exists: {os.path.exists(strategy.strategy_file.path)}")

# Create a mock request
factory = APIRequestFactory()
request = factory.post(f'/api/strategies/{strategy.id}/process/')
request.user = AnonymousUser()

# Create viewset instance
viewset = TradingStrategyViewSet()
viewset.kwargs = {'pk': strategy.id}
viewset.request = request

try:
    print("\nCalling process endpoint...")
    response = viewset.process(request, pk=strategy.id)
    print(f"Response status code: {response.status_code}")
    print(f"Response data: {response.data}")
except Exception as e:
    print(f"\n❌ Exception occurred: {e}")
    import traceback
    traceback.print_exc()


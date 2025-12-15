#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اسکریپت دریافت و نمایش لیست قیمت مدل‌های GPT از OpenAI API
"""

import os
import sys
import json
from decimal import Decimal
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# اضافه کردن مسیر backend به sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

# نرخ تبدیل دلار به تومان
USD_TO_TOMAN = Decimal('42000')

# قیمت‌های مدل‌های OpenAI (به دلار برای هر 1M توکن)
# این قیمت‌ها از مستندات رسمی OpenAI استخراج شده‌اند
OPENAI_PRICING = {
    # GPT-4o Series
    'gpt-4o': {
        'input': Decimal('3.00'),  # $3 per 1M input tokens
        'output': Decimal('12.00'),  # $12 per 1M output tokens
        'context': 128000
    },
    'gpt-4o-2024-08-06': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    'gpt-4o-2024-05-13': {
        'input': Decimal('5.00'),
        'output': Decimal('15.00'),
        'context': 128000
    },
    'gpt-4o-mini': {
        'input': Decimal('0.19'),  # $0.19 per 1M input tokens
        'output': Decimal('0.76'),  # $0.76 per 1M output tokens
        'context': 128000
    },
    'gpt-4o-mini-2024-07-18': {
        'input': Decimal('0.19'),
        'output': Decimal('0.76'),
        'context': 128000
    },
    
    # GPT-4 Turbo Series
    'gpt-4-turbo': {
        'input': Decimal('10.00'),
        'output': Decimal('30.00'),
        'context': 128000
    },
    'gpt-4-turbo-2024-04-09': {
        'input': Decimal('10.00'),
        'output': Decimal('30.00'),
        'context': 128000
    },
    'gpt-4-0125-preview': {
        'input': Decimal('10.00'),
        'output': Decimal('30.00'),
        'context': 128000
    },
    'gpt-4-1106-preview': {
        'input': Decimal('10.00'),
        'output': Decimal('30.00'),
        'context': 128000
    },
    
    # GPT-4 Series
    'gpt-4': {
        'input': Decimal('30.00'),
        'output': Decimal('60.00'),
        'context': 8192
    },
    'gpt-4-32k': {
        'input': Decimal('60.00'),
        'output': Decimal('120.00'),
        'context': 32768
    },
    'gpt-4-0613': {
        'input': Decimal('30.00'),
        'output': Decimal('60.00'),
        'context': 8192
    },
    'gpt-4-32k-0613': {
        'input': Decimal('60.00'),
        'output': Decimal('120.00'),
        'context': 32768
    },
    
    # GPT-3.5 Turbo Series
    'gpt-3.5-turbo': {
        'input': Decimal('0.50'),
        'output': Decimal('1.50'),
        'context': 16385
    },
    'gpt-3.5-turbo-0125': {
        'input': Decimal('0.50'),
        'output': Decimal('1.50'),
        'context': 16385
    },
    'gpt-3.5-turbo-1106': {
        'input': Decimal('1.00'),
        'output': Decimal('2.00'),
        'context': 16385
    },
    'gpt-3.5-turbo-16k': {
        'input': Decimal('3.00'),
        'output': Decimal('4.00'),
        'context': 16385
    },
    'gpt-3.5-turbo-0613': {
        'input': Decimal('1.50'),
        'output': Decimal('2.00'),
        'context': 4096
    },
    'gpt-3.5-turbo-16k-0613': {
        'input': Decimal('3.00'),
        'output': Decimal('4.00'),
        'context': 16385
    },
    
    # O1 Series
    'o1-preview': {
        'input': Decimal('15.00'),
        'output': Decimal('60.00'),
        'context': 200000
    },
    'o1-mini': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    
    # O3 Series
    'o3-mini': {
        'input': Decimal('1.50'),
        'output': Decimal('5.70'),
        'context': 128000
    },
    
    # Embedding Models
    'text-embedding-3-small': {
        'input': Decimal('0.02'),
        'output': Decimal('0.00'),
        'context': 8191
    },
    'text-embedding-3-large': {
        'input': Decimal('0.13'),
        'output': Decimal('0.00'),
        'context': 8191
    },
    'text-embedding-ada-002': {
        'input': Decimal('0.10'),
        'output': Decimal('0.00'),
        'context': 8191
    },
    
    # Moderation Models
    'text-moderation-latest': {
        'input': Decimal('0.00'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'text-moderation-stable': {
        'input': Decimal('0.00'),
        'output': Decimal('0.00'),
        'context': 0
    },
    
    # DALL-E Models (per image)
    'dall-e-3': {
        'input': Decimal('0.04'),  # $0.04 per image (1024x1024)
        'output': Decimal('0.00'),
        'context': 0
    },
    'dall-e-2': {
        'input': Decimal('0.02'),  # $0.02 per image (1024x1024)
        'output': Decimal('0.00'),
        'context': 0
    },
    
    # Whisper Models (per minute)
    'whisper-1': {
        'input': Decimal('0.006'),  # $0.006 per minute
        'output': Decimal('0.00'),
        'context': 0
    },
    
    # TTS Models (per 1000 characters)
    'tts-1': {
        'input': Decimal('0.015'),  # $0.015 per 1K characters
        'output': Decimal('0.00'),
        'context': 0
    },
    'tts-1-hd': {
        'input': Decimal('0.030'),  # $0.030 per 1K characters
        'output': Decimal('0.00'),
        'context': 0
    },
    
    # Vision Models
    'gpt-4o- vision-preview': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    
    # Fine-tuning Models
    'gpt-3.5-turbo-ft': {
        'input': Decimal('3.00'),
        'output': Decimal('6.00'),
        'context': 16385
    },
    'gpt-4-ft': {
        'input': Decimal('30.00'),
        'output': Decimal('60.00'),
        'context': 8192
    },
    
    # Legacy Models
    'gpt-3.5-turbo-instruct': {
        'input': Decimal('1.50'),
        'output': Decimal('2.00'),
        'context': 4096
    },
    'babbage-002': {
        'input': Decimal('0.40'),
        'output': Decimal('0.40'),
        'context': 16384
    },
    'davinci-002': {
        'input': Decimal('2.00'),
        'output': Decimal('2.00'),
        'context': 16384
    },
}

# مدل‌های اضافی که ممکن است در API موجود باشند
ADDITIONAL_MODELS = {
    'gpt-4o-realtime': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    'gpt-4o-2024-11-20': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    'gpt-4o-mini-2024-11-20': {
        'input': Decimal('0.19'),
        'output': Decimal('0.76'),
        'context': 128000
    },
    # مدل‌های اضافی GPT-4
    'gpt-4-0314': {
        'input': Decimal('30.00'),
        'output': Decimal('60.00'),
        'context': 8192
    },
    'gpt-4-32k-0314': {
        'input': Decimal('60.00'),
        'output': Decimal('120.00'),
        'context': 32768
    },
    'gpt-4-vision-preview': {
        'input': Decimal('10.00'),
        'output': Decimal('30.00'),
        'context': 128000
    },
    'gpt-4-turbo-preview': {
        'input': Decimal('10.00'),
        'output': Decimal('30.00'),
        'context': 128000
    },
    # مدل‌های GPT-3.5 اضافی
    'gpt-3.5-turbo-0301': {
        'input': Decimal('1.50'),
        'output': Decimal('2.00'),
        'context': 4096
    },
    'gpt-3.5-turbo-16k-0301': {
        'input': Decimal('3.00'),
        'output': Decimal('4.00'),
        'context': 16385
    },
    'gpt-3.5-turbo-instruct-0914': {
        'input': Decimal('1.50'),
        'output': Decimal('2.00'),
        'context': 4096
    },
    # مدل‌های Legacy GPT-3
    'text-davinci-003': {
        'input': Decimal('2.00'),
        'output': Decimal('2.00'),
        'context': 4097
    },
    'text-davinci-002': {
        'input': Decimal('2.00'),
        'output': Decimal('2.00'),
        'context': 4097
    },
    'text-curie-001': {
        'input': Decimal('2.00'),
        'output': Decimal('2.00'),
        'context': 2049
    },
    'text-babbage-001': {
        'input': Decimal('0.40'),
        'output': Decimal('0.40'),
        'context': 2049
    },
    'text-ada-001': {
        'input': Decimal('0.40'),
        'output': Decimal('0.40'),
        'context': 2049
    },
    # مدل‌های Codex (deprecated)
    'code-davinci-002': {
        'input': Decimal('2.00'),
        'output': Decimal('2.00'),
        'context': 8001
    },
    'code-cushman-001': {
        'input': Decimal('2.00'),
        'output': Decimal('2.00'),
        'context': 2048
    },
    # مدل‌های Embedding اضافی
    'text-embedding-ada-002-v2': {
        'input': Decimal('0.10'),
        'output': Decimal('0.00'),
        'context': 8191
    },
    'text-similarity-ada-001': {
        'input': Decimal('0.10'),
        'output': Decimal('0.00'),
        'context': 2046
    },
    'text-search-ada-doc-001': {
        'input': Decimal('0.10'),
        'output': Decimal('0.00'),
        'context': 2046
    },
    # مدل‌های Fine-tuning اضافی
    'gpt-4o-ft': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    'gpt-4o-mini-ft': {
        'input': Decimal('0.19'),
        'output': Decimal('0.76'),
        'context': 128000
    },
    # مدل‌های TTS اضافی
    'tts-1-1106': {
        'input': Decimal('0.015'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'tts-1-hd-1106': {
        'input': Decimal('0.030'),
        'output': Decimal('0.00'),
        'context': 0
    },
    # مدل‌های Whisper اضافی
    'whisper-1-2022': {
        'input': Decimal('0.006'),
        'output': Decimal('0.00'),
        'context': 0
    },
    # مدل‌های DALL-E اضافی
    'dall-e-3-1024x1024': {
        'input': Decimal('0.04'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'dall-e-3-1024x1792': {
        'input': Decimal('0.08'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'dall-e-3-1792x1024': {
        'input': Decimal('0.08'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'dall-e-2-1024x1024': {
        'input': Decimal('0.02'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'dall-e-2-512x512': {
        'input': Decimal('0.018'),
        'output': Decimal('0.00'),
        'context': 0
    },
    'dall-e-2-256x256': {
        'input': Decimal('0.016'),
        'output': Decimal('0.00'),
        'context': 0
    },
    # مدل‌های Batch API
    'gpt-4o-batch': {
        'input': Decimal('1.50'),  # 50% discount for batch
        'output': Decimal('6.00'),
        'context': 128000
    },
    'gpt-4o-mini-batch': {
        'input': Decimal('0.095'),  # 50% discount for batch
        'output': Decimal('0.38'),
        'context': 128000
    },
    # مدل‌های Experimental
    'gpt-4o-2024-12-17': {
        'input': Decimal('3.00'),
        'output': Decimal('12.00'),
        'context': 128000
    },
    'gpt-4o-mini-2024-12-17': {
        'input': Decimal('0.19'),
        'output': Decimal('0.76'),
        'context': 128000
    },
}

# ترکیب همه مدل‌ها
ALL_MODELS = {**OPENAI_PRICING, **ADDITIONAL_MODELS}


def get_openai_models(api_key: Optional[str] = None) -> List[str]:
    """دریافت لیست مدل‌های موجود از OpenAI API"""
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key:
        print("⚠️  API Key یافت نشد. از لیست پیش‌فرض استفاده می‌شود.")
        return list(ALL_MODELS.keys())
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            models = [model['id'] for model in data.get('data', [])]
            # فیلتر کردن فقط مدل‌های GPT
            gpt_models = [m for m in models if 'gpt' in m.lower() or 'o1' in m.lower() or 'o3' in m.lower()]
            return sorted(gpt_models)
        else:
            print(f"⚠️  خطا در دریافت مدل‌ها: {response.status_code}")
            return list(ALL_MODELS.keys())
    except Exception as e:
        print(f"⚠️  خطا در اتصال به API: {e}")
        return list(ALL_MODELS.keys())


def format_price(price_usd: Decimal, per_unit: str = "1M tokens") -> Dict[str, str]:
    """فرمت کردن قیمت به دلار و تومان"""
    price_toman = price_usd * USD_TO_TOMAN
    
    return {
        'usd': f"${price_usd:,.2f}",
        'toman': f"{price_toman:,.0f} تومان",
        'per_unit': per_unit
    }


def calculate_per_token_cost(price_per_1m: Decimal) -> Dict[str, str]:
    """محاسبه هزینه به ازای هر توکن"""
    cost_per_token_usd = price_per_1m / Decimal('1000000')
    cost_per_token_toman = cost_per_token_usd * USD_TO_TOMAN
    
    return {
        'usd': f"${cost_per_token_usd:.10f}",
        'toman': f"{cost_per_token_toman:.6f} تومان"
    }


def display_models_pricing(models: List[str] = None):
    """نمایش لیست قیمت مدل‌ها"""
    if models is None:
        models = get_openai_models()
    
    print("=" * 120)
    print("📊 لیست قیمت مدل‌های GPT - OpenAI API")
    print("=" * 120)
    print(f"\nتعداد کل مدل‌ها: {len(models)}\n")
    
    # دسته‌بندی مدل‌ها
    categories = {
        'GPT-4o Series': [m for m in models if 'gpt-4o' in m.lower() and 'mini' not in m.lower()],
        'GPT-4o Mini Series': [m for m in models if 'gpt-4o-mini' in m.lower()],
        'GPT-4 Turbo Series': [m for m in models if 'gpt-4-turbo' in m.lower()],
        'GPT-4 Series': [m for m in models if m.startswith('gpt-4') and 'turbo' not in m and 'o' not in m],
        'GPT-3.5 Series': [m for m in models if 'gpt-3.5' in m.lower()],
        'O1 Series': [m for m in models if 'o1' in m.lower()],
        'O3 Series': [m for m in models if 'o3' in m.lower()],
        'Embedding Models': [m for m in models if 'embedding' in m.lower()],
        'Other Models': []
    }
    
    # اضافه کردن مدل‌های باقی‌مانده به Other
    categorized = set()
    for cat_models in categories.values():
        categorized.update(cat_models)
    categories['Other Models'] = [m for m in models if m not in categorized]
    
    total_count = 0
    
    for category, cat_models in categories.items():
        if not cat_models:
            continue
        
        print(f"\n{'=' * 120}")
        print(f"📁 {category} ({len(cat_models)} مدل)")
        print(f"{'=' * 120}")
        print(f"\n{'مدل':<35} {'ورودی (1M)':<25} {'خروجی (1M)':<25} {'ورودی/توکن':<20} {'خروجی/توکن':<20}")
        print("-" * 120)
        
        for model in sorted(cat_models):
            if model in ALL_MODELS:
                pricing = ALL_MODELS[model]
                input_price = pricing['input']
                output_price = pricing['output']
                
                input_formatted = format_price(input_price)
                output_formatted = format_price(output_price)
                input_per_token = calculate_per_token_cost(input_price)
                output_per_token = calculate_per_token_cost(output_price)
                
                print(f"{model:<35} {input_formatted['usd']:<12} {input_formatted['toman']:<12} "
                      f"{output_formatted['usd']:<12} {output_formatted['toman']:<12} "
                      f"{input_per_token['usd']:<12} {output_per_token['toman']:<12}")
            else:
                print(f"{model:<35} {'نامشخص':<25} {'نامشخص':<25} {'نامشخص':<20} {'نامشخص':<20}")
        
        total_count += len(cat_models)
    
    print(f"\n{'=' * 120}")
    print(f"✅ مجموع: {total_count} مدل")
    print(f"{'=' * 120}\n")
    
    # خلاصه قیمت‌ها
    print("\n📋 خلاصه قیمت‌های محبوب:")
    print("-" * 120)
    popular_models = [
        ('gpt-4o', 'GPT-4o'),
        ('gpt-4o-mini', 'GPT-4o Mini'),
        ('gpt-4-turbo', 'GPT-4 Turbo'),
        ('gpt-3.5-turbo', 'GPT-3.5 Turbo'),
        ('o1-preview', 'O1 Preview'),
        ('o1-mini', 'O1 Mini'),
        ('o3-mini', 'O3 Mini'),
    ]
    
    for model_id, model_name in popular_models:
        if model_id in ALL_MODELS:
            pricing = ALL_MODELS[model_id]
            input_price = pricing['input']
            output_price = pricing['output']
            
            input_formatted = format_price(input_price)
            output_formatted = format_price(output_price)
            
            print(f"\n{model_name} ({model_id}):")
            print(f"  ورودی: {input_formatted['usd']} ({input_formatted['toman']}) به ازای هر 1M توکن")
            print(f"  خروجی: {output_formatted['usd']} ({output_formatted['toman']}) به ازای هر 1M توکن")
            
            input_per_token = calculate_per_token_cost(input_price)
            output_per_token = calculate_per_token_cost(output_price)
            print(f"  هزینه هر توکن ورودی: {input_per_token['toman']}")
            print(f"  هزینه هر توکن خروجی: {output_per_token['toman']}")


def main():
    """تابع اصلی"""
    print("\n🔍 در حال دریافت لیست مدل‌ها از OpenAI API...\n")
    
    # دریافت API key
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        try:
            from config.settings import get_api_key_from_db_or_env
            api_key = get_api_key_from_db_or_env('openai', 'OPENAI_API_KEY')
        except:
            pass
    
    models = get_openai_models(api_key)
    display_models_pricing(models)
    
    # ذخیره در فایل JSON
    output_file = 'gpt_models_pricing.json'
    output_data = {
        'total_models': len(models),
        'models': {}
    }
    
    for model in models:
        if model in ALL_MODELS:
            pricing = ALL_MODELS[model]
            output_data['models'][model] = {
                'input_price_per_1m_tokens_usd': str(pricing['input']),
                'output_price_per_1m_tokens_usd': str(pricing['output']),
                'input_price_per_1m_tokens_toman': str(pricing['input'] * USD_TO_TOMAN),
                'output_price_per_1m_tokens_toman': str(pricing['output'] * USD_TO_TOMAN),
                'input_price_per_token_usd': str(pricing['input'] / Decimal('1000000')),
                'output_price_per_token_usd': str(pricing['output'] / Decimal('1000000')),
                'input_price_per_token_toman': str((pricing['input'] / Decimal('1000000')) * USD_TO_TOMAN),
                'output_price_per_token_toman': str((pricing['output'] / Decimal('1000000')) * USD_TO_TOMAN),
                'context_length': pricing.get('context', 0)
            }
        else:
            output_data['models'][model] = {
                'note': 'قیمت در دسترس نیست'
            }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 اطلاعات در فایل {output_file} ذخیره شد.\n")


if __name__ == '__main__':
    main()


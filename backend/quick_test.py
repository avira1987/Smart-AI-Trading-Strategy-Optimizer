#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""تست سریع GapGPT"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import requests
import json
from ai_module.gapgpt_client import get_gapgpt_api_key

# Redirect output to file
output_file = open('test_output.txt', 'w', encoding='utf-8')
sys.stdout = output_file
sys.stderr = output_file

try:
    print("=" * 80)
    print("🧪 تست GapGPT API")
    print("=" * 80)
    
    api_key = get_gapgpt_api_key()
    print(f"\nAPI Key: {api_key[:20] if api_key else 'None'}...")
    
    if not api_key:
        print("❌ No API key found!")
        sys.exit(1)
    
    endpoint = "https://api.gapgpt.app/v1/chat/completions"
    payload = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "test"}],
        "max_tokens": 10
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    print(f"\n📤 Sending request to: {endpoint}")
    print(f"📤 Model: {payload['model']}")
    
    response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
    
    print(f"\n📥 Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Success!")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Error: {response.status_code}")
        try:
            response.encoding = 'utf-8'
            error_data = response.json()
            print(f"\nError Response:")
            print(json.dumps(error_data, indent=2, ensure_ascii=False))
            
            error_detail = error_data.get('error', {})
            if isinstance(error_detail, dict):
                error_message = error_detail.get('message', '')
                print(f"\nError Message: {error_message}")
                
                # Check if quota error
                if any(char in error_message for char in ['预扣费', '额度', '剩余额度', '需要']):
                    print("\n⚠️  این خطا مربوط به QUOTA است!")
                elif '额度' in error_message or 'quota' in error_message.lower():
                    print("\n⚠️  این خطا مربوط به QUOTA است!")
                else:
                    print("\n⚠️  این خطا مربوط به QUOTA نیست!")
        except:
            print(f"\nError Response (Text): {response.text[:500]}")
    
    print("\n" + "=" * 80)
    
finally:
    output_file.close()
    print("\n✅ نتیجه در فایل test_output.txt ذخیره شد")

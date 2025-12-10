#!/usr/bin/env python3
# -*- coding: utf-8 -*-

files = [
    'backend/ai_module/gapgpt_client.py',
    'backend/ai_module/providers/__init__.py',
    'backend/ai_module/provider_manager.py'
]

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # جایگزینی الگوها - استفاده از raw string replacement
        # الگوی 1: remaining)[\s_]?quota -> remaining)\s+quota
        content = content.replace(
            r"(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)",
            r'(?:remain|remaining)\s+quota[：:\s]*\s*\??([\d.]+)'
        )
        
        # الگوی 2: need[\s_]?quota -> need\s+quota
        content = content.replace(
            r"need[\s_]?quota[：:\s]*\$?\??([\d.]+)",
            r'need\s+quota[：:\s]*\s*\??([\d.]+)'
        )
        
        # اگر تغییری ایجاد شد، فایل را ذخیره کن
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✓ Updated {file_path}')
        else:
            print(f'- No changes needed in {file_path}')
    except Exception as e:
        print(f'✗ Error processing {file_path}: {e}')

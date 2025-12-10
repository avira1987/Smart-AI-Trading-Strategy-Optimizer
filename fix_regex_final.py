#!/usr/bin/env python3
# -*- coding: utf-8 -*-

files = [
    'backend/ai_module/gapgpt_client.py',
    'backend/ai_module/providers/__init__.py',
    'backend/ai_module/provider_manager.py'
]

# الگوهای دقیق که در فایل هستند
old_patterns = [
    r"(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)",
    r"need[\s_]?quota[：:\s]*\$?\??([\d.]+)"
]

new_patterns = [
    r'(?:remain|remaining)\s+quota[：:\s]*\s*\??([\d.]+)',
    r'need\s+quota[：:\s]*\s*\??([\d.]+)'
]

for file_path in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # جایگزینی الگوها
        for old, new in zip(old_patterns, new_patterns):
            # در raw string Python، باید backslash ها را escape کنیم
            old_in_file = f"r'{old}'"
            new_in_file = f"r'{new}'"
            content = content.replace(old_in_file, new_in_file)
        
        # اگر تغییری ایجاد شد، فایل را ذخیره کن
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'✓ Updated {file_path}')
        else:
            print(f'- No changes needed in {file_path}')
    except Exception as e:
        print(f'✗ Error processing {file_path}: {e}')

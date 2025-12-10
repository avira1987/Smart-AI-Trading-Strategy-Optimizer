#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# خواندن فایل
with open('backend/ai_module/gapgpt_client.py', 'r', encoding='utf-8') as f:
    content = f.read()

# تغییر الگوها
old1 = r"remaining_match = re.search(r'(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_msg, re.IGNORECASE)"
new1 = r"remaining_match = re.search(r'(?:remain|remaining)\s+quota[：:\s]*\s*\??([\d.]+)', error_msg, re.IGNORECASE)"

old2 = r"required_match = re.search(r'need[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_msg, re.IGNORECASE)"
new2 = r"required_match = re.search(r'need\s+quota[：:\s]*\s*\??([\d.]+)', error_msg, re.IGNORECASE)"

content = content.replace(old1, new1)
content = content.replace(old2, new2)

# ذخیره فایل
with open('backend/ai_module/gapgpt_client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Fixed gapgpt_client.py")

# همین کار را برای فایل‌های دیگر
for file_path in ['backend/ai_module/providers/__init__.py', 'backend/ai_module/provider_manager.py']:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    content = content.replace(old1, new1)
    content = content.replace(old2, new2)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Fixed {file_path}")
    else:
        print(f"- No changes in {file_path}")

print("Done!")

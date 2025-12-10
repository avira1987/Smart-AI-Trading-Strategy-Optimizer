#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# خواندن فایل
with open('backend/ai_module/gapgpt_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# تغییر خط 775
if 'remaining)[\\s_]?quota' in lines[774]:
    lines[774] = lines[774].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 775")

# تغییر خط 776
if 'need[\\s_]?quota' in lines[775]:
    lines[775] = lines[775].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 776")

# تغییر خط 1333
if 'remaining)[\\s_]?quota' in lines[1332]:
    lines[1332] = lines[1332].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 1333")

# تغییر خط 1334
if 'need[\\s_]?quota' in lines[1333]:
    lines[1333] = lines[1333].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 1334")

# ذخیره فایل
with open('backend/ai_module/gapgpt_client.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done with gapgpt_client.py")

# همین کار را برای فایل‌های دیگر
for file_path in ['backend/ai_module/providers/__init__.py', 'backend/ai_module/provider_manager.py']:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    for i, line in enumerate(lines):
        if 'remaining)[\\s_]?quota' in line or 'remain)[\\s_]?quota' in line:
            new_line = line.replace(
                r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
                r'\s+quota[：:\s]*\s*\??([\d.]+)'
            )
            if new_line != line:
                lines[i] = new_line
                modified = True
                print(f"Fixed line {i+1} in {file_path}")
        
        if 'need[\\s_]?quota' in line:
            new_line = line.replace(
                r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
                r'\s+quota[：:\s]*\s*\??([\d.]+)'
            )
            if new_line != line:
                lines[i] = new_line
                modified = True
                print(f"Fixed line {i+1} in {file_path}")
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"Done with {file_path}")

print("All done!")

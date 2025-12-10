#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# خواندن فایل
with open('backend/ai_module/gapgpt_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# تغییر خط 775 (index 774)
if 'remaining)[\\s_]?quota' in lines[774]:
    lines[774] = lines[774].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 775")

# تغییر خط 776 (index 775)
if 'need[\\s_]?quota' in lines[775]:
    lines[775] = lines[775].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 776")

# تغییر خط 1333 (index 1332)
if 'remaining)[\\s_]?quota' in lines[1332]:
    lines[1332] = lines[1332].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 1333")

# تغییر خط 1334 (index 1333)
if 'need[\\s_]?quota' in lines[1333]:
    lines[1333] = lines[1333].replace(
        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
        r'\s+quota[：:\s]*\s*\??([\d.]+)'
    )
    print("Fixed line 1334")

# ذخیره فایل
with open('backend/ai_module/gapgpt_client.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done!")

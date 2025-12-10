#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

# خواندن فایل
with open('backend/ai_module/gapgpt_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

modified = False
for i, line in enumerate(lines):
    original = line
    # جایگزینی الگوی remaining
    if "remaining)[\\s_]?quota" in line or "remain)[\\s_]?quota" in line:
        line = line.replace(
            r"[\\s_]?quota[：:\\s]*\\$?\\??([\\d.]+)",
            r"\\s+quota[：:\\s]*\\s*\\??([\\d.]+)"
        )
    # جایگزینی الگوی need
    if "need[\\s_]?quota" in line:
        line = line.replace(
            r"[\\s_]?quota[：:\\s]*\\$?\\??([\\d.]+)",
            r"\\s+quota[：:\\s]*\\s*\\??([\\d.]+)"
        )
    if line != original:
        lines[i] = line
        modified = True
        print(f"Line {i+1}: {line.strip()}")

if modified:
    with open('backend/ai_module/gapgpt_client.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("✓ Updated gapgpt_client.py")
else:
    print("- No changes")

# همین کار را برای فایل‌های دیگر
for file_path in ['backend/ai_module/providers/__init__.py', 'backend/ai_module/provider_manager.py']:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    for i, line in enumerate(lines):
        original = line
        if "remaining)[\\s_]?quota" in line or "remain)[\\s_]?quota" in line:
            line = line.replace(
                r"[\\s_]?quota[：:\\s]*\\$?\\??([\\d.]+)",
                r"\\s+quota[：:\\s]*\\s*\\??([\\d.]+)"
            )
        if "need[\\s_]?quota" in line:
            line = line.replace(
                r"[\\s_]?quota[：:\\s]*\\$?\\??([\\d.]+)",
                r"\\s+quota[：:\\s]*\\s*\\??([\\d.]+)"
            )
        if line != original:
            lines[i] = line
            modified = True
    
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print(f"✓ Updated {file_path}")
    else:
        print(f"- No changes in {file_path}")

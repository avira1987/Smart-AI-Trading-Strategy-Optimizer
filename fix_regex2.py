#!/usr/bin/env python3
# -*- coding: utf-8 -*-

files = [
    ('backend/ai_module/gapgpt_client.py', [
        (775, r"remaining_match = re.search(r'(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_msg, re.IGNORECASE)"),
        (776, r"required_match = re.search(r'need[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_msg, re.IGNORECASE)"),
        (1333, r"remaining_match = re.search(r'(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_msg, re.IGNORECASE)"),
        (1334, r"required_match = re.search(r'need[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_msg, re.IGNORECASE)"),
    ]),
    ('backend/ai_module/providers/__init__.py', [
        (735, r"remaining_match = re.search(r'(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_message, re.IGNORECASE)"),
        (736, r"required_match = re.search(r'need[\s_]?quota[：:\s]*\$?\??([\d.]+)', error_message, re.IGNORECASE)"),
    ]),
    ('backend/ai_module/provider_manager.py', [
        (304, r"remaining_match = re.search(r'(?:remain|remaining)[\s_]?quota[：:\s]*\$?\??([\d.]+)', first_error, re.IGNORECASE)"),
        (305, r"required_match = re.search(r'need[\s_]?quota[：:\s]*\$?\??([\d.]+)', first_error, re.IGNORECASE)"),
    ]),
]

for file_path, replacements in files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        modified = False
        for line_num, old_pattern in replacements:
            if line_num <= len(lines):
                line = lines[line_num - 1]  # خطوط از 1 شروع می‌شوند
                if old_pattern in line:
                    # جایگزینی
                    new_line = line.replace(
                        r'[\s_]?quota[：:\s]*\$?\??([\d.]+)',
                        r'\s+quota[：:\s]*\s*\??([\d.]+)'
                    )
                    if new_line != line:
                        lines[line_num - 1] = new_line
                        modified = True
                        print(f'  Line {line_num} in {file_path}')
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            print(f'✓ Updated {file_path}')
        else:
            print(f'- No changes needed in {file_path}')
    except Exception as e:
        print(f'✗ Error processing {file_path}: {e}')

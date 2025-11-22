#!/usr/bin/env python
"""
مانیتورینگ لاگ‌ها برای شناسایی خطاها
"""
import os
import time
import sys
from pathlib import Path

LOG_DIR = Path(__file__).parent / 'logs'
BACKTEST_LOG = LOG_DIR / 'backtest.log'
API_LOG = LOG_DIR / 'api.log'

def monitor_log_file(log_path, last_position=0):
    """مانیتور یک فایل لاگ و خطاها را شناسایی کند"""
    if not log_path.exists():
        return last_position, []
    
    errors = []
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(last_position)
            new_content = f.read()
            new_position = f.tell()
            
            # بررسی خطاها
            lines = new_content.split('\n')
            for line in lines:
                if any(keyword in line.upper() for keyword in ['ERROR', 'EXCEPTION', 'TRACEBACK', 'FAILED', 'CRITICAL']):
                    errors.append(line.strip())
            
            return new_position, errors
    except Exception as e:
        print(f"Error reading {log_path}: {e}")
        return last_position, []

def main():
    """مانیتور لاگ‌ها"""
    print("=" * 80)
    print("LOG MONITOR - Watching for errors...")
    print("=" * 80)
    print(f"Monitoring logs in: {LOG_DIR}")
    print(f"Backtest log: {BACKTEST_LOG}")
    print(f"API log: {API_LOG}")
    print("\nPress Ctrl+C to stop monitoring")
    print("=" * 80 + "\n")
    
    backtest_position = 0
    api_position = 0
    
    try:
        while True:
            # مانیتور backtest.log
            if BACKTEST_LOG.exists():
                backtest_position, backtest_errors = monitor_log_file(BACKTEST_LOG, backtest_position)
                if backtest_errors:
                    print(f"\n[{time.strftime('%H:%M:%S')}] ERRORS in backtest.log:")
                    for error in backtest_errors[-5:]:  # آخرین 5 خطا
                        print(f"  {error[:200]}")
            
            # مانیتور api.log
            if API_LOG.exists():
                api_position, api_errors = monitor_log_file(API_LOG, api_position)
                if api_errors:
                    print(f"\n[{time.strftime('%H:%M:%S')}] ERRORS in api.log:")
                    for error in api_errors[-5:]:  # آخرین 5 خطا
                        print(f"  {error[:200]}")
            
            time.sleep(2)  # بررسی هر 2 ثانیه
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    main()


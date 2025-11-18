#!/usr/bin/env python
"""
Script to clear rate limit for localhost or specific IP
Usage:
    python clear_rate_limit.py
    python clear_rate_limit.py 127.0.0.1
    python clear_rate_limit.py --all
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.rate_limiter import rate_limiter, clear_rate_limit_for_ip

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            # Clear all rate limits
            count = len(rate_limiter.blocked_ips)
            rate_limiter.blocked_ips.clear()
            rate_limiter.requests.clear()
            print(f"✓ Cleared all rate limits ({count} blocked IPs)")
        else:
            # Clear for specific IP
            ip = sys.argv[1]
            clear_rate_limit_for_ip(ip)
            print(f"✓ Cleared rate limit for IP: {ip}")
    else:
        # Clear for localhost IPs by default
        localhost_ips = ['127.0.0.1', 'localhost', '::1', '0.0.0.0']
        for ip in localhost_ips:
            clear_rate_limit_for_ip(ip)
        print("✓ Cleared rate limits for localhost IPs")
        print(f"  Currently blocked IPs: {len(rate_limiter.blocked_ips)}")
        print(f"  Tracked IPs: {len(rate_limiter.requests)}")

if __name__ == '__main__':
    main()


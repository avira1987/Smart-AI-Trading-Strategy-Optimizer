# Script to clear rate limit for localhost
# Usage: .\clear_rate_limit.ps1
#        .\clear_rate_limit.ps1 --all
#        .\clear_rate_limit.ps1 127.0.0.1

Write-Host "Clearing rate limits..." -ForegroundColor Cyan

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "..\backend"

cd $backendPath

if ($args[0] -eq "--all") {
    python -c "import os, sys, django; sys.path.insert(0, '.'); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from api.rate_limiter import rate_limiter; count = len(rate_limiter.blocked_ips); rate_limiter.blocked_ips.clear(); rate_limiter.requests.clear(); print(f'✓ Cleared all rate limits ({count} blocked IPs)')"
} elseif ($args[0]) {
    $ip = $args[0]
    python -c "import os, sys, django; sys.path.insert(0, '.'); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from api.rate_limiter import clear_rate_limit_for_ip; clear_rate_limit_for_ip('$ip'); print(f'✓ Cleared rate limit for IP: $ip')"
} else {
    python -c "import os, sys, django; sys.path.insert(0, '.'); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from api.rate_limiter import rate_limiter, clear_rate_limit_for_ip; [clear_rate_limit_for_ip(ip) for ip in ['127.0.0.1', 'localhost', '::1', '0.0.0.0']]; print('✓ Cleared rate limits for localhost IPs'); print(f'  Currently blocked IPs: {len(rate_limiter.blocked_ips)}'); print(f'  Tracked IPs: {len(rate_limiter.requests)}')"
}

Write-Host "Done!" -ForegroundColor Green


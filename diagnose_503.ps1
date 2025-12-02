# Diagnose 503 Error
Write-Host "=== Diagnosing 503 Error ===" -ForegroundColor Cyan

Import-Module WebAdministration -ErrorAction SilentlyContinue

# Check Application Pool worker process
Write-Host "`n1. Application Pool Worker Process:" -ForegroundColor Yellow
$appPool = (Get-Item "IIS:\Sites\MyWebsite").applicationPool
$workerProcesses = Get-WebAppPoolState -Name $appPool
Write-Host "   Pool: $appPool" -ForegroundColor Cyan
Write-Host "   State: $($workerProcesses.Value)" -ForegroundColor Cyan

# Check if we can access ports from Application Pool context
Write-Host "`n2. Testing port access..." -ForegroundColor Yellow

# Try using IP instead of localhost
Write-Host "   Testing with 127.0.0.1 instead of localhost..." -ForegroundColor Cyan

# Update web.config to use 127.0.0.1 (already done, but let's verify)
$webConfigPath = "C:\inetpub\wwwroot\web.config"
if (Test-Path $webConfigPath) {
    $content = Get-Content $webConfigPath -Raw
    if ($content -match "127.0.0.1") {
        Write-Host "   web.config uses 127.0.0.1: OK" -ForegroundColor Green
    } else {
        Write-Host "   web.config needs update" -ForegroundColor Red
    }
}

# Check if ports are listening on all interfaces
Write-Host "`n3. Checking port bindings..." -ForegroundColor Yellow
$netstat3000 = netstat -an | Select-String ":3000"
$netstat8000 = netstat -an | Select-String ":8000"

Write-Host "   Port 3000 listeners:" -ForegroundColor Cyan
$netstat3000 | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }
Write-Host "   Port 8000 listeners:" -ForegroundColor Cyan
$netstat8000 | ForEach-Object { Write-Host "     $_" -ForegroundColor Gray }

# Try a different approach - use HTTP Redirect instead of Rewrite for testing
Write-Host "`n4. Creating test configuration..." -ForegroundColor Yellow

$testConfig = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="Backend API" enabled="true" stopProcessing="true">
                    <match url="^api/(.*)$" />
                    <action type="Rewrite" url="http://127.0.0.1:8000/api/{R:1}" logRewrittenUrl="true" />
                </rule>
                <rule name="Frontend" enabled="true" stopProcessing="true">
                    <match url="^(?!api/)(.*)$" />
                    <conditions>
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="http://127.0.0.1:3000/{R:1}" logRewrittenUrl="true" />
                </rule>
            </rules>
        </rewrite>
        <proxy enabled="true" preserveHostHeader="false" reverseRewriteHostInResponseHeaders="true" />
        <httpErrors errorMode="Detailed" />
    </system.webServer>
</configuration>
"@

Set-Content -Path $webConfigPath -Value $testConfig -Encoding UTF8
Write-Host "   Test configuration created" -ForegroundColor Green

# Restart Application Pool
Write-Host "`n5. Restarting Application Pool..." -ForegroundColor Yellow
Restart-WebAppPool -Name $appPool
Start-Sleep -Seconds 5

Write-Host "`n=== Diagnosis Complete ===" -ForegroundColor Cyan
Write-Host "`nIf still getting 503, the issue might be:" -ForegroundColor Yellow
Write-Host "   1. Application Pool cannot access localhost ports" -ForegroundColor White
Write-Host "   2. URL Rewrite rules are not matching correctly" -ForegroundColor White
Write-Host "   3. Frontend/Backend services are not running" -ForegroundColor White


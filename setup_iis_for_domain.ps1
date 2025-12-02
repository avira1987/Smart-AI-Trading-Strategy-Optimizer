# Setup IIS for Domain Access
Write-Host "=== Setting up IIS for Domain Access ===" -ForegroundColor Cyan

Import-Module WebAdministration -ErrorAction SilentlyContinue

# 1. Start IIS if not running
Write-Host "`n1. Starting IIS..." -ForegroundColor Yellow
$iisService = Get-Service -Name W3SVC -ErrorAction SilentlyContinue
if ($iisService.Status -ne "Running") {
    Start-Service -Name W3SVC
    Start-Sleep -Seconds 3
    Write-Host "   IIS started" -ForegroundColor Green
} else {
    Write-Host "   IIS already running" -ForegroundColor Green
}

# 2. Check and configure MyWebsite
Write-Host "`n2. Configuring MyWebsite..." -ForegroundColor Yellow
$site = Get-Website -Name "MyWebsite" -ErrorAction SilentlyContinue

if (-not $site) {
    Write-Host "   Site 'MyWebsite' not found. Creating..." -ForegroundColor Yellow
    
    # Create Application Pool
    $appPoolName = "MyAibazAppPool"
    if (-not (Test-Path "IIS:\AppPools\$appPoolName")) {
        New-WebAppPool -Name $appPoolName
        Set-ItemProperty "IIS:\AppPools\$appPoolName" -Name managedRuntimeVersion -Value ""
    }
    
    # Create Site
    $sitePath = "C:\inetpub\wwwroot"
    if (-not (Test-Path $sitePath)) {
        New-Item -ItemType Directory -Path $sitePath -Force | Out-Null
    }
    
    New-Website -Name "MyWebsite" -Port 80 -PhysicalPath $sitePath -ApplicationPool $appPoolName
    Write-Host "   Site created" -ForegroundColor Green
} else {
    Write-Host "   Site exists" -ForegroundColor Green
}

# 3. Add bindings for domain
Write-Host "`n3. Adding domain bindings..." -ForegroundColor Yellow
$bindings = Get-WebBinding -Name "MyWebsite"

# Check if domain binding exists
$domainBinding = $bindings | Where-Object { $_.BindingInformation -like "*myaibaz.ir*" }
if (-not $domainBinding) {
    New-WebBinding -Name "MyWebsite" -HostHeader "myaibaz.ir" -Port 80 -Protocol http
    Write-Host "   Added binding: myaibaz.ir:80" -ForegroundColor Green
} else {
    Write-Host "   Domain binding already exists" -ForegroundColor Green
}

# Check if www binding exists
$wwwBinding = $bindings | Where-Object { $_.BindingInformation -like "*www.myaibaz.ir*" }
if (-not $wwwBinding) {
    New-WebBinding -Name "MyWebsite" -HostHeader "www.myaibaz.ir" -Port 80 -Protocol http
    Write-Host "   Added binding: www.myaibaz.ir:80" -ForegroundColor Green
} else {
    Write-Host "   www binding already exists" -ForegroundColor Green
}

# 4. Update web.config for reverse proxy
Write-Host "`n4. Updating web.config..." -ForegroundColor Yellow
$webConfigPath = "C:\inetpub\wwwroot\web.config"

$webConfigContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="Backend API" stopProcessing="true">
                    <match url="^api/(.*)$" />
                    <action type="Rewrite" url="http://191.101.113.163:8000/api/{R:1}" />
                </rule>
                <rule name="Frontend" stopProcessing="true">
                    <match url="(.*)" />
                    <conditions>
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="http://191.101.113.163:3000/{R:1}" />
                </rule>
            </rules>
        </rewrite>
        <proxy enabled="true" preserveHostHeader="false" reverseRewriteHostInResponseHeaders="true" />
        <defaultDocument>
            <files>
                <clear />
            </files>
        </defaultDocument>
    </system.webServer>
</configuration>
"@

Set-Content -Path $webConfigPath -Value $webConfigContent -Encoding UTF8
Write-Host "   web.config updated" -ForegroundColor Green

# 5. Start Site
Write-Host "`n5. Starting Site..." -ForegroundColor Yellow
$siteState = (Get-WebsiteState -Name "MyWebsite").Value
if ($siteState -ne "Started") {
    Start-Website -Name "MyWebsite"
    Write-Host "   Site started" -ForegroundColor Green
} else {
    Write-Host "   Site already started" -ForegroundColor Green
}

# 6. Restart Application Pool
Write-Host "`n6. Restarting Application Pool..." -ForegroundColor Yellow
$appPool = (Get-Item "IIS:\Sites\MyWebsite").applicationPool
Restart-WebAppPool -Name $appPool
Start-Sleep -Seconds 3
Write-Host "   Application Pool restarted" -ForegroundColor Green

# 7. Enable Server Variables
Write-Host "`n7. Enabling Server Variables..." -ForegroundColor Yellow
$allowedVars = @("HTTP_X_FORWARDED_PROTO", "HTTP_X_FORWARDED_HOST", "HTTP_X_REAL_IP")
foreach ($var in $allowedVars) {
    try {
        Add-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" -Filter "system.webServer/rewrite/allowedServerVariables" -Name "." -Value @{name=$var} -ErrorAction SilentlyContinue
    } catch {
        # Variable might already exist
    }
}
Write-Host "   Server Variables enabled" -ForegroundColor Green

# 8. Enable Proxy
Write-Host "`n8. Enabling Proxy..." -ForegroundColor Yellow
try {
    Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" -Filter "system.webServer/proxy" -Name "enabled" -Value $true -ErrorAction SilentlyContinue
    Write-Host "   Proxy enabled" -ForegroundColor Green
} catch {
    Write-Host "   Error enabling proxy" -ForegroundColor Yellow
}

# 9. Open Firewall Port 80
Write-Host "`n9. Opening Firewall Port 80..." -ForegroundColor Yellow
$firewallRule = Get-NetFirewallRule -DisplayName "HTTP Port 80" -ErrorAction SilentlyContinue
if (-not $firewallRule) {
    New-NetFirewallRule -DisplayName "HTTP Port 80" -Direction Inbound -LocalPort 80 -Protocol TCP -Action Allow | Out-Null
    Write-Host "   Firewall rule created" -ForegroundColor Green
} else {
    Write-Host "   Firewall rule already exists" -ForegroundColor Green
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "`nTesting access..." -ForegroundColor Yellow

# Test
Start-Sleep -Seconds 2
try {
    $test = Invoke-WebRequest -Uri "http://191.101.113.163" -UseBasicParsing -TimeoutSec 10
    Write-Host "   IP Test: SUCCESS (Status: $($test.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   IP Test: FAILED - $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $test2 = Invoke-WebRequest -Uri "http://myaibaz.ir" -UseBasicParsing -TimeoutSec 10
    Write-Host "   Domain Test: SUCCESS (Status: $($test2.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "   Domain Test: FAILED - $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Note: Domain might need DNS propagation time" -ForegroundColor Yellow
}

Write-Host "`nAccess URLs:" -ForegroundColor Cyan
Write-Host "   http://191.101.113.163" -ForegroundColor White
Write-Host "   http://myaibaz.ir" -ForegroundColor White




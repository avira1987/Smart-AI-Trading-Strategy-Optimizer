# Fix 503 Error
Write-Host "=== Fixing 503 Error ===" -ForegroundColor Cyan

Import-Module WebAdministration -ErrorAction SilentlyContinue

# 1. Check Application Pool Identity
Write-Host "`n1. Checking Application Pool Identity..." -ForegroundColor Yellow
$appPool = (Get-Item "IIS:\Sites\MyWebsite").applicationPool
$poolConfig = Get-Item "IIS:\AppPools\$appPool"
$identity = $poolConfig.processModel.identityType
Write-Host "   Application Pool: $appPool" -ForegroundColor Cyan
Write-Host "   Identity: $identity" -ForegroundColor Cyan

# 2. Try to change to ApplicationPoolIdentity if needed
if ($identity -ne "ApplicationPoolIdentity") {
    Write-Host "   Changing to ApplicationPoolIdentity..." -ForegroundColor Yellow
    Set-ItemProperty "IIS:\AppPools\$appPool" -Name processModel.identityType -Value ApplicationPoolIdentity
}

# 3. Check if URL Rewrite module is installed
Write-Host "`n2. Checking URL Rewrite Module..." -ForegroundColor Yellow
$rewriteModule = Get-WebGlobalModule | Where-Object { $_.Name -eq "RewriteModule" }
if ($rewriteModule) {
    Write-Host "   URL Rewrite Module: INSTALLED" -ForegroundColor Green
} else {
    Write-Host "   URL Rewrite Module: NOT INSTALLED" -ForegroundColor Red
    Write-Host "   Please install from: https://www.iis.net/downloads/microsoft/url-rewrite" -ForegroundColor Yellow
}

# 4. Check ARR module
Write-Host "`n3. Checking ARR Module..." -ForegroundColor Yellow
$arrModule = Get-WebGlobalModule | Where-Object { $_.Name -eq "ApplicationRequestRouting" }
if ($arrModule) {
    Write-Host "   ARR Module: INSTALLED" -ForegroundColor Green
} else {
    Write-Host "   ARR Module: NOT INSTALLED" -ForegroundColor Red
    Write-Host "   Please install from: https://www.iis.net/downloads/microsoft/application-request-routing" -ForegroundColor Yellow
}

# 5. Create a simpler web.config without rewrite (using HTTP Redirect as fallback)
Write-Host "`n4. Creating alternative configuration..." -ForegroundColor Yellow
$webConfigPath = "C:\inetpub\wwwroot\web.config"

# Backup current config
if (Test-Path $webConfigPath) {
    Copy-Item $webConfigPath "$webConfigPath.backup" -Force
    Write-Host "   Backup created: web.config.backup" -ForegroundColor Green
}

# Create a simpler config that might work better
$simpleConfig = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <defaultDocument>
            <files>
                <clear />
            </files>
        </defaultDocument>
        <rewrite>
            <rules>
                <rule name="Backend API Proxy" stopProcessing="true">
                    <match url="^api/(.*)$" />
                    <action type="Rewrite" url="http://127.0.0.1:8000/api/{R:1}" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="http" />
                        <set name="HTTP_X_FORWARDED_HOST" value="{HTTP_HOST}" />
                    </serverVariables>
                </rule>
                <rule name="Frontend Proxy" stopProcessing="true">
                    <match url="(.*)" />
                    <conditions logicalGrouping="MatchAll">
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="http://127.0.0.1:3000/{R:1}" />
                </rule>
            </rules>
        </rewrite>
        <proxy enabled="true" preserveHostHeader="false" reverseRewriteHostInResponseHeaders="true" />
        <httpErrors errorMode="Detailed" />
    </system.webServer>
</configuration>
"@

Set-Content -Path $webConfigPath -Value $simpleConfig -Encoding UTF8
Write-Host "   New configuration created" -ForegroundColor Green

# 6. Enable Server Variables
Write-Host "`n5. Enabling Server Variables..." -ForegroundColor Yellow
$allowedVars = @("HTTP_X_FORWARDED_PROTO", "HTTP_X_FORWARDED_HOST", "HTTP_X_REAL_IP")
foreach ($var in $allowedVars) {
    try {
        Add-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" -Filter "system.webServer/rewrite/allowedServerVariables" -Name "." -Value @{name=$var} -ErrorAction SilentlyContinue
        Write-Host "   $var : Enabled" -ForegroundColor Green
    } catch {
        # Variable might already exist
    }
}

# 7. Restart everything
Write-Host "`n6. Restarting services..." -ForegroundColor Yellow
Restart-WebAppPool -Name $appPool
Start-Sleep -Seconds 3
iisreset /noforce
Start-Sleep -Seconds 5

Write-Host "`n=== Fix Applied ===" -ForegroundColor Cyan
Write-Host "`nPlease test again:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White


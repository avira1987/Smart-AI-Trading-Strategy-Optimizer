# Fix IIS Configuration
Write-Host "=== Fixing IIS Configuration ===" -ForegroundColor Cyan

Import-Module WebAdministration -ErrorAction SilentlyContinue

# Check Application Pools
Write-Host "`n1. Checking Application Pools..." -ForegroundColor Yellow
$appPools = Get-ChildItem IIS:\AppPools
foreach ($pool in $appPools) {
    $state = (Get-WebAppPoolState -Name $pool.Name).Value
    Write-Host "   $($pool.Name): $state" -ForegroundColor $(if ($state -eq "Started") { "Green" } else { "Red" })
    
    if ($state -ne "Started") {
        Write-Host "   Starting..." -ForegroundColor Yellow
        Start-WebAppPool -Name $pool.Name
        Start-Sleep -Seconds 2
    }
}

# Check Site
Write-Host "`n2. Checking Site..." -ForegroundColor Yellow
$site = Get-Website -Name "MyWebsite"
if ($site) {
    Write-Host "   Site: $($site.Name)" -ForegroundColor Green
    Write-Host "   State: $((Get-WebsiteState -Name $site.Name).Value)" -ForegroundColor Green
    Write-Host "   Physical Path: $($site.physicalPath)" -ForegroundColor Green
    
    $siteAppPool = (Get-Item "IIS:\Sites\$($site.Name)").applicationPool
    Write-Host "   Application Pool: $siteAppPool" -ForegroundColor Cyan
    
    $poolState = (Get-WebAppPoolState -Name $siteAppPool).Value
    if ($poolState -ne "Started") {
        Write-Host "   Starting Application Pool..." -ForegroundColor Red
        Start-WebAppPool -Name $siteAppPool
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host "   Site 'MyWebsite' not found!" -ForegroundColor Red
}

# Check and create web.config
Write-Host "`n3. Checking web.config..." -ForegroundColor Yellow
$sitePath = $site.physicalPath
if (-not $sitePath) {
    $sitePath = "C:\inetpub\wwwroot"
}

$webConfigPath = Join-Path $sitePath "web.config"

if (Test-Path $webConfigPath) {
    Write-Host "   web.config exists" -ForegroundColor Green
    $content = Get-Content $webConfigPath -Raw
    Write-Host "   Content:" -ForegroundColor Cyan
    Write-Host $content -ForegroundColor Gray
} else {
    Write-Host "   Creating web.config..." -ForegroundColor Yellow
    
    $webConfigContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="Backend API" stopProcessing="true">
                    <match url="^api/(.*)$" />
                    <action type="Rewrite" url="http://127.0.0.1:8000/api/{R:1}" />
                </rule>
                <rule name="Frontend" stopProcessing="true">
                    <match url="(.*)" />
                    <conditions>
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="http://127.0.0.1:3000/{R:1}" />
                </rule>
            </rules>
        </rewrite>
        <proxy enabled="true" preserveHostHeader="false" reverseRewriteHostInResponseHeaders="true" />
    </system.webServer>
</configuration>
"@
    
    Set-Content -Path $webConfigPath -Value $webConfigContent -Encoding UTF8
    Write-Host "   web.config created" -ForegroundColor Green
}

# Check ports
Write-Host "`n4. Checking ports..." -ForegroundColor Yellow
$port3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
$port8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue

Write-Host "   Port 3000 (Frontend): " -NoNewline
if ($port3000.TcpTestSucceeded) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT AVAILABLE" -ForegroundColor Red
}

Write-Host "   Port 8000 (Backend): " -NoNewline
if ($port8000.TcpTestSucceeded) {
    Write-Host "OK" -ForegroundColor Green
} else {
    Write-Host "NOT AVAILABLE" -ForegroundColor Red
}

# Enable Proxy in ARR
Write-Host "`n5. Enabling Proxy in ARR..." -ForegroundColor Yellow
try {
    $filter = "system.webServer/proxy"
    Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" -Filter $filter -Name "enabled" -Value $true -ErrorAction SilentlyContinue
    Write-Host "   Proxy enabled" -ForegroundColor Green
} catch {
    Write-Host "   Error enabling proxy" -ForegroundColor Yellow
}

# Restart Application Pool
Write-Host "`n6. Restarting Application Pool..." -ForegroundColor Yellow
if ($site) {
    $siteAppPool = (Get-Item "IIS:\Sites\$($site.Name)").applicationPool
    Restart-WebAppPool -Name $siteAppPool
    Start-Sleep -Seconds 3
    Write-Host "   Application Pool restarted" -ForegroundColor Green
}

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "`nTest URLs:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White
Write-Host "   http://191.101.113.163" -ForegroundColor White


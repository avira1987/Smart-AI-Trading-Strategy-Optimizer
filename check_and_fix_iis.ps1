# اسکریپت بررسی و رفع مشکل IIS
Write-Host "=== بررسی و رفع مشکل IIS ===" -ForegroundColor Cyan

# Import Module
Import-Module WebAdministration -ErrorAction SilentlyContinue

# بررسی Application Pools
Write-Host "`n1. بررسی Application Pools..." -ForegroundColor Yellow
$appPools = Get-ChildItem IIS:\AppPools
foreach ($pool in $appPools) {
    $state = (Get-WebAppPoolState -Name $pool.Name).Value
    Write-Host "   $($pool.Name): $state" -ForegroundColor $(if ($state -eq "Started") { "Green" } else { "Red" })
    
    if ($state -ne "Started") {
        Write-Host "   ⚠️ در حال Start کردن..." -ForegroundColor Yellow
        Start-WebAppPool -Name $pool.Name
        Start-Sleep -Seconds 2
        $newState = (Get-WebAppPoolState -Name $pool.Name).Value
        Write-Host "   ✓ وضعیت جدید: $newState" -ForegroundColor $(if ($newState -eq "Started") { "Green" } else { "Red" })
    }
}

# بررسی Site
Write-Host "`n2. بررسی Site..." -ForegroundColor Yellow
$site = Get-Website -Name "MyWebsite"
if ($site) {
    Write-Host "   Site: $($site.Name)" -ForegroundColor Green
    Write-Host "   State: $((Get-WebsiteState -Name $site.Name).Value)" -ForegroundColor Green
    Write-Host "   Physical Path: $($site.physicalPath)" -ForegroundColor Green
    
    # بررسی Application Pool مربوط به Site
    $siteAppPool = (Get-Item "IIS:\Sites\$($site.Name)").applicationPool
    Write-Host "   Application Pool: $siteAppPool" -ForegroundColor Cyan
    
    # بررسی وضعیت Application Pool
    $poolState = (Get-WebAppPoolState -Name $siteAppPool).Value
    if ($poolState -ne "Started") {
        Write-Host "   ⚠️ Application Pool متوقف است! در حال Start..." -ForegroundColor Red
        Start-WebAppPool -Name $siteAppPool
        Start-Sleep -Seconds 2
    }
} else {
    Write-Host "   ✗ Site 'MyWebsite' پیدا نشد!" -ForegroundColor Red
}

# بررسی و ساخت web.config
Write-Host "`n3. بررسی web.config..." -ForegroundColor Yellow
$sitePath = $site.physicalPath
if (-not $sitePath) {
    $sitePath = "C:\inetpub\wwwroot"
}

$webConfigPath = Join-Path $sitePath "web.config"

if (Test-Path $webConfigPath) {
    Write-Host "   ✓ web.config موجود است" -ForegroundColor Green
    $content = Get-Content $webConfigPath -Raw
    Write-Host "   محتوا:" -ForegroundColor Cyan
    Write-Host $content -ForegroundColor Gray
} else {
    Write-Host "   ⚠️ web.config موجود نیست! در حال ساخت..." -ForegroundColor Yellow
    
    $webConfigContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <!-- Backend API -->
                <rule name="Backend API" stopProcessing="true">
                    <match url="^api/(.*)$" />
                    <action type="Rewrite" url="http://127.0.0.1:8000/api/{R:1}" />
                </rule>
                
                <!-- Frontend -->
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
    Write-Host "   ✓ web.config ساخته شد" -ForegroundColor Green
}

# بررسی پورت‌ها
Write-Host "`n4. بررسی پورت‌ها..." -ForegroundColor Yellow
$port3000 = Test-NetConnection -ComputerName localhost -Port 3000 -WarningAction SilentlyContinue
$port8000 = Test-NetConnection -ComputerName localhost -Port 8000 -WarningAction SilentlyContinue

Write-Host "   پورت 3000 (Frontend): " -NoNewline
if ($port3000.TcpTestSucceeded) {
    Write-Host "✓ در دسترس" -ForegroundColor Green
} else {
    Write-Host "✗ در دسترس نیست" -ForegroundColor Red
}

Write-Host "   پورت 8000 (Backend): " -NoNewline
if ($port8000.TcpTestSucceeded) {
    Write-Host "✓ در دسترس" -ForegroundColor Green
} else {
    Write-Host "✗ در دسترس نیست" -ForegroundColor Red
}

# فعال‌سازی Proxy در ARR
Write-Host "`n5. فعال‌سازی Proxy در ARR..." -ForegroundColor Yellow
try {
    $filter = "system.webServer/proxy"
    Set-WebConfigurationProperty -PSPath "MACHINE/WEBROOT/APPHOST" -Filter $filter -Name "enabled" -Value $true -ErrorAction SilentlyContinue
    Write-Host "   Proxy فعال شد" -ForegroundColor Green
} catch {
    Write-Host "   خطا در فعال‌سازی Proxy" -ForegroundColor Yellow
}

# Restart Application Pool
Write-Host "`n6. Restart Application Pool..." -ForegroundColor Yellow
if ($site) {
    $siteAppPool = (Get-Item "IIS:\Sites\$($site.Name)").applicationPool
    Restart-WebAppPool -Name $siteAppPool
    Start-Sleep -Seconds 3
    Write-Host "   ✓ Application Pool Restart شد" -ForegroundColor Green
}

Write-Host "`n=== بررسی کامل شد ===" -ForegroundColor Cyan
Write-Host "`nبرای تست:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor White
Write-Host "   http://191.101.113.163" -ForegroundColor White


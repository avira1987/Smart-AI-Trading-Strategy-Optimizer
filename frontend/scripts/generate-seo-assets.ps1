# اسکریپت PowerShell برای تولید فایل‌های SEO با استفاده از ImageMagick
# این اسکریپت فایل‌های og-image.jpg و favicon PNG را تولید می‌کند
#
# نیازمندی‌ها:
# - ImageMagick باید نصب باشد (https://imagemagick.org/)
# - یا از اسکریپت Node.js استفاده کنید: node scripts/generate-seo-assets.js
#
# استفاده:
# .\scripts\generate-seo-assets.ps1

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
$publicDir = Join-Path $projectRoot "public"
$faviconSvg = Join-Path $publicDir "favicon.svg"

Write-Host "شروع تولید فایل‌های SEO..." -ForegroundColor Cyan
Write-Host ""

# بررسی وجود ImageMagick
$magickPath = Get-Command magick -ErrorAction SilentlyContinue
if (-not $magickPath) {
    Write-Host "❌ خطا: ImageMagick یافت نشد!" -ForegroundColor Red
    Write-Host "لطفاً ImageMagick را نصب کنید:" -ForegroundColor Yellow
    Write-Host "  - دانلود: https://imagemagick.org/script/download.php" -ForegroundColor Gray
    Write-Host "  - یا از Chocolatey: choco install imagemagick" -ForegroundColor Gray
    Write-Host ""
    Write-Host "یا از اسکریپت Node.js استفاده کنید:" -ForegroundColor Yellow
    Write-Host "  npm install --save-dev sharp" -ForegroundColor Gray
    Write-Host "  node scripts/generate-seo-assets.js" -ForegroundColor Gray
    exit 1
}

# بررسی وجود favicon.svg
if (-not (Test-Path $faviconSvg)) {
    Write-Host "⚠ فایل favicon.svg یافت نشد: $faviconSvg" -ForegroundColor Yellow
    Write-Host "فقط og-image.jpg ایجاد می‌شود..." -ForegroundColor Yellow
    Write-Host ""
}

# ایجاد og-image.jpg با استفاده از ImageMagick
Write-Host "در حال ایجاد og-image.jpg..." -ForegroundColor Yellow
$ogImagePath = Join-Path $publicDir "og-image.jpg"
$ogImageSvg = Join-Path $publicDir "og-image-temp.svg"

# ایجاد SVG موقت برای og-image
$svgContent = @"
<svg width="1200" height="630" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#111827;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1f2937;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  
  <!-- شبکه عصبی AI -->
  <g opacity="0.3">
    <circle cx="200" cy="150" r="8" fill="#3b82f6"/>
    <circle cx="300" cy="120" r="8" fill="#3b82f6"/>
    <circle cx="400" cy="150" r="8" fill="#3b82f6"/>
    <circle cx="250" cy="200" r="8" fill="#3b82f6"/>
    <circle cx="350" cy="200" r="8" fill="#3b82f6"/>
    <line x1="200" y1="150" x2="300" y2="120" stroke="#3b82f6" stroke-width="2" opacity="0.5"/>
    <line x1="300" y1="120" x2="400" y2="150" stroke="#3b82f6" stroke-width="2" opacity="0.5"/>
    <line x1="200" y1="150" x2="250" y2="200" stroke="#3b82f6" stroke-width="2" opacity="0.5"/>
    <line x1="400" y1="150" x2="350" y2="200" stroke="#3b82f6" stroke-width="2" opacity="0.5"/>
  </g>
  
  <!-- نمودار معاملاتی -->
  <polyline points="100,450 200,400 300,350 400,300 500,280 600,250 700,220 800,200 900,180 1000,160 1100,140"
            fill="none" stroke="#10b981" stroke-width="4" opacity="0.8"/>
  
  <!-- عنوان -->
  <text x="600" y="280" font-family="Arial, sans-serif" font-size="64" font-weight="bold" 
        fill="#ffffff" text-anchor="middle">ترید با هوش مصنوعی</text>
  
  <!-- زیرعنوان -->
  <text x="600" y="340" font-family="Arial, sans-serif" font-size="32" 
        fill="#9ca3af" text-anchor="middle">سامانه پیشرفته معاملات هوشمند</text>
  
  <!-- لوگو -->
  <text x="600" y="520" font-family="Arial, sans-serif" font-size="24" 
        fill="#3b82f6" text-anchor="middle">MyAibaz</text>
</svg>
"@

$svgContent | Out-File -FilePath $ogImageSvg -Encoding UTF8

try {
    magick convert -background none "$ogImageSvg" -quality 90 "$ogImagePath"
    Remove-Item $ogImageSvg -ErrorAction SilentlyContinue
    Write-Host "✓ og-image.jpg با موفقیت ایجاد شد" -ForegroundColor Green
} catch {
    Write-Host "❌ خطا در ایجاد og-image.jpg: $_" -ForegroundColor Red
    if (Test-Path $ogImageSvg) {
        Remove-Item $ogImageSvg -ErrorAction SilentlyContinue
    }
    exit 1
}

Write-Host ""

# ایجاد favicon PNG files
if (Test-Path $faviconSvg) {
    Write-Host "در حال ایجاد فایل‌های favicon PNG..." -ForegroundColor Yellow
    
    $faviconSizes = @(
        @{Name="favicon-16x16.png"; Size=16},
        @{Name="favicon-32x32.png"; Size=32},
        @{Name="apple-touch-icon.png"; Size=180},
        @{Name="favicon-192x192.png"; Size=192},
        @{Name="favicon-512x512.png"; Size=512}
    )
    
    foreach ($item in $faviconSizes) {
        $outputPath = Join-Path $publicDir $item.Name
        try {
            magick convert -background none -resize "${($item.Size)}x$($item.Size)" "$faviconSvg" "$outputPath"
            Write-Host "✓ $($item.Name) ایجاد شد" -ForegroundColor Green
        } catch {
            Write-Host "⚠ خطا در ایجاد $($item.Name): $_" -ForegroundColor Yellow
        }
    }
    
    Write-Host ""
}

Write-Host "✅ تمام فایل‌های SEO با موفقیت تولید شدند!" -ForegroundColor Green

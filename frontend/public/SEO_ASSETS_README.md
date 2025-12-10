# راهنمای تولید فایل‌های SEO

این راهنما نحوه تولید فایل‌های مورد نیاز برای SEO را توضیح می‌دهد.

## فایل‌های مورد نیاز

### 1. og-image.jpg
تصویر Open Graph برای نمایش در شبکه‌های اجتماعی (Facebook, Twitter, LinkedIn و غیره)
- **ابعاد**: 1200x630 پیکسل
- **فرمت**: JPG
- **مسیر**: `frontend/public/og-image.jpg`

### 2. Favicon PNG Files (اختیاری)
نسخه‌های PNG از favicon.svg برای سازگاری بهتر:
- `favicon-16x16.png` (16x16)
- `favicon-32x32.png` (32x32)
- `apple-touch-icon.png` (180x180)
- `favicon-192x192.png` (192x192) - برای PWA
- `favicon-512x512.png` (512x512) - برای PWA

## روش‌های تولید

### روش 1: استفاده از اسکریپت Node.js (توصیه می‌شود)

این روش نیاز به نصب `sharp` دارد:

```bash
cd frontend
npm install --save-dev sharp
node scripts/generate-seo-assets.js
```

**مزایا:**
- سریع و قابل اعتماد
- نیازی به نصب نرم‌افزار اضافی ندارد
- به صورت خودکار تمام فایل‌ها را تولید می‌کند

### روش 2: استفاده از اسکریپت PowerShell (با ImageMagick)

این روش نیاز به نصب ImageMagick دارد:

```powershell
# نصب ImageMagick (با Chocolatey)
choco install imagemagick

# یا دانلود از:
# https://imagemagick.org/script/download.php

# اجرای اسکریپت
cd frontend
.\scripts\generate-seo-assets.ps1
```

### روش 3: تولید دستی

#### تولید og-image.jpg

1. **استفاده از ابزارهای آنلاین:**
   - [Canva](https://www.canva.com/) - قالب‌های آماده Open Graph
   - [Bannerbear](https://www.bannerbear.com/) - تولید خودکار
   - [og-image.vercel.app](https://og-image.vercel.app/) - تولید سریع

2. **استفاده از نرم‌افزارهای طراحی:**
   - Adobe Photoshop
   - GIMP (رایگان)
   - Figma

3. **مشخصات تصویر:**
   - ابعاد: 1200x630 پیکسل
   - فرمت: JPG (کیفیت 90%)
   - محتوا: عنوان "ترید با هوش مصنوعی"، لوگو، و طراحی مرتبط با برند

#### تولید Favicon PNG Files

از فایل `favicon.svg` موجود استفاده کنید:

1. **ابزارهای آنلاین:**
   - [CloudConvert](https://cloudconvert.com/svg-to-png)
   - [Convertio](https://convertio.co/svg-png/)
   - [RealFaviconGenerator](https://realfavicongenerator.net/)

2. **ImageMagick (Command Line):**
   ```bash
   magick convert -background none -resize 16x16 favicon.svg favicon-16x16.png
   magick convert -background none -resize 32x32 favicon.svg favicon-32x32.png
   magick convert -background none -resize 180x180 favicon.svg apple-touch-icon.png
   magick convert -background none -resize 192x192 favicon.svg favicon-192x192.png
   magick convert -background none -resize 512x512 favicon.svg favicon-512x512.png
   ```

## بررسی فایل‌های تولید شده

پس از تولید فایل‌ها، می‌توانید آنها را با ابزارهای زیر بررسی کنید:

1. **Open Graph Preview:**
   - [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
   - [Twitter Card Validator](https://cards-dev.twitter.com/validator)
   - [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/)

2. **Favicon Checker:**
   - [Favicon Checker](https://realfavicongenerator.net/favicon_checker)

## فعال‌سازی فایل‌ها در کد

پس از تولید فایل‌ها:

1. **برای og-image.jpg:**
   - فایل باید در `frontend/public/og-image.jpg` قرار گیرد
   - به صورت خودکار در `index.html` و کامپوننت `SEO.tsx` استفاده می‌شود

2. **برای Favicon PNG Files:**
   - فایل‌ها باید در `frontend/public/` قرار گیرند
   - کامنت‌های مربوطه در `index.html` را uncomment کنید
   - فایل‌های PNG را به `site.webmanifest` اضافه کنید

## نکات مهم

1. **og-image.jpg:**
   - باید حتماً وجود داشته باشد (برای SEO و شبکه‌های اجتماعی)
   - ابعاد دقیق 1200x630 را رعایت کنید
   - از متن فارسی با فونت مناسب استفاده کنید

2. **Favicon PNG Files:**
   - اختیاری هستند (SVG در مرورگرهای مدرن کافی است)
   - برای سازگاری با iOS و PWA توصیه می‌شوند

3. **بهینه‌سازی:**
   - فایل‌های تصویری را فشرده کنید
   - از ابزارهایی مانند [TinyPNG](https://tinypng.com/) استفاده کنید

## عیب‌یابی

### خطا: "sharp نصب نشده"
```bash
npm install --save-dev sharp
```

### خطا: "ImageMagick یافت نشد"
- ImageMagick را نصب کنید یا از روش Node.js استفاده کنید

### تصویر og-image نمایش داده نمی‌شود
- بررسی کنید فایل در مسیر صحیح قرار دارد
- Cache مرورگر را پاک کنید
- از ابزارهای Facebook/Twitter برای بررسی استفاده کنید

## پشتیبانی

برای سوالات و مشکلات، به مستندات پروژه مراجعه کنید.

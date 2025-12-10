# راهنمای سریع تنظیم SEO

## 🚀 تولید فایل‌های SEO (گام به گام)

### گام 1: نصب وابستگی‌ها

```bash
cd frontend
npm install --save-dev sharp
```

### گام 2: اجرای اسکریپت تولید

```bash
npm run generate-seo
```

یا مستقیماً:

```bash
node scripts/generate-seo-assets.js
```

### گام 3: بررسی فایل‌های تولید شده

پس از اجرای اسکریپت، فایل‌های زیر باید در `frontend/public/` ایجاد شوند:

- ✅ `og-image.jpg` (1200x630)
- ✅ `favicon-16x16.png`
- ✅ `favicon-32x32.png`
- ✅ `apple-touch-icon.png`
- ✅ `favicon-192x192.png`
- ✅ `favicon-512x512.png`

### گام 4: فعال‌سازی Favicon PNG Files

پس از تولید فایل‌ها، کامنت‌های مربوطه در `index.html` را uncomment کنید:

```html
<!-- در frontend/index.html -->
<link rel="alternate icon" type="image/png" href="/favicon.png" />
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png" />
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png" />
```

و در `site.webmanifest`:

```json
{
  "icons": [
    {
      "src": "/favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml",
      "purpose": "any maskable"
    },
    {
      "src": "/favicon-192x192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/favicon-512x512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

## 🔍 بررسی و تست

### بررسی Open Graph Image

1. **Facebook:**
   - https://developers.facebook.com/tools/debug/
   - URL سایت را وارد کنید و "Scrape Again" بزنید

2. **Twitter:**
   - https://cards-dev.twitter.com/validator
   - URL سایت را وارد کنید

3. **LinkedIn:**
   - https://www.linkedin.com/post-inspector/
   - URL سایت را وارد کنید

### بررسی Favicon

- فایل‌ها را در `frontend/public/` بررسی کنید
- در مرورگر، آیکون favicon را در تب بررسی کنید
- از [Favicon Checker](https://realfavicongenerator.net/favicon_checker) استفاده کنید

## ⚠️ مشکلات رایج

### خطا: "sharp نصب نشده"
```bash
npm install --save-dev sharp
```

### خطا: "Cannot find module 'sharp'"
```bash
npm install --save-dev sharp
cd scripts
node generate-seo-assets.js
```

### تصویر og-image نمایش داده نمی‌شود
- بررسی کنید فایل در `frontend/public/og-image.jpg` وجود دارد
- Cache مرورگر را پاک کنید
- از ابزارهای Facebook/Twitter برای بررسی استفاده کنید

## 📚 مستندات بیشتر

برای اطلاعات بیشتر، به فایل `frontend/public/SEO_ASSETS_README.md` مراجعه کنید.

## 🎨 سفارشی‌سازی

اگر می‌خواهید og-image را سفارشی کنید:

1. فایل `scripts/generate-seo-assets.js` را باز کنید
2. بخش SVG را ویرایش کنید (رنگ‌ها، متن، طراحی)
3. اسکریپت را دوباره اجرا کنید

یا می‌توانید از ابزارهای طراحی مانند Canva یا Figma استفاده کنید و فایل را به صورت دستی ایجاد کنید.

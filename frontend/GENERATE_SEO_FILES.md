# راهنمای تولید فایل‌های SEO

## وضعیت فعلی

✅ فایل `og-image.svg` در `frontend/public/` ایجاد شده است
⚠️ نیاز به تبدیل به `og-image.jpg` دارد

## گام بعدی: تبدیل SVG به JPG

### سریع‌ترین روش (اگر ImageMagick نصب است):

```powershell
cd frontend/public
magick convert -background none og-image.svg -quality 90 og-image.jpg
```

### روش جایگزین (ابزارهای آنلاین):

1. فایل `frontend/public/og-image.svg` را باز کنید
2. به یکی از سایت‌های زیر بروید:
   - https://cloudconvert.com/svg-to-jpg
   - https://convertio.co/svg-jpg/
3. فایل SVG را آپلود کنید
4. فایل JPG را دانلود کنید
5. نام آن را به `og-image.jpg` تغییر دهید
6. در `frontend/public/` قرار دهید

## تولید Favicon PNG Files (اختیاری)

اگر می‌خواهید favicon PNG files را نیز تولید کنید:

### با ImageMagick:

```powershell
cd frontend/public
magick convert -background none -resize 16x16 favicon.svg favicon-16x16.png
magick convert -background none -resize 32x32 favicon.svg favicon-32x32.png
magick convert -background none -resize 180x180 favicon.svg apple-touch-icon.png
magick convert -background none -resize 192x192 favicon.svg favicon-192x192.png
magick convert -background none -resize 512x512 favicon.svg favicon-512x512.png
```

### با ابزارهای آنلاین:

از [RealFaviconGenerator](https://realfavicongenerator.net/) استفاده کنید و فایل `favicon.svg` را آپلود کنید.

## فعال‌سازی Favicon PNG Files

پس از تولید فایل‌ها، کامنت‌های مربوطه در `frontend/index.html` را uncomment کنید.

## بررسی نهایی

پس از تولید `og-image.jpg`:
- ✅ فایل باید در `frontend/public/og-image.jpg` باشد
- ✅ ابعاد: 1200x630 پیکسل
- ✅ فرمت: JPG
- ✅ کیفیت: 90%

برای بررسی:
- از [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) استفاده کنید
- URL سایت را وارد کنید و "Scrape Again" بزنید

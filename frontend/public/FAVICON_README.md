# راهنمای فاوآیکن

فاوآیکن SVG برای وب‌سایت ایجاد شده است. این فایل در مرورگرهای مدرن به خوبی کار می‌کند.

## فایل‌های موجود

- `favicon.svg` - فاوآیکن اصلی (SVG)

## تولید نسخه‌های PNG (اختیاری)

برای تولید نسخه‌های PNG از SVG، می‌توانید از روش‌های زیر استفاده کنید:

### روش 1: استفاده از ابزارهای آنلاین
1. فایل `favicon.svg` را در یک ابزار آنلاین مانند [CloudConvert](https://cloudconvert.com/svg-to-png) یا [Convertio](https://convertio.co/svg-png/) باز کنید
2. اندازه‌های زیر را تولید کنید:
   - `favicon-16x16.png` (16x16 پیکسل)
   - `favicon-32x32.png` (32x32 پیکسل)
   - `apple-touch-icon.png` (180x180 پیکسل)
   - `favicon-192x192.png` (192x192 پیکسل) - برای PWA
   - `favicon-512x512.png` (512x512 پیکسل) - برای PWA

### روش 2: استفاده از ImageMagick (اگر نصب باشد)
```bash
magick convert -background none -resize 16x16 favicon.svg favicon-16x16.png
magick convert -background none -resize 32x32 favicon.svg favicon-32x32.png
magick convert -background none -resize 180x180 favicon.svg apple-touch-icon.png
magick convert -background none -resize 192x192 favicon.svg favicon-192x192.png
magick convert -background none -resize 512x512 favicon.svg favicon-512x512.png
```

### روش 3: استفاده از Node.js و sharp
```bash
npm install --save-dev sharp
```

سپس یک اسکریپت Node.js برای تبدیل ایجاد کنید.

## طراحی فاوآیکن

فاوآیکن طراحی شده شامل:
- **شبکه عصبی AI** (گره‌های متصل در بالا) - نماد هوش مصنوعی
- **نمودار معاملاتی** (خط صعودی در پایین) - نماد معاملات فارکس
- **رنگ‌بندی آبی** - هماهنگ با تم وب‌سایت
- **پس‌زمینه تیره با گرادیان** - مناسب برای تم تاریک

## یادداشت

فاوآیکن SVG در تمام مرورگرهای مدرن پشتیبانی می‌شود. نسخه‌های PNG برای سازگاری با مرورگرهای قدیمی‌تر و دستگاه‌های iOS (apple-touch-icon) توصیه می‌شود اما اجباری نیست.


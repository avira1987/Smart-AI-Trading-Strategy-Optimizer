# تبدیل SVG به JPG برای og-image

فایل `og-image.svg` در `frontend/public/` ایجاد شده است. برای تبدیل آن به JPG:

## روش 1: استفاده از ImageMagick (توصیه می‌شود)

```powershell
cd frontend/public
magick convert -background none og-image.svg -quality 90 og-image.jpg
```

## روش 2: استفاده از ابزارهای آنلاین

1. فایل `og-image.svg` را باز کنید
2. از یکی از ابزارهای زیر استفاده کنید:
   - [CloudConvert](https://cloudconvert.com/svg-to-jpg)
   - [Convertio](https://convertio.co/svg-jpg/)
   - [Online-Convert](https://www.online-convert.com/)
3. فایل JPG را با نام `og-image.jpg` در `frontend/public/` ذخیره کنید

## روش 3: استفاده از Node.js و sharp

```bash
cd frontend
node -e "import('sharp').then(s => s.default('public/og-image.svg').jpeg({quality: 90}).toFile('public/og-image.jpg').then(() => console.log('Done!')).catch(e => console.error(e)))"
```

## روش 4: استفاده از Python و PIL

```python
from PIL import Image
import cairosvg

# تبدیل SVG به PNG
cairosvg.svg2png(url='og-image.svg', write_to='og-image.png')

# تبدیل PNG به JPG
img = Image.open('og-image.png')
rgb_img = img.convert('RGB')
rgb_img.save('og-image.jpg', quality=90)
```

## بررسی

پس از تبدیل، فایل `og-image.jpg` باید:
- در مسیر `frontend/public/og-image.jpg` باشد
- ابعاد 1200x630 پیکسل داشته باشد
- حجم مناسبی داشته باشد (معمولاً کمتر از 200KB)

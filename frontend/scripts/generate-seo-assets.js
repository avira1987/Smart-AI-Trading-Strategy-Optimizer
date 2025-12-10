/**
 * اسکریپت تولید فایل‌های SEO
 * این اسکریپت فایل‌های og-image.jpg و favicon PNG را تولید می‌کند
 * 
 * نیازمندی‌ها:
 * npm install --save-dev sharp
 * 
 * استفاده:
 * node scripts/generate-seo-assets.js
 */

import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync, mkdirSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');
const faviconSvg = join(publicDir, 'favicon.svg');

// رنگ‌های تم وب‌سایت
const colors = {
  primary: '#1f2937',      // gray-800
  secondary: '#111827',    // gray-900
  accent: '#3b82f6',       // blue-500
  text: '#ffffff',         // white
  textSecondary: '#9ca3af' // gray-400
};

/**
 * ایجاد og-image.jpg با ابعاد 1200x630
 */
async function generateOgImage(sharp) {
  const width = 1200;
  const height = 630;
  const outputPath = join(publicDir, 'og-image.jpg');

  console.log('در حال ایجاد og-image.jpg...');

  try {
    // ایجاد یک SVG برای og-image
    const svg = `
      <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#111827;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#1f2937;stop-opacity:1" />
          </linearGradient>
        </defs>
        <rect width="${width}" height="${height}" fill="url(#bg)"/>
        
        <!-- شبکه عصبی AI (نماد هوش مصنوعی) -->
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
        
        <!-- نمودار معاملاتی (خط صعودی) -->
        <polyline points="100,450 200,400 300,350 400,300 500,280 600,250 700,220 800,200 900,180 1000,160 1100,140"
                  fill="none" stroke="#10b981" stroke-width="4" opacity="0.8"/>
        
        <!-- عنوان اصلی -->
        <text x="${width / 2}" y="280" font-family="Arial, sans-serif" font-size="64" font-weight="bold" 
              fill="#ffffff" text-anchor="middle">ترید با هوش مصنوعی</text>
        
        <!-- زیرعنوان -->
        <text x="${width / 2}" y="340" font-family="Arial, sans-serif" font-size="32" 
              fill="#9ca3af" text-anchor="middle">سامانه پیشرفته معاملات هوشمند</text>
        
        <!-- لوگو/نام برند -->
        <text x="${width / 2}" y="520" font-family="Arial, sans-serif" font-size="24" 
              fill="#3b82f6" text-anchor="middle">MyAibaz</text>
      </svg>
    `;

    // تبدیل SVG به JPG
    await sharp(Buffer.from(svg))
      .jpeg({ quality: 90 })
      .toFile(outputPath);

    console.log(`✓ og-image.jpg با موفقیت ایجاد شد: ${outputPath}`);
  } catch (error) {
    console.error('خطا در ایجاد og-image.jpg:', error);
    throw error;
  }
}

/**
 * تولید فایل‌های favicon PNG از SVG
 */
async function generateFavicons(sharp) {
  if (!existsSync(faviconSvg)) {
    console.warn(`⚠ فایل favicon.svg یافت نشد: ${faviconSvg}`);
    return;
  }

  console.log('در حال ایجاد فایل‌های favicon PNG...');

  const sizes = [
    { name: 'favicon-16x16.png', size: 16 },
    { name: 'favicon-32x32.png', size: 32 },
    { name: 'apple-touch-icon.png', size: 180 },
    { name: 'favicon-192x192.png', size: 192 },
    { name: 'favicon-512x512.png', size: 512 }
  ];

  try {
    for (const { name, size } of sizes) {
      const outputPath = join(publicDir, name);
      await sharp(faviconSvg)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 0, g: 0, b: 0, alpha: 0 }
        })
        .png()
        .toFile(outputPath);
      console.log(`✓ ${name} ایجاد شد`);
    }
    console.log('✓ تمام فایل‌های favicon PNG با موفقیت ایجاد شدند');
  } catch (error) {
    console.error('خطا در ایجاد favicon PNG files:', error);
    throw error;
  }
}

/**
 * تابع اصلی
 */
async function main() {
  console.log('شروع تولید فایل‌های SEO...\n');

  try {
    // بررسی وجود sharp
    let sharpModule;
    try {
      sharpModule = await import('sharp');
      console.log('✓ کتابخانه sharp بارگذاری شد\n');
    } catch (e) {
      console.error('❌ خطا: کتابخانه sharp نصب نشده است.');
      console.log('لطفاً با دستور زیر نصب کنید:');
      console.log('npm install --save-dev sharp\n');
      process.exit(1);
    }

    // استفاده از sharp از ماژول import شده
    const sharp = sharpModule.default || sharpModule;

    // ایجاد og-image
    await generateOgImage(sharp);
    console.log('');

    // ایجاد favicon PNG files
    await generateFavicons(sharp);
    console.log('');

    console.log('✅ تمام فایل‌های SEO با موفقیت تولید شدند!');
  } catch (error) {
    console.error('❌ خطا در تولید فایل‌های SEO:', error);
    console.error(error.stack);
    process.exit(1);
  }
}

// اجرای اسکریپت
main().catch(error => {
  console.error('خطای غیرمنتظره:', error);
  process.exit(1);
});

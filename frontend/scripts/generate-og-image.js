/**
 * اسکریپت ساده برای تولید og-image.jpg
 */

import sharp from 'sharp';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { writeFileSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const publicDir = join(__dirname, '..', 'public');
const outputPath = join(publicDir, 'og-image.jpg');

console.log('در حال ایجاد og-image.jpg...');
console.log('مسیر خروجی:', outputPath);

const width = 1200;
const height = 630;

// ایجاد SVG برای og-image
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

try {
  await sharp(Buffer.from(svg))
    .jpeg({ quality: 90 })
    .toFile(outputPath);
  
  console.log('✓ og-image.jpg با موفقیت ایجاد شد!');
  console.log('مسیر:', outputPath);
} catch (error) {
  console.error('❌ خطا در ایجاد og-image.jpg:', error.message);
  console.error(error.stack);
  process.exit(1);
}

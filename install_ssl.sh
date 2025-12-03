#!/bin/bash
# اسکریپت ساده برای نصب SSL با certbot
# استفاده: sudo bash install_ssl.sh

DOMAIN="myaibaz.ir"
WWW_DOMAIN="www.myaibaz.ir"

echo "نصب SSL برای $DOMAIN و $WWW_DOMAIN"
echo ""

# بررسی اینکه آیا certbot نصب است
if ! command -v certbot &> /dev/null; then
    echo "نصب certbot..."
    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-nginx
fi

# اجرای certbot
echo "در حال دریافت گواهینامه SSL..."
sudo certbot --nginx -d $DOMAIN -d $WWW_DOMAIN

# راه‌اندازی مجدد Nginx
echo "راه‌اندازی مجدد Nginx..."
sudo systemctl reload nginx

echo ""
echo "✅ SSL با موفقیت نصب شد!"
echo "🌐 سایت شما در دسترس است: https://$DOMAIN"


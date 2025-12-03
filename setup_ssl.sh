#!/bin/bash
# اسکریپت نصب SSL با Certbot برای Nginx
# این اسکریپت برای سرورهای Linux طراحی شده است

set -e

DOMAIN="myaibaz.ir"
WWW_DOMAIN="www.myaibaz.ir"
EMAIL=""  # ایمیل خود را اینجا وارد کنید (اختیاری اما توصیه می‌شود)

echo "========================================"
echo "  نصب SSL با Let's Encrypt Certbot"
echo "========================================"
echo ""

# بررسی اینکه آیا certbot نصب است
if ! command -v certbot &> /dev/null; then
    echo "❌ Certbot نصب نیست. در حال نصب..."
    
    # تشخیص توزیع Linux
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y certbot python3-certbot-nginx
    elif [ -f /etc/redhat-release ]; then
        # CentOS/RHEL
        sudo yum install -y certbot python3-certbot-nginx
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        sudo pacman -S --noconfirm certbot certbot-nginx
    else
        echo "❌ توزیع Linux شناسایی نشد. لطفاً certbot را به صورت دستی نصب کنید."
        echo "   برای Debian/Ubuntu: sudo apt-get install certbot python3-certbot-nginx"
        echo "   برای CentOS/RHEL: sudo yum install certbot python3-certbot-nginx"
        exit 1
    fi
fi

echo "✓ Certbot نصب است"
echo ""

# بررسی اینکه آیا Nginx در حال اجرا است
if ! systemctl is-active --quiet nginx; then
    echo "⚠️  Nginx در حال اجرا نیست. در حال راه‌اندازی..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
fi

echo "✓ Nginx در حال اجرا است"
echo ""

# بررسی اینکه پورت 80 باز است
if ! sudo netstat -tuln | grep -q ':80 '; then
    echo "⚠️  پورت 80 باز نیست. لطفاً مطمئن شوید که Nginx روی پورت 80 در حال اجرا است."
    exit 1
fi

echo "✓ پورت 80 باز است"
echo ""

# درخواست گواهینامه SSL
echo "📋 در حال درخواست گواهینامه SSL برای $DOMAIN و $WWW_DOMAIN..."
echo ""

if [ -z "$EMAIL" ]; then
    echo "⚠️  ایمیل تنظیم نشده است. استفاده از حالت بدون ایمیل..."
    sudo certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --register-unsafely-without-email
else
    echo "📧 استفاده از ایمیل: $EMAIL"
    sudo certbot --nginx -d $DOMAIN -d $WWW_DOMAIN --non-interactive --agree-tos --email $EMAIL
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ گواهینامه SSL با موفقیت نصب شد!"
    echo ""
    
    # بررسی مسیر گواهینامه‌ها
    CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    KEY_PATH="/etc/letsencrypt/live/$DOMAIN/privkey.pem"
    
    if [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
        echo "📁 مسیر گواهینامه‌ها:"
        echo "   Certificate: $CERT_PATH"
        echo "   Private Key: $KEY_PATH"
        echo ""
    fi
    
    # تست پیکربندی Nginx
    echo "🔍 تست پیکربندی Nginx..."
    if sudo nginx -t; then
        echo "✓ پیکربندی Nginx معتبر است"
        echo ""
        
        # راه‌اندازی مجدد Nginx
        echo "🔄 راه‌اندازی مجدد Nginx..."
        sudo systemctl reload nginx
        echo "✓ Nginx با موفقیت راه‌اندازی مجدد شد"
        echo ""
    else
        echo "❌ خطا در پیکربندی Nginx. لطفاً به صورت دستی بررسی کنید."
        exit 1
    fi
    
    # تنظیم تمدید خودکار
    echo "🔄 تنظیم تمدید خودکار گواهینامه..."
    if ! sudo systemctl is-enabled --quiet certbot.timer; then
        sudo systemctl enable certbot.timer
        sudo systemctl start certbot.timer
    fi
    echo "✓ تمدید خودکار فعال است"
    echo ""
    
    echo "========================================"
    echo "  ✅ SSL با موفقیت نصب شد!"
    echo "========================================"
    echo ""
    echo "🌐 آدرس‌های سایت:"
    echo "   https://$DOMAIN"
    echo "   https://$WWW_DOMAIN"
    echo ""
    echo "📝 نکات مهم:"
    echo "   - گواهینامه به صورت خودکار هر 90 روز تمدید می‌شود"
    echo "   - برای تمدید دستی: sudo certbot renew"
    echo "   - برای تست تمدید: sudo certbot renew --dry-run"
    echo ""
else
    echo ""
    echo "❌ خطا در نصب گواهینامه SSL"
    echo ""
    echo "🔍 بررسی‌های لازم:"
    echo "   1. دامنه باید به IP سرور شما اشاره کند"
    echo "   2. پورت 80 باید از اینترنت قابل دسترسی باشد"
    echo "   3. فایروال باید پورت 80 را باز کند"
    echo "   4. Nginx باید در حال اجرا باشد"
    exit 1
fi


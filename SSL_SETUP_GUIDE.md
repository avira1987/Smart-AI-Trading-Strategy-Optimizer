# راهنمای نصب SSL با Let's Encrypt Certbot

این راهنما به شما کمک می‌کند تا گواهینامه SSL را برای دامنه `myaibaz.ir` نصب کنید.

## 📋 پیش‌نیازها

1. ✅ دامنه `myaibaz.ir` باید به IP سرور شما اشاره کند
2. ✅ پورت 80 باید از اینترنت قابل دسترسی باشد
3. ✅ فایروال باید پورت 80 را باز کند
4. ✅ Nginx باید در حال اجرا باشد

## 🚀 روش‌های نصب SSL

### روش 1: استفاده از اسکریپت خودکار (توصیه می‌شود)

#### برای سرور Linux:

```bash
# اجرای اسکریپت
sudo bash setup_ssl.sh
```

#### برای Windows (با WSL):

```powershell
# اجرای اسکریپت در WSL
wsl bash setup_ssl.sh
```

#### برای Windows (بدون WSL):

```powershell
# اجرای اسکریپت PowerShell
.\setup_ssl.ps1
```

### روش 2: نصب دستی با Certbot

#### برای Nginx در Linux:

```bash
# نصب certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# درخواست گواهینامه
sudo certbot --nginx -d myaibaz.ir -d www.myaibaz.ir
```

#### برای Apache در Linux:

```bash
# نصب certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-apache

# درخواست گواهینامه
sudo certbot --apache -d myaibaz.ir -d www.myaibaz.ir
```

## 📝 مراحل نصب

### مرحله 1: نصب Certbot

اگر certbot نصب نیست، ابتدا آن را نصب کنید:

**Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
```

**CentOS/RHEL:**
```bash
sudo yum install certbot python3-certbot-nginx
```

**Arch Linux:**
```bash
sudo pacman -S certbot certbot-nginx
```

### مرحله 2: اجرای Certbot

```bash
# برای Nginx
sudo certbot --nginx -d myaibaz.ir -d www.myaibaz.ir

# برای Apache
sudo certbot --apache -d myaibaz.ir -d www.myaibaz.ir
```

Certbot به صورت خودکار:
- گواهینامه را دریافت می‌کند
- فایل‌های Nginx/Apache را به‌روزرسانی می‌کند
- SSL را فعال می‌کند

### مرحله 3: به‌روزرسانی فایل‌های Nginx (فقط برای Windows)

اگر از Windows استفاده می‌کنید، بعد از نصب SSL:

```powershell
.\update_nginx_ssl.ps1
```

این اسکریپت به صورت خودکار:
- مسیرهای گواهینامه را پیدا می‌کند
- فایل `nginx_production.conf` را به‌روزرسانی می‌کند
- بخش HTTPS را فعال می‌کند

### مرحله 4: راه‌اندازی مجدد Nginx

```bash
# Linux
sudo systemctl reload nginx

# Windows
# Nginx را از پنجره مربوطه متوقف و دوباره راه‌اندازی کنید
```

## 🔍 بررسی نصب SSL

بعد از نصب، بررسی کنید:

1. **بررسی گواهینامه:**
   ```bash
   sudo certbot certificates
   ```

2. **تست دسترسی HTTPS:**
   ```bash
   curl -I https://myaibaz.ir
   ```

3. **بررسی در مرورگر:**
   - باز کردن `https://myaibaz.ir` در مرورگر
   - بررسی آیکون قفل در نوار آدرس

## 🔄 تمدید خودکار گواهینامه

گواهینامه‌های Let's Encrypt هر 90 روز منقضی می‌شوند. Certbot به صورت خودکار تمدید را تنظیم می‌کند.

### بررسی وضعیت تمدید خودکار:

```bash
sudo systemctl status certbot.timer
```

### تست تمدید (بدون اعمال تغییرات):

```bash
sudo certbot renew --dry-run
```

### تمدید دستی:

```bash
sudo certbot renew
```

## 📁 مسیرهای گواهینامه

بعد از نصب، گواهینامه‌ها در این مسیرها قرار می‌گیرند:

**Linux:**
- Certificate: `/etc/letsencrypt/live/myaibaz.ir/fullchain.pem`
- Private Key: `/etc/letsencrypt/live/myaibaz.ir/privkey.pem`

**Windows (با WSL):**
- Certificate: `/etc/letsencrypt/live/myaibaz.ir/fullchain.pem` (در WSL)
- Private Key: `/etc/letsencrypt/live/myaibaz.ir/privkey.pem` (در WSL)

**Windows (بدون WSL):**
- Certificate: `C:\certbot\conf\live\myaibaz.ir\fullchain.pem`
- Private Key: `C:\certbot\conf\live\myaibaz.ir\privkey.pem`

## ⚠️ مشکلات رایج و راه‌حل

### مشکل 1: دامنه به IP سرور اشاره نمی‌کند

**راه‌حل:**
- بررسی DNS records در پنل دامنه
- اطمینان از اینکه A record به IP سرور اشاره می‌کند

### مشکل 2: پورت 80 بسته است

**راه‌حل:**
```bash
# بررسی فایروال
sudo ufw status
sudo ufw allow 80/tcp

# یا برای iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
```

### مشکل 3: Nginx در حال اجرا نیست

**راه‌حل:**
```bash
# Linux
sudo systemctl start nginx
sudo systemctl enable nginx

# Windows
# اجرای start.ps1
```

### مشکل 4: خطا در پیکربندی Nginx

**راه‌حل:**
```bash
# تست پیکربندی
sudo nginx -t

# بررسی لاگ‌ها
sudo tail -f /var/log/nginx/error.log
```

## 🔒 امنیت

بعد از نصب SSL:

1. ✅ HTTP به HTTPS redirect می‌شود
2. ✅ HSTS (HTTP Strict Transport Security) فعال است
3. ✅ گواهینامه به صورت خودکار تمدید می‌شود

## 📚 منابع بیشتر

- [مستندات Let's Encrypt](https://letsencrypt.org/docs/)
- [مستندات Certbot](https://certbot.eff.org/)
- [راهنمای Nginx SSL](https://nginx.org/en/docs/http/configuring_https_servers.html)

## 🆘 پشتیبانی

اگر مشکلی دارید:

1. بررسی لاگ‌های Certbot: `/var/log/letsencrypt/`
2. بررسی لاگ‌های Nginx: `/var/log/nginx/error.log`
3. اجرای certbot با flag `--verbose` برای اطلاعات بیشتر

---

**نکته مهم:** بعد از نصب SSL، حتماً سایت را در `https://myaibaz.ir` تست کنید و مطمئن شوید که همه چیز به درستی کار می‌کند.


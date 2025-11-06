# راهنمای راه‌اندازی Proxy برای API نرخ

## مشکل فعلی
API نرخ (nerkh.io) فقط از IP ایران قابل دسترسی است. VPS شما از طریق OpenVPN به کلاینت متصل است.

## راه‌حل: راه‌اندازی Proxy روی کلاینت

### گزینه 1: استفاده از Proxy Server ساده (پیشنهادی)

#### مرحله 1: اجرای Proxy روی کلاینت محلی

```bash
# روی کلاینت محلی (با IP ایران):
python client_proxy_server.py 8080
```

یا اگر پورت دیگری می‌خواهید:
```bash
python client_proxy_server.py 5000
```

#### مرحله 2: تست از VPS

```bash
# روی VPS:
python backend/test_nerkh_api.py http://CLIENT_LOCAL_IP:8080
```

### گزینه 2: استفاده از SOCKS Proxy (اگر OpenVPN دارید)

اگر OpenVPN روی کلاینت در حال اجرا است، می‌توانید از SOCKS proxy استفاده کنید:

```bash
# روی کلاینت:
# OpenVPN معمولاً SOCKS proxy ایجاد می‌کند
# یا از SSH tunnel استفاده کنید:
ssh -D 1080 user@localhost
```

سپس در تست:
```bash
python backend/test_nerkh_api.py socks5://127.0.0.1:1080
```

### گزینه 3: استفاده از Proxy موجود

اگر روی کلاینت proxy دیگری دارید (مثلاً HTTP Proxy یا SOCKS):

```bash
# تست با proxy موجود:
python backend/test_nerkh_api.py http://PROXY_IP:PROXY_PORT
```

## مراحل بعدی

بعد از راه‌اندازی proxy:

1. **تست اتصال**:
   ```bash
   python backend/test_nerkh_api.py http://CLIENT_IP:8080
   ```

2. **اگر موفق بود**، endpoint صحیح را پیدا کنید (از مستندات nerkh.io)

3. **اضافه کردن به پروژه**:
   - تنظیمات در `.env`
   - استفاده در `NerkhProvider`

## نکات مهم

1. **Firewall**: مطمئن شوید firewall کلاینت مسدود نمی‌کند
2. **IP کلاینت**: IP کلاینت را از OpenVPN یا ifconfig بگیرید
3. **Port**: پورت 8080 یا هر پورت آزاد دیگر
4. **مستندات API**: endpoint صحیح را از [docs.nerkh.io](https://docs.nerkh.io) پیدا کنید

## عیب‌یابی

### خطا: Connection refused
- Proxy روی کلاینت در حال اجرا نیست
- IP یا Port اشتباه است
- Firewall مسدود می‌کند

### خطا: 404 Not Found
- Endpoint اشتباه است
- باید مستندات API را بررسی کنید

### خطا: Proxy Error
- Proxy نوع اشتباه است (HTTP vs SOCKS)
- Proxy configuration مشکل دارد


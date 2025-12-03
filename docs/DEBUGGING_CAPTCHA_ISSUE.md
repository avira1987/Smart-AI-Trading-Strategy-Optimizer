# راهنمای Debugging مشکل CAPTCHA در دسترسی از اینترنت

## مشکل
در دسترسی از IP اینترنت، پیام "درخواست به سرور ارسال شد اما پاسخی دریافت نشد" نمایش داده می‌شود.

## مراحل Debugging

### 1. بررسی Console مرورگر (F12)

باز کردن Console و بررسی خطاها:

```javascript
// باید این لاگ را ببینید:
Error getting CAPTCHA: {
  message: "...",
  code: "...",
  origin: "http://<IP>",
  hostname: "<IP>",
  ...
}
```

**خطاهای احتمالی**:
- `ERR_NETWORK` - مشکل شبکه
- `ECONNABORTED` - Timeout
- `ERR_CORS` - مشکل CORS
- `error.request` بدون `error.response` - درخواست ارسال شده اما پاسخ دریافت نشده

### 2. بررسی Network Tab

در Developer Tools > Network:
1. فیلتر را روی "XHR" یا "Fetch" تنظیم کنید
2. صفحه را refresh کنید
3. درخواست `/api/captcha/get/` را پیدا کنید
4. بررسی کنید:
   - **Status**: چه status code است؟
   - **Type**: آیا preflight (OPTIONS) است یا POST؟
   - **Time**: چقدر طول کشیده؟
   - **Response**: آیا response وجود دارد؟

### 3. بررسی Backend

```powershell
# بررسی اینکه Backend در حال اجرا است
netstat -ano | findstr :8000

# باید ببینید:
# TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING
```

### 4. تست مستقیم Backend

```powershell
$body = @{action='login'} | ConvertTo-Json
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/captcha/get/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**باید Status 200 و response دریافت کنید.**

### 5. تست از طریق Nginx

```powershell
$body = @{action='login'} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost/api/captcha/get/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

**باید Status 200 و response دریافت کنید.**

### 6. بررسی لاگ‌های Nginx

```powershell
# لاگ‌های خطا
Get-Content C:\nginx-1.28.0\logs\error.log -Tail 50

# لاگ‌های API
Get-Content C:\nginx-1.28.0\logs\api_error.log -Tail 50
```

**خطاهای احتمالی**:
- `connect() failed (10061: No connection could be made...)` - Backend در حال اجرا نیست
- `upstream timed out` - Timeout در اتصال به backend
- `upstream connection failed` - مشکل در اتصال

### 7. بررسی CORS

در Console مرورگر، بررسی کنید که آیا خطای CORS وجود دارد:

```
Access to XMLHttpRequest at 'http://<IP>/api/captcha/get/' from origin 'http://<IP>' 
has been blocked by CORS policy: ...
```

**اگر این خطا را می‌بینید**:
- بررسی کنید که IP شما در `CORS_ALLOWED_ORIGINS` است
- بررسی لاگ Django برای CORS errors

## راه‌حل‌های احتمالی

### راه‌حل 1: افزایش Timeout

اگر مشکل از timeout است:

```nginx
# در nginx_production.conf
proxy_connect_timeout 60s;
proxy_send_timeout 90s;
proxy_read_timeout 90s;
```

### راه‌حل 2: بررسی OPTIONS Preflight

اگر مشکل از OPTIONS request است:

1. بررسی Network tab - آیا OPTIONS request timeout می‌شود؟
2. بررسی nginx config - آیا OPTIONS به درستی handle می‌شود؟

### راه‌حل 3: غیرفعال کردن withCredentials (موقت)

برای تست، می‌توانید `withCredentials: false` را در `client.ts` تنظیم کنید:

```typescript
const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // موقت برای تست
  timeout: getRequestTimeout(),
})
```

**نکته**: این فقط برای تست است. بعد از پیدا کردن مشکل، دوباره `true` کنید.

### راه‌حل 4: بررسی Firewall

ممکن است firewall مانع اتصال شود:

```powershell
# بررسی firewall rules
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*8000*"}
```

## اطلاعات مورد نیاز برای Debugging

وقتی مشکل را گزارش می‌دهید، این اطلاعات را ارسال کنید:

1. **Console Logs**: تمام خطاهای Console
2. **Network Tab**: Screenshot از درخواست `/api/captcha/get/`
3. **Nginx Logs**: آخرین 50 خط از error.log
4. **Backend Status**: آیا backend در حال اجرا است؟
5. **IP Address**: IP که از آن دسترسی دارید
6. **Browser**: چه مرورگری استفاده می‌کنید؟

## تست نهایی

بعد از اعمال تغییرات:

1. **Reload Nginx**:
   ```powershell
   C:\nginx-1.28.0\nginx.exe -s reload
   ```

2. **Clear Browser Cache**: Ctrl+Shift+Delete

3. **Test Again**: از IP اینترنت تست کنید

4. **Check Console**: آیا خطاها برطرف شدند؟


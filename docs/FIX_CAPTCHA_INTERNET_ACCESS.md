# رفع مشکل CAPTCHA در دسترسی از اینترنت - راه‌حل نهایی

## مشکل

در دسترسی از IP اینترنت (`http://191.101.113.163/login`)، خطای زیر نمایش داده می‌شود:

```
Cross-Origin Request Blocked: The Same Origin Policy disallows reading the remote resource at http://127.0.0.1:8000/api/captcha/get/
```

و در Console:
```
baseURL: "http://127.0.0.1:8000/api"
```

## علت مشکل

Frontend در production build، مستقیماً به `http://127.0.0.1:8000/api` درخواست می‌فرستد به جای استفاده از relative URL `/api` که باید از طریق Nginx proxy شود.

**چرا این اتفاق می‌افتد؟**
- در production build، اگر `VITE_BACKEND_URL` تنظیم شده باشد، این مقدار در فایل build شده hardcode می‌شود
- وقتی از IP اینترنت دسترسی دارید، مرورگر نمی‌تواند به `127.0.0.1:8000` دسترسی پیدا کند (این فقط localhost است)
- باید از relative URL `/api` استفاده شود تا Nginx proxy کند

## راه‌حل

### تغییرات اعمال شده

در فایل `frontend/src/api/client.ts`:

```typescript
function getApiBaseUrl(): string {
  // In production (built files), always use relative URL
  // This ensures requests go through Nginx proxy instead of direct backend access
  if (import.meta.env.PROD) {
    return '/api'
  }
  
  // In development, check for environment variable
  const envBackendUrl = import.meta.env.VITE_BACKEND_URL
  if (envBackendUrl && import.meta.env.DEV) {
    return envBackendUrl.endsWith('/api') ? envBackendUrl : `${envBackendUrl}/api`
  }
  
  // Default: use relative URL
  return '/api'
}
```

**تغییرات کلیدی**:
1. در production (`import.meta.env.PROD`)، همیشه از `/api` استفاده می‌شود
2. `VITE_BACKEND_URL` فقط در development mode استفاده می‌شود
3. این اطمینان می‌دهد که در production، همه درخواست‌ها از طریق Nginx proxy می‌شوند

## مراحل اعمال راه‌حل

### 1. Rebuild Frontend

```powershell
cd frontend
npm run build
cd ..
```

یا استفاده از `start.ps1` که به صورت خودکار rebuild می‌کند:

```powershell
.\start.ps1
```

### 2. Reload Nginx

```powershell
C:\nginx-1.28.0\nginx.exe -t
C:\nginx-1.28.0\nginx.exe -s reload
```

### 3. Clear Browser Cache

- Ctrl+Shift+Delete
- یا Hard Refresh: Ctrl+F5

### 4. تست

1. باز کردن `http://191.101.113.163/login`
2. باز کردن Console (F12)
3. بررسی لاگ:
   ```
   API Configuration: {
     baseURL: "/api",  // باید "/api" باشد، نه "http://127.0.0.1:8000/api"
     hostname: "191.101.113.163",
     origin: "http://191.101.113.163",
     isProduction: true,
     usingRelativeURL: true
   }
   ```
4. بررسی Network tab - درخواست `/api/captcha/get/` باید:
   - URL: `http://191.101.113.163/api/captcha/get/` (نه `http://127.0.0.1:8000/api/captcha/get/`)
   - Status: 200
   - Response: JSON با `success: true`

## بررسی

### قبل از Fix:
```
❌ baseURL: "http://127.0.0.1:8000/api"
❌ Cross-Origin Request Blocked
❌ Status code: (null)
```

### بعد از Fix:
```
✅ baseURL: "/api"
✅ Request URL: http://191.101.113.163/api/captcha/get/
✅ Status: 200
✅ Response: {"success": true, "challenge": "5 + 3", ...}
```

## نکات مهم

1. **همیشه Frontend را بعد از تغییرات rebuild کنید**
2. **در production، از relative URL استفاده کنید**
3. **`VITE_BACKEND_URL` فقط برای development است**
4. **Nginx باید `/api/` را به `http://127.0.0.1:8000/api/` proxy کند**

## اگر مشکل باقی ماند

1. بررسی Console - آیا `baseURL` هنوز `http://127.0.0.1:8000/api` است؟
   - اگر بله، Frontend را دوباره rebuild کنید
2. بررسی Network tab - آیا درخواست به `http://191.101.113.163/api/` می‌رود؟
   - اگر نه، مشکل از build است
3. بررسی Nginx - آیا proxy کار می‌کند؟
   ```powershell
   Invoke-WebRequest -Uri "http://localhost/api/captcha/get/" -Method POST -ContentType "application/json" -Body '{"action":"login"}'
   ```


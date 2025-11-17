# راهنمای سیستم CAPTCHA خود مدیریتی

این سیستم یک CAPTCHA سبک و خود مدیریتی است که بدون نیاز به سرویس‌های خارجی (مثل Google reCAPTCHA) کار می‌کند.

## ویژگی‌ها

✅ **خود مدیریتی** - بدون وابستگی به سرویس‌های خارجی  
✅ **سبک** - بدون نیاز به کتابخانه‌های اضافی  
✅ **امن** - ترکیب چند روش محافظت:
   - Math Challenge (حل معادله ریاضی ساده)
   - Honeypot Field (فیلد مخفی)
   - Time-based Validation (بررسی زمان ارسال)
   - Rate Limiting (محدودیت تعداد درخواست)

## نحوه کار

### 1. Math Challenge
- یک معادله ریاضی ساده (جمع یا تفریق) نمایش داده می‌شود
- کاربر باید پاسخ را وارد کند
- پاسخ در Backend بررسی می‌شود

### 2. Honeypot Field
- یک فیلد مخفی در فرم وجود دارد
- اگر این فیلد پر شود، درخواست رد می‌شود (بات‌ها معمولاً همه فیلدها را پر می‌کنند)

### 3. Time-based Validation
- زمان بارگذاری صفحه ثبت می‌شود
- اگر فرم خیلی سریع ارسال شود (< 2 ثانیه) = احتمالاً بات
- اگر خیلی دیر ارسال شود (> 10 دقیقه) = منقضی شده

### 4. Rate Limiting
- محدودیت تعداد درخواست‌ها بر اساس IP
- در صورت تجاوز، IP برای 5 دقیقه مسدود می‌شود

## استفاده در Frontend

### دریافت CAPTCHA

```typescript
import { getCaptcha, initPageLoadTime, prepareCaptchaData } from '../utils/selfCaptcha'

// در useEffect یا componentDidMount
useEffect(() => {
  initPageLoadTime() // ثبت زمان بارگذاری صفحه
  loadCaptcha()
}, [])

const loadCaptcha = async () => {
  try {
    const captcha = await getCaptcha('login')
    setCaptchaChallenge(captcha.challenge) // نمایش معادله
  } catch (error) {
    console.error('Failed to load CAPTCHA:', error)
  }
}
```

### ارسال با CAPTCHA

```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault()
  
  // آماده‌سازی داده‌های CAPTCHA
  const captchaData = prepareCaptchaData(Number(captchaAnswer))
  
  // ارسال درخواست
  const response = await sendOTP(phoneNumber, captchaData)
  // ...
}
```

### فرم HTML

```tsx
<form onSubmit={handleSubmit}>
  {/* فیلدهای دیگر */}
  
  {/* CAPTCHA Challenge */}
  {captchaChallenge && (
    <div>
      <label>امنیت: {captchaChallenge} = ?</label>
      <input
        type="number"
        value={captchaAnswer}
        onChange={(e) => setCaptchaAnswer(e.target.value)}
        required
      />
    </div>
  )}
  
  {/* Honeypot Field - مخفی */}
  <input
    type="text"
    name="website"
    tabIndex={-1}
    autoComplete="off"
    style={{ position: 'absolute', left: '-9999px' }}
    aria-hidden="true"
  />
  
  <button type="submit">ارسال</button>
</form>
```

## تنظیمات Backend

### تنظیمات در `backend/api/self_captcha.py`

```python
# زمان انقضای CAPTCHA (ثانیه)
CAPTCHA_EXPIRY = 300  # 5 دقیقه

# حداقل زمان بین بارگذاری و ارسال (ثانیه)
CAPTCHA_MIN_TIME = 2

# حداکثر زمان (ثانیه)
CAPTCHA_MAX_TIME = 600  # 10 دقیقه
```

### تنظیمات Rate Limiting

در `backend/api/rate_limiter.py`:

```python
RATE_LIMITS = {
    '/api/auth/send-otp/': (5, 300),  # 5 درخواست در 5 دقیقه
    '/api/auth/verify-otp/': (10, 60),  # 10 درخواست در 1 دقیقه
    # ...
}
```

## API Endpoints

### دریافت CAPTCHA

```http
POST /api/captcha/get/
Content-Type: application/json

{
  "action": "login"  // اختیاری
}
```

**Response:**
```json
{
  "success": true,
  "token": "captcha_token_here",
  "challenge": "15 + 7",
  "type": "math"
}
```

### ارسال با CAPTCHA

```http
POST /api/auth/send-otp/
Content-Type: application/json

{
  "phone_number": "09123456789",
  "captcha_token": "captcha_token_here",
  "captcha_answer": 22,
  "page_load_time": 1234567890.123,
  "website": ""  // Honeypot - باید خالی باشد
}
```

## امنیت

### محافظت‌های اعمال شده:

1. **Token Expiry**: هر token فقط 5 دقیقه معتبر است
2. **One-time Use**: هر token فقط یک بار قابل استفاده است
3. **Time Validation**: بررسی زمان ارسال فرم
4. **Honeypot**: تشخیص و مسدودسازی بات‌ها
5. **Rate Limiting**: محدودیت تعداد درخواست‌ها

### نکات امنیتی:

⚠️ **مهم**:
- CAPTCHA token را در Frontend ذخیره نکنید
- Honeypot field را هرگز نمایش ندهید
- Time validation را غیرفعال نکنید
- Rate limiting را در Production فعال نگه دارید

## عیب‌یابی

### خطا: "CAPTCHA token missing"

- مطمئن شوید CAPTCHA را قبل از ارسال فرم دریافت کرده‌اید
- بررسی کنید token به درستی به Backend ارسال می‌شود

### خطا: "CAPTCHA expired"

- Token منقضی شده است (بیش از 5 دقیقه گذشته)
- یک CAPTCHA جدید دریافت کنید

### خطا: "Too fast" یا "Too slow"

- زمان ارسال فرم مشکوک است
- کاربر باید دوباره تلاش کند

### خطا: "Wrong answer"

- پاسخ CAPTCHA اشتباه است
- یک CAPTCHA جدید دریافت کنید

## مقایسه با Google reCAPTCHA

| ویژگی | CAPTCHA خود مدیریتی | Google reCAPTCHA |
|-------|---------------------|------------------|
| وابستگی خارجی | ❌ ندارد | ✅ دارد |
| هزینه | ✅ رایگان | ✅ رایگان |
| سبکی | ✅ بسیار سبک | ⚠️ نیاز به script خارجی |
| حریم خصوصی | ✅ داده‌ها به Google ارسال نمی‌شود | ❌ داده‌ها به Google ارسال می‌شود |
| پیچیدگی | ⚠️ نیاز به پیاده‌سازی | ✅ آماده استفاده |
| سفارشی‌سازی | ✅ کاملاً قابل سفارشی‌سازی | ❌ محدود |

## بهبودهای آینده

- [ ] اضافه کردن challenge های متنوع (تصویر، متن، etc.)
- [ ] استفاده از Redis برای cache (به جای Django cache)
- [ ] اضافه کردن Browser Fingerprinting
- [ ] اضافه کردن Machine Learning برای تشخیص بات

## منابع

- [Django Cache Framework](https://docs.djangoproject.com/en/stable/topics/cache/)
- [Honeypot Technique](https://en.wikipedia.org/wiki/Honeypot_(computing))


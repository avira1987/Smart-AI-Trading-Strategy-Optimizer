# ✅ راه‌اندازی Git Workflow و Deploy - تکمیل شد!

## 📋 کارهای انجام شده

### ✅ 1. فایل `deploy.ps1` ایجاد شد
- اسکریپت PowerShell برای deploy خودکار به VPS
- شامل: Build Frontend، ایجاد ZIP، انتقال به VPS، نصب وابستگی‌ها، راه‌اندازی سرویس‌ها

### ✅ 2. فایل `.gitignore` به‌روزرسانی شد
- اضافه شد: `.env.production` و `.env.*.local`
- اضافه شد: `in vps/` (دیگر نیازی نیست)

### ✅ 3. Git Repository راه‌اندازی شد
- `git init` انجام شد
- Branch اصلی: `main`

### ✅ 4. اسکریپت `setup_env_files.ps1` ایجاد شد
- برای ایجاد خودکار فایل‌های `.env.local` و `.env.production`

---

## 🚀 مراحل بعدی (برای شما)

### مرحله 1: ایجاد فایل‌های Environment

```powershell
# اجرای اسکریپت برای ایجاد فایل‌های .env
.\setup_env_files.ps1
```

یا به صورت دستی:

```powershell
# ایجاد .env.local
Copy-Item env.example .env.local
notepad .env.local

# ایجاد .env.production
Copy-Item env.example .env.production
notepad .env.production
```

**⚠️ مهم برای `.env.production`:**
1. `SECRET_KEY` را تغییر دهید:
   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
2. `DEBUG=False` باشد
3. `PUBLIC_IP=191.101.113.163` تنظیم شده است
4. تمام API keys را با مقادیر واقعی جایگزین کنید

### مرحله 2: تنظیم Git Remote (اختیاری)

اگر می‌خواهید از GitHub/GitLab استفاده کنید:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### مرحله 3: استفاده از فایل‌های Environment

**برای توسعه محلی:**
```powershell
Copy-Item .env.local .env -Force
```

**برای Production (قبل از Deploy):**
```powershell
Copy-Item .env.production .env -Force
```

**نکته:** اسکریپت `deploy.ps1` به صورت خودکار `.env.production` را به `.env` کپی می‌کند.

### مرحله 4: Deploy به VPS

```powershell
# Deploy کامل
.\deploy.ps1

# یا با گزینه‌های مختلف:
.\deploy.ps1 -SkipGit      # بدون commit کردن
.\deploy.ps1 -SkipBuild    # بدون build کردن frontend
.\deploy.ps1 -SkipRestart  # بدون restart کردن سرویس‌ها
```

---

## 📚 مستندات

راهنماهای کامل در پوشه `in vps/deploy/`:

- **`QUICK_START_DEPLOY.md`** - راهنمای سریع 3 مرحله‌ای
- **`GIT_WORKFLOW_GUIDE.md`** - راهنمای کامل Git Workflow
- **`ENV_SETUP_GUIDE.md`** - راهنمای تنظیم Environment Variables
- **`README_GIT_WORKFLOW.md`** - خلاصه و چک‌لیست

---

## 🔧 تنظیمات VPS

قبل از اولین Deploy، روی VPS این دستورات را اجرا کنید:

```powershell
# فعال‌سازی WinRM
Enable-PSRemoting -Force
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "*" -Force

# باز کردن پورت‌ها در Firewall
New-NetFirewallRule -DisplayName "Backend Port" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Frontend Port" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WinRM Port" -Direction Inbound -LocalPort 7230 -Protocol TCP -Action Allow

# نصب Python و Node.js (اگر نصب نشده)
winget install Python.Python.3.11
winget install OpenJS.NodeJS.LTS
```

---

## ✅ چک‌لیست قبل از Deploy

- [ ] فایل `.env.production` ایجاد و تنظیم شده است
- [ ] `SECRET_KEY` در `.env.production` تغییر کرده است
- [ ] `DEBUG=False` در Production
- [ ] `PUBLIC_IP=191.101.113.163` تنظیم شده است
- [ ] `ALLOWED_HOSTS=191.101.113.163,localhost,127.0.0.1` تنظیم شده است
- [ ] تمام API keys در `.env.production` وارد شده‌اند
- [ ] Frontend build می‌شود (`cd frontend && npm run build`)
- [ ] Git repository راه‌اندازی شده است (انجام شد ✅)

---

## 🎯 Workflow پیشنهادی

### روزانه (Development):

```powershell
# 1. استفاده از .env.local
Copy-Item .env.local .env -Force

# 2. راه‌اندازی پروژه
.\start_project.ps1

# 3. توسعه و تست
# ... کد نویسی ...

# 4. Commit تغییرات
git add .
git commit -m "Feature: توضیح تغییرات"
```

### Deploy به VPS:

```powershell
# 1. اطمینان از commit شدن تغییرات
git status

# 2. Deploy
.\deploy.ps1
```

---

## 📞 دسترسی به پروژه

بعد از Deploy موفق:

- **Backend API**: http://191.101.113.163:8000
- **Frontend**: http://191.101.113.163:3000
- **Admin Panel**: http://191.101.113.163:8000/admin

---

## 🐛 مشکلات رایج

### "Cannot connect to VPS"
```powershell
# تست اتصال
Test-NetConnection -ComputerName 191.101.113.163 -Port 7230
```

### "Build Frontend failed"
```powershell
cd frontend
Remove-Item node_modules -Recurse -Force
npm install
npm run build
```

### "Port already in use"
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
Stop-Process -Id <PID> -Force
```

---

**🎉 همه چیز آماده است! برای شروع، `.\setup_env_files.ps1` را اجرا کنید.**


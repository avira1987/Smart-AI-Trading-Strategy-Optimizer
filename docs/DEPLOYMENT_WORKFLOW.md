# 🚀 راهنمای کامل Deploy و Git Workflow

## ✅ کارهای انجام شده

### فایل‌های ایجاد شده:
1. ✅ `deploy.ps1` - اسکریپت Deploy به VPS (با پشتیبانی Git Pull)
2. ✅ `use_local.ps1` - تنظیم Environment برای لوکال
3. ✅ `use_production.ps1` - تنظیم Environment برای Production
4. ✅ `setup_env_files.ps1` - ایجاد فایل‌های Environment
5. ✅ `GIT_DEPLOY_SETUP.md` - راهنمای کامل

### فایل‌های به‌روزرسانی شده:
1. ✅ `start_project.ps1` - اضافه شدن auto-detect برای .env
2. ✅ `.gitignore` - اضافه شدن `.env.production` و `in vps/`
3. ✅ `deploy.ps1` - استفاده از Git Pull به جای ZIP

### Git Repository:
- ✅ Git repository راه‌اندازی شد
- ✅ Remote به GitHub اضافه شد: `https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git`

---

## 📋 مراحل استفاده

### 1️⃣ تنظیم اولیه (فقط یک بار)

```powershell
# ایجاد فایل‌های Environment
.\setup_env_files.ps1

# ویرایش .env.production (مهم!)
notepad .env.production
# - SECRET_KEY را تغییر دهید
# - تمام API keys را وارد کنید
```

### 2️⃣ استفاده روزانه (توسعه روی لوکال)

```powershell
# تنظیم Environment برای لوکال
.\use_local.ps1

# راه‌اندازی پروژه
.\start_project.ps1
```

### 3️⃣ Deploy به VPS

```powershell
# فقط یک دستور!
.\deploy.ps1
```

اسکریپت به صورت خودکار:
1. ✅ تغییرات را commit می‌کند
2. ✅ به GitHub push می‌کند
3. ✅ روی VPS از GitHub pull می‌کند
4. ✅ وابستگی‌ها را نصب می‌کند
5. ✅ Migrations را اجرا می‌کند
6. ✅ سرویس‌ها را راه‌اندازی می‌کند

---

## 🔄 Workflow کامل

```
┌─────────────────────────────────┐
│  توسعه روی لوکال                 │
│  1. .\use_local.ps1             │
│  2. .\start_project.ps1         │
│  3. کد نویسی و تست              │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Commit و Push به GitHub         │
│  (خودکار در deploy.ps1)         │
│  یا دستی:                       │
│  git add .                      │
│  git commit -m "..."            │
│  git push origin main           │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  Deploy به VPS                   │
│  .\deploy.ps1                    │
│  (خودکار Pull از GitHub)        │
└─────────────────────────────────┘
```

---

## 📝 دستورات Git

### Push تغییرات به GitHub:

```powershell
# اضافه کردن تغییرات
git add .

# Commit
git commit -m "Feature: توضیح تغییرات"

# Push
git push origin main
```

### دریافت تغییرات از GitHub:

```powershell
# Pull تغییرات
git pull origin main
```

### مشاهده وضعیت:

```powershell
# وضعیت فایل‌ها
git status

# تاریخچه commits
git log --oneline

# تفاوت‌ها
git diff
```

---

## 🔧 تنظیمات روی VPS (فقط یک بار)

روی VPS این دستورات را اجرا کنید:

```powershell
# نصب Git (اگر نصب نشده)
winget install Git.Git

# تنظیم Git (یک بار)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Clone پروژه (فقط یک بار - اگر از قبل clone نشده)
cd C:\
git clone https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git SmartAITradingStrategyOptimizer

# ایجاد .env.production (یک بار)
cd C:\SmartAITradingStrategyOptimizer
Copy-Item env.example .env.production
notepad .env.production  # ویرایش و تنظیم
```

**⚠️ مهم:** فایل `.env.production` را روی VPS ایجاد کنید و تنظیمات VPS را وارد کنید.

---

## 🎯 تفاوت‌های Environment

| تنظیم | `.env.local` | `.env.production` |
|------|-------------|-------------------|
| `DEBUG` | `True` | `False` |
| `ENV` | `LOCAL` | `PRODUCTION` |
| `PUBLIC_IP` | خالی | `191.101.113.163` |
| `FRONTEND_URL` | `http://localhost:3000` | `http://191.101.113.163:3000` |
| `BACKEND_URL` | `http://localhost:8000` | `http://191.101.113.163:8000` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,*` | `191.101.113.163,localhost,127.0.0.1` |
| Database | SQLite (خودکار) | PostgreSQL (اگر تنظیم کنید) |

---

## ✅ چک‌لیست قبل از Deploy

- [ ] فایل `.env.production` ایجاد و تنظیم شده است
- [ ] `SECRET_KEY` در `.env.production` تغییر کرده است
- [ ] `DEBUG=False` در Production
- [ ] `PUBLIC_IP=191.101.113.163` تنظیم شده است
- [ ] تمام API keys در `.env.production` وارد شده‌اند
- [ ] Git remote تنظیم شده است (`git remote -v`)
- [ ] تغییرات commit شده‌اند

---

## 🐛 مشکلات رایج

### "Git remote تنظیم نشده است"
```powershell
git remote add origin https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git
```

### "Push به GitHub ناموفق بود"
- بررسی کنید Personal Access Token دارید
- یا از SSH key استفاده کنید

### "Cannot connect to VPS"
```powershell
Test-NetConnection -ComputerName 191.101.113.163 -Port 7230
```

### "Git روی VPS نصب نشده است"
```powershell
# روی VPS
winget install Git.Git
```

---

## 📞 دسترسی به پروژه

بعد از Deploy موفق:

- **Backend API**: http://191.101.113.163:8000
- **Frontend**: http://191.101.113.163:3000
- **Admin Panel**: http://191.101.113.163:8000/admin

---

**🎉 همه چیز آماده است! برای شروع، `.\setup_env_files.ps1` را اجرا کنید.**


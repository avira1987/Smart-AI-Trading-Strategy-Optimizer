# AI Forex Strategy Manager

A complete production-ready system for managing Forex trading strategies with AI-powered parsing, backtesting, and demo trading capabilities.

## Features

- **API Integration**: Connect multiple data providers (TwelveData, MetalsAPI, OANDA)
- **Strategy Management**: Upload and manage text-based trading strategies
- **AI Module**: Placeholder for NLP-based strategy parsing
- **Backtesting**: Test strategies against historical data
- **Demo Trading**: Simulate live trading with demo accounts
- **Performance Analytics**: View detailed results with charts and metrics
- **Cost Optimized**: Designed for low-budget, single-developer use

## Project Structure

```
SmartAITradingStrategyOptimizer/
├── backend/              # Django Backend Application
│   ├── tests/           # All test files
│   ├── ai_module/       # AI and NLP modules
│   ├── api/             # API endpoints and views
│   ├── config/          # Django settings
│   └── core/            # Core models and migrations
├── frontend/            # React Frontend Application
├── docs/                # All documentation files
├── scripts/             # All executable scripts (.ps1, .bat, .sh)
├── README.md            # Main documentation
└── ...
```

**Note**: The project structure has been reorganized for better maintainability:
- All documentation files are in `docs/`
- All scripts are in `scripts/`
- All test files are in `backend/tests/`

For detailed structure information, see `docs/PROJECT_STRUCTURE.md`.

## Architecture

### Backend
- **Django** with Django REST Framework
- **PostgreSQL** for production, SQLite for local development
- **Celery + Redis** for asynchronous task processing
- **Data caching** to minimize API calls

### Frontend
- **React + TypeScript**
- **TailwindCSS** with dark mode
- **Chart.js** for performance visualization
- **Vite** for fast development and optimized builds

### Infrastructure
- **Docker Compose** for local development
- **Gunicorn** for production WSGI server
- **Nginx** for serving frontend and proxying API requests

## آموزش: جریان «دریافت داده → پردازش → بهینه‌سازی»

این بخش تصویری کلی از فرایند هوشمند سیستم ارائه می‌دهد تا بدانید هنگام فشردن دکمه «پردازش» دقیقاً چه مراحلی رخ می‌دهد و چه تنظیماتی اهمیت دارند.

1. **پیکربندی کلیدهای API**
   - **ثبت کلیدهای داده**: در صفحه مدیریت API ابتدا کلیدهای FinancialModelingPrep، TwelveData، MetalsAPI و سایر منابع داده را فعال کنید. هر کلید می‌تواند از طریق Environment یا مدل `APIConfiguration` ثبت شود؛ سیستم به صورت خودکار جدیدترین کلید فعال را تشخیص می‌دهد.
   - **ثبت کلیدهای هوش مصنوعی**: کلیدهای OpenAI/ChatGPT، Gemini و سایر LLM ها را وارد کنید. کلاس `AIProviderManager` تمام نام‌های مستعار مانند `chatgpt`, `gpt`, `gpt-4` را هم به عنوان OpenAI تشخیص می‌دهد و بر اساس ترتیب اولویت در تنظیمات `AI_PROVIDER_PRIORITY` آن‌ها را امتحان می‌کند.
   - **مانیتورینگ صحت کلیدها**: پس از ثبت، از دکمه «تست» در داشبورد استفاده کنید یا لاگ‌های سیستم (`api_usage_tracker`) را بررسی کنید تا مطمئن شوید درخواست‌ها با موفقیت پاسخ می‌گیرند. پیام‌های شکست شامل علت دقیق (مثلاً «missing_api_key») ثبت می‌شوند.

2. **آپلود و مدیریت استراتژی**
   - **بارگذاری فایل**: در تب «استراتژی‌های معاملاتی» فایل متنی استراتژی را آپلود کنید. سیستم فایل را ذخیره کرده و وضعیت اولیه را `not_processed` قرار می‌دهد.
   - **مدیریت فعال بودن**: با دکمه «فعال/غیرفعال» می‌توانید مشخص کنید کدام استراتژی در فهرست نشان داده شود یا در ماژول‌های دیگر قابل انتخاب باشد.
   - **استراتژی اصلی**: دکمه «استراتژی اصلی» اکنون عمل toggle دارد؛ یعنی اگر استراتژی از قبل اصلی باشد با کلیک دوباره غیرفعال می‌شود. بک‌تست رسمی تنها زمانی اجازه اجرا دارد که حداقل یک استراتژی اصلی موجود باشد، بنابراین انتخاب دقیق این مورد حائز اهمیت است.
   - **پیگیری خطاها**: اگر پردازش یا بک‌تست با شکست مواجه شود، پیام خطا در فیلد `processing_error` و توست‌های رابط کاربری ثبت شده و برای بررسی بعدی قابل مشاهده است.

3. **فشار دادن دکمه «پردازش»**
   - **تحلیل متن استراتژی**: ماژول `nlp_parser` فایل را می‌خواند و خروجی ساخت‌یافته (entry/exit، مدیریت ریسک، اندیکاتورها، تایم‌فریم، نماد و …) در `parsed_strategy_data` ذخیره می‌شود.
   - **فراخوانی هوش مصنوعی با اولویت ChatGPT**: تابع `analyze_strategy_with_gemini` ابتدا از طریق `AIProviderManager` تلاش می‌کند پاسخ JSON را از ChatGPT/OpenAI دریافت کند. در صورت موفقیت، مدل و نتیجه ثبت می‌شود؛ در غیر این صورت، سیستم به ترتیب سراغ Gemini و سایر ارائه‌دهنده‌ها می‌رود و در آخر «تحلیل پایه» تولید می‌کند. تمام دلایل fallback در `analysis_sources` ذخیره و در داشبورد نشان داده می‌شوند.
   - **دریافت داده بازار**: `DataProviderManager.get_historical_data` نماد را نرمال می‌کند، اگر ارائه‌دهنده‌ی ترجیحی تعیین شده باشد آن را امتحان می‌کند و در صورت نیاز بین ارائه‌دهنده‌ها جابه‌جا می‌شود. برای نمادهای طلا، آخرین قیمت لحظه‌ای MetalsAPI نیز ضمیمه داده تاریخی می‌شود تا بک‌تست به‌روز باشد. نام ارائه‌دهنده و تعداد نقاط داده در `analysis_sources.data_sources` ثبت می‌شود.
   - **به‌روزرسانی وضعیت**: پس از اتمام، وضعیت پردازش به `processed` تغییر می‌کند، زمان شروع/پایان پردازش ذخیره می‌شود و رابط کاربری توست موفقیت نمایش می‌دهد.

4. **بهینه‌سازی ژنتیک و بک‌تست طلا**
   - **آماده‌سازی داده‌ها**: اگر داده‌ی تاریخی کافی وجود داشته باشد، ابتدا بک‌تست پایه با همان پارامترهای استخراج‌شده انجام می‌شود تا معیار مرجع (return، sharpe، win rate و …) در دسترس باشد.
   - **اجرای الگوریتم ژنتیک**: `OptimizationEngine.optimize` با تنظیمات `method='dl'` و `dl_method='neural_evolution'` اجرا می‌شود. جمعیت اولیه با تغییرات تصادفی پیرامون پارامترهای موجود ساخته و طی اپیزودهای پی‌درپی انتخاب، crossover و mutation انجام می‌شود.
   - **حاصل نهایی**: بهترین پارامترها، تاریخچه مختصر نسل‌ها، امتیاز شارپ و نتایج بک‌تست پایه/بهینه در `parsed_strategy_data.genetic_optimization` ذخیره می‌شوند. این اطلاعات برای مقایسه در رابط کاربری و گزارش‌دهی استفاده می‌شود.
   - **مدیریت خطا**: اگر داده‌ی تاریخی یافت نشود یا خطایی در فرآیند رخ دهد، وضعیت `genetic_optimization` برابر `error` یا `no_data` ثبت می‌شود تا کاربر از طریق رابط کاربری مطلع گردد.

5. **نکته تکمیلی: اجبار به استراتژی اصلی برای بک‌تست**
   - **منطق اعتبارسنجی**: قبل از ساخت Job جدید با نوع «backtest»، کنترل می‌شود که حداقل یک استراتژی اصلی در پایگاه داده وجود دارد و همان استراتژی انتخابی نیز `is_primary=True` باشد.
   - **هدف این محدودیت**: این شرط از اجرای بک‌تست روی استراتژی‌های آزمایشی یا ناقص جلوگیری کرده و تضمین می‌کند نتایج رسمی همیشه بر اساس آخرین استراتژی تأیید شده محاسبه شوند.
   - **پیام‌رسانی به کاربر**: در صورت عدم رعایت شرایط، API پاسخ خطای مشخص (همراه با متن فارسی راهنمای اقدام بعدی) می‌دهد و رابط کاربری پیام مناسب را نمایش می‌دهد تا کاربر استراتژی اصلی را تغییر دهد یا ابتدا استراتژی‌ای را به عنوان اصلی تعیین کند.

> **یادآوری**: برای اجرای تست‌های خودکار باید محیط مجازی Python (`venv`) سالم باشد. در وضعیت فعلی مسیر مفسر اصلی در ویندوز حذف شده است؛ قبل از اجرای `pytest`، `venv` را بازسازی یا مسیر Python را اصلاح کنید.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)
- Node.js 18+ (for frontend development)
- تمام وابستگی‌های Python در `backend/requirements.txt` با نسخه دقیق قفل شده‌اند؛ لطفاً از همین فایل برای استقرار Production (`pip install -r backend/requirements.txt`) استفاده کنید.

### Local Development with Docker

1. **Clone the repository**
```bash
git clone <repository-url>
cd Smart-AI-Trading-Strategy-Optimizer
```

2. **Set up environment variables**
```bash
cp env.example .env
# Edit .env with your API keys
```

3. **Start all services**
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin

### Local Development without Docker

**Quick Start Scripts** (Windows):
```powershell
# Start all services
.\scripts\START_ALL.ps1

# Or start individually
.\scripts\start_backend.ps1
.\scripts\start_frontend.ps1
```

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start Django server
python manage.py runserver

# In another terminal, start Celery worker
celery -A config worker --loglevel=info
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at http://localhost:3000

## Deployment

### Backend to Render

1. Push your code to GitHub
2. Connect your repository to Render
3. Use the provided `render.yaml` configuration
4. Set environment variables in Render dashboard

### Frontend to Vercel

1. Push your code to GitHub
2. Connect your repository to Vercel
3. Use the provided `vercel.json` configuration
4. Set environment variables in Vercel dashboard
5. Update the `vercel.json` rewrite destination URL to point to your Render backend

### Deployment to Chabokan Cloud

چابکان سه سرویس اصلی (Python/Django، Node.js و Docker) را در قالب پلن‌های جداگانه ارائه می‌کند. ترکیب پیشنهادی:

1. **سرویس Django**
   - پلتفرم: `django`
   - نسخه Python: 3.11
   - حجم پیشنهادی: حداقل `0.5 vCPU / 0.5 GB RAM / 5 GB Disk` (برای بار متوسط 1 vCPU و 1 GB مطمئن‌تر است)
   - دستور Build: `pip install -r backend/requirements.txt && python backend/manage.py migrate && python backend/manage.py collectstatic --noinput`
   - دستور Start: `cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
   - متغیرها:
     - `SECRET_KEY`، `DEBUG=False`, `ENV=PRODUCTION`
     - `DATABASE_URL` یا `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
     - `REDIS_URL`, `CELERY_BROKER_URL`
     - `ADMIN_NOTIFICATION_PHONES` (لیست شماره‌های موبایل برای هشدارها)
     - کلیدهای API (TwelveData، FinancialModelingPrep، OANDA، MetalsAPI، Gemini و ...)

2. **سرویس Node.js (فرانت‌اند React)**
   - پلتفرم: `nodejs` (Node 18)
   - دستور Build: `npm ci && npm run build`
   - دستور Start (یکی را انتخاب کنید):
     - استفاده از Vite Preview: `npm run preview -- --port $PORT --host 0.0.0.0`
     - یا استفاده از بسته `serve`: `npx serve -s dist -l $PORT`
   - منابع پیشنهادی: `0.25 vCPU / 0.5 GB RAM / 5 GB Disk`

3. **سرویس Docker برای Redis**
   - پلتفرم: `docker`
   - تصویر پیشنهادی: `redis:7-alpine`
   - پورت: `6379`
   - حجم پیشنهادی: `0.15 vCPU / 0.25 GB RAM / 2 GB Disk`
   - مقدار `REDIS_URL` و `CELERY_BROKER_URL` را در سرویس Django به `redis://<redis_service_host>:6379/0` تنظیم کنید.

#### استفاده از CLI چابکان

```bash
npm install -g @cloudiva.net/cli
cloudiva login
cloudiva init
cloudiva deploy
```

**نکته:** قبل از `cloudiva deploy` فایل‌های کانفیگ (`backend/requirements.txt`, `render.yaml`, `docker-compose.yml`) را بررسی کنید تا با پلن انتخابی همخوان باشند.

## API Endpoints

### API Configurations
- `GET /api/apis/` - List all API configurations
- `POST /api/apis/` - Add new API configuration
- `PUT /api/apis/{id}/` - Update API configuration
- `DELETE /api/apis/{id}/` - Delete API configuration
- `POST /api/apis/{id}/test/` - Test API connection

### Trading Strategies
- `GET /api/strategies/` - List all strategies
- `GET /api/strategies/{id}/` - Get strategy details
- `POST /api/strategies/` - Upload new strategy (multipart/form-data)
- `DELETE /api/strategies/{id}/` - Delete strategy
- `GET /api/strategies/{id}/download/` - Download strategy file

### Jobs
- `GET /api/jobs/` - List all jobs
- `GET /api/jobs/{id}/` - Get job details
- `POST /api/jobs/` - Create new job (backtest or demo trade)
- `GET /api/jobs/{id}/status/` - Get job status

### Results
- `GET /api/results/` - List all backtest results
- `GET /api/results/{id}/` - Get result details
- `GET /api/results/summary/` - Get summary of all results

## Cost Optimization Features

1. **Free API Tiers**: Uses free tiers of data providers
2. **Data Caching**: Caches market data locally (SQLite) to minimize API calls
3. **SQLite for Local Dev**: No database cost in development
4. **Optimized Docker Images**: Uses slim Python and Alpine images
5. **Static File Caching**: Long-term caching of static assets
6. **Celery Task Batching**: Efficient task processing

## AI Module

The AI module (`/backend/ai_module/`) contains placeholders for:
- `nlp_parser.py`: Text-based strategy parsing using NLP
- `optimizer.py`: Hyperparameter optimization using Optuna

### Gemini (Google) Hybrid NLP Parsing

The parser uses a cost-optimized hybrid approach:
- First, a fast local regex/keyword parser extracts `entry_conditions`, `exit_conditions`, `risk_management`, `timeframe`, `symbol`, `indicators`.
- If confidence is low or key sections are missing, it calls Google Gemini to fill gaps and returns a compact JSON. Results are cached to reduce API costs.

Configuration (set in `.env`):
```bash
GEMINI_ENABLED=True
GEMINI_API_KEY=your_google_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
GEMINI_MAX_OUTPUT_TOKENS=8000
```

Notes:
- Gemini integration is optional. اگر کلید API تنظیم نشده باشد، سرویس پیام «AI analysis unavailable. Please configure your AI provider (OpenAI ChatGPT or Gemini) in Settings.» را برمی‌گرداند و سیستم با تحلیل پایه ادامه می‌دهد.
- تمام پاسخ‌های Gemini در ساختار JSON استاندارد (`entry_conditions`, `exit_conditions`, `risk_management`, `ai_status`, `raw_output`) بازگردانده می‌شوند تا در فرانت‌اند و تست‌ها به سادگی پردازش شوند.
- ورودی‌ها حوالی ۳۲٬۰۰۰ توکن (حدود ۱۲۸هزار کاراکتر) قطع می‌شوند و خروجی حداکثر ۸٬۰۰۰ توکن است تا هزینه و ریسک خطا کاهش یابد.
- حداکثر ۶۰ فراخوانی در دقیقه پذیرفته می‌شود و نتایج تحلیل تا ۲۴ ساعت در کش فایل ذخیره می‌شود تا از هزینه‌های تکراری جلوگیری شود.
- در صورت بروز خطا، پیام مناسب («Gemini service temporarily unavailable.») به کاربر نمایش داده می‌شود و تحلیل پایه جایگزین می‌گردد.
- A local file cache in `backend/cache/gemini/` prevents repeated calls for the same text.

### Multiple AI Providers

اکنون علاوه بر Gemini می‌توانید از OpenAI (ChatGPT)، Cohere، OpenRouter، Together AI، DeepInfra و GroqCloud نیز استفاده کنید. هر ارائه‌دهنده را در صفحهٔ «تنظیمات API» ثبت کنید یا در `.env` مقداردهی کنید:

```
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
COHERE_API_KEY=...
OPENROUTER_API_KEY=...
TOGETHER_API_KEY=...
DEEPINFRA_API_KEY=...
GROQ_API_KEY=...
AI_PROVIDER_PRIORITY=openai,gemini,cohere,openrouter,together_ai,deepinfra,groq
```

سامانه به ترتیب `AI_PROVIDER_PRIORITY` تلاش می‌کند تا پاسخ JSON دریافت کند؛ در صورت خطای یکی از سرویس‌ها (مثلاً محدودیت نرخ یا عدم دسترسی) به سرویس بعدی می‌رود و تمام تلاش‌ها با جزئیات در `AI_USAGE_LOG` و پیامک هشدار (در صورت فعال‌سازی) ثبت می‌شود.

## Development Guidelines

### Adding New Features

1. **Backend**: Add models in `core/models.py`, create API endpoints in `api/views.py`
2. **Frontend**: Add new components in `src/components/`, update pages in `src/pages/`
3. **Tasks**: Add Celery tasks in `api/tasks.py`

### Database Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Create migration for specific app
python manage.py makemigrations api
```

### Testing

```bash
# Run tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## Troubleshooting

### Backend Issues
- Check Redis is running: `docker-compose ps`
- Check logs: `docker-compose logs backend`
- Restart services: `docker-compose restart backend`

### Frontend Issues
- Clear cache: `npm cache clean --force`
- Reinstall dependencies: `rm -rf node_modules && npm install`
- Check browser console for errors

### Database Issues
- Reset database: `docker-compose down -v` then `docker-compose up`

### Data Provider Alerts
- متغیر `ADMIN_NOTIFICATION_PHONES` را با لیست شماره‌های ادمین (جدا شده با ویرگول) تنظیم کنید تا در صورت انقضای کلیدهای داده یا خطاهای مکرر، پیامک هشدار ارسال شود.
- سرویس پیامک به Kavenegar وابسته است؛ حتماً `KAVENEGAR_API_KEY` و در صورت نیاز `KAVENEGAR_SENDER` را تنظیم کنید.
- سامانه برای هر ارائه‌دهنده (TwelveData، AlphaVantage، OANDA، MetalsAPI، FinancialModelingPrep) در صورت دریافت خطاهای ۴۰۱/۴۰۳/۴۲۹ یا نبود کلید معتبر، یک هشدار ثبت می‌کند و در هر ساعت فقط یک‌بار ادمین را مطلع می‌سازد.

## License

MIT License - See LICENSE file for details

## Managed Setup Option

اگر قصد دارید بدون درگیری با تنظیم APIها و استقرار اولیه از سامانه استفاده کنید، می‌توانید با شارژ حساب به مبلغ **۳۹۹٬۰۰۰ تومان** نسخه آمادهٔ تحلیل و تست استراتژی را به همراه یک ماه پشتیبانی (آنلاین و تلفنی) دریافت کنید. در این نسخه:

- تمامی APIهای داده (TwelveData، FinancialModelingPrep، MetalsAPI، OANDA و ...) فعال و متصل می‌شوند.
- کلید Google Gemini در سامانه ثبت می‌شود و تحلیل هوش مصنوعی بدون وقفه در دسترس است.
- Redis، Celery و دیتابیس PostgreSQL روی هاست چابکان یا سرور اختصاصی شما راه‌اندازی و تست می‌شوند.
- در صورت انقضای کلیدها یا اتمام اعتبار رایگان، ادمین از طریق پیامک هشدار دریافت خواهد کرد.

برای هماهنگی بیشتر از تیکت «پشتیبانی ویژه ۳۹۹K» استفاده کنید.

## Support

For issues and questions, please open an issue on the GitHub repository.


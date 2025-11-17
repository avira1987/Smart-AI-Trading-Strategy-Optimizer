You are an expert full-stack AI and trading system architect.  
Create a complete production-ready, cost-optimized system called **AI Forex Strategy Manager**.  
The project allows a user to connect forex data APIs, upload text-based trading strategies, backtest them locally, and later deploy to cloud for live demo trading.

---

## 🔹 Project Goals
- Build a **Django REST Framework backend** for managing APIs, strategies, and jobs.
- Build a **React + TailwindCSS frontend dashboard** for configuration and monitoring.
- Add a **Celery + Redis worker engine** for backtesting and running demo trades.
- Include a modular **AI parser** placeholder for converting text strategies into logic.
- All infrastructure **must run on Docker Compose**.
- Implement all **cost optimization strategies** for a single-developer, low-budget setup.

---

## 🔹 Architecture Overview

**Backend (Django REST + Celery)**
- API endpoints:
  - `/api/apis/` → Add/edit API keys for TwelveData, MetalsAPI, OANDA (mock for now)
  - `/api/strategies/` → Upload and list text-based strategies
  - `/api/jobs/` → Run backtest or demo trade
  - `/api/results/` → Retrieve results from DB
- Use PostgreSQL in production, SQLite in local dev.
- Cache market data locally to avoid redundant API calls.
- Celery workers execute backtests asynchronously.
- Basic error handling and logging.

**Frontend (React + TailwindCSS)**
- Dashboard page:
  - Display connected APIs and status
  - Add/edit API keys
  - Upload new strategy (text file)
  - Buttons to run “Backtest” or “Demo Trade”
- Results page:
  - Show performance table + small chart (using Chart.js)
- Dark mode enabled by default.

**AI Module (placeholder)**
- Folder `/backend/ai_module/`
- File `nlp_parser.py` with stub for parsing text strategies.
- File `optimizer.py` with basic Optuna structure ready for future tuning.

**Infra**
- `docker-compose.yml` → services: backend, frontend, redis, db
- `Dockerfile` for both backend and frontend.
- `.env.example` for all API keys and local variables.
- `README.md` with setup instructions for local + Render/Vercel deployment.

---

## 🔹 Cost Optimization Requirements (MUST APPLY IN CODE)

1. Use free API tiers (TwelveData, MetalsAPI).
2. Implement caching of market data in `/cache/` folder using SQLite or Redis.
3. Use SQLite by default for local development (`ENV=LOCAL`).
4. Use Redis locally only (no paid Redis cloud service).
5. Configure Celery to use local Redis queue.
6. Optimize Dockerfile for minimal image size (use Python slim image).
7. Provide `vercel.json` config for frontend deployment to free plan.
8. Provide Render deploy configuration for backend.
9. Provide lightweight local test dataset to avoid external calls when offline.

---

## 🔹 Backend File Structure


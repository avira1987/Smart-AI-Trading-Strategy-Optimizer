# Smart AI Trading Strategy Optimizer

---

## 1. Project File Tree

```none
SmartAITradingStrategyOptimizer/
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   ├── smart_trading/
│   │   ├── __init__.py
│   │   ├── celery.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── parser.py
│   │   ├── data_loader.py
│   │   ├── technical_indicators.py
│   │   ├── backtest_engine.py
│   │   ├── ai_optimizer.py
│   │   ├── tasks.py
│   │   ├── serializers.py
│   │   ├── tests.py
│   │   └── views.py
│   └── ...
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── index.css
│       ├── components/
│       │   ├── Dashboard.tsx
│       │   ├── ResultsView.tsx
│       │   └── ...
│       └── api/
│           └── api.ts
├── docker-compose.yml
├── .env.example
├── README.md
├── QUICKSTART.md
└── sample_strategies/
    ├── rsi_simple.txt
    ├── macd_sma_cross.txt
    └── gold_trendbreak.txt
```

---

## 2. Major Files Summary

### Backend

- `backend/Dockerfile`: Django + gunicorn build, optimized for slim images.
- `smart_trading/settings.py`: Django/DRF, DB, Redis, CORS, Celery, file uploads.
- `celery.py`: Configures Celery worker with Redis.
- `strategies/models.py`: Models for Strategy, Job, Result, APIConfig.
- `strategies/parser.py`: Parses human-readable strategy rules into logical structures.
- `strategies/data_loader.py`: Market data fetching (TwelveData, MetalsAPI, MT5) with caching.
- `strategies/technical_indicators.py`: Computes indicators using `pandas-ta`.
- `strategies/backtest_engine.py`: Executes a backtest based on parsed logic and indicator data.
- `strategies/tasks.py`: Celery tasks (e.g., running backtest pipeline).
- `strategies/views.py`: DRF API endpoints for all main operations.
- `requirements.txt`: Includes Django, DRF, Celery, Redis, pandas, pandas-ta, psycopg2, etc.

### Frontend

- `frontend/Dockerfile`: Node+React+TailwindJS build, optimized for production.
- `src/components/Dashboard.tsx`: API keys, strategy upload, job control, dark mode toggle.
- `src/components/ResultsView.tsx`: Table/chart of backtest results and job statuses.
- `src/api/api.ts`: API abstraction for backend endpoints.
- `tailwind.config.js`: Tailwind theme (with dark mode support).

### Deployment & Root

- `docker-compose.yml`: Orchestrates backend, frontend, Redis, Postgres DB.
- `.env.example`: Template for sensitive variables.
- `README.md` and `QUICKSTART.md`: Setup, dev, and usage instructions.
- `sample_strategies/`: Example plain-text strategies.

---

## 3. Core Code Snippets

---

### backend/strategies/models.py

```python
from django.db import models

class TradingStrategy(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='strategies/')
    created_at = models.DateTimeField(auto_now_add=True)

class Job(models.Model):
    STATUS_CHOICES = [("pending", "Pending"), ("running", "Running"), ("completed", "Completed"), ("failed", "Failed")]
    strategy = models.ForeignKey(TradingStrategy, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

class Result(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    profit = models.FloatField()
    drawdown = models.FloatField()
    win_rate = models.FloatField()
    total_trades = models.IntegerField()
    equity_curve = models.JSONField()

class APIConfig(models.Model):
    API_TYPE_CHOICES = [("twelvedata", "TwelveData"), ("metalsapi", "MetalsAPI"), ("mt5", "MT5")]
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    api_type = models.CharField(max_length=20, choices=API_TYPE_CHOICES)
    api_key = models.CharField(max_length=256)
    meta = models.JSONField(default=dict, blank=True)
```

---

### backend/strategies/parser.py

```python
def parse_strategy_file(file_path):
    """
    Reads the strategy file and extracts trading rules.
    Rules must be in the format:
    "if RSI < 30 then Buy"
    Returns structured Python dict.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()
    rules = []
    for line in lines:
        # Very simple parser: can later replace with NLP
        line = line.strip()
        if line.lower().startswith('if'):
            parts = line.lower().split('then')
            condition, action = parts[0][3:].strip(), parts[1].strip()
            rules.append({"condition": condition, "action": action})
    return {"rules": rules}
```

---

### backend/strategies/data_loader.py

```python
import pandas as pd
import requests, os, pickle, time

def fetch_twelvedata(symbol, interval, apikey, start, end):
    cache_file = f".cache_{symbol}_{interval}_{start}_{end}.pkl"
    if os.path.exists(cache_file) and time.time() - os.path.getmtime(cache_file) < 3600:
        return pd.read_pickle(cache_file)
    url = f"https://api.twelvedata.com/time_series"
    params = {'symbol': symbol, 'interval': interval, 'apikey': apikey, 'start_date': start, 'end_date': end, 'format': 'JSON'}
    r = requests.get(url, params=params)
    df = pd.DataFrame(r.json()['values'])
    df.to_pickle(cache_file)
    return df

# Similar logic for MetalsAPI and MT5 with local caching.
```

---

### backend/strategies/technical_indicators.py

```python
import pandas as pd
import pandas_ta as ta

def add_indicators(df):
    df['rsi'] = ta.rsi(df['close'], length=14)
    df['macd'] = ta.macd(df['close'])['MACD_12_26_9']
    df['sma'] = ta.sma(df['close'], length=14)
    df['ema'] = ta.ema(df['close'], length=14)
    # ...other indicators
    return df
```

---

### backend/strategies/backtest_engine.py

```python
def backtest_strategy(df, rules):
    # Very basic example
    equity = [10000]
    position = None
    for i, row in df.iterrows():
        for rule in rules:
            # Evaluate rule condition, act if triggered
            if eval(rule['condition'], {}, dict(row)):
                if rule['action'].lower() == 'buy' and position is None:
                    position = float(row['close'])
                elif rule['action'].lower() == 'sell' and position:
                    pnl = float(row['close']) - position
                    equity.append(equity[-1] + pnl)
                    position = None
    return {
        "profit": equity[-1] - equity[0],
        "drawdown": min(equity) - equity[0],
        "win_rate": 0.5,  # placeholder
        "total_trades": len(equity)-1,
        "equity_curve": equity
    }
```

---

### backend/strategies/tasks.py

```python
from celery import shared_task

@shared_task
def run_backtest(job_id):
    # Load job, strategy, parse file.
    # Fetch data, compute indicators, run backtest, save result.
    ...
```

---

### backend/strategies/views.py

```python
from rest_framework import viewsets, status
from .models import TradingStrategy, Job, Result, APIConfig
from .serializers import *
from .tasks import run_backtest

class TradingStrategyViewSet(viewsets.ModelViewSet):
    queryset = TradingStrategy.objects.all()
    serializer_class = TradingStrategySerializer
    # Create, list, upload strategies

class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    # Starts backtests, checks job status.

# Other ViewSets for Result, APIConfig, and a ManualBacktest API endpoint.
```

---

### frontend/src/components/Dashboard.tsx

```tsx
import React, { useState } from "react";
import api from "../api/api";

const Dashboard = () => {
  // API key management, strategy upload, run backtest button, tabs.
  // Use Tailwind for dark/light mode UI.
  // ... (React hooks, forms, etc)
};
export default Dashboard;
```

---

### frontend/src/components/ResultsView.tsx

```tsx
import React, { useEffect, useState } from "react";
import Chart from "chart.js/auto";
import api from "../api/api";

const ResultsView = () => {
  // Fetch job/results from API, show table + equity chart
  // status badges, summarized metrics
  // ...
};
export default ResultsView;
```

---

### docker-compose.yml

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    command: gunicorn smart_trading.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - ./backend:/app/backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
  db:
    image: postgres:14-alpine
    env_file:
      - .env
    volumes:
      - pg_data:/var/lib/postgresql/data/
  redis:
    image: redis:latest
volumes:
  pg_data:
```

---

### .env.example

```env
DJANGO_SECRET_KEY=changeme
POSTGRES_DB=trading
POSTGRES_USER=trader
POSTGRES_PASSWORD=traderpass
REDIS_URL=redis://redis:6379/0
TWELVEDATA_APIKEY=yourkey
METALSAPI_APIKEY=yourkey
```

---

### sample_strategies/rsi_simple.txt

```none
if RSI < 30 then Buy
if RSI > 70 then Sell
```

---

## 4. Instructions to Run the Project Locally

**Summarized Quickstart:**

1. **Clone repo**
   `git clone https://github.com/youruser/SmartAITradingStrategyOptimizer.git`

2. **Set up environment:**
   - Copy `.env.example` to `.env`
     `cp .env.example .env`
   - Fill in your API keys (TwelveData, MetalsAPI, etc)

3. **Build and start services:**
   `docker-compose up --build`

4. **Access:**
   - Backend API: [http://localhost:8000/api/](http://localhost:8000/api/)
   - Frontend UI: [http://localhost:3000/](http://localhost:3000/)

5. **Run migrations, create superuser**
   In a new terminal:
   ```bash
   docker-compose exec backend bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Upload strategy files, add API keys in dashboard, run backtests!**

---

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

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)
- Node.js 18+ (for frontend development)

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
GEMINI_MAX_OUTPUT_TOKENS=512
```

Notes:
- The input to Gemini is truncated (~4000 chars) and output is forced to compact JSON to minimize tokens.
- A local file cache in `backend/cache/gemini/` prevents repeated calls for the same text.

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

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open an issue on the GitHub repository.


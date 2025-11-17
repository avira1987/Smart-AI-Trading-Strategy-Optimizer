# Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- Basic understanding of forex trading concepts

## Getting Started in 5 Minutes

### 1. Start the Application

```bash
# Copy environment file
cp env.example .env

# Start all services
docker-compose up --build
```

Wait for all services to start (this may take a few minutes the first time).

### 2. Access the Application

- **Dashboard**: http://localhost
- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin

### 3. Add Your First API Key

1. Go to http://localhost
2. Click "Add API Key" button
3. Select a provider (TwelveData, MetalsAPI, or OANDA)
4. Enter your API key
5. Click "Add"

### 4. Upload a Trading Strategy

1. Click "Upload Strategy" button
2. Enter a name and description
3. Upload a strategy file (text or markdown)
4. Click "Upload"

**Sample strategies** are available in `backend/sample_strategies/` folder.

### 5. Run Your First Backtest

1. Select a strategy from the list
2. Click "Run Backtest" button
3. Wait for the job to complete (check status in the top-right)
4. Go to the "Results" page to view results

### 6. View Results

1. Click "Results" in the navigation bar
2. Select a completed job from the list
3. View performance metrics and charts

## Common Tasks

### Add More API Keys

Go to Dashboard → Click "Add API Key" → Select provider → Enter key → Add

### Upload Multiple Strategies

Go to Dashboard → Click "Upload Strategy" → Enter details → Upload file

### Check Job Status

Jobs are listed in the Results page. Status indicators:
- 🟢 **Completed**: Job finished successfully
- 🟡 **Running**: Job is currently executing
- 🔴 **Failed**: Job encountered an error
- ⚪ **Pending**: Job is waiting to start

### View Detailed Metrics

1. Go to Results page
2. Click on any completed job
3. View:
   - Total Return
   - Win Rate
   - Total Trades
   - Max Drawdown
   - Equity Curve Chart

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
netstat -ano | findstr :80
netstat -ano | findstr :8000
netstat -ano | findstr :5432
netstat -ano | findstr :6379

# Stop and restart
docker-compose down
docker-compose up --build
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up --build
```

### Frontend Not Loading

```bash
# Check backend is running
curl http://localhost:8000/api/

# Check nginx logs
docker-compose logs frontend
```

### Backend Not Responding

```bash
# Check Django logs
docker-compose logs backend

# Check Celery worker
docker-compose logs backend | grep celery

# Restart backend
docker-compose restart backend
```

## Next Steps

1. **Read the full README.md** for detailed documentation
2. **Explore the API** using http://localhost:8000/api/
3. **Try different strategies** from the sample folder
4. **Customize strategies** to your needs
5. **Deploy to production** using Render + Vercel

## Support

For issues and questions:
- Check the README.md
- Review the API documentation
- Open an issue on GitHub

Happy trading!


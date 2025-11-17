#!/bin/bash
# Smart AI Trading Strategy Optimizer - Auto Deployment Script
# این اسکریپت پروژه را از GitHub دریافت کرده و راه‌اندازی می‌کند

set -e  # Exit on error

echo "========================================"
echo "  Smart AI Trading Strategy Optimizer"
echo "  Auto Deployment Script"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/avira1987/Smart-AI-Trading-Strategy-Optimizer.git"
BRANCH="main"
PROJECT_DIR="SmartAITradingStrategyOptimizer"

# Step 1: Clone or Pull
echo -e "${YELLOW}[1/9] Cloning/Pulling project from GitHub...${NC}"
if [ -d "$PROJECT_DIR" ]; then
    echo "  Project directory exists. Pulling latest changes..."
    cd "$PROJECT_DIR"
    git pull origin "$BRANCH"
    cd ..
else
    echo "  Cloning project..."
    git clone -b "$BRANCH" "$REPO_URL" "$PROJECT_DIR"
fi
echo -e "${GREEN}  ✓ Project updated${NC}"
echo ""

# Step 2: Check dependencies
echo -e "${YELLOW}[2/9] Checking dependencies...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  ✓ Python: $PYTHON_VERSION"
else
    echo -e "${RED}  ✗ Python 3 is not installed${NC}"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "  ✓ pip3 is available"
else
    echo -e "${RED}  ✗ pip3 is not installed${NC}"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "  ✓ Node.js: $NODE_VERSION"
else
    echo -e "${RED}  ✗ Node.js is not installed${NC}"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "  ✓ npm: $NPM_VERSION"
else
    echo -e "${RED}  ✗ npm is not installed${NC}"
    exit 1
fi

echo ""

# Step 3: Setup Backend
echo -e "${YELLOW}[3/9] Setting up Backend...${NC}"
cd "$PROJECT_DIR/backend"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "  Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "  Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}  ✓ Backend dependencies installed${NC}"
echo ""

# Step 4: Setup Environment Variables
echo -e "${YELLOW}[4/9] Setting up Environment Variables...${NC}"
cd ..

if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        echo "  Creating .env from env.example..."
        cp env.example .env
        
        # Generate SECRET_KEY
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
        
        # Update .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            sed -i '' "s/DEBUG=.*/DEBUG=False/" .env
            sed -i '' "s/ENV=.*/ENV=PRODUCTION/" .env
        else
            # Linux
            sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
            sed -i "s/DEBUG=.*/DEBUG=False/" .env
            sed -i "s/ENV=.*/ENV=PRODUCTION/" .env
        fi
        
        echo -e "${GREEN}  ✓ .env file created${NC}"
        echo -e "${YELLOW}  ⚠ Please edit .env file and add your API keys${NC}"
    else
        echo -e "${RED}  ✗ env.example not found${NC}"
    fi
else
    echo "  .env file already exists"
fi
echo ""

# Step 5: Run Migrations
echo -e "${YELLOW}[5/9] Running Database Migrations...${NC}"
cd backend
source venv/bin/activate
python manage.py migrate
echo -e "${GREEN}  ✓ Migrations completed${NC}"
echo ""

# Step 6: Collect Static Files
echo -e "${YELLOW}[6/9] Collecting Static Files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}  ✓ Static files collected${NC}"
echo ""

# Step 7: Setup Frontend
echo -e "${YELLOW}[7/9] Setting up Frontend...${NC}"
cd ../frontend

# Install dependencies
echo "  Installing Node.js dependencies..."
npm install

# Build frontend
echo "  Building frontend..."
npm run build

echo -e "${GREEN}  ✓ Frontend built${NC}"
echo ""

# Step 8: Check Redis
echo -e "${YELLOW}[8/9] Checking Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}  ✓ Redis is running${NC}"
    else
        echo -e "${YELLOW}  ⚠ Redis is not running. Please start Redis manually${NC}"
    fi
elif command -v docker &> /dev/null; then
    if docker ps | grep -q redis; then
        echo -e "${GREEN}  ✓ Redis container is running${NC}"
    else
        echo -e "${YELLOW}  ⚠ Redis container is not running. Starting Redis container...${NC}"
        docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 || echo "  Redis container might already exist"
    fi
else
    echo -e "${YELLOW}  ⚠ Redis is not available. Please install Redis or Docker${NC}"
fi
echo ""

# Step 9: Final Summary
echo -e "${YELLOW}[9/9] Deployment Summary...${NC}"
echo ""
echo -e "${GREEN}========================================"
echo "  ✓ Deployment Completed Successfully!"
echo "========================================${NC}"
echo ""
echo "Next Steps:"
echo ""
echo "1. Edit .env file and add your API keys:"
echo "   nano $PROJECT_DIR/.env"
echo ""
echo "2. Create superuser (optional):"
echo "   cd $PROJECT_DIR/backend"
echo "   source venv/bin/activate"
echo "   python manage.py createsuperuser"
echo ""
echo "3. Start services:"
echo ""
echo "   Backend (Terminal 1):"
echo "   cd $PROJECT_DIR/backend"
echo "   source venv/bin/activate"
echo "   gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"
echo ""
echo "   Frontend (Terminal 2):"
echo "   cd $PROJECT_DIR/frontend"
echo "   npx serve -s dist -l 3000"
echo ""
echo "   Celery Worker (Terminal 3):"
echo "   cd $PROJECT_DIR/backend"
echo "   source venv/bin/activate"
echo "   celery -A config worker --loglevel=info"
echo ""
echo "   Celery Beat (Terminal 4):"
echo "   cd $PROJECT_DIR/backend"
echo "   source venv/bin/activate"
echo "   celery -A config beat --loglevel=info"
echo ""
echo "Access URLs:"
echo "  - Backend API: http://$(hostname -I | awk '{print $1}'):8000"
echo "  - Frontend: http://$(hostname -I | awk '{print $1}'):3000"
echo "  - Admin Panel: http://$(hostname -I | awk '{print $1}'):8000/admin"
echo ""


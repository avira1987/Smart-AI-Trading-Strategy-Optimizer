# Start Django Backend Server
Write-Host "Starting Django Backend Server..." -ForegroundColor Green
cd backend
# Bind to 0.0.0.0 to allow access from local network
python manage.py runserver 0.0.0.0:8000
cd ..


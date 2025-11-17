# Start Redis using docker-compose
Write-Host "Starting Redis with docker-compose..." -ForegroundColor Cyan

# Check if docker-compose is available
try {
    $composeVersion = docker-compose --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "docker-compose is available: $composeVersion" -ForegroundColor Green
    } else {
        throw "docker-compose not found"
    }
} catch {
    Write-Host "docker-compose is not available. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "Alternative: Use start_redis.ps1 script instead" -ForegroundColor Yellow
    exit 1
}

# Start only Redis service
Write-Host "Starting Redis service..." -ForegroundColor Yellow
docker-compose up -d redis

# Wait for Redis to start
Write-Host "Waiting for Redis to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# Verify Redis is running
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "✓ Redis is running on localhost:6379" -ForegroundColor Green
} catch {
    Write-Host "⚠ Redis container started but connection failed. Please check manually." -ForegroundColor Yellow
    Write-Host "Try: docker-compose logs redis" -ForegroundColor Cyan
}

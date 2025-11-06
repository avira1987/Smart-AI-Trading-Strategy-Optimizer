# Start Redis with Docker
Write-Host "Starting Redis..." -ForegroundColor Cyan

# Check if Docker is available
$dockerAvailable = $false
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerAvailable = $true
        Write-Host "Docker is available: $dockerVersion" -ForegroundColor Green
    }
} catch {
    Write-Host "Docker is not available. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if Redis container already exists
$existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1
if ($existingContainer -eq "redis") {
    Write-Host "Redis container exists. Starting it..." -ForegroundColor Yellow
    docker start redis
} else {
    Write-Host "Creating Redis container..." -ForegroundColor Yellow
    docker run -d --name redis -p 6379:6379 redis:7-alpine
}

# Wait for Redis to start
Write-Host "Waiting for Redis to start..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# Verify Redis is running
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "✓ Redis is running on localhost:6379" -ForegroundColor Green
} catch {
    Write-Host "⚠ Redis container started but connection failed. Please check manually." -ForegroundColor Yellow
    Write-Host "Try: docker logs redis" -ForegroundColor Cyan
}

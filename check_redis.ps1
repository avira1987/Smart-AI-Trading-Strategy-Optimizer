# Check and Start Redis
$ErrorActionPreference = "Continue"

# First, check if Redis is already running
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    Write-Host "  OK Redis is running" -ForegroundColor Green
    exit 0
}
catch {
    Write-Host "  WARNING Redis is NOT running. Starting..." -ForegroundColor Yellow
}

# If we get here, Redis is not running - try to start it
# Check if Docker is available
$dockerAvailable = $false
try {
    $null = docker --version 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerAvailable = $true
    }
}
catch {
    # Docker check failed
}

if (-not $dockerAvailable) {
    Write-Host "  ERROR Docker is not available. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Docker is available, try to start Redis
# Check if Redis container already exists
$existingContainer = docker ps -a --filter "name=redis" --format "{{.Names}}" 2>&1 | Out-String
$existingContainer = $existingContainer.Trim()

if ($existingContainer -eq "redis") {
    Write-Host "    Starting existing container..." -ForegroundColor Cyan
    docker start redis 2>&1 | Out-Null
}
else {
    Write-Host "    Creating new container..." -ForegroundColor Cyan
    docker run -d --name redis -p 6379:6379 redis:7-alpine 2>&1 | Out-Null
}

# Wait for Redis to start
Start-Sleep -Seconds 5

# Verify Redis is now running
$redisStarted = $false
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 6379)
    $tcpClient.Close()
    $redisStarted = $true
}
catch {
    $redisStarted = $false
}

if ($redisStarted) {
    Write-Host "  OK Redis started successfully!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "  ERROR Error starting Redis" -ForegroundColor Red
    exit 1
}

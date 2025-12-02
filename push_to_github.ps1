# Script to push to GitHub using Personal Access Token
# Usage: 
#   $env:GITHUB_TOKEN = "your_token_here"
#   .\push_to_github.ps1
# OR
#   .\push_to_github.ps1 -Token "your_token_here"

param(
    [Parameter(Mandatory=$false)]
    [string]$Token
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitHub Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get token from parameter, environment variable, or user input
if ($Token) {
    $TokenPlain = $Token
    Write-Host "Using token from parameter" -ForegroundColor Gray
} elseif ($env:GITHUB_TOKEN) {
    $TokenPlain = $env:GITHUB_TOKEN
    Write-Host "Using token from environment variable" -ForegroundColor Gray
} else {
    Write-Host "Please enter your GitHub Personal Access Token:" -ForegroundColor Yellow
    Write-Host "(Make sure the token has 'repo' permissions and belongs to account: avira1987)" -ForegroundColor Gray
    Write-Host "Or set environment variable: `$env:GITHUB_TOKEN = 'your_token'" -ForegroundColor Gray
    $Token = Read-Host -AsSecureString
    $TokenPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Token)
    )
}

if ([string]::IsNullOrWhiteSpace($TokenPlain)) {
    Write-Host "Error: Token cannot be empty!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage options:" -ForegroundColor Yellow
    Write-Host "1. .\push_to_github.ps1 -Token 'your_token'" -ForegroundColor Cyan
    Write-Host "2. `$env:GITHUB_TOKEN = 'your_token'; .\push_to_github.ps1" -ForegroundColor Cyan
    exit 1
}

# Get the current remote URL
$remoteUrl = git remote get-url origin
Write-Host ""
Write-Host "Current remote URL: $remoteUrl" -ForegroundColor Cyan

# Extract repository path
if ($remoteUrl -match "github\.com[:/](.+?)(?:\.git)?$") {
    $repoPath = $matches[1]
    if (-not $repoPath.EndsWith(".git")) {
        $repoPath += ".git"
    }
    
    Write-Host "Repository: $repoPath" -ForegroundColor Cyan
    Write-Host ""
    
    # Update remote URL with token
    $newUrl = "https://$TokenPlain@github.com/$repoPath"
    Write-Host "Updating remote URL..." -ForegroundColor Yellow
    git remote set-url origin $newUrl
    
    # Push to GitHub
    Write-Host "Pushing to GitHub..." -ForegroundColor Green
    Write-Host ""
    
    git push origin main 2>&1 | Tee-Object -Variable pushOutput
    
    $pushSuccess = $LASTEXITCODE -eq 0
    
    # Restore original URL (without token for security)
    $originalUrl = "https://github.com/$repoPath"
    git remote set-url origin $originalUrl
    
    Write-Host ""
    
    if ($pushSuccess) {
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "Remote URL restored to original (token removed for security)" -ForegroundColor Cyan
    } else {
        Write-Host "========================================" -ForegroundColor Red
        Write-Host "Push failed!" -ForegroundColor Red
        Write-Host "========================================" -ForegroundColor Red
        Write-Host ""
        Write-Host "Possible reasons:" -ForegroundColor Yellow
        Write-Host "1. Token is invalid or expired" -ForegroundColor Yellow
        Write-Host "2. Token doesn't have 'repo' permissions" -ForegroundColor Yellow
        Write-Host "3. Token doesn't belong to account: avira1987" -ForegroundColor Yellow
        Write-Host "4. Repository is private and token doesn't have access" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To create a new token:" -ForegroundColor Cyan
        Write-Host "1. Go to: https://github.com/settings/tokens" -ForegroundColor Cyan
        Write-Host "2. Click 'Generate new token (classic)'" -ForegroundColor Cyan
        Write-Host "3. Select 'repo' scope" -ForegroundColor Cyan
        Write-Host "4. Generate and copy the token" -ForegroundColor Cyan
        exit 1
    }
} else {
    Write-Host "Error: Could not parse remote URL" -ForegroundColor Red
    exit 1
}

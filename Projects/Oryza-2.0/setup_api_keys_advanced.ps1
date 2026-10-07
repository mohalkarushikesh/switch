# Oryza API Keys Advanced Setup Script
# Requires PowerShell to run

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Oryza API Keys Advanced Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Function to generate secure random strings
function Generate-SecureKey {
    param([int]$length = 64)
    $bytes = New-Object byte[] $length
    $rng = [System.Security.Cryptography.RNGCryptoServiceProvider]::Create()
    $rng.GetBytes($bytes)
    $rng.Dispose()
    return [System.Convert]::ToBase64String($bytes)
}

# Check if .env exists
if (Test-Path ".env") {
    Write-Host "WARNING: .env file already exists!" -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to overwrite it? (y/n)"
    if ($overwrite -ne 'y') {
        Write-Host "Setup cancelled." -ForegroundColor Red
        exit
    }
}

Write-Host "Generating secure keys..." -ForegroundColor Green
$jwtSecret = Generate-SecureKey
$jwtRefreshSecret = Generate-SecureKey
$encryptionKey = Generate-SecureKey 32

# Create .env content
$envContent = @"
# Oryza Environment Configuration
# Generated on $(Get-Date)
# ==========================================

# ==========================================
# MARKET DATA APIs (Required)
# ==========================================

# Alpha Vantage - Stock Market Data
# Free tier: 5 calls/min, 500 calls/day
# Get your free API key at: https://www.alphavantage.co/support/#api-key
REACT_APP_ALPHA_VANTAGE_API_KEY=demo

# NewsAPI - Financial News
# Free tier: 100 requests/day  
# Get your free API key at: https://newsapi.org/register
REACT_APP_NEWS_API_KEY=YOUR_NEWSAPI_KEY_HERE

# RapidAPI - Yahoo Finance & Others
# Get your API key at: https://rapidapi.com/
REACT_APP_RAPID_API_KEY=YOUR_RAPIDAPI_KEY_HERE

# ==========================================
# BROKER INTEGRATION (Choose One)
# ==========================================

# Option 1: Alpaca (Recommended for US Markets)
# Free paper trading account
# Sign up at: https://alpaca.markets/
ALPACA_API_KEY=YOUR_ALPACA_KEY_HERE
ALPACA_SECRET_KEY=YOUR_ALPACA_SECRET_HERE
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Option 2: Interactive Brokers
# Professional trading platform
IB_GATEWAY_HOST=localhost
IB_GATEWAY_PORT=7497
IB_CLIENT_ID=1

# ==========================================
# INDIAN MARKET DATA (Optional)
# ==========================================

# For Indian stocks, use Alpha Vantage with .BSE suffix
# Example: RELIANCE.BSE, TCS.BSE

# ==========================================
# SECURITY (Auto-generated - DO NOT SHARE!)
# ==========================================

JWT_SECRET_KEY=$jwtSecret
JWT_REFRESH_SECRET_KEY=$jwtRefreshSecret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

ENCRYPTION_KEY=$encryptionKey

# ==========================================
# DATABASE CONFIGURATION
# ==========================================

DATABASE_URL=postgresql://oryza_user:oryza_password@localhost:5432/oryza_db
POSTGRES_USER=oryza_user
POSTGRES_PASSWORD=oryza_password
POSTGRES_DB=oryza_db

MONGODB_URL=mongodb://oryza_user:oryza_password@localhost:27017/oryza_db
MONGO_INITDB_ROOT_USERNAME=oryza_user
MONGO_INITDB_ROOT_PASSWORD=oryza_password
MONGO_INITDB_DATABASE=oryza_db

REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=

# ==========================================
# MICROSERVICES URLS (Local Development)
# ==========================================

API_GATEWAY_URL=http://localhost:8080
AUTH_SERVICE_URL=http://localhost:8001
WEBSOCKET_SERVICE_URL=http://localhost:8002
PORTFOLIO_SERVICE_URL=http://localhost:8003
TRADING_SERVICE_URL=http://localhost:8004
MARKET_SERVICE_URL=http://localhost:8005
NEWS_SERVICE_URL=http://localhost:8006
NOTIFICATION_SERVICE_URL=http://localhost:8007
ADVISORY_SERVICE_URL=http://localhost:8008
EXECUTION_SERVICE_URL=http://localhost:8009
COMPLIANCE_SERVICE_URL=http://localhost:8010

# ==========================================
# OPTIONAL SERVICES (Add Later)
# ==========================================

# Enhanced Market Data
POLYGON_API_KEY=
IEX_CLOUD_API_KEY=
CURRENCY_LAYER_API_KEY=

# Social Sentiment Analysis
TWITTER_BEARER_TOKEN=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=

# AI Services
OPENAI_API_KEY=
HUGGINGFACE_API_KEY=

# Email & SMS
SENDGRID_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# ==========================================
# ENVIRONMENT SETTINGS
# ==========================================

NODE_ENV=development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=info
"@

# Write .env file
$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host ".env file created successfully!" -ForegroundColor Green

# Create frontend .env if needed
if (-not (Test-Path "frontend\.env")) {
    Copy-Item ".env" "frontend\.env"
    Write-Host "frontend\.env created!" -ForegroundColor Green
}

# Display next steps
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SETUP COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Secure JWT keys generated automatically" -ForegroundColor Green
Write-Host "✅ Database configuration set to Docker defaults" -ForegroundColor Green
Write-Host "✅ Service URLs configured for local development" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Get your FREE API keys:" -ForegroundColor White
Write-Host "   📊 Alpha Vantage: https://www.alphavantage.co/support/#api-key" -ForegroundColor Cyan
Write-Host "   📰 NewsAPI: https://newsapi.org/register" -ForegroundColor Cyan
Write-Host "   📈 Alpaca (optional): https://alpaca.markets/" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Edit .env file and replace placeholder API keys" -ForegroundColor White
Write-Host ""
Write-Host "3. Start the application:" -ForegroundColor White
Write-Host "   ./start_oryza.bat" -ForegroundColor Green
Write-Host ""
Write-Host "4. Access Oryza at: http://localhost:3000" -ForegroundColor White
Write-Host ""

# Ask if user wants to open .env file
$openFile = Read-Host "Would you like to open .env file now? (y/n)"
if ($openFile -eq 'y') {
    notepad .env
}

Write-Host ""
Write-Host "Happy investing with Oryza!" -ForegroundColor Green 
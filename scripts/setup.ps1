# Setup Script for AI Content Analysis
# This script sets up the project and installs dependencies

Write-Host "🚀 Setting up AI Content Analysis..." -ForegroundColor Cyan

# Check if Python is installed
$pythonCheck = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python is not installed. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python found: $pythonCheck" -ForegroundColor Green

# Install requirements
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Cyan
pip install -r config/requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ Dependencies installed" -ForegroundColor Green

# Check for .env file
if (-not (Test-Path "server\.env")) {
    Write-Host "`n⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "📝 Creating .env from template..." -ForegroundColor Cyan
    Copy-Item "server\.env.example" "server\.env"
    Write-Host "✅ .env created (update with your API key)" -ForegroundColor Green
}

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`n📖 Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit server\.env with your GEMINI_API_KEY" -ForegroundColor White
Write-Host "2. Run: python server\start_server.py" -ForegroundColor White
Write-Host "3. Open: http://localhost:8000" -ForegroundColor White

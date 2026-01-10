# Script de deploy para People Analytics Platform

Write-Host "🚀 Iniciando deploy..." -ForegroundColor Cyan

# Verificar se Firebase CLI está instalado
if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Firebase CLI não encontrado. Instalando..." -ForegroundColor Yellow
    npm install -g firebase-tools
}

# Deploy Firestore Rules
Write-Host "`n📋 Deployando Firestore Rules..." -ForegroundColor Cyan
# Garantir que estamos no diretório raiz
Set-Location $PSScriptRoot
firebase deploy --only firestore:rules --project lrgtechanalytics

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Firestore Rules deployadas com sucesso!" -ForegroundColor Green
} else {
    Write-Host "❌ Erro ao deployar Firestore Rules" -ForegroundColor Red
    exit 1
}

# Instruções para deploy do backend
Write-Host "`n📦 Para deploy do backend no Cloud Run:" -ForegroundColor Yellow
Write-Host "   1. Configure gcloud: gcloud init" -ForegroundColor White
Write-Host "   2. Configure projeto: gcloud config set project lrgtechanalytics" -ForegroundColor White
Write-Host "   3. Execute: cd backend" -ForegroundColor White
Write-Host "   4. Execute: gcloud run deploy people-analytics-api --source . --platform managed --region us-central1 --allow-unauthenticated" -ForegroundColor White

Write-Host "`n✅ Deploy concluído!" -ForegroundColor Green

# Script de deploy do backend para Cloud Run

Write-Host "🚀 Deploy do Backend - People Analytics API" -ForegroundColor Cyan
Write-Host ""

# Verificar se gcloud está instalado
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Google Cloud SDK não encontrado!" -ForegroundColor Red
    exit 1
}

# Configurar projeto
Write-Host "📋 Configurando projeto..." -ForegroundColor Cyan
gcloud config set project lrgtechanalytics
Write-Host "✅ Projeto: lrgtechanalytics" -ForegroundColor Green
Write-Host ""

# Habilitar APIs
Write-Host "📋 Habilitando APIs necessárias..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable artifactregistry.googleapis.com --quiet
Write-Host "✅ APIs habilitadas" -ForegroundColor Green
Write-Host ""

# Service Account
Write-Host "🔐 Configurando Service Account..." -ForegroundColor Cyan
$saEmail = "people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com"

$saCheck = & gcloud iam service-accounts describe $saEmail 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Criando Service Account..." -ForegroundColor Yellow
    gcloud iam service-accounts create people-analytics-sa --display-name="People Analytics Service Account" --project=lrgtechanalytics
    
    Write-Host "   Configurando permissões..." -ForegroundColor Yellow
    gcloud projects add-iam-policy-binding lrgtechanalytics --member="serviceAccount:$saEmail" --role="roles/datastore.user" --quiet
    gcloud projects add-iam-policy-binding lrgtechanalytics --member="serviceAccount:$saEmail" --role="roles/firebase.admin" --quiet
    
    Write-Host "✅ Service Account criada" -ForegroundColor Green
} else {
    Write-Host "✅ Service Account já existe" -ForegroundColor Green
}
Write-Host ""

# Navegar para backend
if (-not (Test-Path "backend")) {
    Write-Host "❌ Diretório 'backend' não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Iniciando deploy no Cloud Run..." -ForegroundColor Cyan
Write-Host "   Isso pode levar alguns minutos..." -ForegroundColor Yellow
Write-Host ""

Push-Location backend

try {
    gcloud run deploy people-analytics-api `
        --source . `
        --platform managed `
        --region us-central1 `
        --allow-unauthenticated `
        --service-account $saEmail `
        --set-env-vars="FIREBASE_PROJECT_ID=lrgtechanalytics" `
        --memory 512Mi `
        --cpu 1 `
        --timeout 300 `
        --max-instances 10
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
        Write-Host "   1. Obter URL:" -ForegroundColor White
        Write-Host "      gcloud run services describe people-analytics-api --region us-central1 --format='value(status.url)'" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   2. Testar: curl [URL]/health" -ForegroundColor White
        Write-Host ""
        Write-Host "   3. Ver logs:" -ForegroundColor White
        Write-Host "      gcloud run services logs tail people-analytics-api --region us-central1" -ForegroundColor Gray
    } else {
        Write-Host ""
        Write-Host "❌ Erro no deploy!" -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

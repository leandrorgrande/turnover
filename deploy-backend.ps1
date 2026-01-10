# Script de deploy do backend para Cloud Run

Write-Host "🚀 Deploy do Backend - People Analytics API" -ForegroundColor Cyan
Write-Host ""

# Verificar se gcloud está instalado
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Google Cloud SDK não encontrado!" -ForegroundColor Red
    Write-Host "   Instale em: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# Verificar se está no projeto correto
$project = gcloud config get-value project 2>$null
if ($project -ne "lrgtechanalytics") {
    Write-Host "⚠️  Projeto atual: $project" -ForegroundColor Yellow
    Write-Host "   Configurando projeto para lrgtechanalytics..." -ForegroundColor Yellow
    gcloud config set project lrgtechanalytics
}

Write-Host "✅ Projeto: lrgtechanalytics" -ForegroundColor Green
Write-Host ""

# Habilitar APIs necessárias
Write-Host "📋 Habilitando APIs necessárias..." -ForegroundColor Cyan
gcloud services enable run.googleapis.com --quiet
gcloud services enable cloudbuild.googleapis.com --quiet
gcloud services enable artifactregistry.googleapis.com --quiet

Write-Host "✅ APIs habilitadas" -ForegroundColor Green
Write-Host ""

# Verificar/criar Service Account
Write-Host "🔐 Verificando Service Account..." -ForegroundColor Cyan
$saEmail = "people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com"

$saExists = gcloud iam service-accounts describe $saEmail 2>$null
if (-not $saExists) {
    Write-Host "   Criando Service Account..." -ForegroundColor Yellow
    gcloud iam service-accounts create people-analytics-sa `
        --display-name="People Analytics Service Account" `
        --project=lrgtechanalytics
    
    Write-Host "   Configurando permissões..." -ForegroundColor Yellow
    gcloud projects add-iam-policy-binding lrgtechanalytics `
        --member="serviceAccount:$saEmail" `
        --role="roles/datastore.user" `
        --quiet
    
    gcloud projects add-iam-policy-binding lrgtechanalytics `
        --member="serviceAccount:$saEmail" `
        --role="roles/firebase.admin" `
        --quiet
    
    Write-Host "✅ Service Account criada e configurada" -ForegroundColor Green
} else {
    Write-Host "✅ Service Account já existe" -ForegroundColor Green
}
Write-Host ""

# Navegar para backend
if (-not (Test-Path "backend")) {
    Write-Host "❌ Diretório 'backend' não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "📦 Preparando deploy do backend..." -ForegroundColor Cyan
Write-Host "   Diretório: backend/" -ForegroundColor White
Write-Host ""

# Deploy no Cloud Run
Write-Host "🚀 Iniciando deploy no Cloud Run..." -ForegroundColor Cyan
Write-Host "   Isso pode levar alguns minutos..." -ForegroundColor Yellow
Write-Host ""

cd backend

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
    cd ..
    Write-Host ""
    Write-Host "✅ Deploy concluído com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Próximos passos:" -ForegroundColor Cyan
    Write-Host "   1. Obter URL do serviço:" -ForegroundColor White
    Write-Host "      gcloud run services describe people-analytics-api --region us-central1 --format='value(status.url)'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   2. Testar endpoint:" -ForegroundColor White
    Write-Host "      curl [URL]/health" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   3. Ver logs:" -ForegroundColor White
    Write-Host "      gcloud run services logs tail people-analytics-api --region us-central1" -ForegroundColor Gray
} else {
    cd ..
    Write-Host ""
    Write-Host "❌ Erro no deploy!" -ForegroundColor Red
    Write-Host "   Verifique os logs acima para mais detalhes" -ForegroundColor Yellow
    exit 1
}

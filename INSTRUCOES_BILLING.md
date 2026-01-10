# 💳 Habilitar Billing no Google Cloud

Para fazer deploy no Cloud Run, é necessário habilitar o billing no projeto.

## 🔗 Como Habilitar Billing

1. **Acesse o Google Cloud Console:**
   https://console.cloud.google.com/billing?project=lrgtechanalytics

2. **Ou pelo menu:**
   - Google Cloud Console → Billing
   - Selecione ou crie uma conta de billing
   - Vincule ao projeto `lrgtechanalytics`

3. **Pelo comando (se tiver acesso):**
   ```bash
   gcloud billing projects link lrgtechanalytics --billing-account=BILLING_ACCOUNT_ID
   ```

## 💰 Custos Estimados

**Cloud Run (Pay-as-you-go):**
- **Gratuito até:** 2 milhões de requisições/mês
- **Depois:** ~$0.0000025 por requisição (com 512MiB)
- **Estimativa mensal (uso moderado):** $10-30

**Firestore:**
- **Gratuito até:** 50K reads, 20K writes, 20K deletes/dia
- **Depois:** Muito barato, geralmente < $5/mês para uso moderado

**Firebase Hosting:**
- **Gratuito até:** 10GB storage, 360MB/day transfer
- **Depois:** $0.026/GB storage, $0.15/GB transfer

**Estimativa Total:** $15-35/mês para uso moderado

## ⚠️ Importante

- Cloud Run só cobra quando está em uso
- Você pode definir alertas de billing no Console
- É possível pausar serviços para evitar custos

## ✅ Após Habilitar Billing

Execute novamente:
```powershell
.\deploy-backend.ps1
```

Ou manualmente:
```powershell
cd backend
gcloud run deploy people-analytics-api `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --service-account people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com `
  --set-env-vars="FIREBASE_PROJECT_ID=lrgtechanalytics" `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300
```

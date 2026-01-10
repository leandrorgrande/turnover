# 🚀 Guia Completo de Deploy - People Analytics Platform

## ✅ O que já está pronto

- ✅ Firestore Rules deployadas
- ✅ Firebase configurado
- ✅ Backend FastAPI pronto
- ✅ Dockerfile criado
- ✅ Código otimizado para Cloud Run

## 📋 Pré-requisitos

1. **Google Cloud SDK instalado** (já está ✅)
2. **Firebase CLI instalado** (já está ✅)
3. **Projeto Google Cloud criado** (`lrgtechanalytics`)
4. **Billing habilitado** no Google Cloud

## 🔧 Passo 1: Configurar Google Cloud

```powershell
# 1. Login no Google Cloud
gcloud auth login

# 2. Configurar projeto
gcloud config set project lrgtechanalytics

# 3. Habilitar APIs necessárias
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# 4. Verificar configuração
gcloud config list
```

## 🔐 Passo 2: Configurar Service Account

Para o Cloud Run funcionar com o Firestore, precisamos configurar uma Service Account:

```powershell
# 1. Criar Service Account (se ainda não existir)
gcloud iam service-accounts create people-analytics-sa `
  --display-name="People Analytics Service Account" `
  --project=lrgtechanalytics

# 2. Dar permissões necessárias
gcloud projects add-iam-policy-binding lrgtechanalytics `
  --member="serviceAccount:people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com" `
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding lrgtechanalytics `
  --member="serviceAccount:people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com" `
  --role="roles/firebase.admin"
```

## 🐳 Passo 3: Deploy no Cloud Run

```powershell
# 1. Navegar para o diretório do backend
cd backend

# 2. Deploy no Cloud Run
gcloud run deploy people-analytics-api `
  --source . `
  --platform managed `
  --region us-central1 `
  --allow-unauthenticated `
  --service-account people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com `
  --set-env-vars="FIREBASE_PROJECT_ID=lrgtechanalytics" `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10

# 3. Após o deploy, você receberá uma URL como:
# https://people-analytics-api-xxxxx-uc.a.run.app
```

## 🔍 Passo 4: Verificar Deploy

```powershell
# 1. Listar serviços deployados
gcloud run services list

# 2. Ver logs do serviço
gcloud run services logs read people-analytics-api --region us-central1

# 3. Testar endpoint
# Substituir URL com a URL recebida no deploy
curl https://people-analytics-api-xxxxx-uc.a.run.app/health
```

## 🌐 Passo 5: Configurar CORS (se necessário)

O CORS já está configurado no código, mas se precisar ajustar:

1. Editar `backend/app/config.py`
2. Adicionar a URL do Cloud Run em `CORS_ORIGINS`
3. Fazer novo deploy

## 🔄 Passo 6: Atualizar Frontend (quando criar)

Quando criar o frontend, atualizar a URL da API:

```javascript
// frontend/src/services/api.js
const API_URL = 'https://people-analytics-api-xxxxx-uc.a.run.app/api/v1';
```

## 📊 Monitoramento

```powershell
# Ver métricas do serviço
gcloud run services describe people-analytics-api --region us-central1

# Ver logs em tempo real
gcloud run services logs tail people-analytics-api --region us-central1
```

## 🔐 Segurança

### Opção 1: Permitir acesso não autenticado (atual)
- Qualquer um pode acessar a API
- Útil para MVP/testes

### Opção 2: Requerer autenticação (recomendado)
```powershell
# Remover --allow-unauthenticated e adicionar:
gcloud run deploy people-analytics-api `
  --no-allow-unauthenticated `
  --service-account people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com
```

Então, no frontend, enviar token do Firebase Auth no header:
```javascript
headers: {
  'Authorization': `Bearer ${firebaseAuthToken}`
}
```

## 💰 Custos

Cloud Run cobra apenas pelo uso:
- 0 USD até 2 milhões de requisições/mês
- 512 MiB de memória = ~$0.0000025 por requisição
- Estimativa: ~$10-20/mês para uso moderado

## 🐛 Troubleshooting

### Erro: "Permission denied"
```powershell
# Verificar permissões da Service Account
gcloud projects get-iam-policy lrgtechanalytics \
  --flatten="bindings[].members" \
  --filter="bindings.members:people-analytics-sa@lrgtechanalytics.iam.gserviceaccount.com"
```

### Erro: "Firebase não inicializado"
- Verificar logs: `gcloud run services logs read people-analytics-api`
- Verificar se Service Account tem permissões corretas
- Verificar se `FIREBASE_PROJECT_ID` está configurado

### Rebuild rápido (após mudanças no código)
```powershell
# Deploy apenas se houver mudanças (mais rápido)
gcloud run deploy people-analytics-api --source . --region us-central1
```

## ✅ Checklist Final

- [ ] Google Cloud configurado
- [ ] APIs habilitadas
- [ ] Service Account criada e com permissões
- [ ] Backend deployado no Cloud Run
- [ ] URL da API anotada
- [ ] Health check funcionando
- [ ] Logs sendo gerados corretamente
- [ ] CORS configurado (se necessário)

## 📞 Próximos Passos

1. ✅ Backend deployado
2. ⏳ Criar frontend React/Vue
3. ⏳ Deploy frontend no Firebase Hosting
4. ⏳ Conectar frontend com backend
5. ⏳ Testar fluxo completo

# Migração: Streamlit → FastAPI + Firestore

## ✅ Estrutura Criada

### Backend (FastAPI)
- ✅ Configuração do Firebase Admin SDK
- ✅ Autenticação com Firebase Auth
- ✅ Serviços de dados e KPIs migrados
- ✅ Endpoints de API (datasets, analyses)
- ✅ Modelos Pydantic para validação
- ✅ Integração com Firestore

### Firebase
- ✅ Regras de segurança do Firestore
- ✅ Configuração de Hosting
- ✅ Estrutura de coleções

## 📋 Próximos Passos

### 1. Configurar Credenciais Firebase
```bash
# Baixar serviceAccountKey.json do Firebase Console
# Projeto: lrgtechanalytics
# Colocar em: backend/firebase-service-account.json
```

### 2. Instalar Dependências
```bash
cd backend
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
```bash
cp backend/.env.example backend/.env
# Editar .env com suas configurações
```

### 4. Testar Backend Localmente
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 5. Criar Frontend
- React/Vue com Firebase SDK
- Autenticação Firebase Auth
- Chamadas para API FastAPI
- Upload de arquivos
- Visualizações de dados

### 6. Deploy
- **Backend**: Cloud Run ou Cloud Functions
- **Frontend**: Firebase Hosting
- **Database**: Firestore (já configurado)

## 🔧 Estrutura de Dados Firestore

```
users/
  {userId}/
    subscriptionLevel: "basic" | "premium"
    email: string
    createdAt: timestamp
    datasets/
      {datasetId}/
        name: string
        filename: string
        rows: number
        uploaded_at: timestamp
        analyses/
          {analysisId}/
            type: string
            results: object
            createdAt: timestamp
```

## 🚀 Comandos Úteis

### Inicializar Firebase
```bash
firebase init
```

### Deploy Firestore Rules
```bash
firebase deploy --only firestore:rules
```

### Deploy Hosting
```bash
firebase deploy --only hosting
```

## 📝 Notas

- O código de cálculos de KPIs foi migrado completamente
- A lógica de filtros por período está preservada
- Autenticação integrada com Firebase Auth
- Estrutura preparada para escalar

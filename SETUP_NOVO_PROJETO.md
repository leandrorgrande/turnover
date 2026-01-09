# 🚀 Setup do Novo Projeto - People Analytics Platform

## 📦 Estrutura Criada

```
lrgtechanalytics/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── api/         # Endpoints REST
│   │   ├── models/      # Schemas Pydantic
│   │   ├── services/    # Lógica de negócio
│   │   ├── utils/       # Utilitários (KPIs, data loader)
│   │   ├── main.py      # App FastAPI
│   │   ├── config.py    # Configurações
│   │   ├── firebase.py  # Firebase Admin SDK
│   │   └── auth.py      # Autenticação
│   └── requirements.txt
│
├── frontend/            # Frontend (a criar)
│   └── src/
│
├── firebase/            # Configuração Firebase
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   └── firebase.json
│
└── README_MIGRATION.md
```

## ✅ O que foi migrado

- ✅ Toda lógica de cálculos de KPIs
- ✅ Processamento de dados Excel
- ✅ Estrutura de autenticação Firebase
- ✅ Endpoints de API (datasets, analyses)
- ✅ Integração com Firestore
- ✅ Regras de segurança

## 🔧 Próximos Passos

### 1. Criar Novo Repositório GitHub

```bash
# Criar repositório no GitHub
# Nome sugerido: lrgtechanalytics ou people-analytics-platform

# Inicializar git
git init
git add .
git commit -m "Initial commit: Migração Streamlit → FastAPI + Firestore"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/lrgtechanalytics.git
git push -u origin main
```

### 2. Configurar Firebase

1. **Baixar Service Account Key:**
   - Firebase Console → Project Settings → Service Accounts
   - Gerar nova chave privada
   - Salvar como `backend/firebase-service-account.json`
   - ⚠️ **NÃO COMMITAR** este arquivo (já está no .gitignore)

2. **Configurar Domínios Autorizados:**
   - Firebase Console → Authentication → Settings → Authorized domains
   - Já configurado: `localhost`, `lrgtechanalytics.firebaseapp.com`, `lrgtechanalytics.web.app`

### 3. Instalar Dependências Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

```bash
cd backend
cp .env.example .env
# Editar .env com suas configurações
```

### 5. Testar Backend Localmente

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Acesse: http://localhost:8000/docs (Swagger UI)

### 6. Deploy Firestore Rules

```bash
# Instalar Firebase CLI (se ainda não tiver)
npm install -g firebase-tools

# Login
firebase login

# Inicializar (se necessário)
firebase init firestore

# Deploy rules
firebase deploy --only firestore:rules
```

### 7. Criar Frontend

Escolher uma das opções:
- **React + Vite** (recomendado)
- **Vue.js**
- **Next.js**

Estrutura básica:
- Autenticação Firebase Auth
- Upload de arquivos Excel
- Chamadas para API FastAPI
- Visualizações com Chart.js/Recharts
- Dashboard responsivo

### 8. Deploy

**Backend:**
- Opção 1: Google Cloud Run (recomendado)
- Opção 2: Cloud Functions
- Opção 3: VPS/Server

**Frontend:**
- Firebase Hosting (já configurado)

```bash
# Deploy frontend
firebase deploy --only hosting
```

## 📝 Notas Importantes

1. **Segurança:**
   - Service Account Key NUNCA deve ser commitado
   - Usar variáveis de ambiente em produção
   - Firestore rules já configuradas para segurança

2. **Dados:**
   - Por enquanto, dados são processados em memória
   - Para produção, considerar:
     - Firebase Storage para arquivos
     - Cache Redis para dados processados
     - BigQuery para análises históricas

3. **Escalabilidade:**
   - Backend FastAPI é stateless (pode escalar horizontalmente)
   - Firestore escala automaticamente
   - Considerar Cloud Run para auto-scaling

## 🔗 Links Úteis

- Firebase Console: https://console.firebase.google.com/project/lrgtechanalytics
- API Docs (local): http://localhost:8000/docs
- Hosting: https://lrgtechanalytics.web.app

## 📞 Suporte

Em caso de dúvidas sobre a migração, consultar:
- `README_MIGRATION.md` - Detalhes técnicos
- `migration_plan.md` - Plano original

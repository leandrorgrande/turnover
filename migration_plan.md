# Plano de Migração: Streamlit → FastAPI + Firestore

## Projeto Firebase
- **Projeto ID**: lrgtechanalytics
- **Hosting**: https://lrgtechanalytics.web.app
- **Firestore**: Configurado
- **Authentication**: Configurado

## Estrutura do Novo Projeto

```
lrgtechanalytics/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configurações
│   │   ├── firebase.py          # Inicialização Firebase
│   │   ├── auth.py              # Autenticação
│   │   ├── models/              # Modelos de dados
│   │   ├── api/                 # Endpoints
│   │   │   ├── datasets.py
│   │   │   ├── analyses.py
│   │   │   └── kpis.py
│   │   ├── services/            # Lógica de negócio
│   │   │   ├── kpi_calculator.py
│   │   │   ├── data_processor.py
│   │   │   └── firestore_service.py
│   │   └── utils/               # Utilitários migrados
│   │       ├── data_loader.py
│   │       └── kpi_helpers.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   ├── package.json
│   └── firebase-config.js
│
├── firebase/
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   └── firebase.json
│
└── README.md
```

## Próximos Passos
1. ✅ Criar estrutura de pastas
2. ⏳ Configurar Firebase Admin SDK
3. ⏳ Migrar lógica de cálculos
4. ⏳ Criar endpoints API
5. ⏳ Implementar frontend básico
6. ⏳ Deploy no Firebase Hosting

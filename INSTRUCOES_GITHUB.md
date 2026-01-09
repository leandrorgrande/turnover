# 📋 Instruções para Criar Novo Repositório GitHub

## 1. Criar Repositório no GitHub

1. Acesse: https://github.com/new
2. **Nome do repositório:** `lrgtechanalytics` ou `people-analytics-platform`
3. **Descrição:** "Plataforma de People Analytics com FastAPI e Firestore"
4. **Visibilidade:** Private (recomendado) ou Public
5. **NÃO** inicializar com README, .gitignore ou license (já temos)
6. Clique em "Create repository"

## 2. Conectar Repositório Local

```bash
# No diretório do projeto (turnover)
git init
git add .
git commit -m "Initial commit: Migração Streamlit → FastAPI + Firestore

- Backend FastAPI com autenticação Firebase
- Migração completa de lógica de KPIs
- Integração com Firestore
- Estrutura preparada para frontend
- Configuração de deploy no Firebase Hosting"

# Adicionar remote (substituir SEU_USUARIO)
git remote add origin https://github.com/SEU_USUARIO/lrgtechanalytics.git

# Push inicial
git branch -M main
git push -u origin main
```

## 3. Configurar Proteções de Branch (Opcional)

No GitHub:
- Settings → Branches → Add rule
- Branch name pattern: `main`
- ✅ Require pull request reviews
- ✅ Require status checks to pass

## 4. Adicionar Secrets (Para CI/CD Futuro)

Settings → Secrets and variables → Actions:
- `FIREBASE_SERVICE_ACCOUNT` (JSON completo)
- `GOOGLE_APPLICATION_CREDENTIALS`

## 5. Estrutura de Branches Recomendada

```
main          → Produção
develop       → Desenvolvimento
feature/*     → Novas features
fix/*         → Correções
```

## ✅ Checklist

- [ ] Repositório criado no GitHub
- [ ] Código commitado e pushado
- [ ] .gitignore configurado (já está)
- [ ] README criado (SETUP_NOVO_PROJETO.md)
- [ ] Service Account Key NÃO commitado
- [ ] Branch protection configurada (opcional)

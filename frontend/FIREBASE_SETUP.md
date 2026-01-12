# 🔧 Configuração do Firebase no Frontend

## 1. Obter Credenciais do Firebase

1. Acesse: https://console.firebase.google.com/project/lrgtechanalytics/settings/general
2. Role até "Seus apps"
3. Clique em "Configuração" do app web (ou crie um novo)
4. Copie o objeto de configuração

## 2. Atualizar `src/config/firebase.js`

Substitua o objeto `firebaseConfig` com as credenciais reais:

```javascript
const firebaseConfig = {
  apiKey: "SUA_API_KEY",
  authDomain: "lrgtechanalytics.firebaseapp.com",
  projectId: "lrgtechanalytics",
  storageBucket: "lrgtechanalytics.appspot.com",
  messagingSenderId: "286602273391",
  appId: "SEU_APP_ID"
}
```

## 3. Habilitar Métodos de Autenticação

1. Firebase Console → Authentication → Sign-in method
2. Habilitar "Email/Password"
3. Configurar domínios autorizados (já configurado)

## 4. Rebuild e Deploy

```bash
npm run build
firebase deploy --only hosting
```

## ⚠️ Importante

Por enquanto, a autenticação está opcional. O sistema funciona sem login, mas para usar recursos premium, será necessário autenticação.

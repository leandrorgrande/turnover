"""
Inicialização e configuração do Firebase Admin SDK
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from pathlib import Path
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Variável global para armazenar a instância
_firebase_app = None
_db = None

def initialize_firebase():
    """
    Inicializa o Firebase Admin SDK.
    Deve ser chamado uma vez no startup da aplicação.
    """
    global _firebase_app, _db
    
    if _firebase_app is not None:
        logger.info("Firebase já inicializado")
        return _firebase_app
    
    try:
        # Em produção (Cloud Run), usar Application Default Credentials
        # Isso funciona automaticamente quando o serviço tem a Service Account configurada
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GAE_ENV") or os.getenv("K_SERVICE"):
            # Cloud Run ou ambiente de produção
            logger.info("Usando Application Default Credentials (Cloud Run/Produção)")
            cred = credentials.ApplicationDefault()
        else:
            # Desenvolvimento local - tentar arquivo de credenciais
            cred_path = settings.get_firebase_credentials_path()
            if cred_path.exists():
                logger.info(f"Usando credenciais do arquivo: {cred_path}")
                cred = credentials.Certificate(str(cred_path))
            else:
                raise FileNotFoundError(
                    f"Arquivo de credenciais não encontrado: {cred_path}\n"
                    "Para desenvolvimento local: Baixe o serviceAccountKey.json do Firebase Console\n"
                    "Para produção: Configure Service Account no Cloud Run"
                )
        
        _firebase_app = firebase_admin.initialize_app(
            cred,
            {
                'projectId': settings.FIREBASE_PROJECT_ID,
            }
        )
        
        _db = firestore.client()
        
        logger.info(f"Firebase inicializado com sucesso. Projeto: {settings.FIREBASE_PROJECT_ID}")
        return _firebase_app
    
    except Exception as e:
        logger.error(f"Erro ao inicializar Firebase: {e}")
        raise


def get_firestore() -> firestore.Client:
    """Retorna instância do Firestore"""
    if _db is None:
        initialize_firebase()
    return _db


def get_auth() -> auth.Client:
    """Retorna instância do Firebase Auth"""
    if _firebase_app is None:
        initialize_firebase()
    return auth


def verify_firebase_token(token: str) -> dict:
    """
    Verifica token do Firebase Auth e retorna dados do usuário.
    
    Args:
        token: Token JWT do Firebase
    
    Returns:
        Dict com dados do usuário (uid, email, etc.)
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return {
            'uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'email_verified': decoded_token.get('email_verified', False)
        }
    except Exception as e:
        logger.error(f"Erro ao verificar token: {e}")
        raise

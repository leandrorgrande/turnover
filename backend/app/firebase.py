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
        cred_path = settings.get_firebase_credentials_path()
        
        if not cred_path.exists():
            # Tentar usar credenciais do ambiente (para produção)
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                cred = credentials.ApplicationDefault()
            else:
                raise FileNotFoundError(
                    f"Arquivo de credenciais não encontrado: {cred_path}\n"
                    "Baixe o serviceAccountKey.json do Firebase Console e coloque na raiz do projeto."
                )
        else:
            cred = credentials.Certificate(str(cred_path))
        
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

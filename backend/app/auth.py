"""
Autenticação e autorização
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.firebase import verify_firebase_token, get_firestore
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency para obter usuário atual autenticado.
    
    Args:
        credentials: Credenciais HTTP Bearer
    
    Returns:
        Dict com dados do usuário
    """
    try:
        token = credentials.credentials
        user = verify_firebase_token(token)
        return user
    except Exception as e:
        logger.error(f"Erro de autenticação: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_user_subscription(user: dict = Depends(get_current_user)) -> str:
    """
    Obtém nível de assinatura do usuário.
    
    Returns:
        "basic" ou "premium"
    """
    db = get_firestore()
    
    try:
        user_doc = db.collection('users').document(user['uid']).get()
        
        if not user_doc.exists:
            # Criar usuário se não existir
            db.collection('users').document(user['uid']).set({
                'email': user.get('email'),
                'subscriptionLevel': 'basic',
                'createdAt': firestore.SERVER_TIMESTAMP
            })
            return 'basic'
        
        user_data = user_doc.to_dict()
        return user_data.get('subscriptionLevel', 'basic')
    
    except Exception as e:
        logger.error(f"Erro ao obter assinatura: {e}")
        return 'basic'  # Default para basic em caso de erro


def require_premium(subscription: str = Depends(get_user_subscription)):
    """
    Dependency que verifica se usuário tem assinatura premium.
    """
    if subscription != 'premium':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta funcionalidade requer assinatura Premium"
        )
    return subscription

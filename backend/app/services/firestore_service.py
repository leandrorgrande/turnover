"""
Serviço para interação com Firestore
"""
from app.firebase import get_firestore
from firebase_admin import firestore
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FirestoreService:
    """Serviço para operações no Firestore"""
    
    def __init__(self):
        self.db = get_firestore()
    
    def save_dataset(self, user_id: str, dataset_id: str, metadata: Dict[str, Any]) -> str:
        """
        Salva metadados de um dataset.
        
        Args:
            user_id: ID do usuário
            dataset_id: ID único do dataset
            metadata: Metadados do dataset
        
        Returns:
            ID do documento criado
        """
        doc_ref = self.db.collection('users').document(user_id).collection('datasets').document(dataset_id)
        doc_ref.set({
            **metadata,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP
        })
        return dataset_id
    
    def get_dataset(self, user_id: str, dataset_id: str) -> Optional[Dict[str, Any]]:
        """Obtém metadados de um dataset"""
        doc_ref = self.db.collection('users').document(user_id).collection('datasets').document(dataset_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    
    def list_datasets(self, user_id: str) -> list:
        """Lista todos os datasets do usuário"""
        docs = self.db.collection('users').document(user_id).collection('datasets').stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in docs]
    
    def delete_dataset(self, user_id: str, dataset_id: str) -> bool:
        """Deleta um dataset"""
        try:
            self.db.collection('users').document(user_id).collection('datasets').document(dataset_id).delete()
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar dataset: {e}")
            return False
    
    def save_analysis(self, user_id: str, dataset_id: str, analysis_type: str, results: Dict[str, Any]) -> str:
        """
        Salva resultados de uma análise.
        
        Args:
            user_id: ID do usuário
            dataset_id: ID do dataset
            analysis_type: Tipo de análise (overview, headcount, turnover, etc.)
            results: Resultados da análise
        
        Returns:
            ID do documento criado
        """
        doc_ref = self.db.collection('users').document(user_id).collection('datasets').document(dataset_id).collection('analyses').document()
        doc_ref.set({
            'type': analysis_type,
            'results': results,
            'createdAt': firestore.SERVER_TIMESTAMP
        })
        return doc_ref.id
    
    def get_user_subscription(self, user_id: str) -> str:
        """Obtém nível de assinatura do usuário"""
        doc = self.db.collection('users').document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            return data.get('subscriptionLevel', 'basic')
        return 'basic'
    
    def update_user_subscription(self, user_id: str, level: str):
        """Atualiza nível de assinatura do usuário"""
        self.db.collection('users').document(user_id).set({
            'subscriptionLevel': level,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }, merge=True)

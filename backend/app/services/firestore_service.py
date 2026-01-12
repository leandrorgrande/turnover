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
    
    def save_dataset_data(self, user_id: str, dataset_id: str, data: Dict[str, Any]) -> bool:
        """
        Salva dados processados do dataset no Firestore de forma flexível.
        Aceita qualquer estrutura de dados (não padronizada).
        Converte DataFrames para listas de dicts para compatibilidade com Firestore.
        
        Args:
            user_id: ID do usuário
            dataset_id: ID do dataset
            data: Dados a serem salvos (pode ser qualquer estrutura)
        
        Returns:
            True se salvou com sucesso
        """
        try:
            import pandas as pd
            
            # Converter DataFrames para listas de dicts (formato compatível com Firestore)
            processed_data = {}
            for key, value in data.items():
                if isinstance(value, pd.DataFrame):
                    # DataFrame: converter para lista de dicts
                    # Manter todas as colunas, mesmo que tenham nomes diferentes
                    if not value.empty:
                        # Converter NaN para None (Firestore não aceita NaN)
                        processed_data[key] = value.replace({pd.NA: None, pd.NaT: None}).to_dict('records')
                    else:
                        processed_data[key] = []
                elif isinstance(value, dict):
                    # Dict: manter como está (mas converter valores NaN se houver)
                    processed_data[key] = self._clean_dict_for_firestore(value)
                elif isinstance(value, list):
                    # Lista: manter como está
                    processed_data[key] = value
                else:
                    # Outros tipos (int, str, float, bool, None) - manter como está
                    processed_data[key] = value
            
            # Salvar no Firestore (estrutura flexível)
            doc_ref = self.db.collection('users').document(user_id).collection('datasets').document(dataset_id)
            doc_ref.set({
                'data': processed_data,  # Dados flexíveis
                'dataUpdatedAt': firestore.SERVER_TIMESTAMP
            }, merge=True)
            
            logger.info(f"Dados salvos no Firestore para dataset {dataset_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar dados do dataset: {e}", exc_info=True)
            return False
    
    def _clean_dict_for_firestore(self, d: Dict) -> Dict:
        """Limpa dict removendo valores incompatíveis com Firestore"""
        import pandas as pd
        cleaned = {}
        for k, v in d.items():
            if pd.isna(v) if hasattr(pd, 'isna') and (isinstance(v, float) or isinstance(v, pd.Timestamp)) else False:
                cleaned[k] = None
            elif isinstance(v, dict):
                cleaned[k] = self._clean_dict_for_firestore(v)
            elif isinstance(v, list):
                cleaned[k] = [self._clean_dict_for_firestore(item) if isinstance(item, dict) else item for item in v]
            else:
                cleaned[k] = v
        return cleaned
    
    def get_dataset_data(self, user_id: str, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados processados do dataset do Firestore.
        Retorna dados em formato flexível (qualquer estrutura).
        Os dados vêm como listas de dicts e podem ser convertidos para DataFrames se necessário.
        
        Args:
            user_id: ID do usuário
            dataset_id: ID do dataset
        
        Returns:
            Dict com os dados (listas de dicts) ou None se não existir
        """
        try:
            doc_ref = self.db.collection('users').document(user_id).collection('datasets').document(dataset_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                dataset_data = data.get('data')
                
                if dataset_data:
                    logger.info(f"Dados carregados do Firestore para dataset {dataset_id}")
                    return dataset_data
                else:
                    logger.warning(f"Dataset {dataset_id} existe mas não tem dados")
                    return None
            else:
                logger.warning(f"Dataset {dataset_id} não encontrado")
                return None
        except Exception as e:
            logger.error(f"Erro ao obter dados do dataset: {e}", exc_info=True)
            return None

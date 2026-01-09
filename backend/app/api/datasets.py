"""
Endpoints para gerenciamento de datasets
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.auth import get_current_user, require_premium
from app.services.firestore_service import FirestoreService
from app.services.data_processor import DataProcessor
from app.models.schemas import UploadResponse, ErrorResponse
from typing import Dict
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    user: Dict = Depends(get_current_user)
):
    """
    Faz upload de um arquivo Excel com dados de colaboradores.
    """
    try:
        # Validar tipo de arquivo
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apenas arquivos Excel (.xlsx, .xls) são permitidos"
            )
        
        # Ler conteúdo do arquivo
        content = await file.read()
        
        # Processar dados
        processor = DataProcessor()
        data = processor.process_upload(content)
        
        # Gerar ID único
        dataset_id = str(uuid.uuid4())
        
        # Salvar metadados no Firestore
        firestore_service = FirestoreService()
        metadata = {
            'name': file.filename,
            'filename': file.filename,
            'rows': len(data['colaboradores']),
            'uploaded_at': None,  # Será preenchido pelo Firestore
        }
        
        firestore_service.save_dataset(user['uid'], dataset_id, metadata)
        
        # TODO: Salvar dados processados (pode ser em storage ou cache)
        
        return UploadResponse(
            dataset_id=dataset_id,
            message="Dataset carregado com sucesso",
            metadata={
                'name': file.filename,
                'filename': file.filename,
                'rows': len(data['colaboradores']),
                'uploaded_at': None
            }
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Erro ao fazer upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar arquivo"
        )


@router.get("/")
async def list_datasets(user: Dict = Depends(get_current_user)):
    """Lista todos os datasets do usuário"""
    firestore_service = FirestoreService()
    datasets = firestore_service.list_datasets(user['uid'])
    return {"datasets": datasets}


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    user: Dict = Depends(get_current_user)
):
    """Deleta um dataset"""
    firestore_service = FirestoreService()
    success = firestore_service.delete_dataset(user['uid'], dataset_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset não encontrado"
        )
    
    return {"message": "Dataset deletado com sucesso"}

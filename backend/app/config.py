"""
Configurações da aplicação
"""
import os
from pathlib import Path
from typing import Optional

class Settings:
    """Configurações da aplicação"""
    
    # Firebase
    FIREBASE_PROJECT_ID: str = "lrgtechanalytics"
    FIREBASE_CREDENTIALS_PATH: Optional[str] = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-service-account.json")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://lrgtechanalytics.web.app",
        "https://lrgtechanalytics.firebaseapp.com"
    ]
    
    # Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: list = [".xlsx", ".xls"]
    
    # Cache
    CACHE_TTL: int = 3600  # 1 hora
    
    # Análises
    MAX_ROWS_PROCESSING: int = 100000
    
    @classmethod
    def get_firebase_credentials_path(cls) -> Path:
        """Retorna o caminho das credenciais do Firebase"""
        path = Path(cls.FIREBASE_CREDENTIALS_PATH)
        if not path.is_absolute():
            # Relativo ao diretório do projeto
            project_root = Path(__file__).parent.parent.parent
            path = project_root / path
        return path

settings = Settings()

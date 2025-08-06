from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, Field
import os
import secrets


class Settings(BaseSettings):
    # Información del proyecto
    PROJECT_NAME: str = "FinancePro API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Configuración del servidor
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    
    # Seguridad - OBLIGATORIO desde variables de entorno
    SECRET_KEY: str = Field(..., min_length=32, description="Clave secreta para JWT (mínimo 32 caracteres)")
    ENCRYPTION_KEY: str = Field(..., min_length=32, max_length=32, description="Clave de encriptación para datos PII (exactamente 32 caracteres)")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Configuración de seguridad adicional
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    REQUIRE_2FA: bool = True
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # Configuración de ambiente
    ENVIRONMENT: str = Field(default="development", description="Ambiente de ejecución (development, production)")
    CREATE_SAMPLE_DATA: bool = Field(default=True, description="Crear datos de prueba en desarrollo")
    
    # Configuración de auditoría
    ENABLE_AUDIT_LOG: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = 365
    
    # Configuración de encriptación
    ENCRYPT_PII_DATA: bool = True
    DATA_RETENTION_DAYS: int = 2555  # 7 años para datos financieros
    
    # Configuración de búsqueda
    ENABLE_FULL_TEXT_SEARCH: bool = True
    SEARCH_RESULTS_LIMIT: int = 50
    SEARCH_HIGHLIGHT: bool = True
    
    # Configuración de mensajería
    ENABLE_ASYNC_PROCESSING: bool = True
    CELERY_BROKER_URL: str = Field(..., description="URL del broker de Celery")
    CELERY_RESULT_BACKEND: str = Field(..., description="Backend de resultados de Celery")
    
    # Configuración de notificaciones
    ENABLE_NOTIFICATIONS: bool = True
    EMAIL_NOTIFICATIONS: bool = True
    SMS_NOTIFICATIONS: bool = False
    
    # Base de datos - OBLIGATORIO desde variables de entorno
    DATABASE_URL: str = Field(..., description="URL de conexión a PostgreSQL")
    
    # Redis - OBLIGATORIO desde variables de entorno
    REDIS_URL: str = Field(..., description="URL de conexión a Redis")
    
    # RabbitMQ - OBLIGATORIO desde variables de entorno
    RABBITMQ_URL: str = Field(..., description="URL completa de RabbitMQ")
    RABBITMQ_HOST: str = Field(..., description="Host de RabbitMQ")
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = Field(..., description="Usuario de RabbitMQ")
    RABBITMQ_PASSWORD: str = Field(..., description="Contraseña de RabbitMQ")
    RABBITMQ_VHOST: str = Field(..., description="Virtual host de RabbitMQ")
    
    # Meilisearch - OBLIGATORIO desde variables de entorno
    MEILISEARCH_URL: str = Field(..., description="URL de Meilisearch")
    MEILISEARCH_MASTER_KEY: str = Field(..., description="Clave maestra de Meilisearch")
    MEILISEARCH_INDEX_PREFIX: str = "financepro"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://frontend:80",
    ]
    
    # Hosts permitidos
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Email (para notificaciones)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # Configuración de archivos
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Configuración de logging
    LOG_LEVEL: str = "INFO"
    
    @validator("SECRET_KEY")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY debe tener al menos 32 caracteres")
        if v == "your-super-secret-key-change-this-in-production" or "change-this" in v:
            raise ValueError("SECRET_KEY debe ser cambiada del valor por defecto")
        return v
    
    @validator("ENCRYPTION_KEY")
    def validate_encryption_key(cls, v):
        if len(v) != 32:
            raise ValueError("ENCRYPTION_KEY debe tener exactamente 32 caracteres")
        if v == "your-encryption-key-32-chars-long" or "change-this" in v:
            raise ValueError("ENCRYPTION_KEY debe ser cambiada del valor por defecto")
        return v
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL debe ser una URL válida de PostgreSQL")
        if "password@" in v and "password" in v:
            print("⚠️  ADVERTENCIA: Usando contraseña por defecto en DATABASE_URL")
        return v
    
    @validator("MEILISEARCH_MASTER_KEY")
    def validate_meilisearch_key(cls, v):
        if "dev" in v or "change" in v:
            print("⚠️  ADVERTENCIA: Usando clave de desarrollo en MEILISEARCH_MASTER_KEY")
        return v
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @classmethod
    def generate_secret_key(cls) -> str:
        """Genera una clave secreta segura de 64 caracteres"""
        return secrets.token_urlsafe(48)  # 48 bytes = 64 caracteres en base64
    
    @classmethod
    def generate_encryption_key(cls) -> str:
        """Genera una clave de encriptación de exactamente 32 caracteres"""
        return secrets.token_urlsafe(24)[:32]  # Truncar a exactamente 32 caracteres
    
    def validate_configuration(self) -> bool:
        """Valida que la configuración sea segura para producción"""
        issues = []
        
        # Verificar claves de seguridad
        if "change-this" in self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            issues.append("SECRET_KEY insegura")
        
        if "change-this" in self.ENCRYPTION_KEY or len(self.ENCRYPTION_KEY) != 32:
            issues.append("ENCRYPTION_KEY insegura")
        
        # Verificar URLs de servicios
        if "password@" in self.DATABASE_URL:
            issues.append("DATABASE_URL con contraseña débil")
        
        if "dev" in self.MEILISEARCH_MASTER_KEY:
            issues.append("MEILISEARCH_MASTER_KEY de desarrollo")
        
        if issues:
            print(f"⚠️  PROBLEMAS DE SEGURIDAD DETECTADOS: {', '.join(issues)}")
            return False
        
        print("✅ Configuración de seguridad validada correctamente")
        return True
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Buscar archivos .env en múltiples ubicaciones
        env_file_encoding = 'utf-8'
        env_nested_delimiter = '__'


settings = Settings()

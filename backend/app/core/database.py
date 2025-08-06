from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Crear engine de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # Cambiar a True para debug SQL
)

# Crear SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos.
    
    Yields:
        Session: Sesión de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de base de datos: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def init_db() -> None:
    """
    Inicializar base de datos creando todas las tablas.
    """
    try:
        # Importar todos los modelos aquí para que SQLAlchemy los registre
        from app.models import secure_models  # noqa: F401
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        logger.info("Base de datos inicializada correctamente")
        
    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")
        raise

def check_db_connection() -> bool:
    """
    Verificar conexión a la base de datos.
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        db = SessionLocal()
        # Ejecutar una consulta simple
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Error conectando a base de datos: {e}")
        return False

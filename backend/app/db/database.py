"""
Configuración de la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Configuración del motor de base de datos
if settings.DATABASE_URL.startswith("sqlite"):
    # Para SQLite (desarrollo local)
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=settings.LOG_LEVEL == "DEBUG"
    )
else:
    # Para PostgreSQL (producción y desarrollo con Docker)
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.LOG_LEVEL == "DEBUG",
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )

# Configuración de la sesión
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
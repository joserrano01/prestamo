"""
Modelos base para la aplicación
"""
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base, declared_attr

# Base de datos declarativa
Base = declarative_base()


class AuditMixin:
    """
    Mixin para auditoría automática de entidades
    """
    
    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def created_by(cls):
        return Column(String(100), nullable=True)
    
    @declared_attr
    def updated_by(cls):
        return Column(String(100), nullable=True)


class BaseModel:
    """
    Modelo base con funcionalidades comunes
    """
    
    def to_dict(self):
        """Convertir modelo a diccionario"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        """Actualizar campos del modelo"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
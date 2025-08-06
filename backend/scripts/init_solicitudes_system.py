#!/usr/bin/env python3
"""
Script de inicialización del sistema de solicitudes y alertas
"""
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.secure_models import Base, ClienteSolicitud, SolicitudAlerta
from app.services.rabbitmq_service import RabbitMQService
from app.core.celery_app import celery_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_database_tables():
    """
    Crear tablas de base de datos si no existen
    """
    try:
        logger.info("Creando tablas de base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {str(e)}")
        return False


def setup_rabbitmq_queues():
    """
    Configurar colas y exchanges de RabbitMQ
    """
    try:
        logger.info("Configurando RabbitMQ...")
        
        with RabbitMQService() as rabbitmq:
            if rabbitmq.connect():
                # Configurar colas por defecto
                success = rabbitmq.setup_default_queues()
                if success:
                    logger.info("✅ Colas de RabbitMQ configuradas exitosamente")
                    return True
                else:
                    logger.error("❌ Error configurando colas de RabbitMQ")
                    return False
            else:
                logger.warning("⚠️  No se pudo conectar a RabbitMQ - continuando sin configurar colas")
                return True
                
    except Exception as e:
        logger.error(f"❌ Error configurando RabbitMQ: {str(e)}")
        return False


def test_celery_connection():
    """
    Probar conexión con Celery
    """
    try:
        logger.info("Probando conexión con Celery...")
        
        # Verificar que Celery puede conectarse al broker
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info("✅ Conexión con Celery exitosa")
            logger.info(f"Workers activos: {len(stats)}")
            return True
        else:
            logger.warning("⚠️  No hay workers de Celery activos")
            return True  # No es un error crítico
            
    except Exception as e:
        logger.error(f"❌ Error conectando con Celery: {str(e)}")
        return False


def create_sample_data():
    """
    Crear datos de ejemplo para pruebas (opcional)
    """
    try:
        logger.info("Verificando datos de ejemplo...")
        
        db: Session = SessionLocal()
        
        # Verificar si ya existen solicitudes
        existing_solicitudes = db.query(ClienteSolicitud).count()
        
        if existing_solicitudes == 0:
            logger.info("No se encontraron solicitudes existentes")
            logger.info("💡 Para crear datos de ejemplo, use el endpoint API correspondiente")
        else:
            logger.info(f"✅ Se encontraron {existing_solicitudes} solicitudes existentes")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando datos: {str(e)}")
        return False


def verify_system_health():
    """
    Verificar salud general del sistema
    """
    try:
        logger.info("Verificando salud del sistema...")
        
        # Verificar base de datos
        db: Session = SessionLocal()
        try:
            # Hacer una consulta simple
            db.execute("SELECT 1")
            logger.info("✅ Base de datos: OK")
        except Exception as e:
            logger.error(f"❌ Base de datos: {str(e)}")
            return False
        finally:
            db.close()
        
        # Verificar RabbitMQ
        rabbitmq = RabbitMQService()
        health = rabbitmq.health_check()
        if health['status'] == 'healthy':
            logger.info("✅ RabbitMQ: OK")
        else:
            logger.warning(f"⚠️  RabbitMQ: {health.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error verificando salud del sistema: {str(e)}")
        return False


def print_system_info():
    """
    Mostrar información del sistema
    """
    logger.info("=" * 60)
    logger.info("🏦 SISTEMA DE SOLICITUDES FINANCEPRO")
    logger.info("=" * 60)
    logger.info("")
    logger.info("📋 COMPONENTES INICIALIZADOS:")
    logger.info("  • Modelos de base de datos (ClienteSolicitud, SolicitudAlerta)")
    logger.info("  • Servicios (SolicitudesService, NotificationService, RabbitMQService)")
    logger.info("  • Tareas Celery automatizadas")
    logger.info("  • API endpoints")
    logger.info("")
    logger.info("🔄 TAREAS AUTOMÁTICAS CONFIGURADAS:")
    logger.info("  • Monitoreo SLA: Cada hora")
    logger.info("  • Procesamiento alertas: Cada 15 minutos")
    logger.info("  • Verificación vencimientos: Cada 6 horas")
    logger.info("  • Reportes diarios: 7:00 AM")
    logger.info("  • Limpieza alertas: Domingos 2:00 AM")
    logger.info("  • Seguimientos: 9:00 AM diario")
    logger.info("")
    logger.info("🚀 PRÓXIMOS PASOS:")
    logger.info("  1. Iniciar workers de Celery: celery -A app.core.celery_app worker --loglevel=info")
    logger.info("  2. Iniciar Celery Beat: celery -A app.core.celery_app beat --loglevel=info")
    logger.info("  3. Iniciar servidor FastAPI: uvicorn app.main:app --reload")
    logger.info("  4. Acceder a la documentación API: http://localhost:8000/docs")
    logger.info("")
    logger.info("=" * 60)


def main():
    """
    Función principal de inicialización
    """
    logger.info("🚀 Iniciando configuración del sistema de solicitudes...")
    
    success_count = 0
    total_steps = 5
    
    # Paso 1: Crear tablas
    if create_database_tables():
        success_count += 1
    
    # Paso 2: Configurar RabbitMQ
    if setup_rabbitmq_queues():
        success_count += 1
    
    # Paso 3: Probar Celery
    if test_celery_connection():
        success_count += 1
    
    # Paso 4: Verificar datos
    if create_sample_data():
        success_count += 1
    
    # Paso 5: Verificar salud del sistema
    if verify_system_health():
        success_count += 1
    
    # Mostrar resultados
    logger.info("")
    logger.info("=" * 60)
    if success_count == total_steps:
        logger.info("✅ INICIALIZACIÓN COMPLETADA EXITOSAMENTE")
        logger.info(f"   {success_count}/{total_steps} pasos completados")
        print_system_info()
        return 0
    else:
        logger.warning("⚠️  INICIALIZACIÓN COMPLETADA CON ADVERTENCIAS")
        logger.warning(f"   {success_count}/{total_steps} pasos completados")
        logger.warning("   Revise los mensajes anteriores para más detalles")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

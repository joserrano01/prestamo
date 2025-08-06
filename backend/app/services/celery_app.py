"""
Configuración de Celery para tareas asíncronas
Maneja procesamiento de documentos, notificaciones y tareas programadas
"""

from celery import Celery
from celery.schedules import crontab
import structlog
from typing import Dict, Any

from app.core.config import settings

logger = structlog.get_logger(__name__)

# Configuración de Celery
celery_app = Celery(
    "financepro",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.services.celery_tasks"
    ]
)

# Configuración de Celery
celery_app.conf.update(
    # Configuración de tareas
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Configuración de workers
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    
    # Configuración de resultados
    result_expires=3600,  # 1 hora
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Configuración de ruteo
    task_routes={
        "app.services.celery_tasks.process_document": {"queue": "document_processing"},
        "app.services.celery_tasks.send_email": {"queue": "email_notifications"},
        "app.services.celery_tasks.send_sms": {"queue": "sms_notifications"},
        "app.services.celery_tasks.index_for_search": {"queue": "search_indexing"},
        "app.services.celery_tasks.backup_data": {"queue": "backup_tasks"},
        "app.services.celery_tasks.cleanup_old_data": {"queue": "maintenance"},
        "app.services.celery_tasks.generate_reports": {"queue": "reports"},
    },
    
    # Configuración de colas
    task_default_queue="default",
    task_default_exchange="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    
    # Configuración de límites
    task_soft_time_limit=300,  # 5 minutos
    task_time_limit=600,       # 10 minutos
    
    # Configuración de reintentos
    task_retry_max=3,
    task_retry_delay=60,
    
    # Tareas programadas (Celery Beat)
    beat_schedule={
        # Limpieza diaria de datos antiguos
        "cleanup-old-data": {
            "task": "app.services.celery_tasks.cleanup_old_data",
            "schedule": crontab(hour=2, minute=0),  # 2:00 AM diario
        },
        
        # Respaldo semanal
        "weekly-backup": {
            "task": "app.services.celery_tasks.backup_data",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Domingo 3:00 AM
        },
        
        # Reporte diario de métricas
        "daily-metrics-report": {
            "task": "app.services.celery_tasks.generate_daily_metrics",
            "schedule": crontab(hour=6, minute=0),  # 6:00 AM diario
        },
        
        # Verificación de préstamos vencidos
        "check-overdue-loans": {
            "task": "app.services.celery_tasks.check_overdue_loans",
            "schedule": crontab(hour=9, minute=0),  # 9:00 AM diario
        },
        
        # Sincronización de índices de búsqueda
        "sync-search-indexes": {
            "task": "app.services.celery_tasks.sync_search_indexes",
            "schedule": crontab(hour=1, minute=0),  # 1:00 AM diario
        },
        
        # Verificación de salud del sistema
        "system-health-check": {
            "task": "app.services.celery_tasks.system_health_check",
            "schedule": crontab(minute="*/30"),  # Cada 30 minutos
        },
    },
)

# Configuración de logging para Celery
@celery_app.task(bind=True)
def debug_task(self):
    """Tarea de debug para verificar configuración"""
    logger.info(f"Request: {self.request!r}")
    return "Debug task executed successfully"

# Configuración de manejo de errores
@celery_app.task(bind=True)
def handle_task_failure(self, task_id, error, traceback):
    """Manejar fallos de tareas"""
    logger.error(
        "Tarea falló",
        task_id=task_id,
        error=str(error),
        traceback=traceback
    )

# Configuración de eventos
@celery_app.task(bind=True)
def log_task_success(self, task_id, result):
    """Log de tareas exitosas"""
    logger.info(
        "Tarea completada exitosamente",
        task_id=task_id,
        result_type=type(result).__name__
    )

# Configuración de monitoreo
def setup_celery_monitoring():
    """Configurar monitoreo de Celery"""
    from celery import signals
    
    @signals.task_prerun.connect
    def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
        logger.info(
            "Iniciando tarea",
            task_id=task_id,
            task_name=task.name if task else "unknown"
        )
    
    @signals.task_postrun.connect
    def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
        logger.info(
            "Tarea finalizada",
            task_id=task_id,
            task_name=task.name if task else "unknown",
            state=state
        )
    
    @signals.task_failure.connect
    def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
        logger.error(
            "Tarea falló",
            task_id=task_id,
            task_name=sender.name if sender else "unknown",
            exception=str(exception),
            traceback=str(traceback)
        )
    
    @signals.task_retry.connect
    def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **kwds):
        logger.warning(
            "Reintentando tarea",
            task_id=task_id,
            task_name=sender.name if sender else "unknown",
            reason=str(reason)
        )

# Configurar monitoreo al importar
setup_celery_monitoring()

# Función para obtener estadísticas de Celery
def get_celery_stats() -> Dict[str, Any]:
    """Obtener estadísticas de Celery"""
    try:
        inspect = celery_app.control.inspect()
        
        stats = {
            "active_tasks": inspect.active(),
            "scheduled_tasks": inspect.scheduled(),
            "reserved_tasks": inspect.reserved(),
            "registered_tasks": list(celery_app.tasks.keys()),
            "worker_stats": inspect.stats(),
        }
        
        return stats
        
    except Exception as e:
        logger.error("Error obteniendo estadísticas de Celery", error=str(e))
        return {}

# Función para verificar salud de Celery
def check_celery_health() -> Dict[str, Any]:
    """Verificar salud de Celery"""
    try:
        inspect = celery_app.control.inspect()
        ping_result = inspect.ping()
        
        if ping_result:
            return {
                "status": "healthy",
                "workers": list(ping_result.keys()),
                "worker_count": len(ping_result)
            }
        else:
            return {
                "status": "unhealthy",
                "workers": [],
                "worker_count": 0
            }
            
    except Exception as e:
        logger.error("Error verificando salud de Celery", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "workers": [],
            "worker_count": 0
        }

"""
Inicialización de la aplicación Celery para FinancePro
"""
import os
from celery import Celery
from app.core.celery_config import get_celery_config

# Crear instancia de Celery
celery_app = Celery("financepro")

# Configurar Celery
celery_app.config_from_object(get_celery_config())

# Auto-descubrir tareas
celery_app.autodiscover_tasks([
    'app.tasks.solicitudes_tasks',
])

# Configuración adicional para desarrollo/producción
if os.getenv('ENVIRONMENT') == 'development':
    celery_app.conf.update(
        task_always_eager=False,  # Ejecutar tareas de forma asíncrona
        task_eager_propagates=True,
        worker_log_level='DEBUG',
    )
else:
    celery_app.conf.update(
        task_always_eager=False,
        worker_log_level='INFO',
    )

# Configurar logging
import logging
from app.core.celery_config import CELERY_LOGGING_CONFIG

logging.config.dictConfig(CELERY_LOGGING_CONFIG)

if __name__ == '__main__':
    celery_app.start()

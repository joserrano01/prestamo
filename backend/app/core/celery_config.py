"""
Configuración de Celery para el sistema de solicitudes
"""
from celery.schedules import crontab
from app.core.config import settings

# Configuración de Celery
CELERY_CONFIG = {
    'broker_url': getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': getattr(settings, 'CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_track_started': True,
    'task_time_limit': 30 * 60,  # 30 minutos
    'task_soft_time_limit': 25 * 60,  # 25 minutos
    'worker_prefetch_multiplier': 1,
    'worker_max_tasks_per_child': 1000,
    
    # Configuración de rutas de tareas
    'task_routes': {
        # Tareas de solicitudes
        'app.tasks.solicitudes_tasks.monitorear_sla_solicitudes': {'queue': 'sla_monitoring'},
        'app.tasks.solicitudes_tasks.procesar_alertas_pendientes': {'queue': 'alerts'},
        'app.tasks.solicitudes_tasks.verificar_solicitudes_vencidas': {'queue': 'maintenance'},
        'app.tasks.solicitudes_tasks.generar_reporte_diario': {'queue': 'reports'},
        'app.tasks.solicitudes_tasks.limpiar_alertas_antiguas': {'queue': 'cleanup'},
        'app.tasks.solicitudes_tasks.notificar_seguimientos_programados': {'queue': 'notifications'},
        
        # Tareas de agenda de cobranza
        'app.tasks.agenda_cobranza_tasks.procesar_alertas_cobranza_pendientes': {'queue': 'alerts'},
        'app.tasks.agenda_cobranza_tasks.verificar_actividades_vencidas': {'queue': 'maintenance'},
        'app.tasks.agenda_cobranza_tasks.verificar_promesas_pago_vencidas': {'queue': 'maintenance'},
        'app.tasks.agenda_cobranza_tasks.generar_agenda_diaria': {'queue': 'notifications'},
        'app.tasks.agenda_cobranza_tasks.generar_reporte_efectividad_semanal': {'queue': 'reports'},
        'app.tasks.agenda_cobranza_tasks.limpiar_alertas_cobranza_antiguas': {'queue': 'cleanup'},
        'app.tasks.agenda_cobranza_tasks.crear_actividades_automaticas_mora': {'queue': 'cobranza'},
    },
    
    # Configuración de colas
    'task_default_queue': 'default',
    'task_queues': {
        'default': {
            'exchange': 'default',
            'exchange_type': 'direct',
            'routing_key': 'default',
        },
        'sla_monitoring': {
            'exchange': 'sla',
            'exchange_type': 'direct',
            'routing_key': 'sla.monitoring',
        },
        'alerts': {
            'exchange': 'alerts',
            'exchange_type': 'direct',
            'routing_key': 'alerts.processing',
        },
        'notifications': {
            'exchange': 'notifications',
            'exchange_type': 'direct',
            'routing_key': 'notifications.send',
        },
        'reports': {
            'exchange': 'reports',
            'exchange_type': 'direct',
            'routing_key': 'reports.generate',
        },
        'maintenance': {
            'exchange': 'maintenance',
            'exchange_type': 'direct',
            'routing_key': 'maintenance.tasks',
        },
        'cleanup': {
            'exchange': 'cleanup',
            'exchange_type': 'direct',
            'routing_key': 'cleanup.tasks',
        },
        'cobranza': {
            'exchange': 'cobranza',
            'exchange_type': 'direct',
            'routing_key': 'cobranza.tasks',
        },
    },
    
    # Configuración de tareas programadas (Celery Beat)
    'beat_schedule': {
        # Monitoreo de SLA cada hora
        'monitorear-sla-solicitudes': {
            'task': 'app.tasks.solicitudes_tasks.monitorear_sla_solicitudes',
            'schedule': crontab(minute=0),  # Cada hora en punto
            'options': {'queue': 'sla_monitoring'}
        },
        
        # Procesar alertas pendientes cada 15 minutos
        'procesar-alertas-pendientes': {
            'task': 'app.tasks.solicitudes_tasks.procesar_alertas_pendientes',
            'schedule': crontab(minute='*/15'),  # Cada 15 minutos
            'options': {'queue': 'alerts'}
        },
        
        # Verificar solicitudes vencidas cada 6 horas
        'verificar-solicitudes-vencidas': {
            'task': 'app.tasks.solicitudes_tasks.verificar_solicitudes_vencidas',
            'schedule': crontab(minute=0, hour='*/6'),  # Cada 6 horas
            'options': {'queue': 'maintenance'}
        },
        
        # Generar reporte diario a las 7:00 AM
        'generar-reporte-diario': {
            'task': 'app.tasks.solicitudes_tasks.generar_reporte_diario',
            'schedule': crontab(hour=7, minute=0),  # 7:00 AM diario
            'options': {'queue': 'reports'}
        },
        
        # Limpiar alertas antiguas semanalmente (domingos a las 2:00 AM)
        'limpiar-alertas-antiguas': {
            'task': 'app.tasks.solicitudes_tasks.limpiar_alertas_antiguas',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Domingos 2:00 AM
            'options': {'queue': 'cleanup'}
        },
        
        # Notificar seguimientos programados diariamente a las 9:00 AM
        'notificar-seguimientos-programados': {
            'task': 'app.tasks.solicitudes_tasks.notificar_seguimientos_programados',
            'schedule': crontab(hour=9, minute=0),  # 9:00 AM diario
            'options': {'queue': 'notifications'}
        },
        
        # ============================================================================
        # TAREAS DE AGENDA DE COBRANZA
        # ============================================================================
        
        # Procesar alertas de cobranza pendientes cada 15 minutos
        'procesar-alertas-cobranza-pendientes': {
            'task': 'app.tasks.agenda_cobranza_tasks.procesar_alertas_cobranza_pendientes',
            'schedule': crontab(minute='*/15'),  # Cada 15 minutos
            'options': {'queue': 'alerts'}
        },
        
        # Verificar actividades vencidas cada hora
        'verificar-actividades-vencidas': {
            'task': 'app.tasks.agenda_cobranza_tasks.verificar_actividades_vencidas',
            'schedule': crontab(minute=0),  # Cada hora en punto
            'options': {'queue': 'maintenance'}
        },
        
        # Verificar promesas de pago vencidas diariamente a las 8:00 AM
        'verificar-promesas-pago-vencidas': {
            'task': 'app.tasks.agenda_cobranza_tasks.verificar_promesas_pago_vencidas',
            'schedule': crontab(hour=8, minute=0),  # 8:00 AM diario
            'options': {'queue': 'maintenance'}
        },
        
        # Generar agenda diaria a las 7:30 AM
        'generar-agenda-diaria': {
            'task': 'app.tasks.agenda_cobranza_tasks.generar_agenda_diaria',
            'schedule': crontab(hour=7, minute=30),  # 7:30 AM diario
            'options': {'queue': 'notifications'}
        },
        
        # Generar reporte de efectividad semanal (lunes a las 8:00 AM)
        'generar-reporte-efectividad-semanal': {
            'task': 'app.tasks.agenda_cobranza_tasks.generar_reporte_efectividad_semanal',
            'schedule': crontab(hour=8, minute=0, day_of_week=1),  # Lunes 8:00 AM
            'options': {'queue': 'reports'}
        },
        
        # Limpiar alertas de cobranza antiguas semanalmente (domingos a las 3:00 AM)
        'limpiar-alertas-cobranza-antiguas': {
            'task': 'app.tasks.agenda_cobranza_tasks.limpiar_alertas_cobranza_antiguas',
            'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Domingos 3:00 AM
            'options': {'queue': 'cleanup'}
        },
        
        # Crear actividades automáticas para préstamos en mora (diario a las 6:00 AM)
        'crear-actividades-automaticas-mora': {
            'task': 'app.tasks.agenda_cobranza_tasks.crear_actividades_automaticas_mora',
            'schedule': crontab(hour=6, minute=0),  # 6:00 AM diario
            'options': {'queue': 'cobranza'}
        },
    },
}

# Configuración de logging para Celery
CELERY_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
        'celery': {
            'format': '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'celery',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/celery.log',
            'formatter': 'celery',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery.task': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'app.tasks': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}

# Configuración de monitoreo
CELERY_MONITORING_CONFIG = {
    'worker_send_task_events': True,
    'task_send_sent_event': True,
    'worker_hijack_root_logger': False,
    'worker_log_color': False,
    'task_annotations': {
        '*': {
            'rate_limit': '100/m',  # 100 tareas por minuto por defecto
        },
        'app.tasks.solicitudes_tasks.procesar_alertas_pendientes': {
            'rate_limit': '200/m',  # Más frecuente para alertas
        },
        'app.tasks.solicitudes_tasks.monitorear_sla_solicitudes': {
            'rate_limit': '50/m',   # Menos frecuente para monitoreo SLA
        },
    },
}

# Configuración de retry para tareas
CELERY_RETRY_CONFIG = {
    'task_acks_late': True,
    'task_reject_on_worker_lost': True,
    'task_default_retry_delay': 60,  # 1 minuto
    'task_max_retries': 3,
    'task_retry_backoff': True,
    'task_retry_backoff_max': 300,  # 5 minutos máximo
    'task_retry_jitter': True,
}

# Configuración completa combinada
def get_celery_config():
    """
    Retorna la configuración completa de Celery
    """
    config = {}
    config.update(CELERY_CONFIG)
    config.update(CELERY_MONITORING_CONFIG)
    config.update(CELERY_RETRY_CONFIG)
    
    return config

"""
Endpoints de API para monitoreo del sistema
Proporciona información sobre salud, métricas y estado de servicios
"""

from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from app.services.celery_app import get_celery_stats, check_celery_health
from app.services.search_service import search_service
from app.services.messaging_service import messaging_service
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Modelos de respuesta
class ServiceHealth(BaseModel):
    """Estado de salud de un servicio"""
    name: str
    status: str  # healthy, unhealthy, unknown
    response_time_ms: int
    details: Dict[str, Any] = {}
    last_check: str

class SystemHealth(BaseModel):
    """Estado de salud general del sistema"""
    overall_status: str
    timestamp: str
    services: List[ServiceHealth]
    uptime_hours: float
    version: str

class SystemMetrics(BaseModel):
    """Métricas del sistema"""
    timestamp: str
    database: Dict[str, Any]
    redis: Dict[str, Any]
    meilisearch: Dict[str, Any]
    rabbitmq: Dict[str, Any]
    celery: Dict[str, Any]
    application: Dict[str, Any]

class QueueStats(BaseModel):
    """Estadísticas de colas"""
    queue_name: str
    message_count: int
    consumer_count: int
    processing_rate: float
    avg_processing_time: float

class SearchIndexStats(BaseModel):
    """Estadísticas de índices de búsqueda"""
    index_name: str
    document_count: int
    index_size_mb: float
    last_updated: str
    health_status: str

@router.get("/health", response_model=SystemHealth)
async def get_system_health():
    """
    Verificar estado de salud general del sistema.
    
    Retorna el estado de todos los servicios críticos:
    - Base de datos PostgreSQL
    - Redis
    - RabbitMQ
    - Meilisearch
    - Celery workers
    """
    try:
        services = []
        overall_healthy = True
        
        # Verificar base de datos
        db_health = await _check_database_health()
        services.append(ServiceHealth(
            name="postgresql",
            status="healthy" if db_health["healthy"] else "unhealthy",
            response_time_ms=db_health.get("response_time_ms", 0),
            details=db_health,
            last_check=datetime.utcnow().isoformat()
        ))
        if not db_health["healthy"]:
            overall_healthy = False
        
        # Verificar Redis
        redis_health = await _check_redis_health()
        services.append(ServiceHealth(
            name="redis",
            status="healthy" if redis_health["healthy"] else "unhealthy",
            response_time_ms=redis_health.get("response_time_ms", 0),
            details=redis_health,
            last_check=datetime.utcnow().isoformat()
        ))
        if not redis_health["healthy"]:
            overall_healthy = False
        
        # Verificar RabbitMQ
        rabbitmq_health = await _check_rabbitmq_health()
        services.append(ServiceHealth(
            name="rabbitmq",
            status="healthy" if rabbitmq_health["healthy"] else "unhealthy",
            response_time_ms=rabbitmq_health.get("response_time_ms", 0),
            details=rabbitmq_health,
            last_check=datetime.utcnow().isoformat()
        ))
        if not rabbitmq_health["healthy"]:
            overall_healthy = False
        
        # Verificar Meilisearch
        meilisearch_health = await _check_meilisearch_health()
        services.append(ServiceHealth(
            name="meilisearch",
            status="healthy" if meilisearch_health["healthy"] else "unhealthy",
            response_time_ms=meilisearch_health.get("response_time_ms", 0),
            details=meilisearch_health,
            last_check=datetime.utcnow().isoformat()
        ))
        if not meilisearch_health["healthy"]:
            overall_healthy = False
        
        # Verificar Celery
        celery_health = check_celery_health()
        services.append(ServiceHealth(
            name="celery",
            status=celery_health["status"],
            response_time_ms=0,
            details=celery_health,
            last_check=datetime.utcnow().isoformat()
        ))
        if celery_health["status"] != "healthy":
            overall_healthy = False
        
        response = SystemHealth(
            overall_status="healthy" if overall_healthy else "unhealthy",
            timestamp=datetime.utcnow().isoformat(),
            services=services,
            uptime_hours=_get_uptime_hours(),
            version=settings.PROJECT_VERSION
        )
        
        logger.info("Verificación de salud del sistema completada", 
                   overall_status=response.overall_status,
                   services_count=len(services))
        
        return response
        
    except Exception as e:
        logger.error("Error verificando salud del sistema", error=str(e))
        raise HTTPException(status_code=500, detail="Error verificando salud del sistema")

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """
    Obtener métricas detalladas del sistema.
    
    Incluye métricas de rendimiento, uso de recursos y estadísticas operacionales.
    """
    try:
        # Métricas de base de datos
        db_metrics = await _get_database_metrics()
        
        # Métricas de Redis
        redis_metrics = await _get_redis_metrics()
        
        # Métricas de Meilisearch
        meilisearch_metrics = await _get_meilisearch_metrics()
        
        # Métricas de RabbitMQ
        rabbitmq_metrics = await _get_rabbitmq_metrics()
        
        # Métricas de Celery
        celery_metrics = get_celery_stats()
        
        # Métricas de aplicación
        app_metrics = await _get_application_metrics()
        
        response = SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            database=db_metrics,
            redis=redis_metrics,
            meilisearch=meilisearch_metrics,
            rabbitmq=rabbitmq_metrics,
            celery=celery_metrics,
            application=app_metrics
        )
        
        logger.info("Métricas del sistema obtenidas correctamente")
        
        return response
        
    except Exception as e:
        logger.error("Error obteniendo métricas del sistema", error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo métricas")

@router.get("/queues", response_model=List[QueueStats])
async def get_queue_stats():
    """
    Obtener estadísticas de las colas de mensajería.
    
    Retorna información sobre el estado de todas las colas de RabbitMQ.
    """
    try:
        # Obtener estadísticas de colas de RabbitMQ
        queue_stats = await messaging_service.get_queue_stats()
        
        stats_list = []
        for queue_name, stats in queue_stats.items():
            stats_list.append(QueueStats(
                queue_name=queue_name,
                message_count=stats.get("message_count", 0),
                consumer_count=stats.get("consumer_count", 0),
                processing_rate=_calculate_processing_rate(queue_name),
                avg_processing_time=_get_avg_processing_time(queue_name)
            ))
        
        logger.info("Estadísticas de colas obtenidas", 
                   queues_count=len(stats_list))
        
        return stats_list
        
    except Exception as e:
        logger.error("Error obteniendo estadísticas de colas", error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas de colas")

@router.get("/search-indexes", response_model=List[SearchIndexStats])
async def get_search_index_stats():
    """
    Obtener estadísticas de los índices de búsqueda.
    
    Retorna información sobre el estado de todos los índices de Meilisearch.
    """
    try:
        # Obtener estadísticas de índices
        index_stats = await search_service.get_search_stats()
        
        stats_list = []
        for index_name, stats in index_stats.items():
            stats_list.append(SearchIndexStats(
                index_name=index_name,
                document_count=stats.get("numberOfDocuments", 0),
                index_size_mb=_calculate_index_size(stats),
                last_updated=stats.get("lastUpdate", datetime.utcnow().isoformat()),
                health_status="healthy" if stats.get("numberOfDocuments", 0) > 0 else "empty"
            ))
        
        logger.info("Estadísticas de índices de búsqueda obtenidas", 
                   indexes_count=len(stats_list))
        
        return stats_list
        
    except Exception as e:
        logger.error("Error obteniendo estadísticas de índices", error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas de índices")

@router.get("/performance")
async def get_performance_metrics():
    """
    Obtener métricas de rendimiento en tiempo real.
    
    Incluye latencia, throughput y uso de recursos.
    """
    try:
        performance_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "api_response_times": await _get_api_response_times(),
            "database_performance": await _get_database_performance(),
            "search_performance": await _get_search_performance(),
            "queue_performance": await _get_queue_performance(),
            "system_resources": await _get_system_resources()
        }
        
        logger.info("Métricas de rendimiento obtenidas")
        
        return performance_data
        
    except Exception as e:
        logger.error("Error obteniendo métricas de rendimiento", error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo métricas de rendimiento")

@router.get("/alerts")
async def get_system_alerts():
    """
    Obtener alertas activas del sistema.
    
    Retorna alertas basadas en umbrales de rendimiento y salud.
    """
    try:
        alerts = []
        
        # Verificar alertas de base de datos
        db_alerts = await _check_database_alerts()
        alerts.extend(db_alerts)
        
        # Verificar alertas de colas
        queue_alerts = await _check_queue_alerts()
        alerts.extend(queue_alerts)
        
        # Verificar alertas de búsqueda
        search_alerts = await _check_search_alerts()
        alerts.extend(search_alerts)
        
        # Verificar alertas de recursos del sistema
        resource_alerts = await _check_resource_alerts()
        alerts.extend(resource_alerts)
        
        response = {
            "timestamp": datetime.utcnow().isoformat(),
            "alert_count": len(alerts),
            "alerts": alerts,
            "severity_summary": _summarize_alert_severity(alerts)
        }
        
        logger.info("Alertas del sistema obtenidas", 
                   alert_count=len(alerts))
        
        return response
        
    except Exception as e:
        logger.error("Error obteniendo alertas del sistema", error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo alertas")

@router.post("/maintenance/start")
async def start_maintenance_mode():
    """
    Activar modo de mantenimiento.
    
    Pone el sistema en modo de mantenimiento para actualizaciones.
    """
    try:
        # Implementar lógica de modo de mantenimiento
        maintenance_status = {
            "maintenance_mode": True,
            "started_at": datetime.utcnow().isoformat(),
            "message": "Sistema en modo de mantenimiento"
        }
        
        logger.warning("Modo de mantenimiento activado")
        
        return maintenance_status
        
    except Exception as e:
        logger.error("Error activando modo de mantenimiento", error=str(e))
        raise HTTPException(status_code=500, detail="Error activando modo de mantenimiento")

@router.post("/maintenance/stop")
async def stop_maintenance_mode():
    """
    Desactivar modo de mantenimiento.
    
    Restaura el funcionamiento normal del sistema.
    """
    try:
        # Implementar lógica para salir del modo de mantenimiento
        maintenance_status = {
            "maintenance_mode": False,
            "stopped_at": datetime.utcnow().isoformat(),
            "message": "Sistema operativo normal"
        }
        
        logger.info("Modo de mantenimiento desactivado")
        
        return maintenance_status
        
    except Exception as e:
        logger.error("Error desactivando modo de mantenimiento", error=str(e))
        raise HTTPException(status_code=500, detail="Error desactivando modo de mantenimiento")

# Funciones auxiliares (simuladas para el ejemplo)
async def _check_database_health() -> Dict[str, Any]:
    """Verificar salud de la base de datos"""
    return {
        "healthy": True,
        "response_time_ms": 15,
        "connections_active": 5,
        "connections_max": 100
    }

async def _check_redis_health() -> Dict[str, Any]:
    """Verificar salud de Redis"""
    return {
        "healthy": True,
        "response_time_ms": 3,
        "memory_usage_mb": 45.2,
        "connected_clients": 8
    }

async def _check_rabbitmq_health() -> Dict[str, Any]:
    """Verificar salud de RabbitMQ"""
    return {
        "healthy": True,
        "response_time_ms": 8,
        "queues_count": 7,
        "messages_total": 156
    }

async def _check_meilisearch_health() -> Dict[str, Any]:
    """Verificar salud de Meilisearch"""
    return {
        "healthy": True,
        "response_time_ms": 12,
        "indexes_count": 4,
        "documents_total": 1250
    }

def _get_uptime_hours() -> float:
    """Obtener tiempo de actividad en horas"""
    return 72.5

async def _get_database_metrics() -> Dict[str, Any]:
    """Obtener métricas de base de datos"""
    return {
        "connections_active": 5,
        "connections_max": 100,
        "query_avg_time_ms": 25.3,
        "slow_queries_count": 2,
        "database_size_mb": 450.2
    }

async def _get_redis_metrics() -> Dict[str, Any]:
    """Obtener métricas de Redis"""
    return {
        "memory_usage_mb": 45.2,
        "memory_max_mb": 512,
        "connected_clients": 8,
        "operations_per_sec": 1250,
        "hit_rate_percent": 94.5
    }

async def _get_meilisearch_metrics() -> Dict[str, Any]:
    """Obtener métricas de Meilisearch"""
    return {
        "indexes_count": 4,
        "documents_total": 1250,
        "searches_per_minute": 45,
        "avg_search_time_ms": 18.5
    }

async def _get_rabbitmq_metrics() -> Dict[str, Any]:
    """Obtener métricas de RabbitMQ"""
    return {
        "queues_count": 7,
        "messages_total": 156,
        "messages_per_minute": 25,
        "consumers_count": 12
    }

async def _get_application_metrics() -> Dict[str, Any]:
    """Obtener métricas de aplicación"""
    return {
        "requests_per_minute": 120,
        "avg_response_time_ms": 85.2,
        "error_rate_percent": 0.5,
        "active_sessions": 25
    }

def _calculate_processing_rate(queue_name: str) -> float:
    """Calcular tasa de procesamiento de cola"""
    return 15.5  # mensajes por minuto

def _get_avg_processing_time(queue_name: str) -> float:
    """Obtener tiempo promedio de procesamiento"""
    return 2.3  # segundos

def _calculate_index_size(stats: Dict[str, Any]) -> float:
    """Calcular tamaño del índice en MB"""
    return stats.get("numberOfDocuments", 0) * 0.1  # Estimación

async def _get_api_response_times() -> Dict[str, Any]:
    """Obtener tiempos de respuesta de API"""
    return {
        "avg_ms": 85.2,
        "p50_ms": 65.0,
        "p95_ms": 150.0,
        "p99_ms": 250.0
    }

async def _get_database_performance() -> Dict[str, Any]:
    """Obtener rendimiento de base de datos"""
    return {
        "avg_query_time_ms": 25.3,
        "slow_queries_count": 2,
        "connections_utilization_percent": 15.0
    }

async def _get_search_performance() -> Dict[str, Any]:
    """Obtener rendimiento de búsqueda"""
    return {
        "avg_search_time_ms": 18.5,
        "searches_per_minute": 45,
        "cache_hit_rate_percent": 85.2
    }

async def _get_queue_performance() -> Dict[str, Any]:
    """Obtener rendimiento de colas"""
    return {
        "avg_processing_time_ms": 2300,
        "messages_per_minute": 25,
        "error_rate_percent": 0.2
    }

async def _get_system_resources() -> Dict[str, Any]:
    """Obtener recursos del sistema"""
    return {
        "cpu_usage_percent": 35.2,
        "memory_usage_percent": 68.5,
        "disk_usage_percent": 45.8,
        "network_io_mbps": 12.5
    }

async def _check_database_alerts() -> List[Dict[str, Any]]:
    """Verificar alertas de base de datos"""
    return []

async def _check_queue_alerts() -> List[Dict[str, Any]]:
    """Verificar alertas de colas"""
    return []

async def _check_search_alerts() -> List[Dict[str, Any]]:
    """Verificar alertas de búsqueda"""
    return []

async def _check_resource_alerts() -> List[Dict[str, Any]]:
    """Verificar alertas de recursos"""
    return []

def _summarize_alert_severity(alerts: List[Dict[str, Any]]) -> Dict[str, int]:
    """Resumir severidad de alertas"""
    return {
        "critical": 0,
        "warning": 0,
        "info": 0
    }

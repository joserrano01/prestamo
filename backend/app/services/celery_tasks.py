"""
Tareas asíncronas de Celery para el sistema de préstamos
Incluye procesamiento de documentos, notificaciones, respaldos y mantenimiento
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog
from celery import current_task
from sqlalchemy.orm import Session

from app.services.celery_app import celery_app
from app.services.search_service import search_service
from app.core.config import settings
from app.core.security import log_audit_event

logger = structlog.get_logger(__name__)

@celery_app.task(bind=True, max_retries=3)
def process_document(self, document_id: str, processing_type: str, document_data: Dict[str, Any]):
    """Procesar documento subido (OCR, validación, extracción de texto)"""
    try:
        logger.info("Iniciando procesamiento de documento", 
                   document_id=document_id, 
                   processing_type=processing_type)
        
        # Simular procesamiento según el tipo
        if processing_type == "ocr":
            result = _process_ocr(document_data)
        elif processing_type == "validation":
            result = _validate_document(document_data)
        elif processing_type == "text_extraction":
            result = _extract_text(document_data)
        elif processing_type == "virus_scan":
            result = _scan_virus(document_data)
        else:
            raise ValueError(f"Tipo de procesamiento no soportado: {processing_type}")
        
        # Indexar documento para búsqueda si el procesamiento fue exitoso
        if result.get("success"):
            index_for_search.delay("document", document_id, "create", {
                "id": document_id,
                "contenido_extraido": result.get("extracted_text", ""),
                "tipo_documento": document_data.get("tipo_documento", ""),
                "nombre_archivo": document_data.get("nombre_archivo", ""),
                **document_data
            })
        
        # Log de auditoría
        log_audit_event(
            action="document_processed",
            resource_type="document",
            resource_id=document_id,
            details={
                "processing_type": processing_type,
                "success": result.get("success"),
                "task_id": self.request.id
            }
        )
        
        logger.info("Documento procesado exitosamente", 
                   document_id=document_id, 
                   processing_type=processing_type,
                   success=result.get("success"))
        
        return result
        
    except Exception as e:
        logger.error("Error procesando documento", 
                    document_id=document_id, 
                    processing_type=processing_type,
                    error=str(e))
        
        # Reintentar si no se han agotado los intentos
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, max_retries=3)
def send_email(self, recipient: str, subject: str, template: str, data: Dict[str, Any]):
    """Enviar notificación por email"""
    try:
        logger.info("Enviando email", recipient=recipient, template=template)
        
        # Simular envío de email
        email_content = _generate_email_content(template, data)
        
        # Aquí iría la integración con servicio de email real (SendGrid, AWS SES, etc.)
        result = _send_email_via_provider(recipient, subject, email_content)
        
        # Log de auditoría
        log_audit_event(
            action="email_sent",
            resource_type="notification",
            resource_id=recipient,
            details={
                "template": template,
                "success": result.get("success"),
                "task_id": self.request.id
            }
        )
        
        logger.info("Email enviado exitosamente", 
                   recipient=recipient, 
                   template=template,
                   success=result.get("success"))
        
        return result
        
    except Exception as e:
        logger.error("Error enviando email", 
                    recipient=recipient, 
                    template=template,
                    error=str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True, max_retries=2)
def send_sms(self, phone: str, message: str, data: Dict[str, Any]):
    """Enviar notificación por SMS"""
    try:
        logger.info("Enviando SMS", phone=phone[:4] + "****")
        
        # Simular envío de SMS
        result = _send_sms_via_provider(phone, message)
        
        # Log de auditoría
        log_audit_event(
            action="sms_sent",
            resource_type="notification",
            resource_id=phone,
            details={
                "success": result.get("success"),
                "task_id": self.request.id
            }
        )
        
        logger.info("SMS enviado exitosamente", 
                   phone=phone[:4] + "****",
                   success=result.get("success"))
        
        return result
        
    except Exception as e:
        logger.error("Error enviando SMS", 
                    phone=phone[:4] + "****",
                    error=str(e))
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30 * (self.request.retries + 1))
        
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def index_for_search(self, entity_type: str, entity_id: str, action: str, data: Dict[str, Any]):
    """Indexar entidad para búsqueda de texto completo"""
    try:
        logger.info("Indexando para búsqueda", 
                   entity_type=entity_type, 
                   entity_id=entity_id, 
                   action=action)
        
        if action == "create" or action == "update":
            if entity_type == "client":
                # Usar asyncio para ejecutar función async
                import asyncio
                asyncio.run(search_service.index_client(data))
            elif entity_type == "loan":
                import asyncio
                asyncio.run(search_service.index_loan(data))
            elif entity_type == "document":
                # Indexar documento con contenido extraído
                pass  # Implementar indexación de documentos
                
        elif action == "delete":
            index_name = f"{settings.MEILISEARCH_INDEX_PREFIX}_{entity_type}s"
            import asyncio
            asyncio.run(search_service.delete_document(index_name, entity_id))
        
        logger.info("Indexación completada", 
                   entity_type=entity_type, 
                   entity_id=entity_id, 
                   action=action)
        
        return {"success": True, "indexed": True}
        
    except Exception as e:
        logger.error("Error indexando para búsqueda", 
                    entity_type=entity_type, 
                    entity_id=entity_id,
                    error=str(e))
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def backup_data(self, backup_type: str = "incremental"):
    """Realizar respaldo de datos"""
    try:
        logger.info("Iniciando respaldo de datos", backup_type=backup_type)
        
        backup_timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{backup_type}_{backup_timestamp}.sql"
        
        # Simular respaldo de base de datos
        result = _perform_database_backup(backup_filename, backup_type)
        
        # Respaldo de archivos subidos
        if backup_type == "full":
            _backup_uploaded_files(backup_timestamp)
        
        # Log de auditoría
        log_audit_event(
            action="backup_completed",
            resource_type="system",
            resource_id="database",
            details={
                "backup_type": backup_type,
                "filename": backup_filename,
                "success": result.get("success"),
                "task_id": self.request.id
            }
        )
        
        logger.info("Respaldo completado", 
                   backup_type=backup_type,
                   filename=backup_filename,
                   success=result.get("success"))
        
        return result
        
    except Exception as e:
        logger.error("Error en respaldo de datos", 
                    backup_type=backup_type,
                    error=str(e))
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def cleanup_old_data(self):
    """Limpiar datos antiguos según políticas de retención"""
    try:
        logger.info("Iniciando limpieza de datos antiguos")
        
        cleanup_date = datetime.utcnow() - timedelta(days=settings.DATA_RETENTION_DAYS)
        
        # Limpiar logs de auditoría antiguos
        audit_cleanup_result = _cleanup_old_audit_logs(cleanup_date)
        
        # Limpiar sesiones expiradas
        session_cleanup_result = _cleanup_expired_sessions()
        
        # Limpiar archivos temporales
        temp_cleanup_result = _cleanup_temp_files()
        
        result = {
            "success": True,
            "audit_logs_cleaned": audit_cleanup_result.get("count", 0),
            "sessions_cleaned": session_cleanup_result.get("count", 0),
            "temp_files_cleaned": temp_cleanup_result.get("count", 0)
        }
        
        # Log de auditoría
        log_audit_event(
            action="data_cleanup",
            resource_type="system",
            resource_id="maintenance",
            details={
                **result,
                "task_id": self.request.id
            }
        )
        
        logger.info("Limpieza de datos completada", **result)
        
        return result
        
    except Exception as e:
        logger.error("Error en limpieza de datos", error=str(e))
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def generate_daily_metrics(self):
    """Generar métricas diarias del sistema"""
    try:
        logger.info("Generando métricas diarias")
        
        metrics = {
            "date": datetime.utcnow().date().isoformat(),
            "loans_created": _count_daily_loans(),
            "clients_registered": _count_daily_clients(),
            "documents_processed": _count_daily_documents(),
            "login_attempts": _count_daily_logins(),
            "system_uptime": _get_system_uptime(),
            "search_queries": _count_daily_searches(),
            "notifications_sent": _count_daily_notifications()
        }
        
        # Guardar métricas en base de datos o enviar a sistema de monitoreo
        _save_daily_metrics(metrics)
        
        logger.info("Métricas diarias generadas", **metrics)
        
        return {"success": True, "metrics": metrics}
        
    except Exception as e:
        logger.error("Error generando métricas diarias", error=str(e))
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def check_overdue_loans(self):
    """Verificar préstamos vencidos y enviar notificaciones"""
    try:
        logger.info("Verificando préstamos vencidos")
        
        overdue_loans = _get_overdue_loans()
        notifications_sent = 0
        
        for loan in overdue_loans:
            # Enviar notificación al cliente
            send_email.delay(
                recipient=loan["client_email"],
                subject="Recordatorio de Pago - Préstamo Vencido",
                template="overdue_loan_notification",
                data={
                    "loan_number": loan["numero_prestamo"],
                    "amount_due": loan["monto_vencido"],
                    "days_overdue": loan["dias_vencido"],
                    "client_name": loan["client_name"]
                }
            )
            
            # Notificar al gestor de cuenta
            send_email.delay(
                recipient=loan["account_manager_email"],
                subject=f"Préstamo Vencido - {loan['numero_prestamo']}",
                template="overdue_loan_manager_notification",
                data=loan
            )
            
            notifications_sent += 1
        
        result = {
            "success": True,
            "overdue_loans_found": len(overdue_loans),
            "notifications_sent": notifications_sent
        }
        
        logger.info("Verificación de préstamos vencidos completada", **result)
        
        return result
        
    except Exception as e:
        logger.error("Error verificando préstamos vencidos", error=str(e))
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def sync_search_indexes(self):
    """Sincronizar índices de búsqueda"""
    try:
        logger.info("Sincronizando índices de búsqueda")
        
        # Obtener estadísticas de índices
        import asyncio
        stats = asyncio.run(search_service.get_search_stats())
        
        # Reindexar si es necesario
        reindex_results = {}
        
        # Verificar si necesitamos reindexar
        for index_name, index_stats in stats.items():
            if _should_reindex(index_stats):
                reindex_results[index_name] = _reindex_data(index_name)
        
        result = {
            "success": True,
            "indexes_checked": len(stats),
            "indexes_reindexed": len(reindex_results),
            "reindex_results": reindex_results
        }
        
        logger.info("Sincronización de índices completada", **result)
        
        return result
        
    except Exception as e:
        logger.error("Error sincronizando índices", error=str(e))
        return {"success": False, "error": str(e)}

@celery_app.task(bind=True)
def system_health_check(self):
    """Verificar salud del sistema"""
    try:
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": _check_database_health(),
            "redis": _check_redis_health(),
            "meilisearch": _check_meilisearch_health(),
            "rabbitmq": _check_rabbitmq_health(),
            "disk_space": _check_disk_space(),
            "memory_usage": _get_memory_usage(),
            "cpu_usage": _get_cpu_usage()
        }
        
        # Determinar estado general
        overall_status = "healthy"
        for service, status in health_status.items():
            if isinstance(status, dict) and not status.get("healthy", True):
                overall_status = "unhealthy"
                break
        
        health_status["overall_status"] = overall_status
        
        # Enviar alerta si hay problemas
        if overall_status == "unhealthy":
            send_email.delay(
                recipient=settings.ADMIN_EMAIL,
                subject="Alerta de Salud del Sistema - FinancePro",
                template="system_health_alert",
                data=health_status
            )
        
        logger.info("Verificación de salud completada", 
                   overall_status=overall_status)
        
        return health_status
        
    except Exception as e:
        logger.error("Error en verificación de salud", error=str(e))
        return {"overall_status": "error", "error": str(e)}

# Funciones auxiliares (simuladas)
def _process_ocr(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simular procesamiento OCR"""
    return {
        "success": True,
        "extracted_text": "Texto extraído del documento...",
        "confidence": 0.95,
        "processing_time": 2.5
    }

def _validate_document(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simular validación de documento"""
    return {
        "success": True,
        "valid": True,
        "validation_errors": [],
        "document_type_detected": "cedula_identidad"
    }

def _extract_text(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simular extracción de texto"""
    return {
        "success": True,
        "extracted_text": "Contenido del documento...",
        "metadata": {"pages": 1, "language": "es"}
    }

def _scan_virus(document_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simular escaneo de virus"""
    return {
        "success": True,
        "clean": True,
        "threats_found": []
    }

def _generate_email_content(template: str, data: Dict[str, Any]) -> str:
    """Generar contenido de email desde template"""
    return f"Email generado desde template {template} con datos: {json.dumps(data)}"

def _send_email_via_provider(recipient: str, subject: str, content: str) -> Dict[str, Any]:
    """Simular envío de email"""
    return {"success": True, "message_id": f"msg_{datetime.utcnow().timestamp()}"}

def _send_sms_via_provider(phone: str, message: str) -> Dict[str, Any]:
    """Simular envío de SMS"""
    return {"success": True, "message_id": f"sms_{datetime.utcnow().timestamp()}"}

def _perform_database_backup(filename: str, backup_type: str) -> Dict[str, Any]:
    """Simular respaldo de base de datos"""
    return {"success": True, "filename": filename, "size_mb": 150.5}

def _backup_uploaded_files(timestamp: str) -> Dict[str, Any]:
    """Simular respaldo de archivos"""
    return {"success": True, "files_backed_up": 245}

def _cleanup_old_audit_logs(cleanup_date: datetime) -> Dict[str, Any]:
    """Simular limpieza de logs de auditoría"""
    return {"success": True, "count": 1250}

def _cleanup_expired_sessions() -> Dict[str, Any]:
    """Simular limpieza de sesiones"""
    return {"success": True, "count": 45}

def _cleanup_temp_files() -> Dict[str, Any]:
    """Simular limpieza de archivos temporales"""
    return {"success": True, "count": 12}

def _count_daily_loans() -> int:
    """Contar préstamos creados hoy"""
    return 15

def _count_daily_clients() -> int:
    """Contar clientes registrados hoy"""
    return 8

def _count_daily_documents() -> int:
    """Contar documentos procesados hoy"""
    return 42

def _count_daily_logins() -> int:
    """Contar intentos de login hoy"""
    return 156

def _get_system_uptime() -> float:
    """Obtener uptime del sistema en horas"""
    return 72.5

def _count_daily_searches() -> int:
    """Contar búsquedas realizadas hoy"""
    return 89

def _count_daily_notifications() -> int:
    """Contar notificaciones enviadas hoy"""
    return 23

def _save_daily_metrics(metrics: Dict[str, Any]):
    """Guardar métricas diarias"""
    pass

def _get_overdue_loans() -> List[Dict[str, Any]]:
    """Obtener préstamos vencidos"""
    return []

def _should_reindex(index_stats: Dict[str, Any]) -> bool:
    """Determinar si se debe reindexar"""
    return False

def _reindex_data(index_name: str) -> Dict[str, Any]:
    """Reindexar datos"""
    return {"success": True, "documents_reindexed": 100}

def _check_database_health() -> Dict[str, Any]:
    """Verificar salud de la base de datos"""
    return {"healthy": True, "response_time_ms": 15}

def _check_redis_health() -> Dict[str, Any]:
    """Verificar salud de Redis"""
    return {"healthy": True, "response_time_ms": 5}

def _check_meilisearch_health() -> Dict[str, Any]:
    """Verificar salud de Meilisearch"""
    return {"healthy": True, "response_time_ms": 25}

def _check_rabbitmq_health() -> Dict[str, Any]:
    """Verificar salud de RabbitMQ"""
    return {"healthy": True, "response_time_ms": 10}

def _check_disk_space() -> Dict[str, Any]:
    """Verificar espacio en disco"""
    return {"healthy": True, "free_space_gb": 45.2, "usage_percent": 65}

def _get_memory_usage() -> Dict[str, Any]:
    """Obtener uso de memoria"""
    return {"usage_percent": 72, "available_gb": 2.1}

def _get_cpu_usage() -> Dict[str, Any]:
    """Obtener uso de CPU"""
    return {"usage_percent": 35, "load_average": 1.2}

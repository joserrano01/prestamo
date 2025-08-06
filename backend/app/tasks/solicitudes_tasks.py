"""
Tareas de Celery para gestión automática de solicitudes y alertas
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

from celery import Celery
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.secure_models import ClienteSolicitud, SolicitudAlerta, Cliente
from app.services.notification_service import NotificationService
from app.services.rabbitmq_service import RabbitMQService
from app.services.solicitudes_service import SolicitudesService

logger = logging.getLogger(__name__)

# Configuración de Celery
celery_app = Celery('solicitudes')

@celery_app.task(name="monitorear_sla_solicitudes")
def monitorear_sla_solicitudes():
    """
    Tarea que se ejecuta cada hora para monitorear el SLA de solicitudes
    y crear alertas automáticas cuando sea necesario
    """
    try:
        db: Session = next(get_db())
        
        # Obtener solicitudes activas que no están completadas
        solicitudes_activas = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.estado.in_([
                'RECIBIDA', 'EN_REVISION', 'DOCUMENTOS_PENDIENTES', 
                'EN_EVALUACION', 'EN_COMITE'
            ])
        ).all()
        
        alertas_creadas = 0
        
        for solicitud in solicitudes_activas:
            # Verificar si requiere alerta
            if solicitud.requiere_alerta:
                # Verificar si ya se envió alerta reciente (últimas 4 horas)
                if solicitud.ultima_alerta:
                    horas_desde_alerta = (datetime.utcnow() - solicitud.ultima_alerta).total_seconds() / 3600
                    if horas_desde_alerta < 4:
                        continue
                
                # Determinar tipo de alerta basado en porcentaje SLA
                porcentaje_sla = solicitud.porcentaje_sla_consumido
                
                if porcentaje_sla >= 100:
                    tipo_alerta = 'SLA_VENCIDO'
                    nivel_urgencia = 'CRITICA'
                elif porcentaje_sla >= 90:
                    tipo_alerta = 'SLA_90'
                    nivel_urgencia = 'ALTA'
                else:
                    tipo_alerta = 'SLA_75'
                    nivel_urgencia = 'ALTA'
                
                # Crear alerta
                alerta = SolicitudAlerta(
                    solicitud_id=solicitud.id,
                    usuario_destinatario_id=solicitud.usuario_asignado_id,
                    tipo_alerta=tipo_alerta,
                    nivel_urgencia=nivel_urgencia,
                    titulo=f'SLA {int(porcentaje_sla)}% - Solicitud {solicitud.numero_solicitud}',
                    mensaje=f'La solicitud {solicitud.numero_solicitud} del cliente {solicitud.cliente.nombres} '
                           f'ha consumido el {int(porcentaje_sla)}% del SLA. '
                           f'Quedan {solicitud.horas_restantes_sla} horas para responder.',
                    fecha_vencimiento=datetime.utcnow() + timedelta(hours=24)
                )
                
                db.add(alerta)
                
                # Actualizar contador de alertas en solicitud
                solicitud.alertas_enviadas += 1
                solicitud.ultima_alerta = datetime.utcnow()
                
                alertas_creadas += 1
        
        db.commit()
        
        # Enviar evento a RabbitMQ
        rabbitmq = RabbitMQService()
        rabbitmq.publish_event('solicitudes', 'sla.monitoreado', {
            'solicitudes_revisadas': len(solicitudes_activas),
            'alertas_creadas': alertas_creadas,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Monitoreo SLA completado: {len(solicitudes_activas)} solicitudes revisadas, {alertas_creadas} alertas creadas")
        
        return {
            'status': 'success',
            'solicitudes_revisadas': len(solicitudes_activas),
            'alertas_creadas': alertas_creadas
        }
        
    except Exception as e:
        logger.error(f"Error en monitoreo SLA: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        db.close()


@celery_app.task(name="procesar_alertas_pendientes")
def procesar_alertas_pendientes():
    """
    Procesa y envía alertas pendientes
    """
    try:
        db: Session = next(get_db())
        notification_service = NotificationService()
        
        # Obtener alertas pendientes programadas para ahora o antes
        alertas_pendientes = db.query(SolicitudAlerta).filter(
            SolicitudAlerta.estado == 'PENDIENTE',
            SolicitudAlerta.fecha_programada <= datetime.utcnow()
        ).all()
        
        alertas_enviadas = 0
        alertas_fallidas = 0
        
        for alerta in alertas_pendientes:
            try:
                # Enviar notificaciones según configuración
                if alerta.enviar_email:
                    notification_service.send_email_alert(alerta)
                
                if alerta.enviar_sms:
                    notification_service.send_sms_alert(alerta)
                
                if alerta.enviar_push:
                    notification_service.send_push_alert(alerta)
                
                # Marcar como enviada
                alerta.marcar_como_enviada()
                alertas_enviadas += 1
                
            except Exception as e:
                logger.error(f"Error enviando alerta {alerta.id}: {str(e)}")
                alerta.incrementar_intentos(str(e))
                alertas_fallidas += 1
                
                # Si ha fallado 3 veces, marcar como vencida
                if alerta.intentos_envio >= 3:
                    alerta.estado = 'VENCIDA'
        
        db.commit()
        
        logger.info(f"Procesamiento de alertas completado: {alertas_enviadas} enviadas, {alertas_fallidas} fallidas")
        
        return {
            'status': 'success',
            'alertas_enviadas': alertas_enviadas,
            'alertas_fallidas': alertas_fallidas
        }
        
    except Exception as e:
        logger.error(f"Error procesando alertas: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        db.close()


@celery_app.task(name="verificar_solicitudes_vencidas")
def verificar_solicitudes_vencidas():
    """
    Verifica solicitudes vencidas y actualiza sus estados
    """
    try:
        db: Session = next(get_db())
        
        # Obtener solicitudes vencidas que no han sido marcadas como tal
        solicitudes_vencidas = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.fecha_vencimiento < datetime.utcnow(),
            ClienteSolicitud.estado != 'VENCIDA'
        ).all()
        
        solicitudes_actualizadas = 0
        
        for solicitud in solicitudes_vencidas:
            # Actualizar estado a vencida
            solicitud.estado = 'VENCIDA'
            solicitud.fecha_completada = datetime.utcnow()
            solicitud.actualizar_tiempo_procesamiento()
            
            # Crear alerta de solicitud vencida
            alerta = SolicitudAlerta(
                solicitud_id=solicitud.id,
                usuario_destinatario_id=solicitud.usuario_asignado_id,
                tipo_alerta='SOLICITUD_VENCIDA',
                nivel_urgencia='CRITICA',
                titulo=f'Solicitud Vencida - {solicitud.numero_solicitud}',
                mensaje=f'La solicitud {solicitud.numero_solicitud} ha vencido sin completarse.'
            )
            
            db.add(alerta)
            solicitudes_actualizadas += 1
        
        db.commit()
        
        logger.info(f"Verificación de vencimientos completada: {solicitudes_actualizadas} solicitudes vencidas")
        
        return {
            'status': 'success',
            'solicitudes_vencidas': solicitudes_actualizadas
        }
        
    except Exception as e:
        logger.error(f"Error verificando vencimientos: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        db.close()


@celery_app.task(name="generar_reporte_solicitudes_diario")
def generar_reporte_solicitudes_diario():
    """
    Genera reporte diario de métricas de solicitudes
    """
    try:
        db: Session = next(get_db())
        
        # Fecha de ayer
        ayer = datetime.utcnow() - timedelta(days=1)
        inicio_dia = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Métricas del día anterior
        solicitudes_creadas = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.fecha_solicitud.between(inicio_dia, fin_dia)
        ).count()
        
        solicitudes_completadas = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.fecha_completada.between(inicio_dia, fin_dia)
        ).count()
        
        solicitudes_vencidas = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.estado == 'VENCIDA',
            ClienteSolicitud.fecha_completada.between(inicio_dia, fin_dia)
        ).count()
        
        # Tiempo promedio de procesamiento
        solicitudes_con_tiempo = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.fecha_completada.between(inicio_dia, fin_dia),
            ClienteSolicitud.tiempo_procesamiento_horas.isnot(None)
        ).all()
        
        tiempo_promedio = 0
        if solicitudes_con_tiempo:
            tiempo_promedio = sum(s.tiempo_procesamiento_horas for s in solicitudes_con_tiempo) / len(solicitudes_con_tiempo)
        
        # Alertas enviadas
        alertas_enviadas = db.query(SolicitudAlerta).filter(
            SolicitudAlerta.fecha_enviada.between(inicio_dia, fin_dia)
        ).count()
        
        reporte = {
            'fecha': ayer.date().isoformat(),
            'solicitudes_creadas': solicitudes_creadas,
            'solicitudes_completadas': solicitudes_completadas,
            'solicitudes_vencidas': solicitudes_vencidas,
            'tiempo_promedio_procesamiento_horas': round(tiempo_promedio, 2),
            'alertas_enviadas': alertas_enviadas,
            'porcentaje_cumplimiento_sla': round(
                ((solicitudes_completadas - solicitudes_vencidas) / max(solicitudes_completadas, 1)) * 100, 2
            )
        }
        
        # Enviar reporte a RabbitMQ
        rabbitmq = RabbitMQService()
        rabbitmq.publish_event('reports', 'solicitudes.reporte_diario', reporte)
        
        logger.info(f"Reporte diario generado: {reporte}")
        
        return reporte
        
    except Exception as e:
        logger.error(f"Error generando reporte diario: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        db.close()


@celery_app.task(name="limpiar_alertas_antiguas")
def limpiar_alertas_antiguas(dias_antiguedad: int = 30):
    """
    Limpia alertas antiguas para mantener la base de datos optimizada
    """
    try:
        db: Session = next(get_db())
        
        fecha_limite = datetime.utcnow() - timedelta(days=dias_antiguedad)
        
        # Eliminar alertas antiguas que ya fueron atendidas o están vencidas
        alertas_eliminadas = db.query(SolicitudAlerta).filter(
            SolicitudAlerta.created_at < fecha_limite,
            SolicitudAlerta.estado.in_(['ATENDIDA', 'VENCIDA', 'IGNORADA'])
        ).delete()
        
        db.commit()
        
        logger.info(f"Limpieza de alertas completada: {alertas_eliminadas} alertas eliminadas")
        
        return {
            'status': 'success',
            'alertas_eliminadas': alertas_eliminadas
        }
        
    except Exception as e:
        logger.error(f"Error en limpieza de alertas: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        db.close()


@celery_app.task(name="notificar_seguimientos_programados")
def notificar_seguimientos_programados():
    """
    Notifica sobre seguimientos programados para hoy
    """
    try:
        db: Session = next(get_db())
        
        # Obtener solicitudes con seguimiento programado para hoy
        hoy = datetime.utcnow().date()
        solicitudes_seguimiento = db.query(ClienteSolicitud).filter(
            ClienteSolicitud.fecha_proximo_seguimiento == hoy,
            ClienteSolicitud.requiere_seguimiento == True,
            ~ClienteSolicitud.estado.in_(['COMPLETADA', 'DESEMBOLSADA', 'RECHAZADA', 'CANCELADA'])
        ).all()
        
        alertas_creadas = 0
        
        for solicitud in solicitudes_seguimiento:
            # Crear alerta de seguimiento
            alerta = SolicitudAlerta(
                solicitud_id=solicitud.id,
                usuario_destinatario_id=solicitud.usuario_asignado_id,
                tipo_alerta='SEGUIMIENTO_REQUERIDO',
                nivel_urgencia='MEDIA',
                titulo=f'Seguimiento Programado - {solicitud.numero_solicitud}',
                mensaje=f'Seguimiento programado para la solicitud {solicitud.numero_solicitud} '
                       f'del cliente {solicitud.cliente.nombres}.'
            )
            
            db.add(alerta)
            alertas_creadas += 1
        
        db.commit()
        
        logger.info(f"Notificaciones de seguimiento enviadas: {alertas_creadas}")
        
        return {
            'status': 'success',
            'seguimientos_notificados': alertas_creadas
        }
        
    except Exception as e:
        logger.error(f"Error notificando seguimientos: {str(e)}")
        return {'status': 'error', 'message': str(e)}
    finally:
        db.close()


# Configuración de tareas periódicas
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # Monitorear SLA cada hora
    'monitorear-sla-solicitudes': {
        'task': 'monitorear_sla_solicitudes',
        'schedule': crontab(minute=0),  # Cada hora en punto
    },
    
    # Procesar alertas cada 15 minutos
    'procesar-alertas-pendientes': {
        'task': 'procesar_alertas_pendientes',
        'schedule': crontab(minute='*/15'),  # Cada 15 minutos
    },
    
    # Verificar vencimientos cada 6 horas
    'verificar-solicitudes-vencidas': {
        'task': 'verificar_solicitudes_vencidas',
        'schedule': crontab(minute=0, hour='*/6'),  # Cada 6 horas
    },
    
    # Reporte diario a las 7:00 AM
    'generar-reporte-diario': {
        'task': 'generar_reporte_solicitudes_diario',
        'schedule': crontab(hour=7, minute=0),  # 7:00 AM todos los días
    },
    
    # Limpieza semanal los domingos a las 2:00 AM
    'limpiar-alertas-antiguas': {
        'task': 'limpiar_alertas_antiguas',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Domingo 2:00 AM
    },
    
    # Seguimientos programados a las 9:00 AM
    'notificar-seguimientos': {
        'task': 'notificar_seguimientos_programados',
        'schedule': crontab(hour=9, minute=0),  # 9:00 AM todos los días
    },
}

celery_app.conf.timezone = 'UTC'

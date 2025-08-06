"""
Tareas Celery para la gestión automática de la agenda de cobranza
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import logging

from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.core.database import SessionLocal
from app.models.agenda_models import AgendaCobranza, AlertaCobranza, EstadoActividad, ResultadoActividad
from app.models.secure_models import Cliente, Usuario, Prestamo
from app.services.agenda_cobranza_service import AgendaCobranzaService
from app.services.notification_service import NotificationService
from app.services.rabbitmq_service import RabbitMQService

logger = logging.getLogger(__name__)

# Importar la instancia de Celery
from app.core.celery_app import celery_app


@celery_app.task(bind=True, max_retries=3)
def procesar_alertas_cobranza_pendientes(self):
    """
    Procesa alertas de cobranza pendientes cada 15 minutos
    """
    try:
        db: Session = SessionLocal()
        service = AgendaCobranzaService(db)
        
        resultado = service.procesar_alertas_cobranza_pendientes()
        
        db.close()
        
        logger.info(f"Alertas de cobranza procesadas: {resultado}")
        
        # Publicar evento
        rabbitmq = RabbitMQService()
        rabbitmq.publish_event('cobranza', 'alertas.procesadas', {
            'timestamp': datetime.utcnow().isoformat(),
            'procesadas': resultado['procesadas'],
            'errores': resultado['errores']
        })
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error procesando alertas de cobranza: {str(e)}")
        
        # Reintentar la tarea
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 5 minutos (intento {self.request.retries + 1})")
            raise self.retry(countdown=300, exc=e)
        
        raise


@celery_app.task(bind=True, max_retries=3)
def verificar_actividades_vencidas(self):
    """
    Verifica y marca actividades vencidas cada hora
    """
    try:
        db: Session = SessionLocal()
        ahora = datetime.utcnow()
        
        # Buscar actividades vencidas que no han sido marcadas
        actividades_vencidas = db.query(AgendaCobranza).filter(
            AgendaCobranza.fecha_vencimiento < ahora,
            AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
        ).all()
        
        actualizadas = 0
        alertas_creadas = 0
        
        for actividad in actividades_vencidas:
            try:
                # Marcar como vencida
                actividad.estado = EstadoActividad.VENCIDA
                
                # Crear alerta de actividad vencida
                alerta = AlertaCobranza(
                    actividad_id=actividad.id,
                    usuario_destinatario_id=actividad.usuario_asignado_id,
                    tipo_alerta='ACTIVIDAD_VENCIDA',
                    nivel_urgencia='ALTA',
                    titulo=f'Actividad Vencida - {actividad.titulo}',
                    mensaje=f'La actividad de cobranza "{actividad.titulo}" '
                           f'programada para {actividad.fecha_programada} ha vencido sin completarse.',
                    fecha_programada=datetime.utcnow()
                )
                
                db.add(alerta)
                actualizadas += 1
                alertas_creadas += 1
                
                # Publicar evento individual
                rabbitmq = RabbitMQService()
                rabbitmq.publish_event('cobranza', 'actividad.vencida', {
                    'actividad_id': str(actividad.id),
                    'cliente_id': str(actividad.cliente_id),
                    'usuario_asignado_id': str(actividad.usuario_asignado_id),
                    'fecha_programada': actividad.fecha_programada.isoformat(),
                    'tipo_actividad': actividad.tipo_actividad.value
                })
                
            except Exception as e:
                logger.error(f"Error procesando actividad vencida {actividad.id}: {str(e)}")
        
        db.commit()
        db.close()
        
        logger.info(f"Actividades vencidas procesadas: {actualizadas}, alertas creadas: {alertas_creadas}")
        
        return {
            'actividades_actualizadas': actualizadas,
            'alertas_creadas': alertas_creadas
        }
        
    except Exception as e:
        logger.error(f"Error verificando actividades vencidas: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 10 minutos (intento {self.request.retries + 1})")
            raise self.retry(countdown=600, exc=e)
        
        raise


@celery_app.task(bind=True, max_retries=3)
def verificar_promesas_pago_vencidas(self):
    """
    Verifica promesas de pago vencidas diariamente
    """
    try:
        db: Session = SessionLocal()
        hoy = date.today()
        
        # Buscar promesas de pago vencidas
        promesas_vencidas = db.query(AgendaCobranza).filter(
            AgendaCobranza.resultado == ResultadoActividad.PROMESA_PAGO,
            AgendaCobranza._fecha_promesa_pago <= hoy,
            AgendaCobranza.requiere_seguimiento == False  # No procesadas aún
        ).all()
        
        procesadas = 0
        alertas_creadas = 0
        
        for actividad in promesas_vencidas:
            try:
                # Marcar como que requiere seguimiento
                actividad.requiere_seguimiento = True
                actividad.fecha_proximo_seguimiento = hoy
                
                # Crear alerta de promesa vencida
                alerta = AlertaCobranza(
                    actividad_id=actividad.id,
                    usuario_destinatario_id=actividad.usuario_asignado_id,
                    tipo_alerta='PROMESA_PAGO_VENCIDA',
                    nivel_urgencia='CRITICA',
                    titulo=f'Promesa de Pago Vencida - {actividad.cliente.nombres}',
                    mensaje=f'El cliente {actividad.cliente.nombres} {actividad.cliente.apellidos} '
                           f'no cumplió con la promesa de pago de ${actividad.monto_prometido} '
                           f'programada para {actividad.fecha_promesa_pago}.',
                    fecha_programada=datetime.utcnow()
                )
                
                db.add(alerta)
                procesadas += 1
                alertas_creadas += 1
                
                # Publicar evento
                rabbitmq = RabbitMQService()
                rabbitmq.publish_event('cobranza', 'promesa_pago.vencida', {
                    'actividad_id': str(actividad.id),
                    'cliente_id': str(actividad.cliente_id),
                    'monto_prometido': float(actividad.monto_prometido) if actividad.monto_prometido else None,
                    'fecha_promesa': actividad.fecha_promesa_pago.isoformat(),
                    'usuario_asignado_id': str(actividad.usuario_asignado_id)
                })
                
            except Exception as e:
                logger.error(f"Error procesando promesa vencida {actividad.id}: {str(e)}")
        
        db.commit()
        db.close()
        
        logger.info(f"Promesas de pago vencidas procesadas: {procesadas}, alertas creadas: {alertas_creadas}")
        
        return {
            'promesas_procesadas': procesadas,
            'alertas_creadas': alertas_creadas
        }
        
    except Exception as e:
        logger.error(f"Error verificando promesas de pago vencidas: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 30 minutos (intento {self.request.retries + 1})")
            raise self.retry(countdown=1800, exc=e)
        
        raise


@celery_app.task(bind=True, max_retries=3)
def generar_agenda_diaria(self):
    """
    Genera resumen de agenda diaria para cada usuario a las 8:00 AM
    """
    try:
        db: Session = SessionLocal()
        hoy = date.today()
        
        # Obtener usuarios con actividades programadas para hoy
        usuarios_con_actividades = db.query(Usuario).join(
            AgendaCobranza, Usuario.id == AgendaCobranza.usuario_asignado_id
        ).filter(
            AgendaCobranza.fecha_programada == hoy,
            AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
        ).distinct().all()
        
        notificaciones_enviadas = 0
        
        for usuario in usuarios_con_actividades:
            try:
                # Obtener actividades del día
                actividades_hoy = db.query(AgendaCobranza).filter(
                    AgendaCobranza.usuario_asignado_id == usuario.id,
                    AgendaCobranza.fecha_programada == hoy,
                    AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
                ).order_by(AgendaCobranza.hora_inicio.asc()).all()
                
                if actividades_hoy:
                    # Crear resumen
                    total_actividades = len(actividades_hoy)
                    alta_prioridad = len([a for a in actividades_hoy if a.prioridad.value in ['ALTA', 'CRITICA', 'URGENTE']])
                    
                    # Crear alerta de agenda diaria
                    alerta = AlertaCobranza(
                        actividad_id=actividades_hoy[0].id,  # Asociar a la primera actividad
                        usuario_destinatario_id=usuario.id,
                        tipo_alerta='AGENDA_DIARIA',
                        nivel_urgencia='MEDIA',
                        titulo=f'Agenda de Cobranza - {hoy.strftime("%d/%m/%Y")}',
                        mensaje=f'Tiene {total_actividades} actividades de cobranza programadas para hoy. '
                               f'{alta_prioridad} son de alta prioridad.',
                        fecha_programada=datetime.utcnow(),
                        enviar_email=True,
                        enviar_push=True
                    )
                    
                    db.add(alerta)
                    notificaciones_enviadas += 1
                    
            except Exception as e:
                logger.error(f"Error generando agenda diaria para usuario {usuario.id}: {str(e)}")
        
        db.commit()
        db.close()
        
        logger.info(f"Agendas diarias generadas: {notificaciones_enviadas}")
        
        return {
            'usuarios_notificados': notificaciones_enviadas
        }
        
    except Exception as e:
        logger.error(f"Error generando agendas diarias: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 15 minutos (intento {self.request.retries + 1})")
            raise self.retry(countdown=900, exc=e)
        
        raise


@celery_app.task(bind=True, max_retries=3)
def generar_reporte_efectividad_cobranza(self):
    """
    Genera reporte semanal de efectividad de cobranza los lunes a las 7:00 AM
    """
    try:
        db: Session = SessionLocal()
        
        # Calcular fechas de la semana anterior
        hoy = date.today()
        inicio_semana = hoy - timedelta(days=hoy.weekday() + 7)  # Lunes de la semana anterior
        fin_semana = inicio_semana + timedelta(days=6)  # Domingo de la semana anterior
        
        # Obtener actividades de la semana anterior
        actividades_semana = db.query(AgendaCobranza).filter(
            AgendaCobranza.fecha_programada.between(inicio_semana, fin_semana)
        ).all()
        
        if not actividades_semana:
            logger.info("No hay actividades para generar reporte de efectividad")
            db.close()
            return {'mensaje': 'No hay datos para reportar'}
        
        # Calcular métricas por usuario
        metricas_usuarios = {}
        
        for actividad in actividades_semana:
            usuario_id = str(actividad.usuario_asignado_id)
            
            if usuario_id not in metricas_usuarios:
                metricas_usuarios[usuario_id] = {
                    'usuario': actividad.usuario_asignado,
                    'total_actividades': 0,
                    'completadas': 0,
                    'exitosas': 0,
                    'promesas_pago': 0,
                    'sin_contacto': 0,
                    'efectividad': 0
                }
            
            metricas = metricas_usuarios[usuario_id]
            metricas['total_actividades'] += 1
            
            if actividad.estado == EstadoActividad.COMPLETADA:
                metricas['completadas'] += 1
                
                if actividad.resultado == ResultadoActividad.EXITOSA:
                    metricas['exitosas'] += 1
                elif actividad.resultado == ResultadoActividad.PROMESA_PAGO:
                    metricas['promesas_pago'] += 1
                elif actividad.resultado in [ResultadoActividad.CLIENTE_INUBICABLE, ResultadoActividad.SIN_EXITO]:
                    metricas['sin_contacto'] += 1
        
        # Calcular efectividad
        for usuario_id, metricas in metricas_usuarios.items():
            if metricas['completadas'] > 0:
                exitosas_total = metricas['exitosas'] + metricas['promesas_pago']
                metricas['efectividad'] = round((exitosas_total / metricas['completadas']) * 100, 2)
        
        # Crear alertas para supervisores con el reporte
        supervisores = db.query(Usuario).filter(
            Usuario.rol.in_(['SUPERVISOR', 'GERENTE', 'ADMIN'])
        ).all()
        
        alertas_creadas = 0
        
        for supervisor in supervisores:
            try:
                # Generar mensaje del reporte
                mensaje_reporte = f"Reporte de Efectividad de Cobranza\n"
                mensaje_reporte += f"Período: {inicio_semana.strftime('%d/%m/%Y')} - {fin_semana.strftime('%d/%m/%Y')}\n\n"
                
                for usuario_id, metricas in metricas_usuarios.items():
                    usuario = metricas['usuario']
                    mensaje_reporte += f"{usuario.nombres} {usuario.apellidos}:\n"
                    mensaje_reporte += f"  • Total actividades: {metricas['total_actividades']}\n"
                    mensaje_reporte += f"  • Completadas: {metricas['completadas']}\n"
                    mensaje_reporte += f"  • Exitosas: {metricas['exitosas']}\n"
                    mensaje_reporte += f"  • Promesas de pago: {metricas['promesas_pago']}\n"
                    mensaje_reporte += f"  • Efectividad: {metricas['efectividad']}%\n\n"
                
                alerta = AlertaCobranza(
                    actividad_id=actividades_semana[0].id,  # Asociar a la primera actividad
                    usuario_destinatario_id=supervisor.id,
                    tipo_alerta='REPORTE_EFECTIVIDAD',
                    nivel_urgencia='BAJA',
                    titulo=f'Reporte Semanal de Efectividad - {inicio_semana.strftime("%d/%m/%Y")}',
                    mensaje=mensaje_reporte,
                    fecha_programada=datetime.utcnow(),
                    enviar_email=True
                )
                
                db.add(alerta)
                alertas_creadas += 1
                
            except Exception as e:
                logger.error(f"Error creando reporte para supervisor {supervisor.id}: {str(e)}")
        
        db.commit()
        db.close()
        
        logger.info(f"Reportes de efectividad generados: {alertas_creadas}")
        
        # Publicar evento
        rabbitmq = RabbitMQService()
        rabbitmq.publish_event('cobranza', 'reporte.efectividad_generado', {
            'periodo_inicio': inicio_semana.isoformat(),
            'periodo_fin': fin_semana.isoformat(),
            'total_actividades': len(actividades_semana),
            'usuarios_evaluados': len(metricas_usuarios),
            'supervisores_notificados': alertas_creadas
        })
        
        return {
            'periodo': f"{inicio_semana} - {fin_semana}",
            'total_actividades': len(actividades_semana),
            'usuarios_evaluados': len(metricas_usuarios),
            'reportes_enviados': alertas_creadas
        }
        
    except Exception as e:
        logger.error(f"Error generando reporte de efectividad: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 1 hora (intento {self.request.retries + 1})")
            raise self.retry(countdown=3600, exc=e)
        
        raise


@celery_app.task(bind=True, max_retries=3)
def limpiar_alertas_cobranza_antiguas(self):
    """
    Limpia alertas de cobranza antiguas semanalmente (domingos a las 3:00 AM)
    """
    try:
        db: Session = SessionLocal()
        
        # Eliminar alertas leídas/atendidas de más de 30 días
        fecha_limite = datetime.utcnow() - timedelta(days=30)
        
        alertas_antiguas = db.query(AlertaCobranza).filter(
            AlertaCobranza.estado.in_(['LEIDA', 'ATENDIDA']),
            AlertaCobranza.created_at < fecha_limite
        )
        
        count_eliminadas = alertas_antiguas.count()
        alertas_antiguas.delete()
        
        # Eliminar alertas pendientes de más de 7 días (probablemente obsoletas)
        fecha_limite_pendientes = datetime.utcnow() - timedelta(days=7)
        
        alertas_obsoletas = db.query(AlertaCobranza).filter(
            AlertaCobranza.estado == 'PENDIENTE',
            AlertaCobranza.created_at < fecha_limite_pendientes
        )
        
        count_obsoletas = alertas_obsoletas.count()
        alertas_obsoletas.delete()
        
        db.commit()
        db.close()
        
        total_eliminadas = count_eliminadas + count_obsoletas
        
        logger.info(f"Alertas de cobranza limpiadas: {total_eliminadas} "
                   f"(antiguas: {count_eliminadas}, obsoletas: {count_obsoletas})")
        
        return {
            'alertas_antiguas_eliminadas': count_eliminadas,
            'alertas_obsoletas_eliminadas': count_obsoletas,
            'total_eliminadas': total_eliminadas
        }
        
    except Exception as e:
        logger.error(f"Error limpiando alertas de cobranza: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 2 horas (intento {self.request.retries + 1})")
            raise self.retry(countdown=7200, exc=e)
        
        raise


@celery_app.task(bind=True, max_retries=3)
def crear_actividades_cobranza_automaticas(self):
    """
    Crea actividades de cobranza automáticas para préstamos en mora
    Ejecuta diariamente a las 6:00 AM
    """
    try:
        db: Session = SessionLocal()
        hoy = date.today()
        
        # Buscar préstamos en mora sin actividades de cobranza recientes
        prestamos_mora = db.query(Prestamo).filter(
            Prestamo.estado == 'MORA',
            Prestamo.dias_mora > 0
        ).all()
        
        actividades_creadas = 0
        
        for prestamo in prestamos_mora:
            try:
                # Verificar si ya tiene actividades de cobranza recientes (últimos 7 días)
                fecha_limite = hoy - timedelta(days=7)
                
                actividad_reciente = db.query(AgendaCobranza).filter(
                    AgendaCobranza.prestamo_id == prestamo.id,
                    AgendaCobranza.fecha_programada >= fecha_limite
                ).first()
                
                if actividad_reciente:
                    continue  # Ya tiene actividad reciente
                
                # Determinar tipo de actividad según días de mora
                if prestamo.dias_mora <= 15:
                    tipo_actividad = 'LLAMADA_TELEFONICA'
                    prioridad = 'NORMAL'
                elif prestamo.dias_mora <= 30:
                    tipo_actividad = 'VISITA_DOMICILIO'
                    prioridad = 'ALTA'
                else:
                    tipo_actividad = 'ESCALAMIENTO_LEGAL'
                    prioridad = 'CRITICA'
                
                # Buscar oficial de crédito asignado o supervisor
                usuario_asignado = prestamo.usuario or db.query(Usuario).filter(
                    Usuario.rol == 'OFICIAL_CREDITO',
                    Usuario.sucursal_id == prestamo.sucursal_id
                ).first()
                
                if not usuario_asignado:
                    continue  # No hay usuario para asignar
                
                # Crear actividad automática
                service = AgendaCobranzaService(db)
                
                actividad = service.crear_actividad_cobranza(
                    cliente_id=str(prestamo.cliente_id),
                    tipo_actividad=getattr(TipoActividad, tipo_actividad),
                    titulo=f'Cobranza Automática - Mora {prestamo.dias_mora} días',
                    descripcion=f'Actividad automática de cobranza para préstamo en mora. '
                               f'Días de mora: {prestamo.dias_mora}. '
                               f'Saldo pendiente: ${prestamo.saldo_pendiente}.',
                    fecha_programada=hoy + timedelta(days=1),  # Programar para mañana
                    usuario_asignado_id=str(usuario_asignado.id),
                    prestamo_id=str(prestamo.id),
                    sucursal_id=str(prestamo.sucursal_id),
                    prioridad=getattr(PrioridadActividad, prioridad),
                    objetivo=f'Gestionar cobro de préstamo en mora por ${prestamo.saldo_pendiente}',
                    monto_gestionado=float(prestamo.saldo_pendiente) if prestamo.saldo_pendiente else None
                )
                
                actividades_creadas += 1
                
            except Exception as e:
                logger.error(f"Error creando actividad automática para préstamo {prestamo.id}: {str(e)}")
        
        db.close()
        
        logger.info(f"Actividades de cobranza automáticas creadas: {actividades_creadas}")
        
        return {
            'actividades_creadas': actividades_creadas,
            'prestamos_evaluados': len(prestamos_mora)
        }
        
    except Exception as e:
        logger.error(f"Error creando actividades automáticas: {str(e)}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Reintentando tarea en 1 hora (intento {self.request.retries + 1})")
            raise self.retry(countdown=3600, exc=e)
        
        raise

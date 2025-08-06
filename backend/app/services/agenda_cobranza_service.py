"""
Servicio para gestión de agenda de cobranza integrada con alertas
"""
from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
import uuid
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.models.agenda_models import (
    AgendaCobranza, AlertaCobranza, TipoActividad, EstadoActividad, 
    PrioridadActividad, ResultadoActividad
)
from app.models.secure_models import Cliente, Usuario, Prestamo, SolicitudAlerta
from app.services.notification_service import NotificationService
from app.services.rabbitmq_service import RabbitMQService

logger = logging.getLogger(__name__)


class AgendaCobranzaService:
    """Servicio para gestión integral de agenda de cobranza"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
        self.rabbitmq_service = RabbitMQService()
    
    def crear_actividad_cobranza(
        self,
        cliente_id: str,
        tipo_actividad: TipoActividad,
        titulo: str,
        descripcion: str,
        fecha_programada: date,
        usuario_asignado_id: str,
        prestamo_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        prioridad: PrioridadActividad = PrioridadActividad.NORMAL,
        hora_inicio: Optional[time] = None,
        duracion_estimada_minutos: Optional[int] = None,
        objetivo: Optional[str] = None,
        direccion_visita: Optional[str] = None,
        telefono_contacto: Optional[str] = None,
        persona_contacto: Optional[str] = None,
        monto_gestionado: Optional[float] = None,
        generar_alerta_previa: bool = True,
        minutos_alerta_previa: int = 60,
        **kwargs
    ) -> AgendaCobranza:
        """
        Crea una nueva actividad de cobranza
        """
        try:
            # Verificar que el cliente existe
            cliente = self.db.query(Cliente).filter(Cliente.id == cliente_id).first()
            if not cliente:
                raise ValueError(f"Cliente {cliente_id} no encontrado")
            
            # Verificar que el usuario existe
            usuario = self.db.query(Usuario).filter(Usuario.id == usuario_asignado_id).first()
            if not usuario:
                raise ValueError(f"Usuario {usuario_asignado_id} no encontrado")
            
            # Calcular fecha de vencimiento (24 horas después de la fecha programada)
            fecha_vencimiento = datetime.combine(fecha_programada, time(23, 59, 59))
            
            # Crear actividad
            actividad = AgendaCobranza(
                cliente_id=cliente_id,
                prestamo_id=prestamo_id,
                usuario_asignado_id=usuario_asignado_id,
                sucursal_id=sucursal_id,
                tipo_actividad=tipo_actividad,
                prioridad=prioridad,
                fecha_programada=fecha_programada,
                hora_inicio=hora_inicio,
                duracion_estimada_minutos=duracion_estimada_minutos,
                fecha_vencimiento=fecha_vencimiento,
                titulo=titulo,
                descripcion=descripcion,
                objetivo=objetivo,
                direccion_visita=direccion_visita,
                telefono_contacto=telefono_contacto,
                persona_contacto=persona_contacto,
                monto_gestionado=monto_gestionado,
                generar_alerta_previa=generar_alerta_previa,
                minutos_alerta_previa=minutos_alerta_previa,
                **kwargs
            )
            
            self.db.add(actividad)
            self.db.flush()  # Para obtener el ID
            
            # Crear alerta previa si está configurada
            if generar_alerta_previa:
                self._crear_alerta_previa(actividad)
            
            # Enviar evento a RabbitMQ
            self.rabbitmq_service.publish_event('cobranza', 'actividad.creada', {
                'actividad_id': str(actividad.id),
                'cliente_id': str(cliente_id),
                'tipo_actividad': tipo_actividad.value,
                'fecha_programada': fecha_programada.isoformat(),
                'usuario_asignado_id': str(usuario_asignado_id),
                'prioridad': prioridad.value
            })
            
            self.db.commit()
            
            logger.info(f"Actividad de cobranza creada: {actividad.id} para cliente {cliente_id}")
            return actividad
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando actividad de cobranza: {str(e)}")
            raise
    
    def actualizar_estado_actividad(
        self,
        actividad_id: str,
        nuevo_estado: EstadoActividad,
        resultado: Optional[ResultadoActividad] = None,
        resultado_detalle: Optional[str] = None,
        proximos_pasos: Optional[str] = None,
        monto_prometido: Optional[float] = None,
        fecha_promesa_pago: Optional[date] = None,
        usuario_id: Optional[str] = None
    ) -> AgendaCobranza:
        """
        Actualiza el estado de una actividad de cobranza
        """
        try:
            actividad = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.id == actividad_id
            ).first()
            
            if not actividad:
                raise ValueError(f"Actividad {actividad_id} no encontrada")
            
            estado_anterior = actividad.estado
            
            # Actualizar estado según el nuevo estado
            if nuevo_estado == EstadoActividad.EN_PROCESO:
                actividad.marcar_como_iniciada()
            elif nuevo_estado == EstadoActividad.COMPLETADA:
                if resultado:
                    actividad.marcar_como_completada(resultado, resultado_detalle)
                else:
                    actividad.estado = nuevo_estado
                    actividad.fecha_fin_real = datetime.utcnow()
            else:
                actividad.estado = nuevo_estado
            
            # Actualizar campos adicionales
            if resultado_detalle:
                actividad.resultado_detalle = resultado_detalle
            
            if proximos_pasos:
                actividad.proximos_pasos = proximos_pasos
            
            if monto_prometido:
                actividad.monto_prometido = monto_prometido
            
            if fecha_promesa_pago:
                actividad.fecha_promesa_pago = fecha_promesa_pago
            
            # Crear alerta de seguimiento si es necesario
            if (resultado == ResultadoActividad.PROMESA_PAGO and 
                fecha_promesa_pago):
                self._crear_alerta_seguimiento_promesa(actividad)
            
            # Enviar evento a RabbitMQ
            self.rabbitmq_service.publish_event('cobranza', 'actividad.actualizada', {
                'actividad_id': str(actividad.id),
                'estado_anterior': estado_anterior.value,
                'estado_nuevo': nuevo_estado.value,
                'resultado': resultado.value if resultado else None,
                'cliente_id': str(actividad.cliente_id)
            })
            
            self.db.commit()
            
            logger.info(f"Actividad {actividad_id} actualizada: {estado_anterior.value} → {nuevo_estado.value}")
            return actividad
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando actividad: {str(e)}")
            raise
    
    def reprogramar_actividad(
        self,
        actividad_id: str,
        nueva_fecha: date,
        nueva_hora: Optional[time] = None,
        motivo: Optional[str] = None,
        usuario_id: Optional[str] = None
    ) -> AgendaCobranza:
        """
        Reprograma una actividad de cobranza
        """
        try:
            actividad = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.id == actividad_id
            ).first()
            
            if not actividad:
                raise ValueError(f"Actividad {actividad_id} no encontrada")
            
            fecha_anterior = actividad.fecha_programada
            actividad.reprogramar(nueva_fecha, nueva_hora)
            
            if motivo:
                observaciones_actuales = actividad.observaciones or ""
                actividad.observaciones = f"{observaciones_actuales}\nReprogramada: {motivo}".strip()
            
            # Crear nueva alerta previa si está configurada
            if actividad.generar_alerta_previa:
                self._crear_alerta_previa(actividad)
            
            # Enviar evento a RabbitMQ
            self.rabbitmq_service.publish_event('cobranza', 'actividad.reprogramada', {
                'actividad_id': str(actividad.id),
                'fecha_anterior': fecha_anterior.isoformat(),
                'fecha_nueva': nueva_fecha.isoformat(),
                'motivo': motivo,
                'cliente_id': str(actividad.cliente_id)
            })
            
            self.db.commit()
            
            logger.info(f"Actividad {actividad_id} reprogramada de {fecha_anterior} a {nueva_fecha}")
            return actividad
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error reprogramando actividad: {str(e)}")
            raise
    
    def obtener_agenda_usuario(
        self,
        usuario_id: str,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        solo_pendientes: bool = False
    ) -> List[AgendaCobranza]:
        """
        Obtiene la agenda de un usuario específico
        """
        try:
            query = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.usuario_asignado_id == usuario_id
            )
            
            # Filtros de fecha
            if fecha_desde:
                query = query.filter(AgendaCobranza.fecha_programada >= fecha_desde)
            
            if fecha_hasta:
                query = query.filter(AgendaCobranza.fecha_programada <= fecha_hasta)
            
            # Solo pendientes
            if solo_pendientes:
                query = query.filter(
                    AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
                )
            
            return query.order_by(
                AgendaCobranza.fecha_programada.asc(),
                AgendaCobranza.hora_inicio.asc()
            ).all()
            
        except Exception as e:
            logger.error(f"Error obteniendo agenda de usuario: {str(e)}")
            raise
    
    def obtener_agenda_cliente(
        self,
        cliente_id: str,
        incluir_completadas: bool = False
    ) -> List[AgendaCobranza]:
        """
        Obtiene todas las actividades de cobranza de un cliente
        """
        try:
            query = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.cliente_id == cliente_id
            )
            
            if not incluir_completadas:
                query = query.filter(
                    AgendaCobranza.estado != EstadoActividad.COMPLETADA
                )
            
            return query.order_by(
                desc(AgendaCobranza.fecha_programada)
            ).all()
            
        except Exception as e:
            logger.error(f"Error obteniendo agenda de cliente: {str(e)}")
            raise
    
    def obtener_actividades_hoy(
        self,
        usuario_id: Optional[str] = None,
        sucursal_id: Optional[str] = None
    ) -> List[AgendaCobranza]:
        """
        Obtiene actividades programadas para hoy
        """
        try:
            hoy = date.today()
            
            query = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.fecha_programada == hoy,
                AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
            )
            
            if usuario_id:
                query = query.filter(AgendaCobranza.usuario_asignado_id == usuario_id)
            
            if sucursal_id:
                query = query.filter(AgendaCobranza.sucursal_id == sucursal_id)
            
            return query.order_by(
                AgendaCobranza.prioridad.desc(),
                AgendaCobranza.hora_inicio.asc()
            ).all()
            
        except Exception as e:
            logger.error(f"Error obteniendo actividades de hoy: {str(e)}")
            raise
    
    def obtener_actividades_vencidas(
        self,
        usuario_id: Optional[str] = None,
        sucursal_id: Optional[str] = None
    ) -> List[AgendaCobranza]:
        """
        Obtiene actividades vencidas
        """
        try:
            ahora = datetime.utcnow()
            
            query = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.fecha_vencimiento < ahora,
                AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
            )
            
            if usuario_id:
                query = query.filter(AgendaCobranza.usuario_asignado_id == usuario_id)
            
            if sucursal_id:
                query = query.filter(AgendaCobranza.sucursal_id == sucursal_id)
            
            return query.order_by(
                AgendaCobranza.fecha_vencimiento.asc()
            ).all()
            
        except Exception as e:
            logger.error(f"Error obteniendo actividades vencidas: {str(e)}")
            raise
    
    def obtener_promesas_pago_vencidas(
        self,
        usuario_id: Optional[str] = None
    ) -> List[AgendaCobranza]:
        """
        Obtiene promesas de pago vencidas
        """
        try:
            hoy = date.today()
            
            query = self.db.query(AgendaCobranza).filter(
                AgendaCobranza.resultado == ResultadoActividad.PROMESA_PAGO,
                AgendaCobranza._fecha_promesa_pago <= hoy
            )
            
            if usuario_id:
                query = query.filter(AgendaCobranza.usuario_asignado_id == usuario_id)
            
            return query.order_by(
                AgendaCobranza._fecha_promesa_pago.asc()
            ).all()
            
        except Exception as e:
            logger.error(f"Error obteniendo promesas de pago vencidas: {str(e)}")
            raise
    
    def obtener_dashboard_cobranza(
        self,
        usuario_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene datos para dashboard de cobranza
        """
        try:
            query = self.db.query(AgendaCobranza)
            
            # Aplicar filtros
            if usuario_id:
                query = query.filter(AgendaCobranza.usuario_asignado_id == usuario_id)
            
            if sucursal_id:
                query = query.filter(AgendaCobranza.sucursal_id == sucursal_id)
            
            if fecha_desde:
                query = query.filter(AgendaCobranza.fecha_programada >= fecha_desde)
            
            if fecha_hasta:
                query = query.filter(AgendaCobranza.fecha_programada <= fecha_hasta)
            
            actividades = query.all()
            
            # Calcular métricas
            total_actividades = len(actividades)
            hoy = date.today()
            
            actividades_hoy = len([a for a in actividades if a.fecha_programada == hoy])
            actividades_pendientes = len([a for a in actividades if a.estado in [EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO]])
            actividades_vencidas = len([a for a in actividades if a.esta_vencida])
            actividades_completadas = len([a for a in actividades if a.estado == EstadoActividad.COMPLETADA])
            
            # Efectividad
            if actividades_completadas > 0:
                exitosas = len([
                    a for a in actividades 
                    if a.estado == EstadoActividad.COMPLETADA and 
                    a.resultado in [ResultadoActividad.EXITOSA, ResultadoActividad.PROMESA_PAGO, ResultadoActividad.ACUERDO_ALCANZADO]
                ])
                efectividad = round((exitosas / actividades_completadas) * 100, 2)
            else:
                efectividad = 0
            
            # Distribución por tipo
            tipos = {}
            for actividad in actividades:
                tipo = actividad.tipo_actividad.value
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Distribución por estado
            estados = {}
            for actividad in actividades:
                estado = actividad.estado.value
                estados[estado] = estados.get(estado, 0) + 1
            
            # Promesas de pago vencidas
            promesas_vencidas = len([
                a for a in actividades 
                if (a.resultado == ResultadoActividad.PROMESA_PAGO and 
                    a.fecha_promesa_pago and a.fecha_promesa_pago <= hoy)
            ])
            
            return {
                'resumen': {
                    'total_actividades': total_actividades,
                    'actividades_hoy': actividades_hoy,
                    'actividades_pendientes': actividades_pendientes,
                    'actividades_vencidas': actividades_vencidas,
                    'actividades_completadas': actividades_completadas,
                    'efectividad_porcentaje': efectividad,
                    'promesas_pago_vencidas': promesas_vencidas
                },
                'distribucion_tipos': tipos,
                'distribucion_estados': estados,
                'actividades_proximas': [
                    {
                        'id': str(a.id),
                        'cliente_nombre': f"{a.cliente.nombres} {a.cliente.apellidos}",
                        'tipo_actividad': a.nombre_tipo_legible,
                        'fecha_programada': a.fecha_programada.isoformat(),
                        'hora_inicio': a.hora_inicio.isoformat() if a.hora_inicio else None,
                        'prioridad': a.prioridad.value
                    }
                    for a in sorted([a for a in actividades if a.fecha_programada >= hoy and a.estado == EstadoActividad.PROGRAMADA], 
                                  key=lambda x: x.fecha_programada)[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard de cobranza: {str(e)}")
            raise
    
    def _crear_alerta_previa(self, actividad: AgendaCobranza):
        """
        Crea alerta previa para una actividad
        """
        try:
            # Calcular fecha de alerta
            if actividad.hora_inicio:
                fecha_hora_actividad = datetime.combine(actividad.fecha_programada, actividad.hora_inicio)
            else:
                fecha_hora_actividad = datetime.combine(actividad.fecha_programada, time(9, 0))  # 9:00 AM por defecto
            
            fecha_alerta = fecha_hora_actividad - timedelta(minutes=actividad.minutos_alerta_previa)
            
            # Solo crear alerta si es futura
            if fecha_alerta > datetime.utcnow():
                alerta = AlertaCobranza(
                    actividad_id=actividad.id,
                    usuario_destinatario_id=actividad.usuario_asignado_id,
                    tipo_alerta='ACTIVIDAD_PROGRAMADA',
                    nivel_urgencia='MEDIA',
                    titulo=f'Actividad Programada - {actividad.titulo}',
                    mensaje=f'Tiene una actividad de cobranza programada: {actividad.nombre_tipo_legible} '
                           f'con el cliente {actividad.cliente.nombres} {actividad.cliente.apellidos}.',
                    fecha_programada=fecha_alerta
                )
                
                self.db.add(alerta)
                
        except Exception as e:
            logger.error(f"Error creando alerta previa: {str(e)}")
    
    def _crear_alerta_seguimiento_promesa(self, actividad: AgendaCobranza):
        """
        Crea alerta de seguimiento para promesa de pago
        """
        try:
            if not actividad.fecha_promesa_pago:
                return
            
            fecha_alerta = datetime.combine(actividad.fecha_promesa_pago, time(9, 0))
            
            alerta = AlertaCobranza(
                actividad_id=actividad.id,
                usuario_destinatario_id=actividad.usuario_asignado_id,
                tipo_alerta='PROMESA_PAGO_VENCIMIENTO',
                nivel_urgencia='ALTA',
                titulo=f'Promesa de Pago - {actividad.cliente.nombres}',
                mensaje=f'El cliente {actividad.cliente.nombres} {actividad.cliente.apellidos} '
                       f'prometió pagar ${actividad.monto_prometido} hoy.',
                fecha_programada=fecha_alerta
            )
            
            self.db.add(alerta)
            
        except Exception as e:
            logger.error(f"Error creando alerta de seguimiento: {str(e)}")
    
    def procesar_alertas_cobranza_pendientes(self):
        """
        Procesa alertas de cobranza pendientes
        """
        try:
            ahora = datetime.utcnow()
            
            alertas_pendientes = self.db.query(AlertaCobranza).filter(
                AlertaCobranza.estado == 'PENDIENTE',
                AlertaCobranza.fecha_programada <= ahora
            ).all()
            
            procesadas = 0
            errores = 0
            
            for alerta in alertas_pendientes:
                try:
                    # Enviar notificación
                    resultado = self.notification_service.enviar_alerta(alerta)
                    
                    if any(r['enviado'] for r in resultado.values()):
                        alerta.marcar_como_enviada()
                        procesadas += 1
                    else:
                        errores += 1
                        
                except Exception as e:
                    logger.error(f"Error procesando alerta {alerta.id}: {str(e)}")
                    errores += 1
            
            self.db.commit()
            
            logger.info(f"Alertas de cobranza procesadas: {procesadas}, errores: {errores}")
            return {'procesadas': procesadas, 'errores': errores}
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error procesando alertas de cobranza: {str(e)}")
            raise

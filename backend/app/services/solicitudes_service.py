"""
Servicio para gestión de solicitudes y alertas automáticas
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.secure_models import (
    ClienteSolicitud, SolicitudAlerta, Cliente, Usuario, 
    ClienteHistorial, Documento
)
from app.services.notification_service import NotificationService
from app.services.rabbitmq_service import RabbitMQService

logger = logging.getLogger(__name__)


class SolicitudesService:
    """Servicio para gestión integral de solicitudes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
        self.rabbitmq_service = RabbitMQService()
    
    def crear_solicitud(
        self,
        cliente_id: str,
        tipo_solicitud: str,
        asunto: str,
        descripcion: str,
        canal: str,
        usuario_asignado_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        prioridad: str = 'NORMAL',
        sla_horas: int = 24,
        **kwargs
    ) -> ClienteSolicitud:
        """
        Crea una nueva solicitud con número único y configuración automática
        """
        try:
            # Generar número único de solicitud
            numero_solicitud = self._generar_numero_solicitud()
            
            # Crear solicitud
            solicitud = ClienteSolicitud(
                numero_solicitud=numero_solicitud,
                cliente_id=cliente_id,
                usuario_asignado_id=usuario_asignado_id,
                sucursal_id=sucursal_id,
                tipo_solicitud=tipo_solicitud,
                prioridad=prioridad,
                canal=canal,
                asunto=asunto,
                descripcion=descripcion,
                sla_horas=sla_horas,
                fecha_limite_respuesta=datetime.utcnow() + timedelta(hours=sla_horas),
                **kwargs
            )
            
            self.db.add(solicitud)
            self.db.flush()  # Para obtener el ID
            
            # Crear entrada en historial
            self._crear_evento_historial(
                solicitud.id,
                'SOLICITUD_CREADA',
                f'Solicitud {numero_solicitud} creada',
                f'Nueva solicitud de tipo {solicitud.nombre_tipo_legible} creada vía {canal}'
            )
            
            # Enviar evento a RabbitMQ
            self.rabbitmq_service.publish_event('solicitudes', 'solicitud.creada', {
                'solicitud_id': str(solicitud.id),
                'numero_solicitud': numero_solicitud,
                'cliente_id': str(cliente_id),
                'tipo_solicitud': tipo_solicitud,
                'prioridad': prioridad,
                'canal': canal
            })
            
            self.db.commit()
            
            logger.info(f"Solicitud {numero_solicitud} creada exitosamente")
            return solicitud
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando solicitud: {str(e)}")
            raise
    
    def actualizar_estado_solicitud(
        self,
        solicitud_id: str,
        nuevo_estado: str,
        observaciones: Optional[str] = None,
        usuario_id: Optional[str] = None
    ) -> ClienteSolicitud:
        """
        Actualiza el estado de una solicitud y registra el cambio
        """
        try:
            solicitud = self.db.query(ClienteSolicitud).filter(
                ClienteSolicitud.id == solicitud_id
            ).first()
            
            if not solicitud:
                raise ValueError(f"Solicitud {solicitud_id} no encontrada")
            
            estado_anterior = solicitud.estado
            solicitud.estado = nuevo_estado
            
            # Actualizar fechas según el estado
            if nuevo_estado in ['APROBADA', 'RECHAZADA', 'CANCELADA']:
                solicitud.fecha_respuesta = datetime.utcnow()
                solicitud.actualizar_tiempo_respuesta()
            
            if nuevo_estado in ['COMPLETADA', 'DESEMBOLSADA', 'RECHAZADA', 'CANCELADA', 'VENCIDA']:
                solicitud.fecha_completada = datetime.utcnow()
                solicitud.actualizar_tiempo_procesamiento()
            
            if observaciones:
                solicitud.observaciones = observaciones
            
            # Crear evento en historial
            self._crear_evento_historial(
                solicitud.id,
                'CAMBIO_ESTADO',
                f'Estado cambiado de {estado_anterior} a {nuevo_estado}',
                observaciones or f'Estado actualizado a {solicitud.nombre_estado_legible}',
                usuario_id
            )
            
            # Crear alerta si es necesario
            if nuevo_estado in ['APROBADA', 'RECHAZADA']:
                self._crear_alerta_respuesta(solicitud, nuevo_estado)
            
            # Enviar evento a RabbitMQ
            self.rabbitmq_service.publish_event('solicitudes', 'solicitud.actualizada', {
                'solicitud_id': str(solicitud.id),
                'numero_solicitud': solicitud.numero_solicitud,
                'estado_anterior': estado_anterior,
                'estado_nuevo': nuevo_estado,
                'cliente_id': str(solicitud.cliente_id)
            })
            
            self.db.commit()
            
            logger.info(f"Solicitud {solicitud.numero_solicitud} actualizada: {estado_anterior} → {nuevo_estado}")
            return solicitud
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando solicitud: {str(e)}")
            raise
    
    def asignar_solicitud(
        self,
        solicitud_id: str,
        usuario_asignado_id: str,
        usuario_asignador_id: Optional[str] = None
    ) -> ClienteSolicitud:
        """
        Asigna una solicitud a un usuario específico
        """
        try:
            solicitud = self.db.query(ClienteSolicitud).filter(
                ClienteSolicitud.id == solicitud_id
            ).first()
            
            if not solicitud:
                raise ValueError(f"Solicitud {solicitud_id} no encontrada")
            
            usuario_anterior = solicitud.usuario_asignado_id
            solicitud.usuario_asignado_id = usuario_asignado_id
            
            # Crear evento en historial
            usuario_asignado = self.db.query(Usuario).filter(
                Usuario.id == usuario_asignado_id
            ).first()
            
            self._crear_evento_historial(
                solicitud.id,
                'SOLICITUD_ASIGNADA',
                f'Solicitud asignada a {usuario_asignado.nombre_completo}',
                f'Solicitud reasignada de usuario anterior',
                usuario_asignador_id
            )
            
            # Crear alerta para el nuevo usuario asignado
            alerta = SolicitudAlerta(
                solicitud_id=solicitud.id,
                usuario_destinatario_id=usuario_asignado_id,
                tipo_alerta='APROBACION_PENDIENTE',
                nivel_urgencia='MEDIA',
                titulo=f'Solicitud Asignada - {solicitud.numero_solicitud}',
                mensaje=f'Se le ha asignado la solicitud {solicitud.numero_solicitud} '
                       f'del cliente {solicitud.cliente.nombres}.'
            )
            
            self.db.add(alerta)
            
            # Enviar evento a RabbitMQ
            self.rabbitmq_service.publish_event('solicitudes', 'solicitud.asignada', {
                'solicitud_id': str(solicitud.id),
                'numero_solicitud': solicitud.numero_solicitud,
                'usuario_anterior': str(usuario_anterior) if usuario_anterior else None,
                'usuario_nuevo': str(usuario_asignado_id),
                'cliente_id': str(solicitud.cliente_id)
            })
            
            self.db.commit()
            
            logger.info(f"Solicitud {solicitud.numero_solicitud} asignada a usuario {usuario_asignado_id}")
            return solicitud
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error asignando solicitud: {str(e)}")
            raise
    
    def obtener_solicitudes_dashboard(
        self,
        usuario_id: Optional[str] = None,
        sucursal_id: Optional[str] = None,
        filtros: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Obtiene datos para dashboard de solicitudes
        """
        try:
            query = self.db.query(ClienteSolicitud)
            
            # Aplicar filtros
            if usuario_id:
                query = query.filter(ClienteSolicitud.usuario_asignado_id == usuario_id)
            
            if sucursal_id:
                query = query.filter(ClienteSolicitud.sucursal_id == sucursal_id)
            
            if filtros:
                if filtros.get('fecha_desde'):
                    query = query.filter(ClienteSolicitud.fecha_solicitud >= filtros['fecha_desde'])
                
                if filtros.get('fecha_hasta'):
                    query = query.filter(ClienteSolicitud.fecha_solicitud <= filtros['fecha_hasta'])
                
                if filtros.get('tipo_solicitud'):
                    query = query.filter(ClienteSolicitud.tipo_solicitud == filtros['tipo_solicitud'])
                
                if filtros.get('estado'):
                    query = query.filter(ClienteSolicitud.estado == filtros['estado'])
            
            solicitudes = query.all()
            
            # Calcular métricas
            total_solicitudes = len(solicitudes)
            activas = len([s for s in solicitudes if not s.esta_completada])
            vencidas = len([s for s in solicitudes if s.esta_vencida])
            fuera_sla = len([s for s in solicitudes if not s.esta_en_sla and not s.esta_completada])
            requieren_alerta = len([s for s in solicitudes if s.requiere_alerta])
            
            # Distribución por estado
            estados = {}
            for solicitud in solicitudes:
                estado = solicitud.estado
                estados[estado] = estados.get(estado, 0) + 1
            
            # Distribución por tipo
            tipos = {}
            for solicitud in solicitudes:
                tipo = solicitud.tipo_solicitud
                tipos[tipo] = tipos.get(tipo, 0) + 1
            
            # Tiempo promedio de procesamiento
            completadas = [s for s in solicitudes if s.tiempo_procesamiento_horas]
            tiempo_promedio = 0
            if completadas:
                tiempo_promedio = sum(s.tiempo_procesamiento_horas for s in completadas) / len(completadas)
            
            # Solicitudes próximas a vencer (próximas 24 horas)
            proximas_vencer = [
                s for s in solicitudes 
                if not s.esta_completada and s.horas_restantes_sla <= 24
            ]
            
            return {
                'resumen': {
                    'total_solicitudes': total_solicitudes,
                    'activas': activas,
                    'vencidas': vencidas,
                    'fuera_sla': fuera_sla,
                    'requieren_alerta': requieren_alerta,
                    'tiempo_promedio_procesamiento': round(tiempo_promedio, 2)
                },
                'distribucion_estados': estados,
                'distribucion_tipos': tipos,
                'proximas_vencer': [
                    {
                        'id': str(s.id),
                        'numero_solicitud': s.numero_solicitud,
                        'cliente': s.cliente.nombres,
                        'tipo': s.nombre_tipo_legible,
                        'horas_restantes': s.horas_restantes_sla,
                        'porcentaje_sla': s.porcentaje_sla_consumido
                    }
                    for s in proximas_vencer[:10]  # Top 10
                ]
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo dashboard: {str(e)}")
            raise
    
    def obtener_alertas_usuario(
        self,
        usuario_id: str,
        solo_pendientes: bool = True
    ) -> List[SolicitudAlerta]:
        """
        Obtiene alertas para un usuario específico
        """
        try:
            query = self.db.query(SolicitudAlerta).filter(
                SolicitudAlerta.usuario_destinatario_id == usuario_id
            )
            
            if solo_pendientes:
                query = query.filter(SolicitudAlerta.estado.in_(['PENDIENTE', 'ENVIADA']))
            
            return query.order_by(
                SolicitudAlerta.nivel_urgencia.desc(),
                SolicitudAlerta.fecha_programada.desc()
            ).all()
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas: {str(e)}")
            raise
    
    def marcar_alerta_leida(self, alerta_id: str, usuario_id: str) -> SolicitudAlerta:
        """
        Marca una alerta como leída
        """
        try:
            alerta = self.db.query(SolicitudAlerta).filter(
                SolicitudAlerta.id == alerta_id,
                SolicitudAlerta.usuario_destinatario_id == usuario_id
            ).first()
            
            if not alerta:
                raise ValueError(f"Alerta {alerta_id} no encontrada")
            
            alerta.marcar_como_leida()
            self.db.commit()
            
            return alerta
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marcando alerta como leída: {str(e)}")
            raise
    
    def programar_seguimiento(
        self,
        solicitud_id: str,
        fecha_seguimiento: datetime,
        observaciones: Optional[str] = None,
        usuario_id: Optional[str] = None
    ) -> ClienteSolicitud:
        """
        Programa un seguimiento para una solicitud
        """
        try:
            solicitud = self.db.query(ClienteSolicitud).filter(
                ClienteSolicitud.id == solicitud_id
            ).first()
            
            if not solicitud:
                raise ValueError(f"Solicitud {solicitud_id} no encontrada")
            
            solicitud.fecha_proximo_seguimiento = fecha_seguimiento.date()
            solicitud.requiere_seguimiento = True
            
            if observaciones:
                solicitud.observaciones = observaciones
            
            # Crear evento en historial
            self._crear_evento_historial(
                solicitud.id,
                'SEGUIMIENTO_PROGRAMADO',
                f'Seguimiento programado para {fecha_seguimiento.strftime("%d/%m/%Y")}',
                observaciones or 'Seguimiento programado',
                usuario_id
            )
            
            self.db.commit()
            
            logger.info(f"Seguimiento programado para solicitud {solicitud.numero_solicitud}")
            return solicitud
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error programando seguimiento: {str(e)}")
            raise
    
    def _generar_numero_solicitud(self) -> str:
        """
        Genera un número único de solicitud
        """
        # Formato: SOL-YYYYMMDD-NNNN
        fecha = datetime.utcnow().strftime("%Y%m%d")
        
        # Contar solicitudes del día
        inicio_dia = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        fin_dia = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = self.db.query(ClienteSolicitud).filter(
            ClienteSolicitud.fecha_solicitud.between(inicio_dia, fin_dia)
        ).count()
        
        numero = f"SOL-{fecha}-{count + 1:04d}"
        
        # Verificar que no exista
        while self.db.query(ClienteSolicitud).filter(
            ClienteSolicitud.numero_solicitud == numero
        ).first():
            count += 1
            numero = f"SOL-{fecha}-{count:04d}"
        
        return numero
    
    def _crear_evento_historial(
        self,
        solicitud_id: str,
        tipo_evento: str,
        titulo: str,
        descripcion: str,
        usuario_id: Optional[str] = None
    ):
        """
        Crea un evento en el historial del cliente
        """
        try:
            solicitud = self.db.query(ClienteSolicitud).filter(
                ClienteSolicitud.id == solicitud_id
            ).first()
            
            if solicitud:
                historial = ClienteHistorial(
                    cliente_id=solicitud.cliente_id,
                    usuario_id=usuario_id or solicitud.usuario_asignado_id,
                    sucursal_id=solicitud.sucursal_id,
                    solicitud_id=solicitud_id,
                    tipo_evento=tipo_evento,
                    titulo=titulo,
                    descripcion=descripcion,
                    prioridad='NORMAL'
                )
                
                self.db.add(historial)
                
        except Exception as e:
            logger.error(f"Error creando evento historial: {str(e)}")
    
    def _crear_alerta_respuesta(self, solicitud: ClienteSolicitud, estado: str):
        """
        Crea alerta de respuesta al cliente
        """
        try:
            if estado == 'APROBADA':
                tipo_alerta = 'APROBACION_PENDIENTE'
                titulo = f'Solicitud Aprobada - {solicitud.numero_solicitud}'
                mensaje = f'La solicitud {solicitud.numero_solicitud} ha sido aprobada. Proceder con desembolso.'
            else:
                tipo_alerta = 'SEGUIMIENTO_REQUERIDO'
                titulo = f'Solicitud Rechazada - {solicitud.numero_solicitud}'
                mensaje = f'La solicitud {solicitud.numero_solicitud} ha sido rechazada. Notificar al cliente.'
            
            alerta = SolicitudAlerta(
                solicitud_id=solicitud.id,
                usuario_destinatario_id=solicitud.usuario_asignado_id,
                tipo_alerta=tipo_alerta,
                nivel_urgencia='ALTA',
                titulo=titulo,
                mensaje=mensaje
            )
            
            self.db.add(alerta)
            
        except Exception as e:
            logger.error(f"Error creando alerta de respuesta: {str(e)}")

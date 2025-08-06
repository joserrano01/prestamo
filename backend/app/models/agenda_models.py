"""
Modelos para el sistema de agenda de cobranza integrado con alertas
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Date, Time, Text, Boolean, Integer, Numeric, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, AuditMixin
from app.models.secure_models import EncryptedColumn


class TipoActividad(enum.Enum):
    """Tipos de actividades de cobranza"""
    LLAMADA_TELEFONICA = "LLAMADA_TELEFONICA"
    VISITA_DOMICILIO = "VISITA_DOMICILIO"
    VISITA_TRABAJO = "VISITA_TRABAJO"
    ENVIO_CARTA = "ENVIO_CARTA"
    ENVIO_EMAIL = "ENVIO_EMAIL"
    ENVIO_SMS = "ENVIO_SMS"
    REUNION_CLIENTE = "REUNION_CLIENTE"
    NEGOCIACION_PAGO = "NEGOCIACION_PAGO"
    ACUERDO_PAGO = "ACUERDO_PAGO"
    ENTREGA_DOCUMENTOS = "ENTREGA_DOCUMENTOS"
    VERIFICACION_DATOS = "VERIFICACION_DATOS"
    SEGUIMIENTO_PROMESA = "SEGUIMIENTO_PROMESA"
    ESCALAMIENTO_LEGAL = "ESCALAMIENTO_LEGAL"
    OTRO = "OTRO"


class EstadoActividad(enum.Enum):
    """Estados de las actividades"""
    PROGRAMADA = "PROGRAMADA"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    REPROGRAMADA = "REPROGRAMADA"
    NO_CONTACTO = "NO_CONTACTO"
    CLIENTE_NO_DISPONIBLE = "CLIENTE_NO_DISPONIBLE"
    VENCIDA = "VENCIDA"


class PrioridadActividad(enum.Enum):
    """Prioridades de actividades"""
    BAJA = "BAJA"
    NORMAL = "NORMAL"
    ALTA = "ALTA"
    CRITICA = "CRITICA"
    URGENTE = "URGENTE"


class ResultadoActividad(enum.Enum):
    """Resultados de las actividades"""
    EXITOSA = "EXITOSA"
    PARCIAL = "PARCIAL"
    SIN_EXITO = "SIN_EXITO"
    PROMESA_PAGO = "PROMESA_PAGO"
    ACUERDO_ALCANZADO = "ACUERDO_ALCANZADO"
    CLIENTE_INUBICABLE = "CLIENTE_INUBICABLE"
    CLIENTE_RENUENTE = "CLIENTE_RENUENTE"
    REQUIERE_ESCALAMIENTO = "REQUIERE_ESCALAMIENTO"
    PENDIENTE = "PENDIENTE"


class TipoAlertaCobranza(enum.Enum):
    """Tipos de alertas de cobranza"""
    PAGO_VENCIDO = "PAGO_VENCIDO"
    CLIENTE_SIN_CONTACTAR = "CLIENTE_SIN_CONTACTAR"
    PROMESA_INCUMPLIDA = "PROMESA_INCUMPLIDA"
    MORA_EXTENDIDA = "MORA_EXTENDIDA"
    ESCALAMIENTO_REQUERIDO = "ESCALAMIENTO_REQUERIDO"
    CLIENTE_ALTO_RIESGO = "CLIENTE_ALTO_RIESGO"


class EstadoAlerta(enum.Enum):
    """Estados de las alertas"""
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    RESUELTA = "RESUELTA"
    DESCARTADA = "DESCARTADA"


class NivelUrgencia(enum.Enum):
    """Niveles de urgencia"""
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


class AgendaCobranza(Base, AuditMixin):
    """
    Modelo para la agenda de actividades de cobranza
    """
    __tablename__ = "agenda_cobranza"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relaciones principales
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False, index=True)
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey("prestamos.id"), nullable=True, index=True)
    usuario_asignado_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey("sucursales.id"), nullable=True, index=True)
    
    # Información básica de la actividad
    tipo_actividad = Column(SQLEnum(TipoActividad), nullable=False, index=True)
    estado = Column(SQLEnum(EstadoActividad), nullable=False, default=EstadoActividad.PROGRAMADA, index=True)
    prioridad = Column(SQLEnum(PrioridadActividad), nullable=False, default=PrioridadActividad.NORMAL, index=True)
    resultado = Column(SQLEnum(ResultadoActividad), nullable=True, index=True)
    
    # Programación temporal
    fecha_programada = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time, nullable=True)
    hora_fin = Column(Time, nullable=True)
    duracion_estimada_minutos = Column(Integer, nullable=True)
    duracion_real_minutos = Column(Integer, nullable=True)
    
    # Fechas de control
    fecha_inicio_real = Column(DateTime, nullable=True)
    fecha_fin_real = Column(DateTime, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=True, index=True)
    fecha_reprogramacion = Column(DateTime, nullable=True)
    
    # Contenido encriptado (columnas de BD)
    _titulo = Column(String(200), nullable=False)
    _descripcion = Column(Text, nullable=True)
    _objetivo = Column(Text, nullable=True)
    _observaciones = Column(Text, nullable=True)
    _resultado_detalle = Column(Text, nullable=True)
    _proximos_pasos = Column(Text, nullable=True)
    _direccion_visita = Column(String(500), nullable=True)
    _telefono_contacto = Column(String(20), nullable=True)
    _persona_contacto = Column(String(100), nullable=True)
    
    # Información financiera encriptada
    _monto_gestionado = Column(Numeric(15, 2), nullable=True)
    _monto_prometido = Column(Numeric(15, 2), nullable=True)
    _fecha_promesa_pago = Column(Date, nullable=True)
    
    # Control de seguimiento
    requiere_seguimiento = Column(Boolean, default=False, index=True)
    fecha_proximo_seguimiento = Column(Date, nullable=True, index=True)
    numero_intentos = Column(Integer, default=0)
    es_actividad_recurrente = Column(Boolean, default=False)
    frecuencia_dias = Column(Integer, nullable=True)
    
    # Alertas y notificaciones
    generar_alerta_previa = Column(Boolean, default=True)
    minutos_alerta_previa = Column(Integer, default=60)  # 1 hora antes
    alerta_generada = Column(Boolean, default=False)
    notificar_supervisor = Column(Boolean, default=False)
    
    # Metadatos adicionales
    _metadata_json = Column(Text, nullable=True)
    
    # Propiedades para acceso a campos encriptados
    @property
    def titulo(self) -> Optional[str]:
        return self._titulo
    
    @titulo.setter
    def titulo(self, value: str):
        self._titulo = value
    
    @property
    def descripcion(self) -> Optional[str]:
        return self._descripcion
    
    @descripcion.setter
    def descripcion(self, value: Optional[str]):
        self._descripcion = value
    
    @property
    def objetivo(self) -> Optional[str]:
        return self._objetivo
    
    @objetivo.setter
    def objetivo(self, value: Optional[str]):
        self._objetivo = value
    
    @property
    def observaciones(self) -> Optional[str]:
        return self._observaciones
    
    @observaciones.setter
    def observaciones(self, value: Optional[str]):
        self._observaciones = value
    
    @property
    def resultado_detalle(self) -> Optional[str]:
        return self._resultado_detalle
    
    @resultado_detalle.setter
    def resultado_detalle(self, value: Optional[str]):
        self._resultado_detalle = value
    
    @property
    def proximos_pasos(self) -> Optional[str]:
        return self._proximos_pasos
    
    @proximos_pasos.setter
    def proximos_pasos(self, value: Optional[str]):
        self._proximos_pasos = value
    
    @property
    def direccion_visita(self) -> Optional[str]:
        return self._direccion_visita
    
    @direccion_visita.setter
    def direccion_visita(self, value: Optional[str]):
        self._direccion_visita = value
    
    @property
    def telefono_contacto(self) -> Optional[str]:
        return self._telefono_contacto
    
    @telefono_contacto.setter
    def telefono_contacto(self, value: Optional[str]):
        self._telefono_contacto = value
    
    @property
    def persona_contacto(self) -> Optional[str]:
        return self._persona_contacto
    
    @persona_contacto.setter
    def persona_contacto(self, value: Optional[str]):
        self._persona_contacto = value
    
    @property
    def monto_gestionado(self) -> Optional[Decimal]:
        return self._monto_gestionado
    
    @monto_gestionado.setter
    def monto_gestionado(self, value: Optional[Decimal]):
        self._monto_gestionado = value
    
    @property
    def monto_prometido(self) -> Optional[Decimal]:
        return self._monto_prometido
    
    @monto_prometido.setter
    def monto_prometido(self, value: Optional[Decimal]):
        self._monto_prometido = value
    
    @property
    def fecha_promesa_pago(self) -> Optional[date]:
        return self._fecha_promesa_pago
    
    @fecha_promesa_pago.setter
    def fecha_promesa_pago(self, value: Optional[date]):
        self._fecha_promesa_pago = value
    
    # Propiedades calculadas
    @property
    def esta_vencida(self) -> bool:
        """Verifica si la actividad está vencida"""
        if self.fecha_vencimiento:
            return datetime.utcnow() > self.fecha_vencimiento
        elif self.fecha_programada:
            fecha_limite = datetime.combine(self.fecha_programada, time(23, 59, 59))
            return datetime.utcnow() > fecha_limite
        return False
    
    @property
    def esta_programada_hoy(self) -> bool:
        """Verifica si la actividad está programada para hoy"""
        return self.fecha_programada == date.today()
    
    @property
    def minutos_para_inicio(self) -> Optional[int]:
        """Calcula minutos hasta el inicio de la actividad"""
        if not self.fecha_programada or not self.hora_inicio:
            return None
        
        fecha_hora_inicio = datetime.combine(self.fecha_programada, self.hora_inicio)
        ahora = datetime.utcnow()
        
        if fecha_hora_inicio > ahora:
            delta = fecha_hora_inicio - ahora
            return int(delta.total_seconds() / 60)
        
        return 0
    
    @property
    def requiere_alerta_previa(self) -> bool:
        """Determina si requiere alerta previa"""
        if not self.generar_alerta_previa or self.alerta_generada:
            return False
        
        minutos_restantes = self.minutos_para_inicio
        if minutos_restantes is None:
            return False
        
        return minutos_restantes <= self.minutos_alerta_previa
    
    @property
    def duracion_total_minutos(self) -> Optional[int]:
        """Calcula la duración total en minutos"""
        if self.fecha_inicio_real and self.fecha_fin_real:
            delta = self.fecha_fin_real - self.fecha_inicio_real
            return int(delta.total_seconds() / 60)
        return self.duracion_real_minutos
    
    @property
    def efectividad(self) -> str:
        """Calcula la efectividad de la actividad"""
        if self.resultado == ResultadoActividad.EXITOSA:
            return "ALTA"
        elif self.resultado in [ResultadoActividad.PARCIAL, ResultadoActividad.PROMESA_PAGO]:
            return "MEDIA"
        elif self.resultado == ResultadoActividad.SIN_EXITO:
            return "BAJA"
        return "PENDIENTE"
    
    @property
    def nombre_tipo_legible(self) -> str:
        """Nombre legible del tipo de actividad"""
        nombres = {
            TipoActividad.LLAMADA_TELEFONICA: "Llamada Telefónica",
            TipoActividad.VISITA_DOMICILIO: "Visita a Domicilio",
            TipoActividad.VISITA_TRABAJO: "Visita al Trabajo",
            TipoActividad.ENVIO_CARTA: "Envío de Carta",
            TipoActividad.ENVIO_EMAIL: "Envío de Email",
            TipoActividad.ENVIO_SMS: "Envío de SMS",
            TipoActividad.REUNION_CLIENTE: "Reunión con Cliente",
            TipoActividad.NEGOCIACION_PAGO: "Negociación de Pago",
            TipoActividad.ACUERDO_PAGO: "Acuerdo de Pago",
            TipoActividad.ENTREGA_DOCUMENTOS: "Entrega de Documentos",
            TipoActividad.VERIFICACION_DATOS: "Verificación de Datos",
            TipoActividad.SEGUIMIENTO_PROMESA: "Seguimiento de Promesa",
            TipoActividad.ESCALAMIENTO_LEGAL: "Escalamiento Legal",
            TipoActividad.OTRO: "Otro"
        }
        return nombres.get(self.tipo_actividad, str(self.tipo_actividad))
    
    @property
    def nombre_estado_legible(self) -> str:
        """Nombre legible del estado"""
        nombres = {
            EstadoActividad.PROGRAMADA: "Programada",
            EstadoActividad.EN_PROCESO: "En Proceso",
            EstadoActividad.COMPLETADA: "Completada",
            EstadoActividad.CANCELADA: "Cancelada",
            EstadoActividad.REPROGRAMADA: "Reprogramada",
            EstadoActividad.NO_CONTACTO: "Sin Contacto",
            EstadoActividad.CLIENTE_NO_DISPONIBLE: "Cliente No Disponible",
            EstadoActividad.VENCIDA: "Vencida"
        }
        return nombres.get(self.estado, str(self.estado))
    
    # Métodos de gestión
    def marcar_como_iniciada(self):
        """Marca la actividad como iniciada"""
        self.estado = EstadoActividad.EN_PROCESO
        self.fecha_inicio_real = datetime.utcnow()
    
    def marcar_como_completada(self, resultado: ResultadoActividad, detalle: Optional[str] = None):
        """Marca la actividad como completada"""
        self.estado = EstadoActividad.COMPLETADA
        self.resultado = resultado
        self.fecha_fin_real = datetime.utcnow()
        
        if detalle:
            self.resultado_detalle = detalle
        
        # Calcular duración real
        if self.fecha_inicio_real:
            delta = self.fecha_fin_real - self.fecha_inicio_real
            self.duracion_real_minutos = int(delta.total_seconds() / 60)
    
    def reprogramar(self, nueva_fecha: date, nueva_hora: Optional[time] = None):
        """Reprograma la actividad"""
        self.estado = EstadoActividad.REPROGRAMADA
        self.fecha_reprogramacion = datetime.utcnow()
        self.fecha_programada = nueva_fecha
        
        if nueva_hora:
            self.hora_inicio = nueva_hora
        
        # Resetear alerta
        self.alerta_generada = False
        self.numero_intentos += 1
    
    def cancelar(self, motivo: Optional[str] = None):
        """Cancela la actividad"""
        self.estado = EstadoActividad.CANCELADA
        if motivo:
            self.observaciones = f"{self.observaciones or ''}\nCancelada: {motivo}".strip()
    
    def programar_seguimiento(self, fecha_seguimiento: date, descripcion: Optional[str] = None):
        """Programa un seguimiento"""
        self.requiere_seguimiento = True
        self.fecha_proximo_seguimiento = fecha_seguimiento
        if descripcion:
            self.proximos_pasos = descripcion
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="actividades_cobranza")
    prestamo = relationship("Prestamo", back_populates="actividades_cobranza")
    usuario_asignado = relationship("Usuario", foreign_keys=[usuario_asignado_id])
    sucursal = relationship("Sucursal")
    alertas = relationship("AlertaCobranza", back_populates="actividad", cascade="all, delete-orphan")


class AlertaCobranza(Base, AuditMixin):
    """
    Modelo para alertas específicas de cobranza
    """
    __tablename__ = "alertas_cobranza"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Relaciones
    actividad_id = Column(UUID(as_uuid=True), ForeignKey("agenda_cobranza.id"), nullable=False, index=True)
    usuario_destinatario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, index=True)
    
    # Información de la alerta
    tipo_alerta = Column(String(50), nullable=False, index=True)  # ACTIVIDAD_PROGRAMADA, ACTIVIDAD_VENCIDA, etc.
    estado = Column(String(20), nullable=False, default="PENDIENTE", index=True)
    nivel_urgencia = Column(String(20), nullable=False, default="MEDIA", index=True)
    
    titulo = Column(String(200), nullable=False)
    mensaje = Column(Text, nullable=False)
    
    # Fechas
    fecha_programada = Column(DateTime, nullable=True, index=True)
    fecha_enviada = Column(DateTime, nullable=True)
    fecha_leida = Column(DateTime, nullable=True)
    fecha_atendida = Column(DateTime, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=True)
    
    # Configuración de envío
    enviar_email = Column(Boolean, default=True)
    enviar_sms = Column(Boolean, default=False)
    enviar_push = Column(Boolean, default=True)
    
    # Control de envío
    intentos_envio = Column(Integer, default=0)
    ultimo_intento = Column(DateTime, nullable=True)
    error_envio = Column(Text, nullable=True)
    
    # Propiedades calculadas
    @property
    def esta_vencida(self) -> bool:
        """Verifica si la alerta está vencida"""
        if self.fecha_vencimiento:
            return datetime.utcnow() > self.fecha_vencimiento
        return False
    
    @property
    def esta_pendiente(self) -> bool:
        """Verifica si la alerta está pendiente"""
        return self.estado in ["PENDIENTE", "ENVIADA"]
    
    # Métodos de gestión
    def marcar_como_enviada(self):
        """Marca la alerta como enviada"""
        self.estado = "ENVIADA"
        self.fecha_enviada = datetime.utcnow()
        self.intentos_envio += 1
    
    def marcar_como_leida(self):
        """Marca la alerta como leída"""
        self.estado = "LEIDA"
        self.fecha_leida = datetime.utcnow()
    
    def marcar_como_atendida(self):
        """Marca la alerta como atendida"""
        self.estado = "ATENDIDA"
        self.fecha_atendida = datetime.utcnow()
    
    # Relaciones
    actividad = relationship("AgendaCobranza", back_populates="alertas")
    usuario_destinatario = relationship("Usuario")


# Índices optimizados
from sqlalchemy import Index

# Índices para AgendaCobranza
Index('idx_agenda_cliente_fecha', AgendaCobranza.cliente_id, AgendaCobranza.fecha_programada)
Index('idx_agenda_usuario_fecha', AgendaCobranza.usuario_asignado_id, AgendaCobranza.fecha_programada)
Index('idx_agenda_estado_prioridad', AgendaCobranza.estado, AgendaCobranza.prioridad)
Index('idx_agenda_tipo_fecha', AgendaCobranza.tipo_actividad, AgendaCobranza.fecha_programada)
Index('idx_agenda_vencimiento', AgendaCobranza.fecha_vencimiento)
Index('idx_agenda_seguimiento', AgendaCobranza.fecha_proximo_seguimiento)
Index('idx_agenda_hoy', AgendaCobranza.fecha_programada, AgendaCobranza.estado)
Index('idx_agenda_alertas', AgendaCobranza.generar_alerta_previa, AgendaCobranza.alerta_generada)

# Índices para AlertaCobranza
Index('idx_alerta_cobranza_usuario', AlertaCobranza.usuario_destinatario_id, AlertaCobranza.estado)
Index('idx_alerta_cobranza_actividad', AlertaCobranza.actividad_id)
Index('idx_alerta_cobranza_tipo', AlertaCobranza.tipo_alerta, AlertaCobranza.estado)
Index('idx_alerta_cobranza_programada', AlertaCobranza.fecha_programada, AlertaCobranza.estado)

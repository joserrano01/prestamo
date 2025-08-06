"""
Esquemas Pydantic para solicitudes de clientes
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


class SolicitudBase(BaseModel):
    """Esquema base para solicitudes"""
    tipo_solicitud: str = Field(..., description="Tipo de solicitud")
    prioridad: str = Field(default="NORMAL", description="Prioridad de la solicitud")
    canal: str = Field(..., description="Canal por el que se recibió")
    asunto: str = Field(..., min_length=1, max_length=200, description="Asunto de la solicitud")
    descripcion: str = Field(..., min_length=1, description="Descripción detallada")
    sla_horas: Optional[int] = Field(default=24, ge=1, le=720, description="SLA en horas")
    monto_solicitado: Optional[Decimal] = Field(None, ge=0, description="Monto solicitado")
    moneda: Optional[str] = Field(default="USD", description="Moneda")
    plazo_solicitado: Optional[int] = Field(None, ge=1, description="Plazo solicitado en meses")
    telefono_contacto: Optional[str] = Field(None, description="Teléfono de contacto")
    email_contacto: Optional[str] = Field(None, description="Email de contacto")
    requiere_documentos: bool = Field(default=False, description="Requiere documentos")
    documentos_pendientes: Optional[str] = Field(None, description="Documentos pendientes")
    requiere_garantia: bool = Field(default=False, description="Requiere garantía")
    requiere_avalista: bool = Field(default=False, description="Requiere avalista")
    
    @validator('tipo_solicitud')
    def validate_tipo_solicitud(cls, v):
        tipos_validos = [
            'CREDITO_PERSONAL', 'CREDITO_VEHICULAR', 'CREDITO_HIPOTECARIO', 'CREDITO_COMERCIAL',
            'REFINANCIAMIENTO', 'RENOVACION', 'AUMENTO_LIMITE', 'CAMBIO_CONDICIONES',
            'CARTA_REFERENCIA', 'CERTIFICACION_INGRESOS', 'ESTADO_CUENTA', 'DUPLICADO_DOCUMENTO',
            'ACTUALIZACION_DATOS', 'RECLAMO', 'QUEJA', 'SUGERENCIA', 'OTRO'
        ]
        if v not in tipos_validos:
            raise ValueError(f'Tipo de solicitud debe ser uno de: {", ".join(tipos_validos)}')
        return v
    
    @validator('prioridad')
    def validate_prioridad(cls, v):
        prioridades_validas = ['BAJA', 'NORMAL', 'ALTA', 'CRITICA']
        if v not in prioridades_validas:
            raise ValueError(f'Prioridad debe ser una de: {", ".join(prioridades_validas)}')
        return v
    
    @validator('canal')
    def validate_canal(cls, v):
        canales_validos = [
            'SUCURSAL', 'ONLINE', 'TELEFONO', 'EMAIL', 'WHATSAPP', 'APP_MOVIL', 'AGENTE'
        ]
        if v not in canales_validos:
            raise ValueError(f'Canal debe ser uno de: {", ".join(canales_validos)}')
        return v


class SolicitudCreate(SolicitudBase):
    """Esquema para crear solicitud"""
    cliente_id: UUID = Field(..., description="ID del cliente")
    usuario_asignado_id: Optional[UUID] = Field(None, description="ID del usuario asignado")


class SolicitudUpdate(BaseModel):
    """Esquema para actualizar solicitud"""
    estado: Optional[str] = Field(None, description="Estado de la solicitud")
    prioridad: Optional[str] = Field(None, description="Prioridad")
    asunto: Optional[str] = Field(None, min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, min_length=1)
    observaciones: Optional[str] = Field(None, description="Observaciones")
    monto_aprobado: Optional[Decimal] = Field(None, ge=0, description="Monto aprobado")
    plazo_aprobado: Optional[int] = Field(None, ge=1, description="Plazo aprobado")
    tasa_interes: Optional[Decimal] = Field(None, ge=0, description="Tasa de interés")
    condiciones_aprobacion: Optional[str] = Field(None, description="Condiciones de aprobación")
    motivo_rechazo: Optional[str] = Field(None, description="Motivo de rechazo")
    respuesta_cliente: Optional[str] = Field(None, description="Respuesta al cliente")
    requiere_seguimiento: Optional[bool] = Field(None, description="Requiere seguimiento")
    requiere_documentos: Optional[bool] = Field(None, description="Requiere documentos")
    documentos_pendientes: Optional[str] = Field(None, description="Documentos pendientes")
    
    @validator('estado')
    def validate_estado(cls, v):
        if v is None:
            return v
        estados_validos = [
            'RECIBIDA', 'EN_REVISION', 'DOCUMENTOS_PENDIENTES', 'EN_EVALUACION',
            'EN_COMITE', 'APROBADA', 'APROBADA_CONDICIONADA', 'RECHAZADA',
            'EN_DESEMBOLSO', 'DESEMBOLSADA', 'COMPLETADA', 'CANCELADA', 'VENCIDA'
        ]
        if v not in estados_validos:
            raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v


class SolicitudAsignar(BaseModel):
    """Esquema para asignar solicitud"""
    usuario_asignado_id: UUID = Field(..., description="ID del usuario a asignar")
    observaciones: Optional[str] = Field(None, description="Observaciones de la asignación")


class SolicitudSeguimiento(BaseModel):
    """Esquema para programar seguimiento"""
    fecha_seguimiento: datetime = Field(..., description="Fecha y hora del seguimiento")
    observaciones: Optional[str] = Field(None, description="Observaciones del seguimiento")
    
    @validator('fecha_seguimiento')
    def validate_fecha_seguimiento(cls, v):
        if v <= datetime.utcnow():
            raise ValueError('La fecha de seguimiento debe ser futura')
        return v


class ClienteInfo(BaseModel):
    """Información básica del cliente"""
    id: UUID
    nombres: str
    apellidos: str
    cedula: str
    telefono: Optional[str]
    email: Optional[str]
    
    class Config:
        from_attributes = True


class UsuarioInfo(BaseModel):
    """Información básica del usuario"""
    id: UUID
    nombres: str
    apellidos: str
    email: str
    
    class Config:
        from_attributes = True


class SucursalInfo(BaseModel):
    """Información básica de la sucursal"""
    id: UUID
    nombre: str
    codigo: str
    
    class Config:
        from_attributes = True


class SolicitudResponse(BaseModel):
    """Esquema de respuesta para solicitud"""
    id: UUID
    numero_solicitud: str
    cliente_id: UUID
    usuario_asignado_id: Optional[UUID]
    sucursal_id: Optional[UUID]
    prestamo_id: Optional[UUID]
    
    tipo_solicitud: str
    estado: str
    prioridad: str
    canal: str
    
    fecha_solicitud: datetime
    fecha_limite_respuesta: Optional[datetime]
    fecha_vencimiento: Optional[datetime]
    fecha_respuesta: Optional[datetime]
    fecha_completada: Optional[datetime]
    
    asunto: str
    descripcion: str
    observaciones: Optional[str]
    
    monto_solicitado: Optional[Decimal]
    monto_aprobado: Optional[Decimal]
    moneda: Optional[str]
    plazo_solicitado: Optional[int]
    plazo_aprobado: Optional[int]
    tasa_interes: Optional[Decimal]
    
    condiciones_aprobacion: Optional[str]
    motivo_rechazo: Optional[str]
    respuesta_cliente: Optional[str]
    
    telefono_contacto: Optional[str]
    email_contacto: Optional[str]
    
    sla_horas: int
    alertas_enviadas: int
    ultima_alerta: Optional[datetime]
    
    requiere_seguimiento: bool
    fecha_proximo_seguimiento: Optional[date]
    requiere_documentos: bool
    documentos_pendientes: Optional[str]
    requiere_garantia: bool
    requiere_avalista: bool
    
    tiempo_respuesta_horas: Optional[Decimal]
    tiempo_procesamiento_horas: Optional[Decimal]
    numero_interacciones: int
    
    # Propiedades calculadas
    esta_vencida: bool
    esta_en_sla: bool
    horas_transcurridas: Optional[int]
    horas_restantes_sla: Optional[int]
    porcentaje_sla_consumido: Optional[Decimal]
    requiere_alerta: bool
    esta_completada: bool
    nombre_tipo_legible: str
    nombre_estado_legible: str
    
    # Relaciones
    cliente: Optional[ClienteInfo]
    usuario_asignado: Optional[UsuarioInfo]
    sucursal: Optional[SucursalInfo]
    
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SolicitudListResponse(BaseModel):
    """Respuesta para lista de solicitudes"""
    items: List[SolicitudResponse]
    total: int
    skip: int
    limit: int


class AlertaResponse(BaseModel):
    """Esquema de respuesta para alerta"""
    id: UUID
    solicitud_id: UUID
    usuario_destinatario_id: UUID
    
    tipo_alerta: str
    estado: str
    nivel_urgencia: str
    
    titulo: str
    mensaje: str
    
    fecha_programada: Optional[datetime]
    fecha_enviada: Optional[datetime]
    fecha_leida: Optional[datetime]
    fecha_atendida: Optional[datetime]
    fecha_vencimiento: Optional[datetime]
    
    enviar_email: bool
    enviar_sms: bool
    enviar_push: bool
    
    intentos_envio: int
    ultimo_intento: Optional[datetime]
    error_envio: Optional[str]
    
    # Propiedades calculadas
    esta_vencida: bool
    esta_pendiente: bool
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class DashboardResumen(BaseModel):
    """Resumen para dashboard"""
    total_solicitudes: int
    activas: int
    vencidas: int
    fuera_sla: int
    requieren_alerta: int
    tiempo_promedio_procesamiento: float


class SolicitudProximaVencer(BaseModel):
    """Solicitud próxima a vencer"""
    id: str
    numero_solicitud: str
    cliente: str
    tipo: str
    horas_restantes: Optional[int]
    porcentaje_sla: Optional[Decimal]


class DashboardResponse(BaseModel):
    """Respuesta completa del dashboard"""
    resumen: DashboardResumen
    distribucion_estados: Dict[str, int]
    distribucion_tipos: Dict[str, int]
    proximas_vencer: List[SolicitudProximaVencer]


class AlertaCreate(BaseModel):
    """Esquema para crear alerta"""
    solicitud_id: UUID
    usuario_destinatario_id: UUID
    tipo_alerta: str
    nivel_urgencia: str = Field(default="MEDIA")
    titulo: str = Field(..., min_length=1, max_length=200)
    mensaje: str = Field(..., min_length=1)
    fecha_programada: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None
    enviar_email: bool = Field(default=True)
    enviar_sms: bool = Field(default=False)
    enviar_push: bool = Field(default=True)
    
    @validator('tipo_alerta')
    def validate_tipo_alerta(cls, v):
        tipos_validos = [
            'SLA_75', 'SLA_90', 'SLA_VENCIDO', 'DOCUMENTOS_PENDIENTES',
            'SOLICITUD_VENCIDA', 'SEGUIMIENTO_REQUERIDO', 'APROBACION_PENDIENTE',
            'DESEMBOLSO_PENDIENTE', 'CLIENTE_INACTIVO'
        ]
        if v not in tipos_validos:
            raise ValueError(f'Tipo de alerta debe ser uno de: {", ".join(tipos_validos)}')
        return v
    
    @validator('nivel_urgencia')
    def validate_nivel_urgencia(cls, v):
        niveles_validos = ['BAJA', 'MEDIA', 'ALTA', 'CRITICA']
        if v not in niveles_validos:
            raise ValueError(f'Nivel de urgencia debe ser uno de: {", ".join(niveles_validos)}')
        return v


class SolicitudEstadisticas(BaseModel):
    """Estadísticas de solicitudes"""
    periodo: str
    total_solicitudes: int
    por_tipo: Dict[str, int]
    por_estado: Dict[str, int]
    por_canal: Dict[str, int]
    por_prioridad: Dict[str, int]
    tiempo_promedio_respuesta: float
    tiempo_promedio_procesamiento: float
    porcentaje_cumplimiento_sla: float
    solicitudes_vencidas: int
    solicitudes_fuera_sla: int


class SolicitudMetricas(BaseModel):
    """Métricas detalladas de solicitud"""
    id: UUID
    numero_solicitud: str
    cliente_nombre: str
    tipo_solicitud: str
    estado: str
    fecha_solicitud: datetime
    fecha_limite_respuesta: Optional[datetime]
    tiempo_transcurrido_horas: Optional[int]
    tiempo_restante_horas: Optional[int]
    porcentaje_sla_consumido: Optional[Decimal]
    numero_interacciones: int
    alertas_enviadas: int
    esta_en_sla: bool
    esta_vencida: bool


class ReporteSolicitudes(BaseModel):
    """Reporte de solicitudes"""
    titulo: str
    fecha_generacion: datetime
    parametros: Dict[str, Any]
    resumen: DashboardResumen
    estadisticas: SolicitudEstadisticas
    solicitudes_detalle: List[SolicitudMetricas]
    total_registros: int

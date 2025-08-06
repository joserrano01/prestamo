"""
Esquemas Pydantic para agenda de cobranza
"""
from datetime import datetime, date, time
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator

from app.models.agenda_models import (
    TipoActividad, EstadoActividad, PrioridadActividad, 
    ResultadoActividad, TipoAlertaCobranza, EstadoAlerta, NivelUrgencia
)


# ============================================================================
# ESQUEMAS BASE
# ============================================================================

class ActividadCobranzaBase(BaseModel):
    """Esquema base para actividad de cobranza"""
    tipo_actividad: str = Field(..., description="Tipo de actividad")
    titulo: str = Field(..., max_length=200, description="Título de la actividad")
    descripcion: Optional[str] = Field(None, description="Descripción detallada")
    fecha_programada: date = Field(..., description="Fecha programada")
    hora_inicio: Optional[time] = Field(None, description="Hora de inicio")
    duracion_estimada_minutos: Optional[int] = Field(None, ge=1, le=480, description="Duración en minutos")
    prioridad: str = Field(default="NORMAL", description="Prioridad de la actividad")
    objetivo: Optional[str] = Field(None, description="Objetivo de la actividad")
    direccion_visita: Optional[str] = Field(None, description="Dirección para visitas")
    telefono_contacto: Optional[str] = Field(None, description="Teléfono de contacto")
    persona_contacto: Optional[str] = Field(None, description="Persona de contacto")
    monto_gestionado: Optional[Decimal] = Field(None, ge=0, description="Monto gestionado")
    observaciones: Optional[str] = Field(None, description="Observaciones")

    @validator('tipo_actividad')
    def validate_tipo_actividad(cls, v):
        if v not in [t.value for t in TipoActividad]:
            raise ValueError(f'Tipo de actividad inválido: {v}')
        return v

    @validator('prioridad')
    def validate_prioridad(cls, v):
        if v not in [p.value for p in PrioridadActividad]:
            raise ValueError(f'Prioridad inválida: {v}')
        return v


class AlertaCobranzaBase(BaseModel):
    """Esquema base para alerta de cobranza"""
    tipo_alerta: str = Field(..., description="Tipo de alerta")
    titulo: str = Field(..., max_length=200, description="Título de la alerta")
    mensaje: str = Field(..., description="Mensaje de la alerta")
    nivel_urgencia: str = Field(default="NORMAL", description="Nivel de urgencia")
    fecha_programada: datetime = Field(..., description="Fecha programada para envío")
    fecha_vencimiento: Optional[datetime] = Field(None, description="Fecha de vencimiento")
    enviar_email: bool = Field(default=True, description="Enviar por email")
    enviar_sms: bool = Field(default=False, description="Enviar por SMS")
    enviar_push: bool = Field(default=True, description="Enviar notificación push")

    @validator('tipo_alerta')
    def validate_tipo_alerta(cls, v):
        if v not in [t.value for t in TipoAlertaCobranza]:
            raise ValueError(f'Tipo de alerta inválido: {v}')
        return v

    @validator('nivel_urgencia')
    def validate_nivel_urgencia(cls, v):
        if v not in [n.value for n in NivelUrgencia]:
            raise ValueError(f'Nivel de urgencia inválido: {v}')
        return v


# ============================================================================
# ESQUEMAS DE CREACIÓN
# ============================================================================

class ActividadCobranzaCreate(ActividadCobranzaBase):
    """Esquema para crear actividad de cobranza"""
    cliente_id: UUID = Field(..., description="ID del cliente")
    prestamo_id: Optional[UUID] = Field(None, description="ID del préstamo")
    usuario_asignado_id: Optional[UUID] = Field(None, description="ID del usuario asignado")
    generar_alerta_previa: bool = Field(default=True, description="Generar alerta previa")
    minutos_alerta_previa: int = Field(default=30, ge=5, le=1440, description="Minutos antes para alerta")

    @root_validator(skip_on_failure=True)
    def validate_fecha_futura(cls, values):
        fecha_programada = values.get('fecha_programada')
        if fecha_programada and fecha_programada < date.today():
            raise ValueError('La fecha programada debe ser hoy o en el futuro')
        return values


class AlertaCobranzaCreate(AlertaCobranzaBase):
    """Esquema para crear alerta de cobranza"""
    actividad_id: UUID = Field(..., description="ID de la actividad")
    usuario_destinatario_id: UUID = Field(..., description="ID del usuario destinatario")


# ============================================================================
# ESQUEMAS DE ACTUALIZACIÓN
# ============================================================================

class ActividadCobranzaUpdate(BaseModel):
    """Esquema para actualizar actividad de cobranza"""
    titulo: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    fecha_programada: Optional[date] = None
    hora_inicio: Optional[time] = None
    duracion_estimada_minutos: Optional[int] = Field(None, ge=1, le=480)
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    resultado: Optional[str] = None
    resultado_detalle: Optional[str] = None
    objetivo: Optional[str] = None
    direccion_visita: Optional[str] = None
    telefono_contacto: Optional[str] = None
    persona_contacto: Optional[str] = None
    monto_gestionado: Optional[Decimal] = Field(None, ge=0)
    monto_prometido: Optional[Decimal] = Field(None, ge=0)
    fecha_promesa_pago: Optional[date] = None
    proximos_pasos: Optional[str] = None
    observaciones: Optional[str] = None

    @validator('prioridad')
    def validate_prioridad(cls, v):
        if v and v not in [p.value for p in PrioridadActividad]:
            raise ValueError(f'Prioridad inválida: {v}')
        return v

    @validator('estado')
    def validate_estado(cls, v):
        if v and v not in [e.value for e in EstadoActividad]:
            raise ValueError(f'Estado inválido: {v}')
        return v

    @validator('resultado')
    def validate_resultado(cls, v):
        if v and v not in [r.value for r in ResultadoActividad]:
            raise ValueError(f'Resultado inválido: {v}')
        return v


# ============================================================================
# ESQUEMAS DE ACCIONES ESPECÍFICAS
# ============================================================================

class ActividadReprogramar(BaseModel):
    """Esquema para reprogramar actividad"""
    nueva_fecha: date = Field(..., description="Nueva fecha programada")
    nueva_hora: Optional[time] = Field(None, description="Nueva hora")
    motivo: str = Field(..., max_length=500, description="Motivo de la reprogramación")

    @validator('nueva_fecha')
    def validate_nueva_fecha(cls, v):
        if v < date.today():
            raise ValueError('La nueva fecha debe ser hoy o en el futuro')
        return v


class ActividadCompletar(BaseModel):
    """Esquema para completar actividad"""
    resultado: str = Field(..., description="Resultado de la actividad")
    resultado_detalle: Optional[str] = Field(None, description="Detalle del resultado")
    monto_prometido: Optional[Decimal] = Field(None, ge=0, description="Monto prometido")
    fecha_promesa_pago: Optional[date] = Field(None, description="Fecha de promesa de pago")
    proximos_pasos: Optional[str] = Field(None, description="Próximos pasos")

    @validator('resultado')
    def validate_resultado(cls, v):
        if v not in [r.value for r in ResultadoActividad]:
            raise ValueError(f'Resultado inválido: {v}')
        return v

    @root_validator(skip_on_failure=True)
    def validate_promesa_pago(cls, values):
        monto_prometido = values.get('monto_prometido')
        fecha_promesa_pago = values.get('fecha_promesa_pago')
        
        if monto_prometido and not fecha_promesa_pago:
            raise ValueError('Si hay monto prometido, debe especificar fecha de promesa')
        
        if fecha_promesa_pago and fecha_promesa_pago <= date.today():
            raise ValueError('La fecha de promesa debe ser futura')
        
        return values


# ============================================================================
# ESQUEMAS DE RESPUESTA
# ============================================================================

class ClienteBasico(BaseModel):
    """Información básica del cliente"""
    id: UUID
    numero_cliente: str
    primer_nombre: str
    primer_apellido: str
    nombre_completo: str

    class Config:
        orm_mode = True


class UsuarioBasico(BaseModel):
    """Información básica del usuario"""
    id: UUID
    username: str
    nombre_completo: str
    email: str

    class Config:
        orm_mode = True


class PrestamoBasico(BaseModel):
    """Información básica del préstamo"""
    id: UUID
    numero_prestamo: str
    monto_prestamo: Decimal
    saldo_actual: Decimal
    dias_mora: int
    estado: str

    class Config:
        orm_mode = True


class ActividadCobranzaResponse(BaseModel):
    """Respuesta completa de actividad de cobranza"""
    id: UUID
    numero_actividad: str
    cliente_id: UUID
    prestamo_id: Optional[UUID]
    usuario_asignado_id: UUID
    sucursal_id: Optional[UUID]
    tipo_actividad: str
    estado: str
    prioridad: str
    titulo: str
    descripcion: Optional[str]
    fecha_programada: date
    hora_inicio: Optional[time]
    duracion_estimada_minutos: Optional[int]
    fecha_inicio_real: Optional[datetime]
    fecha_fin_real: Optional[datetime]
    duracion_real_minutos: Optional[int]
    resultado: Optional[str]
    resultado_detalle: Optional[str]
    objetivo: Optional[str]
    direccion_visita: Optional[str]
    telefono_contacto: Optional[str]
    persona_contacto: Optional[str]
    monto_gestionado: Optional[Decimal]
    monto_prometido: Optional[Decimal]
    fecha_promesa_pago: Optional[date]
    proximos_pasos: Optional[str]
    observaciones: Optional[str]
    fecha_vencimiento: Optional[datetime]
    numero_reprogramaciones: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    # Relaciones
    cliente: Optional[ClienteBasico]
    usuario_asignado: Optional[UsuarioBasico]
    prestamo: Optional[PrestamoBasico]
    
    # Propiedades calculadas
    esta_vencida: bool
    esta_hoy: bool
    dias_para_vencimiento: Optional[int]
    horas_transcurridas: Optional[int]
    nombre_tipo_legible: str
    nombre_estado_legible: str
    nombre_prioridad_legible: str
    nombre_resultado_legible: Optional[str]

    class Config:
        orm_mode = True


class AlertaCobranzaResponse(BaseModel):
    """Respuesta de alerta de cobranza"""
    id: UUID
    actividad_id: UUID
    usuario_destinatario_id: UUID
    tipo_alerta: str
    estado: str
    nivel_urgencia: str
    titulo: str
    mensaje: str
    fecha_programada: datetime
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
    fecha_creacion: datetime
    
    # Propiedades calculadas
    esta_vencida: bool
    esta_pendiente: bool
    puede_reenviar: bool
    nombre_tipo_legible: str
    nombre_estado_legible: str
    nombre_urgencia_legible: str

    class Config:
        orm_mode = True


# ============================================================================
# ESQUEMAS DE LISTAS Y PAGINACIÓN
# ============================================================================

class ActividadCobranzaListResponse(BaseModel):
    """Respuesta de lista de actividades con paginación"""
    items: List[ActividadCobranzaResponse]
    total: int
    skip: int
    limit: int
    has_next: bool = False
    has_prev: bool = False

    @root_validator(skip_on_failure=True)
    def calculate_pagination(cls, values):
        total = values.get('total', 0)
        skip = values.get('skip', 0)
        limit = values.get('limit', 0)
        
        values['has_next'] = (skip + limit) < total
        values['has_prev'] = skip > 0
        
        return values


class AlertaCobranzaListResponse(BaseModel):
    """Respuesta de lista de alertas con paginación"""
    items: List[AlertaCobranzaResponse]
    total: int
    skip: int
    limit: int
    has_next: bool = False
    has_prev: bool = False

    @root_validator(skip_on_failure=True)
    def calculate_pagination(cls, values):
        total = values.get('total', 0)
        skip = values.get('skip', 0)
        limit = values.get('limit', 0)
        
        values['has_next'] = (skip + limit) < total
        values['has_prev'] = skip > 0
        
        return values


# ============================================================================
# ESQUEMAS DE DASHBOARD Y REPORTES
# ============================================================================

class MetricaActividad(BaseModel):
    """Métrica de actividades"""
    total: int = 0
    programadas: int = 0
    en_proceso: int = 0
    completadas: int = 0
    canceladas: int = 0
    vencidas: int = 0


class MetricaResultado(BaseModel):
    """Métrica de resultados"""
    contacto_exitoso: int = 0
    sin_contacto: int = 0
    promesa_pago: int = 0
    pago_realizado: int = 0
    acuerdo_pago: int = 0
    cliente_inubicable: int = 0
    negativa_pago: int = 0
    referido_legal: int = 0


class MetricaPrioridad(BaseModel):
    """Métrica por prioridad"""
    baja: int = 0
    normal: int = 0
    alta: int = 0
    critica: int = 0


class MetricaTipoActividad(BaseModel):
    """Métrica por tipo de actividad"""
    llamada_telefonica: int = 0
    visita_domicilio: int = 0
    visita_trabajo: int = 0
    envio_carta: int = 0
    envio_email: int = 0
    whatsapp: int = 0
    sms: int = 0
    negociacion: int = 0
    escalamiento_legal: int = 0
    seguimiento_promesa: int = 0


class ResumenEfectividad(BaseModel):
    """Resumen de efectividad"""
    total_actividades: int = 0
    actividades_exitosas: int = 0
    porcentaje_efectividad: float = 0.0
    promesas_cumplidas: int = 0
    promesas_incumplidas: int = 0
    porcentaje_cumplimiento_promesas: float = 0.0
    monto_total_gestionado: Decimal = Decimal('0.00')
    monto_total_prometido: Decimal = Decimal('0.00')
    monto_total_recuperado: Decimal = Decimal('0.00')


class DashboardCobranzaResponse(BaseModel):
    """Dashboard completo de cobranza"""
    # Métricas generales
    actividades_hoy: int = 0
    actividades_pendientes: int = 0
    actividades_vencidas: int = 0
    alertas_pendientes: int = 0
    promesas_pago_vencidas: int = 0
    
    # Métricas detalladas
    metricas_actividad: MetricaActividad
    metricas_resultado: MetricaResultado
    metricas_prioridad: MetricaPrioridad
    metricas_tipo: MetricaTipoActividad
    resumen_efectividad: ResumenEfectividad
    
    # Actividades próximas
    proximas_actividades: List[ActividadCobranzaResponse] = []
    
    # Alertas críticas
    alertas_criticas: List[AlertaCobranzaResponse] = []
    
    # Período del reporte
    fecha_desde: Optional[date]
    fecha_hasta: Optional[date]
    fecha_generacion: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# ESQUEMAS DE FILTROS
# ============================================================================

class FiltrosActividad(BaseModel):
    """Filtros para búsqueda de actividades"""
    cliente_id: Optional[UUID] = None
    prestamo_id: Optional[UUID] = None
    usuario_asignado_id: Optional[UUID] = None
    sucursal_id: Optional[UUID] = None
    tipo_actividad: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    resultado: Optional[str] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    solo_hoy: bool = False
    solo_pendientes: bool = False
    solo_vencidas: bool = False
    solo_con_promesas: bool = False


class FiltrosAlerta(BaseModel):
    """Filtros para búsqueda de alertas"""
    actividad_id: Optional[UUID] = None
    usuario_destinatario_id: Optional[UUID] = None
    tipo_alerta: Optional[str] = None
    estado: Optional[str] = None
    nivel_urgencia: Optional[str] = None
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None
    solo_pendientes: bool = True
    solo_criticas: bool = False


# ============================================================================
# ESQUEMAS DE REPORTES
# ============================================================================

class ReporteEfectividadUsuario(BaseModel):
    """Reporte de efectividad por usuario"""
    usuario_id: UUID
    usuario_nombre: str
    total_actividades: int
    actividades_completadas: int
    porcentaje_completadas: float
    actividades_exitosas: int
    porcentaje_efectividad: float
    promesas_obtenidas: int
    promesas_cumplidas: int
    porcentaje_cumplimiento: float
    monto_gestionado: Decimal
    monto_recuperado: Decimal


class ReporteEfectividadSucursal(BaseModel):
    """Reporte de efectividad por sucursal"""
    sucursal_id: UUID
    sucursal_nombre: str
    usuarios: List[ReporteEfectividadUsuario]
    totales: ResumenEfectividad


class ReporteSemanal(BaseModel):
    """Reporte semanal de cobranza"""
    semana_inicio: date
    semana_fin: date
    resumen_general: ResumenEfectividad
    por_sucursal: List[ReporteEfectividadSucursal]
    fecha_generacion: datetime = Field(default_factory=datetime.utcnow)

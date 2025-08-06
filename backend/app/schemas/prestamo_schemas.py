"""
Esquemas Pydantic para préstamos con descuento directo

Este archivo contiene todos los esquemas de validación para préstamos,
incluyendo los nuevos campos para descuento directo específicos del
sistema financiero panameño.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TipoPrestamo(str, Enum):
    """Tipos de préstamo disponibles"""
    PERSONAL = "PERSONAL"
    VEHICULAR = "VEHICULAR"
    HIPOTECARIO = "HIPOTECARIO"
    COMERCIAL = "COMERCIAL"
    CONSUMO = "CONSUMO"
    EDUCATIVO = "EDUCATIVO"
    EMERGENCIA = "EMERGENCIA"


class TipoDescuentoDirecto(str, Enum):
    """Tipos de descuento directo para préstamos personales"""
    JUBILADOS = "JUBILADOS"
    PAGOS_VOLUNTARIOS = "PAGOS_VOLUNTARIOS"
    CONTRALORIA = "CONTRALORIA"
    CSS = "CSS"
    MEF = "MEF"
    MEDUCA = "MEDUCA"
    MINSA = "MINSA"
    EMPRESA_PRIVADA = "EMPRESA_PRIVADA"
    BANCO_NACIONAL = "BANCO_NACIONAL"
    CAJA_AHORROS = "CAJA_AHORROS"
    OTROS_BANCOS = "OTROS_BANCOS"
    COOPERATIVAS = "COOPERATIVAS"
    GARANTIA_HIPOTECARIA = "GARANTIA_HIPOTECARIA"
    GARANTIA_VEHICULAR = "GARANTIA_VEHICULAR"
    GARANTIA_FIDUCIARIA = "GARANTIA_FIDUCIARIA"
    GARANTIA_PRENDARIA = "GARANTIA_PRENDARIA"
    AVAL_SOLIDARIO = "AVAL_SOLIDARIO"
    SIN_DESCUENTO = "SIN_DESCUENTO"


class ModalidadPago(str, Enum):
    """Modalidades de pago disponibles"""
    DESCUENTO_DIRECTO = "DESCUENTO_DIRECTO"
    DEBITO_AUTOMATICO = "DEBITO_AUTOMATICO"
    VENTANILLA = "VENTANILLA"
    TRANSFERENCIA = "TRANSFERENCIA"
    CHEQUE = "CHEQUE"
    EFECTIVO = "EFECTIVO"


class EstadoPrestamo(str, Enum):
    """Estados del préstamo"""
    SOLICITUD = "SOLICITUD"
    EVALUACION = "EVALUACION"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    DESEMBOLSADO = "DESEMBOLSADO"
    VIGENTE = "VIGENTE"
    MORA = "MORA"
    CANCELADO = "CANCELADO"
    REFINANCIADO = "REFINANCIADO"
    CASTIGADO = "CASTIGADO"


class DescuentoDirectoInfo(BaseModel):
    """Información específica para descuento directo"""
    entidad_empleadora: Optional[str] = Field(None, description="Entidad donde trabaja")
    numero_empleado: Optional[str] = Field(None, description="Número de empleado")
    cedula_empleado: Optional[str] = Field(None, description="Cédula del empleado")
    cargo_empleado: Optional[str] = Field(None, description="Cargo del empleado")
    salario_base: Optional[Decimal] = Field(None, description="Salario base para descuento")
    contacto_rrhh: Optional[str] = Field(None, description="Contacto de RRHH")
    telefono_rrhh: Optional[str] = Field(None, description="Teléfono de RRHH")
    email_rrhh: Optional[str] = Field(None, description="Email de RRHH")
    
    @validator('salario_base')
    def validar_salario_base(cls, v):
        if v is not None and v <= 0:
            raise ValueError('El salario base debe ser mayor a cero')
        return v


class PrestamoBase(BaseModel):
    """Esquema base para préstamos"""
    tipo_prestamo: TipoPrestamo = Field(TipoPrestamo.PERSONAL, description="Tipo de préstamo")
    tipo_descuento_directo: Optional[TipoDescuentoDirecto] = Field(None, description="Tipo de descuento directo")
    modalidad_pago: ModalidadPago = Field(ModalidadPago.VENTANILLA, description="Modalidad de pago")
    
    monto: Decimal = Field(..., gt=0, description="Monto del préstamo")
    plazo: int = Field(..., gt=0, le=360, description="Plazo en meses (máximo 30 años)")
    tasa_interes: Decimal = Field(..., gt=0, le=100, description="Tasa de interés anual")
    cuota_mensual: Decimal = Field(..., gt=0, description="Cuota mensual")
    
    garantia: Optional[str] = Field(None, description="Descripción de la garantía")
    proposito: Optional[str] = Field(None, description="Propósito del préstamo")
    observaciones: Optional[str] = Field(None, description="Observaciones adicionales")
    
    porcentaje_descuento_maximo: Decimal = Field(Decimal('30.00'), description="% máximo de descuento del salario")
    
    @validator('porcentaje_descuento_maximo')
    def validar_porcentaje_descuento(cls, v):
        if v > 30:
            raise ValueError('El porcentaje de descuento no puede exceder el 30% según la ley panameña')
        return v


class PrestamoCreate(PrestamoBase):
    """Esquema para crear un préstamo"""
    cliente_id: str = Field(..., description="ID del cliente")
    sucursal_id: str = Field(..., description="ID de la sucursal")
    
    fecha_inicio: date = Field(..., description="Fecha de inicio del préstamo")
    
    # Información de descuento directo (opcional)
    descuento_directo_info: Optional[DescuentoDirectoInfo] = None
    
    @validator('fecha_inicio')
    def validar_fecha_inicio(cls, v):
        if v < date.today():
            raise ValueError('La fecha de inicio no puede ser anterior a hoy')
        return v


class PrestamoUpdate(BaseModel):
    """Esquema para actualizar un préstamo"""
    tipo_descuento_directo: Optional[TipoDescuentoDirecto] = None
    modalidad_pago: Optional[ModalidadPago] = None
    
    tasa_interes: Optional[Decimal] = Field(None, gt=0, le=100)
    cuota_mensual: Optional[Decimal] = Field(None, gt=0)
    
    garantia: Optional[str] = None
    proposito: Optional[str] = None
    observaciones: Optional[str] = None
    
    estado: Optional[EstadoPrestamo] = None
    porcentaje_descuento_maximo: Optional[Decimal] = Field(None, le=30)
    
    # Información de descuento directo
    descuento_directo_info: Optional[DescuentoDirectoInfo] = None


class AutorizarDescuentoRequest(BaseModel):
    """Esquema para autorizar descuento directo"""
    salario_bruto: Decimal = Field(..., gt=0, description="Salario bruto del empleado")
    observaciones: Optional[str] = Field(None, description="Observaciones de la autorización")
    
    @validator('salario_bruto')
    def validar_salario_bruto(cls, v):
        if v < 500:  # Salario mínimo aproximado en Panamá
            raise ValueError('El salario bruto parece muy bajo')
        return v


class PrestamoResponse(PrestamoBase):
    """Esquema de respuesta para préstamos"""
    id: str
    numero_prestamo: Optional[str]
    cliente_id: str
    sucursal_id: str
    usuario_id: str
    
    estado: EstadoPrestamo
    fecha_inicio: datetime
    fecha_vencimiento: datetime
    
    # Cálculos financieros
    monto_total: Decimal
    monto_pagado: Decimal
    
    # Control de descuento directo
    descuento_autorizado: bool
    fecha_autorizacion_descuento: Optional[datetime]
    
    # Información de descuento directo
    descuento_directo_info: Optional[DescuentoDirectoInfo] = None
    
    # Propiedades calculadas
    saldo_pendiente: Decimal
    porcentaje_pagado: float
    dias_mora: int
    estado_mora: str
    
    # Flags de clasificación
    requiere_descuento_directo: bool
    tiene_garantia: bool
    es_empleado_publico: bool
    es_empleado_bancario: bool
    
    # Metadatos
    is_active: bool
    risk_assessment: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PrestamoListResponse(BaseModel):
    """Esquema de respuesta para lista de préstamos"""
    id: str
    numero_prestamo: Optional[str]
    cliente_nombre: str
    tipo_prestamo: TipoPrestamo
    tipo_descuento_directo: Optional[TipoDescuentoDirecto]
    modalidad_pago: ModalidadPago
    estado: EstadoPrestamo
    monto: Decimal
    saldo_pendiente: Decimal
    cuota_mensual: Decimal
    fecha_vencimiento: datetime
    dias_mora: int
    estado_mora: str
    descuento_autorizado: bool
    created_at: datetime


class PrestamoFiltros(BaseModel):
    """Filtros para búsqueda de préstamos"""
    cliente_id: Optional[str] = None
    sucursal_id: Optional[str] = None
    tipo_prestamo: Optional[TipoPrestamo] = None
    tipo_descuento_directo: Optional[TipoDescuentoDirecto] = None
    modalidad_pago: Optional[ModalidadPago] = None
    estado: Optional[EstadoPrestamo] = None
    descuento_autorizado: Optional[bool] = None
    
    fecha_inicio_desde: Optional[date] = None
    fecha_inicio_hasta: Optional[date] = None
    fecha_vencimiento_desde: Optional[date] = None
    fecha_vencimiento_hasta: Optional[date] = None
    
    monto_minimo: Optional[Decimal] = None
    monto_maximo: Optional[Decimal] = None
    
    solo_con_mora: Optional[bool] = None
    dias_mora_minimo: Optional[int] = None


class EstadisticasDescuentoDirecto(BaseModel):
    """Estadísticas de descuento directo"""
    total_prestamos: int
    total_con_descuento_directo: int
    porcentaje_descuento_directo: float
    
    por_tipo_descuento: dict
    por_modalidad_pago: dict
    por_estado: dict
    
    monto_total_descuento_directo: Decimal
    promedio_cuota_descuento_directo: Decimal
    
    empleados_publicos: int
    empleados_bancarios: int
    con_garantia: int
    
    autorizados: int
    pendientes_autorizacion: int


class ValidacionDescuentoResponse(BaseModel):
    """Respuesta de validación de descuento"""
    es_valido: bool
    mensaje: str
    porcentaje_descuento: float
    salario_bruto: Decimal
    cuota_mensual: Decimal
    margen_disponible: Decimal

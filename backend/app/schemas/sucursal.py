"""
Esquemas Pydantic para sucursales y teléfonos
"""
from datetime import time
from decimal import Decimal
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field, validator
from uuid import UUID


class SucursalTelefonoBase(BaseModel):
    """Esquema base para teléfonos de sucursales"""
    numero: str = Field(..., min_length=7, max_length=20, description="Número telefónico")
    tipo: str = Field(default="principal", description="Tipo: principal, secundario, fax, movil, whatsapp")
    extension: Optional[str] = Field(None, max_length=10, description="Extensión telefónica")
    descripcion: Optional[str] = Field(None, max_length=255, description="Descripción del teléfono")
    is_active: bool = Field(default=True)
    is_whatsapp: bool = Field(default=False)
    is_publico: bool = Field(default=True, description="Si se muestra públicamente")

    @validator('tipo')
    def validate_tipo(cls, v):
        tipos_validos = ['principal', 'secundario', 'fax', 'movil', 'whatsapp', 'emergencia']
        if v not in tipos_validos:
            raise ValueError(f'Tipo debe ser uno de: {", ".join(tipos_validos)}')
        return v

    @validator('numero')
    def validate_numero(cls, v):
        # Remover espacios y caracteres especiales para validación
        numero_limpio = ''.join(filter(str.isdigit, v))
        if len(numero_limpio) < 7:
            raise ValueError('El número debe tener al menos 7 dígitos')
        return v


class SucursalTelefonoCreate(SucursalTelefonoBase):
    """Esquema para crear teléfonos de sucursales"""
    pass


class SucursalTelefonoUpdate(BaseModel):
    """Esquema para actualizar teléfonos de sucursales"""
    numero: Optional[str] = Field(None, min_length=7, max_length=20)
    tipo: Optional[str] = None
    extension: Optional[str] = Field(None, max_length=10)
    descripcion: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_whatsapp: Optional[bool] = None
    is_publico: Optional[bool] = None


class SucursalTelefonoResponse(SucursalTelefonoBase):
    """Esquema de respuesta para teléfonos de sucursales"""
    id: UUID
    sucursal_id: UUID
    numero_formateado: str = Field(..., description="Número formateado con extensión")
    
    class Config:
        from_attributes = True


class SucursalBase(BaseModel):
    """Esquema base para sucursales"""
    codigo: str = Field(..., min_length=2, max_length=50, description="Código único de sucursal")
    nombre: str = Field(..., min_length=1, max_length=255, description="Nombre de la sucursal")
    direccion: Optional[str] = Field(None, description="Dirección física")
    
    # Geolocalización
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90, description="Latitud en grados decimales")
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180, description="Longitud en grados decimales")
    altitud: Optional[Decimal] = Field(None, description="Altitud en metros")
    
    # Ubicación adicional
    ciudad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=20)
    pais: str = Field(default="Panamá", max_length=100)
    
    # Información administrativa
    manager: Optional[str] = Field(None, max_length=255, description="Nombre del gerente")
    email_sucursal: Optional[str] = Field(None, max_length=255, description="Email de la sucursal")
    horario_apertura: Optional[time] = Field(None, description="Hora de apertura")
    horario_cierre: Optional[time] = Field(None, description="Hora de cierre")
    dias_operacion: Optional[str] = Field(default="Lunes-Viernes", max_length=50)
    
    # Configuración
    is_active: bool = Field(default=True)
    permite_prestamos: bool = Field(default=True)
    limite_prestamo_diario: Optional[Decimal] = Field(None, ge=0, description="Límite de préstamos diarios")

    @validator('codigo')
    def validate_codigo(cls, v):
        if not v.isalnum():
            raise ValueError('El código debe ser alfanumérico')
        return v.upper()

    @validator('email_sucursal')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('Email inválido')
        return v


class SucursalCreate(SucursalBase):
    """Esquema para crear sucursales"""
    telefonos: Optional[List[SucursalTelefonoCreate]] = Field(default=[], description="Teléfonos de la sucursal")


class SucursalUpdate(BaseModel):
    """Esquema para actualizar sucursales"""
    codigo: Optional[str] = Field(None, min_length=2, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    direccion: Optional[str] = None
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180)
    altitud: Optional[Decimal] = None
    ciudad: Optional[str] = Field(None, max_length=100)
    provincia: Optional[str] = Field(None, max_length=100)
    codigo_postal: Optional[str] = Field(None, max_length=20)
    pais: Optional[str] = Field(None, max_length=100)
    manager: Optional[str] = Field(None, max_length=255)
    email_sucursal: Optional[str] = Field(None, max_length=255)
    horario_apertura: Optional[time] = None
    horario_cierre: Optional[time] = None
    dias_operacion: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None
    permite_prestamos: Optional[bool] = None
    limite_prestamo_diario: Optional[Decimal] = Field(None, ge=0)


class SucursalResponse(SucursalBase):
    """Esquema de respuesta para sucursales"""
    id: UUID
    coordenadas: Optional[Tuple[float, float]] = Field(None, description="Coordenadas (latitud, longitud)")
    ubicacion_completa: Optional[str] = Field(None, description="Dirección completa formateada")
    telefonos: List[SucursalTelefonoResponse] = Field(default=[], description="Teléfonos de la sucursal")
    
    class Config:
        from_attributes = True


class SucursalListResponse(BaseModel):
    """Esquema de respuesta para lista de sucursales"""
    sucursales: List[SucursalResponse]
    total: int
    page: int
    size: int
    pages: int


class SucursalGeolocation(BaseModel):
    """Esquema para datos de geolocalización"""
    latitud: Decimal = Field(..., ge=-90, le=90)
    longitud: Decimal = Field(..., ge=-180, le=180)
    altitud: Optional[Decimal] = None
    precision: Optional[float] = Field(None, description="Precisión en metros")


class SucursalDistancia(SucursalResponse):
    """Esquema para sucursales con distancia calculada"""
    distancia_km: Optional[float] = Field(None, description="Distancia en kilómetros")
    tiempo_estimado_min: Optional[int] = Field(None, description="Tiempo estimado en minutos")


class SucursalHorarios(BaseModel):
    """Esquema para horarios de sucursal"""
    horario_apertura: time
    horario_cierre: time
    dias_operacion: str
    esta_abierta: bool = Field(..., description="Si está abierta actualmente")
    proxima_apertura: Optional[str] = Field(None, description="Próxima apertura si está cerrada")


class SucursalEstadisticas(BaseModel):
    """Esquema para estadísticas de sucursal"""
    total_usuarios: int
    total_prestamos_activos: int
    total_prestamos_mes: int
    monto_prestado_mes: Decimal
    tasa_morosidad: float
    promedio_satisfaccion: Optional[float] = None

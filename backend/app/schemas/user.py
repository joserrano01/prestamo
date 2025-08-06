"""
Esquemas Pydantic para usuarios
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class UsuarioEmailBase(BaseModel):
    """Esquema base para emails de usuario"""
    email: EmailStr
    tipo: str = Field(default="secundario", description="Tipo de email: principal, secundario, trabajo, personal")
    is_principal: bool = Field(default=False, description="Si es el email principal del usuario")
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)


class UsuarioEmailCreate(UsuarioEmailBase):
    """Esquema para crear un email de usuario"""
    pass


class UsuarioEmailUpdate(BaseModel):
    """Esquema para actualizar un email de usuario"""
    email: Optional[EmailStr] = None
    tipo: Optional[str] = None
    is_principal: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None


class UsuarioEmailResponse(UsuarioEmailBase):
    """Esquema de respuesta para emails de usuario"""
    id: UUID
    usuario_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UsuarioBase(BaseModel):
    """Esquema base para usuarios"""
    codigo_usuario: str = Field(..., min_length=3, max_length=50, description="Código único del usuario")
    codigo_empleado: Optional[str] = Field(None, min_length=3, max_length=50, description="Código de empleado (EMP001, EMP002, etc.)")
    nombre: str = Field(..., min_length=1, max_length=255)
    apellido: str = Field(..., min_length=1, max_length=255)
    rol: str = Field(default="employee", description="Rol del usuario: admin, manager, employee")
    sucursal_id: Optional[UUID] = None
    is_active: bool = Field(default=True)


class UsuarioCreate(UsuarioBase):
    """Esquema para crear un usuario"""
    password: str = Field(..., min_length=8, description="Contraseña del usuario")
    email_principal: EmailStr = Field(..., description="Email principal del usuario")
    emails_adicionales: Optional[List[UsuarioEmailCreate]] = Field(default=[], description="Emails adicionales del usuario")


class UsuarioUpdate(BaseModel):
    """Esquema para actualizar un usuario"""
    codigo_usuario: Optional[str] = Field(None, min_length=3, max_length=50)
    codigo_empleado: Optional[str] = Field(None, min_length=3, max_length=50)
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    apellido: Optional[str] = Field(None, min_length=1, max_length=255)
    rol: Optional[str] = None
    sucursal_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class UsuarioPasswordUpdate(BaseModel):
    """Esquema para actualizar contraseña"""
    current_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")


class UsuarioResponse(UsuarioBase):
    """Esquema de respuesta para usuarios"""
    id: UUID
    email_principal: Optional[str] = Field(None, description="Email principal calculado dinámicamente")
    is_verified: bool
    last_login: Optional[datetime]
    two_fa_enabled: bool
    created_at: datetime
    updated_at: datetime
    emails: List[UsuarioEmailResponse] = Field(default=[], description="Todos los emails del usuario")

    class Config:
        from_attributes = True


class UsuarioLogin(BaseModel):
    """Esquema para login de usuario"""
    identifier: str = Field(..., description="Email principal o código de usuario")
    password: str = Field(..., description="Contraseña del usuario")
    sucursal_id: UUID = Field(..., description="ID de la sucursal")
    totp_code: Optional[str] = Field(None, description="Código TOTP para 2FA")


class UsuarioLoginResponse(BaseModel):
    """Esquema de respuesta para login"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UsuarioResponse


class UsuarioListResponse(BaseModel):
    """Esquema de respuesta para lista de usuarios"""
    users: List[UsuarioResponse]
    total: int
    page: int
    size: int
    pages: int

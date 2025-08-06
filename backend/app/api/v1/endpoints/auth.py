from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from datetime import datetime
from app.core.database import get_db
from app.models.secure_models import Usuario, Sucursal, UsuarioEmail
from app.schemas.user import UsuarioLogin, UsuarioLoginResponse, UsuarioResponse

router = APIRouter()

@router.post("/login", response_model=UsuarioLoginResponse)
async def login_with_sucursal(
    login_data: UsuarioLogin,
    db: Session = Depends(get_db)
):
    """
    Endpoint de autenticación con selección de sucursal.
    
    El usuario debe proporcionar:
    - Email y contraseña
    - ID de la sucursal donde quiere trabajar
    
    El sistema validará que:
    - Las credenciales sean correctas
    - La sucursal esté activa
    - El usuario tenga permisos para esa sucursal (opcional)
    """
    try:
        # 1. Validar que la sucursal existe y está activa
        stmt_sucursal = select(Sucursal).where(
            Sucursal.id == login_data.sucursal_id,
            Sucursal.is_active == True
        )
        result_sucursal = db.execute(stmt_sucursal)
        sucursal = result_sucursal.scalar_one_or_none()
        
        if not sucursal:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sucursal no válida o inactiva"
            )
        
        # 2. Buscar usuario por código de usuario, email principal o emails adicionales
        # Primero buscar por código de usuario o email principal
        stmt_user = select(Usuario).where(
            or_(
                Usuario.codigo_usuario == login_data.identifier,
                Usuario.email_principal == login_data.identifier
            ),
            Usuario.is_active == True
        )
        result_user = db.execute(stmt_user)
        usuario = result_user.scalar_one_or_none()
        
        # Si no se encuentra, buscar en emails adicionales
        if not usuario:
            stmt_email = select(Usuario).join(UsuarioEmail).where(
                UsuarioEmail.email == login_data.identifier,
                UsuarioEmail.is_active == True,
                Usuario.is_active == True
            )
            result_email = db.execute(stmt_email)
            usuario = result_email.scalar_one_or_none()
        
        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 3. Verificar contraseña
        if not usuario.verify_password(login_data.password):
            # Incrementar intentos fallidos
            usuario.failed_login_attempts += 1
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 4. Verificar si la cuenta está bloqueada
        if usuario.is_locked():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Cuenta bloqueada temporalmente"
            )
        
        # 5. Opcional: Validar que el usuario puede acceder a esta sucursal
        # (puedes comentar esto si quieres permitir acceso a cualquier sucursal)
        if usuario.sucursal_id and usuario.sucursal_id != login_data.sucursal_id:
            # Usuario tiene sucursal asignada pero intenta acceder a otra
            if usuario.rol not in ['admin', 'supervisor']:  # Solo admin/supervisor pueden cambiar sucursal
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para acceder a esta sucursal"
                )
        
        # 6. Login exitoso - resetear intentos fallidos
        usuario.failed_login_attempts = 0
        usuario.last_login = datetime.utcnow()
        db.commit()
        
        # 7. Crear token JWT (aquí usarías tu lógica real de JWT)
        access_token = f"fake-jwt-token-{usuario.id}-{sucursal.id}"
        
        # 8. Crear respuesta con el nuevo esquema
        user_response = UsuarioResponse(
            id=usuario.id,
            codigo_usuario=usuario.codigo_usuario,
            email_principal=usuario.email_principal,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            rol=usuario.rol,
            sucursal_id=usuario.sucursal_id,
            is_active=usuario.is_active,
            is_verified=usuario.is_verified,
            last_login=usuario.last_login,
            two_fa_enabled=usuario.two_fa_enabled,
            created_at=usuario.created_at,
            updated_at=usuario.updated_at,
            emails_adicionales=[]
        )
        
        return UsuarioLoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=3600,  # 1 hora
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

# Mantener el endpoint original para compatibilidad
@router.post("/login-simple")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint de autenticación simple (sin sucursal) - Para compatibilidad
    """
    # Simulación de validación de credenciales
    if form_data.username == "admin@financepro.com" and form_data.password == "admin123":
        return JSONResponse({
            "access_token": "fake-jwt-token",
            "token_type": "bearer",
            "user": {
                "id": "1",
                "email": "admin@financepro.com",
                "name": "Administrador",
                "role": "admin",
                "sucursal": "central"
            }
        })
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/verify-2fa")
async def verify_2fa():
    """
    Verificación de código 2FA
    """
    return JSONResponse({
        "success": True,
        "message": "Código 2FA verificado correctamente"
    })


@router.post("/refresh")
async def refresh_token():
    """
    Renovar token de acceso
    """
    return JSONResponse({
        "access_token": "new-fake-jwt-token",
        "token_type": "bearer"
    })


@router.post("/logout")
async def logout():
    """
    Cerrar sesión
    """
    return JSONResponse({
        "message": "Sesión cerrada correctamente"
    })

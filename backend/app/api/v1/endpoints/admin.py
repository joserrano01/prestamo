"""
Endpoints administrativos para migraciones y mantenimiento
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
from app.core.init_db import init_database, migrate_descuento_directo
from app.core.database import check_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()

class MigrationResponse(BaseModel):
    """Respuesta de migración"""
    success: bool
    message: str
    details: list[str] = []

class DatabaseStatus(BaseModel):
    """Estado de la base de datos"""
    connected: bool
    message: str

@router.get("/db-status", response_model=DatabaseStatus)
async def get_database_status():
    """
    Verificar el estado de conexión a la base de datos.
    """
    try:
        is_connected = check_db_connection()
        
        return DatabaseStatus(
            connected=is_connected,
            message="Conexión exitosa" if is_connected else "Sin conexión a la base de datos"
        )
        
    except Exception as e:
        logger.error(f"Error verificando estado de BD: {e}")
        return DatabaseStatus(
            connected=False,
            message=f"Error: {str(e)}"
        )

@router.post("/migrate", response_model=MigrationResponse)
async def run_migrations():
    """
    Ejecutar migraciones de base de datos y crear datos de prueba.
    
    Esto creará:
    - Extensiones necesarias de PostgreSQL
    - Todas las tablas del sistema
    - Sucursales de prueba: Bugaba (S01) y David (S02)
    - Usuarios de prueba para cada sucursal
    """
    try:
        logger.info("Iniciando migraciones desde endpoint...")
        
        # Ejecutar migraciones
        success = init_database()
        
        if success:
            return MigrationResponse(
                success=True,
                message="Migraciones ejecutadas exitosamente",
                details=[
                    "✅ Extensiones de PostgreSQL creadas",
                    "✅ Tablas del sistema creadas",
                    "✅ Sucursal S01 (Bugaba) creada",
                    "✅ Sucursal S02 (David) creada", 
                    "✅ Usuarios de prueba creados",
                    "📧 Emails disponibles: admin.bugaba@financepro.com, admin.david@financepro.com",
                    "🔑 Contraseña para todos: admin123"
                ]
            )
        else:
            raise Exception("Error durante la ejecución de migraciones")
            
    except Exception as e:
        logger.error(f"Error en migraciones: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando migraciones: {str(e)}"
        )

@router.post("/migrate-descuento-directo", response_model=MigrationResponse)
async def migrate_descuento_directo_endpoint():
    """
    Ejecutar migración específica para descuento directo en préstamos.
    
    Esta migración agrega:
    - Tipos ENUM para clasificación de préstamos
    - Campos de descuento directo
    - Información encriptada del empleador
    - Campos de control y autorización
    - Índices optimizados
    """
    try:
        logger.info("Ejecutando migración 003: Descuento Directo...")
        
        # Ejecutar migración específica
        success = migrate_descuento_directo()
        
        if success:
            return MigrationResponse(
                success=True,
                message="Migración de descuento directo completada exitosamente",
                details=[
                    "✅ Tipos ENUM creados (tipo_prestamo, tipo_descuento_directo, modalidad_pago, estado_prestamo)",
                    "✅ Campos de clasificación agregados",
                    "✅ Información de empleador (encriptada) agregada",
                    "✅ Campos de control de descuento agregados",
                    "✅ Números únicos de préstamo generados",
                    "✅ Índices optimizados creados",
                    "🏦 Tipos de descuento: JUBILADOS, CSS, CONTRALORÍA, BANCOS, etc.",
                    "⚖️ Cumple regulación panameña (máximo 30% del salario)"
                ]
            )
        else:
            raise Exception("Error durante la migración de descuento directo")
            
    except Exception as e:
        logger.error(f"Error en migración descuento directo: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error ejecutando migración de descuento directo: {str(e)}"
        )

@router.post("/reset-db", response_model=MigrationResponse)
async def reset_database():
    """
    ⚠️ PELIGROSO: Reiniciar completamente la base de datos.
    
    Esto eliminará TODOS los datos y recreará las tablas con datos de prueba.
    Solo usar en desarrollo.
    """
    try:
        logger.warning("🚨 REINICIANDO BASE DE DATOS - TODOS LOS DATOS SE PERDERÁN")
        
        from app.models.secure_models import Base
        from app.core.database import engine
        
        # Eliminar todas las tablas
        Base.metadata.drop_all(bind=engine)
        logger.info("Tablas eliminadas")
        
        # Recrear todo
        success = init_database()
        
        if success:
            return MigrationResponse(
                success=True,
                message="Base de datos reiniciada exitosamente",
                details=[
                    "🗑️ Todas las tablas eliminadas",
                    "✅ Base de datos recreada desde cero",
                    "✅ Datos de prueba restaurados",
                    "🏢 Sucursales: S01 (Bugaba), S02 (David)",
                    "👥 Usuarios de prueba recreados"
                ]
            )
        else:
            raise Exception("Error durante el reinicio de la base de datos")
            
    except Exception as e:
        logger.error(f"Error reiniciando BD: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reiniciando base de datos: {str(e)}"
        )

@router.get("/sample-data")
async def get_sample_data_info():
    """
    Obtener información sobre los datos de prueba disponibles.
    """
    return {
        "sucursales": [
            {
                "codigo": "S01",
                "nombre": "Sucursal Bugaba",
                "ubicacion": "Bugaba, Chiriquí",
                "manager": "Ana María González"
            },
            {
                "codigo": "S02", 
                "nombre": "Sucursal David",
                "ubicacion": "David, Chiriquí",
                "manager": "Carlos Eduardo Mendoza"
            }
        ],
        "usuarios_prueba": [
            {
                "email": "admin.bugaba@financepro.com",
                "rol": "admin",
                "sucursal": "S01 - Bugaba"
            },
            {
                "email": "manager.bugaba@financepro.com", 
                "rol": "manager",
                "sucursal": "S01 - Bugaba"
            },
            {
                "email": "empleado.bugaba@financepro.com",
                "rol": "employee", 
                "sucursal": "S01 - Bugaba"
            },
            {
                "email": "admin.david@financepro.com",
                "rol": "admin",
                "sucursal": "S02 - David"
            },
            {
                "email": "manager.david@financepro.com",
                "rol": "manager",
                "sucursal": "S02 - David"
            },
            {
                "email": "empleado.david@financepro.com",
                "rol": "employee",
                "sucursal": "S02 - David"
            }
        ],
        "credenciales": {
            "password": "admin123",
            "nota": "Misma contraseña para todos los usuarios de prueba"
        }
    }

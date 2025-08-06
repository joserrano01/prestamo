"""
Migración 003: Agregar campos de descuento directo a préstamos

Esta migración agrega los campos necesarios para manejar diferentes tipos
de descuento directo en préstamos personales, incluyendo:
- Tipos de préstamo
- Tipos de descuento directo (jubilados, CSS, contraloría, etc.)
- Modalidades de pago
- Información de empleador para descuento directo
- Control de autorización de descuentos

Fecha: 2024-01-XX
Autor: Sistema FinancePro
"""

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import logging
import os

logger = logging.getLogger(__name__)

def get_database_url():
    """Obtener URL de la base de datos desde variables de entorno"""
    return os.getenv(
        'DATABASE_URL', 
        'postgresql://postgres:Tehwmm%lob1A9Qz0@db:5432/financepro_dev'
    )

def upgrade():
    """Aplicar migración: agregar campos de descuento directo a préstamos"""
    
    # Crear conexión a la base de datos
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            logger.info("Iniciando migración 003: Agregar campos de descuento directo a préstamos")
            
            # 1. Crear tipos ENUM para préstamos
            logger.info("Creando tipos ENUM...")
            
            # Tipo de préstamo
            db.execute(text("""
                CREATE TYPE tipo_prestamo AS ENUM (
                    'PERSONAL', 'VEHICULAR', 'HIPOTECARIO', 'COMERCIAL',
                    'CONSUMO', 'EDUCATIVO', 'EMERGENCIA'
                );
            """))
            
            # Tipo de descuento directo
            db.execute(text("""
                CREATE TYPE tipo_descuento_directo AS ENUM (
                    'JUBILADOS', 'PAGOS_VOLUNTARIOS', 'CONTRALORIA', 'CSS',
                    'MEF', 'MEDUCA', 'MINSA', 'EMPRESA_PRIVADA',
                    'BANCO_NACIONAL', 'CAJA_AHORROS', 'OTROS_BANCOS', 'COOPERATIVAS',
                    'GARANTIA_HIPOTECARIA', 'GARANTIA_VEHICULAR', 'GARANTIA_FIDUCIARIA',
                    'GARANTIA_PRENDARIA', 'AVAL_SOLIDARIO', 'SIN_DESCUENTO'
                );
            """))
            
            # Modalidad de pago
            db.execute(text("""
                CREATE TYPE modalidad_pago AS ENUM (
                    'DESCUENTO_DIRECTO', 'DEBITO_AUTOMATICO', 'VENTANILLA',
                    'TRANSFERENCIA', 'CHEQUE', 'EFECTIVO'
                );
            """))
            
            # Estado de préstamo
            db.execute(text("""
                CREATE TYPE estado_prestamo AS ENUM (
                    'SOLICITUD', 'EVALUACION', 'APROBADO', 'RECHAZADO',
                    'DESEMBOLSADO', 'VIGENTE', 'MORA', 'CANCELADO',
                    'REFINANCIADO', 'CASTIGADO'
                );
            """))
            
            # 2. Agregar nuevas columnas a la tabla prestamos
            logger.info("Agregando nuevas columnas a prestamos...")
            
            # Clasificación del préstamo
            db.execute(text("""
                ALTER TABLE prestamos 
                ADD COLUMN tipo_prestamo tipo_prestamo NOT NULL DEFAULT 'PERSONAL',
                ADD COLUMN tipo_descuento_directo tipo_descuento_directo,
                ADD COLUMN modalidad_pago modalidad_pago NOT NULL DEFAULT 'VENTANILLA';
            """))
            
            # Número único de préstamo
            db.execute(text("""
                ALTER TABLE prestamos 
                ADD COLUMN numero_prestamo VARCHAR(50) UNIQUE;
            """))
            
            # Información de descuento directo (encriptada)
            db.execute(text("""
                ALTER TABLE prestamos 
                ADD COLUMN entidad_empleadora VARCHAR(500),
                ADD COLUMN numero_empleado VARCHAR(500),
                ADD COLUMN cedula_empleado VARCHAR(500),
                ADD COLUMN cargo_empleado VARCHAR(500),
                ADD COLUMN salario_base VARCHAR(500),
                ADD COLUMN contacto_rrhh VARCHAR(500),
                ADD COLUMN telefono_rrhh VARCHAR(500),
                ADD COLUMN email_rrhh VARCHAR(500);
            """))
            
            # Campos adicionales
            db.execute(text("""
                ALTER TABLE prestamos 
                ADD COLUMN observaciones TEXT,
                ADD COLUMN descuento_autorizado BOOLEAN NOT NULL DEFAULT FALSE,
                ADD COLUMN fecha_autorizacion_descuento TIMESTAMP,
                ADD COLUMN porcentaje_descuento_maximo NUMERIC(5,2) NOT NULL DEFAULT 30.00;
            """))
            
            # 3. Actualizar el campo estado para usar el nuevo ENUM
            logger.info("Actualizando campo estado...")
            
            # Primero, mapear estados existentes
            db.execute(text("""
                UPDATE prestamos 
                SET estado = CASE 
                    WHEN estado = 'pendiente' THEN 'SOLICITUD'
                    WHEN estado = 'aprobado' THEN 'APROBADO'
                    WHEN estado = 'activo' THEN 'VIGENTE'
                    WHEN estado = 'pagado' THEN 'CANCELADO'
                    WHEN estado = 'mora' THEN 'MORA'
                    ELSE 'SOLICITUD'
                END;
            """))
            
            # Cambiar tipo de columna
            db.execute(text("""
                ALTER TABLE prestamos 
                ALTER COLUMN estado TYPE estado_prestamo 
                USING estado::estado_prestamo;
            """))
            
            # 4. Crear índices para optimizar consultas
            logger.info("Creando índices...")
            
            db.execute(text("CREATE INDEX idx_prestamo_numero ON prestamos (numero_prestamo);"))
            db.execute(text("CREATE INDEX idx_prestamo_tipo ON prestamos (tipo_prestamo);"))
            db.execute(text("CREATE INDEX idx_prestamo_descuento_directo ON prestamos (tipo_descuento_directo);"))
            db.execute(text("CREATE INDEX idx_prestamo_modalidad_pago ON prestamos (modalidad_pago);"))
            db.execute(text("CREATE INDEX idx_prestamo_descuento_autorizado ON prestamos (descuento_autorizado);"))
            db.execute(text("CREATE INDEX idx_prestamo_sucursal_estado ON prestamos (sucursal_id, estado);"))
            db.execute(text("CREATE INDEX idx_prestamo_tipo_estado ON prestamos (tipo_prestamo, estado);"))
            
            # 5. Generar números de préstamo para registros existentes
            logger.info("Generando números de préstamo para registros existentes...")
            
            db.execute(text("""
                UPDATE prestamos 
                SET numero_prestamo = CONCAT(
                    SUBSTRING(tipo_prestamo::text, 1, 3), '-',
                    COALESCE((SELECT codigo FROM sucursales WHERE id = prestamos.sucursal_id), '001'), '-',
                    EXTRACT(YEAR FROM created_at), '-',
                    LPAD((ROW_NUMBER() OVER (ORDER BY created_at))::text, 4, '0')
                )
                WHERE numero_prestamo IS NULL;
            """))
            
            db.commit()
            logger.info("Migración 003 completada exitosamente")
            
        except Exception as e:
            logger.error(f"Error en migración 003: {str(e)}")
            db.rollback()
            raise

def downgrade():
    """Revertir migración: eliminar campos de descuento directo"""
    
    # Crear conexión a la base de datos
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            logger.info("Revirtiendo migración 003...")
            
            # Eliminar índices
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_numero;"))
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_tipo;"))
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_descuento_directo;"))
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_modalidad_pago;"))
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_descuento_autorizado;"))
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_sucursal_estado;"))
            db.execute(text("DROP INDEX IF EXISTS idx_prestamo_tipo_estado;"))
            
            # Revertir campo estado a VARCHAR
            db.execute(text("""
                ALTER TABLE prestamos 
                ALTER COLUMN estado TYPE VARCHAR(20) 
                USING CASE 
                    WHEN estado = 'SOLICITUD' THEN 'pendiente'
                    WHEN estado = 'APROBADO' THEN 'aprobado'
                    WHEN estado = 'VIGENTE' THEN 'activo'
                    WHEN estado = 'CANCELADO' THEN 'pagado'
                    WHEN estado = 'MORA' THEN 'mora'
                    ELSE 'pendiente'
                END;
            """))
            
            # Eliminar columnas agregadas
            db.execute(text("""
                ALTER TABLE prestamos 
                DROP COLUMN IF EXISTS tipo_prestamo,
                DROP COLUMN IF EXISTS tipo_descuento_directo,
                DROP COLUMN IF EXISTS modalidad_pago,
                DROP COLUMN IF EXISTS numero_prestamo,
                DROP COLUMN IF EXISTS entidad_empleadora,
                DROP COLUMN IF EXISTS numero_empleado,
                DROP COLUMN IF EXISTS cedula_empleado,
                DROP COLUMN IF EXISTS cargo_empleado,
                DROP COLUMN IF EXISTS salario_base,
                DROP COLUMN IF EXISTS contacto_rrhh,
                DROP COLUMN IF EXISTS telefono_rrhh,
                DROP COLUMN IF EXISTS email_rrhh,
                DROP COLUMN IF EXISTS observaciones,
                DROP COLUMN IF EXISTS descuento_autorizado,
                DROP COLUMN IF EXISTS fecha_autorizacion_descuento,
                DROP COLUMN IF EXISTS porcentaje_descuento_maximo;
            """))
            
            # Eliminar tipos ENUM
            db.execute(text("DROP TYPE IF EXISTS tipo_prestamo;"))
            db.execute(text("DROP TYPE IF EXISTS tipo_descuento_directo;"))
            db.execute(text("DROP TYPE IF EXISTS modalidad_pago;"))
            db.execute(text("DROP TYPE IF EXISTS estado_prestamo;"))
            
            db.commit()
            logger.info("Migración 003 revertida exitosamente")
            
        except Exception as e:
            logger.error(f"Error revirtiendo migración 003: {str(e)}")
            db.rollback()
            raise

if __name__ == "__main__":
    # Ejecutar migración directamente
    upgrade()

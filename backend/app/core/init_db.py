"""
Script de inicialización de base de datos con migraciones y datos de prueba
"""
import logging
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from app.core.database import SessionLocal, engine
from app.models.secure_models import Base, Sucursal, SucursalTelefono, Usuario, UsuarioEmail
from app.core.security import hash_password
from app.core.config import settings
import uuid

logger = logging.getLogger(__name__)

def create_tables():
    """Crear todas las tablas usando SQLAlchemy"""
    try:
        logger.info("Creando tablas de base de datos...")
        logger.info(f"Usando engine: {engine.url}")
        
        # Verificar conexión
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            logger.info(f"Conectado a base de datos: {db_info[0]} como usuario: {db_info[1]}")
        
        # Crear tablas
        logger.info("Ejecutando Base.metadata.create_all()...")
        Base.metadata.create_all(bind=engine)
        
        # Verificar qué tablas se crearon
        with engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"Tablas creadas: {tables}")
        
        logger.info("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando tablas: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def create_extensions():
    """Crear extensiones necesarias de PostgreSQL"""
    try:
        db = SessionLocal()
        logger.info("Creando extensiones de PostgreSQL...")
        
        # Crear extensión uuid-ossp
        db.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        db.commit()
        db.close()
        
        logger.info("✅ Extensiones creadas exitosamente")
        return True
    except Exception as e:
        logger.error(f"❌ Error creando extensiones: {e}")
        return False

def create_sample_sucursales():
    """Crear sucursales de prueba: Bugaba y David"""
    try:
        db = SessionLocal()
        logger.info("Creando sucursales de prueba...")
        
        # Verificar si ya existen sucursales
        existing_sucursales = db.query(Sucursal).count()
        if existing_sucursales > 0:
            logger.info("Las sucursales ya existen, omitiendo creación")
            db.close()
            return True
        
        # Crear sucursal de Bugaba
        sucursal_bugaba = Sucursal(
            id=uuid.uuid4(),
            codigo="S01",
            nombre="Sucursal Bugaba",
            direccion="Calle Principal, Bugaba, Chiriquí",
            latitud=8.4833,
            longitud=-82.6167,
            ciudad="Bugaba",
            provincia="Chiriquí",
            pais="Panamá",
            manager="Ana María González",
            email_sucursal="bugaba@financepro.com",
            is_active=True
        )
        
        # Crear sucursal de David
        sucursal_david = Sucursal(
            id=uuid.uuid4(),
            codigo="S02", 
            nombre="Sucursal David",
            direccion="Av. Bolívar, David, Chiriquí",
            latitud=8.4333,
            longitud=-82.4333,
            ciudad="David",
            provincia="Chiriquí",
            pais="Panamá",
            manager="Carlos Eduardo Mendoza",
            email_sucursal="david@financepro.com",
            is_active=True
        )
        
        db.add(sucursal_bugaba)
        db.add(sucursal_david)
        db.commit()
        
        # Crear teléfonos para Sucursal Bugaba
        telefonos_bugaba = [
            SucursalTelefono(
                sucursal_id=sucursal_bugaba.id,
                numero="507-775-1234",
                tipo="principal",
                descripcion="Teléfono principal",
                es_publico=True
            ),
            SucursalTelefono(
                sucursal_id=sucursal_bugaba.id,
                numero="507-775-1235",
                tipo="secundario",
                descripcion="Línea secundaria",
                es_publico=True
            )
        ]
        
        # Crear teléfonos para Sucursal David
        telefonos_david = [
            SucursalTelefono(
                sucursal_id=sucursal_david.id,
                numero="507-775-5678",
                tipo="principal",
                descripcion="Teléfono principal",
                es_publico=True
            ),
            SucursalTelefono(
                sucursal_id=sucursal_david.id,
                numero="507-775-5679",
                tipo="secundario",
                descripcion="Línea secundaria",
                es_publico=True
            )
        ]
        
        # Agregar todos los teléfonos
        for telefono in telefonos_bugaba + telefonos_david:
            db.add(telefono)
        db.commit()
        
        logger.info("✅ Sucursales creadas:")
        logger.info(f"   - {sucursal_bugaba.codigo}: {sucursal_bugaba.nombre} ({len(telefonos_bugaba)} teléfonos)")
        logger.info(f"   - {sucursal_david.codigo}: {sucursal_david.nombre} ({len(telefonos_david)} teléfonos)")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando sucursales: {e}")
        return False

def create_sample_users():
    """Crear usuarios de prueba para cada sucursal con emails separados"""
    try:
        db = SessionLocal()
        logger.info("Creando usuarios de prueba...")
        
        # Verificar si ya existen usuarios
        existing_users = db.query(Usuario).count()
        if existing_users > 0:
            logger.info("Los usuarios ya existen, omitiendo creación")
            db.close()
            return True
        
        # Obtener sucursales
        sucursal_bugaba = db.query(Sucursal).filter(Sucursal.codigo == "S01").first()
        sucursal_david = db.query(Sucursal).filter(Sucursal.codigo == "S02").first()
        
        if not sucursal_bugaba or not sucursal_david:
            logger.error("No se encontraron las sucursales para crear usuarios")
            return False
        
        # Contraseña por defecto: admin123
        password_hash = hash_password("admin123")
        
        # Definir usuarios con sus emails
        usuarios_data = [
            # Usuarios Bugaba
            {
                "codigo_usuario": "ADM001",
                "codigo_empleado": "EMP001",
                "nombre": "José",
                "apellido": "Serrano",
                "rol": "admin",
                "sucursal_id": sucursal_bugaba.id,
                "email_principal": "admin.bugaba@financepro.com",
                "emails_adicionales": ["joseserrano01@gmail.com"]
            },
            {
                "codigo_usuario": "MGR001",
                "codigo_empleado": "EMP002",
                "nombre": "Ana María",
                "apellido": "González",
                "rol": "manager",
                "sucursal_id": sucursal_bugaba.id,
                "email_principal": "manager.bugaba@financepro.com",
                "emails_adicionales": ["ana.gonzalez@financepro.com"]
            },
            {
                "codigo_usuario": "EMP001",
                "codigo_empleado": "EMP003",
                "nombre": "José Luis",
                "apellido": "Herrera",
                "rol": "employee",
                "sucursal_id": sucursal_bugaba.id,
                "email_principal": "empleado.bugaba@financepro.com",
                "emails_adicionales": ["jose.herrera@financepro.com"]
            },
            # Usuarios David
            {
                "codigo_usuario": "ADM002",
                "codigo_empleado": "EMP004",
                "nombre": "Carlos",
                "apellido": "Mendoza",
                "rol": "admin",
                "sucursal_id": sucursal_david.id,
                "email_principal": "admin.david@financepro.com",
                "emails_adicionales": ["carlos.mendoza@financepro.com"]
            },
            {
                "codigo_usuario": "MGR002",
                "codigo_empleado": "EMP005",
                "nombre": "María Elena",
                "apellido": "Rodríguez",
                "rol": "manager",
                "sucursal_id": sucursal_david.id,
                "email_principal": "manager.david@financepro.com",
                "emails_adicionales": ["maria.rodriguez@financepro.com"]
            },
            {
                "codigo_usuario": "EMP002",
                "codigo_empleado": "EMP006",
                "nombre": "Roberto",
                "apellido": "Castillo",
                "rol": "employee",
                "sucursal_id": sucursal_david.id,
                "email_principal": "empleado.david@financepro.com",
                "emails_adicionales": ["roberto.castillo@financepro.com"]
            }
        ]
        
        # Crear usuarios
        for user_data in usuarios_data:
            # Crear usuario
            usuario = Usuario(
                id=uuid.uuid4(),
                codigo_usuario=user_data["codigo_usuario"],
                codigo_empleado=user_data["codigo_empleado"],
                password_hash=password_hash,
                nombre=user_data["nombre"],
                apellido=user_data["apellido"],
                rol=user_data["rol"],
                sucursal_id=user_data["sucursal_id"],
                is_active=True,
                is_verified=True
            )
            
            db.add(usuario)
            db.commit()  # Commit para obtener el ID
            
            # Crear email principal
            email_principal = UsuarioEmail(
                usuario_id=usuario.id,
                email=user_data["email_principal"],
                is_principal=True,
                is_verified=True,
                is_active=True
            )
            db.add(email_principal)
            
            # Crear emails adicionales
            for email_adicional in user_data["emails_adicionales"]:
                email_extra = UsuarioEmail(
                    usuario_id=usuario.id,
                    email=email_adicional,
                    is_principal=False,
                    is_verified=True,
                    is_active=True
                )
                db.add(email_extra)
        
        db.commit()
        
        logger.info("✅ Usuarios creados exitosamente:")
        logger.info("   Contraseña para todos: admin123")
        logger.info("   Sucursal Bugaba:")
        for user_data in usuarios_data[:3]:  # Primeros 3 son de Bugaba
            logger.info(f"     - {user_data['codigo_usuario']}: {user_data['email_principal']} ({user_data['rol']})")
        
        logger.info("   Sucursal David:")
        for user_data in usuarios_data[3:]:  # Últimos 3 son de David
            logger.info(f"     - {user_data['codigo_usuario']}: {user_data['email_principal']} ({user_data['rol']})")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creando usuarios: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def migrate_descuento_directo():
    """Migración 003: Agregar campos de descuento directo a préstamos"""
    try:
        db = SessionLocal()
        logger.info("Ejecutando migración 003: Descuento Directo...")
        
        # Verificar si ya se ejecutó la migración
        try:
            result = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'prestamos' AND column_name = 'tipo_descuento_directo';"))
            if result.fetchone():
                logger.info("Migración 003 ya fue ejecutada, omitiendo...")
                db.close()
                return True
        except Exception:
            pass
        
        # 1. Crear tipos ENUM
        logger.info("Creando tipos ENUM para préstamos...")
        
        # Tipo de préstamo
        try:
            db.execute(text("""
                CREATE TYPE tipo_prestamo AS ENUM (
                    'PERSONAL', 'VEHICULAR', 'HIPOTECARIO', 'COMERCIAL',
                    'CONSUMO', 'EDUCATIVO', 'EMERGENCIA'
                );
            """))
        except ProgrammingError:
            logger.info("Tipo tipo_prestamo ya existe")
        
        # Tipo de descuento directo
        try:
            db.execute(text("""
                CREATE TYPE tipo_descuento_directo AS ENUM (
                    'JUBILADOS', 'PAGOS_VOLUNTARIOS', 'CONTRALORIA', 'CSS',
                    'MEF', 'MEDUCA', 'MINSA', 'EMPRESA_PRIVADA',
                    'BANCO_NACIONAL', 'CAJA_AHORROS', 'OTROS_BANCOS', 'COOPERATIVAS',
                    'GARANTIA_HIPOTECARIA', 'GARANTIA_VEHICULAR', 'GARANTIA_FIDUCIARIA',
                    'GARANTIA_PRENDARIA', 'AVAL_SOLIDARIO', 'SIN_DESCUENTO'
                );
            """))
        except ProgrammingError:
            logger.info("Tipo tipo_descuento_directo ya existe")
        
        # Modalidad de pago
        try:
            db.execute(text("""
                CREATE TYPE modalidad_pago AS ENUM (
                    'DESCUENTO_DIRECTO', 'DEBITO_AUTOMATICO', 'VENTANILLA',
                    'TRANSFERENCIA', 'CHEQUE', 'EFECTIVO'
                );
            """))
        except ProgrammingError:
            logger.info("Tipo modalidad_pago ya existe")
        
        # Estado de préstamo
        try:
            db.execute(text("""
                CREATE TYPE estado_prestamo AS ENUM (
                    'SOLICITUD', 'EVALUACION', 'APROBADO', 'RECHAZADO',
                    'DESEMBOLSADO', 'VIGENTE', 'MORA', 'CANCELADO',
                    'REFINANCIADO', 'CASTIGADO'
                );
            """))
        except ProgrammingError:
            logger.info("Tipo estado_prestamo ya existe")
        
        # 2. Verificar si la tabla prestamos existe
        result = db.execute(text("SELECT to_regclass('prestamos');"))
        table_exists = result.fetchone()[0] is not None
        
        if table_exists:
            logger.info("Agregando columnas a tabla prestamos existente...")
            
            # Agregar columnas de clasificación
            try:
                db.execute(text("""
                    ALTER TABLE prestamos 
                    ADD COLUMN IF NOT EXISTS tipo_prestamo tipo_prestamo DEFAULT 'PERSONAL',
                    ADD COLUMN IF NOT EXISTS tipo_descuento_directo tipo_descuento_directo,
                    ADD COLUMN IF NOT EXISTS modalidad_pago modalidad_pago DEFAULT 'VENTANILLA';
                """))
            except Exception as e:
                logger.warning(f"Error agregando columnas de clasificación: {e}")
            
            # Agregar número único de préstamo
            try:
                db.execute(text("""
                    ALTER TABLE prestamos 
                    ADD COLUMN IF NOT EXISTS numero_prestamo VARCHAR(50) UNIQUE;
                """))
            except Exception as e:
                logger.warning(f"Error agregando numero_prestamo: {e}")
            
            # Agregar información del empleador (encriptada)
            try:
                db.execute(text("""
                    ALTER TABLE prestamos 
                    ADD COLUMN IF NOT EXISTS entidad_empleadora TEXT,
                    ADD COLUMN IF NOT EXISTS numero_empleado TEXT,
                    ADD COLUMN IF NOT EXISTS cedula_empleado TEXT,
                    ADD COLUMN IF NOT EXISTS cargo_empleado TEXT,
                    ADD COLUMN IF NOT EXISTS salario_base TEXT,
                    ADD COLUMN IF NOT EXISTS contacto_rrhh TEXT,
                    ADD COLUMN IF NOT EXISTS telefono_rrhh TEXT,
                    ADD COLUMN IF NOT EXISTS email_rrhh TEXT;
                """))
            except Exception as e:
                logger.warning(f"Error agregando campos de empleador: {e}")
            
            # Agregar campos de control de descuento
            try:
                db.execute(text("""
                    ALTER TABLE prestamos 
                    ADD COLUMN IF NOT EXISTS descuento_autorizado BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS fecha_autorizacion_descuento TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS usuario_autorizacion_id UUID,
                    ADD COLUMN IF NOT EXISTS motivo_revocacion TEXT,
                    ADD COLUMN IF NOT EXISTS porcentaje_descuento_maximo DECIMAL(5,2) DEFAULT 30.00;
                """))
            except Exception as e:
                logger.warning(f"Error agregando campos de control: {e}")
            
            # Convertir estado existente si existe
            try:
                db.execute(text("""
                    ALTER TABLE prestamos 
                    ADD COLUMN IF NOT EXISTS estado_nuevo estado_prestamo DEFAULT 'VIGENTE';
                """))
                
                # Migrar estados existentes si hay una columna estado
                try:
                    db.execute(text("""
                        UPDATE prestamos 
                        SET estado_nuevo = CASE 
                            WHEN estado = 'active' THEN 'VIGENTE'::estado_prestamo
                            WHEN estado = 'pending' THEN 'SOLICITUD'::estado_prestamo
                            WHEN estado = 'approved' THEN 'APROBADO'::estado_prestamo
                            WHEN estado = 'rejected' THEN 'RECHAZADO'::estado_prestamo
                            WHEN estado = 'cancelled' THEN 'CANCELADO'::estado_prestamo
                            ELSE 'VIGENTE'::estado_prestamo
                        END
                        WHERE estado_nuevo IS NULL;
                    """))
                except Exception:
                    # Si no existe columna estado, usar valor por defecto
                    pass
            except Exception as e:
                logger.warning(f"Error agregando estado_nuevo: {e}")
            
            # Crear índices para optimizar consultas
            try:
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_tipo_prestamo ON prestamos(tipo_prestamo);"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_tipo_descuento ON prestamos(tipo_descuento_directo);"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_modalidad_pago ON prestamos(modalidad_pago);"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_numero ON prestamos(numero_prestamo);"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_descuento_autorizado ON prestamos(descuento_autorizado);"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_fecha_autorizacion ON prestamos(fecha_autorizacion_descuento);"))
                db.execute(text("CREATE INDEX IF NOT EXISTS idx_prestamos_estado_nuevo ON prestamos(estado_nuevo);"))
            except Exception as e:
                logger.warning(f"Error creando índices: {e}")
            
            # Generar números de préstamo para registros existentes
            try:
                result = db.execute(text("SELECT COUNT(*) FROM prestamos WHERE numero_prestamo IS NULL;"))
                count = result.fetchone()[0]
                
                if count > 0:
                    logger.info(f"Generando números de préstamo para {count} registros existentes...")
                    db.execute(text("""
                        UPDATE prestamos 
                        SET numero_prestamo = 'PER-' || COALESCE(
                            (SELECT codigo FROM sucursales WHERE id = prestamos.sucursal_id), 'S00'
                        ) || '-' || EXTRACT(YEAR FROM COALESCE(created_at, NOW())) || '-' || 
                        LPAD(ROW_NUMBER() OVER (ORDER BY created_at, id)::TEXT, 6, '0')
                        WHERE numero_prestamo IS NULL;
                    """))
            except Exception as e:
                logger.warning(f"Error generando números de préstamo: {e}")
        
        else:
            logger.info("Tabla prestamos no existe, se creará con las nuevas columnas cuando se ejecute create_tables()")
        
        db.commit()
        db.close()
        
        logger.info("✅ Migración 003 completada exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en migración 003: {e}")
        try:
            db.rollback()
            db.close()
        except:
            pass
        return False

def init_database():
    """Ejecutar todas las migraciones e inicialización"""
    logger.info("🚀 Iniciando migración de base de datos...")
    
    success = True
    
    # 1. Crear extensiones
    if not create_extensions():
        success = False
    
    # 2. Crear tablas
    if not create_tables():
        success = False
    
    # 3. Migración 003: Descuento Directo
    if not migrate_descuento_directo():
        success = False
    
    # 4. Crear datos de prueba solo en desarrollo
    if settings.CREATE_SAMPLE_DATA and settings.ENVIRONMENT == "development":
        logger.info("🧪 Creando datos de prueba para desarrollo...")
        
        # Crear sucursales de prueba
        if not create_sample_sucursales():
            success = False
        
        # Crear usuarios de prueba
        if not create_sample_users():
            success = False
    else:
        logger.info(f"⏭️  Omitiendo creación de datos de prueba (ambiente: {settings.ENVIRONMENT})")
    
    if success:
        logger.info("🎉 ¡Migración completada exitosamente!")
        logger.info("📋 Datos de acceso:")
        logger.info("   Sucursales disponibles:")
        logger.info("     - S01: Sucursal Bugaba")
        logger.info("     - S02: Sucursal David")
        logger.info("   Usuarios de prueba (contraseña: admin123):")
        logger.info("     - admin.bugaba@financepro.com")
        logger.info("     - manager.bugaba@financepro.com") 
        logger.info("     - empleado.bugaba@financepro.com")
        logger.info("     - admin.david@financepro.com")
        logger.info("     - manager.david@financepro.com")
        logger.info("     - empleado.david@financepro.com")
    else:
        logger.error("💥 Error durante la migración")
    
    return success

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    init_database()

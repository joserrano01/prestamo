#!/usr/bin/env python3
"""
Script para generar claves seguras para FinancePro

Uso:
    python generate_secrets.py                    # Generar .env completo
    python generate_secrets.py --only-secrets     # Solo mostrar claves
    python generate_secrets.py --validate         # Validar .env existente
    python generate_secrets.py --backup           # Crear backup del .env
    python generate_secrets.py --help             # Mostrar ayuda
"""

import secrets
import string
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime


def generate_secret_key(length: int = 64) -> str:
    """Genera una clave secreta segura usando caracteres URL-safe"""
    return secrets.token_urlsafe(length)


def generate_encryption_key() -> str:
    """Genera una clave de encriptación de exactamente 32 caracteres"""
    # Generar 32 caracteres alfanuméricos seguros
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def generate_password(length: int = 16) -> str:
    """Genera una contraseña segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_env_file():
    """Crea un archivo .env con valores seguros generados automáticamente"""
    
    # Generar claves seguras
    secret_key = generate_secret_key(64)
    encryption_key = generate_encryption_key()
    postgres_password = generate_password(16)
    rabbitmq_password = generate_password(16)
    meilisearch_key = generate_secret_key(32)
    
    env_content = f"""# FinancePro Backend - Variables de Entorno
# Generado automáticamente el {os.popen('date').read().strip()}
# IMPORTANTE: Mantener este archivo seguro y no compartir

# =============================================================================
# SEGURIDAD - CLAVES GENERADAS AUTOMÁTICAMENTE
# =============================================================================

# Clave secreta para JWT (64 caracteres seguros)
SECRET_KEY={secret_key}

# Clave de encriptación para datos PII (32 caracteres)
ENCRYPTION_KEY={encryption_key}

# Configuración de tokens
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# =============================================================================
# BASE DE DATOS
# =============================================================================

# URL completa de PostgreSQL
DATABASE_URL=postgresql://postgres:{postgres_password}@db:5432/financepro

# Variables individuales de PostgreSQL
POSTGRES_DB=financepro
POSTGRES_USER=postgres
POSTGRES_PASSWORD={postgres_password}

# =============================================================================
# REDIS
# =============================================================================

# URL de Redis para cache y sesiones
REDIS_URL=redis://redis:6379/0

# =============================================================================
# RABBITMQ - MENSAJERÍA ASÍNCRONA
# =============================================================================

# URL completa de RabbitMQ
RABBITMQ_URL=amqp://financepro:{rabbitmq_password}@rabbitmq:5672/financepro_vhost

# Variables individuales de RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=financepro
RABBITMQ_PASSWORD={rabbitmq_password}
RABBITMQ_VHOST=financepro_vhost

# =============================================================================
# MEILISEARCH - BÚSQUEDA DE TEXTO COMPLETO
# =============================================================================

# URL de Meilisearch
MEILISEARCH_URL=http://meilisearch:7700

# Clave maestra de Meilisearch
MEILISEARCH_MASTER_KEY={meilisearch_key}

# Prefijo para índices
MEILISEARCH_INDEX_PREFIX=financepro

# =============================================================================
# CELERY - PROCESAMIENTO ASÍNCRONO
# =============================================================================

# URLs para Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# =============================================================================
# CONFIGURACIÓN DEL SERVIDOR
# =============================================================================

# Información del proyecto
PROJECT_NAME=FinancePro API
VERSION=1.0.0
API_V1_STR=/api/v1

# Configuración del servidor
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# =============================================================================
# SEGURIDAD ADICIONAL
# =============================================================================

# Configuración de login
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
PASSWORD_MIN_LENGTH=8
REQUIRE_2FA=true
SESSION_TIMEOUT_MINUTES=60

# Configuración de auditoría
ENABLE_AUDIT_LOG=true
AUDIT_LOG_RETENTION_DAYS=365

# Configuración de encriptación
ENCRYPT_PII_DATA=true
DATA_RETENTION_DAYS=2555

# =============================================================================
# BÚSQUEDA Y PROCESAMIENTO
# =============================================================================

# Configuración de búsqueda
ENABLE_FULL_TEXT_SEARCH=true
SEARCH_RESULTS_LIMIT=50
SEARCH_HIGHLIGHT=true

# Configuración de procesamiento asíncrono
ENABLE_ASYNC_PROCESSING=true

# Configuración de notificaciones
ENABLE_NOTIFICATIONS=true
EMAIL_NOTIFICATIONS=true
SMS_NOTIFICATIONS=false

# =============================================================================
# CORS Y HOSTS
# =============================================================================

# Orígenes permitidos para CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://frontend:80

# Hosts permitidos
ALLOWED_HOSTS=*

# =============================================================================
# EMAIL (OPCIONAL)
# =============================================================================

# Configuración SMTP
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@financepro.com
EMAILS_FROM_NAME=FinancePro

# =============================================================================
# ARCHIVOS Y UPLOADS
# =============================================================================

# Configuración de archivos
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760

# =============================================================================
# LOGGING Y MONITOREO
# =============================================================================

# Nivel de logging
LOG_LEVEL=INFO

# Configuración de Sentry (opcional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_SENTRY=false

# =============================================================================
# RATE LIMITING
# =============================================================================

# Configuración de rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_LOGIN_ATTEMPTS=5
"""

    # Determinar la ruta del archivo .env
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    env_file = project_root / ".env"
    
    # Crear backup si el archivo ya existe
    if env_file.exists():
        backup_file = project_root / f".env.backup.{secrets.token_hex(4)}"
        print(f"📁 Creando backup del .env existente: {backup_file.name}")
        env_file.rename(backup_file)
    
    # Escribir el nuevo archivo .env
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Archivo .env creado exitosamente en: {env_file}")
    print("🔐 Claves de seguridad generadas:")
    print(f"   - SECRET_KEY: {secret_key[:20]}... (64 caracteres)")
    print(f"   - ENCRYPTION_KEY: {encryption_key[:10]}... (32 caracteres)")
    print(f"   - POSTGRES_PASSWORD: {postgres_password}")
    print(f"   - RABBITMQ_PASSWORD: {rabbitmq_password}")
    print(f"   - MEILISEARCH_MASTER_KEY: {meilisearch_key[:20]}...")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - Mantén este archivo .env seguro y privado")
    print("   - No compartas estas claves en repositorios públicos")
    print("   - Actualiza docker-compose.yml con las nuevas contraseñas si es necesario")


def generate_only_secrets():
    """Solo genera y muestra las claves sin crear archivo"""
    print("🔐 Claves Seguras Generadas:")
    print("=" * 40)
    
    secret_key = generate_secret_key(64)
    encryption_key = generate_encryption_key()
    postgres_password = generate_password(16)
    rabbitmq_password = generate_password(16)
    meilisearch_key = generate_secret_key(32)
    
    print(f"SECRET_KEY={secret_key}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print(f"POSTGRES_PASSWORD={postgres_password}")
    print(f"RABBITMQ_PASSWORD={rabbitmq_password}")
    print(f"MEILISEARCH_MASTER_KEY={meilisearch_key}")
    print("\n⚠️  Copia estas claves a tu archivo .env manualmente")


def validate_existing_env():
    """Valida el archivo .env existente"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ No se encontró archivo .env")
        print(f"📁 Buscado en: {env_file}")
        return False
    
    print("🔍 Validando archivo .env existente...")
    
    required_vars = [
        "SECRET_KEY", "ENCRYPTION_KEY", "DATABASE_URL", "REDIS_URL",
        "RABBITMQ_URL", "MEILISEARCH_URL", "CELERY_BROKER_URL"
    ]
    
    issues = []
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for var in required_vars:
            if f"{var}=" not in content:
                issues.append(f"Variable {var} faltante")
            elif f"{var}=your-" in content or f"{var}=change-this" in content:
                issues.append(f"Variable {var} tiene valor por defecto inseguro")
        
        # Verificar longitudes específicas
        lines = content.split('\n')
        for line in lines:
            if line.startswith('SECRET_KEY='):
                key = line.split('=', 1)[1]
                if len(key) < 32:
                    issues.append("SECRET_KEY muy corta (mínimo 32 caracteres)")
            elif line.startswith('ENCRYPTION_KEY='):
                key = line.split('=', 1)[1]
                if len(key) != 32:
                    issues.append("ENCRYPTION_KEY debe tener exactamente 32 caracteres")
        
        if issues:
            print("❌ Problemas encontrados:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Archivo .env validado correctamente")
            return True
            
    except Exception as e:
        print(f"❌ Error al validar archivo: {e}")
        return False


def create_backup():
    """Crea un backup del archivo .env existente"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ No hay archivo .env para respaldar")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = project_root / f".env.backup.{timestamp}"
    
    try:
        import shutil
        shutil.copy2(env_file, backup_file)
        print(f"✅ Backup creado: {backup_file.name}")
        return True
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return False


def update_docker_compose_passwords():
    """Actualiza las contraseñas en docker-compose.yml"""
    project_root = Path(__file__).parent.parent
    compose_files = [
        project_root / "docker-compose.yml",
        project_root / "docker-compose.dev.yml",
        project_root / "docker-compose.prod.yml"
    ]
    
    print("\n🐳 Archivos Docker Compose encontrados:")
    for compose_file in compose_files:
        if compose_file.exists():
            print(f"   - {compose_file.name}")
    
    print("\n⚠️  IMPORTANTE: Actualiza manualmente las contraseñas en docker-compose.yml")
    print("   Las variables POSTGRES_PASSWORD y RABBITMQ_DEFAULT_PASS deben coincidir")
    print("   con las generadas en el archivo .env")


def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="Generador de claves seguras para FinancePro",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python generate_secrets.py                    # Generar .env completo
  python generate_secrets.py --only-secrets     # Solo mostrar claves
  python generate_secrets.py --validate         # Validar .env existente
  python generate_secrets.py --backup           # Crear backup del .env
        """
    )
    
    parser.add_argument(
        "--only-secrets", 
        action="store_true",
        help="Solo generar y mostrar claves sin crear archivo"
    )
    
    parser.add_argument(
        "--validate", 
        action="store_true",
        help="Validar archivo .env existente"
    )
    
    parser.add_argument(
        "--backup", 
        action="store_true",
        help="Crear backup del archivo .env existente"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Sobrescribir archivo .env sin crear backup"
    )
    
    args = parser.parse_args()
    
    print("🔐 Generador de Claves Seguras para FinancePro")
    print("=" * 50)
    
    try:
        if args.only_secrets:
            generate_only_secrets()
            return 0
        
        if args.validate:
            success = validate_existing_env()
            return 0 if success else 1
        
        if args.backup:
            success = create_backup()
            return 0 if success else 1
        
        # Comportamiento por defecto: crear archivo .env
        if not args.force:
            project_root = Path(__file__).parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                response = input("\n⚠️  El archivo .env ya existe. ¿Crear backup y continuar? (s/N): ")
                if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
                    print("❌ Operación cancelada")
                    return 1
        
        create_env_file()
        update_docker_compose_passwords()
        
        print("\n🎉 ¡Configuración completada exitosamente!")
        print("\nPróximos pasos:")
        print("1. Revisar el archivo .env generado")
        print("2. Actualizar docker-compose.yml con las nuevas contraseñas")
        print("3. Validar configuración: make validate-config")
        print("4. Reiniciar los servicios: make restart")
        
    except KeyboardInterrupt:
        print("\n❌ Operación cancelada por el usuario")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

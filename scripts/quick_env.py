#!/usr/bin/env python3
"""
Script rápido para generar archivo .env básico
Uso: python scripts/quick_env.py
"""

import secrets
import string
from pathlib import Path


def generate_secure_key(length=32):
    """Genera una clave segura de longitud específica"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_password(length=16):
    """Genera una contraseña segura"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_minimal_env():
    """Crea un archivo .env mínimo con las variables esenciales"""
    
    # Generar claves
    secret_key = secrets.token_urlsafe(48)  # 64 caracteres
    encryption_key = generate_secure_key(32)  # Exactamente 32
    db_password = generate_password(16)
    rabbitmq_password = generate_password(16)
    meilisearch_key = secrets.token_urlsafe(24)
    
    env_content = f"""# FinancePro - Configuración Mínima
# Generado automáticamente

# Seguridad
SECRET_KEY={secret_key}
ENCRYPTION_KEY={encryption_key}

# Base de datos
DATABASE_URL=postgresql://postgres:{db_password}@db:5432/financepro
POSTGRES_DB=financepro
POSTGRES_USER=postgres
POSTGRES_PASSWORD={db_password}

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://financepro:{rabbitmq_password}@rabbitmq:5672/financepro_vhost
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=financepro
RABBITMQ_PASSWORD={rabbitmq_password}
RABBITMQ_VHOST=financepro_vhost

# Meilisearch
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_MASTER_KEY={meilisearch_key}
MEILISEARCH_INDEX_PREFIX=financepro

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Configuración básica
PROJECT_NAME=FinancePro API
VERSION=1.0.0
API_V1_STR=/api/v1
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# Seguridad adicional
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
PASSWORD_MIN_LENGTH=8
REQUIRE_2FA=true
SESSION_TIMEOUT_MINUTES=60

# Funcionalidades
ENABLE_AUDIT_LOG=true
AUDIT_LOG_RETENTION_DAYS=365
ENCRYPT_PII_DATA=true
DATA_RETENTION_DAYS=2555
ENABLE_FULL_TEXT_SEARCH=true
SEARCH_RESULTS_LIMIT=50
SEARCH_HIGHLIGHT=true
ENABLE_ASYNC_PROCESSING=true
ENABLE_NOTIFICATIONS=true
EMAIL_NOTIFICATIONS=true
SMS_NOTIFICATIONS=false

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://frontend:80
ALLOWED_HOSTS=*

# Archivos
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760

# Logging
LOG_LEVEL=INFO

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_LOGIN_ATTEMPTS=5

# Email (opcional - configurar si se necesita)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@financepro.com
EMAILS_FROM_NAME=FinancePro

# Sentry (opcional)
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_SENTRY=false
"""

    # Determinar ubicación del archivo
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    env_file = project_root / ".env"
    
    # Verificar si ya existe
    if env_file.exists():
        response = input(f"❓ El archivo {env_file} ya existe. ¿Sobrescribir? (s/N): ")
        if response.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada")
            return False
        
        # Crear backup
        backup_file = project_root / f".env.backup.{secrets.token_hex(4)}"
        env_file.rename(backup_file)
        print(f"📁 Backup creado: {backup_file.name}")
    
    # Escribir archivo
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"✅ Archivo .env creado en: {env_file}")
    print("\n🔐 Claves generadas:")
    print(f"   - SECRET_KEY: {secret_key[:20]}...")
    print(f"   - ENCRYPTION_KEY: {encryption_key}")
    print(f"   - POSTGRES_PASSWORD: {db_password}")
    print(f"   - RABBITMQ_PASSWORD: {rabbitmq_password}")
    print(f"   - MEILISEARCH_MASTER_KEY: {meilisearch_key[:20]}...")
    
    return True


def main():
    """Función principal"""
    print("🚀 Generador Rápido de .env para FinancePro")
    print("=" * 45)
    print("Este script crea un archivo .env con configuración mínima pero segura")
    print()
    
    try:
        if create_minimal_env():
            print("\n🎉 ¡Archivo .env creado exitosamente!")
            print("\n📋 Próximos pasos:")
            print("1. Revisar el archivo .env")
            print("2. Ejecutar: make validate-config")
            print("3. Iniciar servicios: make up-dev")
        else:
            print("❌ No se pudo crear el archivo .env")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

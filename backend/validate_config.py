#!/usr/bin/env python3
"""
Script para validar la configuración de FinancePro
Ejecutar: python validate_config.py
"""

import os
import sys
from pathlib import Path

# Agregar el directorio app al path para importar la configuración
sys.path.insert(0, str(Path(__file__).parent / "app"))

try:
    from core.config import Settings
except ImportError as e:
    print(f"❌ Error al importar configuración: {e}")
    print("💡 Asegúrate de que las dependencias estén instaladas")
    sys.exit(1)


def check_env_file():
    """Verifica que el archivo .env exista"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        print(f"📁 Buscado en: {env_file}")
        print("💡 Ejecuta 'python generate_secrets.py' para crear uno")
        return False
    
    print(f"✅ Archivo .env encontrado: {env_file}")
    return True


def validate_environment():
    """Valida las variables de entorno"""
    print("\n🔍 Validando variables de entorno...")
    
    required_vars = [
        "SECRET_KEY",
        "ENCRYPTION_KEY", 
        "DATABASE_URL",
        "REDIS_URL",
        "RABBITMQ_URL",
        "RABBITMQ_HOST",
        "RABBITMQ_USER", 
        "RABBITMQ_PASSWORD",
        "RABBITMQ_VHOST",
        "MEILISEARCH_URL",
        "MEILISEARCH_MASTER_KEY",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        return False
    
    print("✅ Todas las variables de entorno requeridas están presentes")
    return True


def validate_settings():
    """Valida la configuración usando Pydantic"""
    print("\n🔧 Validando configuración con Pydantic...")
    
    try:
        settings = Settings()
        print("✅ Configuración cargada exitosamente")
        
        # Ejecutar validación personalizada
        is_secure = settings.validate_configuration()
        
        if is_secure:
            print("✅ Configuración segura para producción")
        else:
            print("⚠️  Configuración tiene problemas de seguridad")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error al validar configuración: {e}")
        return False


def check_security_settings():
    """Verifica configuraciones específicas de seguridad"""
    print("\n🔐 Verificando configuraciones de seguridad...")
    
    try:
        settings = Settings()
        issues = []
        
        # Verificar longitud de claves
        if len(settings.SECRET_KEY) < 32:
            issues.append("SECRET_KEY muy corta (mínimo 32 caracteres)")
        
        if len(settings.ENCRYPTION_KEY) != 32:
            issues.append("ENCRYPTION_KEY debe tener exactamente 32 caracteres")
        
        # Verificar valores por defecto
        if "change-this" in settings.SECRET_KEY.lower():
            issues.append("SECRET_KEY contiene valor por defecto")
        
        if "change-this" in settings.ENCRYPTION_KEY.lower():
            issues.append("ENCRYPTION_KEY contiene valor por defecto")
        
        # Verificar configuración de seguridad
        if not settings.REQUIRE_2FA:
            issues.append("2FA no está habilitado")
        
        if not settings.ENCRYPT_PII_DATA:
            issues.append("Encriptación de datos PII no está habilitada")
        
        if settings.SESSION_TIMEOUT_MINUTES > 120:
            issues.append("Timeout de sesión muy largo (recomendado: ≤120 min)")
        
        if issues:
            print("⚠️  Problemas de seguridad encontrados:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        
        print("✅ Configuración de seguridad validada")
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar seguridad: {e}")
        return False


def check_service_urls():
    """Verifica que las URLs de servicios sean válidas"""
    print("\n🌐 Verificando URLs de servicios...")
    
    try:
        settings = Settings()
        
        # Verificar URLs
        url_checks = [
            ("DATABASE_URL", settings.DATABASE_URL, ["postgresql://", "postgres://"]),
            ("REDIS_URL", settings.REDIS_URL, ["redis://"]),
            ("RABBITMQ_URL", settings.RABBITMQ_URL, ["amqp://"]),
            ("MEILISEARCH_URL", settings.MEILISEARCH_URL, ["http://", "https://"]),
            ("CELERY_BROKER_URL", settings.CELERY_BROKER_URL, ["redis://", "amqp://"]),
            ("CELERY_RESULT_BACKEND", settings.CELERY_RESULT_BACKEND, ["redis://", "db+"])
        ]
        
        all_valid = True
        for name, url, valid_prefixes in url_checks:
            if not any(url.startswith(prefix) for prefix in valid_prefixes):
                print(f"❌ {name} tiene formato inválido: {url}")
                all_valid = False
            else:
                print(f"✅ {name}: formato válido")
        
        return all_valid
        
    except Exception as e:
        print(f"❌ Error al verificar URLs: {e}")
        return False


def print_summary(settings):
    """Imprime un resumen de la configuración"""
    print("\n📋 Resumen de Configuración:")
    print("=" * 50)
    print(f"Proyecto: {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Servidor: {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    print(f"API: {settings.API_V1_STR}")
    print(f"Algoritmo JWT: {settings.ALGORITHM}")
    print(f"Expiración token: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} min")
    print(f"2FA habilitado: {'✅' if settings.REQUIRE_2FA else '❌'}")
    print(f"Encriptación PII: {'✅' if settings.ENCRYPT_PII_DATA else '❌'}")
    print(f"Auditoría: {'✅' if settings.ENABLE_AUDIT_LOG else '❌'}")
    print(f"Búsqueda: {'✅' if settings.ENABLE_FULL_TEXT_SEARCH else '❌'}")
    print(f"Procesamiento async: {'✅' if settings.ENABLE_ASYNC_PROCESSING else '❌'}")
    print(f"Notificaciones: {'✅' if settings.ENABLE_NOTIFICATIONS else '❌'}")


def main():
    """Función principal"""
    print("🔍 Validador de Configuración FinancePro")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Verificar archivo .env
    if not check_env_file():
        all_checks_passed = False
    
    # Verificar variables de entorno
    if not validate_environment():
        all_checks_passed = False
    
    # Validar configuración
    if not validate_settings():
        all_checks_passed = False
    
    # Verificar seguridad
    if not check_security_settings():
        all_checks_passed = False
    
    # Verificar URLs
    if not check_service_urls():
        all_checks_passed = False
    
    # Mostrar resumen si todo está bien
    if all_checks_passed:
        try:
            settings = Settings()
            print_summary(settings)
        except Exception as e:
            print(f"❌ Error al generar resumen: {e}")
            all_checks_passed = False
    
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 ¡Todas las validaciones pasaron exitosamente!")
        print("✅ La configuración está lista para usar")
        return 0
    else:
        print("❌ Algunas validaciones fallaron")
        print("💡 Revisa los errores arriba y corrige la configuración")
        return 1


if __name__ == "__main__":
    exit(main())

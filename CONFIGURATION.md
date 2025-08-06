# 🔧 Configuración de FinancePro

Este documento explica cómo configurar correctamente el sistema FinancePro usando variables de entorno y archivos `.env`.

## 📁 Archivos de Configuración

### Estructura de Archivos
```
prestamo/
├── .env                      # Configuración principal (NO en git)
├── .env.example              # Plantilla de configuración
├── .env.production           # Configuración de producción (NO en git)
├── backend/
│   ├── .env.example          # Plantilla específica del backend
│   ├── generate_secrets.py   # Generador de claves seguras
│   └── validate_config.py    # Validador de configuración
└── CONFIGURATION.md          # Este archivo
```

## 🚀 Configuración Rápida

### 1. Generar Configuración Automáticamente
```bash
# Generar archivo .env con claves seguras
make generate-secrets

# Validar la configuración
make validate-config
```

### 2. Configuración Manual
```bash
# Copiar plantilla
cp .env.example .env

# Editar el archivo .env con tus valores
nano .env
```

## 🔐 Variables de Seguridad Obligatorias

### Claves Criptográficas
```bash
# Clave secreta para JWT (mínimo 32 caracteres)
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# Clave de encriptación para datos PII (exactamente 32 caracteres)
ENCRYPTION_KEY=your-encryption-key-32-chars-long
```

### Base de Datos
```bash
# URL completa de PostgreSQL
DATABASE_URL=postgresql://postgres:secure_password@db:5432/financepro

# Variables individuales
POSTGRES_DB=financepro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure_password
```

### Servicios de Infraestructura
```bash
# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://financepro:secure_password@rabbitmq:5672/financepro_vhost
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=financepro
RABBITMQ_PASSWORD=secure_password
RABBITMQ_VHOST=financepro_vhost

# Meilisearch
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_MASTER_KEY=secure_meilisearch_key

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

## ⚙️ Configuración de Seguridad

### Autenticación y Autorización
```bash
# Configuración de tokens JWT
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALGORITHM=HS256

# Configuración de login
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
PASSWORD_MIN_LENGTH=8
REQUIRE_2FA=true
SESSION_TIMEOUT_MINUTES=60
```

### Encriptación y Auditoría
```bash
# Configuración de encriptación
ENCRYPT_PII_DATA=true
DATA_RETENTION_DAYS=2555  # 7 años para datos financieros

# Configuración de auditoría
ENABLE_AUDIT_LOG=true
AUDIT_LOG_RETENTION_DAYS=365
```

## 🌐 Configuración de Red

### CORS y Hosts
```bash
# Orígenes permitidos para CORS (separados por comas)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://frontend:80

# Hosts permitidos
ALLOWED_HOSTS=*
```

## 📧 Configuración de Email (Opcional)

```bash
# Configuración SMTP
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=noreply@financepro.com
EMAILS_FROM_NAME=FinancePro
```

## 🛠️ Comandos Útiles

### Gestión de Configuración
```bash
# Generar claves seguras automáticamente
make generate-secrets

# Validar configuración actual
make validate-config

# Verificar que el archivo .env existe
make check-env

# Mostrar configuración (sin secretos)
make show-config

# Crear backup del archivo .env
make backup-env

# Verificar configuración de seguridad
make security-check

# Mostrar ayuda de configuración
make config-help
```

### Validación Manual
```bash
# Ejecutar validador directamente
python backend/validate_config.py

# Generar nuevas claves
python backend/generate_secrets.py
```

## 🔒 Mejores Prácticas de Seguridad

### ✅ Hacer
- **Usar claves únicas**: Nunca usar valores por defecto en producción
- **Rotar claves regularmente**: Cambiar claves cada 90 días
- **Validar configuración**: Ejecutar `make security-check` regularmente
- **Crear backups**: Respaldar configuración antes de cambios
- **Usar HTTPS**: Siempre en producción
- **Limitar CORS**: Solo orígenes necesarios

### ❌ No Hacer
- **No compartir .env**: Nunca subir archivos .env a repositorios
- **No usar contraseñas débiles**: Mínimo 16 caracteres para passwords
- **No deshabilitar 2FA**: Mantener `REQUIRE_2FA=true`
- **No usar HTTP**: Solo HTTPS en producción
- **No ignorar advertencias**: Revisar logs de seguridad

## 🚨 Configuración de Producción

### Variables Críticas para Producción
```bash
# Claves únicas generadas
SECRET_KEY=<64-caracteres-únicos>
ENCRYPTION_KEY=<32-caracteres-únicos>

# Contraseñas seguras
POSTGRES_PASSWORD=<contraseña-segura-16+>
RABBITMQ_PASSWORD=<contraseña-segura-16+>
MEILISEARCH_MASTER_KEY=<clave-segura-32+>

# Configuración estricta
REQUIRE_2FA=true
ENCRYPT_PII_DATA=true
SESSION_TIMEOUT_MINUTES=30
LOG_LEVEL=WARNING

# CORS restrictivo
BACKEND_CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Lista de Verificación Pre-Producción
- [ ] Claves únicas generadas
- [ ] Contraseñas seguras configuradas
- [ ] 2FA habilitado
- [ ] Encriptación PII habilitada
- [ ] CORS configurado correctamente
- [ ] HTTPS configurado
- [ ] Logs de auditoría habilitados
- [ ] Backup de configuración creado
- [ ] Validación de seguridad pasada

## 🔍 Solución de Problemas

### Error: "SECRET_KEY debe ser cambiada del valor por defecto"
```bash
# Generar nueva clave
make generate-secrets
# O manualmente
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Error: "ENCRYPTION_KEY debe tener exactamente 32 caracteres"
```bash
# Generar clave de 32 caracteres
python -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32)))"
```

### Error: "Variables de entorno faltantes"
```bash
# Verificar qué variables faltan
make validate-config

# Copiar desde plantilla
cp .env.example .env
```

### Error: "DATABASE_URL tiene formato inválido"
```bash
# Formato correcto
DATABASE_URL=postgresql://usuario:contraseña@host:puerto/base_datos
```

## 📞 Soporte

Si tienes problemas con la configuración:

1. **Ejecuta el validador**: `make validate-config`
2. **Revisa los logs**: `make logs-backend`
3. **Verifica la ayuda**: `make config-help`
4. **Consulta este documento**: Revisa las secciones relevantes

## 📚 Referencias

- [Pydantic Settings](https://docs.pydantic.dev/latest/usage/settings/)
- [FastAPI Configuration](https://fastapi.tiangolo.com/advanced/settings/)
- [Docker Compose Environment](https://docs.docker.com/compose/environment-variables/)
- [PostgreSQL Connection Strings](https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING)

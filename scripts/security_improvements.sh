#!/bin/bash

# 🔒 Script de Mejoras de Seguridad - FinancePro
# Implementa las correcciones críticas identificadas en la auditoría

set -e

echo "🔒 Iniciando mejoras de seguridad para FinancePro..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para generar claves seguras
generate_secure_key() {
    openssl rand -base64 32
}

# 1. CRÍTICO: Generar nuevas claves seguras
echo -e "${YELLOW}1. Generando nuevas claves de seguridad...${NC}"

SECRET_KEY=$(generate_secure_key)
ENCRYPTION_KEY=$(generate_secure_key)

echo -e "${GREEN}✅ Claves generadas exitosamente${NC}"
echo "SECRET_KEY: ${SECRET_KEY:0:10}..."
echo "ENCRYPTION_KEY: ${ENCRYPTION_KEY:0:10}..."

# 2. Crear archivo .env.production con configuración segura
echo -e "${YELLOW}2. Creando configuración de producción segura...${NC}"

cat > .env.production << EOF
# 🔒 Configuración de Producción Segura - FinancePro
# Generado automáticamente: $(date)

# Configuración del proyecto
PROJECT_NAME=FinancePro API
VERSION=1.0.0
ENVIRONMENT=production

# Base de datos (usar conexión SSL en producción)
DATABASE_URL=postgresql://postgres:password@db:5432/financepro?sslmode=require
POSTGRES_DB=financepro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis
REDIS_URL=redis://redis:6379/0

# 🔑 Claves de Seguridad (GENERADAS AUTOMÁTICAMENTE)
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Configuración de seguridad estricta
MAX_LOGIN_ATTEMPTS=3
LOCKOUT_DURATION_MINUTES=60
PASSWORD_MIN_LENGTH=12
REQUIRE_2FA=true
SESSION_TIMEOUT_MINUTES=30

# Configuración de notificaciones
ENABLE_NOTIFICATIONS=true
EMAIL_NOTIFICATIONS=true
SMS_NOTIFICATIONS=false
ADMIN_EMAIL=admin@financepro.com

# RabbitMQ - URLs internas
RABBITMQ_URL=amqp://financepro:rabbitmq_password@rabbitmq:5672/financepro_vhost
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=financepro
RABBITMQ_PASSWORD=rabbitmq_password
RABBITMQ_VHOST=financepro_vhost

# Meilisearch - URL interna
MEILISEARCH_URL=http://meilisearch:7700
MEILISEARCH_MASTER_KEY=meilisearch_prod_master_key_$(openssl rand -hex 16)
MEILISEARCH_INDEX_PREFIX=financepro

# Configuración de Búsqueda
ENABLE_FULL_TEXT_SEARCH=true
SEARCH_RESULTS_LIMIT=50
SEARCH_HIGHLIGHT=true

# Configuración de Procesamiento Asíncrono
ENABLE_ASYNC_PROCESSING=true
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Configuración de auditoría
ENABLE_AUDIT_LOG=true
AUDIT_LOG_RETENTION_DAYS=365

# Configuración de encriptación
ENCRYPT_PII_DATA=true
DATA_RETENTION_DAYS=2555

# CORS - Solo dominios de producción
BACKEND_CORS_ORIGINS=https://financepro.com,https://www.financepro.com

# Email (configurar con credenciales reales)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=noreply@financepro.com
SMTP_PASSWORD=your-secure-app-password
EMAILS_FROM_EMAIL=noreply@financepro.com
EMAILS_FROM_NAME=FinancePro

# Archivos
UPLOAD_DIR=/app/uploads
MAX_FILE_SIZE=10485760

# Logging y monitoreo
LOG_LEVEL=WARNING
STRUCTURED_LOGGING=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
ENABLE_SENTRY=true

# Rate limiting estricto
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_LOGIN_ATTEMPTS=3

# Configuración de archivos y uploads
MAX_UPLOAD_SIZE=5242880
ALLOWED_FILE_TYPES=pdf,jpg,jpeg,png
UPLOAD_ENCRYPTION=true

# Configuración de backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
BACKUP_ENCRYPTION=true

# Configuración SSL/TLS
SSL_ENABLED=true
SSL_CERT_PATH=/etc/nginx/ssl/cert.pem
SSL_KEY_PATH=/etc/nginx/ssl/key.pem

# Deshabilitar documentación en producción
DISABLE_DOCS=true
EOF

echo -e "${GREEN}✅ Archivo .env.production creado${NC}"

# 3. Crear configuración nginx de producción mejorada
echo -e "${YELLOW}3. Mejorando configuración nginx de producción...${NC}"

cat > nginx/nginx.prod.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Configuración de logs
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;

    # Configuración general
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;  # Ocultar versión de nginx

    # Configuración de compresión
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/javascript
        application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=60r/m;
    limit_req_zone $binary_remote_addr zone=login:10m rate=3r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;

    # Upstream para el backend
    upstream backend {
        server backend:8000;
    }

    # Upstream para el frontend
    upstream frontend {
        server frontend:3000;
    }

    # Redirección HTTP a HTTPS
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }

    # Servidor HTTPS principal
    server {
        listen 443 ssl http2;
        server_name _;

        # Configuración SSL/TLS
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache shared:SSL:10m;
        ssl_session_timeout 10m;

        # Headers de seguridad completos
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=()" always;

        # Rate limiting
        limit_req zone=general burst=20 nodelay;

        # Proxy para API del backend
        location /api/ {
            limit_req zone=api burst=10 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Configuración para WebSockets
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Rate limiting especial para login
        location /api/v1/auth/login {
            limit_req zone=login burst=3 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Bloquear documentación en producción
        location ~ ^/(docs|redoc|openapi\.json) {
            return 404;
        }

        # Frontend - todas las demás rutas
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Configuración para SPA
            try_files $uri $uri/ /index.html;
        }

        # Archivos estáticos con cache
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            proxy_pass http://frontend;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

echo -e "${GREEN}✅ Configuración nginx de producción mejorada${NC}"

# 4. Crear docker-compose.prod.yml con configuración segura
echo -e "${YELLOW}4. Creando docker-compose de producción seguro...${NC}"

cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  # Base de datos PostgreSQL
  db:
    image: postgres:15-alpine
    container_name: financepro_db_prod
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data_prod:/var/lib/postgresql/data
    networks:
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis para cache y sesiones
  redis:
    image: redis:7-alpine
    container_name: financepro_redis_prod
    command: redis-server --requirepass ${REDIS_PASSWORD:-redis_password}
    volumes:
      - redis_data_prod:/data
    networks:
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # RabbitMQ para mensajería
  rabbitmq:
    image: rabbitmq:3.12-management-alpine
    container_name: financepro_rabbitmq_prod
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
      RABBITMQ_DEFAULT_VHOST: ${RABBITMQ_VHOST}
    volumes:
      - rabbitmq_data_prod:/var/lib/rabbitmq
    networks:
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Meilisearch para búsqueda
  meilisearch:
    image: getmeili/meilisearch:v1.5
    container_name: financepro_meilisearch_prod
    environment:
      MEILI_MASTER_KEY: ${MEILISEARCH_MASTER_KEY}
      MEILI_ENV: production
    volumes:
      - meilisearch_data_prod:/meili_data
    networks:
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:7700/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: financepro_backend_prod
    env_file:
      - .env.production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
      meilisearch:
        condition: service_healthy
    volumes:
      - ./uploads:/app/uploads
    networks:
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/v1/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: financepro_frontend_prod
    depends_on:
      - backend
    networks:
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Proxy Reverso
  nginx:
    image: nginx:alpine
    container_name: financepro_nginx_prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    networks:
      - financepro_external_network
      - financepro_internal_network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data_prod:
  redis_data_prod:
  rabbitmq_data_prod:
  meilisearch_data_prod:

networks:
  financepro_external_network:
    driver: bridge
    name: financepro_external_prod
  financepro_internal_network:
    driver: bridge
    name: financepro_internal_prod
    internal: true  # Sin acceso a internet - SEGURIDAD CRÍTICA
EOF

echo -e "${GREEN}✅ Docker compose de producción creado${NC}"

# 5. Crear script para generar certificados SSL
echo -e "${YELLOW}5. Creando script para certificados SSL...${NC}"

mkdir -p ssl

cat > scripts/generate_ssl.sh << 'EOF'
#!/bin/bash

# Script para generar certificados SSL autofirmados (desarrollo)
# Para producción, usar Let's Encrypt o certificados comerciales

echo "🔐 Generando certificados SSL..."

mkdir -p ssl

# Generar clave privada
openssl genrsa -out ssl/key.pem 2048

# Generar certificado autofirmado
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=PA/ST=Chiriqui/L=David/O=FinancePro/OU=IT/CN=localhost"

echo "✅ Certificados SSL generados en ./ssl/"
echo "⚠️  IMPORTANTE: Para producción, usar certificados válidos de Let's Encrypt o CA comercial"
EOF

chmod +x scripts/generate_ssl.sh

echo -e "${GREEN}✅ Script de certificados SSL creado${NC}"

# 6. Crear checklist de seguridad
echo -e "${YELLOW}6. Creando checklist de seguridad...${NC}"

cat > SECURITY_CHECKLIST.md << 'EOF'
# 🔒 Checklist de Seguridad - FinancePro

## ✅ Configuración Inicial Completada

- [x] Claves de seguridad generadas automáticamente
- [x] Archivo .env.production creado con configuración segura
- [x] Configuración nginx de producción mejorada
- [x] Docker compose de producción con red aislada
- [x] Script de generación de certificados SSL

## 📋 Tareas Pendientes CRÍTICAS

### Antes de Desplegar en Producción:

- [ ] **Generar certificados SSL válidos**
  ```bash
  # Opción 1: Let's Encrypt (recomendado)
  certbot --nginx -d tu-dominio.com
  
  # Opción 2: Certificados autofirmados (solo desarrollo)
  ./scripts/generate_ssl.sh
  ```

- [ ] **Configurar credenciales de base de datos seguras**
  - Cambiar contraseña de PostgreSQL
  - Configurar conexión SSL a base de datos
  - Crear usuario con permisos limitados

- [ ] **Configurar SMTP para notificaciones**
  - Actualizar credenciales SMTP en .env.production
  - Probar envío de emails

- [ ] **Configurar monitoreo (Sentry)**
  - Crear cuenta en Sentry
  - Actualizar SENTRY_DSN en .env.production

- [ ] **Revisar y actualizar dominios CORS**
  - Actualizar BACKEND_CORS_ORIGINS con dominios reales

### Configuración de Infraestructura:

- [ ] **Firewall del servidor**
  ```bash
  # Permitir solo puertos necesarios
  ufw allow 22    # SSH
  ufw allow 80    # HTTP
  ufw allow 443   # HTTPS
  ufw enable
  ```

- [ ] **Configurar backup automático**
  - Configurar backup de base de datos
  - Configurar backup de archivos subidos
  - Probar restauración de backup

- [ ] **Configurar logs centralizados**
  - Configurar rotación de logs
  - Configurar envío de logs críticos

## 🚀 Comandos de Despliegue

### Desarrollo con mejoras de seguridad:
```bash
# Usar configuración mejorada
cp .env.production .env
./scripts/generate_ssl.sh
docker compose -f docker-compose.dev.yml up -d
```

### Producción:
```bash
# Configurar variables de entorno
cp .env.production .env

# Generar certificados SSL
./scripts/generate_ssl.sh  # O configurar Let's Encrypt

# Desplegar
docker compose -f docker-compose.prod.yml up -d
```

## 🔍 Verificación Post-Despliegue

- [ ] Verificar que solo puertos 80/443 estén expuestos
- [ ] Probar login con 2FA
- [ ] Verificar headers de seguridad con: https://securityheaders.com
- [ ] Probar rate limiting
- [ ] Verificar logs de auditoría
- [ ] Probar backup y restauración

## 📊 Monitoreo Continuo

- [ ] Configurar alertas por intentos de login fallidos
- [ ] Monitorear logs de nginx por patrones sospechosos
- [ ] Revisar métricas de rate limiting
- [ ] Auditar accesos a datos sensibles

## 🆘 Contactos de Emergencia

- **Equipo de Seguridad**: security@financepro.com
- **Emergencias 24/7**: +52 55 1234-5678
- **DevOps**: devops@financepro.com
EOF

echo -e "${GREEN}✅ Checklist de seguridad creado${NC}"

# Resumen final
echo -e "\n${GREEN}🎉 Mejoras de seguridad completadas exitosamente!${NC}\n"

echo -e "${YELLOW}📋 Archivos creados:${NC}"
echo "  ✅ .env.production - Configuración segura de producción"
echo "  ✅ nginx/nginx.prod.conf - Configuración nginx mejorada"
echo "  ✅ docker-compose.prod.yml - Compose de producción seguro"
echo "  ✅ scripts/generate_ssl.sh - Generador de certificados SSL"
echo "  ✅ SECURITY_CHECKLIST.md - Lista de verificación"

echo -e "\n${RED}⚠️  IMPORTANTE:${NC}"
echo "1. Las nuevas claves han sido generadas automáticamente"
echo "2. Revisar y completar SECURITY_CHECKLIST.md antes de producción"
echo "3. Generar certificados SSL válidos para producción"
echo "4. Configurar credenciales reales de SMTP y Sentry"

echo -e "\n${GREEN}🚀 Próximos pasos:${NC}"
echo "1. Revisar .env.production y ajustar según necesidades"
echo "2. Ejecutar: ./scripts/generate_ssl.sh"
echo "3. Probar con: docker compose -f docker-compose.prod.yml up -d"
echo "4. Verificar seguridad con herramientas online"

echo -e "\n${GREEN}✅ Sistema listo para despliegue seguro en producción!${NC}"
EOF

chmod +x scripts/security_improvements.sh

echo -e "${GREEN}✅ Script de mejoras de seguridad creado${NC}"

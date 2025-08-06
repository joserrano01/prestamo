# 🔒 Documento de Seguridad - FinancePro

## Resumen Ejecutivo

FinancePro implementa un sistema de seguridad robusto y multicapa diseñado específicamente para proteger datos financieros sensibles. Este documento detalla todas las medidas de seguridad implementadas en el sistema.

## 🆕 MEJORAS DE SEGURIDAD RECIENTES (v1.0-security-enhanced)

### ✅ Mejoras Críticas Implementadas:

#### 🔐 **1. Manejo Seguro de Tokens de Autenticación**
- **ANTES**: Tokens almacenados en localStorage (vulnerable a XSS)
- **AHORA**: Tokens almacenados en sessionStorage con expiración automática
- **BENEFICIO**: Protección contra ataques XSS y eliminación automática al cerrar navegador
- **IMPLEMENTACIÓN**: AuthService con gestión segura de tokens

#### 🛡️ **2. Headers de Seguridad Avanzados**
- **Content-Security-Policy**: Protección contra XSS
- **X-Frame-Options**: Prevención de clickjacking
- **X-Content-Type-Options**: Prevención de MIME sniffing
- **Referrer-Policy**: Control de información de referencia
- **X-Permitted-Cross-Domain-Policies**: Bloqueo de políticas cross-domain

#### 🚦 **3. Rate Limiting Implementado**
- **Login**: 5 intentos por minuto por IP
- **API General**: 30 requests por minuto por IP
- **Frontend**: 60 requests por minuto por IP
- **BENEFICIO**: Protección contra ataques de fuerza bruta y DDoS

#### 🔒 **4. Protección de Rutas**
- **ProtectedRoute**: Componente que protege rutas sensibles
- **Verificación automática**: Validación de tokens en cada navegación
- **Redirección segura**: Preserva destino original después del login

#### 🔑 **5. Variables de Entorno Seguras**
- **Claves generadas**: SECRET_KEY y ENCRYPTION_KEY únicos
- **Contraseñas fuertes**: POSTGRES_PASSWORD segura
- **Separación**: Archivo .env.secure para producción

#### 📝 **6. Logging de Seguridad**
- **Intentos de login**: Log especializado para monitoreo
- **Acceso a API**: Tracking de requests con detalles de seguridad
- **Rate limiting**: Logs de requests bloqueados

#### 🔧 **7. Configuración de Red Segura**
- **Puerto 3001 removido**: Eliminación de puertos innecesarios
- **server_tokens off**: Ocultación de versión de nginx
- **Timeouts configurados**: Prevención de ataques de agotamiento

## 🛡️ Medidas de Seguridad Implementadas

### 1. Encriptación de Datos Sensibles

#### Datos Encriptados
- **RFC**: Registro Federal de Contribuyentes
- **CURP**: Clave Única de Registro de Población
- **Teléfonos**: Números de contacto
- **Direcciones**: Información de domicilio
- **Fechas de nacimiento**: Información personal
- **URLs de documentos**: Rutas de archivos confidenciales
- **Secretos 2FA**: Claves de autenticación de dos factores
- **Códigos de respaldo**: Códigos de recuperación 2FA

#### Algoritmo de Encriptación
- **Algoritmo**: Fernet (AES 128 en modo CBC con HMAC SHA256)
- **Derivación de clave**: PBKDF2 con SHA256 (100,000 iteraciones)
- **Salt**: Único por instalación
- **Longitud de clave**: 256 bits

#### Implementación
```python
# Ejemplo de uso
from app.core.security import data_encryption

# Encriptar datos sensibles
encrypted_rfc = data_encryption.encrypt("ABCD123456789")

# Desencriptar cuando sea necesario
original_rfc = data_encryption.decrypt(encrypted_rfc)
```

### 2. Autenticación y Autorización

#### Autenticación Multifactor (2FA)
- **Obligatorio**: Para todos los usuarios
- **Algoritmo**: TOTP (Time-based One-Time Password)
- **Códigos de respaldo**: 10 códigos únicos por usuario
- **Ventana de tiempo**: 30 segundos
- **Tolerancia**: ±1 ventana de tiempo

#### Tokens JWT
- **Algoritmo**: HS256
- **Expiración**: 30 minutos (configurable)
- **Claims adicionales**:
  - `iss`: Issuer (financepro)
  - `aud`: Audience (financepro-client)
  - `jti`: JWT ID único
  - `iat`: Issued at timestamp

#### Control de Acceso
- **Roles**: admin, manager, employee
- **Permisos granulares**: Por recurso y acción
- **Sesiones**: Timeout automático (60 minutos)
- **Bloqueo de cuenta**: 5 intentos fallidos, bloqueo por 30 minutos

### 3. Protección contra Ataques

#### Rate Limiting
- **General**: 100 requests/minuto por IP
- **Login**: 5 intentos/15 minutos por IP
- **2FA**: 10 intentos/minuto por usuario
- **API sensibles**: Límites específicos por endpoint

#### Headers de Seguridad
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
```

#### Sanitización de Entrada
- **HTML**: Eliminación de tags y scripts
- **SQL Injection**: Uso de ORM con prepared statements
- **XSS**: Escape automático de salida
- **CSRF**: Tokens únicos por sesión

### 4. Auditoría y Monitoreo

#### Logs de Auditoría
Todos los eventos críticos son registrados:
- **Intentos de login** (exitosos y fallidos)
- **Acceso a datos sensibles**
- **Modificaciones de datos**
- **Cambios de configuración**
- **Errores de seguridad**

#### Información Registrada
```json
{
  "timestamp": "2025-01-02T18:22:15Z",
  "event_type": "data_access",
  "user_id": "uuid",
  "resource_type": "cliente",
  "resource_id": "uuid",
  "action": "read",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "success": true
}
```

#### Retención de Logs
- **Logs de auditoría**: 365 días
- **Logs de acceso**: 90 días
- **Logs de error**: 180 días

### 5. Seguridad de Base de Datos

#### Configuración Segura
- **Conexiones encriptadas**: SSL/TLS obligatorio
- **Usuario limitado**: Sin permisos de administrador
- **Backup encriptado**: Respaldos con encriptación AES-256
- **Índices optimizados**: Para consultas de auditoría

#### Campos Sensibles
```sql
-- Ejemplo de tabla con campos encriptados
CREATE TABLE clientes (
    id UUID PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    telefono VARCHAR(500),  -- Encriptado
    rfc VARCHAR(500),       -- Encriptado
    curp VARCHAR(500),      -- Encriptado
    -- Campos de auditoría
    created_at TIMESTAMP,
    last_accessed_at TIMESTAMP,
    access_count INTEGER
);
```

### 6. Seguridad de Sesiones

#### Gestión de Sesiones
- **Tokens seguros**: Generación criptográficamente segura
- **Expiración automática**: 60 minutos de inactividad
- **Revocación**: Logout inmediato en todos los dispositivos
- **Detección de anomalías**: IP y User-Agent inusuales

#### Almacenamiento
- **Redis**: Para sesiones activas
- **Base de datos**: Para auditoría de sesiones
- **Encriptación**: Tokens de sesión hasheados

### 7. Enmascaramiento de Datos

#### Datos Enmascarados en UI
```python
# Ejemplos de enmascaramiento
RFC: "ABCD****"
CURP: "ABCD****"
Teléfono: "****1234"
Email: "us**@example.com"
Cuenta: "****5678"
```

#### Acceso Completo
Solo usuarios autorizados pueden ver datos completos:
- **Administradores**: Acceso completo
- **Gerentes**: Acceso a su sucursal
- **Empleados**: Acceso limitado según permisos

### 8. Arquitectura de Red Segura

#### Segmentación de Red
El sistema implementa una arquitectura de red de dos capas para máxima seguridad:

**Red Externa (`financepro_external_network`)**:
- Solo nginx tiene acceso desde el exterior
- Punto de entrada único al sistema
- Expone únicamente los puertos necesarios (80, 443)
- Configurada con `driver: bridge`

**Red Interna (`financepro_internal_network`)**:
- Todos los servicios se comunican aquí
- Sin acceso directo desde el exterior
- Configurada como `internal: true` en producción
- Comunicación segura entre contenedores

#### Servicios en Red Interna
```yaml
# Servicios que solo operan en red interna:
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- RabbitMQ (puertos 5672, 15672)
- Meilisearch (puerto 7700)
- Backend API (puerto 8000)
- Frontend (puerto 3000/80)
```

#### Nginx como Proxy Reverso Seguro
**Desarrollo (`nginx.dev.conf`)**:
- Acceso a servicios internos para debugging
- Puertos expuestos: 80, 8080, 15672, 7700, 6379
- Rate limiting configurado
- Headers de seguridad básicos

**Producción (`nginx.conf`)**:
- Solo puertos 80 y 443 expuestos
- SSL/TLS obligatorio con redirección HTTP → HTTPS
- Rate limiting agresivo:
  - API general: 10 req/s
  - Login: 5 req/m
- Headers de seguridad completos:
  ```nginx
  add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
  add_header X-Frame-Options "SAMEORIGIN";
  add_header X-Content-Type-Options "nosniff";
  add_header X-XSS-Protection "1; mode=block";
  add_header Content-Security-Policy "default-src 'self'; ...";
  ```

#### Beneficios de Seguridad
1. **Aislamiento de Servicios**: Los servicios internos no son accesibles directamente
2. **Punto de Control Único**: Todo el tráfico pasa por nginx
3. **Monitoreo Centralizado**: Logs de acceso en un solo punto
4. **Protección DDoS**: Rate limiting y buffering en nginx
5. **Terminación SSL**: Certificados gestionados centralmente

#### Configuración de Redes Docker
```yaml
# Desarrollo
networks:
  financepro_external_network:
    driver: bridge
    name: financepro_external_dev
  financepro_internal_network:
    driver: bridge
    name: financepro_internal_dev
    internal: false  # Permite internet para desarrollo

# Producción
networks:
  financepro_external_network:
    driver: bridge
    name: financepro_external
  financepro_internal_network:
    driver: bridge
    name: financepro_internal
    internal: true   # Sin acceso a internet
```

### 9. Configuración de Seguridad

#### Variables de Entorno Críticas
```bash
# Claves de encriptación (OBLIGATORIO cambiar en producción)
SECRET_KEY=your-super-secret-key-32-chars-min
ENCRYPTION_KEY=your-encryption-key-32-chars-exact

# Configuración 2FA
REQUIRE_2FA=true

# Configuración de bloqueo
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Auditoría
ENABLE_AUDIT_LOG=true
ENCRYPT_PII_DATA=true

# URLs de servicios internos (solo para contenedores)
DATABASE_URL=postgresql://postgres:password@db:5432/financepro
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://financepro:password@rabbitmq:5672/vhost
MEILISEARCH_URL=http://meilisearch:7700
```

## 🚨 Procedimientos de Seguridad

### Configuración Inicial

1. **Cambiar claves por defecto**:
   ```bash
   # Generar claves seguras
   openssl rand -base64 32  # Para SECRET_KEY
   openssl rand -base64 32  # Para ENCRYPTION_KEY
   ```

2. **Configurar 2FA**:
   - Habilitar para todos los usuarios
   - Generar códigos de respaldo
   - Documentar proceso de recuperación

3. **Configurar monitoreo**:
   - Alertas por intentos de acceso fallidos
   - Monitoreo de logs de auditoría
   - Alertas por accesos anómalos

### Respuesta a Incidentes

#### Detección de Acceso No Autorizado
1. **Inmediato**:
   - Bloquear cuenta afectada
   - Revocar todas las sesiones
   - Cambiar credenciales comprometidas

2. **Investigación**:
   - Revisar logs de auditoría
   - Identificar datos accedidos
   - Documentar el incidente

3. **Recuperación**:
   - Restaurar desde backup si es necesario
   - Fortalecer medidas de seguridad
   - Notificar a usuarios afectados

#### Compromiso de Datos
1. **Contención**:
   - Aislar sistemas afectados
   - Preservar evidencia
   - Activar plan de continuidad

2. **Evaluación**:
   - Determinar alcance del compromiso
   - Identificar datos afectados
   - Evaluar impacto en clientes

3. **Notificación**:
   - Autoridades regulatorias
   - Clientes afectados
   - Socios comerciales

## 🔧 Mantenimiento de Seguridad

### Actualizaciones Regulares
- **Dependencias**: Actualización mensual
- **Parches de seguridad**: Aplicación inmediata
- **Revisión de configuración**: Trimestral

### Auditorías
- **Interna**: Mensual
- **Externa**: Anual
- **Penetration testing**: Semestral

### Capacitación
- **Personal técnico**: Trimestral
- **Usuarios finales**: Semestral
- **Procedimientos de emergencia**: Anual

## 📋 Checklist de Seguridad

### Configuración Inicial
- [ ] Cambiar SECRET_KEY por defecto
- [ ] Cambiar ENCRYPTION_KEY por defecto
- [ ] Configurar SSL/TLS en base de datos
- [ ] Habilitar 2FA para todos los usuarios
- [ ] Configurar rate limiting
- [ ] Establecer políticas de contraseñas
- [ ] Configurar logs de auditoría
- [ ] Configurar backups encriptados
- [ ] Verificar segmentación de red Docker
- [ ] Configurar certificados SSL para nginx
- [ ] Validar que servicios internos no sean accesibles externamente
- [ ] Configurar firewall del servidor (si aplica)

### Operación Diaria
- [ ] Revisar logs de auditoría
- [ ] Monitorear intentos de acceso fallidos
- [ ] Verificar integridad de backups
- [ ] Revisar alertas de seguridad
- [ ] Monitorear logs de nginx para actividad sospechosa
- [ ] Verificar que todos los servicios estén en la red correcta
- [ ] Revisar métricas de rate limiting

### Mantenimiento Periódico
- [ ] Actualizar dependencias
- [ ] Rotar claves de encriptación
- [ ] Revisar permisos de usuarios
- [ ] Limpiar logs antiguos
- [ ] Probar procedimientos de recuperación

## 📞 Contacto de Seguridad

Para reportar vulnerabilidades o incidentes de seguridad:
- **Email**: security@financepro.com
- **Teléfono**: +52 55 1234-5678
- **Horario**: 24/7 para incidentes críticos

---

**Última actualización**: 2025-01-02  
**Versión del documento**: 1.0  
**Próxima revisión**: 2025-04-02

# Changelog - Sistema de Préstamos FinancePro

## v1.2.0 - Inicio de Sistema (2025-08-08)

### 🚀 Sistema Completamente Funcional

Este release marca el **inicio oficial del sistema** con todas las funcionalidades básicas operativas.

#### ✅ Características Implementadas

**🔐 Sistema de Autenticación**
- Login funcional con usuarios reales de base de datos
- Selección de sucursal durante el login
- Endpoints de autenticación REST API
- Tokens JWT (simulados para desarrollo)
- Validación de credenciales con hash bcrypt

**🏗️ Arquitectura Base**
- Microservicios con Docker Compose
- Frontend React + TypeScript + Vite
- Backend FastAPI + Python con middleware de seguridad
- Base de datos PostgreSQL con datos encriptados
- Cache Redis para sesiones
- RabbitMQ para mensajería asíncrona
- Meilisearch para búsqueda full-text
- Nginx como proxy reverso

**🔒 Seguridad**
- Encriptación de datos PII
- Headers de seguridad implementados
- Auditoría de acceso a endpoints sensibles
- Rate limiting configurado (deshabilitado en desarrollo)
- Validación de entrada y sanitización

**🌐 API Endpoints Funcionales**
- `GET /api/v1/health/` - Health check del sistema
- `GET /api/v1/sucursales/` - Lista de sucursales
- `POST /api/v1/auth/login` - Login con selección de sucursal
- `POST /api/v1/auth/login-simple` - Login simplificado
- `POST /api/v1/auth/logout` - Cerrar sesión
- `POST /api/v1/auth/refresh` - Renovar token

**👥 Usuarios de Prueba Disponibles**
```
Email: admin.bugaba@financepro.com | Password: admin123 | Role: admin
Email: manager.bugaba@financepro.com | Password: admin123 | Role: manager
Email: empleado.bugaba@financepro.com | Password: admin123 | Role: employee
Email: admin.david@financepro.com | Password: admin123 | Role: admin
Email: manager.david@financepro.com | Password: admin123 | Role: manager
Email: empleado.david@financepro.com | Password: admin123 | Role: employee
```

#### 🛠️ Configuración de Desarrollo

**Frontend**
- Vite dev server en puerto 3000
- Hot module replacement (HMR) habilitado
- Tailwind CSS configurado
- Radix UI components

**Backend**
- Uvicorn con recarga automática
- Middleware de seguridad adaptado para desarrollo
- Logs estructurados con structlog
- Conexión con todos los servicios de infraestructura

**Servicios**
- PostgreSQL en puerto interno 5432
- Redis en puerto interno 6379
- RabbitMQ Management UI en puerto 15672
- Meilisearch Dashboard en puerto 7700

#### 📦 Comandos de Desarrollo

```bash
# Iniciar entorno completo de desarrollo
make dev

# Ver estado de contenedores
make status-dev

# Ver logs específicos
make logs-frontend
make logs-backend

# Acceder a base de datos
make shell-db

# Health check completo
make health-check
```

#### 🏷️ Tags Importantes

- `v1.1.0-login-functional` - Sistema de login funcionando
- `v1.2.0` - Sistema inicial completo ⭐ **ESTE RELEASE**

---

## v1.1.0 - Login Functional (2025-08-08)

### 🔑 Sistema de Autenticación Habilitado

**Frontend fixes:**
- Fixed frontend development environment setup 
- Resolved React build and nginx proxy configuration
- Enabled Vite dev server on port 3000 for hot reloading

**Backend authentication:**
- Enabled auth module in API router (/api/v1/auth/*)
- Fixed SQLAlchemy join issue in UsuarioEmail relationship
- Implemented functional login with real database users
- Added support for both simple and sucursal-based login

**Development optimizations:**
- Disabled rate limiting middleware for development
- Disabled session security middleware for development  
- Disabled input sanitization middleware for development
- Adjusted nginx rate limits for development workflow
- Maintained security headers and audit logging

---

## v1.0.0 - Security Foundation (2025-08-06)

### 🔒 Base de Seguridad Implementada

- Implementación de encriptación de datos PII
- Sistema de auditoría completo
- Middleware de seguridad
- Configuración inicial de Docker Compose
- Base de datos con usuarios y sucursales

---

*🤖 Generated with [Claude Code](https://claude.ai/code)*
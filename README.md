# 🏦 FinancePro - Sistema de Préstamos

Sistema completo de gestión de préstamos empresariales desarrollado con React, FastAPI y PostgreSQL, totalmente dockerizado.

## 🎯 Estado Actual - v1.2.0 "Inicio de Sistema"

✅ **Sistema Base Completamente Funcional**
- ✅ Autenticación con usuarios reales de BD
- ✅ Frontend React + Vite con hot reload
- ✅ Backend FastAPI con middleware de seguridad
- ✅ Base de datos PostgreSQL con datos encriptados
- ✅ Docker Compose para desarrollo y producción
- ✅ Nginx proxy con configuración optimizada
- ✅ Redis, RabbitMQ, Meilisearch integrados
- ✅ Documentación completa y comandos Makefile

## 🚀 Características

### Frontend (React + TypeScript)
- **Autenticación segura** con verificación 2FA
- **Dashboard interactivo** con métricas en tiempo real
- **Gestión completa de préstamos**
- **Administración de clientes**
- **Sistema de reportes**
- **Interfaz responsive** y moderna
- **Multi-sucursal** con selección de ubicación

### Backend (FastAPI + Python)
- **API REST** completa y documentada
- **Autenticación JWT** con refresh tokens
- **Base de datos PostgreSQL** con migraciones
- **Cache con Redis**
- **Validación de datos** con Pydantic
- **Documentación automática** con Swagger/OpenAPI

### Infraestructura
- **Docker & Docker Compose** para desarrollo y producción
- **Nginx** como proxy reverso
- **PostgreSQL** como base de datos principal
- **Redis** para caché y sesiones
- **Makefile** con comandos útiles

## 📦 Instalación Rápida

### Prerrequisitos
- Docker
- Docker Compose
- Make (opcional, pero recomendado)

### 1. Clonar y configurar
```bash
git clone <repository-url>
cd prestamo
make install  # Crea el archivo .env
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Iniciar en modo desarrollo
```bash
make dev
```

### 4. Acceder a la aplicación
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Base de datos**: localhost:5432

## 🛠️ Comandos Disponibles

```bash
# Desarrollo
make dev              # Iniciar en modo desarrollo
make build-dev        # Construir imágenes de desarrollo
make up-dev           # Levantar servicios de desarrollo
make logs-dev         # Ver logs de desarrollo

# Producción
make prod             # Iniciar en modo producción
make build            # Construir imágenes de producción
make up               # Levantar servicios de producción
make logs             # Ver logs de producción

# Utilidades
make status           # Ver estado de contenedores
make clean            # Limpiar recursos no utilizados
make backup-db        # Crear backup de la base de datos
make shell-backend    # Acceder al shell del backend
make shell-db         # Acceder a PostgreSQL
make test             # Ejecutar tests

# Ver todos los comandos
make help
```

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   Frontend      │    │   Nginx         │    │   Backend       │
│   (React)       │◄──►│   (Proxy)       │◄──►│   (FastAPI)     │
│   Port: 3000    │    │   Port: 80      │    │   Port: 8000    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │                 │             │
                       │   Redis         │◄────────────┤
                       │   (Cache)       │             │
                       │   Port: 6379    │             │
                       │                 │             │
                       └─────────────────┘             │
                                                       │
                       ┌─────────────────┐             │
                       │                 │             │
                       │   PostgreSQL    │◄────────────┘
                       │   (Database)    │
                       │   Port: 5432    │
                       │                 │
                       └─────────────────┘
```

## 📁 Estructura del Proyecto

```
prestamo/
├── frontend/                 # Aplicación React
│   ├── src/
│   │   ├── components/      # Componentes reutilizables
│   │   ├── pages/          # Páginas de la aplicación
│   │   ├── types/          # Tipos TypeScript
│   │   └── lib/            # Utilidades
│   ├── Dockerfile          # Docker para producción
│   ├── Dockerfile.dev      # Docker para desarrollo
│   └── package.json
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints de la API
│   │   ├── core/           # Configuración
│   │   ├── models/         # Modelos de base de datos
│   │   ├── schemas/        # Esquemas Pydantic
│   │   └── main.py         # Aplicación principal
│   ├── Dockerfile
│   ├── requirements.txt
│   └── init.sql            # Script de inicialización DB
├── nginx/                   # Configuración Nginx
├── docker-compose.yml       # Producción
├── docker-compose.dev.yml   # Desarrollo
├── Makefile                # Comandos útiles
└── README.md
```

## 🔐 Credenciales por Defecto

### 👥 Usuarios de Prueba Disponibles

```bash
# Administradores
Email: admin.bugaba@financepro.com    | Password: admin123 | Role: admin
Email: admin.david@financepro.com     | Password: admin123 | Role: admin

# Managers
Email: manager.bugaba@financepro.com  | Password: admin123 | Role: manager  
Email: manager.david@financepro.com   | Password: admin123 | Role: manager

# Empleados
Email: empleado.bugaba@financepro.com | Password: admin123 | Role: employee
Email: empleado.david@financepro.com  | Password: admin123 | Role: employee
```

**Sucursales disponibles:**
- Sucursal Bugaba (ID: e16de67c-f755-47e0-ab1b-ee6b424c2947)
- Sucursal David (ID: 9e25bb1b-102d-4835-b542-1ebe2b8cf503)

## 🌐 Endpoints Principales

### ✅ Disponibles y Funcionales
- `GET /api/v1/health/` - Health check del sistema
- `GET /api/v1/sucursales/` - Lista de sucursales activas
- `POST /api/v1/auth/login` - Login con selección de sucursal
- `POST /api/v1/auth/login-simple` - Login simplificado 
- `POST /api/v1/auth/verify-2fa` - Verificar código 2FA
- `POST /api/v1/auth/refresh` - Renovar token
- `POST /api/v1/auth/logout` - Cerrar sesión

### 🚧 En Desarrollo (Próximamente)
- `GET /api/v1/users/` - Listar usuarios
- `GET /api/v1/loans/` - Listar préstamos
- `GET /api/v1/clients/` - Listar clientes
- `GET /api/v1/users/me` - Usuario actual

## 🔧 Configuración Avanzada

### Variables de Entorno Importantes

```bash
# Base de datos
DATABASE_URL=postgresql://postgres:password@db:5432/financepro

# Seguridad
SECRET_KEY=your-super-secret-key-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Personalización de Puertos

Editar `docker-compose.yml` o `docker-compose.dev.yml`:

```yaml
services:
  frontend:
    ports:
      - "3001:80"  # Cambiar puerto del frontend
  backend:
    ports:
      - "8001:8000"  # Cambiar puerto del backend
```

## 🧪 Testing

```bash
# Ejecutar tests del backend
make test

# Tests específicos
docker-compose -f docker-compose.dev.yml exec backend pytest tests/test_auth.py
```

## 📊 Monitoreo

### Logs
```bash
# Ver todos los logs
make logs

# Logs específicos
make logs-backend
make logs-frontend
make logs-db
```

### Health Checks
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000

## 🚀 Despliegue en Producción

### 1. Configurar variables de producción
```bash
cp .env.example .env.prod
# Editar .env.prod con configuraciones de producción
```

### 2. Usar configuración de producción
```bash
export COMPOSE_FILE=docker-compose.yml
export COMPOSE_PROJECT_NAME=financepro_prod
make prod
```

### 3. Configurar SSL (opcional)
Agregar certificados SSL en `nginx/ssl/` y actualizar `nginx/nginx.conf`.

## 🔒 Seguridad

- Cambiar `SECRET_KEY` en producción
- Usar contraseñas seguras para la base de datos
- Configurar HTTPS con certificados SSL
- Implementar rate limiting
- Configurar firewall apropiadamente

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📝 Roadmap - Próximas Funcionalidades

### v1.3.0 - Gestión de Usuarios
- [ ] Endpoint `GET /api/v1/users/` - Listar usuarios
- [ ] Endpoint `GET /api/v1/users/me` - Perfil de usuario
- [ ] Endpoint `PUT /api/v1/users/{id}` - Actualizar usuario
- [ ] Frontend para gestión de usuarios
- [ ] Roles y permisos avanzados

### v1.4.0 - CRUD de Clientes
- [ ] CRUD completo de clientes
- [ ] Búsqueda y filtros avanzados
- [ ] Validación de documentos (cédula, pasaporte)
- [ ] Historial de clientes

### v1.5.0 - Sistema de Préstamos
- [ ] CRUD completo de préstamos
- [ ] Calculadora de cuotas
- [ ] Estados de préstamos
- [ ] Sistema de pagos
- [ ] Reportes de mora

### Futuras Versiones
- [ ] Dashboard con métricas y gráficos
- [ ] Sistema de notificaciones
- [ ] Integración con servicios de pago
- [ ] API para aplicaciones móviles
- [ ] Backup automático
- [ ] Auditoría avanzada

## 📄 Licencia

Este proyecto es privado y confidencial.

---

Desarrollado con ❤️ para FinancePro

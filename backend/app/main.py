from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
import structlog

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.middleware import (
    SecurityHeadersMiddleware,
    AuditMiddleware,
    RateLimitMiddleware,
    SessionSecurityMiddleware,
    InputSanitizationMiddleware,
    rate_limit_handler,
    limiter
)
from app.services.search_service import search_service
from app.services.messaging_service import messaging_service
from app.core.init_db import init_database

# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Crear instancia de FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API Segura para Sistema de Préstamos FinancePro",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    # Configuración de seguridad para OpenAPI
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Operaciones de autenticación y autorización"
        },
        {
            "name": "users",
            "description": "Gestión de usuarios (requiere autenticación)"
        },
        {
            "name": "loans",
            "description": "Gestión de préstamos (requiere autenticación)"
        },
        {
            "name": "clients",
            "description": "Gestión de clientes (requiere autenticación)"
        }
    ]
)

# Eventos de inicio y cierre de la aplicación
@app.on_event("startup")
async def startup_event():
    """Inicializar servicios al arrancar la aplicación"""
    logger = structlog.get_logger(__name__)
    
    try:
        # Inicializar base de datos y datos de prueba
        logger.info("Inicializando base de datos...")
        try:
            init_database()
            logger.info("Base de datos inicializada correctamente")
        except Exception as db_error:
            logger.error("Error al inicializar base de datos", error=str(db_error))
            # No continuar si la base de datos falla
            raise
        
        # Inicializar servicios de búsqueda
        if settings.ENABLE_FULL_TEXT_SEARCH:
            logger.info("Inicializando servicio de búsqueda...")
            try:
                await search_service.initialize_indexes()
                logger.info("Servicio de búsqueda inicializado")
            except Exception as search_error:
                logger.warning("Error al inicializar búsqueda, continuando sin ella", error=str(search_error))
        
        # Inicializar servicios de mensajería
        if settings.ENABLE_ASYNC_PROCESSING:
            logger.info("Inicializando servicio de mensajería...")
            try:
                await messaging_service.connect()
                logger.info("Servicio de mensajería inicializado")
            except Exception as messaging_error:
                logger.warning("Error al inicializar mensajería, continuando sin ella", error=str(messaging_error))
        
        logger.info("Aplicación iniciada correctamente")
        
    except Exception as e:
        logger.error("Error durante el inicio de la aplicación", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Limpiar recursos al cerrar la aplicación"""
    logger = structlog.get_logger(__name__)
    
    try:
        # Cerrar conexión de mensajería
        if settings.ENABLE_ASYNC_PROCESSING:
            logger.info("Cerrando servicio de mensajería...")
            await messaging_service.disconnect()
            logger.info("Servicio de mensajería cerrado")
        
        logger.info("Aplicación cerrada correctamente")
        
    except Exception as e:
        logger.error("Error durante el cierre de la aplicación", error=str(e))

# Agregar middleware de seguridad (orden importante)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditMiddleware)
# app.add_middleware(InputSanitizationMiddleware)  # Deshabilitado para desarrollo
# app.add_middleware(SessionSecurityMiddleware)    # Deshabilitado para desarrollo
# app.add_middleware(RateLimitMiddleware)          # Deshabilitado para desarrollo

# Configurar CORS (después de middleware de seguridad)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "User-Agent",
        "DNT",
        "Cache-Control",
        "X-Mx-ReqToken",
        "Keep-Alive",
        "X-Requested-With",
        "If-Modified-Since",
    ],
    expose_headers=["X-Total-Count"],
)

# Middleware de hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)

# Configurar rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Incluir rutas de la API
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    """Endpoint raíz de la API"""
    return JSONResponse({
        "message": "FinancePro API Segura",
        "version": settings.VERSION,
        "status": "active",
        "security": "enabled",
        "docs": f"{settings.API_V1_STR}/docs",
        "features": [
            "Encriptación de datos PII",
            "Auditoría completa",
            "Rate limiting",
            "Headers de seguridad",
            "Validación de entrada",
            "Autenticación JWT",
            "2FA habilitado"
        ]
    })


@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request):
    """Endpoint de verificación de salud con información de seguridad"""
    import time
    from datetime import datetime
    
    return JSONResponse({
        "status": "healthy",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": time.time(),
        "security_features": {
            "encryption_enabled": settings.ENCRYPT_PII_DATA,
            "audit_enabled": settings.ENABLE_AUDIT_LOG,
            "2fa_required": settings.REQUIRE_2FA,
            "rate_limiting": True,
            "secure_headers": True
        }
    })


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

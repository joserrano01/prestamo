"""
Middleware de seguridad para la aplicación
"""
import time
import json
from typing import Callable
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
import structlog

from app.core.config import settings
from app.core.security import audit_logger

# Configurar logger estructurado
logger = structlog.get_logger()

# Configurar Redis para rate limiting
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Configurar rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["100/minute"]
)


class SecurityHeadersMiddleware:
    """Middleware para agregar headers de seguridad"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Headers de seguridad
                    security_headers = {
                        b"x-content-type-options": b"nosniff",
                        b"x-frame-options": b"DENY",
                        b"x-xss-protection": b"1; mode=block",
                        b"strict-transport-security": b"max-age=31536000; includeSubDomains",
                        b"referrer-policy": b"strict-origin-when-cross-origin",
                        b"permissions-policy": b"camera=(), microphone=(), geolocation=()",
                        b"content-security-policy": b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                    }
                    
                    # Agregar headers de seguridad
                    for key, value in security_headers.items():
                        headers[key] = value
                    
                    # Remover headers que revelan información del servidor
                    headers.pop(b"server", None)
                    
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


class AuditMiddleware:
    """Middleware para auditoría de requests"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            start_time = time.time()
            
            # Información del request
            ip_address = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "")
            method = request.method
            path = request.url.path
            
            # Log del request entrante
            logger.info(
                "request_started",
                method=method,
                path=path,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Procesar request
            response = Response()
            
            async def send_wrapper(message):
                nonlocal response
                if message["type"] == "http.response.start":
                    response.status_code = message["status"]
                elif message["type"] == "http.response.body":
                    # Log del response
                    process_time = time.time() - start_time
                    
                    logger.info(
                        "request_completed",
                        method=method,
                        path=path,
                        status_code=response.status_code,
                        process_time=process_time,
                        ip_address=ip_address
                    )
                    
                    # Auditar accesos a endpoints sensibles
                    if self._is_sensitive_endpoint(path):
                        await self._audit_sensitive_access(
                            request, response.status_code, ip_address, user_agent
                        )
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP real del cliente considerando proxies"""
        # Verificar headers de proxy
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Verificar si el endpoint es sensible"""
        sensitive_paths = [
            "/api/v1/auth/login",
            "/api/v1/clients/",
            "/api/v1/loans/",
            "/api/v1/users/",
        ]
        
        return any(path.startswith(sensitive_path) for sensitive_path in sensitive_paths)
    
    async def _audit_sensitive_access(
        self, request: Request, status_code: int, ip_address: str, user_agent: str
    ):
        """Auditar acceso a endpoints sensibles"""
        try:
            # Obtener información del usuario si está autenticado
            user_id = getattr(request.state, "user_id", None)
            
            audit_logger.log_data_access(
                user_id=user_id or "anonymous",
                resource_type="api_endpoint",
                resource_id=request.url.path,
                action=request.method.lower(),
                ip_address=ip_address
            )
        except Exception as e:
            logger.error("audit_error", error=str(e))


class RateLimitMiddleware:
    """Middleware personalizado para rate limiting avanzado"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Aplicar rate limiting específico por endpoint
            if await self._should_rate_limit(request):
                if await self._is_rate_limited(request):
                    response = JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "message": "Too many requests. Please try again later.",
                            "retry_after": 60
                        }
                    )
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
    
    async def _should_rate_limit(self, request: Request) -> bool:
        """Determinar si se debe aplicar rate limiting"""
        # Rate limiting más estricto para endpoints de autenticación
        auth_endpoints = ["/api/v1/auth/login", "/api/v1/auth/verify-2fa"]
        return any(request.url.path.startswith(endpoint) for endpoint in auth_endpoints)
    
    async def _is_rate_limited(self, request: Request) -> bool:
        """Verificar si el cliente ha excedido el rate limit"""
        client_ip = self._get_client_ip(request)
        
        # Rate limit específico para login: 5 intentos por 15 minutos
        if request.url.path.startswith("/api/v1/auth/login"):
            key = f"login_attempts:{client_ip}"
            attempts = redis_client.get(key)
            
            if attempts and int(attempts) >= 5:
                return True
            
            # Incrementar contador
            redis_client.incr(key)
            redis_client.expire(key, 900)  # 15 minutos
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class SessionSecurityMiddleware:
    """Middleware para seguridad de sesiones"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Verificar token de autorización
            if await self._requires_auth(request):
                auth_header = request.headers.get("authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    response = JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"error": "Missing or invalid authorization header"}
                    )
                    await response(scope, receive, send)
                    return
                
                token = auth_header.split(" ")[1]
                if not await self._validate_token(token, request):
                    response = JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"error": "Invalid or expired token"}
                    )
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
    
    async def _requires_auth(self, request: Request) -> bool:
        """Verificar si el endpoint requiere autenticación"""
        public_endpoints = [
            "/api/v1/auth/login",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/"
        ]
        
        path = request.url.path
        return not any(path.startswith(endpoint) for endpoint in public_endpoints)
    
    async def _validate_token(self, token: str, request: Request) -> bool:
        """Validar token JWT"""
        try:
            from app.core.security import TokenSecurity
            
            payload = TokenSecurity.verify_token(token)
            if not payload:
                return False
            
            # Agregar información del usuario al request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.user_role = payload.get("role")
            
            # Verificar expiración de sesión
            issued_at = payload.get("iat")
            if issued_at:
                session_duration = datetime.utcnow().timestamp() - issued_at
                max_session_duration = settings.SESSION_TIMEOUT_MINUTES * 60
                
                if session_duration > max_session_duration:
                    return False
            
            return True
            
        except Exception as e:
            logger.error("token_validation_error", error=str(e))
            return False


class InputSanitizationMiddleware:
    """Middleware para sanitización de inputs"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Solo sanitizar requests con body
            if request.method in ["POST", "PUT", "PATCH"]:
                # Leer y sanitizar el body
                body = await request.body()
                if body:
                    try:
                        data = json.loads(body)
                        sanitized_data = self._sanitize_data(data)
                        
                        # Reemplazar el body con datos sanitizados
                        new_body = json.dumps(sanitized_data).encode()
                        
                        async def receive_wrapper():
                            return {
                                "type": "http.request",
                                "body": new_body,
                                "more_body": False
                            }
                        
                        await self.app(scope, receive_wrapper, send)
                        return
                    except json.JSONDecodeError:
                        pass
        
        await self.app(scope, receive, send)
    
    def _sanitize_data(self, data):
        """Sanitizar datos de entrada"""
        import bleach
        
        if isinstance(data, dict):
            return {key: self._sanitize_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif isinstance(data, str):
            # Sanitizar HTML y scripts
            return bleach.clean(data, tags=[], attributes={}, strip=True)
        else:
            return data


# Handler para rate limit exceeded
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handler personalizado para rate limit exceeded"""
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate limit exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": 60
        }
    )
    return response

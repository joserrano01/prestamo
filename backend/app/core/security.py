"""
Módulo de seguridad para encriptación de datos sensibles
"""
import base64
import hashlib
import secrets
from typing import Optional, Union
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext
from jose import JWTError, jwt

from app.core.config import settings


class DataEncryption:
    """Clase para encriptación de datos sensibles"""
    
    def __init__(self, master_key: Optional[str] = None):
        """
        Inicializar el sistema de encriptación
        
        Args:
            master_key: Clave maestra para encriptación. Si no se proporciona, usa la del config
        """
        self.master_key = master_key or settings.ENCRYPTION_KEY
        self._fernet = self._create_fernet_key()
    
    def _create_fernet_key(self) -> Fernet:
        """Crear clave Fernet a partir de la clave maestra"""
        # Usar la clave maestra para generar una clave Fernet
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'financepro_salt_2025',  # Salt fijo para consistencia
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """
        Encriptar datos sensibles
        
        Args:
            data: Datos a encriptar
            
        Returns:
            Datos encriptados en base64
        """
        if not data:
            return data
        
        encrypted_data = self._fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Desencriptar datos
        
        Args:
            encrypted_data: Datos encriptados en base64
            
        Returns:
            Datos desencriptados
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._fernet.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Error al desencriptar datos: {str(e)}")
    
    def encrypt_pii(self, pii_data: dict) -> dict:
        """
        Encriptar datos de información personal identificable (PII)
        
        Args:
            pii_data: Diccionario con datos PII
            
        Returns:
            Diccionario con datos PII encriptados
        """
        sensitive_fields = [
            'rfc', 'curp', 'telefono', 'direccion', 'numero_cuenta',
            'clabe', 'numero_tarjeta', 'fecha_nacimiento'
        ]
        
        encrypted_data = pii_data.copy()
        
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        
        return encrypted_data
    
    def decrypt_pii(self, encrypted_pii_data: dict) -> dict:
        """
        Desencriptar datos PII
        
        Args:
            encrypted_pii_data: Diccionario con datos PII encriptados
            
        Returns:
            Diccionario con datos PII desencriptados
        """
        sensitive_fields = [
            'rfc', 'curp', 'telefono', 'direccion', 'numero_cuenta',
            'clabe', 'numero_tarjeta', 'fecha_nacimiento'
        ]
        
        decrypted_data = encrypted_pii_data.copy()
        
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except ValueError:
                    # Si no se puede desencriptar, mantener el valor original
                    pass
        
        return decrypted_data


class PasswordSecurity:
    """Clase para manejo seguro de contraseñas"""
    
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto",
            bcrypt__rounds=12  # Aumentar rounds para mayor seguridad
        )
    
    def hash_password(self, password: str) -> str:
        """Hash de contraseña con bcrypt"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verificar contraseña"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generar contraseña segura"""
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class TokenSecurity:
    """Clase para manejo seguro de tokens JWT"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear token de acceso JWT
        
        Args:
            data: Datos a incluir en el token
            expires_delta: Tiempo de expiración
            
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        # Agregar claims adicionales de seguridad
        to_encode.update({
            "iss": "financepro",  # Issuer
            "aud": "financepro-client",  # Audience
            "jti": secrets.token_urlsafe(32),  # JWT ID único
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verificar y decodificar token JWT
        
        Args:
            token: Token JWT a verificar
            
        Returns:
            Payload del token si es válido, None si no
        """
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM],
                audience="financepro-client",
                issuer="financepro"
            )
            return payload
        except JWTError:
            return None


class AuditLogger:
    """Clase para logging de auditoría de seguridad"""
    
    @staticmethod
    def log_access_attempt(
        user_id: Optional[str],
        email: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        failure_reason: Optional[str] = None
    ):
        """
        Log de intentos de acceso
        
        Args:
            user_id: ID del usuario (si existe)
            email: Email usado en el intento
            ip_address: Dirección IP
            user_agent: User agent del navegador
            success: Si el intento fue exitoso
            failure_reason: Razón del fallo si aplica
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "login_attempt",
            "user_id": user_id,
            "email": email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "failure_reason": failure_reason
        }
        
        # En producción, esto debería ir a un sistema de logging seguro
        print(f"AUDIT LOG: {log_data}")
    
    @staticmethod
    def log_data_access(
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: str
    ):
        """
        Log de acceso a datos sensibles
        
        Args:
            user_id: ID del usuario
            resource_type: Tipo de recurso (cliente, prestamo, etc.)
            resource_id: ID del recurso
            action: Acción realizada (read, create, update, delete)
            ip_address: Dirección IP
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "data_access",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "ip_address": ip_address
        }
        
        print(f"AUDIT LOG: {log_data}")


class DataMasking:
    """Clase para enmascaramiento de datos sensibles"""
    
    @staticmethod
    def mask_rfc(rfc: str) -> str:
        """Enmascarar RFC dejando solo los primeros 4 caracteres"""
        if not rfc or len(rfc) < 4:
            return "****"
        return rfc[:4] + "*" * (len(rfc) - 4)
    
    @staticmethod
    def mask_curp(curp: str) -> str:
        """Enmascarar CURP dejando solo los primeros 4 caracteres"""
        if not curp or len(curp) < 4:
            return "****"
        return curp[:4] + "*" * (len(curp) - 4)
    
    @staticmethod
    def mask_phone(phone: str) -> str:
        """Enmascarar teléfono dejando solo los últimos 4 dígitos"""
        if not phone or len(phone) < 4:
            return "****"
        return "*" * (len(phone) - 4) + phone[-4:]
    
    @staticmethod
    def mask_account_number(account: str) -> str:
        """Enmascarar número de cuenta dejando solo los últimos 4 dígitos"""
        if not account or len(account) < 4:
            return "****"
        return "*" * (len(account) - 4) + account[-4:]
    
    @staticmethod
    def mask_email(email: str) -> str:
        """Enmascarar email parcialmente"""
        if not email or "@" not in email:
            return "****@****.***"
        
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = "*" * len(local)
        else:
            masked_local = local[:2] + "*" * (len(local) - 2)
        
        return f"{masked_local}@{domain}"


def mask_sensitive_data(data: dict) -> dict:
    """
    Función utilitaria para enmascarar datos sensibles en un diccionario
    
    Args:
        data: Diccionario con datos que pueden contener información sensible
        
    Returns:
        Diccionario con datos sensibles enmascarados
    """
    if not isinstance(data, dict):
        return data
    
    masked_data = data.copy()
    
    # Campos que necesitan enmascaramiento
    sensitive_fields = {
        'rfc': data_masking.mask_rfc,
        'curp': data_masking.mask_curp,
        'telefono': data_masking.mask_phone,
        'numero_cuenta': data_masking.mask_account_number,
        'clabe': data_masking.mask_account_number,
        'numero_tarjeta': data_masking.mask_account_number,
        'email': data_masking.mask_email,
    }
    
    for field, mask_func in sensitive_fields.items():
        if field in masked_data and masked_data[field]:
            masked_data[field] = mask_func(str(masked_data[field]))
    
    # Enmascarar campos anidados si existen
    for key, value in masked_data.items():
        if isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        elif isinstance(value, list):
            masked_data[key] = [mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
    
    return masked_data


def log_audit_event(event_type: str, user_id: str, details: dict, ip_address: str = None):
    """
    Función utilitaria para registrar eventos de auditoría
    
    Args:
        event_type: Tipo de evento (search, access, etc.)
        user_id: ID del usuario que realiza la acción
        details: Detalles adicionales del evento
        ip_address: Dirección IP del usuario
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "details": details,
        "ip_address": ip_address
    }
    
    # En producción, esto debería ir a un sistema de logging seguro
    print(f"AUDIT LOG: {log_data}")


# Instancias globales
data_encryption = DataEncryption()
password_security = PasswordSecurity()
audit_logger = AuditLogger()
data_masking = DataMasking()

# Funciones utilitarias para contraseñas
def hash_password(password: str) -> str:
    """Hash de contraseña usando bcrypt"""
    return password_security.hash_password(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña contra hash"""
    return password_security.verify_password(plain_password, hashed_password)


def require_permissions(user, required_permissions: list) -> bool:
    """
    Verificar si un usuario tiene los permisos requeridos
    
    Args:
        user: Usuario a verificar
        required_permissions: Lista de permisos requeridos
        
    Returns:
        True si el usuario tiene al menos uno de los permisos requeridos
    """
    if not user:
        return False
    
    # Verificar si el usuario tiene alguno de los permisos requeridos
    user_role = getattr(user, 'rol', '').lower()
    
    # Admin siempre tiene todos los permisos
    if user_role == 'admin':
        return True
    
    # Verificar permisos específicos
    for permission in required_permissions:
        if user_role == permission.lower():
            return True
    
    return False

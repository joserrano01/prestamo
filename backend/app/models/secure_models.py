"""
Modelos de base de datos con encriptación de datos sensibles
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, BigInteger, Numeric, ForeignKey, Index, Time, Date, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
import uuid

from app.core.security import data_encryption, password_security

Base = declarative_base()


class EncryptedColumn:
    """Descriptor para columnas encriptadas"""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        encrypted_value = getattr(instance, f"_{self.column_name}")
        if encrypted_value and hasattr(instance, '_decrypt_enabled') and instance._decrypt_enabled:
            try:
                return data_encryption.decrypt(encrypted_value)
            except Exception:
                return encrypted_value
        return encrypted_value
    
    def __set__(self, instance, value):
        if value and hasattr(instance, '_encrypt_enabled') and instance._encrypt_enabled:
            encrypted_value = data_encryption.encrypt(str(value))
            setattr(instance, f"_{self.column_name}", encrypted_value)
        else:
            setattr(instance, f"_{self.column_name}", value)


class SecureBaseModel:
    """Clase base para modelos con funcionalidades de seguridad"""
    
    def __init__(self, *args, **kwargs):
        self._encrypt_enabled = True
        self._decrypt_enabled = True
        super().__init__(*args, **kwargs)
    
    def enable_encryption(self):
        """Habilitar encriptación para este modelo"""
        self._encrypt_enabled = True
    
    def disable_encryption(self):
        """Deshabilitar encriptación (solo para migración de datos)"""
        self._encrypt_enabled = False
    
    def enable_decryption(self):
        """Habilitar desencriptación para este modelo"""
        self._decrypt_enabled = True
    
    def disable_decryption(self):
        """Deshabilitar desencriptación (para datos enmascarados)"""
        self._decrypt_enabled = False


class BasicAuditMixin:
    """Mixin básico para auditoría de modelos"""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    
    # Relaciones para auditoría
    @declared_attr
    def usuario_creador(cls):
        return relationship("Usuario", foreign_keys=[cls.created_by], post_update=True)
    
    @declared_attr
    def usuario_actualizador(cls):
        return relationship("Usuario", foreign_keys=[cls.updated_by], post_update=True)


class AuditMixin(BasicAuditMixin):
    """Mixin completo para auditoría de modelos con seguimiento de acceso"""
    
    # Campos para auditoría de seguridad
    last_accessed_at = Column(DateTime, nullable=True)
    last_accessed_by = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    access_count = Column(Integer, default=0)
    
    # Relación para auditoría de acceso
    @declared_attr
    def usuario_ultimo_acceso(cls):
        return relationship("Usuario", foreign_keys=[cls.last_accessed_by], post_update=True)


class Sucursal(Base, AuditMixin):
    """Modelo de sucursales con geolocalización y múltiples teléfonos"""
    __tablename__ = "sucursales"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(255), nullable=False)
    direccion = Column(Text, nullable=True)
    
    # Información de geolocalización
    latitud = Column(Numeric(precision=10, scale=8), nullable=True, comment="Latitud en grados decimales")
    longitud = Column(Numeric(precision=11, scale=8), nullable=True, comment="Longitud en grados decimales")
    altitud = Column(Numeric(precision=8, scale=2), nullable=True, comment="Altitud en metros")
    
    # Información adicional de ubicación
    ciudad = Column(String(100), nullable=True)
    provincia = Column(String(100), nullable=True)
    codigo_postal = Column(String(20), nullable=True)
    pais = Column(String(100), default='Panamá', nullable=False)
    
    # Información administrativa
    manager = Column(String(255), nullable=True)
    email_sucursal = Column(String(255), nullable=True)
    horario_apertura = Column(Time, nullable=True)
    horario_cierre = Column(Time, nullable=True)
    dias_operacion = Column(String(50), default='Lunes-Sabado', nullable=True)  # Ej: "Lunes-Viernes", "Lunes-Sábado"
    
    # Estado y configuración
    is_active = Column(Boolean, default=True, nullable=False)
    permite_prestamos = Column(Boolean, default=True, nullable=False)
    limite_prestamo_diario = Column(Numeric(precision=15, scale=2), nullable=True)
    
    # Relaciones
    usuarios = relationship("Usuario", back_populates="sucursal", foreign_keys="Usuario.sucursal_id")
    prestamos = relationship("Prestamo", back_populates="sucursal")
    telefonos = relationship("SucursalTelefono", back_populates="sucursal", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sucursal(codigo='{self.codigo}', nombre='{self.nombre}', ciudad='{self.ciudad}')>"
    
    @property
    def coordenadas(self):
        """Retorna las coordenadas como tupla (latitud, longitud)"""
        if self.latitud and self.longitud:
            return (float(self.latitud), float(self.longitud))
        return None
    
    @property
    def ubicacion_completa(self):
        """Retorna la dirección completa formateada"""
        partes = []
        if self.direccion:
            partes.append(self.direccion)
        if self.ciudad:
            partes.append(self.ciudad)
        if self.provincia:
            partes.append(self.provincia)
        if self.codigo_postal:
            partes.append(self.codigo_postal)
        return ', '.join(partes) if partes else None


class SucursalTelefono(Base, BasicAuditMixin):
    """Modelo para múltiples teléfonos de sucursales"""
    __tablename__ = "sucursal_telefonos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey('sucursales.id', ondelete='CASCADE'), nullable=False)
    numero = Column(String(20), nullable=False)
    tipo = Column(String(50), default='principal', nullable=False)  # principal, secundario, fax, movil, whatsapp
    extension = Column(String(10), nullable=True)
    descripcion = Column(String(255), nullable=True)  # Ej: "Línea directa gerencia", "Atención al cliente"
    is_active = Column(Boolean, default=True, nullable=False)
    is_whatsapp = Column(Boolean, default=False, nullable=False)
    is_publico = Column(Boolean, default=True, nullable=False)  # Si se muestra públicamente
    
    # Relaciones
    sucursal = relationship("Sucursal", back_populates="telefonos")
    
    # Índices
    __table_args__ = (
        Index('idx_sucursal_telefono_numero', 'numero'),
        Index('idx_sucursal_telefono_tipo', 'tipo'),
        Index('idx_sucursal_telefono_sucursal', 'sucursal_id'),
    )
    
    def __repr__(self):
        return f"<SucursalTelefono(numero='{self.numero}', tipo='{self.tipo}')>"
    
    @property
    def numero_formateado(self):
        """Retorna el número formateado con extensión si existe"""
        if self.extension:
            return f"{self.numero} ext. {self.extension}"
        return self.numero


class Usuario(Base, SecureBaseModel, AuditMixin):
    """Modelo de usuarios con seguridad mejorada"""
    __tablename__ = "usuarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_usuario = Column(String(50), unique=True, nullable=False, index=True)  # Código único de usuario
    codigo_empleado = Column(String(50), unique=True, nullable=True, index=True)  # Código de empleado (EMP001, EMP002, etc.)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    apellido = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default='employee')
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey('sucursales.id'), nullable=True)
    
    # Campos de seguridad
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 2FA
    two_fa_secret = Column(String(255), nullable=True)  # Encriptado
    two_fa_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes = Column(Text, nullable=True)  # JSON encriptado con códigos de respaldo
    
    # Relaciones
    sucursal = relationship("Sucursal", back_populates="usuarios", foreign_keys=[sucursal_id])
    prestamos_creados = relationship("Prestamo", back_populates="usuario", foreign_keys="Prestamo.usuario_id")
    audit_logs = relationship("AuditLog", back_populates="usuario")
    emails = relationship("UsuarioEmail", back_populates="usuario", cascade="all, delete-orphan", foreign_keys="UsuarioEmail.usuario_id")
    
    def set_password(self, password: str):
        """Establecer contraseña con hash seguro"""
        self.password_hash = password_security.hash_password(password)
        self.last_password_change = datetime.utcnow()
    
    def verify_password(self, password: str) -> bool:
        """Verificar contraseña"""
        return password_security.verify_password(password, self.password_hash)
    
    def is_locked(self) -> bool:
        """Verificar si la cuenta está bloqueada"""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    @property
    def email_principal(self) -> str:
        """Obtener el email principal del usuario"""
        for email in self.emails:
            if email.is_principal and email.is_active:
                return email.email
        return None
    
    def set_email_principal(self, nuevo_email: str, db_session) -> bool:
        """Establecer un nuevo email como principal"""
        try:
            # Desmarcar el email principal actual
            for email in self.emails:
                if email.is_principal:
                    email.is_principal = False
            
            # Buscar el nuevo email y marcarlo como principal
            for email in self.emails:
                if email.email == nuevo_email and email.is_active:
                    email.is_principal = True
                    db_session.commit()
                    return True
            
            return False
        except Exception:
            db_session.rollback()
            return False
    
    def get_emails_activos(self) -> list:
        """Obtener todos los emails activos del usuario"""
        return [email.email for email in self.emails if email.is_active]
    
    def get_emails_verificados(self) -> list:
        """Obtener todos los emails verificados y activos del usuario"""
        return [email.email for email in self.emails if email.is_verified and email.is_active]
    
    def __repr__(self):
        return f"<Usuario(codigo='{self.codigo_usuario}', empleado='{self.codigo_empleado}', nombre='{self.nombre}', email_principal='{self.email_principal}')>"


class UsuarioEmail(Base, AuditMixin):
    """Modelo para todos los emails de usuarios (incluyendo el principal)"""
    __tablename__ = "usuario_emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    tipo = Column(String(50), nullable=False, default='secundario')  # principal, secundario, trabajo, personal
    is_principal = Column(Boolean, default=False, nullable=False)  # Solo uno puede ser principal por usuario
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="emails", foreign_keys=[usuario_id])
    
    # Índices y constraints
    __table_args__ = (
        Index('idx_usuario_email_usuario', 'usuario_id'),
        Index('idx_usuario_email_email', 'email'),
        Index('idx_usuario_email_tipo', 'tipo'),
        Index('idx_usuario_email_principal', 'is_principal'),
        # Constraint para asegurar que solo hay un email principal por usuario
        # Se implementará a nivel de aplicación para mayor flexibilidad
    )


class Cliente(Base, AuditMixin):
    """Modelo de clientes con datos encriptados"""
    __tablename__ = "clientes"
    
    # Información básica
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_cliente = Column(String(50), unique=True, nullable=True, index=True, comment="Código único del cliente")
    
    # Información personal (encriptada)
    _nombre = Column("nombre", String(500), nullable=False)
    _segundo_nombre = Column("segundo_nombre", String(500), nullable=True)
    _apellido_paterno = Column("apellido_paterno", String(500), nullable=False)
    _apellido_materno = Column("apellido_materno", String(500), nullable=True)
    _fecha_nacimiento = Column("fecha_nacimiento", String(500), nullable=True)
    _genero = Column("genero", String(20), nullable=True)
    _estado_civil = Column("estado_civil", String(50), nullable=True)
    _nacionalidad = Column("nacionalidad", String(100), nullable=True, default='Panameño/a')
    
    # Documentos de identificación (encriptados)
    _tipo_identificacion = Column("tipo_identificacion", String(50), nullable=True)
    _numero_identificacion = Column("numero_identificacion", String(500), nullable=True, index=True)
    _cedula = Column("cedula", String(500), nullable=True, comment="Cédula de identidad panameña")
    _fecha_vencimiento_cedula = Column("fecha_vencimiento_cedula", String(500), nullable=True, comment="Fecha de vencimiento de la cédula")
    _pasaporte = Column("pasaporte", String(500), nullable=True, comment="Número de pasaporte")
    _fecha_vencimiento_pasaporte = Column("fecha_vencimiento_pasaporte", String(500), nullable=True, comment="Fecha de vencimiento del pasaporte")
    _css = Column("css", String(500), nullable=True, comment="Número de Caja de Seguro Social")
    
    # Los emails ahora se manejan en tabla separada ClienteEmail
    
    # Información laboral actual (encriptada)
    _empresa_actual = Column("empresa_actual", String(500), nullable=True)
    _puesto_actual = Column("puesto_actual", String(500), nullable=True)
    _ingreso_mensual = Column("ingreso_mensual", String(500), nullable=True)
    _comisiones = Column("comisiones", String(500), nullable=True, comment="Ingresos por comisiones")
    _otros_ingresos = Column("otros_ingresos", String(500), nullable=True, comment="Otros ingresos")
    
    # Información patrimonial (encriptada)
    _es_propietario_casa = Column("es_propietario_casa", String(500), nullable=True)
    _valor_propiedad = Column("valor_propiedad", String(500), nullable=True)
    _telefono_propiedad = Column("telefono_propiedad", String(500), nullable=True)
    _alquiler_mensual = Column("alquiler_mensual", String(500), nullable=True)
    _hipoteca_mensual = Column("hipoteca_mensual", String(500), nullable=True)
    
    # Los vehículos ahora se manejan en tabla separada ClienteVehiculo
    
    # Las cuentas bancarias ahora se manejan en tabla separada ClienteCuentaBancaria
    
    # Las obligaciones/deudas ahora se manejan en tabla separada ClienteObligacion
    
    # Información adicional
    tipo_cliente = Column(Integer, nullable=True, comment="1=Regular, 2=VIP, 3=Corporativo, etc.")
    estado_cliente = Column(String(20), default='ACTIVO', nullable=False, comment="ACTIVO, INACTIVO, SUSPENDIDO")
    _comentarios = Column("comentarios", Text, nullable=True, comment="Comentarios generales")
    _historial = Column("historial", Text, nullable=True, comment="Historial del cliente")
    
    # Campos de seguridad
    is_active = Column(Boolean, default=True, nullable=False)
    risk_level = Column(String(20), default='medium', nullable=False)  # low, medium, high
    bloqueado = Column(Boolean, default=False, nullable=False)
    motivo_bloqueo = Column(Text, nullable=True)
    
    # Descriptors para encriptación automática
    nombre = EncryptedColumn('nombre')
    segundo_nombre = EncryptedColumn('segundo_nombre')
    apellido_paterno = EncryptedColumn('apellido_paterno')
    apellido_materno = EncryptedColumn('apellido_materno')
    fecha_nacimiento = EncryptedColumn('fecha_nacimiento')
    genero = EncryptedColumn('genero')
    estado_civil = EncryptedColumn('estado_civil')
    nacionalidad = EncryptedColumn('nacionalidad')
    
    tipo_identificacion = EncryptedColumn('tipo_identificacion')  # CEDULA, PASAPORTE, CARNET_EXTRANJERIA
    numero_identificacion = EncryptedColumn('numero_identificacion')
    cedula = EncryptedColumn('cedula')  # Cédula de identidad panameña
    fecha_vencimiento_cedula = EncryptedColumn('fecha_vencimiento_cedula')  # Fecha de vencimiento de cédula
    pasaporte = EncryptedColumn('pasaporte')  # Número de pasaporte
    fecha_vencimiento_pasaporte = EncryptedColumn('fecha_vencimiento_pasaporte')  # Fecha de vencimiento de pasaporte
    css = EncryptedColumn('css')  # Número de Caja de Seguro Social
    
    # Los emails ahora se manejan mediante la relación 'emails'
    
    empresa_actual = EncryptedColumn('empresa_actual')
    puesto_actual = EncryptedColumn('puesto_actual')
    ingreso_mensual = EncryptedColumn('ingreso_mensual')
    comisiones = EncryptedColumn('comisiones')
    otros_ingresos = EncryptedColumn('otros_ingresos')
    
    # Descriptores patrimoniales
    es_propietario_casa = EncryptedColumn('es_propietario_casa')
    valor_propiedad = EncryptedColumn('valor_propiedad')
    telefono_propiedad = EncryptedColumn('telefono_propiedad')
    alquiler_mensual = EncryptedColumn('alquiler_mensual')
    hipoteca_mensual = EncryptedColumn('hipoteca_mensual')
    
    # Los vehículos ahora se manejan mediante la relación 'vehiculos'
    
    # Las cuentas bancarias ahora se manejan mediante la relación 'cuentas_bancarias'
    
    # Las obligaciones ahora se manejan mediante la relación 'obligaciones'
    
    # Descriptores adicionales
    comentarios = EncryptedColumn('comentarios')
    historial = EncryptedColumn('historial')
    
    # Relaciones
    direcciones = relationship("ClienteDireccion", back_populates="cliente", cascade="all, delete-orphan")
    emails = relationship("ClienteEmail", back_populates="cliente", cascade="all, delete-orphan")
    telefonos = relationship("ClienteTelefono", back_populates="cliente", cascade="all, delete-orphan")
    trabajos = relationship("ClienteTrabajo", back_populates="cliente", cascade="all, delete-orphan")
    referencias = relationship("ClienteReferencia", back_populates="cliente", cascade="all, delete-orphan")
    vehiculos = relationship("ClienteVehiculo", back_populates="cliente", cascade="all, delete-orphan")
    propiedades = relationship("ClientePropiedad", back_populates="cliente", cascade="all, delete-orphan")
    cuentas_bancarias = relationship("ClienteCuentaBancaria", back_populates="cliente", cascade="all, delete-orphan")
    obligaciones = relationship("ClienteObligacion", back_populates="cliente", cascade="all, delete-orphan")
    historial = relationship("ClienteHistorial", back_populates="cliente", cascade="all, delete-orphan")
    conversaciones = relationship("ClienteConversacion", back_populates="cliente", cascade="all, delete-orphan")
    solicitudes = relationship("ClienteSolicitud", back_populates="cliente", cascade="all, delete-orphan")
    # actividades_cobranza = relationship("app.models.agenda_models.AgendaCobranza", back_populates="cliente", cascade="all, delete-orphan")
    prestamos = relationship("Prestamo", back_populates="cliente")
    documentos = relationship("Documento", back_populates="cliente")
    
    # Índices
    __table_args__ = (
        Index('idx_cliente_codigo', 'codigo_cliente'),
        Index('idx_cliente_nombre_apellido', 'nombre', 'apellido_paterno'),
        Index('idx_cliente_identificacion', 'tipo_identificacion', 'numero_identificacion'),
        Index('idx_cliente_cedula', 'cedula'),
        Index('idx_cliente_tipo_estado', 'tipo_cliente', 'estado_cliente'),
        Index('idx_cliente_activo', 'is_active'),
        Index('idx_cliente_risk_level', 'risk_level'),
        Index('idx_cliente_bloqueado', 'bloqueado'),
    )
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del cliente"""
        partes = [self.nombre]
        if self.segundo_nombre:
            partes.append(self.segundo_nombre)
        partes.append(self.apellido_paterno)
        if self.apellido_materno:
            partes.append(self.apellido_materno)
        return " ".join(partes)
    
    @property
    def email_principal(self):
        """Retorna el email principal del cliente"""
        for email in self.emails:
            if email.es_principal:
                return email.email
        return None
    
    @property
    def telefono_principal(self):
        """Retorna el teléfono principal del cliente"""
        for telefono in self.telefonos:
            if telefono.es_principal:
                return telefono.numero
        return None
    
    @property
    def direccion_principal(self):
        """Retorna la dirección principal del cliente"""
        for direccion in self.direcciones:
            if direccion.es_principal:
                return direccion
        return None
    
    @property
    def trabajo_actual(self):
        """Retorna el trabajo actual del cliente"""
        for trabajo in self.trabajos:
            if trabajo.es_actual:
                return trabajo
        return None
    
    @property
    def cuenta_bancaria_principal(self):
        """Retorna la cuenta bancaria principal del cliente"""
        for cuenta in self.cuentas_bancarias:
            if cuenta.es_cuenta_principal and cuenta.cuenta_activa:
                return cuenta
        return None
    
    @property
    def cuenta_nomina(self):
        """Retorna la cuenta donde recibe nómina"""
        for cuenta in self.cuentas_bancarias:
            if cuenta.recibe_nomina and cuenta.cuenta_activa:
                return cuenta
        return None
    
    @property
    def cuentas_activas(self):
        """Retorna todas las cuentas activas del cliente"""
        return [cuenta for cuenta in self.cuentas_bancarias if cuenta.cuenta_activa]
    
    @property
    def vehiculo_principal(self):
        """Retorna el vehículo principal del cliente"""
        for vehiculo in self.vehiculos:
            if vehiculo.es_vehiculo_principal and vehiculo.vehiculo_activo:
                return vehiculo
        return None
    
    @property
    def vehiculos_activos(self):
        """Retorna todos los vehículos activos del cliente"""
        return [vehiculo for vehiculo in self.vehiculos if vehiculo.vehiculo_activo]
    
    @property
    def vehiculos_financiados(self):
        """Retorna todos los vehículos financiados activos"""
        return [vehiculo for vehiculo in self.vehiculos if vehiculo.vehiculo_activo and vehiculo.esta_financiado]
    
    @property
    def valor_total_vehiculos(self):
        """Calcula el valor total de los vehículos activos"""
        total = 0
        for vehiculo in self.vehiculos_activos:
            if vehiculo.valor_comercial:
                try:
                    total += float(vehiculo.valor_comercial)
                except (ValueError, TypeError):
                    pass
        return total if total > 0 else 0
    
    @property
    def propiedad_principal(self):
        """Retorna la propiedad principal del cliente"""
        for propiedad in self.propiedades:
            if propiedad.es_propiedad_principal and propiedad.propiedad_activa:
                return propiedad
        return None
    
    @property
    def propiedades_activas(self):
        """Retorna todas las propiedades activas del cliente"""
        return [propiedad for propiedad in self.propiedades if propiedad.propiedad_activa]
    
    @property
    def propiedades_hipotecadas(self):
        """Retorna todas las propiedades hipotecadas activas"""
        return [propiedad for propiedad in self.propiedades if propiedad.propiedad_activa and propiedad.esta_hipotecada]
    
    @property
    def propiedades_rentadas(self):
        """Retorna todas las propiedades que generan ingresos por alquiler"""
        return [propiedad for propiedad in self.propiedades if propiedad.propiedad_activa and propiedad.esta_rentada]
    
    @property
    def valor_total_propiedades(self):
        """Calcula el valor total de las propiedades activas"""
        total = 0
        for propiedad in self.propiedades_activas:
            if propiedad.valor_comercial:
                try:
                    total += float(propiedad.valor_comercial)
                except (ValueError, TypeError):
                    pass
        return total if total > 0 else 0
    
    @property
    def valor_neto_propiedades(self):
        """Calcula el valor neto total de las propiedades (valor comercial - hipotecas)"""
        total = 0
        for propiedad in self.propiedades_activas:
            total += propiedad.valor_neto
        return total
    
    @property
    def ingresos_alquiler_mensual(self):
        """Calcula los ingresos mensuales totales por alquiler de propiedades"""
        total = 0
        for propiedad in self.propiedades_rentadas:
            if propiedad.valor_alquiler:
                try:
                    total += float(propiedad.valor_alquiler)
                except (ValueError, TypeError):
                    pass
        return total
    
    @property
    def ingresos_totales(self):
        """Calcula los ingresos totales estimados"""
        total = 0
        if self.ingreso_mensual:
            try:
                total += float(self.ingreso_mensual)
            except (ValueError, TypeError):
                pass
        if self.comisiones:
            try:
                total += float(self.comisiones)
            except (ValueError, TypeError):
                pass
        if self.otros_ingresos:
            try:
                total += float(self.otros_ingresos)
            except (ValueError, TypeError):
                pass
        total += self.ingresos_alquiler_mensual
        return total if total > 0 else None
    
    def calcular_capacidad_pago(self, porcentaje_ingresos=0.30):
        """Calcula la capacidad de pago basada en ingresos y obligaciones existentes"""
        ingresos = self.ingresos_totales
        if not ingresos:
            return None
        
        gastos_fijos = 0
        
        # Gastos de vivienda
        if self.alquiler_mensual:
            try:
                gastos_fijos += float(self.alquiler_mensual)
            except (ValueError, TypeError):
                pass
        if self.hipoteca_mensual:
            try:
                gastos_fijos += float(self.hipoteca_mensual)
            except (ValueError, TypeError):
                pass
        
        # Sumar cuotas de obligaciones vigentes
        for obligacion in self.obligaciones:
            if obligacion.estado == 'VIGENTE' and obligacion.cuota_mensual:
                try:
                    gastos_fijos += float(obligacion.cuota_mensual)
                except (ValueError, TypeError):
                    pass
        
        # Sumar cuotas de vehículos financiados
        for vehiculo in self.vehiculos_financiados:
            if vehiculo.cuota_mensual:
                try:
                    gastos_fijos += float(vehiculo.cuota_mensual)
                except (ValueError, TypeError):
                    pass
        
        # Sumar cuotas de hipotecas de propiedades
        for propiedad in self.propiedades_hipotecadas:
            if propiedad.cuota_hipoteca:
                try:
                    gastos_fijos += float(propiedad.cuota_hipoteca)
                except (ValueError, TypeError):
                    pass
        
        ingresos_disponibles = ingresos - gastos_fijos
        return ingresos_disponibles * porcentaje_ingresos if ingresos_disponibles > 0 else 0
    
    @property
    def patrimonio_total(self):
        """Calcula el patrimonio total del cliente (propiedades + vehículos + valor propiedad actual)"""
        total = 0
        
        # Valor neto de propiedades (descontando hipotecas)
        total += self.valor_neto_propiedades
        
        # Valor de vehículos
        total += self.valor_total_vehiculos
        
        # Valor de la propiedad actual (si no está en propiedades)
        if self.valor_propiedad and not self.propiedad_principal:
            try:
                valor_propiedad = float(self.valor_propiedad)
                # Descontar hipoteca mensual si existe
                if self.hipoteca_mensual:
                    # Estimamos el saldo de hipoteca como 10 años de cuotas (aproximación)
                    try:
                        saldo_estimado = float(self.hipoteca_mensual) * 120  # 10 años
                        valor_propiedad = max(0, valor_propiedad - saldo_estimado)
                    except (ValueError, TypeError):
                        pass
                total += valor_propiedad
            except (ValueError, TypeError):
                pass
        
        return total
    
    @property
    def historial_reciente(self):
        """Retorna el historial de los últimos 30 días"""
        from datetime import datetime, timedelta
        fecha_limite = datetime.utcnow() - timedelta(days=30)
        return [evento for evento in self.historial if evento.fecha_evento >= fecha_limite]
    
    @property
    def eventos_pendientes(self):
        """Retorna eventos que requieren seguimiento o están pendientes"""
        return [evento for evento in self.historial if evento.requiere_atencion]
    
    @property
    def ultima_interaccion(self):
        """Retorna la última interacción registrada"""
        if not self.historial:
            return None
        return max(self.historial, key=lambda x: x.fecha_evento)
    
    @property
    def conversaciones_recientes(self):
        """Retorna las conversaciones de los últimos 30 días"""
        from datetime import datetime, timedelta
        fecha_limite = datetime.utcnow() - timedelta(days=30)
        return [conv for conv in self.conversaciones if conv.fecha_inicio >= fecha_limite]
    
    @property
    def total_interacciones(self):
        """Cuenta el total de interacciones registradas"""
        return len(self.historial) + len(self.conversaciones)
    
    def dias_desde_ultima_interaccion(self):
        """Calcula cuántos días han pasado desde la última interacción"""
        ultima = self.ultima_interaccion
        if not ultima:
            return None
        
        from datetime import datetime
        diferencia = datetime.utcnow() - ultima.fecha_evento
        return diferencia.days
    
    def obtener_historial_por_tipo(self, tipo_evento):
        """Obtiene el historial filtrado por tipo de evento"""
        return [evento for evento in self.historial if evento.tipo_evento == tipo_evento]
    
    def obtener_conversaciones_por_tipo(self, tipo_conversacion):
        """Obtiene las conversaciones filtradas por tipo"""
        return [conv for conv in self.conversaciones if conv.tipo_conversacion == tipo_conversacion]
    
    @property
    def documentos_pendientes(self):
        """Retorna documentos pendientes de recibir o verificar"""
        return [doc for doc in self.documentos if doc.estado in ['PENDIENTE', 'RECIBIDO']]
    
    @property
    def documentos_vencidos(self):
        """Retorna documentos vencidos"""
        return [doc for doc in self.documentos if doc.esta_vencido]
    
    @property
    def documentos_obligatorios_faltantes(self):
        """Retorna documentos obligatorios que faltan"""
        return [doc for doc in self.documentos if doc.es_obligatorio and doc.estado == 'PENDIENTE']
    
    @property
    def documentos_verificados(self):
        """Retorna documentos verificados"""
        return [doc for doc in self.documentos if doc.esta_verificado]
    
    def obtener_documentos_por_categoria(self, categoria):
        """Obtiene documentos filtrados por categoría"""
        return [doc for doc in self.documentos if doc.categoria == categoria]
    
    def obtener_documentos_por_tipo(self, tipo_documento):
        """Obtiene documentos filtrados por tipo"""
        return [doc for doc in self.documentos if doc.tipo_documento == tipo_documento]
    
    def obtener_documentos_propiedad(self, propiedad_id):
        """Obtiene documentos de una propiedad específica"""
        return [doc for doc in self.documentos if doc.propiedad_id == propiedad_id]
    
    def obtener_documentos_vehiculo(self, vehiculo_id):
        """Obtiene documentos de un vehículo específico"""
        return [doc for doc in self.documentos if doc.vehiculo_id == vehiculo_id]
    
    @property
    def porcentaje_documentos_completos(self):
        """Calcula el porcentaje de documentos completos"""
        if not self.documentos:
            return 0
        
        total_documentos = len(self.documentos)
        documentos_completos = len([doc for doc in self.documentos if doc.esta_verificado])
        
        return int((documentos_completos / total_documentos) * 100)
    
    # Propiedades para gestión de solicitudes
    @property
    def solicitudes_activas(self):
        """Retorna solicitudes activas (no completadas)"""
        return [sol for sol in self.solicitudes if not sol.esta_completada]
    
    @property
    def solicitudes_pendientes_respuesta(self):
        """Retorna solicitudes pendientes de respuesta"""
        return [sol for sol in self.solicitudes if sol.estado in ['RECIBIDA', 'EN_REVISION', 'DOCUMENTOS_PENDIENTES']]
    
    @property
    def solicitudes_vencidas(self):
        """Retorna solicitudes vencidas"""
        return [sol for sol in self.solicitudes if sol.esta_vencida]
    
    @property
    def solicitudes_fuera_sla(self):
        """Retorna solicitudes fuera del SLA"""
        return [sol for sol in self.solicitudes if not sol.esta_en_sla and not sol.esta_completada]
    
    @property
    def solicitudes_requieren_alerta(self):
        """Retorna solicitudes que requieren alerta"""
        return [sol for sol in self.solicitudes if sol.requiere_alerta]
    
    @property
    def ultima_solicitud(self):
        """Retorna la última solicitud del cliente"""
        if self.solicitudes:
            return max(self.solicitudes, key=lambda x: x.fecha_solicitud)
        return None
    
    @property
    def total_solicitudes(self):
        """Cuenta el total de solicitudes"""
        return len(self.solicitudes)
    
    def obtener_solicitudes_por_tipo(self, tipo_solicitud):
        """Obtiene solicitudes filtradas por tipo"""
        return [sol for sol in self.solicitudes if sol.tipo_solicitud == tipo_solicitud]
    
    def obtener_solicitudes_por_estado(self, estado):
        """Obtiene solicitudes filtradas por estado"""
        return [sol for sol in self.solicitudes if sol.estado == estado]
    
    def dias_desde_ultima_solicitud(self):
        """Calcula cuántos días han pasado desde la última solicitud"""
        ultima = self.ultima_solicitud
        if not ultima:
            return None
        
        from datetime import datetime
        diferencia = datetime.utcnow() - ultima.fecha_solicitud
        return diferencia.days
    
    # ========== PROPIEDADES DE AGENDA DE COBRANZA ==========
    
    @property
    def actividades_cobranza_hoy(self):
        """Retorna actividades de cobranza programadas para hoy"""
        from datetime import date
        hoy = date.today()
        return [act for act in self.actividades_cobranza if act.fecha_programada == hoy]
    
    @property
    def actividades_cobranza_pendientes(self):
        """Retorna actividades de cobranza pendientes"""
        return [act for act in self.actividades_cobranza 
                if act.estado in ['PROGRAMADA', 'EN_PROCESO']]
    
    @property
    def actividades_cobranza_vencidas(self):
        """Retorna actividades de cobranza vencidas"""
        return [act for act in self.actividades_cobranza if act.esta_vencida]
    
    @property
    def actividades_cobranza_alta_prioridad(self):
        """Retorna actividades de cobranza de alta prioridad"""
        return [act for act in self.actividades_cobranza 
                if act.prioridad in ['ALTA', 'CRITICA', 'URGENTE']]
    
    @property
    def proxima_actividad_cobranza(self):
        """Retorna la próxima actividad de cobranza programada"""
        from datetime import date
        hoy = date.today()
        
        actividades_futuras = [
            act for act in self.actividades_cobranza 
            if act.fecha_programada >= hoy and act.estado == 'PROGRAMADA'
        ]
        
        if actividades_futuras:
            return min(actividades_futuras, key=lambda x: x.fecha_programada)
        return None
    
    @property
    def ultima_actividad_cobranza(self):
        """Retorna la última actividad de cobranza completada"""
        actividades_completadas = [
            act for act in self.actividades_cobranza 
            if act.estado == 'COMPLETADA'
        ]
        
        if actividades_completadas:
            return max(actividades_completadas, key=lambda x: x.fecha_programada)
        return None
    
    @property
    def total_actividades_cobranza(self):
        """Cuenta el total de actividades de cobranza"""
        return len(self.actividades_cobranza)
    
    @property
    def actividades_cobranza_requieren_seguimiento(self):
        """Retorna actividades que requieren seguimiento"""
        return [act for act in self.actividades_cobranza if act.requiere_seguimiento]
    
    @property
    def efectividad_cobranza(self):
        """Calcula la efectividad de las actividades de cobranza"""
        if not self.actividades_cobranza:
            return 0
        
        actividades_completadas = [
            act for act in self.actividades_cobranza 
            if act.estado == 'COMPLETADA'
        ]
        
        if not actividades_completadas:
            return 0
        
        exitosas = len([
            act for act in actividades_completadas 
            if act.resultado in ['EXITOSA', 'PROMESA_PAGO', 'ACUERDO_ALCANZADO']
        ])
        
        return round((exitosas / len(actividades_completadas)) * 100, 2)
    
    def obtener_actividades_cobranza_por_tipo(self, tipo_actividad):
        """Obtiene actividades de cobranza filtradas por tipo"""
        return [act for act in self.actividades_cobranza if act.tipo_actividad.value == tipo_actividad]
    
    def obtener_actividades_cobranza_por_estado(self, estado):
        """Obtiene actividades de cobranza filtradas por estado"""
        return [act for act in self.actividades_cobranza if act.estado.value == estado]
    
    def obtener_actividades_cobranza_por_resultado(self, resultado):
        """Obtiene actividades de cobranza filtradas por resultado"""
        return [act for act in self.actividades_cobranza if act.resultado and act.resultado.value == resultado]
    
    def dias_desde_ultima_actividad_cobranza(self):
        """Calcula cuántos días han pasado desde la última actividad de cobranza"""
        ultima = self.ultima_actividad_cobranza
        if not ultima:
            return None
        
        from datetime import date
        diferencia = date.today() - ultima.fecha_programada
        return diferencia.days
    
    def tiene_actividades_cobranza_pendientes_hoy(self):
        """Verifica si tiene actividades de cobranza pendientes para hoy"""
        return len(self.actividades_cobranza_hoy) > 0
    
    def promesas_pago_pendientes(self):
        """Retorna actividades con promesas de pago pendientes de cumplir"""
        from datetime import date
        hoy = date.today()
        
        return [
            act for act in self.actividades_cobranza 
            if (act.resultado and act.resultado.value == 'PROMESA_PAGO' and 
                act.fecha_promesa_pago and act.fecha_promesa_pago <= hoy)
        ]
    
    # ========== FIN PROPIEDADES DE AGENDA DE COBRANZA ==========
    
    @property
    def total_obligaciones_vigentes(self):
        """Calcula el total de saldos de obligaciones vigentes"""
        total = 0
        for obligacion in self.obligaciones:
            if obligacion.estado == 'VIGENTE' and obligacion.saldo_actual:
                try:
                    total += float(obligacion.saldo_actual)
                except (ValueError, TypeError):
                    pass
        return total if total > 0 else 0
    
    @property
    def cuotas_mensuales_obligaciones(self):
        """Calcula el total de cuotas mensuales de obligaciones vigentes"""
        total = 0
        for obligacion in self.obligaciones:
            if obligacion.estado == 'VIGENTE' and obligacion.cuota_mensual:
                try:
                    total += float(obligacion.cuota_mensual)
                except (ValueError, TypeError):
                    pass
        return total if total > 0 else 0
    
    @property
    def cedula_vigente(self):
        """Verifica si la cédula está vigente"""
        if not self.fecha_vencimiento_cedula:
            return None  # No se puede determinar
        
        try:
            from datetime import datetime, date
            # Intentar parsear la fecha (puede estar en diferentes formatos)
            fecha_venc = None
            fecha_str = self.fecha_vencimiento_cedula
            
            # Intentar diferentes formatos de fecha
            formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            for formato in formatos:
                try:
                    fecha_venc = datetime.strptime(fecha_str, formato).date()
                    break
                except ValueError:
                    continue
            
            if fecha_venc:
                return date.today() <= fecha_venc
        except (ValueError, TypeError):
            pass
        
        return None  # No se pudo determinar
    
    @property
    def pasaporte_vigente(self):
        """Verifica si el pasaporte está vigente"""
        if not self.fecha_vencimiento_pasaporte:
            return None  # No se puede determinar
        
        try:
            from datetime import datetime, date
            # Intentar parsear la fecha (puede estar en diferentes formatos)
            fecha_venc = None
            fecha_str = self.fecha_vencimiento_pasaporte
            
            # Intentar diferentes formatos de fecha
            formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            for formato in formatos:
                try:
                    fecha_venc = datetime.strptime(fecha_str, formato).date()
                    break
                except ValueError:
                    continue
            
            if fecha_venc:
                return date.today() <= fecha_venc
        except (ValueError, TypeError):
            pass
        
        return None  # No se pudo determinar
    
    @property
    def documentos_vigentes(self):
        """Retorna el estado de vigencia de todos los documentos"""
        return {
            'cedula': self.cedula_vigente,
            'pasaporte': self.pasaporte_vigente
        }
    
    def dias_para_vencimiento_cedula(self):
        """Calcula cuántos días faltan para que venza la cédula"""
        if not self.fecha_vencimiento_cedula:
            return None
        
        try:
            from datetime import datetime, date
            fecha_venc = None
            fecha_str = self.fecha_vencimiento_cedula
            
            # Intentar diferentes formatos de fecha
            formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
            for formato in formatos:
                try:
                    fecha_venc = datetime.strptime(fecha_str, formato).date()
                    break
                except ValueError:
                    continue
            
            if fecha_venc:
                diferencia = fecha_venc - date.today()
                return diferencia.days
        except (ValueError, TypeError):
            pass
        
        return None
    
    # ========== PROPIEDADES PEP (PERSONA POLÍTICAMENTE EXPUESTA) ==========
    
    @property
    def es_pep(self):
        """Determina si el cliente es Persona Políticamente Expuesta"""
        return any(trabajo.es_pep for trabajo in self.trabajos)
    
    @property
    def es_gobierno(self):
        """Determina si el cliente trabaja en el gobierno"""
        return any(trabajo.es_gobierno for trabajo in self.trabajos)
    
    @property
    def es_familiar_pep(self):
        """Determina si el cliente es familiar de PEP"""
        return any(trabajo.familiar_pep for trabajo in self.trabajos)
    
    @property
    def es_asociado_pep(self):
        """Determina si el cliente es asociado comercial de PEP"""
        return any(trabajo.asociado_pep for trabajo in self.trabajos)
    
    @property
    def tiene_cargo_eleccion_popular(self):
        """Determina si el cliente tiene cargo de elección popular"""
        return any(trabajo.cargo_eleccion_popular for trabajo in self.trabajos)
    
    @property
    def es_cliente_riesgo_politico(self):
        """Determina si el cliente representa riesgo por exposición política"""
        return any(trabajo.es_trabajo_riesgo for trabajo in self.trabajos)
    
    @property
    def nivel_exposicion_politica_cliente(self):
        """Retorna el máximo nivel de exposición política del cliente"""
        niveles = [trabajo.nivel_exposicion_politica for trabajo in self.trabajos]
        
        if 'ALTO' in niveles:
            return 'ALTO'
        elif 'MEDIO' in niveles:
            return 'MEDIO'
        elif 'BAJO' in niveles:
            return 'BAJO'
        else:
            return 'NINGUNO'
    
    @property
    def requiere_due_diligence_reforzada(self):
        """Determina si el cliente requiere debida diligencia reforzada"""
        return any(trabajo.requiere_due_diligence_reforzada for trabajo in self.trabajos)
    
    @property
    def trabajos_gobierno(self):
        """Retorna todos los trabajos en entidades gubernamentales"""
        return [trabajo for trabajo in self.trabajos if trabajo.es_gobierno]
    
    @property
    def trabajos_pep(self):
        """Retorna todos los trabajos que califican como PEP"""
        return [trabajo for trabajo in self.trabajos if trabajo.es_pep]
    
    @property
    def trabajos_riesgo_politico(self):
        """Retorna todos los trabajos que representan riesgo político"""
        return [trabajo for trabajo in self.trabajos if trabajo.es_trabajo_riesgo]
    
    @property
    def descripcion_exposicion_politica(self):
        """Retorna descripción completa de la exposición política del cliente"""
        if not self.es_cliente_riesgo_politico:
            return "Sin exposición política"
        
        descripciones = []
        for trabajo in self.trabajos_riesgo_politico:
            if trabajo.es_actual:
                descripciones.append(f"ACTUAL: {trabajo.descripcion_exposicion}")
            else:
                descripciones.append(f"ANTERIOR: {trabajo.descripcion_exposicion}")
        
        return "; ".join(descripciones)
    
    @property
    def instituciones_publicas(self):
        """Retorna lista de instituciones públicas donde ha trabajado"""
        instituciones = set()
        for trabajo in self.trabajos_gobierno:
            if trabajo.institucion_publica:
                instituciones.add(trabajo.institucion_publica)
            else:
                instituciones.add(trabajo.empresa)
        return list(instituciones)
    
    def obtener_trabajos_por_exposicion(self, nivel_exposicion):
        """Obtiene trabajos filtrados por nivel de exposición política"""
        return [trabajo for trabajo in self.trabajos 
                if trabajo.nivel_exposicion_politica == nivel_exposicion]
    
    def __repr__(self):
        pep_flag = " [PEP]" if self.es_cliente_riesgo_politico else ""
        return f"<Cliente {self.codigo_cliente}: {self.nombre_completo}{pep_flag}>"


class ClienteDireccion(Base, AuditMixin):
    """Direcciones del cliente"""
    __tablename__ = "cliente_direcciones"
    
    TIPOS_DIRECCION = [
        ('RESIDENCIAL', 'Residencial'),
        ('LABORAL', 'Laboral'),
        ('FISCAL', 'Fiscal'),
        ('OTRO', 'Otro')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    tipo = Column(Enum(*[t[0] for t in TIPOS_DIRECCION], name='tipo_direccion'), nullable=False)
    calle = Column(String(255), nullable=False)
    numero_exterior = Column(String(20), nullable=True)
    numero_interior = Column(String(20), nullable=True)
    barriada = Column(String(100), nullable=False)
    codigo_postal = Column(String(10), nullable=True)
    ciudad = Column(String(100), nullable=False)
    estado = Column(String(100), nullable=False)
    pais = Column(String(100), default='Panamá', nullable=False)
    referencia = Column(Text, nullable=True)
    
    # Coordenadas GPS
    latitud = Column(Numeric(10, 8), nullable=True, comment="Latitud GPS")
    longitud = Column(Numeric(11, 8), nullable=True, comment="Longitud GPS")
    altitud = Column(Numeric(8, 2), nullable=True, comment="Altitud en metros")
    precision_gps = Column(Numeric(6, 2), nullable=True, comment="Precisión GPS en metros")
    
    es_principal = Column(Boolean, default=False, nullable=False)
    es_facturacion = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="direcciones")
    
    # Índices
    __table_args__ = (
        Index('idx_direccion_cliente', 'cliente_id'),
        Index('idx_direccion_principal', 'cliente_id', 'es_principal'),
        Index('idx_direccion_coordenadas', 'latitud', 'longitud'),
    )
    
    @property
    def coordenadas(self):
        """Retorna las coordenadas como tupla (latitud, longitud)"""
        if self.latitud is not None and self.longitud is not None:
            return (float(self.latitud), float(self.longitud))
        return None
    
    @property
    def direccion_completa(self):
        """Retorna la dirección formateada completa"""
        partes = [self.calle]
        
        if self.numero_exterior:
            partes.append(f"#{self.numero_exterior}")
        if self.numero_interior:
            partes.append(f"Int. {self.numero_interior}")
        
        partes.extend([self.barriada, self.ciudad, self.estado])
        
        if self.codigo_postal:
            partes.append(self.codigo_postal)
        
        return ", ".join(partes)
    
    def calcular_distancia(self, latitud_destino, longitud_destino):
        """Calcula la distancia en kilómetros usando la fórmula de Haversine"""
        if not self.coordenadas:
            return None
        
        import math
        
        # Radio de la Tierra en kilómetros
        R = 6371.0
        
        # Convertir grados a radianes
        lat1 = math.radians(float(self.latitud))
        lon1 = math.radians(float(self.longitud))
        lat2 = math.radians(latitud_destino)
        lon2 = math.radians(longitud_destino)
        
        # Diferencias
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Fórmula de Haversine
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def __repr__(self):
        return f"<Dirección {self.tipo} de {self.cliente_id}>"


class ClienteEmail(Base, AuditMixin):
    """Emails del cliente"""
    __tablename__ = "cliente_emails"
    
    TIPOS_EMAIL = [
        ('PERSONAL', 'Personal'),
        ('TRABAJO', 'Trabajo'),
        ('SECUNDARIO', 'Secundario'),
        ('OTRO', 'Otro')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    tipo = Column(Enum(*[t[0] for t in TIPOS_EMAIL], name='tipo_email'), nullable=False)
    _email = Column("email", String(500), nullable=False)
    es_principal = Column(Boolean, default=False, nullable=False)
    es_verificado = Column(Boolean, default=False, nullable=False)
    fecha_verificacion = Column(DateTime, nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Descriptor para encriptación
    email = EncryptedColumn('email')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="emails")
    
    # Índices
    __table_args__ = (
        Index('idx_cliente_email_principal', 'cliente_id', 'es_principal'),
        Index('idx_cliente_email_verificado', 'cliente_id', 'es_verificado'),
    )
    
    def __repr__(self):
        return f"<Email {self.tipo} de {self.cliente_id}>"


class ClienteTelefono(Base, AuditMixin):
    """Teléfonos del cliente"""
    __tablename__ = "cliente_telefonos"
    
    TIPOS_TELEFONO = [
        ('CELULAR', 'Celular'),
        ('CASA', 'Casa'),
        ('TRABAJO', 'Trabajo'),
        ('FAX', 'Fax'),
        ('OTRO', 'Otro')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    tipo = Column(Enum(*[t[0] for t in TIPOS_TELEFONO], name='tipo_telefono'), nullable=False)
    numero = Column(String(20), nullable=False)
    extension = Column(String(10), nullable=True)
    es_principal = Column(Boolean, default=False, nullable=False)
    tiene_whatsapp = Column(Boolean, default=False, nullable=False)
    observaciones = Column(Text, nullable=True)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="telefonos")
    
    def __repr__(self):
        return f"<Teléfono {self.numero} ({self.tipo}) de {self.cliente_id}>"


class ClienteTrabajo(Base, AuditMixin):
    """Historial laboral del cliente"""
    __tablename__ = "cliente_trabajos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    empresa = Column(String(255), nullable=False)
    puesto = Column(String(255), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=True)
    salario = Column(Numeric(12, 2), nullable=True)
    direccion = Column(Text, nullable=True)
    telefono = Column(String(20), nullable=True)
    jefe_inmediato = Column(String(255), nullable=True)
    telefono_jefe = Column(String(20), nullable=True)
    es_actual = Column(Boolean, default=True, nullable=False)
    motivo_retiro = Column(Text, nullable=True)
    
    # ========== CAMPOS PEP (PERSONA POLÍTICAMENTE EXPUESTA) ==========
    es_gobierno = Column(Boolean, default=False, nullable=False, comment="Trabaja en entidad gubernamental")
    es_pep = Column(Boolean, default=False, nullable=False, comment="Es Persona Políticamente Expuesta")
    tipo_entidad_publica = Column(String(100), nullable=True, comment="Tipo de entidad: EJECUTIVO, LEGISLATIVO, JUDICIAL, MUNICIPAL, AUTONOMA, DESCENTRALIZADA")
    nivel_cargo = Column(String(50), nullable=True, comment="Nivel del cargo: ALTO, MEDIO, OPERATIVO")
    tiene_poder_decision = Column(Boolean, default=False, nullable=False, comment="Tiene poder de decisión en políticas públicas")
    maneja_fondos_publicos = Column(Boolean, default=False, nullable=False, comment="Maneja o autoriza fondos públicos")
    cargo_eleccion_popular = Column(Boolean, default=False, nullable=False, comment="Cargo de elección popular")
    familiar_pep = Column(Boolean, default=False, nullable=False, comment="Familiar cercano de PEP")
    asociado_pep = Column(Boolean, default=False, nullable=False, comment="Asociado comercial de PEP")
    
    # Información adicional para PEP (encriptada)
    _detalle_cargo_publico = Column("detalle_cargo_publico", String(500), nullable=True, comment="Detalle del cargo público")
    _institucion_publica = Column("institucion_publica", String(500), nullable=True, comment="Nombre de la institución pública")
    _observaciones_pep = Column("observaciones_pep", Text, nullable=True, comment="Observaciones sobre exposición política")
    
    # Descriptores para encriptación
    detalle_cargo_publico = EncryptedColumn('detalle_cargo_publico')
    institucion_publica = EncryptedColumn('institucion_publica')
    observaciones_pep = EncryptedColumn('observaciones_pep')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="trabajos")
    
    # ========== PROPIEDADES PEP ==========
    
    @property
    def es_trabajo_riesgo(self):
        """Determina si el trabajo representa riesgo por exposición política"""
        return (self.es_pep or self.es_gobierno or self.familiar_pep or 
                self.asociado_pep or self.cargo_eleccion_popular)
    
    @property
    def nivel_exposicion_politica(self):
        """Calcula el nivel de exposición política: ALTO, MEDIO, BAJO, NINGUNO"""
        if self.cargo_eleccion_popular or (self.es_pep and self.nivel_cargo == 'ALTO'):
            return 'ALTO'
        elif self.es_pep or (self.es_gobierno and self.tiene_poder_decision):
            return 'MEDIO'
        elif self.es_gobierno or self.familiar_pep or self.asociado_pep:
            return 'BAJO'
        else:
            return 'NINGUNO'
    
    @property
    def requiere_due_diligence_reforzada(self):
        """Determina si requiere debida diligencia reforzada"""
        return (self.es_pep or self.cargo_eleccion_popular or 
                self.maneja_fondos_publicos or self.tiene_poder_decision)
    
    @property
    def descripcion_exposicion(self):
        """Retorna descripción legible de la exposición política"""
        if self.cargo_eleccion_popular:
            return f"Cargo de elección popular: {self.puesto}"
        elif self.es_pep:
            return f"PEP - {self.nivel_cargo}: {self.puesto}"
        elif self.es_gobierno:
            return f"Funcionario público: {self.puesto}"
        elif self.familiar_pep:
            return "Familiar de PEP"
        elif self.asociado_pep:
            return "Asociado comercial de PEP"
        else:
            return "Sin exposición política"
    
    @property
    def entidad_completa(self):
        """Retorna información completa de la entidad"""
        if self.institucion_publica:
            return f"{self.empresa} ({self.institucion_publica})"
        return self.empresa
    
    def __repr__(self):
        pep_flag = " [PEP]" if self.es_trabajo_riesgo else ""
        return f"<Trabajo {self.puesto} en {self.empresa}{pep_flag} de {self.cliente_id}>"


class ClienteReferencia(Base, AuditMixin):
    """Referencias personales del cliente"""
    __tablename__ = "cliente_referencias"
    
    TIPOS_REFERENCIA = [
        ('PERSONAL', 'Personal'),
        ('FAMILIAR', 'Familiar'),
        ('LABORAL', 'Laboral'),
        ('COMERCIAL', 'Comercial')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    tipo = Column(Enum(*[t[0] for t in TIPOS_REFERENCIA], name='tipo_referencia'), nullable=False)
    nombre_completo = Column(String(255), nullable=False)
    parentesco = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    telefono_alternativo = Column(String(20), nullable=True)
    direccion = Column(Text, nullable=True)
    tiempo_conocido = Column(String(100), nullable=True)
    es_contacto_emergencia = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="referencias")
    
    def __repr__(self):
        return f"<Referencia {self.nombre_completo} ({self.parentesco}) de {self.cliente_id}>"


class ClienteCuentaBancaria(Base, AuditMixin):
    """Cuentas bancarias del cliente"""
    __tablename__ = "cliente_cuentas_bancarias"
    
    TIPOS_CUENTA = [
        ('AHORRO', 'Cuenta de Ahorro'),
        ('CORRIENTE', 'Cuenta Corriente'),
        ('PLAZO_FIJO', 'Depósito a Plazo Fijo'),
        ('NOMINA', 'Cuenta Nómina'),
        ('EMPRESARIAL', 'Cuenta Empresarial'),
        ('OTRO', 'Otro')
    ]
    
    ESTADOS_CUENTA = [
        ('ACTIVA', 'Activa'),
        ('INACTIVA', 'Inactiva'),
        ('BLOQUEADA', 'Bloqueada'),
        ('CERRADA', 'Cerrada')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    
    # Información básica de la cuenta
    tipo_cuenta = Column(Enum(*[t[0] for t in TIPOS_CUENTA], name='tipo_cuenta_bancaria'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_CUENTA], name='estado_cuenta_bancaria'), default='ACTIVA', nullable=False)
    
    # Información del banco (encriptada)
    _banco = Column("banco", String(500), nullable=False, comment="Nombre del banco")
    _sucursal = Column("sucursal", String(500), nullable=True, comment="Sucursal del banco")
    _numero_cuenta = Column("numero_cuenta", String(500), nullable=False, comment="Número de cuenta")
    _titular_cuenta = Column("titular_cuenta", String(500), nullable=True, comment="Titular de la cuenta si es diferente")
    
    # Información financiera (encriptada)
    _saldo_promedio = Column("saldo_promedio", String(500), nullable=True, comment="Saldo promedio mensual")
    _limite_sobregiro = Column("limite_sobregiro", String(500), nullable=True, comment="Límite de sobregiro")
    _comision_manejo = Column("comision_manejo", String(500), nullable=True, comment="Comisión de manejo mensual")
    
    # Fechas importantes
    fecha_apertura = Column(Date, nullable=True, comment="Fecha de apertura de la cuenta")
    fecha_cierre = Column(Date, nullable=True, comment="Fecha de cierre de la cuenta")
    
    # Información adicional
    es_cuenta_principal = Column(Boolean, default=False, nullable=False, comment="Si es la cuenta principal del cliente")
    recibe_nomina = Column(Boolean, default=False, nullable=False, comment="Si recibe nómina en esta cuenta")
    _observaciones = Column("observaciones", Text, nullable=True)
    
    # Descriptores para encriptación
    banco = EncryptedColumn('banco')
    sucursal = EncryptedColumn('sucursal')
    numero_cuenta = EncryptedColumn('numero_cuenta')
    titular_cuenta = EncryptedColumn('titular_cuenta')
    saldo_promedio = EncryptedColumn('saldo_promedio')
    limite_sobregiro = EncryptedColumn('limite_sobregiro')
    comision_manejo = EncryptedColumn('comision_manejo')
    observaciones = EncryptedColumn('observaciones')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="cuentas_bancarias")
    
    # Índices
    __table_args__ = (
        Index('idx_cuenta_cliente', 'cliente_id'),
        Index('idx_cuenta_tipo_estado', 'tipo_cuenta', 'estado'),
        Index('idx_cuenta_principal', 'cliente_id', 'es_cuenta_principal'),
        Index('idx_cuenta_nomina', 'cliente_id', 'recibe_nomina'),
    )
    
    @property
    def cuenta_activa(self):
        """Verifica si la cuenta está activa"""
        return self.estado == 'ACTIVA'
    
    @property
    def cuenta_completa(self):
        """Retorna información completa de la cuenta formateada"""
        info = f"{self.banco}"
        if self.sucursal:
            info += f" - {self.sucursal}"
        info += f" ({self.tipo_cuenta})"
        return info
    
    def __repr__(self):
        return f"<Cuenta {self.tipo_cuenta} - {self.banco} de {self.cliente_id}>"


class ClienteVehiculo(Base, AuditMixin):
    """Vehículos del cliente"""
    __tablename__ = "cliente_vehiculos"
    
    TIPOS_VEHICULO = [
        ('AUTOMOVIL', 'Automóvil'),
        ('MOTOCICLETA', 'Motocicleta'),
        ('CAMIONETA', 'Camioneta'),
        ('CAMION', 'Camión'),
        ('BUS', 'Bus'),
        ('OTRO', 'Otro')
    ]
    
    ESTADOS_VEHICULO = [
        ('ACTIVO', 'Activo'),
        ('VENDIDO', 'Vendido'),
        ('SINIESTRADO', 'Siniestrado'),
        ('INACTIVO', 'Inactivo')
    ]
    
    COMBUSTIBLES = [
        ('GASOLINA', 'Gasolina'),
        ('DIESEL', 'Diésel'),
        ('HIBRIDO', 'Híbrido'),
        ('ELECTRICO', 'Eléctrico'),
        ('GAS', 'Gas')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    
    # Información básica del vehículo
    tipo_vehiculo = Column(Enum(*[t[0] for t in TIPOS_VEHICULO], name='tipo_vehiculo'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_VEHICULO], name='estado_vehiculo'), default='ACTIVO', nullable=False)
    
    # Información del vehículo (encriptada)
    _marca = Column("marca", String(500), nullable=False, comment="Marca del vehículo")
    _modelo = Column("modelo", String(500), nullable=False, comment="Modelo del vehículo")
    _placa = Column("placa", String(500), nullable=False, comment="Número de placa")
    _numero_chasis = Column("numero_chasis", String(500), nullable=True, comment="Número de chasis/VIN")
    _numero_motor = Column("numero_motor", String(500), nullable=True, comment="Número de motor")
    
    # Características técnicas
    anio = Column(Integer, nullable=True, comment="Año del vehículo")
    _color = Column("color", String(500), nullable=True, comment="Color del vehículo")
    combustible = Column(Enum(*[c[0] for c in COMBUSTIBLES], name='combustible_vehiculo'), nullable=True)
    _cilindraje = Column("cilindraje", String(500), nullable=True, comment="Cilindraje del motor")
    
    # Información financiera (encriptada)
    _valor_comercial = Column("valor_comercial", String(500), nullable=True, comment="Valor comercial estimado")
    _valor_asegurado = Column("valor_asegurado", String(500), nullable=True, comment="Valor asegurado")
    _prima_seguro = Column("prima_seguro", String(500), nullable=True, comment="Prima de seguro anual")
    
    # Información de financiamiento
    esta_financiado = Column(Boolean, default=False, nullable=False, comment="Si el vehículo está financiado")
    _entidad_financiera = Column("entidad_financiera", String(500), nullable=True, comment="Banco o financiera")
    _saldo_credito = Column("saldo_credito", String(500), nullable=True, comment="Saldo pendiente del crédito")
    _cuota_mensual = Column("cuota_mensual", String(500), nullable=True, comment="Cuota mensual del crédito")
    
    # Información de seguro
    tiene_seguro = Column(Boolean, default=False, nullable=False, comment="Si tiene seguro vigente")
    _aseguradora = Column("aseguradora", String(500), nullable=True, comment="Compañía de seguros")
    _numero_poliza = Column("numero_poliza", String(500), nullable=True, comment="Número de póliza")
    fecha_vencimiento_seguro = Column(Date, nullable=True, comment="Fecha de vencimiento del seguro")
    
    # Fechas importantes
    fecha_compra = Column(Date, nullable=True, comment="Fecha de compra del vehículo")
    fecha_venta = Column(Date, nullable=True, comment="Fecha de venta (si aplica)")
    
    # Información adicional
    es_vehiculo_principal = Column(Boolean, default=False, nullable=False, comment="Si es el vehículo principal")
    uso_vehiculo = Column(String(50), nullable=True, comment="Personal, Comercial, Mixto")
    _observaciones = Column("observaciones", Text, nullable=True)
    
    # Descriptores para encriptación
    marca = EncryptedColumn('marca')
    modelo = EncryptedColumn('modelo')
    placa = EncryptedColumn('placa')
    numero_chasis = EncryptedColumn('numero_chasis')
    numero_motor = EncryptedColumn('numero_motor')
    color = EncryptedColumn('color')
    cilindraje = EncryptedColumn('cilindraje')
    valor_comercial = EncryptedColumn('valor_comercial')
    valor_asegurado = EncryptedColumn('valor_asegurado')
    prima_seguro = EncryptedColumn('prima_seguro')
    entidad_financiera = EncryptedColumn('entidad_financiera')
    saldo_credito = EncryptedColumn('saldo_credito')
    cuota_mensual = EncryptedColumn('cuota_mensual')
    aseguradora = EncryptedColumn('aseguradora')
    numero_poliza = EncryptedColumn('numero_poliza')
    observaciones = EncryptedColumn('observaciones')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="vehiculos")
    documentos = relationship("Documento", back_populates="vehiculo", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_vehiculo_cliente', 'cliente_id'),
        Index('idx_vehiculo_tipo_estado', 'tipo_vehiculo', 'estado'),
        Index('idx_vehiculo_principal', 'cliente_id', 'es_vehiculo_principal'),
        Index('idx_vehiculo_financiado', 'esta_financiado'),
        Index('idx_vehiculo_seguro_vencimiento', 'fecha_vencimiento_seguro'),
    )
    
    @property
    def vehiculo_activo(self):
        """Verifica si el vehículo está activo"""
        return self.estado == 'ACTIVO'
    
    @property
    def seguro_vigente(self):
        """Verifica si el seguro está vigente"""
        if not self.tiene_seguro or not self.fecha_vencimiento_seguro:
            return False
        
        from datetime import date
        return date.today() <= self.fecha_vencimiento_seguro
    
    @property
    def vehiculo_completo(self):
        """Retorna información completa del vehículo formateada"""
        info = f"{self.marca} {self.modelo}"
        if self.anio:
            info += f" ({self.anio})"
        if self.placa:
            info += f" - {self.placa}"
        return info
    
    def dias_para_vencimiento_seguro(self):
        """Calcula cuántos días faltan para que venza el seguro"""
        if not self.fecha_vencimiento_seguro:
            return None
        
        from datetime import date
        diferencia = self.fecha_vencimiento_seguro - date.today()
        return diferencia.days
    
    def __repr__(self):
        return f"<Vehículo {self.marca} {self.modelo} - {self.placa} de {self.cliente_id}>"


class ClientePropiedad(Base, AuditMixin):
    """Propiedades inmobiliarias del cliente"""
    __tablename__ = "cliente_propiedades"
    
    TIPOS_PROPIEDAD = [
        ('CASA', 'Casa'),
        ('APARTAMENTO', 'Apartamento'),
        ('TERRENO', 'Terreno'),
        ('LOCAL_COMERCIAL', 'Local Comercial'),
        ('OFICINA', 'Oficina'),
        ('BODEGA', 'Bodega'),
        ('FINCA', 'Finca'),
        ('OTRO', 'Otro')
    ]
    
    ESTADOS_PROPIEDAD = [
        ('ACTIVA', 'Activa'),
        ('VENDIDA', 'Vendida'),
        ('HIPOTECADA', 'Hipotecada'),
        ('EN_VENTA', 'En Venta'),
        ('RENTADA', 'Rentada'),
        ('INACTIVA', 'Inactiva')
    ]
    
    TIPOS_TENENCIA = [
        ('PROPIA', 'Propia'),
        ('HIPOTECADA', 'Hipotecada'),
        ('HEREDADA', 'Heredada'),
        ('FAMILIAR', 'Familiar'),
        ('ARRENDADA', 'Arrendada'),
        ('USUFRUCTO', 'Usufructo')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    
    # Información básica de la propiedad
    tipo_propiedad = Column(Enum(*[t[0] for t in TIPOS_PROPIEDAD], name='tipo_propiedad'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_PROPIEDAD], name='estado_propiedad'), default='ACTIVA', nullable=False)
    tipo_tenencia = Column(Enum(*[t[0] for t in TIPOS_TENENCIA], name='tipo_tenencia'), nullable=False)
    
    # Información de ubicación (encriptada)
    _direccion_completa = Column("direccion_completa", String(500), nullable=False, comment="Dirección completa de la propiedad")
    _barriada = Column("barriada", String(500), nullable=True, comment="Barriada o sector")
    _ciudad = Column("ciudad", String(500), nullable=True, comment="Ciudad")
    _provincia = Column("provincia", String(500), nullable=True, comment="Provincia")
    _codigo_postal = Column("codigo_postal", String(500), nullable=True, comment="Código postal")
    
    # Coordenadas GPS
    latitud = Column(Numeric(10, 8), nullable=True, comment="Latitud GPS")
    longitud = Column(Numeric(11, 8), nullable=True, comment="Longitud GPS")
    altitud = Column(Numeric(8, 2), nullable=True, comment="Altitud en metros")
    precision_gps = Column(Numeric(5, 2), nullable=True, comment="Precisión GPS en metros")
    
    # Información legal (encriptada)
    _numero_finca = Column("numero_finca", String(500), nullable=True, comment="Número de finca registral")
    _folio = Column("folio", String(500), nullable=True, comment="Folio registral")
    _tomo = Column("tomo", String(500), nullable=True, comment="Tomo registral")
    _registro_publico = Column("registro_publico", String(500), nullable=True, comment="Registro Público donde está inscrita")
    
    # Características físicas
    area_terreno = Column(Numeric(10, 2), nullable=True, comment="Área del terreno en m²")
    area_construccion = Column(Numeric(10, 2), nullable=True, comment="Área de construcción en m²")
    numero_habitaciones = Column(Integer, nullable=True, comment="Número de habitaciones")
    numero_banos = Column(Integer, nullable=True, comment="Número de baños")
    numero_plantas = Column(Integer, nullable=True, comment="Número de plantas")
    numero_parqueos = Column(Integer, nullable=True, comment="Número de parqueos")
    anio_construccion = Column(Integer, nullable=True, comment="Año de construcción")
    
    # Información financiera (encriptada)
    _valor_catastral = Column("valor_catastral", String(500), nullable=True, comment="Valor catastral")
    _valor_comercial = Column("valor_comercial", String(500), nullable=True, comment="Valor comercial estimado")
    _valor_avaluo = Column("valor_avaluo", String(500), nullable=True, comment="Valor del avalúo")
    fecha_avaluo = Column(Date, nullable=True, comment="Fecha del último avalúo")
    
    # Información de hipoteca/financiamiento (encriptada)
    esta_hipotecada = Column(Boolean, default=False, nullable=False, comment="Si la propiedad está hipotecada")
    _entidad_hipotecaria = Column("entidad_hipotecaria", String(500), nullable=True, comment="Banco o entidad hipotecaria")
    _saldo_hipoteca = Column("saldo_hipoteca", String(500), nullable=True, comment="Saldo pendiente de hipoteca")
    _cuota_hipoteca = Column("cuota_hipoteca", String(500), nullable=True, comment="Cuota mensual de hipoteca")
    _tasa_interes = Column("tasa_interes", String(500), nullable=True, comment="Tasa de interés de hipoteca")
    fecha_inicio_hipoteca = Column(Date, nullable=True, comment="Fecha de inicio de hipoteca")
    fecha_vencimiento_hipoteca = Column(Date, nullable=True, comment="Fecha de vencimiento de hipoteca")
    
    # Información de alquiler (encriptada)
    esta_rentada = Column(Boolean, default=False, nullable=False, comment="Si la propiedad está rentada")
    _valor_alquiler = Column("valor_alquiler", String(500), nullable=True, comment="Valor mensual de alquiler")
    _inquilino = Column("inquilino", String(500), nullable=True, comment="Nombre del inquilino")
    _telefono_inquilino = Column("telefono_inquilino", String(500), nullable=True, comment="Teléfono del inquilino")
    fecha_inicio_alquiler = Column(Date, nullable=True, comment="Fecha de inicio del contrato de alquiler")
    fecha_vencimiento_alquiler = Column(Date, nullable=True, comment="Fecha de vencimiento del contrato")
    
    # Servicios públicos
    tiene_agua = Column(Boolean, default=False, nullable=False, comment="Tiene servicio de agua")
    tiene_luz = Column(Boolean, default=False, nullable=False, comment="Tiene servicio eléctrico")
    tiene_telefono = Column(Boolean, default=False, nullable=False, comment="Tiene línea telefónica")
    tiene_internet = Column(Boolean, default=False, nullable=False, comment="Tiene servicio de internet")
    tiene_cable = Column(Boolean, default=False, nullable=False, comment="Tiene servicio de cable/TV")
    tiene_gas = Column(Boolean, default=False, nullable=False, comment="Tiene servicio de gas")
    
    # Información adicional
    es_propiedad_principal = Column(Boolean, default=False, nullable=False, comment="Si es la propiedad principal/residencia")
    uso_propiedad = Column(String(50), nullable=True, comment="Residencial, Comercial, Mixto, Inversión")
    _observaciones = Column("observaciones", Text, nullable=True)
    
    # Fechas importantes
    fecha_compra = Column(Date, nullable=True, comment="Fecha de compra de la propiedad")
    fecha_venta = Column(Date, nullable=True, comment="Fecha de venta (si aplica)")
    
    # Descriptores para encriptación
    direccion_completa = EncryptedColumn('direccion_completa')
    barriada = EncryptedColumn('barriada')
    ciudad = EncryptedColumn('ciudad')
    provincia = EncryptedColumn('provincia')
    codigo_postal = EncryptedColumn('codigo_postal')
    numero_finca = EncryptedColumn('numero_finca')
    folio = EncryptedColumn('folio')
    tomo = EncryptedColumn('tomo')
    registro_publico = EncryptedColumn('registro_publico')
    valor_catastral = EncryptedColumn('valor_catastral')
    valor_comercial = EncryptedColumn('valor_comercial')
    valor_avaluo = EncryptedColumn('valor_avaluo')
    entidad_hipotecaria = EncryptedColumn('entidad_hipotecaria')
    saldo_hipoteca = EncryptedColumn('saldo_hipoteca')
    cuota_hipoteca = EncryptedColumn('cuota_hipoteca')
    tasa_interes = EncryptedColumn('tasa_interes')
    valor_alquiler = EncryptedColumn('valor_alquiler')
    inquilino = EncryptedColumn('inquilino')
    telefono_inquilino = EncryptedColumn('telefono_inquilino')
    observaciones = EncryptedColumn('observaciones')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="propiedades")
    documentos = relationship("Documento", back_populates="propiedad", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_propiedad_cliente', 'cliente_id'),
        Index('idx_propiedad_tipo_estado', 'tipo_propiedad', 'estado'),
        Index('idx_propiedad_principal', 'cliente_id', 'es_propiedad_principal'),
        Index('idx_propiedad_hipotecada', 'esta_hipotecada'),
        Index('idx_propiedad_rentada', 'esta_rentada'),
        Index('idx_propiedad_ubicacion', 'latitud', 'longitud'),
        Index('idx_propiedad_vencimiento_hipoteca', 'fecha_vencimiento_hipoteca'),
        Index('idx_propiedad_vencimiento_alquiler', 'fecha_vencimiento_alquiler'),
    )
    
    @property
    def propiedad_activa(self):
        """Verifica si la propiedad está activa"""
        return self.estado == 'ACTIVA'
    
    @property
    def ubicacion_completa(self):
        """Retorna la ubicación completa formateada"""
        partes = [self.direccion_completa]
        if self.barriada:
            partes.append(self.barriada)
        if self.ciudad:
            partes.append(self.ciudad)
        if self.provincia:
            partes.append(self.provincia)
        return ", ".join(filter(None, partes))
    
    @property
    def coordenadas(self):
        """Retorna las coordenadas como tupla"""
        if self.latitud and self.longitud:
            return (float(self.latitud), float(self.longitud))
        return None
    
    @property
    def area_total(self):
        """Retorna el área total (terreno + construcción)"""
        total = 0
        if self.area_terreno:
            total += float(self.area_terreno)
        if self.area_construccion:
            total += float(self.area_construccion)
        return total if total > 0 else None
    
    @property
    def valor_neto(self):
        """Calcula el valor neto de la propiedad (valor comercial - saldo hipoteca)"""
        valor = 0
        if self.valor_comercial:
            try:
                valor = float(self.valor_comercial)
            except (ValueError, TypeError):
                return 0
        
        if self.esta_hipotecada and self.saldo_hipoteca:
            try:
                valor -= float(self.saldo_hipoteca)
            except (ValueError, TypeError):
                pass
        
        return valor if valor > 0 else 0
    
    @property
    def ingreso_alquiler_anual(self):
        """Calcula el ingreso anual por alquiler"""
        if not self.esta_rentada or not self.valor_alquiler:
            return 0
        
        try:
            return float(self.valor_alquiler) * 12
        except (ValueError, TypeError):
            return 0
    
    def dias_para_vencimiento_hipoteca(self):
        """Calcula cuántos días faltan para que venza la hipoteca"""
        if not self.fecha_vencimiento_hipoteca:
            return None
        
        from datetime import date
        diferencia = self.fecha_vencimiento_hipoteca - date.today()
        return diferencia.days
    
    def dias_para_vencimiento_alquiler(self):
        """Calcula cuántos días faltan para que venza el contrato de alquiler"""
        if not self.fecha_vencimiento_alquiler:
            return None
        
        from datetime import date
        diferencia = self.fecha_vencimiento_alquiler - date.today()
        return diferencia.days
    
    def __repr__(self):
        return f"<Propiedad {self.tipo_propiedad} - {self.direccion_completa} de {self.cliente_id}>"


class ClienteObligacion(Base, AuditMixin):
    """Obligaciones financieras del cliente (deudas con bancos y otras entidades)"""
    __tablename__ = "cliente_obligaciones"
    
    TIPOS_OBLIGACION = [
        ('PRESTAMO_PERSONAL', 'Préstamo Personal'),
        ('PRESTAMO_HIPOTECARIO', 'Préstamo Hipotecario'),
        ('PRESTAMO_VEHICULAR', 'Préstamo Vehicular'),
        ('TARJETA_CREDITO', 'Tarjeta de Crédito'),
        ('LINEA_CREDITO', 'Línea de Crédito'),
        ('PRESTAMO_COMERCIAL', 'Préstamo Comercial'),
        ('OTRO', 'Otro')
    ]
    
    ESTADOS_OBLIGACION = [
        ('VIGENTE', 'Vigente'),
        ('VENCIDA', 'Vencida'),
        ('CANCELADA', 'Cancelada'),
        ('REFINANCIADA', 'Refinanciada'),
        ('CASTIGADA', 'Castigada')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    
    # Información básica de la obligación
    tipo = Column(Enum(*[t[0] for t in TIPOS_OBLIGACION], name='tipo_obligacion'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_OBLIGACION], name='estado_obligacion'), default='VIGENTE', nullable=False)
    
    # Entidad acreedora (encriptada)
    _entidad_acreedora = Column("entidad_acreedora", String(500), nullable=False, comment="Banco o entidad financiera")
    _sucursal_acreedora = Column("sucursal_acreedora", String(500), nullable=True)
    _numero_cuenta = Column("numero_cuenta", String(500), nullable=True, comment="Número de cuenta o contrato")
    
    # Montos (encriptados)
    _monto_original = Column("monto_original", String(500), nullable=False, comment="Monto original del préstamo")
    _saldo_actual = Column("saldo_actual", String(500), nullable=False, comment="Saldo pendiente actual")
    _cuota_mensual = Column("cuota_mensual", String(500), nullable=True, comment="Cuota mensual")
    _tasa_interes = Column("tasa_interes", String(500), nullable=True, comment="Tasa de interés anual")
    
    # Fechas importantes
    fecha_inicio = Column(Date, nullable=False, comment="Fecha de inicio del préstamo")
    fecha_vencimiento = Column(Date, nullable=True, comment="Fecha de vencimiento")
    fecha_ultimo_pago = Column(Date, nullable=True, comment="Fecha del último pago")
    
    # Información adicional
    plazo_meses = Column(Integer, nullable=True, comment="Plazo en meses")
    dias_mora = Column(Integer, default=0, nullable=False, comment="Días en mora")
    _observaciones = Column("observaciones", Text, nullable=True)
    
    # Descriptores para encriptación
    entidad_acreedora = EncryptedColumn('entidad_acreedora')
    sucursal_acreedora = EncryptedColumn('sucursal_acreedora')
    numero_cuenta = EncryptedColumn('numero_cuenta')
    monto_original = EncryptedColumn('monto_original')
    saldo_actual = EncryptedColumn('saldo_actual')
    cuota_mensual = EncryptedColumn('cuota_mensual')
    tasa_interes = EncryptedColumn('tasa_interes')
    observaciones = EncryptedColumn('observaciones')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="obligaciones")
    
    # Índices
    __table_args__ = (
        Index('idx_obligacion_cliente', 'cliente_id'),
        Index('idx_obligacion_tipo_estado', 'tipo', 'estado'),
        Index('idx_obligacion_vencimiento', 'fecha_vencimiento'),
        Index('idx_obligacion_mora', 'dias_mora'),
    )
    
    @property
    def esta_vencida(self):
        """Verifica si la obligación está vencida"""
        if self.fecha_vencimiento:
            from datetime import date
            return date.today() > self.fecha_vencimiento
        return False
    
    @property
    def porcentaje_pagado(self):
        """Calcula el porcentaje pagado de la obligación"""
        try:
            monto_original = float(self.monto_original) if self.monto_original else 0
            saldo_actual = float(self.saldo_actual) if self.saldo_actual else 0
            
            if monto_original > 0:
                pagado = monto_original - saldo_actual
                return (pagado / monto_original) * 100
        except (ValueError, TypeError):
            pass
        return 0
    
    def __repr__(self):
        return f"<Obligación {self.tipo} - {self.entidad_acreedora} de {self.cliente_id}>"


class ClienteHistorial(Base, AuditMixin):
    """Historial completo de interacciones y eventos del cliente"""
    __tablename__ = "cliente_historial"
    
    TIPOS_EVENTO = [
        # Interacciones con el cliente
        ('LLAMADA_ENTRANTE', 'Llamada Entrante'),
        ('LLAMADA_SALIENTE', 'Llamada Saliente'),
        ('VISITA_SUCURSAL', 'Visita a Sucursal'),
        ('VISITA_DOMICILIO', 'Visita a Domicilio'),
        ('EMAIL_ENVIADO', 'Email Enviado'),
        ('EMAIL_RECIBIDO', 'Email Recibido'),
        ('SMS_ENVIADO', 'SMS Enviado'),
        ('WHATSAPP', 'Mensaje WhatsApp'),
        ('REUNION', 'Reunión'),
        ('ENTREVISTA', 'Entrevista'),
        
        # Solicitudes y trámites
        ('SOLICITUD_CREDITO', 'Solicitud de Crédito'),
        ('EVALUACION_CREDITO', 'Evaluación Crediticia'),
        ('APROBACION_CREDITO', 'Aprobación de Crédito'),
        ('RECHAZO_CREDITO', 'Rechazo de Crédito'),
        ('DESEMBOLSO', 'Desembolso'),
        ('RENOVACION', 'Renovación de Crédito'),
        ('REFINANCIAMIENTO', 'Refinanciamiento'),
        
        # Pagos y transacciones
        ('PAGO_RECIBIDO', 'Pago Recibido'),
        ('PAGO_ATRASADO', 'Pago Atrasado'),
        ('PAGO_PARCIAL', 'Pago Parcial'),
        ('MORA', 'Entrada en Mora'),
        ('REGULARIZACION', 'Regularización de Mora'),
        ('CONDONACION', 'Condonación'),
        
        # Cobranza
        ('COBRANZA_PREVENTIVA', 'Cobranza Preventiva'),
        ('COBRANZA_ADMINISTRATIVA', 'Cobranza Administrativa'),
        ('COBRANZA_JUDICIAL', 'Cobranza Judicial'),
        ('ACUERDO_PAGO', 'Acuerdo de Pago'),
        ('QUITA', 'Quita'),
        
        # Cambios en el perfil
        ('ACTUALIZACION_DATOS', 'Actualización de Datos'),
        ('CAMBIO_DOMICILIO', 'Cambio de Domicilio'),
        ('CAMBIO_TRABAJO', 'Cambio de Trabajo'),
        ('CAMBIO_INGRESOS', 'Cambio de Ingresos'),
        ('CAMBIO_ESTADO_CIVIL', 'Cambio de Estado Civil'),
        
        # Documentos
        ('DOCUMENTO_RECIBIDO', 'Documento Recibido'),
        ('DOCUMENTO_FALTANTE', 'Documento Faltante'),
        ('DOCUMENTO_VENCIDO', 'Documento Vencido'),
        ('VERIFICACION_DOCUMENTO', 'Verificación de Documento'),
        
        # Alertas y seguimiento
        ('ALERTA_RIESGO', 'Alerta de Riesgo'),
        ('CAMBIO_SCORE', 'Cambio de Score Crediticio'),
        ('REFERENCIA_COMERCIAL', 'Consulta Referencia Comercial'),
        ('CENTRALES_RIESGO', 'Consulta Centrales de Riesgo'),
        
        # Otros
        ('QUEJA', 'Queja del Cliente'),
        ('FELICITACION', 'Felicitación'),
        ('SUGERENCIA', 'Sugerencia'),
        ('NOTA_INTERNA', 'Nota Interna'),
        ('OBSERVACION', 'Observación'),
        ('OTRO', 'Otro')
    ]
    
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('NORMAL', 'Normal'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica')
    ]
    
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROCESO', 'En Proceso'),
        ('COMPLETADO', 'Completado'),
        ('CANCELADO', 'Cancelado')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey('sucursales.id'), nullable=True)
    
    # Información del evento
    tipo_evento = Column(Enum(*[t[0] for t in TIPOS_EVENTO], name='tipo_evento_historial'), nullable=False)
    prioridad = Column(Enum(*[p[0] for p in PRIORIDADES], name='prioridad_historial'), default='NORMAL', nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS], name='estado_historial'), default='COMPLETADO', nullable=False)
    
    # Contenido del evento (encriptado)
    _titulo = Column("titulo", String(500), nullable=False, comment="Título del evento")
    _descripcion = Column("descripcion", Text, nullable=False, comment="Descripción detallada")
    _observaciones = Column("observaciones", Text, nullable=True, comment="Observaciones adicionales")
    _resultado = Column("resultado", Text, nullable=True, comment="Resultado o conclusión")
    
    # Información de contacto (si aplica)
    medio_contacto = Column(String(50), nullable=True, comment="Teléfono, Email, Presencial, etc.")
    _numero_contacto = Column("numero_contacto", String(500), nullable=True, comment="Número o dirección de contacto")
    duracion_minutos = Column(Integer, nullable=True, comment="Duración en minutos (para llamadas, reuniones)")
    
    # Referencias a otros registros
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey('prestamos.id'), nullable=True)
    documento_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'), nullable=True)
    solicitud_id = Column(UUID(as_uuid=True), ForeignKey('cliente_solicitudes.id'), nullable=True)
    
    # Montos involucrados (si aplica)
    monto = Column(Numeric(15, 2), nullable=True, comment="Monto involucrado en el evento")
    moneda = Column(String(3), default='USD', nullable=True, comment="Moneda del monto")
    
    # Fechas importantes
    fecha_evento = Column(DateTime, nullable=False, default=datetime.utcnow, comment="Fecha y hora del evento")
    fecha_seguimiento = Column(Date, nullable=True, comment="Fecha programada para seguimiento")
    fecha_vencimiento = Column(Date, nullable=True, comment="Fecha límite (si aplica)")
    
    # Metadatos adicionales
    es_publico = Column(Boolean, default=True, nullable=False, comment="Si es visible para el cliente")
    requiere_seguimiento = Column(Boolean, default=False, nullable=False, comment="Si requiere seguimiento")
    es_critico = Column(Boolean, default=False, nullable=False, comment="Si es un evento crítico")
    
    # Información técnica
    ip_address = Column(String(45), nullable=True, comment="Dirección IP (para eventos digitales)")
    user_agent = Column(String(500), nullable=True, comment="User Agent (para eventos web)")
    _metadata_json = Column("metadata_json", Text, nullable=True, comment="Metadatos adicionales en JSON")
    
    # Descriptores para encriptación
    titulo = EncryptedColumn('titulo')
    descripcion = EncryptedColumn('descripcion')
    observaciones = EncryptedColumn('observaciones')
    resultado = EncryptedColumn('resultado')
    numero_contacto = EncryptedColumn('numero_contacto')
    metadata_json = EncryptedColumn('metadata_json')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="historial")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    sucursal = relationship("Sucursal", foreign_keys=[sucursal_id])
    prestamo = relationship("Prestamo", foreign_keys=[prestamo_id])
    documento = relationship("Documento", foreign_keys=[documento_id])
    solicitud = relationship("ClienteSolicitud", back_populates="historial")
    
    # Índices
    __table_args__ = (
        Index('idx_historial_cliente', 'cliente_id'),
        Index('idx_historial_fecha', 'fecha_evento'),
        Index('idx_historial_tipo', 'tipo_evento'),
        Index('idx_historial_usuario', 'usuario_id'),
        Index('idx_historial_sucursal', 'sucursal_id'),
        Index('idx_historial_prioridad', 'prioridad'),
        Index('idx_historial_estado', 'estado'),
        Index('idx_historial_seguimiento', 'fecha_seguimiento'),
        Index('idx_historial_critico', 'es_critico'),
        Index('idx_historial_publico', 'es_publico'),
        Index('idx_historial_prestamo', 'prestamo_id'),
        Index('idx_historial_cliente_fecha', 'cliente_id', 'fecha_evento'),
        Index('idx_historial_cliente_tipo', 'cliente_id', 'tipo_evento'),
    )
    
    @property
    def es_reciente(self):
        """Verifica si el evento es reciente (menos de 24 horas)"""
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.fecha_evento < timedelta(hours=24)
    
    @property
    def requiere_atencion(self):
        """Verifica si el evento requiere atención inmediata"""
        return (self.es_critico or 
                self.prioridad in ['ALTA', 'CRITICA'] or 
                self.estado == 'PENDIENTE' or
                self.requiere_seguimiento)
    
    @property
    def dias_desde_evento(self):
        """Calcula cuántos días han pasado desde el evento"""
        from datetime import datetime
        diferencia = datetime.utcnow() - self.fecha_evento
        return diferencia.days
    
    def dias_para_seguimiento(self):
        """Calcula cuántos días faltan para el seguimiento"""
        if not self.fecha_seguimiento:
            return None
        
        from datetime import date
        diferencia = self.fecha_seguimiento - date.today()
        return diferencia.days
    
    def __repr__(self):
        return f"<Historial {self.tipo_evento} - {self.titulo} de {self.cliente_id}>"


class ClienteConversacion(Base, AuditMixin):
    """Conversaciones y diálogos detallados con el cliente"""
    __tablename__ = "cliente_conversaciones"
    
    TIPOS_CONVERSACION = [
        ('LLAMADA', 'Llamada Telefónica'),
        ('REUNION', 'Reunión Presencial'),
        ('VIDEO_LLAMADA', 'Video Llamada'),
        ('CHAT', 'Chat en Línea'),
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Intercambio de Emails'),
        ('SMS', 'Mensajes de Texto'),
        ('OTRO', 'Otro')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    historial_id = Column(UUID(as_uuid=True), ForeignKey('cliente_historial.id'), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    
    # Información de la conversación
    tipo_conversacion = Column(Enum(*[t[0] for t in TIPOS_CONVERSACION], name='tipo_conversacion'), nullable=False)
    fecha_inicio = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)
    duracion_minutos = Column(Integer, nullable=True)
    
    # Contenido de la conversación (encriptado)
    _asunto = Column("asunto", String(500), nullable=False, comment="Asunto o tema principal")
    _transcripcion = Column("transcripcion", Text, nullable=True, comment="Transcripción o resumen de la conversación")
    _puntos_clave = Column("puntos_clave", Text, nullable=True, comment="Puntos clave discutidos")
    _acuerdos = Column("acuerdos", Text, nullable=True, comment="Acuerdos alcanzados")
    _proximos_pasos = Column("proximos_pasos", Text, nullable=True, comment="Próximos pasos a seguir")
    _observaciones = Column("observaciones", Text, nullable=True, comment="Observaciones del oficial")
    
    # Información adicional
    calidad_conversacion = Column(String(20), nullable=True, comment="Excelente, Buena, Regular, Mala")
    satisfaccion_cliente = Column(Integer, nullable=True, comment="Satisfacción del cliente (1-10)")
    requiere_seguimiento = Column(Boolean, default=False, nullable=False)
    fecha_seguimiento = Column(Date, nullable=True)
    
    # Participantes adicionales
    _participantes = Column("participantes", Text, nullable=True, comment="Otros participantes en la conversación")
    
    # Archivos adjuntos
    tiene_grabacion = Column(Boolean, default=False, nullable=False)
    _ruta_grabacion = Column("ruta_grabacion", String(500), nullable=True, comment="Ruta del archivo de grabación")
    _archivos_adjuntos = Column("archivos_adjuntos", Text, nullable=True, comment="Lista de archivos adjuntos")
    
    # Descriptores para encriptación
    asunto = EncryptedColumn('asunto')
    transcripcion = EncryptedColumn('transcripcion')
    puntos_clave = EncryptedColumn('puntos_clave')
    acuerdos = EncryptedColumn('acuerdos')
    proximos_pasos = EncryptedColumn('proximos_pasos')
    observaciones = EncryptedColumn('observaciones')
    participantes = EncryptedColumn('participantes')
    ruta_grabacion = EncryptedColumn('ruta_grabacion')
    archivos_adjuntos = EncryptedColumn('archivos_adjuntos')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="conversaciones")
    historial = relationship("ClienteHistorial")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    
    # Índices
    __table_args__ = (
        Index('idx_conversacion_cliente', 'cliente_id'),
        Index('idx_conversacion_fecha', 'fecha_inicio'),
        Index('idx_conversacion_tipo', 'tipo_conversacion'),
        Index('idx_conversacion_usuario', 'usuario_id'),
        Index('idx_conversacion_seguimiento', 'fecha_seguimiento'),
        Index('idx_conversacion_cliente_fecha', 'cliente_id', 'fecha_inicio'),
    )
    
    @property
    def duracion_calculada(self):
        """Calcula la duración si no está especificada"""
        if self.duracion_minutos:
            return self.duracion_minutos
        
        if self.fecha_fin:
            diferencia = self.fecha_fin - self.fecha_inicio
            return int(diferencia.total_seconds() / 60)
        
        return None
    
    @property
    def conversacion_activa(self):
        """Verifica si la conversación está activa (sin fecha de fin)"""
        return self.fecha_fin is None
    
    def __repr__(self):
        return f"<ClienteConversacion(id={self.id}, cliente_id={self.cliente_id}, tipo={self.tipo_conversacion}, fecha={self.fecha_inicio})>"


# Índices para ClienteConversacion ya están definidos en __table_args__ de la clase


class ClienteSolicitud(Base, AuditMixin):
    """Modelo para gestión integral de solicitudes de clientes con alertas automáticas"""
    
    __tablename__ = 'cliente_solicitudes'
    
    # Tipos de solicitudes
    TIPOS_SOLICITUD = [
        ('CREDITO_PERSONAL', 'Crédito Personal'),
        ('CREDITO_VEHICULAR', 'Crédito Vehicular'),
        ('CREDITO_HIPOTECARIO', 'Crédito Hipotecario'),
        ('CREDITO_COMERCIAL', 'Crédito Comercial'),
        ('REFINANCIAMIENTO', 'Refinanciamiento'),
        ('RENOVACION', 'Renovación de Crédito'),
        ('AUMENTO_LIMITE', 'Aumento de Límite'),
        ('CAMBIO_CONDICIONES', 'Cambio de Condiciones'),
        ('CARTA_REFERENCIA', 'Carta de Referencia'),
        ('CERTIFICACION_INGRESOS', 'Certificación de Ingresos'),
        ('ESTADO_CUENTA', 'Estado de Cuenta'),
        ('DUPLICADO_DOCUMENTO', 'Duplicado de Documento'),
        ('ACTUALIZACION_DATOS', 'Actualización de Datos'),
        ('RECLAMO', 'Reclamo'),
        ('QUEJA', 'Queja'),
        ('SUGERENCIA', 'Sugerencia'),
        ('OTRO', 'Otro')
    ]
    
    # Estados de solicitud
    ESTADOS_SOLICITUD = [
        ('RECIBIDA', 'Recibida'),
        ('EN_REVISION', 'En Revisión'),
        ('DOCUMENTOS_PENDIENTES', 'Documentos Pendientes'),
        ('EN_EVALUACION', 'En Evaluación'),
        ('EN_COMITE', 'En Comité'),
        ('APROBADA', 'Aprobada'),
        ('APROBADA_CONDICIONADA', 'Aprobada con Condiciones'),
        ('RECHAZADA', 'Rechazada'),
        ('EN_DESEMBOLSO', 'En Desembolso'),
        ('DESEMBOLSADA', 'Desembolsada'),
        ('CANCELADA', 'Cancelada'),
        ('VENCIDA', 'Vencida'),
        ('COMPLETADA', 'Completada')
    ]
    
    # Prioridades
    PRIORIDADES = [
        ('BAJA', 'Baja'),
        ('NORMAL', 'Normal'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
        ('CRITICA', 'Crítica')
    ]
    
    # Canales de solicitud
    CANALES = [
        ('SUCURSAL', 'Sucursal'),
        ('ONLINE', 'Plataforma Online'),
        ('TELEFONO', 'Teléfono'),
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('MOVIL', 'App Móvil'),
        ('AGENTE', 'Agente Externo'),
        ('OTRO', 'Otro')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    numero_solicitud = Column(String(50), unique=True, nullable=False, index=True, comment="Número único de solicitud")
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    usuario_asignado_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey('sucursales.id'), nullable=True)
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey('prestamos.id'), nullable=True)
    
    # Información básica de la solicitud
    tipo_solicitud = Column(Enum(*[t[0] for t in TIPOS_SOLICITUD], name='tipo_solicitud'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_SOLICITUD], name='estado_solicitud'), default='RECIBIDA', nullable=False)
    prioridad = Column(Enum(*[p[0] for p in PRIORIDADES], name='prioridad_solicitud'), default='NORMAL', nullable=False)
    canal = Column(Enum(*[c[0] for c in CANALES], name='canal_solicitud'), nullable=False)
    
    # Fechas críticas
    fecha_solicitud = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_limite_respuesta = Column(DateTime, nullable=True, comment="Fecha límite para responder")
    fecha_vencimiento = Column(DateTime, nullable=True, comment="Fecha de vencimiento de la solicitud")
    fecha_respuesta = Column(DateTime, nullable=True, comment="Fecha de respuesta al cliente")
    fecha_completada = Column(DateTime, nullable=True, comment="Fecha de completación")
    
    # Información financiera (encriptada)
    _monto_solicitado = Column("monto_solicitado", Numeric(15, 2), nullable=True, comment="Monto solicitado")
    _monto_aprobado = Column("monto_aprobado", Numeric(15, 2), nullable=True, comment="Monto aprobado")
    moneda = Column(String(3), default='USD', nullable=False)
    _plazo_solicitado = Column("plazo_solicitado", Integer, nullable=True, comment="Plazo en meses")
    _plazo_aprobado = Column("plazo_aprobado", Integer, nullable=True, comment="Plazo aprobado en meses")
    _tasa_interes = Column("tasa_interes", Numeric(5, 4), nullable=True, comment="Tasa de interés")
    
    # Contenido de la solicitud (encriptado)
    _asunto = Column("asunto", String(500), nullable=False, comment="Asunto de la solicitud")
    _descripcion = Column("descripcion", Text, nullable=False, comment="Descripción detallada")
    _observaciones = Column("observaciones", Text, nullable=True, comment="Observaciones del oficial")
    _motivo_rechazo = Column("motivo_rechazo", Text, nullable=True, comment="Motivo de rechazo")
    _condiciones_aprobacion = Column("condiciones_aprobacion", Text, nullable=True, comment="Condiciones de aprobación")
    _respuesta_cliente = Column("respuesta_cliente", Text, nullable=True, comment="Respuesta enviada al cliente")
    
    # Información de contacto (encriptada)
    _telefono_contacto = Column("telefono_contacto", String(20), nullable=True, comment="Teléfono de contacto")
    _email_contacto = Column("email_contacto", String(100), nullable=True, comment="Email de contacto")
    
    # Control de SLA y alertas
    sla_horas = Column(Integer, default=24, nullable=False, comment="SLA en horas para respuesta")
    alertas_enviadas = Column(Integer, default=0, nullable=False, comment="Número de alertas enviadas")
    ultima_alerta = Column(DateTime, nullable=True, comment="Fecha de última alerta")
    requiere_seguimiento = Column(Boolean, default=True, nullable=False)
    fecha_proximo_seguimiento = Column(DateTime, nullable=True)
    
    # Información adicional
    requiere_documentos = Column(Boolean, default=False, nullable=False)
    documentos_pendientes = Column(Text, nullable=True, comment="JSON con documentos pendientes")
    requiere_garantia = Column(Boolean, default=False, nullable=False)
    requiere_avalista = Column(Boolean, default=False, nullable=False)
    
    # Métricas
    tiempo_respuesta_horas = Column(Integer, nullable=True, comment="Tiempo de respuesta en horas")
    tiempo_procesamiento_horas = Column(Integer, nullable=True, comment="Tiempo total de procesamiento")
    numero_interacciones = Column(Integer, default=0, nullable=False)
    
    # Metadatos (encriptados)
    _metadata_json = Column("metadata_json", Text, nullable=True, comment="Metadatos adicionales en JSON")
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="solicitudes")
    usuario_asignado = relationship("Usuario", foreign_keys=[usuario_asignado_id])
    sucursal = relationship("Sucursal")
    prestamo = relationship("Prestamo")
    documentos = relationship("Documento", back_populates="solicitud", cascade="all, delete-orphan")
    historial = relationship("ClienteHistorial", back_populates="solicitud", cascade="all, delete-orphan")
    alertas = relationship("SolicitudAlerta", back_populates="solicitud", cascade="all, delete-orphan")
    
    # Propiedades para encriptación
    @hybrid_property
    def monto_solicitado(self):
        return self._monto_solicitado
    
    @monto_solicitado.setter
    def monto_solicitado(self, value):
        self._monto_solicitado = value
    
    @hybrid_property
    def monto_aprobado(self):
        return self._monto_aprobado
    
    @monto_aprobado.setter
    def monto_aprobado(self, value):
        self._monto_aprobado = value
    
    @hybrid_property
    def plazo_solicitado(self):
        return self._plazo_solicitado
    
    @plazo_solicitado.setter
    def plazo_solicitado(self, value):
        self._plazo_solicitado = value
    
    @hybrid_property
    def plazo_aprobado(self):
        return self._plazo_aprobado
    
    @plazo_aprobado.setter
    def plazo_aprobado(self, value):
        self._plazo_aprobado = value
    
    @hybrid_property
    def tasa_interes(self):
        return self._tasa_interes
    
    @tasa_interes.setter
    def tasa_interes(self, value):
        self._tasa_interes = value
    
    @hybrid_property
    def asunto(self):
        return self._asunto
    
    @asunto.setter
    def asunto(self, value):
        self._asunto = value
    
    @hybrid_property
    def descripcion(self):
        return self._descripcion
    
    @descripcion.setter
    def descripcion(self, value):
        self._descripcion = value
    
    @hybrid_property
    def observaciones(self):
        return self._observaciones
    
    @observaciones.setter
    def observaciones(self, value):
        self._observaciones = value
    
    @hybrid_property
    def motivo_rechazo(self):
        return self._motivo_rechazo
    
    @motivo_rechazo.setter
    def motivo_rechazo(self, value):
        self._motivo_rechazo = value
    
    @hybrid_property
    def condiciones_aprobacion(self):
        return self._condiciones_aprobacion
    
    @condiciones_aprobacion.setter
    def condiciones_aprobacion(self, value):
        self._condiciones_aprobacion = value
    
    @hybrid_property
    def respuesta_cliente(self):
        return self._respuesta_cliente
    
    @respuesta_cliente.setter
    def respuesta_cliente(self, value):
        self._respuesta_cliente = value
    
    @hybrid_property
    def telefono_contacto(self):
        return self._telefono_contacto
    
    @telefono_contacto.setter
    def telefono_contacto(self, value):
        self._telefono_contacto = value
    
    @hybrid_property
    def email_contacto(self):
        return self._email_contacto
    
    @email_contacto.setter
    def email_contacto(self, value):
        self._email_contacto = value
    
    @hybrid_property
    def metadata_json(self):
        return self._metadata_json
    
    @metadata_json.setter
    def metadata_json(self, value):
        self._metadata_json = value
    
    # Propiedades útiles
    @property
    def esta_vencida(self):
        """Verifica si la solicitud está vencida"""
        if self.fecha_vencimiento:
            return datetime.utcnow() > self.fecha_vencimiento
        return False
    
    @property
    def esta_en_sla(self):
        """Verifica si la solicitud está dentro del SLA"""
        if self.fecha_limite_respuesta:
            return datetime.utcnow() <= self.fecha_limite_respuesta
        # Si no hay fecha límite, calcular basado en SLA
        fecha_limite = self.fecha_solicitud + timedelta(hours=self.sla_horas)
        return datetime.utcnow() <= fecha_limite
    
    @property
    def horas_transcurridas(self):
        """Horas transcurridas desde la solicitud"""
        delta = datetime.utcnow() - self.fecha_solicitud
        return int(delta.total_seconds() / 3600)
    
    @property
    def horas_restantes_sla(self):
        """Horas restantes para cumplir SLA"""
        if self.fecha_limite_respuesta:
            fecha_limite = self.fecha_limite_respuesta
        else:
            fecha_limite = self.fecha_solicitud + timedelta(hours=self.sla_horas)
        
        delta = fecha_limite - datetime.utcnow()
        horas = int(delta.total_seconds() / 3600)
        return max(0, horas)
    
    @property
    def porcentaje_sla_consumido(self):
        """Porcentaje del SLA consumido"""
        return min(100, (self.horas_transcurridas / self.sla_horas) * 100)
    
    @property
    def requiere_alerta(self):
        """Determina si requiere envío de alerta"""
        # Alerta si está al 75% del SLA o más
        return self.porcentaje_sla_consumido >= 75 and self.estado in ['RECIBIDA', 'EN_REVISION', 'DOCUMENTOS_PENDIENTES']
    
    @property
    def esta_completada(self):
        """Verifica si la solicitud está completada"""
        return self.estado in ['COMPLETADA', 'DESEMBOLSADA', 'RECHAZADA', 'CANCELADA']
    
    @property
    def nombre_tipo_legible(self):
        """Nombre legible del tipo de solicitud"""
        for codigo, nombre in self.TIPOS_SOLICITUD:
            if codigo == self.tipo_solicitud:
                return nombre
        return self.tipo_solicitud
    
    @property
    def nombre_estado_legible(self):
        """Nombre legible del estado"""
        for codigo, nombre in self.ESTADOS_SOLICITUD:
            if codigo == self.estado:
                return nombre
        return self.estado
    
    def calcular_fecha_limite(self):
        """Calcula la fecha límite basada en el SLA"""
        return self.fecha_solicitud + timedelta(hours=self.sla_horas)
    
    def actualizar_tiempo_respuesta(self):
        """Actualiza el tiempo de respuesta cuando se responde"""
        if self.fecha_respuesta:
            delta = self.fecha_respuesta - self.fecha_solicitud
            self.tiempo_respuesta_horas = int(delta.total_seconds() / 3600)
    
    def actualizar_tiempo_procesamiento(self):
        """Actualiza el tiempo total de procesamiento"""
        if self.fecha_completada:
            delta = self.fecha_completada - self.fecha_solicitud
            self.tiempo_procesamiento_horas = int(delta.total_seconds() / 3600)
    
    def incrementar_interacciones(self):
        """Incrementa el contador de interacciones"""
        self.numero_interacciones += 1
    
    def dias_para_vencimiento(self):
        """Días restantes para vencimiento"""
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - datetime.utcnow()
            return max(0, delta.days)
        return None
    
    def __repr__(self):
        return f"<ClienteSolicitud(numero={self.numero_solicitud}, cliente_id={self.cliente_id}, tipo={self.tipo_solicitud}, estado={self.estado})>"


class SolicitudAlerta(Base, AuditMixin):
    """Modelo para alertas de solicitudes"""
    
    __tablename__ = 'solicitud_alertas'
    
    # Tipos de alerta
    TIPOS_ALERTA = [
        ('SLA_75', 'SLA al 75%'),
        ('SLA_90', 'SLA al 90%'),
        ('SLA_VENCIDO', 'SLA Vencido'),
        ('DOCUMENTOS_PENDIENTES', 'Documentos Pendientes'),
        ('SOLICITUD_VENCIDA', 'Solicitud Vencida'),
        ('SEGUIMIENTO_REQUERIDO', 'Seguimiento Requerido'),
        ('APROBACION_PENDIENTE', 'Aprobación Pendiente'),
        ('DESEMBOLSO_PENDIENTE', 'Desembolso Pendiente'),
        ('CLIENTE_INACTIVO', 'Cliente Inactivo'),
        ('OTRO', 'Otro')
    ]
    
    # Estados de alerta
    ESTADOS_ALERTA = [
        ('PENDIENTE', 'Pendiente'),
        ('ENVIADA', 'Enviada'),
        ('LEIDA', 'Leída'),
        ('ATENDIDA', 'Atendida'),
        ('IGNORADA', 'Ignorada'),
        ('VENCIDA', 'Vencida')
    ]
    
    # Niveles de urgencia
    NIVELES_URGENCIA = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    solicitud_id = Column(UUID(as_uuid=True), ForeignKey('cliente_solicitudes.id'), nullable=False)
    usuario_destinatario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    
    # Información de la alerta
    tipo_alerta = Column(Enum(*[t[0] for t in TIPOS_ALERTA], name='tipo_alerta'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_ALERTA], name='estado_alerta'), default='PENDIENTE', nullable=False)
    nivel_urgencia = Column(Enum(*[n[0] for n in NIVELES_URGENCIA], name='nivel_urgencia'), default='MEDIA', nullable=False)
    
    # Contenido de la alerta
    titulo = Column(String(200), nullable=False, comment="Título de la alerta")
    mensaje = Column(Text, nullable=False, comment="Mensaje de la alerta")
    
    # Fechas
    fecha_programada = Column(DateTime, nullable=False, default=datetime.utcnow)
    fecha_enviada = Column(DateTime, nullable=True)
    fecha_leida = Column(DateTime, nullable=True)
    fecha_atendida = Column(DateTime, nullable=True)
    fecha_vencimiento = Column(DateTime, nullable=True)
    
    # Configuración de envío
    enviar_email = Column(Boolean, default=True, nullable=False)
    enviar_sms = Column(Boolean, default=False, nullable=False)
    enviar_push = Column(Boolean, default=True, nullable=False)
    
    # Información adicional
    intentos_envio = Column(Integer, default=0, nullable=False)
    ultimo_intento = Column(DateTime, nullable=True)
    error_envio = Column(Text, nullable=True)
    
    # Relaciones
    solicitud = relationship("ClienteSolicitud", back_populates="alertas")
    usuario_destinatario = relationship("Usuario", foreign_keys=[usuario_destinatario_id])
    
    # Propiedades útiles
    @property
    def esta_vencida(self):
        """Verifica si la alerta está vencida"""
        if self.fecha_vencimiento:
            return datetime.utcnow() > self.fecha_vencimiento
        return False
    
    @property
    def esta_pendiente(self):
        """Verifica si la alerta está pendiente de envío"""
        return self.estado == 'PENDIENTE'
    
    @property
    def requiere_reenvio(self):
        """Determina si requiere reenvío por fallos"""
        return self.intentos_envio > 0 and self.estado == 'PENDIENTE' and self.intentos_envio < 3
    
    def marcar_como_enviada(self):
        """Marca la alerta como enviada"""
        self.estado = 'ENVIADA'
        self.fecha_enviada = datetime.utcnow()
    
    def marcar_como_leida(self):
        """Marca la alerta como leída"""
        self.estado = 'LEIDA'
        self.fecha_leida = datetime.utcnow()
    
    def marcar_como_atendida(self):
        """Marca la alerta como atendida"""
        self.estado = 'ATENDIDA'
        self.fecha_atendida = datetime.utcnow()
    
    def incrementar_intentos(self, error=None):
        """Incrementa los intentos de envío"""
        self.intentos_envio += 1
        self.ultimo_intento = datetime.utcnow()
        if error:
            self.error_envio = error
    
    def __repr__(self):
        return f"<SolicitudAlerta(id={self.id}, solicitud_id={self.solicitud_id}, tipo={self.tipo_alerta}, estado={self.estado})>"


# Índices para ClienteSolicitud
Index('idx_solicitud_numero', ClienteSolicitud.numero_solicitud)
Index('idx_solicitud_cliente', ClienteSolicitud.cliente_id)
Index('idx_solicitud_tipo_estado', ClienteSolicitud.tipo_solicitud, ClienteSolicitud.estado)
Index('idx_solicitud_fecha', ClienteSolicitud.fecha_solicitud)
Index('idx_solicitud_fecha_limite', ClienteSolicitud.fecha_limite_respuesta)
Index('idx_solicitud_fecha_vencimiento', ClienteSolicitud.fecha_vencimiento)
Index('idx_solicitud_usuario_asignado', ClienteSolicitud.usuario_asignado_id)
Index('idx_solicitud_sucursal', ClienteSolicitud.sucursal_id)
Index('idx_solicitud_prioridad', ClienteSolicitud.prioridad)
Index('idx_solicitud_canal', ClienteSolicitud.canal)
Index('idx_solicitud_sla', ClienteSolicitud.sla_horas)
Index('idx_solicitud_seguimiento', ClienteSolicitud.requiere_seguimiento, ClienteSolicitud.fecha_proximo_seguimiento)
Index('idx_solicitud_prestamo', ClienteSolicitud.prestamo_id)

# Índices para SolicitudAlerta
Index('idx_alerta_solicitud', SolicitudAlerta.solicitud_id)
Index('idx_alerta_usuario', SolicitudAlerta.usuario_destinatario_id)
Index('idx_alerta_tipo_estado', SolicitudAlerta.tipo_alerta, SolicitudAlerta.estado)
Index('idx_alerta_fecha_programada', SolicitudAlerta.fecha_programada)
Index('idx_alerta_fecha_enviada', SolicitudAlerta.fecha_enviada)
Index('idx_alerta_nivel_urgencia', SolicitudAlerta.nivel_urgencia)
Index('idx_alerta_pendiente', SolicitudAlerta.estado, SolicitudAlerta.fecha_programada)


class Prestamo(Base, AuditMixin):
    """Modelo de préstamos con soporte para descuento directo"""
    __tablename__ = "prestamos"
    
    # Tipos de préstamo
    TIPOS_PRESTAMO = [
        ('PERSONAL', 'Préstamo Personal'),
        ('VEHICULAR', 'Préstamo Vehicular'),
        ('HIPOTECARIO', 'Préstamo Hipotecario'),
        ('COMERCIAL', 'Préstamo Comercial'),
        ('CONSUMO', 'Préstamo de Consumo'),
        ('EDUCATIVO', 'Préstamo Educativo'),
        ('EMERGENCIA', 'Préstamo de Emergencia')
    ]
    
    # Tipos de descuento directo para préstamos personales
    TIPOS_DESCUENTO_DIRECTO = [
        ('JUBILADOS', 'Jubilados y Pensionados'),
        ('PAGOS_VOLUNTARIOS', 'Pagos Voluntarios'),
        ('CONTRALORIA', 'Contraloría General de la República'),
        ('CSS', 'Caja de Seguro Social'),
        ('MEF', 'Ministerio de Economía y Finanzas'),
        ('MEDUCA', 'Ministerio de Educación'),
        ('MINSA', 'Ministerio de Salud'),
        ('EMPRESA_PRIVADA', 'Empresa Privada'),
        ('BANCO_NACIONAL', 'Banco Nacional de Panamá'),
        ('CAJA_AHORROS', 'Caja de Ahorros'),
        ('OTROS_BANCOS', 'Otros Bancos'),
        ('COOPERATIVAS', 'Cooperativas'),
        ('GARANTIA_HIPOTECARIA', 'Con Garantía Hipotecaria'),
        ('GARANTIA_VEHICULAR', 'Con Garantía Vehicular'),
        ('GARANTIA_FIDUCIARIA', 'Con Garantía Fiduciaria'),
        ('GARANTIA_PRENDARIA', 'Con Garantía Prendaria'),
        ('AVAL_SOLIDARIO', 'Con Aval Solidario'),
        ('SIN_DESCUENTO', 'Sin Descuento Directo')
    ]
    
    # Estados del préstamo
    ESTADOS_PRESTAMO = [
        ('SOLICITUD', 'En Solicitud'),
        ('EVALUACION', 'En Evaluación'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('DESEMBOLSADO', 'Desembolsado'),
        ('VIGENTE', 'Vigente'),
        ('MORA', 'En Mora'),
        ('CANCELADO', 'Cancelado'),
        ('REFINANCIADO', 'Refinanciado'),
        ('CASTIGADO', 'Castigado')
    ]
    
    # Modalidades de pago
    MODALIDADES_PAGO = [
        ('DESCUENTO_DIRECTO', 'Descuento Directo'),
        ('DEBITO_AUTOMATICO', 'Débito Automático'),
        ('VENTANILLA', 'Pago en Ventanilla'),
        ('TRANSFERENCIA', 'Transferencia Bancaria'),
        ('CHEQUE', 'Cheque'),
        ('EFECTIVO', 'Efectivo')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=False)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey('sucursales.id'), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    
    # Clasificación del préstamo
    tipo_prestamo = Column(Enum(*[t[0] for t in TIPOS_PRESTAMO], name='tipo_prestamo'), nullable=False, default='PERSONAL')
    tipo_descuento_directo = Column(Enum(*[t[0] for t in TIPOS_DESCUENTO_DIRECTO], name='tipo_descuento_directo'), nullable=True)
    modalidad_pago = Column(Enum(*[m[0] for m in MODALIDADES_PAGO], name='modalidad_pago'), nullable=False, default='VENTANILLA')
    
    # Datos del préstamo
    numero_prestamo = Column(String(50), unique=True, nullable=True, index=True, comment="Número único del préstamo")
    monto = Column(Numeric(12, 2), nullable=False)
    plazo = Column(Integer, nullable=False)  # en meses
    tasa_interes = Column(Numeric(5, 2), nullable=False)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_PRESTAMO], name='estado_prestamo'), nullable=False, default='SOLICITUD')
    
    # Cálculos financieros
    monto_total = Column(Numeric(12, 2), nullable=False)
    monto_pagado = Column(Numeric(12, 2), default=0, nullable=False)
    cuota_mensual = Column(Numeric(12, 2), nullable=False)
    
    # Información de descuento directo (encriptada)
    _entidad_empleadora = Column("entidad_empleadora", String(500), nullable=True, comment="Entidad donde trabaja para descuento")
    _numero_empleado = Column("numero_empleado", String(500), nullable=True, comment="Número de empleado")
    _cedula_empleado = Column("cedula_empleado", String(500), nullable=True, comment="Cédula del empleado")
    _cargo_empleado = Column("cargo_empleado", String(500), nullable=True, comment="Cargo del empleado")
    _salario_base = Column("salario_base", String(500), nullable=True, comment="Salario base para descuento")
    _contacto_rrhh = Column("contacto_rrhh", String(500), nullable=True, comment="Contacto de RRHH")
    _telefono_rrhh = Column("telefono_rrhh", String(500), nullable=True, comment="Teléfono de RRHH")
    _email_rrhh = Column("email_rrhh", String(500), nullable=True, comment="Email de RRHH")
    
    # Propiedades encriptadas
    entidad_empleadora = EncryptedColumn('entidad_empleadora')
    numero_empleado = EncryptedColumn('numero_empleado')
    cedula_empleado = EncryptedColumn('cedula_empleado')
    cargo_empleado = EncryptedColumn('cargo_empleado')
    salario_base = EncryptedColumn('salario_base')
    contacto_rrhh = EncryptedColumn('contacto_rrhh')
    telefono_rrhh = EncryptedColumn('telefono_rrhh')
    email_rrhh = EncryptedColumn('email_rrhh')
    
    # Información adicional
    garantia = Column(Text, nullable=True)
    proposito = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    
    # Control de descuento directo
    descuento_autorizado = Column(Boolean, default=False, nullable=False, comment="Si está autorizado el descuento")
    fecha_autorizacion_descuento = Column(DateTime, nullable=True, comment="Fecha de autorización del descuento")
    porcentaje_descuento_maximo = Column(Numeric(5, 2), default=30.00, nullable=False, comment="% máximo de descuento del salario")
    
    # Campos de seguridad
    is_active = Column(Boolean, default=True, nullable=False)
    risk_assessment = Column(String(20), default='medium', nullable=False)
    
    # Métodos y propiedades calculadas
    @property
    def requiere_descuento_directo(self):
        """Verifica si el préstamo requiere descuento directo"""
        return self.modalidad_pago == 'DESCUENTO_DIRECTO'
    
    @property
    def tiene_garantia(self):
        """Verifica si el préstamo tiene algún tipo de garantía"""
        tipos_con_garantia = [
            'GARANTIA_HIPOTECARIA', 'GARANTIA_VEHICULAR', 
            'GARANTIA_FIDUCIARIA', 'GARANTIA_PRENDARIA', 'AVAL_SOLIDARIO'
        ]
        return self.tipo_descuento_directo in tipos_con_garantia
    
    @property
    def es_empleado_publico(self):
        """Verifica si es empleado público"""
        entidades_publicas = [
            'JUBILADOS', 'CONTRALORIA', 'CSS', 'MEF', 'MEDUCA', 'MINSA'
        ]
        return self.tipo_descuento_directo in entidades_publicas
    
    @property
    def es_empleado_bancario(self):
        """Verifica si es empleado bancario"""
        entidades_bancarias = [
            'BANCO_NACIONAL', 'CAJA_AHORROS', 'OTROS_BANCOS', 'COOPERATIVAS'
        ]
        return self.tipo_descuento_directo in entidades_bancarias
    
    @property
    def saldo_pendiente(self):
        """Calcula el saldo pendiente del préstamo"""
        return float(self.monto_total - self.monto_pagado)
    
    @property
    def porcentaje_pagado(self):
        """Calcula el porcentaje pagado del préstamo"""
        if self.monto_total == 0:
            return 0
        return float((self.monto_pagado / self.monto_total) * 100)
    
    @property
    def dias_mora(self):
        """Calcula los días de mora del préstamo"""
        from datetime import date
        if self.estado not in ['VIGENTE', 'MORA'] or not self.fecha_vencimiento:
            return 0
        
        hoy = date.today()
        fecha_venc = self.fecha_vencimiento.date() if hasattr(self.fecha_vencimiento, 'date') else self.fecha_vencimiento
        
        if hoy > fecha_venc:
            return (hoy - fecha_venc).days
        return 0
    
    @property
    def estado_mora(self):
        """Determina el estado de mora del préstamo"""
        dias = self.dias_mora
        if dias == 0:
            return 'AL_DIA'
        elif dias <= 30:
            return 'MORA_TEMPRANA'
        elif dias <= 60:
            return 'MORA_MEDIA'
        elif dias <= 90:
            return 'MORA_TARDIA'
        else:
            return 'MORA_CRITICA'
    
    def autorizar_descuento(self, usuario_id=None):
        """Autoriza el descuento directo del préstamo"""
        from datetime import datetime
        self.descuento_autorizado = True
        self.fecha_autorizacion_descuento = datetime.utcnow()
        if usuario_id:
            self.updated_by = usuario_id
    
    def revocar_descuento(self, usuario_id=None):
        """Revoca la autorización de descuento directo"""
        self.descuento_autorizado = False
        self.fecha_autorizacion_descuento = None
        if usuario_id:
            self.updated_by = usuario_id
    
    def validar_porcentaje_descuento(self, salario_bruto):
        """Valida si el porcentaje de descuento es válido según la ley panameña"""
        if not salario_bruto or salario_bruto <= 0:
            return False, "Salario bruto inválido"
        
        porcentaje_actual = (float(self.cuota_mensual) / float(salario_bruto)) * 100
        
        if porcentaje_actual > float(self.porcentaje_descuento_maximo):
            return False, f"El descuento ({porcentaje_actual:.2f}%) excede el máximo permitido ({self.porcentaje_descuento_maximo}%)"
        
        # Validación según ley panameña (máximo 30% del salario)
        if porcentaje_actual > 30.0:
            return False, f"El descuento ({porcentaje_actual:.2f}%) excede el límite legal del 30%"
        
        return True, f"Descuento válido: {porcentaje_actual:.2f}% del salario"
    
    def generar_numero_prestamo(self):
        """Genera un número único de préstamo"""
        from datetime import datetime
        import random
        
        if not self.numero_prestamo:
            # Formato: TIPO-SUCURSAL-AÑO-SECUENCIAL
            tipo_codigo = self.tipo_prestamo[:3].upper()
            sucursal_codigo = self.sucursal.codigo if self.sucursal else "001"
            año = datetime.now().year
            secuencial = random.randint(1000, 9999)
            
            self.numero_prestamo = f"{tipo_codigo}-{sucursal_codigo}-{año}-{secuencial}"
    
    def obtener_descripcion_tipo_descuento(self):
        """Obtiene la descripción del tipo de descuento directo"""
        for codigo, descripcion in self.TIPOS_DESCUENTO_DIRECTO:
            if codigo == self.tipo_descuento_directo:
                return descripcion
        return "Sin Descuento Directo"
    
    def obtener_descripcion_modalidad_pago(self):
        """Obtiene la descripción de la modalidad de pago"""
        for codigo, descripcion in self.MODALIDADES_PAGO:
            if codigo == self.modalidad_pago:
                return descripcion
        return "No Especificada"
    
    def __repr__(self):
        return f"<Préstamo {self.numero_prestamo or self.id} - {self.cliente.nombre_completo if self.cliente else 'N/A'} - ${self.monto}>"
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="prestamos")
    sucursal = relationship("Sucursal", back_populates="prestamos")
    usuario = relationship("Usuario", back_populates="prestamos_creados", foreign_keys=[usuario_id])
    pagos = relationship("Pago", back_populates="prestamo")
    documentos = relationship("Documento", back_populates="prestamo")
    # actividades_cobranza = relationship("app.models.agenda_models.AgendaCobranza", back_populates="prestamo")
    
    # Índices
    __table_args__ = (
        Index('idx_prestamo_cliente', 'cliente_id'),
        Index('idx_prestamo_estado', 'estado'),
        Index('idx_prestamo_fecha_vencimiento', 'fecha_vencimiento'),
        Index('idx_prestamo_numero', 'numero_prestamo'),
        Index('idx_prestamo_tipo', 'tipo_prestamo'),
        Index('idx_prestamo_descuento_directo', 'tipo_descuento_directo'),
        Index('idx_prestamo_modalidad_pago', 'modalidad_pago'),
        Index('idx_prestamo_descuento_autorizado', 'descuento_autorizado'),
        Index('idx_prestamo_sucursal_estado', 'sucursal_id', 'estado'),
        Index('idx_prestamo_tipo_estado', 'tipo_prestamo', 'estado'),
    )


class Pago(Base, AuditMixin):
    """Modelo de pagos"""
    __tablename__ = "pagos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey('prestamos.id'), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    
    monto = Column(Numeric(12, 2), nullable=False)
    fecha_pago = Column(DateTime, nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    estado = Column(String(20), nullable=False, default='pendiente')
    metodo_pago = Column(String(50), nullable=False)
    referencia = Column(String(255), nullable=True)
    notas = Column(Text, nullable=True)
    
    # Relaciones
    prestamo = relationship("Prestamo", back_populates="pagos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])


class Documento(Base, SecureBaseModel, AuditMixin):
    """Modelo de documentos con metadatos de seguridad expandido"""
    __tablename__ = "documentos"
    
    TIPOS_DOCUMENTO = [
        # Documentos de identificación
        ('CEDULA', 'Cédula de Identidad'),
        ('PASAPORTE', 'Pasaporte'),
        ('LICENCIA_CONDUCIR', 'Licencia de Conducir'),
        
        # Documentos laborales
        ('CARTA_TRABAJO', 'Carta de Trabajo'),
        ('COLILLA_PAGO', 'Colilla de Pago'),
        ('CERTIFICADO_INGRESOS', 'Certificado de Ingresos'),
        ('DECLARACION_RENTA', 'Declaración de Renta'),
        
        # Documentos bancarios
        ('ESTADO_CUENTA', 'Estado de Cuenta Bancaria'),
        ('CARTA_BANCO', 'Carta del Banco'),
        ('AUTORIZACION_DESCUENTO', 'Autorización de Descuento'),
        
        # Documentos de propiedades
        ('TITULO_PROPIEDAD', 'Título de Propiedad'),
        ('ESCRITURA_PUBLICA', 'Escritura Pública'),
        ('REGISTRO_PUBLICO', 'Certificado de Registro Público'),
        ('AVALUO_PROPIEDAD', 'Avalúo de Propiedad'),
        ('PLANO_CATASTRADO', 'Plano Catastrado'),
        ('PAZ_SALVO_IMPUESTOS', 'Paz y Salvo de Impuestos'),
        ('CONTRATO_ALQUILER', 'Contrato de Alquiler'),
        ('RECIBO_SERVICIOS', 'Recibo de Servicios Públicos'),
        
        # Documentos de vehículos
        ('TARJETA_CIRCULACION', 'Tarjeta de Circulación'),
        ('POLIZA_SEGURO_VEHICULO', 'Póliza de Seguro de Vehículo'),
        ('CONTRATO_COMPRAVENTA_VEHICULO', 'Contrato de Compraventa de Vehículo'),
        
        # Documentos de crédito
        ('SOLICITUD_CREDITO', 'Solicitud de Crédito'),
        ('PAGARE', 'Pagaré'),
        ('CONTRATO_PRESTAMO', 'Contrato de Préstamo'),
        ('TABLA_AMORTIZACION', 'Tabla de Amortización'),
        ('AUTORIZACION_CENTRALES', 'Autorización Consulta Centrales de Riesgo'),
        
        # Referencias
        ('REFERENCIA_PERSONAL', 'Referencia Personal'),
        ('REFERENCIA_COMERCIAL', 'Referencia Comercial'),
        ('REFERENCIA_FAMILIAR', 'Referencia Familiar'),
        
        # Otros documentos
        ('FOTO_CLIENTE', 'Fotografía del Cliente'),
        ('ACTA_MATRIMONIO', 'Acta de Matrimonio'),
        ('ACTA_DIVORCIO', 'Acta de Divorcio'),
        ('PODER_NOTARIAL', 'Poder Notarial'),
        ('OTRO', 'Otro Documento')
    ]
    
    ESTADOS_DOCUMENTO = [
        ('PENDIENTE', 'Pendiente de Recibir'),
        ('RECIBIDO', 'Recibido'),
        ('VERIFICADO', 'Verificado'),
        ('RECHAZADO', 'Rechazado'),
        ('VENCIDO', 'Vencido'),
        ('RENOVADO', 'Renovado')
    ]
    
    CATEGORIAS = [
        ('IDENTIFICACION', 'Identificación'),
        ('LABORAL', 'Laboral'),
        ('BANCARIO', 'Bancario'),
        ('PROPIEDAD', 'Propiedad'),
        ('VEHICULO', 'Vehículo'),
        ('CREDITO', 'Crédito'),
        ('REFERENCIA', 'Referencia'),
        ('LEGAL', 'Legal'),
        ('OTRO', 'Otro')
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Relaciones con diferentes entidades
    cliente_id = Column(UUID(as_uuid=True), ForeignKey('clientes.id'), nullable=True)
    prestamo_id = Column(UUID(as_uuid=True), ForeignKey('prestamos.id'), nullable=True)
    solicitud_id = Column(UUID(as_uuid=True), ForeignKey('cliente_solicitudes.id'), nullable=True)
    propiedad_id = Column(UUID(as_uuid=True), ForeignKey('cliente_propiedades.id'), nullable=True)
    vehiculo_id = Column(UUID(as_uuid=True), ForeignKey('cliente_vehiculos.id'), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    sucursal_id = Column(UUID(as_uuid=True), ForeignKey('sucursales.id'), nullable=True)
    
    # Información del documento
    tipo_documento = Column(Enum(*[t[0] for t in TIPOS_DOCUMENTO], name='tipo_documento'), nullable=False)
    categoria = Column(Enum(*[c[0] for c in CATEGORIAS], name='categoria_documento'), nullable=False)
    estado = Column(Enum(*[e[0] for e in ESTADOS_DOCUMENTO], name='estado_documento'), default='PENDIENTE', nullable=False)
    
    # Metadatos del documento (encriptados)
    _nombre_archivo = Column("nombre_archivo", String(500), nullable=False, comment="Nombre original del archivo")
    _descripcion = Column("descripcion", Text, nullable=True, comment="Descripción del documento")
    _url_archivo = Column("url_archivo", String(500), nullable=False, comment="URL del archivo almacenado")
    _ruta_fisica = Column("ruta_fisica", String(500), nullable=True, comment="Ruta física del archivo")
    
    # Propiedades del archivo
    tamaño_bytes = Column(BigInteger, nullable=False, comment="Tamaño del archivo en bytes")
    mime_type = Column(String(100), nullable=False, comment="Tipo MIME del archivo")
    extension = Column(String(10), nullable=False, comment="Extensión del archivo")
    
    # Seguridad e integridad
    file_hash = Column(String(64), nullable=False, comment="Hash SHA-256 del archivo")
    checksum_md5 = Column(String(32), nullable=True, comment="Checksum MD5 adicional")
    esta_encriptado = Column(Boolean, default=True, nullable=False, comment="Si el archivo está encriptado")
    
    # Fechas importantes
    fecha_documento = Column(Date, nullable=True, comment="Fecha del documento (si aplica)")
    fecha_vencimiento = Column(Date, nullable=True, comment="Fecha de vencimiento del documento")
    fecha_recepcion = Column(DateTime, nullable=True, comment="Fecha de recepción del documento")
    fecha_verificacion = Column(DateTime, nullable=True, comment="Fecha de verificación")
    
    # Información de verificación
    verificado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    _observaciones_verificacion = Column("observaciones_verificacion", Text, nullable=True)
    es_obligatorio = Column(Boolean, default=False, nullable=False, comment="Si es un documento obligatorio")
    es_original = Column(Boolean, default=False, nullable=False, comment="Si es el documento original")
    
    # Metadatos adicionales
    numero_paginas = Column(Integer, nullable=True, comment="Número de páginas (para PDFs)")
    resolucion_dpi = Column(Integer, nullable=True, comment="Resolución en DPI (para imágenes)")
    _metadata_json = Column("metadata_json", Text, nullable=True, comment="Metadatos adicionales en JSON")
    
    # Control de versiones
    version = Column(Integer, default=1, nullable=False, comment="Versión del documento")
    documento_padre_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'), nullable=True)
    es_version_actual = Column(Boolean, default=True, nullable=False)
    
    # Información de acceso
    es_publico = Column(Boolean, default=False, nullable=False, comment="Si el cliente puede ver este documento")
    requiere_autorizacion = Column(Boolean, default=False, nullable=False)
    nivel_confidencialidad = Column(String(20), default='NORMAL', nullable=False)  # BAJO, NORMAL, ALTO, CRITICO
    
    # Descriptores para encriptación
    nombre_archivo = EncryptedColumn('nombre_archivo')
    descripcion = EncryptedColumn('descripcion')
    url_archivo = EncryptedColumn('url_archivo')
    ruta_fisica = EncryptedColumn('ruta_fisica')
    observaciones_verificacion = EncryptedColumn('observaciones_verificacion')
    metadata_json = EncryptedColumn('metadata_json')
    
    # Relaciones
    cliente = relationship("Cliente", back_populates="documentos")
    prestamo = relationship("Prestamo", back_populates="documentos")
    solicitud = relationship("ClienteSolicitud", back_populates="documentos")
    propiedad = relationship("ClientePropiedad")
    vehiculo = relationship("ClienteVehiculo")
    usuario_subida = relationship("Usuario", foreign_keys=[usuario_id])
    usuario_verificacion = relationship("Usuario", foreign_keys=[verificado_por])
    sucursal = relationship("Sucursal")
    documento_padre = relationship("Documento", remote_side=[id])
    versiones = relationship("Documento", back_populates="documento_padre")
    
    # Índices
    __table_args__ = (
        Index('idx_documento_cliente', 'cliente_id'),
        Index('idx_documento_prestamo', 'prestamo_id'),
        Index('idx_documento_propiedad', 'propiedad_id'),
        Index('idx_documento_vehiculo', 'vehiculo_id'),
        Index('idx_documento_tipo', 'tipo_documento'),
        Index('idx_documento_categoria', 'categoria'),
        Index('idx_documento_estado', 'estado'),
        Index('idx_documento_fecha_vencimiento', 'fecha_vencimiento'),
        Index('idx_documento_obligatorio', 'es_obligatorio'),
        Index('idx_documento_verificado', 'verificado_por'),
        Index('idx_documento_hash', 'file_hash'),
        Index('idx_documento_version_actual', 'es_version_actual'),
        Index('idx_documento_cliente_tipo', 'cliente_id', 'tipo_documento'),
        Index('idx_documento_cliente_categoria', 'cliente_id', 'categoria'),
    )
    
    @property
    def esta_vencido(self):
        """Verifica si el documento está vencido"""
        if not self.fecha_vencimiento:
            return False
        
        from datetime import date
        return date.today() > self.fecha_vencimiento
    
    @property
    def dias_para_vencimiento(self):
        """Calcula cuántos días faltan para el vencimiento"""
        if not self.fecha_vencimiento:
            return None
        
        from datetime import date
        diferencia = self.fecha_vencimiento - date.today()
        return diferencia.days
    
    @property
    def esta_verificado(self):
        """Verifica si el documento ha sido verificado"""
        return self.estado == 'VERIFICADO' and self.verificado_por is not None
    
    @property
    def tamaño_legible(self):
        """Retorna el tamaño del archivo en formato legible"""
        if self.tamaño_bytes < 1024:
            return f"{self.tamaño_bytes} B"
        elif self.tamaño_bytes < 1024 * 1024:
            return f"{self.tamaño_bytes / 1024:.1f} KB"
        elif self.tamaño_bytes < 1024 * 1024 * 1024:
            return f"{self.tamaño_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{self.tamaño_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    @property
    def nombre_tipo_legible(self):
        """Retorna el nombre legible del tipo de documento"""
        for codigo, nombre in self.TIPOS_DOCUMENTO:
            if codigo == self.tipo_documento:
                return nombre
        return self.tipo_documento
    
    def dias_desde_recepcion(self):
        """Calcula cuántos días han pasado desde la recepción"""
        if not self.fecha_recepcion:
            return None
        
        from datetime import datetime
        diferencia = datetime.utcnow() - self.fecha_recepcion
        return diferencia.days
    
    def __repr__(self):
        return f"<Documento {self.tipo_documento} - {self.nombre_archivo} de {self.cliente_id}>"


class AuditLog(Base):
    """Modelo para logs de auditoría"""
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=True)
    
    # Información del evento
    event_type = Column(String(50), nullable=False)  # login, data_access, etc.
    resource_type = Column(String(50), nullable=True)  # cliente, prestamo, etc.
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String(20), nullable=True)  # create, read, update, delete
    
    # Información de la sesión
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Detalles adicionales
    details = Column(Text, nullable=True)  # JSON con información adicional
    success = Column(Boolean, nullable=False, default=True)
    failure_reason = Column(String(255), nullable=True)
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="audit_logs")
    
    # Índices para consultas eficientes
    __table_args__ = (
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_usuario', 'usuario_id'),
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
    )

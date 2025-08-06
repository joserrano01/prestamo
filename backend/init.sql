-- Script de inicialización de la base de datos
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Crear esquema principal
CREATE SCHEMA IF NOT EXISTS financepro;

-- Tabla de sucursales
CREATE TABLE IF NOT EXISTS sucursales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    direccion TEXT,
    telefono VARCHAR(20),
    manager VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de usuarios con seguridad mejorada
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL DEFAULT 'employee',
    sucursal_id UUID REFERENCES sucursales(id),
    
    -- Campos de seguridad
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    last_login TIMESTAMP WITH TIME ZONE,
    last_password_change TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 2FA
    two_fa_secret VARCHAR(255),  -- Encriptado
    two_fa_enabled BOOLEAN DEFAULT false,
    backup_codes TEXT,  -- JSON encriptado
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_accessed_by UUID,
    access_count INTEGER DEFAULT 0
);

-- Tabla de clientes con encriptación
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre VARCHAR(255) NOT NULL,
    apellido VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    
    -- Campos encriptados (tamaño aumentado para datos encriptados)
    telefono VARCHAR(500),  -- Encriptado
    direccion TEXT,         -- Encriptado
    rfc VARCHAR(500),       -- Encriptado
    curp VARCHAR(500),      -- Encriptado
    fecha_nacimiento VARCHAR(500),  -- Encriptado
    
    -- Datos financieros
    ingresos_mensuales DECIMAL(12,2),
    ocupacion VARCHAR(255),
    estado_civil VARCHAR(20),
    credit_score INTEGER,
    
    -- Campos de seguridad
    is_active BOOLEAN DEFAULT true,
    risk_level VARCHAR(20) DEFAULT 'medium',
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_accessed_by UUID,
    access_count INTEGER DEFAULT 0
);

-- Tabla de préstamos con auditoría
CREATE TABLE IF NOT EXISTS prestamos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id UUID REFERENCES clientes(id),
    sucursal_id UUID REFERENCES sucursales(id),
    usuario_id UUID REFERENCES usuarios(id),
    
    -- Datos del préstamo
    monto DECIMAL(12,2) NOT NULL,
    plazo INTEGER NOT NULL, -- en meses
    tasa_interes DECIMAL(5,2) NOT NULL,
    fecha_inicio TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_vencimiento TIMESTAMP WITH TIME ZONE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    
    -- Cálculos financieros
    monto_total DECIMAL(12,2) NOT NULL,
    monto_pagado DECIMAL(12,2) DEFAULT 0,
    cuota_mensual DECIMAL(12,2) NOT NULL,
    
    -- Información adicional
    garantia TEXT,
    proposito TEXT,
    
    -- Campos de seguridad
    is_active BOOLEAN DEFAULT true,
    risk_assessment VARCHAR(20) DEFAULT 'medium',
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_accessed_by UUID,
    access_count INTEGER DEFAULT 0
);

-- Insertar datos iniciales
INSERT INTO sucursales (codigo, nombre, direccion, telefono, manager) VALUES
('central', 'Oficina Central - Ciudad de México', 'Av. Reforma 123, CDMX', '55-1234-5678', 'Juan Pérez'),
('guadalajara', 'Sucursal Guadalajara', 'Av. Vallarta 456, GDL', '33-2345-6789', 'María García'),
('monterrey', 'Sucursal Monterrey', 'Av. Constitución 789, MTY', '81-3456-7890', 'Carlos López')
ON CONFLICT (codigo) DO NOTHING;

-- Tabla de pagos
CREATE TABLE IF NOT EXISTS pagos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prestamo_id UUID REFERENCES prestamos(id),
    usuario_id UUID REFERENCES usuarios(id),
    
    monto DECIMAL(12,2) NOT NULL,
    fecha_pago TIMESTAMP WITH TIME ZONE NOT NULL,
    fecha_vencimiento TIMESTAMP WITH TIME ZONE NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    metodo_pago VARCHAR(50) NOT NULL,
    referencia VARCHAR(255),
    notas TEXT,
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Tabla de documentos con encriptación
CREATE TABLE IF NOT EXISTS documentos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prestamo_id UUID REFERENCES prestamos(id),
    cliente_id UUID REFERENCES clientes(id),
    
    tipo VARCHAR(50) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,  -- Encriptado
    tamaño INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA-256 para integridad
    
    -- Auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    updated_by UUID
);

-- Tabla de logs de auditoría
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    usuario_id UUID REFERENCES usuarios(id),
    
    -- Información del evento
    event_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    action VARCHAR(20),
    
    -- Información de la sesión
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(255),
    
    -- Detalles adicionales
    details TEXT,  -- JSON con información adicional
    success BOOLEAN DEFAULT true,
    failure_reason VARCHAR(255)
);

-- Tabla de sesiones activas
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_clientes_nombre_apellido ON clientes(nombre, apellido);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
CREATE INDEX IF NOT EXISTS idx_prestamos_cliente ON prestamos(cliente_id);
CREATE INDEX IF NOT EXISTS idx_prestamos_estado ON prestamos(estado);
CREATE INDEX IF NOT EXISTS idx_prestamos_fecha_vencimiento ON prestamos(fecha_vencimiento);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_usuario ON audit_logs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_sessions_usuario ON user_sessions(usuario_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON user_sessions(expires_at);

-- Insertar usuario administrador por defecto
INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'admin@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- password: admin123
    'Administrador',
    'Sistema',
    'admin',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'central'
ON CONFLICT (email) DO NOTHING;

-- Insertar sucursales de ejemplo
INSERT INTO sucursales (codigo, nombre, direccion, telefono, manager) VALUES
('SUC001', 'Sucursal Central', 'Av. Principal 123, Centro', '555-0001', 'Juan Pérez'),
('SUC002', 'Sucursal Norte', 'Calle Norte 456, Zona Norte', '555-0002', 'María García'),
('SUC003', 'Sucursal Sur', 'Av. Sur 789, Zona Sur', '555-0003', 'Carlos López'),
('SUC004', 'Sucursal Este', 'Blvd. Oriente 321, Zona Este', '555-0004', 'Ana Martínez'),
('SUC005', 'Sucursal Oeste', 'Calle Poniente 654, Zona Oeste', '555-0005', 'Roberto Silva')
ON CONFLICT (codigo) DO NOTHING;

-- Insertar usuarios de ejemplo para cada sucursal
-- Contraseña para todos: admin123 (hash: $2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW)
INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'admin@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Administrador',
    'Sistema',
    'admin',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'SUC001'
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'manager.central@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Juan',
    'Pérez',
    'manager',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'SUC001'
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'empleado.central@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Pedro',
    'González',
    'employee',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'SUC001'
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'manager.norte@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'María',
    'García',
    'manager',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'SUC002'
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'empleado.norte@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Laura',
    'Rodríguez',
    'employee',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'SUC002'
ON CONFLICT (email) DO NOTHING;

INSERT INTO usuarios (email, password_hash, nombre, apellido, rol, sucursal_id, is_verified) 
SELECT 
    'manager.sur@financepro.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    'Carlos',
    'López',
    'manager',
    s.id,
    true
FROM sucursales s WHERE s.codigo = 'SUC003'
ON CONFLICT (email) DO NOTHING;

-- Insertar log de auditoría inicial
INSERT INTO audit_logs (event_type, details, success)
VALUES ('system_init', 'Sistema inicializado con configuración de seguridad y datos de ejemplo', true);

-- Migración 002: Agregar geolocalización y múltiples teléfonos a sucursales
-- Fecha: 2025-01-04
-- Descripción: Mejora el modelo de sucursales con coordenadas GPS y soporte para múltiples teléfonos

BEGIN;

-- 1. Agregar nuevas columnas de geolocalización a la tabla sucursales
ALTER TABLE sucursales 
ADD COLUMN latitud NUMERIC(10,8) NULL,
ADD COLUMN longitud NUMERIC(11,8) NULL,
ADD COLUMN altitud NUMERIC(8,2) NULL,
ADD COLUMN ciudad VARCHAR(100) NULL,
ADD COLUMN provincia VARCHAR(100) NULL,
ADD COLUMN codigo_postal VARCHAR(20) NULL,
ADD COLUMN pais VARCHAR(100) NOT NULL DEFAULT 'Panamá',
ADD COLUMN email_sucursal VARCHAR(255) NULL,
ADD COLUMN horario_apertura TIME NULL,
ADD COLUMN horario_cierre TIME NULL,
ADD COLUMN dias_operacion VARCHAR(50) NULL DEFAULT 'Lunes-Viernes',
ADD COLUMN permite_prestamos BOOLEAN NOT NULL DEFAULT TRUE,
ADD COLUMN limite_prestamo_diario NUMERIC(15,2) NULL;

-- 2. Crear tabla para múltiples teléfonos de sucursales
CREATE TABLE sucursal_telefonos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sucursal_id UUID NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    numero VARCHAR(20) NOT NULL,
    tipo VARCHAR(50) NOT NULL DEFAULT 'principal',
    extension VARCHAR(10) NULL,
    descripcion VARCHAR(255) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_whatsapp BOOLEAN NOT NULL DEFAULT FALSE,
    is_publico BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Campos de auditoría
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID NULL,
    updated_by UUID NULL,
    
    -- Constraints
    CONSTRAINT chk_sucursal_telefono_tipo CHECK (tipo IN ('principal', 'secundario', 'fax', 'movil', 'whatsapp', 'emergencia'))
);

-- 3. Crear índices para optimizar consultas
CREATE INDEX idx_sucursal_telefono_numero ON sucursal_telefonos(numero);
CREATE INDEX idx_sucursal_telefono_tipo ON sucursal_telefonos(tipo);
CREATE INDEX idx_sucursal_telefono_sucursal ON sucursal_telefonos(sucursal_id);
CREATE INDEX idx_sucursal_geolocation ON sucursales(latitud, longitud) WHERE latitud IS NOT NULL AND longitud IS NOT NULL;
CREATE INDEX idx_sucursal_ciudad ON sucursales(ciudad);
CREATE INDEX idx_sucursal_provincia ON sucursales(provincia);

-- 4. Migrar teléfonos existentes de la columna telefono a la nueva tabla
INSERT INTO sucursal_telefonos (sucursal_id, numero, tipo, descripcion, is_active, is_publico)
SELECT 
    id as sucursal_id,
    telefono as numero,
    'principal' as tipo,
    'Teléfono principal migrado' as descripcion,
    TRUE as is_active,
    TRUE as is_publico
FROM sucursales 
WHERE telefono IS NOT NULL AND telefono != '';

-- 5. Actualizar datos de ubicación para sucursales existentes
-- Sucursal Bugaba (aproximadamente)
UPDATE sucursales 
SET 
    latitud = 8.4833,
    longitud = -82.6167,
    ciudad = 'Bugaba',
    provincia = 'Chiriquí',
    codigo_postal = '0426',
    horario_apertura = '08:00:00',
    horario_cierre = '17:00:00',
    dias_operacion = 'Lunes-Viernes',
    email_sucursal = 'bugaba@financepro.com'
WHERE codigo = 'S01';

-- Sucursal David (aproximadamente)
UPDATE sucursales 
SET 
    latitud = 8.4333,
    longitud = -82.4333,
    ciudad = 'David',
    provincia = 'Chiriquí',
    codigo_postal = '0401',
    horario_apertura = '08:00:00',
    horario_cierre = '17:00:00',
    dias_operacion = 'Lunes-Viernes',
    email_sucursal = 'david@financepro.com'
WHERE codigo = 'S02';

-- 6. Agregar teléfonos adicionales de ejemplo
INSERT INTO sucursal_telefonos (sucursal_id, numero, tipo, descripcion, is_active, is_whatsapp, is_publico) VALUES
-- Sucursal Bugaba
((SELECT id FROM sucursales WHERE codigo = 'S01'), '507-775-1235', 'secundario', 'Línea directa gerencia', TRUE, FALSE, TRUE),
((SELECT id FROM sucursales WHERE codigo = 'S01'), '507-775-1236', 'fax', 'Fax oficina', TRUE, FALSE, FALSE),
((SELECT id FROM sucursales WHERE codigo = 'S01'), '507-6123-4567', 'movil', 'WhatsApp atención cliente', TRUE, TRUE, TRUE),

-- Sucursal David
((SELECT id FROM sucursales WHERE codigo = 'S02'), '507-775-5679', 'secundario', 'Línea directa gerencia', TRUE, FALSE, TRUE),
((SELECT id FROM sucursales WHERE codigo = 'S02'), '507-775-5680', 'fax', 'Fax oficina', TRUE, FALSE, FALSE),
((SELECT id FROM sucursales WHERE codigo = 'S02'), '507-6987-6543', 'movil', 'WhatsApp atención cliente', TRUE, TRUE, TRUE);

-- 7. Crear trigger para actualizar updated_at en sucursal_telefonos
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_sucursal_telefonos_updated_at 
    BEFORE UPDATE ON sucursal_telefonos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 8. Agregar comentarios a las tablas y columnas
COMMENT ON TABLE sucursal_telefonos IS 'Múltiples teléfonos por sucursal con tipos y características específicas';
COMMENT ON COLUMN sucursales.latitud IS 'Latitud en grados decimales (WGS84)';
COMMENT ON COLUMN sucursales.longitud IS 'Longitud en grados decimales (WGS84)';
COMMENT ON COLUMN sucursales.altitud IS 'Altitud sobre el nivel del mar en metros';
COMMENT ON COLUMN sucursales.limite_prestamo_diario IS 'Límite máximo de préstamos que puede otorgar la sucursal por día';

-- 9. Verificar que la migración se ejecutó correctamente
DO $$
DECLARE
    sucursal_count INTEGER;
    telefono_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO sucursal_count FROM sucursales WHERE latitud IS NOT NULL;
    SELECT COUNT(*) INTO telefono_count FROM sucursal_telefonos;
    
    RAISE NOTICE 'Migración completada:';
    RAISE NOTICE '- Sucursales con coordenadas: %', sucursal_count;
    RAISE NOTICE '- Teléfonos migrados: %', telefono_count;
    
    IF sucursal_count = 0 THEN
        RAISE WARNING 'No se encontraron sucursales con coordenadas actualizadas';
    END IF;
    
    IF telefono_count = 0 THEN
        RAISE WARNING 'No se migraron teléfonos a la nueva tabla';
    END IF;
END $$;

COMMIT;

-- Opcional: Eliminar la columna telefono antigua después de verificar que todo funciona
-- ALTER TABLE sucursales DROP COLUMN telefono;

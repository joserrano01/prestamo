-- Migración 001: Agregar código de usuario y soporte para múltiples emails
-- Fecha: 2024-01-XX
-- Descripción: Agrega codigo_usuario y cambia email a email_principal

BEGIN;

-- 1. Agregar nueva columna codigo_usuario
ALTER TABLE usuarios ADD COLUMN codigo_usuario VARCHAR(50);

-- 2. Generar códigos únicos para usuarios existentes usando un enfoque diferente
DO $$
DECLARE
    user_record RECORD;
    counter INTEGER := 1;
BEGIN
    FOR user_record IN SELECT id FROM usuarios ORDER BY created_at LOOP
        UPDATE usuarios SET codigo_usuario = 'USR' || LPAD(counter::text, 3, '0') WHERE id = user_record.id;
        counter := counter + 1;
    END LOOP;
END $$;

-- 3. Hacer codigo_usuario NOT NULL y único
ALTER TABLE usuarios ALTER COLUMN codigo_usuario SET NOT NULL;
CREATE UNIQUE INDEX ix_usuarios_codigo_usuario ON usuarios(codigo_usuario);

-- 4. Renombrar columna email a email_principal
ALTER TABLE usuarios RENAME COLUMN email TO email_principal;

-- 5. Renombrar índice correspondiente
ALTER INDEX ix_usuarios_email RENAME TO ix_usuarios_email_principal;

-- 6. Verificar que la tabla usuario_emails ya existe (creada por SQLAlchemy)
-- Si no existe, la creamos
CREATE TABLE IF NOT EXISTS usuario_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    tipo_email VARCHAR(50) NOT NULL DEFAULT 'secundario',
    is_verified BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Crear índices para usuario_emails si no existen
CREATE INDEX IF NOT EXISTS ix_usuario_emails_email ON usuario_emails(email);
CREATE INDEX IF NOT EXISTS ix_usuario_emails_usuario_id ON usuario_emails(usuario_id);

-- 8. Verificar integridad de datos
DO $$
BEGIN
    -- Verificar que todos los usuarios tienen codigo_usuario
    IF EXISTS (SELECT 1 FROM usuarios WHERE codigo_usuario IS NULL) THEN
        RAISE EXCEPTION 'Hay usuarios sin codigo_usuario';
    END IF;
    
    -- Verificar que todos los códigos son únicos
    IF (SELECT COUNT(*) FROM usuarios) != (SELECT COUNT(DISTINCT codigo_usuario) FROM usuarios) THEN
        RAISE EXCEPTION 'Hay códigos de usuario duplicados';
    END IF;
    
    RAISE NOTICE 'Migración completada exitosamente';
END $$;

COMMIT;

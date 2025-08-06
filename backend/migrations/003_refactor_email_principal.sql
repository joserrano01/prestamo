-- Migración 003: Refactorizar email principal y agregar código de empleado
-- Fecha: 2025-01-04
-- Descripción: Mover el email_principal de usuarios a usuario_emails con flag is_principal y agregar codigo_empleado

BEGIN;

-- 1. Agregar columna is_principal a usuario_emails
ALTER TABLE usuario_emails 
ADD COLUMN is_principal BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Agregar columna codigo_empleado a usuarios
ALTER TABLE usuarios 
ADD COLUMN codigo_empleado VARCHAR(50) UNIQUE NULL;

-- 3. Crear índice para codigo_empleado
CREATE INDEX idx_usuario_codigo_empleado ON usuarios(codigo_empleado);

-- 4. Crear índice para is_principal
CREATE INDEX idx_usuario_email_principal ON usuario_emails(is_principal);

-- 3. Migrar emails principales existentes de usuarios a usuario_emails
INSERT INTO usuario_emails (usuario_id, email, tipo, is_principal, is_verified, is_active)
SELECT 
    id as usuario_id,
    email_principal as email,
    'principal' as tipo,
    TRUE as is_principal,
    TRUE as is_verified,  -- Asumimos que los emails principales están verificados
    TRUE as is_active
FROM usuarios 
WHERE email_principal IS NOT NULL AND email_principal != '';

-- 4. Verificar que no hay duplicados (por si el email principal ya existe en usuario_emails)
-- Eliminar duplicados manteniendo el que tiene is_principal = TRUE
DELETE FROM usuario_emails 
WHERE id IN (
    SELECT id FROM (
        SELECT id, 
               ROW_NUMBER() OVER (PARTITION BY usuario_id, email ORDER BY is_principal DESC, created_at ASC) as rn
        FROM usuario_emails
    ) t 
    WHERE rn > 1
);

-- 5. Asegurar que cada usuario tenga exactamente un email principal
-- Si un usuario no tiene email principal, marcar el más antiguo como principal
UPDATE usuario_emails 
SET is_principal = TRUE 
WHERE id IN (
    SELECT DISTINCT ON (usuario_id) id
    FROM usuario_emails ue1
    WHERE is_active = TRUE 
    AND NOT EXISTS (
        SELECT 1 FROM usuario_emails ue2 
        WHERE ue2.usuario_id = ue1.usuario_id 
        AND ue2.is_principal = TRUE
    )
    ORDER BY usuario_id, created_at ASC
);

-- 6. Verificar integridad: cada usuario debe tener exactamente un email principal
DO $$
DECLARE
    usuarios_sin_principal INTEGER;
    usuarios_multiples_principales INTEGER;
BEGIN
    -- Contar usuarios sin email principal
    SELECT COUNT(DISTINCT u.id) INTO usuarios_sin_principal
    FROM usuarios u
    LEFT JOIN usuario_emails ue ON u.id = ue.usuario_id AND ue.is_principal = TRUE AND ue.is_active = TRUE
    WHERE ue.id IS NULL;
    
    -- Contar usuarios con múltiples emails principales
    SELECT COUNT(*) INTO usuarios_multiples_principales
    FROM (
        SELECT usuario_id, COUNT(*) as count_principales
        FROM usuario_emails 
        WHERE is_principal = TRUE AND is_active = TRUE
        GROUP BY usuario_id
        HAVING COUNT(*) > 1
    ) t;
    
    IF usuarios_sin_principal > 0 THEN
        RAISE WARNING 'Hay % usuarios sin email principal', usuarios_sin_principal;
    END IF;
    
    IF usuarios_multiples_principales > 0 THEN
        RAISE WARNING 'Hay % usuarios con múltiples emails principales', usuarios_multiples_principales;
    END IF;
    
    RAISE NOTICE 'Verificación completada:';
    RAISE NOTICE '- Usuarios sin email principal: %', usuarios_sin_principal;
    RAISE NOTICE '- Usuarios con múltiples principales: %', usuarios_multiples_principales;
END $$;

-- 7. Actualizar constraint para evitar múltiples emails principales por usuario
-- (Se implementará a nivel de aplicación para mayor flexibilidad)

-- 8. Agregar comentarios
COMMENT ON COLUMN usuario_emails.is_principal IS 'Indica si este es el email principal del usuario (solo uno por usuario)';

-- 9. Mostrar estadísticas finales
DO $$
DECLARE
    total_usuarios INTEGER;
    total_emails INTEGER;
    emails_principales INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_usuarios FROM usuarios;
    SELECT COUNT(*) INTO total_emails FROM usuario_emails WHERE is_active = TRUE;
    SELECT COUNT(*) INTO emails_principales FROM usuario_emails WHERE is_principal = TRUE AND is_active = TRUE;
    
    RAISE NOTICE 'Migración completada exitosamente:';
    RAISE NOTICE '- Total usuarios: %', total_usuarios;
    RAISE NOTICE '- Total emails activos: %', total_emails;
    RAISE NOTICE '- Emails principales: %', emails_principales;
END $$;

COMMIT;

-- Nota: La columna email_principal se eliminará en una migración posterior
-- después de verificar que todo funciona correctamente
-- ALTER TABLE usuarios DROP COLUMN email_principal;

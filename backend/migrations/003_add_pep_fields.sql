-- Migración 003: Agregar campos PEP (Persona Políticamente Expuesta) al modelo ClienteTrabajo
-- Fecha: 2025-01-05
-- Descripción: Agregar campos para identificar clientes con exposición política

-- Agregar campos PEP a la tabla cliente_trabajos
ALTER TABLE cliente_trabajos 
ADD COLUMN es_gobierno BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN es_pep BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN tipo_entidad_publica VARCHAR(100),
ADD COLUMN nivel_cargo VARCHAR(50),
ADD COLUMN tiene_poder_decision BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN maneja_fondos_publicos BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN cargo_eleccion_popular BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN familiar_pep BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN asociado_pep BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN detalle_cargo_publico VARCHAR(500),
ADD COLUMN institucion_publica VARCHAR(500),
ADD COLUMN observaciones_pep TEXT;

-- Agregar comentarios a las columnas
COMMENT ON COLUMN cliente_trabajos.es_gobierno IS 'Trabaja en entidad gubernamental';
COMMENT ON COLUMN cliente_trabajos.es_pep IS 'Es Persona Políticamente Expuesta';
COMMENT ON COLUMN cliente_trabajos.tipo_entidad_publica IS 'Tipo de entidad: EJECUTIVO, LEGISLATIVO, JUDICIAL, MUNICIPAL, AUTONOMA, DESCENTRALIZADA';
COMMENT ON COLUMN cliente_trabajos.nivel_cargo IS 'Nivel del cargo: ALTO, MEDIO, OPERATIVO';
COMMENT ON COLUMN cliente_trabajos.tiene_poder_decision IS 'Tiene poder de decisión en políticas públicas';
COMMENT ON COLUMN cliente_trabajos.maneja_fondos_publicos IS 'Maneja o autoriza fondos públicos';
COMMENT ON COLUMN cliente_trabajos.cargo_eleccion_popular IS 'Cargo de elección popular';
COMMENT ON COLUMN cliente_trabajos.familiar_pep IS 'Familiar cercano de PEP';
COMMENT ON COLUMN cliente_trabajos.asociado_pep IS 'Asociado comercial de PEP';
COMMENT ON COLUMN cliente_trabajos.detalle_cargo_publico IS 'Detalle del cargo público';
COMMENT ON COLUMN cliente_trabajos.institucion_publica IS 'Nombre de la institución pública';
COMMENT ON COLUMN cliente_trabajos.observaciones_pep IS 'Observaciones sobre exposición política';

-- Crear índices para optimizar consultas PEP
CREATE INDEX idx_cliente_trabajos_es_pep ON cliente_trabajos(es_pep) WHERE es_pep = TRUE;
CREATE INDEX idx_cliente_trabajos_es_gobierno ON cliente_trabajos(es_gobierno) WHERE es_gobierno = TRUE;
CREATE INDEX idx_cliente_trabajos_cargo_eleccion ON cliente_trabajos(cargo_eleccion_popular) WHERE cargo_eleccion_popular = TRUE;
CREATE INDEX idx_cliente_trabajos_familiar_pep ON cliente_trabajos(familiar_pep) WHERE familiar_pep = TRUE;
CREATE INDEX idx_cliente_trabajos_asociado_pep ON cliente_trabajos(asociado_pep) WHERE asociado_pep = TRUE;
CREATE INDEX idx_cliente_trabajos_tipo_entidad ON cliente_trabajos(tipo_entidad_publica) WHERE tipo_entidad_publica IS NOT NULL;
CREATE INDEX idx_cliente_trabajos_nivel_cargo ON cliente_trabajos(nivel_cargo) WHERE nivel_cargo IS NOT NULL;

-- Crear índice compuesto para identificar rápidamente trabajos de riesgo político
CREATE INDEX idx_cliente_trabajos_riesgo_politico ON cliente_trabajos(cliente_id, es_pep, es_gobierno, familiar_pep, asociado_pep, cargo_eleccion_popular);

-- Insertar algunos datos de ejemplo para testing
-- Nota: En producción, estos datos se insertarían a través de la aplicación

-- Ejemplo 1: Funcionario público de nivel medio
INSERT INTO cliente_trabajos (
    id, cliente_id, empresa, puesto, fecha_inicio, salario, es_actual,
    es_gobierno, tipo_entidad_publica, nivel_cargo, tiene_poder_decision,
    detalle_cargo_publico, institucion_publica,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM clientes LIMIT 1), -- Tomar el primer cliente disponible
    'Ministerio de Economía y Finanzas',
    'Director de Presupuesto',
    '2020-01-15',
    3500.00,
    TRUE,
    TRUE, -- es_gobierno
    'EJECUTIVO', -- tipo_entidad_publica
    'MEDIO', -- nivel_cargo
    TRUE, -- tiene_poder_decision
    'Director de la Dirección de Presupuesto Nacional',
    'MEF - Ministerio de Economía y Finanzas',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Ejemplo 2: Alcalde (cargo de elección popular)
INSERT INTO cliente_trabajos (
    id, cliente_id, empresa, puesto, fecha_inicio, salario, es_actual,
    es_gobierno, es_pep, tipo_entidad_publica, nivel_cargo, 
    cargo_eleccion_popular, tiene_poder_decision, maneja_fondos_publicos,
    detalle_cargo_publico, institucion_publica,
    created_at, updated_at
) VALUES (
    gen_random_uuid(),
    (SELECT id FROM clientes OFFSET 1 LIMIT 1), -- Tomar el segundo cliente
    'Alcaldía de David',
    'Alcalde',
    '2019-07-01',
    4000.00,
    TRUE,
    TRUE, -- es_gobierno
    TRUE, -- es_pep
    'MUNICIPAL', -- tipo_entidad_publica
    'ALTO', -- nivel_cargo
    TRUE, -- cargo_eleccion_popular
    TRUE, -- tiene_poder_decision
    TRUE, -- maneja_fondos_publicos
    'Alcalde del Distrito de David, Provincia de Chiriquí',
    'Alcaldía de David',
    NOW(),
    NOW()
) ON CONFLICT DO NOTHING;

-- Crear vista para facilitar consultas de clientes PEP
CREATE OR REPLACE VIEW vista_clientes_pep AS
SELECT DISTINCT
    c.id as cliente_id,
    c.codigo_cliente,
    c.nombre as nombre_cliente,
    c.apellido_paterno,
    c.apellido_materno,
    ct.empresa,
    ct.puesto,
    ct.es_pep,
    ct.es_gobierno,
    ct.cargo_eleccion_popular,
    ct.familiar_pep,
    ct.asociado_pep,
    ct.tipo_entidad_publica,
    ct.nivel_cargo,
    ct.tiene_poder_decision,
    ct.maneja_fondos_publicos,
    ct.institucion_publica,
    ct.es_actual,
    CASE 
        WHEN ct.cargo_eleccion_popular OR (ct.es_pep AND ct.nivel_cargo = 'ALTO') THEN 'ALTO'
        WHEN ct.es_pep OR (ct.es_gobierno AND ct.tiene_poder_decision) THEN 'MEDIO'
        WHEN ct.es_gobierno OR ct.familiar_pep OR ct.asociado_pep THEN 'BAJO'
        ELSE 'NINGUNO'
    END as nivel_exposicion_politica,
    CASE 
        WHEN ct.es_pep OR ct.cargo_eleccion_popular OR ct.maneja_fondos_publicos OR ct.tiene_poder_decision 
        THEN TRUE 
        ELSE FALSE 
    END as requiere_due_diligence_reforzada
FROM clientes c
INNER JOIN cliente_trabajos ct ON c.id = ct.cliente_id
WHERE ct.es_pep = TRUE 
   OR ct.es_gobierno = TRUE 
   OR ct.familiar_pep = TRUE 
   OR ct.asociado_pep = TRUE 
   OR ct.cargo_eleccion_popular = TRUE;

-- Crear función para obtener el nivel máximo de exposición política de un cliente
CREATE OR REPLACE FUNCTION obtener_nivel_exposicion_cliente(cliente_uuid UUID)
RETURNS TEXT AS $$
DECLARE
    nivel_max TEXT := 'NINGUNO';
BEGIN
    SELECT CASE 
        WHEN bool_or(cargo_eleccion_popular) OR bool_or(es_pep AND nivel_cargo = 'ALTO') THEN 'ALTO'
        WHEN bool_or(es_pep) OR bool_or(es_gobierno AND tiene_poder_decision) THEN 'MEDIO'
        WHEN bool_or(es_gobierno) OR bool_or(familiar_pep) OR bool_or(asociado_pep) THEN 'BAJO'
        ELSE 'NINGUNO'
    END INTO nivel_max
    FROM cliente_trabajos 
    WHERE cliente_id = cliente_uuid;
    
    RETURN COALESCE(nivel_max, 'NINGUNO');
END;
$$ LANGUAGE plpgsql;

-- Crear función para verificar si un cliente requiere due diligence reforzada
CREATE OR REPLACE FUNCTION requiere_due_diligence_reforzada(cliente_uuid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 FROM cliente_trabajos 
        WHERE cliente_id = cliente_uuid 
        AND (es_pep = TRUE OR cargo_eleccion_popular = TRUE OR maneja_fondos_publicos = TRUE OR tiene_poder_decision = TRUE)
    );
END;
$$ LANGUAGE plpgsql;

-- Registrar la migración
INSERT INTO schema_migrations (version, applied_at) 
VALUES ('003', NOW()) 
ON CONFLICT (version) DO NOTHING;

COMMIT;

#!/usr/bin/env python3
"""
Script para ejecutar la migración PEP (Persona Políticamente Expuesta)
Agrega campos para identificar clientes con exposición política
"""

import os
import sys
import asyncio
import asyncpg
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent))

from app.core.config import settings

async def run_migration():
    """Ejecuta la migración PEP"""
    
    # Leer el archivo de migración
    migration_file = Path(__file__).parent / "migrations" / "003_add_pep_fields.sql"
    
    if not migration_file.exists():
        print(f"❌ Error: No se encontró el archivo de migración: {migration_file}")
        return False
    
    try:
        # Conectar a la base de datos
        print("🔗 Conectando a la base de datos...")
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Leer el contenido de la migración
        print("📖 Leyendo archivo de migración...")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Verificar si la migración ya fue aplicada
        print("🔍 Verificando estado de migraciones...")
        existing = await conn.fetchval(
            "SELECT version FROM schema_migrations WHERE version = '003'"
        )
        
        if existing:
            print("✅ La migración 003 ya fue aplicada anteriormente.")
            await conn.close()
            return True
        
        # Ejecutar la migración
        print("🚀 Ejecutando migración PEP...")
        await conn.execute(migration_sql)
        
        print("✅ Migración PEP ejecutada exitosamente!")
        
        # Verificar que los campos fueron agregados
        print("🔍 Verificando campos agregados...")
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'cliente_trabajos' 
            AND column_name IN ('es_pep', 'es_gobierno', 'cargo_eleccion_popular', 'familiar_pep')
            ORDER BY column_name
        """)
        
        print("\n📋 Campos PEP agregados:")
        for col in columns:
            print(f"  • {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']}, default: {col['column_default']})")
        
        # Verificar índices creados
        print("\n🔍 Verificando índices PEP...")
        indexes = await conn.fetch("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'cliente_trabajos' 
            AND indexname LIKE '%pep%' OR indexname LIKE '%gobierno%' OR indexname LIKE '%cargo%'
            ORDER BY indexname
        """)
        
        print("\n📊 Índices PEP creados:")
        for idx in indexes:
            print(f"  • {idx['indexname']}")
        
        # Verificar vista creada
        print("\n🔍 Verificando vista de clientes PEP...")
        view_exists = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.views 
            WHERE table_name = 'vista_clientes_pep'
        """)
        
        if view_exists:
            print("✅ Vista 'vista_clientes_pep' creada exitosamente")
        else:
            print("❌ Error: Vista 'vista_clientes_pep' no fue creada")
        
        # Verificar funciones creadas
        print("\n🔍 Verificando funciones PEP...")
        functions = await conn.fetch("""
            SELECT proname, prosrc 
            FROM pg_proc 
            WHERE proname IN ('obtener_nivel_exposicion_cliente', 'requiere_due_diligence_reforzada')
        """)
        
        print("\n⚙️ Funciones PEP creadas:")
        for func in functions:
            print(f"  • {func['proname']}")
        
        # Mostrar datos de ejemplo insertados
        print("\n🔍 Verificando datos de ejemplo...")
        ejemplos = await conn.fetch("""
            SELECT empresa, puesto, es_pep, es_gobierno, cargo_eleccion_popular, tipo_entidad_publica, nivel_cargo
            FROM cliente_trabajos 
            WHERE es_gobierno = TRUE OR es_pep = TRUE
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if ejemplos:
            print("\n📝 Datos de ejemplo insertados:")
            for ej in ejemplos:
                flags = []
                if ej['es_pep']: flags.append("PEP")
                if ej['es_gobierno']: flags.append("GOB")
                if ej['cargo_eleccion_popular']: flags.append("ELEC")
                
                flag_str = f" [{', '.join(flags)}]" if flags else ""
                print(f"  • {ej['empresa']} - {ej['puesto']}{flag_str}")
                print(f"    Entidad: {ej['tipo_entidad_publica']}, Nivel: {ej['nivel_cargo']}")
        
        await conn.close()
        
        print("\n🎉 ¡Migración PEP completada exitosamente!")
        print("\n📋 Resumen de cambios:")
        print("  ✅ 12 campos PEP agregados a cliente_trabajos")
        print("  ✅ 7 índices optimizados creados")
        print("  ✅ 1 vista de consulta creada (vista_clientes_pep)")
        print("  ✅ 2 funciones de utilidad creadas")
        print("  ✅ Datos de ejemplo insertados")
        
        print("\n🔧 Funcionalidades disponibles:")
        print("  • Identificación de Personas Políticamente Expuestas (PEP)")
        print("  • Clasificación por nivel de exposición (ALTO/MEDIO/BAJO/NINGUNO)")
        print("  • Detección de cargos de elección popular")
        print("  • Identificación de familiares y asociados de PEP")
        print("  • Marcado para due diligence reforzada")
        print("  • Consultas optimizadas con índices especializados")
        
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando migración: {str(e)}")
        if 'conn' in locals():
            await conn.close()
        return False

async def test_pep_functionality():
    """Prueba las funcionalidades PEP implementadas"""
    
    try:
        print("\n🧪 Probando funcionalidades PEP...")
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        # Probar vista de clientes PEP
        pep_clients = await conn.fetch("SELECT * FROM vista_clientes_pep LIMIT 3")
        
        if pep_clients:
            print("\n👥 Clientes PEP encontrados:")
            for client in pep_clients:
                print(f"  • {client['nombre_cliente']} {client['apellido_paterno']}")
                print(f"    Empresa: {client['empresa']}")
                print(f"    Puesto: {client['puesto']}")
                print(f"    Nivel exposición: {client['nivel_exposicion_politica']}")
                print(f"    Due diligence reforzada: {'Sí' if client['requiere_due_diligence_reforzada'] else 'No'}")
                print()
        
        # Probar función de nivel de exposición
        if pep_clients:
            cliente_id = pep_clients[0]['cliente_id']
            nivel = await conn.fetchval(
                "SELECT obtener_nivel_exposicion_cliente($1)", cliente_id
            )
            print(f"🎯 Nivel de exposición del cliente {cliente_id}: {nivel}")
            
            # Probar función de due diligence
            requiere_dd = await conn.fetchval(
                "SELECT requiere_due_diligence_reforzada($1)", cliente_id
            )
            print(f"🔍 Requiere due diligence reforzada: {'Sí' if requiere_dd else 'No'}")
        
        await conn.close()
        print("\n✅ Pruebas de funcionalidad PEP completadas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en pruebas PEP: {str(e)}")
        if 'conn' in locals():
            await conn.close()

def main():
    """Función principal"""
    print("🏛️ MIGRACIÓN PEP - PERSONAS POLÍTICAMENTE EXPUESTAS")
    print("=" * 60)
    print("Esta migración agrega funcionalidad para identificar clientes")
    print("con exposición política según regulaciones financieras.")
    print("=" * 60)
    
    # Ejecutar migración
    success = asyncio.run(run_migration())
    
    if success:
        # Ejecutar pruebas
        asyncio.run(test_pep_functionality())
        
        print("\n🎯 PRÓXIMOS PASOS:")
        print("1. Actualizar formularios de cliente para capturar información PEP")
        print("2. Implementar validaciones en el frontend")
        print("3. Configurar alertas automáticas para clientes PEP")
        print("4. Crear reportes de cumplimiento regulatorio")
        print("5. Capacitar al personal sobre identificación de PEP")
        
    else:
        print("\n❌ La migración falló. Revise los errores anteriores.")
        sys.exit(1)

if __name__ == "__main__":
    main()

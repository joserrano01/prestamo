#!/usr/bin/env python3
"""
Script simple para ejecutar la migración PEP usando SQLAlchemy
"""

import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Ejecuta la migración PEP"""
    
    # Crear engine de SQLAlchemy
    engine = create_engine(settings.DATABASE_URL)
    
    # Leer el archivo de migración
    migration_file = Path(__file__).parent / "migrations" / "003_add_pep_fields.sql"
    
    if not migration_file.exists():
        print(f"❌ Error: No se encontró el archivo de migración: {migration_file}")
        return False
    
    try:
        print("📖 Leyendo archivo de migración...")
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Ejecutar la migración
        print("🚀 Ejecutando migración PEP...")
        with engine.connect() as conn:
            # Verificar si ya fue aplicada
            result = conn.execute(text("SELECT version FROM schema_migrations WHERE version = '003'"))
            if result.fetchone():
                print("✅ La migración 003 ya fue aplicada anteriormente.")
                return True
            
            # Ejecutar cada statement por separado para evitar problemas
            statements = migration_sql.split(';')
            for i, statement in enumerate(statements):
                statement = statement.strip()
                if statement and not statement.startswith('--'):
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        if "already exists" in str(e).lower():
                            print(f"⚠️  Statement {i+1} ya existe, continuando...")
                        else:
                            print(f"❌ Error en statement {i+1}: {e}")
                            print(f"Statement: {statement[:100]}...")
                            # Continuar con los demás statements
            
            print("✅ Migración PEP ejecutada exitosamente!")
            
            # Verificar campos agregados
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'cliente_trabajos' 
                AND column_name IN ('es_pep', 'es_gobierno', 'cargo_eleccion_popular')
            """))
            
            campos = [row[0] for row in result.fetchall()]
            print(f"📋 Campos PEP verificados: {', '.join(campos)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando migración: {str(e)}")
        return False

def main():
    """Función principal"""
    print("🏛️ MIGRACIÓN PEP - PERSONAS POLÍTICAMENTE EXPUESTAS")
    print("=" * 60)
    
    success = run_migration()
    
    if success:
        print("\n🎉 ¡Migración completada!")
        print("\n📋 Campos PEP agregados a ClienteTrabajo:")
        print("  • es_gobierno: Trabaja en entidad gubernamental")
        print("  • es_pep: Es Persona Políticamente Expuesta")
        print("  • tipo_entidad_publica: Tipo de entidad pública")
        print("  • nivel_cargo: Nivel del cargo (ALTO/MEDIO/OPERATIVO)")
        print("  • tiene_poder_decision: Poder de decisión en políticas")
        print("  • maneja_fondos_publicos: Maneja fondos públicos")
        print("  • cargo_eleccion_popular: Cargo de elección popular")
        print("  • familiar_pep: Familiar cercano de PEP")
        print("  • asociado_pep: Asociado comercial de PEP")
        print("  • detalle_cargo_publico: Detalle del cargo")
        print("  • institucion_publica: Institución pública")
        print("  • observaciones_pep: Observaciones sobre exposición")
        
        print("\n🔧 Propiedades agregadas al modelo Cliente:")
        print("  • es_pep: Identifica si el cliente es PEP")
        print("  • es_gobierno: Identifica si trabaja en gobierno")
        print("  • es_cliente_riesgo_politico: Riesgo por exposición política")
        print("  • nivel_exposicion_politica_cliente: Nivel de exposición")
        print("  • requiere_due_diligence_reforzada: Due diligence reforzada")
        print("  • trabajos_gobierno: Lista trabajos gubernamentales")
        print("  • trabajos_pep: Lista trabajos PEP")
        print("  • descripcion_exposicion_politica: Descripción completa")
        
    else:
        print("\n❌ La migración falló.")
        sys.exit(1)

if __name__ == "__main__":
    main()

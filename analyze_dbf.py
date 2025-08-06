from dbfread import DBF
import os
import json

def analyze_dbf(filepath):
    try:
        print(f"\nAnalizando archivo: {os.path.basename(filepath)}")
        table = DBF(filepath, encoding='latin1')  # Usamos latin1 para manejar caracteres especiales
        
        print(f"\nEstructura del archivo: {filepath}")
        print(f"Número de registros: {len(table)}")
        print("\nCampos encontrados:")
        
        fields_info = []
        for field in table.fields:
            field_info = {
                'name': field.name.strip(),
                'type': field.type,
                'length': field.length,
                'decimal': field.decimal_count if hasattr(field, 'decimal_count') else 0
            }
            fields_info.append(field_info)
            print(f"- {field.name}: {field.type} (Length: {field.length}, Decimal: {field_info['decimal']})")
        
        # Mostrar el primer registro como ejemplo
        if len(table) > 0:
            print("\nPrimer registro de ejemplo:")
            record = next(iter(table))
            for field in fields_info:
                value = record.get(field['name'], 'N/A')
                print(f"{field['name']}: {value} ({type(value).__name__})")
                field['example_value'] = str(value) if value is not None else 'NULL'
        
        return fields_info
        
    except Exception as e:
        print(f"Error al analizar {filepath}: {str(e)}")
        return []

if __name__ == "__main__":
    dbf_dir = "/Users/joseserrano/projects/python/prestamo/dbfs"
    dbf_files = [f for f in os.listdir(dbf_dir) if f.endswith('.dbf')]
    
    all_fields = {}
    
    # Primero buscamos el archivo de clientes
    client_file = next((f for f in dbf_files if 'cte' in f.lower() or 'clie' in f.lower()), None)
    
    if not client_file:
        print("No se encontró un archivo de clientes. Analizando todos los archivos...")
        client_file = dbf_files[0]  # Tomamos el primer archivo si no encontramos uno de clientes
    
    filepath = os.path.join(dbf_dir, client_file)
    print("\n" + "="*80)
    print(f"ANALIZANDO ARCHIVO: {client_file}")
    print("="*80)
    
    fields = analyze_dbf(filepath)
    all_fields[client_file] = fields
    
    # Guardar resumen detallado
    output_file = "clientes_fields_analysis.txt"
    with open(output_file, "w", encoding='utf-8') as f:
        f.write("ANÁLISIS DE CAMPOS DE CLIENTES\n")
        f.write("="*80 + "\n\n")
        
        for file, fields in all_fields.items():
            f.write(f"ARCHIVO: {file}\n")
            f.write("-"*80 + "\n")
            for field in fields:
                f.write(f"Campo: {field['name']}\n")
                f.write(f"Tipo: {field['type']}\n")
                f.write(f"Longitud: {field['length']}\n")
                if field['decimal'] > 0:
                    f.write(f"Decimales: {field['decimal']}\n")
                if 'example_value' in field:
                    f.write(f"Ejemplo: {field['example_value']}\n")
                f.write("\n")
    
    print(f"\nAnálisis completado. Los resultados se han guardado en '{output_file}'")
    
    # Mostrar sugerencias de campos relevantes basados en el análisis
    print("\nSUGERENCIAS DE CAMPOS PARA EL MAESTRO DE CLIENTES:")
    print("-"*80)
    
    # Mapeo de tipos DBF a tipos de datos sugeridos
    type_mapping = {
        'C': 'str',
        'N': 'float' if any(f.get('decimal', 0) > 0 for f in fields) else 'int',
        'D': 'date',
        'L': 'bool',
        'M': 'str',
        'F': 'float',
        'I': 'int',
        'T': 'datetime',
        'Y': 'decimal'
    }
    
    # Campos sugeridos basados en el análisis
    suggested_fields = []
    for field in fields:
        field_name = field['name'].strip().upper()
        field_type = type_mapping.get(field['type'], 'str')
        
        # Mapear nombres de campos comunes
        if any(name in field_name for name in ['COD', 'ID', 'CLAVE']):
            suggested_fields.append(("ID_CLIENTE", field_type, field['length']))
        elif any(name in field_name for name in ['NOMBRE']):
            suggested_fields.append(("NOMBRE", field_type, field['length']))
        elif any(name in field_name for name in ['APELLIDO', 'APEL']):
            suggested_fields.append(("APELLIDO", field_type, field['length']))
        elif any(name in field_name for name in ['DIRECCION', 'DIREC']):
            suggested_fields.append(("DIRECCION", field_type, field['length']))
        elif any(name in field_name for name in ['CIUDAD']):
            suggested_fields.append(("CIUDAD", field_type, field['length']))
        elif any(name in field_name for name in ['TELEFONO', 'TEL', 'CEL']):
            suggested_fields.append(("TELEFONO", field_type, field['length']))
        elif any(name in field_name for name in ['IDENTIF', 'CEDULA', 'RUC', 'DNI']):
            suggested_fields.append(("IDENTIFICACION", field_type, field['length']))
    
    # Si no encontramos campos por nombre, mostramos los primeros 10
    if not suggested_fields:
        print("No se pudieron identificar campos comunes. Mostrando los primeros 10 campos:")
        for field in fields[:10]:
            field_type = type_mapping.get(field['type'], 'str')
            print(f"- {field['name']}: {field_type} (Length: {field['length']})")
    else:
        # Mostrar campos sugeridos únicos
        seen = set()
        for name, ftype, length in suggested_fields:
            if name not in seen:
                print(f"- {name}: {ftype} (Max length: {length})")
                seen.add(name)
    
    print("\nNota: Estos son campos sugeridos basados en el análisis del archivo. "
          "Ajusta según las necesidades específicas de tu aplicación.")

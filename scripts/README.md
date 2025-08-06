# 🔧 Scripts de Configuración FinancePro

Este directorio contiene scripts útiles para la configuración y gestión del sistema FinancePro.

## 📁 Scripts Disponibles

### `quick_env.py` - Generador Rápido de .env
Script simple para generar un archivo `.env` con configuración mínima pero segura.

```bash
# Uso básico
python scripts/quick_env.py

# Desde el directorio raíz con make
make quick-env
```

**Características:**
- ✅ Genera claves criptográficamente seguras
- ✅ Configuración mínima pero completa
- ✅ Crea backup automático si ya existe .env
- ✅ Validación interactiva antes de sobrescribir

**Cuándo usar:**
- Primera configuración del proyecto
- Desarrollo local rápido
- Cuando necesitas un .env básico funcionando

---

## 🔐 Scripts del Backend

### `backend/generate_secrets.py` - Generador Completo
Script avanzado con múltiples opciones para gestión completa de configuración.

```bash
# Generar .env completo
python backend/generate_secrets.py

# Solo mostrar claves sin crear archivo
python backend/generate_secrets.py --only-secrets

# Validar .env existente
python backend/generate_secrets.py --validate

# Crear backup del .env
python backend/generate_secrets.py --backup

# Sobrescribir sin backup
python backend/generate_secrets.py --force

# Ver ayuda completa
python backend/generate_secrets.py --help
```

**Características:**
- ✅ Configuración completa con documentación
- ✅ Múltiples opciones de línea de comandos
- ✅ Validación avanzada de configuración
- ✅ Gestión de backups automática
- ✅ Detección de problemas de seguridad

### `backend/validate_config.py` - Validador de Configuración
Script para validar la configuración actual del sistema.

```bash
# Validar configuración
python backend/validate_config.py

# Desde el directorio raíz con make
make validate-config
```

**Características:**
- ✅ Validación completa de variables de entorno
- ✅ Verificación de seguridad
- ✅ Detección de valores por defecto inseguros
- ✅ Reporte detallado de problemas

---

## 🚀 Comandos Make Disponibles

### Generación de Configuración
```bash
make generate-secrets    # Generar .env completo (avanzado)
make quick-env           # Generar .env rápido (básico)
make generate-keys       # Solo mostrar claves
```

### Validación y Verificación
```bash
make validate-config     # Validar configuración actual
make check-env          # Verificar que .env existe
make show-config        # Mostrar configuración (sin secretos)
make security-check     # Verificación completa de seguridad
```

### Gestión de Archivos
```bash
make backup-env         # Crear backup del .env
make config-help        # Mostrar ayuda completa
```

---

## 📋 Flujo de Trabajo Recomendado

### 1. Primera Configuración
```bash
# Opción A: Configuración rápida
make quick-env

# Opción B: Configuración completa
make generate-secrets
```

### 2. Validación
```bash
# Validar que todo esté correcto
make validate-config

# Verificar seguridad
make security-check
```

### 3. Desarrollo
```bash
# Iniciar servicios
make up-dev

# Ver logs si hay problemas
make logs-backend
```

### 4. Mantenimiento
```bash
# Crear backup antes de cambios
make backup-env

# Regenerar claves si es necesario
make generate-secrets --force

# Validar después de cambios
make validate-config
```

---

## 🔒 Consideraciones de Seguridad

### ✅ Buenas Prácticas
- **Usar scripts oficiales**: Siempre usa los scripts proporcionados
- **Validar regularmente**: Ejecuta `make security-check` periódicamente
- **Crear backups**: Usa `make backup-env` antes de cambios importantes
- **Claves únicas**: Regenera claves para cada entorno

### ❌ Evitar
- **No editar manualmente**: Evita editar .env a mano si es posible
- **No compartir claves**: Nunca compartas archivos .env
- **No usar valores por defecto**: Los scripts detectan y previenen esto
- **No ignorar advertencias**: Atiende las advertencias de seguridad

---

## 🐛 Solución de Problemas

### Error: "No se puede importar pydantic"
```bash
# Asegúrate de estar en el entorno correcto
# Los scripts usan solo librerías estándar de Python
python --version  # Debe ser Python 3.7+
```

### Error: "Archivo .env no encontrado"
```bash
# Generar nuevo archivo
make quick-env
# O
make generate-secrets
```

### Error: "Variables de entorno faltantes"
```bash
# Validar qué falta
make validate-config

# Regenerar archivo completo
make generate-secrets
```

### Error: "Claves inseguras detectadas"
```bash
# Regenerar con claves seguras
make generate-secrets --force

# Validar resultado
make security-check
```

---

## 📚 Referencias

- [Documentación completa de configuración](../CONFIGURATION.md)
- [Guía de seguridad](../SECURITY.md)
- [README principal](../README.md)

---

## 🤝 Contribuir

Si necesitas agregar nuevos scripts de configuración:

1. **Ubicación**: Coloca scripts generales en `scripts/`, específicos del backend en `backend/`
2. **Naming**: Usa nombres descriptivos con guiones bajos
3. **Documentación**: Agrega docstrings y comentarios
4. **Makefile**: Agrega comandos make correspondientes
5. **Testing**: Prueba en entorno limpio antes de commit

### Plantilla para Nuevos Scripts
```python
#!/usr/bin/env python3
"""
Descripción del script

Uso:
    python scripts/mi_script.py [opciones]
"""

import argparse
from pathlib import Path


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Descripción")
    # Agregar argumentos
    args = parser.parse_args()
    
    try:
        # Lógica del script
        print("✅ Operación completada")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
```

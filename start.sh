#!/bin/bash

# Script de inicio rápido para FinancePro
echo "🏦 Iniciando FinancePro - Sistema de Préstamos"
echo "=============================================="

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor instala Docker primero."
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor instala Docker Compose primero."
    exit 1
fi

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo de configuración .env..."
    cp .env.example .env
    echo "✅ Archivo .env creado. Puedes editarlo para personalizar la configuración."
fi

# Preguntar el modo de ejecución
echo ""
echo "Selecciona el modo de ejecución:"
echo "1) Desarrollo (con hot reload)"
echo "2) Producción"
read -p "Ingresa tu opción (1 o 2): " mode

case $mode in
    1)
        echo "🚀 Iniciando en modo DESARROLLO..."
        docker compose -f docker-compose.dev.yml down -v 2>/dev/null
        docker compose -f docker-compose.dev.yml build
        docker compose -f docker-compose.dev.yml up -d
        
        echo ""
        echo "✅ FinancePro iniciado en modo desarrollo!"
        echo "📱 Frontend: http://localhost:3000"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📚 Documentación: http://localhost:8000/docs"
        echo "🗄️  Base de datos: localhost:5432"
        echo ""
        echo "Credenciales de prueba:"
        echo "Email: admin@financepro.com"
        echo "Contraseña: admin123"
        echo ""
        echo "Para ver los logs: docker compose -f docker-compose.dev.yml logs -f"
        echo "Para detener: docker compose -f docker-compose.dev.yml down"
        ;;
    2)
        echo "🚀 Iniciando en modo PRODUCCIÓN..."
        docker compose down -v 2>/dev/null
        docker compose build
        docker compose up -d
        
        echo ""
        echo "✅ FinancePro iniciado en modo producción!"
        echo "🌐 Aplicación: http://localhost"
        echo "🔧 Backend API: http://localhost/api/v1"
        echo "📚 Documentación: http://localhost/docs"
        echo ""
        echo "Para ver los logs: docker compose logs -f"
        echo "Para detener: docker compose down"
        ;;
    *)
        echo "❌ Opción inválida. Saliendo..."
        exit 1
        ;;
esac

echo ""
echo "🎉 ¡FinancePro está listo para usar!"

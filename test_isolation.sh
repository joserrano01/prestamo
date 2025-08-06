#!/bin/bash

echo "🧪 Test de aislamiento para identificar el origen de los refreshes"
echo "=================================================================="

echo "1. Monitoreando logs durante 15 segundos SIN navegador abierto..."
echo "   (Por favor, cierra TODOS los navegadores durante esta prueba)"
echo ""
read -p "Presiona ENTER cuando hayas cerrado todos los navegadores..."

echo "Iniciando monitoreo..."
timeout 15s docker compose -f docker-compose.dev.yml logs -f nginx 2>/dev/null | grep "GET /" | while read line; do
    if [[ $line == *"token"* ]]; then
        echo "🚨 ENCONTRADO TOKEN: $line"
    elif [[ $line == *"GET / HTTP"* ]]; then
        echo "📄 GET /: $line"
    fi
done

echo ""
echo "2. Ahora abre SOLO Firefox y navega a http://localhost"
echo "   Deja la pestaña abierta sin hacer nada..."
echo ""
read -p "Presiona ENTER cuando tengas Firefox abierto en localhost..."

echo "Monitoreando con Firefox..."
timeout 10s docker compose -f docker-compose.dev.yml logs -f nginx 2>/dev/null | grep -E "(GET /|token)" | while read line; do
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $line"
done

echo ""
echo "3. Ahora abre Chrome (ADICIONALMENTE a Firefox)"
echo "   Navega también a http://localhost..."
echo ""
read -p "Presiona ENTER cuando tengas ambos navegadores abiertos..."

echo "Monitoreando con ambos navegadores..."
timeout 10s docker compose -f docker-compose.dev.yml logs -f nginx 2>/dev/null | grep -E "(GET /|token)" | while read line; do
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $line"
done

echo ""
echo "🔍 Análisis completado. Esto nos ayudará a identificar:"
echo "- Si el problema ocurre sin navegadores (proceso del sistema)"
echo "- Si es específico de un navegador"
echo "- Qué navegador genera el token misterioso"
#!/bin/bash

# 📊 Dashboard de Seguridad en Tiempo Real - FinancePro
# Monitorea el estado de seguridad del sistema continuamente

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Función para limpiar pantalla
clear_screen() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🛡️  DASHBOARD DE SEGURIDAD - FinancePro                    ║${NC}"
    echo -e "${BLUE}║                           $(date '+%Y-%m-%d %H:%M:%S')                            ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Función para mostrar estado de servicios
show_services_status() {
    echo -e "${CYAN}📦 ESTADO DE SERVICIOS DOCKER${NC}"
    echo -e "════════════════════════════════════════"
    
    if command -v docker &> /dev/null; then
        # Verificar si hay servicios ejecutándose
        if docker compose -f docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep -q "Up"; then
            docker compose -f docker-compose.dev.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | while read line; do
                if echo "$line" | grep -q "Up.*healthy"; then
                    echo -e "${GREEN}✅ $line${NC}"
                elif echo "$line" | grep -q "Up.*unhealthy"; then
                    echo -e "${YELLOW}⚠️  $line${NC}"
                elif echo "$line" | grep -q "Up"; then
                    echo -e "${BLUE}🔄 $line${NC}"
                else
                    echo -e "${RED}❌ $line${NC}"
                fi
            done
        else
            echo -e "${YELLOW}⚠️  No hay servicios ejecutándose${NC}"
        fi
    else
        echo -e "${RED}❌ Docker no está disponible${NC}"
    fi
    echo ""
}

# Función para mostrar estado de redes
show_network_status() {
    echo -e "${CYAN}🌐 ESTADO DE REDES DOCKER${NC}"
    echo -e "════════════════════════════════════════"
    
    if command -v docker &> /dev/null; then
        # Verificar redes de FinancePro
        if docker network ls | grep -q "financepro"; then
            docker network ls | grep "financepro" | while read line; do
                network_name=$(echo "$line" | awk '{print $2}')
                if echo "$network_name" | grep -q "internal"; then
                    echo -e "${GREEN}🔒 $line (Red Interna Segura)${NC}"
                elif echo "$network_name" | grep -q "external"; then
                    echo -e "${BLUE}🌍 $line (Red Externa)${NC}"
                else
                    echo -e "${YELLOW}🔗 $line${NC}"
                fi
            done
        else
            echo -e "${YELLOW}⚠️  No se encontraron redes de FinancePro${NC}"
        fi
    else
        echo -e "${RED}❌ Docker no está disponible${NC}"
    fi
    echo ""
}

# Función para mostrar puertos expuestos
show_exposed_ports() {
    echo -e "${CYAN}🔌 PUERTOS EXPUESTOS${NC}"
    echo -e "════════════════════════════════════════"
    
    if command -v lsof &> /dev/null; then
        echo -e "${BLUE}Puertos activos en el sistema:${NC}"
        lsof -i -P | grep LISTEN | grep -E ":(80|443|5432|6379|5672|15672|7700|8000|3000|3001)" | while read line; do
            port=$(echo "$line" | awk '{print $9}' | cut -d':' -f2)
            case $port in
                80|443)
                    echo -e "${GREEN}✅ Puerto $port - HTTP/HTTPS (Seguro)${NC}"
                    ;;
                5432|6379|5672|7700|8000|3000)
                    echo -e "${YELLOW}⚠️  Puerto $port - Servicio interno expuesto${NC}"
                    ;;
                15672)
                    echo -e "${BLUE}🔧 Puerto $port - RabbitMQ Management (Desarrollo)${NC}"
                    ;;
                *)
                    echo -e "${RED}❓ Puerto $port - Desconocido${NC}"
                    ;;
            esac
        done
    else
        echo -e "${YELLOW}⚠️  lsof no está disponible${NC}"
    fi
    echo ""
}

# Función para mostrar métricas de seguridad
show_security_metrics() {
    echo -e "${CYAN}📊 MÉTRICAS DE SEGURIDAD${NC}"
    echo -e "════════════════════════════════════════"
    
    # Verificar archivos de configuración críticos
    local config_score=0
    local total_configs=5
    
    [ -f ".env.production" ] && config_score=$((config_score + 1))
    [ -f "docker-compose.prod.yml" ] && config_score=$((config_score + 1))
    [ -f "nginx/nginx.prod.conf" ] && config_score=$((config_score + 1))
    [ -f "ssl/cert.pem" ] && config_score=$((config_score + 1))
    [ -f "ssl/key.pem" ] && config_score=$((config_score + 1))
    
    local config_percentage=$((config_score * 100 / total_configs))
    
    echo -e "Configuración de Seguridad: ${config_score}/${total_configs} (${config_percentage}%)"
    if [ $config_percentage -ge 90 ]; then
        echo -e "${GREEN}🛡️  Estado: EXCELENTE${NC}"
    elif [ $config_percentage -ge 70 ]; then
        echo -e "${YELLOW}⚠️  Estado: BUENO${NC}"
    else
        echo -e "${RED}🚨 Estado: CRÍTICO${NC}"
    fi
    
    # Verificar claves de seguridad
    if [ -f ".env.production" ]; then
        if grep -q "your-super-secret-key" .env.production 2>/dev/null; then
            echo -e "${RED}❌ Claves por defecto detectadas${NC}"
        else
            echo -e "${GREEN}✅ Claves de seguridad únicas${NC}"
        fi
    fi
    
    # Verificar certificados SSL
    if [ -f "ssl/cert.pem" ] && [ -f "ssl/key.pem" ]; then
        local cert_days=$(openssl x509 -in ssl/cert.pem -noout -dates 2>/dev/null | grep "notAfter" | cut -d= -f2)
        if [ -n "$cert_days" ]; then
            echo -e "${GREEN}✅ Certificados SSL válidos${NC}"
        else
            echo -e "${YELLOW}⚠️  Certificados SSL presentes pero no verificables${NC}"
        fi
    else
        echo -e "${RED}❌ Certificados SSL faltantes${NC}"
    fi
    
    echo ""
}

# Función para mostrar logs recientes
show_recent_logs() {
    echo -e "${CYAN}📝 LOGS RECIENTES DE SEGURIDAD${NC}"
    echo -e "════════════════════════════════════════"
    
    # Buscar logs de validación recientes
    local latest_log=$(ls -t security_validation_*.log 2>/dev/null | head -1)
    if [ -n "$latest_log" ]; then
        echo -e "${GREEN}📄 Último reporte: $latest_log${NC}"
        echo -e "${BLUE}Contenido:${NC}"
        head -10 "$latest_log" | sed 's/^/  /'
    else
        echo -e "${YELLOW}⚠️  No se encontraron logs de validación recientes${NC}"
    fi
    
    # Mostrar logs de Docker si están disponibles
    if command -v docker &> /dev/null; then
        echo -e "\n${BLUE}🐳 Logs recientes de nginx:${NC}"
        docker compose -f docker-compose.dev.yml logs --tail=5 nginx 2>/dev/null | sed 's/^/  /' || echo -e "${YELLOW}  No hay logs disponibles${NC}"
    fi
    
    echo ""
}

# Función para mostrar alertas de seguridad
show_security_alerts() {
    echo -e "${CYAN}🚨 ALERTAS DE SEGURIDAD${NC}"
    echo -e "════════════════════════════════════════"
    
    local alerts=0
    
    # Verificar puertos críticos expuestos
    if lsof -i -P 2>/dev/null | grep LISTEN | grep -E ":(5432|6379|5672)" >/dev/null; then
        echo -e "${RED}🚨 ALERTA: Puertos de base de datos expuestos${NC}"
        alerts=$((alerts + 1))
    fi
    
    # Verificar claves por defecto
    if [ -f ".env" ] && grep -q "your-super-secret-key" .env 2>/dev/null; then
        echo -e "${RED}🚨 ALERTA: Claves por defecto en .env${NC}"
        alerts=$((alerts + 1))
    fi
    
    # Verificar certificados próximos a vencer
    if [ -f "ssl/cert.pem" ]; then
        if openssl x509 -in ssl/cert.pem -checkend 604800 -noout 2>/dev/null; then
            : # Certificado válido por más de 7 días
        else
            echo -e "${YELLOW}⚠️  ALERTA: Certificado SSL vence pronto${NC}"
            alerts=$((alerts + 1))
        fi
    fi
    
    if [ $alerts -eq 0 ]; then
        echo -e "${GREEN}✅ No hay alertas de seguridad activas${NC}"
    else
        echo -e "${RED}Total de alertas: $alerts${NC}"
    fi
    
    echo ""
}

# Función para mostrar comandos útiles
show_useful_commands() {
    echo -e "${CYAN}🛠️  COMANDOS ÚTILES${NC}"
    echo -e "════════════════════════════════════════"
    echo -e "${BLUE}Validar seguridad:${NC} ./scripts/validate_security.sh"
    echo -e "${BLUE}Generar SSL:${NC} ./scripts/generate_ssl.sh"
    echo -e "${BLUE}Producción:${NC} docker compose -f docker-compose.prod.yml up -d"
    echo -e "${BLUE}Desarrollo:${NC} docker compose -f docker-compose.dev.yml up -d"
    echo -e "${BLUE}Ver logs:${NC} docker compose logs -f nginx"
    echo -e "${BLUE}Estado servicios:${NC} docker compose ps"
    echo ""
}

# Función principal del dashboard
main_dashboard() {
    while true; do
        clear_screen
        show_services_status
        show_network_status
        show_exposed_ports
        show_security_metrics
        show_recent_logs
        show_security_alerts
        show_useful_commands
        
        echo -e "${PURPLE}Presiona Ctrl+C para salir o espera 30 segundos para actualizar...${NC}"
        
        # Esperar 30 segundos o hasta que se presione Ctrl+C
        for i in {30..1}; do
            echo -ne "\rActualizando en $i segundos... "
            sleep 1
        done
        echo ""
    done
}

# Función para mostrar dashboard una sola vez
single_dashboard() {
    clear_screen
    show_services_status
    show_network_status
    show_exposed_ports
    show_security_metrics
    show_recent_logs
    show_security_alerts
    show_useful_commands
}

# Verificar argumentos
if [ "$1" = "--once" ] || [ "$1" = "-o" ]; then
    single_dashboard
else
    echo -e "${BLUE}🛡️  Iniciando Dashboard de Seguridad de FinancePro${NC}"
    echo -e "${YELLOW}Usa --once para mostrar una sola vez, o Ctrl+C para salir del modo continuo${NC}"
    echo ""
    sleep 2
    main_dashboard
fi

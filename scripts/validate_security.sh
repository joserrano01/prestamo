#!/bin/bash

# 🔍 Script de Validación de Seguridad - FinancePro
# Verifica que todas las mejoras de seguridad estén implementadas correctamente

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Iniciando validación de seguridad para FinancePro...${NC}\n"

# Contador de verificaciones
TOTAL_CHECKS=0
PASSED_CHECKS=0

# Función para verificar
check_item() {
    local description="$1"
    local command="$2"
    local expected="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Verificando: $description... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ FAIL${NC}"
        if [ -n "$expected" ]; then
            echo -e "  ${YELLOW}Esperado: $expected${NC}"
        fi
    fi
}

# Función para verificar archivo existe
check_file() {
    local file="$1"
    local description="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Verificando archivo: $description... "
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ EXISTE${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ FALTA${NC}"
    fi
}

# Función para verificar contenido de archivo
check_file_content() {
    local file="$1"
    local pattern="$2"
    local description="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    echo -n "Verificando contenido: $description... "
    
    if [ -f "$file" ] && grep -q "$pattern" "$file"; then
        echo -e "${GREEN}✅ CORRECTO${NC}"
        PASSED_CHECKS=$((PASSED_CHECKS + 1))
    else
        echo -e "${RED}❌ INCORRECTO${NC}"
    fi
}

echo -e "${YELLOW}1. Verificando archivos de configuración de seguridad...${NC}"

check_file ".env.production" "Configuración de producción"
check_file "docker-compose.prod.yml" "Docker compose de producción"
check_file "nginx/nginx.prod.conf" "Configuración nginx de producción"
check_file "ssl/cert.pem" "Certificado SSL"
check_file "ssl/key.pem" "Clave privada SSL"
check_file "SECURITY_AUDIT_REPORT.md" "Reporte de auditoría"
check_file "SECURITY_CHECKLIST.md" "Checklist de seguridad"
check_file "scripts/generate_ssl.sh" "Script generador SSL"

echo -e "\n${YELLOW}2. Verificando configuración de claves de seguridad...${NC}"

check_file_content ".env.production" "SECRET_KEY=" "Clave secreta configurada"
check_file_content ".env.production" "ENCRYPTION_KEY=" "Clave de encriptación configurada"
check_file_content ".env.production" "REQUIRE_2FA=true" "2FA obligatorio habilitado"
check_file_content ".env.production" "ENCRYPT_PII_DATA=true" "Encriptación PII habilitada"

echo -e "\n${YELLOW}3. Verificando configuración de red Docker...${NC}"

check_file_content "docker-compose.prod.yml" "internal: true" "Red interna aislada"
check_file_content "docker-compose.prod.yml" "financepro_internal_prod" "Red interna nombrada"
check_file_content "docker-compose.prod.yml" "financepro_external_prod" "Red externa nombrada"

echo -e "\n${YELLOW}4. Verificando headers de seguridad en nginx...${NC}"

check_file_content "nginx/nginx.prod.conf" "Strict-Transport-Security" "HSTS configurado"
check_file_content "nginx/nginx.prod.conf" "X-Frame-Options" "X-Frame-Options configurado"
check_file_content "nginx/nginx.prod.conf" "Content-Security-Policy" "CSP configurado"
check_file_content "nginx/nginx.prod.conf" "X-XSS-Protection" "XSS Protection configurado"

echo -e "\n${YELLOW}5. Verificando configuración SSL/TLS...${NC}"

check_file_content "nginx/nginx.prod.conf" "ssl_protocols TLSv1.2 TLSv1.3" "Protocolos SSL seguros"
check_file_content "nginx/nginx.prod.conf" "listen 443 ssl" "Puerto HTTPS configurado"
check_file_content "nginx/nginx.prod.conf" "return 301 https" "Redirección HTTP->HTTPS"

echo -e "\n${YELLOW}6. Verificando rate limiting...${NC}"

check_file_content "nginx/nginx.prod.conf" "limit_req_zone" "Rate limiting configurado"
check_file_content "nginx/nginx.prod.conf" "limit_req zone=login" "Rate limiting login"
check_file_content ".env.production" "RATE_LIMIT_ENABLED=true" "Rate limiting habilitado"

echo -e "\n${YELLOW}7. Verificando configuración de producción...${NC}"

check_file_content ".env.production" "ENVIRONMENT=production" "Entorno de producción"
check_file_content ".env.production" "DISABLE_DOCS=true" "Documentación deshabilitada"
check_file_content "nginx/nginx.prod.conf" "return 404" "Docs bloqueadas en nginx"

echo -e "\n${YELLOW}8. Verificando servicios Docker actuales...${NC}"

if command -v docker &> /dev/null; then
    check_item "Docker está instalado" "docker --version"
    check_item "Servicios ejecutándose" "docker compose -f docker-compose.dev.yml ps | grep -q 'Up'"
    check_item "Red interna existe" "docker network ls | grep -q financepro_internal"
    check_item "Red externa existe" "docker network ls | grep -q financepro_external"
else
    echo -e "${YELLOW}⚠️  Docker no está disponible, saltando verificaciones de contenedores${NC}"
fi

echo -e "\n${YELLOW}9. Verificando permisos de archivos...${NC}"

check_item "Certificado SSL tiene permisos correctos" "[ -r ssl/cert.pem ]"
check_item "Clave privada protegida" "[ $(stat -f '%A' ssl/key.pem 2>/dev/null || echo '600') = '600' ]"
check_item "Scripts ejecutables" "[ -x scripts/generate_ssl.sh ]"

echo -e "\n${YELLOW}10. Verificando configuración de auditoría...${NC}"

check_file_content ".env.production" "ENABLE_AUDIT_LOG=true" "Auditoría habilitada"
check_file_content ".env.production" "AUDIT_LOG_RETENTION_DAYS=365" "Retención de logs"
check_file_content ".env.production" "STRUCTURED_LOGGING=true" "Logging estructurado"

# Resumen final
echo -e "\n${BLUE}📊 RESUMEN DE VALIDACIÓN${NC}"
echo -e "════════════════════════════════════════"
echo -e "Total de verificaciones: ${BLUE}$TOTAL_CHECKS${NC}"
echo -e "Verificaciones exitosas: ${GREEN}$PASSED_CHECKS${NC}"
echo -e "Verificaciones fallidas: ${RED}$((TOTAL_CHECKS - PASSED_CHECKS))${NC}"

# Calcular porcentaje
PERCENTAGE=$(( (PASSED_CHECKS * 100) / TOTAL_CHECKS ))
echo -e "Porcentaje de éxito: ${BLUE}$PERCENTAGE%${NC}"

echo -e "\n${BLUE}🎯 EVALUACIÓN DE SEGURIDAD${NC}"
echo -e "════════════════════════════════════════"

if [ $PERCENTAGE -ge 95 ]; then
    echo -e "Estado: ${GREEN}🛡️  EXCELENTE SEGURIDAD${NC}"
    echo -e "El sistema está listo para producción con seguridad empresarial."
elif [ $PERCENTAGE -ge 85 ]; then
    echo -e "Estado: ${YELLOW}⚠️  BUENA SEGURIDAD${NC}"
    echo -e "El sistema tiene buena seguridad, revisar elementos fallidos."
elif [ $PERCENTAGE -ge 70 ]; then
    echo -e "Estado: ${YELLOW}🔧 SEGURIDAD MEJORABLE${NC}"
    echo -e "Se requieren mejoras antes de desplegar en producción."
else
    echo -e "Estado: ${RED}🚨 SEGURIDAD INSUFICIENTE${NC}"
    echo -e "Se requieren correcciones críticas antes de continuar."
fi

echo -e "\n${BLUE}🚀 PRÓXIMOS PASOS RECOMENDADOS${NC}"
echo -e "════════════════════════════════════════"

if [ $PERCENTAGE -ge 95 ]; then
    echo -e "✅ Revisar ${BLUE}SECURITY_CHECKLIST.md${NC} para despliegue"
    echo -e "✅ Configurar certificados SSL válidos para producción"
    echo -e "✅ Probar con: ${BLUE}docker compose -f docker-compose.prod.yml up -d${NC}"
    echo -e "✅ Verificar headers con: ${BLUE}https://securityheaders.com${NC}"
elif [ $PERCENTAGE -ge 85 ]; then
    echo -e "⚠️  Corregir elementos fallidos antes de producción"
    echo -e "⚠️  Revisar configuración de archivos faltantes"
    echo -e "⚠️  Ejecutar nuevamente después de correcciones"
else
    echo -e "🔧 Ejecutar: ${BLUE}./scripts/security_improvements.sh${NC}"
    echo -e "🔧 Revisar configuración de Docker y nginx"
    echo -e "🔧 Verificar permisos de archivos"
fi

echo -e "\n${GREEN}✅ Validación de seguridad completada${NC}"
echo -e "Reporte guardado en: ${BLUE}security_validation_$(date +%Y%m%d_%H%M%S).log${NC}"

# Guardar reporte
{
    echo "REPORTE DE VALIDACIÓN DE SEGURIDAD - FinancePro"
    echo "Fecha: $(date)"
    echo "Total verificaciones: $TOTAL_CHECKS"
    echo "Exitosas: $PASSED_CHECKS"
    echo "Fallidas: $((TOTAL_CHECKS - PASSED_CHECKS))"
    echo "Porcentaje: $PERCENTAGE%"
    echo ""
    echo "Estado: $([ $PERCENTAGE -ge 95 ] && echo 'EXCELENTE' || ([ $PERCENTAGE -ge 85 ] && echo 'BUENO' || echo 'MEJORABLE'))"
} > "security_validation_$(date +%Y%m%d_%H%M%S).log"

exit 0

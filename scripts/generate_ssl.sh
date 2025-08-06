#!/bin/bash

# Script para generar certificados SSL autofirmados (desarrollo)
# Para producción, usar Let's Encrypt o certificados comerciales

echo "🔐 Generando certificados SSL..."

mkdir -p ssl

# Generar clave privada
openssl genrsa -out ssl/key.pem 2048

# Generar certificado autofirmado
openssl req -new -x509 -key ssl/key.pem -out ssl/cert.pem -days 365 -subj "/C=PA/ST=Chiriqui/L=David/O=FinancePro/OU=IT/CN=localhost"

echo "✅ Certificados SSL generados en ./ssl/"
echo "⚠️  IMPORTANTE: Para producción, usar certificados válidos de Let's Encrypt o CA comercial"

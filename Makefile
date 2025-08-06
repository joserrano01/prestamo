# Makefile para el proyecto FinancePro

.PHONY: help build up down logs clean dev prod test

# Variables
COMPOSE_FILE = docker-compose.yml
COMPOSE_DEV_FILE = docker-compose.dev.yml

help: ## Mostrar esta ayuda
	@echo "Comandos disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Construir todas las imágenes
	docker compose -f $(COMPOSE_FILE) build

build-dev: ## Construir imágenes para desarrollo
	docker compose -f $(COMPOSE_DEV_FILE) build

up: ## Levantar servicios en producción
	docker compose -f $(COMPOSE_FILE) up -d

up-dev: ## Levantar servicios en desarrollo
	docker compose -f $(COMPOSE_DEV_FILE) up -d

down: ## Detener todos los servicios
	docker compose -f $(COMPOSE_FILE) down
	docker compose -f $(COMPOSE_DEV_FILE) down

down-v: ## Detener servicios y eliminar volúmenes
	docker compose -f $(COMPOSE_FILE) down -v
	docker compose -f $(COMPOSE_DEV_FILE) down -v

logs: ## Ver logs de todos los servicios
	docker compose -f $(COMPOSE_FILE) logs -f

logs-dev: ## Ver logs en desarrollo
	docker compose -f $(COMPOSE_DEV_FILE) logs -f

logs-backend: ## Ver logs del backend
	docker compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend: ## Ver logs del frontend
	docker compose -f $(COMPOSE_FILE) logs -f frontend

logs-db: ## Ver logs de la base de datos
	docker compose -f $(COMPOSE_FILE) logs -f db

logs-redis: ## Ver logs de Redis
	docker compose -f $(COMPOSE_FILE) logs -f redis

logs-rabbitmq: ## Ver logs de RabbitMQ
	docker compose -f $(COMPOSE_FILE) logs -f rabbitmq

logs-meilisearch: ## Ver logs de Meilisearch
	docker compose -f $(COMPOSE_FILE) logs -f meilisearch

restart: ## Reiniciar todos los servicios
	docker compose -f $(COMPOSE_FILE) restart

restart-dev: ## Reiniciar servicios en desarrollo
	docker compose -f $(COMPOSE_DEV_FILE) restart

clean: ## Limpiar contenedores, imágenes y volúmenes no utilizados
	docker system prune -f
	docker volume prune -f

clean-all: ## Limpiar todo (¡CUIDADO! Elimina todos los datos)
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker compose -f $(COMPOSE_DEV_FILE) down -v --remove-orphans
	docker system prune -af
	docker volume prune -f

dev: build-dev up-dev ## Modo desarrollo completo

prod: build up ## Modo producción completo

status: ## Ver estado de los contenedores
	docker compose -f $(COMPOSE_FILE) ps

status-dev: ## Ver estado en desarrollo
	docker compose -f $(COMPOSE_DEV_FILE) ps

shell-backend: ## Acceder al shell del backend
	docker compose -f $(COMPOSE_FILE) exec backend /bin/bash

shell-frontend: ## Acceder al shell del frontend
	docker compose -f $(COMPOSE_FILE) exec frontend /bin/sh

shell-db: ## Acceder al shell de la base de datos
	docker compose -f $(COMPOSE_FILE) exec db psql -U postgres -d financepro

backup-db: ## Crear backup de la base de datos
	docker compose -f $(COMPOSE_FILE) exec db pg_dump -U postgres financepro > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restaurar base de datos (especificar archivo con FILE=backup.sql)
	docker compose -f $(COMPOSE_FILE) exec -T db psql -U postgres -d financepro < $(FILE)

install: ## Configuración inicial del proyecto
	@echo "Configurando proyecto FinancePro..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "Archivo .env creado. Por favor configúralo antes de continuar."; fi
	@echo "Ejecuta 'make dev' para iniciar en modo desarrollo"

test: ## Ejecutar tests del backend
	docker compose -f $(COMPOSE_FILE) exec backend python -m pytest

test-coverage: ## Ejecutar tests con cobertura
	docker compose -f $(COMPOSE_FILE) exec backend python -m pytest --cov=app --cov-report=html

migrate: ## Ejecutar migraciones de base de datos
	docker compose -f $(COMPOSE_FILE) exec backend alembic upgrade head

migrate-dev: ## Ejecutar migraciones en desarrollo
	docker compose -f $(COMPOSE_DEV_FILE) exec backend alembic upgrade head

# Comandos de servicios adicionales
rabbitmq-management:
	@echo "RabbitMQ Management: http://localhost:15672"
	@echo "Usuario: financepro"
	@echo "Contraseña: rabbitmq_password"

meilisearch-dashboard:
	@echo "Meilisearch Dashboard: http://localhost:7700"
	@echo "Master Key: meilisearch_master_key_change_in_production"

# Comandos de Celery
celery-worker:
	docker compose -f $(COMPOSE_FILE) exec backend celery -A app.services.celery_app worker --loglevel=info

celery-beat:
	docker compose -f $(COMPOSE_FILE) exec backend celery -A app.services.celery_app beat --loglevel=info

celery-flower:
	docker compose -f $(COMPOSE_FILE) exec backend celery -A app.services.celery_app flower

# Comandos de búsqueda
search-reindex:
	docker compose -f $(COMPOSE_FILE) exec backend python -c "import asyncio; from app.services.search_service import search_service; asyncio.run(search_service.initialize_indexes())"

search-stats:
	curl -X GET "http://localhost:8000/api/v1/search/stats" | jq

# Comandos de monitoreo
health-check:
	curl -X GET "http://localhost:8000/api/v1/monitoring/health" | jq

metrics:
	curl -X GET "http://localhost:8000/api/v1/monitoring/metrics" | jq

queue-stats:
	curl -X GET "http://localhost:8000/api/v1/monitoring/queues" | jq

# Comandos de configuración y seguridad
generate-secrets: ## Generar claves seguras y crear archivo .env completo
	python backend/generate_secrets.py

quick-env: ## Generar archivo .env rápido con configuración mínima
	python scripts/quick_env.py

generate-keys: ## Solo generar y mostrar claves sin crear archivo
	python backend/generate_secrets.py --only-secrets

validate-config: ## Validar configuración actual
	python backend/validate_config.py

check-env: ## Verificar que el archivo .env existe
	@if [ ! -f .env ]; then echo "❌ Archivo .env no encontrado. Ejecuta 'make generate-secrets'"; exit 1; else echo "✅ Archivo .env encontrado"; fi

show-config: ## Mostrar configuración actual (sin secretos)
	@echo "📋 Configuración actual:"
	@echo "PROJECT_NAME: $$(grep '^PROJECT_NAME=' .env 2>/dev/null | cut -d'=' -f2 || echo 'No configurado')"
	@echo "VERSION: $$(grep '^VERSION=' .env 2>/dev/null | cut -d'=' -f2 || echo 'No configurado')"
	@echo "SERVER_PORT: $$(grep '^SERVER_PORT=' .env 2>/dev/null | cut -d'=' -f2 || echo '8000')"
	@echo "REQUIRE_2FA: $$(grep '^REQUIRE_2FA=' .env 2>/dev/null | cut -d'=' -f2 || echo 'true')"
	@echo "ENCRYPT_PII_DATA: $$(grep '^ENCRYPT_PII_DATA=' .env 2>/dev/null | cut -d'=' -f2 || echo 'true')"
	@echo "LOG_LEVEL: $$(grep '^LOG_LEVEL=' .env 2>/dev/null | cut -d'=' -f2 || echo 'INFO')"

backup-env: ## Crear backup del archivo .env
	@if [ -f .env ]; then cp .env .env.backup.$$(date +%Y%m%d_%H%M%S); echo "✅ Backup creado: .env.backup.$$(date +%Y%m%d_%H%M%S)"; else echo "❌ No hay archivo .env para respaldar"; fi

security-check: ## Verificar configuración de seguridad
	@echo "🔐 Verificando configuración de seguridad..."
	@python backend/validate_config.py
	@echo "📋 Verificando permisos de archivos..."
	@ls -la .env* 2>/dev/null || echo "No hay archivos .env"

config-help: ## Mostrar ayuda sobre configuración
	@echo "🔧 Comandos de Configuración:"
	@echo "  make generate-secrets  - Generar .env completo con todas las opciones"
	@echo "  make quick-env         - Generar .env rápido con configuración mínima"
	@echo "  make generate-keys     - Solo mostrar claves sin crear archivo"
	@echo "  make validate-config   - Validar configuración actual"
	@echo "  make check-env         - Verificar archivo .env"
	@echo "  make show-config       - Mostrar configuración (sin secretos)"
	@echo "  make backup-env        - Crear backup del .env"
	@echo "  make security-check    - Verificar seguridad"
	@echo ""
	@echo "🔧 Opciones del generador avanzado:"
	@echo "  python backend/generate_secrets.py --help      - Ver todas las opciones"
	@echo "  python backend/generate_secrets.py --validate  - Solo validar .env"
	@echo "  python backend/generate_secrets.py --backup    - Solo crear backup"
	@echo "  python backend/generate_secrets.py --force     - Sobrescribir sin backup"
	@echo ""
	@echo "📁 Archivos importantes:"
	@echo "  .env                   - Configuración principal (no en git)"
	@echo "  .env.example           - Plantilla de configuración"
	@echo "  backend/.env.example   - Plantilla específica del backend"
	@echo "  scripts/quick_env.py   - Generador rápido"
	@echo "  backend/generate_secrets.py - Generador completo"
	@echo ""
	@echo "⚠️  IMPORTANTE:"
	@echo "  - Nunca compartas el archivo .env"
	@echo "  - Usa claves únicas en producción"
	@echo "  - Ejecuta 'make security-check' regularmente"

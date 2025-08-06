# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏗️ Project Architecture

FinancePro is a secure loan management system built with a microservices architecture:

- **Frontend**: React + TypeScript + Vite with Tailwind CSS and Radix UI components
- **Backend**: FastAPI + Python with comprehensive security middleware
- **Database**: PostgreSQL with security-focused models
- **Cache/Sessions**: Redis for caching and session management
- **Message Queue**: RabbitMQ for async processing with Celery workers
- **Search**: Meilisearch for full-text search capabilities
- **Infrastructure**: Docker Compose with separate dev/prod configurations

### Key Security Features
- Mandatory 2FA authentication
- PII data encryption at rest
- Comprehensive audit logging
- Rate limiting and DDoS protection
- Input sanitization middleware
- Security headers enforcement
- Session security monitoring

## 🚀 Development Commands

### Essential Commands (via Makefile)
```bash
# Start development environment
make dev                    # Full dev setup (build + up)
make up-dev                 # Start dev services only

# Production deployment
make prod                   # Full prod setup (build + up)
make up                     # Start prod services only

# Testing & Quality
make test                   # Run backend pytest suite
make test-coverage          # Run tests with coverage report

# Database operations
make migrate                # Run Alembic migrations (prod)
make migrate-dev            # Run Alembic migrations (dev)
make backup-db              # Create PostgreSQL backup
make shell-db              # Access PostgreSQL shell

# Monitoring & Debugging
make logs                   # View all service logs
make logs-backend          # Backend-specific logs
make logs-frontend         # Frontend-specific logs
make status                # Check container status
make health-check          # API health endpoint check

# Configuration & Security
make generate-secrets      # Generate secure .env file
make validate-config       # Validate security configuration
make security-check        # Run security validation
```

### Frontend Development
```bash
cd frontend
npm run dev                # Start Vite dev server
npm run build              # Production build
npm run lint               # ESLint check
npm run type-check         # TypeScript validation
```

### Backend Development
```bash
cd backend
python -m pytest          # Run tests
python -m pytest --cov=app --cov-report=html  # Coverage
black .                    # Code formatting
isort .                    # Import sorting
flake8 .                   # Linting
```

## 📁 Key Directory Structure

```
prestamo/
├── backend/app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── core/                 # Config, security, middleware
│   ├── models/               # SQLAlchemy models (secure_models.py, agenda_models.py)
│   ├── schemas/              # Pydantic schemas for validation
│   ├── services/             # Business logic (search, messaging, celery)
│   ├── tasks/                # Celery async tasks
│   └── utils/                # Shared utilities
├── frontend/src/
│   ├── components/           # Reusable React components
│   ├── pages/                # Route-level components
│   ├── types/                # TypeScript type definitions
│   └── lib/                  # Utilities and helpers
├── docker-compose.dev.yml    # Development services
├── docker-compose.yml        # Production services
└── Makefile                  # Automation commands
```

## 🔧 Configuration Management

### Environment Setup
1. **Auto-generate secure config**: `make generate-secrets`
2. **Quick minimal setup**: `python scripts/quick_env.py`
3. **Validate current config**: `make validate-config`

### Required Environment Variables
- `SECRET_KEY`: JWT signing key (minimum 32 chars)
- `ENCRYPTION_KEY`: PII encryption key (exactly 32 chars)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `RABBITMQ_URL`: RabbitMQ connection string
- `MEILISEARCH_URL` & `MEILISEARCH_MASTER_KEY`: Search service config

## 🏛️ Application Architecture Patterns

### Backend Structure
- **Layered Architecture**: API → Services → Models → Database
- **Dependency Injection**: FastAPI's dependency system for auth, db sessions
- **Middleware Chain**: Security headers → Audit → Sanitization → Rate limiting
- **Event-Driven**: RabbitMQ + Celery for async operations

### Security Implementation
- **Authentication Flow**: JWT with refresh tokens + mandatory 2FA
- **Data Protection**: AES encryption for PII data via `ENCRYPT_PII_DATA`
- **Audit Trail**: All operations logged with `AuditMiddleware`
- **Input Validation**: Pydantic schemas + sanitization middleware

### Frontend Patterns
- **Component Architecture**: Atomic design with Radix UI primitives
- **State Management**: React hooks with TypeScript strict mode
- **Routing**: React Router v6 with protected routes
- **Styling**: Tailwind CSS with consistent design tokens

## 🧪 Testing Strategy

### Backend Testing
- **Location**: `backend/tests/`
- **Framework**: pytest with async support
- **Coverage**: Aim for >80% coverage on business logic
- **Run**: `make test` or `docker-compose exec backend python -m pytest`

### Test Categories
- Unit tests for services and utilities
- Integration tests for API endpoints
- Security tests for auth and middleware
- Database migration tests

## 🔍 Search & Async Processing

### Meilisearch Integration
- **Service**: `app/services/search_service.py`
- **Indexes**: Auto-initialized on startup
- **Usage**: Full-text search across clients, loans, documents

### Celery Tasks
- **Worker**: Background processing for heavy operations
- **Beat**: Scheduled tasks (notifications, cleanup)
- **Monitoring**: Access via `make celery-flower`

## 🚦 Development Workflow

1. **Start Development**: `make dev`
2. **Check Health**: Visit `http://localhost/health`
3. **API Documentation**: `http://localhost/api/v1/docs`
4. **Frontend**: `http://localhost` (proxied through Nginx)
5. **Database Shell**: `make shell-db`

### Important Notes
- Always validate security config before deployment: `make security-check`
- Use provided Makefile commands instead of direct Docker commands
- Check logs regularly: `make logs-dev` for debugging
- Run migrations after model changes: `make migrate-dev`
- Never commit `.env` files - use `.env.example` as template

## 🔐 Security Considerations

- All PII data is encrypted using Fernet (AES 128)
- 2FA is mandatory - disable only for development
- Rate limiting is enforced on all endpoints
- Audit logs track all user actions and system events
- CORS is configured for development origins only
- Database migrations include security enhancements
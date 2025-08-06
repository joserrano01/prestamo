from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, sucursales
    # auth, users, loans, clients, search, monitoring, admin  # Temporalmente comentado
    # solicitudes, agenda_cobranza  # Temporalmente comentado para resolver errores de modelos
)

api_router = APIRouter()

# Incluir rutas de salud
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# Incluir rutas de sucursales
api_router.include_router(
    sucursales.router,
    prefix="/sucursales",
    tags=["sucursales"]
)

# # Incluir rutas de solicitudes
# api_router.include_router(
#     solicitudes.router,
#     prefix="/solicitudes",
#     tags=["solicitudes"]
# )

# # Incluir rutas de agenda de cobranza
# api_router.include_router(
#     agenda_cobranza.router,
#     prefix="/agenda-cobranza",
#     tags=["agenda-cobranza"]
# )

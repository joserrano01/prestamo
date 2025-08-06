from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def get_loans():
    """Obtener lista de préstamos"""
    return JSONResponse([
        {
            "id": "1",
            "clienteId": "1",
            "monto": 50000,
            "plazo": 12,
            "tasaInteres": 12.5,
            "estado": "activo",
            "fechaInicio": "2025-01-01",
            "fechaVencimiento": "2025-12-31"
        }
    ])


@router.get("/stats")
async def get_loan_stats():
    """Obtener estadísticas de préstamos"""
    return JSONResponse({
        "prestamosActivos": 1234,
        "totalPrestado": 2450000,
        "clientesActivos": 892,
        "tasaRecuperacion": 94.2
    })

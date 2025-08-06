from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/")
async def get_clients():
    """Obtener lista de clientes"""
    return JSONResponse([
        {
            "id": "1",
            "nombre": "Juan",
            "apellido": "Pérez",
            "email": "juan.perez@email.com",
            "telefono": "555-0123",
            "ingresosMensuales": 25000
        }
    ])

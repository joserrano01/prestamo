from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/me")
async def get_current_user():
    """Obtener información del usuario actual"""
    return JSONResponse({
        "id": "1",
        "email": "admin@financepro.com",
        "name": "Administrador",
        "role": "admin",
        "sucursal": "central",
        "isActive": True
    })


@router.get("/")
async def get_users():
    """Obtener lista de usuarios"""
    return JSONResponse([
        {
            "id": "1",
            "email": "admin@financepro.com",
            "name": "Administrador",
            "role": "admin",
            "sucursal": "central",
            "isActive": True
        }
    ])

"""
Endpoint de salud del sistema
"""
from fastapi import APIRouter
from typing import Dict

router = APIRouter()

@router.get("/")
def health_check() -> Dict[str, str]:
    """
    Endpoint simple de salud
    """
    return {
        "status": "healthy",
        "message": "Backend is running"
    }
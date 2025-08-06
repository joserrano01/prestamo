"""
API endpoints para gestión de préstamos con descuento directo

Este módulo contiene todos los endpoints para manejar préstamos,
especialmente aquellos con descuento directo según las regulaciones
del sistema financiero panameño.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from backend.app.core.database import get_db
from backend.app.core.auth import get_current_user, require_permissions
from backend.app.models.secure_models import Usuario, Prestamo
from backend.app.services.prestamo_service import PrestamoService
from backend.app.schemas.prestamo_schemas import (
    PrestamoCreate, PrestamoUpdate, PrestamoResponse, PrestamoListResponse,
    PrestamoFiltros, AutorizarDescuentoRequest, EstadisticasDescuentoDirecto,
    ValidacionDescuentoResponse, TipoPrestamo, TipoDescuentoDirecto,
    ModalidadPago, EstadoPrestamo
)

router = APIRouter()


@router.post("/", response_model=PrestamoResponse, status_code=status.HTTP_201_CREATED)
def crear_prestamo(
    prestamo_data: PrestamoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear un nuevo préstamo
    
    Requiere permisos de creación de préstamos.
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:create"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear préstamos"
        )
    
    service = PrestamoService(db)
    
    try:
        prestamo = service.crear_prestamo(prestamo_data, str(current_user.id))
        return prestamo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/", response_model=List[PrestamoListResponse])
def listar_prestamos(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    cliente_id: Optional[str] = Query(None, description="Filtrar por cliente"),
    tipo_prestamo: Optional[TipoPrestamo] = Query(None, description="Filtrar por tipo de préstamo"),
    tipo_descuento_directo: Optional[TipoDescuentoDirecto] = Query(None, description="Filtrar por tipo de descuento"),
    modalidad_pago: Optional[ModalidadPago] = Query(None, description="Filtrar por modalidad de pago"),
    estado: Optional[EstadoPrestamo] = Query(None, description="Filtrar por estado"),
    descuento_autorizado: Optional[bool] = Query(None, description="Filtrar por autorización de descuento"),
    solo_con_mora: Optional[bool] = Query(False, description="Solo préstamos en mora"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Listar préstamos con filtros
    
    Los usuarios solo pueden ver préstamos de su sucursal, excepto administradores.
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver préstamos"
        )
    
    # Filtro de sucursal para control de acceso
    sucursal_id = None if current_user.rol == "admin" else str(current_user.sucursal_id)
    
    filtros = PrestamoFiltros(
        cliente_id=cliente_id,
        tipo_prestamo=tipo_prestamo,
        tipo_descuento_directo=tipo_descuento_directo,
        modalidad_pago=modalidad_pago,
        estado=estado,
        descuento_autorizado=descuento_autorizado,
        solo_con_mora=solo_con_mora
    )
    
    service = PrestamoService(db)
    prestamos = service.listar_prestamos(filtros, skip, limit, sucursal_id)
    
    # Convertir a respuesta simplificada
    return [
        PrestamoListResponse(
            id=str(p.id),
            numero_prestamo=p.numero_prestamo,
            cliente_nombre=p.cliente.nombre_completo if p.cliente else "N/A",
            tipo_prestamo=p.tipo_prestamo,
            tipo_descuento_directo=p.tipo_descuento_directo,
            modalidad_pago=p.modalidad_pago,
            estado=p.estado,
            monto=p.monto,
            saldo_pendiente=Decimal(str(p.saldo_pendiente)),
            cuota_mensual=p.cuota_mensual,
            fecha_vencimiento=p.fecha_vencimiento,
            dias_mora=p.dias_mora,
            estado_mora=p.estado_mora,
            descuento_autorizado=p.descuento_autorizado,
            created_at=p.created_at
        )
        for p in prestamos
    ]


@router.get("/{prestamo_id}", response_model=PrestamoResponse)
def obtener_prestamo(
    prestamo_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener un préstamo por ID
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver préstamos"
        )
    
    service = PrestamoService(db)
    prestamo = service.obtener_prestamo(prestamo_id)
    
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    # Verificar acceso por sucursal (excepto admin)
    if current_user.rol != "admin" and str(prestamo.sucursal_id) != str(current_user.sucursal_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este préstamo"
        )
    
    return prestamo


@router.get("/numero/{numero_prestamo}", response_model=PrestamoResponse)
def obtener_prestamo_por_numero(
    numero_prestamo: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener un préstamo por número
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver préstamos"
        )
    
    service = PrestamoService(db)
    prestamo = service.obtener_prestamo_por_numero(numero_prestamo)
    
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    # Verificar acceso por sucursal (excepto admin)
    if current_user.rol != "admin" and str(prestamo.sucursal_id) != str(current_user.sucursal_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este préstamo"
        )
    
    return prestamo


@router.put("/{prestamo_id}", response_model=PrestamoResponse)
def actualizar_prestamo(
    prestamo_id: str,
    prestamo_data: PrestamoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar un préstamo
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:update"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar préstamos"
        )
    
    service = PrestamoService(db)
    
    # Verificar que el préstamo existe y el usuario tiene acceso
    prestamo_existente = service.obtener_prestamo(prestamo_id)
    if not prestamo_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    # Verificar acceso por sucursal (excepto admin)
    if current_user.rol != "admin" and str(prestamo_existente.sucursal_id) != str(current_user.sucursal_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este préstamo"
        )
    
    try:
        prestamo = service.actualizar_prestamo(prestamo_id, prestamo_data, str(current_user.id))
        return prestamo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/{prestamo_id}/autorizar-descuento")
def autorizar_descuento_directo(
    prestamo_id: str,
    autorizacion_data: AutorizarDescuentoRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Autorizar descuento directo de un préstamo
    
    Requiere permisos especiales de autorización.
    """
    # Verificar permisos especiales
    if not require_permissions(current_user, ["prestamos:authorize_discount"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para autorizar descuentos directos"
        )
    
    service = PrestamoService(db)
    
    # Verificar acceso al préstamo
    prestamo = service.obtener_prestamo(prestamo_id)
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    # Verificar acceso por sucursal (excepto admin)
    if current_user.rol != "admin" and str(prestamo.sucursal_id) != str(current_user.sucursal_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este préstamo"
        )
    
    exito, mensaje = service.autorizar_descuento_directo(
        prestamo_id, autorizacion_data, str(current_user.id)
    )
    
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )
    
    return {"mensaje": mensaje, "autorizado": True}


@router.post("/{prestamo_id}/revocar-descuento")
def revocar_descuento_directo(
    prestamo_id: str,
    motivo: str = Query(..., description="Motivo de la revocación"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Revocar autorización de descuento directo
    """
    # Verificar permisos especiales
    if not require_permissions(current_user, ["prestamos:revoke_discount"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para revocar descuentos directos"
        )
    
    service = PrestamoService(db)
    
    # Verificar acceso al préstamo
    prestamo = service.obtener_prestamo(prestamo_id)
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    # Verificar acceso por sucursal (excepto admin)
    if current_user.rol != "admin" and str(prestamo.sucursal_id) != str(current_user.sucursal_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este préstamo"
        )
    
    exito, mensaje = service.revocar_descuento_directo(
        prestamo_id, motivo, str(current_user.id)
    )
    
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=mensaje
        )
    
    return {"mensaje": mensaje, "revocado": True}


@router.get("/{prestamo_id}/validar-descuento", response_model=ValidacionDescuentoResponse)
def validar_descuento_directo(
    prestamo_id: str,
    salario_bruto: Decimal = Query(..., description="Salario bruto del empleado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Validar si el descuento directo es viable para un préstamo
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para validar descuentos"
        )
    
    service = PrestamoService(db)
    
    # Verificar acceso al préstamo
    prestamo = service.obtener_prestamo(prestamo_id)
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )
    
    # Verificar acceso por sucursal (excepto admin)
    if current_user.rol != "admin" and str(prestamo.sucursal_id) != str(current_user.sucursal_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a este préstamo"
        )
    
    return service.validar_descuento_directo(prestamo_id, salario_bruto)


@router.get("/estadisticas/descuento-directo", response_model=EstadisticasDescuentoDirecto)
def obtener_estadisticas_descuento_directo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener estadísticas de descuento directo
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:stats"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver estadísticas"
        )
    
    # Filtro de sucursal para control de acceso
    sucursal_id = None if current_user.rol == "admin" else str(current_user.sucursal_id)
    
    service = PrestamoService(db)
    return service.obtener_estadisticas_descuento_directo(sucursal_id)


@router.get("/reportes/por-vencer", response_model=List[PrestamoListResponse])
def obtener_prestamos_por_vencer(
    dias: int = Query(30, ge=1, le=365, description="Días para vencimiento"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener préstamos que vencen en X días
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver reportes"
        )
    
    # Filtro de sucursal para control de acceso
    sucursal_id = None if current_user.rol == "admin" else str(current_user.sucursal_id)
    
    service = PrestamoService(db)
    prestamos = service.obtener_prestamos_por_vencer(dias, sucursal_id)
    
    return [
        PrestamoListResponse(
            id=str(p.id),
            numero_prestamo=p.numero_prestamo,
            cliente_nombre=p.cliente.nombre_completo if p.cliente else "N/A",
            tipo_prestamo=p.tipo_prestamo,
            tipo_descuento_directo=p.tipo_descuento_directo,
            modalidad_pago=p.modalidad_pago,
            estado=p.estado,
            monto=p.monto,
            saldo_pendiente=Decimal(str(p.saldo_pendiente)),
            cuota_mensual=p.cuota_mensual,
            fecha_vencimiento=p.fecha_vencimiento,
            dias_mora=p.dias_mora,
            estado_mora=p.estado_mora,
            descuento_autorizado=p.descuento_autorizado,
            created_at=p.created_at
        )
        for p in prestamos
    ]


@router.get("/reportes/en-mora", response_model=List[PrestamoListResponse])
def obtener_prestamos_en_mora(
    dias_minimos: int = Query(1, ge=1, description="Días mínimos de mora"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener préstamos en mora
    """
    # Verificar permisos
    if not require_permissions(current_user, ["prestamos:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver reportes"
        )
    
    # Filtro de sucursal para control de acceso
    sucursal_id = None if current_user.rol == "admin" else str(current_user.sucursal_id)
    
    service = PrestamoService(db)
    prestamos = service.obtener_prestamos_en_mora(dias_minimos, sucursal_id)
    
    return [
        PrestamoListResponse(
            id=str(p.id),
            numero_prestamo=p.numero_prestamo,
            cliente_nombre=p.cliente.nombre_completo if p.cliente else "N/A",
            tipo_prestamo=p.tipo_prestamo,
            tipo_descuento_directo=p.tipo_descuento_directo,
            modalidad_pago=p.modalidad_pago,
            estado=p.estado,
            monto=p.monto,
            saldo_pendiente=Decimal(str(p.saldo_pendiente)),
            cuota_mensual=p.cuota_mensual,
            fecha_vencimiento=p.fecha_vencimiento,
            dias_mora=p.dias_mora,
            estado_mora=p.estado_mora,
            descuento_autorizado=p.descuento_autorizado,
            created_at=p.created_at
        )
        for p in prestamos
    ]


# Endpoints para obtener catálogos
@router.get("/catalogos/tipos-prestamo")
def obtener_tipos_prestamo():
    """Obtener catálogo de tipos de préstamo"""
    return [{"codigo": tipo.value, "descripcion": tipo.value.replace("_", " ").title()} for tipo in TipoPrestamo]


@router.get("/catalogos/tipos-descuento-directo")
def obtener_tipos_descuento_directo():
    """Obtener catálogo de tipos de descuento directo"""
    descripciones = {
        "JUBILADOS": "Jubilados y Pensionados",
        "PAGOS_VOLUNTARIOS": "Pagos Voluntarios",
        "CONTRALORIA": "Contraloría General de la República",
        "CSS": "Caja de Seguro Social",
        "MEF": "Ministerio de Economía y Finanzas",
        "MEDUCA": "Ministerio de Educación",
        "MINSA": "Ministerio de Salud",
        "EMPRESA_PRIVADA": "Empresa Privada",
        "BANCO_NACIONAL": "Banco Nacional de Panamá",
        "CAJA_AHORROS": "Caja de Ahorros",
        "OTROS_BANCOS": "Otros Bancos",
        "COOPERATIVAS": "Cooperativas",
        "GARANTIA_HIPOTECARIA": "Con Garantía Hipotecaria",
        "GARANTIA_VEHICULAR": "Con Garantía Vehicular",
        "GARANTIA_FIDUCIARIA": "Con Garantía Fiduciaria",
        "GARANTIA_PRENDARIA": "Con Garantía Prendaria",
        "AVAL_SOLIDARIO": "Con Aval Solidario",
        "SIN_DESCUENTO": "Sin Descuento Directo"
    }
    
    return [
        {"codigo": tipo.value, "descripcion": descripciones.get(tipo.value, tipo.value)}
        for tipo in TipoDescuentoDirecto
    ]


@router.get("/catalogos/modalidades-pago")
def obtener_modalidades_pago():
    """Obtener catálogo de modalidades de pago"""
    descripciones = {
        "DESCUENTO_DIRECTO": "Descuento Directo",
        "DEBITO_AUTOMATICO": "Débito Automático",
        "VENTANILLA": "Pago en Ventanilla",
        "TRANSFERENCIA": "Transferencia Bancaria",
        "CHEQUE": "Cheque",
        "EFECTIVO": "Efectivo"
    }
    
    return [
        {"codigo": modalidad.value, "descripcion": descripciones.get(modalidad.value, modalidad.value)}
        for modalidad in ModalidadPago
    ]


@router.get("/catalogos/estados-prestamo")
def obtener_estados_prestamo():
    """Obtener catálogo de estados de préstamo"""
    descripciones = {
        "SOLICITUD": "En Solicitud",
        "EVALUACION": "En Evaluación",
        "APROBADO": "Aprobado",
        "RECHAZADO": "Rechazado",
        "DESEMBOLSADO": "Desembolsado",
        "VIGENTE": "Vigente",
        "MORA": "En Mora",
        "CANCELADO": "Cancelado",
        "REFINANCIADO": "Refinanciado",
        "CASTIGADO": "Castigado"
    }
    
    return [
        {"codigo": estado.value, "descripcion": descripciones.get(estado.value, estado.value)}
        for estado in EstadoPrestamo
    ]

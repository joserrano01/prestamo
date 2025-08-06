"""
API endpoints para gestión de solicitudes de clientes
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.api.deps import get_current_user, get_db
from app.models.secure_models import (
    ClienteSolicitud, SolicitudAlerta, Cliente, Usuario
)
from app.schemas.solicitudes import (
    SolicitudCreate, SolicitudUpdate, SolicitudResponse,
    SolicitudListResponse, AlertaResponse, DashboardResponse,
    SolicitudAsignar, SolicitudSeguimiento
)
from app.services.solicitudes_service import SolicitudesService
from app.core.security import require_permissions

router = APIRouter()


@router.post("/", response_model=SolicitudResponse)
def crear_solicitud(
    *,
    db: Session = Depends(get_db),
    solicitud_in: SolicitudCreate,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear nueva solicitud de cliente
    """
    try:
        # Verificar que el cliente existe
        cliente = db.query(Cliente).filter(Cliente.id == solicitud_in.cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        # Crear servicio
        service = SolicitudesService(db)
        
        # Crear solicitud
        solicitud = service.crear_solicitud(
            cliente_id=str(solicitud_in.cliente_id),
            tipo_solicitud=solicitud_in.tipo_solicitud,
            asunto=solicitud_in.asunto,
            descripcion=solicitud_in.descripcion,
            canal=solicitud_in.canal,
            usuario_asignado_id=str(solicitud_in.usuario_asignado_id) if solicitud_in.usuario_asignado_id else None,
            sucursal_id=str(current_user.sucursal_id) if current_user.sucursal_id else None,
            prioridad=solicitud_in.prioridad,
            sla_horas=solicitud_in.sla_horas or 24,
            monto_solicitado=solicitud_in.monto_solicitado,
            moneda=solicitud_in.moneda,
            plazo_solicitado=solicitud_in.plazo_solicitado,
            telefono_contacto=solicitud_in.telefono_contacto,
            email_contacto=solicitud_in.email_contacto,
            requiere_documentos=solicitud_in.requiere_documentos,
            documentos_pendientes=solicitud_in.documentos_pendientes,
            requiere_garantia=solicitud_in.requiere_garantia,
            requiere_avalista=solicitud_in.requiere_avalista
        )
        
        return SolicitudResponse.from_orm(solicitud)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creando solicitud: {str(e)}"
        )


@router.get("/", response_model=SolicitudListResponse)
def listar_solicitudes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    cliente_id: Optional[UUID] = None,
    tipo_solicitud: Optional[str] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    canal: Optional[str] = None,
    usuario_asignado_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    solo_activas: bool = False,
    solo_vencidas: bool = False,
    solo_fuera_sla: bool = False
):
    """
    Listar solicitudes con filtros
    """
    try:
        query = db.query(ClienteSolicitud)
        
        # Filtros básicos
        if cliente_id:
            query = query.filter(ClienteSolicitud.cliente_id == cliente_id)
        
        if tipo_solicitud:
            query = query.filter(ClienteSolicitud.tipo_solicitud == tipo_solicitud)
        
        if estado:
            query = query.filter(ClienteSolicitud.estado == estado)
        
        if prioridad:
            query = query.filter(ClienteSolicitud.prioridad == prioridad)
        
        if canal:
            query = query.filter(ClienteSolicitud.canal == canal)
        
        if usuario_asignado_id:
            query = query.filter(ClienteSolicitud.usuario_asignado_id == usuario_asignado_id)
        
        if sucursal_id:
            query = query.filter(ClienteSolicitud.sucursal_id == sucursal_id)
        elif not require_permissions(current_user, ["admin", "gerente"]):
            # Usuarios normales solo ven solicitudes de su sucursal
            if current_user.sucursal_id:
                query = query.filter(ClienteSolicitud.sucursal_id == current_user.sucursal_id)
        
        # Filtros de fecha
        if fecha_desde:
            query = query.filter(ClienteSolicitud.fecha_solicitud >= fecha_desde)
        
        if fecha_hasta:
            query = query.filter(ClienteSolicitud.fecha_solicitud <= fecha_hasta)
        
        # Filtros especiales
        if solo_activas:
            query = query.filter(
                ~ClienteSolicitud.estado.in_([
                    'COMPLETADA', 'DESEMBOLSADA', 'RECHAZADA', 'CANCELADA', 'VENCIDA'
                ])
            )
        
        if solo_vencidas:
            query = query.filter(ClienteSolicitud.fecha_vencimiento < datetime.utcnow())
        
        if solo_fuera_sla:
            query = query.filter(ClienteSolicitud.fecha_limite_respuesta < datetime.utcnow())
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación y ordenamiento
        solicitudes = query.order_by(
            desc(ClienteSolicitud.fecha_solicitud)
        ).offset(skip).limit(limit).all()
        
        return SolicitudListResponse(
            items=[SolicitudResponse.from_orm(s) for s in solicitudes],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error listando solicitudes: {str(e)}"
        )


@router.get("/{solicitud_id}", response_model=SolicitudResponse)
def obtener_solicitud(
    *,
    db: Session = Depends(get_db),
    solicitud_id: UUID,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener solicitud por ID
    """
    solicitud = db.query(ClienteSolicitud).filter(
        ClienteSolicitud.id == solicitud_id
    ).first()
    
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    # Verificar permisos
    if not require_permissions(current_user, ["admin", "gerente"]):
        if (solicitud.sucursal_id != current_user.sucursal_id and 
            solicitud.usuario_asignado_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta solicitud"
            )
    
    return SolicitudResponse.from_orm(solicitud)


@router.put("/{solicitud_id}", response_model=SolicitudResponse)
def actualizar_solicitud(
    *,
    db: Session = Depends(get_db),
    solicitud_id: UUID,
    solicitud_in: SolicitudUpdate,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar solicitud
    """
    solicitud = db.query(ClienteSolicitud).filter(
        ClienteSolicitud.id == solicitud_id
    ).first()
    
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitud no encontrada"
        )
    
    # Verificar permisos
    if not require_permissions(current_user, ["admin", "gerente"]):
        if (solicitud.sucursal_id != current_user.sucursal_id and 
            solicitud.usuario_asignado_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para actualizar esta solicitud"
            )
    
    try:
        service = SolicitudesService(db)
        
        # Actualizar campos permitidos
        update_data = solicitud_in.dict(exclude_unset=True)
        
        # Si se actualiza el estado, usar el servicio
        if 'estado' in update_data:
            nuevo_estado = update_data.pop('estado')
            observaciones = update_data.get('observaciones')
            
            solicitud = service.actualizar_estado_solicitud(
                str(solicitud_id),
                nuevo_estado,
                observaciones,
                str(current_user.id)
            )
        
        # Actualizar otros campos
        for field, value in update_data.items():
            if hasattr(solicitud, field):
                setattr(solicitud, field, value)
        
        solicitud.incrementar_interacciones()
        db.commit()
        db.refresh(solicitud)
        
        return SolicitudResponse.from_orm(solicitud)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error actualizando solicitud: {str(e)}"
        )


@router.post("/{solicitud_id}/asignar", response_model=SolicitudResponse)
def asignar_solicitud(
    *,
    db: Session = Depends(get_db),
    solicitud_id: UUID,
    asignacion: SolicitudAsignar,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Asignar solicitud a un usuario
    """
    # Verificar permisos (solo gerentes y admins pueden asignar)
    if not require_permissions(current_user, ["admin", "gerente"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para asignar solicitudes"
        )
    
    # Verificar que el usuario destino existe
    usuario_destino = db.query(Usuario).filter(
        Usuario.id == asignacion.usuario_asignado_id
    ).first()
    
    if not usuario_destino:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario destino no encontrado"
        )
    
    try:
        service = SolicitudesService(db)
        
        solicitud = service.asignar_solicitud(
            str(solicitud_id),
            str(asignacion.usuario_asignado_id),
            str(current_user.id)
        )
        
        return SolicitudResponse.from_orm(solicitud)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error asignando solicitud: {str(e)}"
        )


@router.post("/{solicitud_id}/seguimiento", response_model=SolicitudResponse)
def programar_seguimiento(
    *,
    db: Session = Depends(get_db),
    solicitud_id: UUID,
    seguimiento: SolicitudSeguimiento,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Programar seguimiento para una solicitud
    """
    try:
        service = SolicitudesService(db)
        
        solicitud = service.programar_seguimiento(
            str(solicitud_id),
            seguimiento.fecha_seguimiento,
            seguimiento.observaciones,
            str(current_user.id)
        )
        
        return SolicitudResponse.from_orm(solicitud)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error programando seguimiento: {str(e)}"
        )


@router.get("/dashboard/resumen", response_model=DashboardResponse)
def obtener_dashboard(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    usuario_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
):
    """
    Obtener datos para dashboard de solicitudes
    """
    try:
        service = SolicitudesService(db)
        
        # Preparar filtros
        filtros = {}
        if fecha_desde:
            filtros['fecha_desde'] = fecha_desde
        if fecha_hasta:
            filtros['fecha_hasta'] = fecha_hasta
        
        # Determinar alcance según permisos
        if require_permissions(current_user, ["admin"]):
            # Admin ve todo
            pass
        elif require_permissions(current_user, ["gerente"]):
            # Gerente ve su sucursal
            sucursal_id = sucursal_id or current_user.sucursal_id
        else:
            # Usuario normal ve solo sus solicitudes
            usuario_id = current_user.id
            sucursal_id = current_user.sucursal_id
        
        dashboard_data = service.obtener_solicitudes_dashboard(
            usuario_id=str(usuario_id) if usuario_id else None,
            sucursal_id=str(sucursal_id) if sucursal_id else None,
            filtros=filtros
        )
        
        return DashboardResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo dashboard: {str(e)}"
        )


@router.get("/alertas/usuario", response_model=List[AlertaResponse])
def obtener_alertas_usuario(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    solo_pendientes: bool = True,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Obtener alertas del usuario actual
    """
    try:
        service = SolicitudesService(db)
        
        alertas = service.obtener_alertas_usuario(
            str(current_user.id),
            solo_pendientes
        )
        
        # Limitar resultados
        alertas = alertas[:limit]
        
        return [AlertaResponse.from_orm(alerta) for alerta in alertas]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo alertas: {str(e)}"
        )


@router.put("/alertas/{alerta_id}/leida", response_model=AlertaResponse)
def marcar_alerta_leida(
    *,
    db: Session = Depends(get_db),
    alerta_id: UUID,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Marcar alerta como leída
    """
    try:
        service = SolicitudesService(db)
        
        alerta = service.marcar_alerta_leida(
            str(alerta_id),
            str(current_user.id)
        )
        
        return AlertaResponse.from_orm(alerta)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error marcando alerta como leída: {str(e)}"
        )


@router.get("/tipos", response_model=Dict[str, str])
def obtener_tipos_solicitud():
    """
    Obtener tipos de solicitud disponibles
    """
    return {
        tipo[0]: tipo[0].replace('_', ' ').title()
        for tipo in ClienteSolicitud.TIPOS_SOLICITUD
    }


@router.get("/estados", response_model=Dict[str, str])
def obtener_estados_solicitud():
    """
    Obtener estados de solicitud disponibles
    """
    return {
        estado[0]: estado[0].replace('_', ' ').title()
        for estado in ClienteSolicitud.ESTADOS_SOLICITUD
    }


@router.get("/canales", response_model=Dict[str, str])
def obtener_canales():
    """
    Obtener canales disponibles
    """
    return {
        canal[0]: canal[0].replace('_', ' ').title()
        for canal in ClienteSolicitud.CANALES
    }


@router.get("/prioridades", response_model=Dict[str, str])
def obtener_prioridades():
    """
    Obtener prioridades disponibles
    """
    return {
        prioridad[0]: prioridad[0].replace('_', ' ').title()
        for prioridad in ClienteSolicitud.PRIORIDADES
    }

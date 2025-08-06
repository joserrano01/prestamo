"""
API endpoints para gestión de agenda de cobranza
"""
from datetime import datetime, date, time
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.api.deps import get_current_user, get_db
from app.models.agenda_models import (
    AgendaCobranza, AlertaCobranza, TipoActividad, EstadoActividad, 
    PrioridadActividad, ResultadoActividad
)
from app.models.secure_models import Cliente, Usuario
from app.schemas.agenda_cobranza import (
    ActividadCobranzaCreate, ActividadCobranzaUpdate, ActividadCobranzaResponse,
    ActividadCobranzaListResponse, AlertaCobranzaResponse, DashboardCobranzaResponse,
    ActividadReprogramar, ActividadCompletar
)
from app.services.agenda_cobranza_service import AgendaCobranzaService
from app.core.security import require_permissions

router = APIRouter()


@router.post("/", response_model=ActividadCobranzaResponse)
def crear_actividad_cobranza(
    *,
    db: Session = Depends(get_db),
    actividad_in: ActividadCobranzaCreate,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crear nueva actividad de cobranza
    """
    try:
        # Verificar que el cliente existe
        cliente = db.query(Cliente).filter(Cliente.id == actividad_in.cliente_id).first()
        if not cliente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado"
            )
        
        # Crear servicio
        service = AgendaCobranzaService(db)
        
        # Crear actividad
        actividad = service.crear_actividad_cobranza(
            cliente_id=str(actividad_in.cliente_id),
            tipo_actividad=TipoActividad(actividad_in.tipo_actividad),
            titulo=actividad_in.titulo,
            descripcion=actividad_in.descripcion,
            fecha_programada=actividad_in.fecha_programada,
            usuario_asignado_id=str(actividad_in.usuario_asignado_id or current_user.id),
            prestamo_id=str(actividad_in.prestamo_id) if actividad_in.prestamo_id else None,
            sucursal_id=str(current_user.sucursal_id) if current_user.sucursal_id else None,
            prioridad=PrioridadActividad(actividad_in.prioridad),
            hora_inicio=actividad_in.hora_inicio,
            duracion_estimada_minutos=actividad_in.duracion_estimada_minutos,
            objetivo=actividad_in.objetivo,
            direccion_visita=actividad_in.direccion_visita,
            telefono_contacto=actividad_in.telefono_contacto,
            persona_contacto=actividad_in.persona_contacto,
            monto_gestionado=actividad_in.monto_gestionado,
            generar_alerta_previa=actividad_in.generar_alerta_previa,
            minutos_alerta_previa=actividad_in.minutos_alerta_previa
        )
        
        return ActividadCobranzaResponse.from_orm(actividad)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creando actividad de cobranza: {str(e)}"
        )


@router.get("/", response_model=ActividadCobranzaListResponse)
def listar_actividades_cobranza(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    cliente_id: Optional[UUID] = None,
    prestamo_id: Optional[UUID] = None,
    tipo_actividad: Optional[str] = None,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    usuario_asignado_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    solo_hoy: bool = False,
    solo_pendientes: bool = False,
    solo_vencidas: bool = False
):
    """
    Listar actividades de cobranza con filtros
    """
    try:
        query = db.query(AgendaCobranza)
        
        # Filtros básicos
        if cliente_id:
            query = query.filter(AgendaCobranza.cliente_id == cliente_id)
        
        if prestamo_id:
            query = query.filter(AgendaCobranza.prestamo_id == prestamo_id)
        
        if tipo_actividad:
            query = query.filter(AgendaCobranza.tipo_actividad == TipoActividad(tipo_actividad))
        
        if estado:
            query = query.filter(AgendaCobranza.estado == EstadoActividad(estado))
        
        if prioridad:
            query = query.filter(AgendaCobranza.prioridad == PrioridadActividad(prioridad))
        
        if usuario_asignado_id:
            query = query.filter(AgendaCobranza.usuario_asignado_id == usuario_asignado_id)
        elif not require_permissions(current_user, ["admin", "gerente", "supervisor"]):
            # Usuarios normales solo ven sus actividades
            query = query.filter(AgendaCobranza.usuario_asignado_id == current_user.id)
        
        if sucursal_id:
            query = query.filter(AgendaCobranza.sucursal_id == sucursal_id)
        elif not require_permissions(current_user, ["admin", "gerente"]):
            # Usuarios no admin/gerente solo ven actividades de su sucursal
            if current_user.sucursal_id:
                query = query.filter(AgendaCobranza.sucursal_id == current_user.sucursal_id)
        
        # Filtros de fecha
        if fecha_desde:
            query = query.filter(AgendaCobranza.fecha_programada >= fecha_desde)
        
        if fecha_hasta:
            query = query.filter(AgendaCobranza.fecha_programada <= fecha_hasta)
        
        # Filtros especiales
        if solo_hoy:
            hoy = date.today()
            query = query.filter(AgendaCobranza.fecha_programada == hoy)
        
        if solo_pendientes:
            query = query.filter(
                AgendaCobranza.estado.in_([EstadoActividad.PROGRAMADA, EstadoActividad.EN_PROCESO])
            )
        
        if solo_vencidas:
            query = query.filter(AgendaCobranza.fecha_vencimiento < datetime.utcnow())
        
        # Contar total
        total = query.count()
        
        # Aplicar paginación y ordenamiento
        actividades = query.order_by(
            desc(AgendaCobranza.fecha_programada),
            AgendaCobranza.hora_inicio.asc()
        ).offset(skip).limit(limit).all()
        
        return ActividadCobranzaListResponse(
            items=[ActividadCobranzaResponse.from_orm(a) for a in actividades],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error listando actividades de cobranza: {str(e)}"
        )


@router.get("/{actividad_id}", response_model=ActividadCobranzaResponse)
def obtener_actividad_cobranza(
    *,
    db: Session = Depends(get_db),
    actividad_id: UUID,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtener actividad de cobranza por ID
    """
    actividad = db.query(AgendaCobranza).filter(
        AgendaCobranza.id == actividad_id
    ).first()
    
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad de cobranza no encontrada"
        )
    
    # Verificar permisos
    if not require_permissions(current_user, ["admin", "gerente", "supervisor"]):
        if (actividad.sucursal_id != current_user.sucursal_id and 
            actividad.usuario_asignado_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para ver esta actividad"
            )
    
    return ActividadCobranzaResponse.from_orm(actividad)


@router.put("/{actividad_id}", response_model=ActividadCobranzaResponse)
def actualizar_actividad_cobranza(
    *,
    db: Session = Depends(get_db),
    actividad_id: UUID,
    actividad_in: ActividadCobranzaUpdate,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualizar actividad de cobranza
    """
    actividad = db.query(AgendaCobranza).filter(
        AgendaCobranza.id == actividad_id
    ).first()
    
    if not actividad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Actividad de cobranza no encontrada"
        )
    
    # Verificar permisos
    if not require_permissions(current_user, ["admin", "gerente", "supervisor"]):
        if (actividad.sucursal_id != current_user.sucursal_id and 
            actividad.usuario_asignado_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para actualizar esta actividad"
            )
    
    try:
        service = AgendaCobranzaService(db)
        
        # Actualizar campos permitidos
        update_data = actividad_in.dict(exclude_unset=True)
        
        # Si se actualiza el estado, usar el servicio
        if 'estado' in update_data:
            nuevo_estado = EstadoActividad(update_data.pop('estado'))
            resultado = None
            if 'resultado' in update_data:
                resultado = ResultadoActividad(update_data.pop('resultado'))
            
            actividad = service.actualizar_estado_actividad(
                str(actividad_id),
                nuevo_estado,
                resultado,
                update_data.get('resultado_detalle'),
                update_data.get('proximos_pasos'),
                update_data.get('monto_prometido'),
                update_data.get('fecha_promesa_pago'),
                str(current_user.id)
            )
        
        # Actualizar otros campos
        for field, value in update_data.items():
            if hasattr(actividad, field) and value is not None:
                setattr(actividad, field, value)
        
        db.commit()
        db.refresh(actividad)
        
        return ActividadCobranzaResponse.from_orm(actividad)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error actualizando actividad de cobranza: {str(e)}"
        )


@router.post("/{actividad_id}/completar", response_model=ActividadCobranzaResponse)
def completar_actividad_cobranza(
    *,
    db: Session = Depends(get_db),
    actividad_id: UUID,
    completar_data: ActividadCompletar,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Completar actividad de cobranza
    """
    try:
        service = AgendaCobranzaService(db)
        
        actividad = service.actualizar_estado_actividad(
            str(actividad_id),
            EstadoActividad.COMPLETADA,
            ResultadoActividad(completar_data.resultado),
            completar_data.resultado_detalle,
            completar_data.proximos_pasos,
            completar_data.monto_prometido,
            completar_data.fecha_promesa_pago,
            str(current_user.id)
        )
        
        return ActividadCobranzaResponse.from_orm(actividad)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error completando actividad: {str(e)}"
        )


@router.post("/{actividad_id}/reprogramar", response_model=ActividadCobranzaResponse)
def reprogramar_actividad_cobranza(
    *,
    db: Session = Depends(get_db),
    actividad_id: UUID,
    reprogramar_data: ActividadReprogramar,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Reprogramar actividad de cobranza
    """
    try:
        service = AgendaCobranzaService(db)
        
        actividad = service.reprogramar_actividad(
            str(actividad_id),
            reprogramar_data.nueva_fecha,
            reprogramar_data.nueva_hora,
            reprogramar_data.motivo,
            str(current_user.id)
        )
        
        return ActividadCobranzaResponse.from_orm(actividad)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error reprogramando actividad: {str(e)}"
        )


@router.get("/agenda/hoy", response_model=List[ActividadCobranzaResponse])
def obtener_agenda_hoy(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    usuario_id: Optional[UUID] = None
):
    """
    Obtener actividades programadas para hoy
    """
    try:
        service = AgendaCobranzaService(db)
        
        # Determinar usuario según permisos
        if usuario_id and require_permissions(current_user, ["admin", "gerente", "supervisor"]):
            target_user_id = str(usuario_id)
        else:
            target_user_id = str(current_user.id)
        
        actividades = service.obtener_actividades_hoy(
            usuario_id=target_user_id,
            sucursal_id=str(current_user.sucursal_id) if current_user.sucursal_id else None
        )
        
        return [ActividadCobranzaResponse.from_orm(a) for a in actividades]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo agenda de hoy: {str(e)}"
        )


@router.get("/agenda/vencidas", response_model=List[ActividadCobranzaResponse])
def obtener_actividades_vencidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    usuario_id: Optional[UUID] = None
):
    """
    Obtener actividades vencidas
    """
    try:
        service = AgendaCobranzaService(db)
        
        # Determinar usuario según permisos
        if usuario_id and require_permissions(current_user, ["admin", "gerente", "supervisor"]):
            target_user_id = str(usuario_id)
        else:
            target_user_id = str(current_user.id)
        
        actividades = service.obtener_actividades_vencidas(
            usuario_id=target_user_id,
            sucursal_id=str(current_user.sucursal_id) if current_user.sucursal_id else None
        )
        
        return [ActividadCobranzaResponse.from_orm(a) for a in actividades]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo actividades vencidas: {str(e)}"
        )


@router.get("/promesas/vencidas", response_model=List[ActividadCobranzaResponse])
def obtener_promesas_pago_vencidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    usuario_id: Optional[UUID] = None
):
    """
    Obtener promesas de pago vencidas
    """
    try:
        service = AgendaCobranzaService(db)
        
        # Determinar usuario según permisos
        if usuario_id and require_permissions(current_user, ["admin", "gerente", "supervisor"]):
            target_user_id = str(usuario_id)
        else:
            target_user_id = str(current_user.id)
        
        actividades = service.obtener_promesas_pago_vencidas(usuario_id=target_user_id)
        
        return [ActividadCobranzaResponse.from_orm(a) for a in actividades]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo promesas vencidas: {str(e)}"
        )


@router.get("/cliente/{cliente_id}", response_model=List[ActividadCobranzaResponse])
def obtener_actividades_cliente(
    *,
    db: Session = Depends(get_db),
    cliente_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    incluir_completadas: bool = False
):
    """
    Obtener actividades de cobranza de un cliente específico
    """
    try:
        service = AgendaCobranzaService(db)
        
        actividades = service.obtener_agenda_cliente(
            str(cliente_id),
            incluir_completadas
        )
        
        return [ActividadCobranzaResponse.from_orm(a) for a in actividades]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo actividades del cliente: {str(e)}"
        )


@router.get("/dashboard/resumen", response_model=DashboardCobranzaResponse)
def obtener_dashboard_cobranza(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    usuario_id: Optional[UUID] = None,
    sucursal_id: Optional[UUID] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None
):
    """
    Obtener datos para dashboard de cobranza
    """
    try:
        service = AgendaCobranzaService(db)
        
        # Determinar alcance según permisos
        if require_permissions(current_user, ["admin"]):
            # Admin ve todo
            pass
        elif require_permissions(current_user, ["gerente", "supervisor"]):
            # Gerente/Supervisor ve su sucursal
            sucursal_id = sucursal_id or current_user.sucursal_id
        else:
            # Usuario normal ve solo sus actividades
            usuario_id = current_user.id
            sucursal_id = current_user.sucursal_id
        
        dashboard_data = service.obtener_dashboard_cobranza(
            usuario_id=str(usuario_id) if usuario_id else None,
            sucursal_id=str(sucursal_id) if sucursal_id else None,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta
        )
        
        return DashboardCobranzaResponse(**dashboard_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo dashboard de cobranza: {str(e)}"
        )


@router.get("/alertas/usuario", response_model=List[AlertaCobranzaResponse])
def obtener_alertas_cobranza_usuario(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
    solo_pendientes: bool = True,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Obtener alertas de cobranza del usuario actual
    """
    try:
        query = db.query(AlertaCobranza).filter(
            AlertaCobranza.usuario_destinatario_id == current_user.id
        )
        
        if solo_pendientes:
            query = query.filter(AlertaCobranza.estado.in_(['PENDIENTE', 'ENVIADA']))
        
        alertas = query.order_by(
            AlertaCobranza.nivel_urgencia.desc(),
            AlertaCobranza.fecha_programada.desc()
        ).limit(limit).all()
        
        return [AlertaCobranzaResponse.from_orm(alerta) for alerta in alertas]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error obteniendo alertas de cobranza: {str(e)}"
        )


@router.put("/alertas/{alerta_id}/leida", response_model=AlertaCobranzaResponse)
def marcar_alerta_cobranza_leida(
    *,
    db: Session = Depends(get_db),
    alerta_id: UUID,
    current_user: Usuario = Depends(get_current_user)
):
    """
    Marcar alerta de cobranza como leída
    """
    alerta = db.query(AlertaCobranza).filter(
        AlertaCobranza.id == alerta_id,
        AlertaCobranza.usuario_destinatario_id == current_user.id
    ).first()
    
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta de cobranza no encontrada"
        )
    
    try:
        alerta.marcar_como_leida()
        db.commit()
        
        return AlertaCobranzaResponse.from_orm(alerta)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error marcando alerta como leída: {str(e)}"
        )


@router.get("/tipos-actividad", response_model=Dict[str, str])
def obtener_tipos_actividad():
    """
    Obtener tipos de actividad disponibles
    """
    return {
        tipo.value: tipo.value.replace('_', ' ').title()
        for tipo in TipoActividad
    }


@router.get("/estados", response_model=Dict[str, str])
def obtener_estados_actividad():
    """
    Obtener estados de actividad disponibles
    """
    return {
        estado.value: estado.value.replace('_', ' ').title()
        for estado in EstadoActividad
    }


@router.get("/prioridades", response_model=Dict[str, str])
def obtener_prioridades():
    """
    Obtener prioridades disponibles
    """
    return {
        prioridad.value: prioridad.value.replace('_', ' ').title()
        for prioridad in PrioridadActividad
    }


@router.get("/resultados", response_model=Dict[str, str])
def obtener_resultados():
    """
    Obtener resultados disponibles
    """
    return {
        resultado.value: resultado.value.replace('_', ' ').title()
        for resultado in ResultadoActividad
    }

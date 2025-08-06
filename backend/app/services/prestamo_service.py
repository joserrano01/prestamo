"""
Servicio para gestión de préstamos con descuento directo

Este servicio maneja toda la lógica de negocio relacionada con préstamos,
especialmente los préstamos con descuento directo según las regulaciones
del sistema financiero panameño.
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging

from backend.app.models.secure_models import Prestamo, Cliente, Sucursal, Usuario
from backend.app.schemas.prestamo_schemas import (
    PrestamoCreate, PrestamoUpdate, PrestamoFiltros,
    AutorizarDescuentoRequest, EstadisticasDescuentoDirecto,
    ValidacionDescuentoResponse, TipoDescuentoDirecto, EstadoPrestamo
)

logger = logging.getLogger(__name__)


class PrestamoService:
    """Servicio para gestión integral de préstamos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def crear_prestamo(
        self, 
        prestamo_data: PrestamoCreate, 
        usuario_id: str
    ) -> Prestamo:
        """Crear un nuevo préstamo"""
        try:
            # Validar que el cliente existe
            cliente = self.db.query(Cliente).filter(Cliente.id == prestamo_data.cliente_id).first()
            if not cliente:
                raise ValueError(f"Cliente {prestamo_data.cliente_id} no encontrado")
            
            # Validar que la sucursal existe
            sucursal = self.db.query(Sucursal).filter(Sucursal.id == prestamo_data.sucursal_id).first()
            if not sucursal:
                raise ValueError(f"Sucursal {prestamo_data.sucursal_id} no encontrada")
            
            # Calcular fecha de vencimiento
            fecha_vencimiento = prestamo_data.fecha_inicio + timedelta(days=prestamo_data.plazo * 30)
            
            # Calcular monto total (simplificado - aquí se podría usar una fórmula más compleja)
            monto_total = prestamo_data.monto * (1 + (prestamo_data.tasa_interes / 100) * (prestamo_data.plazo / 12))
            
            # Crear el préstamo
            prestamo = Prestamo(
                cliente_id=prestamo_data.cliente_id,
                sucursal_id=prestamo_data.sucursal_id,
                usuario_id=usuario_id,
                tipo_prestamo=prestamo_data.tipo_prestamo,
                tipo_descuento_directo=prestamo_data.tipo_descuento_directo,
                modalidad_pago=prestamo_data.modalidad_pago,
                monto=prestamo_data.monto,
                plazo=prestamo_data.plazo,
                tasa_interes=prestamo_data.tasa_interes,
                fecha_inicio=prestamo_data.fecha_inicio,
                fecha_vencimiento=fecha_vencimiento,
                monto_total=monto_total,
                cuota_mensual=prestamo_data.cuota_mensual,
                garantia=prestamo_data.garantia,
                proposito=prestamo_data.proposito,
                observaciones=prestamo_data.observaciones,
                porcentaje_descuento_maximo=prestamo_data.porcentaje_descuento_maximo,
                created_by=usuario_id
            )
            
            # Agregar información de descuento directo si se proporciona
            if prestamo_data.descuento_directo_info:
                info = prestamo_data.descuento_directo_info
                prestamo.entidad_empleadora = info.entidad_empleadora
                prestamo.numero_empleado = info.numero_empleado
                prestamo.cedula_empleado = info.cedula_empleado
                prestamo.cargo_empleado = info.cargo_empleado
                prestamo.salario_base = str(info.salario_base) if info.salario_base else None
                prestamo.contacto_rrhh = info.contacto_rrhh
                prestamo.telefono_rrhh = info.telefono_rrhh
                prestamo.email_rrhh = info.email_rrhh
            
            # Generar número de préstamo
            prestamo.generar_numero_prestamo()
            
            self.db.add(prestamo)
            self.db.commit()
            self.db.refresh(prestamo)
            
            logger.info(f"Préstamo {prestamo.numero_prestamo} creado exitosamente")
            return prestamo
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando préstamo: {str(e)}")
            raise
    
    def obtener_prestamo(self, prestamo_id: str) -> Optional[Prestamo]:
        """Obtener un préstamo por ID"""
        return self.db.query(Prestamo).filter(Prestamo.id == prestamo_id).first()
    
    def obtener_prestamo_por_numero(self, numero_prestamo: str) -> Optional[Prestamo]:
        """Obtener un préstamo por número"""
        return self.db.query(Prestamo).filter(Prestamo.numero_prestamo == numero_prestamo).first()
    
    def listar_prestamos(
        self, 
        filtros: PrestamoFiltros,
        skip: int = 0,
        limit: int = 100,
        sucursal_id: Optional[str] = None
    ) -> List[Prestamo]:
        """Listar préstamos con filtros"""
        query = self.db.query(Prestamo)
        
        # Filtro por sucursal (para control de acceso)
        if sucursal_id:
            query = query.filter(Prestamo.sucursal_id == sucursal_id)
        
        # Aplicar filtros
        if filtros.cliente_id:
            query = query.filter(Prestamo.cliente_id == filtros.cliente_id)
        
        if filtros.tipo_prestamo:
            query = query.filter(Prestamo.tipo_prestamo == filtros.tipo_prestamo)
        
        if filtros.tipo_descuento_directo:
            query = query.filter(Prestamo.tipo_descuento_directo == filtros.tipo_descuento_directo)
        
        if filtros.modalidad_pago:
            query = query.filter(Prestamo.modalidad_pago == filtros.modalidad_pago)
        
        if filtros.estado:
            query = query.filter(Prestamo.estado == filtros.estado)
        
        if filtros.descuento_autorizado is not None:
            query = query.filter(Prestamo.descuento_autorizado == filtros.descuento_autorizado)
        
        # Filtros de fecha
        if filtros.fecha_inicio_desde:
            query = query.filter(Prestamo.fecha_inicio >= filtros.fecha_inicio_desde)
        
        if filtros.fecha_inicio_hasta:
            query = query.filter(Prestamo.fecha_inicio <= filtros.fecha_inicio_hasta)
        
        if filtros.fecha_vencimiento_desde:
            query = query.filter(Prestamo.fecha_vencimiento >= filtros.fecha_vencimiento_desde)
        
        if filtros.fecha_vencimiento_hasta:
            query = query.filter(Prestamo.fecha_vencimiento <= filtros.fecha_vencimiento_hasta)
        
        # Filtros de monto
        if filtros.monto_minimo:
            query = query.filter(Prestamo.monto >= filtros.monto_minimo)
        
        if filtros.monto_maximo:
            query = query.filter(Prestamo.monto <= filtros.monto_maximo)
        
        # Filtros especiales
        if filtros.solo_con_mora:
            query = query.filter(Prestamo.estado == EstadoPrestamo.MORA)
        
        # Ordenar por fecha de creación (más recientes primero)
        query = query.order_by(desc(Prestamo.created_at))
        
        return query.offset(skip).limit(limit).all()
    
    def actualizar_prestamo(
        self, 
        prestamo_id: str, 
        prestamo_data: PrestamoUpdate,
        usuario_id: str
    ) -> Optional[Prestamo]:
        """Actualizar un préstamo"""
        try:
            prestamo = self.obtener_prestamo(prestamo_id)
            if not prestamo:
                return None
            
            # Actualizar campos básicos
            for field, value in prestamo_data.dict(exclude_unset=True).items():
                if field != 'descuento_directo_info' and hasattr(prestamo, field):
                    setattr(prestamo, field, value)
            
            # Actualizar información de descuento directo
            if prestamo_data.descuento_directo_info:
                info = prestamo_data.descuento_directo_info
                prestamo.entidad_empleadora = info.entidad_empleadora
                prestamo.numero_empleado = info.numero_empleado
                prestamo.cedula_empleado = info.cedula_empleado
                prestamo.cargo_empleado = info.cargo_empleado
                prestamo.salario_base = str(info.salario_base) if info.salario_base else None
                prestamo.contacto_rrhh = info.contacto_rrhh
                prestamo.telefono_rrhh = info.telefono_rrhh
                prestamo.email_rrhh = info.email_rrhh
            
            prestamo.updated_by = usuario_id
            
            self.db.commit()
            self.db.refresh(prestamo)
            
            logger.info(f"Préstamo {prestamo.numero_prestamo} actualizado")
            return prestamo
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando préstamo: {str(e)}")
            raise
    
    def autorizar_descuento_directo(
        self, 
        prestamo_id: str, 
        autorizacion_data: AutorizarDescuentoRequest,
        usuario_id: str
    ) -> Tuple[bool, str]:
        """Autorizar descuento directo de un préstamo"""
        try:
            prestamo = self.obtener_prestamo(prestamo_id)
            if not prestamo:
                return False, "Préstamo no encontrado"
            
            # Validar que requiere descuento directo
            if not prestamo.requiere_descuento_directo:
                return False, "El préstamo no requiere descuento directo"
            
            # Validar porcentaje de descuento
            es_valido, mensaje = prestamo.validar_porcentaje_descuento(autorizacion_data.salario_bruto)
            
            if not es_valido:
                return False, mensaje
            
            # Autorizar descuento
            prestamo.autorizar_descuento(usuario_id)
            
            # Actualizar observaciones si se proporcionan
            if autorizacion_data.observaciones:
                observaciones_actuales = prestamo.observaciones or ""
                prestamo.observaciones = f"{observaciones_actuales}\n[AUTORIZACIÓN] {autorizacion_data.observaciones}"
            
            self.db.commit()
            
            logger.info(f"Descuento directo autorizado para préstamo {prestamo.numero_prestamo}")
            return True, "Descuento directo autorizado exitosamente"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error autorizando descuento: {str(e)}")
            return False, f"Error interno: {str(e)}"
    
    def revocar_descuento_directo(
        self, 
        prestamo_id: str, 
        motivo: str,
        usuario_id: str
    ) -> Tuple[bool, str]:
        """Revocar autorización de descuento directo"""
        try:
            prestamo = self.obtener_prestamo(prestamo_id)
            if not prestamo:
                return False, "Préstamo no encontrado"
            
            if not prestamo.descuento_autorizado:
                return False, "El préstamo no tiene descuento autorizado"
            
            # Revocar descuento
            prestamo.revocar_descuento(usuario_id)
            
            # Agregar motivo a observaciones
            observaciones_actuales = prestamo.observaciones or ""
            prestamo.observaciones = f"{observaciones_actuales}\n[REVOCACIÓN] {motivo}"
            
            self.db.commit()
            
            logger.info(f"Descuento directo revocado para préstamo {prestamo.numero_prestamo}")
            return True, "Descuento directo revocado exitosamente"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error revocando descuento: {str(e)}")
            return False, f"Error interno: {str(e)}"
    
    def validar_descuento_directo(
        self, 
        prestamo_id: str, 
        salario_bruto: Decimal
    ) -> ValidacionDescuentoResponse:
        """Validar si el descuento directo es viable"""
        prestamo = self.obtener_prestamo(prestamo_id)
        if not prestamo:
            return ValidacionDescuentoResponse(
                es_valido=False,
                mensaje="Préstamo no encontrado",
                porcentaje_descuento=0,
                salario_bruto=salario_bruto,
                cuota_mensual=Decimal('0'),
                margen_disponible=Decimal('0')
            )
        
        porcentaje_descuento = (float(prestamo.cuota_mensual) / float(salario_bruto)) * 100
        margen_disponible = salario_bruto * Decimal('0.30') - prestamo.cuota_mensual
        
        es_valido, mensaje = prestamo.validar_porcentaje_descuento(salario_bruto)
        
        return ValidacionDescuentoResponse(
            es_valido=es_valido,
            mensaje=mensaje,
            porcentaje_descuento=porcentaje_descuento,
            salario_bruto=salario_bruto,
            cuota_mensual=prestamo.cuota_mensual,
            margen_disponible=margen_disponible
        )
    
    def obtener_estadisticas_descuento_directo(
        self, 
        sucursal_id: Optional[str] = None
    ) -> EstadisticasDescuentoDirecto:
        """Obtener estadísticas de descuento directo"""
        query = self.db.query(Prestamo)
        
        if sucursal_id:
            query = query.filter(Prestamo.sucursal_id == sucursal_id)
        
        prestamos = query.all()
        
        total_prestamos = len(prestamos)
        con_descuento_directo = len([p for p in prestamos if p.requiere_descuento_directo])
        
        # Estadísticas por tipo de descuento
        por_tipo_descuento = {}
        for prestamo in prestamos:
            if prestamo.tipo_descuento_directo:
                tipo = prestamo.tipo_descuento_directo
                por_tipo_descuento[tipo] = por_tipo_descuento.get(tipo, 0) + 1
        
        # Estadísticas por modalidad de pago
        por_modalidad_pago = {}
        for prestamo in prestamos:
            modalidad = prestamo.modalidad_pago
            por_modalidad_pago[modalidad] = por_modalidad_pago.get(modalidad, 0) + 1
        
        # Estadísticas por estado
        por_estado = {}
        for prestamo in prestamos:
            estado = prestamo.estado
            por_estado[estado] = por_estado.get(estado, 0) + 1
        
        # Montos
        prestamos_descuento = [p for p in prestamos if p.requiere_descuento_directo]
        monto_total_descuento = sum(p.monto for p in prestamos_descuento)
        promedio_cuota = sum(p.cuota_mensual for p in prestamos_descuento) / len(prestamos_descuento) if prestamos_descuento else Decimal('0')
        
        # Clasificaciones
        empleados_publicos = len([p for p in prestamos if p.es_empleado_publico])
        empleados_bancarios = len([p for p in prestamos if p.es_empleado_bancario])
        con_garantia = len([p for p in prestamos if p.tiene_garantia])
        
        # Autorizaciones
        autorizados = len([p for p in prestamos if p.descuento_autorizado])
        pendientes_autorizacion = len([p for p in prestamos if p.requiere_descuento_directo and not p.descuento_autorizado])
        
        return EstadisticasDescuentoDirecto(
            total_prestamos=total_prestamos,
            total_con_descuento_directo=con_descuento_directo,
            porcentaje_descuento_directo=float(con_descuento_directo / total_prestamos * 100) if total_prestamos > 0 else 0,
            por_tipo_descuento=por_tipo_descuento,
            por_modalidad_pago=por_modalidad_pago,
            por_estado=por_estado,
            monto_total_descuento_directo=monto_total_descuento,
            promedio_cuota_descuento_directo=promedio_cuota,
            empleados_publicos=empleados_publicos,
            empleados_bancarios=empleados_bancarios,
            con_garantia=con_garantia,
            autorizados=autorizados,
            pendientes_autorizacion=pendientes_autorizacion
        )
    
    def obtener_prestamos_por_vencer(
        self, 
        dias: int = 30,
        sucursal_id: Optional[str] = None
    ) -> List[Prestamo]:
        """Obtener préstamos que vencen en X días"""
        fecha_limite = datetime.now() + timedelta(days=dias)
        
        query = self.db.query(Prestamo).filter(
            and_(
                Prestamo.fecha_vencimiento <= fecha_limite,
                Prestamo.estado.in_([EstadoPrestamo.VIGENTE, EstadoPrestamo.MORA])
            )
        )
        
        if sucursal_id:
            query = query.filter(Prestamo.sucursal_id == sucursal_id)
        
        return query.order_by(Prestamo.fecha_vencimiento).all()
    
    def obtener_prestamos_en_mora(
        self, 
        dias_minimos: int = 1,
        sucursal_id: Optional[str] = None
    ) -> List[Prestamo]:
        """Obtener préstamos en mora"""
        query = self.db.query(Prestamo).filter(Prestamo.estado == EstadoPrestamo.MORA)
        
        if sucursal_id:
            query = query.filter(Prestamo.sucursal_id == sucursal_id)
        
        prestamos = query.all()
        
        # Filtrar por días de mora si se especifica
        if dias_minimos > 1:
            prestamos = [p for p in prestamos if p.dias_mora >= dias_minimos]
        
        return sorted(prestamos, key=lambda x: x.dias_mora, reverse=True)

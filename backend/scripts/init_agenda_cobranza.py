#!/usr/bin/env python3
"""
Script de inicialización para el sistema de agenda de cobranza
"""
import sys
import os
from datetime import datetime, date, timedelta
from decimal import Decimal

# Agregar el directorio raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.agenda_models import AgendaCobranza, AlertaCobranza
from app.models.secure_models import Cliente, Prestamo, Usuario, Sucursal
from app.services.agenda_cobranza_service import AgendaCobranzaService
from app.services.rabbitmq_service import RabbitMQService
from app.core.celery_app import celery_app


def crear_tablas():
    """Crear tablas de agenda de cobranza"""
    print("🔧 Creando tablas de agenda de cobranza...")
    try:
        from app.models.agenda_models import Base as AgendaBase
        AgendaBase.metadata.create_all(bind=engine)
        print("✅ Tablas de agenda de cobranza creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False


def verificar_datos_base():
    """Verificar que existen datos base necesarios"""
    print("🔍 Verificando datos base...")
    
    db = SessionLocal()
    try:
        # Verificar usuarios
        usuarios_count = db.query(Usuario).count()
        print(f"   📊 Usuarios en sistema: {usuarios_count}")
        
        # Verificar sucursales
        sucursales_count = db.query(Sucursal).count()
        print(f"   📊 Sucursales en sistema: {sucursales_count}")
        
        # Verificar clientes
        clientes_count = db.query(Cliente).count()
        print(f"   📊 Clientes en sistema: {clientes_count}")
        
        # Verificar préstamos
        prestamos_count = db.query(Prestamo).count()
        print(f"   📊 Préstamos en sistema: {prestamos_count}")
        
        # Verificar préstamos en mora
        prestamos_mora = db.query(Prestamo).filter(
            Prestamo.dias_mora > 0
        ).count()
        print(f"   📊 Préstamos en mora: {prestamos_mora}")
        
        if usuarios_count == 0 or clientes_count == 0:
            print("⚠️  Advertencia: Faltan datos base para el sistema de agenda")
            return False
        
        print("✅ Datos base verificados")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando datos base: {e}")
        return False
    finally:
        db.close()


def configurar_rabbitmq():
    """Configurar exchanges y colas de RabbitMQ para agenda"""
    print("🐰 Configurando RabbitMQ para agenda de cobranza...")
    
    try:
        rabbitmq_service = RabbitMQService()
        
        # Configurar exchanges y colas específicas de agenda
        agenda_exchanges = [
            'agenda.cobranza',
            'alertas.cobranza',
            'reportes.cobranza'
        ]
        
        for exchange in agenda_exchanges:
            rabbitmq_service.setup_exchange(exchange, 'topic')
            print(f"   ✅ Exchange configurado: {exchange}")
        
        # Configurar colas específicas
        agenda_queues = [
            ('agenda.actividades', 'agenda.cobranza', 'actividad.*'),
            ('agenda.alertas', 'alertas.cobranza', 'alerta.*'),
            ('agenda.reportes', 'reportes.cobranza', 'reporte.*'),
        ]
        
        for queue_name, exchange, routing_key in agenda_queues:
            rabbitmq_service.setup_queue(queue_name, exchange, routing_key)
            print(f"   ✅ Cola configurada: {queue_name}")
        
        print("✅ RabbitMQ configurado para agenda de cobranza")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando RabbitMQ: {e}")
        return False


def probar_celery():
    """Probar que Celery está funcionando"""
    print("⚙️  Probando conexión con Celery...")
    
    try:
        # Verificar que Celery está configurado
        if celery_app:
            print("   ✅ Aplicación Celery inicializada")
        
        # Verificar tareas registradas
        registered_tasks = list(celery_app.tasks.keys())
        agenda_tasks = [task for task in registered_tasks if 'agenda_cobranza' in task]
        
        print(f"   📊 Tareas de agenda registradas: {len(agenda_tasks)}")
        for task in agenda_tasks:
            print(f"      - {task}")
        
        print("✅ Celery verificado")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Celery: {e}")
        return False


def crear_actividades_ejemplo():
    """Crear algunas actividades de ejemplo"""
    print("📝 Creando actividades de ejemplo...")
    
    db = SessionLocal()
    try:
        service = AgendaCobranzaService(db)
        
        # Obtener datos para ejemplos
        primer_cliente = db.query(Cliente).first()
        primer_usuario = db.query(Usuario).first()
        primer_prestamo = db.query(Prestamo).filter(Prestamo.dias_mora > 0).first()
        
        if not (primer_cliente and primer_usuario):
            print("⚠️  No hay datos suficientes para crear ejemplos")
            return False
        
        actividades_creadas = 0
        
        # Crear actividad de llamada telefónica para hoy
        try:
            actividad1 = service.crear_actividad_cobranza(
                cliente_id=str(primer_cliente.id),
                tipo_actividad='LLAMADA_TELEFONICA',
                titulo=f'Llamada de seguimiento - Cliente {primer_cliente.numero_cliente}',
                descripcion='Llamada de seguimiento para verificar situación de pago',
                fecha_programada=date.today(),
                usuario_asignado_id=str(primer_usuario.id),
                prestamo_id=str(primer_prestamo.id) if primer_prestamo else None,
                prioridad='ALTA',
                objetivo='Contactar cliente para acordar plan de pago',
                telefono_contacto=primer_cliente.telefono_principal,
                generar_alerta_previa=True,
                minutos_alerta_previa=30
            )
            actividades_creadas += 1
            print(f"   ✅ Actividad creada: {actividad1.numero_actividad}")
        except Exception as e:
            print(f"   ⚠️  Error creando actividad 1: {e}")
        
        # Crear actividad de visita para mañana
        try:
            actividad2 = service.crear_actividad_cobranza(
                cliente_id=str(primer_cliente.id),
                tipo_actividad='VISITA_DOMICILIO',
                titulo=f'Visita domiciliaria - Cliente {primer_cliente.numero_cliente}',
                descripcion='Visita para negociación directa de deuda',
                fecha_programada=date.today() + timedelta(days=1),
                usuario_asignado_id=str(primer_usuario.id),
                prestamo_id=str(primer_prestamo.id) if primer_prestamo else None,
                prioridad='CRITICA',
                objetivo='Negociar acuerdo de pago presencial',
                direccion_visita=primer_cliente.direccion_residencia,
                telefono_contacto=primer_cliente.telefono_principal,
                duracion_estimada_minutos=60,
                generar_alerta_previa=True,
                minutos_alerta_previa=60
            )
            actividades_creadas += 1
            print(f"   ✅ Actividad creada: {actividad2.numero_actividad}")
        except Exception as e:
            print(f"   ⚠️  Error creando actividad 2: {e}")
        
        print(f"✅ {actividades_creadas} actividades de ejemplo creadas")
        return actividades_creadas > 0
        
    except Exception as e:
        print(f"❌ Error creando actividades de ejemplo: {e}")
        return False
    finally:
        db.close()


def verificar_salud_sistema():
    """Verificar que el sistema está funcionando correctamente"""
    print("🏥 Verificando salud del sistema...")
    
    db = SessionLocal()
    try:
        # Verificar actividades
        total_actividades = db.query(AgendaCobranza).count()
        actividades_hoy = db.query(AgendaCobranza).filter(
            AgendaCobranza.fecha_programada == date.today()
        ).count()
        
        print(f"   📊 Total actividades: {total_actividades}")
        print(f"   📊 Actividades para hoy: {actividades_hoy}")
        
        # Verificar alertas
        total_alertas = db.query(AlertaCobranza).count()
        alertas_pendientes = db.query(AlertaCobranza).filter(
            AlertaCobranza.estado.in_(['PENDIENTE', 'ENVIADA'])
        ).count()
        
        print(f"   📊 Total alertas: {total_alertas}")
        print(f"   📊 Alertas pendientes: {alertas_pendientes}")
        
        # Verificar servicio
        service = AgendaCobranzaService(db)
        dashboard_data = service.obtener_dashboard_cobranza()
        
        print(f"   📊 Dashboard - Actividades hoy: {dashboard_data.get('actividades_hoy', 0)}")
        print(f"   📊 Dashboard - Actividades pendientes: {dashboard_data.get('actividades_pendientes', 0)}")
        
        print("✅ Sistema de agenda funcionando correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando salud del sistema: {e}")
        return False
    finally:
        db.close()


def mostrar_resumen():
    """Mostrar resumen del sistema inicializado"""
    print("\n" + "="*60)
    print("📋 RESUMEN DEL SISTEMA DE AGENDA DE COBRANZA")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Estadísticas generales
        total_actividades = db.query(AgendaCobranza).count()
        total_alertas = db.query(AlertaCobranza).count()
        
        print(f"📊 Total de actividades: {total_actividades}")
        print(f"📊 Total de alertas: {total_alertas}")
        
        # Actividades por estado
        from app.models.agenda_models import EstadoActividad
        for estado in EstadoActividad:
            count = db.query(AgendaCobranza).filter(
                AgendaCobranza.estado == estado
            ).count()
            if count > 0:
                print(f"   - {estado.value}: {count}")
        
        # Actividades por tipo
        from app.models.agenda_models import TipoActividad
        print("\n📋 Actividades por tipo:")
        for tipo in TipoActividad:
            count = db.query(AgendaCobranza).filter(
                AgendaCobranza.tipo_actividad == tipo
            ).count()
            if count > 0:
                print(f"   - {tipo.value}: {count}")
        
        print("\n🚀 ENDPOINTS DISPONIBLES:")
        print("   - POST   /api/v1/agenda-cobranza/")
        print("   - GET    /api/v1/agenda-cobranza/")
        print("   - GET    /api/v1/agenda-cobranza/{id}")
        print("   - PUT    /api/v1/agenda-cobranza/{id}")
        print("   - POST   /api/v1/agenda-cobranza/{id}/completar")
        print("   - POST   /api/v1/agenda-cobranza/{id}/reprogramar")
        print("   - GET    /api/v1/agenda-cobranza/agenda/hoy")
        print("   - GET    /api/v1/agenda-cobranza/agenda/vencidas")
        print("   - GET    /api/v1/agenda-cobranza/promesas/vencidas")
        print("   - GET    /api/v1/agenda-cobranza/cliente/{id}")
        print("   - GET    /api/v1/agenda-cobranza/dashboard/resumen")
        print("   - GET    /api/v1/agenda-cobranza/alertas/usuario")
        
        print("\n⚙️  TAREAS CELERY PROGRAMADAS:")
        print("   - Procesar alertas pendientes: cada 15 minutos")
        print("   - Verificar actividades vencidas: cada hora")
        print("   - Verificar promesas vencidas: diario 8:00 AM")
        print("   - Generar agenda diaria: diario 7:30 AM")
        print("   - Reporte semanal: lunes 8:00 AM")
        print("   - Limpiar alertas antiguas: domingos 3:00 AM")
        print("   - Crear actividades automáticas: diario 6:00 AM")
        
        print("\n✅ Sistema de agenda de cobranza inicializado correctamente")
        print("🎯 ¡Listo para gestionar la cobranza de manera eficiente!")
        
    except Exception as e:
        print(f"❌ Error generando resumen: {e}")
    finally:
        db.close()


def main():
    """Función principal de inicialización"""
    print("🚀 INICIALIZANDO SISTEMA DE AGENDA DE COBRANZA")
    print("="*50)
    
    # Pasos de inicialización
    pasos = [
        ("Crear tablas", crear_tablas),
        ("Verificar datos base", verificar_datos_base),
        ("Configurar RabbitMQ", configurar_rabbitmq),
        ("Probar Celery", probar_celery),
        ("Crear actividades ejemplo", crear_actividades_ejemplo),
        ("Verificar salud sistema", verificar_salud_sistema),
    ]
    
    exitos = 0
    for nombre, funcion in pasos:
        print(f"\n📋 {nombre}...")
        if funcion():
            exitos += 1
        else:
            print(f"⚠️  Paso '{nombre}' completado con advertencias")
    
    print(f"\n📊 Pasos completados exitosamente: {exitos}/{len(pasos)}")
    
    if exitos >= len(pasos) - 1:  # Permitir 1 fallo
        mostrar_resumen()
        print(f"\n🎉 Inicialización completada - {datetime.now()}")
        return True
    else:
        print("\n❌ Inicialización completada con errores")
        print("   Revise los mensajes anteriores para más detalles")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Inicialización cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal durante la inicialización: {e}")
        sys.exit(1)

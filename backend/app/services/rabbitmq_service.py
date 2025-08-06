"""
Servicio RabbitMQ para publicación de eventos del sistema de solicitudes
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQService:
    """Servicio para publicación de eventos en RabbitMQ"""
    
    def __init__(self):
        self.host = getattr(settings, 'RABBITMQ_HOST', 'localhost')
        self.port = getattr(settings, 'RABBITMQ_PORT', 5672)
        self.username = getattr(settings, 'RABBITMQ_USERNAME', 'guest')
        self.password = getattr(settings, 'RABBITMQ_PASSWORD', 'guest')
        self.virtual_host = getattr(settings, 'RABBITMQ_VIRTUAL_HOST', '/')
        
        self.connection = None
        self.channel = None
        
        # Configuración de exchanges
        self.exchanges = {
            'solicitudes': {
                'name': 'solicitudes.events',
                'type': 'topic',
                'durable': True
            },
            'alertas': {
                'name': 'alertas.events',
                'type': 'topic',
                'durable': True
            },
            'sla': {
                'name': 'sla.events',
                'type': 'topic',
                'durable': True
            },
            'notificaciones': {
                'name': 'notificaciones.events',
                'type': 'topic',
                'durable': True
            }
        }
    
    def connect(self) -> bool:
        """
        Establece conexión con RabbitMQ
        """
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declarar exchanges
            self._declare_exchanges()
            
            logger.info("Conexión a RabbitMQ establecida exitosamente")
            return True
            
        except AMQPConnectionError as e:
            logger.error(f"Error conectando a RabbitMQ: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado conectando a RabbitMQ: {str(e)}")
            return False
    
    def disconnect(self):
        """
        Cierra conexión con RabbitMQ
        """
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Conexión a RabbitMQ cerrada")
        except Exception as e:
            logger.error(f"Error cerrando conexión RabbitMQ: {str(e)}")
    
    def _declare_exchanges(self):
        """
        Declara los exchanges necesarios
        """
        try:
            for exchange_config in self.exchanges.values():
                self.channel.exchange_declare(
                    exchange=exchange_config['name'],
                    exchange_type=exchange_config['type'],
                    durable=exchange_config['durable']
                )
            
            logger.info("Exchanges declarados exitosamente")
            
        except AMQPChannelError as e:
            logger.error(f"Error declarando exchanges: {str(e)}")
            raise
    
    def publish_event(
        self,
        exchange_key: str,
        routing_key: str,
        event_data: Dict[str, Any],
        priority: int = 0
    ) -> bool:
        """
        Publica un evento en RabbitMQ
        
        Args:
            exchange_key: Clave del exchange ('solicitudes', 'alertas', etc.)
            routing_key: Routing key para el mensaje
            event_data: Datos del evento
            priority: Prioridad del mensaje (0-255)
        """
        try:
            # Verificar conexión
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False
            
            # Obtener configuración del exchange
            exchange_config = self.exchanges.get(exchange_key)
            if not exchange_config:
                logger.error(f"Exchange '{exchange_key}' no configurado")
                return False
            
            # Preparar mensaje
            message = {
                'event_id': self._generate_event_id(),
                'timestamp': datetime.utcnow().isoformat(),
                'exchange': exchange_key,
                'routing_key': routing_key,
                'data': event_data
            }
            
            # Publicar mensaje
            self.channel.basic_publish(
                exchange=exchange_config['name'],
                routing_key=routing_key,
                body=json.dumps(message, default=str),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Mensaje persistente
                    priority=priority,
                    timestamp=int(datetime.utcnow().timestamp()),
                    content_type='application/json'
                )
            )
            
            logger.info(f"Evento publicado: {exchange_key}.{routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error publicando evento: {str(e)}")
            return False
    
    def publish_solicitud_event(
        self,
        event_type: str,
        solicitud_data: Dict[str, Any],
        priority: int = 0
    ) -> bool:
        """
        Publica eventos relacionados con solicitudes
        
        Tipos de eventos:
        - solicitud.creada
        - solicitud.asignada
        - solicitud.actualizada
        - solicitud.completada
        - solicitud.vencida
        """
        routing_key = f"solicitud.{event_type}"
        return self.publish_event('solicitudes', routing_key, solicitud_data, priority)
    
    def publish_alerta_event(
        self,
        event_type: str,
        alerta_data: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """
        Publica eventos relacionados con alertas
        
        Tipos de eventos:
        - alerta.creada
        - alerta.enviada
        - alerta.leida
        - alerta.atendida
        - alerta.vencida
        """
        routing_key = f"alerta.{event_type}"
        return self.publish_event('alertas', routing_key, alerta_data, priority)
    
    def publish_sla_event(
        self,
        event_type: str,
        sla_data: Dict[str, Any],
        priority: int = 8
    ) -> bool:
        """
        Publica eventos relacionados con SLA
        
        Tipos de eventos:
        - sla.75_porciento
        - sla.90_porciento
        - sla.vencido
        - sla.cumplido
        """
        routing_key = f"sla.{event_type}"
        return self.publish_event('sla', routing_key, sla_data, priority)
    
    def publish_notificacion_event(
        self,
        event_type: str,
        notificacion_data: Dict[str, Any],
        priority: int = 3
    ) -> bool:
        """
        Publica eventos relacionados con notificaciones
        
        Tipos de eventos:
        - notificacion.email_enviado
        - notificacion.sms_enviado
        - notificacion.push_enviado
        - notificacion.error_envio
        """
        routing_key = f"notificacion.{event_type}"
        return self.publish_event('notificaciones', routing_key, notificacion_data, priority)
    
    def _generate_event_id(self) -> str:
        """
        Genera un ID único para el evento
        """
        import uuid
        return str(uuid.uuid4())
    
    def create_queue_binding(
        self,
        queue_name: str,
        exchange_key: str,
        routing_key: str,
        durable: bool = True
    ) -> bool:
        """
        Crea una cola y la vincula a un exchange
        """
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False
            
            exchange_config = self.exchanges.get(exchange_key)
            if not exchange_config:
                logger.error(f"Exchange '{exchange_key}' no configurado")
                return False
            
            # Declarar cola
            self.channel.queue_declare(queue=queue_name, durable=durable)
            
            # Vincular cola al exchange
            self.channel.queue_bind(
                exchange=exchange_config['name'],
                queue=queue_name,
                routing_key=routing_key
            )
            
            logger.info(f"Cola '{queue_name}' vinculada a '{exchange_key}' con routing key '{routing_key}'")
            return True
            
        except Exception as e:
            logger.error(f"Error creando binding de cola: {str(e)}")
            return False
    
    def setup_default_queues(self) -> bool:
        """
        Configura las colas por defecto del sistema
        """
        try:
            # Colas para solicitudes
            queues_config = [
                # Solicitudes
                ('solicitudes.procesamiento', 'solicitudes', 'solicitud.*'),
                ('solicitudes.alta_prioridad', 'solicitudes', 'solicitud.*.alta'),
                ('solicitudes.vencidas', 'solicitudes', 'solicitud.vencida'),
                
                # Alertas
                ('alertas.criticas', 'alertas', 'alerta.*.critica'),
                ('alertas.procesamiento', 'alertas', 'alerta.*'),
                
                # SLA
                ('sla.monitoreo', 'sla', 'sla.*'),
                ('sla.vencimientos', 'sla', 'sla.vencido'),
                
                # Notificaciones
                ('notificaciones.email', 'notificaciones', 'notificacion.email_*'),
                ('notificaciones.sms', 'notificaciones', 'notificacion.sms_*'),
                ('notificaciones.push', 'notificaciones', 'notificacion.push_*'),
                ('notificaciones.errores', 'notificaciones', 'notificacion.error_*')
            ]
            
            for queue_name, exchange_key, routing_key in queues_config:
                self.create_queue_binding(queue_name, exchange_key, routing_key)
            
            logger.info("Colas por defecto configuradas exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando colas por defecto: {str(e)}")
            return False
    
    def get_queue_info(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una cola
        """
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return None
            
            method = self.channel.queue_declare(queue=queue_name, passive=True)
            
            return {
                'queue': queue_name,
                'message_count': method.method.message_count,
                'consumer_count': method.method.consumer_count
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de cola '{queue_name}': {str(e)}")
            return None
    
    def purge_queue(self, queue_name: str) -> bool:
        """
        Limpia todos los mensajes de una cola
        """
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False
            
            self.channel.queue_purge(queue=queue_name)
            logger.info(f"Cola '{queue_name}' limpiada exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error limpiando cola '{queue_name}': {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica el estado de la conexión RabbitMQ
        """
        try:
            if not self.connection or self.connection.is_closed:
                connected = self.connect()
            else:
                connected = True
            
            if connected:
                # Verificar que podemos declarar un exchange temporal
                test_exchange = 'health_check_temp'
                self.channel.exchange_declare(
                    exchange=test_exchange,
                    exchange_type='direct',
                    durable=False,
                    auto_delete=True
                )
                self.channel.exchange_delete(exchange=test_exchange)
                
                return {
                    'status': 'healthy',
                    'connected': True,
                    'host': self.host,
                    'port': self.port,
                    'virtual_host': self.virtual_host,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'status': 'unhealthy',
                    'connected': False,
                    'error': 'No se pudo establecer conexión',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Instancia global del servicio
rabbitmq_service = RabbitMQService()

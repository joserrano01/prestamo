"""
Servicio de mensajería asíncrona con RabbitMQ
Maneja notificaciones, procesamiento de documentos y tareas en segundo plano
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import structlog
import aio_pika
from aio_pika import Message, DeliveryMode
from aio_pika.abc import AbstractConnection, AbstractChannel, AbstractQueue

from app.core.config import settings

logger = structlog.get_logger(__name__)

class MessagingService:
    """Servicio de mensajería asíncrona con RabbitMQ"""
    
    def __init__(self):
        self.connection: Optional[AbstractConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.queues: Dict[str, AbstractQueue] = {}
        
        # Nombres de colas
        self.LOAN_NOTIFICATIONS_QUEUE = "loan_notifications"
        self.DOCUMENT_PROCESSING_QUEUE = "document_processing"
        self.EMAIL_QUEUE = "email_notifications"
        self.SMS_QUEUE = "sms_notifications"
        self.AUDIT_QUEUE = "audit_logs"
        self.SEARCH_INDEXING_QUEUE = "search_indexing"
        self.BACKUP_QUEUE = "backup_tasks"
        
        # Exchanges
        self.NOTIFICATIONS_EXCHANGE = "notifications"
        self.PROCESSING_EXCHANGE = "processing"
        self.AUDIT_EXCHANGE = "audit"
    
    async def connect(self):
        """Establecer conexión con RabbitMQ"""
        try:
            self.connection = await aio_pika.connect_robust(
                url=settings.RABBITMQ_URL,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=10)
            
            # Configurar exchanges y colas
            await self._setup_exchanges()
            await self._setup_queues()
            
            logger.info("Conexión a RabbitMQ establecida correctamente")
            
        except Exception as e:
            logger.error("Error conectando a RabbitMQ", error=str(e))
            raise
    
    async def disconnect(self):
        """Cerrar conexión con RabbitMQ"""
        try:
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            logger.info("Conexión a RabbitMQ cerrada")
        except Exception as e:
            logger.error("Error cerrando conexión RabbitMQ", error=str(e))
    
    async def _setup_exchanges(self):
        """Configurar exchanges de RabbitMQ"""
        # Exchange para notificaciones
        self.notifications_exchange = await self.channel.declare_exchange(
            self.NOTIFICATIONS_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        # Exchange para procesamiento
        self.processing_exchange = await self.channel.declare_exchange(
            self.PROCESSING_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Exchange para auditoría
        self.audit_exchange = await self.channel.declare_exchange(
            self.AUDIT_EXCHANGE,
            aio_pika.ExchangeType.FANOUT,
            durable=True
        )
    
    async def _setup_queues(self):
        """Configurar colas de RabbitMQ"""
        # Cola de notificaciones de préstamos
        self.queues[self.LOAN_NOTIFICATIONS_QUEUE] = await self.channel.declare_queue(
            self.LOAN_NOTIFICATIONS_QUEUE,
            durable=True,
            arguments={"x-message-ttl": 86400000}  # TTL de 24 horas
        )
        await self.queues[self.LOAN_NOTIFICATIONS_QUEUE].bind(
            self.notifications_exchange, 
            "loan.*"
        )
        
        # Cola de procesamiento de documentos
        self.queues[self.DOCUMENT_PROCESSING_QUEUE] = await self.channel.declare_queue(
            self.DOCUMENT_PROCESSING_QUEUE,
            durable=True,
            arguments={
                "x-message-ttl": 3600000,  # TTL de 1 hora
                "x-max-retries": 3
            }
        )
        await self.queues[self.DOCUMENT_PROCESSING_QUEUE].bind(
            self.processing_exchange,
            self.DOCUMENT_PROCESSING_QUEUE
        )
        
        # Cola de emails
        self.queues[self.EMAIL_QUEUE] = await self.channel.declare_queue(
            self.EMAIL_QUEUE,
            durable=True,
            arguments={"x-message-ttl": 3600000}
        )
        await self.queues[self.EMAIL_QUEUE].bind(
            self.notifications_exchange,
            "email.*"
        )
        
        # Cola de SMS
        self.queues[self.SMS_QUEUE] = await self.channel.declare_queue(
            self.SMS_QUEUE,
            durable=True,
            arguments={"x-message-ttl": 1800000}  # TTL de 30 minutos
        )
        await self.queues[self.SMS_QUEUE].bind(
            self.notifications_exchange,
            "sms.*"
        )
        
        # Cola de auditoría
        self.queues[self.AUDIT_QUEUE] = await self.channel.declare_queue(
            self.AUDIT_QUEUE,
            durable=True
        )
        await self.queues[self.AUDIT_QUEUE].bind(
            self.audit_exchange
        )
        
        # Cola de indexación de búsqueda
        self.queues[self.SEARCH_INDEXING_QUEUE] = await self.channel.declare_queue(
            self.SEARCH_INDEXING_QUEUE,
            durable=True
        )
        await self.queues[self.SEARCH_INDEXING_QUEUE].bind(
            self.processing_exchange,
            self.SEARCH_INDEXING_QUEUE
        )
        
        # Cola de respaldos
        self.queues[self.BACKUP_QUEUE] = await self.channel.declare_queue(
            self.BACKUP_QUEUE,
            durable=True
        )
        await self.queues[self.BACKUP_QUEUE].bind(
            self.processing_exchange,
            self.BACKUP_QUEUE
        )
    
    async def publish_loan_notification(
        self, 
        loan_id: str, 
        event_type: str, 
        data: Dict[str, Any]
    ):
        """Publicar notificación de préstamo"""
        try:
            message_data = {
                "loan_id": loan_id,
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "loan_service"
            }
            
            message = Message(
                json.dumps(message_data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "loan_id": loan_id,
                    "event_type": event_type,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            routing_key = f"loan.{event_type}"
            await self.notifications_exchange.publish(message, routing_key)
            
            logger.info("Notificación de préstamo publicada", 
                       loan_id=loan_id, 
                       event_type=event_type)
            
        except Exception as e:
            logger.error("Error publicando notificación de préstamo", 
                        loan_id=loan_id, 
                        event_type=event_type, 
                        error=str(e))
    
    async def publish_document_processing(
        self, 
        document_id: str, 
        processing_type: str, 
        data: Dict[str, Any]
    ):
        """Publicar tarea de procesamiento de documento"""
        try:
            message_data = {
                "document_id": document_id,
                "processing_type": processing_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "priority": data.get("priority", "normal")
            }
            
            message = Message(
                json.dumps(message_data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=self._get_message_priority(data.get("priority", "normal")),
                headers={
                    "document_id": document_id,
                    "processing_type": processing_type
                }
            )
            
            await self.processing_exchange.publish(
                message, 
                self.DOCUMENT_PROCESSING_QUEUE
            )
            
            logger.info("Tarea de procesamiento de documento publicada", 
                       document_id=document_id, 
                       processing_type=processing_type)
            
        except Exception as e:
            logger.error("Error publicando procesamiento de documento", 
                        document_id=document_id, 
                        error=str(e))
    
    async def publish_email_notification(
        self, 
        recipient: str, 
        subject: str, 
        template: str, 
        data: Dict[str, Any]
    ):
        """Publicar notificación por email"""
        try:
            message_data = {
                "recipient": recipient,
                "subject": subject,
                "template": template,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "priority": data.get("priority", "normal")
            }
            
            message = Message(
                json.dumps(message_data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "recipient": recipient,
                    "template": template
                }
            )
            
            routing_key = f"email.{data.get('category', 'general')}"
            await self.notifications_exchange.publish(message, routing_key)
            
            logger.info("Notificación de email publicada", 
                       recipient=recipient, 
                       template=template)
            
        except Exception as e:
            logger.error("Error publicando notificación de email", 
                        recipient=recipient, 
                        error=str(e))
    
    async def publish_audit_log(self, audit_data: Dict[str, Any]):
        """Publicar log de auditoría"""
        try:
            message_data = {
                **audit_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "audit_service"
            }
            
            message = Message(
                json.dumps(message_data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await self.audit_exchange.publish(message, "")
            
            logger.debug("Log de auditoría publicado", 
                        action=audit_data.get("action"))
            
        except Exception as e:
            logger.error("Error publicando log de auditoría", error=str(e))
    
    async def publish_search_indexing(
        self, 
        entity_type: str, 
        entity_id: str, 
        action: str, 
        data: Dict[str, Any]
    ):
        """Publicar tarea de indexación de búsqueda"""
        try:
            message_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,  # create, update, delete
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            message = Message(
                json.dumps(message_data).encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                headers={
                    "entity_type": entity_type,
                    "action": action
                }
            )
            
            await self.processing_exchange.publish(
                message, 
                self.SEARCH_INDEXING_QUEUE
            )
            
            logger.info("Tarea de indexación publicada", 
                       entity_type=entity_type, 
                       entity_id=entity_id, 
                       action=action)
            
        except Exception as e:
            logger.error("Error publicando indexación", 
                        entity_type=entity_type, 
                        entity_id=entity_id, 
                        error=str(e))
    
    async def start_consumer(self, queue_name: str, callback: Callable):
        """Iniciar consumidor para una cola específica"""
        try:
            if queue_name not in self.queues:
                raise ValueError(f"Cola {queue_name} no configurada")
            
            queue = self.queues[queue_name]
            
            async def process_message(message):
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        await callback(body, message)
                        logger.debug("Mensaje procesado correctamente", 
                                   queue=queue_name)
                    except Exception as e:
                        logger.error("Error procesando mensaje", 
                                   queue=queue_name, 
                                   error=str(e))
                        raise
            
            await queue.consume(process_message)
            
            logger.info("Consumidor iniciado", queue=queue_name)
            
        except Exception as e:
            logger.error("Error iniciando consumidor", 
                        queue=queue_name, 
                        error=str(e))
            raise
    
    def _get_message_priority(self, priority_str: str) -> int:
        """Convertir prioridad string a número"""
        priority_map = {
            "low": 1,
            "normal": 5,
            "high": 8,
            "urgent": 10
        }
        return priority_map.get(priority_str.lower(), 5)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de las colas"""
        try:
            stats = {}
            
            for queue_name, queue in self.queues.items():
                queue_info = await queue.declare(passive=True)
                stats[queue_name] = {
                    "message_count": queue_info.message_count,
                    "consumer_count": queue_info.consumer_count
                }
            
            return stats
            
        except Exception as e:
            logger.error("Error obteniendo estadísticas de colas", error=str(e))
            return {}

# Instancia global del servicio de mensajería
messaging_service = MessagingService()

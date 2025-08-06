"""
Servicio de notificaciones para alertas de solicitudes
"""
import smtplib
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import requests
from jinja2 import Template

from app.core.config import settings
from app.models.secure_models import SolicitudAlerta, Usuario, Cliente

logger = logging.getLogger(__name__)


class NotificationService:
    """Servicio para envío de notificaciones por múltiples canales"""
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'localhost')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@financepro.com')
        
        # Configuración SMS
        self.sms_provider_url = getattr(settings, 'SMS_PROVIDER_URL', '')
        self.sms_api_key = getattr(settings, 'SMS_API_KEY', '')
        
        # Configuración Push Notifications
        self.push_service_url = getattr(settings, 'PUSH_SERVICE_URL', '')
        self.push_api_key = getattr(settings, 'PUSH_API_KEY', '')
    
    def enviar_alerta(self, alerta: SolicitudAlerta) -> Dict[str, Any]:
        """
        Envía una alerta por los canales configurados
        """
        resultados = {
            'email': {'enviado': False, 'error': None},
            'sms': {'enviado': False, 'error': None},
            'push': {'enviado': False, 'error': None}
        }
        
        try:
            # Obtener datos del usuario destinatario
            usuario = alerta.usuario_destinatario
            if not usuario:
                raise ValueError("Usuario destinatario no encontrado")
            
            # Preparar contexto para templates
            contexto = self._preparar_contexto_alerta(alerta)
            
            # Enviar por email
            if alerta.enviar_email and usuario.email:
                try:
                    self._enviar_email(usuario.email, alerta, contexto)
                    resultados['email']['enviado'] = True
                    logger.info(f"Email enviado a {usuario.email} para alerta {alerta.id}")
                except Exception as e:
                    resultados['email']['error'] = str(e)
                    logger.error(f"Error enviando email: {str(e)}")
            
            # Enviar por SMS
            if alerta.enviar_sms and usuario.telefono:
                try:
                    self._enviar_sms(usuario.telefono, alerta, contexto)
                    resultados['sms']['enviado'] = True
                    logger.info(f"SMS enviado a {usuario.telefono} para alerta {alerta.id}")
                except Exception as e:
                    resultados['sms']['error'] = str(e)
                    logger.error(f"Error enviando SMS: {str(e)}")
            
            # Enviar push notification
            if alerta.enviar_push:
                try:
                    self._enviar_push_notification(usuario, alerta, contexto)
                    resultados['push']['enviado'] = True
                    logger.info(f"Push notification enviada a usuario {usuario.id}")
                except Exception as e:
                    resultados['push']['error'] = str(e)
                    logger.error(f"Error enviando push notification: {str(e)}")
            
            # Actualizar alerta
            alerta.fecha_enviada = datetime.utcnow()
            alerta.intentos_envio += 1
            
            # Determinar estado final
            if any(r['enviado'] for r in resultados.values()):
                alerta.estado = 'ENVIADA'
                alerta.error_envio = None
            else:
                errores = [r['error'] for r in resultados.values() if r['error']]
                alerta.error_envio = '; '.join(errores)
            
            alerta.ultimo_intento = datetime.utcnow()
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error general enviando alerta {alerta.id}: {str(e)}")
            alerta.error_envio = str(e)
            alerta.ultimo_intento = datetime.utcnow()
            alerta.intentos_envio += 1
            
            return {
                'email': {'enviado': False, 'error': str(e)},
                'sms': {'enviado': False, 'error': str(e)},
                'push': {'enviado': False, 'error': str(e)}
            }
    
    def _enviar_email(self, destinatario: str, alerta: SolicitudAlerta, contexto: Dict):
        """
        Envía notificación por email
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['Subject'] = alerta.titulo
            msg['From'] = self.from_email
            msg['To'] = destinatario
            
            # Generar contenido HTML
            html_content = self._generar_template_email(alerta, contexto)
            
            # Generar contenido texto plano
            text_content = self._generar_template_texto(alerta, contexto)
            
            # Adjuntar contenido
            part1 = MIMEText(text_content, 'plain', 'utf-8')
            part2 = MIMEText(html_content, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
            
        except Exception as e:
            logger.error(f"Error enviando email a {destinatario}: {str(e)}")
            raise
    
    def _enviar_sms(self, telefono: str, alerta: SolicitudAlerta, contexto: Dict):
        """
        Envía notificación por SMS
        """
        if not self.sms_provider_url or not self.sms_api_key:
            raise ValueError("Configuración SMS no disponible")
        
        try:
            # Generar mensaje SMS (máximo 160 caracteres)
            mensaje = self._generar_mensaje_sms(alerta, contexto)
            
            # Preparar datos para API
            data = {
                'to': telefono,
                'message': mensaje,
                'api_key': self.sms_api_key
            }
            
            # Enviar SMS
            response = requests.post(
                self.sms_provider_url,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValueError(f"Error del proveedor SMS: {response.status_code}")
            
            result = response.json()
            if not result.get('success', False):
                raise ValueError(f"SMS no enviado: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error enviando SMS a {telefono}: {str(e)}")
            raise
    
    def _enviar_push_notification(self, usuario: Usuario, alerta: SolicitudAlerta, contexto: Dict):
        """
        Envía push notification
        """
        if not self.push_service_url or not self.push_api_key:
            raise ValueError("Configuración Push Notifications no disponible")
        
        try:
            # Preparar datos para push notification
            data = {
                'user_id': str(usuario.id),
                'title': alerta.titulo,
                'body': alerta.mensaje,
                'data': {
                    'alerta_id': str(alerta.id),
                    'solicitud_id': str(alerta.solicitud_id),
                    'tipo_alerta': alerta.tipo_alerta,
                    'nivel_urgencia': alerta.nivel_urgencia
                },
                'api_key': self.push_api_key
            }
            
            # Enviar push notification
            response = requests.post(
                self.push_service_url,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValueError(f"Error del servicio Push: {response.status_code}")
            
            result = response.json()
            if not result.get('success', False):
                raise ValueError(f"Push no enviada: {result.get('error', 'Error desconocido')}")
            
        except Exception as e:
            logger.error(f"Error enviando push notification: {str(e)}")
            raise
    
    def _preparar_contexto_alerta(self, alerta: SolicitudAlerta) -> Dict[str, Any]:
        """
        Prepara el contexto para los templates de notificación
        """
        solicitud = alerta.solicitud
        cliente = solicitud.cliente if solicitud else None
        usuario = alerta.usuario_destinatario
        
        return {
            'alerta': {
                'id': str(alerta.id),
                'titulo': alerta.titulo,
                'mensaje': alerta.mensaje,
                'tipo_alerta': alerta.tipo_alerta,
                'nivel_urgencia': alerta.nivel_urgencia,
                'fecha_programada': alerta.fecha_programada
            },
            'solicitud': {
                'id': str(solicitud.id) if solicitud else None,
                'numero_solicitud': solicitud.numero_solicitud if solicitud else None,
                'tipo_solicitud': solicitud.nombre_tipo_legible if solicitud else None,
                'estado': solicitud.nombre_estado_legible if solicitud else None,
                'fecha_limite': solicitud.fecha_limite_respuesta if solicitud else None,
                'horas_restantes': solicitud.horas_restantes_sla if solicitud else None,
                'porcentaje_sla': solicitud.porcentaje_sla_consumido if solicitud else None
            } if solicitud else None,
            'cliente': {
                'nombres': cliente.nombres if cliente else None,
                'apellidos': cliente.apellidos if cliente else None,
                'cedula': cliente.cedula if cliente else None,
                'telefono': cliente.telefono if cliente else None
            } if cliente else None,
            'usuario': {
                'nombres': usuario.nombres if usuario else None,
                'apellidos': usuario.apellidos if usuario else None,
                'email': usuario.email if usuario else None
            } if usuario else None,
            'sistema': {
                'nombre': 'FinancePro',
                'url': getattr(settings, 'FRONTEND_URL', 'https://app.financepro.com'),
                'fecha_envio': datetime.utcnow().strftime('%d/%m/%Y %H:%M')
            }
        }
    
    def _generar_template_email(self, alerta: SolicitudAlerta, contexto: Dict) -> str:
        """
        Genera template HTML para email
        """
        template_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{{ alerta.titulo }}</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #007bff; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .alert-high { border-left: 4px solid #dc3545; }
                .alert-medium { border-left: 4px solid #ffc107; }
                .alert-low { border-left: 4px solid #28a745; }
                .alert-critical { border-left: 4px solid #6f42c1; }
                .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
                .button { display: inline-block; padding: 10px 20px; background: #007bff; 
                         color: white; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{{ sistema.nombre }}</h1>
                    <h2>{{ alerta.titulo }}</h2>
                </div>
                
                <div class="content alert-{{ alerta.nivel_urgencia|lower }}">
                    <h3>Detalles de la Alerta</h3>
                    <p><strong>Tipo:</strong> {{ alerta.tipo_alerta }}</p>
                    <p><strong>Nivel de Urgencia:</strong> {{ alerta.nivel_urgencia }}</p>
                    <p><strong>Fecha:</strong> {{ sistema.fecha_envio }}</p>
                    
                    {% if solicitud %}
                    <h3>Información de la Solicitud</h3>
                    <p><strong>Número:</strong> {{ solicitud.numero_solicitud }}</p>
                    <p><strong>Tipo:</strong> {{ solicitud.tipo_solicitud }}</p>
                    <p><strong>Estado:</strong> {{ solicitud.estado }}</p>
                    {% if solicitud.horas_restantes %}
                    <p><strong>Horas Restantes SLA:</strong> {{ solicitud.horas_restantes }}</p>
                    <p><strong>% SLA Consumido:</strong> {{ solicitud.porcentaje_sla }}%</p>
                    {% endif %}
                    {% endif %}
                    
                    {% if cliente %}
                    <h3>Cliente</h3>
                    <p><strong>Nombre:</strong> {{ cliente.nombres }} {{ cliente.apellidos }}</p>
                    <p><strong>Cédula:</strong> {{ cliente.cedula }}</p>
                    {% endif %}
                    
                    <h3>Mensaje</h3>
                    <p>{{ alerta.mensaje }}</p>
                    
                    <p style="text-align: center; margin-top: 30px;">
                        <a href="{{ sistema.url }}" class="button">Acceder al Sistema</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>Este es un mensaje automático de {{ sistema.nombre }}.</p>
                    <p>Por favor no responda a este email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_html)
        return template.render(**contexto)
    
    def _generar_template_texto(self, alerta: SolicitudAlerta, contexto: Dict) -> str:
        """
        Genera template de texto plano para email
        """
        template_texto = """
{{ sistema.nombre }}
{{ alerta.titulo }}

Detalles de la Alerta:
- Tipo: {{ alerta.tipo_alerta }}
- Nivel de Urgencia: {{ alerta.nivel_urgencia }}
- Fecha: {{ sistema.fecha_envio }}

{% if solicitud %}
Información de la Solicitud:
- Número: {{ solicitud.numero_solicitud }}
- Tipo: {{ solicitud.tipo_solicitud }}
- Estado: {{ solicitud.estado }}
{% if solicitud.horas_restantes %}
- Horas Restantes SLA: {{ solicitud.horas_restantes }}
- % SLA Consumido: {{ solicitud.porcentaje_sla }}%
{% endif %}
{% endif %}

{% if cliente %}
Cliente:
- Nombre: {{ cliente.nombres }} {{ cliente.apellidos }}
- Cédula: {{ cliente.cedula }}
{% endif %}

Mensaje:
{{ alerta.mensaje }}

Acceder al sistema: {{ sistema.url }}

---
Este es un mensaje automático de {{ sistema.nombre }}.
Por favor no responda a este email.
        """
        
        template = Template(template_texto)
        return template.render(**contexto)
    
    def _generar_mensaje_sms(self, alerta: SolicitudAlerta, contexto: Dict) -> str:
        """
        Genera mensaje SMS (máximo 160 caracteres)
        """
        solicitud = contexto.get('solicitud', {})
        
        if solicitud and solicitud.get('numero_solicitud'):
            mensaje = f"FinancePro: {alerta.tipo_alerta} - Sol. {solicitud['numero_solicitud']}. "
            if solicitud.get('horas_restantes'):
                mensaje += f"SLA: {solicitud['horas_restantes']}h restantes. "
        else:
            mensaje = f"FinancePro: {alerta.titulo}. "
        
        # Truncar si es muy largo
        if len(mensaje) > 140:
            mensaje = mensaje[:137] + "..."
        
        mensaje += " Ver app."
        
        return mensaje
    
    def enviar_notificacion_personalizada(
        self,
        destinatarios: List[str],
        titulo: str,
        mensaje: str,
        canales: List[str] = ['email'],
        datos_adicionales: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Envía notificación personalizada a múltiples destinatarios
        """
        resultados = []
        
        for destinatario in destinatarios:
            resultado = {
                'destinatario': destinatario,
                'canales': {}
            }
            
            try:
                if 'email' in canales:
                    # Implementar envío de email personalizado
                    pass
                
                if 'sms' in canales:
                    # Implementar envío de SMS personalizado
                    pass
                
                if 'push' in canales:
                    # Implementar envío de push personalizado
                    pass
                
            except Exception as e:
                logger.error(f"Error enviando notificación personalizada: {str(e)}")
            
            resultados.append(resultado)
        
        return {
            'total_destinatarios': len(destinatarios),
            'resultados': resultados
        }
    
    def obtener_estadisticas_envios(
        self,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de envíos de notificaciones
        """
        # Esta función se implementaría consultando la base de datos
        # de alertas para generar estadísticas de envío
        return {
            'total_alertas': 0,
            'enviadas_exitosamente': 0,
            'errores_envio': 0,
            'por_canal': {
                'email': {'enviadas': 0, 'errores': 0},
                'sms': {'enviadas': 0, 'errores': 0},
                'push': {'enviadas': 0, 'errores': 0}
            },
            'por_tipo_alerta': {},
            'por_nivel_urgencia': {}
        }

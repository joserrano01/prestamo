"""
Servicio de búsqueda de texto completo con Meilisearch
Proporciona capacidades avanzadas de búsqueda para clientes, préstamos y documentos
"""

import asyncio
from typing import List, Dict, Any, Optional
import structlog
from meilisearch_python_async import Client as AsyncClient
from meilisearch import Client

from app.core.config import settings
from app.core.security import mask_sensitive_data

logger = structlog.get_logger(__name__)

class SearchService:
    """Servicio de búsqueda de texto completo con Meilisearch"""
    
    def __init__(self):
        self.client = AsyncClient(
            url=settings.MEILISEARCH_URL,
            api_key=settings.MEILISEARCH_MASTER_KEY
        )
        self.sync_client = Client(
            url=settings.MEILISEARCH_URL,
            api_key=settings.MEILISEARCH_MASTER_KEY
        )
        
        # Nombres de índices
        self.clients_index = f"{settings.MEILISEARCH_INDEX_PREFIX}_clients"
        self.loans_index = f"{settings.MEILISEARCH_INDEX_PREFIX}_loans"
        self.documents_index = f"{settings.MEILISEARCH_INDEX_PREFIX}_documents"
        self.users_index = f"{settings.MEILISEARCH_INDEX_PREFIX}_users"
    
    async def initialize_indexes(self):
        """Inicializar todos los índices de búsqueda"""
        try:
            # Configurar índice de clientes
            await self._setup_clients_index()
            
            # Configurar índice de préstamos
            await self._setup_loans_index()
            
            # Configurar índice de documentos
            await self._setup_documents_index()
            
            # Configurar índice de usuarios
            await self._setup_users_index()
            
            logger.info("Índices de búsqueda inicializados correctamente")
            
        except Exception as e:
            logger.error("Error inicializando índices de búsqueda", error=str(e))
            raise
    
    async def _setup_clients_index(self):
        """Configurar índice de clientes"""
        index = await self.client.create_index(
            uid=self.clients_index,
            primary_key="id"
        )
        
        # Configurar campos de búsqueda
        await index.update_searchable_attributes([
            "nombre_completo",
            "email", 
            "rfc_masked",
            "curp_masked",
            "telefono_masked",
            "direccion_masked",
            "ocupacion",
            "empresa",
            "referencias_personales"
        ])
        
        # Configurar campos de filtrado
        await index.update_filterable_attributes([
            "sucursal_id",
            "estado",
            "fecha_registro",
            "score_crediticio",
            "activo"
        ])
        
        # Configurar campos de ordenamiento
        await index.update_sortable_attributes([
            "fecha_registro",
            "score_crediticio",
            "nombre_completo"
        ])
    
    async def _setup_loans_index(self):
        """Configurar índice de préstamos"""
        index = await self.client.create_index(
            uid=self.loans_index,
            primary_key="id"
        )
        
        await index.update_searchable_attributes([
            "numero_prestamo",
            "cliente_nombre",
            "tipo_prestamo",
            "proposito",
            "observaciones",
            "garantias"
        ])
        
        await index.update_filterable_attributes([
            "cliente_id",
            "sucursal_id",
            "estado",
            "fecha_solicitud",
            "fecha_aprobacion",
            "monto_solicitado",
            "monto_aprobado",
            "tasa_interes",
            "plazo_meses"
        ])
        
        await index.update_sortable_attributes([
            "fecha_solicitud",
            "fecha_aprobacion",
            "monto_aprobado",
            "tasa_interes"
        ])
    
    async def _setup_documents_index(self):
        """Configurar índice de documentos"""
        index = await self.client.create_index(
            uid=self.documents_index,
            primary_key="id"
        )
        
        await index.update_searchable_attributes([
            "nombre_archivo",
            "tipo_documento",
            "descripcion",
            "contenido_extraido",
            "tags"
        ])
        
        await index.update_filterable_attributes([
            "cliente_id",
            "prestamo_id",
            "tipo_documento",
            "fecha_subida",
            "tamaño_archivo",
            "verificado"
        ])
    
    async def _setup_users_index(self):
        """Configurar índice de usuarios"""
        index = await self.client.create_index(
            uid=self.users_index,
            primary_key="id"
        )
        
        await index.update_searchable_attributes([
            "nombre_completo",
            "email",
            "username",
            "sucursal_nombre",
            "rol"
        ])
        
        await index.update_filterable_attributes([
            "sucursal_id",
            "rol",
            "activo",
            "fecha_ultimo_acceso",
            "require_2fa"
        ])
    
    async def index_client(self, client_data: Dict[str, Any]):
        """Indexar un cliente para búsqueda"""
        try:
            # Enmascarar datos sensibles antes de indexar
            searchable_data = {
                "id": client_data["id"],
                "nombre_completo": client_data.get("nombre_completo", ""),
                "email": client_data.get("email", ""),
                "rfc_masked": mask_sensitive_data(client_data.get("rfc", ""), "rfc"),
                "curp_masked": mask_sensitive_data(client_data.get("curp", ""), "curp"),
                "telefono_masked": mask_sensitive_data(client_data.get("telefono", ""), "phone"),
                "direccion_masked": mask_sensitive_data(client_data.get("direccion", ""), "address"),
                "ocupacion": client_data.get("ocupacion", ""),
                "empresa": client_data.get("empresa", ""),
                "sucursal_id": client_data.get("sucursal_id"),
                "estado": client_data.get("estado", ""),
                "fecha_registro": client_data.get("fecha_registro"),
                "score_crediticio": client_data.get("score_crediticio"),
                "activo": client_data.get("activo", True),
                "referencias_personales": client_data.get("referencias_personales", "")
            }
            
            index = await self.client.get_index(self.clients_index)
            await index.add_documents([searchable_data])
            
            logger.info("Cliente indexado para búsqueda", client_id=client_data["id"])
            
        except Exception as e:
            logger.error("Error indexando cliente", client_id=client_data.get("id"), error=str(e))
    
    async def index_loan(self, loan_data: Dict[str, Any]):
        """Indexar un préstamo para búsqueda"""
        try:
            searchable_data = {
                "id": loan_data["id"],
                "numero_prestamo": loan_data.get("numero_prestamo", ""),
                "cliente_id": loan_data.get("cliente_id"),
                "cliente_nombre": loan_data.get("cliente_nombre", ""),
                "tipo_prestamo": loan_data.get("tipo_prestamo", ""),
                "proposito": loan_data.get("proposito", ""),
                "observaciones": loan_data.get("observaciones", ""),
                "garantias": loan_data.get("garantias", ""),
                "sucursal_id": loan_data.get("sucursal_id"),
                "estado": loan_data.get("estado", ""),
                "fecha_solicitud": loan_data.get("fecha_solicitud"),
                "fecha_aprobacion": loan_data.get("fecha_aprobacion"),
                "monto_solicitado": loan_data.get("monto_solicitado"),
                "monto_aprobado": loan_data.get("monto_aprobado"),
                "tasa_interes": loan_data.get("tasa_interes"),
                "plazo_meses": loan_data.get("plazo_meses")
            }
            
            index = await self.client.get_index(self.loans_index)
            await index.add_documents([searchable_data])
            
            logger.info("Préstamo indexado para búsqueda", loan_id=loan_data["id"])
            
        except Exception as e:
            logger.error("Error indexando préstamo", loan_id=loan_data.get("id"), error=str(e))
    
    async def search_clients(
        self, 
        query: str, 
        filters: Optional[str] = None,
        limit: int = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Buscar clientes"""
        try:
            index = await self.client.get_index(self.clients_index)
            
            search_params = {
                "q": query,
                "limit": limit or settings.SEARCH_RESULTS_LIMIT,
                "offset": offset,
                "attributesToHighlight": ["nombre_completo", "email"] if settings.SEARCH_HIGHLIGHT else []
            }
            
            if filters:
                search_params["filter"] = filters
            
            results = await index.search(**search_params)
            
            logger.info("Búsqueda de clientes realizada", 
                       query=query, 
                       results_count=len(results.get("hits", [])))
            
            return results
            
        except Exception as e:
            logger.error("Error en búsqueda de clientes", query=query, error=str(e))
            return {"hits": [], "estimatedTotalHits": 0}
    
    async def search_loans(
        self, 
        query: str, 
        filters: Optional[str] = None,
        limit: int = None,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Buscar préstamos"""
        try:
            index = await self.client.get_index(self.loans_index)
            
            search_params = {
                "q": query,
                "limit": limit or settings.SEARCH_RESULTS_LIMIT,
                "offset": offset,
                "attributesToHighlight": ["numero_prestamo", "cliente_nombre"] if settings.SEARCH_HIGHLIGHT else []
            }
            
            if filters:
                search_params["filter"] = filters
            
            results = await index.search(**search_params)
            
            logger.info("Búsqueda de préstamos realizada", 
                       query=query, 
                       results_count=len(results.get("hits", [])))
            
            return results
            
        except Exception as e:
            logger.error("Error en búsqueda de préstamos", query=query, error=str(e))
            return {"hits": [], "estimatedTotalHits": 0}
    
    async def search_global(
        self, 
        query: str, 
        indexes: List[str] = None,
        limit: int = None
    ) -> Dict[str, Any]:
        """Búsqueda global en múltiples índices"""
        try:
            if not indexes:
                indexes = [self.clients_index, self.loans_index, self.documents_index]
            
            results = {}
            
            for index_name in indexes:
                try:
                    index = await self.client.get_index(index_name)
                    search_result = await index.search(
                        q=query,
                        limit=limit or 10,
                        attributesToHighlight=["*"] if settings.SEARCH_HIGHLIGHT else []
                    )
                    results[index_name] = search_result
                except Exception as e:
                    logger.warning(f"Error buscando en índice {index_name}", error=str(e))
                    results[index_name] = {"hits": [], "estimatedTotalHits": 0}
            
            logger.info("Búsqueda global realizada", query=query, indexes=indexes)
            
            return results
            
        except Exception as e:
            logger.error("Error en búsqueda global", query=query, error=str(e))
            return {}
    
    async def delete_document(self, index_name: str, document_id: str):
        """Eliminar un documento del índice"""
        try:
            index = await self.client.get_index(index_name)
            await index.delete_document(document_id)
            
            logger.info("Documento eliminado del índice", 
                       index=index_name, 
                       document_id=document_id)
            
        except Exception as e:
            logger.error("Error eliminando documento del índice", 
                        index=index_name, 
                        document_id=document_id, 
                        error=str(e))
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de los índices de búsqueda"""
        try:
            stats = {}
            
            for index_name in [self.clients_index, self.loans_index, self.documents_index, self.users_index]:
                try:
                    index = await self.client.get_index(index_name)
                    index_stats = await index.get_stats()
                    stats[index_name] = index_stats
                except Exception as e:
                    logger.warning(f"Error obteniendo stats de {index_name}", error=str(e))
                    stats[index_name] = {"numberOfDocuments": 0}
            
            return stats
            
        except Exception as e:
            logger.error("Error obteniendo estadísticas de búsqueda", error=str(e))
            return {}

# Instancia global del servicio de búsqueda
search_service = SearchService()

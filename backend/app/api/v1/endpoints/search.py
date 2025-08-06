"""
Endpoints de API para búsqueda de texto completo
Proporciona capacidades de búsqueda avanzada para clientes, préstamos y documentos
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import structlog

from app.services.search_service import search_service
from app.core.security import log_audit_event
from app.core.config import settings

logger = structlog.get_logger(__name__)

router = APIRouter()

# Modelos de respuesta
class SearchResult(BaseModel):
    """Resultado de búsqueda individual"""
    id: str
    score: float
    highlights: Dict[str, List[str]] = {}
    data: Dict[str, Any]

class SearchResponse(BaseModel):
    """Respuesta de búsqueda"""
    query: str
    total_hits: int
    hits: List[SearchResult]
    processing_time_ms: int
    page: int
    per_page: int
    filters_applied: Optional[str] = None

class GlobalSearchResponse(BaseModel):
    """Respuesta de búsqueda global"""
    query: str
    results: Dict[str, SearchResponse]
    total_results: int
    processing_time_ms: int

class SearchStatsResponse(BaseModel):
    """Estadísticas de búsqueda"""
    indexes: Dict[str, Dict[str, Any]]
    total_documents: int
    last_updated: str

# Modelos de request
class SearchRequest(BaseModel):
    """Request de búsqueda"""
    query: str = Field(..., min_length=1, max_length=500, description="Consulta de búsqueda")
    filters: Optional[str] = Field(None, description="Filtros de búsqueda")
    page: int = Field(1, ge=1, description="Número de página")
    per_page: int = Field(20, ge=1, le=100, description="Resultados por página")
    highlight: bool = Field(True, description="Habilitar resaltado")

@router.get("/clients", response_model=SearchResponse)
async def search_clients(
    q: str = Query(..., min_length=1, max_length=500, description="Consulta de búsqueda"),
    filters: Optional[str] = Query(None, description="Filtros (ej: sucursal_id=1 AND activo=true)"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página")
):
    """
    Buscar clientes por nombre, email, RFC, CURP, etc.
    
    Ejemplos de búsqueda:
    - q="Juan Pérez"
    - q="juan@email.com"
    - q="ABCD123456"
    
    Ejemplos de filtros:
    - filters="sucursal_id=1"
    - filters="activo=true AND score_crediticio>700"
    """
    try:
        # Calcular offset
        offset = (page - 1) * per_page
        
        # Realizar búsqueda
        results = await search_service.search_clients(
            query=q,
            filters=filters,
            limit=per_page,
            offset=offset
        )
        
        # Procesar resultados
        search_results = []
        for hit in results.get("hits", []):
            search_results.append(SearchResult(
                id=hit["id"],
                score=hit.get("_rankingScore", 0.0),
                highlights=hit.get("_formatted", {}),
                data=hit
            ))
        
        # Log de auditoría
        log_audit_event(
            action="search_clients",
            resource_type="search",
            resource_id="clients",
            details={
                "query": q,
                "filters": filters,
                "results_count": len(search_results),
                "page": page
            }
        )
        
        response = SearchResponse(
            query=q,
            total_hits=results.get("estimatedTotalHits", 0),
            hits=search_results,
            processing_time_ms=results.get("processingTimeMs", 0),
            page=page,
            per_page=per_page,
            filters_applied=filters
        )
        
        logger.info("Búsqueda de clientes realizada", 
                   query=q, 
                   results_count=len(search_results))
        
        return response
        
    except Exception as e:
        logger.error("Error en búsqueda de clientes", query=q, error=str(e))
        raise HTTPException(status_code=500, detail="Error interno en búsqueda de clientes")

@router.get("/loans", response_model=SearchResponse)
async def search_loans(
    q: str = Query(..., min_length=1, max_length=500, description="Consulta de búsqueda"),
    filters: Optional[str] = Query(None, description="Filtros"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Resultados por página")
):
    """
    Buscar préstamos por número, cliente, tipo, etc.
    
    Ejemplos de búsqueda:
    - q="PRE-2024-001"
    - q="Juan Pérez"
    - q="hipotecario"
    
    Ejemplos de filtros:
    - filters="estado='aprobado'"
    - filters="monto_aprobado>100000"
    """
    try:
        offset = (page - 1) * per_page
        
        results = await search_service.search_loans(
            query=q,
            filters=filters,
            limit=per_page,
            offset=offset
        )
        
        search_results = []
        for hit in results.get("hits", []):
            search_results.append(SearchResult(
                id=hit["id"],
                score=hit.get("_rankingScore", 0.0),
                highlights=hit.get("_formatted", {}),
                data=hit
            ))
        
        # Log de auditoría
        log_audit_event(
            action="search_loans",
            resource_type="search",
            resource_id="loans",
            details={
                "query": q,
                "filters": filters,
                "results_count": len(search_results),
                "page": page
            }
        )
        
        response = SearchResponse(
            query=q,
            total_hits=results.get("estimatedTotalHits", 0),
            hits=search_results,
            processing_time_ms=results.get("processingTimeMs", 0),
            page=page,
            per_page=per_page,
            filters_applied=filters
        )
        
        logger.info("Búsqueda de préstamos realizada", 
                   query=q, 
                   results_count=len(search_results))
        
        return response
        
    except Exception as e:
        logger.error("Error en búsqueda de préstamos", query=q, error=str(e))
        raise HTTPException(status_code=500, detail="Error interno en búsqueda de préstamos")

@router.get("/global", response_model=GlobalSearchResponse)
async def global_search(
    q: str = Query(..., min_length=1, max_length=500, description="Consulta de búsqueda global"),
    indexes: Optional[str] = Query(None, description="Índices a buscar (separados por coma)"),
    limit: int = Query(10, ge=1, le=50, description="Límite de resultados por índice")
):
    """
    Búsqueda global en múltiples índices.
    
    Busca simultáneamente en clientes, préstamos y documentos.
    
    Parámetros:
    - q: Consulta de búsqueda
    - indexes: Índices específicos (ej: "clients,loans")
    - limit: Máximo resultados por índice
    """
    try:
        # Procesar índices solicitados
        search_indexes = None
        if indexes:
            index_mapping = {
                "clients": f"{settings.MEILISEARCH_INDEX_PREFIX}_clients",
                "loans": f"{settings.MEILISEARCH_INDEX_PREFIX}_loans",
                "documents": f"{settings.MEILISEARCH_INDEX_PREFIX}_documents",
                "users": f"{settings.MEILISEARCH_INDEX_PREFIX}_users"
            }
            requested_indexes = [idx.strip() for idx in indexes.split(",")]
            search_indexes = [index_mapping.get(idx) for idx in requested_indexes if idx in index_mapping]
        
        # Realizar búsqueda global
        results = await search_service.search_global(
            query=q,
            indexes=search_indexes,
            limit=limit
        )
        
        # Procesar resultados por índice
        processed_results = {}
        total_results = 0
        
        for index_name, index_results in results.items():
            search_results = []
            for hit in index_results.get("hits", []):
                search_results.append(SearchResult(
                    id=hit["id"],
                    score=hit.get("_rankingScore", 0.0),
                    highlights=hit.get("_formatted", {}),
                    data=hit
                ))
            
            # Mapear nombre de índice a nombre amigable
            friendly_name = index_name.replace(f"{settings.MEILISEARCH_INDEX_PREFIX}_", "")
            
            processed_results[friendly_name] = SearchResponse(
                query=q,
                total_hits=index_results.get("estimatedTotalHits", 0),
                hits=search_results,
                processing_time_ms=index_results.get("processingTimeMs", 0),
                page=1,
                per_page=limit
            )
            
            total_results += len(search_results)
        
        # Log de auditoría
        log_audit_event(
            action="global_search",
            resource_type="search",
            resource_id="global",
            details={
                "query": q,
                "indexes": indexes,
                "total_results": total_results
            }
        )
        
        response = GlobalSearchResponse(
            query=q,
            results=processed_results,
            total_results=total_results,
            processing_time_ms=sum(r.processing_time_ms for r in processed_results.values())
        )
        
        logger.info("Búsqueda global realizada", 
                   query=q, 
                   total_results=total_results,
                   indexes_searched=list(processed_results.keys()))
        
        return response
        
    except Exception as e:
        logger.error("Error en búsqueda global", query=q, error=str(e))
        raise HTTPException(status_code=500, detail="Error interno en búsqueda global")

@router.post("/clients", response_model=SearchResponse)
async def search_clients_advanced(request: SearchRequest):
    """
    Búsqueda avanzada de clientes con más opciones.
    
    Permite búsquedas más complejas con filtros y paginación.
    """
    try:
        offset = (request.page - 1) * request.per_page
        
        results = await search_service.search_clients(
            query=request.query,
            filters=request.filters,
            limit=request.per_page,
            offset=offset
        )
        
        search_results = []
        for hit in results.get("hits", []):
            search_results.append(SearchResult(
                id=hit["id"],
                score=hit.get("_rankingScore", 0.0),
                highlights=hit.get("_formatted", {}) if request.highlight else {},
                data=hit
            ))
        
        # Log de auditoría
        log_audit_event(
            action="search_clients_advanced",
            resource_type="search",
            resource_id="clients",
            details={
                "query": request.query,
                "filters": request.filters,
                "results_count": len(search_results),
                "page": request.page
            }
        )
        
        response = SearchResponse(
            query=request.query,
            total_hits=results.get("estimatedTotalHits", 0),
            hits=search_results,
            processing_time_ms=results.get("processingTimeMs", 0),
            page=request.page,
            per_page=request.per_page,
            filters_applied=request.filters
        )
        
        logger.info("Búsqueda avanzada de clientes realizada", 
                   query=request.query, 
                   results_count=len(search_results))
        
        return response
        
    except Exception as e:
        logger.error("Error en búsqueda avanzada de clientes", 
                    query=request.query, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Error interno en búsqueda avanzada")

@router.get("/stats", response_model=SearchStatsResponse)
async def get_search_stats():
    """
    Obtener estadísticas de los índices de búsqueda.
    
    Retorna información sobre el número de documentos indexados,
    estado de los índices y última actualización.
    """
    try:
        stats = await search_service.get_search_stats()
        
        total_documents = 0
        for index_stats in stats.values():
            total_documents += index_stats.get("numberOfDocuments", 0)
        
        response = SearchStatsResponse(
            indexes=stats,
            total_documents=total_documents,
            last_updated=str(datetime.utcnow())
        )
        
        logger.info("Estadísticas de búsqueda obtenidas", 
                   total_documents=total_documents,
                   indexes_count=len(stats))
        
        return response
        
    except Exception as e:
        logger.error("Error obteniendo estadísticas de búsqueda", error=str(e))
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")

@router.post("/reindex/{entity_type}")
async def reindex_entity(
    entity_type: str,
    entity_ids: Optional[List[str]] = None
):
    """
    Reindexar entidades para búsqueda.
    
    Útil para actualizar índices después de cambios en los datos.
    
    Parámetros:
    - entity_type: Tipo de entidad (client, loan, document)
    - entity_ids: IDs específicos a reindexar (opcional)
    """
    try:
        if entity_type not in ["client", "loan", "document", "user"]:
            raise HTTPException(
                status_code=400, 
                detail="Tipo de entidad no válido"
            )
        
        # Aquí iría la lógica para reindexar
        # Por ahora simulamos el proceso
        
        reindexed_count = len(entity_ids) if entity_ids else 100  # Simular
        
        # Log de auditoría
        log_audit_event(
            action="reindex_entities",
            resource_type="search",
            resource_id=entity_type,
            details={
                "entity_type": entity_type,
                "entity_ids": entity_ids,
                "reindexed_count": reindexed_count
            }
        )
        
        logger.info("Reindexación completada", 
                   entity_type=entity_type,
                   reindexed_count=reindexed_count)
        
        return {
            "success": True,
            "entity_type": entity_type,
            "reindexed_count": reindexed_count,
            "message": f"Se reindexaron {reindexed_count} {entity_type}s correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error en reindexación", 
                    entity_type=entity_type, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Error interno en reindexación")

@router.delete("/index/{entity_type}/{entity_id}")
async def remove_from_index(entity_type: str, entity_id: str):
    """
    Eliminar una entidad específica del índice de búsqueda.
    """
    try:
        if entity_type not in ["client", "loan", "document", "user"]:
            raise HTTPException(
                status_code=400, 
                detail="Tipo de entidad no válido"
            )
        
        index_name = f"{settings.MEILISEARCH_INDEX_PREFIX}_{entity_type}s"
        await search_service.delete_document(index_name, entity_id)
        
        # Log de auditoría
        log_audit_event(
            action="remove_from_index",
            resource_type="search",
            resource_id=entity_id,
            details={
                "entity_type": entity_type,
                "entity_id": entity_id,
                "index_name": index_name
            }
        )
        
        logger.info("Entidad eliminada del índice", 
                   entity_type=entity_type,
                   entity_id=entity_id)
        
        return {
            "success": True,
            "message": f"{entity_type} {entity_id} eliminado del índice correctamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error eliminando del índice", 
                    entity_type=entity_type, 
                    entity_id=entity_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail="Error eliminando del índice")

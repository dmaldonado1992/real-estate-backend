from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import Product, SearchIARequest, SearchIAResponse, SearchRealStateRequest, SearchRealStateResponse
from .services.property_service import IPropertyService
from .dependencies import get_property_service
from .services.llm_coordination_service import LLMService

router = APIRouter()

@router.get("/api/products", tags=["Productos"])
async def get_products(service: IPropertyService = Depends(get_property_service)):
    result = service.get_all_properties()
    return {
        "products": result.get('products', []),
        "sql": result.get('sql')
    }

@router.get("/api/products/{product_id}", response_model=Product, tags=["Productos"])
async def get_product(product_id: int, service: IPropertyService = Depends(get_property_service)) -> Product:
    product = service.get_property_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto con ID {product_id} no encontrado")
    return product

@router.post("/api/products", response_model=Product, tags=["Productos"], status_code=201)
async def create_product(product: Product, service: IPropertyService = Depends(get_property_service)) -> Product:
    created_product = service.create_property(product)
    if not created_product:
        raise HTTPException(status_code=500, detail="Error al crear el producto")
    return created_product

@router.put("/api/products/{product_id}", response_model=Product, tags=["Productos"])
async def update_product(product_id: int, product: Product, service: IPropertyService = Depends(get_property_service)) -> Product:
    updated_product = service.update_property(product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail=f"Producto con ID {product_id} no encontrado")
    return updated_product

@router.delete("/api/products/{product_id}", tags=["Productos"], status_code=204)
async def delete_product(product_id: int, service: IPropertyService = Depends(get_property_service)):
    deleted = service.delete_property(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Producto con ID {product_id} no encontrado")
    return None


@router.post("/api/search-ia", tags=["IA"])
async def search_con_ia(request: SearchIARequest):
    """
    Endpoint para consultas directas a la IA - Devuelve respuesta completa sin procesar.
    
    Utiliza Ollama Cloud con modelo Perplexity para responder cualquier consulta
    sobre bienes raíces de forma conversacional y natural.
    
    Args:
        request: SearchIARequest con query, context opcional y use_cloud
    
    Returns:
        Respuesta directa y completa de la IA sin procesamiento adicional
    """
    try:
        llm_service = LLMService()
        
        # Usar el método search_ia del servicio
        response = await llm_service.search_ia(request.query)
        
        # Devolver respuesta completa de la IA
        return {
            "success": True,
            "response": response if response else "No pude procesar tu consulta en este momento.",
            "query": request.query,
            "ai_used": True,
            "model": "deepseek-v3.1:671b-cloud"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda con IA: {str(e)}"
        )


@router.post("/api/ask-ai", tags=["IA"])
async def ask_ai_endpoint(request: SearchIARequest):
    """Endpoint simple - devuelve exactamente lo que responde la IA"""
    llm_service = LLMService()
    response = await llm_service.ask_ai_direct(request.query)
    return {"response": response}


@router.post("/api/generate-sql", tags=["IA"])
async def generate_sql_endpoint(request: SearchIARequest):
    """
    Genera consultas SQL basadas en lenguaje natural usando IA.
    
    Convierte consultas en lenguaje natural a SQL válido para la tabla 'propiedades'.
    Utiliza DeepSeek v3.1 para generar SQL optimizado y seguro.
    
    Args:
        request: SearchIARequest con query en lenguaje natural
    
    Returns:
        Dict con el SQL generado, query original y metadatos
    """
    try:
        llm_service = LLMService()
        sql_result = await llm_service.generate_sql_async(request.query)
        
        if sql_result.get('success'):
            return {
                "success": True,
                "sql": sql_result.get('sql'),
                "original_query": request.query,
                "model": "deepseek-v3.1:671b-cloud",
                "note": "SQL generado por IA - revisar antes de ejecutar en producción"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Error al generar SQL: {sql_result.get('error', 'Error desconocido')}"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar SQL: {str(e)}"
        )



@router.post("/api/search-ia-real-state", response_model=SearchRealStateResponse, tags=["IA"])
async def search_ia_real_state(request: SearchRealStateRequest) -> SearchRealStateResponse:
    """
    Búsqueda inteligente de propiedades combinando IA con base de datos.
    
    Proceso:
    1. Obtiene todas las propiedades de la BD
    2. Usa IA (deepseek-v3.1:671b-cloud) para extraer keywords de la consulta
    3. Filtra propiedades usando LIKE con las keywords sugeridas
    4. Retorna resultados con análisis inteligente de la IA
    
    Args:
        request: SearchRealStateRequest con query y use_cloud
    
    Returns:
        SearchRealStateResponse con propiedades filtradas, keywords y análisis
    """
    try:
        llm_service = LLMService()
        result = await llm_service.search_ia_real_state(
            query=request.query,
            use_cloud=request.use_cloud
        )
        # Sanitizar propiedades para reducir tamaño del payload y memoria
        props = result.get('properties', []) or []
        sanitized = []
        for p in props[:50]:  # limitar a 50 propiedades por respuesta
            sanitized.append({
                'id': p.get('id'),
                'titulo': p.get('titulo'),
                'ubicacion': p.get('ubicacion'),
                'precio': p.get('precio'),
                'habitaciones': p.get('habitaciones'),
                'banos': p.get('banos'),
                'area_m2': p.get('area_m2'),
                'imagen_url': p.get('imagen_url'),
                'descripcion': (p.get('descripcion') or '')[:400]
            })
        result['properties'] = sanitized
        return SearchRealStateResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en búsqueda de propiedades con IA: {str(e)}"
        )

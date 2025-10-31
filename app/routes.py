from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from datetime import date
from .models import Product
from .utils import CustomJSONEncoder
from .llm_service import LLMService
from .database import db

router = APIRouter()

@router.get("/api/products", response_model=List[Product], 
             summary="Obtener todos los productos",
             description="Retorna una lista de todos los productos disponibles")
async def get_products():
    """
    Retorna todos los productos almacenados en la base de datos.
    
    Returns:
        List[Product]: Lista de productos ordenados por fecha de publicación
    """
    properties = db.get_all_properties()
    # Convertir las fechas de string a objetos date para compatibilidad
    for prop in properties:
        if isinstance(prop.get("fecha_publicacion"), str):
            prop["fecha_publicacion"] = date.fromisoformat(prop["fecha_publicacion"])
    return properties

@router.get("/api/products/{product_id}",
             response_model=Product,
             summary="Obtener un producto por ID",
             description="Retorna un producto específico basado en su ID")
async def get_product(product_id: int):
    """
    Obtiene un producto específico por su ID
    
    Args:
        product_id (int): ID del producto a buscar
        
    Returns:
        Product: Detalles del producto
        
    Raises:
        HTTPException: Si el producto no se encuentra (404)
    """
    product = db.get_property_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Convertir fecha si es necesario
    if isinstance(product.get("fecha_publicacion"), str):
        product["fecha_publicacion"] = date.fromisoformat(product["fecha_publicacion"])
    
    return product

@router.post("/api/products", 
              response_model=Product,
              summary="Crear un nuevo producto",
              description="Crea un nuevo producto con los datos proporcionados")
async def create_product(product: Product):
    """
    Crea un nuevo producto
    
    Args:
        product (Product): Datos del producto a crear
        
    Returns:
        Product: Producto creado con su ID asignado
    """
    try:
        product_dict = product.dict()
        
        # Asignar la fecha actual si no se proporciona una
        if not product_dict.get("fecha_publicacion"):
            product_dict["fecha_publicacion"] = date.today()
        elif isinstance(product_dict.get("fecha_publicacion"), str):
            product_dict["fecha_publicacion"] = date.fromisoformat(product_dict["fecha_publicacion"])
            
        created_product = db.create_property(product_dict)
        if not created_product:
            raise HTTPException(status_code=500, detail="Error al guardar el producto en la base de datos")
        
        return created_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar el producto: {str(e)}")

@router.put("/api/products/{product_id}", 
             response_model=Product,
             summary="Actualizar un producto",
             description="Actualiza un producto existente por su ID")
async def update_product(product_id: int, updated_product: Product):
    """
    Actualiza un producto existente
    
    Args:
        product_id (int): ID del producto a actualizar
        updated_product (Product): Nuevos datos del producto
        
    Returns:
        Product: Producto actualizado
        
    Raises:
        HTTPException: Si el producto no se encuentra (404)
    """
    try:
        updated_dict = updated_product.dict()
        if isinstance(updated_dict.get("fecha_publicacion"), str):
            updated_dict["fecha_publicacion"] = date.fromisoformat(updated_dict["fecha_publicacion"])
        
        updated_property = db.update_property(product_id, updated_dict)
        if not updated_property:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return updated_property
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el producto: {str(e)}")

@router.delete("/api/products/{product_id}",
                summary="Eliminar un producto",
                description="Elimina un producto por su ID")
async def delete_product(product_id: int):
    """
    Elimina un producto
    
    Args:
        product_id (int): ID del producto a eliminar
        
    Returns:
        dict: Mensaje de confirmación
        
    Raises:
        HTTPException: Si el producto no se encuentra (404)
    """
    try:
        deleted = db.delete_property(product_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        
        return {"message": "Producto eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar el producto: {str(e)}")

# Inicializar el servicio LLM usando únicamente Ollama local
llm_service = LLMService(model_name="llama3.2:1b")

@router.get("/api/llm/test",
            summary="Probar conexión con Ollama local",
            description="Prueba la conexión únicamente con Ollama local")
async def test_llm():
    """
    Prueba la conexión con los proveedores LLM disponibles
    
    Returns:
        dict: Estado de la conexión y proveedor activo
    """
    try:
        is_working = await llm_service.test_connection()
        
        current_provider = "Ollama Local"
        if is_working:
            return {
                "status": "success",
                "message": "Ollama local funcionando correctamente",
                "provider": current_provider,
                "provider_code": llm_service.provider
            }
        else:
            return {"status": "error", "message": "No se pudo conectar con Ollama local", "provider": current_provider}
    except Exception as e:
        return {"status": "error", "message": f"Error al probar LLM: {str(e)}"}

# Eliminada la ruta de validación multi-proveedor para forzar uso único de Ollama local

@router.post("/api/llm/description",
             summary="Generar descripción de producto con LLM",
             description="Genera una descripción atractiva usando Ollama local")
async def generate_product_description(product_name: str):
    """
    Genera una descripción de producto usando el mejor proveedor disponible
    
    Args:
        product_name (str): Nombre del producto
        
    Returns:
        dict: Descripción generada y proveedor usado
    """
    try:
        description = await llm_service.get_product_description(product_name)
        
        return {
            "product_name": product_name,
            "description": description,
            "provider": "Ollama Local",
            "provider_code": llm_service.provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar descripción: {str(e)}")

@router.post("/api/llm/recommendations",
             summary="Generar recomendaciones con LLM",
             description="Genera recomendaciones de productos relacionados usando Ollama local")
async def generate_recommendations(product_description: str, num_recommendations: int = 3):
    """
    Genera recomendaciones de productos usando el mejor proveedor disponible
    
    Args:
        product_description (str): Descripción del producto base
        num_recommendations (int): Número de recomendaciones a generar
        
    Returns:
        dict: Lista de recomendaciones y proveedor usado
    """
    try:
        recommendations = await llm_service.get_product_recommendations(product_description, num_recommendations)
        
        return {
            "base_product": product_description,
            "recommendations": recommendations,
            "provider": "Ollama Local",
            "provider_code": llm_service.provider
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar recomendaciones: {str(e)}")
from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from datetime import date
from .models import Product
from .utils import CustomJSONEncoder

# Obtener la ruta absoluta al directorio de datos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, 'app', 'data', 'products.json')

router = APIRouter()

# Lista para almacenar los productos
products = []

# Cargar productos iniciales desde el archivo JSON
try:
    with open(DATA_FILE, "r", encoding='utf-8') as file:
        products = json.load(file)
        # Convertir las fechas de string a objetos date
        for product in products:
            if isinstance(product.get("fecha_publicacion"), str):
                product["fecha_publicacion"] = date.fromisoformat(product["fecha_publicacion"])
except FileNotFoundError:
    products = []
    # Crear el archivo si no existe
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding='utf-8') as file:
        json.dump(products, file, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)

@router.get("/api/products", response_model=List[Product], 
             summary="Obtener todos los productos",
             description="Retorna una lista de todos los productos disponibles")
async def get_products():
    """
    Retorna todos los productos almacenados en la base de datos.
    
    Returns:
        List[Product]: Lista de productos ordenados por fecha de publicación
    """
    # Ordenar productos por fecha de publicación (más recientes primero)
    return sorted(products, key=lambda x: x.get('fecha_publicacion', ''), reverse=True)

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
    for product in products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Producto no encontrado")

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
    # Asignar un nuevo ID
    if products:
        new_id = max(p["id"] for p in products) + 1
    else:
        new_id = 1
    
    try:
        product_dict = product.dict()
        product_dict["id"] = new_id
        
        # Asignar la fecha actual si no se proporciona una
        if not product_dict.get("fecha_publicacion"):
            product_dict["fecha_publicacion"] = date.today()
        elif isinstance(product_dict.get("fecha_publicacion"), str):
            product_dict["fecha_publicacion"] = date.fromisoformat(product_dict["fecha_publicacion"])
            
        products.append(product_dict)
        
        # Guardar en el archivo JSON usando la ruta absoluta y el codificador personalizado
        with open(DATA_FILE, "w", encoding='utf-8') as file:
            json.dump(products, file, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
        
        return product_dict
    except Exception as e:
        # Si hay un error, eliminar el producto de la lista y lanzar excepción
        if product_dict in products:
            products.remove(product_dict)
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
    for i, product in enumerate(products):
        if product["id"] == product_id:
            try:
                updated_dict = updated_product.dict()
                updated_dict["id"] = product_id
                if isinstance(updated_dict.get("fecha_publicacion"), str):
                    updated_dict["fecha_publicacion"] = date.fromisoformat(updated_dict["fecha_publicacion"])
                old_product = products[i]  # Guardar el producto anterior
                products[i] = updated_dict
                
                # Guardar en el archivo JSON usando la ruta absoluta y el codificador personalizado
                with open(DATA_FILE, "w", encoding='utf-8') as file:
                    json.dump(products, file, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
                
                return updated_dict
            except Exception as e:
                # Si hay un error, restaurar el producto anterior
                products[i] = old_product
                raise HTTPException(status_code=500, detail=f"Error al actualizar el producto: {str(e)}")
    raise HTTPException(status_code=404, detail="Producto no encontrado")

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
    for i, product in enumerate(products):
        if product["id"] == product_id:
            try:
                removed_product = products.pop(i)
                
                # Guardar en el archivo JSON usando la ruta absoluta y el codificador personalizado
                with open(DATA_FILE, "w", encoding='utf-8') as file:
                    json.dump(products, file, indent=2, ensure_ascii=False, cls=CustomJSONEncoder)
                
                return {"message": "Producto eliminado"}
            except Exception as e:
                # Si hay un error, restaurar el producto eliminado
                products.insert(i, removed_product)
                raise HTTPException(status_code=500, detail=f"Error al eliminar el producto: {str(e)}")
    raise HTTPException(status_code=404, detail="Producto no encontrado")
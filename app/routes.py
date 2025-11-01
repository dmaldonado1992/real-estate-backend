from fastapi import APIRouter, HTTPException, Depends
from typing import List
from .models import Product
from .services.property_service import IPropertyService
from .dependencies import get_property_service

router = APIRouter()

@router.get("/api/products", response_model=List[Product], tags=["Productos"])
async def get_products(service: IPropertyService = Depends(get_property_service)) -> List[Product]:
    return service.get_all_properties()

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

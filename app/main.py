from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import List
import json
from app.models import Product

# Crear la aplicación FastAPI con metadatos para Swagger
app = FastAPI(
    title="API de Productos",
    description="API para gestionar productos con FastAPI",
    version="1.0.0",
    docs_url=None,  # Deshabilitamos la ruta por defecto
    redoc_url=None  # Deshabilitamos la documentación ReDoc
)

# Configurar CORS para permitir las solicitudes del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    expose_headers=["Content-Type"],
    max_age=3600,
)

# Montar archivos estáticos para Swagger UI
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Ruta personalizada para la documentación Swagger UI
    """
    return FileResponse("static/docs.html")

# Importar y agregar las rutas
from .routes import router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Lista para almacenar los productos
products = []

# Cargar productos iniciales desde el archivo JSON
try:
    with open("app/data/products.json", "r") as file:
        products = json.load(file)
except FileNotFoundError:
    products = []

@app.get("/api/products", response_model=dict)
async def get_products(
    search: str = None,
    page: int = 1,
    limit: int = 6
):
    filtered_products = products
    
    # Aplicar búsqueda si existe
    if search and search.strip():
        search = search.lower()
        # Filtrar productos que contienen el término de búsqueda en titulo, descripcion o ubicacion
        filtered_products = [
            p for p in products 
            if search in p['titulo'].lower() or 
               search in p['descripcion'].lower() or 
               search in p['ubicacion'].lower() or 
               search in p['tipo'].lower()
        ]
    
    # Calcular paginación
    total = len(filtered_products)
    total_pages = (total + limit - 1) // limit
    
    # Ajustar página si está fuera de rango
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "items": filtered_products[start:end],
        "total": total,
        "page": page,
        "totalPages": total_pages
    }

@app.get("/api/products/{product_id}")
async def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.post("/api/products", response_model=Product)
async def create_product(product: Product):
    # Asignar un nuevo ID
    if products:
        new_id = max(p["id"] for p in products) + 1
    else:
        new_id = 1
    
    product_dict = product.dict()
    product_dict["id"] = new_id
    products.append(product_dict)
    
    # Guardar en el archivo JSON
    with open("app/data/products.json", "w") as file:
        json.dump(products, file, indent=2)
    
    return product_dict

@app.put("/api/products/{product_id}", response_model=Product)
async def update_product(product_id: int, updated_product: Product):
    for i, product in enumerate(products):
        if product["id"] == product_id:
            updated_dict = updated_product.dict()
            updated_dict["id"] = product_id
            products[i] = updated_dict
            
            # Guardar en el archivo JSON
            with open("app/data/products.json", "w") as file:
                json.dump(products, file, indent=2)
            
            return updated_dict
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: int):
    for i, product in enumerate(products):
        if product["id"] == product_id:
            products.pop(i)
            
            # Guardar en el archivo JSON
            with open("app/data/products.json", "w") as file:
                json.dump(products, file, indent=2)
            
            return {"message": "Producto eliminado"}
    raise HTTPException(status_code=404, detail="Producto no encontrado")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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

@app.get("/health", include_in_schema=False)
async def health_check():
    """
    Endpoint de health check para Docker
    """
    return {"status": "ok", "service": "backend-api"}

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
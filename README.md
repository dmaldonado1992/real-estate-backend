# Backend API con FastAPI

Este es el backend de la aplicación de productos, construido con FastAPI y PostgreSQL.

## Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   └── llm_service.py
├── persistencia/
│   ├── schema.sql
│   └── seed_data.sql
├── Dockerfile
├── requirements.txt
└── docker-compose.yml
```

## Configuración (local-only)

Este backend está preparado para funcionar con Ollama local y una base de datos
local (la composición final del sistema está en el `docker-compose.yml` raíz).

Pasos recomendados:

- 1) Asegúrate de tener Ollama corriendo localmente en http://127.0.0.1:11434.
- 2) Si usas Docker, utiliza el `docker-compose.yml` en la raíz del repo:

```powershell
cd "C:\Users\Daniel Maldonado\Documents\vue"
docker-compose up --build
```

### Ejecutar sin Docker (desarrollo)

1. Crea y activa un entorno virtual:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Instala dependencias:

```powershell
pip install -r requirements.txt
```

3. Inicia el backend:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Visita http://127.0.0.1:8000/docs para la documentación de la API.

## API Endpoints

- GET `/api/products` - Lista todos los productos
- GET `/api/products/{id}` - Obtiene un producto específico
- POST `/api/products` - Crea un nuevo producto
- PUT `/api/products/{id}` - Actualiza un producto
- DELETE `/api/products/{id}` - Elimina un producto
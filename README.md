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

## Configuración

1. Copia `.env.example` a `.env` y configura las variables de entorno:
```bash
cp .env.example .env
```

2. Edita `.env` y agrega tu API key de OpenAI:
```
OPENAI_API_KEY=tu-api-key-aqui
```

## Ejecución

### Con Docker:

```bash
docker-compose up --build
```

### Sin Docker:

1. Crea un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Inicia el servidor:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- GET `/api/products` - Lista todos los productos
- GET `/api/products/{id}` - Obtiene un producto específico
- POST `/api/products` - Crea un nuevo producto
- PUT `/api/products/{id}` - Actualiza un producto
- DELETE `/api/products/{id}` - Elimina un producto
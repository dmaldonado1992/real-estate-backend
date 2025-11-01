# Proyecto Vue + FastAPI + LLM

Este proyecto contiene:
- **Backend**: FastAPI (Python) con arquitectura SOLID + IA (Ollama)
- **Frontend**: Vue 3 + Vite + Tailwind CSS
- **Base de datos**: MySQL 8.0 en Docker
- **LLM**: Modelos Ollama (local y cloud)

## 📁 Estructura del Proyecto

```
vue/
├── backend/                      # Backend FastAPI con IA
│   ├── .venv/                   # Entorno virtual Python
│   ├── app/                     # Código de la aplicación
│   │   ├── llm_service.py      # Servicios de IA
│   │   ├── routes.py           # Endpoints API
│   │   ├── models.py           # Modelos Pydantic
│   │   └── database.py         # Conexión BD
│   ├── mysql/                   # MySQL Docker
│   │   ├── docker-compose.yml
│   │   └── README.md
│   ├── persistencia/            # Scripts SQL inicialización
│   │   ├── 01_schema.sql
│   │   └── 02_seed_data.sql
│   ├── requirements.txt
│   ├── activate.bat            # Activar venv
│   └── start-mysql.bat         # Iniciar MySQL
├── frontend/                    # Frontend Vue
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── start_backend_ia.bat        # Iniciar backend con IA
└── README.md
```

## 🤖 Modelos LLM Disponibles

### Scripts de Chat Interactivo

| Script | Modelo | Tamaño | RAM | Uso Recomendado |
|--------|--------|--------|-----|-----------------|
| `chat_llama_lite.bat` | llama3.2:1b | 1.3GB | 2-3GB | Recursos MUY limitados |
| `chat_gemma.bat` | Varios (interactivo) | Variable | Variable | **Uso general** |
| `chat_llama31.bat` | llama3.1:8b | 4.7GB | 8GB | Máxima calidad |
| `gestor_modelos.bat` | - | - | - | Administrar modelos |

📖 **Guía completa**: Ver [GUIA_MODELOS_LLM.md](./GUIA_MODELOS_LLM.md)

---

## 🚀 Inicio Rápido

---

## 🚀 Inicio Rápido

### Aplicación Web (Frontend + Backend)

Objetivo: poder desarrollar con Vite (hot-reload) y que las llamadas a la API vayan al backend local.

Requisitos locales en tu máquina Windows:
- Node.js 20.x o superior (requerido por Vite)
- npm (v9+)
- Python (en tu caso ya tienes la distribución embebida en `tools/python39`)

Pasos para usar Vite (frontend) y el backend juntos:

1. Actualiza Node a la versión recomendada (20.x) desde https://nodejs.org/
   - Después de instalar, cierra y abre de nuevo PowerShell/VS Code.

2. Instala dependencias del frontend y arráncalo:

```powershell
cd C:\Users\Daniel Maldonado\Documents\vue\frontend\frontend
npm install
npm run dev
```

Esto arrancará Vite en http://localhost:5173 y el `vite.config.js` está configurado para proxear las llamadas a `/api` hacia `http://127.0.0.1:8000`.

3. Instala dependencias del backend (si no lo hiciste):

```powershell
cd C:\Users\Daniel Maldonado\Documents\vue\backend
..\tools\python39\python.exe -m pip install -r requirements.txt
```

4. Arranca el backend (usar la Python embebida):

```powershell
cd C:\Users\Daniel Maldonado\Documents\vue\backend
..\tools\python39\python.exe -m uvicorn main:app --reload
```

5. Flujo de trabajo recomendado durante desarrollo:
- Primero arranca el backend en el puerto 8000.
- Luego arranca Vite con `npm run dev` en la carpeta del frontend.
- Abre el navegador en `http://localhost:5173` — la app Vue consumirá la API sin problemas gracias al proxy.

Notas:
- Si no quieres instalar Node, hay una versión estática del frontend servida por FastAPI en `/` (archivo `frontend_static/`), pero para desarrollo con HMR conviene usar Vite.
- Asegúrate de tener Node >= 20 antes de ejecutar `npm run dev`.

Usar Docker (construye frontend y backend y sirve todo junto)
-------------------------------------------------------

Si quieres ejecutar todo dentro de Docker (recomendado para reproducibilidad):

```powershell
# Desde la raíz del repositorio
docker compose up --build
```

Esto construirá la imagen (el Dockerfile compilará el frontend con Node 20 y empacará el backend) y expondrá el servicio en `http://localhost:8000`.

Comprobaciones después de `docker compose up`:
- Frontend y backend estarán en la misma imagen: abre `http://localhost:8000/` para ver la SPA y `http://localhost:8000/docs` para Swagger/OpenAPI.

Makefile (opciones rápidas)
---------------------------

Si tienes `make` en Windows (WSL, Git Bash o similar), puedes usar los atajos:

```powershell
# Construir y levantar en background
make up

# Levantar en foreground (sin build)
docker compose up

# Bajar contenedores
make down

# Ver logs
make logs
```

Si no tienes `make`, usa los comandos `docker compose` directamente como se indicó arriba.


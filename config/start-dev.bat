@echo off
echo Iniciando entorno de desarrollo...

REM Matar procesos existentes en puertos 8000 y 5173
echo Limpiando procesos existentes...
taskkill /F /IM node.exe /FI "MEMUSAGE gt 0" 2>NUL
taskkill /F /IM python.exe /FI "MEMUSAGE gt 0" 2>NUL

REM Limpiar e instalar backend
echo.
echo Configurando Backend...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo Error instalando dependencias del backend
    pause
    exit /b 1
)

REM Configurar frontend (solo instala si no existe node_modules)
echo.
echo Configurando Frontend...
cd ..\frontend
echo Comprobando existencia de node_modules...
if exist node_modules goto SKIP_FRONTEND_INSTALL
echo node_modules no encontrado. Limpiando caches y instalando dependencias...
del /f /q package-lock.json 2>NUL
echo Limpiando caches de Vite/NPM (.vite, node_modules\.vite, node_modules\.cache)...
rmdir /s /q node_modules\.vite 2>NUL
rmdir /s /q .vite 2>NUL
rmdir /s /q node_modules\.cache 2>NUL
echo Limpiando cache de npm (force)...
call npm cache clean --force
echo Instalando dependencias...
call npm install
if errorlevel 1 (
    echo Error instalando dependencias del frontend
    pause
    exit /b 1
)
:SKIP_FRONTEND_INSTALL

REM Volver al directorio raíz
cd ..

REM Detener servicios si ya están en ejecución (puertos 8000 y 5173)
echo.
echo Comprobando y deteniendo servicios en puertos 8000 y 5173 si existen...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    echo Matando proceso en puerto 8000: PID %%a
    taskkill /F /PID %%a 2>NUL
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do (
    echo Matando proceso en puerto 5173: PID %%a
    taskkill /F /PID %%a 2>NUL
)
echo Matando procesos por nombre (node.exe y python.exe) por si acaso...
taskkill /F /IM node.exe 2>NUL
taskkill /F /IM python.exe 2>NUL

REM Iniciar servicios
echo.
echo Iniciando Backend (FastAPI)...
cd backend
start cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Iniciando Frontend (Vue)...
cd ..\frontend
start cmd /k "npm run dev"

echo.
echo Servicios iniciándose...
echo.
echo Espera unos segundos y abre en tu navegador:
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Para detener los servicios:
echo 1. Presiona Ctrl+C en cada ventana de terminal
echo 2. Escribe 'Y' cuando te pregunte si deseas terminar el proceso
echo.
pause
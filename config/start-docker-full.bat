@echo off
echo ========================================
echo   INICIALIZANDO PROYECTO CON DOCKER
echo ========================================
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

echo [1/5] Verificando Docker Desktop...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no esta disponible. Iniciando Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo ⏳ Esperando 30 segundos a que Docker Desktop inicie...
    timeout /t 30 /nobreak >nul
)

echo.
echo [2/5] Verificando conexion a Docker...
:WAIT_DOCKER
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ⏳ Esperando a que Docker Desktop este listo...
    timeout /t 5 /nobreak >nul
    goto WAIT_DOCKER
)

echo ✅ Docker Desktop esta listo
echo.

echo [3/5] Deteniendo contenedores anteriores...
docker-compose down 2>nul
echo.

echo [4/5] Reconstruyendo e iniciando servicios...
docker-compose build --no-cache
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo ❌ Error al iniciar los servicios
    pause
    exit /b 1
)

echo.
echo [5/5] Verificando estado de los servicios...
timeout /t 10 /nobreak >nul
docker-compose ps

echo.
echo ========================================
echo    SERVICIOS DISPONIBLES:
echo ========================================
echo    MySQL:         localhost:3306
echo    Backend API:   http://localhost:8000
echo    Health Check:  http://localhost:8000/health
echo    Documentacion: http://localhost:8000/docs
echo    Frontend:      http://localhost:5173
echo ========================================
echo.
echo Comandos utiles:
echo   - Ver logs:      docker-compose logs -f
echo   - Ver logs backend: docker-compose logs backend -f
echo   - Detener todo:  docker-compose down
echo   - Reiniciar:     docker-compose restart
echo   - Probar conexion: docker-compose exec backend python test_docker_connection.py
echo.
pause

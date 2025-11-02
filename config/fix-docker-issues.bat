@echo off
setlocal enabledelayedexpansion
echo ========================================
echo    🔧 SOLUCIONADOR DE PROBLEMAS DOCKER
echo ========================================
echo.

cd /d "%~dp0\..\.."

echo 🔍 Diagnosticando problemas comunes...
echo.

REM Verificar Docker
echo [1/7] Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker no está disponible
    echo 💡 Solución: Instalar Docker Desktop desde https://docker.com
    goto END_DIAG
) else (
    echo ✅ Docker está instalado
)

REM Verificar Docker daemon
echo [2/7] Verificando Docker daemon...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker daemon no responde
    echo 💡 Solución: Reiniciar Docker Desktop
    goto RESTART_DOCKER
) else (
    echo ✅ Docker daemon está corriendo
)

REM Verificar docker-compose
echo [3/7] Verificando docker-compose.yml...
if not exist "docker-compose.yml" (
    echo ❌ No se encuentra docker-compose.yml
    echo 💡 Solución: Ejecutar desde la raíz del proyecto
    goto END_DIAG
) else (
    echo ✅ docker-compose.yml encontrado
)

REM Verificar puertos
echo [4/7] Verificando puertos ocupados...
netstat -an | findstr ":3306 " >nul
if %errorlevel%==0 (
    echo ⚠️  Puerto 3306 (MySQL) está ocupado
    echo 💡 Puede causar conflictos con el contenedor MySQL
)

netstat -an | findstr ":8000 " >nul
if %errorlevel%==0 (
    echo ⚠️  Puerto 8000 (Backend) está ocupado
    echo 💡 Puede causar conflictos con el contenedor backend
)

netstat -an | findstr ":5173 " >nul
if %errorlevel%==0 (
    echo ⚠️  Puerto 5173 (Frontend) está ocupado
    echo 💡 Puede causar conflictos con el contenedor frontend
)

REM Verificar memoria
echo [5/7] Verificando memoria del sistema...
for /f "tokens=2 delims=:" %%a in ('wmic OS get TotalVisibleMemorySize /value ^| find "="') do set total_mem=%%a
set /a total_mem_gb=!total_mem!/1024/1024
if !total_mem_gb! lss 4 (
    echo ⚠️  Memoria total: !total_mem_gb!GB (Recomendado: 8GB+)
    echo 💡 Docker puede funcionar lento con poca memoria
) else (
    echo ✅ Memoria suficiente: !total_mem_gb!GB
)

REM Verificar espacio en disco
echo [6/7] Verificando espacio en disco...
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do set free_space=%%a
set free_space=!free_space:,=!
set /a free_space_gb=!free_space!/1024/1024/1024
if !free_space_gb! lss 10 (
    echo ⚠️  Espacio libre: !free_space_gb!GB (Recomendado: 20GB+)
    echo 💡 Puede causar errores en build de imágenes
) else (
    echo ✅ Espacio suficiente: !free_space_gb!GB
)

REM Verificar contenedores problemáticos
echo [7/7] Verificando contenedores problemáticos...
docker ps -a --filter "status=exited" --format "{{.Names}}" | findstr /r "real-estate" >nul
if %errorlevel%==0 (
    echo ⚠️  Hay contenedores que han fallado
    echo 💡 Puede requerir limpieza
)

echo.
echo ========================================
echo 🛠️  OPCIONES DE SOLUCIÓN:
echo ========================================
echo [1] Reiniciar Docker Desktop
echo [2] Limpiar contenedores y volúmenes
echo [3] Reconstruir imágenes desde cero
echo [4] Liberar puertos ocupados
echo [5] Ejecutar diagnóstico completo
echo [6] Reparación automática (recomendado)
echo [Q] Salir
echo.

set /p choice="Selecciona una opción: "

if /i "%choice%"=="1" goto RESTART_DOCKER
if /i "%choice%"=="2" goto CLEAN_CONTAINERS
if /i "%choice%"=="3" goto REBUILD_IMAGES
if /i "%choice%"=="4" goto FREE_PORTS
if /i "%choice%"=="5" goto FULL_DIAGNOSTIC
if /i "%choice%"=="6" goto AUTO_REPAIR
if /i "%choice%"=="Q" goto END_DIAG

echo ❌ Opción inválida
timeout /t 2 /nobreak >nul
goto END_DIAG

:RESTART_DOCKER
echo.
echo 🔄 Reiniciando Docker Desktop...
taskkill /f /im "Docker Desktop.exe" >nul 2>&1
timeout /t 5 /nobreak >nul
start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
echo ⏳ Esperando 60 segundos...
timeout /t 60 /nobreak >nul
goto END_DIAG

:CLEAN_CONTAINERS
echo.
echo 🧹 Limpiando contenedores y volúmenes...
docker-compose down --volumes --remove-orphans
docker system prune -af --volumes
echo ✅ Limpieza completada
goto END_DIAG

:REBUILD_IMAGES
echo.
echo 🔨 Reconstruyendo imágenes desde cero...
docker-compose down
docker-compose build --no-cache
echo ✅ Imágenes reconstruidas
goto END_DIAG

:FREE_PORTS
echo.
echo 🔓 Liberando puertos ocupados...
echo Buscando procesos en puertos 3306, 8000, 5173...
for %%p in (3306 8000 5173) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p "') do (
        echo Terminando proceso %%a en puerto %%p
        taskkill /f /pid %%a >nul 2>&1
    )
)
echo ✅ Puertos liberados
goto END_DIAG

:FULL_DIAGNOSTIC
echo.
echo 🔍 Ejecutando diagnóstico completo...
echo.
echo === Docker Info ===
docker info
echo.
echo === Docker Version ===
docker version
echo.
echo === Compose Version ===
docker-compose version
echo.
echo === System Resources ===
docker system df
echo.
echo === Running Containers ===
docker ps -a
echo.
pause
goto END_DIAG

:AUTO_REPAIR
echo.
echo 🔧 Iniciando reparación automática...
echo.
echo Paso 1: Deteniendo contenedores...
docker-compose down --remove-orphans
echo.
echo Paso 2: Limpiando recursos...
docker system prune -f
echo.
echo Paso 3: Liberando puertos...
for %%p in (3306 8000 5173) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%p " 2^>nul') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)
echo.
echo Paso 4: Reconstruyendo imágenes...
docker-compose build --no-cache backend frontend
echo.
echo Paso 5: Iniciando servicios...
docker-compose up -d
echo.
echo ✅ Reparación automática completada
echo.
echo 🔍 Verificando estado final...
timeout /t 10 /nobreak >nul
docker-compose ps
goto END_DIAG

:END_DIAG
echo.
echo ========================================
echo 📋 Si los problemas persisten:
echo ========================================
echo 1. Reinicia tu computadora
echo 2. Reinstala Docker Desktop
echo 3. Verifica que tengas permisos de administrador
echo 4. Contacta al equipo de desarrollo
echo.
pause
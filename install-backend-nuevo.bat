@echo off
setlocal enabledelayedexpansion
title Instalador Backend + MySQL (Nuevo)
color 0C

echo ===============================================
echo    INSTALADOR BACKEND + MYSQL (DESDE CERO)
echo ===============================================
echo.

:: Cambiar al directorio del script
cd /d "%~dp0"

:: Buscar carpeta backend si no estamos en ella
if not exist "requirements.txt" (
    if exist "backend\requirements.txt" (
        echo Cambiando a directorio backend...
        cd backend
    ) else (
        echo ERROR: No se encuentra la carpeta backend ni requirements.txt
        pause
        exit /b 1
    )
)

echo Directorio Backend: %CD%
echo.

:: Verificar Docker
echo Verificando Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no esta disponible
    echo Por favor instala Docker Desktop
    pause
    exit /b 1
)

docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker daemon no esta corriendo
    echo Por favor inicia Docker Desktop
    pause
    exit /b 1
)

echo OK: Docker esta listo
echo.

:: Verificar archivos necesarios
if not exist "Dockerfile" (
    echo ERROR: Dockerfile no encontrado
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ERROR: requirements.txt no encontrado
    pause
    exit /b 1
)

echo OK: Archivos necesarios encontrados
echo.

:: Configuracion de puertos
set backend_port=8000
set mysql_port=3307

echo Configuracion:
echo   Backend: Puerto %backend_port%
echo   MySQL:   Puerto %mysql_port% (3306 ocupado por MySQL del sistema)
echo.

:: Limpieza previa
echo Limpiando instalacion previa...
docker stop backend-app mysql 2>nul
docker rm backend-app mysql 2>nul
docker network rm backend-network 2>nul

:: Crear red Docker
echo Creando red Docker...
docker network create backend-network
if %errorlevel% neq 0 (
    echo ERROR: No se pudo crear la red Docker
    pause
    exit /b 1
)

:: Iniciar MySQL
echo Iniciando MySQL...
docker run -d ^
    --name mysql ^
    --network backend-network ^
    -p %mysql_port%:3306 ^
    -e MYSQL_ROOT_PASSWORD=backendpass ^
    -e MYSQL_DATABASE=propiedades_db ^
    -e MYSQL_USER=backend_user ^
    -e MYSQL_PASSWORD=backend_pass ^
    mysql:8.0

if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar MySQL
    echo Verificando si el puerto %mysql_port% esta ocupado...
    netstat -an | findstr ":%mysql_port%"
    pause
    exit /b 1
)

echo OK: MySQL iniciado
echo.

:: Esperar que MySQL este listo
echo Esperando que MySQL este listo...
timeout /t 30 /nobreak > nul

:: Verificar conexion a MySQL
echo Verificando conexion a MySQL...
:mysql_check
docker exec mysql mysql -uroot -pbackendpass -e "SELECT 1;" 2>nul
if %errorlevel% neq 0 (
    echo Esperando MySQL...
    timeout /t 5 /nobreak > nul
    goto mysql_check
)

echo OK: MySQL esta listo y acepta conexiones
echo.

:: Crear base de datos y ejecutar scripts
echo Configurando base de datos...
docker exec mysql mysql -uroot -pbackendpass -e "CREATE DATABASE IF NOT EXISTS propiedades_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

:: Ejecutar scripts de persistencia si existen
if exist "persistencia\" (
    echo Ejecutando scripts de inicializacion...
    for %%f in (persistencia\*.sql) do (
        echo   Ejecutando: %%f
        docker exec -i mysql mysql -uroot -pbackendpass propiedades_db < "%%f"
        if %errorlevel% equ 0 (
            echo   OK: %%f ejecutado
        ) else (
            echo   ADVERTENCIA: Error en %%f
        )
    )
)

echo OK: Base de datos configurada
echo.

:: Construir imagen del backend
echo Construyendo imagen del backend...
docker build -t backend-app .
if %errorlevel% neq 0 (
    echo ERROR: No se pudo construir la imagen del backend
    pause
    exit /b 1
)

echo OK: Imagen del backend construida
echo.

:: Iniciar contenedor del backend
echo Iniciando contenedor del backend...
docker run -d ^
    --name backend-app ^
    --network backend-network ^
    -p %backend_port%:%backend_port% ^
    -v "%CD%:/app" ^
    -e DB_HOST=mysql ^
    -e DB_PORT=3306 ^
    -e DB_USER=root ^
    -e DB_PASSWORD=backendpass ^
    -e DB_NAME=propiedades_db ^
    -e PYTHONPATH=/app ^
    -e PYTHONUNBUFFERED=1 ^
    backend-app

if %errorlevel% neq 0 (
    echo ERROR: No se pudo iniciar el contenedor del backend
    pause
    exit /b 1
)

echo OK: Backend iniciado
echo.

:: Esperar que el backend este listo
echo Esperando que el backend este listo...
timeout /t 20 /nobreak > nul

:: Verificar estado
echo Verificando estado de los contenedores...
docker ps --filter "name=backend-app" --filter "name=mysql"

echo.
echo ===============================================
echo    INSTALACION COMPLETADA EXITOSAMENTE
echo ===============================================
echo.

echo SERVICIOS DISPONIBLES:
echo   Backend API:      http://localhost:%backend_port%
echo   Documentacion:    http://localhost:%backend_port%/docs
echo   MySQL:            localhost:%mysql_port%
echo.

echo CREDENCIALES DE BASE DE DATOS:
echo   Host:             mysql (interno) / localhost:%mysql_port% (externo)
echo   Usuario root:     root / backendpass
echo   Usuario app:      backend_user / backend_pass
echo   Base de datos:    propiedades_db
echo.

echo COMANDOS UTILES:
echo.
echo   Ver logs del backend:
echo      docker logs -f backend-app
echo.
echo   Ver logs de MySQL:
echo      docker logs -f mysql
echo.
echo   Conectar a MySQL:
echo      docker exec -it mysql mysql -uroot -pbackendpass propiedades_db
echo.
echo   Detener todo:
echo      docker stop backend-app mysql
echo.
echo   Eliminar todo:
echo      docker rm backend-app mysql
echo      docker network rm backend-network
echo.

echo NOTAS:
echo   - Los archivos estan montados como volumen para desarrollo
echo   - Los cambios en el codigo se reflejan automaticamente
echo   - La base de datos persiste entre reinicios
echo.

:: Abrir documentacion
echo Abriendo documentacion de la API...
timeout /t 3 /nobreak > nul
start http://localhost:%backend_port%/docs

echo.
echo Sistema listo para desarrollo!
echo.

pause
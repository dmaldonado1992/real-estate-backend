@echo off
echo ====================================
echo   INICIANDO MYSQL EN DOCKER
echo ====================================
echo.

REM Paso 1: Eliminar contenedor anterior si existe
echo [1/5] Eliminando contenedor mysql-db anterior (si existe)...
docker rm -f mysql-db 2>nul
if %errorlevel% equ 0 (
    echo       Contenedor anterior eliminado
) else (
    echo       No habia contenedor anterior
)
echo.

REM Paso 2: Verificar que Docker este corriendo
echo [2/5] Verificando Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo       ERROR: Docker no esta corriendo. Inicia Docker Desktop.
    pause
    exit /b 1
)
echo       Docker OK
echo.

REM Paso 3: Crear contenedor MySQL con base de datos
echo [3/5] Creando contenedor MySQL (puede tardar si descarga la imagen)...
docker run --name mysql-db ^
    -e MYSQL_ROOT_PASSWORD=rootpassword ^
    -e MYSQL_DATABASE=propiedades_db ^
    -p 3306:3306 ^
    -v "%cd%\persistencia:/docker-entrypoint-initdb.d:ro" ^
    -d mysql:8.0

if %errorlevel% neq 0 (
    echo       ERROR: No se pudo crear el contenedor
    pause
    exit /b 1
)
echo       Contenedor creado exitosamente
echo.

REM Paso 4: Esperar a que MySQL este listo
echo [4/5] Esperando a que MySQL este listo (30 segundos)...
timeout /t 30 /nobreak >nul
echo       Tiempo de espera completado
echo.

REM Paso 5: Verificar logs
echo [5/5] Verificando logs de MySQL...
docker logs --tail 20 mysql-db
echo.

echo ====================================
echo   MYSQL INICIADO CORRECTAMENTE
echo ====================================
echo.
echo Conexion disponible en:
echo   Host: localhost
echo   Puerto: 3306
echo   Usuario: root
echo   Password: rootpassword
echo   Base de datos: propiedades_db
echo.
echo Para ver logs completos: docker logs -f mysql-db
echo Para detener: docker stop mysql-db
echo Para eliminar: docker rm -f mysql-db
echo.
pause

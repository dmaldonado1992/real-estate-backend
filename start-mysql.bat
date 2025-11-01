@echo off
echo ====================================
echo   INICIANDO MYSQL EN DOCKER
echo ====================================
echo.

REM Usar docker-compose desde backend/mysql
cd mysql

if not exist docker-compose.yml (
    echo ERROR: No se encontró docker-compose.yml en backend\mysql
    cd ..
    pause
    exit /b 1
)

echo [1/2] Deteniendo contenedores previos...
docker-compose down 2>nul

echo.
echo [2/2] Iniciando MySQL con docker-compose...
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo ERROR: No se pudo iniciar MySQL
    cd ..
    pause
    exit /b 1
)

echo.
echo ✅ MySQL iniciado correctamente
echo.
echo 📊 Información de conexión:
echo    Host: localhost
echo    Puerto: 3306
echo    Usuario: root
echo    Password: rootpassword
echo    Base de datos: propiedades_db
echo.
echo Comandos útiles:
echo    Ver logs: cd mysql; docker-compose logs -f
echo    Detener: cd mysql; docker-compose down
echo.

cd ..
pause

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

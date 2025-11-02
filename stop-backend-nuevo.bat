@echo off
echo.
echo ===============================================
echo    DETENIENDO BACKEND + MYSQL
echo ===============================================
echo.

echo Deteniendo contenedores...
docker stop backend-app mysql

echo Eliminando contenedores...
docker rm backend-app mysql

echo Eliminando red...
docker network rm backend-network

echo.
echo OK: Backend y MySQL detenidos completamente
echo.

pause
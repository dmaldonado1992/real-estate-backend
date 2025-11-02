@echo off
echo.
echo Deteniendo backend y MySQL...
echo.

echo Deteniendo contenedores...
docker stop backend-app 2>nul
docker stop mysql 2>nul

echo Eliminando contenedores...
docker rm backend-app 2>nul
docker rm mysql 2>nul

echo Eliminando red...
docker network rm backend-network 2>nul

echo.
echo OK: Backend detenido completamente
echo.
pause
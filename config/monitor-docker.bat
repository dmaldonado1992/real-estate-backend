@echo off
setlocal enabledelayedexpansion
echo ========================================
echo       MONITOR DE RECURSOS DOCKER
echo ========================================
echo.

REM Función para mostrar uso de memoria
:SHOW_STATS
cls
echo 📊 ESTADO ACTUAL - %DATE% %TIME%
echo ========================================
echo.

echo 🐳 Docker System Info:
docker system df 2>nul || echo ❌ Docker no disponible

echo.
echo 📦 Contenedores activos:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>nul || echo ❌ No se pueden obtener contenedores

echo.
echo 💾 Uso de memoria por contenedor:
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>nul || echo ❌ No se pueden obtener estadísticas

echo.
echo 🧹 Recursos para limpiar:
echo --- Imágenes sin usar ---
docker images --filter "dangling=true" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" 2>nul

echo.
echo --- Volúmenes sin usar ---
docker volume ls --filter "dangling=true" -q 2>nul | find /c /v "" > temp_count.txt
set /p unused_volumes=<temp_count.txt
del temp_count.txt
echo Volúmenes sin usar: !unused_volumes!

echo.
echo ========================================
echo 🛠️  OPCIONES:
echo ========================================
echo [1] Actualizar estadísticas (auto-refresh cada 10s)
echo [2] Limpiar recursos no utilizados
echo [3] Reiniciar contenedores problemáticos  
echo [4] Ver logs detallados
echo [5] Parar todo y limpiar completamente
echo [Q] Salir
echo.

if "%1"=="auto" (
    timeout /t 10 /nobreak >nul
    goto SHOW_STATS
)

set /p choice="Selecciona una opción: "

if /i "%choice%"=="1" (
    echo.
    echo 🔄 Iniciando monitoreo automático (Ctrl+C para detener)...
    timeout /t 3 /nobreak >nul
    "%~f0" auto
    goto END
)

if /i "%choice%"=="2" (
    echo.
    echo 🧹 Limpiando recursos no utilizados...
    docker system prune -f --volumes
    echo ✅ Limpieza completada
    timeout /t 3 /nobreak >nul
    goto SHOW_STATS
)

if /i "%choice%"=="3" (
    echo.
    echo 🔄 Reiniciando contenedores...
    docker-compose restart
    echo ✅ Contenedores reiniciados
    timeout /t 5 /nobreak >nul
    goto SHOW_STATS
)

if /i "%choice%"=="4" (
    echo.
    echo 📋 Logs detallados:
    echo.
    echo --- Backend ---
    docker-compose logs backend --tail=20
    echo.
    echo --- Frontend ---
    docker-compose logs frontend --tail=10
    echo.
    echo --- MySQL ---
    docker-compose logs mysql --tail=10
    echo.
    pause
    goto SHOW_STATS
)

if /i "%choice%"=="5" (
    echo.
    echo ⚠️  CUIDADO: Esto detendrá todos los contenedores y limpiará datos
    set /p confirm="¿Estás seguro? (S/N): "
    if /i "!confirm!"=="S" (
        echo 🛑 Deteniendo contenedores...
        docker-compose down --volumes --remove-orphans
        echo 🧹 Limpiando sistema...
        docker system prune -af --volumes
        echo ✅ Limpieza completa terminada
    ) else (
        echo ❌ Operación cancelada
    )
    timeout /t 3 /nobreak >nul
    goto SHOW_STATS
)

if /i "%choice%"=="Q" (
    goto END
)

echo ❌ Opción inválida
timeout /t 2 /nobreak >nul
goto SHOW_STATS

:END
echo.
echo 👋 ¡Hasta luego!
pause
@echo off
setlocal enabledelayedexpansion
title Diagnóstico Rápido - Docker & VSCode
color 0E
echo ========================================
echo   DIAGNOSTICO RAPIDO DEL SISTEMA
echo ========================================
echo   Versión 1.0 - Detección de Problemas
echo ========================================
echo.

echo 🔍 VERIFICANDO ESTADO DEL SISTEMA...
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0\..\.."
echo 📁 Directorio: %CD%
echo.

echo ========================================
echo   1. VERIFICACION WSL
echo ========================================
echo.

echo 🔍 Estado de WSL:
wsl --list --verbose 2>nul
if %errorlevel% neq 0 (
    echo ❌ WSL no disponible o no configurado
    echo 🔧 Solución: Ejecutar fix-docker-wsl-complete.bat
) else (
    echo ✅ WSL está funcionando
    
    echo.
    echo 🔍 Versión de WSL:
    wsl --version 2>nul || echo ℹ️  WSL versión antigua detectada
    
    echo.
    echo 🔍 Distribuciones instaladas:
    wsl --list --online | head -5 2>nul || echo ℹ️  No se pudo obtener lista en línea
)

echo.
echo ========================================
echo   2. VERIFICACION DOCKER
echo ========================================
echo.

echo 🔍 Versión de Docker:
docker --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker no disponible
    echo 🔧 Solución: Ejecutar fix-docker-wsl-complete.bat
) else (
    echo ✅ Docker instalado
    
    echo.
    echo 🔍 Estado de Docker:
    docker ps 2>nul
    if %errorlevel% neq 0 (
        echo ❌ Docker no está ejecutándose
        echo 🔧 Solución: Iniciar Docker Desktop
    ) else (
        echo ✅ Docker funcionando correctamente
        
        echo.
        echo 🔍 Contenedores del proyecto:
        docker-compose ps 2>nul || echo ℹ️  No hay contenedores iniciados
        
        echo.
        echo 🔍 Uso de recursos:
        docker system df 2>nul || echo ℹ️  No se pudo obtener información de recursos
    )
)

echo.
echo ========================================
echo   3. VERIFICACION SERVICIOS
echo ========================================
echo.

echo 🔍 Puerto 3306 (MySQL):
netstat -an | find ":3306" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ MySQL está escuchando en puerto 3306
) else (
    echo ❌ MySQL no está disponible en puerto 3306
)

echo 🔍 Puerto 8000 (Backend):
netstat -an | find ":8000" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend está escuchando en puerto 8000
) else (
    echo ❌ Backend no está disponible en puerto 8000
)

echo 🔍 Puerto 5173 (Frontend):
netstat -an | find ":5173" >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Frontend está escuchando en puerto 5173
) else (
    echo ❌ Frontend no está disponible en puerto 5173
)

echo.
echo ========================================
echo   4. VERIFICACION CONECTIVIDAD
echo ========================================
echo.

echo 🔍 Test Backend API:
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 3; 'Backend: HTTP ' + $response.StatusCode + ' - ' + $response.StatusDescription } catch { 'Backend: No responde o error de conexión' }" 2>nul

echo 🔍 Test Frontend:
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5173' -TimeoutSec 3; 'Frontend: HTTP ' + $response.StatusCode + ' - Disponible' } catch { 'Frontend: No responde o error de conexión' }" 2>nul

echo.
echo ========================================
echo   5. VERIFICACION ARCHIVOS
echo ========================================
echo.

echo 🔍 Archivos esenciales:
if exist "docker-compose.yml" (
    echo ✅ docker-compose.yml encontrado
) else (
    echo ❌ docker-compose.yml NO encontrado
)

if exist "backend\Dockerfile" (
    echo ✅ backend\Dockerfile encontrado
) else (
    echo ❌ backend\Dockerfile NO encontrado
)

if exist "frontend\Dockerfile" (
    echo ✅ frontend\Dockerfile encontrado
) else (
    echo ❌ frontend\Dockerfile NO encontrado
)

if exist "backend\requirements.txt" (
    echo ✅ backend\requirements.txt encontrado
) else (
    echo ❌ backend\requirements.txt NO encontrado
)

if exist "frontend\package.json" (
    echo ✅ frontend\package.json encontrado
) else (
    echo ❌ frontend\package.json NO encontrado
)

echo.
echo ========================================
echo   6. VERIFICACION VSCODE
echo ========================================
echo.

echo 🔍 Procesos de VS Code:
tasklist /FI "IMAGENAME eq Code.exe" 2>nul | find "Code.exe" >nul
if %errorlevel% equ 0 (
    echo ✅ VS Code está ejecutándose
    echo ℹ️  Extensiones relevantes:
    echo    - GitHub Copilot
    echo    - Docker
    echo    - WSL
    echo    - Python
    echo    - Vue.js
) else (
    echo ℹ️  VS Code no está ejecutándose actualmente
)

echo.
echo ========================================
echo   7. VERIFICACION SISTEMA
echo ========================================
echo.

echo 🔍 Memoria disponible:
powershell -Command "[math]::Round((Get-WmiObject -Class Win32_OperatingSystem).FreePhysicalMemory/1MB, 2)" 2>nul || echo "No disponible"

echo 🔍 Espacio en disco:
powershell -Command "Get-WmiObject -Class Win32_LogicalDisk | Where-Object {$_.DeviceID -eq 'C:'} | ForEach-Object {[math]::Round($_.FreeSpace/1GB, 2)}" 2>nul || echo "No disponible"

echo.
echo ========================================
echo     📋 RESUMEN Y RECOMENDACIONES
echo ========================================
echo.

REM Determinar estado general
set "issues_found=false"

wsl --list --verbose >nul 2>&1 || set "issues_found=true"
docker --version >nul 2>&1 || set "issues_found=true"
docker ps >nul 2>&1 || set "issues_found=true"

if "!issues_found!"=="true" (
    echo ❌ PROBLEMAS DETECTADOS
    echo.
    echo 🔧 SOLUCIONES RECOMENDADAS:
    echo.
    echo 1. 🚨 CRITICO - Ejecutar reparación completa:
    echo    fix-docker-wsl-complete.bat
    echo.
    echo 2. 🔄 Después del fix, reinicia el PC
    echo.
    echo 3. 🚀 Luego ejecuta:
    echo    start-docker-full.bat
    echo.
    echo 4. 📝 Si persisten problemas:
    echo    - Verificar antivirus
    echo    - Verificar permisos de administrador
    echo    - Comprobar conexión a internet
    echo.
) else (
    echo ✅ SISTEMA EN BUEN ESTADO
    echo.
    echo 🎯 TODO PARECE ESTAR FUNCIONANDO CORRECTAMENTE
    echo.
    echo 💡 ACCIONES RECOMENDADAS:
    echo.
    echo 1. 🌐 Abrir navegador en:
    echo    http://localhost:5173 (Frontend)
    echo    http://localhost:8000/docs (API Docs)
    echo.
    echo 2. 📝 En VS Code, GitHub Copilot debería funcionar
    echo.
    echo 3. 🔍 Si encuentras problemas específicos:
    echo    docker-compose logs -f
    echo.
)

echo ========================================
echo.
echo ⚡ Diagnóstico completado
echo.
pause
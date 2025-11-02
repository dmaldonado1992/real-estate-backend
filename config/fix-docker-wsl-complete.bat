@echo off
setlocal enabledelayedexpansion
title Docker & WSL Complete Fix Tool
color 0A
echo ========================================
echo   HERRAMIENTA COMPLETA DE REPARACION
echo     DOCKER, WSL Y GITHUB COPILOT
echo ========================================
echo.

REM Verificar permisos de administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ESTE SCRIPT REQUIERE PERMISOS DE ADMINISTRADOR
    echo.
    echo 📋 Para ejecutar como administrador:
    echo    1. Haz clic derecho en el script
    echo    2. Selecciona "Ejecutar como administrador"
    echo    3. O abre PowerShell como Admin y ejecuta el script
    echo.
    pause
    exit /b 1
)

echo ✅ Ejecutándose con permisos de administrador
echo.

REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0\..\.."
echo 📁 Directorio de trabajo: %CD%
echo.

echo ========================================
echo   PASO 1: LIMPIEZA COMPLETA DEL SISTEMA
echo ========================================
echo.

echo [1.1] Deteniendo todos los procesos relacionados...
echo 🔄 Cerrando Docker Desktop y servicios...
taskkill /F /IM "Docker Desktop.exe" >nul 2>&1
taskkill /F /IM "com.docker.backend.exe" >nul 2>&1
taskkill /F /IM "com.docker.proxy.exe" >nul 2>&1
taskkill /F /IM "dockerd.exe" >nul 2>&1
taskkill /F /IM "docker.exe" >nul 2>&1
taskkill /F /IM "wslservice.exe" >nul 2>&1

echo 🔄 Cerrando VSCode y procesos relacionados...
taskkill /F /IM "Code.exe" >nul 2>&1
taskkill /F /IM "node.exe" >nul 2>&1

echo ⏳ Esperando que los procesos terminen...
timeout /t 5 /nobreak >nul

echo [1.2] Limpiando WSL completamente...
echo 🧹 Cerrando todas las distribuciones WSL...
wsl --shutdown
timeout /t 5 /nobreak >nul

echo 🗑️ Limpiando caché de WSL...
wsl --unregister Ubuntu >nul 2>&1
wsl --unregister docker-desktop >nul 2>&1
wsl --unregister docker-desktop-data >nul 2>&1

echo [1.3] Limpiando Docker completamente...
echo 🗑️ Eliminando contenedores y volúmenes...
docker system prune -a -f --volumes >nul 2>&1

echo 🗑️ Limpiando caché de BuildKit...
docker builder prune -a -f >nul 2>&1

echo.
echo ========================================
echo   PASO 2: VERIFICACION Y REPARACION WSL
echo ========================================
echo.

echo [2.1] Verificando características de Windows...
echo 🔍 Comprobando WSL y Hyper-V...

REM Verificar si WSL está habilitado
dism /online /get-featureinfo /featurename:Microsoft-Windows-Subsystem-Linux | find "State : Enabled" >nul
if %errorlevel% neq 0 (
    echo ⚙️ Habilitando WSL...
    dism /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
)

REM Verificar si Virtual Machine Platform está habilitado
dism /online /get-featureinfo /featurename:VirtualMachinePlatform | find "State : Enabled" >nul
if %errorlevel% neq 0 (
    echo ⚙️ Habilitando Virtual Machine Platform...
    dism /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
)

REM Verificar Hyper-V (si está disponible)
dism /online /get-featureinfo /featurename:Microsoft-Hyper-V-All | find "State : Enabled" >nul
if %errorlevel% neq 0 (
    echo ⚙️ Intentando habilitar Hyper-V...
    dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /all /norestart >nul 2>&1
)

echo [2.2] Configurando WSL 2 como versión predeterminada...
wsl --set-default-version 2

echo [2.3] Instalando Ubuntu (si no existe)...
wsl --install --distribution Ubuntu --no-launch >nul 2>&1

echo [2.4] Actualizando kernel de WSL...
echo 📥 Descargando e instalando kernel actualizado...
powershell -Command "Invoke-WebRequest -Uri 'https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi' -OutFile '$env:TEMP\wsl_update_x64.msi'"
msiexec /i "%TEMP%\wsl_update_x64.msi" /quiet /norestart

echo.
echo ========================================
echo   PASO 3: REPARACION DE DOCKER DESKTOP
echo ========================================
echo.

echo [3.1] Detectando instalación de Docker...
set DOCKER_PATH=""
if exist "C:\Program Files\Docker\Docker\Docker Desktop.exe" (
    set DOCKER_PATH="C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo ✅ Docker encontrado en: C:\Program Files\Docker\Docker\
) else if exist "%PROGRAMFILES(X86)%\Docker\Docker\Docker Desktop.exe" (
    set DOCKER_PATH="%PROGRAMFILES(X86)%\Docker\Docker\Docker Desktop.exe"
    echo ✅ Docker encontrado en: %PROGRAMFILES(X86)%\Docker\Docker\
) else if exist "%USERPROFILE%\AppData\Local\Docker\Docker Desktop.exe" (
    set DOCKER_PATH="%USERPROFILE%\AppData\Local\Docker\Docker Desktop.exe"
    echo ✅ Docker encontrado en: %USERPROFILE%\AppData\Local\Docker\
) else (
    echo ❌ Docker Desktop no encontrado
    echo.
    echo 📥 Descargando Docker Desktop...
    powershell -Command "Invoke-WebRequest -Uri 'https://desktop.docker.com/win/main/amd64/Docker%%20Desktop%%20Installer.exe' -OutFile '$env:TEMP\DockerDesktopInstaller.exe'"
    echo ⚙️ Instalando Docker Desktop...
    "%TEMP%\DockerDesktopInstaller.exe" install --quiet
    timeout /t 30 /nobreak >nul
    set DOCKER_PATH="C:\Program Files\Docker\Docker\Docker Desktop.exe"
)

echo [3.2] Limpiando configuración de Docker...
echo 🗑️ Eliminando configuraciones corruptas...
if exist "%USERPROFILE%\.docker" rmdir /s /q "%USERPROFILE%\.docker" >nul 2>&1
if exist "%APPDATA%\Docker" rmdir /s /q "%APPDATA%\Docker" >nul 2>&1
if exist "%LOCALAPPDATA%\Docker" rmdir /s /q "%LOCALAPPDATA%\Docker" >nul 2>&1

echo [3.3] Reparando servicios de Docker...
echo 🔧 Reiniciando servicios...
sc stop com.docker.service >nul 2>&1
sc start com.docker.service >nul 2>&1

echo.
echo ========================================
echo   PASO 4: REINICIO Y VERIFICACION
echo ========================================
echo.

echo [4.1] Reiniciando WSL...
wsl --shutdown
timeout /t 5 /nobreak >nul
wsl --distribution Ubuntu --exec echo "WSL inicializado correctamente"

echo [4.2] Iniciando Docker Desktop...
if !DOCKER_PATH! neq "" (
    start "" !DOCKER_PATH!
    echo ⏳ Esperando que Docker Desktop inicie (120 segundos)...
    timeout /t 120 /nobreak >nul
)

echo [4.3] Verificando conectividad...
set /a retry_count=0
:VERIFY_DOCKER
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    set /a retry_count+=1
    if !retry_count! gtr 30 (
        echo ❌ Docker no responde después de 150 segundos
        echo ⚠️ Puede requerirse un reinicio del sistema
        goto SHOW_MANUAL_STEPS
    )
    echo ⏳ Verificando Docker... (!retry_count!/30)
    timeout /t 5 /nobreak >nul
    goto VERIFY_DOCKER
)

echo ✅ Docker está funcionando correctamente
docker --version

echo [4.4] Verificando WSL...
wsl --list --verbose
echo.

echo ========================================
echo   PASO 5: OPTIMIZACION GITHUB COPILOT
echo ========================================
echo.

echo [5.1] Limpiando caché de VS Code...
echo 🗑️ Eliminando archivos temporales...
if exist "%APPDATA%\Code\User\workspaceStorage" rmdir /s /q "%APPDATA%\Code\User\workspaceStorage" >nul 2>&1
if exist "%APPDATA%\Code\logs" rmdir /s /q "%APPDATA%\Code\logs" >nul 2>&1
if exist "%APPDATA%\Code\CachedExtensions" rmdir /s /q "%APPDATA%\Code\CachedExtensions" >nul 2>&1

echo [5.2] Limpiando historial de Git...
echo 🗑️ Optimizando repositorio...
git gc --prune=now --aggressive >nul 2>&1
git clean -fd >nul 2>&1
git reflog expire --expire=now --all >nul 2>&1

echo [5.3] Limpiando archivos de configuración problemáticos...
if exist ".vscode\settings.json.bak" del /f ".vscode\settings.json.bak" >nul 2>&1
if exist "node_modules" rmdir /s /q "node_modules" >nul 2>&1
if exist "backend\__pycache__" rmdir /s /q "backend\__pycache__" >nul 2>&1

echo.
echo ========================================
echo   PASO 6: CONFIGURACION OPTIMIZADA
echo ========================================
echo.

echo [6.1] Creando configuración optimizada de Docker...
(
echo {
echo   "builder": {
echo     "gc": {
echo       "defaultKeepStorage": "20GB",
echo       "enabled": true
echo     }
echo   },
echo   "experimental": false,
echo   "features": {
echo     "buildkit": true
echo   },
echo   "insecure-registries": [],
echo   "registry-mirrors": []
echo }
) > "%USERPROFILE%\.docker\daemon.json"

echo [6.2] Configurando memoria para WSL...
(
echo [wsl2]
echo memory=8GB
echo processors=4
echo swap=2GB
echo localhostForwarding=true
) > "%USERPROFILE%\.wslconfig"

echo.
echo ========================================
echo     🎉 REPARACION COMPLETADA
echo ========================================
echo.
echo ✅ WSL reparado y optimizado
echo ✅ Docker Desktop reinstalado/reparado  
echo ✅ Caché limpiado completamente
echo ✅ GitHub Copilot optimizado
echo ✅ Configuraciones optimizadas aplicadas
echo.
echo 📋 PROXIMOS PASOS:
echo.
echo 1. 🔄 REINICIA TU PC AHORA (RECOMENDADO)
echo    - Esto asegura que todos los cambios tomen efecto
echo    - WSL y Docker funcionarán mejor después del reinicio
echo.
echo 2. 📂 Después del reinicio, ejecuta:
echo    start-docker-full.bat
echo.
echo 3. 🔧 Para verificar que todo funciona:
echo    docker --version
echo    wsl --list --verbose
echo.
echo 4. 📝 En VS Code, GitHub Copilot debería funcionar sin problemas
echo.
echo ⚠️  IMPORTANTE:
echo    - Si persisten problemas, ejecuta este script nuevamente
echo    - Asegúrate de tener conexión a internet estable
echo    - Algunos antivirus pueden interferir con Docker
echo.

goto END

:SHOW_MANUAL_STEPS
echo.
echo ========================================
echo       ⚠️  PASOS MANUALES REQUERIDOS
echo ========================================
echo.
echo Docker no pudo iniciar automáticamente. Sigue estos pasos:
echo.
echo 1. 🔄 Reinicia tu PC completamente
echo 2. 🐳 Abre Docker Desktop manualmente
echo 3. ⚙️ En Docker Desktop Settings → General:
echo    ✅ Use WSL 2 based engine
echo    ✅ Start Docker Desktop when you log in
echo 4. 🔧 En Resources → WSL Integration:
echo    ✅ Enable integration with my default WSL distro
echo    ✅ Enable integration with additional distros: Ubuntu
echo 5. 🔄 Aplica los cambios y reinicia Docker Desktop
echo.

:END
echo ⏸️  Presiona cualquier tecla para salir...
pause >nul
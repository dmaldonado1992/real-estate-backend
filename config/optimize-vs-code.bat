@echo off
setlocal enabledelayedexpansion
title GitHub Copilot - Limpieza y Optimización
color 0A
echo ========================================
echo   GITHUB COPILOT - OPTIMIZACION
echo ========================================
echo   Limpieza de caché y configuraciones
echo ========================================
echo.

echo ⚠️  IMPORTANTE: Cierra VS Code antes de continuar
echo.
echo ¿Continuar con la limpieza? (S/N)
set /p choice="Respuesta: "
if /i "%choice%" neq "S" (
    echo Operación cancelada
    pause
    exit /b 0
)

echo.
echo 🔄 Cerrando procesos de VS Code...
taskkill /F /IM "Code.exe" >nul 2>&1
taskkill /F /IM "code.exe" >nul 2>&1
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   LIMPIEZA DE CACHE DE VSCODE
echo ========================================
echo.

echo [1/6] Limpiando workspace storage...
if exist "%APPDATA%\Code\User\workspaceStorage" (
    echo 🗑️ Eliminando workspaceStorage...
    rmdir /s /q "%APPDATA%\Code\User\workspaceStorage" >nul 2>&1
    echo ✅ Workspace storage limpiado
) else (
    echo ℹ️  Workspace storage no encontrado
)

echo [2/6] Limpiando logs...
if exist "%APPDATA%\Code\logs" (
    echo 🗑️ Eliminando logs antiguos...
    rmdir /s /q "%APPDATA%\Code\logs" >nul 2>&1
    echo ✅ Logs limpiados
) else (
    echo ℹ️  Logs no encontrados
)

echo [3/6] Limpiando caché de extensiones...
if exist "%APPDATA%\Code\CachedExtensions" (
    echo 🗑️ Eliminando caché de extensiones...
    rmdir /s /q "%APPDATA%\Code\CachedExtensions" >nul 2>&1
    echo ✅ Caché de extensiones limpiado
) else (
    echo ℹ️  Caché de extensiones no encontrado
)

echo [4/6] Limpiando archivos temporales...
if exist "%TEMP%\vscode-*" (
    echo 🗑️ Eliminando archivos temporales de VSCode...
    for /d %%i in ("%TEMP%\vscode-*") do rmdir /s /q "%%i" >nul 2>&1
    echo ✅ Archivos temporales limpiados
) else (
    echo ℹ️  Archivos temporales no encontrados
)

echo [5/6] Limpiando configuraciones problemáticas...
cd /d "%~dp0\..\.."
if exist ".vscode\settings.json.bak" (
    echo 🗑️ Eliminando backup de configuración...
    del /f ".vscode\settings.json.bak" >nul 2>&1
)

echo [6/6] Optimizando configuración de GitHub Copilot...
if not exist ".vscode" mkdir ".vscode"

echo 📝 Creando configuración optimizada...
(
echo {
echo   "github.copilot.enable": {
echo     "*": true,
echo     "yaml": true,
echo     "plaintext": false,
echo     "markdown": true,
echo     "javascript": true,
echo     "typescript": true,
echo     "python": true,
echo     "vue": true,
echo     "json": true,
echo     "html": true,
echo     "css": true,
echo     "scss": true
echo   },
echo   "github.copilot.advanced": {
echo     "debug.overrideEngine": "codex",
echo     "debug.testOverrideProxyUrl": "",
echo     "debug.overrideProxyUrl": ""
echo   },
echo   "editor.inlineSuggest.enabled": true,
echo   "editor.suggestSelection": "first",
echo   "editor.acceptSuggestionOnCommitCharacter": false,
echo   "editor.acceptSuggestionOnEnter": "on",
echo   "editor.quickSuggestions": {
echo     "other": true,
echo     "comments": true,
echo     "strings": true
echo   },
echo   "python.analysis.typeCheckingMode": "basic",
echo   "python.linting.enabled": true,
echo   "python.linting.pylintEnabled": false,
echo   "python.linting.flake8Enabled": true,
echo   "files.watcherExclude": {
echo     "**/.git/objects/**": true,
echo     "**/.git/subtree-cache/**": true,
echo     "**/node_modules/**": true,
echo     "**/__pycache__/**": true,
echo     "**/.pytest_cache/**": true
echo   },
echo   "files.exclude": {
echo     "**/__pycache__": true,
echo     "**/.pytest_cache": true,
echo     "**/node_modules": false
echo   }
echo }
) > ".vscode\settings.json"

echo ✅ Configuración optimizada creada

echo.
echo ========================================
echo   LIMPIEZA DEL PROYECTO
echo ========================================
echo.

echo 🗑️ Limpiando archivos de caché del proyecto...

if exist "backend\__pycache__" (
    echo   - Eliminando __pycache__ de backend...
    rmdir /s /q "backend\__pycache__" >nul 2>&1
)

if exist "backend\app\__pycache__" (
    echo   - Eliminando __pycache__ de app...
    rmdir /s /q "backend\app\__pycache__" >nul 2>&1
)

if exist "frontend\node_modules\.cache" (
    echo   - Eliminando caché de node_modules...
    rmdir /s /q "frontend\node_modules\.cache" >nul 2>&1
)

if exist ".pytest_cache" (
    echo   - Eliminando caché de pytest...
    rmdir /s /q ".pytest_cache" >nul 2>&1
)

echo ✅ Proyecto limpiado

echo.
echo ========================================
echo   OPTIMIZACION GIT
echo ========================================
echo.

echo 🔧 Optimizando repositorio Git...
git gc --prune=now --aggressive >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Repositorio Git optimizado
) else (
    echo ℹ️  Git no disponible o no es un repositorio
)

echo 🗑️ Limpiando reflog...
git reflog expire --expire=now --all >nul 2>&1

echo.
echo ========================================
echo     🎉 OPTIMIZACION COMPLETADA
echo ========================================
echo.
echo ✅ Caché de VS Code limpiado
echo ✅ Configuración de GitHub Copilot optimizada
echo ✅ Archivos temporales eliminados
echo ✅ Proyecto limpiado
echo ✅ Git optimizado
echo.
echo 🚀 SIGUIENTES PASOS:
echo.
echo 1. 📂 Abre VS Code en este directorio:
echo    code .
echo.
echo 2. 🔌 Verifica que GitHub Copilot esté activo:
echo    - Mira el ícono de Copilot en la barra de estado
echo    - Debería mostrar "GitHub Copilot: Ready"
echo.
echo 3. 🧪 Prueba GitHub Copilot:
echo    - Abre cualquier archivo .py o .js
echo    - Escribe un comentario describiendo una función
echo    - Copilot debería sugerir código automáticamente
echo.
echo 4. ⚙️ Si Copilot no funciona:
echo    - Ctrl+Shift+P → "GitHub Copilot: Sign In"
echo    - Reinicia VS Code
echo    - Verifica tu suscripción en github.com
echo.
echo 💡 CONSEJOS PARA MEJOR RENDIMIENTO:
echo.
echo   - Usa comentarios descriptivos para mejores sugerencias
echo   - Tab para aceptar sugerencias
echo   - Alt+] para ver siguiente sugerencia
echo   - Alt+[ para ver sugerencia anterior
echo   - Ctrl+Enter para abrir panel de sugerencias
echo.
echo 🎯 GitHub Copilot está ahora optimizado y listo para usar
echo.
pause
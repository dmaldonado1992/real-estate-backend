@echo off
setlocal enabledelayedexpansion

:: =====================================================
:: Configuracion de Ollama Cloud Models
:: Acceso a modelos potentes sin GPU
:: =====================================================

echo.
echo ====================================
echo   OLLAMA CLOUD - CONFIGURACION
echo ====================================
echo.

:check_signin
echo Verificando sesion de Ollama...
ollama list >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo Ollama no esta instalado o no esta corriendo.
    echo Descargalo desde: https://ollama.com/download
    pause
    exit /b 1
)

echo.
echo Para usar modelos en la nube, necesitas una cuenta en ollama.com
echo.
echo Opciones:
echo 1. Iniciar sesion o crear cuenta
echo 2. Continuar (si ya tienes sesion activa)
echo 3. Salir
echo.
set /p "opcion=Selecciona (1-3): "

if "%opcion%"=="1" goto signin
if "%opcion%"=="2" goto menu
if "%opcion%"=="3" exit /b 0
goto check_signin

:signin
echo.
echo Abriendo proceso de autenticacion...
echo.
ollama signin
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error en la autenticacion. Intentalo de nuevo.
    pause
    goto check_signin
)
echo.
echo Sesion iniciada correctamente!
timeout /t 3 >nul
goto menu

:menu
cls
echo.
echo ====================================
echo   OLLAMA CLOUD MODELS
echo ====================================
echo.
echo Modelos disponibles (sin necesidad de GPU):
echo.
echo 1. deepseek-v3.1:671b-cloud    - DeepSeek V3 (671B parametros)
echo 2. gpt-oss:20b-cloud           - GPT OSS 20B
echo 3. gpt-oss:120b-cloud          - GPT OSS 120B [RECOMENDADO]
echo 4. kimi-k2:1t-cloud            - Kimi K2 (1T parametros)
echo 5. qwen3-coder:480b-cloud      - Qwen3 Coder 480B (programacion)
echo 6. glm-4.6:cloud               - GLM 4.6
echo 7. minimax-m2:cloud            - MiniMax M2
echo 8. Salir
echo.
set /p "modelo_opcion=Selecciona un modelo (1-8): "

if "%modelo_opcion%"=="1" set "MODEL=deepseek-v3.1:671b-cloud"
if "%modelo_opcion%"=="2" set "MODEL=gpt-oss:20b-cloud"
if "%modelo_opcion%"=="3" set "MODEL=gpt-oss:120b-cloud"
if "%modelo_opcion%"=="4" set "MODEL=kimi-k2:1t-cloud"
if "%modelo_opcion%"=="5" set "MODEL=qwen3-coder:480b-cloud"
if "%modelo_opcion%"=="6" set "MODEL=glm-4.6:cloud"
if "%modelo_opcion%"=="7" set "MODEL=minimax-m2:cloud"
if "%modelo_opcion%"=="8" exit /b 0

if not defined MODEL goto menu

echo.
echo Modelo seleccionado: %MODEL%
echo.
echo Descargando modelo (solo la primera vez)...
ollama pull %MODEL%

if %ERRORLEVEL% neq 0 (
    echo.
    echo Error descargando el modelo. Verifica tu sesion.
    pause
    goto menu
)

echo.
echo.
echo ====================================
echo   CHAT CON %MODEL%
echo ====================================
echo.
echo Comandos disponibles:
echo   - "exit" o "salir" para cerrar
echo   - "clear" para limpiar pantalla
echo   - "modelo" para cambiar de modelo
echo.
echo ====================================
echo.

:chat_loop
set "prompt="
set /p "prompt=Tu: "

if "!prompt!"=="" goto chat_loop
if /i "!prompt!"=="exit" goto end
if /i "!prompt!"=="salir" goto end
if /i "!prompt!"=="clear" (cls & goto chat_loop)
if /i "!prompt!"=="limpiar" (cls & goto chat_loop)
if /i "!prompt!"=="modelo" goto menu

echo.
echo %MODEL%:
ollama run %MODEL% "!prompt!"
echo.
echo ------------------------------------
echo.

goto chat_loop

:end
echo.
echo Hasta luego!
pause
exit /b 0

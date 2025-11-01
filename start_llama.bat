@echo off
echo Iniciando servidor con Llama...
cd /d "C:\Users\Daniel Maldonado\Documents\vue\backend"

echo.
echo Verificando que Ollama este ejecutandose...
ollama list
if %errorlevel% neq 0 (
    echo Error: Ollama no esta ejecutandose
    echo Por favor inicia Ollama primero
    pause
    exit /b 1
)

echo.
echo Iniciando servidor FastAPI...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
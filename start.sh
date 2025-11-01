#!/bin/bash

echo "Iniciando aplicación FastAPI con limpieza automática..."

# Hacer el script de limpieza ejecutable
chmod +x /app/cleanup.sh

# Iniciar el script de limpieza en segundo plano
/app/cleanup.sh &
CLEANUP_PID=$!

echo "Script de limpieza iniciado con PID: $CLEANUP_PID"

# Función para manejar la terminación del contenedor
cleanup_on_exit() {
    echo "Deteniendo procesos..."
    kill $CLEANUP_PID 2>/dev/null
    exit 0
}

# Capturar señales de terminación
trap cleanup_on_exit SIGTERM SIGINT

# Inicializar base de datos
echo "Inicializando base de datos..."
python init_db.py

# Iniciar la aplicación FastAPI
echo "Iniciando servidor FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
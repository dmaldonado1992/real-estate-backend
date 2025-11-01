#!/bin/bash

# Script de limpieza AGRESIVA para archivos de paginación y temporales
# USAR SOLO SI EL PROBLEMA PERSISTE - Este script es más intensivo

echo "Iniciando script de limpieza AGRESIVA..."

while true; do
    # Limpiar archivos de paginación de Windows (búsqueda recursiva)
    find / -name "pagefile.sys" -type f -delete 2>/dev/null
    find / -name "swapfile.sys" -type f -delete 2>/dev/null
    find / -name "hiberfil.sys" -type f -delete 2>/dev/null
    
    # Limpiar archivos temporales masivamente
    find /app -name "*.tmp" -type f -delete 2>/dev/null
    find /app -name "*.temp" -type f -delete 2>/dev/null
    find /app -name "*.log" -type f -mmin +30 -delete 2>/dev/null
    
    # Limpiar archivos de Windows que no deberían estar en Linux
    find /app -name "Thumbs.db" -type f -delete 2>/dev/null
    find /app -name "desktop.ini" -type f -delete 2>/dev/null
    find /app -name "*.lnk" -type f -delete 2>/dev/null
    find /app -name "*.url" -type f -delete 2>/dev/null
    
    # Limpiar cache agresivamente
    find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    find /app -name "*.pyc" -type f -delete 2>/dev/null
    find /app -name "*.pyo" -type f -delete 2>/dev/null
    find /app -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null
    
    # Limpiar directorios temporales del sistema
    rm -rf /tmp/* 2>/dev/null
    rm -rf /var/tmp/* 2>/dev/null
    
    # Liberar memoria cache del sistema
    sync
    echo 1 > /proc/sys/vm/drop_caches 2>/dev/null
    
    # Log de actividad
    echo "$(date): Limpieza agresiva ejecutada - Memoria liberada"
    
    # Esperar 10 segundos
    sleep 10
done
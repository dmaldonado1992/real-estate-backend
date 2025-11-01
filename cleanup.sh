#!/bin/bash

# Script de limpieza automática para archivos de paginación y temporales
# Se ejecuta cada 10 segundos en segundo plano

echo "Iniciando script de limpieza automática..."

while true; do
    # Limpiar archivos de paginación de Windows si existen
    find /app -name "pagefile.sys" -type f -delete 2>/dev/null
    find /app -name "swapfile.sys" -type f -delete 2>/dev/null
    find /app -name "hiberfil.sys" -type f -delete 2>/dev/null
    
    # Limpiar archivos temporales comunes
    find /app -name "*.tmp" -type f -delete 2>/dev/null
    find /app -name "*.temp" -type f -delete 2>/dev/null
    find /app -name ".DS_Store" -type f -delete 2>/dev/null
    find /app -name "Thumbs.db" -type f -delete 2>/dev/null
    find /app -name "desktop.ini" -type f -delete 2>/dev/null
    
    # Limpiar archivos de log antiguos (más de 1 hora)
    find /app -name "*.log" -type f -mmin +60 -delete 2>/dev/null
    
    # Limpiar cache de Python
    find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    find /app -name "*.pyc" -type f -delete 2>/dev/null
    find /app -name "*.pyo" -type f -delete 2>/dev/null
    
    # Limpiar archivos temporales del sistema
    rm -rf /tmp/* 2>/dev/null
    
    # Información de limpieza (opcional, comentar si genera mucho ruido)
    # echo "$(date): Limpieza automática ejecutada"
    
    # Esperar 10 segundos antes de la siguiente ejecución
    sleep 10
done
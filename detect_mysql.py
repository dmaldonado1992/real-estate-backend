"""
Detector de MySQL y configuración automática
"""
import subprocess
import os
import sys
from pathlib import Path

def check_mysql_service():
    """Verificar si el servicio MySQL está ejecutándose"""
    try:
        # Verificar usando sc command en Windows
        result = subprocess.run(['sc', 'query', 'MySQL'], 
                              capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            print("✅ Servicio MySQL está ejecutándose")
            return True
        else:
            print("⚠️  Servicio MySQL no está ejecutándose")
            return False
    except:
        print("❌ No se pudo verificar el servicio MySQL")
        return False

def check_mysql_paths():
    """Buscar instalaciones de MySQL en rutas comunes"""
    mysql_paths = [
        r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe",
        r"C:\Program Files\MySQL\MySQL Server 5.7\bin\mysql.exe",
        r"C:\Program Files (x86)\MySQL\MySQL Server 8.0\bin\mysql.exe",
        r"C:\Program Files (x86)\MySQL\MySQL Server 5.7\bin\mysql.exe",
        r"C:\xampp\mysql\bin\mysql.exe",
        r"C:\wamp64\bin\mysql\mysql8.0.21\bin\mysql.exe",
        r"C:\laragon\bin\mysql\mysql-8.0.30-winx64\bin\mysql.exe"
    ]
    
    for path in mysql_paths:
        if os.path.exists(path):
            print(f"✅ MySQL encontrado en: {path}")
            return path
    
    print("❌ MySQL no encontrado en rutas estándar")
    return None

def check_docker_mysql():
    """Verificar si hay contenedores MySQL en Docker"""
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=mysql'], 
                              capture_output=True, text=True)
        if 'mysql' in result.stdout:
            print("✅ Contenedor MySQL encontrado en Docker")
            return True
    except:
        pass
    
    try:
        result = subprocess.run(['docker', 'ps', '--filter', 'name=propiedades_mysql'], 
                              capture_output=True, text=True)
        if 'propiedades_mysql' in result.stdout:
            print("✅ Contenedor propiedades_mysql encontrado")
            return True
    except:
        pass
    
    print("❌ No hay contenedores MySQL en Docker")
    return False

def suggest_installation():
    """Sugerir métodos de instalación"""
    print("\n📋 Opciones para instalar MySQL:")
    print("1. XAMPP (Recomendado para desarrollo):")
    print("   - Descarga: https://www.apachefriends.org/download.html")
    print("   - Incluye MySQL, Apache y phpMyAdmin")
    print()
    print("2. MySQL Community Server:")
    print("   - Descarga: https://dev.mysql.com/downloads/mysql/")
    print("   - Instalación oficial de MySQL")
    print()
    print("3. Docker (si funciona):")
    print("   - Ejecuta: docker-compose -f docker-compose-mysql.yml up -d")
    print()
    print("4. Chocolatey (con permisos de administrador):")
    print("   - Ejecuta PowerShell como administrador")
    print("   - Ejecuta: choco install mysql")
    print()

def main():
    print("🔍 Detectando MySQL en el sistema...")
    print()
    
    mysql_found = False
    
    # Verificar servicio
    if check_mysql_service():
        mysql_found = True
    
    # Verificar rutas de instalación
    mysql_path = check_mysql_paths()
    if mysql_path:
        mysql_found = True
    
    # Verificar Docker
    if check_docker_mysql():
        mysql_found = True
    
    if mysql_found:
        print("\n✅ MySQL está disponible en tu sistema")
        print("🚀 Puedes ejecutar: python setup_database.py")
        return True
    else:
        print("\n❌ MySQL no está disponible")
        suggest_installation()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
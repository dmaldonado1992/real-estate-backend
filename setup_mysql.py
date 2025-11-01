#!/usr/bin/env python3
"""
Script de inicialización de la base de datos MySQL únicamente
"""
import mysql.connector
import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Obtener el directorio del script
BASE_DIR = Path(__file__).parent
PERSISTENCIA_DIR = BASE_DIR / "persistencia"

def create_database_if_not_exists(connection, database_name):
    """Crear base de datos si no existe"""
    cursor = connection.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        cursor.execute(f"USE {database_name}")
        print(f"✅ Base de datos '{database_name}' lista")
        return True
    except mysql.connector.Error as e:
        print(f"❌ Error creando base de datos: {e}")
        return False
    finally:
        cursor.close()

def init_mysql_database():
    """Inicializar base de datos MySQL"""
    # Configuración de la base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'mysql'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
    }
    
    database_name = os.getenv('DB_NAME', 'propiedades_db')

    print("🐬 Inicializando base de datos MySQL...")
    print(f"📊 Host: {db_config['host']}:{db_config['port']}")
    print(f"👤 Usuario: {db_config['user']}")
    print(f"🗄️  Base de datos: {database_name}")

    try:
        # Conectar sin especificar base de datos para crearla si no existe
        print("🔌 Conectando a MySQL...")
        connection = mysql.connector.connect(**db_config)
        
        # Crear base de datos si no existe
        if not create_database_if_not_exists(connection, database_name):
            return False
        
        cursor = connection.cursor()
        
        print("📄 Ejecutando schema...")
        
        # Leer y ejecutar el schema
        schema_file = PERSISTENCIA_DIR / "01_schema.sql"
        if schema_file.exists():
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                # Ejecutar statement principal
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    if statement:
                        cursor.execute(statement)
                        print(f"  ✓ Ejecutado: {statement[:50]}...")
        else:
            print(f"⚠️  Archivo schema no encontrado: {schema_file}")

        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("🌱 Insertando datos de ejemplo...")
            # Leer y ejecutar los datos de semilla
            seed_file = PERSISTENCIA_DIR / "02_seed_data.sql"
            if seed_file.exists():
                with open(seed_file, 'r', encoding='utf-8') as f:
                    seed_sql = f.read()
                    # Encontrar solo los INSERT statements
                    statements = [s.strip() for s in seed_sql.split(';') if s.strip()]
                    insert_count = 0
                    for statement in statements:
                        if statement.upper().startswith('INSERT'):
                            try:
                                cursor.execute(statement)
                                insert_count += 1
                            except mysql.connector.Error as e:
                                print(f"⚠️  Error en INSERT: {e}")
                    print(f"  ✓ Ejecutados {insert_count} INSERT statements")
            else:
                print(f"⚠️  Archivo seed no encontrado: {seed_file}")
        else:
            print(f"📊 Base de datos ya contiene {count} registros")

        # Confirmar cambios
        connection.commit()

        # Verificar que los datos se insertaron
        cursor.execute("SELECT COUNT(*) FROM propiedades")
        result = cursor.fetchone()
        print(f"✅ Base de datos MySQL configurada con {result[0]} propiedades")

        # Mostrar algunas propiedades como ejemplo
        cursor.execute("SELECT id, titulo, tipo, precio FROM propiedades LIMIT 3")
        propiedades = cursor.fetchall()
        if propiedades:
            print("📋 Ejemplos de propiedades:")
            for prop in propiedades:
                print(f"  • ID: {prop[0]}, {prop[1]} ({prop[2]}) - ${prop[3]:,.2f}")

        cursor.close()
        connection.close()

        return True

    except mysql.connector.Error as e:
        error_code = e.errno if hasattr(e, 'errno') else 'N/A'
        print(f"❌ Error MySQL ({error_code}): {e}")
        
        if error_code == 1045:
            print("💡 Sugerencias:")
            print("   - Verificar usuario y contraseña en .env")
            print("   - Asegurar que MySQL esté corriendo")
            print("   - Probar conexión: mysql -u root -p")
        elif error_code == 2003:
            print("💡 Sugerencias:")
            print("   - Verificar que MySQL esté instalado y corriendo")
            print("   - Verificar host y puerto en .env")
        
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def check_mysql_installation():
    """Verificar si MySQL está instalado y accesible"""
    print("🔍 Verificando instalación de MySQL...")
    
    # Verificar si mysql está en PATH
    import subprocess
    try:
        result = subprocess.run(['mysql', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ MySQL encontrado: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    print("❌ MySQL no encontrado en PATH")
    print("💡 Para instalar MySQL:")
    print("   1. Descargar de: https://dev.mysql.com/downloads/installer/")
    print("   2. O usar Docker: docker run --name mysql -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 -d mysql:8.0")
    print("   3. O usar XAMPP: https://www.apachefriends.org/download.html")
    
    return False

def main():
    """Función principal"""
    print("🚀 Configurador de Base de Datos MySQL")
    print("=" * 50)
    
    # Verificar instalación de MySQL (comentado - intentaremos conectar directamente)
    # mysql_available = check_mysql_installation()
    # 
    # if not mysql_available:
    #     print("\n⚠️  MySQL no está disponible. Por favor instálalo primero.")
    #     return False
    
    print(f"\n📋 Configuración desde .env:")
    print(f"   Host: {os.getenv('DB_HOST', 'localhost')}")
    print(f"   Puerto: {os.getenv('DB_PORT', '3306')}")
    print(f"   Usuario: {os.getenv('DB_USER', 'root')}")
    print(f"   Base de datos: {os.getenv('DB_NAME', 'propiedades_db')}")
    
    # Intentar inicializar MySQL
    success = init_mysql_database()
    
    if success:
        print("\n🎉 ¡Base de datos MySQL configurada exitosamente!")
        print("\n📌 Próximos pasos:")
        print("   1. Verificar que el servidor backend se conecte correctamente")
        print("   2. Probar las APIs de propiedades")
        print("   3. Configurar el frontend para usar la API")
    else:
        print("\n💥 Falló la configuración de base de datos MySQL")
        print("\n🔧 Soluciones:")
        print("   1. Verificar que MySQL esté corriendo: net start mysql")
        print("   2. Verificar credenciales en .env")
        print("   3. Crear usuario: mysql -u root -p")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
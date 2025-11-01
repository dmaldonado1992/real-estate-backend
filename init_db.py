#!/usr/bin/env python3
"""
Script de inicialización de la base de datos MySQL
"""
import mysql.connector
import os
import time
from dotenv import load_dotenv

load_dotenv()

def wait_for_mysql(host, user, password, database, max_attempts=30):
    """Esperar a que MySQL esté disponible"""
    for attempt in range(max_attempts):
        try:
            connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            connection.close()
            print("✅ MySQL está listo!")
            return True
        except mysql.connector.Error as e:
            print(f"⏳ Esperando MySQL... intento {attempt + 1}/{max_attempts}")
            time.sleep(2)
    return False

def init_database():
    """Inicializar la base de datos con schema y datos"""
    # Configuración de la base de datos
    db_config = {
        'host': os.getenv('DB_HOST', 'mysql'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', 'rootpassword'),
        'database': os.getenv('DB_NAME', 'propiedades_db')
    }

    print("🚀 Inicializando base de datos...")

    # Esperar a que MySQL esté disponible
    if not wait_for_mysql(**db_config):
        print("❌ No se pudo conectar a MySQL")
        return False

    try:
        # Conectar a la base de datos
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        # Verificar si la tabla ya existe y tiene datos
        cursor.execute("SHOW TABLES LIKE 'propiedades'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM propiedades")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"✅ Base de datos ya inicializada con {count} propiedades")
                return True

        # Leer y ejecutar el schema
        print("📄 Creando tablas...")
        schema_path = '/app/persistencia/01_schema.sql'
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                # Ejecutar múltiples statements
                for statement in schema_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
        else:
            print(f"⚠️  Archivo de schema no encontrado: {schema_path}")

        # Leer y ejecutar los datos de semilla
        print("🌱 Insertando datos de ejemplo...")
        seed_path = '/app/persistencia/02_seed_data.sql'
        if os.path.exists(seed_path):
            with open(seed_path, 'r', encoding='utf-8') as f:
                seed_sql = f.read()
                # Ejecutar múltiples statements
                for statement in seed_sql.split(';'):
                    statement = statement.strip()
                    if statement:
                        cursor.execute(statement)
        else:
            print(f"⚠️  Archivo de datos no encontrado: {seed_path}")

        # Confirmar cambios
        connection.commit()

        # Verificar que los datos se insertaron
        cursor.execute("SELECT COUNT(*) as total FROM propiedades")
        result = cursor.fetchone()
        print(f"✅ Base de datos inicializada con {result[0]} propiedades")

        cursor.close()
        connection.close()

        return True

    except mysql.connector.Error as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
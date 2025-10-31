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
        'user': os.getenv('DB_USER', 'appuser'),
        'password': os.getenv('DB_PASSWORD', 'apppass'),
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

        # Leer y ejecutar el schema
        print("📄 Creando tablas...")
        with open('/app/persistencia/01_schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
            # Ejecutar múltiples statements
            for statement in schema_sql.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)

        # Leer y ejecutar los datos de semilla
        print("🌱 Insertando datos de ejemplo...")
        with open('/app/persistencia/02_seed_data.sql', 'r', encoding='utf-8') as f:
            seed_sql = f.read()
            # Ejecutar múltiples statements
            for statement in seed_sql.split(';'):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)

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
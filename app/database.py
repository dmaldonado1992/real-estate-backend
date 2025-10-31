"""
Módulo de conexión a la base de datos MySQL
"""
import mysql.connector
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'mysql'),
            'user': os.getenv('DB_USER', 'appuser'),
            'password': os.getenv('DB_PASSWORD', 'apppass'),
            'database': os.getenv('DB_NAME', 'propiedades_db')
        }
        self.connection = None

    def connect(self):
        """Establecer conexión con la base de datos"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            return True
        except mysql.connector.Error as e:
            print(f"Error conectando a MySQL: {e}")
            return False

    def disconnect(self):
        """Cerrar conexión con la base de datos"""
        if self.connection:
            self.connection.close()

    def get_all_properties(self) -> List[Dict[str, Any]]:
        """Obtener todas las propiedades"""
        if not self.connection:
            if not self.connect():
                return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, titulo as name, descripcion as description,
                       precio as price, habitaciones, banos, area_m2,
                       ubicacion as location, fecha_publicacion as fecha_publicacion,
                       imagen_url as image
                FROM propiedades
                ORDER BY fecha_publicacion DESC
            """)
            results = cursor.fetchall()
            cursor.close()
            return results
        except mysql.connector.Error as e:
            print(f"Error obteniendo propiedades: {e}")
            return []

    def get_property_by_id(self, property_id: int) -> Dict[str, Any]:
        """Obtener una propiedad por ID"""
        if not self.connection:
            if not self.connect():
                return None

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, titulo as name, descripcion as description,
                       precio as price, habitaciones, banos, area_m2,
                       ubicacion as location, fecha_publicacion as fecha_publicacion,
                       imagen_url as image
                FROM propiedades
                WHERE id = %s
            """, (property_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print(f"Error obteniendo propiedad {property_id}: {e}")
            return None

    def create_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crear una nueva propiedad"""
        if not self.connection:
            if not self.connect():
                return None

        try:
            cursor = self.connection.cursor()
            sql = """
                INSERT INTO propiedades
                (titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, ubicacion, fecha_publicacion, imagen_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                property_data.get('titulo', property_data.get('name', '')),
                property_data.get('descripcion', property_data.get('description', '')),
                property_data.get('tipo', 'casa'),
                property_data.get('precio', property_data.get('price', 0)),
                property_data.get('habitaciones', 0),
                property_data.get('banos', 0.0),
                property_data.get('area_m2', 0.0),
                property_data.get('ubicacion', property_data.get('location', '')),
                property_data.get('fecha_publicacion', property_data.get('fecha_publicacion')),
                property_data.get('imagen_url', property_data.get('image', ''))
            )

            cursor.execute(sql, values)
            self.connection.commit()

            # Obtener el ID generado
            property_id = cursor.lastrowid
            cursor.close()

            # Retornar la propiedad creada
            return self.get_property_by_id(property_id)

        except mysql.connector.Error as e:
            print(f"Error creando propiedad: {e}")
            return None

    def update_property(self, property_id: int, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar una propiedad existente"""
        if not self.connection:
            if not self.connect():
                return None

        try:
            cursor = self.connection.cursor()
            sql = """
                UPDATE propiedades
                SET titulo = %s, descripcion = %s, tipo = %s, precio = %s,
                    habitaciones = %s, banos = %s, area_m2 = %s, ubicacion = %s,
                    fecha_publicacion = %s, imagen_url = %s
                WHERE id = %s
            """
            values = (
                property_data.get('titulo', property_data.get('name', '')),
                property_data.get('descripcion', property_data.get('description', '')),
                property_data.get('tipo', 'casa'),
                property_data.get('precio', property_data.get('price', 0)),
                property_data.get('habitaciones', 0),
                property_data.get('banos', 0.0),
                property_data.get('area_m2', 0.0),
                property_data.get('ubicacion', property_data.get('location', '')),
                property_data.get('fecha_publicacion', property_data.get('fecha_publicacion')),
                property_data.get('imagen_url', property_data.get('image', '')),
                property_id
            )

            cursor.execute(sql, values)
            self.connection.commit()
            cursor.close()

            return self.get_property_by_id(property_id)

        except mysql.connector.Error as e:
            print(f"Error actualizando propiedad {property_id}: {e}")
            return None

    def delete_property(self, property_id: int) -> bool:
        """Eliminar una propiedad"""
        if not self.connection:
            if not self.connect():
                return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM propiedades WHERE id = %s", (property_id,))
            self.connection.commit()
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted
        except mysql.connector.Error as e:
            print(f"Error eliminando propiedad {property_id}: {e}")
            return False

# Instancia global de la base de datos
db = Database()
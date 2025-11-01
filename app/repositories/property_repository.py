"""
Property Repository Pattern
Implementa el patrón Repository para abstracción de acceso a datos
Sigue principios SOLID: SRP, OCP, DIP
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()


class IPropertyRepository(ABC):
    """
    Interface para el repositorio de propiedades (Interface Segregation Principle)
    Define el contrato que deben cumplir todas las implementaciones
    """
    
    @abstractmethod
    def find_all(self) -> Dict[str, Any]:
        """Obtener todas las propiedades con la query SQL utilizada"""
        pass
    
    @abstractmethod
    def find_by_id(self, property_id: int) -> Optional[Dict[str, Any]]:
        """Obtener una propiedad por ID"""
        pass
    
    @abstractmethod
    def create(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crear una nueva propiedad"""
        pass
    
    @abstractmethod
    def update(self, property_id: int, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualizar una propiedad existente"""
        pass
    
    @abstractmethod
    def delete(self, property_id: int) -> bool:
        """Eliminar una propiedad"""
        pass


class DatabaseConnection:
    """
    Manejo de conexión a base de datos (Single Responsibility Principle)
    Responsable únicamente de gestionar la conexión
    """
    
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'mysql'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', 'rootpassword'),
            'database': os.getenv('DB_NAME', 'propiedades_db')
        }
        self._connection = None
    
    @property
    def connection(self):
        """Obtener conexión, creándola si no existe"""
        if self._connection is None or not self._connection.is_connected():
            self._connect()
        return self._connection
    
    def _connect(self):
        """Establecer conexión con la base de datos"""
        try:
            self._connection = mysql.connector.connect(**self.config)
        except mysql.connector.Error as e:
            print(f"Error conectando a MySQL: {e}")
            raise
    
    def disconnect(self):
        """Cerrar conexión con la base de datos"""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            self._connection = None


class PropertyRepository(IPropertyRepository):
    """
    Implementación concreta del repositorio de propiedades
    Utiliza MySQL como almacenamiento de datos
    """
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Constructor con inyección de dependencias (Dependency Inversion Principle)
        Depende de abstracción (DatabaseConnection) no de implementación concreta
        """
        self.db = db_connection
    
    def find_all(self) -> Dict[str, Any]:
        """Obtener todas las propiedades ordenadas por fecha con la query SQL utilizada"""
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            sql_query = """
                SELECT id, titulo, descripcion, tipo, precio, 
                       habitaciones, banos, area_m2,
                       ubicacion, fecha_publicacion, imagen_url
                FROM propiedades
                ORDER BY fecha_publicacion DESC
            """
            cursor.execute(sql_query)
            results = cursor.fetchall()
            cursor.close()
            
            return {
                'properties': results,
                'sql': sql_query.strip()
            }
        except mysql.connector.Error as e:
            print(f"Error obteniendo propiedades: {e}")
            return {
                'properties': [],
                'sql': None
            }
    
    def find_by_id(self, property_id: int) -> Optional[Dict[str, Any]]:
        """Obtener una propiedad específica por ID"""
        try:
            cursor = self.db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, titulo, descripcion, tipo, precio,
                       habitaciones, banos, area_m2,
                       ubicacion, fecha_publicacion, imagen_url
                FROM propiedades
                WHERE id = %s
            """, (property_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except mysql.connector.Error as e:
            print(f"Error obteniendo propiedad {property_id}: {e}")
            return None
    
    def create(self, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Crear una nueva propiedad en la base de datos"""
        try:
            cursor = self.db.connection.cursor()
            sql = """
                INSERT INTO propiedades
                (titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, 
                 ubicacion, fecha_publicacion, imagen_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                property_data.get('titulo', ''),
                property_data.get('descripcion', ''),
                property_data.get('tipo', 'casa'),
                property_data.get('precio', 0),
                property_data.get('habitaciones', 0),
                property_data.get('banos', 0.0),
                property_data.get('area_m2', 0.0),
                property_data.get('ubicacion', ''),
                property_data.get('fecha_publicacion'),
                property_data.get('imagen_url', '')
            )
            
            cursor.execute(sql, values)
            self.db.connection.commit()
            
            property_id = cursor.lastrowid
            cursor.close()
            
            return self.find_by_id(property_id)
            
        except mysql.connector.Error as e:
            print(f"Error creando propiedad: {e}")
            return None
    
    def update(self, property_id: int, property_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Actualizar una propiedad existente"""
        try:
            cursor = self.db.connection.cursor()
            sql = """
                UPDATE propiedades
                SET titulo = %s, descripcion = %s, tipo = %s, precio = %s,
                    habitaciones = %s, banos = %s, area_m2 = %s, ubicacion = %s,
                    fecha_publicacion = %s, imagen_url = %s
                WHERE id = %s
            """
            values = (
                property_data.get('titulo', ''),
                property_data.get('descripcion', ''),
                property_data.get('tipo', 'casa'),
                property_data.get('precio', 0),
                property_data.get('habitaciones', 0),
                property_data.get('banos', 0.0),
                property_data.get('area_m2', 0.0),
                property_data.get('ubicacion', ''),
                property_data.get('fecha_publicacion'),
                property_data.get('imagen_url', ''),
                property_id
            )
            
            cursor.execute(sql, values)
            self.db.connection.commit()
            cursor.close()
            
            return self.find_by_id(property_id)
            
        except mysql.connector.Error as e:
            print(f"Error actualizando propiedad {property_id}: {e}")
            return None
    
    def delete(self, property_id: int) -> bool:
        """Eliminar una propiedad de la base de datos"""
        try:
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM propiedades WHERE id = %s", (property_id,))
            self.db.connection.commit()
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted
        except mysql.connector.Error as e:
            print(f"Error eliminando propiedad {property_id}: {e}")
            return False

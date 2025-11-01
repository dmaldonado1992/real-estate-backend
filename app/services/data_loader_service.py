"""
Servicio para carga de datos desde base de datos y JSON
"""
import json
import logging
import mysql.connector
from typing import Dict, List, Optional
from dotenv import load_dotenv
import os
from .sql_validation_service import SQLService

# Cargar variables de entorno desde .env
load_dotenv()

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, sql_service: SQLService):
        self.sql_service = sql_service

    def load_properties_from_db_or_json_with_query(self) -> dict:
        """
        Carga propiedades desde base de datos o JSON como fallback
        Retorna dict con propiedades y información de query
        """
        try:
            # Intentar cargar desde base de datos
            db_properties = self._load_from_database()
            if db_properties:
                return {
                    'properties': db_properties,
                    'data_source': 'database',
                    'user_query': None,
                    'generated_sql': None
                }
        except Exception as e:
            logger.warning(f"Error cargando desde DB: {e}")
        
        # Fallback a JSON
        json_properties = self._load_from_json()
        return {
            'properties': json_properties,
            'data_source': 'json',
            'user_query': None,
            'generated_sql': None
        }

    def load_properties_from_generated_query_with_info(self, user_query: str) -> dict:
        """
        Genera SQL con IA y ejecuta query en base de datos
        Retorna propiedades + información del query generado
        """
        try:
            # Generar SQL con IA
            sql_result = self.sql_service.generate_sql(user_query)
            
            if not sql_result['success']:
                logger.warning(f"No se pudo generar SQL: {sql_result.get('error')}")
                return {
                    'properties': [],
                    'data_source': 'none',
                    'user_query': user_query,
                    'generated_sql': None,
                    'error': 'No se pudo generar SQL'
                }
            
            generated_sql = sql_result['sql']
            logger.info(f"SQL generado para '{user_query}': {generated_sql}")
            
            # Ejecutar query en base de datos
            db_properties = self.execute_generated_query(generated_sql)
            
            if db_properties is not None:
                return {
                    'properties': db_properties,
                    'data_source': 'database',
                    'user_query': user_query,
                    'generated_sql': generated_sql
                }
            else:
                # Fallback a método normal si falla la ejecución
                logger.warning("Fallo ejecutando query generado, usando fallback")
                return {
                    'properties': self._load_from_json(),
                    'data_source': 'json',
                    'user_query': user_query,
                    'generated_sql': generated_sql,
                    'fallback_reason': 'Error ejecutando query en DB'
                }
                
        except Exception as e:
            logger.error(f"Error en load_properties_from_generated_query_with_info: {e}")
            return {
                'properties': self._load_from_json(),
                'data_source': 'json',
                'user_query': user_query,
                'generated_sql': None,
                'error': str(e)
            }

    def execute_generated_query(self, sql: str) -> Optional[List[Dict]]:
        """
        Ejecuta un query SQL generado por IA en la base de datos
        """
        if not self.sql_service.validate_sql(sql):
            logger.warning(f"SQL no válido o inseguro: {sql}")
            return None
        
        try:
            connection = self._get_db_connection()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute(sql)
            results = cursor.fetchall()
            
            # Convertir Decimal a float para JSON
            processed_results = []
            for row in results:
                processed_row = {}
                for key, value in row.items():
                    if hasattr(value, 'decimal'):  # Decimal type
                        processed_row[key] = float(value)
                    else:
                        processed_row[key] = value
                processed_results.append(processed_row)
            
            cursor.close()
            connection.close()
            
            logger.info(f"Query ejecutado exitosamente, {len(processed_results)} resultados")
            return processed_results
            
        except mysql.connector.Error as e:
            logger.error(f"Error ejecutando query generado: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado ejecutando query: {e}")
            return None

    def load_properties_from_db_or_json(self) -> list:
        """
        Carga propiedades desde base de datos con fallback a JSON
        Método simplificado que retorna solo la lista de propiedades
        """
        result = self.load_properties_from_db_or_json_with_query()
        return result.get('properties', [])

    def _load_from_database(self) -> Optional[List[Dict]]:
        """Carga propiedades desde MySQL"""
        try:
            connection = self._get_db_connection()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM propiedades ORDER BY fecha_publicacion DESC")
            properties = cursor.fetchall()
            
            # Convertir Decimal a float para JSON serialization
            processed_properties = []
            for prop in properties:
                processed_prop = {}
                for key, value in prop.items():
                    if hasattr(value, 'decimal'):  # Decimal type
                        processed_prop[key] = float(value)
                    else:
                        processed_prop[key] = value
                processed_properties.append(processed_prop)
            
            cursor.close()
            connection.close()
            
            logger.info(f"Cargadas {len(processed_properties)} propiedades desde DB")
            return processed_properties
            
        except mysql.connector.Error as e:
            logger.error(f"Error conectando a base de datos: {e}")
            return None

    def _load_from_json(self) -> List[Dict]:
        """Carga propiedades desde archivo JSON"""
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'products.json')
            
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
                # El JSON puede ser un array directamente o tener una clave 'propiedades'
                if isinstance(data, list):
                    properties = data
                elif isinstance(data, dict) and 'propiedades' in data:
                    properties = data['propiedades']
                else:
                    logger.error(f"Formato de JSON no reconocido: {type(data)}")
                    return []
                
                logger.info(f"Cargadas {len(properties)} propiedades desde JSON")
                return properties
        except Exception as e:
            logger.error(f"Error cargando desde JSON: {e}")
            return []

    def _get_db_connection(self):
        """Obtiene conexión a base de datos MySQL"""
        try:
            connection = mysql.connector.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                database=os.getenv('DB_NAME', 'propiedades_db'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', 'rootpassword'),
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            return connection
        except Exception as e:
            logger.error(f"No se pudo conectar a la base de datos: {e}")
            return None
"""
Property Service Layer
Implementa la lógica de negocio separada del acceso a datos
Sigue principios SOLID: SRP, OCP, DIP
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import date
from ..models import Product
from ..repositories.property_repository import IPropertyRepository


class IPropertyService(ABC):
    """
    Interface para el servicio de propiedades (Interface Segregation Principle)
    Define el contrato de operaciones de negocio
    """
    
    @abstractmethod
    def get_all_properties(self) -> Dict[str, Any]:
        """Obtener todas las propiedades con información SQL"""
        pass
    
    @abstractmethod
    def get_property_by_id(self, property_id: int) -> Optional[Product]:
        """Obtener una propiedad por ID"""
        pass
    
    @abstractmethod
    def create_property(self, product: Product) -> Optional[Product]:
        """Crear una nueva propiedad"""
        pass
    
    @abstractmethod
    def update_property(self, property_id: int, product: Product) -> Optional[Product]:
        """Actualizar una propiedad existente"""
        pass
    
    @abstractmethod
    def delete_property(self, property_id: int) -> bool:
        """Eliminar una propiedad"""
        pass


class DateConverter:
    """
    Conversor de fechas (Single Responsibility Principle)
    Responsable únicamente de conversión de fechas
    """
    
    @staticmethod
    def to_date(date_value) -> Optional[date]:
        """Convertir valor a objeto date"""
        if date_value is None:
            return None
        if isinstance(date_value, date):
            return date_value
        if isinstance(date_value, str):
            return date.fromisoformat(date_value)
        return None


class PropertyMapper:
    """
    Mapper de propiedades (Single Responsibility Principle)
    Responsable de transformar entre diccionarios y modelos
    """
    
    @staticmethod
    def to_product(property_dict: dict) -> Product:
        """Convertir diccionario a modelo Product"""
        if not property_dict:
            return None
        
        # Convertir fecha si es necesario
        fecha_pub = DateConverter.to_date(property_dict.get('fecha_publicacion'))
        
        return Product(
            id=property_dict.get('id'),
            titulo=property_dict.get('titulo', ''),
            descripcion=property_dict.get('descripcion', ''),
            tipo=property_dict.get('tipo', 'casa'),
            precio=property_dict.get('precio', 0.0),
            habitaciones=property_dict.get('habitaciones', 0),
            banos=property_dict.get('banos', 0.0),
            area_m2=property_dict.get('area_m2', 0.0),
            ubicacion=property_dict.get('ubicacion', ''),
            fecha_publicacion=fecha_pub,
            imagen_url=property_dict.get('imagen_url', '')
        )
    
    @staticmethod
    def to_dict(product: Product) -> dict:
        """Convertir modelo Product a diccionario"""
        product_dict = product.model_dump()
        
        # Asegurar que la fecha esté en formato correcto
        if product_dict.get('fecha_publicacion'):
            if isinstance(product_dict['fecha_publicacion'], date):
                product_dict['fecha_publicacion'] = product_dict['fecha_publicacion'].isoformat()
        
        return product_dict


class PropertyService(IPropertyService):
    """
    Implementación del servicio de propiedades
    Contiene la lógica de negocio y coordina operaciones
    """
    
    def __init__(self, repository: IPropertyRepository):
        """
        Constructor con inyección de dependencias (Dependency Inversion Principle)
        Depende de la abstracción IPropertyRepository, no de implementación concreta
        """
        self.repository = repository
        self.mapper = PropertyMapper()
    
    def get_all_properties(self) -> Dict[str, Any]:
        """
        Obtener todas las propiedades como modelos Product con información SQL
        Aplica lógica de negocio (ordenamiento, transformación)
        Con fallback a JSON si no hay datos en BD
        """
        repository_result = self.repository.find_all()
        properties_dict = repository_result.get('properties', [])
        sql_query = repository_result.get('sql')
        
        # Si no hay propiedades, intentar cargar desde JSON
        if not properties_dict or len(properties_dict) == 0:
            import json
            import os
            
            try:
                json_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.json')
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        print(f"PropertyService: Cargando {len(json_data)} propiedades desde JSON como fallback")
                        properties_dict = json_data
                        sql_query = "Datos cargados desde archivo JSON (fallback)"
            except Exception as e:
                print(f"Error al cargar JSON fallback en PropertyService: {e}")
                properties_dict = []
                sql_query = "Error al cargar datos"
        
        products = [self.mapper.to_product(prop) for prop in properties_dict]
        
        return {
            'products': products,
            'sql': sql_query
        }
    
    def get_property_by_id(self, property_id: int) -> Optional[Product]:
        """
        Obtener una propiedad específica por ID
        Retorna None si no existe
        """
        property_dict = self.repository.find_by_id(property_id)
        if not property_dict:
            return None
        return self.mapper.to_product(property_dict)
    
    def create_property(self, product: Product) -> Optional[Product]:
        """
        Crear una nueva propiedad
        Aplica reglas de negocio (fecha por defecto, validaciones)
        """
        # Aplicar fecha actual si no se proporciona
        if not product.fecha_publicacion:
            product.fecha_publicacion = date.today()
        
        # Convertir a diccionario para el repositorio
        property_data = self.mapper.to_dict(product)
        
        # Crear en el repositorio
        created_property = self.repository.create(property_data)
        
        if not created_property:
            return None
        
        return self.mapper.to_product(created_property)
    
    def update_property(self, property_id: int, product: Product) -> Optional[Product]:
        """
        Actualizar una propiedad existente
        Valida que la propiedad exista antes de actualizar
        """
        # Verificar que la propiedad existe
        existing = self.repository.find_by_id(property_id)
        if not existing:
            return None
        
        # Convertir a diccionario para el repositorio
        property_data = self.mapper.to_dict(product)
        
        # Actualizar en el repositorio
        updated_property = self.repository.update(property_id, property_data)
        
        if not updated_property:
            return None
        
        return self.mapper.to_product(updated_property)
    
    def delete_property(self, property_id: int) -> bool:
        """
        Eliminar una propiedad
        Retorna True si se eliminó correctamente
        """
        return self.repository.delete(property_id)

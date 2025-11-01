"""
Dependency Injection Container
Gestiona la creación e inyección de dependencias
Sigue el principio de Inversión de Dependencias (DIP)
"""
from functools import lru_cache
from .repositories.property_repository import PropertyRepository, DatabaseConnection, IPropertyRepository
from .services.property_service import PropertyService, IPropertyService


class DependencyContainer:
    """
    Contenedor de dependencias (Singleton Pattern)
    Centraliza la creación de instancias y gestión del ciclo de vida
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._db_connection = None
        self._property_repository = None
        self._property_service = None
        self._initialized = True
    
    @property
    def db_connection(self) -> DatabaseConnection:
        """Obtener instancia de conexión a base de datos"""
        if self._db_connection is None:
            self._db_connection = DatabaseConnection()
        return self._db_connection
    
    @property
    def property_repository(self) -> IPropertyRepository:
        """Obtener instancia de repositorio de propiedades"""
        if self._property_repository is None:
            self._property_repository = PropertyRepository(self.db_connection)
        return self._property_repository
    
    @property
    def property_service(self) -> IPropertyService:
        """Obtener instancia de servicio de propiedades"""
        if self._property_service is None:
            self._property_service = PropertyService(self.property_repository)
        return self._property_service


# Instancia global del contenedor
_container = DependencyContainer()


@lru_cache()
def get_property_service() -> IPropertyService:
    """
    Función de inyección de dependencias para FastAPI
    Retorna el servicio de propiedades configurado
    
    Uso en rutas:
        @router.get("/api/products")
        async def get_products(service: IPropertyService = Depends(get_property_service)):
            return service.get_all_properties()
    """
    return _container.property_service

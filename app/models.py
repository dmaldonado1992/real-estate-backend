from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict, Any, List

from datetime import datetime

class Product(BaseModel):
    id: int = None
    titulo: str
    descripcion: str
    tipo: str
    precio: float
    habitaciones: int
    banos: float
    area_m2: float
    ubicacion: str
    fecha_publicacion: date = None
    imagen_url: str


class SearchIARequest(BaseModel):
    query: str
    context: Optional[str] = None
    use_cloud: bool = True


class SearchIAResponse(BaseModel):
    response: str
    metadata: Dict[str, Any]


class SearchRealStateRequest(BaseModel):
    query: str
    use_cloud: bool = True


class SearchRealStateResponse(BaseModel):
    properties: List[Dict[str, Any]]
    keywords: List[str]
    analysis: str
    metadata: Dict[str, Any]
from pydantic import BaseModel
from datetime import date

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
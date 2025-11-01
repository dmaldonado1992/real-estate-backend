"""
Servicio LLM simplificado - SOLO HEURÍSTICAS para evitar problemas de memoria.
"""
from typing import List
import os
import json
import re
from datetime import datetime, timedelta


class LLMService:
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        self.provider = "heuristics_only"
        print(f"LLMService: Modo simplificado (solo heurísticas) para evitar OOM")

    async def test_connection(self) -> bool:
        return True

    async def get_product_description(self, product_name: str) -> str:
        return f"Descripción de {product_name}"

    async def get_product_recommendations(self, product_description: str, num_recommendations: int = 3) -> List[str]:
        return [f"Recomendación {i+1}" for i in range(num_recommendations)]

    async def search_con_ia(self, query: str, context: str = None, use_cloud: bool = True) -> dict:
        """
        Búsqueda con respuestas predefinidas - SIN LLM para evitar OOM.
        """
        
        # Respuestas simples basadas en keywords
        responses = {
            "casa": "Tenemos casas disponibles en diferentes ubicaciones con excelentes acabados.",
            "apartamento": "Contamos con apartamentos modernos y cómodos en las mejores zonas.",
            "terreno": "Disponemos de terrenos en zonas exclusivas, ideales para inversión.",
            "precio": "Nuestros precios son competitivos y tenemos opciones para todos los presupuestos.",
            "habitaciones": "Ofrecemos propiedades con 1, 2, 3 y 4 habitaciones según tus necesidades.",
            "baños": "Todas nuestras propiedades tienen baños modernos y funcionales.",
            "ubicacion": "Tenemos propiedades en las mejores ubicaciones de la ciudad."
        }
        
        query_lower = query.lower()
        response = "Gracias por contactarnos. "
        
        for keyword, resp in responses.items():
            if keyword in query_lower:
                response = resp
                break
        else:
            response = "Te ayudaremos a encontrar la propiedad perfecta para ti."
        
        return {
            "response": response,
            "metadata": {
                "model_used": "simple_responses",
                "query": query[:50]
            },
            "properties": [],
            "keywords": []
        }
    
    async def search_ia_real_state(self, query: str, use_cloud: bool = True) -> dict:
        """
        Búsqueda de propiedades usando SOLO heurísticas - SIN LLM para evitar OOM.
        """
        print(f"🔍 Búsqueda: {query}")
        
        # Parsear criterios usando heurísticas locales
        criteria = self._parse_query_heuristics(query)
        keywords = criteria.get('keywords', [])
        
        # Cargar propiedades del JSON (máximo 16 para evitar OOM)
        all_properties = self._load_properties_json()
        
        if not all_properties:
            return {
                "properties": [],
                "keywords": keywords,
                "analysis": "No hay propiedades disponibles.",
                "metadata": {"total_properties": 0, "criteria": criteria}
            }
        
        # Filtrar propiedades (máximo 5 resultados)
        filtered_properties = self._filter_properties(all_properties, criteria, keywords)
        
        # Generar análisis
        analysis = self._generate_analysis(filtered_properties, criteria)
        
        return {
            "properties": filtered_properties,
            "keywords": keywords[:3],
            "analysis": analysis,
            "metadata": {
                "model_used": "heuristics_only",
                "total_properties_db": len(all_properties),
                "filtered_properties": len(filtered_properties),
                "criteria": criteria
            }
        }
    
    def _parse_query_heuristics(self, query: str) -> dict:
        """Extraer criterios usando expresiones regulares."""
        ql = query.lower()
        criteria = {}
        
        # Precio (entre X y Y)
        m = re.search(r"entre\s+\$?\s*([0-9\.,]+)\s*(?:y|a)\s*\$?\s*([0-9\.,]+)", ql)
        if m:
            try:
                n1 = float(m.group(1).replace(',', ''))
                n2 = float(m.group(2).replace(',', ''))
                criteria['precio_min'] = min(n1, n2)
                criteria['precio_max'] = max(n1, n2)
            except:
                pass
        
        # Precio máximo (menos de / hasta)
        if 'precio_max' not in criteria:
            m = re.search(r"(?:menos de|hasta)\s+\$?\s*([0-9\.,]+)", ql)
            if m:
                try:
                    criteria['precio_max'] = float(m.group(1).replace(',', ''))
                except:
                    pass
        
        # Habitaciones
        m = re.search(r"(\d+)\s+habitaciones", ql)
        if m:
            criteria['habitaciones'] = int(m.group(1))
        
        # Baños
        m = re.search(r"(\d+(?:\.\d+)?)\s+ba[ñn]os", ql)
        if m:
            criteria['banos'] = float(m.group(1))
        
        # Zona
        m = re.search(r"zona\s*(\d{1,3})", ql)
        if m:
            criteria['ubicacion'] = f"zona {m.group(1)}"
        
        # Tipo de propiedad
        if "casa" in ql:
            criteria['tipo'] = "casa"
        elif "apartamento" in ql or "departamento" in ql:
            criteria['tipo'] = "departamento"
        elif "terreno" in ql:
            criteria['tipo'] = "terreno"
        
        # Keywords como fallback
        criteria['keywords'] = [w for w in re.findall(r"\w+", ql) if len(w) > 3][:5]
        
        return criteria
    
    def _load_properties_json(self) -> list:
        """Cargar propiedades del JSON (máximo 16)."""
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'products.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            properties = []
            for item in json_data[:16]:  # Máximo 16 para evitar OOM
                try:
                    properties.append({
                        'id': item.get('id'),
                        'titulo': item.get('titulo', '')[:80],
                        'descripcion': item.get('descripcion', '')[:150],
                        'tipo': item.get('tipo', ''),
                        'precio': float(item.get('precio', 0) or 0),
                        'habitaciones': int(item.get('habitaciones', 0) or 0),
                        'banos': float(item.get('banos', 0) or 0),
                        'area_m2': float(item.get('area_m2', 0) or 0),
                        'ubicacion': item.get('ubicacion', '')[:40],
                        'fecha_publicacion': item.get('fecha_publicacion'),
                        'imagen_url': item.get('imagen_url', '')[:150]
                    })
                except:
                    continue
            
            return properties
        except Exception as e:
            print(f"Error cargando JSON: {e}")
            return []
    
    def _filter_properties(self, properties: list, criteria: dict, keywords: list) -> list:
        """Filtrar propiedades según criterios (máximo 5 resultados)."""
        filtered = []
        
        for prop in properties:
            if len(filtered) >= 5:  # Máximo 5 resultados
                break
            
            matches = True
            
            # Filtro por ubicación
            if criteria.get('ubicacion'):
                ubicacion_prop = (prop.get('ubicacion') or '').lower()
                ubicacion_busqueda = str(criteria.get('ubicacion')).lower()
                if ubicacion_busqueda not in ubicacion_prop:
                    matches = False
            
            # Filtro por precio
            if matches and criteria.get('precio_min'):
                if prop.get('precio', 0) < criteria['precio_min']:
                    matches = False
            
            if matches and criteria.get('precio_max'):
                if prop.get('precio', 0) > criteria['precio_max']:
                    matches = False
            
            # Filtro por habitaciones
            if matches and criteria.get('habitaciones'):
                if prop.get('habitaciones', 0) != criteria['habitaciones']:
                    matches = False
            
            # Filtro por baños
            if matches and criteria.get('banos'):
                if prop.get('banos', 0) < criteria['banos']:
                    matches = False
            
            # Filtro por tipo
            if matches and criteria.get('tipo'):
                tipo_prop = (prop.get('tipo') or '').lower()
                if criteria['tipo'].lower() not in tipo_prop:
                    matches = False
            
            if matches:
                filtered.append(prop)
        
        return filtered
    
    def _generate_analysis(self, filtered_properties: list, criteria: dict) -> str:
        """Generar análisis descriptivo."""
        if not filtered_properties:
            return "No encontramos propiedades con esos criterios. Intenta ampliar tu búsqueda."
        
        descripcion = []
        if criteria.get('ubicacion'):
            descripcion.append(f"en {criteria['ubicacion']}")
        if criteria.get('habitaciones'):
            descripcion.append(f"con {criteria['habitaciones']} habitaciones")
        if criteria.get('precio_max'):
            descripcion.append(f"hasta ${int(criteria['precio_max']):,}")
        if criteria.get('tipo'):
            descripcion.append(f"tipo {criteria['tipo']}")
        
        if descripcion:
            return f"Encontramos {len(filtered_properties)} propiedades {' '.join(descripcion)}."
        else:
            return f"Encontramos {len(filtered_properties)} propiedades que coinciden con tu búsqueda."
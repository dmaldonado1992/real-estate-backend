"""
Servicio para búsqueda y filtrado de propiedades inmobiliarias
"""
import re
import logging
from typing import List, Dict, Optional
from .ollama_client_service import OllamaClient

logger = logging.getLogger(__name__)

class PropertySearchService:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    async def search_ia(self, query: str, properties_context: str = None) -> str:
        """
        Búsqueda básica usando IA
        """
        try:
            if properties_context:
                prompt = f"""
                Basándote en estas propiedades disponibles:
                {properties_context}
                
                Responde a esta consulta del usuario: "{query}"
                
                Proporciona una respuesta útil y específica sobre las propiedades que mejor coincidan.
                """
            else:
                prompt = f"Consulta sobre propiedades inmobiliarias: {query}"
            
            system_prompt = "Eres un experto en bienes raíces que ayuda a encontrar propiedades. Responde de manera amigable y profesional."
            
            response = await self.ollama_client.ask_ai_direct(prompt, system_prompt)
            return response if response else "No se pudo procesar la consulta"
            
        except Exception as e:
            logger.error(f"Error en search_ia: {e}")
            return f"Error procesando consulta: {str(e)}"

    def filter_exact_matches(self, properties: list, query: str) -> list:
        """
        Aplica filtros exactos basados en la consulta del usuario
        """
        if not properties or not query:
            return properties
        
        query_lower = query.lower()
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        numbers = [float(n) for n in numbers]
        
        # Extraer filtros de la consulta
        filters = self._extract_filters(query_lower, numbers)
        
        if not filters:
            return properties
        
        # Aplicar filtros estrictos
        filtered = []
        for prop in properties:
            if self._matches_strict_filters(prop, filters):
                filtered.append(prop)
        
        logger.info(f"Filtros aplicados: {filters}, propiedades filtradas: {len(filtered)}")
        return filtered

    def _extract_filters(self, query_lower: str, numbers: list) -> dict:
        """
        Extrae filtros específicos de la consulta del usuario con mayor precisión
        """
        filters = {}
        
        # Filtro de tipo de propiedad
        if any(word in query_lower for word in ['casa', 'casas']):
            filters['tipo'] = 'casa'
        elif any(word in query_lower for word in ['departamento', 'departamentos', 'apartamento', 'apartamentos']):
            filters['tipo'] = 'departamento'
        elif any(word in query_lower for word in ['terreno', 'terrenos', 'lote', 'lotes']):
            filters['tipo'] = 'terreno'
        
        # DETECCIÓN MEJORADA DE RANGOS DE PRECIO
        # Detectar frases como "menos de X mil", "más de X mil", "entre X y Y"
        precio_detectado = False
        
        # Patrones: "menos de X mil/millón", "más de X mil/millón"
        import re
        
        # Patrón: menos/hasta de [número] mil/millón/millones (con soporte de acentos)
        match_menos = re.search(r'(menos|hasta|máximo|maximo|max)\s+(?:de\s+)?(\d+(?:\.\d+)?)\s*(mil(?:es|lones)?|mill[oó]n(?:es)?|k|m)?', query_lower)
        if match_menos:
            num = float(match_menos.group(2))
            multiplicador = match_menos.group(3)
            
            # Aplicar multiplicador
            if multiplicador and multiplicador in ['mil', 'k']:
                num *= 1000
            elif multiplicador and 'mill' in multiplicador:  # millón, millon, millones
                num *= 1000000
            
            # Si el número es mayor a 1000, asumimos que es precio
            if num >= 1000:
                filters['precio_max'] = num
                precio_detectado = True
                logger.info(f"Detectado precio máximo: {num} desde '{match_menos.group(0)}'")
        
        # Patrón: más/desde de [número] mil/millón (con soporte de acentos)
        match_mas = re.search(r'(más|mas|desde|mínimo|minimo|min|mayor)\s+(?:de\s+)?(\d+(?:\.\d+)?)\s*(mil(?:es|lones)?|mill[oó]n(?:es)?|k|m)?', query_lower)
        if match_mas:
            num = float(match_mas.group(2))
            multiplicador = match_mas.group(3)
            
            # Aplicar multiplicador
            if multiplicador and multiplicador in ['mil', 'k']:
                num *= 1000
            elif multiplicador and 'mill' in multiplicador:  # millón, millon, millones
                num *= 1000000
            
            # Si el número es mayor a 1000, asumimos que es precio
            if num >= 1000:
                filters['precio_min'] = num
                precio_detectado = True
                logger.info(f"Detectado precio mínimo: {num} desde '{match_mas.group(0)}'")
        
        # Patrón: entre X y Y (mil/millón)
        # Ahora soporta dos formatos:
        # 1. "entre 200 y 400 mil" (multiplicador solo al final)
        # 2. "entre 200 mil y 300 mil" (multiplicador en ambos números)
        
        # Primero intentar con multiplicadores individuales: "entre X mil y Y mil"
        # Soporta: mil, millón, millones, k, m (con o sin acento)
        match_entre_doble = re.search(r'entre\s+(\d+(?:\.\d+)?)\s*(mil(?:es|lones)?|mill[oó]n(?:es)?|k|m)?\s+y\s+(\d+(?:\.\d+)?)\s*(mil(?:es|lones)?|mill[oó]n(?:es)?|k|m)?', query_lower)
        if match_entre_doble:
            num1 = float(match_entre_doble.group(1))
            mult1 = match_entre_doble.group(2)
            num2 = float(match_entre_doble.group(3))
            mult2 = match_entre_doble.group(4)
            
            # Si solo el segundo número tiene multiplicador, aplicarlo a ambos
            # Ejemplo: "entre 200 y 400 mil" → ambos se multiplican por mil
            if mult2 and not mult1:
                mult1 = mult2
            
            # Aplicar multiplicador al primer número
            if mult1 and mult1 in ['mil', 'k']:
                num1 *= 1000
            elif mult1 and 'mill' in mult1:  # millón, millon, millones
                num1 *= 1000000
            
            # Aplicar multiplicador al segundo número
            if mult2 and mult2 in ['mil', 'k']:
                num2 *= 1000
            elif mult2 and 'mill' in mult2:  # millón, millon, millones
                num2 *= 1000000
            
            # Si son precios razonables
            if num1 >= 1000 and num2 >= 1000:
                filters['precio_min'] = min(num1, num2)
                filters['precio_max'] = max(num1, num2)
                precio_detectado = True
                logger.info(f"Detectado rango de precio: {num1} - {num2} desde '{match_entre_doble.group(0)}'")
        
        # Patrón adicional: "X millón" o "X millones" sin "entre" (con soporte de acentos)
        if not precio_detectado:
            match_millones = re.search(r'(\d+(?:\.\d+)?)\s+(mill[oó]n(?:es)?)', query_lower)
            if match_millones:
                num = float(match_millones.group(1)) * 1000000
                # Buscar modificadores cerca
                idx = query_lower.find(match_millones.group(0))
                context_before = query_lower[max(0, idx-15):idx]
                
                if any(mod in context_before for mod in ['menos', 'hasta', 'máximo', 'maximo', 'max']):
                    filters['precio_max'] = num
                    precio_detectado = True
                elif any(mod in context_before for mod in ['más', 'mas', 'desde', 'mínimo', 'minimo', 'min']):
                    filters['precio_min'] = num
                    precio_detectado = True
                else:
                    # Asumir exacto si no hay modificador
                    filters['precio_exacto'] = num
                    filters['precio_tolerancia'] = 0.10
                    precio_detectado = True
        
        # Análisis más preciso de números con contexto (solo si no se detectó precio arriba)
        for i, num in enumerate(numbers):
            # Buscar el contexto alrededor del número
            num_str = str(int(num)) if num == int(num) else str(num)
            num_index = query_lower.find(num_str)
            
            if num_index == -1:
                continue
                
            # Contexto antes y después del número (30 caracteres cada lado para mejor detección)
            start_context = max(0, num_index - 30)
            end_context = min(len(query_lower), num_index + len(num_str) + 30)
            context = query_lower[start_context:end_context]
            
            # Filtros de habitaciones (MÁS ESTRICTO)
            if any(keyword in context for keyword in ['habitacion', 'habitaciones', 'cuarto', 'cuartos', 'recamara', 'recamaras', 'dormitorio', 'dormitorios']):
                if 1 <= num <= 10:  # Rango razonable
                    filters['habitaciones'] = int(num)
                    continue
            
            # Filtros de baños (MÁS ESTRICTO)
            if any(keyword in context for keyword in ['baño', 'baños', 'bano', 'banos', 'sanitario', 'sanitarios']):
                if 0.5 <= num <= 10:  # Rango razonable
                    filters['banos'] = float(num)
                    continue
            
            # Filtros de área (MÁS ESTRICTO)
            if any(keyword in context for keyword in ['metro', 'metros', 'm2', 'area', 'superficie', 'cuadrado', 'cuadrados']):
                if 20 <= num <= 2000:  # Rango razonable para área
                    # Verificar si hay modificadores
                    if any(mod in context for mod in ['hasta', 'máximo', 'max', 'menos']):
                        filters['area_max'] = num
                    elif any(mod in context for mod in ['desde', 'mínimo', 'min', 'más', 'mayor']):
                        filters['area_min'] = num
                    else:
                        filters['area_exacta'] = num
                        filters['area_tolerancia'] = 0.05  # Reducir tolerancia a 5%
                    continue
            
            # Filtros de precio (solo si no fue detectado con regex arriba)
            if not precio_detectado:
                if any(keyword in context for keyword in ['precio', 'cuesta', 'vale', '$', 'quetzales', 'q', 'dolar', 'dolares', 'presupuesto', 'costo']):
                    if num > 1000:  # Debe ser un precio razonable
                        # Verificar modificadores
                        if any(mod in context for mod in ['hasta', 'máximo', 'max', 'menos']):
                            filters['precio_max'] = num
                        elif any(mod in context for mod in ['desde', 'mínimo', 'min', 'más', 'mayor']):
                            filters['precio_min'] = num
                        else:
                            filters['precio_exacto'] = num
                            filters['precio_tolerancia'] = 0.05  # Reducir tolerancia a 5%
                        continue
        
        # Si hay número grande sin contexto específico, asumirlo como precio
        if not precio_detectado and not filters:
            for num in numbers:
                # Si es un número muy grande (> 50000), probablemente es precio
                if num >= 50000:
                    # Buscar modificadores alrededor
                    num_str = str(int(num))
                    num_index = query_lower.find(num_str)
                    if num_index != -1:
                        context = query_lower[max(0, num_index - 20):min(len(query_lower), num_index + len(num_str) + 20)]
                        
                        if any(mod in context for mod in ['menos', 'hasta', 'máximo', 'max']):
                            filters['precio_max'] = num
                        elif any(mod in context for mod in ['más', 'mas', 'desde', 'mínimo', 'min', 'mayor']):
                            filters['precio_min'] = num
                        else:
                            filters['precio_exacto'] = num
                            filters['precio_tolerancia'] = 0.10
                        break
        
        # Filtro de ubicación específica (MEJORADO)
        # Zonas de Guatemala (más específico)
        guatemala_zones = [
            'zona 1', 'zona 2', 'zona 3', 'zona 4', 'zona 5', 'zona 6', 'zona 7', 'zona 8', 
            'zona 9', 'zona 10', 'zona 11', 'zona 12', 'zona 13', 'zona 14', 'zona 15', 'zona 16'
        ]
        for zone in guatemala_zones:
            if zone in query_lower:
                filters['ubicacion_incluye'] = zone
                break
        
        # Ubicaciones específicas adicionales
        ubicaciones_especificas = [
            'eco villa', 'antigua', 'mixco', 'villa nueva', 'san lucas', 'santa catarina', 
            'amatitlán', 'chinautla', 'fraijanes', 'cayalá', 'vista hermosa', 'colina del valle',
            'zona residencial', 'suburbia', 'valle campestre', 'distrito artístico'
        ]
        for ubicacion in ubicaciones_especificas:
            if ubicacion in query_lower:
                filters['ubicacion_incluye'] = ubicacion
                break
        
        return filters

    def _matches_strict_filters(self, prop: dict, filters: dict) -> bool:
        """
        Verifica si una propiedad cumple con los filtros estrictos
        """
        try:
            # Filtro de tipo
            if 'tipo' in filters and prop.get('tipo') != filters['tipo']:
                return False
            
            # Filtros de precio
            precio = float(prop.get('precio', 0))
            
            if 'precio_exacto' in filters:
                target_price = filters['precio_exacto']
                tolerance = filters.get('precio_tolerancia', 0.05)  # 5% por defecto
                min_price = target_price * (1 - tolerance)
                max_price = target_price * (1 + tolerance)
                if not (min_price <= precio <= max_price):
                    return False
            
            if 'precio_min' in filters and precio < filters['precio_min']:
                return False
            
            if 'precio_max' in filters and precio > filters['precio_max']:
                return False
            
            # Filtro de habitaciones (EXACTO - sin tolerancia)
            if 'habitaciones' in filters:
                prop_habitaciones = int(prop.get('habitaciones', 0))
                if prop_habitaciones != filters['habitaciones']:
                    return False
            
            # Filtro de baños (EXACTO - tolerancia mínima para decimales)
            if 'banos' in filters:
                prop_banos = float(prop.get('banos', 0))
                target_banos = float(filters['banos'])
                # Tolerancia muy pequeña solo para diferencias de redondeo
                if abs(prop_banos - target_banos) > 0.01:
                    return False
            
            # Filtros de área (MEJORADOS)
            area = float(prop.get('area_m2', 0))
            
            if 'area_exacta' in filters:
                target_area = filters['area_exacta']
                tolerance = filters.get('area_tolerancia', 0.05)  # 5% por defecto
                min_area = target_area * (1 - tolerance)
                max_area = target_area * (1 + tolerance)
                if not (min_area <= area <= max_area):
                    return False
            
            if 'area_min' in filters and area < filters['area_min']:
                return False
            
            if 'area_max' in filters and area > filters['area_max']:
                return False
            
            # Filtro de ubicación (MEJORADO - más flexible en búsqueda)
            if 'ubicacion_incluye' in filters:
                ubicacion_prop = prop.get('ubicacion', '').lower()
                ubicacion_filtro = filters['ubicacion_incluye'].lower()
                
                # Buscar coincidencias parciales también
                if ubicacion_filtro not in ubicacion_prop:
                    # Intentar con palabras clave individuales para mayor flexibilidad
                    palabras_filtro = ubicacion_filtro.split()
                    palabras_encontradas = sum(1 for palabra in palabras_filtro if palabra in ubicacion_prop)
                    # Si no encuentra al menos la mitad de las palabras, rechazar
                    if palabras_encontradas < len(palabras_filtro) / 2:
                        return False
            
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Error procesando filtros para propiedad {prop.get('id', 'unknown')}: {e}")
            return False

    async def ai_semantic_search(self, properties: list, query: str) -> list:
        """
        Búsqueda semántica usando IA para encontrar propiedades relevantes
        """
        if not properties:
            return []
        
        try:
            # Limitar propiedades para evitar prompt muy largo
            max_properties = 20
            sample_properties = properties[:max_properties]
            
            # Crear contexto de propiedades para la IA
            properties_context = ""
            for i, prop in enumerate(sample_properties):
                properties_context += f"""
                ID: {prop.get('id', i)}
                Título: {prop.get('titulo', 'Sin título')}
                Tipo: {prop.get('tipo', 'N/A')}
                Precio: Q{prop.get('precio', 0):,.2f}
                Habitaciones: {prop.get('habitaciones', 0)}
                Baños: {prop.get('banos', 0)}
                Área: {prop.get('area_m2', 0)} m²
                Ubicación: {prop.get('ubicacion', 'N/A')}
                Descripción: {prop.get('descripcion', 'Sin descripción')[:100]}...
                ---
                """
            
            prompt = f"""
            Analiza estas propiedades inmobiliarias y encuentra las más relevantes para la consulta: "{query}"

            Propiedades disponibles:
            {properties_context}

            Criterios de evaluación:
            1. Relevancia directa con la consulta
            2. Coincidencia de características específicas (precio, habitaciones, ubicación, etc.)
            3. Tipo de propiedad solicitado
            4. Descripción y características especiales

            Responde ÚNICAMENTE con una lista de IDs de las propiedades más relevantes, ordenadas por relevancia (máximo 10).
            Formato: [1, 5, 3, 8, 2]
            """
            
            system_prompt = "Eres un experto en bienes raíces. Respondes ÚNICAMENTE con la lista de IDs en formato JSON array."
            
            ai_response = await self.ollama_client.ask_ai_direct(prompt, system_prompt)
            
            if not ai_response or "Error:" in ai_response:
                logger.warning("Error en búsqueda semántica, usando fallback")
                return self._simple_text_filter(properties, query)
            
            # Extraer IDs de la respuesta
            try:
                # Buscar array JSON en la respuesta
                import json
                ids_match = re.search(r'\[[\d\s,]+\]', ai_response)
                if ids_match:
                    relevant_ids = json.loads(ids_match.group())
                    
                    # Filtrar propiedades por IDs relevantes
                    relevant_properties = []
                    for prop in properties:
                        if prop.get('id') in relevant_ids:
                            relevant_properties.append(prop)
                    
                    # Ordenar según el orden de relevancia de la IA
                    ordered_properties = []
                    for prop_id in relevant_ids:
                        for prop in relevant_properties:
                            if prop.get('id') == prop_id:
                                ordered_properties.append(prop)
                                break
                    
                    logger.info(f"Búsqueda semántica encontró {len(ordered_properties)} propiedades relevantes")
                    return ordered_properties
                else:
                    logger.warning("No se pudo extraer IDs de respuesta de IA")
                    return self._simple_text_filter(properties, query)
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Error procesando respuesta de IA: {e}")
                return self._simple_text_filter(properties, query)
                
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {e}")
            return self._simple_text_filter(properties, query)

    def calculate_specific_boost(self, prop: dict, query_lower: str, numbers: list) -> dict:
        """
        Calcula boost de puntuación para características específicas
        """
        boost_info = {
            'total_boost': 0,
            'reasons': []
        }
        
        # Boost por precio específico
        if numbers:
            prop_precio = float(prop.get('precio', 0))
            for num in numbers:
                if 300000 <= num <= 1000000:  # Rango de precios razonable
                    if abs(prop_precio - num) / num <= 0.1:  # 10% de tolerancia
                        boost = 15
                        boost_info['total_boost'] += boost
                        boost_info['reasons'].append(f"Precio cercano a Q{num:,.0f} (+{boost})")
                        break
        
        # Boost por habitaciones específicas
        for num in numbers:
            if 1 <= num <= 6:  # Rango razonable de habitaciones
                context = ""
                for word in ['habitacion', 'habitaciones', 'cuarto', 'cuartos']:
                    if word in query_lower:
                        context = query_lower
                        break
                
                if context and int(prop.get('habitaciones', 0)) == int(num):
                    boost = 12
                    boost_info['total_boost'] += boost
                    boost_info['reasons'].append(f"Habitaciones exactas: {int(num)} (+{boost})")
                    break
        
        # Boost por baños específicos
        for num in numbers:
            if 1 <= num <= 5:  # Rango razonable de baños
                if any(word in query_lower for word in ['baño', 'baños', 'sanitario']):
                    prop_banos = float(prop.get('banos', 0))
                    if abs(prop_banos - num) <= 0.1:
                        boost = 10
                        boost_info['total_boost'] += boost
                        boost_info['reasons'].append(f"Baños exactos: {num} (+{boost})")
                        break
        
        # Boost por área específica
        for num in numbers:
            if 50 <= num <= 1000:  # Rango razonable de área
                if any(word in query_lower for word in ['metro', 'metros', 'm2', 'area']):
                    prop_area = float(prop.get('area_m2', 0))
                    if abs(prop_area - num) / num <= 0.15:  # 15% de tolerancia
                        boost = 8
                        boost_info['total_boost'] += boost
                        boost_info['reasons'].append(f"Área cercana a {num}m² (+{boost})")
                        break
        
        # Boost por ubicación específica
        ubicacion = prop.get('ubicacion', '').lower()
        
        # Zonas específicas de Guatemala
        zonas_guatemala = {
            'zona 10': 10, 'zona 14': 10, 'zona 15': 9,
            'zona 9': 8, 'zona 1': 8, 'zona 4': 7,
            'antigua': 12, 'cayalá': 11, 'vista hermosa': 10
        }
        
        for zona, boost in zonas_guatemala.items():
            if zona in query_lower and zona in ubicacion:
                boost_info['total_boost'] += boost
                boost_info['reasons'].append(f"Ubicación específica: {zona} (+{boost})")
                break
        
        return boost_info

    def _simple_text_filter(self, properties: list, query: str) -> list:
        """
        Filtro de texto simple como fallback
        """
        if not query:
            return properties
        
        keywords = self._extract_keywords(query)
        scored_properties = []
        
        for prop in properties:
            score = 0
            text_to_search = f"{prop.get('titulo', '')} {prop.get('descripcion', '')} {prop.get('ubicacion', '')} {prop.get('tipo', '')}".lower()
            
            for keyword in keywords:
                if keyword in text_to_search:
                    score += 1
            
            if score > 0:
                scored_properties.append((prop, score))
        
        # Ordenar por puntuación descendente
        scored_properties.sort(key=lambda x: x[1], reverse=True)
        return [prop for prop, score in scored_properties]

    def _extract_keywords(self, query: str) -> list:
        """
        Extrae palabras clave de la consulta
        """
        # Palabras comunes a ignorar
        stop_words = {'el', 'la', 'de', 'en', 'y', 'a', 'que', 'con', 'por', 'para', 'un', 'una', 'es', 'se', 'del', 'los', 'las'}
        
        # Limpiar y dividir
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
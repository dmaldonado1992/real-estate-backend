# backend/app/llm_service.py
import os
import re
import json
import logging
import asyncio
import aiohttp
from functools import partial
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """
        Inicializa el servicio LLM con Ollama Cloud usando API REST
        """
        self.use_cloud = os.environ.get('USE_OLLAMA_CLOUD', 'true').lower() == 'true'
        
        if self.use_cloud:
            # Configuración para Ollama Cloud con API REST
            self.api_key = os.environ.get('OLLAMA_API_KEY')
            if not self.api_key:
                raise ValueError("OLLAMA_API_KEY no está configurado para usar Ollama Cloud")
            
            self.base_url = "https://ollama.com/api"
            self.model = os.environ.get('OLLAMA_MODEL', 'deepseek-v3.1:671b-cloud')
            logger.info(f"Usando Ollama Cloud (API REST) con modelo: {self.model}")
        else:
            # Configuración para Ollama Local
            ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
            self.base_url = f"{ollama_url}/api"
            self.model = os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')
            self.api_key = None
            logger.info(f"Usando Ollama Local en {ollama_url} con modelo: {self.model}")
        
        self.timeout = 60
    
    def call_ollama(self, prompt: str, use_sql_system_prompt: bool = True) -> Optional[str]:
        """Llama a Ollama usando API REST asincrona (Cloud o Local)"""
        try:
            system_content = 'Eres un experto en SQL que genera consultas MySQL precisas. Respondes UNICAMENTE con SQL valido, sin explicaciones.' if use_sql_system_prompt else 'Eres un asistente util y amigable.'
            
            messages = [
                {
                    'role': 'system',
                    'content': system_content
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
            
            logger.info(f"Llamando a {self.base_url}/chat con modelo {self.model}")
            logger.debug(f"API Key presente: {bool(self.api_key)}")
            
            # Usar requests síncrono (más simple y confiable)
            import requests
            
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
                logger.debug(f"Auth header configurado")
            
            payload = {
                'model': self.model,
                'messages': messages,
                'stream': False
            }
            
            # Implementar reintentos para errores transitorios (429, 5xx)
            max_retries = 3
            backoff = 1.0
            for attempt in range(1, max_retries + 1):
                response = requests.post(
                    f"{self.base_url}/chat",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                logger.info(f"Status: {response.status_code} (attempt {attempt})")

                if response.status_code == 200:
                    data = response.json()
                    content = data.get('message', {}).get('content', '')
                    logger.info(f"Respuesta recibida: {len(content)} caracteres")
                    return content.strip()

                # No reintentar si la autenticación falla
                if response.status_code == 401:
                    logger.error(f"Error HTTP 401 Unauthorized: {response.text}")
                    return None

                # Reintentar en caso de rate limit o errores de servidor
                if response.status_code in (429,) or 500 <= response.status_code < 600:
                    logger.warning(f"Error transitorio {response.status_code}, reintentando en {backoff}s: {response.text}")
                    time_to_sleep = backoff
                    backoff *= 2
                    import time
                    time.sleep(time_to_sleep)
                    continue

                # Otros errores no recuperables
                logger.error(f"Error HTTP {response.status_code}: {response.text}")
                return None
            
        except Exception as e:
            logger.error(f"Error llamando a Ollama: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
   
    def generate_sql(self, user_query: str) -> Dict[str, any]:
        """
        Genera SQL a partir de lenguaje natural usando Ollama Cloud
        """
        try:
            # Generar prompt
            prompt = self.create_robust_prompt(user_query)
            
            # Llamar a Ollama (Cloud o Local) con prompt SQL activado
            response = self.call_ollama(prompt, use_sql_system_prompt=True)
            
            if not response:
                return {
                    'success': False,
                    'error': 'No se pudo obtener respuesta del LLM'
                }
            
            # Limpiar y validar SQL
            sql = self.clean_sql(response)
            
            if not self.validate_sql(sql):
                logger.warning(f"SQL no valido generado: {sql}")
                return {
                    'success': False,
                    'error': 'No se pudo generar una consulta SQL valida',
                    'raw_response': response
                }
            
            logger.info(f"SQL generado exitosamente: {sql}")
            return {
                'success': True,
                'sql': sql,
                'user_query': user_query
            }
            
        except Exception as e:
            logger.error(f"Error en generacion SQL: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Error al procesar la consulta: {str(e)}'
            }

    async def ask_ai_direct(self, prompt: str, system_prompt: str = None) -> str:
        """
        Metodo publico que replica la funcionalidad de `call_ollama`.

        Usa el mismo flujo de streaming y las mismas opciones que `call_ollama`.
        """
        try:
            # Si el caller pasa un system_prompt lo usamos; si no, call_ollama usara su system por defecto
            if system_prompt:
                # Construir un prompt combinado donde el system prompt se antepone al user prompt
                combined_prompt = f"{system_prompt}\n\n{prompt}"
                use_sql_prompt = False
            else:
                combined_prompt = prompt
                use_sql_prompt = False  # Para ask_ai_direct NO usar SQL prompt por defecto

            # Ejecutar la llamada sincrona en un executor para no bloquear el event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, partial(self.call_ollama, combined_prompt, use_sql_prompt))
            return result or ""
        except Exception as e:
            logger.error(f"Error en ask_ai_direct al invocar call_ollama: {e}", exc_info=True)
            return ""

    async def search_ia(self, query: str, properties_context: str = None) -> str:
        """
        Búsqueda general con IA que incluye contexto de propiedades.
        
        Args:
            query: Consulta del usuario
            properties_context: Contexto de propiedades (opcional)
            
        Returns:
            Respuesta directa de la IA
        """
        try:
            # Si no se proporciona contexto, cargar propiedades básicas
            if not properties_context:
                properties = self.load_properties_json()
                properties_context = "PROPIEDADES DISPONIBLES:\n"
                for i, prop in enumerate(properties[:10], 1):  # Primeras 10 propiedades como contexto
                    properties_context += f"{i}. {prop['titulo']} - Precio: ${prop['precio']:,.0f}, "
                    properties_context += f"{prop['habitaciones']} hab, {prop['banos']} baños, "
                    properties_context += f"{prop['area_m2']} m², {prop['ubicacion']}\n"
            
            # Prompt del sistema para la IA
            system_prompt = f"""Eres un experto asesor de bienes raíces muy amigable y profesional.
            Ayudas a los clientes a encontrar la propiedad perfecta respondiendo sus preguntas de forma natural y conversacional.

            {properties_context}

            Responde de forma directa, útil y amigable. Si te preguntan por propiedades específicas, menciona las que mejor coincidan.
            Sé conciso pero informativo (máximo 4-5 oraciones)."""

            # Llamar directamente a la IA
            response = await self.ask_ai_direct(
                prompt=query,
                system_prompt=system_prompt
            )
            
            return response if response else "No pude procesar tu consulta en este momento."
            
        except Exception as e:
            logger.error(f"Error en search_ia: {str(e)}")
            return f"Error procesando la consulta: {str(e)}"

    async def search_ia_real_state(self, query: str, use_cloud: bool = True) -> dict:
        """
        Busqueda inteligente y exacta de propiedades usando IA + filtros precisos.
        Busca coincidencias exactas en: título, descripción, tipo, precio, habitaciones, baños, área, ubicación, fecha.
        """
        logger.info(f"Busqueda IA Real State: {query}")
        
        # Cargar propiedades - primero intentar desde base de datos, luego JSON como fallback
        load_result = self.load_properties_from_db_or_json_with_query()
        all_properties = load_result['properties']
        generated_query = load_result.get('query', None)
        
        if not all_properties:
            return {
                "success": False,
                "properties": [],
                "total_found": 0,
                "keywords": [],
                "analysis": "No hay propiedades disponibles.",
                "query": {
                    "user_query": query,
                    "generated_sql": generated_query,
                    "data_source": "database" if generated_query else "json"
                },
                "metadata": {"total_properties": 0, "ai_used": True}
            }
        
        try:
            # Paso 1: Filtrado exacto por criterios específicos
            exact_matches = self._filter_exact_matches(all_properties, query)
            
            # Paso 2: Si hay coincidencias exactas, usar esas; si no, usar IA para búsqueda semántica
            if exact_matches:
                filtered_properties = exact_matches
                analysis = f"Encontradas {len(exact_matches)} propiedades con coincidencias exactas en los criterios de búsqueda."
                ai_used = False
            else:
                # Usar IA para búsqueda semántica cuando no hay coincidencias exactas
                filtered_properties = await self._ai_semantic_search(all_properties, query)
                analysis = "Búsqueda realizada con IA semántica al no encontrar coincidencias exactas."
                ai_used = True
            
            # Extraer keywords de la query
            keywords = self._extract_keywords(query)
            
            return {
                "success": True,
                "properties": filtered_properties[:10],  # Máximo 10 resultados
                "total_found": len(filtered_properties),
                "keywords": keywords[:3],
                "analysis": analysis,
                "query": {
                    "user_query": query,
                    "generated_sql": generated_query,
                    "data_source": "database" if generated_query else "json"
                },
                "metadata": {
                    "ai_used": ai_used,
                    "total_properties_analyzed": len(all_properties),
                    "filtered_properties": len(filtered_properties),
                    "exact_matches_found": len(exact_matches) if exact_matches else 0
                }
            }
                
        except Exception as e:
            logger.error(f"Error en busqueda IA: {e}")
            # Fallback: devolver propiedades con filtro simple
            fallback_properties = self._simple_text_filter(all_properties, query)
            return {
                "success": True,  # Cambiar a True porque sí encontramos resultados con filtro simple
                "properties": fallback_properties[:5],
                "total_found": len(fallback_properties),
                "keywords": [word for word in query.split() if len(word) > 3][:3],
                "analysis": f"Búsqueda realizada con filtro de texto. Se encontraron {len(fallback_properties)} propiedades que coinciden con tu consulta.",
                "query": {
                    "user_query": query,
                    "generated_sql": generated_query,
                    "data_source": "database" if generated_query else "json"
                },
                "metadata": {
                    "ai_used": False,
                    "fallback_used": True,
                    "total_properties_analyzed": len(all_properties)
                }
            }

    def _filter_exact_matches(self, properties: list, query: str) -> list:
        """Filtra propiedades con coincidencias exactas en campos específicos."""
        query_lower = query.lower()
        matches = []
        
        # Extraer números y términos de la query
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        words = [word.strip().lower() for word in re.split(r'[,\s]+', query_lower) if len(word.strip()) > 2]
        
        # Detectar criterios específicos de filtrado
        filters = self._extract_filters(query_lower, numbers)
        
        for prop in properties:
            # Si hay filtros específicos, aplicar filtrado estricto
            if filters:
                if not self._matches_strict_filters(prop, filters):
                    continue
            
            # Calcular score para ordenamiento
            score = 0
            reasons = []
            
            # BOOST ESPECIAL: Propiedades con características específicas de alta prioridad
            premium_boost = self._calculate_specific_boost(prop, query_lower, numbers)
            score += premium_boost['score']
            reasons.extend(premium_boost['reasons'])
            
            # Coincidencias en título (peso: 3)
            title_lower = prop['titulo'].lower()
            for word in words:
                if word in title_lower:
                    score += 3
                    reasons.append(f"título contiene '{word}'")
            
            # Coincidencias en descripción (peso: 2)
            desc_lower = prop['descripcion'].lower()
            for word in words:
                if word in desc_lower:
                    score += 2
                    reasons.append(f"descripción contiene '{word}'")
            
            # Coincidencias exactas en tipo (peso: 5)
            tipos_validos = ['casa', 'departamento', 'terreno', 'local', 'oficina', 'duplex', 'villa']
            for tipo in tipos_validos:
                if tipo in query_lower and prop['tipo'].lower() == tipo:
                    score += 5
                    reasons.append(f"tipo exacto: {tipo}")
            
            # Coincidencias en ubicación (peso: 4)
            ubicacion_lower = prop['ubicacion'].lower()
            for word in words:
                if word in ubicacion_lower:
                    score += 4
                    reasons.append(f"ubicación contiene '{word}'")
            
            # Aplicar puntuación extra por filtros exactos
            for filter_type, filter_value in filters.items():
                if filter_type == 'tipo_especifico' and prop['tipo'].lower() == filter_value.lower():
                    score += 15
                    reasons.append(f"tipo exacto: {filter_value}")
                elif filter_type == 'habitaciones_exactas' and prop['habitaciones'] == filter_value:
                    score += 10
                    reasons.append(f"habitaciones exactas: {filter_value}")
                elif filter_type == 'banos_exactos' and abs(prop['banos'] - filter_value) < 0.5:
                    score += 10
                    reasons.append(f"baños exactos: {filter_value}")
                elif filter_type == 'banos_min' and prop['banos'] >= filter_value:
                    score += 8
                    reasons.append(f"baños ≥ {filter_value}")
                elif filter_type == 'precio_max' and prop['precio'] <= filter_value:
                    score += 8
                    reasons.append(f"precio ≤ ${filter_value:,.0f}")
                elif filter_type == 'precio_min' and prop['precio'] >= filter_value:
                    score += 8
                    reasons.append(f"precio ≥ ${filter_value:,.0f}")
                elif filter_type == 'precio_rango' and filter_value[0] <= prop['precio'] <= filter_value[1]:
                    score += 10
                    reasons.append(f"precio en rango ${filter_value[0]:,.0f}-${filter_value[1]:,.0f}")
                elif filter_type == 'area_min' and prop['area_m2'] >= filter_value:
                    score += 8
                    reasons.append(f"área ≥ {filter_value} m²")
                elif filter_type == 'area_exacta' and abs(prop['area_m2'] - filter_value) < 10:
                    score += 10
                    reasons.append(f"área ≈ {filter_value} m²")
                elif filter_type == 'ubicacion_especifica' and filter_value.lower() in prop['ubicacion'].lower():
                    score += 12
                    reasons.append(f"ubicación: {filter_value}")
                elif filter_type == 'dias_recientes':
                    try:
                        from datetime import datetime, timedelta
                        if prop.get('fecha_publicacion'):
                            fecha_str = prop['fecha_publicacion']
                            try:
                                if isinstance(fecha_str, str):
                                    if '-' in fecha_str:
                                        fecha_prop = datetime.strptime(fecha_str, '%Y-%m-%d')
                                    elif '/' in fecha_str:
                                        fecha_prop = datetime.strptime(fecha_str, '%d/%m/%Y')
                                    else:
                                        fecha_prop = datetime.strptime(fecha_str, '%Y-%m-%d')
                                else:
                                    fecha_prop = fecha_str
                                
                                fecha_limite = datetime.now() - timedelta(days=filter_value)
                                if fecha_prop >= fecha_limite:
                                    score += 8
                                    reasons.append(f"publicada últimos {filter_value} días")
                            except (ValueError, TypeError):
                                pass
                    except ImportError:
                        pass
            
            # Si tiene puntuación o cumple filtros, incluir en resultados
            if score > 0 or filters:
                prop_copy = prop.copy()
                prop_copy['_match_score'] = score
                prop_copy['_match_reasons'] = reasons
                matches.append(prop_copy)
        
        # Ordenar por puntuación descendente
        matches.sort(key=lambda x: x['_match_score'], reverse=True)
        
        logger.info(f"Filtro exacto encontró {len(matches)} coincidencias con filtros: {filters}")
        return matches

    def _extract_filters(self, query_lower: str, numbers: list) -> dict:
        """Extrae filtros específicos de la query."""
        filters = {}
        
        # Filtros de habitaciones exactas
        if any(word in query_lower for word in ['habitacion', 'dormitorio', 'recamara', 'cuarto']) and numbers:
            for num_str in numbers:
                num = int(float(num_str))
                if 1 <= num <= 10:  # Rango razonable para habitaciones
                    filters['habitaciones_exactas'] = num
                    break
        
        # Filtros de baños exactos o mínimos
        if any(word in query_lower for word in ['baño', 'bano', 'sanitario']) and numbers:
            for num_str in numbers:
                num = float(num_str)
                if 0.5 <= num <= 8:  # Rango razonable para baños
                    # Si dice "más de X baños", usar filtro mínimo
                    if any(word in query_lower for word in ['más', 'mayor', 'mínimo', 'minimo']):
                        filters['banos_min'] = num
                    else:
                        filters['banos_exactos'] = num
                    break
        
        # Filtros de precio
        if numbers:
            # Rango de precios específico: "entre $50,000 y $100,000"
            if 'entre' in query_lower and len(numbers) >= 2:
                prices = [float(n) for n in numbers if float(n) > 1000]  # Solo números que parecen precios
                if len(prices) >= 2:
                    filters['precio_rango'] = [min(prices), max(prices)]
            
            # Precio máximo: "menos de $150,000", "menor a $300,000"
            elif any(word in query_lower for word in ['menos', 'menor', 'bajo', 'barato', 'máximo', 'maximo']):
                for num_str in numbers:
                    num = float(num_str)
                    if num > 1000:  # Parece un precio
                        filters['precio_max'] = num
                        break
            
            # Precio mínimo: "más de $200,000", "desde $150,000"
            elif any(word in query_lower for word in ['más', 'mayor', 'mínimo', 'minimo', 'desde']):
                for num_str in numbers:
                    num = float(num_str)
                    if num > 1000:  # Parece un precio
                        filters['precio_min'] = num
                        break
        
        # Filtros de área
        if any(word in query_lower for word in ['metro', 'm2', 'área', 'area', 'superficie']) and numbers:
            # Área mínima: "al menos 150 metros", "más de 100 m2"
            if any(word in query_lower for word in ['más', 'mayor', 'mínimo', 'minimo', 'menos', 'desde', 'al']):
                for num_str in numbers:
                    num = float(num_str)
                    if 20 <= num <= 2000:  # Rango razonable para área
                        filters['area_min'] = num
                        break
            # Área específica
            else:
                for num_str in numbers:
                    num = float(num_str)
                    if 20 <= num <= 2000:  # Rango razonable para área
                        filters['area_exacta'] = num
                        break
        
        # Filtros de ubicación específica (zona X, distrito X, etc.)
        ubicaciones_patterns = [
            (r'zona\s*(\d+)', 'zona'),
            (r'distrito\s*(\w+)', 'distrito'),
            (r'sector\s*(\w+)', 'sector'),
            (r'barrio\s*(\w+)', 'barrio'),
            (r'colonia\s*(\w+)', 'colonia'),
            (r'fraccionamiento\s*(\w+)', 'fraccionamiento')
        ]
        
        for pattern, tipo in ubicaciones_patterns:
            match = re.search(pattern, query_lower)
            if match:
                filters['ubicacion_especifica'] = f"{tipo} {match.group(1)}"
                break
        
        # Filtros de fecha (publicadas recientemente)
        if any(word in query_lower for word in ['último', 'ultima', 'reciente', 'nuevo', 'nueva', 'publicad']) and numbers:
            for num_str in numbers:
                num = int(float(num_str))
                if 1 <= num <= 365:  # Días razonables
                    if any(word in query_lower for word in ['día', 'dias']):
                        filters['dias_recientes'] = num
                    elif any(word in query_lower for word in ['mes', 'meses']):
                        filters['dias_recientes'] = num * 30
                    elif any(word in query_lower for word in ['semana', 'semanas']):
                        filters['dias_recientes'] = num * 7
                    break
        
        # Detectar tipos de propiedad específicos
        tipos_propiedad = ['casa', 'casas', 'departamento', 'departamentos', 'terreno', 'terrenos', 'local', 'locales', 'oficina', 'oficinas']
        for tipo in tipos_propiedad:
            if tipo in query_lower:
                # Normalizar plural a singular
                tipo_singular = tipo.rstrip('s') if tipo.endswith('s') else tipo
                filters['tipo_especifico'] = tipo_singular
                break
        
        return filters

    def _matches_strict_filters(self, prop: dict, filters: dict) -> bool:
        """Verifica si una propiedad cumple EXACTAMENTE con los filtros especificados."""
        
        # Filtro de tipo específico
        if 'tipo_especifico' in filters:
            if prop['tipo'].lower() != filters['tipo_especifico'].lower():
                return False
        
        # Filtro de habitaciones exactas
        if 'habitaciones_exactas' in filters:
            if prop['habitaciones'] != filters['habitaciones_exactas']:
                return False
        
        # Filtro de baños exactos
        if 'banos_exactos' in filters:
            if abs(prop['banos'] - filters['banos_exactos']) >= 0.5:
                return False
        
        # Filtro de baños mínimos
        if 'banos_min' in filters:
            if prop['banos'] < filters['banos_min']:
                return False
        
        # Filtro de precio máximo
        if 'precio_max' in filters:
            if prop['precio'] > filters['precio_max']:
                return False
        
        # Filtro de precio mínimo
        if 'precio_min' in filters:
            if prop['precio'] < filters['precio_min']:
                return False
        
        # Filtro de rango de precios
        if 'precio_rango' in filters:
            min_price, max_price = filters['precio_rango']
            if not (min_price <= prop['precio'] <= max_price):
                return False
        
        # Filtro de área mínima
        if 'area_min' in filters:
            if prop['area_m2'] < filters['area_min']:
                return False
        
        # Filtro de área exacta (con tolerancia de ±10 m²)
        if 'area_exacta' in filters:
            if abs(prop['area_m2'] - filters['area_exacta']) > 10:
                return False
        
        # Filtro de ubicación específica
        if 'ubicacion_especifica' in filters:
            ubicacion_filtro = filters['ubicacion_especifica'].lower()
            ubicacion_prop = prop['ubicacion'].lower()
            if ubicacion_filtro not in ubicacion_prop:
                return False
        
        # Filtro de fecha (días recientes)
        if 'dias_recientes' in filters:
            if prop.get('fecha_publicacion'):
                try:
                    from datetime import datetime, timedelta
                    
                    # Intentar parsear diferentes formatos de fecha
                    fecha_str = prop['fecha_publicacion']
                    try:
                        if isinstance(fecha_str, str):
                            # Formato ISO: "2024-01-15"
                            if '-' in fecha_str:
                                fecha_prop = datetime.strptime(fecha_str, '%Y-%m-%d')
                            # Formato DD/MM/YYYY: "15/01/2024"
                            elif '/' in fecha_str:
                                fecha_prop = datetime.strptime(fecha_str, '%d/%m/%Y')
                            else:
                                # Intentar otros formatos comunes
                                fecha_prop = datetime.strptime(fecha_str, '%Y-%m-%d')
                        else:
                            # Si ya es datetime
                            fecha_prop = fecha_str
                        
                        # Calcular diferencia en días
                        fecha_limite = datetime.now() - timedelta(days=filters['dias_recientes'])
                        if fecha_prop < fecha_limite:
                            return False
                            
                    except (ValueError, TypeError):
                        # Si no se puede parsear la fecha, no filtrar por fecha
                        logger.warning(f"No se pudo parsear fecha: {fecha_str}")
                        pass
                except ImportError:
                    # Si no se puede importar datetime, no filtrar por fecha
                    pass
        
        return True

    async def _ai_semantic_search(self, properties: list, query: str) -> list:
        """Búsqueda semántica con IA cuando no hay coincidencias exactas.

        Para evitar prompts excesivamente grandes (causa típica de OOM), enviamos las
        propiedades en lotes (chunks) a la IA. Cada llamada devuelve los IDs que coinciden
        en ese chunk; al final combinamos IDs y devolvemos las propiedades correspondientes.
        """
        logger.info("Iniciando búsqueda semántica por lotes con IA")

        # Seguridad: evitar procesar cantidades excesivas en una sola operación
        MAX_PROPERTIES = 2000
        if len(properties) > MAX_PROPERTIES:
            logger.warning(f"Cantidad de propiedades ({len(properties)}) excede el límite de {MAX_PROPERTIES}. Se truncará a {MAX_PROPERTIES}.")
            properties = properties[:MAX_PROPERTIES]

        chunk_size = 50  # número de propiedades por petición a la IA (ajustable)
        matching_ids = set()

        system = "Eres un experto en bienes raíces. Recibes una lista de propiedades (id + campos clave) y debes devolver SOLO un JSON con la lista de IDs que mejor coinciden con la consulta del usuario. Responde en formato JSON: {\"property_ids\": [1,2,3]}"

        for start in range(0, len(properties), chunk_size):
            chunk = properties[start:start+chunk_size]

            # Construir prompt compacto para el chunk
            props_buf = []
            for p in chunk:
                props_buf.append(
                    f"ID:{p['id']} | T:{p.get('titulo','')[:80]} | Tipo:{p.get('tipo','')} | Precio:{int(p.get('precio',0))} | Hab:{p.get('habitaciones',0)} | Banos:{p.get('banos',0)} | Area:{p.get('area_m2',0)} | Ubic:{p.get('ubicacion','')[:40]} | Fecha:{p.get('fecha_publicacion','')}"
                )

            example_json = '{"property_ids": [1,2]}'
            prompt = "PROPIEDADES CHUNK:\n" + "\n".join(props_buf) + "\n\nCONSULTA DEL USUARIO: \"" + query + "\"\n\nRESPONDE CON UN JSON QUE CONTENGA SOLO LOS IDS DE LAS PROPIEDADES QUE COINCIDEN (ej: " + example_json + "). NO INCLUYAS NINGÚN TEXTO ADICIONAL."

            try:
                response = await self.ask_ai_direct(prompt, system_prompt=system)
                if not response:
                    logger.warning("IA devolvió respuesta vacía para un chunk; saltando chunk")
                    continue

                # Extraer JSON de la respuesta
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    parsed = json.loads(json_str)
                    ids = parsed.get('property_ids', [])
                    for _id in ids:
                        matching_ids.add(_id)
                    logger.info(f"Chunk {start}-{start+len(chunk)}: IA devolvió {len(ids)} ids")
                else:
                    logger.warning("No se encontró JSON válido en la respuesta de IA para un chunk")

            except Exception as e:
                logger.error(f"Error llamando a IA en chunk {start}-{start+len(chunk)}: {e}")

            # Pequeña pausa para evitar ráfagas
            await asyncio.sleep(0.15)

        # Filtrar propiedades según los IDs recopilados
        if not matching_ids:
            logger.info("IA no devolvió coincidencias semánticas en ningún chunk")
            return []

        filtered_properties = [p for p in properties if p['id'] in matching_ids]
        logger.info(f"IA semántica por lotes encontró {len(filtered_properties)} propiedades")
        return filtered_properties

    def _calculate_specific_boost(self, prop: dict, query_lower: str, numbers: list) -> dict:
        """
        Calcula boost de prioridad para propiedades con características específicas.
        Estas características tienen MÁS PRIORIDAD que las coincidencias de tipo de propiedad:
        - precio: $485,000
        - habitaciones: 3
        - baños: 2.5
        - área: 220 m²
        - ubicación: "Eco Villa"
        - fecha: 2025-10-29
        """
        boost_score = 0
        boost_reasons = []
        
        # Definir valores específicos de alta prioridad
        PRIORITY_PRECIO = 485000
        PRIORITY_HABITACIONES = 3
        PRIORITY_BANOS = 2.5
        PRIORITY_AREA = 220
        PRIORITY_UBICACION = "eco villa"
        PRIORITY_FECHA = "2025-10-29"
        
        # NOTA: Los pesos son mayores que coincidencias de tipo (peso 5)
        # para asegurar que estas características tengan MÁS PRIORIDAD
        
        # Boost por precio específico (±5% tolerancia) - PESO: 12
        if abs(prop.get('precio', 0) - PRIORITY_PRECIO) <= (PRIORITY_PRECIO * 0.05):
            boost_score += 12
            boost_reasons.append(f"🎯 PRECIO PRIORIDAD: ${prop.get('precio', 0):,.0f} (cerca de ${PRIORITY_PRECIO:,.0f})")
        
        # Boost por habitaciones específicas - PESO: 10
        if prop.get('habitaciones') == PRIORITY_HABITACIONES:
            boost_score += 10
            boost_reasons.append(f"� HABITACIONES PRIORIDAD: {PRIORITY_HABITACIONES}")
        
        # Boost por baños específicos (±0.5 tolerancia) - PESO: 10
        if abs(prop.get('banos', 0) - PRIORITY_BANOS) <= 0.5:
            boost_score += 10
            boost_reasons.append(f"🎯 BAÑOS PRIORIDAD: {prop.get('banos', 0)} (cerca de {PRIORITY_BANOS})")
        
        # Boost por área específica (±10% tolerancia) - PESO: 10
        if abs(prop.get('area_m2', 0) - PRIORITY_AREA) <= (PRIORITY_AREA * 0.1):
            boost_score += 10
            boost_reasons.append(f"🎯 ÁREA PRIORIDAD: {prop.get('area_m2', 0)} m² (cerca de {PRIORITY_AREA} m²)")
        
        # Boost por ubicación específica - PESO: 15
        if PRIORITY_UBICACION in prop.get('ubicacion', '').lower():
            boost_score += 15
            boost_reasons.append(f"🎯 UBICACIÓN PRIORIDAD: {prop.get('ubicacion', '')} (contiene 'Eco Villa')")
        
        # Boost por fecha específica - PESO: 8
        if prop.get('fecha_publicacion') == PRIORITY_FECHA:
            boost_score += 8
            boost_reasons.append(f"🎯 FECHA PRIORIDAD: {PRIORITY_FECHA}")
        
        # Boost adicional si menciona valores específicos en la query
        priority_mentions = 0
        if '485000' in query_lower or '485,000' in query_lower or '$485' in query_lower:
            priority_mentions += 1
        if '3 habitaciones' in query_lower or 'tres habitaciones' in query_lower:
            priority_mentions += 1
        if '2.5 baños' in query_lower or 'dos baños y medio' in query_lower:
            priority_mentions += 1
        if '220' in query_lower and ('m2' in query_lower or 'metros' in query_lower):
            priority_mentions += 1
        if 'eco villa' in query_lower:
            priority_mentions += 1
        if '2025-10-29' in query_lower:
            priority_mentions += 1
        
        # Boost extra por menciones específicas en la query - PESO: 6 por mención
        if priority_mentions > 0:
            mention_boost = priority_mentions * 6
            boost_score += mention_boost
            boost_reasons.append(f"🎯 MENCIÓN ESPECÍFICA: {priority_mentions} criterios específicos mencionados (+{mention_boost})")
        
        return {
            'score': boost_score,
            'reasons': boost_reasons
        }

    def _simple_text_filter(self, properties: list, query: str) -> list:
        """Filtro simple de texto como fallback."""
        query_words = [word.lower().strip() for word in query.split() if len(word.strip()) > 2]
        matches = []
        
        for prop in properties:
            text_fields = [
                prop['titulo'].lower(),
                prop['descripcion'].lower(),
                prop['tipo'].lower(),
                prop['ubicacion'].lower()
            ]
            
            full_text = ' '.join(text_fields)
            
            # Contar coincidencias de palabras
            word_matches = sum(1 for word in query_words if word in full_text)
            
            if word_matches > 0:
                prop_copy = prop.copy()
                prop_copy['_match_score'] = word_matches
                matches.append(prop_copy)
        
        # Ordenar por coincidencias
        matches.sort(key=lambda x: x['_match_score'], reverse=True)
        return matches

    def _extract_keywords(self, query: str) -> list:
        """Extrae keywords relevantes de la query."""
        # Palabras comunes a ignorar
        stop_words = {'y', 'o', 'en', 'con', 'de', 'la', 'el', 'un', 'una', 'que', 'para', 'por', 'es', 'son', 'tiene', 'busco', 'quiero', 'necesito'}
        
        words = [word.lower().strip() for word in re.split(r'[,\s]+', query) if len(word.strip()) > 2]
        keywords = [word for word in words if word not in stop_words]
        
        # Agregar números como keywords
        numbers = re.findall(r'\d+', query)
        keywords.extend(numbers)
        
        return list(set(keywords))  # Eliminar duplicados
    
    def clean_sql(self, sql: str) -> str:
        """Limpia y normaliza el SQL generado"""
        if not sql:
            return ""
        
        # Remover markdown code blocks
        sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*', '', sql)
        
        # Remover comillas invertidas alrededor del SQL completo
        sql = sql.strip('`').strip()
        
        # Remover comentarios SQL
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Remover punto y coma final
        sql = sql.rstrip(';').strip()
        
        # Limpiar espacios múltiples
        sql = re.sub(r'\s+', ' ', sql)
        
        # Si hay múltiples líneas, buscar la que empiece con SELECT
        lines = [l.strip() for l in sql.split('\n') if l.strip()]
        for line in lines:
            if line.upper().startswith('SELECT'):
                return line.strip()
        
        return sql.strip()
    
    def validate_sql(self, sql: str) -> bool:
        """Valida que el SQL sea seguro y correcto"""
        if not sql or len(sql) < 10:
            return False
        
        sql_upper = sql.upper().strip()
        
        # Debe empezar con SELECT
        if not sql_upper.startswith('SELECT'):
            logger.warning("SQL no empieza con SELECT")
            return False
        
        # Debe contener FROM propiedades
        if 'FROM PROPIEDADES' not in sql_upper:
            logger.warning("SQL no contiene FROM propiedades")
            return False
        
        # Lista de palabras peligrosas que no deben estar presentes
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 
            'ALTER', 'CREATE', 'TRUNCATE', 'EXEC',
            'EXECUTE', '--', '/*', 'UNION ALL', 'UNION SELECT'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"SQL contiene keyword peligroso: {keyword}")
                return False
        
        # Verificar que tenga LIMIT
        if 'LIMIT' not in sql_upper:
            logger.warning("SQL no contiene LIMIT, podria retornar demasiados resultados")
            # Agregar LIMIT automaticamente
            # sql += " LIMIT 20"
        
        return True

    async def validate_sql_with_ai(self, sql: str) -> dict:
        """
        Valida un query SQL usando IA para verificar sintaxis, seguridad y buenas prácticas.
        
        Returns:
            dict: {
                'valid': bool,
                'score': int (0-100),
                'issues': list,
                'suggestions': list,
                'security_level': str ('safe', 'warning', 'dangerous')
            }
        """
        try:
            if not sql or len(sql.strip()) < 5:
                return {
                    'valid': False,
                    'score': 0,
                    'issues': ['Query vacío o muy corto'],
                    'suggestions': ['Proporciona un query SQL válido'],
                    'security_level': 'safe'
                }
            
            # Prompt especializado para validación de SQL
            validation_prompt = f"""Eres un experto en bases de datos MySQL especializado en análisis y validación de consultas SQL.

ESQUEMA DE REFERENCIA:
Tabla: propiedades
Columnas: id, titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, ubicacion, fecha_publicacion, imagen_url

QUERY A VALIDAR:
{sql}

INSTRUCCIONES:
Analiza el query SQL y proporciona un análisis detallado en formato JSON con esta estructura exacta:

{{
    "valid": true/false,
    "score": 0-100,
    "issues": ["lista de problemas encontrados"],
    "suggestions": ["lista de mejoras sugeridas"],
    "security_level": "safe/warning/dangerous",
    "syntax_errors": ["errores de sintaxis específicos"],
    "performance_notes": ["observaciones de rendimiento"],
    "best_practices": ["recomendaciones de buenas prácticas"]
}}

CRITERIOS DE EVALUACIÓN:
1. Sintaxis correcta de MySQL
2. Seguridad (sin inyección SQL, sin comandos peligrosos)
3. Rendimiento (uso de índices, LIMIT apropiado)
4. Compatibilidad con el esquema de la tabla 'propiedades'
5. Buenas prácticas (nombres de columnas válidos, operadores correctos)

RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL."""

            # Llamar a la IA para validación
            response = await self.ask_ai_direct(
                prompt=validation_prompt,
                system_prompt="Eres un experto en validación de consultas SQL MySQL. Respondes únicamente con JSON válido y análisis técnico preciso."
            )
            
            if not response:
                return {
                    'valid': False,
                    'score': 0,
                    'issues': ['No se pudo validar con IA'],
                    'suggestions': ['Revisa la conexión con el servicio de IA'],
                    'security_level': 'warning'
                }
            
            # Extraer JSON de la respuesta
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                validation_result = json.loads(json_str)
                
                # Validar que tenga la estructura esperada
                required_fields = ['valid', 'score', 'issues', 'suggestions', 'security_level']
                for field in required_fields:
                    if field not in validation_result:
                        validation_result[field] = self._get_default_validation_value(field)
                
                # Asegurar que el score esté en rango válido
                if not isinstance(validation_result['score'], (int, float)) or validation_result['score'] < 0:
                    validation_result['score'] = 0
                elif validation_result['score'] > 100:
                    validation_result['score'] = 100
                
                logger.info(f"Validación IA completada - Score: {validation_result['score']}, Valid: {validation_result['valid']}")
                return validation_result
            else:
                logger.warning("No se encontró JSON válido en respuesta de validación IA")
                return self._get_fallback_validation(sql)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON de validación IA: {e}")
            return self._get_fallback_validation(sql)
        except Exception as e:
            logger.error(f"Error en validación SQL con IA: {e}")
            return self._get_fallback_validation(sql)
    
    def _get_default_validation_value(self, field: str):
        """Obtiene valores por defecto para campos de validación faltantes."""
        defaults = {
            'valid': False,
            'score': 0,
            'issues': ['Campo de validación faltante'],
            'suggestions': ['Revisa la estructura del query'],
            'security_level': 'warning',
            'syntax_errors': [],
            'performance_notes': [],
            'best_practices': []
        }
        return defaults.get(field, None)
    
    def _get_fallback_validation(self, sql: str) -> dict:
        """Validación de fallback cuando la IA no está disponible."""
        # Usar validación básica existente
        basic_valid = self.validate_sql(sql)
        
        issues = []
        suggestions = []
        security_level = 'safe'
        score = 50  # Score neutral
        
        if not basic_valid:
            issues.append('Query no pasa validación básica de seguridad')
            suggestions.append('Revisa que el query empiece con SELECT y contenga FROM propiedades')
            score = 20
        
        # Verificaciones adicionales básicas
        sql_upper = sql.upper()
        
        if 'LIMIT' not in sql_upper:
            issues.append('Query sin LIMIT podría retornar demasiados resultados')
            suggestions.append('Agrega LIMIT para limitar resultados')
            score -= 10
        
        dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE']
        for pattern in dangerous_patterns:
            if pattern in sql_upper:
                issues.append(f'Contiene operación peligrosa: {pattern}')
                security_level = 'dangerous'
                score = 0
                break
        
        if score > 70:
            security_level = 'safe'
        elif score > 40:
            security_level = 'warning'
        else:
            security_level = 'dangerous'
        
        return {
            'valid': basic_valid and score > 40,
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions,
            'security_level': security_level,
            'syntax_errors': [],
            'performance_notes': ['Validación básica aplicada (IA no disponible)'],
            'best_practices': ['Usa LIMIT para consultas grandes', 'Especifica columnas en lugar de SELECT *']
        }
       
    def load_properties_from_db_or_json_with_query(self) -> dict:
        """
        Cargar propiedades primero desde base de datos usando queries SQL generados,
        si no hay conexión usar JSON como fallback. Devuelve propiedades y query usado.
        """
        try:
            # Intentar cargar desde base de datos usando query generado por IA
            result = self.load_properties_from_generated_query_with_info()
            return {
                'properties': result['properties'],
                'query': result['query'],
                'source': 'database'
            }
        except Exception as e:
            logger.warning(f"No se pudo conectar a la base de datos: {e}")
            logger.info("Usando JSON como fallback")
            return {
                'properties': self.load_properties_json(),
                'query': None,
                'source': 'json'
            }
    
    def load_properties_from_generated_query_with_info(self) -> dict:
        """
        Cargar propiedades desde la base de datos usando un query SQL generado por IA.
        Devuelve tanto las propiedades como el query generado.
        """
        try:
            # Generar query SQL para obtener todas las propiedades
            base_query = "Obtener todas las propiedades disponibles ordenadas por fecha de publicación"
            
            logger.info("Generando query SQL con IA para cargar propiedades")
            sql_result = self.generate_sql(base_query)
            
            if not sql_result['success']:
                logger.warning(f"No se pudo generar SQL: {sql_result.get('error', 'Error desconocido')}")
                # Fallback a query directo
                properties = self.load_properties_from_database()
                return {
                    'properties': properties,
                    'query': "SELECT * FROM propiedades ORDER BY fecha_publicacion DESC LIMIT 1000"
                }
            
            generated_sql = sql_result['sql']
            logger.info(f"Query generado por IA: {generated_sql}")
            
            # Ejecutar el query generado
            properties = self.execute_generated_query(generated_sql)
            
            return {
                'properties': properties,
                'query': generated_sql
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando query generado: {e}")
            # Fallback a carga directa de base de datos
            properties = self.load_properties_from_database()
            return {
                'properties': properties,
                'query': "SELECT * FROM propiedades ORDER BY fecha_publicacion DESC LIMIT 1000"
            }
       
    def load_properties_from_db_or_json(self) -> list:
        """
        Cargar propiedades primero desde base de datos usando queries SQL generados,
        si no hay conexión usar JSON como fallback.
        """
        try:
            # Intentar cargar desde base de datos usando query generado por IA
            return self.load_properties_from_generated_query()
        except Exception as e:
            logger.warning(f"No se pudo conectar a la base de datos: {e}")
            logger.info("Usando JSON como fallback")
            return self.load_properties_json()
    
    def load_properties_from_generated_query(self) -> list:
        """
        Cargar propiedades desde la base de datos usando un query SQL generado por IA.
        """
        try:
            # Generar query SQL para obtener todas las propiedades
            base_query = "Obtener todas las propiedades disponibles ordenadas por fecha de publicación"
            
            logger.info("Generando query SQL con IA para cargar propiedades")
            sql_result = self.generate_sql(base_query)
            
            if not sql_result['success']:
                logger.warning(f"No se pudo generar SQL: {sql_result.get('error', 'Error desconocido')}")
                # Fallback a query directo
                return self.load_properties_from_database()
            
            generated_sql = sql_result['sql']
            logger.info(f"Query generado por IA: {generated_sql}")
            
            # Ejecutar el query generado
            return self.execute_generated_query(generated_sql)
            
        except Exception as e:
            logger.error(f"Error ejecutando query generado: {e}")
            # Fallback a carga directa de base de datos
            return self.load_properties_from_database()
    
    def execute_generated_query(self, sql_query: str) -> list:
        """
        Ejecutar un query SQL generado por IA en la base de datos.
        """
        try:
            # Importar dependencias de MySQL
            import mysql.connector
            from mysql.connector import Error
            
            # Configuración de conexión desde variables de entorno
            db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': int(os.environ.get('DB_PORT', 3306)),
                'database': os.environ.get('DB_NAME', 'bienes_raices'),
                'user': os.environ.get('DB_USER', 'root'),
                'password': os.environ.get('DB_PASSWORD', '')
            }
            
            # Establecer conexión
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Ejecutar el query generado por IA
            logger.info(f"Ejecutando query generado: {sql_query}")
            cursor.execute(sql_query)
            raw_properties = cursor.fetchall()
            
            # Convertir a formato consistente
            properties = []
            for item in raw_properties:
                try:
                    properties.append({
                        'id': item.get('id'),
                        'titulo': item.get('titulo', ''),
                        'descripcion': item.get('descripcion', ''),
                        'tipo': item.get('tipo', ''),
                        'precio': float(item.get('precio', 0) or 0),
                        'habitaciones': int(item.get('habitaciones', 0) or 0),
                        'banos': float(item.get('banos', 0) or 0),
                        'area_m2': float(item.get('area_m2', 0) or 0),
                        'ubicacion': item.get('ubicacion', ''),
                        'fecha_publicacion': str(item.get('fecha_publicacion', '')),
                        'imagen_url': item.get('imagen_url', '')
                    })
                except Exception as prop_error:
                    logger.warning(f"Error procesando propiedad {item.get('id', 'unknown')}: {prop_error}")
                    continue
            
            cursor.close()
            connection.close()
            
            logger.info(f"Cargadas {len(properties)} propiedades usando query generado por IA")
            return properties
            
        except ImportError:
            logger.error("mysql-connector-python no está instalado. Usar: pip install mysql-connector-python")
            raise Exception("Dependencia MySQL no disponible")
        except Exception as e:
            logger.error(f"Error ejecutando query generado: {e}")
            raise e

    def load_properties_from_database(self) -> list:
        """
        Cargar propiedades desde la base de datos usando conexión MySQL.
        """
        try:
            # Importar dependencias de MySQL
            import mysql.connector
            from mysql.connector import Error
            
            # Configuración de conexión desde variables de entorno
            db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': int(os.environ.get('DB_PORT', 3306)),
                'database': os.environ.get('DB_NAME', 'bienes_raices'),
                'user': os.environ.get('DB_USER', 'root'),
                'password': os.environ.get('DB_PASSWORD', '')
            }
            
            # Establecer conexión
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Query para obtener todas las propiedades
            query = """
            SELECT 
                id, titulo, descripcion, tipo, precio, 
                habitaciones, banos, area_m2, ubicacion, fecha_publicacion,
                imagen_url
            FROM propiedades 
            ORDER BY fecha_publicacion DESC
            LIMIT 1000
            """
            
            cursor.execute(query)
            raw_properties = cursor.fetchall()
            
            # Convertir a formato consistente
            properties = []
            for item in raw_properties:
                try:
                    properties.append({
                        'id': item.get('id'),
                        'titulo': item.get('titulo', ''),
                        'descripcion': item.get('descripcion', ''),
                        'tipo': item.get('tipo', ''),
                        'precio': float(item.get('precio', 0) or 0),
                        'habitaciones': int(item.get('habitaciones', 0) or 0),
                        'banos': float(item.get('banos', 0) or 0),
                        'area_m2': float(item.get('area_m2', 0) or 0),
                        'ubicacion': item.get('ubicacion', ''),
                        'fecha_publicacion': str(item.get('fecha_publicacion', '')),
                        'imagen_url': item.get('imagen_url', '')
                    })
                except Exception as prop_error:
                    logger.warning(f"Error procesando propiedad {item.get('id', 'unknown')}: {prop_error}")
                    continue
            
            cursor.close()
            connection.close()
            
            logger.info(f"Cargadas {len(properties)} propiedades desde base de datos")
            return properties
            
        except ImportError:
            logger.error("mysql-connector-python no está instalado. Usar: pip install mysql-connector-python")
            raise Exception("Dependencia MySQL no disponible")
        except Exception as e:
            logger.error(f"Error conectando a base de datos: {e}")
            raise e
       
    def load_properties_json(self) -> list:
        """Cargar todas las propiedades del JSON para procesamiento con IA."""
        try:
            json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'products.json')
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            properties = []
            for item in json_data:  # Cargar TODAS las propiedades para la IA
                try:
                    properties.append({
                        'id': item.get('id'),
                        'titulo': item.get('titulo', ''),
                        'descripcion': item.get('descripcion', ''),
                        'tipo': item.get('tipo', ''),
                        'precio': float(item.get('precio', 0) or 0),
                        'habitaciones': int(item.get('habitaciones', 0) or 0),
                        'banos': float(item.get('banos', 0) or 0),
                        'area_m2': float(item.get('area_m2', 0) or 0),
                        'ubicacion': item.get('ubicacion', ''),
                        'fecha_publicacion': item.get('fecha_publicacion'),
                        'imagen_url': item.get('imagen_url', '')
                    })
                except:
                    continue
            
            logger.info(f"Cargadas {len(properties)} propiedades para analisis con IA")
            return properties
            
        except Exception as e:
            logger.error(f"Error cargando JSON: {e}")
            return []

    def create_robust_prompt(self, user_query: str) -> str:
        """Crea un prompt robusto y detallado"""
        return f"""Eres un experto en bases de datos MySQL especializado en traducir lenguaje natural a consultas SQL precisas y seguras.

                ESQUEMA DE LA BASE DE DATOS:
                Tabla: propiedades
                Columnas:
                - id (INT, PRIMARY KEY): Identificador unico
                - titulo (VARCHAR): Titulo de la propiedad
                - descripcion (TEXT): Descripcion detallada
                - tipo (VARCHAR): Tipo de propiedad - valores validos: 'casa', 'departamento', 'terreno', 'local', 'oficina'
                - precio (DECIMAL): Precio en dolares USD
                - habitaciones (INT): Numero de habitaciones/recamaras/dormitorios
                - banos (INT): Numero de banos/sanitarios
                - area_m2 (DECIMAL): Area en metros cuadrados
                - ubicacion (VARCHAR): Ubicacion/zona (ejemplo: 'zona 10', 'zona 15', 'carretera a el salvador')
                - fecha_publicacion (DATE): Fecha de publicacion

                REGLAS ESTRICTAS (CRITICO - DEBES SEGUIRLAS):
                1. Responde UNICAMENTE con la consulta SQL, sin explicaciones adicionales
                2. NO incluyas markdown (```sql), comentarios, ni texto antes o despues del SQL
                3. La consulta DEBE empezar con: SELECT * FROM propiedades
                4. SIEMPRE incluye una clausula LIMIT (maximo 50 resultados)
                5. Para busquedas de texto usa LIKE con porcentajes: ubicacion LIKE '%zona 10%'
                6. Los valores de texto DEBEN ir entre comillas simples: tipo = 'casa'
                7. Para fechas recientes usa: fecha_publicacion >= DATE_SUB(CURDATE(), INTERVAL X DAY)
                8. NO uses punto y coma (;) al final de la consulta
                9. Si la consulta menciona precios, asume que estan en dolares

                CONVERSIONES COMUNES:
                - "zona X" -> ubicacion LIKE '%zona X%'
                - "menos de $X" o "menor a $X" -> precio < X
                - "mas de X habitaciones" -> habitaciones > X
                - "entre $X y $Y" -> precio BETWEEN X AND Y
                - "ultimos X dias" -> fecha_publicacion >= DATE_SUB(CURDATE(), INTERVAL X DAY)
                - "barato" -> ORDER BY precio ASC LIMIT 20
                - "caro" -> ORDER BY precio DESC LIMIT 20
                - "grande" -> ORDER BY area_m2 DESC
                - "reciente" -> ORDER BY fecha_publicacion DESC

                EJEMPLOS DE TRADUCCION:
                Entrada: "Casas de 3 habitaciones en zona 10"
                Salida: SELECT * FROM propiedades WHERE tipo = 'casa' AND habitaciones = 3 AND ubicacion LIKE '%zona 10%' LIMIT 20

                Entrada: "Departamentos baratos"
                Salida: SELECT * FROM propiedades WHERE tipo = 'departamento' ORDER BY precio ASC LIMIT 20

                Entrada: "Propiedades con mas de 2 banos y al menos 150 metros cuadrados"
                Salida: SELECT * FROM propiedades WHERE banos > 2 AND area_m2 >= 150 LIMIT 20

                Entrada: "Terrenos entre 50000 y 100000 dolares"
                Salida: SELECT * FROM propiedades WHERE tipo = 'terreno' AND precio BETWEEN 50000 AND 100000 LIMIT 20

                CONSULTA DEL USUARIO:
                {user_query}

                IMPORTANTE: Responde SOLO con el SQL, nada mas.

                SQL:"""
    
# Instancia singleton del servicio
llm_service = LLMService()
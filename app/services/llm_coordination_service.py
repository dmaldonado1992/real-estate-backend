"""
Servicio LLM modular que coordina todas las operaciones de IA y búsqueda de propiedades
"""
import re
import logging
from typing import Dict, List, Optional
from .ollama_client_service import OllamaClient
from .sql_validation_service import SQLService
from .data_loader_service import DataLoader
from .property_search_service import PropertySearchService

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """
        Inicializa el servicio LLM modular con todos los componentes
        """
        # Inicializar componentes
        self.ollama_client = OllamaClient()
        self.sql_service = SQLService(self.ollama_client)
        self.data_loader = DataLoader(self.sql_service)
        self.search_service = PropertySearchService(self.ollama_client)
        
        logger.info("LLM Service modular inicializado correctamente")

    # ==================== MÉTODOS PRINCIPALES ====================

    async def search_ia_real_state(self, query: str, use_cloud: bool = True) -> dict:
        """
        Búsqueda inteligente de propiedades inmobiliarias con múltiples estrategias
        """
        try:
            logger.info(f"Iniciando búsqueda IA para: '{query}'")
            
            # 1. Cargar propiedades desde base de datos o JSON
            data_result = self.data_loader.load_properties_from_db_or_json_with_query()
            properties = data_result.get('properties', [])
            
            if not properties:
                logger.warning("No se encontraron propiedades para buscar")
                return {
                    'properties': [],
                    'keywords': self._extract_keywords(query),
                    'analysis': 'No hay propiedades disponibles en la base de datos.',
                    'metadata': {
                        'total_found': 0,
                        'search_strategy': 'none',
                        'data_source': data_result.get('data_source', 'none'),
                        'generated_sql': data_result.get('generated_sql'),
                        'user_query': query,
                        'ai_used': False,
                        'boost_applied': False
                    }
                }
            
            # 2. Aplicar filtros exactos primero
            exact_matches = self.search_service.filter_exact_matches(properties, query)
            
            # 3. Si tenemos coincidencias exactas, priorizarlas (cambiado el umbral)
            final_properties = exact_matches
            search_strategy = 'exact_filters'
            
            # Si hay pocos resultados exactos (menos de 3), complementar con búsqueda semántica
            if len(exact_matches) < 3 and use_cloud:
                try:
                    semantic_results = await self.search_service.ai_semantic_search(properties, query)
                    # Solo usar semántica si mejora significativamente los resultados
                    if len(semantic_results) > len(exact_matches) * 1.5:
                        final_properties = semantic_results
                        search_strategy = 'ai_semantic'
                        logger.info(f"Usando búsqueda semántica: {len(semantic_results)} resultados")
                    else:
                        # Combinar resultados exactos con algunos semánticos
                        combined_results = exact_matches[:]
                        for prop in semantic_results[:5]:  # Máximo 5 adicionales
                            if prop not in combined_results:
                                combined_results.append(prop)
                        final_properties = combined_results
                        search_strategy = 'exact_plus_semantic'
                except Exception as e:
                    logger.warning(f"Error en búsqueda semántica: {e}")
            
            # 4. Solo usar filtro de texto simple si no hay resultados exactos
            if len(final_properties) == 0:
                text_results = self.search_service._simple_text_filter(properties, query)
                if len(text_results) > 0:
                    final_properties = text_results
                    search_strategy = 'text_filter'
                    logger.info(f"Usando filtro de texto como último recurso: {len(text_results)} resultados")
            
            # 5. Aplicar boost de puntuación para características específicas
            numbers = re.findall(r'\d+(?:\.\d+)?', query)
            numbers = [float(n) for n in numbers]
            query_lower = query.lower()
            
            for prop in final_properties:
                boost_info = self.search_service.calculate_specific_boost(prop, query_lower, numbers)
                prop['_boost_score'] = boost_info['total_boost']
                prop['_boost_reasons'] = boost_info['reasons']
            
            # 6. Ordenar por boost score si hay boosts aplicados
            if any(prop.get('_boost_score', 0) > 0 for prop in final_properties):
                final_properties.sort(key=lambda x: x.get('_boost_score', 0), reverse=True)
                search_strategy += '_with_boost'
            
            # 7. Limitar resultados
            max_results = 10
            limited_properties = final_properties[:max_results]
            
            # 8. Limpiar campos internos antes de retornar
            for prop in limited_properties:
                prop.pop('_boost_score', None)
                prop.pop('_boost_reasons', None)
                prop.pop('_match_score', None)
                prop.pop('_match_reasons', None)
            
            # 9. Extraer keywords de la query
            keywords = self._extract_keywords(query)
            
            # 10. Generar análisis descriptivo
            analysis = self._generate_analysis(query, len(limited_properties), search_strategy)
            
            logger.info(f"Búsqueda completada: {len(limited_properties)} propiedades, estrategia: {search_strategy}")
            
            return {
                'properties': limited_properties,
                'keywords': keywords[:5],  # Máximo 5 keywords
                'analysis': analysis,
                'metadata': {
                    'total_found': len(limited_properties),
                    'search_strategy': search_strategy,
                    'data_source': data_result.get('data_source', 'unknown'),
                    'generated_sql': data_result.get('generated_sql'),
                    'user_query': query,
                    'ai_used': 'ai_semantic' in search_strategy,
                    'boost_applied': '_with_boost' in search_strategy
                }
            }
            
        except Exception as e:
            logger.error(f"Error en search_ia_real_state: {e}")
            return {
                'properties': [],
                'keywords': [],
                'analysis': f'Error en búsqueda: {str(e)}',
                'metadata': {
                    'total_found': 0,
                    'search_strategy': 'error',
                    'data_source': 'error',
                    'generated_sql': None,
                    'user_query': query,
                    'ai_used': False,
                    'boost_applied': False,
                    'error': str(e)
                }
            }

    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extrae keywords relevantes de la consulta del usuario
        """
        import re
        
        # Palabras comunes a ignorar
        stop_words = {
            'el', 'la', 'de', 'en', 'y', 'a', 'que', 'con', 'por', 'para', 'un', 'una', 
            'es', 'se', 'del', 'los', 'las', 'al', 'te', 'le', 'da', 'su', 'sus',
            'busco', 'quiero', 'necesito', 'tengo', 'hay', 'está', 'son', 'tienen'
        }
        
        # Extraer palabras
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Extraer números como keywords especiales
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        for num in numbers:
            keywords.append(f"${num}" if float(num) > 1000 else num)
        
        # Detectar tipos de propiedad
        property_types = ['casa', 'departamento', 'terreno', 'local', 'oficina', 'duplex']
        for prop_type in property_types:
            if prop_type in query.lower():
                keywords.insert(0, prop_type)  # Priorizar tipos de propiedad
        
        return list(dict.fromkeys(keywords))  # Eliminar duplicados manteniendo orden

    def _generate_analysis(self, query: str, results_count: int, strategy: str) -> str:
        """
        Genera un análisis descriptivo de la búsqueda realizada
        """
        if results_count == 0:
            return f"No se encontraron propiedades que coincidan con '{query}'. Intenta con criterios más amplios o diferentes palabras clave."
        
        # Análisis base
        analysis_parts = []
        
        # Resultados encontrados
        if results_count == 1:
            analysis_parts.append("Se encontró 1 propiedad")
        else:
            analysis_parts.append(f"Se encontraron {results_count} propiedades")
        
        # Estrategia utilizada
        strategy_descriptions = {
            'exact_filters': 'mediante filtros exactos de características específicas',
            'exact_filters_with_boost': 'con filtros exactos y priorización de características relevantes',
            'ai_semantic': 'usando búsqueda semántica con inteligencia artificial',
            'ai_semantic_with_boost': 'combinando IA semántica con boost de características específicas',
            'text_filter': 'mediante filtrado de texto simple',
            'text_filter_with_boost': 'con filtrado de texto y priorización inteligente'
        }
        
        strategy_desc = strategy_descriptions.get(strategy, 'usando estrategia de búsqueda avanzada')
        analysis_parts.append(strategy_desc)
        
        # Detectar características específicas mencionadas
        query_lower = query.lower()
        features = []
        
        if any(word in query_lower for word in ['3 habitaciones', 'tres habitaciones']):
            features.append('3 habitaciones')
        if any(word in query_lower for word in ['zona 10', 'zona diez']):
            features.append('zona 10')
        if 'precio' in query_lower or '$' in query:
            features.append('precio específico')
        if any(word in query_lower for word in ['jardín', 'jardin', 'piscina', 'garage']):
            features.append('características especiales')
        
        if features:
            analysis_parts.append(f"priorizando: {', '.join(features)}")
        
        # Recomendaciones
        recommendations = []
        if results_count > 8:
            recommendations.append("Considera refinar tu búsqueda con criterios más específicos")
        elif results_count < 3:
            recommendations.append("Intenta ampliar los criterios de búsqueda para más opciones")
        
        if 'boost' in strategy:
            recommendations.append("Los resultados están ordenados por relevancia según tus criterios")
        
        analysis = '. '.join(analysis_parts) + '.'
        
        if recommendations:
            analysis += ' ' + '. '.join(recommendations) + '.'
        
        return analysis

    # ==================== MÉTODOS DELEGADOS ====================

    async def ask_ai_direct(self, prompt: str, system_prompt: str = None) -> str:
        """Delegado a OllamaClient"""
        return await self.ollama_client.ask_ai_direct(prompt, system_prompt)

    async def search_ia(self, query: str, properties_context: str = None) -> str:
        """Delegado a PropertySearchService"""
        return await self.search_service.search_ia(query, properties_context)

    def call_ollama(self, prompt: str, use_sql_system_prompt: bool = True) -> Optional[str]:
        """Delegado a OllamaClient"""
        return self.ollama_client.call_ollama(prompt, use_sql_system_prompt)

    def generate_sql(self, user_query: str) -> Dict[str, any]:
        """Delegado a SQLService"""
        return self.sql_service.generate_sql(user_query)

    async def generate_sql_async(self, user_query: str) -> Dict[str, any]:
        """Versión asíncrona de generate_sql"""
        try:
            prompt = f"""
            Genera una consulta SQL para buscar propiedades inmobiliarias basada en esta consulta: "{user_query}"

            Esquema de la tabla:
            CREATE TABLE propiedades (
                id INT PRIMARY KEY,
                titulo VARCHAR(255),
                descripcion TEXT,
                tipo ENUM('casa', 'departamento', 'terreno'),
                precio DECIMAL(12,2),
                habitaciones INT,
                banos DECIMAL(3,1),
                area_m2 DECIMAL(8,2),
                ubicacion VARCHAR(255),
                fecha_publicacion DATE,
                imagen_url VARCHAR(500)
            );

            Instrucciones:
            - Usa LIKE '%valor%' para búsquedas de texto flexibles
            - Para precios, usa rangos razonables si no se especifica exacto
            - Incluye LIMIT 50 para evitar resultados excesivos
            - Ordena por relevancia (precio, fecha_publicacion)
            - Usa OR para múltiples criterios similares
            - Si mencionan ubicación, busca en campo ubicacion

            Responde SOLO con la query SQL, sin explicaciones.
            """
            
            system_prompt = 'Eres un experto en SQL que genera consultas MySQL precisas. Respondes UNICAMENTE con SQL valido, sin explicaciones.'
            sql_response = await self.ollama_client.ask_ai_direct(prompt, system_prompt)
            
            if sql_response and not sql_response.startswith("Error:"):
                clean_sql = self.sql_service.clean_sql(sql_response)
                return {
                    'success': True,
                    'sql': clean_sql,
                    'original_response': sql_response
                }
            else:
                return {
                    'success': False,
                    'error': 'No se pudo generar SQL',
                    'sql': None
                }
                
        except Exception as e:
            logger.error(f"Error generando SQL async: {e}")
            return {
                'success': False,
                'error': str(e),
                'sql': None
            }

    def clean_sql(self, sql: str) -> str:
        """Delegado a SQLService"""
        return self.sql_service.clean_sql(sql)

    def validate_sql(self, sql: str) -> bool:
        """Delegado a SQLService"""
        return self.sql_service.validate_sql(sql)

    async def validate_sql_with_ai(self, sql: str) -> dict:
        """Delegado a SQLService"""
        return await self.sql_service.validate_sql_with_ai(sql)

    def load_properties_from_db_or_json_with_query(self) -> dict:
        """Delegado a DataLoader"""
        return self.data_loader.load_properties_from_db_or_json_with_query()

    def load_properties_from_generated_query_with_info(self, user_query: str) -> dict:
        """Delegado a DataLoader"""
        return self.data_loader.load_properties_from_generated_query_with_info(user_query)

    def execute_generated_query(self, sql: str) -> Optional[List[Dict]]:
        """Delegado a DataLoader"""
        return self.data_loader.execute_generated_query(sql)

    def load_properties_from_db_or_json(self) -> list:
        """Delegado a DataLoader"""
        return self.data_loader.load_properties_from_db_or_json()

    # ==================== MÉTODOS DE BÚSQUEDA ESPECÍFICOS ====================

    def _filter_exact_matches(self, properties: list, query: str) -> list:
        """Delegado a PropertySearchService"""
        return self.search_service.filter_exact_matches(properties, query)

    def _extract_filters(self, query_lower: str, numbers: list) -> dict:
        """Delegado a PropertySearchService"""
        return self.search_service._extract_filters(query_lower, numbers)

    def _matches_strict_filters(self, prop: dict, filters: dict) -> bool:
        """Delegado a PropertySearchService"""
        return self.search_service._matches_strict_filters(prop, filters)

    async def _ai_semantic_search(self, properties: list, query: str) -> list:
        """Delegado a PropertySearchService"""
        return await self.search_service.ai_semantic_search(properties, query)

    def _calculate_specific_boost(self, prop: dict, query_lower: str, numbers: list) -> dict:
        """Delegado a PropertySearchService"""
        return self.search_service.calculate_specific_boost(prop, query_lower, numbers)

    def _simple_text_filter(self, properties: list, query: str) -> list:
        """Delegado a PropertySearchService"""
        return self.search_service._simple_text_filter(properties, query)

    def _extract_keywords(self, query: str) -> list:
        """Delegado a PropertySearchService"""
        return self.search_service._extract_keywords(query)

    # ==================== MÉTODOS DE COMPATIBILIDAD ====================

    def _get_default_validation_value(self, field: str):
        """Delegado a SQLService para compatibilidad"""
        return self.sql_service._get_default_validation_value(field)

    def _get_fallback_validation(self, sql: str) -> dict:
        """Delegado a SQLService para compatibilidad"""
        return self.sql_service._get_fallback_validation(sql)
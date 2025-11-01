"""
Servicio para generación y validación de SQL
"""
import re
import json
import logging
from typing import Dict, Optional
from .ollama_client_service import OllamaClient

logger = logging.getLogger(__name__)

class SQLService:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama_client = ollama_client

    def generate_sql(self, user_query: str) -> Dict[str, any]:
        """
        Genera SQL usando IA basado en consulta de usuario
        """
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
            
            sql_response = self.ollama_client.call_ollama(prompt, use_sql_system_prompt=True)
            
            if sql_response:
                clean_sql = self.clean_sql(sql_response)
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
            logger.error(f"Error generando SQL: {e}")
            return {
                'success': False,
                'error': str(e),
                'sql': None
            }

    def clean_sql(self, sql: str) -> str:
        """
        Limpia y normaliza una consulta SQL
        """
        if not sql:
            return ""
        
        # Remover comentarios
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        
        # Remover caracteres de código markdown si existen
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*$', '', sql)
        sql = re.sub(r'`', '', sql)
        
        # Limpiar espacios y saltos de línea excesivos
        sql = re.sub(r'\s+', ' ', sql)
        sql = sql.strip()
        
        # Agregar punto y coma al final si no lo tiene
        if sql and not sql.endswith(';'):
            sql += ';'
        
        return sql

    def validate_sql(self, sql: str) -> bool:
        """
        Validación básica de SQL para seguridad
        """
        if not sql or len(sql.strip()) < 10:
            return False
        
        sql_lower = sql.lower().strip()
        
        # Comandos peligrosos prohibidos
        dangerous_commands = [
            'drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update',
            'grant', 'revoke', 'use', 'show', 'describe', 'exec', 'execute',
            'sp_', 'xp_', '--', '/*', '*/', 'union', 'information_schema'
        ]
        
        for cmd in dangerous_commands:
            if cmd in sql_lower:
                logger.warning(f"Comando peligroso detectado: {cmd}")
                return False
        
        # Debe empezar con SELECT
        if not sql_lower.startswith('select'):
            return False
        
        # Debe referenciar la tabla propiedades
        if 'propiedades' not in sql_lower:
            return False
        
        return True

    async def validate_sql_with_ai(self, sql: str) -> dict:
        """
        Valida una consulta SQL usando IA para análisis profundo de:
        - Sintaxis correcta
        - Seguridad (inyección SQL, comandos peligrosos)
        - Rendimiento (uso de índices, LIMIT, etc.)
        - Mejores prácticas
        
        Retorna un dict con:
        - valid: bool
        - score: int (0-100)
        - issues: list
        - suggestions: list
        - security_level: str ('safe', 'warning', 'dangerous')
        """
        try:
            # Validación básica primero
            if not sql or len(sql.strip()) < 5:
                return self._get_fallback_validation("Query vacío o muy corto")
            
            # Prompt para análisis de IA
            validation_prompt = f"""
            Analiza esta consulta SQL y evalúa:
            
            1. SINTAXIS: ¿Es sintácticamente correcta?
            2. SEGURIDAD: ¿Tiene riesgos de inyección SQL o comandos peligrosos?
            3. RENDIMIENTO: ¿Usa LIMIT? ¿Está optimizada?
            4. MEJORES PRÁCTICAS: ¿Sigue estándares MySQL?
            
            SQL a analizar: {sql}
            
            Esquema esperado:
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
            
            Responde ÚNICAMENTE con un JSON válido en este formato exacto:
            {{
                "valid": true/false,
                "score": 0-100,
                "issues": ["problema1", "problema2"],
                "suggestions": ["mejora1", "mejora2"],
                "security_level": "safe/warning/dangerous"
            }}
            """
            
            system_prompt = "Eres un experto en bases de datos MySQL que analiza consultas SQL. Respondes ÚNICAMENTE en formato JSON válido, sin explicaciones adicionales."
            
            ai_response = await self.ollama_client.ask_ai_direct(validation_prompt, system_prompt)
            
            if not ai_response or "Error:" in ai_response:
                logger.warning(f"Error en validación con IA: {ai_response}")
                return self._get_fallback_validation("No se pudo validar con IA")
            
            try:
                # Limpiar respuesta de markdown si existe
                response_clean = ai_response.strip()
                if response_clean.startswith('```json'):
                    response_clean = response_clean.replace('```json', '').replace('```', '').strip()
                elif response_clean.startswith('```'):
                    response_clean = response_clean.replace('```', '').strip()
                
                # Intentar parsear el JSON de respuesta
                validation_result = json.loads(response_clean)
                
                # Validar que tenga los campos requeridos
                required_fields = ['valid', 'score', 'issues', 'suggestions', 'security_level']
                for field in required_fields:
                    if field not in validation_result:
                        validation_result[field] = self._get_default_validation_value(field)
                
                # Asegurar tipos correctos
                validation_result['valid'] = bool(validation_result.get('valid', False))
                validation_result['score'] = max(0, min(100, int(validation_result.get('score', 0))))
                validation_result['issues'] = list(validation_result.get('issues', []))
                validation_result['suggestions'] = list(validation_result.get('suggestions', []))
                
                security_level = validation_result.get('security_level', 'warning')
                if security_level not in ['safe', 'warning', 'dangerous']:
                    security_level = 'warning'
                validation_result['security_level'] = security_level
                
                logger.info(f"Validación SQL exitosa: valid={validation_result['valid']}, score={validation_result['score']}")
                return validation_result
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON de IA: {e}, Response: {ai_response[:200]}")
                return self._get_fallback_validation("Respuesta de IA inválida")
                
        except Exception as e:
            logger.error(f"Error en validate_sql_with_ai: {e}")
            return self._get_fallback_validation(f"Error de validación: {str(e)}")

    def _get_default_validation_value(self, field: str):
        """Retorna valores por defecto para campos de validación"""
        defaults = {
            'valid': False,
            'score': 0,
            'issues': ["No se pudo validar completamente"],
            'suggestions': ["Revisa la consulta manualmente"],
            'security_level': 'warning'
        }
        return defaults.get(field, None)

    def _get_fallback_validation(self, sql: str) -> dict:
        """
        Validación de respaldo cuando la IA no está disponible
        """
        if not sql or len(sql.strip()) < 5:
            return {
                'valid': False,
                'score': 0,
                'issues': ["Query vacío o muy corto"],
                'suggestions': ["Proporciona un query SQL válido"],
                'security_level': 'safe'
            }
        
        sql_lower = sql.lower().strip()
        issues = []
        suggestions = []
        score = 50  # Score base
        security_level = 'safe'
        
        # Verificaciones básicas de seguridad
        dangerous_patterns = ['drop', 'delete', 'truncate', 'alter', 'insert', 'update', 'grant', 'revoke']
        for pattern in dangerous_patterns:
            if pattern in sql_lower:
                issues.append(f"Comando potencialmente peligroso detectado: {pattern}")
                security_level = 'dangerous'
                score = 0
        
        # Verificar que sea SELECT
        if not sql_lower.startswith('select'):
            issues.append("La consulta debe empezar con SELECT")
            score -= 20
        
        # Verificar tabla propiedades
        if 'propiedades' not in sql_lower:
            issues.append("La consulta debe referenciar la tabla 'propiedades'")
            score -= 15
        
        # Verificar LIMIT
        if 'limit' not in sql_lower:
            issues.append("Considera agregar LIMIT para mejorar rendimiento")
            suggestions.append("Agrega LIMIT para limitar resultados")
            score -= 10
            if security_level == 'safe':
                security_level = 'warning'
        
        # Determinar validez
        valid = len(issues) == 0 or (security_level != 'dangerous' and score > 30)
        
        if not issues:
            suggestions.append("La consulta parece básicamente correcta")
        
        return {
            'valid': valid,
            'score': max(0, score),
            'issues': issues,
            'suggestions': suggestions,
            'security_level': security_level
        }
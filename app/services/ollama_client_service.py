"""
Cliente para comunicación con Ollama Cloud y Local
"""
import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, Optional
from dotenv import load_dotenv

# Limpiar variables de entorno existentes y cargar desde .env
os.environ.pop('OLLAMA_API_KEY', None)
os.environ.pop('USE_OLLAMA_CLOUD', None)
os.environ.pop('OLLAMA_MODEL', None)

# Cargar variables de entorno desde .env con override
load_dotenv(override=True)

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        """
        Inicializa el cliente Ollama con configuración Cloud o Local
        """
        # Cargar configuración directamente desde .env
        self.use_cloud = os.getenv('USE_OLLAMA_CLOUD', 'true').lower() == 'true'
        
        if self.use_cloud:
            # Configuración para Ollama Cloud con API REST
            self.api_key = os.getenv('OLLAMA_API_KEY')
            if not self.api_key:
                raise ValueError("OLLAMA_API_KEY no está configurado en el archivo .env")
            
            self.base_url = "https://ollama.com/api"
            self.model = os.getenv('OLLAMA_MODEL', 'deepseek-v3.1:671b-cloud')
            logger.info(f"Usando Ollama Cloud (API REST) con modelo: {self.model}")
            logger.info(f"API Key cargada: {self.api_key[:20]}...")
        else:
            # Configuración para Ollama Local
            ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
            self.base_url = f"{ollama_url}/api"
            self.model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
            self.api_key = None
            logger.info(f"Usando Ollama Local en {ollama_url} con modelo: {self.model}")
        
        self.timeout = 60

    def call_ollama(self, prompt: str, use_sql_system_prompt: bool = True) -> Optional[str]:
        """Llama a Ollama usando API REST síncrono (Cloud o Local)"""
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

    async def _async_call_ollama(self, messages: list) -> Optional[str]:
        """Método interno para llamada asíncrona a Ollama"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        if self.use_cloud and self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        payload = {
            'model': self.model,
            'messages': messages,
            'stream': False
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(
                        f"{self.base_url}/chat",
                        headers=headers,
                        json=payload
                    ) as response:
                        
                        if response.status == 200:
                            data = await response.json()
                            content = data.get('message', {}).get('content', '').strip()
                            if content:
                                return content
                            else:
                                logger.warning("Respuesta vacía de Ollama")
                                return None
                        else:
                            error_text = await response.text()
                            logger.error(f"Error HTTP {response.status}: {error_text}")
                            
                            if response.status == 401:
                                logger.error("Error de autenticación con Ollama Cloud")
                                return None
                            
                            if attempt < max_retries - 1:
                                logger.info(f"Reintentando en {retry_delay} segundos...")
                                await asyncio.sleep(retry_delay)
                                retry_delay *= 2
                            else:
                                return None
                                
            except asyncio.TimeoutError:
                logger.error(f"Timeout en intento {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None
        
        return None

    async def ask_ai_direct(self, prompt: str, system_prompt: str = None) -> str:
        """
        Método directo para hacer preguntas a la IA con system prompt personalizable
        """
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            if self.use_cloud and self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            messages = []
            if system_prompt:
                messages.append({
                    'role': 'system',
                    'content': system_prompt
                })
            
            messages.append({
                'role': 'user',
                'content': prompt
            })
            
            payload = {
                'model': self.model,
                'messages': messages,
                'stream': False
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(f"{self.base_url}/chat", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('message', {}).get('content', '').strip()
                    else:
                        error_text = await response.text()
                        logger.error(f"Error HTTP {response.status}: {error_text}")
                        return f"Error: No se pudo obtener respuesta del LLM"
        except Exception as e:
            logger.error(f"Error en ask_ai_direct: {e}")
            return f"Error: {str(e)}"
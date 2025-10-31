"""
Servicio LLM muy simple que usa únicamente Ollama local.
Elimina cualquier referencia a proveedores cloud/Claude/Anthropic.
"""
from typing import List
import os
import asyncio
from dotenv import load_dotenv
import ollama

load_dotenv()


class LLMService:
    def __init__(self, model_name: str = "llama3.2:1b"):
        self.model_name = model_name
        self.provider = "ollama_local"
        try:
            # Cliente Ollama local (por defecto conecta a http://127.0.0.1:11434)
            self.client = ollama.Client()
            print(f"LLMService: usando Ollama local con modelo {self.model_name}")
        except Exception as e:
            print(f"LLMService: error iniciando cliente Ollama local: {e}")
            self.client = None

    def _chat_sync(self, messages: List[dict], options: dict = None) -> str:
        options = options or {"num_predict": 128, "temperature": 0.7}
        if not self.client:
            raise RuntimeError("Cliente Ollama no inicializado")
        resp = self.client.chat(model=self.model_name, messages=messages, options=options)
        return resp.get("message", {}).get("content", "")

    async def _chat(self, messages: List[dict], options: dict = None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._chat_sync, messages, options)

    async def test_connection(self) -> bool:
        try:
            messages = [{"role": "user", "content": "Hola"}]
            resp = await self._chat(messages, options={"num_predict": 8})
            return bool(resp and len(resp) > 0)
        except Exception as e:
            print(f"LLMService.test_connection error: {e}")
            return False

    async def get_product_description(self, product_name: str) -> str:
        messages = [
            {
                "role": "system",
                "content": "Eres un experto en marketing que escribe descripciones atractivas de productos en español. Sé conciso."
            },
            {"role": "user", "content": f"Escribe una descripción breve y atractiva para: {product_name}"}
        ]
        try:
            resp = await self._chat(messages)
            return resp.strip()
        except Exception as e:
            return f"Error generando descripción: {e}"

    async def get_product_recommendations(self, product_description: str, num_recommendations: int = 3) -> List[str]:
        messages = [
            {"role": "system", "content": "Eres un sistema que recomienda productos relacionados en español. Devuelve solo una lista de nombres, uno por línea."},
            {"role": "user", "content": f"Basado en: {product_description}, sugiere {num_recommendations} productos relacionados."}
        ]
        try:
            resp = await self._chat(messages)
            lines = [l.strip() for l in resp.splitlines() if l.strip()]
            # limpiar numeración
            clean = []
            for l in lines:
                if l and (l[0].isdigit() and "." in l[:4]):
                    _, rest = l.split(".", 1)
                    clean.append(rest.strip())
                else:
                    clean.append(l)
            return clean[:num_recommendations]
        except Exception as e:
            return [f"Error: {e}"]
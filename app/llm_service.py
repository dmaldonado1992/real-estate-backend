from typing import Optional
import openai

class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            openai.api_key = api_key
        
    async def get_product_description(self, product_name: str) -> str:
        """
        Descripción de producto 
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en marketing que escribe descripciones atractivas de productos."},
                    {"role": "user", "content": f"Escribe una descripción breve pero atractiva para este producto: {product_name}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"No se pudo generar la descripción: {str(e)}"

    async def get_product_recommendations(self, product_description: str, num_recommendations: int = 3) -> list:
        """
        Genera recomendaciones de productos relacionados
        """
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un experto en recomendaciones de productos."},
                    {"role": "user", "content": f"Basado en este producto: {product_description}, sugiere {num_recommendations} productos relacionados"}
                ]
            )
            recommendations = response.choices[0].message.content.strip().split("\n")
            return recommendations[:num_recommendations]
        except Exception as e:
            return [f"Error al generar recomendaciones: {str(e)}"]
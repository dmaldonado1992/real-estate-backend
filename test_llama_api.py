import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.llm_service import LLMService

async def test_llama_api():
    """Test the Llama API configuration"""
    service = LLMService()
    
    print("✅ Configuración:")
    print(f"   - Provider: {service.provider}")
    print(f"   - Modelo local: {service.model_name}")
    
    print("\n🧪 Probando conexión...")
    try:
        is_working = await service.test_connection()
        if is_working:
            print("✅ ¡Conexión exitosa!")
        else:
            print("❌ Conexión falló")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🧪 Probando generación de descripción...")
    try:
        description = await service.get_product_description("Smartphone Samsung Galaxy")
        print(f"📝 Descripción generada:")
        print(f"   {description}")
    except Exception as e:
        print(f"❌ Error generando descripción: {e}")

if __name__ == "__main__":
    asyncio.run(test_llama_api())
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_api_providers():
    """Probar diferentes proveedores de API para encontrar el correcto"""
    api_key = os.getenv("LLAMA_API_KEY")
    if not api_key:
        print("❌ No API key found")
        return None
    
    providers = [
        {
            "name": "Groq",
            "url": "https://api.groq.com/openai/v1/chat/completions",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "model": "llama3-8b-8192",
            "format": "openai"
        },
        {
            "name": "Together AI", 
            "url": "https://api.together.xyz/v1/chat/completions",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "model": "meta-llama/Llama-2-7b-chat-hf",
            "format": "openai"
        },
        {
            "name": "Perplexity",
            "url": "https://api.perplexity.ai/chat/completions", 
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "model": "llama-3.1-sonar-small-128k-online",
            "format": "openai"
        },
        {
            "name": "Fireworks",
            "url": "https://api.fireworks.ai/inference/v1/chat/completions",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "model": "accounts/fireworks/models/llama-v3-8b-instruct",
            "format": "openai"
        }
    ]
    
    test_messages = [{"role": "user", "content": "Hola, responde solo 'OK'"}]
    
    for provider in providers:
        try:
            print(f"🧪 Probando {provider['name']}...")
            
            payload = {
                "model": provider["model"],
                "messages": test_messages,
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    provider["url"],
                    headers=provider["headers"],
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        print(f"✅ {provider['name']} funciona! Respuesta: {content}")
                        return provider
                    else:
                        print(f"❌ {provider['name']}: Formato de respuesta inválido")
                else:
                    print(f"❌ {provider['name']}: {response.status_code} - {response.text[:100]}")
                    
        except Exception as e:
            print(f"❌ {provider['name']}: Error - {str(e)[:100]}")
    
    print("❌ Ningún proveedor funcionó con esta API key")
    return None

if __name__ == "__main__":
    result = asyncio.run(test_api_providers())
    if result:
        print(f"\n🎉 Proveedor recomendado: {result['name']}")
        print(f"   URL: {result['url']}")
        print(f"   Modelo: {result['model']}")
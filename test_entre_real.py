"""
Test real de búsqueda con "entre"
"""
import asyncio
from app.services.llm_coordination_service import LLMService

async def test_entre_search():
    print("🧪 Probando búsqueda real con 'entre'...\n")
    
    llm_service = LLMService()
    
    # Casos de prueba con "entre"
    queries = [
        "Entre 200 y 400 mil",
        "entre 300000 y 500000",
        "Busco casa entre 200 mil y 300 mil",
        "Apartamento entre 250 mil y 350 mil en zona 10"
    ]
    
    for query in queries:
        print(f"📝 Query: '{query}'")
        try:
            result = await llm_service.search_ia_real_state(query, use_cloud=True)
            
            print(f"   Propiedades encontradas: {len(result.get('properties', []))}")
            print(f"   Metadata: {result.get('metadata', {})}")
            
            # Mostrar primeras 3 propiedades con precios
            props = result.get('properties', [])[:3]
            for i, prop in enumerate(props, 1):
                print(f"   {i}. {prop.get('titulo')} - Q{prop.get('precio'):,.0f}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_entre_search())

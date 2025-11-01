"""
Test para verificar detección de rangos de precio
"""
import asyncio
from app.services.ollama_client_service import OllamaClient
from app.services.property_search_service import PropertySearchService

async def test_price_ranges():
    print("🧪 Probando detección de rangos de precio...\n")
    
    ollama_client = OllamaClient()
    search_service = PropertySearchService(ollama_client)
    
    # Casos de prueba
    test_cases = [
        "Menos de 300 mil",
        "Más de 300 mil",
        "menos de 500 mil",
        "mas de 200 mil",
        "Entre 200 y 400 mil",
        "Hasta 350 mil",
        "Desde 250 mil",
        "Máximo 300000",
        "Mínimo 400000",
        "Casa menos de 300 mil en zona 10",
        "Apartamento más de 500 mil con 3 habitaciones",
        "Entre 1 millón y 2 millones",
        "Menos de 1.5 millones",
    ]
    
    for query in test_cases:
        print(f"📝 Query: '{query}'")
        
        # Extraer números
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        numbers = [float(n) for n in numbers]
        
        # Extraer filtros
        filters = search_service._extract_filters(query.lower(), numbers)
        
        print(f"   Números detectados: {numbers}")
        print(f"   Filtros extraídos: {filters}")
        
        # Verificar resultados esperados
        if 'precio_min' in filters:
            print(f"   ✅ Precio mínimo: Q{filters['precio_min']:,.0f}")
        if 'precio_max' in filters:
            print(f"   ✅ Precio máximo: Q{filters['precio_max']:,.0f}")
        if 'precio_exacto' in filters:
            print(f"   ✅ Precio exacto: Q{filters['precio_exacto']:,.0f}")
        
        if not any(k in filters for k in ['precio_min', 'precio_max', 'precio_exacto']):
            print(f"   ❌ NO se detectó filtro de precio")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_price_ranges())

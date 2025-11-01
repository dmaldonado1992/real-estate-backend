import asyncio
from app.services.property_search_service import PropertySearchService
import json

async def test_filter_extraction():
    """Prueba solo la extracción de filtros"""
    
    service = PropertySearchService(None)
    
    # Cargar datos directamente del JSON
    with open('app/data/products.json', 'r', encoding='utf-8') as f:
        properties = json.load(f)
    
    test_queries = [
        "Entre 200 y 400 mil",
        "entre 300000 y 500000",
        "Busco casa entre 200 mil y 300 mil",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print(f"{'='*60}")
        
        # 1. Ver qué filtros se extraen
        query_lower = query.lower()
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', query)
        numbers = [float(n) for n in numbers]
        
        filters = service._extract_filters(query_lower, numbers)
        print(f"\n🔍 Filtros extraídos:")
        for key, value in filters.items():
            print(f"   {key}: {value}")
        
        # 2. Ver qué propiedades pasan el filtro
        filtered = service.filter_exact_matches(properties, query)
        print(f"\n✅ Propiedades que pasaron filtro: {len(filtered)}")
        
        for i, prop in enumerate(filtered[:5], 1):
            precio = prop.get('precio', 0)
            print(f"   {i}. {prop.get('titulo')} - Q{precio:,}")
        
        # 3. Verificar manualmente si el filtro debería funcionar
        if 'precio_min' in filters or 'precio_max' in filters:
            min_p = filters.get('precio_min', 0)
            max_p = filters.get('precio_max', float('inf'))
            
            should_match = [
                p for p in properties 
                if min_p <= p.get('precio', 0) <= max_p
            ]
            
            print(f"\n🎯 Propiedades que DEBERÍAN pasar (manual):")
            print(f"   Rango: Q{min_p:,} - Q{max_p:,}")
            print(f"   Total esperadas: {len(should_match)}")
            
            for i, prop in enumerate(should_match[:5], 1):
                precio = prop.get('precio', 0)
                print(f"   {i}. {prop.get('titulo')} - Q{precio:,}")

if __name__ == "__main__":
    asyncio.run(test_filter_extraction())

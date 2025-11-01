#!/usr/bin/env python3
"""
Debug de filtros de área
"""
import asyncio
from app.services.property_search_service import PropertySearchService
from app.services.ollama_client_service import OllamaClient
import re

async def debug_area_extraction():
    """Debug específico para extracción de filtros de área"""
    
    ollama_client = OllamaClient()
    search_service = PropertySearchService(ollama_client)
    
    query = "casa de 220 metros cuadrados"
    query_lower = query.lower()
    numbers = re.findall(r'\d+(?:\.\d+)?', query)
    numbers = [float(n) for n in numbers]
    
    print(f"Query original: '{query}'")
    print(f"Query lower: '{query_lower}'")
    print(f"Numbers encontrados: {numbers}")
    print()
    
    # Test manual del algoritmo
    for num in numbers:
        num_str = str(int(num)) if num == int(num) else str(num)
        num_index = query_lower.find(num_str)
        
        print(f"Procesando número: {num} (como string: '{num_str}')")
        print(f"Índice en query: {num_index}")
        
        if num_index != -1:
            start_context = max(0, num_index - 20)
            end_context = min(len(query_lower), num_index + len(num_str) + 20)
            context = query_lower[start_context:end_context]
            
            print(f"Contexto: '{context}'")
            
            # Check keywords
            area_keywords = ['metro', 'metros', 'm2', 'area', 'superficie', 'cuadrado', 'cuadrados']
            found_keywords = [kw for kw in area_keywords if kw in context]
            print(f"Keywords de área encontradas: {found_keywords}")
            
            if found_keywords and 20 <= num <= 2000:
                print(f"✅ Debería detectar área: {num}")
            else:
                print(f"❌ No detecta área")
    
    print()
    print("=== Extracción real ===")
    filters = search_service._extract_filters(query_lower, numbers)
    print(f"Filtros extraídos: {filters}")

if __name__ == "__main__":
    asyncio.run(debug_area_extraction())
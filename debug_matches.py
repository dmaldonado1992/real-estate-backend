#!/usr/bin/env python3
"""
Debug de coincidencias de filtros
"""
import asyncio
from app.services.property_search_service import PropertySearchService
from app.services.ollama_client_service import OllamaClient

async def debug_matches():
    """Debug específico para coincidencias de filtros"""
    
    ollama_client = OllamaClient()
    search_service = PropertySearchService(ollama_client)
    
    # Propiedad de prueba
    prop = {'id': 1, 'titulo': 'Casa A', 'area_m2': 220.0, 'tipo': 'casa', 'ubicacion': 'Zona 1'}
    
    # Filtros de prueba
    filters = {'tipo': 'casa', 'area_exacta': 220.0, 'area_tolerancia': 0.05}
    
    print(f"Propiedad: {prop}")
    print(f"Filtros: {filters}")
    print()
    
    # Test manual paso a paso
    print("=== Test paso a paso ===")
    
    # Tipo
    if 'tipo' in filters:
        prop_tipo = prop.get('tipo')
        filter_tipo = filters['tipo']
        tipo_match = prop_tipo == filter_tipo
        print(f"Tipo: prop='{prop_tipo}', filter='{filter_tipo}', match={tipo_match}")
    
    # Área
    if 'area_exacta' in filters:
        area = float(prop.get('area_m2', 0))
        target_area = filters['area_exacta']
        tolerance = filters.get('area_tolerancia', 0.05)
        min_area = target_area * (1 - tolerance)
        max_area = target_area * (1 + tolerance)
        area_match = min_area <= area <= max_area
        
        print(f"Área: prop={area}, target={target_area}, tolerance={tolerance}")
        print(f"Rango: {min_area} <= {area} <= {max_area}")
        print(f"Área match: {area_match}")
    
    # Test real
    result = search_service._matches_strict_filters(prop, filters)
    print(f"Resultado final: {result}")

if __name__ == "__main__":
    asyncio.run(debug_matches())
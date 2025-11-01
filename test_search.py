#!/usr/bin/env python3
"""
Script de prueba para validar la funcionalidad de búsqueda con IA.
Prueba los criterios: ubicación, precio, baños, habitaciones, área y fecha.
"""
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import LLMService
import json

async def test_search_queries():
    """Probar las consultas específicas solicitadas por el usuario."""
    
    # Crear servicio LLM
    llm_service = LLMService()
    
    # Queries de prueba
    test_queries = [
        "Busco casas de 3 habitaciones en zona 10",
        "Muéstrame departamentos de menos de $150,000", 
        "Propiedades con más de 2 baños y al menos 150 metros cuadrados",
        "Casas publicadas en los últimos 30 días",
        "Terrenos en venta con precio entre $50,000 y $100,000",
        "Departamentos con 2 habitaciones en zona 15"
    ]
    
    print("🔍 PRUEBAS DE BÚSQUEDA INTELIGENTE CON IA")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. CONSULTA: '{query}'")
        print("-" * 50)
        
        try:
            # Llamar al servicio (con cloud=False para evitar dependencias externas)
            result = await llm_service.search_ia_real_state(query, use_cloud=False)
            
            # Mostrar criterios detectados
            criteria = result.get('metadata', {}).get('criteria', {})
            print(f"📋 Criterios detectados: {json.dumps(criteria, ensure_ascii=False, indent=2)}")
            
            # Mostrar resultados
            properties = result.get('properties', [])
            print(f"🏠 Propiedades encontradas: {len(properties)}")
            
            if properties:
                for prop in properties[:3]:  # Mostrar solo las primeras 3
                    print(f"   - {prop.get('titulo', 'Sin título')} ({prop.get('tipo', 'N/A')})")
                    print(f"     💰 ${prop.get('precio', 0):,.0f} | 🛏️ {prop.get('habitaciones', 0)} hab | 🚿 {prop.get('banos', 0)} baños")
                    print(f"     📍 {prop.get('ubicacion', 'Sin ubicación')} | 📐 {prop.get('area_m2', 0)} m²")
                
                if len(properties) > 3:
                    print(f"   ... y {len(properties) - 3} propiedades más")
            
            # Mostrar análisis
            analysis = result.get('analysis', 'Sin análisis')
            print(f"💡 Análisis: {analysis}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")

if __name__ == "__main__":
    asyncio.run(test_search_queries())
#!/usr/bin/env python3
"""
Test para verificar que las características específicas tengan MÁS PRIORIDAD
que las coincidencias de tipo de propiedad.

Sistema de pesos:
- Tipo de propiedad: 5 puntos
- Características específicas: 8-15 puntos (MÁS que tipo)

Características específicas de alta prioridad:
- precio: $485,000
- habitaciones: 3  
- baños: 2.5
- área: 220 m²
- ubicación: "Eco Villa"
- fecha: 2025-10-29
"""

import sys
import os
import asyncio

# Agregar el directorio backend al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.llm_service import LLMService

async def test_priority_vs_type():
    """Test que valida que características específicas tengan más peso que tipo."""
    
    print("🧪 Probando PRIORIDAD de características específicas vs tipo...")
    print("=" * 70)
    
    llm_service = LLMService()
    
    # Test cases que deben priorizar características específicas sobre tipo
    test_cases = [
        {
            "query": "Busco casa de 3 habitaciones",
            "expected": "La propiedad con 3 habitaciones debe tener más prioridad, sin importar si hay más casas"
        },
        {
            "query": "Necesito propiedad con 2.5 baños",
            "expected": "Propiedad con 2.5 baños debe estar primero, independiente del tipo"
        },
        {
            "query": "Quiero algo en Eco Villa",
            "expected": "Eco Villa debe estar primero por ubicación específica"
        },
        {
            "query": "Busco departamento con precio de $485,000",
            "expected": "Precio específico debe tener más peso que solo 'departamento'"
        },
        {
            "query": "Casa con 220 metros cuadrados",
            "expected": "Área específica + casa debe ganar sobre solo casa"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        print(f"\n{i}. Testing: '{query}'")
        print("-" * 60)
        print(f"   📋 Expectativa: {test_case['expected']}")
        print("-" * 60)
        
        try:
            result = await llm_service.search_ia_real_state(query)
            
            if result['success']:
                print(f"   ✅ Success: {result['success']}")
                print(f"   📊 Total found: {result['total_found']}")
                
                # Mostrar los primeros 3 resultados con sus scores y razones
                properties = result['properties'][:3]
                
                if properties:
                    print(f"   🏆 Ranking de propiedades (ordenadas por prioridad):")
                    for j, prop in enumerate(properties, 1):
                        score = prop.get('_match_score', 0)
                        reasons = prop.get('_match_reasons', [])
                        
                        print(f"\n      {j}. {prop['titulo']} (Score: {score})")
                        print(f"         💰 ${prop['precio']:,.0f} | 🛏️ {prop['habitaciones']} hab | 🚿 {prop['banos']} baños")
                        print(f"         📐 {prop['area_m2']} m² | 📍 {prop['ubicacion']}")
                        print(f"         📅 {prop.get('fecha_publicacion', 'N/A')}")
                        
                        # Separar razones de prioridad vs otras razones
                        priority_reasons = [r for r in reasons if '🎯' in r]
                        other_reasons = [r for r in reasons if '🎯' not in r]
                        
                        if priority_reasons:
                            print(f"         🎯 PRIORIDADES: {', '.join(priority_reasons[:2])}")
                        if other_reasons:
                            print(f"         📝 Otras: {', '.join(other_reasons[:3])}")
                        
                        # Analizar si cumple con la expectativa
                        if j == 1:  # Primera propiedad
                            has_priority_characteristics = any('🎯' in r for r in reasons)
                            if has_priority_characteristics:
                                print(f"         ✅ CORRECTO: Tiene características de prioridad")
                            else:
                                print(f"         ⚠️  Solo coincidencias básicas (tipo, texto)")
                else:
                    print("   📋 No se encontraron propiedades")
                
            else:
                print(f"   ❌ Error: {result.get('analysis', 'Error desconocido')}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
        
        print("=" * 70)

    # Test adicional: comparar directamente
    print(f"\n🔍 TEST COMPARATIVO: ¿Qué tiene más prioridad?")
    print("=" * 70)
    
    comparative_test = "Busco casa de 3 habitaciones con 2.5 baños en Eco Villa por $485,000"
    print(f"Query completa: '{comparative_test}'")
    
    try:
        result = await llm_service.search_ia_real_state(comparative_test)
        if result['success'] and result['properties']:
            prop = result['properties'][0]  # La primera debe ser la que coincide todo
            score = prop.get('_match_score', 0)
            reasons = prop.get('_match_reasons', [])
            
            print(f"\n🏆 GANADORA: {prop['titulo']} (Score total: {score})")
            
            # Contar puntos por categoría
            priority_points = sum(6 if '🎯 MENCIÓN' in r else 
                                 15 if '🎯 UBICACIÓN' in r else
                                 12 if '🎯 PRECIO' in r else
                                 10 if '🎯 HABITACIONES' in r or '🎯 BAÑOS' in r or '🎯 ÁREA' in r else
                                 8 if '🎯 FECHA' in r else 0 
                                 for r in reasons if '🎯' in r)
            
            type_points = sum(5 for r in reasons if 'tipo exacto:' in r)
            other_points = score - priority_points - type_points
            
            print(f"   🎯 Puntos por PRIORIDADES específicas: {priority_points}")
            print(f"   🏠 Puntos por TIPO de propiedad: {type_points}")
            print(f"   📝 Otros puntos (texto, ubicación): {other_points}")
            print(f"   📊 TOTAL: {score}")
            
            if priority_points > type_points:
                print(f"   ✅ CORRECTO: Prioridades específicas ({priority_points}) > Tipo ({type_points})")
            else:
                print(f"   ❌ ERROR: Tipo ({type_points}) >= Prioridades ({priority_points})")
                
    except Exception as e:
        print(f"   💥 Error en test comparativo: {str(e)}")

if __name__ == "__main__":
    # Ejecutar test
    asyncio.run(test_priority_vs_type())
    print("\n🎉 Test de prioridad vs tipo completado!")
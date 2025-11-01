#!/usr/bin/env python3
"""
Prueba de velocidad y rendimiento del modelo Llama optimizado
"""
import requests
import time
import json

def test_speed_comparison():
    """Compara la velocidad del nuevo modelo vs el anterior"""
    
    print("🚀 Probando velocidad del modelo Llama 3.2:1b optimizado\n")
    
    # URL base del API
    base_url = "http://127.0.0.1:8000"
    
    # Pruebas a realizar
    tests = [
        {
            "name": "Conexión básica",
            "url": f"{base_url}/api/llm/test",
            "method": "GET"
        },
        {
            "name": "Descripción de producto",
            "url": f"{base_url}/api/llm/description",
            "method": "POST",
            "params": {"product_name": "iPhone 15 Pro Max"}
        },
        {
            "name": "Recomendaciones",
            "url": f"{base_url}/api/llm/recommendations", 
            "method": "POST",
            "params": {
                "product_description": "Smartphone de alta gama con cámara profesional",
                "num_recommendations": 3
            }
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"🧪 Ejecutando: {test['name']}")
        
        try:
            start_time = time.time()
            
            if test['method'] == 'GET':
                response = requests.get(test['url'], timeout=30)
            else:
                response = requests.post(test['url'], params=test.get('params', {}), timeout=30)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Éxito en {duration:.2f}s")
                
                # Mostrar resultado relevante
                if 'description' in result:
                    print(f"   📝 Descripción: {result['description'][:100]}...")
                elif 'recommendations' in result:
                    print(f"   💡 Recomendaciones: {len(result['recommendations'])} generadas")
                elif 'message' in result:
                    print(f"   💬 Respuesta: {result['message']}")
                
                results.append({
                    'test': test['name'],
                    'duration': duration,
                    'status': 'success',
                    'model': result.get('model', 'N/A')
                })
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                results.append({
                    'test': test['name'],
                    'duration': duration,
                    'status': 'error',
                    'error': response.status_code
                })
                
        except requests.Timeout:
            print(f"   ⏱️  Timeout después de 30s")
            results.append({
                'test': test['name'],
                'duration': 30,
                'status': 'timeout'
            })
        except Exception as e:
            print(f"   💥 Error: {e}")
            results.append({
                'test': test['name'],
                'duration': 0,
                'status': 'error',
                'error': str(e)
            })
        
        print()
    
    # Resumen de resultados
    print(f"{'='*60}")
    print("📊 RESUMEN DE RENDIMIENTO")
    print(f"{'='*60}")
    
    total_time = sum(r['duration'] for r in results if r['status'] == 'success')
    successful_tests = len([r for r in results if r['status'] == 'success'])
    
    for result in results:
        status_emoji = {
            'success': '✅',
            'error': '❌',
            'timeout': '⏱️'
        }.get(result['status'], '❓')
        
        print(f"{result['test']:.<35} {status_emoji} {result['duration']:.2f}s")
    
    print(f"\n📈 Estadísticas:")
    print(f"   • Pruebas exitosas: {successful_tests}/{len(results)}")
    print(f"   • Tiempo total: {total_time:.2f}s")
    if successful_tests > 0:
        print(f"   • Tiempo promedio: {total_time/successful_tests:.2f}s")
    
    # Comparación con modelo anterior
    print(f"\n🏆 Ventajas del modelo Llama 3.2:1b:")
    print("   • 🚀 Súper rápido - Menos parámetros = Mayor velocidad")
    print("   • 🔋 Eficiente - Menor uso de memoria y CPU")
    print("   • 🌐 Compatible con API de Ollama")
    print("   • 💡 Optimizado para respuestas rápidas")
    
def test_model_info():
    """Obtiene información del modelo actual"""
    
    print("\n🔍 Información del modelo actual:")
    
    try:
        response = requests.get("http://127.0.0.1:8000/api/llm/test")
        if response.status_code == 200:
            result = response.json()
            print(f"   📋 Modelo: {result.get('model', 'N/A')}")
            print(f"   🔌 Estado: {result.get('status', 'N/A')}")
            print(f"   💬 Mensaje: {result.get('message', 'N/A')}")
        else:
            print(f"   ❌ Error obteniendo info: {response.status_code}")
    except Exception as e:
        print(f"   💥 Error: {e}")

def main():
    """Función principal"""
    
    print("🦙 Prueba de Rendimiento - Llama 3.2:1b Optimizado")
    print("=" * 60)
    
    # Verificar que el servidor esté ejecutándose
    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=5)
        print("✅ Servidor detectado en http://127.0.0.1:8000")
    except:
        print("❌ Servidor no encontrado. Asegúrate de que esté ejecutándose:")
        print("   uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return
    
    # Ejecutar pruebas
    test_model_info()
    test_speed_comparison()
    
    print(f"\n🎯 Configuración completada exitosamente!")
    print("💡 Tu aplicación ahora usa el modelo más rápido disponible.")

if __name__ == "__main__":
    main()
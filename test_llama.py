#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de Llama
"""
import asyncio
import requests
import json

def test_llama_connection():
    """Prueba la conexión con el API de Llama"""
    try:
        response = requests.get("http://127.0.0.1:8000/api/llm/test")
        print("=== Prueba de Conexión con Llama ===")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error al conectar con el API: {e}")
        return False

def test_product_description():
    """Prueba la generación de descripción de producto"""
    try:
        data = {"product_name": "Smartphone Samsung Galaxy"}
        response = requests.post(
            "http://127.0.0.1:8000/api/llm/description",
            params=data
        )
        print("\n=== Prueba de Descripción de Producto ===")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Producto: {result.get('product_name')}")
            print(f"Descripción: {result.get('description')}")
            print(f"Modelo: {result.get('model')}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error al generar descripción: {e}")
        return False

def test_recommendations():
    """Prueba la generación de recomendaciones"""
    try:
        data = {
            "product_description": "Smartphone con cámara de alta resolución",
            "num_recommendations": 3
        }
        response = requests.post(
            "http://127.0.0.1:8000/api/llm/recommendations",
            params=data
        )
        print("\n=== Prueba de Recomendaciones ===")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Producto base: {result.get('base_product')}")
            print(f"Modelo: {result.get('model')}")
            print("Recomendaciones:")
            for i, rec in enumerate(result.get('recommendations', []), 1):
                print(f"  {i}. {rec}")
        else:
            print(f"Error: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error al generar recomendaciones: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🦙 Probando configuración de Llama 3.2\n")
    
    # Verificar que el servidor esté ejecutándose
    try:
        requests.get("http://127.0.0.1:8000/docs", timeout=5)
        print("✅ Servidor FastAPI está ejecutándose")
    except:
        print("❌ El servidor FastAPI no está ejecutándose en el puerto 8000")
        print("   Por favor ejecuta: uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return
    
    # Ejecutar pruebas
    tests = [
        ("Conexión con Llama", test_llama_connection),
        ("Descripción de producto", test_product_description),
        ("Recomendaciones", test_recommendations)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Ejecutando: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: EXITOSO")
            else:
                print(f"❌ {test_name}: FALLIDO")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Resumen
    print(f"\n{'='*50}")
    print("📊 RESUMEN DE PRUEBAS")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nTotal: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! Llama está configurado correctamente.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa la configuración.")

if __name__ == "__main__":
    main()
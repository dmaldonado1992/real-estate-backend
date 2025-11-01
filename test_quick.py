#!/usr/bin/env python3
"""
Prueba rápida: verifica Ollama local y el backend.
No se buscan ni usan API keys de proveedores externos.
"""
import requests


def test_local_ollama():
    print("🏠 Probando Ollama local...")
    try:
        r = requests.get("http://127.0.0.1:11434/api/version", timeout=5)
        if r.status_code == 200:
            info = r.json()
            print(f"   ✅ Ollama local responde - {info}")
            return True
        print(f"   ❌ Ollama respondió con status {r.status_code}")
        return False
    except requests.RequestException:
        print("   ❌ No se pudo conectar a Ollama local en http://127.0.0.1:11434")
        return False


def test_backend():
    print("\n🖥️ Probando backend FastAPI...")
    try:
        r = requests.get("http://127.0.0.1:8000/docs", timeout=5)
        if r.status_code == 200:
            print("   ✅ Backend responde en /docs")
            return True
        print(f"   ❌ Backend respondió con status {r.status_code}")
        return False
    except requests.RequestException:
        print("   ❌ No se pudo conectar al backend en http://127.0.0.1:8000")
        return False


def main():
    print("🧪 Prueba rápida de configuración (solo local)")
    results = [
        ("Ollama local", test_local_ollama()),
        ("Backend", test_backend()),
    ]

    print("\n📊 Resumen:")
    for name, ok in results:
        print(f" - {name}: {'OK' if ok else 'FALLÓ'}")

    ok_count = sum(1 for _, ok in results if ok)
    if ok_count == len(results):
        print("\n🎉 Todo listo: Ollama y backend funcionan localmente.")
    else:
        print("\n⚠️  Revisa los servicios que fallaron arriba.")


if __name__ == '__main__':
    main()
import re

# Nuevo pattern que soporta multiplicadores individuales Y acentos
# Importante: usar \b para word boundary al final
pattern_new = r'entre\s+(\d+(?:\.\d+)?)\s*(mil(?:es|lones)?|mill[oó]n(?:es)?|k|m)?\s+y\s+(\d+(?:\.\d+)?)\s*(mil(?:es|lones)?|mill[oó]n(?:es)?|k|m)?'

print("="*60)
print("Probando NUEVO pattern (soporta multiplicadores individuales):")
print("="*60)

test_queries = [
    "Entre 200 y 400 mil",
    "entre 300000 y 500000",
    "Busco casa entre 200 mil y 300 mil",
    "entre 200 mil y 300 mil",
    "casa entre 200 y 300 mil",
    "Entre 1 millón y 2 millones",
]

for test in test_queries:
    match = re.search(pattern_new, test.lower())
    if match:
        num1 = float(match.group(1))
        mult1 = match.group(2)
        num2 = float(match.group(3))
        mult2 = match.group(4)
        
        # Si solo el segundo número tiene multiplicador, aplicarlo a ambos
        if mult2 and not mult1:
            mult1 = mult2
        
        # Aplicar multiplicadores
        if mult1 and mult1 in ['mil', 'k']:
            num1 *= 1000
        elif mult1 and 'mill' in mult1:  # millón, millon, millones
            num1 *= 1000000
            
        if mult2 and mult2 in ['mil', 'k']:
            num2 *= 1000
        elif mult2 and 'mill' in mult2:  # millón, millon, millones
            num2 *= 1000000
        
        print(f"✅ {test:45}")
        print(f"   Match: '{match.group(0)}'")
        print(f"   Num1: {match.group(1)} x {mult1 or '1'} = {num1:,.0f}")
        print(f"   Num2: {match.group(3)} x {mult2 or '1'} = {num2:,.0f}")
        print(f"   → Rango: Q{num1:,.0f} - Q{num2:,.0f}")
        print()
    else:
        print(f"❌ {test:45} → No match")
        print()

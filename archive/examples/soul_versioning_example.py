
"""
Przykład systemu wersjonowania Soul - niezmienność i ewolucja.
"""

import asyncio
from luxdb.models.soul import Soul

def calculate_area(length: float, width: float) -> float:
    """Oblicza pole prostokąta"""
    return length * width

def calculate_volume(length: float, width: float, height: float) -> float:
    """Oblicza objętość prostopadłościanu"""
    return length * width * height

def calculate_perimeter(length: float, width: float) -> float:
    """Oblicza obwód prostokąta"""
    return 2 * (length + width)

async def demo_soul_versioning():
    print("🧬 Demonstracja systemu wersjonowania Soul")
    print("=" * 50)
    
    # 1. Utwórz pierwszą wersję Soul
    print("\n📦 Tworzenie Soul v1.0.0 - podstawowe operacje geometryczne")
    soul_v1 = await Soul.create_function_soul(
        name="calculate_area",
        func=calculate_area,
        description="Oblicza pole prostokąta",
        alias="geometry_calculator",
        version="1.0.0"
    )
    
    print(f"✅ Utworzono: {soul_v1}")
    print(f"   Hash: {soul_v1.soul_hash}")
    print(f"   Wersja: {soul_v1.get_version()}")
    
    # 2. Ewolucja - dodaj nową funkcję
    print("\n🔄 Ewolucja Soul - dodawanie funkcji objętości")
    soul_v2 = await Soul.create_evolved_version(
        original_soul=soul_v1,
        changes={
            "functions.calculate_volume": {
                "py_type": "function",
                "description": "Oblicza objętość prostopadłościanu",
                "is_primary": False
            }
        },
        new_version="1.1.0"
    )
    
    # Załaduj nową funkcję
    soul_v2._register_immutable_function("calculate_volume", calculate_volume)
    
    print(f"✅ Utworzono: {soul_v2}")
    print(f"   Hash: {soul_v2.soul_hash}")
    print(f"   Wersja: {soul_v2.get_version()}")
    print(f"   Rodzic: {soul_v2.get_parent_hash()[:8]}...")
    
    # 3. Kolejna ewolucja - major version
    print("\n🚀 Major ewolucja Soul - przeprojektowanie interfejsu")
    soul_v3 = await Soul.create_evolved_version(
        original_soul=soul_v2,
        changes={
            "genesis.interface_version": "2.0",
            "functions.calculate_perimeter": {
                "py_type": "function", 
                "description": "Oblicza obwód prostokąta",
                "is_primary": False
            },
            "attributes.calculation_units": {
                "py_type": "str",
                "default": "meters"
            }
        },
        new_version="2.0.0"
    )
    
    soul_v3._register_immutable_function("calculate_perimeter", calculate_perimeter)
    
    print(f"✅ Utworzono: {soul_v3}")
    print(f"   Hash: {soul_v3.soul_hash}")
    print(f"   Wersja: {soul_v3.get_version()}")
    
    # 4. Testuj kompatybilność
    print("\n🔗 Testowanie kompatybilności wersji")
    print(f"v1.0.0 kompatybilna z v1.1.0: {soul_v1.is_compatible_with(soul_v2)}")
    print(f"v1.1.0 kompatybilna z v2.0.0: {soul_v2.is_compatible_with(soul_v3)}")
    print(f"v2.0.0 jest ewolucją v1.1.0: {soul_v3.is_evolution_of(soul_v2)}")
    
    # 5. Pokaż linię ewolucji
    print("\n📈 Linia ewolucji Soul v2.0.0:")
    lineage = await soul_v3.get_lineage()
    for i, soul in enumerate(lineage):
        indent = "  " * i
        print(f"{indent}├─ {soul.get_version()} (hash: {soul.soul_hash[:8]}...)")
    
    # 6. Testuj wykonywanie funkcji w różnych wersjach
    print("\n⚡ Testowanie wykonywania funkcji")
    
    # v1 - tylko area
    result_v1 = await soul_v1.execute_function("calculate_area", 5.0, 3.0)
    print(f"Soul v1.0.0 - pole: {result_v1['data']['result']}")
    
    # v2 - area + volume  
    result_v2_area = await soul_v2.execute_function("calculate_area", 5.0, 3.0)
    result_v2_volume = await soul_v2.execute_function("calculate_volume", 5.0, 3.0, 2.0)
    print(f"Soul v1.1.0 - pole: {result_v2_area['data']['result']}")
    print(f"Soul v1.1.0 - objętość: {result_v2_volume['data']['result']}")
    
    # v3 - wszystkie funkcje
    result_v3_perimeter = await soul_v3.execute_function("calculate_perimeter", 5.0, 3.0)
    print(f"Soul v2.0.0 - obwód: {result_v3_perimeter['data']['result']}")
    
    print("\n✨ Demonstracja zakończona!")
    print("\n📝 Kluczowe zasady:")
    print("  • Każda Soul jest niezmieniona po utworzeniu")
    print("  • Zmiany wymagają nowej wersji z nowym hashem")
    print("  • System śledzi linię ewolucji")
    print("  • Kompatybilność wersji jest kontrolowana")
    print("  • Funkcje są definiowane w genotypie, nie dodawane dynamicznie")

if __name__ == "__main__":
    asyncio.run(demo_soul_versioning())

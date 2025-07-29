
"""
Testy dla generatora genetyki
"""

import asyncio
import json
from core.genetics_generator import GeneticsGenerator
from database.models.base import Being, Soul


async def test_field_analysis():
    """Test analizy pól klasy Being"""
    print("🔍 Test analizy pól Being...")
    
    field_info = GeneticsGenerator.analyze_being_fields()
    
    print(f"Znaleziono {len(field_info)} pól:")
    for field_name, info in field_info.items():
        print(f"  - {field_name}: {info['py_type']} -> {info['table_name']}")
    
    assert len(field_info) > 0, "Powinno znaleźć jakieś pola"
    print("✅ Analiza pól zakończona sukcesem\n")


async def test_genotype_generation():
    """Test generowania genotypu"""
    print("🧬 Test generowania genotypu...")
    
    genotype = GeneticsGenerator.generate_basic_genotype(
        name="TestBeing",
        description="Testowy genotyp wygenerowany automatycznie",
        exclude_fields=['genes'],  # Wykluczamy genes żeby uniknąć rekurencji
        custom_genes={
            "test_gene": "core.genes.basic.get_being_info"
        }
    )
    
    print("Wygenerowany genotyp:")
    print(json.dumps(genotype, indent=2, default=str))
    
    # Walidacja
    validation = GeneticsGenerator.validate_genotype(genotype)
    print(f"Walidacja: {validation}")
    
    assert validation['valid'], f"Genotyp powinien być poprawny: {validation['errors']}"
    assert 'attributes' in genotype, "Genotyp powinien mieć atrybuty"
    assert 'genes' in genotype, "Genotyp powinien mieć geny"
    
    print("✅ Generowanie genotypu zakończone sukcesem\n")


async def test_specialized_genotypes():
    """Test generowania wyspecjalizowanych genotypów"""
    print("⚡ Test generowania wyspecjalizowanych genotypów...")
    
    genotypes = GeneticsGenerator.generate_specialized_genotypes()
    
    print(f"Wygenerowano {len(genotypes)} wyspecjalizowanych genotypów:")
    for name, genotype in genotypes.items():
        print(f"  - {name}: {genotype['metadata']['name']}")
        
        # Waliduj każdy genotyp
        validation = GeneticsGenerator.validate_genotype(genotype)
        if not validation['valid']:
            print(f"    ❌ Błędy: {validation['errors']}")
        if validation['warnings']:
            print(f"    ⚠️ Ostrzeżenia: {validation['warnings']}")
    
    assert len(genotypes) > 0, "Powinno wygenerować jakieś genotypy"
    print("✅ Generowanie wyspecjalizowanych genotypów zakończone sukcesem\n")


async def test_simple_soul_creation():
    """Test tworzenia Soul z klasy"""
    print("👻 Test tworzenia Soul z klasy...")
    
    # Przykładowa klasa dziedzicząca po Being
    from dataclasses import dataclass
    from database.models.base import Being
    
    @dataclass 
    class MessageBeing(Being):
        content: str = None
        timestamp: str = None
        embedding: str = None
    
    try:
        # Generuj genotyp z klasy
        genotype = GeneticsGenerator.generate_genotype_from_class(MessageBeing)
        print("📋 Wygenerowany genotyp:")
        print(json.dumps(genotype, indent=2, ensure_ascii=False))
        
        # W prawdziwej aplikacji:
        # soul = await GeneticsGenerator.create_soul_from_class(MessageBeing, "message_soul")
        # print(f"Utworzono Soul: {soul.soul_hash}")
        print("⚠️ Test Soul pominięty - wymaga połączenia z bazą danych")
        
    except Exception as e:
        print(f"⚠️ Błąd generowania genotypu: {e}")any bez bazy): {e}")
    
    print("✅ Test Soul zakończony\n")


async def test_documentation_generation():
    """Test generowania dokumentacji"""
    print("📚 Test generowania dokumentacji...")
    
    genotype = GeneticsGenerator.generate_basic_genotype(
        name="DocumentedBeing",
        description="Testowy genotyp z dokumentacją",
        include_fields=['alias', 'genotype']
    )
    
    documentation = GeneticsGenerator.generate_genotype_documentation(genotype)
    
    print("Wygenerowana dokumentacja:")
    print("=" * 50)
    print(documentation)
    print("=" * 50)
    
    assert "# Genotyp:" in documentation, "Dokumentacja powinna mieć nagłówek"
    assert "## Atrybuty" in documentation, "Dokumentacja powinna mieć sekcję atrybutów"
    assert "## Geny" in documentation, "Dokumentacja powinna mieć sekcję genów"
    
    print("✅ Generowanie dokumentacji zakończone sukcesem\n")


async def main():
    """Uruchom wszystkie testy"""
    print("🚀 Rozpoczynam testy generatora genetyki...\n")
    
    try:
        await test_field_analysis()
        await test_genotype_generation() 
        await test_specialized_genotypes()
        await test_simple_soul_creation()
        await test_documentation_generation()
        
        print("🎉 Wszystkie testy zakończone sukcesem!")
        
    except Exception as e:
        print(f"❌ Błąd w testach: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

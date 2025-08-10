
"""
LuxDB Soul Unit Tests
====================

Szczegółowe testy jednostkowe dla klasy Soul i operacji genotypów.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from luxdb.models.soul import Soul
from luxdb.utils.validators import validate_genotype
from database.postgre_db import Postgre_db


class TestSoulOperations:
    """Testy jednostkowe dla operacji Soul"""
    
    @pytest.fixture
    async def sample_genotype(self):
        """Przykładowy genotyp do testów"""
        return {
            "genesis": {
                "name": "test_entity",
                "type": "unit_test",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            },
            "attributes": {
                "name": {"py_type": "str", "max_length": 100, "required": True},
                "count": {"py_type": "int", "min_value": 0, "default": 0},
                "active": {"py_type": "bool", "default": True},
                "metadata": {"py_type": "dict", "default": {}},
                "tags": {"py_type": "List[str]", "default": []},
                "score": {"py_type": "float", "min_value": 0.0, "max_value": 10.0}
            },
            "constraints": {
                "unique_fields": ["name"],
                "required_fields": ["name"]
            }
        }
    
    @pytest.fixture
    async def invalid_genotype(self):
        """Nieprawidłowy genotyp do testów walidacji"""
        return {
            "genesis": {
                "name": "",  # Pusty name
                "type": "invalid"
                # Brak version
            },
            "attributes": {
                "invalid_field": {"py_type": "unknown_type"}
            }
        }
    
    async def test_genotype_validation_success(self, sample_genotype):
        """Test poprawnej walidacji genotypu"""
        is_valid, errors = validate_genotype(sample_genotype)
        
        assert is_valid is True
        assert len(errors) == 0
    
    async def test_genotype_validation_failure(self, invalid_genotype):
        """Test niepoprawnej walidacji genotypu"""
        is_valid, errors = validate_genotype(invalid_genotype)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in error for error in errors)
    
    async def test_soul_creation(self, sample_genotype):
        """Test tworzenia Soul"""
        soul = await Soul.create(sample_genotype, alias="test_soul_unit")
        
        assert soul is not None
        assert soul.soul_hash is not None
        assert len(soul.soul_hash) == 64  # SHA256 hex
        assert soul.alias == "test_soul_unit"
        assert soul.genotype == sample_genotype
    
    async def test_soul_creation_without_alias(self, sample_genotype):
        """Test tworzenia Soul bez aliasu"""
        soul = await Soul.create(sample_genotype)
        
        assert soul is not None
        assert soul.soul_hash is not None
        assert soul.alias is None
    
    async def test_soul_loading_by_hash(self, sample_genotype):
        """Test ładowania Soul po hash"""
        # Utwórz Soul
        original_soul = await Soul.create(sample_genotype, alias="test_load_hash")
        
        # Załaduj po hash
        loaded_soul = await Soul.get(original_soul.soul_hash)
        
        assert loaded_soul is not None
        assert loaded_soul.soul_hash == original_soul.soul_hash
        assert loaded_soul.alias == original_soul.alias
        assert loaded_soul.genotype == original_soul.genotype
    
    async def test_soul_loading_by_alias(self, sample_genotype):
        """Test ładowania Soul po alias"""
        # Utwórz Soul
        original_soul = await Soul.create(sample_genotype, alias="test_load_alias")
        
        # Załaduj po alias
        loaded_soul = await Soul.load_by_alias("test_load_alias")
        
        assert loaded_soul is not None
        assert loaded_soul.soul_hash == original_soul.soul_hash
        assert loaded_soul.alias == "test_load_alias"
    
    async def test_soul_hash_consistency(self, sample_genotype):
        """Test spójności hash dla identycznych genotypów"""
        soul1 = await Soul.create(sample_genotype, alias="test_hash_1")
        soul2 = await Soul.create(sample_genotype, alias="test_hash_2")
        
        # Te same genotypy powinny mieć ten sam hash
        assert soul1.soul_hash == soul2.soul_hash
    
    async def test_soul_hash_difference(self, sample_genotype):
        """Test różnic hash dla różnych genotypów"""
        # Zmodyfikuj genotyp
        modified_genotype = sample_genotype.copy()
        modified_genotype["genesis"]["version"] = "2.0.0"
        
        soul1 = await Soul.create(sample_genotype, alias="test_diff_1")
        soul2 = await Soul.create(modified_genotype, alias="test_diff_2")
        
        # Różne genotypy powinny mieć różne hash
        assert soul1.soul_hash != soul2.soul_hash
    
    async def test_soul_serialization(self, sample_genotype):
        """Test serializacji Soul"""
        soul = await Soul.create(sample_genotype, alias="test_serialization")
        
        # Test to_dict
        soul_dict = soul.to_dict()
        
        assert "soul_hash" in soul_dict
        assert "alias" in soul_dict
        assert "genotype" in soul_dict
        assert soul_dict["soul_hash"] == soul.soul_hash
        assert soul_dict["alias"] == soul.alias
    
    async def test_soul_load_all(self, sample_genotype):
        """Test ładowania wszystkich Soul"""
        # Utwórz kilka Soul
        souls_created = []
        for i in range(3):
            soul = await Soul.create(sample_genotype, alias=f"test_load_all_{i}")
            souls_created.append(soul)
        
        # Załaduj wszystkie
        all_souls = await Soul.load_all()
        
        # Sprawdź czy nasze Soul są w wynikach
        created_hashes = {s.soul_hash for s in souls_created}
        loaded_hashes = {s.soul_hash for s in all_souls}
        
        assert created_hashes.issubset(loaded_hashes)
    
    async def test_soul_genotype_evolution(self, sample_genotype):
        """Test ewolucji genotypu"""
        # Wersja 1.0.0
        v1_soul = await Soul.create(sample_genotype, alias="test_evolution_v1")
        
        # Wersja 2.0.0 - dodane pole
        v2_genotype = sample_genotype.copy()
        v2_genotype["genesis"]["version"] = "2.0.0"
        v2_genotype["attributes"]["description"] = {
            "py_type": "str", 
            "default": "No description"
        }
        
        v2_soul = await Soul.create(v2_genotype, alias="test_evolution_v2")
        
        # Sprawdź że to różne Soul
        assert v1_soul.soul_hash != v2_soul.soul_hash
        assert v1_soul.genotype["genesis"]["version"] == "1.0.0"
        assert v2_soul.genotype["genesis"]["version"] == "2.0.0"
    
    async def test_soul_attribute_types_validation(self):
        """Test walidacji typów atrybutów"""
        test_cases = [
            {"py_type": "str", "valid": True},
            {"py_type": "int", "valid": True},
            {"py_type": "float", "valid": True},
            {"py_type": "bool", "valid": True},
            {"py_type": "dict", "valid": True},
            {"py_type": "List[str]", "valid": True},
            {"py_type": "List[int]", "valid": True},
            {"py_type": "unknown_type", "valid": False}
        ]
        
        for case in test_cases:
            genotype = {
                "genesis": {
                    "name": "test_types",
                    "type": "validation_test",
                    "version": "1.0.0"
                },
                "attributes": {
                    "test_field": case
                }
            }
            
            is_valid, errors = validate_genotype(genotype)
            
            if case["valid"]:
                assert is_valid, f"Type {case['py_type']} should be valid"
            else:
                assert not is_valid, f"Type {case['py_type']} should be invalid"
    
    async def test_soul_constraints_validation(self, sample_genotype):
        """Test walidacji ograniczeń"""
        # Dodaj ograniczenia
        genotype_with_constraints = sample_genotype.copy()
        genotype_with_constraints["constraints"] = {
            "unique_fields": ["name", "email"],
            "required_fields": ["name"],
            "max_instances": 100
        }
        
        is_valid, errors = validate_genotype(genotype_with_constraints)
        assert is_valid is True
    
    async def test_soul_cleanup(self):
        """Cleanup testowych danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                # Usuń testowe Soul
                await conn.execute("""
                    DELETE FROM souls 
                    WHERE alias LIKE 'test_%' 
                    OR genotype->>'genesis'->>'type' = 'unit_test'
                """)
        except Exception as e:
            print(f"Cleanup warning: {e}")


# Uruchomienie testów
async def run_soul_tests():
    """Uruchom testy Soul"""
    test_instance = TestSoulOperations()
    
    print("🧠 Uruchamianie testów jednostkowych Soul...")
    
    # Sample genotype fixture
    sample_genotype = await test_instance.sample_genotype()
    invalid_genotype = await test_instance.invalid_genotype()
    
    tests = [
        ("Walidacja genotypu - poprawna", test_instance.test_genotype_validation_success(sample_genotype)),
        ("Walidacja genotypu - niepoprawna", test_instance.test_genotype_validation_failure(invalid_genotype)),
        ("Tworzenie Soul", test_instance.test_soul_creation(sample_genotype)),
        ("Tworzenie Soul bez aliasu", test_instance.test_soul_creation_without_alias(sample_genotype)),
        ("Ładowanie Soul po hash", test_instance.test_soul_loading_by_hash(sample_genotype)),
        ("Ładowanie Soul po alias", test_instance.test_soul_loading_by_alias(sample_genotype)),
        ("Spójność hash", test_instance.test_soul_hash_consistency(sample_genotype)),
        ("Różnice hash", test_instance.test_soul_hash_difference(sample_genotype)),
        ("Serializacja Soul", test_instance.test_soul_serialization(sample_genotype)),
        ("Ładowanie wszystkich Soul", test_instance.test_soul_load_all(sample_genotype)),
        ("Ewolucja genotypu", test_instance.test_soul_genotype_evolution(sample_genotype)),
        ("Walidacja typów atrybutów", test_instance.test_soul_attribute_types_validation()),
        ("Walidacja ograniczeń", test_instance.test_soul_constraints_validation(sample_genotype))
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_coro in tests:
        try:
            await test_coro
            print(f"  ✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            failed += 1
    
    # Cleanup
    await test_instance.test_soul_cleanup()
    
    print(f"\n📊 Wyniki testów Soul: {passed} ✅ | {failed} ❌")
    return passed, failed


if __name__ == "__main__":
    asyncio.run(run_soul_tests())

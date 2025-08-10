
"""
LuxDB Being Unit Tests
=====================

Szczegółowe testy jednostkowe dla klasy Being i operacji bytów.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from luxdb.models.soul import Soul
from luxdb.models.being import Being
from database.postgre_db import Postgre_db


class TestBeingOperations:
    """Testy jednostkowe dla operacji Being"""
    
    @pytest.fixture
    async def test_soul(self):
        """Soul testowy do tworzenia Being"""
        genotype = {
            "genesis": {
                "name": "test_being_entity",
                "type": "unit_test_being",
                "version": "1.0.0"
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "count": {"py_type": "int", "default": 0},
                "active": {"py_type": "bool", "default": True},
                "metadata": {"py_type": "dict", "default": {}},
                "tags": {"py_type": "List[str]", "default": []},
                "score": {"py_type": "float", "default": 0.0}
            }
        }
        
        return await Soul.create(genotype, alias="test_being_soul")
    
    @pytest.fixture
    async def sample_being_data(self):
        """Przykładowe dane Being"""
        return {
            "name": "Test Being",
            "count": 42,
            "active": True,
            "metadata": {
                "test": True,
                "created_at": datetime.now().isoformat(),
                "category": "unit_test"
            },
            "tags": ["test", "unit", "being"],
            "score": 8.5
        }
    
    async def test_being_creation(self, test_soul, sample_being_data):
        """Test tworzenia Being"""
        being = await Being.create(test_soul, sample_being_data)
        
        assert being is not None
        assert being.ulid is not None
        assert len(being.ulid) == 26  # ULID length
        assert being.soul_hash == test_soul.soul_hash
        assert being.created_at is not None
    
    async def test_being_creation_with_validation(self, test_soul):
        """Test tworzenia Being z walidacją danych"""
        # Poprawne dane
        valid_data = {
            "name": "Valid Being",
            "count": 10,
            "active": True
        }
        
        being = await Being.create(test_soul, valid_data)
        assert being is not None
        
        # Niepoprawne dane - brak wymaganego pola 'name'
        invalid_data = {
            "count": 10,
            "active": True
        }
        
        try:
            await Being.create(test_soul, invalid_data)
            assert False, "Should raise validation error"
        except Exception as e:
            assert "name" in str(e).lower()
    
    async def test_being_loading_by_ulid(self, test_soul, sample_being_data):
        """Test ładowania Being po ULID"""
        # Utwórz Being
        original_being = await Being.create(test_soul, sample_being_data)
        
        # Załaduj po ULID
        loaded_being = await Being.load_by_ulid(original_being.ulid)
        
        assert loaded_being is not None
        assert loaded_being.ulid == original_being.ulid
        assert loaded_being.soul_hash == original_being.soul_hash
    
    async def test_being_attribute_access(self, test_soul, sample_being_data):
        """Test dostępu do atrybutów Being"""
        being = await Being.create(test_soul, sample_being_data)
        
        # Test get_attributes
        attributes = await being.get_attributes()
        
        assert attributes["name"] == sample_being_data["name"]
        assert attributes["count"] == sample_being_data["count"]
        assert attributes["active"] == sample_being_data["active"]
        assert attributes["metadata"] == sample_being_data["metadata"]
    
    async def test_being_attribute_update(self, test_soul, sample_being_data):
        """Test aktualizacji atrybutów Being"""
        being = await Being.create(test_soul, sample_being_data)
        
        # Aktualizuj pojedynczy atrybut
        await being.update_attribute("count", 100)
        
        # Sprawdź aktualizację
        updated_attributes = await being.get_attributes()
        assert updated_attributes["count"] == 100
        
        # Inne atrybuty powinny pozostać niezmienione
        assert updated_attributes["name"] == sample_being_data["name"]
        assert updated_attributes["active"] == sample_being_data["active"]
    
    async def test_being_multiple_attributes_update(self, test_soul, sample_being_data):
        """Test aktualizacji wielu atrybutów Being"""
        being = await Being.create(test_soul, sample_being_data)
        
        # Aktualizuj wiele atrybutów
        updates = {
            "count": 200,
            "active": False,
            "score": 9.5
        }
        
        for attr, value in updates.items():
            await being.update_attribute(attr, value)
        
        # Sprawdź aktualizacje
        updated_attributes = await being.get_attributes()
        
        for attr, expected_value in updates.items():
            assert updated_attributes[attr] == expected_value
    
    async def test_being_complex_attribute_update(self, test_soul, sample_being_data):
        """Test aktualizacji złożonych atrybutów (dict, list)"""
        being = await Being.create(test_soul, sample_being_data)
        
        # Aktualizuj dict
        new_metadata = {
            "test": False,
            "updated_at": datetime.now().isoformat(),
            "version": 2,
            "settings": {"theme": "dark", "lang": "pl"}
        }
        await being.update_attribute("metadata", new_metadata)
        
        # Aktualizuj list
        new_tags = ["updated", "test", "complex"]
        await being.update_attribute("tags", new_tags)
        
        # Sprawdź aktualizacje
        attributes = await being.get_attributes()
        assert attributes["metadata"] == new_metadata
        assert attributes["tags"] == new_tags
    
    async def test_being_load_all(self, test_soul, sample_being_data):
        """Test ładowania wszystkich Being"""
        # Utwórz kilka Being
        beings_created = []
        for i in range(3):
            data = sample_being_data.copy()
            data["name"] = f"Test Being {i}"
            data["count"] = i * 10
            
            being = await Being.create(test_soul, data)
            beings_created.append(being)
        
        # Załaduj wszystkie Being
        all_beings = await Being.load_all()
        
        # Sprawdź czy nasze Being są w wynikach
        created_ulids = {b.ulid for b in beings_created}
        loaded_ulids = {b.ulid for b in all_beings}
        
        assert created_ulids.issubset(loaded_ulids)
    
    async def test_being_load_by_soul(self, test_soul, sample_being_data):
        """Test ładowania Being po Soul"""
        # Utwórz Being z tym Soul
        being1 = await Being.create(test_soul, sample_being_data)
        
        data2 = sample_being_data.copy()
        data2["name"] = "Second Being"
        being2 = await Being.create(test_soul, data2)
        
        # Załaduj Being tego Soul
        soul_beings = await Being.load_by_soul(test_soul.soul_hash)
        
        # Powinniśmy znaleźć nasze Being
        soul_ulids = {b.ulid for b in soul_beings}
        assert being1.ulid in soul_ulids
        assert being2.ulid in soul_ulids
    
    async def test_being_deletion(self, test_soul, sample_being_data):
        """Test usuwania Being"""
        being = await Being.create(test_soul, sample_being_data)
        original_ulid = being.ulid
        
        # Usuń Being
        await being.delete()
        
        # Sprawdź czy Being został usunięty
        deleted_being = await Being.load_by_ulid(original_ulid)
        assert deleted_being is None
    
    async def test_being_serialization(self, test_soul, sample_being_data):
        """Test serializacji Being"""
        being = await Being.create(test_soul, sample_being_data)
        
        # Test to_dict
        being_dict = being.to_dict()
        
        assert "ulid" in being_dict
        assert "soul_hash" in being_dict
        assert "created_at" in being_dict
        assert "attributes" in being_dict
        
        assert being_dict["ulid"] == being.ulid
        assert being_dict["soul_hash"] == being.soul_hash
    
    async def test_being_timestamps(self, test_soul, sample_being_data):
        """Test znaczników czasu Being"""
        start_time = datetime.now()
        
        being = await Being.create(test_soul, sample_being_data)
        
        end_time = datetime.now()
        
        # created_at powinno być między start_time a end_time
        assert start_time <= being.created_at <= end_time
        
        # updated_at powinno być ustawione przy aktualizacji
        await being.update_attribute("count", 999)
        
        # Odśwież Being z bazy
        refreshed_being = await Being.load_by_ulid(being.ulid)
        
        assert refreshed_being.updated_at is not None
        assert refreshed_being.updated_at >= being.created_at
    
    async def test_being_bulk_operations(self, test_soul):
        """Test operacji masowych na Being"""
        # Utwórz wiele Being
        beings = []
        for i in range(10):
            data = {
                "name": f"Bulk Being {i}",
                "count": i,
                "active": i % 2 == 0,
                "metadata": {"bulk": True, "index": i}
            }
            being = await Being.create(test_soul, data)
            beings.append(being)
        
        assert len(beings) == 10
        
        # Test masowej aktualizacji (symulacja)
        for being in beings:
            await being.update_attribute("count", 1000)
        
        # Sprawdź aktualizacje
        for being in beings:
            refreshed = await Being.load_by_ulid(being.ulid)
            attrs = await refreshed.get_attributes()
            assert attrs["count"] == 1000
    
    async def test_being_data_types_handling(self, test_soul):
        """Test obsługi różnych typów danych"""
        test_data = {
            "name": "Type Test Being",
            "count": 42,
            "active": True,
            "metadata": {
                "string": "text",
                "number": 123,
                "boolean": False,
                "list": [1, 2, 3],
                "nested": {"key": "value"}
            },
            "tags": ["string1", "string2"],
            "score": 7.5
        }
        
        being = await Being.create(test_soul, test_data)
        attributes = await being.get_attributes()
        
        # Sprawdź typy danych
        assert isinstance(attributes["name"], str)
        assert isinstance(attributes["count"], int)
        assert isinstance(attributes["active"], bool)
        assert isinstance(attributes["metadata"], dict)
        assert isinstance(attributes["tags"], list)
        assert isinstance(attributes["score"], float)
        
        # Sprawdź zagnieżdżone struktury
        assert attributes["metadata"]["nested"]["key"] == "value"
        assert attributes["tags"][0] == "string1"
    
    async def test_being_cleanup(self):
        """Cleanup testowych danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                # Usuń testowe Being i Soul
                await conn.execute("""
                    DELETE FROM beings 
                    WHERE soul_hash IN (
                        SELECT soul_hash FROM souls 
                        WHERE alias = 'test_being_soul' 
                        OR genotype->>'genesis'->>'type' = 'unit_test_being'
                    )
                """)
                await conn.execute("""
                    DELETE FROM souls 
                    WHERE alias = 'test_being_soul' 
                    OR genotype->>'genesis'->>'type' = 'unit_test_being'
                """)
        except Exception as e:
            print(f"Cleanup warning: {e}")


# Uruchomienie testów
async def run_being_tests():
    """Uruchom testy Being"""
    test_instance = TestBeingOperations()
    
    print("🤖 Uruchamianie testów jednostkowych Being...")
    
    # Przygotuj fixtures
    test_soul = await test_instance.test_soul()
    sample_being_data = await test_instance.sample_being_data()
    
    tests = [
        ("Tworzenie Being", test_instance.test_being_creation(test_soul, sample_being_data)),
        ("Tworzenie Being z walidacją", test_instance.test_being_creation_with_validation(test_soul)),
        ("Ładowanie Being po ULID", test_instance.test_being_loading_by_ulid(test_soul, sample_being_data)),
        ("Dostęp do atrybutów", test_instance.test_being_attribute_access(test_soul, sample_being_data)),
        ("Aktualizacja atrybutów", test_instance.test_being_attribute_update(test_soul, sample_being_data)),
        ("Aktualizacja wielu atrybutów", test_instance.test_being_multiple_attributes_update(test_soul, sample_being_data)),
        ("Aktualizacja złożonych atrybutów", test_instance.test_being_complex_attribute_update(test_soul, sample_being_data)),
        ("Ładowanie wszystkich Being", test_instance.test_being_load_all(test_soul, sample_being_data)),
        ("Ładowanie Being po Soul", test_instance.test_being_load_by_soul(test_soul, sample_being_data)),
        ("Usuwanie Being", test_instance.test_being_deletion(test_soul, sample_being_data)),
        ("Serializacja Being", test_instance.test_being_serialization(test_soul, sample_being_data)),
        ("Znaczniki czasu", test_instance.test_being_timestamps(test_soul, sample_being_data)),
        ("Operacje masowe", test_instance.test_being_bulk_operations(test_soul)),
        ("Obsługa typów danych", test_instance.test_being_data_types_handling(test_soul))
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
    await test_instance.test_being_cleanup()
    
    print(f"\n📊 Wyniki testów Being: {passed} ✅ | {failed} ❌")
    return passed, failed


if __name__ == "__main__":
    asyncio.run(run_being_tests())

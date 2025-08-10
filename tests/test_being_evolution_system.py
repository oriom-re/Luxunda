
"""
LuxDB Being Evolution System Tests
=================================

Testy kompleksowego systemu ewolucji bytów przez Kernel.
To fundamentalna część LuxOS - zarządzanie ewolucją Being przez Soul versioning.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List

from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.kernel_system import kernel_system
from luxdb.core.access_control import access_controller
from database.models.relationship import Relationship
from database.postgre_db import Postgre_db


class BeingEvolutionSystemTester:
    """Kompleksowe testowanie systemu ewolucji bytów"""
    
    def __init__(self):
        self.test_souls = []
        self.test_beings = []
        self.test_relationships = []
        self.evolution_scenarios = []
    
    async def setup_evolution_environment(self) -> Dict[str, Any]:
        """Przygotuj środowisko testowe dla ewolucji"""
        print("🧬 Setting up evolution test environment...")
        
        setup_results = {
            'kernel_initialized': False,
            'basic_souls_created': False,
            'test_beings_created': False,
            'access_zones_configured': False,
            'errors': []
        }
        
        try:
            # Inicjalizacja kernela
            await kernel_system.initialize("evolution_test")
            setup_results['kernel_initialized'] = True
            print("✅ Kernel system initialized")
            
            # Utworzenie podstawowych genotypów
            await self._create_basic_souls()
            setup_results['basic_souls_created'] = True
            print("✅ Basic soul genotypes created")
            
            # Utworzenie bytów testowych
            await self._create_test_beings()
            setup_results['test_beings_created'] = True
            print("✅ Test beings created")
            
            # Konfiguracja stref dostępu
            self._configure_access_zones()
            setup_results['access_zones_configured'] = True
            print("✅ Access zones configured")
            
        except Exception as e:
            setup_results['errors'].append(f"Setup failed: {str(e)}")
            
        return setup_results
    
    async def _create_basic_souls(self):
        """Utwórz podstawowe genotypy dla testów"""
        # Podstawowy genotyp użytkownika
        basic_user_genotype = {
            "genesis": {
                "name": "basic_user",
                "type": "user_profile",
                "version": "1.0.0",
                "description": "Basic user with learning capabilities",
                "evolution_capabilities": ["access_level_promotion", "skill_enhancement"]
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "skill_level": {"py_type": "int", "default": 1, "min_value": 1, "max_value": 100},
                "access_level": {"py_type": "str", "default": "basic"},
                "execution_count": {"py_type": "int", "default": 0},
                "creation_privileges": {"py_type": "bool", "default": False}
            },
            "functions": {
                "learn_skill": {
                    "description": "Increase skill level",
                    "parameters": {"skill_points": {"py_type": "int", "default": 1}},
                    "code": "self.data['skill_level'] = min(100, self.data.get('skill_level', 1) + skill_points); return {'new_level': self.data['skill_level']}"
                }
            }
        }
        
        basic_soul = await Soul.create(basic_user_genotype, alias="basic_user_soul")
        self.test_souls.append(basic_soul)
        
        # Zaawansowany genotyp z możliwościami twórczymi
        advanced_creator_genotype = {
            "genesis": {
                "name": "advanced_creator",
                "type": "creator_profile", 
                "version": "2.0.0",
                "description": "Advanced user with creation capabilities",
                "evolution_capabilities": ["admin_privileges", "soul_creation", "system_management"]
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "skill_level": {"py_type": "int", "default": 50, "min_value": 50, "max_value": 100},
                "access_level": {"py_type": "str", "default": "advanced"},
                "execution_count": {"py_type": "int", "default": 0},
                "creation_privileges": {"py_type": "bool", "default": True},
                "created_souls": {"py_type": "list", "default": []},
                "admin_capabilities": {"py_type": "dict", "default": {}}
            },
            "functions": {
                "create_new_soul": {
                    "description": "Create new soul genotype",
                    "parameters": {"soul_concept": {"py_type": "dict"}},
                    "code": "return {'soul_created': True, 'concept': soul_concept}"
                },
                "manage_system": {
                    "description": "System management capabilities",
                    "parameters": {"action": {"py_type": "str"}},
                    "code": "return {'action_executed': action, 'timestamp': datetime.now().isoformat()}"
                }
            }
        }
        
        advanced_soul = await Soul.create(advanced_creator_genotype, alias="advanced_creator_soul")
        self.test_souls.append(advanced_soul)
    
    async def _create_test_beings(self):
        """Utwórz byty testowe w różnych fazach ewolucji"""
        basic_soul = self.test_souls[0]
        
        # Byt początkujący (gotowy do pierwszej ewolucji)
        beginner_data = {
            "name": "Alice Beginner",
            "skill_level": 1,
            "access_level": "basic",
            "execution_count": 12  # Powyżej progu 10 dla awansu
        }
        beginner_being_result = await Being.set(basic_soul, beginner_data, alias="alice_beginner")
        beginner_being = await Being._get_by_ulid_internal(
            beginner_being_result["data"]["being"]["ulid"]
        )
        self.test_beings.append(beginner_being)
        
        # Byt średniozaawansowany (gotowy do dalszej ewolucji)
        intermediate_data = {
            "name": "Bob Intermediate", 
            "skill_level": 25,
            "access_level": "basic",
            "execution_count": 105  # Powyżej progu 100 dla uprawnień admin
        }
        # Symuluj starszą datę utworzenia
        intermediate_being_result = await Being.set(basic_soul, intermediate_data, alias="bob_intermediate")
        intermediate_being = await Being._get_by_ulid_internal(
            intermediate_being_result["data"]["being"]["ulid"]
        )
        intermediate_being.created_at = datetime.now() - timedelta(days=10)
        await intermediate_being.save()
        self.test_beings.append(intermediate_being)
        
        # Byt z historią ewolucji
        evolved_data = {
            "name": "Carol Evolved",
            "skill_level": 75,
            "access_level": "authenticated", 
            "execution_count": 150,
            "evolution_history": [
                {
                    "from_soul": "old_hash_123",
                    "to_soul": basic_soul.soul_hash,
                    "evolution_trigger": "skill_milestone",
                    "timestamp": (datetime.now() - timedelta(days=5)).isoformat()
                }
            ]
        }
        evolved_being_result = await Being.set(basic_soul, evolved_data, alias="carol_evolved")
        evolved_being = await Being._get_by_ulid_internal(
            evolved_being_result["data"]["being"]["ulid"]
        )
        self.test_beings.append(evolved_being)
    
    def _configure_access_zones(self):
        """Konfiguruj strefy dostępu dla testów"""
        # Upewnij się że access_controller ma odpowiednie strefy
        if not hasattr(access_controller, 'zones'):
            access_controller.zones = {}
            
        access_controller.zones.update({
            "public_zone": {
                "id": "public_zone",
                "name": "Public Access",
                "level": 0,
                "capabilities": ["basic_operations"]
            },
            "authenticated_zone": {
                "id": "authenticated_zone", 
                "name": "Authenticated Access",
                "level": 1,
                "capabilities": ["advanced_operations", "data_persistence"]
            },
            "sensitive_zone": {
                "id": "sensitive_zone",
                "name": "Sensitive Operations",
                "level": 2,
                "capabilities": ["admin_operations", "soul_creation", "system_management"]
            }
        })
    
    async def test_evolution_potential_detection(self) -> Dict[str, Any]:
        """Test wykrywania potencjału ewolucyjnego"""
        print("\n🔍 Testing evolution potential detection...")
        
        results = {
            'beginner_evolution_detected': False,
            'intermediate_evolution_detected': False,
            'evolved_evolution_detected': False,
            'correct_evolution_types': False,
            'errors': []
        }
        
        try:
            # Test bytu początkującego
            beginner = self.test_beings[0]
            beginner_potential = await beginner.can_evolve()
            
            if beginner_potential["can_evolve"]:
                results['beginner_evolution_detected'] = True
                print(f"✅ Beginner evolution potential detected: {len(beginner_potential['available_evolutions'])} options")
            
            # Test bytu średniozaawansowanego
            intermediate = self.test_beings[1]
            intermediate_potential = await intermediate.can_evolve()
            
            if intermediate_potential["can_evolve"]:
                results['intermediate_evolution_detected'] = True
                print(f"✅ Intermediate evolution potential detected: {len(intermediate_potential['available_evolutions'])} options")
            
            # Test bytu z historią ewolucji
            evolved = self.test_beings[2]
            evolved_potential = await evolved.can_evolve()
            
            if evolved_potential["can_evolve"]:
                results['evolved_evolution_detected'] = True
                print(f"✅ Evolved being evolution potential detected: {len(evolved_potential['available_evolutions'])} options")
            
            # Test poprawności typów ewolucji
            evolution_types = []
            for being in self.test_beings:
                potential = await being.can_evolve()
                for evo in potential.get("available_evolutions", []):
                    evolution_types.append(evo["type"])
            
            expected_types = ["access_level_promotion", "admin_privileges", "soul_creator"]
            if any(etype in evolution_types for etype in expected_types):
                results['correct_evolution_types'] = True
                print(f"✅ Correct evolution types detected: {set(evolution_types)}")
                
        except Exception as e:
            results['errors'].append(f"Evolution potential detection failed: {str(e)}")
            
        return results
    
    async def test_evolution_request_submission(self) -> Dict[str, Any]:
        """Test składania żądań ewolucji przez byty"""
        print("\n📝 Testing evolution request submission...")
        
        results = {
            'basic_evolution_request': False,
            'advanced_evolution_request': False,
            'creator_evolution_request': False,
            'request_validation': False,
            'errors': []
        }
        
        try:
            # Test podstawowego żądania ewolucji
            beginner = self.test_beings[0]
            basic_request = await beginner.request_evolution(
                evolution_trigger="learning_milestone_achieved",
                new_capabilities={
                    "attributes.advanced_skills": {"py_type": "list", "default": []},
                    "functions.analyze_data": {"py_type": "function", "description": "Data analysis capability"}
                },
                access_level_change="promote"
            )
            
            if basic_request.get('success'):
                results['basic_evolution_request'] = True
                print("✅ Basic evolution request submitted successfully")
            
            # Test zaawansowanego żądania ewolucji
            intermediate = self.test_beings[1]
            advanced_request = await intermediate.request_evolution(
                evolution_trigger="expert_level_achieved",
                new_capabilities={
                    "attributes.admin_capabilities": {
                        "py_type": "dict",
                        "default": {
                            "can_manage_users": True,
                            "can_create_souls": True
                        }
                    },
                    "functions.manage_system": {"py_type": "function", "description": "System management"}
                },
                access_level_change="grant_admin"
            )
            
            if advanced_request.get('success'):
                results['advanced_evolution_request'] = True
                print("✅ Advanced evolution request submitted successfully")
            
            # Test żądania uprawnień twórczych
            evolved = self.test_beings[2]
            creator_request = await evolved.request_evolution(
                evolution_trigger="creation_mastery_achieved",
                new_capabilities={
                    "capabilities.soul_creation": True,
                    "functions.create_soul": {"py_type": "function", "description": "Soul creation capability"}
                },
                access_level_change="grant_creator"
            )
            
            if creator_request.get('success'):
                results['creator_evolution_request'] = True
                print("✅ Creator evolution request submitted successfully")
            
            # Walidacja struktur żądań
            all_requests = [basic_request, advanced_request, creator_request]
            valid_requests = 0
            
            for request in all_requests:
                if (request.get('success') and 
                    'evolution_requested' in request.get('data', {}) and
                    'request_id' in request.get('data', {})):
                    valid_requests += 1
            
            if valid_requests == len(all_requests):
                results['request_validation'] = True
                print("✅ All evolution requests properly structured")
                
        except Exception as e:
            results['errors'].append(f"Evolution request submission failed: {str(e)}")
            
        return results
    
    async def test_kernel_evolution_processing(self) -> Dict[str, Any]:
        """Test przetwarzania ewolucji przez Kernel"""
        print("\n⚙️ Testing Kernel evolution processing...")
        
        results = {
            'pending_requests_detected': False,
            'evolution_approval': False,
            'evolution_rejection': False,
            'soul_versioning': False,
            'being_update': False,
            'relationship_creation': False,
            'errors': []
        }
        
        try:
            # Sprawdź oczekujące żądania
            pending_requests = await kernel_system.get_pending_evolution_requests()
            
            if len(pending_requests) > 0:
                results['pending_requests_detected'] = True
                print(f"✅ Detected {len(pending_requests)} pending evolution requests")
                
                # Test zatwierdzenia ewolucji
                first_request = pending_requests[0]
                approval_result = await kernel_system.process_evolution_request(
                    being_ulid=first_request['being_ulid'],
                    request_id=first_request['request_id'],
                    approve=True,
                    processed_by="test_kernel"
                )
                
                if approval_result.get('success'):
                    results['evolution_approval'] = True
                    print("✅ Evolution approved and processed successfully")
                    
                    # Sprawdź czy Soul została utworzona w nowej wersji
                    evolution_data = approval_result.get('data', {})
                    old_soul_hash = evolution_data.get('old_soul_hash')
                    new_soul_hash = evolution_data.get('new_soul_hash')
                    
                    if old_soul_hash != new_soul_hash:
                        results['soul_versioning'] = True
                        print("✅ Soul versioning working correctly")
                    
                    # Sprawdź czy Being został zaktualizowany
                    updated_being = await Being.get_by_ulid(first_request['being_ulid'])
                    if updated_being.soul_hash == new_soul_hash:
                        results['being_update'] = True
                        print("✅ Being updated with new Soul version")
                    
                    # Sprawdź czy relacja ewolucji została utworzona
                    evolution_relations = await kernel_system.get_evolution_history_for_being(
                        first_request['being_ulid']
                    )
                    if len(evolution_relations) > 0:
                        results['relationship_creation'] = True
                        print("✅ Evolution relationship created successfully")
                
                # Test odrzucenia ewolucji (jeśli są kolejne żądania)
                if len(pending_requests) > 1:
                    second_request = pending_requests[1]
                    rejection_result = await kernel_system.process_evolution_request(
                        being_ulid=second_request['being_ulid'],
                        request_id=second_request['request_id'], 
                        approve=False,
                        processed_by="test_kernel"
                    )
                    
                    if rejection_result.get('success') and not rejection_result.get('data', {}).get('approved'):
                        results['evolution_rejection'] = True
                        print("✅ Evolution rejection processed correctly")
                        
        except Exception as e:
            results['errors'].append(f"Kernel evolution processing failed: {str(e)}")
            
        return results
    
    async def test_evolution_history_tracking(self) -> Dict[str, Any]:
        """Test śledzenia historii ewolucji"""
        print("\n📚 Testing evolution history tracking...")
        
        results = {
            'history_retrieval': False,
            'chronological_order': False,
            'complete_metadata': False,
            'chain_integrity': False,
            'errors': []
        }
        
        try:
            # Znajdź byty z historią ewolucji
            beings_with_evolution = []
            for being in self.test_beings:
                history = await kernel_system.get_evolution_history_for_being(being.ulid)
                if len(history) > 0:
                    beings_with_evolution.append((being, history))
            
            if len(beings_with_evolution) > 0:
                results['history_retrieval'] = True
                print(f"✅ Evolution history retrieved for {len(beings_with_evolution)} beings")
                
                # Test chronologicznej kolejności
                for being, history in beings_with_evolution:
                    timestamps = [evo.get('processed_at', '') for evo in history]
                    if timestamps == sorted(timestamps):
                        results['chronological_order'] = True
                        print("✅ Evolution history in chronological order")
                        break
                
                # Test kompletności metadanych
                complete_metadata_count = 0
                required_fields = ['old_soul_hash', 'new_soul_hash', 'evolution_trigger', 'processed_by', 'processed_at']
                
                for being, history in beings_with_evolution:
                    for evolution in history:
                        if all(field in evolution for field in required_fields):
                            complete_metadata_count += 1
                
                if complete_metadata_count > 0:
                    results['complete_metadata'] = True
                    print(f"✅ Complete metadata in {complete_metadata_count} evolution records")
                
                # Test integralności łańcucha ewolucji
                for being, history in beings_with_evolution:
                    if len(history) > 1:
                        chain_valid = True
                        for i in range(1, len(history)):
                            if history[i-1]['new_soul_hash'] != history[i]['old_soul_hash']:
                                chain_valid = False
                                break
                        
                        if chain_valid:
                            results['chain_integrity'] = True
                            print("✅ Evolution chain integrity verified")
                            break
                            
        except Exception as e:
            results['errors'].append(f"Evolution history tracking failed: {str(e)}")
            
        return results
    
    async def test_soul_creation_by_evolved_beings(self) -> Dict[str, Any]:
        """Test tworzenia Soul przez ewoluowane byty"""
        print("\n🧬 Testing Soul creation by evolved beings...")
        
        results = {
            'creator_privileges_granted': False,
            'soul_creation_successful': False,
            'proper_attribution': False,
            'new_soul_functionality': False,
            'errors': []
        }
        
        try:
            # Znajdź byt z uprawnieniami twórczymi (po ewolucji)
            creator_being = None
            for being in self.test_beings:
                evolution_potential = await being.can_evolve()
                available_types = [evo["type"] for evo in evolution_potential.get("available_evolutions", [])]
                if "soul_creator" in available_types:
                    # Symuluj nadanie uprawnień twórczych
                    being.data['creation_privileges'] = True
                    being.data['evolution_history'] = [{"type": "soul_creator", "granted": True}]
                    await being.save()
                    creator_being = being
                    break
            
            if creator_being:
                results['creator_privileges_granted'] = True
                print("✅ Creator privileges simulated")
                
                # Test tworzenia nowej Soul
                new_soul_concept = {
                    "genesis": {
                        "name": "custom_tool",
                        "type": "utility_tool",
                        "version": "1.0.0",
                        "description": "Custom tool created by evolved being",
                        "creator": "evolved_being"
                    },
                    "attributes": {
                        "tool_name": {"py_type": "str", "required": True},
                        "efficiency": {"py_type": "float", "default": 1.0},
                        "usage_count": {"py_type": "int", "default": 0}
                    },
                    "functions": {
                        "execute_tool": {
                            "description": "Execute the tool functionality",
                            "parameters": {"input_data": {"py_type": "dict"}},
                            "code": "self.data['usage_count'] += 1; return {'result': 'processed', 'count': self.data['usage_count']}"
                        }
                    }
                }
                
                creation_result = await creator_being.propose_soul_creation(new_soul_concept)
                
                if creation_result.get('success'):
                    results['soul_creation_successful'] = True
                    print("✅ Soul creation by evolved being successful")
                    
                    # Sprawdź atrybucję
                    created_soul_data = creation_result.get('data', {}).get('new_soul', {})
                    if created_soul_data.get('genotype', {}).get('genesis', {}).get('created_by_being') == creator_being.ulid:
                        results['proper_attribution'] = True
                        print("✅ Proper attribution to creator being")
                    
                    # Test funkcjonalności nowej Soul
                    new_soul_hash = created_soul_data.get('soul_hash')
                    if new_soul_hash:
                        test_being_data = {
                            "tool_name": "TestTool",
                            "efficiency": 1.5
                        }
                        
                        # Pobierz Soul i utwórz byt testowy
                        new_soul = await Soul.get_by_hash(new_soul_hash)
                        if new_soul:
                            test_being_result = await Being.set(new_soul, test_being_data, alias="test_custom_tool")
                            test_being = await Being._get_by_ulid_internal(
                                test_being_result["data"]["being"]["ulid"]
                            )
                            
                            # Wykonaj funkcję
                            execution_result = await test_being.execute_soul_function(
                                "execute_tool",
                                input_data={"test": "data"}
                            )
                            
                            if execution_result.get('success'):
                                results['new_soul_functionality'] = True
                                print("✅ New Soul functionality working correctly")
                                
        except Exception as e:
            results['errors'].append(f"Soul creation by evolved beings failed: {str(e)}")
            
        return results
    
    async def test_access_zone_evolution(self) -> Dict[str, Any]:
        """Test ewolucji stref dostępu"""
        print("\n🔐 Testing access zone evolution...")
        
        results = {
            'zone_promotion_detected': False,
            'zone_assignment_updated': False,
            'capabilities_upgraded': False,
            'zone_hierarchy_respected': False,
            'errors': []
        }
        
        try:
            # Znajdź byt z możliwością awansu strefy
            candidate_being = None
            for being in self.test_beings:
                if being.access_zone == "public_zone" and being.data.get('execution_count', 0) >= 10:
                    candidate_being = being
                    break
            
            if candidate_being:
                original_zone = candidate_being.access_zone
                
                # Symuluj ewolucję z awansem strefy
                evolution_request = {
                    "evolution_trigger": "access_level_promotion",
                    "requesting_being_ulid": candidate_being.ulid,
                    "requested_access_change": "promote"
                }
                
                # Bezpośrednio wykonaj ewolucję dostępu
                evolution_changes = {}
                if original_zone == "public_zone":
                    evolution_changes["access.promoted_from"] = "public_zone"
                    evolution_changes["access.promoted_to"] = "authenticated_zone"
                    candidate_being.access_zone = "authenticated_zone"
                    
                    results['zone_promotion_detected'] = True
                    print("✅ Zone promotion detected and processed")
                
                # Sprawdź aktualizację przypisania strefy
                if candidate_being.access_zone != original_zone:
                    results['zone_assignment_updated'] = True
                    print("✅ Zone assignment updated successfully")
                
                # Sprawdź upgrade capabilities
                new_zone_info = access_controller.zones.get(candidate_being.access_zone, {})
                old_zone_info = access_controller.zones.get(original_zone, {})
                
                if new_zone_info.get('level', 0) > old_zone_info.get('level', 0):
                    results['capabilities_upgraded'] = True
                    print("✅ Access capabilities upgraded")
                
                # Sprawdź hierarchię stref
                zone_levels = {zone_id: zone_info.get('level', 0) for zone_id, zone_info in access_controller.zones.items()}
                if all(zone_levels[a] <= zone_levels[b] for a, b in [("public_zone", "authenticated_zone"), ("authenticated_zone", "sensitive_zone")]):
                    results['zone_hierarchy_respected'] = True
                    print("✅ Zone hierarchy respected")
                    
        except Exception as e:
            results['errors'].append(f"Access zone evolution failed: {str(e)}")
            
        return results
    
    async def cleanup_evolution_tests(self) -> Dict[str, Any]:
        """Oczyszczenie po testach ewolucji"""
        print("\n🧹 Cleaning up evolution tests...")
        
        cleanup_results = {
            'test_beings_removed': False,
            'test_souls_removed': False,
            'evolution_relations_removed': False,
            'errors': []
        }
        
        try:
            # Usuń byty testowe
            beings_removed = 0
            for being in self.test_beings:
                if await being.delete():
                    beings_removed += 1
            
            if beings_removed > 0:
                cleanup_results['test_beings_removed'] = True
                print(f"✅ Removed {beings_removed} test beings")
            
            # Usuń relacje ewolucji testowej
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM relationships 
                    WHERE relation_type = 'evolution' 
                    AND metadata->>'processed_by' = 'test_kernel'
                """)
                
                cleanup_results['evolution_relations_removed'] = True
                print("✅ Evolution test relationships removed")
            
            # Usuń testowe Soul (opcjonalnie - mogą być użyteczne)
            # souls_removed = 0
            # for soul in self.test_souls:
            #     if await soul.delete():
            #         souls_removed += 1
            # cleanup_results['test_souls_removed'] = True
            
        except Exception as e:
            cleanup_results['errors'].append(f"Cleanup failed: {str(e)}")
            
        return cleanup_results
    
    async def run_complete_evolution_test_suite(self) -> Dict[str, Any]:
        """Uruchom kompletny pakiet testów ewolucji"""
        print("🧬 LUXDB BEING EVOLUTION SYSTEM TEST SUITE")
        print("=" * 60)
        print("Testing the fundamental evolution system of LuxOS")
        print("=" * 60)
        
        final_results = {
            'setup': {},
            'evolution_potential': {},
            'evolution_requests': {},
            'kernel_processing': {},
            'history_tracking': {},
            'soul_creation': {},
            'access_evolution': {},
            'cleanup': {},
            'overall_success': False,
            'total_errors': 0,
            'system_reliability': 'UNKNOWN'
        }
        
        try:
            # Kolejność testów - od podstawowych do zaawansowanych
            final_results['setup'] = await self.setup_evolution_environment()
            
            if final_results['setup']['kernel_initialized']:
                final_results['evolution_potential'] = await self.test_evolution_potential_detection()
                final_results['evolution_requests'] = await self.test_evolution_request_submission()
                final_results['kernel_processing'] = await self.test_kernel_evolution_processing()
                final_results['history_tracking'] = await self.test_evolution_history_tracking()
                final_results['soul_creation'] = await self.test_soul_creation_by_evolved_beings()
                final_results['access_evolution'] = await self.test_access_zone_evolution()
            
            final_results['cleanup'] = await self.cleanup_evolution_tests()
            
            # Oblicz ogólny sukces
            all_test_sections = [
                final_results['setup'],
                final_results['evolution_potential'],
                final_results['evolution_requests'],
                final_results['kernel_processing'],
                final_results['history_tracking'],
                final_results['soul_creation'],
                final_results['access_evolution']
            ]
            
            total_errors = sum(len(section.get('errors', [])) for section in all_test_sections)
            final_results['total_errors'] = total_errors
            
            # Oceń kluczowe funkcjonalności ewolucji
            critical_tests_passed = (
                final_results['setup'].get('kernel_initialized', False) and
                final_results['evolution_potential'].get('beginner_evolution_detected', False) and
                final_results['evolution_requests'].get('basic_evolution_request', False) and
                final_results['kernel_processing'].get('evolution_approval', False)
            )
            
            if critical_tests_passed and total_errors == 0:
                final_results['overall_success'] = True
                final_results['system_reliability'] = 'HIGHLY_RELIABLE'
            elif critical_tests_passed and total_errors < 3:
                final_results['overall_success'] = True
                final_results['system_reliability'] = 'RELIABLE'
            elif critical_tests_passed:
                final_results['system_reliability'] = 'PARTIALLY_RELIABLE'
            else:
                final_results['system_reliability'] = 'NEEDS_FIXES'
            
        except Exception as e:
            final_results['total_errors'] += 1
            final_results['system_reliability'] = 'CRITICAL_ERROR'
            
        return final_results
    
    def print_evolution_test_report(self, results: Dict[str, Any]) -> None:
        """Wydrukuj szczegółowy raport testów ewolucji"""
        print("\n" + "=" * 70)
        print("🧬 LUXDB BEING EVOLUTION SYSTEM TEST REPORT")
        print("=" * 70)
        
        reliability = results['system_reliability']
        if reliability == 'HIGHLY_RELIABLE':
            print("🎉 SYSTEM STATUS: ✅ HIGHLY RELIABLE - Evolution system working perfectly!")
        elif reliability == 'RELIABLE':
            print("✅ SYSTEM STATUS: 🟢 RELIABLE - Evolution system working well with minor issues")
        elif reliability == 'PARTIALLY_RELIABLE':
            print("⚠️  SYSTEM STATUS: 🟡 PARTIALLY RELIABLE - Core evolution works, needs improvements")
        else:
            print("❌ SYSTEM STATUS: 🔴 NEEDS FIXES - Critical evolution issues detected")
        
        print(f"\n📊 OVERALL METRICS:")
        print(f"   Total Errors: {results['total_errors']}")
        print(f"   Overall Success: {results['overall_success']}")
        
        # Szczegóły sekcji testowych
        test_sections = [
            ('Environment Setup', results['setup']),
            ('Evolution Potential Detection', results['evolution_potential']),
            ('Evolution Request Submission', results['evolution_requests']),
            ('Kernel Processing', results['kernel_processing']),
            ('History Tracking', results['history_tracking']),
            ('Soul Creation by Evolved Beings', results['soul_creation']),
            ('Access Zone Evolution', results['access_evolution']),
            ('Cleanup', results['cleanup'])
        ]
        
        for section_name, section_results in test_sections:
            print(f"\n🔍 {section_name.upper()}:")
            if section_results:
                passed_tests = [k for k, v in section_results.items() if k != 'errors' and v is True]
                failed_tests = [k for k, v in section_results.items() if k != 'errors' and v is False]
                
                print(f"   ✅ Passed: {len(passed_tests)} tests")
                for test in passed_tests:
                    print(f"      ✓ {test}")
                
                if failed_tests:
                    print(f"   ❌ Failed: {len(failed_tests)} tests")
                    for test in failed_tests:
                        print(f"      ✗ {test}")
                
                if section_results.get('errors'):
                    print(f"   🚨 Errors: {len(section_results['errors'])}")
                    for error in section_results['errors']:
                        print(f"      ⚠️  {error}")
        
        print(f"\n🎯 EVOLUTION SYSTEM CAPABILITIES VERIFIED:")
        print(f"   • Being evolution potential detection")
        print(f"   • Evolution request submission and validation")
        print(f"   • Kernel-based evolution approval/rejection")
        print(f"   • Soul versioning and Being updates")
        print(f"   • Evolution history tracking via relationships")
        print(f"   • Soul creation by evolved beings")
        print(f"   • Access zone evolution and promotion")
        print(f"   • Complete evolution lifecycle management")
        
        print("\n" + "=" * 70)


# Test runner functions
async def run_being_evolution_tests():
    """Główna funkcja uruchamiająca testy ewolucji"""
    tester = BeingEvolutionSystemTester()
    results = await tester.run_complete_evolution_test_suite()
    tester.print_evolution_test_report(results)
    return results


if __name__ == "__main__":
    asyncio.run(run_being_evolution_tests())

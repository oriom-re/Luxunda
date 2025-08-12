"""
Genotype System Initialization
Automatyczne ładowanie i inicjalizacja genotypów przy starcie systemu
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from ..utils.genotype_loader import genotype_loader
from ..models.soul import Soul
from ..models.being import Being
from .postgre_db import Postgre_db

class GenotypeSystem:
    """System zarządzania genotypami"""

    def __init__(self):
        self.loaded_souls: List[Soul] = []
        self.statistics = {}
        self.initialization_complete = False

    async def initialize_system(self) -> Dict[str, Any]:
        """Inicjalizuje system genotypów przy starcie"""
        print("🧬 Inicjalizacja systemu genotypów...")

        try:
            # Utwórz przykładowe genotypy jeśli folder jest pusty
            genotype_loader.create_example_genotypes()

            # Załaduj wszystkie genotypy
            self.loaded_souls = await genotype_loader.load_all_genotypes()

            # Migracja starych danych - sprawdź czy są Soul w bazie które nie mają odpowiedników w plikach
            await self._migrate_old_souls()

            # Pobierz statystyki
            self.statistics = genotype_loader.get_load_statistics()

            self.initialization_complete = True

            result = {
                "success": True,
                "loaded_souls_count": len(self.loaded_souls),
                "statistics": self.statistics,
                "souls": [
                    {
                        "alias": soul.alias,
                        "hash": soul.soul_hash[:8] + "...",
                        "version": soul.get_version(),
                        "type": soul.genotype.get("genesis", {}).get("type", "unknown")
                    }
                    for soul in self.loaded_souls
                ]
            }

            print(f"✅ System genotypów zainicjalizowany: {len(self.loaded_souls)} Soul")
            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "loaded_souls_count": 0
            }

            print(f"❌ Błąd inicjalizacji systemu genotypów: {e}")
            return error_result

    def get_soul_by_alias(self, alias: str) -> Soul:
        """Znajdź Soul po aliasie"""
        for soul in self.loaded_souls:
            if soul.alias == alias:
                return soul
        return None

    def get_souls_by_type(self, soul_type: str) -> List[Soul]:
        """Znajdź Soul po typie"""
        matching_souls = []
        for soul in self.loaded_souls:
            genesis_type = soul.genotype.get("genesis", {}).get("type")
            if genesis_type == soul_type:
                matching_souls.append(soul)
        return matching_souls

    async def _migrate_old_souls(self):
        """Migruje stare Soul z bazy danych"""
        try:
            from ..models.soul import Soul
            
            # Pobierz wszystkie Soul z bazy
            all_souls = await Soul.get_all()
            print(f"🔄 Sprawdzanie {len(all_souls)} Soul w bazie...")
            
            migrated_count = 0
            for soul in all_souls:
                # Sprawdź czy soul ma stary format (brak genesis)
                if not soul.genotype.get("genesis"):
                    print(f"🔧 Migracja Soul: {soul.alias}")
                    await self._migrate_single_soul(soul)
                    migrated_count += 1
                    
                # Dodaj do loaded_souls jeśli nie ma
                if not any(s.soul_hash == soul.soul_hash for s in self.loaded_souls):
                    self.loaded_souls.append(soul)
                    
            if migrated_count > 0:
                print(f"✅ Zmigrowano {migrated_count} Soul")
                
        except Exception as e:
            print(f"⚠️ Problem z migracją Soul: {e}")

    async def _migrate_single_soul(self, soul):
        """Migruje pojedynczą Soul do nowego formatu"""
        try:
            # Utwórz nowy genotyp z genesis
            new_genotype = {
                "genesis": {
                    "name": soul.alias or "migrated_soul",
                    "type": "migrated",
                    "version": "1.0.0",
                    "description": f"Migrated soul: {soul.alias}",
                    "migration_date": datetime.now().isoformat()
                },
                "attributes": soul.genotype.get("attributes", {}),
                "functions": soul.genotype.get("functions", {}),
                "capabilities": soul.genotype.get("capabilities", {}),
                # Zachowaj stare dane w sekcji legacy
                "legacy": {
                    "original_genotype": soul.genotype,
                    "migration_source": "genotype_system"
                }
            }
            
            # Aktualizuj Soul
            soul.genotype = new_genotype
            
            from ..repository.soul_repository import SoulRepository
            await SoulRepository.set(soul)
            
            print(f"✅ Soul {soul.alias} zmigrowana")
            
        except Exception as e:
            print(f"❌ Błąd migracji Soul {soul.alias}: {e}")

    def list_available_souls(self) -> List[Dict[str, Any]]:
        """Lista dostępnych Soul z podstawowymi informacjami"""
        return [
            {
                "alias": soul.alias,
                "hash": soul.soul_hash,
                "type": soul.genotype.get("genesis", {}).get("type", "unknown"),
                "description": soul.genotype.get("genesis", {}).get("description", ""),
                "version": soul.get_version() if hasattr(soul, 'get_version') else "1.0.0",
                "capabilities": soul.genotype.get("capabilities", {}),
                "attributes_count": len(soul.genotype.get("attributes", {})),
                "functions_count": len(soul.genotype.get("functions", {}))
            }
            for soul in self.loaded_souls
        ]

    async def reload_genotypes(self) -> Dict[str, Any]:
        """Przeładuj genotypy z folderu"""
        print("🔄 Przeładowywanie genotypów...")

        # Wyczyść obecne
        self.loaded_souls = []
        genotype_loader.loaded_genotypes = {}
        genotype_loader.load_log = []

        # Załaduj ponownie
        return await self.initialize_system()

async def initialize_system(self) -> Dict[str, Any]:
        """
        Alias dla initialize_system - zgodność z istniejącym kodem
        """
        return await self.initialize_system()

# Globalna instancja
genotype_system = GenotypeSystem()

# Dodaj funkcję na poziomie modułu dla kompatybilności
async def initialize_system() -> Dict[str, Any]:
    """
    Initialize genotype system at module level
    """
    return await genotype_system.initialize_system()
"""
LuxOS Kernel System - Zarządza ładowaniem bytów według scenariuszy hash
"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from luxdb.models.soul import Soul
from luxdb.models.being import Being

class KernelBeing:
    """Prosta klasa Kernel Being dla systemu jądra"""
    def __init__(self):
        self.active = False
        self.registered_beings = {}
        self.intentions = {
            "register_being": self._register_being,
            "get_system_status": self._get_system_status
        }

    async def process_intention(self, intention):
        intention_type = intention.get('type')
        handler = self.intentions.get(intention_type)
        if handler:
            return await handler(intention)
        return {"status": "ok", "message": f"Handled {intention_type}"}

    async def _register_being(self, intention):
        being_info = intention.get('being_info', {})
        being_id = being_info.get('ulid')
        self.registered_beings[being_id] = being_info
        return {"status": "success", "being_id": being_id}

    async def _get_system_status(self, intention):
        return {
            "status": "success",
            "active": self.active,
            "registered_beings": len(self.registered_beings)
        }

class ScenarioLoader:
    """Ładuje scenariusze z hashami bytów"""

    def __init__(self, scenarios_path: str = "scenarios"):
        self.scenarios_path = Path(scenarios_path)
        self.scenarios_path.mkdir(exist_ok=True)
        self.loaded_beings = {}
        self.being_hashes = {}

    def create_being_hash(self, being_data: Dict[str, Any]) -> str:
        """Tworzy hash dla bytu z automatyczną detekcją serializacji"""
        # Automatycznie konwertuj obiekty do JSON-serializable
        serializable_data = self._make_json_serializable(being_data)
        content = json.dumps(serializable_data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _make_json_serializable(self, data: Any) -> Any:
        """Automatycznie wykrywa i konwertuje dane do JSON-serializable"""
        if data is None:
            return None
        elif isinstance(data, (str, int, float, bool)):
            return data
        elif hasattr(data, 'to_json_serializable'):
            return data.to_json_serializable()
        elif hasattr(data, 'to_dict'):
            return data.to_dict()
        elif hasattr(data, '__json__'):
            return data.__json__()
        elif isinstance(data, dict):
            return {k: self._make_json_serializable(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._make_json_serializable(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            # Obiekt z atrybutami - konwertuj na słownik
            return {k: self._make_json_serializable(v) for k, v in data.__dict__.items() if not k.startswith('_')}
        else:
            return data

    async def save_scenario(self, scenario_name: str, beings: List[Dict[str, Any]]) -> str:
        """Zapisuje scenariusz z hashami bytów"""
        scenario_data = {
            "name": scenario_name,
            "created_at": datetime.now().isoformat(),
            "beings": []
        }

        for being_data in beings:
            being_hash = self.create_being_hash(being_data)
            scenario_data["beings"].append({
                "hash": being_hash,
                "load_order": being_data.get("load_order", 0),
                "dependencies": being_data.get("dependencies", [])
            })

            # Zapisz byt pod hashiem z automatyczną serializacją
            being_file = self.scenarios_path / f"{being_hash}.json"
            serializable_data = self._make_json_serializable(being_data)
            with open(being_file, 'w') as f:
                json.dump(serializable_data, f, indent=2)

        # Zapisz scenariusz z automatyczną serializacją
        scenario_file = self.scenarios_path / f"{scenario_name}.scenario"
        serializable_scenario = self._make_json_serializable(scenario_data)
        with open(scenario_file, 'w') as f:
            json.dump(serializable_scenario, f, indent=2)

        scenario_hash = self.create_being_hash(scenario_data)
        print(f"💾 Zapisano scenariusz: {scenario_name} (hash: {scenario_hash})")
        return scenario_hash

    async def load_scenario(self, scenario_name: str) -> List[Being]:
        """Ładuje scenariusz z pliku i tworzy byty"""
        scenario_path = Path(f"scenarios/{scenario_name}.scenario")

        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenariusz {scenario_name} nie istnieje")

        with open(scenario_path, 'r', encoding='utf-8') as f:
            scenario_content = f.read()

        # Sprawdź czy to JSON czy zwykły tekst
        try:
            scenario_data = json.loads(scenario_content)
        except json.JSONDecodeError:
            # Jeśli nie JSON, traktuj jako prostą listę bytów
            scenario_data = {"beings": []}

        beings = []
        for being_config in scenario_data.get('beings', []):
            # Upewnij się że being_config to dict, nie string
            if isinstance(being_config, str):
                try:
                    being_config = json.loads(being_config)
                except json.JSONDecodeError:
                    continue

            being = await self.load_being_from_config(being_config)
            if being:
                beings.append(being)
                self.loaded_beings[being.ulid] = being
                self.being_hashes[being.ulid] = self.create_being_hash(being_config)

        return beings

    async def load_being_by_hash(self, being_hash: str) -> Optional[Being]:
        """Ładuje byt według hasha"""
        if being_hash in self.loaded_beings:
            return self.loaded_beings[being_hash]

        being_file = self.scenarios_path / f"{being_hash}.json"

        if not being_file.exists():
            return None

        with open(being_file, 'r') as f:
            being_data = json.load(f)

        # Sprawdź czy being_data jest stringiem i zdekoduj go
        if isinstance(being_data, str):
            being_data = json.loads(being_data)

        # Utwórz Soul jeśli nie istnieje
        soul_alias = being_data.get("soul_alias", f"soul_{being_hash[:8]}")
        soul = await Soul.get(alias=soul_alias)

        if not soul:
            soul = await Soul.set(
                genotype=being_data.get("genotype", {}),
                alias=soul_alias
            )

        # Utwórz Being
        being = await Being.set(
            soul=soul,  # Przekaż obiekt Soul
            data=being_data.get("attributes", {}),
            alias=being_data.get("alias", f"being_{being_hash[:8]}"))

        # Zapisz obiekt soul w cache dla przyszłego użytku
        being._soul_cache = soul

        self.loaded_beings[being_hash] = being
        self.being_hashes[being.ulid] = being_hash

        return being

    async def _save_being_to_database(self, being_data):
        """Zapisuje byt do bazy danych używając Being.create"""
        try:
            # Sprawdź czy being_data jest stringiem i zdekoduj go
            if isinstance(being_data, str):
                being_data = json.loads(being_data)

            # Sprawdź czy to jest słownik z danymi
            if isinstance(being_data, dict):
                # Przygotuj genotype dla Soul
                genotype = being_data.get('genotype', {})
                if not genotype:
                    # Domyślny genotype jeśli brak
                    genotype = {
                        "genesis": {
                            "name": being_data.get('alias', 'unknown_being'),
                            "version": "1.0"
                        },
                        "attributes": {
                            "name": {"py_type": "str"},
                            "type": {"py_type": "str"}
                        }
                    }

                # Utwórz Soul
                soul = await Soul.set(genotype, being_data.get('alias', 'unknown'))

                # Przygotuj dane dla Being
                attributes = being_data.get('attributes', {})

                # Utwórz Being z obiektem Soul
                being = await Being.set(
                    soul=soul,  # Przekaż obiekt Soul
                    data=attributes,
                    alias=being_data.get('alias', f"being_{soul.soul_hash[:8]}"))

                # Zapisz obiekt soul w cache
                being._soul_cache = soul

                return being
            else:
                print(f"❌ Error saving being: Invalid being_data type: {type(being_data)}")
                return None
        except Exception as e:
            print(f"❌ Error saving being: {str(e)}")
            return None

    async def load_being_from_config(self, config: Dict[str, Any]) -> Optional[Being]:
        """Ładuje byt z konfiguracji"""
        try:
            # Upewnij się że config ma wymagane pola
            if not isinstance(config, dict):
                return None

            alias = config.get('alias', f'being_{uuid.uuid4().hex[:8]}')

            # Znajdź lub utwórz soul dla tego bytu
            soul_alias = config.get('soul_alias', f"soul_{alias}")
            genotype = config.get('genotype', {})

            # Upewnij się że genotype ma wymagane sekcje
            if 'genesis' not in genotype:
                genotype['genesis'] = {
                    'name': alias,
                    'type': 'generic',
                    'version': '1.0.0'
                }

            if 'attributes' not in genotype:
                genotype['attributes'] = {}

            # Utwórz soul
            soul = await Soul.create(
                alias=soul_alias,
                genotype=genotype
            )

            # Utwórz byt
            being_data = {
                'alias': alias,
                'soul_hash': soul.soul_hash,
                'type': config.get('type', 'generic'),
                **config.get('attributes', {})
            }

            being = await Being.create(
                soul_hash=soul.soul_hash,
                data=being_data
            )

            return being

        except Exception as e:
            print(f"⚠️ Nie udało się załadować bytu {config.get('alias', 'unknown')}: {e}")
            return None


class KernelSystem:
    """System Kernel zarządzający całym LuxOS"""

    def __init__(self):
        self.kernel_being = KernelBeing()
        self.scenario_loader = ScenarioLoader()
        self.active_scenario = None
        self.beings_registry = {}
        self.load_sequence = [
            "kernel",
            "communication",
            "database",
            "platform",
            "agents",
            "presentation"
        ]

    async def initialize(self, scenario_name: str = "default"):
        """Inicjalizuje system według scenariusza"""
        print("🚀 Inicjalizacja LuxOS Kernel System...")

        # Aktywuj Kernel Being
        self.kernel_being.active = True

        # Załaduj scenariusz
        try:
            beings = await self.scenario_loader.load_scenario(scenario_name)
            self.active_scenario = scenario_name

            # Zarejestruj byty w kernel
            for being in beings:
                await self.register_being(being)

        except FileNotFoundError:
            print(f"⚠️ Scenariusz {scenario_name} nie istnieje, tworzę domyślny...")
            await self.create_default_scenario()

        print("✅ LuxOS Kernel System zainicjalizowany")

    async def register_being(self, being: Being):
        """Rejestruje byt w systemie"""
        await self.kernel_being.process_intention({
            "type": "register_being",
            "being_info": {
                "ulid": being.ulid,
                "soul_hash": being.soul_hash,
                "alias": being.alias,
                "type": getattr(being, 'being_type', 'generic')
            }
        })

        self.beings_registry[being.ulid] = being
        print(f"📋 Zarejestrowano byt: {being.alias} ({being.ulid[:8]}...)")

    async def create_default_scenario(self):
        """Tworzy domyślny scenariusz"""
        default_beings = [
            {
                "alias": "kernel_core",
                "soul_alias": "kernel_soul",
                "genotype": {
                    "genesis": {
                        "name": "kernel_system",
                        "type": "system_kernel",
                        "version": "1.0.0",
                        "description": "Główny kernel systemu LuxOS"
                    },
                },
                "attributes": {
                    "system_role": "kernel",
                    "priority": 100
                },
                "load_order": 0
            },
            {
                "alias": "communication_hub",
                "soul_alias": "comm_soul",
                "genotype": {
                    "genesis": {
                        "name": "communication",
                        "type": "system_io",
                        "doc": "Hub komunikacyjny systemu"
                    }
                },
                "attributes": {
                    "system_role": "communication",
                    "priority": 90
                },
                "load_order": 1,
                "dependencies": ["kernel_core"]
            },
            {
                "alias": "platform_manager",
                "soul_alias": "platform_soul",
                "genotype": {
                    "genesis": {
                        "name": "platform",
                        "type": "system_platform",
                        "doc": "Manager platformy LuxOS"
                    }
                },
                "attributes": {
                    "system_role": "platform",
                    "priority": 80
                },
                "load_order": 2,
                "dependencies": ["kernel_core", "communication_hub"]
            }
        ]

        scenario_hash = await self.scenario_loader.save_scenario("default", default_beings)
        beings = await self.scenario_loader.load_scenario("default")

        for being in beings:
            await self.register_being(being)

        self.active_scenario = "default"

    async def load_new_configuration(self, scenario_name: str):
        """Ładuje nową konfigurację (nowy scenariusz)"""
        print(f"🔄 Przełączanie na scenariusz: {scenario_name}")

        # Wyczyść obecny stan
        self.beings_registry.clear()
        self.scenario_loader.loaded_beings.clear()

        # Załaduj nowy scenariusz
        await self.initialize(scenario_name)

        print(f"✅ Przełączono na scenariusz: {scenario_name}")

    async def get_system_status(self) -> Dict[str, Any]:
        """Zwraca status systemu"""
        kernel_status = await self.kernel_being.process_intention({
            "type": "get_system_status"
        })

        return {
            "kernel_status": kernel_status,
            "active_scenario": self.active_scenario,
            "registered_beings": len(self.beings_registry),
            "loaded_hashes": len(self.scenario_loader.loaded_beings),
            "beings_list": [
                {
                    "ulid": ulid[:8] + "...",
                    "alias": being.alias,
                    "hash": self.scenario_loader.being_hashes.get(ulid, "unknown")[:8] + "..."
                }
                for ulid, being in self.beings_registry.items()
            ]
        }

    async def create_new_being(self, being_data: Dict[str, Any]) -> str:
        """Tworzy nowy byt (nowy plik = nowy byt)"""
        # Każdy nowy byt to nowy plik z nowym hashem
        being_hash = self.scenario_loader.create_being_hash(being_data)

        # Utwórz byt
        being = await self.scenario_loader.load_being_by_hash(being_hash)

        if being:
            await self.register_being(being)
            print(f"🆕 Utworzono nowy byt: {being.alias} (hash: {being_hash[:8]}...)")

        return being_hash

# Globalna instancja
kernel_system = KernelSystem()
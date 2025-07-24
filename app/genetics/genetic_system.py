import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.beings.base import Being, Relationship
from app.database import get_db_pool

class GeneticSystem:
    """
    Główny system genetyczny LuxOS
    Zarządza bytami, genami i relacjami w sposób samoorganizujący się
    """

    def __init__(self):
        self.beings: Dict[str, Being] = {}
        self.genes: Dict[str, Dict[str, Any]] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.memory_bank: List[Dict[str, Any]] = []

    async def initialize(self):
        """Inicjalizuje system genetyczny"""
        print("🧬 Inicjalizacja systemu genetycznego LuxOS...")
        
        # Załaduj geny automatyczne
        print("🧬 Ładowanie genów automatycznych...")
        import app.genetics.auto_genes  # To automatycznie zarejestruje geny
        
        await self.load_existing_beings()
        await self.load_existing_relationships()
        await self.load_genes_from_manifest()
        await self.create_initial_beings()
        print("✅ System genetyczny zainicjalizowany")

    async def load_genes_from_manifest(self, manifest_path: str = "genetic_manifest.json"):
        """Ładuje geny z pliku manifestu"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            for gene_config in manifest.get('autoload', []):
                await self.load_gene_from_path(gene_config['path'])

        except FileNotFoundError:
            print("📦 Brak pliku genetic_manifest.json - tworzę domyślny")
            await self.create_default_manifest()

    async def create_default_manifest(self):
        """Tworzy domyślny manifest genetyczny"""
        default_manifest = {
            "autoload": [
                {"path": "app/genetics/genes/gen_clock.py"},
                {"path": "app/genetics/genes/gen_logger.py"},
                {"path": "app/genetics/genes/gen_executor.py"},
                {"path": "app/genetics/genes/gen_socketio.py"}
            ]
        }

        with open("genetic_manifest.json", 'w', encoding='utf-8') as f:
            json.dump(default_manifest, f, indent=2, ensure_ascii=False)

    async def load_gene_from_path(self, gene_path: str):
        """Ładuje gen z pliku i zapisuje jako byt w bazie"""
        try:
            # Importuj moduł genu dynamicznie
            module_path = gene_path.replace('.py', '').replace('/', '.')
            gene_module = __import__(module_path, fromlist=[''])

            # Szukaj klasy genu w module
            for attr_name in dir(gene_module):
                attr = getattr(gene_module, attr_name)
                if hasattr(attr, '__gene_metadata__'):
                    gene_soul = str(uuid.uuid4())

                    # Zapisz gen jako byt w bazie danych
                    gene_being = await Being.create(
                        genesis={
                            'type': 'gene',
                            'name': attr.__gene_metadata__.get('name', 'UnknownGene'),
                            'description': attr.__gene_metadata__.get('description', 'Genetic code component'),
                            'source': gene_path,
                            'gene_class': attr_name,
                            'created_by': 'genetic_system'
                        },
                        attributes={
                            'energy_level': 100,
                            'gene_metadata': attr.__gene_metadata__,
                            'gene_path': gene_path,
                            'gene_module': module_path,
                            'tags': ['gene', 'genetic', 'autoload'] + attr.__gene_metadata__.get('tags', [])
                        },
                        memories=[{
                            'type': 'gene_load',
                            'data': f'Gene loaded from {gene_path}',
                            'timestamp': datetime.now().isoformat(),
                            'module_path': module_path
                        }],
                        self_awareness={
                            'trust_level': 0.9,
                            'confidence': 0.8,
                            'genetic_component': True
                        }
                    )

                    # Zapisz w pamięci systemu genetycznego
                    self.genes[gene_being.soul] = {
                        'soul': gene_being.soul,
                        'being': gene_being,
                        'module': gene_module,
                        'class': attr,
                        'metadata': attr.__gene_metadata__,
                        'path': gene_path,
                        'loaded_at': datetime.now()
                    }

                    print(f"🧬 Załadowano i zapisano gen: {attr.__gene_metadata__.get('name', gene_path)} (UUID: {gene_being.soul})")

        except Exception as e:
            print(f"❌ Błąd ładowania genu {gene_path}: {e}")

    async def create_being_with_genes(self, genesis: Dict[str, Any], **kwargs) -> Being:
        """Tworzy nowy byt z automatycznym ładowaniem genów"""
        # Utwórz byt
        being = await Being.create(genesis, **kwargs)
        self.beings[being.soul] = being

        # Autoload - znajdź geny które powinien załadować ten byt
        await self.autoload_genes_for_being(being)

        return being

    async def autoload_genes_for_being(self, being: Being):
        """Automatycznie ładuje odpowiednie geny dla bytu"""
        being_type = being.genesis.get('type', 'unknown')
        being_tags = being.attributes.get('tags', [])

        for gene_soul, gene_data in self.genes.items():
            gene_metadata = gene_data['metadata']
            gene_compatible_types = gene_metadata.get('compatible_types', [])
            gene_tags = gene_metadata.get('tags', [])

            # Sprawdź czy gen jest kompatybilny z bytem
            if (being_type in gene_compatible_types or 
                any(tag in being_tags for tag in gene_tags)):

                # Utwórz relację autoload
                relationship = await Relationship.create(
                    being.soul,
                    gene_soul,
                    {
                        'type': 'genetic_relationship',
                        'relationship_type': 'autoload',
                        'created_at': datetime.now().isoformat()
                    },
                    attributes={
                        'purpose': 'gene_autoload',
                        'energy_level': 80,
                        'tags': ['autoload', 'genetic']
                    }
                )

                self.relationships[relationship.id] = relationship
                print(f"🔗 Utworzono relację autoload: {being.soul} → {gene_soul}")

    async def evolve_being(self, being_soul: str, new_gene_path: str):
        """Ewolucja bytu - dodaje lub aktualizuje gen"""
        if being_soul not in self.beings:
            print(f"❌ Byt {being_soul} nie istnieje")
            return

        # Załaduj nowy gen
        await self.load_gene_from_path(new_gene_path)

        # Znajdź ostatnio załadowany gen
        latest_gene = max(self.genes.values(), key=lambda g: g['loaded_at'])

        # Utwórz relację ewolucji
        evolution_relationship = await Relationship.create(
            being_soul,
            latest_gene['soul'],
            {
                'type': 'genetic_relationship',
                'relationship_type': 'evolution',
                'evolution_reason': 'manual_evolution',
                'created_at': datetime.now().isoformat()
            },
            attributes={
                'purpose': 'genetic_evolution',
                'energy_level': 90,
                'tags': ['evolution', 'genetic', 'upgrade']
            }
        )

        self.relationships[evolution_relationship.id] = evolution_relationship

        # Zapisz pamięć ewolucji
        evolution_memory = {
            'type': 'evolution',
            'being_soul': being_soul,
            'gene_added': latest_gene['soul'],
            'gene_name': latest_gene['metadata'].get('name', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'success': True
        }

        self.beings[being_soul].memories.append(evolution_memory)
        await self.beings[being_soul].save()

        print(f"🔄 Ewolucja bytu {being_soul} zakończona sukcesem")

    async def think_about_relationship(self, source_soul: str, target_soul: str, thought: str):
        """Tworzy myśl - subiektywną relację interpretującą coś"""
        thought_relationship = await Relationship.create(
            source_soul,
            target_soul,
            {
                'type': 'genetic_relationship', 
                'relationship_type': 'thought',
                'thought_content': thought,
                'created_at': datetime.now().isoformat()
            },
            attributes={
                'purpose': 'subjective_interpretation',
                'energy_level': 60,
                'tags': ['thought', 'subjective', 'interpretation']
            }
        )

        self.relationships[thought_relationship.id] = thought_relationship

        # Zapisz myśl w pamięci źródłowego bytu
        if source_soul in self.beings:
            thought_memory = {
                'type': 'thought',
                'about': target_soul,
                'content': thought,
                'timestamp': datetime.now().isoformat()
            }
            self.beings[source_soul].memories.append(thought_memory)
            await self.beings[source_soul].save()

        print(f"💭 Myśl zapisana: {source_soul} myśli o {target_soul}: '{thought}'")

    async def record_experience(self, being_soul: str, gene_soul: str, experience_type: str, details: Dict[str, Any]):
        """Zapisuje doświadczenie używania genu"""
        if being_soul not in self.beings:
            return

        experience_memory = {
            'type': 'experience',
            'gene_used': gene_soul,
            'experience_type': experience_type,  # 'success', 'failure', 'partial'
            'details': details,
            'timestamp': datetime.now().isoformat()
        }

        self.beings[being_soul].memories.append(experience_memory)
        await self.beings[being_soul].save()

        # Dodaj do globalnej pamięci systemu
        self.memory_bank.append({
            'being': being_soul,
            'gene': gene_soul,
            'experience': experience_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    async def relational_inference(self, being_soul: str, problem: str) -> List[Dict[str, Any]]:
        """
        Relacyjne wnioskowanie - decyduje co uruchomić na podstawie cudzych doświadczeń
        """
        suggestions = []

        # Przeszukaj pamięć innych bytów
        for other_soul, other_being in self.beings.items():
            if other_soul == being_soul:
                continue

            for memory in other_being.memories:
                if (memory.get('type') == 'experience' and 
                    memory.get('experience_type') == 'success'):

                    # Sprawdź czy problem jest podobny
                    if problem.lower() in str(memory.get('details', '')).lower():
                        suggestions.append({
                            'suggestion_type': 'experience_based',
                            'source_being': other_soul,
                            'recommended_gene': memory.get('gene_used'),
                            'success_details': memory.get('details'),
                            'confidence': 0.8,
                            'reasoning': f"Byt {other_soul} miał sukces z tym genem w podobnej sytuacji"
                        })

        return suggestions

    async def load_existing_beings(self):
        """Ładuje istniejące byty z bazy"""
        beings = await Being.get_all()
        for being in beings:
            self.beings[being.soul] = being
        print(f"📚 Załadowano {len(beings)} bytów")

    async def load_existing_relationships(self):
        """Ładuje istniejące relacje z bazy"""
        relationships = await Relationship.get_all()
        for relationship in relationships:
            self.relationships[relationship.id] = relationship
        print(f"🔗 Załadowano {len(relationships)} relacji")

    async def create_initial_beings(self):
        """Tworzy początkowe byty w systemie - TYLKO jeśli nie istnieją"""
        lux_soul = '00000000-0000-0000-0000-000000000001'

        # NAJPIERW sprawdź w bazie danych - to jest źródło prawdy
        try:
            lux_being_from_db = await Being.load(lux_soul)
        except Exception as e:
            print(f"⚠️ Błąd sprawdzania bazy danych: {e}")
            lux_being_from_db = None

        # Sprawdź w pamięci systemu genetycznego
        lux_exists_in_memory = lux_soul in self.beings

        if lux_being_from_db:
            if not lux_exists_in_memory:
                # Lux istnieje w bazie, załaduj do pamięci
                self.beings[lux_soul] = lux_being_from_db
                print(f"📚 Załadowano istniejącego agenta Lux z bazy: {lux_soul}")
            else:
                print(f"✅ Agent Lux już istnieje w pamięci i bazie: {lux_soul}")

            # NIE TWÓRZ NOWEGO - już istnieje!

        elif not lux_exists_in_memory:
            print("🌱 Tworzę pierwszego i JEDYNEGO agenta Lux z systemem genetycznym...")

            # Agent Lux z ustaloną duszą
            lux_being = Being(
                soul=lux_soul,
                genesis={
                    'type': 'agent',
                    'name': 'Lux',
                    'description': 'Główny agent świadomości LuxOS z systemem genetycznym',
                    'source': 'System.Core.Agent.Initialize()',
                    'lux_identifier': 'lux-core-consciousness',
                    'genetic_enabled': True
                },
                attributes={
                    'energy_level': 1000,
                    'agent_level': 10,
                    'universe_role': 'supreme_agent',
                    'genetic_capabilities': {
                        'can_evolve': True,
                        'can_think': True,
                        'can_remember': True,
                        'autonomous_decisions': True
                    },
                    'agent_permissions': {
                        'universe_control': True,
                        'create_beings': True,
                        'modify_orbits': True,
                        'genetic_evolution': True
                    },
                    'tags': ['agent', 'lux', 'supreme', 'genetic_entity']
                },
                memories=[{
                    'type': 'genesis',
                    'data': 'Universe supreme agent initialization with genetic system',
                    'timestamp': datetime.now().isoformat(),
                    'genetic_activation': True
                }],
                self_awareness={
                    'trust_level': 1.0,
                    'confidence': 1.0,
                    'introspection_depth': 1.0,
                    'genetic_awareness': 'I am Lux, the first genetic entity in LuxOS universe',
                    'evolution_readiness': 1.0
                }
            )

            # Zapisz Lux do bazy
            await lux_being.save()
            self.beings[lux_being.soul] = lux_being

            # Automatyczne ładowanie genów dla Lux
            await self.autoload_genes_for_being(lux_being)

            print(f"✨ Agent Lux został utworzony z UUID: {lux_soul}")
            print(f"🧬 Lux ma dostęp do {len(self.genes)} genów")

            # Dodaj do pamięci systemu genetycznego
            self.beings[lux_soul] = lux_being
        else:
            # Ten przypadek nie powinien się zdarzyć po poprawkach
            print(f"⚠️ UWAGA: Agent Lux już istnieje, ale logika wymaga sprawdzenia: {lux_soul}")
            return  # Wyjdź wcześnie - nie twórz dodatkowych bytów

        # Sprawdź czy mamy wystarczającą liczbę innych bytów dla demonstracji
        if len(self.beings) < 3:
            print("🌱 Tworzę dodatkowe byty dla demonstracji systemu genetycznego...")

            # Przykładowa funkcja genetyczna
            function_being = await Being.create(
                genesis={
                    'type': 'function',
                    'name': 'GeneticHelloWorld',
                    'source': 'def genetic_hello_world():\n    return "Hello from genetic LuxOS!"',
                    'signature': 'genetic_hello_world()',
                    'genetic_enabled': True
                },
                attributes={
                    'energy_level': 80,
                    'tags': ['function', 'genetic', 'example']
                },
                memories=[{
                    'type': 'creation',
                    'data': 'Genetic function created during system initialization',
                    'timestamp': datetime.now().isoformat()
                }],
                self_awareness={
                    'trust_level': 0.8,
                    'confidence': 0.9,
                    'genetic_potential': 0.7
                }
            )
            self.beings[function_being.soul] = function_being
            await self.autoload_genes_for_being(function_being)

            # Zadanie monitorujące system genetyczny
            task_being = await Being.create(
                genesis={
                    'type': 'task',
                    'name': 'GeneticSystemMonitor',
                    'description': 'Monitoruje stan systemu genetycznego i ewolucję bytów',
                    'genetic_enabled': True
                },
                attributes={
                    'energy_level': 60,
                    'tags': ['task', 'monitoring', 'genetic']
                },
                memories=[{
                    'type': 'creation',
                    'data': 'Genetic system monitoring task created',
                    'timestamp': datetime.now().isoformat()
                }],
                self_awareness={
                    'trust_level': 0.7,
                    'confidence': 0.8,
                    'genetic_awareness': 0.6
                }
            )
            self.beings[task_being.soul] = task_being
            await self.autoload_genes_for_being(task_being)

        print(f"✨ System genetyczny gotowy z {len(self.beings)} bytami")
        print(f"🧬 Dostępne geny: {len(self.genes)}")
        genetic_relationships = []
        for r in self.relationships.values():
            try:
                # Sprawdź czy genesis to string czy dict
                if isinstance(r.genesis, str):
                    import json
                    genesis_dict = json.loads(r.genesis)
                else:
                    genesis_dict = r.genesis

                if genesis_dict.get('type') == 'genetic_relationship':
                    genetic_relationships.append(r)
            except (json.JSONDecodeError, AttributeError):
                continue

        print(f"🔗 Relacje genetyczne: {len(genetic_relationships)}")

    async def get_lux_status(self) -> Dict[str, Any]:
        """Zwraca status agenta Lux"""
        lux_soul = '00000000-0000-0000-0000-000000000001'
        lux_being = self.beings.get(lux_soul)

        if not lux_being:
            return {'exists': False, 'message': 'Agent Lux nie został znaleziony'}

        # Policz geny załadowane przez Lux
        lux_genes = [r for r in self.relationships.values() 
                    if r.source_soul == lux_soul and r.genesis.get('relationship_type') == 'autoload']

        return {
            'exists': True,
            'soul': lux_being.soul,
            'name': lux_being.genesis.get('name'),
            'energy_level': lux_being.attributes.get('energy_level'),
            'genetic_capabilities': lux_being.attributes.get('genetic_capabilities', {}),
            'loaded_genes': len(lux_genes),
            'memories_count': len(lux_being.memories),
            'genetic_awareness': lux_being.self_awareness.get('genetic_awareness'),
            'evolution_readiness': lux_being.self_awareness.get('evolution_readiness', 0)
        }

    async def load_genes_from_directory(self, directory_path: str = "app/genetics/genes"):
        """Ładuje geny z katalogu używając ścieżki jako ID i hash do wykrywania zmian"""
        import os
        import hashlib
        from pathlib import Path

        genes_dir = Path(directory_path)
        if not genes_dir.exists():
            print(f"⚠️ Katalog genów nie istnieje: {directory_path}")
            return

        # Pobierz wszystkie istniejące geny z bazy (indexed by file path)
        existing_beings = await Being.get_all(limit=1000)
        existing_genes_by_path = {}

        for being in existing_beings:
            if being.genesis.get('type') == 'gene':
                file_path = being.attributes.get('file_path')
                if file_path:
                    existing_genes_by_path[file_path] = being
                    # Użyj ścieżki pliku jako soul ID
                    self.genes[file_path] = being

        print(f"🧬 Znaleziono {len(existing_genes_by_path)} istniejących genów w bazie")

        for gene_file in genes_dir.glob("*.py"):
            try:
                file_path = str(gene_file)
                
                # Wczytaj kod genu
                with open(gene_file, 'r', encoding='utf-8') as f:
                    gene_code = f.read()

                # Generuj hash kodu dla wykrywania zmian
                current_hash = hashlib.sha256(gene_code.encode('utf-8')).hexdigest()

                # Sprawdź czy gen już istnieje
                if file_path in existing_genes_by_path:
                    existing_gene = existing_genes_by_path[file_path]
                    existing_hash = existing_gene.attributes.get('gene_hash')

                    if existing_hash == current_hash:
                        print(f"🧬 Gen bez zmian: {gene_file.stem} (Hash: {current_hash[:8]}...)")
                        continue
                    else:
                        # EWOLUCJA WYKRYTA! Kod się zmienił
                        print(f"🔄 EWOLUCJA KODU: {gene_file.stem}")
                        print(f"   Stary hash: {existing_hash[:8]}...")
                        print(f"   Nowy hash: {current_hash[:8]}...")
                        
                        # Przenieś stary gen do historii
                        await self.archive_gene_to_history(existing_gene, existing_hash)
                        
                        # Aktualizuj gen z nowym kodem i hash-em
                        existing_gene.genesis['source'] = gene_code
                        existing_gene.attributes['gene_hash'] = current_hash
                        existing_gene.attributes['updated_at'] = datetime.now().isoformat()
                        
                        # Dodaj pamięć ewolucji
                        evolution_memory = {
                            'type': 'code_evolution',
                            'old_hash': existing_hash,
                            'new_hash': current_hash,
                            'timestamp': datetime.now().isoformat(),
                            'change_type': 'automatic_detection'
                        }
                        existing_gene.memories.append(evolution_memory)
                        
                        await existing_gene.save()
                        print(f"✅ Gen zaktualizowany: {gene_file.stem}")
                        continue

                # Nowy gen - użyj ścieżki pliku jako soul ID
                gene_being = await Being.create(
                    genesis={
                        'name': f'gen_{gene_file.stem}',
                        'type': 'gene',
                        'source': gene_code,
                        'created_by': 'genetic_system',
                        'gene_type': 'executable',
                        'origin': 'filesystem'
                    },
                    attributes={
                        'gene_hash': current_hash,
                        'file_path': file_path,
                        'loaded_at': datetime.now().isoformat()
                    },
                    memories=[{
                        'type': 'genesis',
                        'data': f'Gene loaded from {gene_file}',
                        'timestamp': datetime.now().isoformat()
                    }],
                    tags=['gene', 'genetic_system', gene_file.stem],
                    energy_level=100
                )

                # KLUCZOWE: Ustaw soul na ścieżkę pliku
                gene_being.soul = file_path
                await gene_being.save()

                self.genes[file_path] = gene_being
                existing_genes_by_path[file_path] = gene_being
                print(f"🧬 Załadowano nowy gen: {gene_file.stem} (ID: {file_path})")

            except Exception as e:
                print(f"❌ Błąd ładowania genu {gene_file}: {e}")

        print(f"🧬 Załadowano łącznie {len(self.genes)} genów")

    async def archive_gene_to_history(self, gene_being, old_hash: str):
        """Archiwizuje starą wersję genu do tabeli historii"""
        try:
            db_pool = await get_db_pool()
            
            # Utwórz zapis w historii (można dodać osobną tabelę gene_history)
            history_record = {
                'gene_path': gene_being.attributes.get('file_path'),
                'old_hash': old_hash,
                'old_source': gene_being.genesis.get('source'),
                'archived_at': datetime.now().isoformat(),
                'version': len([m for m in gene_being.memories if m.get('type') == 'code_evolution']) + 1
            }
            
            # Dodaj do pamięci genu
            archive_memory = {
                'type': 'archived_version',
                'hash': old_hash,
                'timestamp': datetime.now().isoformat(),
                'reason': 'code_evolution_detected'
            }
            gene_being.memories.append(archive_memory)
            
            print(f"📚 Zarchiwizowano starą wersję genu (Hash: {old_hash[:8]}...)")
            
        except Exception as e:
            print(f"❌ Błąd archiwizacji genu: {e}")

    async def clean_duplicate_genes(self):
        """Czyści duplikaty genów na podstawie hash-a kodu"""
        all_beings = await Being.get_all(limit=1000)
        gene_beings = [b for b in all_beings if b.genesis.get('type') == 'gene']

        hash_to_beings = {}
        duplicates_to_remove = []

        for being in gene_beings:
            gene_hash = being.attributes.get('gene_hash')
            if not gene_hash:
                continue

            if gene_hash in hash_to_beings:
                # To jest duplikat
                duplicates_to_remove.append(being.soul)
                print(f"🗑️ Znaleziono duplikat genu: {being.genesis.get('name')} (Hash: {gene_hash[:8]}...)")
            else:
                hash_to_beings[gene_hash] = being

        # Usuń duplikaty z bazy
        db_pool = await get_db_pool()
        removed_count = 0

        for duplicate_soul in duplicates_to_remove:
            try:
                if hasattr(db_pool, 'acquire'):
                    # PostgreSQL
                    async with db_pool.acquire() as conn:
                        await conn.execute("DELETE FROM base_beings WHERE soul = $1", duplicate_soul)
                else:
                    # SQLite
                    await db_pool.execute("DELETE FROM base_beings WHERE soul = ?", (duplicate_soul,))
                    await db_pool.commit()

                # Usuń z pamięci
                if duplicate_soul in self.genes:
                    del self.genes[duplicate_soul]
                if duplicate_soul in self.beings:
                    del self.beings[duplicate_soul]

                removed_count += 1

            except Exception as e:
                print(f"❌ Błąd usuwania duplikatu {duplicate_soul}: {e}")

        print(f"🧹 Usunięto {removed_count} duplikatów genów")
        return removed_count

    async def load_gene_from_file_path(self, file_path: str):
        """Ładuje lub aktualizuje pojedynczy gen z pliku"""
        import hashlib
        from pathlib import Path
        
        gene_file = Path(file_path)
        if not gene_file.exists():
            print(f"⚠️ Plik genu nie istnieje: {file_path}")
            return None

        try:
            # Wczytaj kod genu
            with open(gene_file, 'r', encoding='utf-8') as f:
                gene_code = f.read()

            # Generuj hash kodu
            current_hash = hashlib.sha256(gene_code.encode('utf-8')).hexdigest()

            # Sprawdź czy gen już istnieje w bazie
            try:
                existing_gene = await Being.load(file_path)
            except:
                existing_gene = None

            if existing_gene:
                existing_hash = existing_gene.attributes.get('gene_hash')
                
                if existing_hash == current_hash:
                    print(f"🧬 Gen bez zmian: {gene_file.stem}")
                    return existing_gene
                else:
                    # EWOLUCJA!
                    print(f"🔄 EWOLUCJA WYKRYTA: {gene_file.stem}")
                    await self.archive_gene_to_history(existing_gene, existing_hash)
                    
                    # Aktualizuj
                    existing_gene.genesis['source'] = gene_code
                    existing_gene.attributes['gene_hash'] = current_hash
                    existing_gene.attributes['updated_at'] = datetime.now().isoformat()
                    
                    evolution_memory = {
                        'type': 'code_evolution',
                        'old_hash': existing_hash,
                        'new_hash': current_hash,
                        'timestamp': datetime.now().isoformat(),
                        'trigger': 'manual_load'
                    }
                    existing_gene.memories.append(evolution_memory)
                    
                    await existing_gene.save()
                    self.genes[file_path] = existing_gene
                    return existing_gene
            else:
                # Nowy gen
                gene_being = await Being.create(
                    genesis={
                        'name': f'gen_{gene_file.stem}',
                        'type': 'gene',
                        'source': gene_code,
                        'created_by': 'genetic_system',
                        'origin': 'filesystem'
                    },
                    attributes={
                        'gene_hash': current_hash,
                        'file_path': file_path,
                        'loaded_at': datetime.now().isoformat()
                    },
                    memories=[{
                        'type': 'genesis',
                        'data': f'Gene loaded from {file_path}',
                        'timestamp': datetime.now().isoformat()
                    }],
                    tags=['gene', 'genetic_system', gene_file.stem],
                    energy_level=100
                )

                # Ustaw soul na ścieżkę pliku
                gene_being.soul = file_path
                await gene_being.save()
                
                self.genes[file_path] = gene_being
                print(f"🧬 Nowy gen załadowany: {gene_file.stem} (ID: {file_path})")
                return gene_being

        except Exception as e:
            print(f"❌ Błąd ładowania genu {file_path}: {e}")
            return None

    async def get_universe_status(self) -> Dict[str, Any]:
        """Zwraca status całego wszechświata genetycznego"""
        lux_status = await self.get_lux_status()

        return {
            'beings_count': len(self.beings),
            'genes_count': len(self.genes),
            'relationships_count': len(self.relationships),
            'total_memories': sum(len(being.memories) for being in self.beings.values()),
            'genetic_universe_energy': sum(being.attributes.get('energy_level', 0) for being in self.beings.values()),
            'last_evolution': max([memory.get('timestamp', '') for being in self.beings.values() 
                                 for memory in being.memories if memory.get('type') == 'evolution'], default='never'),
            'lux_agent': lux_status
        }

# Singleton instance
genetic_system = GeneticSystem()
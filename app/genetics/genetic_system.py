
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.beings.base import BaseBeing, Relationship
from app.database import get_db_pool

class GeneticSystem:
    """
    Główny system genetyczny LuxOS
    Zarządza bytami, genami i relacjami w sposób samoorganizujący się
    """
    
    def __init__(self):
        self.beings: Dict[str, BaseBeing] = {}
        self.genes: Dict[str, Dict[str, Any]] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.memory_bank: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """Inicjalizuje system genetyczny"""
        print("🧬 Inicjalizacja systemu genetycznego LuxOS...")
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
                    gene_being = await BaseBeing.create(
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
    
    async def create_being_with_genes(self, genesis: Dict[str, Any], **kwargs) -> BaseBeing:
        """Tworzy nowy byt z automatycznym ładowaniem genów"""
        # Utwórz byt
        being = await BaseBeing.create(genesis, **kwargs)
        self.beings[being.soul] = being
        
        # Autoload - znajdź geny które powinien załadować ten byt
        await self.autoload_genes_for_being(being)
        
        return being
    
    async def autoload_genes_for_being(self, being: BaseBeing):
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
        beings = await BaseBeing.get_all()
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
            lux_being_from_db = await BaseBeing.load(lux_soul)
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
            lux_being = BaseBeing(
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
            function_being = await BaseBeing.create(
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
            task_being = await BaseBeing.create(
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

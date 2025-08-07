"""
Simplified LuxDB API - intuitive interface for developers
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from database.postgre_db import Postgre_db
from database.models.base import Soul, Being
from database.models.relationship import Relationship


class SimpleEntity:
    """Prosta encja - wszystko czego potrzebuje deweloper"""

    def __init__(self, id: str, name: str, data: dict, entity_type: str):
        self.id = id
        self.name = name
        self.data = data
        self.type = entity_type
        self._being = None  # Internal Being object

    async def update(self, new_data: dict):
        """Aktualizuje dane encji"""
        self.data.update(new_data)
        if self._being:
            for key, value in new_data.items():
                setattr(self._being, key, value)
            # Save to database
            await self._being.save(self._being._soul, new_data)

    async def connect_to(self, other_entity, relation_type: str = "connected"):
        """Łączy z inną encją"""
        await Relationship.create(
            source_id=self.id,
            target_id=other_entity.id,
            source_type="being",
            target_type="being",
            relation_type=relation_type
        )

    async def execute_gene(self, gene_name: str, *args, **kwargs):
        """Wykonuje gen (funkcję) na tym bycie"""
        if not self._being:
            return {"error": "No underlying being available"}

        try:
            # Sprawdź czy being ma ten gen
            genes = getattr(self._being, 'genes', {})
            if gene_name not in genes:
                return {"error": f"Gene '{gene_name}' not found in being"}

            gene_path = genes[gene_name]

            # Import modułu genów (dynamiczny)
            try:
                from genes import GeneRegistry
                gene_func = GeneRegistry.get_gene(gene_path)

                if not gene_func:
                    return {"error": f"Gene function not found: {gene_path}"}

                # Wykonaj gen
                if asyncio.iscoroutinefunction(gene_func):
                    result = await gene_func(self._being, *args, **kwargs)
                else:
                    result = gene_func(self._being, *args, **kwargs)

                return {"success": True, "result": result, "gene": gene_name}

            except ImportError:
                return {"error": "Genes module not available"}

        except Exception as e:
            return {"error": f"Gene execution failed: {str(e)}"}

    async def get_connections(self):
        """Zwraca wszystkie połączenia tej encji"""
        relationships = await Relationship.get_by_being(self.id)
        connections = []
        for rel in relationships:
            target_id = rel.target_id if rel.source_id == self.id else rel.source_id
            connections.append({
                'target_id': target_id,
                'relation_type': rel.relation_type,
                'strength': rel.strength
            })
        return connections

    def to_dict(self):
        """Standardowy format dla frontenda"""
        return {
            'id': self.id,
            'name': self.name,
            'data': self.data,
            'type': self.type
        }


class SimpleLuxDB:
    """Uproszczone API dla LuxDB - wszystko w jednym miejscu"""

    def __init__(self, db_config=None):
        self._entities = {}  # Cache entities
        self._initialized = False

    async def _ensure_initialized(self):
        """Upewnia się, że baza jest gotowa"""
        if not self._initialized:
            try:
                pool = await Postgre_db.get_db_pool()
                if pool:
                    self._initialized = True
                    print("✅ SimpleLuxDB ready!")
            except Exception as e:
                print(f"❌ SimpleLuxDB initialization error: {e}")

    async def create_entity(self, name: str, data: dict, entity_type: str = "entity"):
        """
        Tworzy nową encję - to wszystko czego potrzebuje deweloper

        Args:
            name: Nazwa encji
            data: Dane encji (dowolna struktura)
            entity_type: Typ encji (opcjonalnie)

        Returns:
            Encja z ID i wszystkimi potrzebnymi metodami
        """
        await self._ensure_initialized()

        try:
            # Automatycznie generuj genotyp na podstawie danych
            genotype = self._generate_genotype_from_data(data, entity_type, name)

            # Znajdź lub utwórz soul
            soul_alias = f"{entity_type}_{name}"
            existing_soul = await Soul.load_by_alias(soul_alias)

            if not existing_soul:
                soul = await Soul.create(genotype, soul_alias)
            else:
                soul = existing_soul

            # Utwórz being
            being_data = {"name": name, **data}
            being = await Being.create(soul, being_data)

            # Utwórz prostą encję
            entity = SimpleEntity(being.ulid, name, data, entity_type)
            entity._being = being
            entity._being._soul = soul

            # Cache entity
            self._entities[being.ulid] = entity

            print(f"✅ Created entity '{name}' ({entity_type}) with ID: {being.ulid}")
            return entity

        except Exception as e:
            print(f"❌ Error creating entity '{name}': {e}")
            # Zwróć prostą encję nawet przy błędzie
            fake_id = f"temp_{len(self._entities)}"
            entity = SimpleEntity(fake_id, name, data, entity_type)
            self._entities[fake_id] = entity
            return entity

    def _generate_genotype_from_data(self, data: dict, entity_type: str, name: str) -> dict:
        """Automatycznie generuje genotyp na podstawie danych"""
        attributes = {}

        # Dodaj standardowe pola
        attributes["name"] = {"py_type": "str"}

        # Analizuj dane i dodaj odpowiednie typy
        for key, value in data.items():
            if isinstance(value, str):
                attributes[key] = {"py_type": "str"}
            elif isinstance(value, int):
                attributes[key] = {"py_type": "int"}
            elif isinstance(value, float):
                attributes[key] = {"py_type": "float"}
            elif isinstance(value, bool):
                attributes[key] = {"py_type": "bool"}
            elif isinstance(value, list):
                if value and isinstance(value[0], str):
                    attributes[key] = {"py_type": "List[str]"}
                elif value and isinstance(value[0], (int, float)):
                    attributes[key] = {"py_type": "List[float]"}
                else:
                    attributes[key] = {"py_type": "dict"}  # Fallback to JSONB
            else:
                attributes[key] = {"py_type": "dict"}  # Store as JSONB

        return {
            "genesis": {
                "name": entity_type,
                "version": "1.0",
                "description": f"Auto-generated genotype for {name}"
            },
            "attributes": attributes
        }

    async def get_entity(self, entity_id: str):
        """Pobiera encję po ID"""
        if entity_id in self._entities:
            return self._entities[entity_id]

        try:
            # Spróbuj załadować z bazy
            beings = await Being.load_by_ulid(entity_id)
            if beings:
                being = beings[0] if isinstance(beings, list) else beings

                # Odtwórz atrybuty
                attributes = await being.get_attributes()

                entity = SimpleEntity(
                    being.ulid,
                    attributes.get('name', 'Unknown'),
                    attributes,
                    'entity'
                )
                entity._being = being
                self._entities[entity_id] = entity
                return entity

        except Exception as e:
            print(f"❌ Error loading entity {entity_id}: {e}")

        return None

    async def connect_entities(self, entity1_id: str, entity2_id: str, relation_type: str = "connected"):
        """Łączy dwie encje prostą relacją"""
        try:
            await Relationship.create(
                source_id=entity1_id,
                target_id=entity2_id,
                source_type="being",
                target_type="being",
                relation_type=relation_type
            )
            print(f"✅ Connected {entity1_id} -> {entity2_id} ({relation_type})")
            return True
        except Exception as e:
            print(f"❌ Error connecting entities: {e}")
            return False

    async def query_entities(self, filters: dict = None):
        """Wyszukuje encje według filtrów"""
        try:
            # Załaduj wszystkie beings
            beings = await Being.load_all()
            entities = []

            for being in beings:
                try:
                    attributes = await being.get_attributes()
                    entity = SimpleEntity(
                        being.ulid,
                        attributes.get('name', 'Unknown'),
                        attributes,
                        attributes.get('type', 'entity')
                    )
                    entity._being = being
                    entities.append(entity)
                    self._entities[being.ulid] = entity
                except Exception as e:
                    print(f"⚠️ Error processing being {being.ulid}: {e}")
                    continue

            return entities

        except Exception as e:
            print(f"❌ Error querying entities: {e}")
            return list(self._entities.values())

    async def get_graph_data(self):
        """Zwraca dane dla grafu w standardowym formacie"""
        try:
            # Pobierz wszystkie encje
            entities = await self.query_entities()

            # Pobierz wszystkie relacje
            relationships = await Relationship.get_all()

            # Format dla frontenda
            nodes = []
            links = []

            for entity in entities:
                nodes.append({
                    'id': entity.id,
                    'label': entity.name,
                    'type': entity.type,
                    'data': entity.data
                })

            for rel in relationships:
                links.append({
                    'source': rel.source_id,
                    'target': rel.target_id,
                    'relation_type': rel.relation_type,
                    'strength': rel.strength
                })

            return {
                'nodes': nodes,
                'links': links,
                'stats': {
                    'total_entities': len(entities),
                    'total_connections': len(relationships)
                }
            }

        except Exception as e:
            print(f"❌ Error getting graph data: {e}")
            return {
                'nodes': [],
                'links': [],
                'stats': {'total_entities': 0, 'total_connections': 0}
            }

    async def get_graph_data_async(self) -> Dict[str, Any]:
        """Async version of get_graph_data for better performance"""
        return self.get_graph_data()
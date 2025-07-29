
"""
Relation Manager Service
========================

Serwis zarządzający relacjami w systemie LuxDB.
Implementuje inteligentne uczenie się i optymalizację relacji.
"""

from typing import Dict, List, Any, Optional, Tuple
from database.models.relationship import Relationship, create_tag, create_directional, create_bidirectional
from datetime import datetime
import asyncio

class RelationManager:
    """Inteligentny menedżer relacji w LuxDB"""
    
    def __init__(self):
        self.relation_cache = {}  # Cache często używanych relacji
        self.learning_patterns = {}  # Wzorce uczenia się
        self.usage_statistics = {}  # Statystyki użycia
    
    async def create_smart_tag(self, source_uid: str, target_uid: str, 
                              tag_name: str, context: Dict[str, Any] = None) -> Relationship:
        """Tworzy inteligentną relację tagową"""
        
        # Sprawdź czy podobna relacja już istnieje
        existing_relations = await self._find_similar_relations(source_uid, target_uid, tag_name)
        
        if existing_relations:
            print(f"🔍 Znaleziono podobne relacje tagowe: {len(existing_relations)}")
            # Zwiększ usage_count dla istniejącej relacji
            best_relation = existing_relations[0]
            await best_relation.update_usage_stats(True)
            return best_relation
        
        # Generuj opis na podstawie kontekstu
        description = self._generate_tag_description(tag_name, context)
        
        # Utwórz nową relację
        relation = await create_tag(source_uid, target_uid, tag_name, description)
        
        # Dodaj do cache
        cache_key = f"{source_uid}:{target_uid}:{tag_name}"
        self.relation_cache[cache_key] = relation
        
        print(f"✅ Utworzono nową relację tagową: {tag_name} ({relation.hash_code})")
        return relation
    
    async def create_smart_directional(self, source_uid: str, target_uid: str,
                                     relation_name: str, perspective: str,
                                     context: Dict[str, Any] = None,
                                     bidirectional: bool = False) -> Relationship:
        """Tworzy inteligentną relację kierunkową"""
        
        # Sprawdź czy relacja ma sens w tym kontekście
        if await self._should_create_relation(source_uid, target_uid, relation_name, context):
            
            description = self._generate_relation_description(relation_name, perspective, context)
            
            if bidirectional:
                relation = await create_bidirectional(
                    source_uid, target_uid, relation_name, perspective, description
                )
                print(f"✅ Utworzono relację obustronną: {relation_name} ({relation.hash_code})")
            else:
                relation = await create_directional(
                    source_uid, target_uid, relation_name, perspective, description
                )
                print(f"✅ Utworzono relację kierunkową: {relation_name} ({relation.hash_code})")
            
            return relation
        else:
            print(f"⚠️ Relacja {relation_name} nie została utworzona - kontekst nieodpowiedni")
            return None
    
    def _generate_tag_description(self, tag_name: str, context: Dict[str, Any] = None) -> str:
        """Generuje opis dla relacji tagowej"""
        base_description = f"Relacja tagowa: {tag_name}"
        
        if context:
            if "domain" in context:
                base_description += f" w domenie {context['domain']}"
            if "purpose" in context:
                base_description += f" dla celu: {context['purpose']}"
            if "metadata" in context:
                base_description += f" z metadanymi: {context['metadata']}"
        
        return base_description
    
    def _generate_relation_description(self, relation_name: str, perspective: str, 
                                     context: Dict[str, Any] = None) -> str:
        """Generuje opis dla relacji kierunkowej"""
        base_description = f"Relacja {relation_name} z perspektywą {perspective}"
        
        if context:
            if "strength" in context:
                base_description += f" (siła: {context['strength']})"
            if "domain" in context:
                base_description += f" w domenie {context['domain']}"
            if "temporal" in context:
                base_description += f" w czasie: {context['temporal']}"
        
        return base_description
    
    async def _find_similar_relations(self, source_uid: str, target_uid: str, 
                                    tag_name: str) -> List[Relationship]:
        """Znajduje podobne relacje"""
        # TODO: Implementacja wyszukiwania w bazie
        return []
    
    async def _should_create_relation(self, source_uid: str, target_uid: str,
                                    relation_name: str, context: Dict[str, Any] = None) -> bool:
        """Decyduje czy relacja powinna zostać utworzona"""
        
        # Podstawowe sprawdzenia
        if source_uid == target_uid:
            return False  # Nie tworzy relacji do siebie
        
        # Sprawdź czy istnieją przeciwstawne relacje
        conflicting_relations = await self._check_conflicting_relations(
            source_uid, target_uid, relation_name
        )
        
        if conflicting_relations:
            print(f"⚠️ Znaleziono konfliktowe relacje dla {relation_name}")
            return False
        
        # Sprawdź kontekst
        if context and "force_create" in context:
            return context["force_create"]
        
        # Domyślnie pozwól na tworzenie
        return True
    
    async def _check_conflicting_relations(self, source_uid: str, target_uid: str,
                                         relation_name: str) -> List[Relationship]:
        """Sprawdza czy istnieją konfliktowe relacje"""
        # TODO: Implementacja sprawdzania konfliktów
        return []
    
    async def optimize_relations(self, entity_uid: str) -> Dict[str, Any]:
        """Optymalizuje relacje dla danego bytu"""
        optimization_results = {
            "optimized_count": 0,
            "removed_count": 0,
            "merged_count": 0,
            "strengthened_count": 0
        }
        
        # TODO: Implementacja optymalizacji
        # 1. Usuń nieużywane relacje
        # 2. Scal podobne relacje
        # 3. Wzmocnij często używane relacje
        # 4. Osłab rzadko używane relacje
        
        print(f"🔧 Optymalizacja relacji dla {entity_uid}: {optimization_results}")
        return optimization_results
    
    async def learn_from_interaction(self, source_uid: str, target_uid: str,
                                   interaction_type: str, success: bool,
                                   context: Dict[str, Any] = None):
        """Uczy się z interakcji między bytami"""
        
        # Znajdź relacje między bytami
        relations = await self._find_relations_between(source_uid, target_uid)
        
        for relation in relations:
            await relation.update_usage_stats(success)
            
            # Dodaj do wzorców uczenia
            pattern_key = f"{interaction_type}:{relation.relation_type}"
            if pattern_key not in self.learning_patterns:
                self.learning_patterns[pattern_key] = {
                    "success_count": 0,
                    "total_count": 0,
                    "contexts": []
                }
            
            self.learning_patterns[pattern_key]["total_count"] += 1
            if success:
                self.learning_patterns[pattern_key]["success_count"] += 1
            
            if context:
                self.learning_patterns[pattern_key]["contexts"].append(context)
        
        print(f"📚 Nauczono się z interakcji {interaction_type}: {success}")
    
    async def _find_relations_between(self, source_uid: str, target_uid: str) -> List[Relationship]:
        """Znajduje wszystkie relacje między dwoma bytami"""
        # TODO: Implementacja wyszukiwania
        return []
    
    async def suggest_relations(self, source_uid: str, target_uid: str,
                              context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Sugeruje potencjalne relacje między bytami"""
        suggestions = []
        
        # Analizuj wzorce uczenia
        for pattern_key, pattern_data in self.learning_patterns.items():
            if pattern_data["total_count"] > 5:  # Minimalny próg
                success_rate = pattern_data["success_count"] / pattern_data["total_count"]
                
                if success_rate > 0.7:  # Wysokia skuteczność
                    interaction_type, relation_type = pattern_key.split(":", 1)
                    
                    suggestions.append({
                        "relation_type": relation_type,
                        "interaction_type": interaction_type,
                        "success_rate": success_rate,
                        "confidence": min(pattern_data["total_count"] / 20, 1.0),
                        "reasoning": f"Wzorce wskazują na {success_rate:.2%} skuteczność"
                    })
        
        # Sortuj sugestie po skuteczności
        suggestions.sort(key=lambda x: x["success_rate"] * x["confidence"], reverse=True)
        
        print(f"💡 Wygenerowano {len(suggestions)} sugestii relacji")
        return suggestions[:5]  # Zwróć top 5
    
    async def get_relation_insights(self, entity_uid: str) -> Dict[str, Any]:
        """Zwraca insights o relacjach bytu"""
        insights = {
            "total_relations": 0,
            "most_used_relations": [],
            "success_patterns": [],
            "optimization_suggestions": []
        }
        
        # TODO: Implementacja analizy insights
        
        return insights

# Global instance
relation_manager = RelationManager()

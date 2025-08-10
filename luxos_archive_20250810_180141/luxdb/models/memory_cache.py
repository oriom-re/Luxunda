
"""
Model MemoryCache - pamięć podręczna istotnych wydarzeń i faktów
"""

import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import ulid

from ..core.globals import Globals
from .soul import Soul
from .relationship import Relationship

@dataclass
class MemoryCache:
    """
    MemoryCache przechowuje istotne wydarzenia, fakty i skróty myślowe.
    Każdy element pamięci jest połączony relacjami z konwersacjami i wątkami.
    """
    
    ulid: str = field(default_factory=lambda: str(ulid.ulid()))
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def create_memory(
        cls,
        memory_type: str,
        content: str,
        importance_level: float,
        context_ulids: List[str] = None,
        conversation_id: str = None,
        author_ulid: str = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> 'MemoryCache':
        """
        Tworzy nowy element pamięci.
        
        Args:
            memory_type: Typ pamięci (fact, event, insight, conclusion, etc.)
            content: Treść pamięci
            importance_level: Poziom ważności (0.0-1.0)
            context_ulids: Lista ULID powiązanych elementów
            conversation_id: ID konwersacji
            author_ulid: ULID autora/użytkownika
            tags: Tagi kategoryzujące
            metadata: Dodatkowe metadane
            
        Returns:
            Nowy obiekt MemoryCache
        """
        soul = await cls._get_or_create_memory_soul()
        
        memory = cls(
            ulid=str(ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype,
            alias=f"memory_{memory_type}_{datetime.now().strftime('%H%M%S')}"
        )
        
        # Zastosowanie genotypu
        memory._apply_genotype(soul.genotype)
        
        # Ustawienie danych pamięci
        memory_data = {
            "content": content,
            "memory_type": memory_type,
            "importance_level": importance_level,
            "conversation_id": conversation_id,
            "author_ulid": author_ulid,
            "tags": tags or [],
            "context_ulids": context_ulids or [],
            "created_timestamp": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        for key, value in memory_data.items():
            setattr(memory, key, value)
        
        # Zapis do bazy danych
        from ..repository.dynamic_repository import DynamicRepository
        await DynamicRepository.insert_data_transaction(memory, soul.genotype)
        
        # Tworzenie relacji kontekstowych
        await cls._create_memory_relationships(memory, context_ulids or [])
        
        return memory

    @classmethod
    async def _create_memory_relationships(
        cls,
        memory: 'MemoryCache',
        context_ulids: List[str]
    ):
        """Tworzy relacje między pamięcią a kontekstowymi elementami"""
        
        # Relacje do kontekstowych elementów
        for context_ulid in context_ulids:
            await Relationship.create(
                source_ulid=memory.ulid,
                target_ulid=context_ulid,
                relation_type="memory_context",
                strength=getattr(memory, 'importance_level', 0.5),
                metadata={
                    "memory_type": getattr(memory, 'memory_type', 'unknown'),
                    "created_at": datetime.now().isoformat(),
                    "relationship_type": "contextual"
                }
            )

    @classmethod
    async def get_relevant_memories(
        cls,
        conversation_id: str = None,
        author_ulid: str = None,
        tags: List[str] = None,
        min_importance: float = 0.3,
        time_limit_hours: int = 24,
        limit: int = 10
    ) -> List['MemoryCache']:
        """
        Pobiera istotne wspomnienia na podstawie kontekstu.
        
        Args:
            conversation_id: ID konwersacji
            author_ulid: ULID użytkownika
            tags: Tagi do filtrowania
            min_importance: Minimalny poziom ważności
            time_limit_hours: Limit czasowy w godzinach (0 = bez limitu)
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista istotnych wspomnień
        """
        # Implementacja uproszczona - w rzeczywistości używałbyś zapytań SQL
        from ..repository.being_repository import BeingRepository
        
        all_memories_result = await BeingRepository.load_all()
        if not all_memories_result.get('success'):
            return []
        
        memories = []
        time_cutoff = datetime.now() - timedelta(hours=time_limit_hours) if time_limit_hours > 0 else None
        
        for being_data in all_memories_result.get('beings', []):
            # Sprawdź czy to memory cache
            if not being_data.get('alias', '').startswith('memory_'):
                continue
            
            memory = cls.from_dict(being_data)
            
            # Filtry
            if conversation_id and getattr(memory, 'conversation_id', '') != conversation_id:
                continue
            
            if author_ulid and getattr(memory, 'author_ulid', '') != author_ulid:
                continue
            
            if min_importance and getattr(memory, 'importance_level', 0) < min_importance:
                continue
            
            if time_cutoff and memory.created_at and memory.created_at < time_cutoff:
                continue
            
            if tags:
                memory_tags = getattr(memory, 'tags', [])
                if not any(tag in memory_tags for tag in tags):
                    continue
            
            memories.append(memory)
        
        # Sortuj według ważności i czasu
        memories.sort(
            key=lambda m: (getattr(m, 'importance_level', 0), getattr(m, 'access_count', 0)), 
            reverse=True
        )
        
        return memories[:limit]

    @classmethod
    async def update_memory_access(cls, memory_ulid: str):
        """Aktualizuje statystyki dostępu do pamięci"""
        memory = await cls.load_by_ulid(memory_ulid)
        if memory:
            current_access_count = getattr(memory, 'access_count', 0)
            setattr(memory, 'access_count', current_access_count + 1)
            setattr(memory, 'last_accessed', datetime.now().isoformat())
            
            # Zapisz aktualizację (implementacja zależy od DynamicRepository)
            # await memory.save()

    @classmethod
    async def create_insight_from_conversation(
        cls,
        conversation_fragments: List[str],
        conversation_id: str,
        author_ulid: str = None
    ) -> Optional['MemoryCache']:
        """
        Tworzy wgląd/skrót myślowy z fragmentów konwersacji.
        """
        if not conversation_fragments:
            return None
        
        # Prosta heurystyka dla tworzenia insightów
        # W rzeczywistości można użyć AI do analizy
        combined_content = ' '.join(conversation_fragments)
        
        # Identyfikuj kluczowe tematy/fakty
        key_phrases = cls._extract_key_phrases(combined_content)
        
        if key_phrases:
            insight_content = f"Kluczowe punkty z rozmowy: {', '.join(key_phrases[:5])}"
            
            return await cls.create_memory(
                memory_type="insight",
                content=insight_content,
                importance_level=0.7,
                conversation_id=conversation_id,
                author_ulid=author_ulid,
                tags=["conversation_summary", "auto_generated"],
                metadata={
                    "source_fragments_count": len(conversation_fragments),
                    "key_phrases": key_phrases,
                    "auto_generated": True
                }
            )
        
        return None

    @classmethod
    def _extract_key_phrases(cls, text: str) -> List[str]:
        """Prosta ekstrakcja kluczowych fraz (można rozbudować o NLP)"""
        import re
        
        # Usuń słowa funkcyjne i znajdź istotne frazy
        words = re.findall(r'\b[a-ząćęłńóśźż]{3,}\b', text.lower())
        
        # Proste liczenie częstości
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Zwróć najczęstsze słowa
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]

    @classmethod
    async def get_conversation_summary(
        cls,
        conversation_id: str,
        author_ulid: str = None
    ) -> Dict[str, Any]:
        """Zwraca podsumowanie pamięci dla konwersacji"""
        memories = await cls.get_relevant_memories(
            conversation_id=conversation_id,
            author_ulid=author_ulid,
            limit=20
        )
        
        summary = {
            "total_memories": len(memories),
            "memory_types": {},
            "key_insights": [],
            "important_facts": [],
            "recent_events": []
        }
        
        for memory in memories:
            memory_type = getattr(memory, 'memory_type', 'unknown')
            summary["memory_types"][memory_type] = summary["memory_types"].get(memory_type, 0) + 1
            
            importance = getattr(memory, 'importance_level', 0)
            content = getattr(memory, 'content', '')
            
            if memory_type == "insight" and importance > 0.6:
                summary["key_insights"].append(content)
            elif memory_type == "fact" and importance > 0.7:
                summary["important_facts"].append(content)
            elif memory_type == "event":
                summary["recent_events"].append({
                    "content": content,
                    "timestamp": getattr(memory, 'created_timestamp', '')
                })
        
        return summary

    def _apply_genotype(self, genotype: dict):
        """Dynamicznie dodaje pola z genotypu do obiektu MemoryCache"""
        from dataclasses import make_dataclass, field
        
        fields = []
        type_map = {
            "str": str, 
            "int": int, 
            "bool": bool, 
            "float": float, 
            "dict": dict, 
            "List[str]": list, 
            "List[float]": list
        }

        attributes = genotype.get("attributes", {})
        for name, meta in attributes.items():
            type_name = meta.get("py_type", "str")
            py_type = type_map.get(type_name, str)
            fields.append((name, py_type, field(default=None)))

        if fields:
            DynamicMemoryCache = make_dataclass(
                cls_name="DynamicMemoryCache",
                fields=fields,
                bases=(self.__class__,),
                frozen=False
            )
            self.__class__ = DynamicMemoryCache

    @classmethod
    async def _get_or_create_memory_soul(cls) -> Soul:
        """Pobiera lub tworzy Soul dla pamięci podręcznej"""
        try:
            soul = await Soul.load_by_alias("memory_cache")
            if soul:
                return soul
        except:
            pass
        
        # Utwórz nowy soul
        memory_genotype = {
            "genesis": {
                "name": "memory_cache",
                "type": "memory",
                "doc": "Pamięć podręczna istotnych wydarzeń i faktów"
            },
            "attributes": {
                "content": {"py_type": "str", "table_name": "_text"},
                "memory_type": {"py_type": "str", "table_name": "_text"},
                "importance_level": {"py_type": "float", "table_name": "_numeric"},
                "conversation_id": {"py_type": "str", "table_name": "_text"},
                "author_ulid": {"py_type": "str", "table_name": "_text"},
                "tags": {"py_type": "List[str]", "table_name": "_jsonb"},
                "context_ulids": {"py_type": "List[str]", "table_name": "_jsonb"},
                "created_timestamp": {"py_type": "str", "table_name": "_text"},
                "access_count": {"py_type": "int", "table_name": "_numeric"},
                "last_accessed": {"py_type": "str", "table_name": "_text"},
                "metadata": {"py_type": "dict", "table_name": "_jsonb"}
            }
        }
        
        return await Soul.create(memory_genotype, alias="memory_cache")

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> Optional['MemoryCache']:
        """Ładuje MemoryCache po ULID"""
        from ..repository.being_repository import BeingRepository
        
        result = await BeingRepository.load_by_ulid(ulid)
        return result.get('being') if result.get('success') else None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryCache':
        """Tworzy MemoryCache z słownika"""
        memory = cls(
            ulid=data.get('ulid', str(ulid.ulid())),
            soul_hash=data.get('soul_hash'),
            alias=data.get('alias'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            genotype=data.get('genotype', {})
        )
        
        # Zastosuj dodatkowe pola
        for key, value in data.items():
            if key not in ['ulid', 'soul_hash', 'alias', 'created_at', 'updated_at', 'genotype']:
                setattr(memory, key, value)
        
        return memory

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje MemoryCache do słownika"""
        from dataclasses import asdict
        result = asdict(self)
        
        # Dodaj dodatkowe pola jeśli istnieją
        for attr in ['content', 'memory_type', 'importance_level', 'tags', 'context_ulids']:
            if hasattr(self, attr):
                result[attr] = getattr(self, attr)
        
        return result

    def __repr__(self):
        content_preview = getattr(self, 'content', '')[:50] + "..." if len(getattr(self, 'content', '')) > 50 else getattr(self, 'content', '')
        memory_type = getattr(self, 'memory_type', 'unknown')
        importance = getattr(self, 'importance_level', 0)
        return f"MemoryCache({memory_type}:{importance:.2f}: {content_preview})"

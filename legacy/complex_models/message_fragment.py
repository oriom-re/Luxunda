
"""
Model MessageFragment - fragmenty wiadomości połączone relacjami
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import ulid
import re

from ..core.globals import Globals
from .soul import Soul
from .relationship import Relationship

@dataclass
class MessageFragment:
    """
    MessageFragment reprezentuje pojedynczy fragment wiadomości (zdanie, paragraf).
    Fragmenty są połączone relacjami, co pozwala na odtworzenie całego kontekstu.
    """
    
    ulid: str = field(default_factory=lambda: str(ulid.ulid()))
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def create_from_message(
        cls, 
        message_content: str, 
        message_ulid: str,
        author_ulid: Optional[str] = None,
        fingerprint: str = None,
        conversation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> List['MessageFragment']:
        """
        Tworzy fragmenty z wiadomości i łączy je relacjami.
        
        Args:
            message_content: Treść wiadomości do fragmentacji
            message_ulid: ULID nadrzędnej wiadomości
            author_ulid: ULID autora
            fingerprint: Browser fingerprint
            conversation_id: ID konwersacji
            metadata: Dodatkowe metadane
            
        Returns:
            Lista fragmentów połączonych relacjami
        """
        # Pobierz lub utwórz Soul dla fragmentu
        soul = await cls._get_or_create_fragment_soul()
        
        # Fragmentacja wiadomości
        fragments_data = cls._fragment_message(message_content)
        created_fragments = []
        
        for i, fragment_data in enumerate(fragments_data):
            fragment = cls(
                ulid=str(ulid.ulid()),
                soul_hash=soul.soul_hash,
                genotype=soul.genotype,
                alias=f"fragment_{message_ulid[:8]}_{i}"
            )
            
            # Zastosowanie genotypu
            fragment._apply_genotype(soul.genotype)
            
            # Ustawienie danych fragmentu
            fragment_metadata = {
                **(metadata or {}),
                "parent_message_ulid": message_ulid,
                "fragment_index": i,
                "fragment_type": fragment_data["type"],
                "total_fragments": len(fragments_data)
            }
            
            for key, value in {
                "content": fragment_data["content"],
                "fragment_type": fragment_data["type"],
                "word_count": fragment_data["word_count"],
                "author_ulid": author_ulid,
                "fingerprint": fingerprint,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "metadata": fragment_metadata
            }.items():
                setattr(fragment, key, value)
            
            # Zapis do bazy danych
            from ..repository.dynamic_repository import DynamicRepository
            await DynamicRepository.insert_data_transaction(fragment, soul.genotype)
            
            created_fragments.append(fragment)
        
        # Tworzenie relacji między fragmentami
        await cls._create_fragment_relationships(created_fragments, message_ulid)
        
        return created_fragments

    @classmethod
    def _fragment_message(cls, content: str) -> List[Dict[str, Any]]:
        """Fragmentuje wiadomość na paragrafy i zdania"""
        fragments = []
        
        # Podział na paragrafy
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        for para_idx, paragraph in enumerate(paragraphs):
            if len(paragraph) > 200:  # Długie paragrafy dziel na zdania
                sentences = re.split(r'[.!?]+', paragraph)
                for sent_idx, sentence in enumerate(sentences):
                    sentence = sentence.strip()
                    if sentence:
                        fragments.append({
                            "content": sentence,
                            "type": "sentence",
                            "word_count": len(sentence.split()),
                            "paragraph_index": para_idx,
                            "sentence_index": sent_idx
                        })
            else:
                fragments.append({
                    "content": paragraph,
                    "type": "paragraph", 
                    "word_count": len(paragraph.split()),
                    "paragraph_index": para_idx,
                    "sentence_index": 0
                })
        
        return fragments

    @classmethod
    async def _create_fragment_relationships(
        cls, 
        fragments: List['MessageFragment'], 
        message_ulid: str
    ):
        """Tworzy relacje między fragmentami wiadomości"""
        
        # Relacje między sąsiednimi fragmentami (sequence)
        for i in range(len(fragments) - 1):
            await Relationship.create(
                source_ulid=fragments[i].ulid,
                target_ulid=fragments[i + 1].ulid,
                relation_type="sequence_next",
                strength=1.0,
                metadata={
                    "sequence_order": i,
                    "parent_message": message_ulid,
                    "relationship_type": "structural"
                }
            )
        
        # Relacja do nadrzędnej wiadomości
        for fragment in fragments:
            await Relationship.create(
                source_ulid=message_ulid,
                target_ulid=fragment.ulid,
                relation_type="contains_fragment",
                strength=1.0,
                metadata={
                    "fragment_type": getattr(fragment, 'fragment_type', 'unknown'),
                    "relationship_type": "containment"
                }
            )

    @classmethod
    async def get_message_fragments(cls, message_ulid: str) -> List['MessageFragment']:
        """Pobiera wszystkie fragmenty dla danej wiadomości"""
        # Znajdź relacje "contains_fragment"
        relationships = await Relationship.get_all()
        fragment_ulids = []
        
        for rel in relationships:
            if (rel.source_ulid == message_ulid and 
                rel.relation_type == "contains_fragment"):
                fragment_ulids.append(rel.target_ulid)
        
        # Pobierz fragmenty
        fragments = []
        for fragment_ulid in fragment_ulids:
            fragment = await cls.load_by_ulid(fragment_ulid)
            if fragment:
                fragments.append(fragment)
        
        # Sortuj według indeksu fragmentu
        fragments.sort(key=lambda f: getattr(f, 'metadata', {}).get('fragment_index', 0))
        
        return fragments

    @classmethod
    async def find_related_fragments(
        cls, 
        fragment_ulid: str, 
        relation_types: List[str] = None
    ) -> List['MessageFragment']:
        """Znajduje fragmenty powiązane z danym fragmentem"""
        if not relation_types:
            relation_types = ["sequence_next", "semantic_similarity", "contextual_reference"]
        
        relationships = await Relationship.get_all()
        related_ulids = []
        
        for rel in relationships:
            if (rel.source_ulid == fragment_ulid and 
                rel.relation_type in relation_types):
                related_ulids.append(rel.target_ulid)
            elif (rel.target_ulid == fragment_ulid and 
                  rel.relation_type in relation_types):
                related_ulids.append(rel.source_ulid)
        
        # Pobierz powiązane fragmenty
        related_fragments = []
        for related_ulid in related_ulids:
            fragment = await cls.load_by_ulid(related_ulid)
            if fragment:
                related_fragments.append(fragment)
        
        return related_fragments

    @classmethod
    async def reconstruct_full_context(cls, fragment_ulid: str) -> str:
        """Odtwarza pełny kontekst dla danego fragmentu"""
        fragment = await cls.load_by_ulid(fragment_ulid)
        if not fragment:
            return ""
        
        # Pobierz wiadomość nadrzędną
        parent_message_ulid = getattr(fragment, 'metadata', {}).get('parent_message_ulid')
        if not parent_message_ulid:
            return getattr(fragment, 'content', '')
        
        # Pobierz wszystkie fragmenty wiadomości
        all_fragments = await cls.get_message_fragments(parent_message_ulid)
        
        # Zrekonstruuj pełną wiadomość
        full_content = []
        for frag in all_fragments:
            content = getattr(frag, 'content', '')
            if content:
                full_content.append(content)
        
        return ' '.join(full_content)

    def _apply_genotype(self, genotype: dict):
        """Dynamicznie dodaje pola z genotypu do obiektu MessageFragment"""
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
            DynamicMessageFragment = make_dataclass(
                cls_name="DynamicMessageFragment",
                fields=fields,
                bases=(self.__class__,),
                frozen=False
            )
            self.__class__ = DynamicMessageFragment

    @classmethod
    async def _get_or_create_fragment_soul(cls) -> Soul:
        """Pobiera lub tworzy Soul dla fragmentu wiadomości"""
        try:
            soul = await Soul.load_by_alias("message_fragment")
            if soul:
                return soul
        except:
            pass
        
        # Utwórz nowy soul
        fragment_genotype = {
            "genesis": {
                "name": "message_fragment",
                "type": "fragment",
                "doc": "Fragment wiadomości z relacjami strukturalnymi"
            },
            "attributes": {
                "content": {"py_type": "str", "table_name": "_text"},
                "fragment_type": {"py_type": "str", "table_name": "_text"},
                "word_count": {"py_type": "int", "table_name": "_numeric"},
                "author_ulid": {"py_type": "str", "table_name": "_text"},
                "fingerprint": {"py_type": "str", "table_name": "_text"},
                "conversation_id": {"py_type": "str", "table_name": "_text"},
                "timestamp": {"py_type": "str", "table_name": "_text"},
                "metadata": {"py_type": "dict", "table_name": "_jsonb"}
            }
        }
        
        return await Soul.create(fragment_genotype, alias="message_fragment")

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> Optional['MessageFragment']:
        """Ładuje MessageFragment po ULID"""
        from ..repository.being_repository import BeingRepository
        
        result = await BeingRepository.load_by_ulid(ulid)
        return result.get('being') if result.get('success') else None

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje MessageFragment do słownika"""
        from dataclasses import asdict
        result = asdict(self)
        
        # Dodaj dodatkowe pola jeśli istnieją
        for attr in ['content', 'fragment_type', 'word_count', 'author_ulid', 'fingerprint', 'timestamp']:
            if hasattr(self, attr):
                result[attr] = getattr(self, attr)
        
        return result

    def __repr__(self):
        content_preview = getattr(self, 'content', '')[:50] + "..." if len(getattr(self, 'content', '')) > 50 else getattr(self, 'content', '')
        fragment_type = getattr(self, 'fragment_type', 'unknown')
        return f"MessageFragment({fragment_type}: {content_preview})"

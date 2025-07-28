from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import uuid


@dataclass
class Relationship:
    """Klasa reprezentująca relacje między bytami"""
    
    uid: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unikalny identyfikator relacji
    global_uid: str = field(default_factory=lambda: str(uuid.uuid4()))  # Global

    alias: str = None  # Alias dla relacji
    
    genotype_hex: str = None
    genotype: Dict[str, Any] = field(default_factory=dict)

    source_uid: str
    target_uid: str

    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None # Data zapisu bytu w bazie danych

    def __post_init__(self):
        if "created_at" not in self.genotype:
            self.attributes["created_at"] = self.created_at.isoformat()
    
    @classmethod
    async def create(cls, source_uid: str, target_uid: str, attributes: Dict[str, Any] = None):
        """Tworzy nową relację między bytami"""
        from app_v2.database.soul_repository import RelationshipRepository
        relationship_data = {
            "uid": str(uuid.uuid4()),
            "source_uid": source_uid,
            "target_uid": target_uid,
            "attributes": attributes or {},
            "created_at": datetime.now().isoformat()
        }
        return await RelationshipRepository.save(relationship_data)
    
    @classmethod
    async def create_after(source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'after' dla bytu"""
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'after'
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )
    
    @classmethod
    async def create_before(source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'before' dla bytu"""
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'before'
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )
    
    @classmethod
    async def create_from_author(source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'from_author' dla bytu"""
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'from_author'
        attributes['being'] = 'author'
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )   
    
    @classmethod
    async def create_from_message(source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'from_message' dla bytu"""
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'from_message'
        attributes['being'] = 'message'
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )
    
    @classmethod
    async def create_from_thread(source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'from_thread' dla bytu"""
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'from_thread'
        attributes['being'] = 'thread'
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )

    @classmethod
    async def create_from(being:str, source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'from' dla bytu """
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'from'
        attributes['being'] = being
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )
    
    @classmethod
    async def create_to(being:str, source_uid: str, target_uid: str, **kwargs) -> 'Relationship':
        """Tworzy relację 'to' dla bytu """
        attributes = kwargs.get('attributes', {})
        attributes['type'] = 'to'
        attributes['being'] = being
        return await Relationship.create(
            source_uid=source_uid,
            target_uid=target_uid,
            attributes= attributes
        )



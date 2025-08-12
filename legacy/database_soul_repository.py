
"""
Legacy soul repository implementation - moved to legacy folder
"""

from database.soul_repository import SoulRepository as CurrentSoulRepository
from database.soul_repository import BeingRepository as CurrentBeingRepository
from database.soul_repository import RelationRepository as CurrentRelationRepository

# Legacy compatibility classes
class SoulRepository:
    """Legacy wrapper - use database.soul_repository.SoulRepository instead"""
    
    @staticmethod
    async def load_by_alias(alias: str):
        return await CurrentSoulRepository.load_by_alias(alias)
    
    @staticmethod
    async def load_by_hash(hash: str):
        return await CurrentSoulRepository.load_by_hash(hash)
    
    @staticmethod 
    async def get_all():
        return await CurrentSoulRepository.get_all()

class BeingRepository:
    """Legacy wrapper - use database.soul_repository.BeingRepository instead"""
    
    @staticmethod
    async def save_jsonb(being):
        return await CurrentBeingRepository.save_jsonb(being)
    
    @staticmethod
    async def load_by_ulid(ulid: str):
        return await CurrentBeingRepository.load_by_ulid(ulid)
    
    @staticmethod
    async def get_all():
        return await CurrentBeingRepository.get_all()

class RelationRepository:
    """Legacy wrapper - use database.soul_repository.RelationRepository instead"""
    
    @staticmethod
    async def save(relation):
        return await CurrentRelationRepository.save(relation)
    
    @staticmethod
    async def load_by_ulid(ulid: str):
        return await CurrentRelationRepository.load_by_ulid(ulid)

print("⚠️ Using legacy soul_repository wrapper - migrate to database.soul_repository")


#!/usr/bin/env python3
"""
🔗 Relationships Manager - Zarządzanie relacjami między bytami
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import ulid as _ulid
from luxdb.core.postgre_db import Postgre_db

class RelationshipsManager:
    """Manager do zarządzania relacjami między bytami w prywatnej tabeli"""
    
    @staticmethod
    async def create_relationship(
        source_ulid: str,
        target_ulid: str,
        relation_type: str = "connection",
        strength: float = 1.0,
        metadata: Dict[str, Any] = None,
        observer_context: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        expires_hours: int = None
    ) -> Dict[str, Any]:
        """
        Tworzy nową relację między bytami
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                relationship_ulid = str(_ulid.ulid())
                expires_at = None
                
                if expires_hours:
                    expires_at = datetime.now() + timedelta(hours=expires_hours)
                
                query = """
                    INSERT INTO relationships 
                    (ulid, source_ulid, target_ulid, relation_type, strength, 
                     metadata, observer_context, data, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id, ulid, created_at
                """
                
                result = await conn.fetchrow(query,
                    relationship_ulid,
                    source_ulid,
                    target_ulid,
                    relation_type,
                    strength,
                    metadata or {},
                    observer_context or {},
                    data or {},
                    expires_at
                )
                
                return {
                    "success": True,
                    "relationship": {
                        "id": str(result["id"]),
                        "ulid": result["ulid"],
                        "source_ulid": source_ulid,
                        "target_ulid": target_ulid,
                        "relation_type": relation_type,
                        "strength": strength,
                        "created_at": result["created_at"].isoformat()
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create relationship: {e}"
            }

    @staticmethod
    async def get_relationships_for_being(ulid: str, as_source: bool = True, as_target: bool = True) -> List[Dict[str, Any]]:
        """
        Pobiera wszystkie relacje dla danego bytu
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                conditions = []
                params = [ulid]
                
                if as_source and as_target:
                    conditions.append("(source_ulid = $1 OR target_ulid = $1)")
                elif as_source:
                    conditions.append("source_ulid = $1")
                elif as_target:
                    conditions.append("target_ulid = $1")
                
                # Filtruj nieaktywne (wygasłe)
                conditions.append("(expires_at IS NULL OR expires_at > NOW())")
                
                query = f"""
                    SELECT * FROM relationships 
                    WHERE {" AND ".join(conditions)}
                    ORDER BY created_at DESC
                """
                
                rows = await conn.fetch(query, *params)
                
                relationships = []
                for row in rows:
                    relationships.append({
                        "id": str(row["id"]),
                        "ulid": row["ulid"],
                        "source_ulid": row["source_ulid"],
                        "target_ulid": row["target_ulid"],
                        "relation_type": row["relation_type"],
                        "strength": row["strength"],
                        "metadata": row["metadata"],
                        "observer_context": row["observer_context"],
                        "data": row["data"],
                        "created_at": row["created_at"].isoformat(),
                        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                        "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None
                    })
                
                return relationships
                
        except Exception as e:
            print(f"❌ Error getting relationships: {e}")
            return []

    @staticmethod
    async def update_relationship_strength(ulid: str, new_strength: float) -> Dict[str, Any]:
        """
        Aktualizuje siłę relacji
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    UPDATE relationships 
                    SET strength = $2, updated_at = NOW()
                    WHERE ulid = $1
                    RETURNING ulid, strength
                """
                
                result = await conn.fetchrow(query, ulid, new_strength)
                
                if result:
                    return {
                        "success": True,
                        "relationship_ulid": result["ulid"],
                        "new_strength": result["strength"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Relationship not found"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update relationship: {e}"
            }

    @staticmethod
    async def delete_relationship(ulid: str) -> Dict[str, Any]:
        """
        Usuwa relację
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = "DELETE FROM relationships WHERE ulid = $1 RETURNING ulid"
                result = await conn.fetchrow(query, ulid)
                
                if result:
                    return {
                        "success": True,
                        "deleted_ulid": result["ulid"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Relationship not found"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete relationship: {e}"
            }

    @staticmethod
    async def cleanup_expired_relationships() -> Dict[str, Any]:
        """
        Usuwa wygasłe relacje
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    DELETE FROM relationships 
                    WHERE expires_at IS NOT NULL AND expires_at <= NOW()
                    RETURNING COUNT(*)
                """
                
                result = await conn.fetchval(query)
                
                return {
                    "success": True,
                    "deleted_count": result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to cleanup relationships: {e}"
            }

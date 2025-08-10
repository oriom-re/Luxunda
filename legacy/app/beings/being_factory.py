from typing import Dict, Any, Optional
import uuid
import json


# Import db_pool from database module
from app.database import get_db_pool
from app.beings.function_being import FunctionBeing
from app.beings.base import Being
from app.beings.class_being import ClassBeing
from app.beings.data_being import DataBeing
from app.beings.scenario_being import ScenarioBeing
from app.beings.task_being import TaskBeing
from app.beings.component_being import ComponentBeing
from app.beings.message_being import MessageBeing


class BeingFactory:
    """Factory do tworzenia różnych typów bytów"""
    
    BEING_TYPES = {
        'function': FunctionBeing,
        'class': ClassBeing,
        'data': DataBeing,
        'scenario': ScenarioBeing,
        'task': TaskBeing,
        'component': ComponentBeing,
        'message': MessageBeing,
        'base': Being
    }
    
    @classmethod
    async def create_being(cls, being_type: str, genesis: Dict[str, Any], **kwargs) -> Being:
        """Tworzy byt odpowiedniego typu"""
        BeingClass = cls.BEING_TYPES.get(being_type, Being)
        
        # Upewnij się, że typ jest ustawiony w genesis
        genesis['type'] = being_type
        
        # Generuj unikalne soul
        soul = str(uuid.uuid4())
        
        # Przygotuj atrybuty
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']
        
        # Utwórz byt
        being = BeingClass(
            soul=soul,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )
        
        await being.save()
        return being
    
    @classmethod
    async def load_being(cls, soul: str) -> Optional[Being]:
        """Ładuje byt odpowiedniego typu z bazy danych"""
        db_pool = await get_db_pool()
        
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
        else:
            async with db_pool.execute("SELECT * FROM base_beings WHERE soul = ?", (soul,)) as cursor:
                row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Określ typ bytu
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            genesis = row['genesis']
            being_type = genesis.get('type', 'base')
        else:
            # SQLite
            genesis = json.loads(row[3]) if row[3] else {}
            being_type = genesis.get('type', 'base')
        
        # Wybierz odpowiednią klasę
        BeingClass = cls.BEING_TYPES.get(being_type, Being)
        
        # Utwórz instancję
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            return BeingClass(
                soul=str(row['soul']),
                genesis=row['genesis'],
                attributes=row['attributes'],
                memories=row['memories'],
                self_awareness=row['self_awareness'],
                created_at=row['created_at']
            )
        else:
            # SQLite
            attributes = json.loads(row[4]) if row[4] else {}
            memories = json.loads(row[5]) if row[5] else []
            self_awareness = json.loads(row[6]) if row[6] else {}
            
            return BeingClass(
                soul=row[0],
                genesis=genesis,
                attributes=attributes,
                memories=memories,
                self_awareness=self_awareness,
                created_at=row[7]
            )
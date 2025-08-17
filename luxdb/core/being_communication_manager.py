
#!/usr/bin/env python3
"""
🔄 Being Communication Manager - Komunikacja z automatycznym budzeniem
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import ulid as _ulid
from luxdb.core.postgre_db import Postgre_db

class BeingCommunicationManager:
    """Manager komunikacji między bytami z automatycznym budzeniem"""
    
    # Rejestr aktywnych bytów w pamięci
    _active_beings: Dict[str, Any] = {}
    _communication_queue: List[Dict[str, Any]] = []
    
    @staticmethod
    async def send_intention_to_being(
        source_ulid: str,
        target_ulid: str, 
        intention_type: str,
        content: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Wysyła intencję do konkretnego bytu (po ULID).
        Automatycznie budzi byt jeśli śpi.
        """
        try:
            # Sprawdź czy target jest aktywny
            if target_ulid in BeingCommunicationManager._active_beings:
                # Komunikacja bezpośrednia
                return await BeingCommunicationManager._direct_communication(
                    source_ulid, target_ulid, intention_type, content, data
                )
            else:
                # Byt śpi - musi być wybudzony przez dispenser
                return await BeingCommunicationManager._wake_and_communicate(
                    source_ulid, target_ulid, intention_type, content, data
                )
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Communication failed: {e}",
                "source_ulid": source_ulid,
                "target_ulid": target_ulid
            }

    @staticmethod
    async def _direct_communication(
        source_ulid: str,
        target_ulid: str,
        intention_type: str, 
        content: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Bezpośrednia komunikacja z aktywnym bytem"""
        active_being = BeingCommunicationManager._active_beings[target_ulid]
        
        message = {
            "message_id": str(_ulid.ulid()),
            "source_ulid": source_ulid,
            "target_ulid": target_ulid,
            "intention_type": intention_type,
            "content": content,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "communication_type": "direct"
        }
        
        # Wyślij message do aktywnego bytu
        if hasattr(active_being, 'receive_intention'):
            response = await active_being.receive_intention(message)
            return {
                "success": True,
                "communication_type": "direct",
                "response": response,
                "message": message
            }
        else:
            return {
                "success": False,
                "error": "Target being doesn't support receive_intention",
                "communication_type": "direct_failed"
            }

    @staticmethod
    async def _wake_and_communicate(
        source_ulid: str,
        target_ulid: str,
        intention_type: str,
        content: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Budzi śpiący byt i wysyła komunikat przez dispenser"""
        
        # Stwórz task dla dispenser'a
        wake_task = {
            "task_id": str(_ulid.ulid()),
            "task_type": "wake_and_communicate",
            "source_ulid": source_ulid,
            "target_ulid": target_ulid,
            "intention": {
                "type": intention_type,
                "content": content,
                "data": data or {}
            },
            "created_at": datetime.now().isoformat(),
            "priority": "normal"
        }
        
        # Dodaj do queue dispenser'a
        BeingCommunicationManager._communication_queue.append(wake_task)
        
        # Powiadom dispenser o nowym task'u
        await BeingCommunicationManager._notify_dispenser(wake_task)
        
        return {
            "success": True,
            "communication_type": "wake_and_communicate",
            "task_id": wake_task["task_id"],
            "status": "queued_for_waking",
            "message": "Target being will be awakened by dispenser"
        }

    @staticmethod
    async def _notify_dispenser(task: Dict[str, Any]):
        """Powiadamia dispenser'a o nowym task'u budzenia"""
        try:
            # Zapisz task do bazy danych dla dispenser'a
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO communication_tasks 
                    (task_id, task_type, source_ulid, target_ulid, task_data, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """
                await conn.execute(query,
                    task["task_id"],
                    task["task_type"], 
                    task["source_ulid"],
                    task["target_ulid"],
                    task,
                    datetime.now()
                )
                
                # Wyślij notification przez PostgreSQL NOTIFY
                await conn.execute(
                    "NOTIFY communication_channel, $1", 
                    task["task_id"]
                )
                
        except Exception as e:
            print(f"❌ Failed to notify dispenser: {e}")

    @staticmethod
    async def register_active_being(ulid: str, being_instance: Any):
        """Rejestruje byt jako aktywny w systemie"""
        BeingCommunicationManager._active_beings[ulid] = being_instance
        print(f"✅ Being {ulid} registered as active")

    @staticmethod
    async def unregister_being(ulid: str):
        """Usuwa byt z rejestru aktywnych"""
        if ulid in BeingCommunicationManager._active_beings:
            del BeingCommunicationManager._active_beings[ulid]
            print(f"🛑 Being {ulid} unregistered (sleeping)")

    @staticmethod
    def get_active_beings() -> List[str]:
        """Zwraca listę aktywnych bytów (ULID)"""
        return list(BeingCommunicationManager._active_beings.keys())

    @staticmethod
    async def wake_being_by_ulid(target_ulid: str) -> Dict[str, Any]:
        """Budzi konkretny byt po ULID"""
        try:
            # Załaduj byt z bazy danych
            from luxdb.repository.soul_repository import BeingRepository
            result = await BeingRepository.get_by_ulid(target_ulid)
            
            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Being {target_ulid} not found in database"
                }
            
            being = result["being"]
            
            # Rejestruj jako aktywny
            await BeingCommunicationManager.register_active_being(target_ulid, being)
            
            # Wywołaj init() jeśli byt ma tę funkcję
            if hasattr(being, 'init'):
                await being.init()
            
            return {
                "success": True,
                "ulid": target_ulid,
                "status": "awakened_and_active",
                "being": being
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to wake being {target_ulid}: {e}"
            }

class CommunicationDispenser:
    """Dispenser odpowiedzialny za budzenie bytów i dostarczanie komunikatów"""
    
    def __init__(self):
        self.active = True
        
    async def start_listening(self):
        """Uruchamia nasłuchiwanie na communication_channel"""
        pool = await Postgre_db.get_db_pool()
        async with pool.acquire() as conn:
            await conn.execute("LISTEN communication_channel")
            await conn.add_listener("communication_channel", self.on_communication_task)
            
            print("🔔 Communication Dispenser listening for wake tasks...")
            
            while self.active:
                await asyncio.sleep(1)  # Keep listening

    async def on_communication_task(self, connection, pid, channel, payload):
        """Obsługuje nowe task'i komunikacyjne"""
        task_id = payload
        
        try:
            # Pobierz szczegóły task'a z bazy
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM communication_tasks 
                    WHERE task_id = $1 AND processed = false
                """
                task_row = await conn.fetchrow(query, task_id)
                
                if not task_row:
                    return
                
                task_data = task_row["task_data"]
                
                if task_data["task_type"] == "wake_and_communicate":
                    await self._handle_wake_and_communicate(task_data)
                
                # Oznacz jako processed
                await conn.execute(
                    "UPDATE communication_tasks SET processed = true WHERE task_id = $1",
                    task_id
                )
                
        except Exception as e:
            print(f"❌ Error processing communication task {task_id}: {e}")

    async def _handle_wake_and_communicate(self, task_data: Dict[str, Any]):
        """Budzi byt i przekazuje mu komunikat"""
        target_ulid = task_data["target_ulid"]
        
        # Wybudź byt
        wake_result = await BeingCommunicationManager.wake_being_by_ulid(target_ulid)
        
        if wake_result["success"]:
            # Wyślij komunikat do wybudzonego bytu
            await BeingCommunicationManager._direct_communication(
                task_data["source_ulid"],
                task_data["target_ulid"],
                task_data["intention"]["type"],
                task_data["intention"]["content"],
                task_data["intention"]["data"]
            )
            
            print(f"✅ Successfully awakened and communicated with {target_ulid}")
        else:
            print(f"❌ Failed to wake {target_ulid}: {wake_result['error']}")

# Inicjalizacja globalnego dispenser'a
communication_dispenser = CommunicationDispenser()

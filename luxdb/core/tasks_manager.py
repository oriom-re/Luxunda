
#!/usr/bin/env python3
"""
📋 Tasks Manager - Zarządzanie zadaniami w prywatnej tabeli
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import ulid as _ulid
from luxdb.core.postgre_db import Postgre_db

class TasksManager:
    """Manager do zarządzania zadaniami w prywatnej tabeli"""
    
    @staticmethod
    async def create_task(
        task_type: str,
        payload: Dict[str, Any],
        source_ulid: str = None,
        target_ulid: str = None,
        priority: int = 5,
        scheduled_at: datetime = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Tworzy nowe zadanie
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                task_id = str(_ulid.ulid())
                
                if scheduled_at is None:
                    scheduled_at = datetime.now()
                
                query = """
                    INSERT INTO tasks 
                    (task_id, task_type, source_ulid, target_ulid, payload, 
                     priority, scheduled_at, max_retries)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id, task_id, created_at
                """
                
                result = await conn.fetchrow(query,
                    task_id,
                    task_type,
                    source_ulid,
                    target_ulid,
                    payload,
                    priority,
                    scheduled_at,
                    max_retries
                )
                
                return {
                    "success": True,
                    "task": {
                        "id": str(result["id"]),
                        "task_id": result["task_id"],
                        "task_type": task_type,
                        "status": "pending",
                        "created_at": result["created_at"].isoformat()
                    }
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create task: {e}"
            }

    @staticmethod
    async def get_pending_tasks(limit: int = 10, task_type: str = None) -> List[Dict[str, Any]]:
        """
        Pobiera zadania do wykonania
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                conditions = ["status = 'pending'", "scheduled_at <= NOW()"]
                params = [limit]
                
                if task_type:
                    conditions.append("task_type = $2")
                    params.append(task_type)
                
                query = f"""
                    SELECT * FROM tasks 
                    WHERE {" AND ".join(conditions)}
                    ORDER BY priority ASC, scheduled_at ASC
                    LIMIT $1
                """
                
                rows = await conn.fetch(query, *params)
                
                tasks = []
                for row in rows:
                    tasks.append({
                        "id": str(row["id"]),
                        "task_id": row["task_id"],
                        "task_type": row["task_type"],
                        "source_ulid": row["source_ulid"],
                        "target_ulid": row["target_ulid"],
                        "payload": row["payload"],
                        "status": row["status"],
                        "priority": row["priority"],
                        "created_at": row["created_at"].isoformat(),
                        "scheduled_at": row["scheduled_at"].isoformat(),
                        "retry_count": row["retry_count"],
                        "max_retries": row["max_retries"]
                    })
                
                return tasks
                
        except Exception as e:
            print(f"❌ Error getting pending tasks: {e}")
            return []

    @staticmethod
    async def start_task(task_id: str) -> Dict[str, Any]:
        """
        Oznacza zadanie jako rozpoczęte
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    UPDATE tasks 
                    SET status = 'running', started_at = NOW()
                    WHERE task_id = $1 AND status = 'pending'
                    RETURNING task_id, status
                """
                
                result = await conn.fetchrow(query, task_id)
                
                if result:
                    return {
                        "success": True,
                        "task_id": result["task_id"],
                        "status": result["status"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Task not found or already started"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start task: {e}"
            }

    @staticmethod
    async def complete_task(task_id: str, result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Oznacza zadanie jako zakończone z wynikiem
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    UPDATE tasks 
                    SET status = 'completed', completed_at = NOW(), result = $2
                    WHERE task_id = $1
                    RETURNING task_id, status
                """
                
                db_result = await conn.fetchrow(query, task_id, result or {})
                
                if db_result:
                    return {
                        "success": True,
                        "task_id": db_result["task_id"],
                        "status": db_result["status"]
                    }
                else:
                    return {
                        "success": False,
                        "error": "Task not found"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to complete task: {e}"
            }

    @staticmethod
    async def fail_task(task_id: str, error_message: str, should_retry: bool = True) -> Dict[str, Any]:
        """
        Oznacza zadanie jako nieudane z możliwością retry
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                # Pobierz aktualne dane zadania
                get_query = """
                    SELECT retry_count, max_retries FROM tasks 
                    WHERE task_id = $1
                """
                task_data = await conn.fetchrow(get_query, task_id)
                
                if not task_data:
                    return {
                        "success": False,
                        "error": "Task not found"
                    }
                
                new_retry_count = task_data["retry_count"] + 1
                
                if should_retry and new_retry_count <= task_data["max_retries"]:
                    # Zaplanuj ponownie za kilka minut
                    next_attempt = datetime.now() + timedelta(minutes=5 * new_retry_count)
                    
                    query = """
                        UPDATE tasks 
                        SET status = 'pending', retry_count = $2, 
                            error_message = $3, scheduled_at = $4
                        WHERE task_id = $1
                        RETURNING task_id, status, retry_count
                    """
                    
                    result = await conn.fetchrow(query, task_id, new_retry_count, error_message, next_attempt)
                    
                    return {
                        "success": True,
                        "task_id": result["task_id"],
                        "status": "scheduled_for_retry",
                        "retry_count": result["retry_count"],
                        "next_attempt_at": next_attempt.isoformat()
                    }
                else:
                    # Zadanie ostatecznie nieudane
                    query = """
                        UPDATE tasks 
                        SET status = 'failed', retry_count = $2, 
                            error_message = $3, completed_at = NOW()
                        WHERE task_id = $1
                        RETURNING task_id, status
                    """
                    
                    result = await conn.fetchrow(query, task_id, new_retry_count, error_message)
                    
                    return {
                        "success": True,
                        "task_id": result["task_id"],
                        "status": "permanently_failed"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to fail task: {e}"
            }

    @staticmethod
    async def get_task_statistics() -> Dict[str, Any]:
        """
        Zwraca statystyki zadań
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = """
                    SELECT 
                        status,
                        COUNT(*) as count,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '1 hour' THEN 1 END) as last_hour
                    FROM tasks 
                    GROUP BY status
                """
                
                rows = await conn.fetch(query)
                
                stats = {
                    "total_tasks": 0,
                    "by_status": {},
                    "last_hour": {}
                }
                
                for row in rows:
                    status = row["status"]
                    count = row["count"]
                    last_hour = row["last_hour"]
                    
                    stats["total_tasks"] += count
                    stats["by_status"][status] = count
                    stats["last_hour"][status] = last_hour
                
                return {
                    "success": True,
                    "statistics": stats
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get statistics: {e}"
            }

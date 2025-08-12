
"""
Legacy PostgreSQL implementation - moved to legacy folder
"""

from database.postgre_db import Postgre_db as CurrentPostgreDb

# Legacy compatibility
class Postgre_db:
    """Legacy wrapper - use database.postgre_db.Postgre_db instead"""
    
    @staticmethod
    async def get_db_pool():
        """Legacy compatibility - delegates to current implementation"""
        return await CurrentPostgreDb.get_db_pool()
    
    @staticmethod
    async def setup_tables():
        """Legacy compatibility - delegates to current implementation"""
        return await CurrentPostgreDb.setup_tables()
        
    @staticmethod
    async def ensure_table(conn, table_hash: str, table_name: str, column_def: str, index: bool, foreign_key: bool, unique: dict):
        """Legacy compatibility - delegates to current implementation"""
        return await CurrentPostgreDb.ensure_table(conn, table_hash, table_name, column_def, index, foreign_key, unique)

print("⚠️ Using legacy postgre_db wrapper - migrate to database.postgre_db.Postgre_db")

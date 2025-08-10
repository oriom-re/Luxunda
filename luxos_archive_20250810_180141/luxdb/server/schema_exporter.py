
"""
Schema Exporter - Export and import namespace schemas
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.luxdb import LuxDB


class SchemaExporter:
    """
    Handles export and import of LuxDB namespace schemas
    """
    
    async def export_namespace_schema(self, namespace_id: str, db: LuxDB) -> Dict[str, Any]:
        """Export complete namespace schema including souls, beings and relationships"""
        
        pool = await db.connection_manager.get_pool()
        
        async with pool.acquire() as conn:
            # Get table prefix for namespace
            if hasattr(db, 'table_prefix'):
                prefix = db.table_prefix
            else:
                prefix = ""
            
            # Export souls
            souls_table = f"{prefix}souls"
            souls_result = await conn.fetch(f"""
                SELECT soul_hash, global_ulid, alias, genotype, created_at
                FROM {souls_table}
                ORDER BY created_at
            """)
            
            souls = []
            for row in souls_result:
                souls.append({
                    "soul_hash": row['soul_hash'],
                    "global_ulid": row['global_ulid'],
                    "alias": row['alias'],
                    "genotype": row['genotype'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            # Export beings
            beings_table = f"{prefix}beings"
            beings_result = await conn.fetch(f"""
                SELECT ulid, soul_hash, alias, created_at, updated_at
                FROM {beings_table}
                ORDER BY created_at
            """)
            
            beings = []
            for row in beings_result:
                beings.append({
                    "ulid": row['ulid'],
                    "soul_hash": row['soul_hash'],
                    "alias": row['alias'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            # Export relationships
            relationships_table = f"{prefix}relationships"
            relationships_result = await conn.fetch(f"""
                SELECT id, source_ulid, target_ulid, relation_type, strength, metadata, created_at, updated_at
                FROM {relationships_table}
                ORDER BY created_at
            """)
            
            relationships = []
            for row in relationships_result:
                relationships.append({
                    "id": str(row['id']),
                    "source_ulid": row['source_ulid'],
                    "target_ulid": row['target_ulid'],
                    "relation_type": row['relation_type'],
                    "strength": float(row['strength']) if row['strength'] else None,
                    "metadata": row['metadata'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                    "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
                })
            
            # Export dynamic attribute tables
            dynamic_tables = await self._export_dynamic_tables(conn, prefix)
            
            # Build schema
            schema = {
                "export_info": {
                    "namespace_id": namespace_id,
                    "exported_at": datetime.utcnow().isoformat(),
                    "luxdb_version": "1.0.0",
                    "schema_version": "1.0"
                },
                "souls": souls,
                "beings": beings,
                "relationships": relationships,
                "dynamic_tables": dynamic_tables,
                "stats": {
                    "souls_count": len(souls),
                    "beings_count": len(beings),
                    "relationships_count": len(relationships),
                    "dynamic_tables_count": len(dynamic_tables)
                }
            }
            
            return schema
    
    async def _export_dynamic_tables(self, conn, prefix: str) -> Dict[str, List[Dict[str, Any]]]:
        """Export data from dynamic attribute tables"""
        dynamic_tables = {}
        
        # Get all tables that match dynamic attribute pattern
        table_pattern = f"{prefix}attr_%"
        tables_result = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename LIKE $1
        """, table_pattern)
        
        for table_row in tables_result:
            table_name = table_row['tablename']
            
            # Export table data
            data_result = await conn.fetch(f"""
                SELECT being_ulid, key, value
                FROM {table_name}
                ORDER BY being_ulid, key
            """)
            
            table_data = []
            for row in data_result:
                table_data.append({
                    "being_ulid": row['being_ulid'],
                    "key": row['key'],
                    "value": row['value']
                })
            
            dynamic_tables[table_name] = table_data
        
        return dynamic_tables
    
    async def import_namespace_schema(self, namespace_id: str, db: LuxDB, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Import schema data to namespace"""
        
        pool = await db.connection_manager.get_pool()
        
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Get table prefix for namespace
                if hasattr(db, 'table_prefix'):
                    prefix = db.table_prefix
                else:
                    prefix = ""
                
                # Import souls
                souls_imported = 0
                for soul_data in schema_data.get('souls', []):
                    souls_table = f"{prefix}souls"
                    await conn.execute(f"""
                        INSERT INTO {souls_table} (soul_hash, global_ulid, alias, genotype, created_at)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (soul_hash) DO UPDATE SET
                            global_ulid = EXCLUDED.global_ulid,
                            alias = EXCLUDED.alias,
                            genotype = EXCLUDED.genotype
                    """, 
                    soul_data['soul_hash'],
                    soul_data['global_ulid'],
                    soul_data['alias'],
                    soul_data['genotype'],
                    datetime.fromisoformat(soul_data['created_at']) if soul_data.get('created_at') else None
                    )
                    souls_imported += 1
                
                # Import beings
                beings_imported = 0
                for being_data in schema_data.get('beings', []):
                    beings_table = f"{prefix}beings"
                    await conn.execute(f"""
                        INSERT INTO {beings_table} (ulid, soul_hash, alias, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (ulid) DO UPDATE SET
                            soul_hash = EXCLUDED.soul_hash,
                            alias = EXCLUDED.alias,
                            updated_at = CURRENT_TIMESTAMP
                    """,
                    being_data['ulid'],
                    being_data['soul_hash'],
                    being_data['alias'],
                    datetime.fromisoformat(being_data['created_at']) if being_data.get('created_at') else None,
                    datetime.fromisoformat(being_data['updated_at']) if being_data.get('updated_at') else None
                    )
                    beings_imported += 1
                
                # Import relationships
                relationships_imported = 0
                for rel_data in schema_data.get('relationships', []):
                    relationships_table = f"{prefix}relationships"
                    await conn.execute(f"""
                        INSERT INTO {relationships_table} (source_ulid, target_ulid, relation_type, strength, metadata, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT DO NOTHING
                    """,
                    rel_data['source_ulid'],
                    rel_data['target_ulid'],
                    rel_data['relation_type'],
                    rel_data['strength'],
                    rel_data['metadata'],
                    datetime.fromisoformat(rel_data['created_at']) if rel_data.get('created_at') else None,
                    datetime.fromisoformat(rel_data['updated_at']) if rel_data.get('updated_at') else None
                    )
                    relationships_imported += 1
                
                # Import dynamic tables
                dynamic_imported = await self._import_dynamic_tables(conn, prefix, schema_data.get('dynamic_tables', {}))
                
                return {
                    "namespace_id": namespace_id,
                    "imported_at": datetime.utcnow().isoformat(),
                    "souls_imported": souls_imported,
                    "beings_imported": beings_imported,
                    "relationships_imported": relationships_imported,
                    "dynamic_tables_imported": dynamic_imported
                }
    
    async def _import_dynamic_tables(self, conn, prefix: str, dynamic_tables: Dict[str, List[Dict[str, Any]]]) -> int:
        """Import dynamic attribute tables data"""
        imported_count = 0
        
        for table_name, table_data in dynamic_tables.items():
            # Ensure table exists (create if needed)
            # This is a simplified version - in production you might want more sophisticated table creation
            try:
                for row_data in table_data:
                    await conn.execute(f"""
                        INSERT INTO {table_name} (being_ulid, key, value)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (being_ulid, key) DO UPDATE SET
                            value = EXCLUDED.value
                    """,
                    row_data['being_ulid'],
                    row_data['key'],
                    row_data['value']
                    )
                    imported_count += 1
            except Exception as e:
                # Log error but continue with other tables
                print(f"Error importing table {table_name}: {e}")
        
        return imported_count


def save_schema_to_file(schema: Dict[str, Any], filename: str):
    """Save schema to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)


def load_schema_from_file(filename: str) -> Dict[str, Any]:
    """Load schema from JSON file"""
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

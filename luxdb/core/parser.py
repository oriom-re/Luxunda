
"""
LuxDB Parser Module
==================

Parser for genotypes and SQL table generation.
"""

from typing import Dict, Any, List, Optional
from ..utils.types import GenotypeDef

class GenotypParser:
    """Parser for LuxDB genotypes"""
    
    def __init__(self):
        self.type_mapping = {
            'str': 'VARCHAR',
            'int': 'INTEGER',
            'float': 'FLOAT',
            'bool': 'BOOLEAN',
            'dict': 'JSONB',
            'List[str]': 'JSONB',
            'List[float]': 'VECTOR'
        }
    
    def parse_genotype(self, genotype: GenotypeDef) -> Dict[str, Any]:
        """Parse genotype into SQL table definitions"""
        tables = []
        
        if 'attributes' in genotype:
            for attr_name, attr_def in genotype['attributes'].items():
                py_type = attr_def.get('py_type', 'str')
                sql_type = self.type_mapping.get(py_type, 'VARCHAR')
                
                table_info = {
                    'attribute': attr_name,
                    'py_type': py_type,
                    'sql_type': sql_type,
                    'table_name': f"attr_{sql_type.lower()}",
                    'create_sql': f"CREATE TABLE IF NOT EXISTS attr_{sql_type.lower()} (id SERIAL PRIMARY KEY, being_ulid VARCHAR, value {sql_type});",
                    'index': True,
                    'index_sql': f"CREATE INDEX IF NOT EXISTS idx_attr_{sql_type.lower()}_being ON attr_{sql_type.lower()}(being_ulid);"
                }
                tables.append(table_info)
        
        return {
            'genotype': genotype,
            'tables': tables,
            'sql_statements': [t['create_sql'] for t in tables] + [t['index_sql'] for t in tables if t['index_sql']]
        }
    
    def validate_genotype(self, genotype: GenotypeDef) -> bool:
        """Validate genotype structure"""
        if not isinstance(genotype, dict):
            return False
        
        if 'attributes' not in genotype:
            return False
        
        for attr_name, attr_def in genotype['attributes'].items():
            if 'py_type' not in attr_def:
                return False
            
            if attr_def['py_type'] not in self.type_mapping:
                return False
        
        return True

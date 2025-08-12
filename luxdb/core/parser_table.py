
"""
Parser table utilities for legacy compatibility
"""

def create_foreign_key(conn, table_name: str, column: str, ref_table: str, ref_column: str):
    """Legacy compatibility function"""
    pass

def parse_py_type(py_type):
    """Legacy compatibility function"""
    return "TEXT"

def build_table_name(prefix: str, suffix: str = ""):
    """Legacy compatibility function"""
    return f"{prefix}_{suffix}" if suffix else prefix

def create_query_table(table_name: str, columns: dict):
    """Legacy compatibility function"""
    return f"CREATE TABLE IF NOT EXISTS {table_name} (id SERIAL PRIMARY KEY)"

def create_index(conn, table_name: str, column: str):
    """Legacy compatibility function"""
    pass

def create_unique(conn, table_name: str, columns: list):
    """Legacy compatibility function"""
    pass

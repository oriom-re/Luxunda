import json
from typing import get_origin, get_args, Optional, Union, List, Dict, Any

def parse_py_type(attr_name: str, attr_meta: dict):
    # Bezpieczny eval + podstawowe typy
    namespace = {
        "Optional": Optional,
        "Union": Union,
        "List": List,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "List[float]": List[float],
        "dict": dict,
        "None": None,
        "List[str]": List[str],
        "List[int]": List[int],
        "List[bool]": List[bool],
    }

    py_type_str = attr_meta.get("py_type", "str")
    py_type = eval(py_type_str, namespace)

    # Czy to Optional / Union?
    is_optional = (
        get_origin(py_type) is Optional or
        (get_origin(py_type) is Union and type(None) in get_args(py_type))
    )

    # Bazowy typ
    base_type = get_args(py_type)[0] if is_optional else py_type

    # Czy wymaga serializacji (np. listy, słowniki)
    requires_serialization = get_origin(base_type) in [list, dict, List] or isinstance(base_type, type) and base_type in [list, dict]


    # Flagi i dodatkowe informacje
    return {
        "name": attr_name,
        "base_type": base_type,
        "is_optional": is_optional,
        "requires_serialization": requires_serialization,  # Dodana flaga
        "index": attr_meta.get("index", False),
        "unique": attr_meta.get("unique", False),
        "max_length": attr_meta.get("max_length"),
        "vector_size": attr_meta.get("vector_size"),
        "default": attr_meta.get("default"),
        "encoder": json.dumps if requires_serialization else lambda x: x,
        "decoder": json.loads if requires_serialization else lambda x: x,

    }

def build_table_name(parsed: dict) -> str:
    base = parsed["base_type"]
    table_name = "attr_"  # prefiks zamiast tylko "_"
    column_name = "value "
    
    # Typ bazowy → SQL-friendly name
    if base is str:
        table_name += "text"
        max_len = parsed.get("max_length", 255)
        column_name += f"VARCHAR({max_len})"
    elif base is int:
        table_name += "int"
        column_name += "INTEGER"
    elif base is float:
        table_name += "float"
        column_name += "FLOAT"
    elif base is bool:
        table_name += "boolean"
        column_name += "BOOLEAN"
    elif base is dict:
        table_name += "jsonb"
        column_name += "JSONB"
    elif base is list or str(base).startswith("typing.List"):
        # Obsługa list np. List[float]
        if parsed.get("vector_size"):
            size = parsed["vector_size"]
            table_name += f"vector_{size}"
            column_name += f"VECTOR({size})"
        else:
            table_name += "list"
            column_name += "JSONB"  # lista jako jsonb, jeśli brak szczegółów
    else:
        table_name += "unknown"
        column_name += "TEXT"
        print(f"Warning: Unknown type {base} for attribute {parsed['name']}")
    
    # Flagi i ograniczenia
    if parsed.get("unique"):
        column_name += " UNIQUE"
    if not parsed.get("is_optional", True):
        column_name += " NOT NULL"
    
    return table_name, column_name.strip(), parsed.get("index", False), parsed.get("foreign_key", False)


def create_query_table(table_name: str, column_def: str) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        ulid CHAR(26) NOT NULL,
        being_ulid CHAR(26) NOT NULL,
        soul_hash CHAR(64) NOT NULL,
        key TEXT NOT NULL,
        {column_def},
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (being_ulid, key),
        FOREIGN KEY (being_ulid) REFERENCES beings(ulid),
        FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash)
    );
    """

def create_index(table_name: str) -> str:
    return f"CREATE INDEX IF NOT EXISTS idx_{table_name}_key ON {table_name} (key);"

def process_genotype_for_tables(genotype: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Przetwarza genotyp i zwraca listę definicji tabel do utworzenia"""
    tables_to_create = []
    
    attributes = genotype.get("attributes", {})
    for attr_name, attr_meta in attributes.items():
        parsed = parse_py_type(attr_name, attr_meta)
        table_name, column_def, index, foreign_key = build_table_name(parsed)
        
        table_info = {
            "table_name": table_name,
            "column_def": column_def,
            "index": index,
            "foreign_key": foreign_key,
            "create_sql": create_query_table(table_name, column_def),
            "index_sql": create_index(table_name) if index else None,
            "attr_name": attr_name,
            "parsed": parsed
        }
        tables_to_create.append(table_info)
    
    return tables_to_create

def validate_genotype(genotype: Dict[str, Any]) -> Dict[str, Any]:
    """Waliduje strukturę genotypu"""
    errors = []
    warnings = []
    
    if not isinstance(genotype, dict):
        errors.append("Genotype must be a dictionary")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    if "attributes" not in genotype:
        errors.append("Genotype must have 'attributes' key")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    attributes = genotype.get("attributes", {})
    if not isinstance(attributes, dict):
        errors.append("Genotype attributes must be a dictionary")
        return {"valid": False, "errors": errors, "warnings": warnings}
    
    for attr_name, attr_meta in attributes.items():
        if not isinstance(attr_meta, dict):
            errors.append(f"Attribute '{attr_name}' metadata must be a dictionary")
            continue
            
        py_type = attr_meta.get("py_type", "str")
        try:
            parse_py_type(attr_name, attr_meta)
        except Exception as e:
            errors.append(f"Invalid py_type '{py_type}' for attribute '{attr_name}': {e}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }



# Przykład użycia i testowania
if __name__ == "__main__":
    # Przykładowy genotyp testowy
    test_genotype = {
        "attributes": {
            "name": {
                "py_type": "Optional[str]",
                "max_length": 255,
                "index": True,
                "unique": True
            },
            "embedding": {
                "py_type": "List[float]",
                "vector_size": 1536
            },
            "active": {
                "py_type": "bool",
                "default": True
            }
        }
    }
    
    print("==============================================")
    print("LuxDB Parser Table - Validation and Processing")
    print("==============================================")
    
    # Walidacja genotypu
    validation = validate_genotype(test_genotype)
    print(f"Genotype validation: {'✅ VALID' if validation['valid'] else '❌ INVALID'}")
    if validation['errors']:
        for error in validation['errors']:
            print(f"  ❌ Error: {error}")
    if validation['warnings']:
        for warning in validation['warnings']:
            print(f"  ⚠️  Warning: {warning}")
    
    if validation['valid']:
        # Przetwarzanie genotypu
        tables = process_genotype_for_tables(test_genotype)
        print(f"\n📊 Generated {len(tables)} table definitions:")
        
        for table in tables:
            print(f"\n🔧 Attribute: {table['attr_name']}")
            print(f"   Table: {table['table_name']}")
            print(f"   Index: {'Yes' if table['index'] else 'No'}")
            print(f"   SQL: {table['create_sql'].strip()}")
            if table['index_sql']:
                print(f"   Index SQL: {table['index_sql']}")
    
    print("\n==============================================")
    print("Ready for LuxDB MVP integration! 🚀")
    print("==============================================")


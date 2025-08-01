import json
from typing import get_origin, get_args, Optional, Union, List, Dict, Any
import hashlib

def is_value_serializable(value) -> bool:
    """Sprawdza czy wartość może być serializowana do JSON w runtime"""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False
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

    # Sprawdź czy typ jest serializable dla JSONB
    def is_serializable(typ):
        """Sprawdza czy typ można serializować do JSON/JSONB"""
        # Podstawowe typy JSON-safe
        json_safe_types = {str, int, float, bool, type(None)}
        
        # Jeśli to bezpośrednio JSON-safe typ
        if typ in json_safe_types:
            return False
        
        # Jeśli to dict - zawsze wymaga serializacji
        if typ is dict:
            return True
            
        # Sprawdź typy generyczne (List, Optional, Union)
        origin = get_origin(typ)
        if origin is not None:
            # Lista wymaga serializacji, chyba że to List[float] z vector_size (embedding)
            if origin in [list, List]:
                # Sprawdź czy to embedding vector
                if attr_meta.get("vector_size"):
                    return False  # Embeddings idą do VECTOR, nie JSONB
                return True  # Inne listy idą do JSONB
            
            # Union/Optional - sprawdź składniki
            if origin in [Union, Optional]:
                args = get_args(typ)
                # Sprawdź czy któryś z argumentów wymaga serializacji
                for arg in args:
                    if arg is not type(None) and is_serializable(arg):
                        return True
                return False
        
        # Złożone typy niestandardowe wymagają serializacji
        if hasattr(typ, '__module__') and typ.__module__ not in ['builtins', '__builtin__']:
            return True
            
        return False

    # Czy wymaga serializacji (np. listy, słowniki, obiekty niestandardowe)
    requires_serialization = is_serializable(base_type)


    # Flagi i dodatkowe informacje
    return {
        "name": attr_name,
        "base_type": base_type,
        "is_optional": is_optional,
        "requires_serialization": requires_serialization,
        "is_jsonb_type": requires_serialization and not attr_meta.get("vector_size"),  # JSONB ale nie VECTOR
        "is_vector_type": bool(attr_meta.get("vector_size")),  # VECTOR type
        "index": attr_meta.get("index", False),
        "unique": attr_meta.get("unique", False),
        "max_length": attr_meta.get("max_length"),
        "vector_size": attr_meta.get("vector_size"),
        "default": attr_meta.get("default"),
        "encoder": json.dumps if requires_serialization else lambda x: x,
        "decoder": json.loads if requires_serialization else lambda x: x,
    }

def build_table_name(parsed: dict) -> tuple:
    base = parsed["base_type"]
    name = "attr_"  # prefiks zamiast tylko "_"
    column_name = "value "
    
    # Typ bazowy → SQL-friendly name
    if base is str:
        name += "text"
        max_len = parsed.get("max_length", 255)
        if not max_len:
            max_len = 255
        print(f"Max length for {parsed['name']}: {max_len}")
        column_name += f"VARCHAR({max_len})"
    elif base is int:
        name += "int"
        column_name += "INTEGER"
    elif base is float:
        name += "float"
        column_name += "FLOAT"
    elif base is bool:
        name += "boolean"
        column_name += "BOOLEAN"
    elif base is dict:
        name += "jsonb"
        column_name += "JSONB"
    elif base is list or str(base).startswith("typing.List"):
        # Obsługa list np. List[float]
        if parsed.get("vector_size"):
            size = parsed["vector_size"]
            if not size or size <= 0:
                size = 1536
            name += f"vector_{size}"
            column_name += f"VECTOR({size})"
        else:
            name += "jsonb"  # lista jako jsonb
            column_name += "JSONB"
    elif parsed.get("requires_serialization"):
        # Dla wszystkich typów które wymagają serializacji
        name += "jsonb"
        column_name += "JSONB"
    else:
        name += "unknown"
        column_name += "TEXT"
        print(f"Warning: Unknown type {base} for attribute {parsed['name']}")
    
    # Flagi i ograniczenia
    if parsed.get("unique"):
        name += "_unique"
    if not parsed.get("is_optional", True):
        name += "_not_null"
        column_name += " NOT NULL"
    # zamiana na hash dla unikalnych kolumn
    table_hash = "attr_" + str(hashlib.sha256(name.encode()).hexdigest()[:50])  # skrócenie do 10 znaków
    return table_hash, name, column_name.strip(), parsed.get("index", False), parsed.get("foreign_key", False), parsed.get("unique", False)


def create_query_table(table_hash: str, name: str, column_def: str) -> str:
    print(f"Creating table {table_hash} with definition: {column_def} name: {name}")
    return f"""
    CREATE TABLE IF NOT EXISTS {table_hash} (
        ulid CHAR(26) NOT NULL,
        being_ulid CHAR(26) NOT NULL,
        soul_hash CHAR(64) NOT NULL,
        name TEXT NOT NULL DEFAULT '{name}',
        key TEXT NOT NULL,
        {column_def},
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (being_ulid, key),
        FOREIGN KEY (being_ulid) REFERENCES beings(ulid),
        FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash)
    );
    """

def create_index(table_hash: str) -> str:
    return f"CREATE INDEX IF NOT EXISTS idx_{table_hash}_key ON {table_hash} (key);"

def create_foreign_key(table_hash: str, foreign_table: str) -> str:
    return f"ALTER TABLE {table_hash} ADD CONSTRAINT fk_{table_hash}_{foreign_table} FOREIGN KEY (value) REFERENCES {foreign_table}(ulid);"

def create_unique(table_hash: str) -> str:
    return f"ALTER TABLE {table_hash} ADD CONSTRAINT unique_{table_hash}_value UNIQUE (soul_hash, value);"

def process_genotype_for_tables(genotype: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Przetwarza genotyp i zwraca listę definicji tabel do utworzenia"""
    tables_to_create = []
    
    attributes = genotype.get("attributes", {})
    for attr_name, attr_meta in attributes.items():
        parsed = parse_py_type(attr_name, attr_meta)
        table_hash, table_name, column_def, index, foreign_key, unique = build_table_name(parsed)

        table_info = {
            "table_name": table_name,
            "table_hash": table_hash,  # używamy tego samego jako hash
            "column_def": column_def,
            "index": index,
            "foreign_key": foreign_key,
            "unique": unique,
            "unique_sql": create_unique(table_hash) if unique else None,
            "create_sql": create_query_table(table_hash, table_name, column_def),
            "index_sql": create_index(table_hash) if index else None,
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


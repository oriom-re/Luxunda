from typing import get_origin, get_args, Optional, Union

def parse_py_type(attr_name: str, attr_meta: dict):
    # Bezpieczny eval + podstawowe typy
    namespace = {
        "Optional": Optional,
        "Union": Union,
        "List": list,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
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

    # Flagi i dodatkowe informacje
    return {
        "name": attr_name,
        "base_type": base_type,
        "is_optional": is_optional,
        "index": attr_meta.get("index", False),
        "unique": attr_meta.get("unique", False),
        "max_length": attr_meta.get("max_length"),
        "vector_size": attr_meta.get("vector_size"),
        "default": attr_meta.get("default"),
    }

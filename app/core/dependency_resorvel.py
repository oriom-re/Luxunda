import ast
import hashlib
from typing import List, Dict, Optional

def extract_imports(source_code: str) -> List[str]:
    """Parsuje kod źródłowy i zwraca listę importowanych modułów."""
    tree = ast.parse(source_code)
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def hash_code(content: str) -> str:
    """Zwraca skrót SHA256 kodu źródłowego."""
    return hashlib.sha256(content.encode()).hexdigest()


def load_gen_file_as_soul(file_path: str) -> Dict:
    """Ładuje kod z pliku jako soul z informacją o importach i hash."""
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    soul_id = file_path  # ID może być ścieżką
    version = hash_code(code)
    imports = extract_imports(code)

    return {
        "soul": soul_id,
        "genesis": {
            "type": "gen",
            "path": file_path,
            "version": version,
            "provides": [],  # można dodać ręcznie
            "dependencies": imports
        },
        "attributes": {},
        "memories": [],
        "self_awareness": {}
    }

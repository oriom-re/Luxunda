# app/core/gen_loader_from_file.py
# description: This module provides functions to load Python files as souls, extract imports, and save them to the database.

from ast import Dict
import ast
from datetime import datetime
import hashlib
import os
import re
import json
from typing import List
import uuid
import aiosqlite
from app.beings.base import Being
from app.beings.genotype import Genotype
from app.database import get_db_pool
import hashlib
import os

def get_info_from_file(file_path: str):
    """Zwraca funkcje z pliku jako słownik."""
    if not os.path.exists(file_path):
        return None
    functions = {}
    metadata = {}
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()
        tree = ast.parse(source_code)
        # Wyszukaj funkcje w AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                func_source = ast.get_source_segment(source_code, node)
                functions[func_name] = {
                    "name": func_name,
                    "source": func_source,
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
        # Dodaj metadane pliku
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Str):
                    name = target.id
                    if name.startswith("__"):
                        # usuwamy podkreślenia z obu stron
                        name = name[2:] if name.startswith("__") else name
                        name = name[:-2] if name.endswith("__") else name
                        if name not in metadata:  # unikaj nadpisywania
                            metadata[name] = node.value.s
        metadata["file_path_rel"] = os.path.relpath(file_path)
        metadata["file_path"] = os.path.abspath(file_path)
        metadata["file_name"] = os.path.basename(file_path)
        metadata["type"] = "genotype"  # Dodajemy typ genotypu
        metadata["language"] = get_language_from_file(file_path)
        metadata["created_at"] = datetime.now().isoformat()
        metadata["code"] = source_code
        metadata["hash_hex"] = hashlib.sha256(get_live_code(source_code).encode()).hexdigest()
        metadata["dependencies"] = extract_imports(source_code)
    return functions, metadata

def get_language_from_file(file_path: str) -> str:
    """Zwraca język pliku na podstawie rozszerzenia."""
    _, ext = os.path.splitext(file_path)
    if ext == ".py":
        return "python"
    elif ext == ".js":
        return "javascript"
    elif ext == ".java":
        return "java"
    elif ext == ".c":
        return "c"
    elif ext == ".cpp":
        return "cpp"
    elif ext == ".go":
        return "go"
    elif ext == "json":
        return "json"
    elif ext == ".yaml" or ext == ".yml":
        return "yaml"
    elif ext == ".html":
        return "html"
    elif ext == ".css":
        return "css"
    elif ext == ".md":
        return "markdown"
    elif ext == ".txt":
        return "text"
    else:
        return "unknown"
    
def get_live_code(code: str) -> str:
    # Usuń komentarze wieloliniowe """ """ i ''' '''
    code = re.sub(r'""".*?"""', '', code, flags=re.DOTALL)
    code = re.sub(r"'''.*?'''", '', code, flags=re.DOTALL)

    # Usuń komentarze liniowe i puste linie
    lines = code.split('\n')
    live_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        # Usuń trailing inline komentarze (opcjonalnie)
        cleaned = re.sub(r'#.*', '', line)
        if cleaned.strip():  # Sprawdź, czy po usunięciu coś zostało
            live_lines.append(cleaned.strip())
    print(f"Extracted live code: {live_lines}")
    return '\n'.join(live_lines)

# get soul by genesis.path
async def get_soul_by_name(name: str):
    pool = await get_db_pool()
    # get all tables
    if not pool:
        print("Database pool is not initialized.")
        return None

    if hasattr(pool, 'acquire'):  # PostgreSQL (np. asyncpg)
        async with pool.acquire() as conn:
            tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            print(f"Available tables: {[table['table_name'] for table in tables]}")
            query = """
                SELECT * FROM souls
                WHERE genesis->>'name' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, name)
            print(f"🔍 Searching for soul with name: {name}")
            if row:
                return {
                    "uid": str(row['uid']),
                    "genesis": json.loads(row['genesis']),
                    "attributes": json.loads(row['attributes']),
                    "memories": json.loads(row['memories']),
                    "self_awareness": json.loads(row['self_awareness']),
                    "created_at": row['created_at']
                }
            print(f"No soul found for name: {name}")
    else:  # SQLite (np. aiosqlite)
        pool.row_factory = aiosqlite.Row
        query = """
            SELECT * FROM souls
            WHERE json_extract(genesis, '$.name') = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with pool.execute(query, (name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "uid": row["uid"],
                    "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                    "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                    "memories": json.loads(row["memories"]) if row["memories"] else [],
                    "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                    "created_at": row["created_at"]
                }
    return None

async def get_soul_by(element, value):
    pool = await get_db_pool()
    if not pool:
        print("Database pool is not initialized.")
        return None
    if hasattr(pool, 'acquire'):  # PostgreSQL (np. asyncpg)
        async with pool.acquire() as conn:
            query = f"""
                SELECT * FROM souls
                WHERE genesis->>'{element}' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, value)
            if row:
                return {
                    "uid": str(row['uid']),
                    "genesis": json.loads(row['genesis']),
                    "attributes": json.loads(row['attributes']),
                    "memories": json.loads(row['memories']),
                    "self_awareness": json.loads(row['self_awareness']),
                    "created_at": row['created_at']
                }
    else:  # SQLite (np. aiosqlite)
        pool.row_factory = aiosqlite.Row
        query = f"""
            SELECT * FROM souls
            WHERE json_extract(genesis, '$.{element}') = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with pool.execute(query, (value,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "uid": row["uid"],
                    "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                    "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                    "memories": json.loads(row["memories"]) if row["memories"] else [],
                    "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                    "created_at": row["created_at"]
                }
    return None

async def send_module_to_db(soul: Dict):
    """Zapisuje moduł jako soul w bazie danych."""
    existing_soul = await get_soul_by_name(soul["genesis"]["name"])
    if existing_soul:
        print(f"🔍 Soul with name {soul['genesis']['name']} already exists. Updating existing soul.")
        if await get_soul_by('hash_hex', soul["genesis"]["hash_hex"]):
            # Jeśli istnieje już taki soul, nie zapisuj ponownie
            print(f"🔍 Soul with name {soul['genesis']['name']} already exists. Skipping save.")
            return
        else:
            print(f"🔍 Soul with name {soul['genesis']['name']} already exists. Replacing with new soul.")
            await Relationship.create(
                source_uid=existing_soul["uid"],
                target_uid=soul["uid"],
                attributes={"replaces": soul["uid"]}
            )
    await Being.create(soul)

def load_module_from_file(path: str):
    functions, metadata = get_info_from_file(path)
    for func_name, func_info in functions.items():
        print(f"Found function: {func_name} in {path}")
    # for key, value in metadata.items():
    #     print(f"Metadata {key}: {value}")

    print(f"Loading module from file: {path}")
    if not os.path.isfile(path):
        print(f"File not found: {path}")
        return None

    soul = {
        "uid": str(uuid.uuid4()),
        "genesis": metadata,
        "attributes": {},
        "memories": [],
        "self_awareness": {},
        "created_at": datetime.now(),
    }
    return soul

async def register_all_genotypes(directory: str) -> List[Dict]:
    souls = []
    directory = os.path.abspath(directory)  # Użycie ścieżki absolutnej dla katalogu
    print(f"Processing directory: {directory}")
    for filename in os.listdir(directory):
        print(f"Processing file: {filename}")
        if filename.endswith(".py") and not filename.startswith("__"):
            file_path = os.path.abspath(os.path.join(directory, filename))  # Ścieżka absolutna dla pliku
            print(f"Loading module file: {file_path}")
            if not os.path.isfile(file_path):
                print(f"Skipping non-file: {file_path}")
                continue
            soul = load_module_from_file(file_path)
            if soul:
                await Genotype.send_genotype_to_db(soul)
                souls.append(soul)
            else:
                print(f"Failed to create soul for file: {file_path}")
    return souls

async def load_module_from_db(soul_id: str):
    """Ładuje moduł z bazy danych na podstawie ID."""
    pool = await get_db_pool()
    if hasattr(pool, 'acquire'):  # PostgreSQL (np. asyncpg)
        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE uid = $1
            """
            row = await conn.fetchrow(query, soul_id)
            if row:
                return {
                    "uid": str(row['uid']),
                    "genesis": row['genesis'],
                    "attributes": row['attributes'],
                    "memories": row['memories'],
                    "self_awareness": row['self_awareness'],
                    "created_at": row['created_at']
                }
    else:  # SQLite (np. aiosqlite)
        query = """
            SELECT * FROM souls
            WHERE uid = ?
        """
        async with pool.execute(query, (soul_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "uid": row["uid"],
                    "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                    "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                    "memories": json.loads(row["memories"]) if row["memories"] else [],
                    "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                    "created_at": row["created_at"]
                }
    return None

async def load_module_from_db_by_path(path: str):
    """Ładuje moduł z bazy danych na podstawie ścieżki."""
    pool = await get_db_pool()
    if hasattr(pool, 'acquire'):  # PostgreSQL (np. asyncpg)
        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE genesis->>'path' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, path)
            if row:
                return {
                    "uid": str(row['uid']),
                    "genesis": row['genesis'],
                    "attributes": row['attributes'],
                    "memories": row['memories'],
                    "self_awareness": row['self_awareness'],
                    "created_at": row['created_at']
                }
    else:  # SQLite (np. aiosqlite)
        query = """
            SELECT * FROM souls
            WHERE json_extract(genesis, '$.path') = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        async with pool.execute(query, (path,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "uid": row["uid"],
                    "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                    "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                    "memories": json.loads(row["memories"]) if row["memories"] else [],
                    "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                    "created_at": row["created_at"]
                }
    return None

def extract_imports(source_code: str) -> List[str]:
    """Parsuje kod źródłowy i zwraca listę importowanych modułów."""
    import ast
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

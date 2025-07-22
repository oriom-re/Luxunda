# soul: app/core/gen_loader_from_file.py

from datetime import datetime
import hashlib
import os

def generate_soul_id_from_code(code: str, preferred_name: str = "gen") -> str:
    hash_hex = hashlib.sha256(code.encode("utf-8")).hexdigest()[:10]
    return f"{preferred_name}-{hash_hex}"

def extract_soul_name_from_code(code: str) -> str:
    for line in code.splitlines():
        if line.strip().startswith("# soul:"):
            return line.split(":", 1)[1].strip()
        else:
            return generate_soul_id_from_code(code, "gen")
    return "gen"

def load_gen_file_as_soul(path: str, autoload: bool = True):
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    soul_id = extract_soul_name_from_code(code)

    soul = {
        "soul": soul_id,
        "genesis": {
            "type": "gen",
            "hash": hashlib.sha256(code.encode("utf-8")).hexdigest(),
            "origin": "filesystem",
            "data": code,
            "created_at": datetime.now().isoformat()
        },
        "attributes": {"tags": ["proto"]},
        "memories": [],
        "self_awareness": {},
        "created_at": datetime.now(),
        "modified_at": datetime.now()
    }

    return soul

def load_all_gen_files_as_souls(directory: str, autoload: bool = True):
    souls = []
    for filename in os.listdir(directory):
        if filename.endswith(".gen"):
            soul = load_gen_file_as_soul(os.path.join(directory, filename), autoload)
            souls.append(soul)
    return souls

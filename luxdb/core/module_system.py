
"""
System automatycznej rejestracji modułów jako Being w LuxDB
"""

import os
import hashlib
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from datetime import datetime
import ast
import importlib.util

from ..models.soul import Soul
from ..models.being import Being
from .kernel_system import kernel_system

class ModuleWatcher:
    """Obserwuje pliki i automatycznie rejestruje je jako moduły Being"""
    
    def __init__(self, watch_paths: List[str] = None):
        self.watch_paths = watch_paths or [
            "luxdb", "ai", "core", "database", "genes", 
            "services", "static", "scenarios"
        ]
        self.registered_modules = {}
        self.module_hashes = {}
        self.change_log = []
        
    def generate_module_hash(self, file_path: str, content: str) -> str:
        """Generuje hash dla modułu na podstawie ścieżki i zawartości"""
        combined = f"{file_path}:{content}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def extract_functions_and_classes(self, content: str) -> Dict[str, Any]:
        """Wyciąga funkcje i klasy z kodu"""
        try:
            tree = ast.parse(content)
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "decorators": [d.id if hasattr(d, 'id') else str(d) for d in node.decorator_list]
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports
            }
        except Exception as e:
            print(f"⚠️ Błąd parsowania {content[:50]}...: {e}")
            return {"functions": [], "classes": [], "imports": []}
    
    async def register_module_as_being(self, file_path: str) -> Optional[Being]:
        """Rejestruje plik jako Being typu module"""
        try:
            if not os.path.exists(file_path):
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generuj hash
            current_hash = self.generate_module_hash(file_path, content)
            
            # Sprawdź czy już istnieje z tym samym hashem
            if file_path in self.module_hashes:
                if self.module_hashes[file_path] == current_hash:
                    return self.registered_modules.get(file_path)
            
            # Wyciągnij strukturę kodu
            code_structure = self.extract_functions_and_classes(content)
            
            # Określ typ pliku
            file_extension = Path(file_path).suffix
            module_type = {
                '.py': 'python_module',
                '.js': 'javascript_module', 
                '.html': 'html_template',
                '.css': 'css_stylesheet',
                '.json': 'json_data',
                '.md': 'markdown_doc'
            }.get(file_extension, 'generic_module')
            
            # Przygotuj genesis z pełnym kodem
            genesis = {
                "name": Path(file_path).stem,
                "type": "module",
                "module_type": module_type,
                "file_path": file_path,
                "code": content,
                "hash": current_hash,
                "created_at": datetime.now().isoformat(),
                "structure": code_structure,
                "size": len(content),
                "lines": len(content.split('\n'))
            }
            
            # Przygotuj genotyp
            genotype = {
                "genesis": genesis,
                "attributes": {
                    "file_path": {"py_type": "str"},
                    "module_hash": {"py_type": "str"},
                    "last_modified": {"py_type": "str"},
                    "dependencies": {"py_type": "List[str]"},
                    "exports": {"py_type": "List[str]"},
                    "size": {"py_type": "int"}
                }
            }
            
            # Utwórz Soul
            soul_alias = f"module_{Path(file_path).stem}_{current_hash[:8]}"
            soul = await Soul.create(genotype, alias=soul_alias)
            
            # Utwórz Being
            being_data = {
                "file_path": file_path,
                "module_hash": current_hash,
                "last_modified": datetime.now().isoformat(),
                "dependencies": code_structure["imports"],
                "exports": [f["name"] for f in code_structure["functions"]] + 
                          [c["name"] for c in code_structure["classes"]],
                "size": len(content)
            }
            
            being = await Being.create(
                soul=soul,
                data=being_data,
                alias=f"module_{Path(file_path).stem}"
            )
            
            # Zapisz w rejestrze
            self.registered_modules[file_path] = being
            old_hash = self.module_hashes.get(file_path, "new")
            self.module_hashes[file_path] = current_hash
            
            # Dodaj do logu zmian
            change_entry = {
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "action": "updated" if old_hash != "new" else "created",
                "old_hash": old_hash,
                "new_hash": current_hash,
                "being_ulid": being.ulid,
                "soul_hash": soul.soul_hash
            }
            self.change_log.append(change_entry)
            
            # Zarejestruj w kernel
            if hasattr(kernel_system, 'register_being'):
                await kernel_system.register_being(being)
            
            print(f"📦 Zarejestrowano moduł: {file_path} (hash: {current_hash[:8]}...)")
            return being
            
        except Exception as e:
            print(f"❌ Błąd rejestracji modułu {file_path}: {e}")
            return None
    
    async def scan_and_register_all(self) -> List[Being]:
        """Skanuje wszystkie pliki w obserwowanych ścieżkach"""
        registered_beings = []
        
        for watch_path in self.watch_paths:
            if not os.path.exists(watch_path):
                continue
                
            for root, dirs, files in os.walk(watch_path):
                # Pomijaj ukryte katalogi i __pycache__
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    if file.startswith('.') or file.endswith('.pyc'):
                        continue
                        
                    file_path = os.path.join(root, file)
                    being = await self.register_module_as_being(file_path)
                    if being:
                        registered_beings.append(being)
        
        print(f"📚 Zarejestrowano {len(registered_beings)} modułów")
        return registered_beings
    
    async def create_module_relationships(self):
        """Tworzy relacje między modułami na podstawie importów"""
        from ..models.relationship import Relationship
        
        for file_path, being in self.registered_modules.items():
            try:
                # Pobierz dependencje z being
                await being.load_full_data()
                dependencies = getattr(being, 'dependencies', [])
                
                for dep in dependencies:
                    # Znajdź moduł dependency
                    dep_being = None
                    for dep_path, dep_being_candidate in self.registered_modules.items():
                        if dep.split('.')[-1] in dep_path:
                            dep_being = dep_being_candidate
                            break
                    
                    if dep_being:
                        # Utwórz relację
                        relationship = await Relationship.create(
                            source_ulid=being.ulid,
                            target_ulid=dep_being.ulid,
                            relationship_type="imports",
                            attributes={
                                "import_name": dep,
                                "created_at": datetime.now().isoformat()
                            }
                        )
                        print(f"🔗 Relacja: {file_path} importuje {dep}")
                        
            except Exception as e:
                print(f"⚠️ Błąd tworzenia relacji dla {file_path}: {e}")
    
    def get_change_log(self) -> List[Dict]:
        """Zwraca historię zmian modułów"""
        return self.change_log
    
    def get_module_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki modułów"""
        total_modules = len(self.registered_modules)
        total_size = sum(
            getattr(being, 'size', 0) 
            for being in self.registered_modules.values()
        )
        
        module_types = {}
        for being in self.registered_modules.values():
            if hasattr(being, 'genotype') and 'genesis' in being.genotype:
                mod_type = being.genotype['genesis'].get('module_type', 'unknown')
                module_types[mod_type] = module_types.get(mod_type, 0) + 1
        
        return {
            "total_modules": total_modules,
            "total_size_bytes": total_size,
            "module_types": module_types,
            "total_changes": len(self.change_log)
        }

# Globalna instancja
module_watcher = ModuleWatcher()

# app_v2/core/module_registry.py
"""
Rejestr modułów - odpowiada za rejestrację i wersjonowanie modułów z plików
"""

import os
from datetime import datetime
from typing import Dict, List, Any

from app_v2.genetics import GeneRegistry

class ModuleRegistry:
    """Rejestr modułów - odpowiada za rejestrację i wersjonowanie"""
    
    @staticmethod
    def load_module_file_as_soul(file_path: str) -> Dict[str, Any]:
        """Ładuje plik jako soul i wykrywa geny"""
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return None
        
        print(f"Loading module from file: {file_path}")
        
        # Wczytaj kod z pliku
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Wykryj geny w kodzie (proste parsowanie)
        discovered_genes = ModuleRegistry._discover_genes_in_code(code)
        
        # Mock soul creation
        return {
            "uid": f"mock_uid_{os.path.basename(file_path)}",
            "genesis": {
                "name": f"genom_{os.path.basename(file_path).replace('.module', '')}",
                "path": file_path,
                "type": "module",
                "language": "python",
                "hash_hex": "mock_hash",
                "created_at": datetime.now().isoformat(),
                "code": code,
                "discovered_genes": discovered_genes,
                "dependencies": []  # TODO: Extract from imports
            },
            "attributes": {},
            "memories": [],
            "self_awareness": {}
        }
    
    @staticmethod
    async def register_module_from_file(file_path: str) -> bool:
        """Rejestruje pojedynczy moduł z pliku do bazy danych"""
        # Użyj nowej metody która obsługuje geny
        return await ModuleRegistry.register_module_and_genes(file_path)
    
    @staticmethod
    async def register_all_modules_from_directory(directory: str = "app_v2/gen_files") -> int:
        """Rejestruje wszystkie moduły z katalogu"""
        if not os.path.exists(directory):
            print(f"❌ Katalog nie istnieje: {directory}")
            return 0
        
        registered_count = 0
        
        print(f"🔍 Skanowanie katalogu: {directory}")
        for filename in os.listdir(directory):
            if filename.endswith('.module') and not filename.startswith('__'):
                file_path = os.path.join(directory, filename)
                if await ModuleRegistry.register_module_from_file(file_path):
                    registered_count += 1
        
        print(f"✅ Zarejestrowano {registered_count} modułów z katalogu {directory}")
        return registered_count
    
    @staticmethod
    def _discover_genes_in_code(code: str) -> List[Dict[str, Any]]:
        """Wykrywa definicje genów w kodzie źródłowym"""
        import re
        
        genes = []
        
        # Szukaj dekoratorów @gene
        gene_pattern = r'@gene\s*\(\s*([^)]*)\s*\)\s*def\s+(\w+)'
        matches = re.finditer(gene_pattern, code, re.MULTILINE)
        
        for match in matches:
            decorator_args = match.group(1)
            function_name = match.group(2)
            
            # Parsuj argumenty dekoratora (bardzo podstawowo)
            gene_info = {
                "function_name": function_name,
                "decorator_args": decorator_args,
                "type": "decorated_gene"
            }
            
            # Spróbuj wyciągnąć nazwę genu
            name_match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', decorator_args)
            if name_match:
                gene_info["name"] = name_match.group(1)
            else:
                gene_info["name"] = function_name
            
            genes.append(gene_info)
        
        print(f"🧬 Wykryto {len(genes)} genów w kodzie: {[g['name'] for g in genes]}")
        return genes
    
    @staticmethod
    async def register_module_and_genes(file_path: str) -> bool:
        """Rejestruje moduł i automatycznie wszystkie zawarte w nim geny"""
        try:
            print(f"📝 Rejestrowanie modułu i genów z pliku: {file_path}")
            
            # Załaduj soul z pliku
            soul = ModuleRegistry.load_module_file_as_soul(file_path)
            if not soul:
                print(f"❌ Nie udało się załadować soul z pliku: {file_path}")
                return False
            
            # Zapisz moduł do bazy danych
            from app_v2.database.soul_repository import SoulRepository
            success = await SoulRepository.save(soul)
            
            if not success:
                print(f"❌ Nie udało się zapisać modułu do bazy: {soul['genesis']['name']}")
                return False
            
            # Wykonaj kod modułu żeby zarejestrować geny przez dekoratory
            try:
                # Tworzymy tymczasową przestrzeń nazw
                temp_namespace = {}
                
                # Dodaj geny i dekoratory do namespace
                from app_v2.genetics import gene, requires, capability

                temp_namespace.update({
                    'gene': gene,
                    'requires': requires,
                    'capability': capability,
                    'print': print,  # Podstawowe funkcje
                    'datetime': __import__('datetime')
                })
                
                # Wykonaj kod - to zarejestruje geny przez dekoratory
                exec(soul['genesis']['code'], temp_namespace)
                
                # Zapisz wszystkie nowo zarejestrowane geny do bazy
                genes_saved = await GeneRegistry.register_all_genes_in_database()
                
                print(f"✅ Zarejestrowano moduł {soul['genesis']['name']} i {genes_saved} genów")
                return True
                
            except Exception as e:
                print(f"⚠️ Błąd podczas wykonywania kodu modułu {file_path}: {e}")
                # Moduł został zapisany, ale geny mogły nie zostać zarejestrowane
                return True
                
        except Exception as e:
            print(f"❌ Błąd podczas rejestracji modułu {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return False

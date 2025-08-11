
"""
Automatic Genotype Dictionary Loader
Ładuje genotypy z plików JSON w folderze genotypes/
"""

import os
import json
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime

from ..models.soul import Soul

class GenotypeDictionaryLoader:
    """Automatyczny loader genotypów ze słowników JSON"""
    
    def __init__(self, genotypes_folder: str = "genotypes"):
        self.genotypes_folder = genotypes_folder
        self.loaded_genotypes = {}
        self.load_log = []
        
    def scan_genotype_folder(self) -> List[str]:
        """Skanuje folder w poszukiwaniu plików .json z genotypami"""
        genotype_files = []
        
        if not os.path.exists(self.genotypes_folder):
            os.makedirs(self.genotypes_folder)
            print(f"📁 Utworzono folder: {self.genotypes_folder}")
            
        for root, dirs, files in os.walk(self.genotypes_folder):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    genotype_files.append(file_path)
                    
        return genotype_files
    
    def load_genotype_from_file(self, file_path: str) -> Dict[str, Any]:
        """Ładuje genotyp z pliku JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                genotype_data = json.load(f)
                
            # Walidacja podstawowej struktury
            required_fields = ["genesis", "attributes"]
            for field in required_fields:
                if field not in genotype_data:
                    raise ValueError(f"Brak wymaganego pola: {field}")
                    
            # Dodaj metadane o źródle
            if "genesis" not in genotype_data:
                genotype_data["genesis"] = {}
                
            genotype_data["genesis"]["source_file"] = file_path
            genotype_data["genesis"]["loaded_at"] = datetime.now().isoformat()
            genotype_data["genesis"]["loader_type"] = "dictionary_json"
            
            return genotype_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Błędny JSON w pliku {file_path}: {e}")
        except Exception as e:
            raise Exception(f"Błąd ładowania {file_path}: {e}")
    
    async def load_all_genotypes(self) -> List[Soul]:
        """Ładuje wszystkie genotypy z folderu i tworzy Soul"""
        loaded_souls = []
        genotype_files = self.scan_genotype_folder()
        
        print(f"📚 Znaleziono {len(genotype_files)} plików genotypów")
        
        for file_path in genotype_files:
            try:
                # Ładuj genotyp
                genotype_data = self.load_genotype_from_file(file_path)
                
                # Przygotuj alias z nazwy pliku
                file_name = Path(file_path).stem
                alias = genotype_data.get("genesis", {}).get("name", file_name)
                
                # Utwórz Soul
                soul = await Soul.create(genotype_data, alias=alias)
                loaded_souls.append(soul)
                
                # Log sukcesu
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "file_path": file_path,
                    "alias": alias,
                    "soul_hash": soul.soul_hash,
                    "status": "success"
                }
                self.load_log.append(log_entry)
                
                print(f"✅ Załadowano genotyp: {alias} ({file_path})")
                
            except Exception as e:
                # Log błędu
                log_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "file_path": file_path,
                    "status": "error",
                    "error": str(e)
                }
                self.load_log.append(log_entry)
                
                print(f"❌ Błąd ładowania {file_path}: {e}")
                
        print(f"🎯 Pomyślnie załadowano {len(loaded_souls)} genotypów")
        return loaded_souls
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Zwraca statystyki ładowania"""
        total = len(self.load_log)
        successful = len([log for log in self.load_log if log["status"] == "success"])
        failed = total - successful
        
        return {
            "total_files": total,
            "successful_loads": successful,
            "failed_loads": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "last_scan": datetime.now().isoformat()
        }
    
    def create_example_genotypes(self):
        """Tworzy przykładowe genotypy w folderze"""
        if not os.path.exists(self.genotypes_folder):
            os.makedirs(self.genotypes_folder)
            
        examples = [
            {
                "filename": "logger_being.json",
                "genotype": {
                    "genesis": {
                        "name": "logger_being",
                        "type": "utility_being",
                        "description": "Simple logging utility being",
                        "version": "1.0.0"
                    },
                    "attributes": {
                        "log_level": {"py_type": "str", "default": "INFO"},
                        "log_file": {"py_type": "str", "default": "app.log"},
                        "max_file_size": {"py_type": "int", "default": 10485760}
                    },
                    "capabilities": {
                        "can_log": True,
                        "can_rotate_logs": True,
                        "can_filter_levels": True
                    }
                }
            },
            {
                "filename": "math_calculator.json", 
                "genotype": {
                    "genesis": {
                        "name": "math_calculator",
                        "type": "computation_being",
                        "description": "Mathematical calculations being",
                        "version": "1.0.0"
                    },
                    "attributes": {
                        "precision": {"py_type": "int", "default": 10},
                        "last_result": {"py_type": "float", "default": 0.0},
                        "operation_history": {"py_type": "List[str]", "default": []}
                    },
                    "capabilities": {
                        "basic_math": True,
                        "advanced_math": False,
                        "statistics": True
                    }
                }
            },
            {
                "filename": "message_processor.json",
                "genotype": {
                    "genesis": {
                        "name": "message_processor", 
                        "type": "communication_being",
                        "description": "Message processing and routing being",
                        "version": "1.0.0"
                    },
                    "attributes": {
                        "max_message_length": {"py_type": "int", "default": 1000},
                        "encoding": {"py_type": "str", "default": "utf-8"},
                        "processed_count": {"py_type": "int", "default": 0}
                    },
                    "capabilities": {
                        "can_process": True,
                        "can_route": True,
                        "can_validate": True
                    }
                }
            }
        ]
        
        for example in examples:
            file_path = os.path.join(self.genotypes_folder, example["filename"])
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(example["genotype"], f, indent=2, ensure_ascii=False)
                print(f"📝 Utworzono przykład: {file_path}")

# Globalna instancja
genotype_loader = GenotypeDictionaryLoader()

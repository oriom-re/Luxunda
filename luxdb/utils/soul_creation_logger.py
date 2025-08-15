
#!/usr/bin/env python3
"""
🧬 Soul Creation Logger - System logowania tworzenia dusz z raportami

Każde utworzenie Soul generuje szczegółowy raport z unikalnym hashem.
Umożliwia łatwe śledzenie wersji i wykorzystanie hashów w produkcji.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class SoulCreationLogger:
    """Logger dla procesu tworzenia dusz z generowaniem raportów"""
    
    def __init__(self, logs_dir: str = "logs/souls"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def log_soul_creation(self, soul: 'Soul', creation_context: Dict[str, Any] = None) -> str:
        """
        Loguje utworzenie Soul i generuje szczegółowy raport.
        
        Args:
            soul: Utworzona Soul
            creation_context: Dodatkowy kontekst tworzenia
            
        Returns:
            Ścieżka do wygenerowanego raportu
        """
        timestamp = datetime.now()
        
        # Przygotuj dane raportu
        report_data = {
            "soul_info": {
                "soul_hash": soul.soul_hash,
                "alias": soul.alias,
                "global_ulid": soul.global_ulid,
                "version": soul.get_version(),
                "parent_hash": soul.get_parent_hash(),
                "created_at": timestamp.isoformat()
            },
            "genotype": {
                "genesis": soul.genotype.get("genesis", {}),
                "attributes": soul.genotype.get("attributes", {}),
                "functions": soul.genotype.get("functions", {}),
                "capabilities": soul.genotype.get("capabilities", {}),
                "dependencies": soul.genotype.get("dependencies", {})
            },
            "analysis": {
                "has_module_source": soul.has_module_source(),
                "language": soul.get_language(),
                "functions_count": len(soul._function_registry),
                "public_functions": [f for f in soul.genotype.get("functions", {}) if not f.startswith('_')],
                "private_functions": [f for f in soul._function_registry if f.startswith('_')],
                "attribute_types": soul.get_attribute_types(),
                "is_evolution": bool(soul.get_parent_hash())
            },
            "creation_context": creation_context or {},
            "system_info": {
                "timestamp": timestamp.isoformat(),
                "luxos_version": "3.0.0-unified",
                "creation_method": "Soul.create"
            }
        }
        
        # Generuj nazwę pliku z hashem i timestampem
        report_filename = f"{soul.soul_hash[:16]}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.logs_dir / report_filename
        
        # Zapisz raport
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        # Utwórz skrócony raport tekstowy
        self._create_summary_report(soul, report_data, report_path.with_suffix('.md'))
        
        # Aktualizuj indeks hashów
        self._update_hash_index(soul, report_filename)
        
        print(f"📝 Soul creation report generated: {report_path}")
        return str(report_path)
        
    def _create_summary_report(self, soul: 'Soul', report_data: Dict[str, Any], summary_path: Path):
        """Tworzy skrócony raport tekstowy"""
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(f"# Soul Creation Report\n\n")
            f.write(f"## 🧬 Soul Information\n")
            f.write(f"- **Hash**: `{soul.soul_hash}`\n")
            f.write(f"- **Alias**: {soul.alias}\n")
            f.write(f"- **Version**: {soul.get_version()}\n")
            f.write(f"- **Created**: {report_data['system_info']['timestamp']}\n\n")
            
            if soul.get_parent_hash():
                f.write(f"- **Parent Hash**: `{soul.get_parent_hash()}`\n")
                f.write(f"- **Evolution**: Yes\n\n")
            else:
                f.write(f"- **Evolution**: No (Original)\n\n")
                
            f.write(f"## 🔧 Technical Details\n")
            f.write(f"- **Language**: {soul.get_language()}\n")
            f.write(f"- **Functions**: {len(soul._function_registry)} total\n")
            f.write(f"- **Public Functions**: {len(report_data['analysis']['public_functions'])}\n")
            f.write(f"- **Private Functions**: {len(report_data['analysis']['private_functions'])}\n")
            f.write(f"- **Attributes**: {len(report_data['genotype']['attributes'])}\n")
            f.write(f"- **Has Module Source**: {soul.has_module_source()}\n\n")
            
            if report_data['analysis']['public_functions']:
                f.write(f"## 🎯 Public Functions\n")
                for func_name in report_data['analysis']['public_functions']:
                    f.write(f"- `{func_name}()`\n")
                f.write("\n")
                
            f.write(f"## 📊 Production Usage\n")
            f.write(f"```python\n")
            f.write(f"# By hash (production - immutable)\n")
            f.write(f"soul = await Soul.get_by_hash('{soul.soul_hash}')\n\n")
            f.write(f"# By alias (development - current version)\n")
            f.write(f"soul = await Soul.get_by_alias('{soul.alias}')\n")
            f.write(f"```\n")
            
    def _update_hash_index(self, soul: 'Soul', report_filename: str):
        """Aktualizuje indeks hashów dla łatwego wyszukiwania"""
        index_path = self.logs_dir / "hash_index.json"
        
        # Ładuj istniejący indeks
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"souls": {}, "aliases": {}}
            
        # Dodaj nową Soul do indeksu
        index["souls"][soul.soul_hash] = {
            "alias": soul.alias,
            "version": soul.get_version(),
            "parent_hash": soul.get_parent_hash(),
            "report_file": report_filename,
            "created_at": datetime.now().isoformat()
        }
        
        # Aktualizuj indeks aliasów
        if soul.alias not in index["aliases"]:
            index["aliases"][soul.alias] = []
        index["aliases"][soul.alias].append({
            "soul_hash": soul.soul_hash,
            "version": soul.get_version(),
            "created_at": datetime.now().isoformat()
        })
        
        # Zapisz zaktualizowany indeks
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
            
    def get_soul_by_hash(self, soul_hash: str) -> Optional[Dict[str, Any]]:
        """Pobiera informacje o Soul z indeksu na podstawie hash"""
        index_path = self.logs_dir / "hash_index.json"
        if not index_path.exists():
            return None
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
            
        return index["souls"].get(soul_hash)
        
    def get_souls_by_alias(self, alias: str) -> Optional[list]:
        """Pobiera wszystkie wersje Soul dla danego aliasu"""
        index_path = self.logs_dir / "hash_index.json"
        if not index_path.exists():
            return None
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
            
        return index["aliases"].get(alias)
        
    def generate_production_hash_list(self, output_file: str = "production_hashes.txt"):
        """Generuje listę hashów do użycia w produkcji"""
        index_path = self.logs_dir / "hash_index.json"
        if not index_path.exists():
            print("❌ No hash index found")
            return
            
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
            
        output_path = self.logs_dir / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# LuxOS Production Soul Hashes\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            
            for soul_hash, info in index["souls"].items():
                f.write(f"{soul_hash}  # {info['alias']} v{info['version']}\n")
                
        print(f"✅ Production hash list generated: {output_path}")

# Globalna instancja loggera
soul_creation_logger = SoulCreationLogger()

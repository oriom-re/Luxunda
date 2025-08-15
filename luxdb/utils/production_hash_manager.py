
#!/usr/bin/env python3
"""
🏭 Production Hash Manager - Narzędzia do zarządzania hashami produkcyjnymi

Wykorzystuje logi tworzenia dusz do zarządzania wersjami produkcyjnymi.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class ProductionHashManager:
    """Manager hashów dla środowiska produkcyjnego"""
    
    def __init__(self, logs_dir: str = "logs/souls"):
        self.logs_dir = Path(logs_dir)
        self.production_config_path = self.logs_dir / "production_config.json"
        
    def promote_to_production(self, soul_hash: str, environment: str = "production") -> bool:
        """
        Promuje Soul hash do środowiska produkcyjnego.
        
        Args:
            soul_hash: Hash Soul do promowania
            environment: Środowisko ('production', 'staging', etc.)
            
        Returns:
            True jeśli promocja się powiodła
        """
        # Sprawdź czy hash istnieje w logach
        from .soul_creation_logger import soul_creation_logger
        soul_info = soul_creation_logger.get_soul_by_hash(soul_hash)
        
        if not soul_info:
            print(f"❌ Soul hash {soul_hash} not found in logs")
            return False
            
        # Ładuj konfigurację produkcyjną
        if self.production_config_path.exists():
            with open(self.production_config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {"environments": {}}
            
        # Dodaj do środowiska
        if environment not in config["environments"]:
            config["environments"][environment] = {}
            
        config["environments"][environment][soul_hash] = {
            "alias": soul_info["alias"],
            "version": soul_info["version"],
            "promoted_at": datetime.now().isoformat(),
            "report_file": soul_info["report_file"]
        }
        
        # Zapisz konfigurację
        with open(self.production_config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"✅ Soul {soul_hash[:16]}... promoted to {environment}")
        return True
        
    def get_production_souls(self, environment: str = "production") -> Dict[str, Dict]:
        """Zwraca wszystkie Soul w danym środowisku"""
        if not self.production_config_path.exists():
            return {}
            
        with open(self.production_config_path, 'r') as f:
            config = json.load(f)
            
        return config.get("environments", {}).get(environment, {})
        
    def generate_deployment_manifest(self, environment: str = "production") -> str:
        """Generuje manifest deploymentu dla danego środowiska"""
        souls = self.get_production_souls(environment)
        
        manifest_path = self.logs_dir / f"deployment_manifest_{environment}.json"
        
        manifest = {
            "environment": environment,
            "generated_at": datetime.now().isoformat(),
            "souls_count": len(souls),
            "souls": souls
        }
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
        print(f"📦 Deployment manifest for {environment}: {manifest_path}")
        return str(manifest_path)
        
    def validate_production_hashes(self, environment: str = "production") -> Dict[str, List]:
        """Waliduje czy wszystkie produkcyjne hashe są dostępne"""
        souls = self.get_production_souls(environment)
        
        valid_hashes = []
        invalid_hashes = []
        
        from .soul_creation_logger import soul_creation_logger
        
        for soul_hash in souls.keys():
            soul_info = soul_creation_logger.get_soul_by_hash(soul_hash)
            if soul_info:
                valid_hashes.append(soul_hash)
            else:
                invalid_hashes.append(soul_hash)
                
        return {
            "valid": valid_hashes,
            "invalid": invalid_hashes
        }

# Globalna instancja
production_hash_manager = ProductionHashManager()

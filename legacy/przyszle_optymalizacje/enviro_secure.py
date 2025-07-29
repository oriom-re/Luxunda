from typing import Dict, Set, Any, Optional
import sys
import os
import subprocess
import importlib

class SecurityLevel:
    """Poziomy bezpieczeństwa dla bytów"""
    RESTRICTED = "restricted"     # Podstawowe funkcje
    TRUSTED = "trusted"          # Dostęp do plików
    SYSTEM = "system"            # Pełny dostęp systemowy
    ROOT = "root"                # Nieograniczony dostęp

class SecureBuiltins:
    """Bezpieczne wersje funkcji systemowych"""
    
    @staticmethod
    def safe_print(*args, **kwargs):
        """Bezpieczny print z logowaniem"""
        # Można dodać filtrowanie/logowanie
        print(*args, **kwargs)
    
    @staticmethod
    def restricted_import(name, *args, **kwargs):
        """Ograniczony import - tylko białe listy"""
        allowed_modules = {
            'json', 'datetime', 'math', 'random', 'asyncio',
            'typing', 'collections', 're', 'hashlib'
        }
        if name in allowed_modules:
            return __import__(name, *args, **kwargs)
        raise ImportError(f"Moduł {name} nie jest dozwolony dla tego poziomu bezpieczeństwa")
    
    @staticmethod
    def no_access(*args, **kwargs):
        """Funkcja blokująca dostęp"""
        raise PermissionError("Brak uprawnień do tej funkcji")

class VirtualEnvironmentSecurity:
    """Menedżer bezpieczeństwa dla wirtualnych środowisk"""
    
    # Definicje poziomów bezpieczeństwa
    SECURITY_PROFILES = {
        SecurityLevel.RESTRICTED: {
            'allowed_builtins': {
                'print': SecureBuiltins.safe_print,
                '__import__': SecureBuiltins.restricted_import,
                'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple',
                'range', 'enumerate', 'zip', 'map', 'filter', 'sorted',
            },
            'blocked_builtins': {
                'exec': SecureBuiltins.no_access,
                'eval': SecureBuiltins.no_access,
                'open': SecureBuiltins.no_access,
                'compile': SecureBuiltins.no_access,
            },
            'blocked_modules': ['os', 'sys', 'subprocess', 'importlib']
        },
        
        SecurityLevel.TRUSTED: {
            'allowed_builtins': {
                'open': lambda *args, **kwargs: open(*args, **kwargs),  # Kontrolowany dostęp
            },
            'additional_modules': ['pathlib', 'tempfile'],
        },
        
        SecurityLevel.SYSTEM: {
            'allowed_modules': ['os', 'sys', 'subprocess'],
            'restricted_functions': {
                'os.system': 'controlled_system',  # Zastąp kontrolowaną wersją
                'subprocess.run': 'controlled_subprocess',
            }
        },
        
        SecurityLevel.ROOT: {
            'unrestricted': True  # Pełny dostęp
        }
    }
    
    @classmethod
    def create_secure_builtins(cls, security_level: str) -> Dict[str, Any]:
        """Tworzy bezpieczne builtins dla danego poziomu"""
        profile = cls.SECURITY_PROFILES.get(security_level, cls.SECURITY_PROFILES[SecurityLevel.RESTRICTED])
        
        if profile.get('unrestricted'):
            return dict(__builtins__)
        
        # Startujemy z bezpiecznymi podstawami
        secure_builtins = {
            # Podstawowe typy i funkcje
            'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'range': range, 'enumerate': enumerate, 'zip': zip,
            'map': map, 'filter': filter, 'sorted': sorted, 'reversed': reversed,
            'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
            
            # Bezpieczne wersje
            'print': SecureBuiltins.safe_print,
            '__import__': SecureBuiltins.restricted_import,
        }
        
        # Dodaj dozwolone builtins
        allowed = profile.get('allowed_builtins', {})
        secure_builtins.update(allowed)
        
        # Zablokuj niebezpieczne funkcje
        blocked = profile.get('blocked_builtins', {})
        secure_builtins.update(blocked)
        
        return secure_builtins

# Rozszerzenie klasy Genotype
# filepath: /home/runner/workspace/app/beings/genotype.py
class Genotype(Being):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.security_level = self.determine_security_level()
        self._secure_context = None
    
    def determine_security_level(self) -> str:
        """Określa poziom bezpieczeństwa na podstawie atrybutów bytu"""
        # Sprawdź atrybuty bytu
        security_attr = self.attributes.get('security_level')
        if security_attr:
            return security_attr
        
        # Sprawdź na podstawie roli
        role = self.genesis.get('role', '')
        if role == 'system_admin':
            return SecurityLevel.SYSTEM
        elif role == 'file_manager':
            return SecurityLevel.TRUSTED
        elif role in ['logger', 'monitor', 'basic']:
            return SecurityLevel.RESTRICTED
        
        # Domyślnie najbardziej restrykcyjny
        return SecurityLevel.RESTRICTED
    
    def create_secure_context(self) -> Dict[str, Any]:
        """Tworzy bezpieczny kontekst dla tego bytu"""
        if self._secure_context is None:
            # Podstawowy bezpieczny kontekst
            secure_builtins = VirtualEnvironmentSecurity.create_secure_builtins(self.security_level)
            
            self._secure_context = {
                '__name__': f'entity_{self.uid[:8]}',
                '__builtins__': secure_builtins,
                
                # Kontekst bytu (zawsze dostępny)
                'entity': self,
                'entity_name': self.genesis.get('name', 'Unknown'),
                'entity_uid': self.uid,
                'security_level': self.security_level,
                
                # Bezpieczne metody bytu
                'log': self.create_secure_logger(),
                'remember': self.remember,
                'recall': self.recall,
                
                # Kontrolowane funkcje systemowe (tylko dla uprzywilejowanych)
                **self.get_privileged_functions()
            }
        
        return self._secure_context
    
    def get_privileged_functions(self) -> Dict[str, Any]:
        """Zwraca funkcje uprzywilejowane na podstawie poziomu bezpieczeństwa"""
        if self.security_level == SecurityLevel.ROOT:
            return {
                'sys': sys,
                'os': os,
                'subprocess': subprocess,
                'importlib': importlib,
                'exec': exec,
                'eval': eval,
            }
        elif self.security_level == SecurityLevel.SYSTEM:
            return {
                'controlled_system': self.controlled_system,
                'controlled_subprocess': self.controlled_subprocess,
                'safe_import': self.safe_import,
            }
        elif self.security_level == SecurityLevel.TRUSTED:
            return {
                'safe_file_access': self.safe_file_access,
                'list_directory': self.list_directory,
            }
        else:
            return {}  # RESTRICTED - brak uprzywilejowanych funkcji
    
    def controlled_system(self, command: str):
        """Kontrolowana wersja os.system"""
        allowed_commands = ['ls', 'pwd', 'date', 'whoami']
        cmd_parts = command.strip().split()
        if cmd_parts and cmd_parts[0] in allowed_commands:
            self.log(f"Executing controlled command: {command}", "SYSTEM")
            return os.system(command)
        else:
            self.log(f"Blocked dangerous command: {command}", "SECURITY")
            raise PermissionError(f"Command '{command}' not allowed")
    
    def controlled_subprocess(self, *args, **kwargs):
        """Kontrolowana wersja subprocess.run"""
        self.log(f"Subprocess request: {args}", "SYSTEM")
        # Dodaj tutaj logikę walidacji
        return subprocess.run(*args, **kwargs)
    
    def safe_file_access(self, path: str, mode: str = 'r'):
        """Bezpieczny dostęp do plików"""
        # Sprawdź czy ścieżka jest dozwolona
        allowed_paths = ['/tmp/', './data/', './logs/']
        if any(path.startswith(allowed) for allowed in allowed_paths):
            self.log(f"File access: {path} ({mode})", "FILE")
            return open(path, mode)
        else:
            raise PermissionError(f"Access to {path} not allowed")
    
    async def load_and_run_genotype(self, genotype_name, call_init: bool = True):
        soul = await self.get_soul_by_name(genotype_name)
        if not soul:
            print(f"❌ Nie znaleziono duszy dla nazwy: {genotype_name}")
            return None
        
        print(f"🔍 Ładowanie modułu {genotype_name} z poziomem bezpieczeństwa: {self.security_level}")
        
        if genotype_name in self.cxt:
            return self.cxt[genotype_name]

        try:
            # Tworzymy moduł z bezpiecznym kontekstem
            spec = importlib.util.spec_from_loader(genotype_name, loader=None, origin="virtual")
            genotype = importlib.util.module_from_spec(spec)
            
            # 🔒 Wykonujemy kod w bezpiecznym kontekście
            secure_context = self.create_secure_context()
            exec(soul['genesis']['code'], secure_context)
            
            # Kopiujemy wyniki do modułu
            for key, value in secure_context.items():
                if not key.startswith('__') and key not in ['entity', 'entity_name', 'entity_uid']:
                    setattr(genotype, key, value)
            
            self.cxt[genotype_name] = genotype
            
            # Inicjalizacja
            if call_init and hasattr(genotype, "init"):
                await self.maybe_async(genotype.init)
                print(f"✅ Moduł {genotype_name} zainicjalizowany bezpiecznie")
            
            return genotype
            
        except PermissionError as e:
            print(f"🔒 Naruszenie bezpieczeństwa w module {genotype_name}: {e}")
            return None
        except Exception as e:
            print(f"❌ Błąd podczas ładowania modułu {genotype_name}: {e}")
            return None
        

# przykładowe użycie w kodzie testowym
async def main():
    # ...existing code...
    
    # Byt z ograniczeniami (logger)
    logger_genesis = {"name": "Logger", "role": "logger"}
    logger_attributes = {"security_level": "restricted"}
    logger = Genotype(uid=str(uuid.uuid4()), genesis=logger_genesis, 
                     attributes=logger_attributes, memories=[], self_awareness={})
    
    # Byt systemowy (administrator)
    admin_genesis = {"name": "SystemAdmin", "role": "system_admin"}
    admin_attributes = {"security_level": "system"}
    admin = Genotype(uid=str(uuid.uuid4()), genesis=admin_genesis,
                    attributes=admin_attributes, memories=[], self_awareness={})
    
    # Test bezpieczeństwa
    await logger.load_and_run_genotype("gen_logger")  # Ograniczony dostęp
    await admin.load_and_run_genotype("system_manager")  # Pełny dostęp
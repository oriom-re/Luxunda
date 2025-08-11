
"""
Module Validator for .module files
"""

import ast
import inspect
import asyncio
from typing import Dict, Any, List
from pathlib import Path


class ModuleValidator:
    """Validator for .module files"""
    
    @staticmethod
    def validate_file(file_path: str) -> Dict[str, Any]:
        """
        Waliduje plik .module
        
        Args:
            file_path: Ścieżka do pliku .module
            
        Returns:
            Wynik walidacji
        """
        result = {
            "valid": False,
            "file_path": file_path,
            "errors": [],
            "warnings": [],
            "info": {}
        }
        
        try:
            module_path = Path(file_path)
            
            if not module_path.exists():
                result["errors"].append(f"File does not exist: {file_path}")
                return result
                
            if module_path.suffix != '.module':
                result["warnings"].append("File should have .module extension")
                
            # Wczytaj kod
            with open(module_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                
            # Waliduj składnię
            try:
                ast.parse(source_code)
            except SyntaxError as e:
                result["errors"].append(f"Syntax error: {e}")
                return result
                
            # Analizuj zawartość
            analysis = ModuleValidator.analyze_module_source(source_code)
            result["info"] = analysis
            
            # Sprawdź czy ma wymagane funkcje
            if analysis["has_init"]:
                result["info"]["init_function"] = "✅ Found init function"
            else:
                result["warnings"].append("No init function found")
                
            if analysis["has_execute"]:
                result["info"]["execute_function"] = "✅ Found execute function"
            else:
                result["warnings"].append("No execute function found")
                
            result["valid"] = len(result["errors"]) == 0
            
        except Exception as e:
            result["errors"].append(f"Validation error: {e}")
            
        return result
    
    @staticmethod
    def analyze_module_source(source_code: str) -> Dict[str, Any]:
        """
        Analizuje kod źródłowy modułu z szczegółową analizą typów
        
        Args:
            source_code: Kod źródłowy do analizy
            
        Returns:
            Szczegółowa analiza modułu
        """
        analysis = {
            "functions": {},
            "attributes": {},
            "has_init": False,
            "has_execute": False,
            "async_functions": [],
            "private_functions": [],
            "language": "python",
            "python_version": None
        }
        
        try:
            import sys
            analysis["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            # Wykonaj kod w izolowanym środowisku
            temp_globals = {"__name__": "__temp_module__"}
            exec(source_code, temp_globals)
            
            # Analizuj elementy
            for name, obj in temp_globals.items():
                if name.startswith('__'):  # Pomijaj dunder methods
                    continue
                    
                if name.startswith('_'):
                    if callable(obj):
                        analysis["private_functions"].append(name)
                    continue
                    
                if callable(obj):
                    # Szczegółowa analiza funkcji
                    try:
                        sig = inspect.signature(obj)
                        is_async = asyncio.iscoroutinefunction(obj)
                        
                        analysis["functions"][name] = {
                            "py_type": "function",
                            "is_async": is_async,
                            "parameters": {
                                param.name: {
                                    "type": str(param.annotation) if param.annotation != param.empty else "Any",
                                    "default": repr(param.default) if param.default != param.empty else None,
                                    "required": param.default == param.empty
                                }
                                for param in sig.parameters.values()
                            },
                            "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any",
                            "signature": str(sig),
                            "docstring": getattr(obj, '__doc__', None)
                        }
                        
                        if is_async:
                            analysis["async_functions"].append(name)
                            
                        if name == 'init':
                            analysis["has_init"] = True
                        elif name == 'execute':
                            analysis["has_execute"] = True
                            
                    except Exception as e:
                        analysis["functions"][name] = {
                            "py_type": "function",
                            "error": str(e)
                        }
                else:
                    # Szczegółowa analiza atrybutów
                    obj_type = type(obj)
                    type_name = obj_type.__name__
                    
                    analysis["attributes"][name] = {
                        "py_type": type_name,
                        "full_type": f"{obj_type.__module__}.{type_name}" if obj_type.__module__ != 'builtins' else type_name,
                        "value": obj if isinstance(obj, (str, int, float, bool, type(None))) else repr(obj)[:100],
                        "is_optional": obj is None,
                        "is_mutable": isinstance(obj, (list, dict, set)),
                        "is_constant": name.isupper(),
                        "size": len(obj) if hasattr(obj, '__len__') else None
                    }
                    
        except Exception as e:
            analysis["error"] = str(e)
            
        return analysis
    
    @staticmethod
    def validate_directory(directory_path: str) -> Dict[str, Any]:
        """
        Waliduje wszystkie pliki .module w katalogu
        
        Args:
            directory_path: Ścieżka do katalogu
            
        Returns:
            Wyniki walidacji wszystkich plików
        """
        directory = Path(directory_path)
        results = {
            "directory": str(directory),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "files": {}
        }
        
        if not directory.exists():
            results["error"] = f"Directory does not exist: {directory_path}"
            return results
            
        # Znajdź wszystkie pliki .module
        module_files = list(directory.glob("*.module"))
        results["total_files"] = len(module_files)
        
        for module_file in module_files:
            file_result = ModuleValidator.validate_file(str(module_file))
            results["files"][module_file.name] = file_result
            
            if file_result["valid"]:
                results["valid_files"] += 1
            else:
                results["invalid_files"] += 1
                
        return results


# CLI interface for module validation
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python module_validator.py <file_or_directory>")
        sys.exit(1)
        
    target_path = sys.argv[1]
    path = Path(target_path)
    
    if path.is_file():
        # Waliduj pojedynczy plik
        result = ModuleValidator.validate_file(target_path)
        
        print(f"\n🔍 Validating: {target_path}")
        print(f"Valid: {'✅' if result['valid'] else '❌'}")
        
        if result["errors"]:
            print("\n❌ Errors:")
            for error in result["errors"]:
                print(f"  - {error}")
                
        if result["warnings"]:
            print("\n⚠️ Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
                
        if result["info"]:
            print("\n📊 Analysis:")
            info = result["info"]
            print(f"  Functions: {len(info.get('functions', {}))}")
            print(f"  Attributes: {len(info.get('attributes', {}))}")
            print(f"  Has init: {'✅' if info.get('has_init') else '❌'}")
            print(f"  Has execute: {'✅' if info.get('has_execute') else '❌'}")
            
            if info.get('async_functions'):
                print(f"  Async functions: {', '.join(info['async_functions'])}")
                
    elif path.is_dir():
        # Waliduj katalog
        results = ModuleValidator.validate_directory(target_path)
        
        print(f"\n🔍 Validating directory: {target_path}")
        print(f"Total files: {results['total_files']}")
        print(f"Valid: {results['valid_files']} ✅")
        print(f"Invalid: {results['invalid_files']} ❌")
        
        for filename, file_result in results["files"].items():
            status = "✅" if file_result["valid"] else "❌"
            print(f"\n{status} {filename}")
            
            if file_result["errors"]:
                for error in file_result["errors"]:
                    print(f"    ❌ {error}")
                    
            if file_result["warnings"]:
                for warning in file_result["warnings"]:
                    print(f"    ⚠️ {warning}")
    else:
        print(f"❌ Path not found: {target_path}")
        sys.exit(1)

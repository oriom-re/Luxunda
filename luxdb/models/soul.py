"""
Model Soul (Dusza/Genotyp) dla LuxDB.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
import ulid
import inspect
import asyncio

from ..core.globals import Globals

@dataclass
class Soul:
    """
    Soul reprezentuje genotyp - szablon dla bytów.

    Każdy Soul ma unikalny hash wygenerowany z genotypu
    i może być używany do tworzenia wielu Being (bytów).
    """

    soul_hash: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    alias: str = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Function registry for this soul
    _function_registry: Dict[str, Callable] = field(default_factory=dict, init=False, repr=False)

    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """
        Tworzy Soul na podstawie genotypu. 
        Jeśli Soul o tym samym hash już istnieje - zwraca istniejący.
        To zapewnia unikalność i bezpieczeństwo.

        Args:
            genotype: Definicja struktury danych (słownik)
            alias: OBOWIĄZKOWY alias dla Soul

        Returns:
            Soul (nowy lub istniejący)
        """
        if not alias:
            raise ValueError("Alias is required for Soul creation")
        from ..utils.validators import validate_genotype
        from ..repository.soul_repository import SoulRepository

        # Automatycznie rozpoznaj funkcje publiczne z module_source
        processed_genotype = cls._process_module_source_for_genotype(genotype.copy())

        # Walidacja genotypu
        is_valid, validation_errors = validate_genotype(processed_genotype)
        if not is_valid:
            error_message = f"Genotype validation failed: {'; '.join(validation_errors)}"
            print(f"❌ {error_message}")
            raise ValueError(error_message)

        # Generuj hash z genotypu - to jest unikalny kod genetyczny
        soul_hash = hashlib.sha256(
            json.dumps(processed_genotype, sort_keys=True).encode()
        ).hexdigest()

        # Sprawdź czy Soul o tym hash już istnieje
        existing_soul = await cls.get_by_hash(soul_hash)
        if existing_soul:
            # Aktualizuj alias jeśli podano nowy
            if alias and existing_soul.alias != alias:
                existing_soul.alias = alias
                await SoulRepository.set(existing_soul)
            return existing_soul

        # Utwórz nową Soul
        soul = cls()
        soul.alias = alias
        soul.genotype = processed_genotype
        soul.soul_hash = soul_hash
        # created_at będzie ustawione automatycznie przez bazę danych

        # Załaduj moduł i zarejestruj funkcje w rejestrze
        if soul.has_module_source():
            soul._load_and_register_module_functions()

        # Zapis do bazy danych - baza automatycznie ustawi created_at/updated_at
        result = await SoulRepository.set(soul)
        if not result.get('success'):
            error_details = result.get('error', 'Unknown database error')
            error_type = result.get('error_type', 'general_error')
            raise Exception(f"Failed to create soul ({error_type}): {error_details}")

        # Loguj utworzenie Soul z raportem
        try:
            from ..utils.soul_creation_logger import soul_creation_logger
            soul_creation_logger.log_soul_creation(soul, {
                "method": "Soul.create",
                "genotype_processed": True,
                "function_registry_loaded": bool(soul.has_module_source()),
                "validation_passed": True
            })
        except Exception as e:
            print(f"⚠️ Soul creation logging failed: {e}")

        return soul

    @classmethod
    async def get(cls, **kwargs) -> Optional['Soul']:
        """
        Uniwersalna metoda get dla Soul.

        Args:
            **kwargs: Parametry wyszukiwania (alias, hash, itp.)

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        if 'alias' in kwargs:
            return await cls.get_by_alias(kwargs['alias'])
        elif 'hash' in kwargs:
            return await cls.get_by_hash(kwargs['hash'])
        elif 'soul_hash' in kwargs:
            return await cls.get_by_hash(kwargs['soul_hash'])
        else:
            # Jeśli podano tylko alias jako pierwszy argument
            for value in kwargs.values():
                if isinstance(value, str):
                    # Próbuj najpierw alias, potem hash
                    soul = await cls.get_by_alias(value)
                    if soul:
                        return soul
                    return await cls.get_by_hash(value)
        return None

    @classmethod
    async def set(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """
        Metoda set dla Soul (alias dla create).

        Args:
            genotype: Definicja struktury danych
            alias: Opcjonalny alias

        Returns:
            Nowy obiekt Soul
        """
        return await cls.create(genotype, alias)

    @classmethod
    async def get_by_hash(cls, soul_hash: str) -> Optional['Soul']:
        """
        Ładuje Soul po jego hash (kodzie genetycznym).

        Args:
            soul_hash: Hash wygenerowany z genotypu - unikalny kod genetyczny

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_soul_by_hash(soul_hash)
        return result.get('soul') if result.get('success') else None

    @classmethod
    async def get_by_alias(cls, alias: str) -> Optional['Soul']:
        """
        Ładuje Soul po aliasie.

        Args:
            alias: Alias soul

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_by_alias(alias)
        return result.get('soul') if result.get('success') else None

    @classmethod
    async def get_all(cls) -> List['Soul']:
        """
        Ładuje wszystkie Soul z bazy danych.

        Returns:
            Lista wszystkich Soul
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_all_souls()
        souls = result.get('souls', [])
        return [soul for soul in souls if soul is not None]

    @classmethod
    async def get_all_by_alias(cls, alias: str) -> List['Soul']:
        """
        Ładuje wszystkie Soul o danym aliasie.

        Args:
            alias: Alias do wyszukania

        Returns:
            Lista Soul o podanym aliasie
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_all_by_alias(alias)
        souls = result.get('souls', [])
        return [soul for soul in souls if soul is not None]



    def get_attribute_types(self) -> Dict[str, str]:
        """
        Zwraca mapowanie nazw atrybutów na ich typy.

        Returns:
            Słownik {nazwa_atrybutu: typ_py}
        """
        attributes = self.genotype.get("attributes", {})
        return {
            name: attr.get("py_type", "str")
            for name, attr in attributes.items()
        }

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Waliduje dane względem genotypu.

        Args:
            data: Dane do walidacji

        Returns:
            Lista błędów walidacji (pusta jeśli brak błędów)
        """
        errors = []
        
        # Fix: Ensure genotype is dict, not string
        if isinstance(self.genotype, str):
            try:
                import json
                genotype_dict = json.loads(self.genotype)
            except:
                print(f"❌ ERROR: genotype is string but cannot parse as JSON: {self.genotype}")
                return ["Invalid genotype format - cannot parse as JSON"]
        else:
            genotype_dict = self.genotype
            
        attributes = genotype_dict.get("attributes", {})

        for attr_name, attr_config in attributes.items():
            py_type = attr_config.get("py_type", "str")
            value = data.get(attr_name)

            # Sprawdź wymagane pola
            if value is None and not attr_config.get("default"):
                errors.append(f"Missing required attribute: {attr_name}")
                continue

            # Sprawdź typ
            if value is not None:
                if py_type == "str" and not isinstance(value, str):
                    errors.append(f"Attribute {attr_name} must be string")
                elif py_type == "int" and not isinstance(value, int):
                    errors.append(f"Attribute {attr_name} must be integer")
                elif py_type == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Attribute {attr_name} must be float")
                elif py_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Attribute {attr_name} must be boolean")
                elif py_type == "dict" and not isinstance(value, dict):
                    errors.append(f"Attribute {attr_name} must be dict")
                elif py_type.startswith("List[") and not isinstance(value, list):
                    errors.append(f"Attribute {attr_name} must be list")

        return errors

    async def get_hash(self) -> str:
        """Zwraca hash Soul"""
        return self.soul_hash



    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Soul do słownika dla serializacji"""
        return {
            'soul_hash': self.soul_hash,
            'global_ulid': self.global_ulid,
            'alias': self.alias,
            'genotype': self.genotype,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_json_serializable(self) -> Dict[str, Any]:
        """Automatycznie wykrywa i konwertuje strukturę do JSON-serializable"""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Soul':
        """Tworzy Soul z słownika"""
        soul = cls()
        soul.soul_hash = data.get('soul_hash')
        soul.global_ulid = data.get('global_ulid', Globals.GLOBAL_ULID)
        soul.alias = data.get('alias')
        
        # Deserializacja genotype - może być string (JSON z bazy) lub dict
        genotype_data = data.get('genotype', {})
        if isinstance(genotype_data, str):
            try:
                soul.genotype = json.loads(genotype_data)
            except json.JSONDecodeError:
                print(f"⚠️ Failed to parse genotype JSON: {genotype_data}")
                soul.genotype = {}
        else:
            soul.genotype = genotype_data
            
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                soul.created_at = datetime.fromisoformat(data['created_at'])
            else:
                soul.created_at = data['created_at']
        return soul

    def __json__(self):
        """Protokół dla automatycznej serializacji JSON"""
        return self.to_dict()

    def _register_immutable_function(self, name: str, func: Callable):
        """
        Rejestruje funkcję w niezmiennym rejestrze (tylko wewnętrznie).
        Ta metoda nie modyfikuje genotypu - funkcje muszą być zdefiniowane przy tworzeniu.
        """
        self._function_registry[name] = func

    def _get_function_signature(self, func: Callable) -> Dict[str, Any]:
        """Pobiera sygnaturę funkcji"""
        try:
            sig = inspect.signature(func)
            return {
                "parameters": {
                    param.name: {
                        "type": str(param.annotation) if param.annotation != param.empty else "Any",
                        "default": str(param.default) if param.default != param.empty else None
                    }
                    for param in sig.parameters.values()
                },
                "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any"
            }
        except Exception as e:
            return {"error": str(e)}

    def get_function(self, name: str) -> Optional[Callable]:
        """Pobiera funkcję z rejestru"""
        return self._function_registry.get(name)

    def list_functions(self) -> List[str]:
        """Lista dostępnych funkcji"""
        return list(self._function_registry.keys())

    def get_functions_count(self) -> int:
        """Zwraca liczbę zarejestrowanych funkcji"""
        return len(self._function_registry)

    def get_version(self) -> str:
        """Zwraca wersję Soul"""
        return self.genotype.get("genesis", {}).get("version", "1.0.0")

    def get_available_functions_clear(self) -> Dict[str, Dict[str, Any]]:
        """
        Zwraca czytelną listę dostępnych funkcji dla Being z pełnymi informacjami.

        Returns:
            Dict z funkcjami publicznymi i ich szczegółami
        """
        available_functions = {}

        # Funkcje publiczne z genotype.functions (zewnętrzny dostęp)
        public_functions = self.genotype.get("functions", {})
        for func_name, func_info in public_functions.items():
            if not func_name.startswith('_'):
                available_functions[func_name] = {
                    "name": func_name,
                    "type": "public",
                    "description": func_info.get("description", f"Public function {func_name}"),
                    "is_async": func_info.get("is_async", False),
                    "signature": func_info.get("signature", {}),
                    "source": "genotype.functions",
                    "accessible_via": "being.execute_soul_function()"
                }

        # Dodaj informacje o funkcjach prywatnych (dla debugowania)
        if self.has_module_source():
            for func_name in self._function_registry:
                if func_name.startswith('_') and func_name not in available_functions:
                    available_functions[f"[PRIVATE] {func_name}"] = {
                        "name": func_name,
                        "type": "private",
                        "description": f"Private function {func_name} (available only to execute)",
                        "source": "module_source",
                        "accessible_via": "internal execute logic"
                    }

        return available_functions

    def get_function_visibility_info(self) -> Dict[str, Any]:
        """
        Zwraca informacje o widoczności funkcji w Soul.

        Returns:
            Informacje o funkcjach publicznych, prywatnych i capabilities
        """
        public_functions = [f for f in self.genotype.get("functions", {}) if not f.startswith('_')]
        private_functions = [f for f in self._function_registry if f.startswith('_')]

        return {
            "soul_hash": self.soul_hash[:8] + "..." if self.soul_hash else "None",
            "alias": self.alias,
            "has_module_source": self.has_module_source(),
            "capabilities": self.genotype.get("capabilities", {}),
            "functions": {
                "public": {
                    "count": len(public_functions),
                    "names": public_functions,
                    "source": "genotype.functions",
                    "access": "external via Being"
                },
                "private": {
                    "count": len(private_functions), 
                    "names": private_functions,
                    "source": "module_source",
                    "access": "internal via execute"
                },
                "total_registered": len(self._function_registry)
            }
        }

    def get_function_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Pobiera informacje o funkcji"""
        if name in self.genotype.get("functions", {}):
            return self.genotype["functions"][name]
        return None

    def has_module_source(self) -> bool:
        """Sprawdza czy Soul zawiera kod źródłowy modułu"""
        return "module_source" in self.genotype and self.genotype["module_source"] is not None

    def get_language(self) -> str:
        """Zwraca język modułu z genotypu"""
        return self.genotype.get("genesis", {}).get("language", "python")

    def is_executable_in_language(self, language: str) -> bool:
        """Sprawdza czy Soul może być wykonana w danym języku"""
        soul_language = self.get_language()
        return soul_language == language or soul_language == "multi"

    def get_module_source(self) -> Optional[str]:
        """Zwraca kod źródłowy modułu"""
        return self.genotype.get("module_source")

    @classmethod
    def validate_module_source(cls, module_source: str) -> Dict[str, Any]:
        """
        Waliduje kod źródłowy modułu i zwraca informacje o funkcjach i atrybutach.

        Args:
            module_source: Kod źródłowy modułu do walidacji

        Returns:
            Dict z wynikami walidacji
        """
        validation_result = {
            "valid": False,
            "functions": {},
            "attributes": {},
            "dependencies": {},
            "errors": [],
            "warnings": [],
            "has_init": False,
            "has_execute": False,
            "language": "python",
            "python_version": "3.8+"
        }

        try:
            import ast
            import inspect
            import sys

            # Parsuj kod AST dla bezpiecznej analizy
            tree = ast.parse(module_source)

            # Wyciągnij zależności z AST
            dependencies = cls._extract_dependencies_from_ast(tree)
            validation_result["dependencies"] = dependencies

            # Przygotuj środowisko z zależnościami
            temp_globals = {"__name__": "__temp_module__"}

            # Próbuj załadować zależności
            missing_deps = []
            for dep_name, dep_info in dependencies.items():
                try:
                    if dep_info["type"] == "standard":
                        # Standardowe biblioteki Python
                        temp_globals[dep_name] = __import__(dep_name)
                    elif dep_info["type"] == "external":
                        # Zewnętrzne pakiety (openai, requests, etc.)
                        try:
                            temp_globals[dep_name] = __import__(dep_name)
                        except ImportError:
                            missing_deps.append(dep_name)
                            validation_result["warnings"].append(f"Missing external dependency: {dep_name}")
                except ImportError as e:
                    missing_deps.append(dep_name)
                    validation_result["warnings"].append(f"Cannot import {dep_name}: {e}")

            validation_result["missing_dependencies"] = missing_deps

            # Wykonaj kod w przygotowanym środowisku
            exec(module_source, temp_globals)

            # Analizuj funkcje (bez "_")
            for name, obj in temp_globals.items():
                if name.startswith('__'):  # Pomijaj dunder methods
                    continue

                if callable(obj) and not name.startswith('_'):
                    try:
                        sig = inspect.signature(obj)
                        is_async = asyncio.iscoroutinefunction(obj)

                        validation_result["functions"][name] = {
                            "py_type": "function",
                            "description": getattr(obj, '__doc__', None) or f"Function {name}",
                            "is_async": is_async,
                            "is_coroutine": is_async,
                            "signature": {
                                "parameters": {
                                    param.name: {
                                        "type": str(param.annotation) if param.annotation != param.empty else "Any",
                                        "default": repr(param.default) if param.default != param.empty else None,
                                        "required": param.default == param.empty,
                                        "kind": str(param.kind)
                                    }
                                    for param in sig.parameters.values()
                                },
                                "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any"
                            }
                        }

                        # Sprawdź specjalne funkcje
                        if name == 'init':
                            validation_result["has_init"] = True
                        elif name == 'execute':
                            validation_result["has_execute"] = True

                    except Exception as e:
                        validation_result["warnings"].append(f"Cannot analyze function {name}: {e}")

                elif not callable(obj) and not name.startswith('_'):
                    # Szczegółowa analiza atrybutów modułu
                    obj_type = type(obj)
                    type_name = obj_type.__name__

                    # Określ czy jest Optional
                    is_optional = obj is None
                    is_mutable = isinstance(obj, (list, dict, set))

                    validation_result["attributes"][name] = {
                        "py_type": type_name,
                        "full_type": f"{obj_type.__module__}.{type_name}" if obj_type.__module__ != 'builtins' else type_name,
                        "default": obj if isinstance(obj, (str, int, float, bool, type(None))) else repr(obj)[:100],
                        "description": f"Module attribute {name} of type {type_name}",
                        "is_optional": is_optional,
                        "is_mutable": is_mutable,
                        "is_constant": name.isupper(),
                        "size": len(obj) if hasattr(obj, '__len__') else None
                    }

            validation_result["valid"] = True
            validation_result["python_version"] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        except SyntaxError as e:
            validation_result["errors"].append(f"Python syntax error: {e}")
        except Exception as e:
            validation_result["errors"].append(f"Module validation error: {e}")

        return validation_result

    async def execute_directly(self, function_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        DIRECT SOUL EXECUTION - wykonuje funkcję bez tworzenia Being.
        Używane gdy nie ma danych do zapisu.

        Args:
            function_name: Nazwa funkcji
            *args, **kwargs: Argumenty

        Returns:
            Wynik funkcji w formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        print(f"🧬 Soul {self.alias} executing '{function_name}' directly (no Being)")

        try:
            result = await self.execute_function(function_name, *args, **kwargs)

            if result.get('success'):
                result['soul_context']['execution_mode'] = 'soul_direct'
                result['soul_context']['performance_optimized'] = True
                result['data']['execution_info'] = {
                    "executed_by": "soul_direct",
                    "being_avoided": True,
                    "reason": "no_persistent_data_needed"
                }

            return result

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Direct Soul execution failed: {str(e)}",
                error_code="SOUL_DIRECT_EXECUTION_ERROR",
                soul_context={"soul_hash": self.soul_hash, "execution_mode": "soul_direct"}
            )

    def can_execute_directly(self, data_context: Dict[str, Any] = None) -> bool:
        """
        Sprawdza czy Soul może wykonać operację bezpośrednio bez Being.

        Args:
            data_context: Kontekst danych operacji

        Returns:
            True jeśli Soul może działać bezpośrednio
        """
        # Soul może działać bezpośrednio jeśli:
        # 1. Ma zarejestrowane funkcje
        # 2. Nie ma danych do zapisu
        # 3. To tylko obliczenia/przetwarzanie

        has_functions = len(self._function_registry) > 0
        needs_persistence = self.should_create_persistent_being(data_context)

        return has_functions and not needs_persistence


    def load_module_dynamically(self) -> Optional[Any]:
        """Ładuje moduł dynamicznie z kodu źródłowego - obsługuje różne języki"""
        if not self.has_module_source():
            return None

        # Sprawdź czy już załadowano
        module_name = f"dynamic_soul_{self.soul_hash[:8]}"
        if hasattr(self, '_loaded_module') and self._loaded_module is not None:
            return self._loaded_module

        language = self.get_language()

        try:
            if language == "python":
                return self._load_python_module(module_name)
            elif language == "javascript":
                return self._load_javascript_module(module_name)
            elif language == "multi":
                return self._load_multi_language_module(module_name)
            else:
                print(f"⚠️ Unsupported language: {language}")
                return None

        except Exception as e:
            print(f"❌ Error loading dynamic module ({language}): {e}")
            return None

    def _load_python_module(self, module_name: str) -> Optional[Any]:
        """Ładuje moduł Python"""
        import types
        import sys

        # Utwórz nowy moduł
        module = types.ModuleType(module_name)

        # Przygotuj bezpieczne środowisko wykonania
        safe_globals = {
            "__name__": module_name,
            "__file__": f"<dynamic_soul_{self.soul_hash[:8]}>",
            "__builtins__": __builtins__
        }

        # Wykonaj kod w kontekście modułu
        exec(self.get_module_source(), safe_globals, module.__dict__)

        # Zarejestruj funkcje
        functions = {}
        for attr_name in dir(module):
            if not attr_name.startswith('_'):
                attr = getattr(module, attr_name)
                if callable(attr):
                    functions[attr_name] = attr
                    if attr_name not in self._function_registry:
                        self._function_registry[attr_name] = attr

        # Cache'uj moduł
        self._loaded_module = module

        if module_name not in sys.modules:
            sys.modules[module_name] = module

        print(f"✅ Loaded Python module {module_name} with {len(functions)} functions")
        return module

    def _load_javascript_module(self, module_name: str) -> Optional[Any]:
        """Ładuje moduł JavaScript przez bridge"""
        try:
            # Wrapper dla JavaScript - może być rozszerzony o PyV8, Node.js bridge itp.
            js_wrapper = JavaScriptWrapper(self.get_module_source(), module_name)

            # Zarejestruj funkcje JavaScript jako callable Python objects
            for func_name in js_wrapper.get_function_names():
                if func_name not in self._function_registry:
                    self._function_registry[func_name] = js_wrapper.create_python_callable(func_name)

            self._loaded_module = js_wrapper
            print(f"✅ Loaded JavaScript module {module_name}")
            return js_wrapper

        except Exception as e:
            print(f"❌ JavaScript loading failed: {e}")
            return None

    def _load_multi_language_module(self, module_name: str) -> Optional[Any]:
        """Ładuje moduł wielojęzyczny"""
        try:
            # Multi-language modules mają sekcje dla różnych języków
            module_source = self.get_module_source()

            # Parsuj sekcje językowe (format: ```python ... ``` ```javascript ... ```)
            language_sections = self._parse_multi_language_source(module_source)

            combined_module = MultiLanguageModule(module_name)

            for lang, code in language_sections.items():
                if lang == "python":
                    python_funcs = self._extract_python_functions(code)
                    for name, func in python_funcs.items():
                        self._function_registry[name] = func
                        combined_module.add_function(name, func, "python")

                elif lang == "javascript":
                    js_wrapper = JavaScriptWrapper(code, f"{module_name}_{lang}")
                    for func_name in js_wrapper.get_function_names():
                        js_callable = js_wrapper.create_python_callable(func_name)
                        self._function_registry[func_name] = js_callable
                        combined_module.add_function(func_name, js_callable, "javascript")

            self._loaded_module = combined_module
            print(f"✅ Loaded multi-language module {module_name}")
            return combined_module

        except Exception as e:
            print(f"❌ Multi-language loading failed: {e}")
            return None

    def _parse_multi_language_source(self, source: str) -> Dict[str, str]:
        """Parsuje kod wielojęzyczny na sekcje"""
        import re

        sections = {}
        pattern = r'```(\w+)\n(.*?)\n```'
        matches = re.findall(pattern, source, re.DOTALL)

        for language, code in matches:
            sections[language.lower()] = code.strip()

        return sections

    def _extract_python_functions(self, code: str) -> Dict[str, Any]:
        """Wyciąga funkcje z kodu Python"""
        import types

        temp_globals = {}
        exec(code, temp_globals)

        functions = {}
        for name, obj in temp_globals.items():
            if callable(obj) and not name.startswith('_'):
                functions[name] = obj

        return functions

    def extract_functions_from_module(self, module: Any) -> Dict[str, Callable]:
        """Wyciąga funkcje z załadowanego modułu"""
        functions = {}

        if not module:
            return functions

        # Znajdź wszystkie callable obiekty w module
        for attr_name in dir(module):
            if not attr_name.startswith('_'):  # Pomijaj prywatne
                attr = getattr(module, attr_name)
                if callable(attr):
                    functions[attr_name] = attr

        return functions

    async def execute_function(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje funkcję zarejestrowaną w Soul.

        Args:
            name: Nazwa funkcji
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane (NIE zawierają atrybutów Being)

        Returns:
            Wynik wykonania funkcji w standardowym formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            func = self.get_function(name)
            if not func:
                return GeneticResponseFormat.error_response(
                    error=f"Function '{name}' not found in soul '{self.alias}'",
                    error_code="FUNCTION_NOT_FOUND"
                )

            # Wykonaj funkcję - kwargs to tylko argumenty funkcji, nie atrybuty Being
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            return GeneticResponseFormat.success_response(
                data={
                    "function_name": name,
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                },
                soul_context={
                    "soul_hash": self.soul_hash,
                    "function_info": self.get_function_info(name)
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Function execution error: {str(e)}",
                error_code="FUNCTION_EXECUTION_ERROR",
                soul_context={"soul_hash": self.soul_hash, "function_name": name}
            )

    def has_init_function(self) -> bool:
        """Sprawdza czy Soul ma funkcję init"""
        return self.get_function('init') is not None

    def has_execute_function(self) -> bool:
        """Sprawdza czy Soul ma funkcję execute"""
        return self.get_function('execute') is not None

    async def auto_init(self, being_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Automatyczne wywołanie funkcji init jeśli istnieje.

        Soul.init() może zdecydować czy Being powinno być persistent na podstawie:
        - Obecności atrybutów (dane do zapisania)
        - Typu operacji (message, log, temp processing)
        - Jawnego parametru persistent w being_context

        Args:
            being_context: Kontekst Being (ulid, alias, data, itp.)

        Returns:
            Wynik funkcji init z rekomendacją persistence
        """
        if self.has_init_function():
            # Dodaj informację o persistence do kontekstu
            enhanced_context = (being_context or {}).copy()
            enhanced_context.update({
                'soul_type': self.genotype.get('genesis', {}).get('type', 'unknown'),
                'has_attributes': len(enhanced_context.get('data', {})) > 0,
                'persistence_hint': self._suggest_persistence(enhanced_context)
            })

            return await self.execute_function('init', being_context=enhanced_context)
        else:
            from luxdb.utils.serializer import GeneticResponseFormat
            return GeneticResponseFormat.success_response(
                data={"message": "No init function found, skipping auto-initialization"}
            )

    def _suggest_persistence(self, being_context: Dict[str, Any]) -> bool:
        """
        Sugeruje czy Being powinno być persistent na podstawie kontekstu.

        Returns:
            True jeśli Being powinno być zapisane do bazy
        """
        # Sprawdź typ Soul
        soul_type = self.genotype.get('genesis', {}).get('type', '')

        # Typy które zazwyczaj są persistent
        persistent_types = ['message', 'log', 'user_data', 'relation', 'registry']
        if soul_type in persistent_types:
            return True

        # Typy które zazwyczaj są temporary  
        temp_types = ['processor', 'calculator', 'validator', 'transformer']
        if soul_type in temp_types:
            return False

        # Sprawdź czy ma dane do zapisania
        data = being_context.get('data', {})
        if data and len(data) > 0:
            return True

        # Sprawdź czy ma alias (sugeruje trwałość)
        alias = being_context.get('alias')
        if alias and not alias.startswith('temp_'):
            return True

        # Domyślnie temporary
        return False

    async def default_execute(self, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje domyślną funkcję execute z danymi.

        Args:
            data: Dane do przetworzenia
            **kwargs: Dodatkowe argumenty

        Returns:
            Wynik funkcji execute
        """
        if self.has_execute_function():
            return await self.execute_function('execute', data=data, **kwargs)
        else:
            from luxdb.utils.serializer import GeneticResponseFormat
            return GeneticResponseFormat.error_response(
                error="No execute function found in soul",
                error_code="EXECUTE_FUNCTION_NOT_FOUND"
            )

    def should_create_persistent_being(self, attributes: Dict[str, Any] = None, operation_type: str = "function") -> bool:
        """
        LAZY CREATION LOGIC: Decyduje czy potrzebne jest Being czy Soul może wykonać bezpośrednio.

        Args:
            attributes: Atrybuty do sprawdzenia
            operation_type: Typ operacji ("function", "data_storage", "relationship")

        Returns:
            True jeśli Being jest potrzebne (są dane do zapisu)
        """
        # Bez atrybutów = Soul wykonuje bezpośrednio
        if not attributes or len(attributes) == 0:
            return False

        # Sprawdź czy to tylko metadane (nie wymagają Being)
        metadata_only_keys = ['_temp', '_cache', '_session', '_debug']
        non_metadata_attrs = {k: v for k, v in attributes.items() 
                             if not any(k.startswith(meta) for meta in metadata_only_keys)}

        # Jeśli są tylko metadane = Soul wykonuje bezpośrednio
        if len(non_metadata_attrs) == 0:
            return False

        # Z rzeczywistymi danymi = potrzebne Being
        print(f"🧬 Being needed for {len(non_metadata_attrs)} persistent attributes")
        return True

    async def execute_or_create_being(self, function_name: str = None, attributes: Dict[str, Any] = None, alias: str = None, force_being: bool = False, *args, **kwargs) -> Dict[str, Any]:
        """
        LAZY BEING CREATION: Soul wykonuje funkcje bezpośrednio, Being tworzy się tylko gdy zajdzie potrzeba zapisu.

        Logika:
        1. Jeśli nie ma atrybutów do zapisu -> Soul wykonuje bezpośrednio
        2. Jeśli są atrybuty -> Utwórz Being i wykonaj przez niego
        3. Jeśli force_being=True -> Zawsze utwórz Being

        Args:
            function_name: Nazwa funkcji do wykonania
            attributes: Atrybuty - jeśli podane, wymusza utworzenie Being
            alias: Alias dla Being (jeśli zostanie utworzony)
            force_being: Wymusza utworzenie Being nawet bez atrybutów
            *args, **kwargs: Argumenty dla funkcji

        Returns:
            Wynik operacji w formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        # TRYB 1: Bezpośrednie wykonanie przez Soul (bez Being)
        if not attributes and not force_being:
            print(f"🧬 Soul {self.alias} executing function '{function_name}' directly (no Being needed)")

            if function_name:
                result = await self.execute_function(function_name, *args, **kwargs)

                # Dodaj informację o trybie wykonania
                if result.get('success'):
                    result['soul_context']['execution_mode'] = 'soul_direct'
                    result['soul_context']['being_created'] = False

                return result
            else:
                return GeneticResponseFormat.success_response(
                    data={"message": "Soul ready for execution, no function specified"},
                    soul_context={
                        "soul_hash": self.soul_hash,
                        "execution_mode": "soul_ready",
                        "being_created": False
                    }
                )

        # TRYB 2: Lazy Being Creation - tworzymy Being bo są dane do zapisu
        else:
            print(f"🧬 Soul {self.alias} creating Being for persistent execution")

            from .being import Being

            being = await Being.create(
                soul=self,
                attributes=attributes or {},
                alias=alias,
                persistent=True
            )

            # Wykonaj funkcję przez Being jeśli podana
            if function_name:
                result = await being.execute_soul_function(function_name, *args, **kwargs)

                return GeneticResponseFormat.success_response(
                    data={
                        "being_created": True,
                        "being": being.to_json_serializable(),
                        "function_result": result.get('data', {}),
                        "lazy_creation_reason": "attributes_provided" if attributes else "force_being"
                    },
                    soul_context={
                        "soul_hash": self.soul_hash,
                        "execution_mode": "lazy_being_creation"
                    }
                )
            else:
                return GeneticResponseFormat.success_response(
                    data={
                        "being_created": True,
                        "being": being.to_json_serializable(),
                        "lazy_creation_reason": "attributes_provided" if attributes else "force_being"
                    },
                    soul_context={
                        "soul_hash": self.soul_hash,
                        "execution_mode": "lazy_being_creation"
                    }
                )

    @classmethod
    async def create_function_soul(cls, name: str, func: Callable, description: str = None, alias: str = None, version: str = "1.0.0") -> 'Soul':
        """
        Tworzy specjalizowany Soul dla pojedynczej funkcji z niezmiennym genotypem.

        Args:
            name: Nazwa funkcji
            func: Funkcja
            description: Opis funkcji
            alias: Alias dla soul
            version: Wersja genotypu

        Returns:
            Nowy Soul z funkcją
        """
        # Genotyp dla funkcji - KOMPLETNY i NIEZMIENNY
        function_genotype = {
            "genesis": {
                "name": alias or f"function_{name}",
                "type": "function_soul", 
                "version": version,
                "description": description or f"Soul for function {name}",
                "immutable": True
            },
            "attributes": {
                "function_name": {"py_type": "str", "default": name},
                "last_execution": {"py_type": "str"},
                "execution_count": {"py_type": "int", "default": 0}
            },
            "functions": {
                name: {
                    "py_type": "function",
                    "description": description or f"Main function {name}",
                    "is_primary": True,
                    "signature": cls._get_function_signature_static(func),
                    "is_async": asyncio.iscoroutinefunction(func)
                }
            }
        }

        # Utwórz Soul
        soul = await cls.create(function_genotype, alias or f"function_{name}")

        # Załaduj funkcję do rejestru (bez modyfikacji genotypu)
        soul._register_immutable_function(name, func)

        return soul

    @classmethod
    async def create_evolved_version(cls, original_soul: 'Soul', changes: Dict[str, Any], new_version: str = None) -> 'Soul':
        """
        Tworzy nową wersję Soul z ewolucją genotypu.

        Args:
            original_soul: Oryginalna Soul
            changes: Zmiany do wprowadzenia
            new_version: Nowa wersja (automatyczna jeśli None)

        Returns:
            Nowy Soul z nowym hashem
        """
        # Skopiuj oryginalny genotyp
        evolved_genotype = original_soul.genotype.copy()

        # Automatyczne wersjonowanie
        if new_version is None:
            old_version = evolved_genotype.get("genesis", {}).get("version", "1.0.0")
            parts = old_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
            new_version = f"{major}.{minor}.{patch + 1}"

        # Aktualizuj genesis
        if "genesis" not in evolved_genotype:
            evolved_genotype["genesis"] = {}
        evolved_genotype["genesis"]["version"] = new_version
        evolved_genotype["genesis"]["parent_hash"] = original_soul.soul_hash
        evolved_genotype["genesis"]["evolution_timestamp"] = datetime.now().isoformat()

        # Zastosuj zmiany
        for key, value in changes.items():
            if "." in key:  # Nested path like "attributes.new_field"
                keys = key.split(".")
                current = evolved_genotype
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                evolved_genotype[key] = value

        # Utwórz nową Soul
        evolved_soul = await cls.create(evolved_genotype, original_soul.alias)

        # Dodatkowe logowanie dla ewolucji
        try:
            from ..utils.soul_creation_logger import soul_creation_logger
            soul_creation_logger.log_soul_creation(evolved_soul, {
                "method": "Soul.create_evolved_version",
                "original_hash": original_soul.soul_hash,
                "evolution_changes": changes,
                "version_increment": new_version,
                "evolution_type": "version_update"
            })
        except Exception as e:
            print(f"⚠️ Evolution logging failed: {e}")

        return evolved_soul

    @classmethod
    def _process_module_source_for_genotype(cls, genotype: Dict[str, Any]) -> Dict[str, Any]:
        """
        Przetwarza module_source w genotypie i automatycznie dodaje funkcje publiczne do functions.
        Obsługuje różne języki programowania.

        Args:
            genotype: Oryginalny genotyp

        Returns:
            Przetworzony genotyp z automatycznie rozpoznanymi funkcjami
        """
        if "module_source" not in genotype or not genotype["module_source"]:
            return genotype

        module_source = genotype["module_source"]

        # Automatycznie wykryj język jeśli nie podano
        if "genesis" not in genotype:
            genotype["genesis"] = {}

        if "language" not in genotype["genesis"]:
            from ..utils.language_bridge import LanguageDetector
            detected_language = LanguageDetector.detect_language(module_source)
            genotype["genesis"]["language"] = detected_language
            print(f"🔍 Auto-detected language: {detected_language}")

        language = genotype["genesis"]["language"]

        # Waliduj i wyciągnij funkcje z module_source zgodnie z językiem
        if language == "python":
            validation = cls.validate_module_source(module_source)
        elif language == "javascript":
            validation = cls._validate_javascript_source(module_source)
        elif language == "multi":
            validation = cls._validate_multi_language_source(module_source)
        else:
            print(f"⚠️ Unsupported language: {language}")
            validation = {"valid": False, "functions": {}, "errors": [f"Unsupported language: {language}"]}

        if not validation["valid"]:
            print(f"⚠️ Warning: Invalid module_source in genotype: {validation['errors']}")
            return genotype

        # Automatycznie dodaj funkcje publiczne do functions jeśli nie istnieją
        if "functions" not in genotype:
            genotype["functions"] = {}

        # Dodaj funkcje publiczne (bez "_") do functions
        for func_name, func_info in validation["functions"].items():
            if not func_name.startswith('_'):  # Tylko publiczne funkcje
                genotype["functions"][func_name] = func_info

        # Dodaj informacje o capabilities jeśli nie istnieją
        if "capabilities" not in genotype:
            genotype["capabilities"] = {}

        genotype["capabilities"].update({
            "language": language,
            "has_init": validation.get("has_init", False),
            "has_execute": validation.get("has_execute", False),
            "function_count": len(validation["functions"]),
            "public_function_count": len([f for f in validation["functions"] if not f.startswith('_')]),
            "private_function_count": len([f for f in validation["functions"] if f.startswith('_')]),
            "attribute_count": len(validation.get("attributes", {})),
            "dependencies_count": len(validation.get("dependencies", {})),
            "missing_dependencies": validation.get("missing_dependencies", [])
        })

        # Dodaj informacje o zależnościach
        if validation.get("dependencies"):
            genotype["dependencies"] = validation["dependencies"]

        # Dodaj attributes z modułu jeśli nie istnieją (tylko dla Python)
        if language == "python":
            if "attributes" not in genotype:
                genotype["attributes"] = {}

            # Merge attributes z modułu (module attributes mają niższy priorytet)
            for attr_name, attr_info in validation.get("attributes", {}).items():
                if attr_name not in genotype["attributes"]:
                    genotype["attributes"][attr_name] = attr_info

        return genotype

    @classmethod
    def _validate_javascript_source(cls, source: str) -> Dict[str, Any]:
        """Waliduje kod JavaScript"""
        # Podstawowa walidacja JavaScript - można rozszerzyć
        import re

        validation_result = {
            "valid": True,
            "functions": {},
            "errors": [],
            "warnings": [],
            "language": "javascript"
        }

        try:
            # Znajdź funkcje
            function_pattern = r'function\s+(\w+)\s*\([^)]*\)'
            arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>'

            functions = re.findall(function_pattern, source)
            arrow_functions = re.findall(arrow_pattern, source)

            all_functions = functions + arrow_functions

            for func_name in all_functions:
                validation_result["functions"][func_name] = {
                    "py_type": "function",
                    "description": f"JavaScript function {func_name}",
                    "is_async": False,  # Można rozszerzyć o async detection
                    "language": "javascript"
                }

                if func_name == 'init':
                    validation_result["has_init"] = True
                elif func_name == 'execute':
                    validation_result["has_execute"] = True

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"JavaScript validation error: {str(e)}")

        return validation_result

    @classmethod 
    def _validate_multi_language_source(cls, source: str) -> Dict[str, Any]:
        """Waliduje kod wielojęzyczny"""
        import re

        validation_result = {
            "valid": True,
            "functions": {},
            "errors": [],
            "warnings": [],
            "language": "multi",
            "has_init": False,
            "has_execute": False
        }

        try:
            # Parsuj sekcje językowe
            pattern = r'```(\w+)\n(.*?)\n```'
            matches = re.findall(pattern, source, re.DOTALL)

            if not matches:
                validation_result["valid"] = False
                validation_result["errors"].append("No language sections found in multi-language source")
                return validation_result

            for language, code in matches:
                lang = language.lower()

                if lang == "python":
                    py_validation = cls.validate_module_source(code)
                    if py_validation["valid"]:
                        for func_name, func_info in py_validation["functions"].items():
                            func_info["source_language"] = "python"
                            validation_result["functions"][func_name] = func_info

                        if py_validation.get("has_init"):
                            validation_result["has_init"] = True
                        if py_validation.get("has_execute"):
                            validation_result["has_execute"] = True
                    else:
                        validation_result["warnings"].extend(py_validation["errors"])

                elif lang == "javascript":
                    js_validation = cls._validate_javascript_source(code)
                    if js_validation["valid"]:
                        for func_name, func_info in js_validation["functions"].items():
                            func_info["source_language"] = "javascript"
                            validation_result["functions"][func_name] = func_info

                        if js_validation.get("has_init"):
                            validation_result["has_init"] = True
                        if js_validation.get("has_execute"):
                            validation_result["has_execute"] = True
                    else:
                        validation_result["warnings"].extend(js_validation["errors"])

                else:
                    validation_result["warnings"].append(f"Unsupported language section: {language}")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Multi-language validation error: {str(e)}")

        return validation_result

    def _load_and_register_module_functions(self):
        """Ładuje moduł i rejestruje funkcje w _function_registry"""
        try:
            module = self.load_module_dynamically()
            if module:
                # Rejestruj WSZYSTKIE funkcje (publiczne i prywatne) w rejestrze
                functions = self.extract_functions_from_module(module)
                for func_name, func in functions.items():
                    self._function_registry[func_name] = func

                print(f"✅ Registered {len(functions)} functions in Soul {self.alias}")
        except Exception as e:
            print(f"❌ Failed to load and register module functions: {e}")

    @classmethod
    def _extract_dependencies_from_ast(cls, tree: Any) -> Dict[str, Any]:
        """Wyciąga zależności z AST"""
        import ast
        dependencies = {}

        class DependencyVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname or alias.name
                    dependencies[name] = {
                        "type": cls._classify_dependency(alias.name),
                        "module": alias.name,
                        "alias": alias.asname,
                        "source": "import"
                    }
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    for alias in node.names:
                        name = alias.asname or alias.name
                        dependencies[name] = {
                            "type": cls._classify_dependency(node.module),
                            "module": node.module,
                            "imported_name": alias.name,
                            "alias": alias.asname,
                            "source": "from_import"
                        }
                self.generic_visit(node)

        visitor = DependencyVisitor()
        visitor.visit(tree)
        return dependencies

    @classmethod
    def _classify_dependency(cls, module_name: str) -> str:
        """Klasyfikuje zależność jako standard/external/local"""
        import sys

        standard_libs = {
            'os', 'sys', 'json', 'asyncio', 'datetime', 'time', 'math', 
            'random', 'hashlib', 'uuid', 'logging', 'pathlib', 'typing',
            'collections', 'itertools', 'functools', 're', 'urllib', 'http'
        }

        if module_name in standard_libs or module_name in sys.stdlib_module_names:
            return "standard"
        elif module_name.startswith('.'):
            return "local"
        else:
            return "external"

    @classmethod
    def _get_function_signature_static(cls, func: Callable) -> Dict[str, Any]:
        """Statyczna wersja pobierania sygnatury funkcji"""
        try:
            sig = inspect.signature(func)
            return {
                "parameters": {
                    param.name: {
                        "type": str(param.annotation) if param.annotation != param.empty else "Any",
                        "default": str(param.default) if param.default != param.empty else None
                    }
                    for param in sig.parameters.values()
                },
                "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any"
            }
        except Exception as e:
            return {"error": str(e)}

    def validate_function_call(self, name: str, *args, **kwargs) -> List[str]:
        """
        Waliduje wywołanie funkcji.

        Args:
            name: Nazwa funkcji
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            Lista błędów walidacji
        """
        errors = []

        if name not in self._function_registry:
            errors.append(f"Function '{name}' not found")
            return errors

        func = self._function_registry[name]
        func_info = self.get_function_info(name)

        if not func_info:
            return errors

        try:
            # Sprawdź sygnaturę funkcji
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
        except TypeError as e:
            errors.append(f"Function signature error: {str(e)}")

        return errors

    def get_version(self) -> str:
        """Zwraca wersję Soul"""
        # Sprawdź nową strukturę genotypu
        if "version" in self.genotype:
            return self.genotype["version"]
        # Fallback na starą strukturę
        return self.genotype.get("genesis", {}).get("version", "1.0.0")

    def get_parent_hash(self) -> Optional[str]:
        """Zwraca hash rodzica (jeśli Soul jest ewolucją)"""
        return self.genotype.get("genesis", {}).get("parent_hash")

    def is_evolution_of(self, other_soul: 'Soul') -> bool:
        """Sprawdza czy ta Soul jest ewolucją innej"""
        return self.get_parent_hash() == other_soul.soul_hash

    async def get_lineage(self) -> List['Soul']:
        """Zwraca pełną linię ewolucji Soul"""
        lineage = [self]
        current = self

        while current.get_parent_hash():
            parent = await Soul.get_by_hash(current.get_parent_hash())
            if parent:
                lineage.append(parent)
                current = parent
            else:
                break

        return lineage

    async def evolve_with_new_functions(self, new_functions: Dict[str, Dict[str, Any]], 
                                       reason: str = "Function enhancement") -> 'Soul':
        """
        Ewolucja Soul z nowymi funkcjami spoza module_source.

        Args:
            new_functions: Nowe funkcje do dodania
            reason: Powód ewolucji

        Returns:
            Nowa Soul z rozszerzonymi funkcjami
        """
        # Przygotuj zmiany
        current_functions = self.genotype.get("functions", {}).copy()
        current_functions.update(new_functions)

        changes = {
            "functions": current_functions,
            "evolution_info": {
                "reason": reason,
                "added_functions": list(new_functions.keys()),
                "evolution_type": "function_enhancement"
            }
        }

        # Aktualizuj capabilities
        if "capabilities" not in changes:
            changes["capabilities"] = self.genotype.get("capabilities", {}).copy()

        changes["capabilities"]["function_count"] = len(current_functions)
        changes["capabilities"]["evolved_function_count"] = len(new_functions)

        return await self.create_evolved_version(self, changes)

    def can_accept_new_functions(self) -> bool:
        """Sprawdza czy Soul może przyjąć nowe funkcje"""
        # Soul może ewoluować jeśli ma podstawowe możliwości
        capabilities = self.genotype.get("capabilities", {})

        # Wymagania: ma init lub execute, nie jest immutable
        has_init = capabilities.get("has_init", False)
        has_execute = capabilities.get("has_execute", False)
        is_immutable = self.genotype.get("genesis", {}).get("immutable", False)

        return (has_init or has_execute) and not is_immutable

    @classmethod
    async def get_all_versions(cls, base_name: str) -> List['Soul']:
        """Zwraca wszystkie wersje Soul o danej nazwie"""
        all_souls = await cls.get_all()
        versions = []

        for soul in all_souls:
            genesis_name = soul.genotype.get("genesis", {}).get("name")
            if genesis_name and genesis_name.startswith(base_name):
                versions.append(soul)

        # Sortuj po wersji
        versions.sort(key=lambda s: s.get_version())
        return versions

    def is_compatible_with(self, other_soul: 'Soul') -> bool:
        """Sprawdza kompatybilność między wersjami Soul"""
        # Podstawowa kompatybilność - ten sam typ genesis
        self_genesis = self.genotype.get("genesis", {})
        other_genesis = other_soul.genotype.get("genesis", {})

        if self_genesis.get("name") != other_genesis.get("name"):
            return False

        # Sprawdź kompatybilność wersji (uproszczona)
        self_version = self.get_version().split(".")
        other_version = other_soul.get_version().split(".")

        # Kompatybilne jeśli major version jest taka sama
        return self_version[0] == other_version[0]

    def __repr__(self):
        functions_count = len(self._function_registry)
        version = self.get_version()
        parent = self.get_parent_hash()
        parent_info = f", parent={parent[:8]}..." if parent else ""
        return f"Soul(hash={self.soul_hash[:8] if self.soul_hash else 'None'}..., alias={self.alias}, v={version}, functions={functions_count}{parent_info})"
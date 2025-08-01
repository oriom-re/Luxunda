# app_v2/ai/ai_brain.py
"""
AI Brain - łączy wszystko w całość!
Analizuje intencje, znajduje geny, wykonuje funkcje
"""

import json
import asyncio
import inspect
from typing import Dict, Any, List, Optional
from datetime import datetime

class AIBrain:
    """Centralny AI brain który łączy geny, intencje i wykonanie"""
    
    def __init__(self):
        self.available_functions = {}
        self.gene_functions = {}
        self._build_function_registry()
    
    def _build_function_registry(self):
        """Buduje rejestr wszystkich dostępnych funkcji dla AI"""
        try:
            from database.soul_repository import SoulRepository
        except ImportError:
            print("⚠️ SoulRepository not available")
            SoulRepository = None
        
        print("🧠 Budowanie rejestru funkcji dla AI Brain...")
        
        # 1. Funkcje z bazy danych
        if SoulRepository:
            self.available_functions.update({
                "get_soul_by_hash": {
                    "description": "Pobiera soul z bazy po ULID",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "hash": {"type": "string", "description": "ULID soul do pobrania"}
                        },
                        "required": ["hash"]
                    },
                    "function": SoulRepository.load_by_hash
                },
                "get_soul_by_alias": {
                    "description": "Pobiera soul z bazy po aliasie",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "alias": {"type": "string", "description": "Alias soul do pobrania"}
                        },
                        "required": ["alias"]
                    },
                    "function": SoulRepository.load_by_alias
                },
                "save_soul": {
                    "description": "Zapisuje soul do bazy danych", 
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "soul": {"type": "object", "description": "Dane soul do zapisania"}
                        },
                        "required": ["soul"]
                    },
                    "function": SoulRepository.save
                },
                "get_all_souls": {
                    "description": "Pobiera wszystkie souls z bazy danych",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    },
                    "function": SoulRepository.load_all
                }
            })
        
        # 2. Funkcje z genów - na razie mock funkcje
        print(f"🧬 Zarejestrowano podstawowe funkcje AI Brain")
        
        print(f"✅ AI Brain ma {len(self.available_functions)} dostępnych funkcji")
    
    def _gene_to_function_spec(self, gene) -> Dict[str, Any]:
        """Konwertuje gen na specyfikację funkcji dla AI"""
        try:
            sig = inspect.signature(gene.function)
            properties = {}
            required = []
            
            for param_name, param in sig.parameters.items():
                if param_name in ['self', 'cls']:
                    continue
                    
                param_type = "string"  # domyślnie
                description = f"Parameter {param_name}"
                
                # Spróbuj określić typ z annotacji
                if param.annotation != inspect.Parameter.empty:
                    if param.annotation == str:
                        param_type = "string"
                    elif param.annotation == int:
                        param_type = "integer"
                    elif param.annotation == float:
                        param_type = "number"
                    elif param.annotation == bool:
                        param_type = "boolean"
                    elif param.annotation == dict:
                        param_type = "object"
                    elif param.annotation == list:
                        param_type = "array"
                
                properties[param_name] = {
                    "type": param_type,
                    "description": description
                }
                
                # Jeśli nie ma default value, to jest required
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
            
            return {
                "description": gene.description or f"Executes gene {gene.name}",
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                },
                "function": gene.function,
                "gene": gene
            }
            
        except Exception as e:
            print(f"⚠️ Nie udało się przeanalizować genu {gene.name}: {e}")
            return {
                "description": f"Executes gene {gene.name}",
                "parameters": {"type": "object", "properties": {}, "required": []},
                "function": gene.function,
                "gene": gene
            }
    
    async def process_user_intent(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Główna funkcja - analizuje intencję użytkownika i wykonuje odpowiednie akcje"""
        context = context or {}
        
        print(f"🧠 AI Brain analizuje: '{user_input}'")
        
        # 1. Przeanalizuj intencję użytkownika
        intent_analysis = await self._analyze_intent(user_input, context)
        
        # 2. Znajdź odpowiednie funkcje/geny
        relevant_functions = await self._find_relevant_functions(intent_analysis)
        
        # 3. Wykonaj akcje
        results = await self._execute_actions(relevant_functions, intent_analysis)
        
        return {
            "user_input": user_input,
            "intent_analysis": intent_analysis,
            "relevant_functions": relevant_functions,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _analyze_intent(self, user_input: str, context: Dict) -> Dict[str, Any]:
        """Analizuje intencję użytkownika (na razie proste reguły, później LLM)"""
        
        user_lower = user_input.lower()
        
        # Proste rozpoznawanie wzorców - później zastąpimy LLM
        if any(word in user_lower for word in ["create", "make", "new", "generate"]):
            return {
                "intent": "create",
                "confidence": 0.8,
                "entities": self._extract_entities(user_input),
                "action_type": "creation",
                "raw_input": user_input
            }
        elif any(word in user_lower for word in ["find", "search", "get", "show", "list"]):
            return {
                "intent": "retrieve", 
                "confidence": 0.8,
                "entities": self._extract_entities(user_input),
                "action_type": "query",
                "raw_input": user_input
            }
        elif any(word in user_lower for word in ["run", "execute", "call", "do"]):
            return {
                "intent": "execute",
                "confidence": 0.8, 
                "entities": self._extract_entities(user_input),
                "action_type": "execution",
                "raw_input": user_input
            }
        elif any(word in user_lower for word in ["analyze", "process", "check"]):
            return {
                "intent": "analyze",
                "confidence": 0.7,
                "entities": self._extract_entities(user_input),
                "action_type": "analysis",
                "raw_input": user_input
            }
        else:
            return {
                "intent": "unknown",
                "confidence": 0.3,
                "entities": self._extract_entities(user_input),
                "action_type": "unknown",
                "raw_input": user_input
            }
    
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Wyciąga entities z tekstu (na razie proste, później NER)"""
        entities = []
        
        # Proste rozpoznawanie nazw plików
        import re
        file_matches = re.findall(r'\b\w+\.(module|py|txt|json)\b', text)
        for match in file_matches:
            entities.append({
                "type": "file",
                "value": match,
                "confidence": 0.9
            })
        
        # Rozpoznawanie nazw genów/funkcji
        words = text.split()
        for word in words:
            if word in self.gene_functions:
                entities.append({
                    "type": "gene",
                    "value": word,
                    "confidence": 0.95
                })
        
        return entities
    
    async def _find_relevant_functions(self, intent_analysis: Dict) -> List[Dict[str, Any]]:
        """Znajduje funkcje relevant dla danej intencji"""
        relevant = []
        intent = intent_analysis["intent"]
        entities = intent_analysis["entities"]
        
        # Na podstawie intencji
        if intent == "create":
            # Szukaj funkcji tworzących
            for func_name, func_spec in self.available_functions.items():
                if any(word in func_spec["description"].lower() 
                       for word in ["create", "save", "new", "generate"]):
                    relevant.append({
                        "function_name": func_name,
                        "spec": func_spec,
                        "relevance_score": 0.8,
                        "reason": "matches_create_intent"
                    })
        
        elif intent == "retrieve":
            # Szukaj funkcji pobierających
            for func_name, func_spec in self.available_functions.items():
                if any(word in func_spec["description"].lower()
                       for word in ["get", "find", "search", "retrieve", "pobiera"]):
                    relevant.append({
                        "function_name": func_name, 
                        "spec": func_spec,
                        "relevance_score": 0.8,
                        "reason": "matches_retrieve_intent"
                    })
        
        elif intent == "execute":
            # Szukaj genów do wykonania
            for entity in entities:
                if entity["type"] == "gene":
                    gene_name = entity["value"]
                    func_name = f"gene_{gene_name}"
                    if func_name in self.available_functions:
                        relevant.append({
                            "function_name": func_name,
                            "spec": self.available_functions[func_name],
                            "relevance_score": 0.95,
                            "reason": f"direct_gene_match: {gene_name}"
                        })
        
        # Sortuj po relevance score
        relevant.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return relevant[:5]  # Max 5 najbardziej relevant
    
    async def _execute_actions(self, relevant_functions: List[Dict], intent_analysis: Dict) -> List[Dict[str, Any]]:
        """Wykonuje wybrane funkcje"""
        results = []
        
        for func_info in relevant_functions:
            try:
                func_name = func_info["function_name"]
                func_spec = func_info["spec"]
                function = func_spec["function"]
                
                if not function:
                    continue
                
                # Przygotuj argumenty (na razie puste - później będziemy parsować z user input)
                args = self._prepare_function_args(func_spec, intent_analysis)
                
                print(f"🚀 Wykonuję funkcję: {func_name} z args: {args}")
                
                # Wykonaj funkcję
                if asyncio.iscoroutinefunction(function):
                    result = await function(**args)
                else:
                    result = function(**args)
                
                results.append({
                    "function_name": func_name,
                    "args": args,
                    "result": result,
                    "success": True,
                    "relevance_score": func_info["relevance_score"]
                })
                
            except Exception as e:
                print(f"❌ Błąd wykonania funkcji {func_name}: {e}")
                results.append({
                    "function_name": func_name,
                    "error": str(e),
                    "success": False,
                    "relevance_score": func_info["relevance_score"]
                })
        
        return results
    
    def _prepare_function_args(self, func_spec: Dict, intent_analysis: Dict) -> Dict[str, Any]:
        """Przygotowuje argumenty dla funkcji na podstawie analizy intencji"""
        args = {}
        
        # Na razie proste mapowanie - później będzie bardziej inteligentne
        entities = intent_analysis.get("entities", [])
        raw_input = intent_analysis.get("raw_input", "")
        
        # Jeśli funkcja potrzebuje 'hash' (ULID)
        if "hash" in func_spec["parameters"].get("properties", {}):
            # Sprawdź entities
            for entity in entities:
                if entity["type"] in ["gene", "file", "ulid"]:
                    args["hash"] = entity["value"].replace(".module", "").replace(".py", "")
                    break
            
            # Jeśli nie znaleziono w entities, spróbuj wyciągnąć z tekstu
            if "hash" not in args:
                # Pattern: "find soul with hash X" -> hash = "X"
                import re
                hash_patterns = [
                    r'hash\s+([A-Z0-9]{26})',
                    r'ulid\s+([A-Z0-9]{26})',
                    r'id\s+([A-Z0-9]{26})',
                    r'with\s+([A-Z0-9]{26})'
                ]
                
                for pattern in hash_patterns:
                    match = re.search(pattern, raw_input, re.IGNORECASE)
                    if match:
                        args["hash"] = match.group(1)
                        break
        
        # Jeśli funkcja potrzebuje 'alias'
        if "alias" in func_spec["parameters"].get("properties", {}):
            # Sprawdź entities
            for entity in entities:
                if entity["type"] in ["gene", "file", "alias"]:
                    args["alias"] = entity["value"].replace(".module", "").replace(".py", "")
                    break
            
            # Jeśli nie znaleziono w entities, spróbuj wyciągnąć z tekstu
            if "alias" not in args:
                # Pattern: "find soul named X" -> alias = "X"
                import re
                alias_patterns = [
                    r'named\s+(\w+)',
                    r'called\s+(\w+)', 
                    r'alias\s+(\w+)',
                    r'find\s+(\w+)',
                    r'get\s+(\w+)',
                    r'soul\s+(\w+)'
                ]
                
                for pattern in alias_patterns:
                    match = re.search(pattern, raw_input, re.IGNORECASE)
                    if match:
                        args["alias"] = match.group(1)
                        break
        
        # Jeśli funkcja potrzebuje 'query' 
        if "query" in func_spec["parameters"].get("properties", {}):
            args["query"] = raw_input
        
        # NOWE: Parser argumentów dla genów
        if func_spec.get("gene"):
            args.update(self._parse_gene_arguments(func_spec, raw_input))
        
        print(f"🔧 Prepared args for {func_spec.get('description', 'function')}: {args}")
        return args
    
    def _parse_gene_arguments(self, func_spec: Dict, raw_input: str) -> Dict[str, Any]:
        """Wyciąga argumenty dla genów z natural language"""
        import re
        args = {}
        
        gene_name = func_spec.get("gene", {}).name if func_spec.get("gene") else ""
        properties = func_spec["parameters"].get("properties", {})
        
        # Wzorce dla różnych genów
        if "message" in properties:
            # Pattern: "execute basic_log with hello world" -> message = "hello world"
            patterns = [
                rf'execute\s+{gene_name}\s+with\s+(.+)',
                rf'{gene_name}\s+with\s+(.+)',
                rf'log\s+(.+)',
                rf'message\s+(.+)',
                r'with\s+(.+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, raw_input, re.IGNORECASE)
                if match:
                    args["message"] = match.group(1).strip()
                    break
        
        if "key" in properties and "value" in properties:
            # Pattern: "store key_name as value_content"
            store_patterns = [
                r'store\s+(\w+)\s+as\s+(.+)',
                r'save\s+(\w+)\s+with\s+(.+)',
                r'memory_store\s+(\w+)\s+(.+)'
            ]
            
            for pattern in store_patterns:
                match = re.search(pattern, raw_input, re.IGNORECASE)
                if match:
                    args["key"] = match.group(1)
                    args["value"] = match.group(2)
                    break
        
        if "level" in properties and "message" not in args:
            # Sprawdź czy jest poziom loga
            level_patterns = [
                r'(DEBUG|INFO|WARNING|ERROR|CRITICAL)',
                r'level\s+(\w+)'
            ]
            
            for pattern in level_patterns:
                match = re.search(pattern, raw_input, re.IGNORECASE)
                if match:
                    args["level"] = match.group(1).upper()
                    break
        
        return args
    
    def get_function_registry_for_openai(self) -> List[Dict[str, Any]]:
        """Zwraca specyfikacje funkcji w formacie OpenAI function calling"""
        functions = []
        
        for func_name, func_spec in self.available_functions.items():
            if func_spec.get("function"):  # Tylko jeśli funkcja istnieje
                functions.append({
                    "name": func_name,
                    "description": func_spec["description"],
                    "parameters": func_spec["parameters"]
                })
        
        return functions
    
    def list_available_functions(self) -> Dict[str, str]:
        """Zwraca listę dostępnych funkcji z opisami"""
        return {
            func_name: func_spec["description"] 
            for func_name, func_spec in self.available_functions.items()
        }

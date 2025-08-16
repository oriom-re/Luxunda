# app_v2/ai/openai_function_caller.py
"""
OpenAI Function Caller dostosowany do app_v2 - geny jako funkcje
"""

import json
import ast
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

class OpenAIFunctionCaller:
    """System wywoływania funkcji przez OpenAI - wersja app_v2"""
    
    def __init__(self, openai_api_key: str):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.available_functions = {}
        self.model = "gpt-4"
        
    async def register_gene_as_function(self, gene_name: str, gene) -> bool:
        """Rejestruje gen jako dostępną funkcję dla OpenAI"""
        try:
            # Wyciągnij informacje o genie
            name = gene.name
            description = gene.description or f"Gen {name}"
            
            # Ekstraktuj parametry z funkcji genu
            parameters = self._extract_function_parameters_from_gene(gene)
            
            function_schema = {
                "type": "function",
                "function": {
                    "name": f"gene_{name}",
                    "description": description,
                    "parameters": parameters
                }
            }
            
            self.available_functions[f"gene_{name}"] = {
                "schema": function_schema,
                "gene": gene,
                "type": "gene"
            }
            
            print(f"🧬 Registered gene as function: {name}")
            return True
            
        except Exception as e:
            print(f"❌ Error registering gene {gene_name}: {e}")
            return False
    
    async def register_database_function(self, func_name: str, func, description: str, parameters: Dict[str, Any]) -> bool:
        """Rejestruje funkcję bazodanową"""
        try:
            function_schema = {
                "type": "function", 
                "function": {
                    "name": func_name,
                    "description": description,
                    "parameters": parameters
                }
            }
            
            self.available_functions[func_name] = {
                "schema": function_schema,
                "function": func,
                "type": "database"
            }
            
            print(f"🗄️ Registered database function: {func_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error registering function {func_name}: {e}")
            return False
    
    def _extract_function_parameters_from_gene(self, gene) -> Dict[str, Any]:
        """Ekstraktuje parametry z genu używając inspection"""
        type_map = {
            "str": "string",
            "int": "integer", 
            "float": "number",
            "bool": "boolean",
            "dict": "object",
            "list": "array"
        }
        
        try:
            import inspect
            
            if hasattr(gene, 'function') and gene.function:
                sig = inspect.signature(gene.function)
                
                parameters = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for param_name, param in sig.parameters.items():
                    if param_name in ['self', 'cls']:
                        continue
                    
                    # Określ typ
                    param_type = "string"  # default
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
                    
                    parameters["properties"][param_name] = {
                        "type": param_type,
                        "description": f"Parameter {param_name} for gene {gene.name}"
                    }
                    
                    # Required jeśli nie ma default
                    if param.default == inspect.Parameter.empty:
                        parameters["required"].append(param_name)
                
                return parameters
            
        except Exception as e:
            print(f"⚠️ Could not extract parameters for gene {gene.name}: {e}")
        
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def call_with_functions(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Wywołuje OpenAI z dostępnymi funkcjami"""
        try:
            # Przygotuj tools dla OpenAI
            tools = [func_info["schema"] for func_info in self.available_functions.values()]
            
            messages = [
                {
                    "role": "system",
                    "content": """Jesteś Lux - inteligentny agent w systemie LuxOS app_v2.
                    Masz dostęp do genów (funkcji biologicznych) i operacji bazodanowych.
                    Analizuj intencje użytkownika i wybieraj odpowiednie funkcje do wykonania.
                    Geny to atomowe jednostki funkcjonalności - używaj ich mądrze.
                    Odpowiadaj po polsku w sposób pomocny i konkretny."""
                },
                {"role": "user", "content": prompt}
            ]
            
            if context:
                messages.insert(1, {
                    "role": "system",
                    "content": f"Kontekst: {json.dumps(context, ensure_ascii=False)}"
                })
            
            print(f"🤖 Calling OpenAI with {len(tools)} available functions...")
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                temperature=0.7
            )
            
            message = response.choices[0].message
            
            result = {
                "response": message.content,
                "tool_calls": [],
                "function_results": []
            }
            
            # Wykonaj function calls
            if message.tool_calls:
                print(f"🚀 OpenAI wants to call {len(message.tool_calls)} functions")
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"📞 Calling: {function_name}({function_args})")
                    
                    # Wykonaj funkcję
                    function_result = await self._execute_function(function_name, function_args)
                    
                    result["tool_calls"].append({
                        "function": function_name,
                        "arguments": function_args,
                        "result": function_result
                    })
                    result["function_results"].append(function_result)
                
                # Drugi call z wynikami funkcji
                messages.append(message)
                for tool_call, func_result in zip(message.tool_calls, result["function_results"]):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(func_result, ensure_ascii=False)
                    })
                
                # Finalna odpowiedź
                final_response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )
                
                result["final_response"] = final_response.choices[0].message.content
            
            return result
            
        except Exception as e:
            return {
                "error": f"OpenAI call failed: {str(e)}",
                "response": None,
                "tool_calls": [],
                "function_results": []
            }
    
    async def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje funkcję (gen lub database)"""
        if function_name not in self.available_functions:
            return {"error": f"Function {function_name} not available"}
        
        func_info = self.available_functions[function_name]
        func_type = func_info["type"]
        
        try:
            if func_type == "gene":
                # Wykonaj gen
                gene = func_info["gene"]
                result = await gene.execute(**arguments)
                
                return {
                    "success": True,
                    "result": result,
                    "function_name": function_name,
                    "type": "gene_execution",
                    "gene_name": gene.name
                }
                
            elif func_type == "database":
                # Wykonaj funkcję bazodanową
                function = func_info["function"]
                
                if asyncio.iscoroutinefunction(function):
                    result = await function(**arguments)
                else:
                    result = function(**arguments)
                
                return {
                    "success": True,
                    "result": result,
                    "function_name": function_name,
                    "type": "database_operation"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name,
                "arguments": arguments
            }
    
    async def auto_register_from_ai_brain(self, ai_brain) -> int:
        """Automatycznie rejestruje funkcje z AI Brain"""
        registered_count = 0
        
        try:
            # Rejestruj geny
            for gene_name, gene in ai_brain.gene_functions.items():
                if await self.register_gene_as_function(gene_name, gene):
                    registered_count += 1
            
            # Rejestruj funkcje database
            database_functions = [
                ("get_soul_by_name", "Pobiera soul z bazy po nazwie"),
                ("save_soul", "Zapisuje soul do bazy danych"),
                ("get_soul_by_field", "Pobiera soul z bazy po dowolnym polu")
            ]
            
            for func_name, description in database_functions:
                if func_name in ai_brain.available_functions:
                    func_spec = ai_brain.available_functions[func_name]
                    await self.register_database_function(
                        func_name,
                        func_spec["function"],
                        description,
                        func_spec["parameters"]
                    )
                    registered_count += 1
            
            print(f"✅ Auto-registered {registered_count} functions from AI Brain")
            return registered_count
            
        except Exception as e:
            print(f"❌ Auto-registration failed: {e}")
            return 0
    
    def get_available_functions(self) -> List[str]:
        """Zwraca listę dostępnych funkcji"""
        return list(self.available_functions.keys())
    
    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """Zwraca schematy funkcji"""
        return [func_info["schema"] for func_info in self.available_functions.values()]

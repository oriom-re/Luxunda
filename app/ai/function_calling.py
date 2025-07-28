
import json
import openai
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.beings.base import Being
from app.beings.function_being import FunctionBeing
from app.beings.being_factory import BeingFactory
from app.safety.executor import SafeCodeExecutor
from app_v2.beings.thread import Thread
import ast

class OpenAIFunctionCaller:
    """System wywoływania funkcji przez OpenAI"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.available_functions = {}
        
    async def register_function_being(self, function_being: FunctionBeing) -> bool:
        """Rejestruje byt funkcyjny jako dostępną funkcję dla OpenAI"""
        try:
            source = function_being.genesis.get('source', '')
            name = function_being.genesis.get('name', 'unknown_function')
            description = function_being.genesis.get('description', f'Funkcja {name}')
            
            # Ekstraktuj parametry z kodu funkcji
            parameters = self._extract_function_parameters(source, name)
            
            function_schema = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters
                }
            }
            
            self.available_functions[name] = {
                "schema": function_schema,
                "being": function_being,
                "soul": function_being.soul
            }
            
            return True
            
        except Exception as e:
            print(f"Błąd rejestracji funkcji {name}: {e}")
            return False
    
    def _extract_function_parameters(self, source: str, function_name: str) -> Dict[str, Any]:
        """Ekstraktuje parametry funkcji z kodu źródłowego"""
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "dict": "object",
            "list": "array"
        }
        
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == function_name:
                    parameters = {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }

                    for arg in node.args.args:
                        arg_name = arg.arg
                        annotation = None
                        if arg.annotation:
                            if isinstance(arg.annotation, ast.Name):
                                annotation = type_map.get(arg.annotation.id, "string")
                            elif isinstance(arg.annotation, ast.Subscript):
                                annotation = "array" if arg.annotation.value.id == "list" else "object"
                            else:
                                annotation = "string"
                        else:
                            annotation = "string"

                        parameters["properties"][arg_name] = {
                            "type": annotation,
                            "description": f"Parametr {arg_name}"
                        }
                        parameters["required"].append(arg_name)

                    return parameters

        except Exception as e:
            print(f"Błąd ekstraktowania parametrów: {e}")
        
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    async def call_with_functions(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Wywołuje OpenAI z dostępnymi funkcjami"""
        try:
            # Przygotuj schemat funkcji dla OpenAI
            # tools = [func_info["schema"] for func_info in self.available_functions.values()]
            tools = []
            for func_info in self.available_functions.values():
                tools.append(func_info["schema"])
                print(f"Zarejestrowano funkcję: {func_info['schema']}")

            message_system = {
                    "role": "system", 
                    "content": """Jesteś Lux - inteligentny agent w systemie LuxOS. 
                    Masz dostęp do funkcji z bytów astralnych. Używaj ich mądrze.
                    Odpowiadaj po polsku."""
                }
            messages_user = [
                
                {"role": "user", "content": prompt}
            ]
            thread = Thread.get_current_thread(id)
            thread.add_message(message_system)
            thread.add_messages(messages_user)
            messages = [message_system] + messages_user
            
            if context:
                messages.insert(1, {
                    "role": "system",
                    "content": f"Kontekst: {json.dumps(context, ensure_ascii=False)}"
                })
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                # model="gpt-3.5-turbo",
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
            
            # Jeśli OpenAI chce wywołać funkcje
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Wywołaj funkcję
                    function_result = await self._execute_function(function_name, function_args)
                    
                    result["tool_calls"].append({
                        "function": function_name,
                        "arguments": function_args,
                        "result": function_result
                    })
                    result["function_results"].append(function_result)
                
                # Drugi wywołanie z wynikami funkcji
                messages.append(message)
                for tool_call, func_result in zip(message.tool_calls, result["function_results"]):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(func_result, ensure_ascii=False)
                    })
                    thread.add_message({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(func_result, ensure_ascii=False)
                    })
                
                # Otrzymaj finalną odpowiedź
                final_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7
                )
                
                result["final_response"] = final_response.choices[0].message.content
                thread.add_message({
                    "role": "assistant",
                    "content": final_response.choices[0].message.content
                })
            return result
            
        except Exception as e:
            return {
                "error": f"Błąd wywołania OpenAI: {str(e)}",
                "response": None,
                "tool_calls": [],
                "function_results": []
            }
    
    async def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje funkcję z bytu"""
        if function_name not in self.available_functions:
            return {"error": f"Funkcja {function_name} nie jest dostępna"}
        
        func_info = self.available_functions[function_name]
        function_being = func_info["being"]
        
        try:
            # Wykonaj funkcję
            result = await function_being(**arguments)
            
            # Zapisz wywołanie w pamięci bytu
            memory_entry = {
                "type": "openai_execution",
                "timestamp": datetime.now().isoformat(),
                "arguments": arguments,
                "result": str(result.get('result', '')),
                "success": result.get('success', False),
                "called_by": "openai_function_calling"
            }
            function_being.memories.append(memory_entry)
            await function_being.save()
            print(f"✅ Wykonano funkcję {function_name} z argumentami {arguments} rezultatem {result}") 
            return {
                "success": result.get('success', False),
                "result": result.get('result'),
                "output": result.get('output', ''),
                "function_name": function_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Błąd wykonania funkcji {function_name}: {str(e)}",
                "function_name": function_name
            }
    
    def get_available_functions(self) -> List[str]:
        """Zwraca listę dostępnych funkcji"""
        return list(self.available_functions.keys())
    
    async def auto_register_function_beings(self) -> int:
        """Automatycznie rejestruje wszystkie byty funkcyjne"""
        registered_count = 0
        
        try:
            # Pobierz wszystkie byty
            all_beings = await Being.get_all()
            
            for being in all_beings:
                if being.genesis.get('type') == 'function':
                    # Konwertuj na FunctionBeing
                    function_being = FunctionBeing(
                        soul=being.soul,
                        genesis=being.genesis,
                        attributes=being.attributes,
                        memories=being.memories,
                        self_awareness=being.self_awareness,
                        created_at=being.created_at
                    )
                    
                    if await self.register_function_being(function_being):
                        registered_count += 1
            
            return registered_count
            
        except Exception as e:
            print(f"Błąd auto-rejestracji funkcji: {e}")
            return 0

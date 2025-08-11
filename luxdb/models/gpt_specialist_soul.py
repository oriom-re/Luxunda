
#!/usr/bin/env python3
"""
GPT Specialist Soul - Self-contained GPT specialist with tools
"""

import json
import openai
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .soul import Soul

class GPTSpecialistSoul:
    """Factory for creating GPT specialist souls with built-in tools"""
    
    @classmethod
    async def create_gpt_callfunction_soul(
        cls, 
        specialist_name: str,
        api_key: str,
        model: str = "gpt-4",
        available_functions: Dict[str, Callable] = None,
        system_prompt: str = None
    ) -> Soul:
        """
        Tworzy specjalistyczną Soul GPT z wbudowanymi narzędziami
        
        Args:
            specialist_name: Nazwa specjalisty (np. "code_analyst", "data_processor")
            api_key: Klucz API OpenAI
            model: Model GPT do użycia
            available_functions: Słownik funkcji dostępnych dla GPT
            system_prompt: Systemowy prompt dla specjalisty
        """
        
        # Przygotuj funkcje do tools format dla OpenAI
        tools_schema = []
        if available_functions:
            for func_name, func in available_functions.items():
                tool_schema = cls._create_tool_schema(func_name, func)
                if tool_schema:
                    tools_schema.append(tool_schema)
        
        # Genotyp dla GPT specjalisty
        genotype = {
            "genesis": {
                "name": specialist_name,
                "type": "gpt_specialist",
                "version": "1.0.0",
                "description": f"GPT specialist: {specialist_name}",
                "created_at": datetime.now().isoformat()
            },
            "attributes": {
                "api_key": {"py_type": "str", "private": True},
                "model": {"py_type": "str", "default": model},
                "system_prompt": {"py_type": "str"},
                "conversation_history": {"py_type": "list", "default": []},
                "tools_schema": {"py_type": "list"},
                "execution_count": {"py_type": "int", "default": 0}
            },
            "functions": {
                "gpt_call": {
                    "py_type": "function",
                    "description": "Main GPT call with tools",
                    "is_primary": True,
                    "parameters": {
                        "user_message": {"type": "str", "required": True},
                        "use_tools": {"type": "bool", "default": True}
                    }
                },
                "add_tool": {
                    "py_type": "function", 
                    "description": "Add new tool to specialist",
                    "parameters": {
                        "tool_name": {"type": "str", "required": True},
                        "tool_function": {"type": "callable", "required": True}
                    }
                },
                "get_conversation": {
                    "py_type": "function",
                    "description": "Get conversation history"
                }
            }
        }
        
        # Utwórz Soul
        soul = await Soul.create(genotype, alias=specialist_name)
        
        # Zarejestruj funkcje w soul
        soul._register_immutable_function("gpt_call", cls._create_gpt_call_function(
            api_key, model, system_prompt, available_functions or {}, tools_schema
        ))
        
        soul._register_immutable_function("add_tool", cls._create_add_tool_function())
        soul._register_immutable_function("get_conversation", cls._create_get_conversation_function())
        
        return soul
    
    @classmethod
    def _create_gpt_call_function(
        cls, 
        api_key: str, 
        model: str, 
        system_prompt: str,
        available_functions: Dict[str, Callable],
        tools_schema: List[Dict]
    ) -> Callable:
        """Tworzy główną funkcję GPT call"""
        
        def gpt_call(user_message: str, use_tools: bool = True, being_context: Dict = None):
            """
            Główna funkcja wywoływania GPT z narzędziami
            """
            try:
                # Inicjalizacja klienta OpenAI
                client = openai.OpenAI(api_key=api_key)
                
                # Pobierz historię konwersacji z kontekstu being
                conversation_history = []
                if being_context:
                    conversation_history = being_context.get('data', {}).get('conversation_history', [])
                
                # Przygotuj messages
                messages = []
                
                # Dodaj system prompt jeśli istnieje
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                # Dodaj historię konwersacji
                messages.extend(conversation_history)
                
                # Dodaj aktualną wiadomość użytkownika
                messages.append({"role": "user", "content": user_message})
                
                # Przygotuj parametry wywołania
                call_params = {
                    "model": model,
                    "messages": messages
                }
                
                # Dodaj tools jeśli są dostępne i włączone
                if use_tools and tools_schema:
                    call_params["tools"] = tools_schema
                    call_params["tool_choice"] = "auto"
                
                # Wywołaj GPT
                response = client.chat.completions.create(**call_params)
                
                # Przetwórz odpowiedź
                result = cls._process_gpt_response(
                    response, available_functions, being_context
                )
                
                # Aktualizuj historię konwersacji
                if being_context:
                    being_data = being_context.get('data', {})
                    if 'conversation_history' not in being_data:
                        being_data['conversation_history'] = []
                    
                    # Dodaj user message
                    being_data['conversation_history'].append({
                        "role": "user", 
                        "content": user_message
                    })
                    
                    # Dodaj assistant response
                    being_data['conversation_history'].append({
                        "role": "assistant",
                        "content": result.get('content', ''),
                        "tool_calls": result.get('tool_calls', [])
                    })
                    
                    # Zwiększ licznik wykonań
                    being_data['execution_count'] = being_data.get('execution_count', 0) + 1
                
                return result
                
            except Exception as e:
                return {
                    "error": f"GPT call failed: {str(e)}",
                    "success": False
                }
        
        return gpt_call
    
    @classmethod
    def _process_gpt_response(
        cls, 
        response, 
        available_functions: Dict[str, Callable],
        being_context: Dict = None
    ) -> Dict[str, Any]:
        """Przetwarza odpowiedź GPT i wykonuje tool calls"""
        
        message = response.choices[0].message
        result = {
            "content": message.content,
            "success": True,
            "tool_calls": [],
            "tool_results": []
        }
        
        # Sprawdź czy są tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "name": tool_name,
                    "arguments": tool_args
                })
                
                # Wykonaj funkcję jeśli jest dostępna
                if tool_name in available_functions:
                    try:
                        # Dodaj being_context do argumentów jeśli funkcja tego potrzebuje
                        if 'being_context' in available_functions[tool_name].__code__.co_varnames:
                            tool_args['being_context'] = being_context
                        
                        tool_result = available_functions[tool_name](**tool_args)
                        
                        result["tool_results"].append({
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "result": tool_result,
                            "success": True
                        })
                        
                    except Exception as e:
                        result["tool_results"].append({
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "error": str(e),
                            "success": False
                        })
                else:
                    result["tool_results"].append({
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "error": f"Function {tool_name} not available",
                        "success": False
                    })
        
        return result
    
    @classmethod
    def _create_tool_schema(cls, func_name: str, func: Callable) -> Optional[Dict]:
        """Tworzy schema narzędzia dla OpenAI tools format"""
        
        try:
            import inspect
            
            sig = inspect.signature(func)
            doc = inspect.getdoc(func) or f"Function {func_name}"
            
            # Podstawowe schema
            schema = {
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": doc,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            # Dodaj parametry
            for param_name, param in sig.parameters.items():
                # Pomiń being_context - to jest wewnętrzny parametr
                if param_name == 'being_context':
                    continue
                    
                param_schema = {"type": "string"}  # domyślnie string
                
                # Spróbuj określić typ z annotacji
                if param.annotation != param.empty:
                    if param.annotation == int:
                        param_schema["type"] = "integer"
                    elif param.annotation == float:
                        param_schema["type"] = "number"
                    elif param.annotation == bool:
                        param_schema["type"] = "boolean"
                    elif param.annotation == list:
                        param_schema["type"] = "array"
                    elif param.annotation == dict:
                        param_schema["type"] = "object"
                
                schema["function"]["parameters"]["properties"][param_name] = param_schema
                
                # Dodaj do required jeśli nie ma wartości domyślnej
                if param.default == param.empty:
                    schema["function"]["parameters"]["required"].append(param_name)
            
            return schema
            
        except Exception as e:
            print(f"Error creating tool schema for {func_name}: {e}")
            return None
    
    @classmethod
    def _create_add_tool_function(cls) -> Callable:
        """Tworzy funkcję do dodawania nowych narzędzi"""
        
        def add_tool(tool_name: str, tool_function: Callable, being_context: Dict = None):
            """Dodaje nowe narzędzie do specjalisty"""
            # Ta funkcja pozwoli dynamicznie dodawać nowe narzędzia
            # Implementacja zależna od potrzeb
            return {
                "success": True,
                "message": f"Tool {tool_name} would be added",
                "note": "Dynamic tool addition not implemented yet"
            }
        
        return add_tool
    
    @classmethod  
    def _create_get_conversation_function(cls) -> Callable:
        """Tworzy funkcję do pobierania historii konwersacji"""
        
        def get_conversation(being_context: Dict = None):
            """Pobiera historię konwersacji"""
            if being_context:
                history = being_context.get('data', {}).get('conversation_history', [])
                return {
                    "success": True,
                    "conversation_history": history,
                    "message_count": len(history)
                }
            return {
                "success": False,
                "error": "No being context available"
            }
        
        return get_conversation

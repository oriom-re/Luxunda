#!/usr/bin/env python3
"""
GPT Specialist Soul Factory - Creates regular Soul instances with GPT capabilities
"""

import json
import openai
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .soul import Soul


class GPTSpecialistFactory:
    """Factory for creating Soul instances with built-in GPT capabilities"""

    @classmethod
    async def create_gpt_specialist_soul(
        cls,
        specialist_name: str,
        api_key: str,
        model: str = "gpt-4",
        available_functions: Dict[str, Callable] = None,
        system_prompt: str = None,
        alias: str = None
    ) -> Soul:
        """
        Tworzy regularną Soul z wbudowanymi funkcjami GPT

        Args:
            specialist_name: Nazwa specjalisty
            api_key: Klucz API OpenAI
            model: Model GPT
            available_functions: Funkcje dostępne dla GPT jako tools
            system_prompt: Prompt systemowy
            alias: Alias dla Soul

        Returns:
            Soul z funkcjami GPT w _function_registry
        """

        # Przygotuj tools schema dla OpenAI
        tools_schema = []
        if available_functions:
            for func_name, func in available_functions.items():
                tool_schema = cls._create_tool_schema(func_name, func)
                if tool_schema:
                    tools_schema.append(tool_schema)

        # Genotyp dla GPT specjalisty - CZYSTA SOUL
        genotype = {
            "genesis": {
                "name": specialist_name,
                "type": "gpt_specialist",
                "version": "1.0.0",
                "description": f"GPT specialist: {specialist_name}",
                "created_at": datetime.now().isoformat()
            },
            "attributes": {
                "model": {"py_type": "str", "default": model},
                "system_prompt": {"py_type": "str", "default": system_prompt or ""},
                "conversation_history": {"py_type": "list", "default": []},
                "total_calls": {"py_type": "int", "default": 0},
                "last_call": {"py_type": "str"}
            },
            "functions": {
                "gpt_call": {
                    "description": "Make GPT call with tools support",
                    "parameters": {
                        "user_message": {"py_type": "str", "required": True},
                        "use_tools": {"py_type": "bool", "default": True}
                    },
                    "tools_schema": tools_schema
                },
                "add_conversation": {
                    "description": "Add message to conversation history",
                    "parameters": {
                        "role": {"py_type": "str", "required": True},
                        "content": {"py_type": "str", "required": True}
                    }
                },
                "get_conversation": {
                    "description": "Get conversation history",
                    "parameters": {}
                }
            }
        }

        # Utwórz REGULARNĄ Soul
        soul = await Soul.create(genotype, alias or f"gpt_{specialist_name}")

        # Załaduj funkcje do rejestru Soul (bez modyfikacji genotypu!)
        soul._register_immutable_function("gpt_call", cls._create_gpt_call_function(
            api_key, model, system_prompt, available_functions or {}, tools_schema
        ))

        soul._register_immutable_function("add_conversation", cls._create_add_conversation_function())
        soul._register_immutable_function("get_conversation", cls._create_get_conversation_function())

        # Załaduj dodatkowe funkcje tools
        if available_functions:
            for func_name, func in available_functions.items():
                soul._register_immutable_function(func_name, func)

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
        """Tworzy główną funkcję GPT call dla Soul"""

        async def gpt_call(user_message: str, use_tools: bool = True, being_context: Dict = None):
            """
            Główna funkcja GPT z tools - działa w kontekście Soul
            """
            try:
                # Inicjalizacja klienta OpenAI
                client = openai.OpenAI(api_key=api_key)

                # Pobierz historię z kontekstu being
                conversation_history = []
                if being_context:
                    conversation_history = being_context.get('data', {}).get('conversation_history', [])

                # Przygotuj messages
                messages = []

                # System prompt
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

                # Historia konwersacji
                messages.extend(conversation_history)

                # Aktualna wiadomość
                messages.append({"role": "user", "content": user_message})

                # Wywołanie OpenAI
                if use_tools and tools_schema:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        tools=tools_schema,
                        tool_choice="auto"
                    )
                else:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages
                    )

                assistant_message = response.choices[0].message
                result = {
                    "response": assistant_message.content,
                    "tool_calls": [],
                    "usage": dict(response.usage) if response.usage else {}
                }

                # Obsługa tool calls
                if assistant_message.tool_calls:
                    for tool_call in assistant_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)

                        if func_name in available_functions:
                            try:
                                # Użyj await dla funkcji asynchronicznych
                                if inspect.iscoroutinefunction(available_functions[func_name]):
                                    tool_result = await available_functions[func_name](**func_args)
                                else:
                                    tool_result = available_functions[func_name](**func_args)

                                result["tool_calls"].append({
                                    "function": func_name,
                                    "arguments": func_args,
                                    "result": tool_result
                                })
                            except Exception as e:
                                result["tool_calls"].append({
                                    "function": func_name,
                                    "arguments": func_args,
                                    "error": str(e)
                                })

                # Aktualizuj statystyki w being_context jeśli dostępny
                if being_context:
                    if 'data' not in being_context:
                        being_context['data'] = {}

                    being_context['data']['total_calls'] = being_context['data'].get('total_calls', 0) + 1
                    being_context['data']['last_call'] = datetime.now().isoformat()

                    # Dodaj do historii
                    if 'conversation_history' not in being_context['data']:
                        being_context['data']['conversation_history'] = []

                    being_context['data']['conversation_history'].append({
                        "role": "user",
                        "content": user_message
                    })

                    if assistant_message.content:
                        being_context['data']['conversation_history'].append({
                            "role": "assistant",
                            "content": assistant_message.content
                        })

                return result

            except Exception as e:
                return {
                    "error": str(e),
                    "response": None,
                    "tool_calls": []
                }

        return gpt_call

    @classmethod
    def _create_add_conversation_function(cls) -> Callable:
        """Funkcja dodawania wiadomości do historii"""
        def add_conversation(role: str, content: str, being_context: Dict = None):
            if being_context and 'data' in being_context:
                if 'conversation_history' not in being_context['data']:
                    being_context['data']['conversation_history'] = []

                being_context['data']['conversation_history'].append({
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat()
                })
                return {"success": True, "message": "Message added to conversation"}

            return {"success": False, "error": "No being context available"}

        return add_conversation

    @classmethod
    def _create_get_conversation_function(cls) -> Callable:
        """Funkcja pobierania historii konwersacji"""
        def get_conversation(being_context: Dict = None):
            if being_context and 'data' in being_context:
                return being_context['data'].get('conversation_history', [])
            return []

        return get_conversation

    @classmethod
    def _create_tool_schema(cls, func_name: str, func: Callable) -> Optional[Dict]:
        """Tworzy schema narzędzia dla OpenAI Tools API"""
        try:
            import inspect
            sig = inspect.signature(func)

            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }

            for param_name, param in sig.parameters.items():
                if param_name == "being_context":  # Pomijamy kontekst
                    continue

                param_info = {
                    "type": "string"  # Domyślnie string
                }

                # Próba określenia typu z annotacji
                if param.annotation != param.empty:
                    if param.annotation == int:
                        param_info["type"] = "integer"
                    elif param.annotation == float:
                        param_info["type"] = "number"
                    elif param.annotation == bool:
                        param_info["type"] = "boolean"
                    elif param.annotation == list:
                        param_info["type"] = "array"
                    elif param.annotation == dict:
                        param_info["type"] = "object"

                parameters["properties"][param_name] = param_info

                # Sprawdź czy wymagany
                if param.default == param.empty:
                    parameters["required"].append(param_name)

            return {
                "type": "function",
                "function": {
                    "name": func_name,
                    "description": func.__doc__ or f"Function {func_name}",
                    "parameters": parameters
                }
            }

        except Exception as e:
            print(f"Error creating tool schema for {func_name}: {e}")
            return None
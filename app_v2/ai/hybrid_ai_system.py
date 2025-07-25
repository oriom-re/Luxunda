# app_v2/ai/hybrid_ai_system.py
"""
Hybrydowy system AI - łączy AI Brain z OpenAI Function Calling
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from app_v2.ai.ai_brain import AIBrain
from app_v2.genetics.gene_registry import GeneRegistry

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

class HybridAISystem:
    """Łączy AI Brain z OpenAI Function Calling dla najlepszych rezultatów"""
    
    def __init__(self, openai_api_key: str = None):
        self.ai_brain = AIBrain()
        self.openai_enabled = OPENAI_AVAILABLE and openai_api_key
        
        if self.openai_enabled:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            self.model = "gpt-4"
        else:
            self.openai_client = None
            print("⚠️ OpenAI nie jest dostępne, używam tylko AI Brain")
    
    async def process_request(self, user_input: str, context: Dict[str, Any] = None, 
                            use_openai: bool = True) -> Dict[str, Any]:
        """
        Główna funkcja - przetwarza request używając AI Brain i/lub OpenAI
        """
        print(f"🤖 Hybrid AI processing: '{user_input}'")
        
        # 1. Zawsze użyj AI Brain dla podstawowej analizy
        brain_result = await self.ai_brain.process_user_intent(user_input, context)
        
        result = {
            "user_input": user_input,
            "ai_brain_analysis": brain_result,
            "openai_analysis": None,
            "final_result": None,
            "method_used": "ai_brain_only"
        }
        
        # 2. Jeśli OpenAI jest dostępne i requested, użyj go dla lepszej analizy
        if self.openai_enabled and use_openai:
            try:
                openai_result = await self._process_with_openai(user_input, context)
                result["openai_analysis"] = openai_result
                result["method_used"] = "hybrid"
                
                # Kombinuj wyniki
                result["final_result"] = self._combine_results(brain_result, openai_result)
                
            except Exception as e:
                print(f"⚠️ OpenAI failed, fallback to AI Brain: {e}")
                result["final_result"] = brain_result
                result["method_used"] = "ai_brain_fallback"
        else:
            result["final_result"] = brain_result
        
        return result
    
    async def _process_with_openai(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Przetwarza request używając OpenAI Function Calling"""
        
        # Przygotuj funkcje dla OpenAI
        available_functions = self._prepare_openai_functions()
        
        messages = [
            {
                "role": "system",
                "content": """Jesteś Lux - inteligentny agent w systemie LuxOS app_v2.
                Masz dostęp do genów (funkcji) i operacji bazodanowych.
                Analizuj intencje użytkownika i wybieraj odpowiednie funkcje.
                Odpowiadaj po polsku w sposób pomocny i konkretny."""
            },
            {"role": "user", "content": user_input}
        ]
        
        if context:
            messages.insert(1, {
                "role": "system", 
                "content": f"Kontekst: {json.dumps(context, ensure_ascii=False)}"
            })
        
        try:
            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model=self.model,
                messages=messages,
                tools=available_functions if available_functions else None,
                tool_choice="auto" if available_functions else None,
                temperature=0.7
            )
            
            message = response.choices[0].message
            
            result = {
                "response": message.content,
                "tool_calls": [],
                "function_results": []
            }
            
            # Wykonaj function calls jeśli są
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    print(f"🚀 OpenAI calls: {function_name}({function_args})")
                    
                    # Wykonaj funkcję przez AI Brain
                    function_result = await self._execute_function_via_brain(function_name, function_args)
                    
                    result["tool_calls"].append({
                        "function": function_name,
                        "arguments": function_args,
                        "result": function_result
                    })
                    result["function_results"].append(function_result)
                
                # Drugi call z wynikami
                messages.append(message)
                for tool_call, func_result in zip(message.tool_calls, result["function_results"]):
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(func_result, ensure_ascii=False)
                    })
                
                final_response = await asyncio.to_thread(
                    self.openai_client.chat.completions.create,
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )
                
                result["final_response"] = final_response.choices[0].message.content
            
            return result
            
        except Exception as e:
            return {"error": f"OpenAI processing failed: {e}"}
    
    def _prepare_openai_functions(self) -> List[Dict[str, Any]]:
        """Przygotowuje funkcje AI Brain dla OpenAI Function Calling"""
        functions = []
        
        for func_name, func_spec in self.ai_brain.available_functions.items():
            if func_spec.get("function"):
                openai_function = {
                    "type": "function",
                    "function": {
                        "name": func_name,
                        "description": func_spec["description"],
                        "parameters": func_spec["parameters"]
                    }
                }
                functions.append(openai_function)
        
        print(f"📋 Prepared {len(functions)} functions for OpenAI")
        return functions
    
    async def _execute_function_via_brain(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje funkcję przez AI Brain"""
        try:
            if function_name not in self.ai_brain.available_functions:
                return {"error": f"Function {function_name} not available"}
            
            func_spec = self.ai_brain.available_functions[function_name]
            function = func_spec["function"]
            
            # Wykonaj funkcję
            if asyncio.iscoroutinefunction(function):
                result = await function(**arguments)
            else:
                result = function(**arguments)
            
            return {
                "success": True,
                "result": result,
                "function_name": function_name,
                "arguments": arguments
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "function_name": function_name,
                "arguments": arguments
            }
    
    def _combine_results(self, brain_result: Dict[str, Any], openai_result: Dict[str, Any]) -> Dict[str, Any]:
        """Kombinuje wyniki z AI Brain i OpenAI"""
        
        # Jeśli OpenAI wykonał funkcje, użyj jego wyników
        if openai_result.get("tool_calls"):
            return {
                "method": "openai_function_calling",
                "ai_brain_intent": brain_result["intent_analysis"]["intent"],
                "openai_response": openai_result.get("final_response", openai_result.get("response")),
                "functions_executed": openai_result["tool_calls"],
                "success": True
            }
        
        # Jeśli OpenAI nie wykonał funkcji, ale AI Brain tak
        elif brain_result.get("results"):
            return {
                "method": "ai_brain_execution", 
                "intent": brain_result["intent_analysis"]["intent"],
                "openai_analysis": openai_result.get("response"),
                "brain_results": brain_result["results"],
                "success": any(r.get("success", False) for r in brain_result["results"])
            }
        
        # Tylko analiza tekstu
        else:
            return {
                "method": "text_analysis",
                "intent": brain_result["intent_analysis"]["intent"],
                "openai_response": openai_result.get("response"),
                "confidence": brain_result["intent_analysis"]["confidence"],
                "success": True
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Zwraca status systemu"""
        return {
            "ai_brain_functions": len(self.ai_brain.available_functions),
            "ai_brain_genes": len(self.ai_brain.gene_functions),
            "openai_enabled": self.openai_enabled,
            "available_functions": list(self.ai_brain.available_functions.keys()),
            "gene_functions": list(self.ai_brain.gene_functions.keys())
        }
    
    async def chat_mode(self):
        """Tryb interaktywnego chatu"""
        print("🤖 Hybrid AI Chat Mode - wpisz 'quit' aby wyjść")
        print(f"📊 System status: {self.get_system_status()}")
        
        while True:
            try:
                user_input = input("\n👤 You: ")
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Do widzenia!")
                    break
                
                result = await self.process_request(user_input)
                
                final_result = result["final_result"]
                method = result["method_used"]
                
                print(f"🤖 Lux ({method}):")
                
                if method == "hybrid" and final_result.get("openai_response"):
                    print(final_result["openai_response"])
                elif final_result.get("results"):
                    for res in final_result["results"][:3]:
                        if res.get("success"):
                            print(f"✅ {res['function_name']}: {res['result']}")
                        else:
                            print(f"❌ {res['function_name']}: {res['error']}")
                else:
                    print(f"Intent: {final_result.get('intent', 'unknown')}")
                
            except KeyboardInterrupt:
                print("\n👋 Do widzenia!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

# Test function
async def test_hybrid_system():
    """Test hybrydowego systemu"""
    from app_v2.database.db_manager import init_database
    from app_v2.core.module_registry import ModuleRegistry
    
    # Initialize
    await init_database()
    await ModuleRegistry.register_all_modules_from_directory('app_v2/gen_files')
    
    # Create hybrid system
    hybrid = HybridAISystem()  # Bez API key = tylko AI Brain
    
    print("🧪 Testing Hybrid AI System")
    print(f"📊 Status: {hybrid.get_system_status()}")
    
    test_inputs = [
        "Find soul named logger",
        "Execute basic_log with test message", 
        "What genes are available?",
        "Create a new entity called test_bot"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 Test: {user_input}")
        result = await hybrid.process_request(user_input, use_openai=False)
        
        final = result["final_result"]
        print(f"🎯 Intent: {final.get('intent_analysis', {}).get('intent', 'unknown')}")
        print(f"🔧 Method: {result['method_used']}")
        
        if final.get("results"):
            for res in final["results"][:2]:
                status = "✅" if res.get("success") else "❌"
                print(f"  {status} {res['function_name']}")

if __name__ == "__main__":
    asyncio.run(test_hybrid_system())



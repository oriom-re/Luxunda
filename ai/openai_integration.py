# app_v2/ai/openai_integration.py
"""
Integracja z OpenAI dla bardziej zaawansowanej analizy intencji
"""

import json
from typing import Dict, Any, List, Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

class OpenAIIntegration:
    """Integracja z OpenAI API dla analizy intencji i function calling"""
    
    def __init__(self, api_key: str = None):
        if OPENAI_AVAILABLE and api_key:
            self.client = openai.AsyncOpenAI(api_key=api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            if not OPENAI_AVAILABLE:
                print("⚠️ OpenAI nie jest zainstalowane. Użyj: pip install openai")
            else:
                print("⚠️ Brak API key dla OpenAI")
        
        self.model = "gpt-4"
    
    async def analyze_intent_with_llm(self, user_input: str, available_functions: List[Dict]) -> Dict[str, Any]:
        """Analizuje intencję używając LLM"""
        if not self.enabled:
            return {
                "error": "OpenAI integration not available",
                "fallback": True
            }
        
        try:
            system_prompt = """You are an AI assistant that analyzes user intents and recommends appropriate functions to call.

Available functions and their purposes:
""" + "\n".join([f"- {func['name']}: {func['description']}" for func in available_functions])
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze this request and suggest which functions to call: {user_input}"}
                ],
                functions=available_functions,
                function_call="auto"
            )
            
            message = response.choices[0].message
            
            return {
                "llm_response": message.content,
                "function_call": message.function_call.name if message.function_call else None,
                "function_arguments": json.loads(message.function_call.arguments) if message.function_call else {},
                "confidence": 0.9,
                "source": "openai_gpt4"
            }
            
        except Exception as e:
            return {
                "error": f"LLM analysis failed: {e}",
                "fallback": True
            }
    
    async def enhance_intent_analysis(self, user_input: str, basic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Wzbogaca podstawową analizę intencji używając LLM"""
        if not self.enabled:
            return basic_analysis
        
        try:
            prompt = f"""
            Analyze this user request and provide enhanced intent analysis:
            
            User input: "{user_input}"
            Basic analysis: {json.dumps(basic_analysis, indent=2)}
            
            Please provide:
            1. More accurate intent classification
            2. Better entity extraction
            3. Confidence scores
            4. Suggested parameters for function calls
            
            Response in JSON format.
            """
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing user intents and extracting relevant information."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Spróbuj sparsować JSON response
            try:
                enhanced = json.loads(response.choices[0].message.content)
                return {
                    **basic_analysis,
                    "enhanced": enhanced,
                    "llm_confidence": enhanced.get("confidence", 0.8),
                    "source": "openai_enhanced"
                }
            except json.JSONDecodeError:
                return {
                    **basic_analysis,
                    "llm_raw_response": response.choices[0].message.content,
                    "source": "openai_raw"
                }
                
        except Exception as e:
            print(f"⚠️ Enhanced analysis failed: {e}")
            return basic_analysis

class MockOpenAI:
    """Mock implementation for testing without OpenAI API"""
    
    def __init__(self):
        self.enabled = True
        print("🤖 Using mock OpenAI for testing")
    
    async def analyze_intent_with_llm(self, user_input: str, available_functions: List[Dict]) -> Dict[str, Any]:
        """Mock LLM analysis"""
        
        # Simple mock responses based on keywords
        user_lower = user_input.lower()
        
        if "find" in user_lower or "get" in user_lower:
            return {
                "llm_response": f"I should help you find something. Looking for functions that can retrieve data.",
                "function_call": "get_soul_by_name",
                "function_arguments": {"name": "logger"},  # Mock argument
                "confidence": 0.7,
                "source": "mock_openai"
            }
        elif "create" in user_lower or "make" in user_lower:
            return {
                "llm_response": f"I should help you create something new.",
                "function_call": "save_soul",
                "function_arguments": {"soul": {"name": "new_entity"}},  # Mock argument
                "confidence": 0.7,
                "source": "mock_openai"
            }
        else:
            return {
                "llm_response": f"I'm not sure what you want to do with: {user_input}",
                "function_call": None,
                "function_arguments": {},
                "confidence": 0.3,
                "source": "mock_openai"
            }
    
    async def enhance_intent_analysis(self, user_input: str, basic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Mock enhanced analysis"""
        return {
            **basic_analysis,
            "enhanced": {
                "mock_enhancement": True,
                "confidence": 0.6,
                "suggested_action": "Use real OpenAI for better results"
            },
            "source": "mock_enhanced"
        }

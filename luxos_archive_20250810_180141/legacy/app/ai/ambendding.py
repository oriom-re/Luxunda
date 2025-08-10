# openai embendding system

import openai
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
Available functions and their purposes:""" + "\n".join([f"- {func['name']}: {func['description']}" for func in available_functions])
            
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
                "fallback": False
            }
        except Exception as e:
            print(f"Error during LLM analysis: {e}")
            return {
                "error": str(e),
                "fallback": True
            }
        
    
    
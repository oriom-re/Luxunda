# init open ai integration

import openai
from typing import Dict, Any, List

client: openai.OpenAI = None

class OpenAIClient:
    """Integracja z OpenAI API dla analizy intencji i function calling"""

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini", openai_module: Any = None):
        global client
        if openai and api_key:
            client = openai.AsyncOpenAI(api_key=api_key)
            self.enabled = True
        else:
            client = None
            self.enabled = False
            if not openai:
                print("⚠️ OpenAI nie jest zainstalowane. Użyj: pip install openai")
            else:
                print("⚠️ Brak API key dla OpenAI")
        
        self.model = model
    
    def get_client(self) -> openai.OpenAI:
        """Zwraca klienta OpenAI"""
        return client
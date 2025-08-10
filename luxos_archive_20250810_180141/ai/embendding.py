
from clients.openai import OpenAIClient
from typing import Dict, Any, List

async def create_embedding(self, text: str) -> List[float]:
    """Tworzy embedding dla danego tekstu"""
    
    try:
        client = OpenAIClient.get_client()
        response = await client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error creating embedding: {e}")
        return {
            "error": str(e),
            "fallback": True
        }
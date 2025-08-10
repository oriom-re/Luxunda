
"""
Geny komunikacji - obsługa interakcji z użytkownikami i systemami
"""

import asyncio
from typing import Dict, Any, List
from ..genes import gene

@gene("genes.communication.advanced_chat")
async def advanced_chat(being, message: str, context: Dict = None) -> Dict[str, Any]:
    """Zaawansowany system czatowania z kontekstem"""
    
    # Pobierz historię konwersacji
    history = getattr(being, 'conversation_history', [])
    
    # Dodaj kontekst jeśli istnieje
    if context:
        message = f"Context: {context}\nMessage: {message}"
    
    # Symulacja przetwarzania przez AI
    response = f"Processed: {message} (with {len(history)} previous messages)"
    
    # Aktualizuj historię
    history.append({
        "input": message,
        "output": response,
        "timestamp": "2025-08-07T10:00:00Z"
    })
    
    # Zapisz w being
    being.conversation_history = history[-100:]  # Zachowaj ostatnie 100
    
    return {
        "response": response,
        "confidence": 0.92,
        "context_used": bool(context),
        "history_length": len(being.conversation_history)
    }

@gene("genes.communication.language_translator")
async def language_translator(being, text: str, target_language: str = "en") -> Dict[str, Any]:
    """Tłumaczenie tekstu na wybrany język"""
    
    # Symulacja tłumaczenia
    translations = {
        "pl": "Cześć, jak się masz?",
        "en": "Hello, how are you?",
        "es": "Hola, ¿cómo estás?",
        "fr": "Salut, comment ça va?",
        "de": "Hallo, wie geht es dir?"
    }
    
    translated = translations.get(target_language, text)
    
    return {
        "original": text,
        "translated": translated,
        "source_language": "auto-detected",
        "target_language": target_language,
        "confidence": 0.95
    }

@gene("genes.communication.text_summarizer")
async def text_summarizer(being, text: str, max_length: int = 100) -> Dict[str, Any]:
    """Streszczenie długiego tekstu"""
    
    words = text.split()
    
    if len(words) <= max_length:
        summary = text
        compression_ratio = 1.0
    else:
        # Prosta logika streszczenia - pierwsze i ostatnie zdania + kluczowe słowa
        sentences = text.split('.')
        if len(sentences) > 2:
            summary = f"{sentences[0].strip()}. ... {sentences[-1].strip()}."
        else:
            summary = text[:max_length] + "..."
        
        compression_ratio = len(summary.split()) / len(words)
    
    return {
        "original_length": len(words),
        "summary": summary,
        "summary_length": len(summary.split()),
        "compression_ratio": compression_ratio
    }

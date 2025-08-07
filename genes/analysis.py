
"""
Geny analizy - analiza tekstu, danych i wzorców
"""

import asyncio
import re
from typing import Dict, Any, List
from ..genes import gene

@gene("genes.analysis.sentiment_analyzer")
async def sentiment_analyzer(being, text: str) -> Dict[str, Any]:
    """Analiza sentymentu tekstu"""
    
    # Proste słowniki do analizy sentymentu
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "dobry", "świetny", "wspaniały"]
    negative_words = ["bad", "terrible", "awful", "horrible", "zły", "okropny", "straszny"]
    
    text_lower = text.lower()
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        sentiment = "positive"
        confidence = min(0.9, 0.5 + (pos_count - neg_count) * 0.1)
    elif neg_count > pos_count:
        sentiment = "negative" 
        confidence = min(0.9, 0.5 + (neg_count - pos_count) * 0.1)
    else:
        sentiment = "neutral"
        confidence = 0.6
    
    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "positive_indicators": pos_count,
        "negative_indicators": neg_count,
        "text_length": len(text.split())
    }

@gene("genes.analysis.entity_extractor")
async def entity_extractor(being, text: str) -> Dict[str, Any]:
    """Ekstrakcja nazwanych encji z tekstu"""
    
    # Proste wyrażenia regularne do identyfikacji encji
    patterns = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "date": r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
        "money": r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
        "url": r'https?://[^\s]+',
        "person": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'  # Prosta identyfikacja imion
    }
    
    entities = {}
    
    for entity_type, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            entities[entity_type] = matches
    
    return {
        "entities": entities,
        "total_found": sum(len(v) for v in entities.values()),
        "text_processed": len(text),
        "entity_types": list(entities.keys())
    }

@gene("genes.analysis.text_classifier")
async def text_classifier(being, text: str, categories: List[str] = None) -> Dict[str, Any]:
    """Klasyfikacja tekstu do kategorii"""
    
    if not categories:
        categories = ["business", "technology", "health", "entertainment", "sports"]
    
    # Słowa kluczowe dla każdej kategorii
    keywords = {
        "business": ["company", "profit", "market", "investment", "sales", "firma", "zysk"],
        "technology": ["computer", "software", "AI", "internet", "data", "komputer", "oprogramowanie"],
        "health": ["doctor", "medicine", "hospital", "treatment", "lekarz", "medycyna"],
        "entertainment": ["movie", "music", "show", "actor", "film", "muzyka"],
        "sports": ["football", "basketball", "game", "player", "sport", "piłka"]
    }
    
    text_lower = text.lower()
    scores = {}
    
    for category in categories:
        if category in keywords:
            score = sum(1 for keyword in keywords[category] if keyword in text_lower)
            scores[category] = score / len(keywords[category])  # Normalizacja
    
    if scores:
        best_category = max(scores, key=scores.get)
        confidence = scores[best_category]
    else:
        best_category = "unknown"
        confidence = 0.0
    
    return {
        "category": best_category,
        "confidence": confidence,
        "all_scores": scores,
        "text_length": len(text.split())
    }

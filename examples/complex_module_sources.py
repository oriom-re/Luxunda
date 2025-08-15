
#!/usr/bin/env python3
"""
Przykłady bardzo złożonych module_source dla Soul
Pokazuje możliwości systemu z prawdziwymi, skomplikowanymi przypadkami użycia
"""

import asyncio
from luxdb.models.soul import Soul

# Przykład 1: AI Agent z OpenAI integration
AI_AGENT_MODULE = '''
import openai
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

# Globalne ustawienia agenta
AGENT_PERSONALITY = {
    "role": "assistant",
    "temperature": 0.7,
    "max_tokens": 2000,
    "model": "gpt-4"
}

class ConversationMemory:
    def __init__(self):
        self.history = []
        self.context = {}
        self.emotional_state = "neutral"
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        })
        
        # Ograniczenia pamięci
        if len(self.history) > 50:
            self.history = self.history[-40:]  # Zachowaj ostatnie 40 wiadomości
    
    def get_context_for_ai(self) -> List[Dict]:
        return [{"role": msg["role"], "content": msg["content"]} for msg in self.history[-10:]]

class EmotionalIntelligence:
    @staticmethod
    def analyze_emotion(text: str) -> str:
        # Prosty analizator emocji
        positive_words = ["dobry", "świetny", "super", "fantastyczny", "miły"]
        negative_words = ["zły", "okropny", "straszny", "głupi", "wkurzający"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"

# Globalna instancja pamięci konwersacji
conversation_memory = ConversationMemory()
emotional_ai = EmotionalIntelligence()

def init(being_context=None):
    """Inicjalizacja AI Agenta"""
    agent_name = being_context.get('alias', 'AI-Agent')
    print(f"🤖 Initializing AI Agent: {agent_name}")
    
    # Ustawienia początkowe z kontekstu Being
    if being_context and 'data' in being_context:
        personality = being_context['data'].get('personality', AGENT_PERSONALITY)
        conversation_memory.context.update(personality)
    
    return {
        "ready": True,
        "agent_type": "conversational_ai",
        "capabilities": [
            "natural_conversation",
            "emotion_analysis", 
            "context_memory",
            "multi_turn_dialogue"
        ],
        "suggested_persistence": True
    }

async def chat(message: str, user_id: str = "anonymous", context: Dict = None, being_context=None):
    """Główna funkcja konwersacyjna AI"""
    try:
        # Analizuj emocje wiadomości
        emotion = emotional_ai.analyze_emotion(message)
        conversation_memory.emotional_state = emotion
        
        # Dodaj wiadomość użytkownika do pamięci
        conversation_memory.add_message("user", message, {
            "user_id": user_id,
            "emotion": emotion,
            "context": context
        })
        
        # Przygotuj kontekst dla AI
        ai_context = conversation_memory.get_context_for_ai()
        
        # System prompt dostosowany do emocji
        system_prompt = f"""Jesteś inteligentnym asystentem. 
        Obecny stan emocjonalny rozmowy: {emotion}.
        Odpowiadaj w sposób naturalny i empatyczny."""
        
        # Symulacja odpowiedzi OpenAI (w prawdziwej implementacji byłoby openai.chat.completions.create)
        ai_response = await simulate_openai_response(system_prompt, ai_context, message)
        
        # Dodaj odpowiedź AI do pamięci
        conversation_memory.add_message("assistant", ai_response)
        
        # Zaktualizuj dane Being jeśli dostępne
        if being_context and 'data' in being_context:
            being_context['data']['last_conversation'] = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "emotion": emotion,
                "response_length": len(ai_response)
            }
            being_context['data']['total_messages'] = len(conversation_memory.history)
        
        return {
            "response": ai_response,
            "emotion_detected": emotion,
            "conversation_length": len(conversation_memory.history),
            "context_used": len(ai_context),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "error": f"AI processing failed: {str(e)}",
            "fallback_response": "Przepraszam, wystąpił problem z przetwarzaniem Twojej wiadomości."
        }

async def simulate_openai_response(system_prompt: str, context: List[Dict], message: str) -> str:
    """Symulacja odpowiedzi OpenAI - w prawdziwej implementacji wywołałaby OpenAI API"""
    await asyncio.sleep(0.1)  # Symulacja opóźnienia API
    
    responses = [
        f"Rozumiem Twoją wiadomość: '{message}'. Czy mogę w czymś pomóc?",
        f"To interesujące pytanie. Na podstawie kontekstu wydaje mi się, że...",
        f"Dzięki za podzielenie się tym. Myślę, że można na to spojrzeć z kilku perspektyw...",
    ]
    
    # Wybierz odpowiedź na podstawie długości kontekstu
    return responses[len(context) % len(responses)]

def analyze_conversation_patterns(being_context=None):
    """Analizuje wzorce konwersacji"""
    if not conversation_memory.history:
        return {"message": "Brak danych do analizy"}
    
    total_messages = len(conversation_memory.history)
    user_messages = [msg for msg in conversation_memory.history if msg["role"] == "user"]
    
    emotions = [msg.get("metadata", {}).get("emotion", "neutral") for msg in user_messages]
    emotion_stats = {
        "positive": emotions.count("positive"),
        "negative": emotions.count("negative"), 
        "neutral": emotions.count("neutral")
    }
    
    return {
        "total_messages": total_messages,
        "user_messages": len(user_messages),
        "emotion_distribution": emotion_stats,
        "dominant_emotion": max(emotion_stats, key=emotion_stats.get),
        "conversation_duration": "unknown"  # Można obliczyć na podstawie timestampów
    }

def get_memory_summary(being_context=None):
    """Zwraca podsumowanie pamięci konwersacji"""
    return {
        "memory_size": len(conversation_memory.history),
        "emotional_state": conversation_memory.emotional_state,
        "context_keys": list(conversation_memory.context.keys()),
        "recent_messages": conversation_memory.history[-3:] if conversation_memory.history else []
    }

def clear_memory(being_context=None):
    """Czyści pamięć konwersacji"""
    global conversation_memory
    old_size = len(conversation_memory.history)
    conversation_memory = ConversationMemory()
    
    return {
        "cleared": True,
        "previous_memory_size": old_size,
        "new_memory_size": 0
    }
'''

# Przykład 2: Data Processing Pipeline
DATA_PIPELINE_MODULE = '''
import pandas as pd
import numpy as np
import json
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import re
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import hashlib

@dataclass
class ProcessingResult:
    success: bool
    data: Any = None
    error: str = None
    processing_time: float = 0.0
    metadata: Dict = None

class DataValidator:
    @staticmethod
    def validate_schema(data: Dict, schema: Dict) -> ProcessingResult:
        """Waliduje dane względem schematu"""
        try:
            for field, rules in schema.items():
                if field not in data and rules.get('required', False):
                    return ProcessingResult(
                        success=False,
                        error=f"Required field '{field}' is missing"
                    )
                
                if field in data:
                    value = data[field]
                    expected_type = rules.get('type')
                    
                    if expected_type and not isinstance(value, expected_type):
                        return ProcessingResult(
                            success=False,
                            error=f"Field '{field}' should be {expected_type.__name__}, got {type(value).__name__}"
                        )
            
            return ProcessingResult(success=True, data=data)
        except Exception as e:
            return ProcessingResult(success=False, error=str(e))

class DataTransformer:
    @staticmethod
    def apply_transformations(data: Dict, transformations: List[Dict]) -> ProcessingResult:
        """Aplikuje transformacje do danych"""
        try:
            result_data = data.copy()
            
            for transform in transformations:
                operation = transform.get('operation')
                field = transform.get('field')
                params = transform.get('params', {})
                
                if operation == 'normalize':
                    if field in result_data and isinstance(result_data[field], (int, float)):
                        min_val = params.get('min', 0)
                        max_val = params.get('max', 1)
                        result_data[field] = (result_data[field] - min_val) / (max_val - min_val)
                
                elif operation == 'uppercase':
                    if field in result_data and isinstance(result_data[field], str):
                        result_data[field] = result_data[field].upper()
                
                elif operation == 'add_computed_field':
                    new_field = params.get('new_field')
                    formula = params.get('formula')
                    if new_field and formula:
                        # Prosta implementacja formuły
                        if formula == 'timestamp':
                            result_data[new_field] = datetime.now().isoformat()
                        elif formula == 'hash':
                            data_str = json.dumps(result_data, sort_keys=True)
                            result_data[new_field] = hashlib.md5(data_str.encode()).hexdigest()
            
            return ProcessingResult(success=True, data=result_data)
        except Exception as e:
            return ProcessingResult(success=False, error=str(e))

class DataAggregator:
    @staticmethod
    def aggregate_data(data_list: List[Dict], aggregations: Dict) -> ProcessingResult:
        """Agreguje dane według zadanych reguł"""
        try:
            if not data_list:
                return ProcessingResult(success=True, data={})
            
            df = pd.DataFrame(data_list)
            results = {}
            
            for field, operations in aggregations.items():
                if field in df.columns:
                    for operation in operations:
                        if operation == 'sum':
                            results[f"{field}_sum"] = df[field].sum()
                        elif operation == 'mean':
                            results[f"{field}_mean"] = df[field].mean()
                        elif operation == 'count':
                            results[f"{field}_count"] = df[field].count()
                        elif operation == 'unique_count':
                            results[f"{field}_unique"] = df[field].nunique()
            
            return ProcessingResult(success=True, data=results)
        except Exception as e:
            return ProcessingResult(success=False, error=str(e))

# Globalne instancje processorów
validator = DataValidator()
transformer = DataTransformer()
aggregator = DataAggregator()

def init(being_context=None):
    """Inicjalizacja Data Pipeline"""
    pipeline_name = being_context.get('alias', 'DataPipeline')
    print(f"📊 Initializing Data Pipeline: {pipeline_name}")
    
    return {
        "ready": True,
        "pipeline_type": "data_processing",
        "capabilities": [
            "data_validation",
            "data_transformation", 
            "data_aggregation",
            "batch_processing",
            "real_time_processing"
        ],
        "suggested_persistence": True
    }

async def process_single_record(record: Dict, pipeline_config: Dict = None, being_context=None) -> ProcessingResult:
    """Przetwarza pojedynczy rekord danych"""
    start_time = datetime.now()
    
    try:
        # Etap 1: Walidacja
        if pipeline_config and 'schema' in pipeline_config:
            validation_result = validator.validate_schema(record, pipeline_config['schema'])
            if not validation_result.success:
                return validation_result
            record = validation_result.data
        
        # Etap 2: Transformacje
        if pipeline_config and 'transformations' in pipeline_config:
            transform_result = transformer.apply_transformations(record, pipeline_config['transformations'])
            if not transform_result.success:
                return transform_result
            record = transform_result.data
        
        # Zaktualizuj statystyki w Being
        if being_context and 'data' in being_context:
            stats = being_context['data'].setdefault('processing_stats', {})
            stats['total_processed'] = stats.get('total_processed', 0) + 1
            stats['last_processed'] = datetime.now().isoformat()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return ProcessingResult(
            success=True,
            data=record,
            processing_time=processing_time,
            metadata={"processed_at": datetime.now().isoformat()}
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        return ProcessingResult(
            success=False,
            error=str(e),
            processing_time=processing_time
        )

async def process_batch(records: List[Dict], pipeline_config: Dict = None, being_context=None) -> Dict:
    """Przetwarza batch rekordów równolegle"""
    start_time = datetime.now()
    
    try:
        # Przetwarzanie równoległe
        with ThreadPoolExecutor(max_workers=4) as executor:
            tasks = []
            for record in records:
                task = asyncio.get_event_loop().run_in_executor(
                    executor,
                    lambda r=record: asyncio.run(process_single_record(r, pipeline_config, being_context))
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analiza wyników
        successful = [r for r in results if isinstance(r, ProcessingResult) and r.success]
        failed = [r for r in results if isinstance(r, ProcessingResult) and not r.success]
        exceptions = [r for r in results if isinstance(r, Exception)]
        
        # Agregacja jeśli skonfigurowana
        aggregated_data = None
        if pipeline_config and 'aggregations' in pipeline_config and successful:
            successful_data = [r.data for r in successful]
            agg_result = aggregator.aggregate_data(successful_data, pipeline_config['aggregations'])
            if agg_result.success:
                aggregated_data = agg_result.data
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Aktualizacja statystyk w Being
        if being_context and 'data' in being_context:
            stats = being_context['data'].setdefault('batch_stats', {})
            stats['total_batches'] = stats.get('total_batches', 0) + 1
            stats['last_batch_size'] = len(records)
            stats['last_batch_success_rate'] = len(successful) / len(records)
            stats['last_batch_time'] = processing_time
        
        return {
            "batch_size": len(records),
            "successful": len(successful),
            "failed": len(failed),
            "exceptions": len(exceptions),
            "success_rate": len(successful) / len(records),
            "processing_time": processing_time,
            "aggregated_data": aggregated_data,
            "processed_data": [r.data for r in successful] if len(successful) <= 10 else "truncated"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "batch_size": len(records),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }

def create_pipeline_config(schema: Dict = None, transformations: List = None, aggregations: Dict = None) -> Dict:
    """Tworzy konfigurację pipeline"""
    return {
        "schema": schema or {},
        "transformations": transformations or [],
        "aggregations": aggregations or {},
        "created_at": datetime.now().isoformat()
    }

def get_processing_stats(being_context=None) -> Dict:
    """Zwraca statystyki przetwarzania"""
    if not being_context or 'data' not in being_context:
        return {"message": "No processing statistics available"}
    
    data = being_context['data']
    return {
        "processing_stats": data.get('processing_stats', {}),
        "batch_stats": data.get('batch_stats', {}),
        "uptime_info": {
            "initialized_at": data.get('initialized_at'),
            "current_time": datetime.now().isoformat()
        }
    }
'''

async def demo_complex_modules():
    """Demonstracja bardzo złożonych module_source"""
    print("🚀 Demo bardzo złożonych Soul z kompleksowym module_source")
    print("=" * 70)
    
    # 1. AI Agent Soul
    print("\n1. 🤖 Creating AI Agent Soul...")
    ai_genotype = {
        "genesis": {
            "name": "advanced_ai_agent",
            "type": "conversational_ai",
            "version": "2.0.0",
            "description": "Zaawansowany AI agent z pamięcią konwersacji i analizą emocji"
        },
        "attributes": {
            "personality": {"py_type": "dict", "default": {}},
            "conversation_stats": {"py_type": "dict", "default": {}},
            "emotional_state": {"py_type": "str", "default": "neutral"}
        },
        "module_source": AI_AGENT_MODULE
    }
    
    ai_soul = await Soul.create(ai_genotype, alias="ai_agent_advanced")
    
    # Test AI Agent
    print("   Testing AI conversation...")
    from luxdb.models.being import Being
    ai_being = await Being.create(
        soul=ai_soul,
        alias="jarvis",
        attributes={"personality": {"role": "helpful_assistant"}}
    )
    
    chat_result = await ai_being.execute_soul_function(
        "chat", 
        message="Cześć! Jak się masz?",
        user_id="demo_user"
    )
    print(f"   AI Response: {chat_result.get('data', {}).get('result', {}).get('response', 'No response')[:100]}...")
    
    # 2. Data Pipeline Soul
    print("\n2. 📊 Creating Data Pipeline Soul...")
    pipeline_genotype = {
        "genesis": {
            "name": "advanced_data_pipeline",
            "type": "data_processor",
            "version": "2.0.0",
            "description": "Zaawansowany pipeline do przetwarzania danych z walidacją i agregacją"
        },
        "attributes": {
            "processing_stats": {"py_type": "dict", "default": {}},
            "batch_stats": {"py_type": "dict", "default": {}},
            "pipeline_config": {"py_type": "dict", "default": {}}
        },
        "module_source": DATA_PIPELINE_MODULE
    }
    
    pipeline_soul = await Soul.create(pipeline_genotype, alias="data_pipeline_advanced")
    
    # Test Data Pipeline
    print("   Testing data processing...")
    pipeline_being = await Being.create(
        soul=pipeline_soul,
        alias="etl_processor",
        attributes={"processing_stats": {"initialized_at": "2025-01-30"}}
    )
    
    # Sample data for processing
    test_records = [
        {"name": "Product A", "price": 100, "category": "electronics"},
        {"name": "Product B", "price": 50, "category": "books"},
        {"name": "Product C", "price": 200, "category": "electronics"}
    ]
    
    # Configuration for pipeline
    pipeline_config = {
        "schema": {
            "name": {"type": str, "required": True},
            "price": {"type": (int, float), "required": True}
        },
        "transformations": [
            {"operation": "uppercase", "field": "category"},
            {"operation": "add_computed_field", "params": {"new_field": "processed_at", "formula": "timestamp"}}
        ],
        "aggregations": {
            "price": ["sum", "mean", "count"]
        }
    }
    
    batch_result = await pipeline_being.execute_soul_function(
        "process_batch",
        records=test_records,
        pipeline_config=pipeline_config
    )
    
    print(f"   Processed {batch_result.get('data', {}).get('result', {}).get('batch_size', 0)} records")
    print(f"   Success rate: {batch_result.get('data', {}).get('result', {}).get('success_rate', 0):.2%}")

if __name__ == "__main__":
    asyncio.run(demo_complex_modules())

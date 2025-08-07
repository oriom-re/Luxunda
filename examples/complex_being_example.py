
"""
Przykład tworzenia złożonego bytu z genami i zależnościami w LuxDB
"""

import asyncio
from luxdb.simple_api import SimpleLuxDB
from database.models.base import Soul, Being

async def create_complex_ai_agent():
    """
    Tworzy złożonego agenta AI z wieloma genami i funkcjami
    """
    
    # Inicjalizuj LuxDB
    luxdb = SimpleLuxDB()
    
    # Definiuj złożony genotyp z genami
    ai_agent_genotype = {
        "genesis": {
            "name": "advanced_ai_agent",
            "version": "2.0",
            "description": "Zaawansowany agent AI z wieloma zdolnościami",
            "dependencies": [
                "memory_system",
                "learning_module", 
                "communication_hub",
                "decision_engine"
            ]
        },
        "attributes": {
            # Podstawowe atrybuty
            "name": {"py_type": "str"},
            "agent_type": {"py_type": "str"},
            "status": {"py_type": "str", "default": "active"},
            
            # Konfiguracja AI
            "model_config": {"py_type": "dict"},
            "learning_rate": {"py_type": "float", "default": 0.01},
            "confidence_threshold": {"py_type": "float", "default": 0.8},
            
            # Pamięć i kontekst
            "memory_bank": {"py_type": "dict"},
            "context_window": {"py_type": "int", "default": 4096},
            "conversation_history": {"py_type": "List[dict]"},
            
            # Embeddings dla semantycznego wyszukiwania
            "knowledge_embeddings": {"py_type": "List[float]", "vector_size": 1536},
            "skill_embeddings": {"py_type": "List[float]", "vector_size": 1536},
            
            # Zdolności specjalistyczne
            "capabilities": {"py_type": "List[str]"},
            "specializations": {"py_type": "dict"},
            "performance_metrics": {"py_type": "dict"}
        },
        "genes": {
            # Geny komunikacji
            "communicate": "genes.communication.advanced_chat",
            "translate": "genes.communication.language_translator",
            "summarize": "genes.communication.text_summarizer",
            
            # Geny analizy
            "analyze_sentiment": "genes.analysis.sentiment_analyzer",
            "extract_entities": "genes.analysis.entity_extractor",
            "classify_text": "genes.analysis.text_classifier",
            
            # Geny uczenia się
            "learn_from_feedback": "genes.learning.feedback_processor",
            "update_knowledge": "genes.learning.knowledge_updater",
            "adapt_behavior": "genes.learning.behavior_adapter",
            
            # Geny decyzyjne
            "make_decision": "genes.decision.decision_maker",
            "prioritize_tasks": "genes.decision.task_prioritizer",
            "evaluate_options": "genes.decision.option_evaluator",
            
            # Geny pamięci
            "store_memory": "genes.memory.memory_storage",
            "retrieve_memory": "genes.memory.memory_retrieval",
            "forget_obsolete": "genes.memory.memory_cleanup"
        }
    }
    
    # Utwórz soul z genotypem
    soul = await Soul.create(ai_agent_genotype, "advanced_ai_agent")
    
    # Dane inicjalne dla bytu
    agent_data = {
        "name": "ARIA", # Advanced Reasoning Intelligence Agent
        "agent_type": "conversational_ai",
        "model_config": {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 0.9
        },
        "capabilities": [
            "natural_language_processing",
            "sentiment_analysis",
            "knowledge_extraction",
            "decision_making",
            "learning_adaptation"
        ],
        "specializations": {
            "communication": 0.95,
            "analysis": 0.88,
            "learning": 0.82,
            "problem_solving": 0.91
        },
        "memory_bank": {},
        "conversation_history": [],
        "performance_metrics": {
            "accuracy": 0.92,
            "response_time": 1.2,
            "user_satisfaction": 0.89
        }
    }
    
    # Utwórz being z danymi
    aria_agent = await Being.create(soul, agent_data)
    
    print(f"✅ Utworzono zaawansowanego agenta AI: {aria_agent.ulid}")
    print(f"📊 Nazwa: {agent_data['name']}")
    print(f"🎯 Typ: {agent_data['agent_type']}")
    print(f"🧬 Geny: {len(ai_agent_genotype['genes'])}")
    print(f"⚙️ Zdolności: {len(agent_data['capabilities'])}")
    
    return aria_agent

async def create_complex_data_processor():
    """
    Tworzy złożony procesor danych z wieloma modułami
    """
    
    luxdb = SimpleLuxDB()
    
    # Genotyp procesora danych
    data_processor_genotype = {
        "genesis": {
            "name": "advanced_data_processor",
            "version": "1.5",
            "description": "Zaawansowany system przetwarzania danych",
            "dependencies": [
                "data_ingestion",
                "transformation_engine",
                "validation_suite",
                "export_manager"
            ]
        },
        "attributes": {
            "processor_name": {"py_type": "str"},
            "processing_mode": {"py_type": "str", "default": "batch"},
            "data_sources": {"py_type": "List[str]"},
            "output_formats": {"py_type": "List[str]"},
            
            # Konfiguracja przetwarzania
            "batch_size": {"py_type": "int", "default": 1000},
            "parallel_workers": {"py_type": "int", "default": 4},
            "memory_limit": {"py_type": "int", "default": 2048},
            
            # Metryki i monitoring
            "processed_records": {"py_type": "int", "default": 0},
            "error_count": {"py_type": "int", "default": 0},
            "processing_stats": {"py_type": "dict"},
            
            # Reguły i filtry
            "transformation_rules": {"py_type": "dict"},
            "validation_rules": {"py_type": "List[dict]"},
            "quality_thresholds": {"py_type": "dict"}
        },
        "genes": {
            # Geny pobierania danych
            "fetch_from_api": "genes.ingestion.api_fetcher",
            "read_from_file": "genes.ingestion.file_reader",
            "stream_from_db": "genes.ingestion.db_streamer",
            
            # Geny transformacji
            "clean_data": "genes.transform.data_cleaner",
            "normalize_values": "genes.transform.normalizer",
            "enrich_data": "genes.transform.data_enricher",
            "aggregate_data": "genes.transform.aggregator",
            
            # Geny walidacji
            "validate_schema": "genes.validation.schema_validator",
            "check_quality": "genes.validation.quality_checker",
            "detect_anomalies": "genes.validation.anomaly_detector",
            
            # Geny eksportu
            "export_to_json": "genes.export.json_exporter",
            "export_to_csv": "genes.export.csv_exporter",
            "save_to_db": "genes.export.db_saver",
            
            # Geny monitoringu
            "track_performance": "genes.monitoring.performance_tracker",
            "generate_reports": "genes.monitoring.report_generator",
            "alert_on_errors": "genes.monitoring.error_alerter"
        }
    }
    
    # Utwórz soul
    processor_soul = await Soul.create(data_processor_genotype, "advanced_data_processor")
    
    # Dane procesora
    processor_data = {
        "processor_name": "DataFlow Pro",
        "processing_mode": "real_time",
        "data_sources": [
            "api://sales.company.com/v1/transactions",
            "file://data/customer_data.json",
            "db://postgresql://analytics_db"
        ],
        "output_formats": ["json", "parquet", "csv"],
        "batch_size": 5000,
        "parallel_workers": 8,
        "transformation_rules": {
            "currency_conversion": {"from": "PLN", "to": "USD"},
            "date_formatting": {"format": "ISO8601"},
            "field_mapping": {
                "customer_id": "cust_id",
                "purchase_date": "date",
                "amount": "value"
            }
        },
        "validation_rules": [
            {"field": "amount", "type": "numeric", "min": 0},
            {"field": "email", "type": "email", "required": True},
            {"field": "date", "type": "datetime", "format": "ISO"}
        ],
        "quality_thresholds": {
            "completeness": 0.95,
            "accuracy": 0.98,
            "consistency": 0.92
        }
    }
    
    # Utwórz being
    processor = await Being.create(processor_soul, processor_data)
    
    print(f"✅ Utworzono procesor danych: {processor.ulid}")
    print(f"⚙️ Nazwa: {processor_data['processor_name']}")
    print(f"🔄 Tryb: {processor_data['processing_mode']}")
    print(f"📊 Źródła danych: {len(processor_data['data_sources'])}")
    print(f"🧬 Geny przetwarzania: {len(data_processor_genotype['genes'])}")
    
    return processor

async def create_interconnected_system():
    """
    Tworzy system połączonych bytów z zależnościami
    """
    
    luxdb = SimpleLuxDB()
    
    # Utwórz różne komponenty systemu
    ai_agent = await create_complex_ai_agent()
    data_processor = await create_complex_data_processor()
    
    # Utwórz koordynatora systemu
    coordinator_genotype = {
        "genesis": {
            "name": "system_coordinator", 
            "version": "1.0",
            "description": "Koordynator zarządzający całym systemem"
        },
        "attributes": {
            "coordinator_name": {"py_type": "str"},
            "managed_components": {"py_type": "List[str]"},
            "system_status": {"py_type": "str", "default": "running"},
            "orchestration_rules": {"py_type": "dict"}
        },
        "genes": {
            "coordinate_tasks": "genes.coordination.task_coordinator",
            "monitor_health": "genes.coordination.health_monitor",
            "balance_load": "genes.coordination.load_balancer",
            "handle_failures": "genes.coordination.failure_handler"
        }
    }
    
    coordinator_soul = await Soul.create(coordinator_genotype, "system_coordinator")
    coordinator = await Being.create(coordinator_soul, {
        "coordinator_name": "MasterControl",
        "managed_components": [ai_agent.ulid, data_processor.ulid],
        "orchestration_rules": {
            "priority_queue": True,
            "failover_enabled": True,
            "auto_scaling": True
        }
    })
    
    # Połącz komponenty relacjami
    await luxdb.connect_entities(coordinator.ulid, ai_agent.ulid, "manages")
    await luxdb.connect_entities(coordinator.ulid, data_processor.ulid, "manages") 
    await luxdb.connect_entities(ai_agent.ulid, data_processor.ulid, "uses_data_from")
    
    print(f"🔗 Utworzono system połączonych bytów:")
    print(f"   🧠 AI Agent: {ai_agent.ulid}")
    print(f"   ⚙️ Data Processor: {data_processor.ulid}")
    print(f"   🎛️ Coordinator: {coordinator.ulid}")
    
    return {
        "coordinator": coordinator,
        "ai_agent": ai_agent, 
        "data_processor": data_processor
    }

async def demonstrate_gene_execution():
    """
    Demonstruje wykonywanie genów w złożonym bycie
    """
    
    print("\n🧬 Demonstracja wykonywania genów...")
    
    # Utwórz system
    system = await create_interconnected_system()
    ai_agent = system["ai_agent"]
    
    # Symuluj wykonanie różnych genów
    print(f"\n🎯 Symulacja wykonania genów dla agenta {ai_agent.ulid[:8]}...")
    
    # Przykład wykonania genu komunikacji
    try:
        # W prawdziwej implementacji:
        # result = await ai_agent.execute("communicate", message="Hello, how can I help?")
        print("✅ Gen 'communicate' - Przetworzono wiadomość użytkownika")
    except Exception as e:
        print(f"⚠️ Gen 'communicate' - {e}")
    
    # Przykład wykonania genu analizy
    try:
        # result = await ai_agent.execute("analyze_sentiment", text="This is amazing!")
        print("✅ Gen 'analyze_sentiment' - Przeanalizowano sentiment")
    except Exception as e:
        print(f"⚠️ Gen 'analyze_sentiment' - {e}")
    
    # Przykład wykonania genu uczenia
    try:
        # result = await ai_agent.execute("learn_from_feedback", feedback={"rating": 5, "comment": "Great!"})
        print("✅ Gen 'learn_from_feedback' - Przetworzono feedback")
    except Exception as e:
        print(f"⚠️ Gen 'learn_from_feedback' - {e}")

async def main():
    """
    Główna funkcja demonstracyjna
    """
    
    print("🚀 Tworzenie złożonych bytów z genami i zależnościami w LuxDB")
    print("=" * 60)
    
    # Utwórz pojedyncze złożone byty
    await create_complex_ai_agent()
    print()
    await create_complex_data_processor()
    print()
    
    # Utwórz połączony system
    await create_interconnected_system()
    print()
    
    # Zademonstruj wykonywanie genów
    await demonstrate_gene_execution()
    
    print("\n🎉 Demo zakończone!")

if __name__ == "__main__":
    asyncio.run(main())

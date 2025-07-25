# app_v2/hybrid_demo.py
"""
Demonstracja działania HybridAISystem: uruchamia podstawowy przepływ AI Brain + Gene Registry
"""
import asyncio

from app_v2.ai.hybrid_ai_system import HybridAISystem
from app_v2.database.db_manager import init_database
from app_v2.core.module_registry import ModuleRegistry

async def run_demo():
    # Inicjalizacja bazy i rejestracja genów
    await init_database()
    count = await ModuleRegistry.register_all_modules_from_directory("app_v2/gen_files")
    print(f"Zarejestrowano modułów/genów: {count}")

    hybrid = HybridAISystem()
    print("Status systemu:", hybrid.get_system_status())

    # Lista przykładowych zapytań
    demo_queries = [
        "What genes are available?",
        "Execute basic_log with message Hello Demo",
        "Store memory key1 value1",
        "Retrieve memory for key1"
    ]

    for query in demo_queries:
        print(f"\n👤 Zapytanie: {query}")
        result = await hybrid.process_request(query, use_openai=False)
        final = result["final_result"]
        print("Metoda:", result["method_used"])
        print("Wynik finalny:", final)

if __name__ == "__main__":
    asyncio.run(run_demo())

# app_v2/test_hybrid_system.py
"""
Test hybrydowego systemu AI (HybridAISystem) w architekturze LuxOS app_v2
"""

import pytest

from app_v2.ai.hybrid_ai_system import HybridAISystem
from app_v2.database.not_in_use.sqlite_db import init_database
from app_v2.core.module_registry import ModuleRegistry


@pytest.mark.asyncio
async def test_hybrid_system_basic():
    # 1. Inicjalizacja bazy i rejestracja modułów/genów
    await init_database()
    registered = await ModuleRegistry.register_all_modules_from_directory("app_v2/gen_files")
    assert registered > 0, "Nie zarejestrowano żadnych modułów/genów"

    # 2. Utworzenie instancji hybrydowego systemu AI
    hybrid = HybridAISystem()
    status = hybrid.get_system_status()
    assert isinstance(status["ai_brain_functions"], int)
    assert status["ai_brain_functions"] > 0, "Brak dostępnych funkcji AI Brain"
    assert status["openai_enabled"] is False, "OpenAI powinno być wyłączone w teście podstawowym"

    # 3. Przetwarzanie prostego zapytania
    result = await hybrid.process_request("Pokaż wszystkie geny", use_openai=False)
    assert result["method_used"] in ["ai_brain_only", "ai_brain_fallback"]
    final = result["final_result"]
    assert final is not None, "Brak finalnego wyniku przetwarzania"

    # 4. Sprawdź strukturę odpowiedzi
    assert "intent_analysis" in result["ai_brain_analysis"], "Brak analizy intencji w AI Brain"
    # Metoda hybrydowa powinna zawierać klucz openai_analysis nawet jeśli None
    assert "openai_analysis" in result

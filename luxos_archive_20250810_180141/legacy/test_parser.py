
#!/usr/bin/env python3
"""
Testy dla parsera narzędzi
"""

from tool_parser import ToolParser, analyze_message_for_tools

def test_parser():
    """Testuje parser narzędzi z przykładowymi wiadomościami"""
    
    test_messages = [
        # Test odczytu plików
        "Odczytaj plik main.py",
        "Pokaż kod z lux_tools.py", 
        "Sprawdź zawartość static/chat-component.js",
        
        # Test zapisu plików
        "Utwórz nowy plik test.py",
        "Zapisz kod do pliku utils.py",
        
        # Test analizy kodu
        "Analizuj kod w main.py",
        "Sprawdź błędy w kodzie",
        "Składnia pliku main.py",
        
        # Test wyszukiwania
        "Znajdź funkcję create_being",
        "Szukaj 'LuxTools' w plikach",
        "Gdzie jest definicja klasy BaseBeing",
        
        # Test listowania
        "Jakie pliki są w katalogu static",
        "Lista plików",
        "Pokaż wszystkie pliki Python",
        
        # Test GPT
        "Co myślisz o tym kodzie?",
        "Jak mogę poprawić wydajność?",
        "Wyjaśnij mi jak działa asyncio",
        
        # Test testów
        "Uruchom testy",
        "Testuj main.py",
        
        # Wiadomości ogólne
        "Cześć",
        "Pomóż mi",
        "Jak się masz?"
    ]
    
    parser = ToolParser()
    
    print("=== TESTY PARSERA NARZĘDZI ===\n")
    
    for i, message in enumerate(test_messages, 1):
        print(f"{i:2d}. Wiadomość: '{message}'")
        
        detections = parser.parse_message(message)
        
        if detections:
            for j, detection in enumerate(detections):
                print(f"    {j+1}. {detection.tool_name} (pewność: {detection.confidence:.2f})")
                print(f"       Powód: {detection.reason}")
                if detection.parameters:
                    print(f"       Parametry: {detection.parameters}")
        else:
            print("    Brak wykrytych narzędzi")
        
        print()

def test_integration():
    """Testuje integrację z funkcją analyze_message_for_tools"""
    print("=== TEST INTEGRACJI ===\n")
    
    test_cases = [
        "Odczytaj main.py i sprawdź błędy",
        "Znajdź wszystkie funkcje w projekcie",
        "Co myślisz o strukturze kodu?",
        "Lista plików w katalogu static"
    ]
    
    for message in test_cases:
        print(f"Wiadomość: '{message}'")
        result = analyze_message_for_tools(message)
        
        print(f"Wykryto narzędzi: {result['total_detected']}")
        print(f"Najwyższa pewność: {result['highest_confidence']:.2f}")
        
        for tool in result['suggested_tools']:
            print(f"  - {tool['tool']}: {tool['reason']} (pewność: {tool.get('confidence', 'N/A')})")
        
        print()

if __name__ == "__main__":
    test_parser()
    test_integration()

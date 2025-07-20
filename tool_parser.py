
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ToolDetection:
    """Reprezentuje wykryte narzędzie z parametrami"""
    tool_name: str
    confidence: float
    parameters: Dict[str, Any]
    reason: str
    keywords_matched: List[str]

class ToolParser:
    """Parser do wykrywania narzędzi na podstawie tekstu wiadomości"""
    
    def __init__(self):
        # Wzorce dla różnych narzędzi
        self.tool_patterns = {
            'read_file': {
                'keywords': [
                    'odczytaj', 'przeczytaj', 'pokaż', 'wyświetl', 'otwórz', 'sprawdź',
                    'zobacz', 'plik', 'kod', 'zawartość', 'read', 'show', 'open'
                ],
                'file_patterns': [
                    r'plik\s+([a-zA-Z0-9_\-/.]+\.py)',
                    r'([a-zA-Z0-9_\-/.]+\.py)',
                    r'([a-zA-Z0-9_\-/.]+\.js)',
                    r'([a-zA-Z0-9_\-/.]+\.html)',
                    r'([a-zA-Z0-9_\-/.]+\.css)',
                    r'main\.py',
                    r'lux_tools\.py',
                    r'static/.*\.(js|html|css)'
                ],
                'confidence_boost': {
                    'plik': 0.8,
                    'kod': 0.7,
                    'main.py': 0.9,
                    'odczytaj': 0.8
                }
            },
            
            'write_file': {
                'keywords': [
                    'zapisz', 'utwórz', 'stwórz', 'napisz', 'dodaj plik', 'nowy plik',
                    'save', 'create', 'write', 'make file'
                ],
                'patterns': [
                    r'utwórz\s+plik\s+([a-zA-Z0-9_\-/.]+)',
                    r'zapisz\s+([a-zA-Z0-9_\-/.]+)',
                    r'nowy\s+plik\s+([a-zA-Z0-9_\-/.]+)'
                ],
                'confidence_boost': {
                    'utwórz': 0.9,
                    'zapisz': 0.9,
                    'nowy plik': 0.8
                }
            },
            
            'list_files': {
                'keywords': [
                    'listuj', 'pokaż pliki', 'jakie pliki', 'lista plików', 'katalog',
                    'list', 'files', 'directory', 'ls', 'dir'
                ],
                'patterns': [
                    r'lista\s+plików',
                    r'jakie\s+pliki',
                    r'pliki\s+w\s+([a-zA-Z0-9_\-/]+)',
                    r'katalog\s+([a-zA-Z0-9_\-/]+)'
                ],
                'confidence_boost': {
                    'lista plików': 0.9,
                    'jakie pliki': 0.8,
                    'katalog': 0.7
                }
            },
            
            'analyze_code': {
                'keywords': [
                    'analizuj', 'sprawdź kod', 'analiza', 'błędy', 'poprawność',
                    'metryki', 'analyze', 'check', 'validate', 'review'
                ],
                'patterns': [
                    r'analizuj\s+([a-zA-Z0-9_\-/.]+\.py)',
                    r'sprawdź\s+kod\s+([a-zA-Z0-9_\-/.]+)',
                    r'błędy\s+w\s+([a-zA-Z0-9_\-/.]+)'
                ],
                'confidence_boost': {
                    'analizuj': 0.9,
                    'sprawdź kod': 0.8,
                    'błędy': 0.7
                }
            },
            
            'run_tests': {
                'keywords': [
                    'testy', 'uruchom testy', 'test', 'testuj', 'pytest',
                    'run tests', 'testing', 'unit test'
                ],
                'patterns': [
                    r'uruchom\s+testy',
                    r'testy\s+([a-zA-Z0-9_\-/.]+)',
                    r'testuj\s+([a-zA-Z0-9_\-/.]+)'
                ],
                'confidence_boost': {
                    'uruchom testy': 0.9,
                    'testy': 0.8,
                    'pytest': 0.9
                }
            },
            
            'search_in_files': {
                'keywords': [
                    'znajdź', 'szukaj', 'wyszukaj', 'grep', 'search', 'find',
                    'gdzie jest', 'lokalizuj'
                ],
                'patterns': [
                    r'znajdź\s+"([^"]+)"',
                    r'szukaj\s+"([^"]+)"',
                    r'gdzie\s+jest\s+"([^"]+)"',
                    r'znajdź\s+(\w+)'
                ],
                'confidence_boost': {
                    'znajdź': 0.8,
                    'szukaj': 0.8,
                    'gdzie jest': 0.7
                }
            },
            
            'check_syntax': {
                'keywords': [
                    'składnia', 'syntax', 'poprawność składni', 'błąd składni',
                    'syntax error', 'validate syntax'
                ],
                'patterns': [
                    r'składnia\s+([a-zA-Z0-9_\-/.]+)',
                    r'błąd\s+składni\s+([a-zA-Z0-9_\-/.]+)'
                ],
                'confidence_boost': {
                    'składnia': 0.9,
                    'błąd składni': 0.8
                }
            },
            
            'ask_gpt': {
                'keywords': [
                    'gpt', 'zapytaj', 'co myślisz', 'pomóż', 'wyjaśnij',
                    'jak', 'dlaczego', 'czy możesz', 'porada'
                ],
                'patterns': [
                    r'zapytaj\s+gpt',
                    r'co\s+myślisz\s+o',
                    r'jak\s+(.+)',
                    r'dlaczego\s+(.+)',
                    r'czy\s+możesz\s+(.+)'
                ],
                'confidence_boost': {
                    'gpt': 0.9,
                    'zapytaj': 0.7,
                    'co myślisz': 0.6,
                    'jak': 0.5,
                    'dlaczego': 0.5
                }
            }
        }
        
        # Wzorce do wykrywania ścieżek plików
        self.file_path_patterns = [
            r'([a-zA-Z0-9_\-/.]+\.py)',
            r'([a-zA-Z0-9_\-/.]+\.js)',
            r'([a-zA-Z0-9_\-/.]+\.html)',
            r'([a-zA-Z0-9_\-/.]+\.css)',
            r'([a-zA-Z0-9_\-/.]+\.json)',
            r'static/([a-zA-Z0-9_\-/.]+)',
            r'main\.py',
            r'lux_tools\.py'
        ]
    
    def parse_message(self, message: str) -> List[ToolDetection]:
        """Parsuje wiadomość i zwraca listę wykrytych narzędzi"""
        message_lower = message.lower()
        detections = []
        
        for tool_name, tool_config in self.tool_patterns.items():
            detection = self._analyze_tool(tool_name, tool_config, message, message_lower)
            if detection and detection.confidence > 0.3:  # Próg wykrycia
                detections.append(detection)
        
        # Sortuj według pewności
        detections.sort(key=lambda x: x.confidence, reverse=True)
        
        # Usuń duplikaty podobnych narzędzi
        detections = self._remove_duplicates(detections)
        
        return detections
    
    def _analyze_tool(self, tool_name: str, config: Dict, original_message: str, message_lower: str) -> Optional[ToolDetection]:
        """Analizuje czy wiadomość pasuje do konkretnego narzędzia"""
        matched_keywords = []
        confidence = 0.0
        parameters = {}
        
        # Sprawdź słowa kluczowe
        for keyword in config['keywords']:
            if keyword.lower() in message_lower:
                matched_keywords.append(keyword)
                # Bonus za dokładność dopasowania
                boost = config.get('confidence_boost', {}).get(keyword, 0.1)
                confidence += boost
        
        if not matched_keywords:
            return None
        
        # Sprawdź wzorce specyficzne dla narzędzia
        if 'patterns' in config:
            for pattern in config['patterns']:
                match = re.search(pattern, message_lower)
                if match:
                    confidence += 0.3
                    # Wyciągnij parametry z wzorca
                    if match.groups():
                        if tool_name in ['read_file', 'analyze_code', 'check_syntax']:
                            parameters['file_path'] = match.group(1)
                        elif tool_name == 'write_file':
                            parameters['file_path'] = match.group(1)
                        elif tool_name == 'search_in_files':
                            parameters['search_term'] = match.group(1)
                        elif tool_name == 'list_files':
                            parameters['directory'] = match.group(1)
        
        # Wykryj ścieżki plików dla narzędzi plikowych
        if tool_name in ['read_file', 'analyze_code', 'check_syntax'] and 'file_path' not in parameters:
            file_path = self._extract_file_path(original_message)
            if file_path:
                parameters['file_path'] = file_path
                confidence += 0.2
        
        # Specjalne przypadki dla ask_gpt
        if tool_name == 'ask_gpt':
            parameters['prompt'] = f"Użytkownik napisał: '{original_message}'. Jak mogę pomóc?"
            # GPT jako fallback ma niższą pewność
            if len(matched_keywords) == 1 and matched_keywords[0] in ['jak', 'dlaczego']:
                confidence = max(confidence, 0.4)
        
        # Dodatkowe parametry dla search_in_files
        if tool_name == 'search_in_files' and 'search_term' not in parameters:
            # Spróbuj wyciągnąć termin wyszukiwania z kontekstu
            search_term = self._extract_search_term(original_message)
            if search_term:
                parameters['search_term'] = search_term
                confidence += 0.2
        
        # Normalizuj pewność
        confidence = min(confidence, 1.0)
        
        # Powód wykrycia
        reason = f"Wykryto słowa kluczowe: {', '.join(matched_keywords)}"
        if parameters:
            reason += f" z parametrami: {list(parameters.keys())}"
        
        return ToolDetection(
            tool_name=tool_name,
            confidence=confidence,
            parameters=parameters,
            reason=reason,
            keywords_matched=matched_keywords
        )
    
    def _extract_file_path(self, message: str) -> Optional[str]:
        """Wyciąga ścieżkę pliku z wiadomości"""
        for pattern in self.file_path_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        
        # Fallback dla popularnych plików
        message_lower = message.lower()
        if 'main' in message_lower:
            return 'main.py'
        elif 'lux_tools' in message_lower or 'narzędzia' in message_lower:
            return 'lux_tools.py'
        elif 'chat' in message_lower:
            return 'static/chat-component.js'
        
        return None
    
    def _extract_search_term(self, message: str) -> Optional[str]:
        """Wyciąga termin wyszukiwania z wiadomości"""
        # Wzorce z cudzysłowami
        quoted_patterns = [
            r'"([^"]+)"',
            r"'([^']+)'",
            r'„([^"]+)"'
        ]
        
        for pattern in quoted_patterns:
            match = re.search(pattern, message)
            if match:
                return match.group(1)
        
        # Wzorce bez cudzysłowów
        search_patterns = [
            r'znajdź\s+(\w+)',
            r'szukaj\s+(\w+)',
            r'gdzie\s+jest\s+(\w+)'
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1)
        
        return None
    
    def _remove_duplicates(self, detections: List[ToolDetection]) -> List[ToolDetection]:
        """Usuwa duplikaty podobnych wykryć"""
        if len(detections) <= 1:
            return detections
        
        # Grupuj podobne narzędzia
        groups = {
            'file_operations': ['read_file', 'write_file', 'analyze_code', 'check_syntax'],
            'search_operations': ['search_in_files', 'list_files'],
            'execution': ['run_tests'],
            'ai_assistance': ['ask_gpt']
        }
        
        filtered = []
        used_groups = set()
        
        for detection in detections:
            # Znajdź grupę narzędzia
            tool_group = None
            for group, tools in groups.items():
                if detection.tool_name in tools:
                    tool_group = group
                    break
            
            if tool_group and tool_group in used_groups:
                # Już mamy narzędzie z tej grupy, pomiń jeśli pewność jest znacznie niższa
                if detection.confidence < 0.7:
                    continue
            
            filtered.append(detection)
            if tool_group:
                used_groups.add(tool_group)
        
        return filtered
    
    def get_tool_suggestions(self, message: str) -> Dict[str, Any]:
        """Zwraca sugestie narzędzi w formacie kompatybilnym z istniejącym kodem"""
        detections = self.parse_message(message)
        
        suggestions = []
        for detection in detections:
            suggestion = {
                'tool': detection.tool_name,
                'reason': detection.reason,
                'confidence': detection.confidence
            }
            
            if detection.parameters:
                suggestion['parameters'] = detection.parameters
            
            suggestions.append(suggestion)
        
        return {
            'suggested_tools': suggestions,
            'total_detected': len(suggestions),
            'highest_confidence': suggestions[0].confidence if suggestions else 0.0
        }

# Funkcje pomocnicze dla kompatybilności
def create_tool_parser() -> ToolParser:
    """Tworzy instancję parsera narzędzi"""
    return ToolParser()

def analyze_message_for_tools(message: str) -> Dict[str, Any]:
    """Analizuje wiadomość i zwraca sugestie narzędzi"""
    parser = create_tool_parser()
    return parser.get_tool_suggestions(message)

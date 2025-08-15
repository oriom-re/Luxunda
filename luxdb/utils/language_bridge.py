
"""
Multi-language execution bridge for Soul modules
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List, Optional, Callable


class JavaScriptWrapper:
    """Wrapper dla wykonywania JavaScript w kontekście Soul"""
    
    def __init__(self, js_source: str, module_name: str):
        self.js_source = js_source
        self.module_name = module_name
        self.functions = self._extract_functions()
        
    def _extract_functions(self) -> List[str]:
        """Wyciąga nazwy funkcji z kodu JavaScript"""
        import re
        
        # Proste rozpoznawanie funkcji - można rozszerzyć
        pattern = r'function\s+(\w+)\s*\('
        matches = re.findall(pattern, self.js_source)
        
        # Dodaj arrow functions
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        arrow_matches = re.findall(arrow_pattern, self.js_source)
        
        return matches + arrow_matches
    
    def get_function_names(self) -> List[str]:
        """Zwraca listę dostępnych funkcji"""
        return self.functions
    
    def create_python_callable(self, func_name: str) -> Callable:
        """Tworzy Python callable dla funkcji JavaScript"""
        def js_function_wrapper(*args, **kwargs):
            return self._execute_js_function(func_name, args, kwargs)
        
        js_function_wrapper.__name__ = func_name
        js_function_wrapper.__doc__ = f"JavaScript function {func_name} from {self.module_name}"
        
        return js_function_wrapper
    
    def _execute_js_function(self, func_name: str, args: tuple, kwargs: dict) -> Any:
        """Wykonuje funkcję JavaScript"""
        try:
            # Przygotuj kod JavaScript dla wykonania
            execution_code = f"""
{self.js_source}

// Wykonaj funkcję
const args = {json.dumps(list(args))};
const kwargs = {json.dumps(kwargs)};
const result = {func_name}(...args);
console.log(JSON.stringify({{ success: true, result: result }}));
"""
            
            # Zapisz do tymczasowego pliku
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(execution_code)
                temp_file = f.name
            
            try:
                # Wykonaj przez Node.js (jeśli dostępny)
                result = subprocess.run(
                    ['node', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        response = json.loads(output)
                        if response.get('success'):
                            return response.get('result')
                
                # Fallback - zwróć informację o błędzie
                return {
                    "error": "JavaScript execution failed",
                    "stderr": result.stderr,
                    "function": func_name
                }
                
            finally:
                # Usuń tymczasowy plik
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    
        except Exception as e:
            return {
                "error": f"JavaScript bridge error: {str(e)}",
                "function": func_name
            }


class MultiLanguageModule:
    """Kontener dla modułu wielojęzycznego"""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.functions = {}
        self.function_languages = {}
        
    def add_function(self, name: str, func: Callable, language: str):
        """Dodaje funkcję do modułu"""
        self.functions[name] = func
        self.function_languages[name] = language
        
    def get_function(self, name: str) -> Optional[Callable]:
        """Pobiera funkcję po nazwie"""
        return self.functions.get(name)
        
    def get_function_language(self, name: str) -> Optional[str]:
        """Zwraca język funkcji"""
        return self.function_languages.get(name)
        
    def list_functions(self) -> Dict[str, str]:
        """Lista funkcji z ich językami"""
        return self.function_languages.copy()


class LanguageDetector:
    """Detektor języka dla module_source"""
    
    @staticmethod
    def detect_language(source: str) -> str:
        """Automatycznie wykrywa język kodu"""
        
        # Sprawdź markery wielojęzyczne
        if '```python' in source and '```javascript' in source:
            return "multi"
            
        # Python indicators
        python_indicators = [
            'def ', 'import ', 'from ', 'class ', 'async def',
            'elif', 'except:', 'finally:', '__name__'
        ]
        
        # JavaScript indicators
        js_indicators = [
            'function ', 'const ', 'let ', 'var ', '=>', 
            'console.log', 'module.exports', 'require('
        ]
        
        python_score = sum(1 for indicator in python_indicators if indicator in source)
        js_score = sum(1 for indicator in js_indicators if indicator in source)
        
        if python_score > js_score:
            return "python"
        elif js_score > python_score:
            return "javascript"
        else:
            # Default to Python if unclear
            return "python"


# Language execution registry
LANGUAGE_EXECUTORS = {
    "python": "native",
    "javascript": JavaScriptWrapper,
    "multi": MultiLanguageModule
}

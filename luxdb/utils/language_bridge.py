"""
Multi-language execution bridge for Soul modules
"""

import subprocess
import json
import tempfile
import os
from typing import Dict, Any, List, Optional, Callable
import re # Import added for re.search in LanguageDetector

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
    """Wykrywa język na podstawie składni kodu"""

    @staticmethod
    def detect_language(source_code: str) -> str:
        """Automatycznie wykrywa język na podstawie składni"""

        # JavaScript patterns
        js_patterns = [
            r'function\s+\w+\s*\(',
            r'const\s+\w+\s*=',
            r'let\s+\w+\s*=',
            r'var\s+\w+\s*=',
            r'=>\s*{',
            r'console\.log\(',
        ]

        # Python patterns  
        py_patterns = [
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*:',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'print\s*\(',
            r'if\s+__name__\s*==\s*[\'"]__main__[\'"]',
        ]

        js_score = sum(1 for pattern in js_patterns if re.search(pattern, source_code))
        py_score = sum(1 for pattern in py_patterns if re.search(pattern, source_code))

        if js_score > py_score:
            return "javascript"
        elif py_score > 0:
            return "python"
        else:
            return "unknown"

class LanguageBridge:
    """Bridge dla obsługi Soul w różnych językach"""

    @staticmethod
    async def get_souls_by_language(language: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Pobiera Soul z bazy dla określonego języka - zwraca surowe dane"""
        from luxdb.core.postgre_db import Postgre_db

        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM souls
                    WHERE genotype->>'genesis'->>'language' = $1
                    OR genotype->>'language' = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, language, limit)

                souls = []
                for row in rows:
                    soul_data = {
                        'soul_hash': row['soul_hash'],
                        'global_ulid': row['global_ulid'],
                        'alias': row['alias'],
                        'genotype': row['genotype'],  # Już w formie dict (JSONB)
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    }
                    souls.append(soul_data)

                return souls

        except Exception as e:
            print(f"❌ Error getting souls by language {language}: {e}")
            return []

    @staticmethod
    async def get_executable_functions_by_language(language: str) -> Dict[str, Dict[str, Any]]:
        """Zwraca funkcje wykonywalne dla danego języka jako słownik"""
        souls = await LanguageBridge.get_souls_by_language(language)

        functions_dict = {}

        for soul_data in souls:
            genotype = soul_data['genotype']
            functions = genotype.get('functions', {})

            for func_name, func_info in functions.items():
                if not func_name.startswith('_'):  # Tylko publiczne funkcje
                    # Unikalna nazwa funkcji z kontekstem soul
                    unique_key = f"{soul_data['alias']}::{func_name}"

                    functions_dict[unique_key] = {
                        'soul_hash': soul_data['soul_hash'],
                        'soul_alias': soul_data['alias'],
                        'function_name': func_name,
                        'function_info': func_info,
                        'module_source': genotype.get('module_source'),
                        'language': language,
                        'genotype': genotype
                    }

        return functions_dict

    @staticmethod
    def create_js_execution_context(soul_data: Dict[str, Any]) -> str:
        """Tworzy kontekst wykonania dla JavaScript Soul"""
        genotype = soul_data['genotype']
        module_source = genotype.get('module_source', '')

        # Template dla JavaScript
        js_context = f"""
// Soul: {soul_data['alias']} ({soul_data['soul_hash'][:8]})
// Auto-generated execution context

// Module source
{module_source}

// Export functions for external execution
if (typeof module !== 'undefined' && module.exports) {{
    // Node.js environment
    const soulFunctions = {{}};

    // Auto-detect and export functions
    Object.getOwnPropertyNames(global).forEach(name => {{
        if (typeof global[name] === 'function' && !name.startsWith('_')) {{
            soulFunctions[name] = global[name];
        }}
    }});

    module.exports = {{
        soulData: {json.dumps(soul_data)},
        functions: soulFunctions
    }};
}}
"""
        return js_context


# Language execution registry
LANGUAGE_EXECUTORS = {
    "python": "native",
    "javascript": JavaScriptWrapper,
    "multi": MultiLanguageModule
}
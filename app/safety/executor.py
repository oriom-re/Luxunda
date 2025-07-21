import ast
import builtins
import sys
import traceback
from io import StringIO

class SafeCodeExecutor:
    """Bezpieczny executor kodu z ograniczeniami"""

    # Dozwolone built-in funkcje
    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter', 'float',
        'int', 'len', 'list', 'max', 'min', 'range', 'reversed', 'round',
        'sorted', 'str', 'sum', 'tuple', 'zip', 'print', '__import__'
    }

    # Bezpieczne moduły/pakiety do importu
    SAFE_IMPORTS = {
        'math', 'random', 'datetime', 'json', 'uuid', 'hashlib',
        'base64', 'urllib.parse', 'collections', 'itertools',
        'functools', 'operator', 'string', 'textwrap',
        're', 'decimal', 'fractions', 'statistics'
    }

    # Bezpieczne imports z modułów
    SAFE_FROM_IMPORTS = {
        'datetime': {'datetime', 'date', 'time', 'timedelta'},
        'collections': {'namedtuple', 'defaultdict', 'Counter', 'deque'},
        'typing': {'List', 'Dict', 'Set', 'Tuple', 'Optional', 'Union', 'Any'},
        'math': {'pi', 'e', 'sin', 'cos', 'tan', 'sqrt', 'log', 'exp'},
        'json': {'loads', 'dumps'},
        'random': {'randint', 'random', 'choice', 'shuffle'}
    }

    # Zabronione wyrażenia AST
    FORBIDDEN_NODES = {
        ast.Call  # Będziemy sprawdzać wywołania funkcji osobno
    }

    @classmethod
    def validate_code(cls, code: str) -> tuple[bool, str]:
        """Waliduje kod przed wykonaniem"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Błąd składni: {str(e)}"

        for node in ast.walk(tree):
            # Sprawdź zabronione typy węzłów
            if type(node) in cls.FORBIDDEN_NODES:
                if isinstance(node, ast.Call):
                    # Sprawdź czy wywołanie funkcji jest dozwolone
                    if hasattr(node.func, 'id') and node.func.id not in cls.ALLOWED_BUILTINS:
                        return False, f"Zabronione wywołanie funkcji: {node.func.id}"

            # Sprawdź importy
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    if module_name not in cls.SAFE_IMPORTS:
                        print(f"❌ Zabroniony import modułu: {module_name}")
                        return False, f"Zabroniony import modułu: {module_name}"

            if isinstance(node, ast.ImportFrom):
                module_name = node.module
                if module_name not in cls.SAFE_FROM_IMPORTS:
                    print(f"❌ Zabroniony import z modułu: {module_name}")
                    return False, f"Zabroniony import z modułu: {module_name}"
                
                # Sprawdź czy importowane elementy są bezpieczne
                allowed_names = cls.SAFE_FROM_IMPORTS[module_name]
                for alias in node.names:
                    if alias.name not in allowed_names and alias.name != '*':
                        print(f"❌ Zabroniony import {alias.name} z modułu {module_name}")
                        return False, f"Zabroniony import {alias.name} z modułu {module_name}"

            # Sprawdź dostęp do atrybutów
            if isinstance(node, ast.Attribute):
                attr_name = node.attr
                if attr_name.startswith('_') or attr_name in ['__import__', 'exec', 'eval']:
                    print(f"❌ Zabroniony dostęp do atrybutu: {attr_name}")
                    return False, f"Zabroniony dostęp do atrybutu: {attr_name}"

        return True, "Kod jest bezpieczny"

    @classmethod
    async def execute_function(cls, code: str, function_name: str, *args, **kwargs) -> dict:
        """Wykonuje funkcję z kodu w bezpiecznym środowisku"""
        is_valid, validation_msg = cls.validate_code(code)
        if not is_valid:
            return {
                'success': False,
                'error': validation_msg,
                'output': '',
                'result': None
            }

        # Przygotuj bezpieczne środowisko wykonania
        safe_builtins = {name: getattr(builtins, name) for name in cls.ALLOWED_BUILTINS}
        
        # Dodaj bezpieczne moduły do środowiska
        safe_modules = {}
        for module_name in cls.SAFE_IMPORTS:
            try:
                safe_modules[module_name] = __import__(module_name)
            except ImportError:
                pass  # Ignoruj moduły których nie ma
        
        safe_globals = {
            '__builtins__': safe_builtins,
            **safe_modules
        }
        safe_locals = {}

        # Przekieruj stdout do przechwycenia print
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Wykonaj kod
            exec(code, safe_globals, safe_locals)

            # Sprawdź czy funkcja została zdefiniowana
            if function_name not in safe_locals:
                return {
                    'success': False,
                    'error': f"Funkcja '{function_name}' nie została znaleziona w kodzie",
                    'output': captured_output.getvalue(),
                    'result': None
                }

            # Wykonaj funkcję
            func = safe_locals[function_name]
            if not callable(func):
                return {
                    'success': False,
                    'error': f"'{function_name}' nie jest funkcją",
                    'output': captured_output.getvalue(),
                    'result': None
                }

            result = func(*args, **kwargs)

            return {
                'success': True,
                'error': None,
                'output': captured_output.getvalue(),
                'result': result
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Błąd wykonania: {str(e)}",
                'output': captured_output.getvalue(),
                'result': None,
                'traceback': traceback.format_exc()
            }
        finally:
            sys.stdout = old_stdout
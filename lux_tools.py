
import os
import json
import ast
import subprocess
import tempfile
from typing import Dict, Any, List, Optional
from pathlib import Path
import openai
from datetime import datetime

class LuxTools:
    """Narzędzia dostępne dla agenta Lux"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_client = None
        if openai_api_key:
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje narzędzie o podanej nazwie z parametrami"""
        
        tools_map = {
            'read_file': self.read_file,
            'write_file': self.write_file,
            'list_files': self.list_files,
            'analyze_code': self.analyze_code,
            'run_tests': self.run_tests,
            'ask_gpt': self.ask_gpt,
            'create_directory': self.create_directory,
            'delete_file': self.delete_file,
            'check_syntax': self.check_syntax,
            'search_in_files': self.search_in_files
        }
        
        if tool_name not in tools_map:
            return {
                'success': False,
                'error': f'Nieznane narzędzie: {tool_name}',
                'available_tools': list(tools_map.keys())
            }
        
        try:
            result = await tools_map[tool_name](**parameters)
            return {
                'success': True,
                'tool': tool_name,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name,
                'parameters': parameters
            }
    
    async def read_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """Odczytuje zawartość pliku"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {'error': f'Plik nie istnieje: {file_path}'}
            
            if not path.is_file():
                return {'error': f'Ścieżka nie jest plikiem: {file_path}'}
            
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            return {
                'file_path': file_path,
                'content': content,
                'size': len(content),
                'lines': len(content.splitlines()),
                'encoding': encoding
            }
        except Exception as e:
            return {'error': f'Błąd odczytu pliku: {str(e)}'}
    
    async def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                        create_dirs: bool = True) -> Dict[str, Any]:
        """Zapisuje zawartość do pliku"""
        try:
            path = Path(file_path)
            
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            return {
                'file_path': file_path,
                'size': len(content),
                'lines': len(content.splitlines()),
                'created': not path.existed_before if hasattr(path, 'existed_before') else True
            }
        except Exception as e:
            return {'error': f'Błąd zapisu pliku: {str(e)}'}
    
    async def list_files(self, directory: str = '.', pattern: str = '*', 
                        recursive: bool = False) -> Dict[str, Any]:
        """Listuje pliki w katalogu"""
        try:
            path = Path(directory)
            if not path.exists():
                return {'error': f'Katalog nie istnieje: {directory}'}
            
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))
            
            result = {
                'directory': directory,
                'pattern': pattern,
                'recursive': recursive,
                'files': [],
                'directories': [],
                'total_count': 0
            }
            
            for item in files:
                item_info = {
                    'name': item.name,
                    'path': str(item),
                    'size': item.stat().st_size if item.is_file() else 0,
                    'modified': datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                }
                
                if item.is_file():
                    result['files'].append(item_info)
                elif item.is_dir():
                    result['directories'].append(item_info)
            
            result['total_count'] = len(result['files']) + len(result['directories'])
            return result
            
        except Exception as e:
            return {'error': f'Błąd listowania plików: {str(e)}'}
    
    async def analyze_code(self, file_path: str) -> Dict[str, Any]:
        """Analizuje kod Python pod kątem poprawności i metryki"""
        try:
            file_content = await self.read_file(file_path)
            if 'error' in file_content:
                return file_content
            
            content = file_content['content']
            
            # Analiza AST
            try:
                tree = ast.parse(content)
                syntax_valid = True
                syntax_error = None
            except SyntaxError as e:
                syntax_valid = False
                syntax_error = str(e)
                tree = None
            
            analysis = {
                'file_path': file_path,
                'syntax_valid': syntax_valid,
                'syntax_error': syntax_error,
                'metrics': {}
            }
            
            if tree:
                # Zbierz metryki
                analyzer = CodeAnalyzer()
                metrics = analyzer.analyze(tree, content)
                analysis['metrics'] = metrics
            
            return analysis
            
        except Exception as e:
            return {'error': f'Błąd analizy kodu: {str(e)}'}
    
    async def check_syntax(self, code: str, language: str = 'python') -> Dict[str, Any]:
        """Sprawdza poprawność składni kodu"""
        try:
            if language.lower() == 'python':
                try:
                    ast.parse(code)
                    return {
                        'valid': True,
                        'language': language,
                        'message': 'Składnia poprawna'
                    }
                except SyntaxError as e:
                    return {
                        'valid': False,
                        'language': language,
                        'error': str(e),
                        'line': e.lineno,
                        'column': e.offset
                    }
            else:
                return {'error': f'Nieobsługiwany język: {language}'}
                
        except Exception as e:
            return {'error': f'Błąd sprawdzania składni: {str(e)}'}
    
    async def run_tests(self, test_file: str = None, test_directory: str = None) -> Dict[str, Any]:
        """Uruchamia testy"""
        try:
            if test_file:
                cmd = ['python', '-m', 'pytest', test_file, '-v']
            elif test_directory:
                cmd = ['python', '-m', 'pytest', test_directory, '-v']
            else:
                cmd = ['python', '-m', 'pytest', '-v']
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            return {
                'command': ' '.join(cmd),
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {'error': 'Testy przekroczyły limit czasu (30s)'}
        except Exception as e:
            return {'error': f'Błąd uruchamiania testów: {str(e)}'}
    
    async def ask_gpt(self, prompt: str, model: str = 'gpt-3.5-turbo', 
                     max_tokens: int = 1000) -> Dict[str, Any]:
        """Wysyła zapytanie do GPT"""
        if not self.openai_client:
            return {'error': 'Klucz API OpenAI nie jest skonfigurowany'}
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Jesteś pomocnym asystentem programisty. Odpowiadaj po polsku."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                'prompt': prompt,
                'model': model,
                'response': response.choices[0].message.content,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {'error': f'Błąd GPT: {str(e)}'}
    
    async def create_directory(self, directory_path: str) -> Dict[str, Any]:
        """Tworzy katalog"""
        try:
            path = Path(directory_path)
            path.mkdir(parents=True, exist_ok=True)
            
            return {
                'directory_path': directory_path,
                'created': True,
                'exists': path.exists()
            }
        except Exception as e:
            return {'error': f'Błąd tworzenia katalogu: {str(e)}'}
    
    async def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Usuwa plik"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {'error': f'Plik nie istnieje: {file_path}'}
            
            if path.is_file():
                path.unlink()
                return {
                    'file_path': file_path,
                    'deleted': True
                }
            else:
                return {'error': f'Ścieżka nie jest plikiem: {file_path}'}
                
        except Exception as e:
            return {'error': f'Błąd usuwania pliku: {str(e)}'}
    
    async def search_in_files(self, search_term: str, directory: str = '.', 
                             pattern: str = '*.py', recursive: bool = True) -> Dict[str, Any]:
        """Wyszukuje tekst w plikach"""
        try:
            path = Path(directory)
            if recursive:
                files = list(path.rglob(pattern))
            else:
                files = list(path.glob(pattern))
            
            results = []
            
            for file_path in files:
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            if search_term in line:
                                results.append({
                                    'file': str(file_path),
                                    'line_number': line_num,
                                    'line_content': line.strip(),
                                    'match_position': line.find(search_term)
                                })
                    except Exception:
                        continue  # Pomiń pliki, których nie można odczytać
            
            return {
                'search_term': search_term,
                'directory': directory,
                'pattern': pattern,
                'recursive': recursive,
                'total_matches': len(results),
                'matches': results
            }
            
        except Exception as e:
            return {'error': f'Błąd wyszukiwania: {str(e)}'}


class CodeAnalyzer(ast.NodeVisitor):
    """Analizator kodu Python"""
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.lines_of_code = 0
        self.complexity = 0
    
    def analyze(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Analizuje drzewo AST i zwraca metryki"""
        self.visit(tree)
        
        lines = content.splitlines()
        code_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]
        
        return {
            'total_lines': len(lines),
            'code_lines': len(code_lines),
            'empty_lines': len(lines) - len(code_lines),
            'functions_count': len(self.functions),
            'classes_count': len(self.classes),
            'imports_count': len(self.imports),
            'complexity_score': self.complexity,
            'functions': self.functions,
            'classes': self.classes,
            'imports': self.imports
        }
    
    def visit_FunctionDef(self, node):
        self.functions.append({
            'name': node.name,
            'line': node.lineno,
            'args_count': len(node.args.args),
            'decorators_count': len(node.decorator_list)
        })
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        self.classes.append({
            'name': node.name,
            'line': node.lineno,
            'bases_count': len(node.bases),
            'decorators_count': len(node.decorator_list)
        })
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.append({
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'from_import'
            })
        self.generic_visit(node)
    
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_Try(self, node):
        self.complexity += 1
        self.generic_visit(node)

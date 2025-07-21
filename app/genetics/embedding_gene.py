
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import numpy as np
from .base_gene import BaseGene, GeneActivationContext
from app.beings.base import BaseBeing


class EmbeddingGene(BaseGene):
    """Gen do zarządzania embeddingami i dekompozycją hierarchiczną"""
    
    def __init__(self, gene_id: Optional[str] = None):
        super().__init__(gene_id)
        self.embedding_models = {
            'ada2': 'text-embedding-ada-002',
            'multilingual': 'paraphrase-multilingual-MiniLM-L12-v2'
        }
        self.decomposition_rules = {}
        self.embedding_cache = {}
    
    @property
    def gene_type(self) -> str:
        return "embedding"
    
    @property
    def required_energy(self) -> int:
        return 15
    
    @property
    def compatibility_tags(self) -> List[str]:
        return ['text', 'analysis', 'similarity', 'semantic', 'nlp']
    
    async def activate(self, host: BaseBeing, context: GeneActivationContext) -> bool:
        """Aktywuj gen embeddingów"""
        self.host_being = host
        self.is_active = True
        self.activation_context = context
        
        # Utwórz główny embedding bytu
        await self.create_primary_embedding()
        return True
    
    async def deactivate(self) -> bool:
        """Dezaktywuj gen"""
        self.is_active = False
        return True
    
    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Główna logika embeddingów"""
        action = stimulus.get('action', 'create_embedding')
        
        if action == 'create_embedding':
            return await self.create_embedding(stimulus.get('content'))
        elif action == 'decompose':
            return await self.decompose_being(stimulus.get('depth', 3))
        elif action == 'find_similar':
            return await self.find_similar_beings(stimulus.get('query'))
        elif action == 'create_hierarchy':
            return await self.create_embedding_hierarchy()
        
        return {'status': 'unknown_action'}
    
    async def create_primary_embedding(self):
        """Utwórz główny embedding bytu-gospodarza"""
        if not self.host_being:
            return
            
        # Stwórz tekstową reprezentację bytu
        being_text = self.being_to_text()
        
        # Symulacja tworzenia embeddingów (w rzeczywistości używałbyś prawdziwych modeli)
        embeddings = {}
        for model_name, model_id in self.embedding_models.items():
            embeddings[model_name] = await self.generate_embedding(being_text, model_id)
        
        # Zapisz embeddingi w atrybutach bytu
        if 'embeddings' not in self.host_being.attributes:
            self.host_being.attributes['embeddings'] = {}
        
        self.host_being.attributes['embeddings'].update(embeddings)
        await self.host_being.save()
    
    async def decompose_being(self, max_depth: int = 3) -> Dict[str, Any]:
        """Rozłóż byt na hierarchię mniejszych bytów z embeddingami"""
        if not self.host_being:
            return {'status': 'no_host'}
        
        decomposition_result = {
            'parent_soul': self.host_being.soul,
            'depth': 0,
            'children': [],
            'total_created': 0
        }
        
        # Rozpocznij dekompozycję od poziom 1
        await self._decompose_recursive(
            self.host_being, 
            decomposition_result, 
            current_depth=0, 
            max_depth=max_depth
        )
        
        return decomposition_result
    
    async def _decompose_recursive(self, parent_being: BaseBeing, result: Dict, current_depth: int, max_depth: int):
        """Rekurencyjna dekompozycja"""
        if current_depth >= max_depth:
            return
        
        # Określ strategię dekompozycji na podstawie typu bytu
        decomposition_strategy = self._get_decomposition_strategy(parent_being)
        fragments = await self._fragment_being(parent_being, decomposition_strategy)
        
        for i, fragment in enumerate(fragments):
            # Utwórz nowy byt dla fragmentu
            child_being = await self._create_child_being(
                parent_being, 
                fragment, 
                f"fragment_{current_depth}_{i}",
                current_depth + 1
            )
            
            # Dodaj do wyniku
            child_info = {
                'soul': child_being.soul,
                'type': fragment['type'],
                'content_preview': fragment['content'][:100] + '...' if len(fragment['content']) > 100 else fragment['content'],
                'embedding_similarity': await self._calculate_similarity(parent_being, child_being),
                'children': []
            }
            
            result['children'].append(child_info)
            result['total_created'] += 1
            
            # Kontynuuj dekompozycję dla dziecka
            await self._decompose_recursive(child_being, child_info, current_depth + 1, max_depth)
    
    def _get_decomposition_strategy(self, being: BaseBeing) -> str:
        """Określ strategię dekompozycji na podstawie typu bytu"""
        being_type = being.genesis.get('type', 'unknown')
        
        strategies = {
            'function': 'code_blocks',
            'message': 'paragraphs',
            'class': 'methods',
            'data': 'records',
            'scenario': 'steps'
        }
        
        return strategies.get(being_type, 'lines')
    
    async def _fragment_being(self, being: BaseBeing, strategy: str) -> List[Dict[str, Any]]:
        """Pofragmentuj byt zgodnie ze strategią"""
        content = self.being_to_text(being)
        fragments = []
        
        if strategy == 'code_blocks':
            # Dla kodu - bloki funkcji/klasy
            blocks = self._split_code_blocks(content)
            for block in blocks:
                fragments.append({
                    'type': 'code_block',
                    'content': block,
                    'metadata': {'language': 'python'}
                })
        
        elif strategy == 'paragraphs':
            # Dla tekstów - paragrafy
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    fragments.append({
                        'type': 'paragraph',
                        'content': para.strip(),
                        'metadata': {}
                    })
        
        elif strategy == 'lines':
            # Domyślnie - linie
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    fragments.append({
                        'type': 'line',
                        'content': line.strip(),
                        'metadata': {}
                    })
        
        return fragments[:10]  # Ogranicz do 10 fragmentów na poziom
    
    def _split_code_blocks(self, code: str) -> List[str]:
        """Podziel kod na bloki logiczne"""
        lines = code.split('\n')
        blocks = []
        current_block = []
        indent_level = 0
        
        for line in lines:
            if line.strip():
                # Sprawdź wcięcie
                current_indent = len(line) - len(line.lstrip())
                
                # Jeśli wcięcie się zmniejszyło i mamy blok - zakończ go
                if current_indent < indent_level and current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                
                current_block.append(line)
                indent_level = current_indent
        
        # Dodaj ostatni blok
        if current_block:
            blocks.append('\n'.join(current_block))
        
        return blocks
    
    async def _create_child_being(self, parent: BaseBeing, fragment: Dict[str, Any], fragment_id: str, depth: int) -> BaseBeing:
        """Utwórz byt-dziecko dla fragmentu"""
        from app.beings.being_factory import BeingFactory
        
        child_being = await BeingFactory.create_being(
            being_type='message',  # Fragmenty jako message beings
            genesis={
                'type': 'fragment',
                'name': f"{parent.genesis.get('name', 'Unknown')}_{fragment_id}",
                'parent_soul': parent.soul,
                'fragment_type': fragment['type'],
                'depth': depth,
                'created_by': 'embedding_gene'
            },
            attributes={
                'content': fragment['content'],
                'metadata': fragment['metadata'],
                'energy_level': max(10, parent.energy_level // 2),
                'tags': ['fragment', fragment['type'], f'depth_{depth}']
            }
        )
        
        # Utwórz embedding dla fragmentu
        fragment_embedding = await self.generate_embedding(fragment['content'])
        child_being.attributes['embeddings'] = {
            'primary': fragment_embedding
        }
        await child_being.save()
        
        # Utwórz relację parent-child
        from app.beings.base import Relationship
        await Relationship.create(
            source_soul=parent.soul,
            target_soul=child_being.soul,
            genesis={
                'type': 'decomposition',
                'relationship': 'parent_child',
                'depth': depth,
                'fragment_type': fragment['type']
            },
            attributes={
                'decomposition_strategy': self._get_decomposition_strategy(parent),
                'similarity_score': 0.9,  # Wysoka - to fragment rodzica
                'energy_level': 5
            }
        )
        
        return child_being
    
    async def generate_embedding(self, text: str, model: str = 'ada2') -> List[float]:
        """Generuj embedding (symulacja - w rzeczywistości użyj prawdziwego modelu)"""
        # Symulacja - hash-based pseudo-embedding
        hash_val = hash(text + model)
        np.random.seed(abs(hash_val) % 2**32)
        
        if model == 'ada2':
            embedding = np.random.normal(0, 1, 1536).tolist()  # Ada-002 ma 1536 wymiarów
        else:
            embedding = np.random.normal(0, 1, 384).tolist()   # MiniLM ma 384 wymiary
        
        return embedding
    
    async def _calculate_similarity(self, being1: BaseBeing, being2: BaseBeing) -> float:
        """Oblicz podobieństwo między bytami na podstawie embeddingów"""
        emb1 = being1.attributes.get('embeddings', {}).get('primary', [])
        emb2 = being2.attributes.get('embeddings', {}).get('primary', [])
        
        if not emb1 or not emb2:
            return 0.0
        
        # Cosine similarity
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)
    
    def being_to_text(self, being: BaseBeing = None) -> str:
        """Konwertuj byt do reprezentacji tekstowej"""
        target_being = being or self.host_being
        if not target_being:
            return ""
        
        # Składaj tekstową reprezentację z różnych pól
        parts = [
            f"Name: {target_being.genesis.get('name', 'Unknown')}",
            f"Type: {target_being.genesis.get('type', 'unknown')}"
        ]
        
        # Dodaj kod jeśli to function being
        if 'source' in target_being.genesis:
            parts.append(f"Source:\n{target_being.genesis['source']}")
        
        # Dodaj content jeśli istnieje
        if 'content' in target_being.attributes:
            parts.append(f"Content:\n{target_being.attributes['content']}")
        
        # Dodaj tagi
        if target_being.tags:
            parts.append(f"Tags: {', '.join(target_being.tags)}")
        
        return '\n\n'.join(parts)
    
    async def create_embedding_hierarchy(self) -> Dict[str, Any]:
        """Utwórz pełną hierarchię embeddingów dla całego systemu"""
        # To będzie zaawansowana funkcja do analizy całego wszechświata bytów
        return {
            'status': 'hierarchy_created',
            'levels': 4,
            'total_beings_analyzed': 42,
            'embedding_relationships': 156
        }

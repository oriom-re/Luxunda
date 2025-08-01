
from typing import List, Dict, Any, Optional
import numpy as np
from database.models.base import Soul, Being, Message
from database.soul_repository import BeingRepository
from ai.embendding import create_embedding
import asyncio

class MessageSimilarityService:
    """Serwis do porównywania wiadomości i tworzenia relacji na podstawie podobieństwa"""
    
    def __init__(self, similarity_threshold: float = 0.75):
        self.similarity_threshold = similarity_threshold
    
    async def calculate_cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Oblicza podobieństwo kosinusowe między dwoma embeddings"""
        if not embedding1 or not embedding2:
            return 0.0
        
        # Konwertuj na numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Oblicz podobieństwo kosinusowe
        dot_product = np.dot(vec1, vec2)
        magnitude1 = np.linalg.norm(vec1)
        magnitude2 = np.linalg.norm(vec2)
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        return float(similarity)
    
    async def get_message_embedding(self, message_content: str) -> List[float]:
        """Generuje embedding dla treści wiadomości"""
        try:
            embedding = await create_embedding(None, message_content)
            if isinstance(embedding, dict) and embedding.get('error'):
                # Fallback - prosty hash-based embedding dla testów
                return self._generate_fallback_embedding(message_content)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return self._generate_fallback_embedding(message_content)
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generuje prosty fallback embedding na potrzeby testów"""
        # Bardzo prosty embedding oparty na charakterystykach tekstu
        words = text.lower().split()
        embedding = []
        
        # 10-wymiarowy embedding
        for i in range(10):
            if i < len(words):
                char_sum = sum(ord(c) for c in words[i])
                embedding.append((char_sum % 100) / 100.0)
            else:
                embedding.append(0.0)
        
        return embedding
    
    async def compare_messages_and_create_relations(self, soul_hash: str) -> Dict[str, Any]:
        """Porównuje wszystkie wiadomości dla danego soul_hash i tworzy relacje"""
        messages = await BeingRepository.load_all_by_soul_hash(soul_hash)
        if not messages or len(messages.get('beings', [])) < 2:
            return {"message": "Potrzeba co najmniej 2 wiadomości do porównania", "created_relations": 0}
        
        beings = messages.get('beings', [])
        created_relations = 0
        relations_created = []
        
        # Pobierz soul relacji
        relation_soul = await self._get_or_create_relation_soul()
        
        print(f"📊 Porównywanie {len(beings)} wiadomości...")
        
        # Porównaj każdą wiadomość z każdą inną
        for i in range(len(beings)):
            for j in range(i + 1, len(beings)):
                message1 = beings[i]
                message2 = beings[j]
                
                # Pobierz treść wiadomości
                content1 = self._extract_message_content(message1)
                content2 = self._extract_message_content(message2)
                
                if not content1 or not content2:
                    continue
                
                # Generuj embeddings
                embedding1 = await self.get_message_embedding(content1)
                embedding2 = await self.get_message_embedding(content2)
                
                # Oblicz podobieństwo
                similarity = await self.calculate_cosine_similarity(embedding1, embedding2)
                
                print(f"🔍 Podobieństwo między wiadomościami: {similarity:.3f}")
                
                # Jeśli podobieństwo przekracza próg, stwórz relację
                if similarity >= self.similarity_threshold:
                    relation_data = {
                        "source_uid": message1.get('ulid'),
                        "target_uid": message2.get('ulid'),
                        "relation_type": "similar_content",
                        "strength": similarity,
                        "metadata": {
                            "similarity_score": similarity,
                            "content1_preview": content1[:50] + "..." if len(content1) > 50 else content1,
                            "content2_preview": content2[:50] + "..." if len(content2) > 50 else content2,
                            "created_by": "message_similarity_service"
                        }
                    }
                    
                    try:
                        relation_being = await Being.create(relation_soul, relation_data)
                        created_relations += 1
                        relations_created.append({
                            "relation_id": relation_being.ulid,
                            "similarity_score": similarity,
                            "message1_id": message1.get('ulid'),
                            "message2_id": message2.get('ulid')
                        })
                        print(f"✅ Utworzono relację podobieństwa: {similarity:.3f}")
                    except Exception as e:
                        print(f"⚠️ Błąd tworzenia relacji: {e}")
        
        return {
            "message": f"Przeanalizowano {len(beings)} wiadomości",
            "created_relations": created_relations,
            "relations_details": relations_created,
            "similarity_threshold": self.similarity_threshold
        }
    
    def _extract_message_content(self, message_being: Dict[str, Any]) -> str:
        """Wyciąga treść wiadomości z bytu"""
        if 'message' in message_being and isinstance(message_being['message'], dict):
            return message_being['message'].get('content', '')
        elif 'content' in message_being:
            return str(message_being['content'])
        return ''
    
    async def _get_or_create_relation_soul(self) -> Soul:
        """Pobiera lub tworzy soul dla relacji podobieństwa"""
        try:
            # Spróbuj załadować istniejący soul
            soul = await Soul.load_by_alias("message_similarity_relation")
            if soul:
                return soul
        except:
            pass
        
        # Utwórz nowy soul jeśli nie istnieje
        similarity_relation_genotype = {
            "genesis": {
                "name": "message_similarity_relation",
                "type": "relation",
                "doc": "Relacja podobieństwa między wiadomościami"
            },
            "attributes": {
                "source_uid": {"py_type": "str", "table_name": "_text"},
                "target_uid": {"py_type": "str", "table_name": "_text"},
                "relation_type": {"py_type": "str", "table_name": "_text"},
                "strength": {"py_type": "float", "table_name": "_numeric"},
                "metadata": {"py_type": "dict", "table_name": "_jsonb"}
            }
        }
        
        return await Soul.create(similarity_relation_genotype, alias="message_similarity_relation")
    
    async def get_similar_messages(self, message_ulid: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Znajduje wiadomości podobne do danej wiadomości"""
        # Pobierz wszystkie relacje podobieństwa dla danej wiadomości
        relations = await BeingRepository.load_all()
        if not relations:
            return []
        
        similar_messages = []
        for relation in relations.get('beings', []):
            if (relation.get('source_uid') == message_ulid or 
                relation.get('target_uid') == message_ulid):
                
                similarity_score = relation.get('strength', 0)
                other_message_id = (relation.get('target_uid') if 
                                  relation.get('source_uid') == message_ulid 
                                  else relation.get('source_uid'))
                
                similar_messages.append({
                    "message_id": other_message_id,
                    "similarity_score": similarity_score,
                    "relation_id": relation.get('ulid')
                })
        
        # Sortuj według podobieństwa
        similar_messages.sort(key=lambda x: x['similarity_score'], reverse=True)
        return similar_messages[:limit]
    
    def set_similarity_threshold(self, threshold: float):
        """Ustawia próg podobieństwa"""
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
        else:
            raise ValueError("Próg podobieństwa musi być między 0.0 a 1.0")

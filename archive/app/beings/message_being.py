from dataclasses import dataclass
from datetime import datetime
from app.beings.base import Being

@dataclass
class MessageBeing(Being):
    """Byt wiadomości z metadanymi i embedingami"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'message':
            self.genesis['type'] = 'message'
        if 'message_data' not in self.attributes:
            self.attributes['message_data'] = {}
        if 'embedding' not in self.attributes:
            self.attributes['embedding'] = None
        if 'metadata' not in self.attributes:
            self.attributes['metadata'] = {}
    
    def set_content(self, content: str):
        """Ustawia treść wiadomości"""
        self.attributes['message_data']['content'] = content
        self.attributes['message_data']['length'] = len(content)
        self.attributes['message_data']['timestamp'] = datetime.now().isoformat()
        
        # Symulacja wygenerowania embedingu (w rzeczywistości byłby to model AI)
        self.attributes['embedding'] = [hash(content + str(i)) % 1000 / 1000.0 for i in range(10)]
    
    def set_sender(self, sender_soul: str):
        """Ustawia nadawcę wiadomości"""
        self.attributes['metadata']['sender'] = sender_soul
    
    def set_context_being(self, context_soul: str):
        """Ustawia byt będący kontekstem wiadomości"""
        self.attributes['metadata']['context_being'] = context_soul
    
    def get_similarity(self, other_message: 'MessageBeing') -> float:
        """Oblicza podobieństwo z inną wiadomością na podstawie embedingu"""
        if not self.attributes.get('embedding') or not other_message.attributes.get('embedding'):
            return 0.0
        
        # Proste podobieństwo cosinusowe (symulowane)
        emb1 = self.attributes['embedding']
        emb2 = other_message.attributes['embedding']
        
        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        magnitude1 = sum(a * a for a in emb1) ** 0.5
        magnitude2 = sum(a * a for a in emb2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
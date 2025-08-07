
"""
Simplified LuxDB API - intuitive interface for developers
"""

class SimpleLuxDB:
    """Uproszczone API dla LuxDB - wszystko w jednym miejscu"""
    
    def __init__(self, db_config=None):
        self.db = None  # Wewnętrzna instancja LuxDB
    
    async def create_entity(self, name: str, data: dict, entity_type: str = "entity"):
        """
        Tworzy nową encję - to wszystko czego potrzebuje deweloper
        
        Args:
            name: Nazwa encji
            data: Dane encji (dowolna struktura)
            entity_type: Typ encji (opcjonalnie)
        
        Returns:
            Encja z ID i wszystkimi potrzebnymi metodami
        """
        # Automatycznie tworzy genotyp na podstawie danych
        # Tworzy soul i being w tle
        # Zwraca prostą encję
        pass
    
    async def get_entity(self, entity_id: str):
        """Pobiera encję po ID"""
        pass
    
    async def connect_entities(self, entity1_id: str, entity2_id: str, relation_type: str = "connected"):
        """Łączy dwie encje prostą relacją"""
        pass
    
    async def query_entities(self, filters: dict = None):
        """Wyszukuje encje według filtrów"""
        pass
    
    async def get_graph_data(self):
        """Zwraca dane dla grafu w standardowym formacie"""
        pass

class SimpleEntity:
    """Prosta encja - wszystko czego potrzebuje deweloper"""
    
    def __init__(self, id: str, name: str, data: dict, entity_type: str):
        self.id = id
        self.name = name  
        self.data = data
        self.type = entity_type
    
    async def update(self, new_data: dict):
        """Aktualizuje dane encji"""
        pass
    
    async def connect_to(self, other_entity, relation_type: str = "connected"):
        """Łączy z inną encją"""
        pass
    
    async def get_connections(self):
        """Zwraca wszystkie połączenia tej encji"""
        pass
    
    def to_dict(self):
        """Standardowy format dla frontenda"""
        return {
            'id': self.id,
            'name': self.name,
            'data': self.data,
            'type': self.type
        }

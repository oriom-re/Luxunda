import weakref
from typing import Dict, Any, Optional
import copy

class VirtualEnvironmentManager:
    """Menedżer wirtualnych środowisk - optymalizuje pamięć"""
    
    _shared_base = {}  # Współdzielona baza dla wszystkich środowisk
    _environments = weakref.WeakValueDictionary()  # Auto cleanup
    
    @classmethod
    def setup_shared_base(cls, base_context: Dict[str, Any]):
        """Ustawia wspólny kontekst dla wszystkich środowisk"""
        cls._shared_base = base_context
    
    @classmethod
    def create_environment(cls, entity_id: str, entity) -> 'VirtualEnvironment':
        """Tworzy środowisko dla bytu (z cache)"""
        if entity_id in cls._environments:
            return cls._environments[entity_id]
        
        env = VirtualEnvironment(entity, cls._shared_base)
        cls._environments[entity_id] = env
        return env

class VirtualEnvironment:
    """Wirtualne środowisko dla pojedynczego bytu"""
    
    def __init__(self, entity, shared_base: Dict[str, Any]):
        self.entity = entity
        self._shared_base = shared_base  # Reference, nie kopia
        self._local_overrides = {}  # Tylko lokalne zmiany
        self._cached_globals = None
        
    @property
    def globals(self) -> Dict[str, Any]:
        """Lazy-loaded globals z cache invalidation"""
        if self._cached_globals is None:
            self._cached_globals = {
                **self._shared_base,  # Współdzielona baza
                **self._local_overrides,  # Lokalne nadpisania
                
                # Specyficzne dla bytu
                'entity': self.entity,
                'entity_name': self.entity.genesis.get('name', 'Unknown'),
                'entity_uid': self.entity.uid,
                
                # Metody pomocnicze
                'log': self._create_logger(),
                'remember': lambda k, v: self.entity.remember(k, v),
                'recall': lambda k: self.entity.recall(k),
            }
        return self._cached_globals
    
    def set_local(self, key: str, value: Any):
        """Ustawia wartość lokalną (tylko dla tego bytu)"""
        self._local_overrides[key] = value
        self._invalidate_cache()
    
    def _create_logger(self):
        """Tworzy logger specyficzny dla bytu"""
        entity_name = self.entity.genesis.get('name', self.entity.uid[:8])
        
        def log(message: str, level: str = "INFO"):
            timestamp = datetime.now().isoformat()
            print(f"[{timestamp}] [{level}] [Entity:{entity_name}] {message}")
            return {
                "type": "log",
                "level": level,
                "message": message,
                "timestamp": timestamp,
                "source": entity_name
            }
        return log
    
    def _invalidate_cache(self):
        """Invaliduje cache globals"""
        self._cached_globals = None

# Rozszerzenie klasy Genotype
class Genotype(Being):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._virtual_env = None
    
    @property
    def virtual_env(self) -> VirtualEnvironment:
        """Lazy-loaded virtual environment"""
        if self._virtual_env is None:
            self._virtual_env = VirtualEnvironmentManager.create_environment(
                self.uid, self
            )
        return self._virtual_env
    
    async def load_and_run_genotype(self, genotype_name, call_init: bool = True):
        soul = await self.get_soul_by_name(genotype_name)
        if not soul:
            print(f"❌ Nie znaleziono duszy dla nazwy: {genotype_name}")
            return None
        
        # Sprawdź cache
        if genotype_name in self.cxt:
            return self.cxt[genotype_name]
        
        try:
            # Tworzymy moduł
            spec = importlib.util.spec_from_loader(genotype_name, loader=None, origin="virtual")
            genotype_module = importlib.util.module_from_spec(spec)
            
            # 🌐 Wykonujemy w wirtualnym środowisku
            exec(soul['genesis']['code'], self.virtual_env.globals)
            
            # Cache wynik
            self.cxt[genotype_name] = genotype_module
            
            # Inicjalizacja
            if call_init and 'init' in self.virtual_env.globals:
                init_func = self.virtual_env.globals['init']
                await self.maybe_async(init_func)
            
            return genotype_module
            
        except Exception as e:
            print(f"❌ Błąd w środowisku {genotype_name}: {e}")
            return None
        
# VirtualEnvironmentManager.setup_shared_base({
#     **globals(),
#     'app_version': '1.0.0',
#     'debug_mode': True,
#     # Inne współdzielone zasoby
# })
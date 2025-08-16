#!/usr/bin/env python3
"""
🧬 Being Model - Nowoczesny model JSONB bez legacy systemów
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from ..repository.soul_repository import BeingRepository
from luxdb.utils.serializer import JSONBSerializer
import ulid # Import ulid globally
import time # Import time globally
import asyncio # Import asyncio globally
from dataclasses import dataclass, field # Import dataclass and field
from luxdb.core.globals import Globals # Import Globals

@dataclass
class Being:
    """
    Being reprezentuje instancję bytu - konkretny obiekt utworzony na podstawie Soul.

    Każdy Being:
    - Ma unikalny ULID
    - Odwołuje się do Soul przez hash
    - Zawiera dane w formacie JSONB
    - Ma kontrolę dostępu i TTL
    """

    ulid: str = None
    _ulid: str = field(default=None, init=False, repr=False) # Internal ULID storage
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: str = None
    data: Dict[str, Any] = field(default_factory=dict)
    access_zone: str = "public_zone"  # Domyślnie publiczne
    ttl_expires: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cache dla Soul (lazy loading z TTL)
    _soul_cache: Optional[Any] = field(default=None, init=False, repr=False)
    _soul_cache_ttl: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Inicjalizacja po utworzeniu obiektu"""
        if not self.ulid and not self._ulid: # Use _ulid if provided by from_dict
            self.ulid = str(ulid.ulid())
        elif self._ulid:
            self.ulid = self._ulid # Set public ulid from internal _ulid

        # NIE ustawiamy automatycznie created_at - tylko przy zapisie do bazy
        self.updated_at = datetime.now()

        # Cache dla dynamicznie załadowanych handlerów
        self._dynamic_handlers: Dict[str, Callable] = {}
        self._module_loaded = False

    @classmethod
    async def set(cls, soul, data: Dict[str, Any], alias: str = None,
                  access_zone: str = "public_zone", ttl_hours: int = None) -> Dict[str, Any]:
        """
        Metoda set dla Being - tworzy i automatycznie zapisuje do bazy.

        Args:
            soul: Obiekt Soul (genotyp)
            data: Dane bytu
            alias: Opcjonalny alias
            access_zone: Strefa dostępu
            ttl_hours: TTL w godzinach

        Returns:
            Standardowy słownik odpowiedzi z nowym Being
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            # Utwórz Being w pamięci
            being = await cls.create(soul, alias=alias, attributes=data)
            being.access_zone = access_zone

            # TTL
            if ttl_hours:
                from datetime import timedelta
                being.ttl_expires = datetime.now() + timedelta(hours=ttl_hours)

            # ZAWSZE zapisz przez set()
            save_result = await being.save()

            if not save_result.get('success'):
                return save_result  # Zwróć błąd zapisu

            soul_context = {
                "soul_hash": being.soul_hash,
                "genotype": soul.genotype if hasattr(soul, 'genotype') else {}
            }

            return GeneticResponseFormat.success_response(
                data={"being": being.to_json_serializable()},
                soul_context=soul_context
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=str(e),
                error_code="BEING_SET_ERROR"
            )

    @classmethod
    async def _get_by_ulid_internal(cls, ulid_value: str) -> Optional['Being']:
        """Wewnętrzna metoda get_by_ulid zwracająca obiekt Being"""
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_ulid(ulid_value)
        return result.get('being') if result.get('success') else None

    @classmethod
    async def _create_internal(cls, soul_or_hash=None, alias: str = None, attributes: Dict[str, Any] = None, **kwargs) -> 'Being':
        """Wewnętrzna metoda create zwracająca obiekt Being"""

    @classmethod
    async def get(cls, ulid_value: str) -> Dict[str, Any]:
        """
        Standardowa metoda get dla Being zgodna z formatem genetycznym.

        Args:
            ulid_value: ULID bytu

        Returns:
            Standardowy słownik odpowiedzi z Being lub błędem
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            being = await cls._get_by_ulid_internal(ulid_value)

            if being:
                # Pobierz kontekst Soul
                soul = await being.get_soul()
                soul_context = {
                    "soul_hash": being.soul_hash,
                    "genotype": soul.genotype if soul else {}
                }

                return GeneticResponseFormat.success_response(
                    data={"being": being.to_json_serializable()},
                    soul_context=soul_context
                )
            else:
                return GeneticResponseFormat.error_response(
                    error="Being not found",
                    error_code="BEING_NOT_FOUND"
                )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=str(e),
                error_code="BEING_GET_ERROR"
            )

    @classmethod
    async def get_by_alias(cls, alias: str) -> List['Being']:
        """
        Pobiera wszystkie Being o danym aliasie.

        Args:
            alias: Alias bytu

        Returns:
            Lista Being o podanym aliasie
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_alias(alias)
        beings = result.get('beings', []) if result.get('success') else []
        return [being for being in beings if being is not None]

    @classmethod
    async def get_by_soul_hash(cls, soul_hash: str) -> List['Being']:
        """
        Pobiera wszystkie Being dla danego soul_hash.

        Args:
            soul_hash: Hash Soul

        Returns:
            Lista Being o podanym soul_hash
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_soul_hash(soul_hash)
        beings = result.get('beings', []) if result.get('success') else []
        return [being for being in beings if being is not None]

    @classmethod
    async def get_or_create(cls, soul_or_hash=None, attributes: Dict[str, Any] = None,
                           unique_by: str = "soul_hash", soul: 'Soul' = None, soul_hash: str = None, 
                           max_instances: int = None) -> 'Being':
        """
        Pobiera istniejący Being lub tworzy nowy z obsługą poolingu.

        Args:
            soul_or_hash: Soul lub hash do bytu
            alias: Alias bytu
            attributes: Atrybuty do ustawienia
            unique_by: Sposób szukania unikalności ("alias", "soul_hash")
            soul: Soul object (nowy styl)
            soul_hash: Hash soul (legacy)
            max_instances: Maksymalna liczba aktywnych instancji (None = bez limitu)

        Returns:
            Istniejący lub nowy Being
        """
        # Resolve target soul
        if soul is not None:
            target_soul = soul
        elif soul_hash is not None:
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_hash} not found")
            target_soul = result.get('soul')
        elif isinstance(soul_or_hash, str):
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_or_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_or_hash} not found")
            target_soul = result.get('soul')
        else:
            target_soul = soul_or_hash

        if not target_soul:
            raise ValueError("Soul object or hash must be provided.")

        

        # POOLING LOGIC - ograniczona liczba aktywnych instancji
        if max_instances is not None:
            beings_for_soul = await cls.get_by_soul_hash(target_soul.soul_hash)
            active_beings = [b for b in beings_for_soul if b.data.get('active', False)]
            
            if len(active_beings) < max_instances:
                # Sprawdź czy są nieaktywne do reaktywacji
                inactive_beings = [b for b in beings_for_soul if not b.data.get('active', False)]
                if inactive_beings:
                    # Reaktywuj nieaktywny Being
                    existing_being = inactive_beings[0]
                    existing_being.data['active'] = True
                    existing_being.updated_at = datetime.now()
                    
                    if attributes:
                        existing_being.data.update(attributes)
                    
                    await existing_being.save()
                    print(f"🔄 Reactivated pooled Being: {existing_being.ulid[:8]} ({len(active_beings)+1}/{max_instances})")
                    return existing_being
            else:
                # Limit osiągnięty, zwróć pierwszy aktywny
                first_active = active_beings[0]
                print(f"⚠️ Pool limit reached ({max_instances}), returning existing Being: {first_active.ulid[:8]}")
                return first_active

        # STANDARDOWA LOGIKA - soul_hash
        existing_being = None

        if unique_by == "soul_hash":
            # PRECYZYJNE zapytanie - jeden Being per soul_hash (Kernel style)
            beings_for_soul = await cls.get_by_soul_hash(target_soul.soul_hash)
            if beings_for_soul:
                existing_being = beings_for_soul[0]  # Pierwszy Being od tego Soul

        # Jeśli istnieje - zwróć go (opcjonalnie aktualizuj dane)
        if existing_being:
            # Aktualizuj atrybuty jeśli podano
            if attributes:
                existing_being.data.update(attributes)
                existing_being.updated_at = datetime.now()
                await existing_being.save()
            return existing_being

        # Jeśli nie istnieje - utwórz nowy
        new_being = await cls.create(target_soul, attributes=attributes)
        
        # Ustaw active dla poolingu
        if max_instances is not None:
            new_being.data['active'] = True
            await new_being.save()
            print(f"🆕 Created new pooled Being: {new_being.ulid[:8]} (active)")
        
        return new_being

    @classmethod
    async def create(cls, soul_or_hash=None, attributes: Dict[str, Any] = None, force_new: bool = False, soul: 'Soul' = None, soul_hash: str = None) -> 'Being':
        """
        Tworzy nowy Being w pamięci (nie zapisuje do bazy automatycznie).

        Do zapisu używaj being.set() lub Being.set()
        """

        # Being nie ma alias - usunięta niepotrzebna logika

        # Standardowa logika rozpoznawania Soul
        if soul is not None:
            target_soul = soul
        elif soul_hash is not None:
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_hash} not found")
            target_soul = result.get('soul')
        elif isinstance(soul_or_hash, str):
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_or_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_or_hash} not found")
            target_soul = result.get('soul')
        else:
            target_soul = soul_or_hash

        if not target_soul:
             raise ValueError("Soul object or hash must be provided.")

        being = cls()
        being.soul_hash = target_soul.soul_hash
        being.global_ulid = target_soul.global_ulid

        # Walidacja danych (bez serializacji - tylko przy zapisie do bazy)
        if attributes:
            errors = target_soul.validate_data(attributes)
            if errors:
                raise ValueError(f"Validation errors: {', '.join(errors)}")
            being.data = attributes
        else:
            being.data = {}

        # Oznacz jako nietrwałe (domyślnie w pamięci)
        being.data['_persistent'] = False

        # Ustawienie pozostałych atrybutów z metadanych Soul
        for key, value in target_soul.genotype.items():
            if key != 'attributes':
                setattr(being, key, value)

        print(f"💭 Created transient being: {being.ulid[:8]} (use .set() to persist)")

        # *** AUTOMATYCZNA INICJALIZACJA PO UTWORZENIU ***
        await being._auto_initialize_after_creation(target_soul)

        return being

    @classmethod
    async def _create_internal(cls, soul_or_hash=None, attributes: Dict[str, Any] = None, force_new: bool = False, soul: 'Soul' = None, soul_hash: str = None, access_zone: str = "public_zone", ttl_hours: int = None) -> 'Being':
        """Wewnętrzna metoda create - kopia oryginalnej logiki"""
        # Backward compatibility handling
        if soul is not None:
            target_soul = soul
        elif soul_hash is not None:
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_hash} not found")
            target_soul = result.get('soul')
        elif isinstance(soul_or_hash, str):
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_or_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_or_hash} not found")
            target_soul = result.get('soul')
        else:
            target_soul = soul_or_hash

        if not target_soul:
             raise ValueError("Soul object or hash must be provided.")

        being = cls()
        being.soul_hash = target_soul.soul_hash
        being.global_ulid = target_soul.global_ulid
        being.access_zone = access_zone

        # Walidacja danych (bez serializacji - tylko przy zapisie do bazy)
        if attributes:
            errors = target_soul.validate_data(attributes)
            if errors:
                raise ValueError(f"Validation errors: {', '.join(errors)}")
            being.data = attributes
        else:
            being.data = {}

        # TTL
        if ttl_hours:
            from datetime import timedelta
            being.ttl_expires = datetime.now() + timedelta(hours=hours)

        # NIE zapisuj automatycznie - tylko przez set() lub save()
        being.data['_persistent'] = False
        print(f"💭 Created internal being: {being.ulid[:8]} (transient)")

        # *** AUTOMATYCZNA INICJALIZACJA PO UTWORZENIU ***
        await being._auto_initialize_after_creation(target_soul)

        return being

    async def get_soul(self):
        """
        Pobiera Soul z cache lub bazy danych (lazy loading z TTL).

        Returns:
            Obiekt Soul
        """
        # Sprawdź cache i TTL
        current_time = time.time()
        if (self._soul_cache and self._soul_cache_ttl and
            current_time < self._soul_cache_ttl):
            return self._soul_cache

        # Załaduj Soul z bazy
        if self.soul_hash:
            from .soul import Soul
            soul = await Soul.get_by_hash(self.soul_hash)

            # Zaktualizuj cache
            if soul:
                self._soul_cache = soul
                self._soul_cache_ttl = current_time + 3600  # 1 godzina TTL

                # Inicjalizuj handlery z modułu jeśli jeszcze nie zostało to zrobione
                if not self._module_loaded:
                    await self._initialize_dynamic_handlers(soul)

            return soul

        return None

    async def _auto_initialize_after_creation(self, soul):
        """
        Automatyczna inicjalizacja Being po utworzeniu.
        Being z funkcją init staje się masterem zarządzania swoimi funkcjami.
        """
        try:
            if soul.has_init_function():
                print(f"🧬 Auto-initializing master being {self.ulid[:8]} with init function")

                # Przygotuj kontekst Being (NIE są to atrybuty!)
                being_context = {
                    'ulid': self.ulid,
                    'creation_time': datetime.now().isoformat(),
                    'data': self.data.copy(),
                    'soul_functions': soul.list_functions(),
                    'function_count': soul.get_functions_count()
                }

                result = await soul.auto_init(being_context=being_context)

                if result.get('success'):
                    print(f"🎯 Being {self.ulid[:8]} is now a function master - knows {soul.get_functions_count()} functions")
                    # Being staje się masterem swoich funkcji
                    self.data['_function_master'] = True
                    self.data['_initialized'] = True
                    self.data['_init_time'] = datetime.now().isoformat()
                    self.data['_managed_functions'] = soul.list_functions()
                    self.data['_function_signatures'] = {
                        name: soul.get_function_info(name) for name in soul.list_functions()
                    }

                    if self.is_persistent():
                        await self.save()
                    return result # Return result for persistence check
                else:
                    print(f"❌ Being {self.ulid[:8]} initialization failed: {result.get('error')}")
                    return result # Return result for persistence check

        except Exception as e:
            print(f"💥 Auto-initialization failed for being {self.ulid[:8]}: {e}")
            return {'success': False, 'error': str(e)} # Return error result

    async def _initialize_dynamic_handlers(self, soul):
        """Inicjalizuje dynamiczne handlery z kodu źródłowego modułu Soul"""
        try:
            if soul.has_module_source():
                # Załaduj moduł dynamicznie
                module = soul.load_module_dynamically()
                if module:
                    # Wyciągnij funkcje z modułu
                    module_functions = soul.extract_functions_from_module(module)

                    # Dodaj funkcje jako handlery
                    for func_name, func in module_functions.items():
                        self._dynamic_handlers[func_name] = func

                        # Opcjonalnie: dodaj też do rejestru funkcji Soul
                        if func_name not in soul._function_registry:
                            soul._register_immutable_function(func_name, func)

                    self._module_loaded = True
                    print(f"Loaded {len(module_functions)} dynamic handlers for being {self.ulid[:8]}")

        except Exception as e:
            print(f"Failed to initialize dynamic handlers: {e}")

    def get_dynamic_handler(self, handler_name: str) -> Optional[Callable]:
        """Pobiera dynamiczny handler po nazwie"""
        return self._dynamic_handlers.get(handler_name)

    def list_dynamic_handlers(self) -> List[str]:
        """Lista dostępnych dynamicznych handlerów"""
        return list(self._dynamic_handlers.keys())

    async def execute_dynamic_handler(self, handler_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Wykonuje dynamiczny handler"""
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            handler = self.get_dynamic_handler(handler_name)
            if not handler:
                return GeneticResponseFormat.error_response(
                    error=f"Dynamic handler '{handler_name}' not found",
                    error_code="HANDLER_NOT_FOUND"
                )

            # Dodaj kontekst Being do kwargs
            if 'being_context' not in kwargs:
                kwargs['being_context'] = {
                    'ulid': self.ulid,
                    'data': self.data
                }

            # Wykonaj handler
            if asyncio.iscoroutinefunction(handler):
                result = await handler(*args, **kwargs)
            else:
                result = handler(*args, **kwargs)

            # Zaktualizuj statystyki
            execution_count = self.data.get('handler_executions', 0) + 1
            self.data['handler_executions'] = execution_count
            self.data['last_handler_execution'] = datetime.now().isoformat()
            self.updated_at = datetime.now()

            return GeneticResponseFormat.success_response(
                data={
                    "handler_name": handler_name,
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Handler execution failed: {str(e)}",
                error_code="HANDLER_EXECUTION_ERROR"
            )

    async def request_function_execution_via_kernel(self, function_name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        DELEGUJE wykonanie funkcji do Kernel - Being nie wykonuje funkcji bezpośrednio!
        Being to niezmienne instancje, wykonanie odbywa się przez Master Soul + Kernel.
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            # Deleguj do Kernel
            from ..core.intelligent_kernel import intelligent_kernel

            execution_request = {
                "being_ulid": self.ulid,
                "soul_hash": self.soul_hash,
                "function_name": function_name,
                "arguments": {"args": args, "kwargs": kwargs},
                "request_type": "function_execution",
                "timestamp": datetime.now().isoformat()
            }

            print(f"🏛️ Being {self.ulid[:8]} delegating function '{function_name}' execution to Kernel")

            # Kernel znajdzie odpowiedni Master Soul Being i wykona funkcję
            result = await intelligent_kernel.execute_function_via_master_soul(
                self.soul_hash,
                function_name,
                execution_request
            )

            return GeneticResponseFormat.success_response(
                data={
                    "delegated_to": "kernel",
                    "function_name": function_name,
                    "execution_result": result,
                    "being_role": "request_delegator_only"
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Function execution delegation failed: {str(e)}",
                error_code="KERNEL_DELEGATION_ERROR"
            )

    def _simulate_function_execution(self, function_name: str, function_data: Dict[str, Any], args: tuple, kwargs: Dict[str, Any]) -> str:
        """Symuluje wykonanie funkcji na podstawie jej definicji"""
        domain = function_data.get('domain', 'general')

        if domain == 'mathematics':
            if 'expression' in kwargs:
                return f"Calculated {kwargs['expression']} = 42 (simulated)"
            return "Mathematical operation completed (simulated)"

        elif domain == 'nlp':
            if 'text' in kwargs:
                text = kwargs['text']
                return f"Text analysis of '{text[:50]}...': Sentiment: Positive, Keywords: ['AI', 'development'] (simulated)"
            return "Text analysis completed (simulated)"

        else:
            return f"Function {function_name} executed with {len(args)} args and {len(kwargs)} kwargs (simulated)"

    async def _execute_via_real_openai(self, function_name: str, function_schema: Dict, args: tuple, kwargs: Dict, openai_client) -> Dict[str, Any]:
        """Wykonuje funkcję przez prawdziwe API OpenAI"""
        try:
            import json

            # Przygotuj prompt dla OpenAI
            prompt = f"""
            Execute the function {function_name} with the following arguments:
            Args: {args}
            Kwargs: {kwargs}

            Function definition: {json.dumps(function_schema, indent=2)}

            Please provide a realistic result for this function call.
            """

            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a function execution assistant. Execute the requested function and provide realistic results."},
                    {"role": "user", "content": prompt}
                ],
                tools=[function_schema] if function_schema else None,
                tool_choice="auto"
            )

            return {
                "function_name": function_name,
                "executed_via": "real_openai_api",
                "arguments": {"args": args, "kwargs": kwargs},
                "openai_response": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ OpenAI execution failed: {e}")
            return {
                "function_name": function_name,
                "executed_via": "openai_fallback_simulation",
                "arguments": {"args": args, "kwargs": kwargs},
                "result": f"OpenAI execution failed, using simulation: {self._simulate_function_execution(function_name, {}, args, kwargs)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def execute_soul_function(self, function_name: str = None, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje funkcję z Soul poprzez Being context.

        Args:
            function_name: Nazwa funkcji do wykonania (None = domyślne execute)
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            Wynik wykonania funkcji
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        soul = await self.get_soul()
        if not soul:
            return GeneticResponseFormat.error_response(
                error="No soul attached to being",
                error_code="NO_SOUL"
            )

        # Przygotuj being_context dla funkcji Soul
        being_context = {
            "ulid": self.ulid,
            "data": self.data,
            "soul_hash": soul.soul_hash,
            "attributes": self.data  # Alias dla kompatybilności
        }

        # Jeśli Soul ma module_source - używaj standardowego protokołu execute
        if soul.has_module_source():
            # Wszystkie Soul z module_source muszą mieć execute
            if not soul.has_execute_function():
                return GeneticResponseFormat.error_response(
                    error="Soul with module_source must have execute function",
                    error_code="MISSING_EXECUTE"
                )

            # Standardowe wywołanie execute z request protocol
            if function_name and function_name != 'execute':
                # Przekaż żądanie konkretnej funkcji przez execute
                request = {
                    "action": function_name,
                    "data": kwargs.get('data'),
                    "args": args,
                    "kwargs": {k: v for k, v in kwargs.items() if k != 'data'}
                }
                return await soul.execute_function('execute', request=request, being_context=being_context)
            else:
                # Bezpośrednie wywołanie execute
                return await soul.execute_function('execute', being_context=being_context, *args, **kwargs)

        # Dla Soul bez module_source - bezpośrednie wywołanie funkcji
        target_function = function_name or 'execute'
        return await soul.execute_function(target_function, being_context=being_context, *args, **kwargs)

    def is_function_master(self) -> bool:
        """Sprawdza czy Being jest masterem funkcji (ma init i został zainicjalizowany)"""
        return self.data.get('_function_master', False) and self.data.get('_initialized', False)

    async def add_dynamic_function(self, function_name: str, function_definition: Dict[str, Any], source: str = "user") -> Dict[str, Any]:
        """
        Dodaje nową funkcję do Being jako atrybut.
        Master Function Being może dodawać sobie funkcje dynamicznie.
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            if not self.is_function_master():
                return GeneticResponseFormat.error_response(
                    error="Only function masters can add dynamic functions",
                    error_code="NOT_FUNCTION_MASTER"
                )

            # Inicjalizuj dynamic_functions jeśli nie istnieje
            if '_dynamic_functions' not in self.data:
                self.data['_dynamic_functions'] = {}

            # Dodaj definicję funkcji
            self.data['_dynamic_functions'][function_name] = {
                "definition": function_definition,
                "description": function_definition.get('description', ''),
                "parameters": function_definition.get('parameters', {}),
                "source": source,
                "added_at": datetime.now().isoformat(),
                "execution_count": 0,
                "last_executed": None,
                "enabled": True
            }

            # Aktualizuj listę zarządzanych funkcji
            managed_functions = self.data.get('_managed_functions', [])
            if function_name not in managed_functions:
                managed_functions.append(function_name)
                self.data['_managed_functions'] = managed_functions

            # Zapisz zmiany
            if self.is_persistent():
                await self.save()

            print(f"🔧 Master {self.ulid[:8]} added dynamic function: {function_name}")

            return GeneticResponseFormat.success_response(
                data={
                    "function_name": function_name,
                    "added": True,
                    "total_dynamic_functions": len(self.data['_dynamic_functions'])
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Failed to add dynamic function: {str(e)}",
                error_code="DYNAMIC_FUNCTION_ADD_ERROR"
            )

    async def _intelligent_execute(self, data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Inteligentna procedura execute - Being sam decyduje jaką funkcję wywołać.
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            soul = await self.get_soul()

            # Sprawdź czy ma domyślną funkcję execute
            if soul.has_execute_function():
                print(f"🎯 Master {self.alias} delegating to default execute function")
                result = await soul.default_execute(data=data, **kwargs)
            else:
                # Inteligentne wybieranie funkcji na podstawie danych lub kontekstu
                available_functions = self.data.get('_managed_functions', [])

                if not available_functions:
                    return GeneticResponseFormat.error_response(
                        error="Function master has no available functions",
                        error_code="NO_FUNCTIONS_AVAILABLE"
                    )

                # Prosta logika wyboru - można rozbudować o AI/ML
                selected_function = self._select_best_function_for_data(data, available_functions)
                print(f"🧠 Master {self.alias} intelligently selected function: {selected_function}")

                result = await self.execute_soul_function(selected_function, data=data, **kwargs)

            # Aktualizuj statystyki inteligentnego wykonania
            self.data['_intelligent_executions'] = self.data.get('_intelligent_executions', 0) + 1
            self.data['_last_intelligent_execution'] = datetime.now().isoformat()

            return result

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Intelligent execution failed: {str(e)}",
                error_code="INTELLIGENT_EXECUTION_ERROR"
            )

    def _select_best_function_for_data(self, data: Dict[str, Any], available_functions: List[str]) -> str:
        """
        Inteligentne wybieranie najlepszej funkcji dla danych.
        Można rozbudować o zaawansowaną logikę AI/ML.
        """
        if not available_functions:
            return "execute"  # fallback

        # Prosta logika - można zastąpić zaawansowanym AI
        if data:
            # Jeśli są dane, preferuj funkcje które prawdopodobnie je przetwarzają
            processing_functions = [f for f in available_functions if any(
                keyword in f.lower() for keyword in ['process', 'handle', 'execute', 'run']
            )]
            if processing_functions:
                return processing_functions[0]

        # Domyślnie zwróć pierwszą dostępną funkcję
        return available_functions[0]

    async def _update_function_usage_stats(self, function_name: str, success: bool):
        """Aktualizuje statystyki użycia funkcji przez mastera"""
        if '_function_stats' not in self.data:
            self.data['_function_stats'] = {}

        if function_name not in self.data['_function_stats']:
            self.data['_function_stats'][function_name] = {
                'total_calls': 0,
                'successful_calls': 0,
                'last_called': None
            }

        stats = self.data['_function_stats'][function_name]
        stats['total_calls'] += 1
        if success:
            stats['successful_calls'] += 1
        stats['last_called'] = datetime.now().isoformat()

    def is_persistent(self) -> bool:
        """Sprawdza czy Being jest trwałe (zapisywane w bazie)"""
        return self.data.get('_persistent', False)

    def is_active(self) -> bool:
        """Sprawdza czy Being jest aktywny w puli"""
        return self.data.get('active', False)

    async def activate(self) -> Dict[str, Any]:
        """Aktywuje Being w puli"""
        from luxdb.utils.serializer import GeneticResponseFormat
        
        self.data['active'] = True
        self.updated_at = datetime.now()
        
        save_result = await self.save()
        if save_result.get('success'):
            print(f"🟢 Activated Being: {self.alias or self.ulid[:8]}")
            return GeneticResponseFormat.success_response(
                data={"being_activated": True, "ulid": self.ulid}
            )
        else:
            return save_result

    async def deactivate(self) -> Dict[str, Any]:
        """Deaktywuje Being w puli (zwraca do pool)"""
        from luxdb.utils.serializer import GeneticResponseFormat
        
        self.data['active'] = False
        self.updated_at = datetime.now()
        
        save_result = await self.save()
        if save_result.get('success'):
            print(f"🔴 Deactivated Being: {self.alias or self.ulid[:8]} (returned to pool)")
            return GeneticResponseFormat.success_response(
                data={"being_deactivated": True, "ulid": self.ulid}
            )
        else:
            return save_result

    @classmethod
    async def get_pool_status(cls, soul_hash: str) -> Dict[str, Any]:
        """Zwraca status puli dla danego Soul"""
        beings_for_soul = await cls.get_by_soul_hash(soul_hash)
        
        active_beings = [b for b in beings_for_soul if b.data.get('active', False)]
        inactive_beings = [b for b in beings_for_soul if not b.data.get('active', False)]
        
        return {
            'success': True,
            'soul_hash': soul_hash,
            'total_beings': len(beings_for_soul),
            'active_count': len(active_beings),
            'inactive_count': len(inactive_beings),
            'active_beings': [
                {
                    'ulid': b.ulid,
                    'alias': b.alias,
                    'created_at': b.created_at.isoformat() if b.created_at else None,
                    'updated_at': b.updated_at.isoformat() if b.updated_at else None
                }
                for b in active_beings
            ],
            'inactive_beings': [
                {
                    'ulid': b.ulid,
                    'alias': b.alias,
                    'created_at': b.created_at.isoformat() if b.created_at else None,
                    'updated_at': b.updated_at.isoformat() if b.updated_at else None
                }
                for b in inactive_beings
            ]
        }

    async def save(self) -> Dict[str, Any]:
        """
        Zapisuje Being do bazy danych (transactional).
        Serializacja odbywa się TYLKO tutaj, przy zapisie do bazy.
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            soul = await self.get_soul()
            if not soul:
                return GeneticResponseFormat.error_response(
                    error="Cannot save being without soul",
                    error_code="NO_SOUL_FOR_SAVE"
                )

            # TUTAJ ODBYWA SIĘ JEDYNA SERIALIZACJA - przy zapisie do bazy
            from luxdb.utils.serializer import JSONBSerializer
            serialized_data, errors = JSONBSerializer.validate_and_serialize(self.data, soul)
            if errors:
                return GeneticResponseFormat.error_response(
                    error=f"Serialization errors: {', '.join(errors)}",
                    error_code="SERIALIZATION_ERROR"
                )

            # Tymczasowo podmień dane na zserializowane do zapisu
            original_data = self.data
            self.data = serialized_data

            try:
                # Zapisz do bazy w transakcji
                from ..repository.soul_repository import BeingRepository
                await BeingRepository.insert_data_transaction(self, soul.genotype)
            finally:
                # Przywróć oryginalne dane do pamięci
                self.data = original_data

            # Przypisanie do strefy dostępu
            from ..core.access_control import access_controller
            access_controller.assign_being_to_zone(self.ulid, self.access_zone)

            # Oznacz jako trwałe
            self.data['_persistent'] = True
            self.updated_at = datetime.now()

            print(f"💾 Being {self.alias or self.ulid[:8]} saved to database")

            return GeneticResponseFormat.success_response(
                data={
                    "being_saved": True,
                    "ulid": self.ulid,
                    "persistent": True
                },
                soul_context={"soul_hash": self.soul_hash}
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Failed to save being: {str(e)}",
                error_code="BEING_SAVE_ERROR"
            )

    def get_function_mastery_info(self) -> Dict[str, Any]:
        """Zwraca informacje o masterowaniu funkcji przez tego Being"""
        dynamic_functions = self.data.get('_dynamic_functions', {})

        return {
            'is_function_master': self.is_function_master(),
            'managed_functions': self.data.get('_managed_functions', []),
            'function_count': len(self.data.get('_managed_functions', [])),
            'intelligent_executions': self.data.get('_intelligent_executions', 0),
            'function_stats': self.data.get('_function_stats', {}),
            'initialized_at': self.data.get('_init_time'),
            'function_signatures': self.data.get('_function_signatures', {}),
            'dynamic_functions': {
                'count': len(dynamic_functions),
                'functions': list(dynamic_functions.keys()),
                'total_executions': sum(f.get('execution_count', 0) for f in dynamic_functions.values()),
                'enabled_count': len([f for f in dynamic_functions.values() if f.get('enabled', True)])
            }
        }

    async def init(self, **kwargs) -> Dict[str, Any]:
        """
        Wygodna metoda do ręcznego wywołania inicjalizacji.

        Args:
            **kwargs: Dodatkowe argumenty dla funkcji init

        Returns:
            Wynik funkcji init
        """
        soul = await self.get_soul()
        if not soul:
            from luxdb.utils.serializer import GeneticResponseFormat
            return GeneticResponseFormat.error_response(
                error="Soul not found for this being",
                error_code="SOUL_NOT_FOUND"
            )

        being_context = {
            'ulid': self.ulid,
            'alias': self.alias,
            'data': self.data.copy()
        }

        return await soul.auto_init(being_context=being_context, **kwargs)

    async def request_evolution(self, evolution_trigger: str, new_capabilities: Dict[str, Any] = None,
                               access_level_change: str = None) -> Dict[str, Any]:
        """
        Being może poprosić system o ewolucję, ale nie może się sam ewoluować.
        Żądanie ewolucji musi zostać zatwierdzone przez Kernel lub uprawniony byt.

        Args:
            evolution_trigger: Powód ewolucji
            new_capabilities: Żądane nowe zdolności
            access_level_change: Żądana zmiana poziomu dostępu

        Returns:
            Potwierdzenie żądania ewolucji w formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            # Sprawdź czy może żądać ewolucji
            evolution_potential = await self.can_evolve()
            if not evolution_potential["can_evolve"]:
                return GeneticResponseFormat.error_response(
                    error="Being does not meet evolution requirements",
                    error_code="EVOLUTION_REQUIREMENTS_NOT_MET",
                    data={"requirements_not_met": evolution_potential["requirements_not_met"]}
                )

            # Przygotuj żądanie ewolucji
            evolution_request = {
                "requesting_being_ulid": self.ulid,
                "requesting_being_alias": self.alias,
                "evolution_trigger": evolution_trigger,
                "requested_capabilities": new_capabilities or {},
                "requested_access_change": access_level_change,
                "request_timestamp": datetime.now().isoformat(),
                "being_stats": {
                    "execution_count": self.data.get('execution_count', 0),
                    "current_access_zone": self.access_zone,
                    "age_in_system": (datetime.now() - (self.created_at or datetime.now())).days
                },
                "justification": self._generate_evolution_justification(evolution_trigger, evolution_potential)
            }

            # Dodaj żądanie do danych bytu
            if 'evolution_requests' not in self.data:
                self.data['evolution_requests'] = []

            self.data['evolution_requests'].append(evolution_request)
            from ..repository.soul_repository import BeingRepository
            await BeingRepository.set(self)

            return GeneticResponseFormat.success_response(
                data={
                    "evolution_requested": True,
                    "request_id": len(self.data['evolution_requests']) - 1,
                    "evolution_request": evolution_request,
                    "message": "Evolution request submitted to system. Awaiting Kernel approval."
                },
                soul_context={
                    "soul_hash": self.soul_hash,
                    "current_capabilities": await self.get_soul() and (await self.get_soul()).genotype or {}
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Evolution request failed: {str(e)}",
                error_code="EVOLUTION_REQUEST_ERROR"
            )

    def _generate_evolution_justification(self, evolution_trigger: str, evolution_potential: Dict[str, Any]) -> str:
        """Generuje uzasadnienie dla żądania ewolucji"""
        stats = evolution_potential["current_stats"]
        justification = f"Being {self.alias} requests evolution based on {evolution_trigger}. "
        justification += f"Current stats: {stats['execution_count']} executions, "
        justification += f"{stats['age_in_system']} days in system, "
        justification += f"access zone: {stats['access_zone']}. "

        if evolution_potential["available_evolutions"]:
            justification += "Available evolutions: " + ", ".join([
                evo["type"] for evo in evolution_potential["available_evolutions"]
            ])

        return justification

    async def can_evolve(self) -> Dict[str, Any]:
        """
        Sprawdza czy Being może ewoluować i jakie opcje ewolucji są dostępne.

        Returns:
            Informacje o możliwościach ewolucji
        """
        evolution_potential = {
            "can_evolve": False,
            "available_evolutions": [],
            "requirements_not_met": [],
            "current_stats": {
                "execution_count": self.data.get('execution_count', 0),
                "access_zone": self.access_zone,
                "age_in_system": (datetime.now() - (self.created_at or datetime.now())).days,
                "evolution_count": len(self.data.get('evolution_history', []))
            }
        }

        execution_count = self.data.get('execution_count', 0)
        system_age = (datetime.now() - (self.created_at or datetime.now())).days

        # Sprawdź możliwość awansu dostępu
        if self.access_zone == "public_zone" and execution_count >= 10:
            evolution_potential["available_evolutions"].append({
                "type": "access_level_promotion",
                "description": "Promote to authenticated access level",
                "requirements_met": True
            })
            evolution_potential["can_evolve"] = True

        # Sprawdź możliwość otrzymania uprawnień administratora
        if (self.access_zone == "authenticated_zone" and
            execution_count >= 100 and
            system_age >= 7):
            evolution_potential["available_evolutions"].append({
                "type": "admin_privileges",
                "description": "Grant administrative capabilities",
                "requirements_met": True
            })
            evolution_potential["can_evolve"] = True

        # Sprawdź możliwość zostania twórcą Soul
        if (execution_count >= 50 and
            len(self.data.get('evolution_history', [])) >= 1):
            evolution_potential["available_evolutions"].append({
                "type": "soul_creator",
                "description": "Grant ability to create new Soul genotypes",
                "requirements_met": True
            })
            evolution_potential["can_evolve"] = True

        # Dodaj wymagania które nie zostały spełnione
        if execution_count < 10:
            evolution_potential["requirements_not_met"].append(
                f"Need {10 - execution_count} more function executions for basic promotion"
            )

        if system_age < 7:
            evolution_potential["requirements_not_met"].append(
                f"Need {7 - system_age} more days in system for admin privileges"
            )

        return evolution_potential

    async def request_function_evolution(self, new_functions: Dict[str, Dict[str, Any]],
                                              justification: str) -> Dict[str, Any]:
        """
        Being może poprosić o ewolucję swojej Soul z nowymi funkcjami.

        Args:
            new_functions: Nowe funkcje do dodania
            justification: Uzasadnienie potrzeby nowych funkcji

        Returns:
            Wynik żądania ewolucji funkcji
        """
        from luxdb.utils.serializer import GeneticResponseFormat

        try:
            soul = await self.get_soul()
            if not soul:
                return GeneticResponseFormat.error_response(
                    error="Soul not found for function evolution",
                    error_code="SOUL_NOT_FOUND"
                )

            # Sprawdź czy Soul może ewoluować
            if not soul.can_accept_new_functions():
                return GeneticResponseFormat.error_response(
                    error="Soul cannot accept new functions (immutable or lacks basic capabilities)",
                    error_code="EVOLUTION_NOT_ALLOWED"
                )

            # Utwórz żądanie ewolucji funkcji
            evolution_request = {
                "type": "function_evolution",
                "requesting_being": self.ulid,
                "new_functions": new_functions,
                "justification": justification,
                "current_soul_hash": soul.soul_hash,
                "requested_at": datetime.now().isoformat(),
                "being_stats": {
                    "function_executions": self.data.get('execution_count', 0),
                    "is_function_master": self.is_function_master(),
                    "current_functions": soul.list_functions()
                }
            }

            # Dodaj do danych bytu
            if 'function_evolution_requests' not in self.data:
                self.data['function_evolution_requests'] = []

            self.data['function_evolution_requests'].append(evolution_request)
            await self.save()

            return GeneticResponseFormat.success_response(
                data={
                    "evolution_requested": True,
                    "request_type": "function_evolution",
                    "request_id": len(self.data['function_evolution_requests']) - 1,
                    "evolution_request": evolution_request,
                    "message": f"Function evolution requested: {list(new_functions.keys())}"
                },
                soul_context={
                    "soul_hash": soul.soul_hash,
                    "current_functions": soul.list_functions()
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Function evolution request failed: {str(e)}",
                error_code="FUNCTION_EVOLUTION_ERROR"
            )

    async def propose_soul_creation(self, new_soul_concept: Dict[str, Any]) -> Dict[str, Any]:
        """
        Being może zaproponować utworzenie nowej Soul (jeśli ma odpowiednie uprawnienia).

        Args:
            new_soul_concept: Koncepcja nowej Soul do utworzenia

        Returns:
            Wynik propozycji w formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        from .soul import Soul

        try:
            # Sprawdź uprawnienia
            can_evolve_info = await self.can_evolve()
            has_creator_rights = any(
                evo["type"] == "soul_creator" and evo["requirements_met"]
                for evo in can_evolve_info["available_evolutions"]
            )

            if not has_creator_rights:
                return GeneticResponseFormat.error_response(
                    error="Being does not have soul creation privileges",
                    error_code="INSUFFICIENT_CREATOR_PRIVILEGES"
                )

            # Waliduj koncepcję Soul
            if "genesis" not in new_soul_concept:
                new_soul_concept["genesis"] = {}

            new_soul_concept["genesis"]["created_by_being"] = self.ulid
            new_soul_concept["genesis"]["creator_alias"] = self.alias
            new_soul_concept["genesis"]["creation_timestamp"] = datetime.now().isoformat()
            new_soul_concept["genesis"]["creation_method"] = "being_proposal"

            # Utwórz nową Soul
            new_soul = await Soul.create(
                genotype=new_soul_concept,
                alias=new_soul_concept.get("genesis", {}).get("name", f"soul_by_{self.alias}")
            )

            # Zaktualizuj statystyki bytu
            if 'souls_created' not in self.data:
                self.data['souls_created'] = []

            self.data['souls_created'].append({
                "soul_hash": new_soul.soul_hash,
                "created_at": datetime.now().isoformat(),
                "soul_name": new_soul.alias
            })

            from ..repository.soul_repository import BeingRepository
            await BeingRepository.set(self)

            return GeneticResponseFormat.success_response(
                data={
                    "soul_created": True,
                    "new_soul": new_soul.to_json_serializable(),
                    "creator_being": {
                        "ulid": self.ulid,
                        "alias": self.alias,
                        "total_souls_created": len(self.data.get('souls_created', []))
                    }
                },
                soul_context={
                    "soul_hash": new_soul.soul_hash,
                    "genotype": new_soul.genotype
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Soul creation proposal failed: {str(e)}",
                error_code="SOUL_CREATION_FAILED"
            )

    def list_available_functions(self) -> List[str]:
        """Lista dostępnych funkcji do wykonania (tylko publiczne)"""
        if not self.soul:
            return []

        # Zwróć tylko funkcje publiczne z genotype.functions
        public_functions = []
        for func_name in self.soul.genotype.get("functions", {}):
            if not func_name.startswith('_'):
                public_functions.append(func_name)

        return public_functions

    async def get_function_details(self) -> Dict[str, Any]:
        """Szczegółowe informacje o dostępnych funkcjach"""
        if not self.soul:
            return {"error": "No soul attached"}

        return self.soul.get_available_functions_clear()

    async def get_soul_capabilities(self) -> Dict[str, Any]:
        """Informacje o możliwościach Soul"""
        if not self.soul:
            return {"error": "No soul attached"}

        return self.soul.get_function_visibility_info()

    def check_access(self, user_ulid: str = None, user_session: Dict[str, Any] = None) -> bool:
        """
        Sprawdza czy użytkownik ma dostęp do tego bytu.

        Args:
            user_ulid: ULID użytkownika
            user_session: Sesja użytkownika

        Returns:
            True jeśli ma dostęp
        """
        from ..core.access_control import access_controller
        return access_controller.check_access(self.ulid, user_ulid, user_session)

    def is_expired(self) -> bool:
        """Sprawdza czy byt wygasł (TTL)"""
        if not self.ttl_expires:
            return False
        return datetime.now() > self.ttl_expires

    def is_persistent(self) -> bool:
        """Sprawdza czy Being jest trwałe (zapisywane w bazie)"""
        return self.data.get('_persistent', True)

    async def save(self) -> Dict[str, Any]:
        """
        Zapisuje Being do bazy danych.

        Returns:
            Dict z wynikiem operacji
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.set(self)
        if result.get('success'):
            self.updated_at = datetime.now()

        return result

    async def execute(self, request=None, **kwargs) -> Dict[str, Any]:
        """
        Standardowa metoda execute - wywołuje Soul.execute przez protokół.

        Args:
            request: Request object lub dict z action, data, etc.
            **kwargs: Dodatkowe argumenty

        Returns:
            Wynik wykonania Soul.execute
        """
        # Jeśli request to string - przekształć na action
        if isinstance(request, str):
            request = {"action": request}

        return await self.execute_soul_function('execute', request=request, **kwargs)

    async def evolve_to_soul(self, new_genotype_changes: Dict[str, Any] = None, new_alias: str = None) -> Dict[str, Any]:
        """
        Being ewoluuje w nową Soul na podstawie swoich doświadczeń i danych.

        Args:
            new_genotype_changes: Zmiany w genotypie dla nowej Soul
            new_alias: Nowy alias dla Soul

        Returns:
            Wynik ewolucji w formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        from .soul import Soul

        try:
            current_soul = await self.get_soul()
            if not current_soul:
                return GeneticResponseFormat.error_response(
                    error="Cannot evolve Being without Soul",
                    error_code="SOUL_NOT_FOUND"
                )

            # Przygotuj nowy genotyp na podstawie doświadczeń Being
            evolved_genotype = current_soul.genotype.copy()

            # Dodaj informacje o ewolucji z Being
            if "genesis" not in evolved_genotype:
                evolved_genotype["genesis"] = {}

            evolved_genotype["genesis"]["evolved_from_being"] = self.ulid
            evolved_genotype["genesis"]["being_alias"] = self.alias
            evolved_genotype["genesis"]["evolution_timestamp"] = datetime.now().isoformat()
            evolved_genotype["genesis"]["evolution_trigger"] = "being_to_soul"

            # Włącz dane z Being jako nowe atrybuty genotypu
            if "attributes" not in evolved_genotype:
                evolved_genotype["attributes"] = {}

            # Dodaj doświadczenia Being jako atrybuty
            for key, value in self.data.items():
                if not key.startswith('_'):  # Pomijaj metadane
                    attr_name = f"inherited_{key}"
                    evolved_genotype["attributes"][attr_name] = {
                        "py_type": type(value).__name__,
                        "default": value,
                        "description": f"Inherited from Being {self.alias}"
                    }

            # Zastosuj dodatkowe zmiany
            if new_genotype_changes:
                for key, value in new_genotype_changes.items():
                    if "." in key:  # Nested path
                        keys = key.split(".")
                        current = evolved_genotype
                        for k in keys[:-1]:
                            if k not in current:
                                current[k] = {}
                            current = current[k]
                        current[keys[-1]] = value
                    else:
                        evolved_genotype[key] = value

            # Utwórz nową Soul
            new_soul = await Soul.create(
                genotype=evolved_genotype,
                alias=new_alias or f"evolved_{self.alias}"
            )

            # Zaktualizuj informacje w Being
            self.data['_evolved_to_soul'] = new_soul.soul_hash
            self.data['_evolution_timestamp'] = datetime.now().isoformat()
            await self.save()

            return GeneticResponseFormat.success_response(
                data={
                    "evolution_successful": True,
                    "new_soul": new_soul.to_json_serializable(),
                    "source_being": {
                        "ulid": self.ulid,
                        "alias": self.alias
                    }
                },
                soul_context={
                    "new_soul_hash": new_soul.soul_hash,
                    "source_soul_hash": current_soul.soul_hash,
                    "evolution_type": "being_to_soul"
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Being evolution failed: {str(e)}",
                error_code="BEING_EVOLUTION_ERROR"
            )

    def extend_ttl(self, hours: int):
        """Przedłuża TTL bytu"""
        if self.ttl_expires:
            self.ttl_expires += timedelta(hours=hours)
        else:
            self.ttl_expires = datetime.now() + timedelta(hours=hours)
        self.updated_at = datetime.now()

    @classmethod
    async def get_by_ulid(cls, ulid_value: str) -> Optional['Being']:
        """
        Ładuje Being po ULID.

        Args:
            ulid_value: ULID bytu

        Returns:
            Being lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_ulid(ulid_value)
        return result.get('being') if result.get('success') else None

    @classmethod
    async def get_by_alias(cls, alias: str) -> List['Being']:
        """
        Ładuje Beings po aliasie.

        Args:
            alias: Alias bytów

        Returns:
            Lista Being
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_alias(alias)
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def get_by_soul_alias(cls, soul_alias: str) -> List['Being']:
        """
        Ładuje Beings po aliasie Soul.

        Args:
            soul_alias: Alias Soul

        Returns:
            Lista Being powiązanych z Soul o podanym aliasie
        """
        from ..repository.soul_repository import SoulRepository
        from ..repository.being_repository import BeingRepository

        soul_result = await SoulRepository.get_soul_by_alias(soul_alias)
        if not soul_result or not soul_result.get('success'):
            return []

        target_soul = soul_result.get('soul')
        if not target_soul:
            return []

        # Użyj metody repozytorium do pobrania bytów po soul_hash
        beings_result = await BeingRepository.get_beings_by_soul_hash(target_soul.soul_hash)
        beings = beings_result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def get_by_soul_hash(cls, soul_hash: str) -> List['Being']:
        """
        PRECYZYJNE zapytanie - tylko Being od konkretnego Soul hash.

        Args:
            soul_hash: Dokładny hash Soul - żadnych losowych danych!

        Returns:
            Lista Being TYLKO dla tego Soul hash
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_soul_hash(soul_hash)
        beings = result.get('beings', []) if result.get('success') else []
        return [being for being in beings if being is not None]


    @classmethod
    async def get_all(cls, user_ulid: str = None, user_session: Dict[str, Any] = None) -> List['Being']:
        """
        Ładuje wszystkie Being z kontrolą dostępu.

        Args:
            user_ulid: ULID użytkownika (dla kontroli dostępu)
            user_session: Sesja użytkownika

        Returns:
            Lista dostępnych Being
        """
        from ..repository.soul_repository import BeingRepository
        from ..core.access_control import access_controller

        result = await BeingRepository.get_all_beings()
        beings = result.get('beings', [])
        beings = [being for being in beings if being is not None]

        # Filtrowanie według uprawnień dostępu
        return access_controller.filter_accessible_beings(beings, user_ulid, user_session)

    @classmethod
    async def get_by_access_zone(cls, zone_id: str, user_ulid: str = None,
                                user_session: Dict[str, Any] = None) -> List['Being']:
        """
        Pobiera byty z określonej strefy dostępu.

        Args:
            zone_id: ID strefy dostępu
            user_ulid: ULID użytkownika
            user_session: Sesja użytkownika

        Returns:
            Lista dostępnych bytów ze strefy
        """
        from ..repository.soul_repository import BeingRepository
        from ..core.access_control import access_controller

        # Sprawdź czy użytkownik ma dostęp do strefy
        zone = access_controller.zones.get(zone_id)
        if not zone:
            return []

        # Pobierz wszystkie byty i filtruj według strefy
        result = await BeingRepository.get_all_beings()
        beings = result.get('beings', [])
        beings = [being for being in beings if being is not None]

        zone_beings = [being for being in beings if being.access_zone == zone_id]

        # Filtrowanie według uprawnień dostępu
        return access_controller.filter_accessible_beings(zone_beings, user_ulid, user_session)

    async def save(self) -> Dict[str, Any]:
        """
        Zapisuje Being do bazy danych.

        Returns:
            Dict z wynikiem operacji
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.set(self)
        if result.get('success'):
            self.updated_at = datetime.now()

        return result

    async def delete(self) -> bool:
        """
        Usuwa Being z bazy danych.

        Returns:
            True jeśli usunięcie się powiodło
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.delete_being(self.ulid)
        return result.get('success', False)

    def get_attributes(self) -> Dict[str, Any]:
        """Zwraca atrybuty/dane bytu"""
        return self.data

    def set_attribute(self, key: str, value: Any):
        """Ustawia atrybut bytu"""
        self.data[key] = value
        self.updated_at = datetime.now()

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Pobiera atrybut bytu"""
        return self.data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Being do słownika dla serializacji"""
        return {
            'ulid': self.ulid,
            'global_ulid': self.global_ulid,
            'soul_hash': self.soul_hash,
            'alias': self.alias,
            'data': self.data,
            'access_zone': self.access_zone,
            'ttl_expires': self.ttl_expires.isoformat() if self.ttl_expires else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_json_serializable(self) -> Dict[str, Any]:
        """Automatycznie wykrywa i konwertuje strukturę do JSON-serializable"""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Being':
        """Tworzy Being z słownika"""
        being = cls()
        being._ulid = data.get('ulid') # Use _ulid for internal field
        being.ulid = data.get('ulid')  # Also set public ulid for consistency

        being.global_ulid = data.get('global_ulid', Globals.GLOBAL_ULID)
        being.soul_hash = data.get('soul_hash')
        being.alias = data.get('alias') # Alias jest zachowany dla kompatybilności z danymi
        being.data = data.get('data', {})
        being.access_zone = data.get('access_zone', 'public_zone')

        # Konwersja dat
        if data.get('ttl_expires'):
            if isinstance(data['ttl_expires'], str):
                being.ttl_expires = datetime.fromisoformat(data['ttl_expires'])
            else:
                being.ttl_expires = data['ttl_expires']

        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                being.created_at = datetime.fromisoformat(data['created_at'])
            else:
                being.created_at = data['created_at']

        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                being.updated_at = datetime.fromisoformat(data['updated_at'])
            else:
                being.updated_at = data['updated_at']

        return being

    def __json__(self):
        """Protokół dla automatycznej serializacji JSON"""
        return self.to_dict()

    def __repr__(self):
        status = "EXPIRED" if self.is_expired() else "ACTIVE"
        return f"Being(ulid={self.ulid[:8]}..., alias={self.alias}, zone={self.access_zone}, status={status})"
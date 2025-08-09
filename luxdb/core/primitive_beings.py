#!/usr/bin/env python3
"""
🧬 Primitive Beings - Podstawowe typy bytów używające tylko JSONB
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..models.being import Being

class PrimitiveBeing(Being):
    """
    Bazowa klasa dla prymitywnych bytów
    Używa tylko JSONB, bez legacy systemów
    """

    def __init__(self, being_type: str = "primitive"):
        super().__init__()
        self.being_type = being_type
        self.set_data('type', being_type)
        self.set_data('created_timestamp', datetime.now().isoformat())

    async def initialize(self, **kwargs) -> None:
        """Inicjalizuje byt z podanymi parametrami"""
        for key, value in kwargs.items():
            self.set_data(key, value)
        await self.save()

class DataBeing(PrimitiveBeing):
    """
    Byt do przechowywania i manipulacji danych
    """

    def __init__(self):
        super().__init__("data")
        self.set_data('storage', {})

    async def store_value(self, key: str, value: Any) -> None:
        """Przechowuje wartość pod kluczem"""
        storage = self.get_data('storage', {})
        storage[key] = value
        self.set_data('storage', storage)
        self.set_data('last_updated', datetime.now().isoformat())
        await self.save()

    async def get_value(self, key: str, default: Any = None) -> Any:
        """Pobiera wartość pod kluczem"""
        storage = self.get_data('storage', {})
        return storage.get(key, default)

    async def has_key(self, key: str) -> bool:
        """Sprawdza czy klucz istnieje"""
        storage = self.get_data('storage', {})
        return key in storage

    async def get_all_keys(self) -> List[str]:
        """Pobiera wszystkie klucze"""
        storage = self.get_data('storage', {})
        return list(storage.keys())

class FunctionBeing(PrimitiveBeing):
    """
    Byt reprezentujący funkcję
    """

    def __init__(self):
        super().__init__("function")
        self.set_data('function_code', '')
        self.set_data('function_name', '')
        self.set_data('execution_count', 0)

    async def set_function(self, name: str, code: str) -> None:
        """Ustawia kod funkcji"""
        self.set_data('function_name', name)
        self.set_data('function_code', code)
        self.set_data('function_defined_at', datetime.now().isoformat())
        await self.save()

    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje funkcję (symulacja)
        W prawdziwej implementacji można by dodać bezpieczny executor
        """
        execution_count = self.get_data('execution_count', 0)
        self.set_data('execution_count', execution_count + 1)
        self.set_data('last_execution', datetime.now().isoformat())

        result = {
            'success': True,
            'function_name': self.get_data('function_name'),
            'args': args,
            'kwargs': kwargs,
            'execution_time': datetime.now().isoformat(),
            'message': f"Function {self.get_data('function_name')} executed successfully"
        }

        await self.save()
        return result

class MessageBeing(PrimitiveBeing):
    """
    Byt reprezentujący wiadomość
    """

    def __init__(self):
        super().__init__("message")
        self.set_data('content', '')
        self.set_data('sender', '')
        self.set_data('metadata', {})

    async def set_message(self, content: str, sender: str = '', **metadata) -> None:
        """Ustawia treść wiadomości"""
        self.set_data('content', content)
        self.set_data('sender', sender)
        self.set_data('sent_at', datetime.now().isoformat())

        current_metadata = self.get_data('metadata', {})
        current_metadata.update(metadata)
        self.set_data('metadata', current_metadata)

        await self.save()

    async def get_content(self) -> str:
        """Pobiera treść wiadomości"""
        return self.get_data('content', '')

    async def get_sender(self) -> str:
        """Pobiera nadawcę wiadomości"""
        return self.get_data('sender', '')

class TaskBeing(PrimitiveBeing):
    """
    Byt reprezentujący zadanie
    """

    def __init__(self):
        super().__init__("task")
        self.set_data('task_name', '')
        self.set_data('task_description', '')
        self.set_data('status', 'pending')  # pending, running, completed, failed
        self.set_data('progress', 0)
        self.set_data('results', {})

    async def create_task(self, name: str, description: str = '') -> None:
        """Tworzy nowe zadanie"""
        self.set_data('task_name', name)
        self.set_data('task_description', description)
        self.set_data('created_at', datetime.now().isoformat())
        self.set_data('status', 'pending')
        await self.save()

    async def start_task(self) -> None:
        """Rozpoczyna wykonanie zadania"""
        self.set_data('status', 'running')
        self.set_data('started_at', datetime.now().isoformat())
        await self.save()

    async def update_progress(self, progress: int) -> None:
        """Aktualizuje postęp zadania"""
        self.set_data('progress', max(0, min(100, progress)))
        self.set_data('last_progress_update', datetime.now().isoformat())
        await self.save()

    async def complete_task(self, results: Dict[str, Any] = None) -> None:
        """Kończy zadanie jako zakończone"""
        self.set_data('status', 'completed')
        self.set_data('completed_at', datetime.now().isoformat())
        self.set_data('progress', 100)

        if results:
            self.set_data('results', results)

        await self.save()

    async def fail_task(self, error: str = '') -> None:
        """Kończy zadanie jako nieudane"""
        self.set_data('status', 'failed')
        self.set_data('failed_at', datetime.now().isoformat())
        self.set_data('error', error)
        await self.save()

class ComponentBeing(PrimitiveBeing):
    """
    Byt reprezentujący komponent interfejsu
    """

    def __init__(self):
        super().__init__("component")
        self.set_data('component_type', 'generic')
        self.set_data('properties', {})
        self.set_data('children', [])

    async def set_component_type(self, component_type: str) -> None:
        """Ustawia typ komponentu"""
        self.set_data('component_type', component_type)
        await self.save()

    async def set_property(self, key: str, value: Any) -> None:
        """Ustawia właściwość komponentu"""
        properties = self.get_data('properties', {})
        properties[key] = value
        self.set_data('properties', properties)
        await self.save()

    async def add_child(self, child_ulid: str) -> None:
        """Dodaje dziecko do komponentu"""
        children = self.get_data('children', [])
        if child_ulid not in children:
            children.append(child_ulid)
            self.set_data('children', children)
            await self.save()

    async def remove_child(self, child_ulid: str) -> None:
        """Usuwa dziecko z komponentu"""
        children = self.get_data('children', [])
        if child_ulid in children:
            children.remove(child_ulid)
            self.set_data('children', children)
            await self.save()

# Factory do tworzenia prymitywnych bytów
class PrimitiveBeingFactory:
    """
    Factory do tworzenia różnych typów prymitywnych bytów
    """

    BEING_TYPES = {
        'data': DataBeing,
        'function': FunctionBeing,
        'message': MessageBeing,
        'task': TaskBeing,
        'component': ComponentBeing,
        'primitive': PrimitiveBeing
    }

    @classmethod
    async def create_being(cls, being_type: str, **kwargs) -> PrimitiveBeing:
        """
        Tworzy byt określonego typu

        Args:
            being_type: Typ bytu do utworzenia
            **kwargs: Parametry inicjalizacji

        Returns:
            Nowy byt
        """
        BeingClass = cls.BEING_TYPES.get(being_type, PrimitiveBeing)
        being = BeingClass()

        # Ustaw alias jeśli podany
        if 'alias' in kwargs:
            being.alias = kwargs.pop('alias')

        # Inicjalizuj z pozostałymi parametrami
        await being.initialize(**kwargs)

        return being

    @classmethod
    async def load_being(cls, ulid: str) -> Optional[PrimitiveBeing]:
        """
        Ładuje byt i tworzy odpowiednią instancję na podstawie typu

        Args:
            ulid: ULID bytu

        Returns:
            Byt lub None jeśli nie znaleziono
        """
        being = await Being.load_by_ulid(ulid)
        if not being:
            return None

        # Określ typ bytu
        being_type = being.get_data('type', 'primitive')
        BeingClass = cls.BEING_TYPES.get(being_type, PrimitiveBeing)

        # Utwórz instancję odpowiedniej klasy
        typed_being = BeingClass()
        typed_being.ulid = being.ulid
        typed_being.soul_hash = being.soul_hash
        typed_being.alias = being.alias
        typed_being.data = being.data
        typed_being.vector_embedding = being.vector_embedding
        typed_being.table_type = being.table_type
        typed_being.created_at = being.created_at
        typed_being.updated_at = being.updated_at

        return typed_being
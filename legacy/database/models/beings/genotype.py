# app_v2/beings/genotype.py
"""
Genotype class with communication system and clean architecture
"""

import asyncio
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from database.models.base import Being
from core.communication import Communication, IntentRecognizer
from services.entity_manager import EntityManager
from database.soul_repository import SoulRepository

class Genotype(Being):
    """
    Genotype class that extends the Being class.
    Skupia się na logice biznesowej, deleguje operacje DB do serwisów.
    """
    loaded_genes: Optional[List[str]] = []
    cxt: Dict[str, Any] = {}
    local_cxt: Dict[str, Any] = {}

    async def execute(self, content: Any, sender_uid: str = None, metadata: Dict[str, Any] = None) -> Any:
        """
        Uniwersalna funkcja wykonania - punkt wejścia dla wszystkich komunikacji
        """
        # Twórz wiadomość
        message = Communication.create_message(
            sender_uid or "system", 
            content, 
            "execute", 
            metadata
        )
        
        # Rozpoznaj intencję
        intent = IntentRecognizer.recognize_intent(content)
        print(f"🎯 Rozpoznana intencja: {intent}")
        
        # Zapisz w pamięci komunikację
        self.remember(f"message_{message['id']}", message)
        
        try:
            # Dispatch na podstawie intencji
            if intent == "create_entity":
                return await self._handle_create_entity(content, message)
            elif intent == "load_entity":
                return await self._handle_load_entity(content, message)
            elif intent == "execute_function":
                return await self._handle_execute_function(content, message)
            elif intent == "query_data":
                return await self._handle_query_data(content, message)
            elif intent == "communicate":
                return await self._handle_communicate(content, message)
            else:
                return await self._handle_unknown_intent(content, message)
                
        except Exception as e:
            error_msg = f"❌ Błąd podczas wykonywania intencji {intent}: {e}"
            print(error_msg)
            self.remember("last_error", {"error": str(e), "intent": intent, "content": content})
            return {"error": error_msg, "success": False}

    @classmethod
    async def send_genotype_to_db(cls, soul: Dict):
        """Zapisuje genotyp do bazy danych (delegacja do repository)"""
        return await SoulRepository.save(soul)
    
    async def load_and_run_genotype(self, genotype_name: str, call_init: bool = True):
        """Ładuje i uruchamia genotyp używając serwisu"""
        from app_v2.services.genotype_service import GenotypeService
        try:
            # Przygotuj kontekst dla genotypu
            execution_context = {
                **self.cxt,
                'entity': self,
                'entity_name': self.genesis.get('name', 'Unknown'),
                'entity_uid': self.uid,
                'log': self.log,
                'remember': self.remember,
                'recall': self.recall,
            }
            
            # Deleguj do serwisu
            genotype_module = await GenotypeService.load_and_execute(
                genotype_name, 
                execution_context, 
                call_init
            )
            
            if genotype_module:
                # Zapisz w kontekście bytu
                self.cxt[genotype_name] = genotype_module
                print(f"✅ Genotyp {genotype_name} załadowany do kontekstu bytu")
            
            return genotype_module
        except Exception as e:
            print(f"❌ Błąd podczas ładowania genotypu {genotype_name}: {e}")
            return None

    # Handler methods for different intents
    async def _handle_create_entity(self, content: Any, message: Dict) -> Dict[str, Any]:
        """Obsługuje tworzenie nowych bytów"""
        if isinstance(content, dict):
            alias = content.get("alias", f"entity_{str(uuid.uuid4())[:8]}")
            template = content.get("template", "basic_entity")
            force_new = content.get("force_new", False)
            version = content.get("version", "latest")
        else:
            # Prosta komenda tekstowa: "create new logger"
            parts = str(content).split()
            alias = parts[-1] if len(parts) > 2 else f"entity_{str(uuid.uuid4())[:8]}"
            template = "basic_entity"
            force_new = "new" in str(content).lower()
            version = "latest"
        
        print(f"🆕 Tworzenie bytu: alias={alias}, template={template}, force_new={force_new}")
        
        entity = await EntityManager.create_or_load(alias, template, force_new, version)
        
        if entity:
            # Ustanów relację z nowo utworzonym bytem
            await Relationship.create(
                source_uid=self.uid,
                target_uid=entity.uid,
                attributes={"type": "created", "timestamp": datetime.now().isoformat()}
            )
            
            return {
                "success": True,
                "entity_uid": entity.uid,
                "alias": alias,
                "template": template,
                "message": f"Utworzono byt {alias}"
            }
        else:
            return {
                "success": False,
                "message": f"Nie udało się utworzyć bytu {alias}"
            }

    async def _handle_load_entity(self, content: Any, message: Dict) -> Dict[str, Any]:
        """Obsługuje ładowanie istniejących bytów"""
        if isinstance(content, dict):
            alias = content.get("alias")
        else:
            # "load entity logger" -> alias = "logger"
            parts = str(content).split()
            alias = parts[-1] if len(parts) >= 2 else None
        
        if not alias:
            return {"success": False, "message": "Nie podano aliasu do załadowania"}
        
        entity = await EntityManager.create_or_load(alias, force_new=False)
        
        if entity:
            return {
                "success": True,
                "entity_uid": entity.uid,
                "alias": alias,
                "message": f"Załadowano byt {alias}"
            }
        else:
            return {
                "success": False,
                "message": f"Nie znaleziono bytu {alias}"
            }

    async def _handle_execute_function(self, content: Any, message: Dict) -> Dict[str, Any]:
        """Obsługuje wykonywanie funkcji w kontekście bytu"""
        if isinstance(content, dict):
            function_name = content.get("function")
            args = content.get("args", [])
            kwargs = content.get("kwargs", {})
        else:
            # "execute log hello world" -> function="log", args=["hello", "world"]
            parts = str(content).split()
            function_name = parts[1] if len(parts) > 1 else None
            args = parts[2:] if len(parts) > 2 else []
            kwargs = {}
        
        if not function_name:
            return {"success": False, "message": "Nie podano nazwy funkcji"}
        
        # Szukaj funkcji w załadowanych genotypach
        for genotype_name, genotype_module in self.cxt.items():
            if hasattr(genotype_module, function_name):
                func = getattr(genotype_module, function_name)
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    return {
                        "success": True,
                        "result": result,
                        "function": function_name,
                        "genotype": genotype_name
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "function": function_name
                    }
        
        return {
            "success": False,
            "message": f"Nie znaleziono funkcji {function_name}"
        }

    async def _handle_query_data(self, content: Any, message: Dict) -> Dict[str, Any]:
        """Obsługuje zapytania o dane"""
        return {
            "success": True,
            "message": "Query handler not implemented yet",
            "data": {}
        }

    async def _handle_communicate(self, content: Any, message: Dict) -> Dict[str, Any]:
        """Obsługuje komunikację z innymi bytami"""
        if isinstance(content, dict):
            target_alias = content.get("target")
            msg_content = content.get("message")
        else:
            # "send to logger hello" -> target="logger", message="hello"
            parts = str(content).split()
            if "to" in parts:
                to_index = parts.index("to")
                target_alias = parts[to_index + 1] if to_index + 1 < len(parts) else None
                msg_content = " ".join(parts[to_index + 2:]) if to_index + 2 < len(parts) else ""
            else:
                return {"success": False, "message": "Nieprawidłowy format komunikacji"}
        
        if not target_alias or not msg_content:
            return {"success": False, "message": "Brak celu lub treści wiadomości"}
        
        # Znajdź docelowy byt
        target_entity = await EntityManager.create_or_load(target_alias, force_new=False)
        
        if target_entity:
            # Wyślij wiadomość do docelowego bytu
            response = await target_entity.execute(msg_content, self.uid)
            
            # Zapisz komunikację w relacjach
            await Relationship.create(
                source_uid=self.uid,
                target_uid=target_entity.uid,
                attributes={
                    "type": "communication",
                    "message": msg_content,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "success": True,
                "target": target_alias,
                "message": msg_content,
                "response": response
            }
        else:
            return {
                "success": False,
                "message": f"Nie znaleziono bytu {target_alias}"
            }

    async def _handle_unknown_intent(self, content: Any, message: Dict) -> Dict[str, Any]:
        """Obsługuje nierozpoznane intencje"""
        print(f"🤔 Nierozpoznana intencja dla: {content}")
        
        return {
            "success": False,
            "message": f"Nie rozumiem polecenia: {content}",
            "suggestion": "Spróbuj: create/load/execute/send/query"
        }

    def log(self, message: str, level: str = "INFO"):
        """Metoda logowania specyficzna dla bytu"""
        entity_name = self.genesis.get('name', self.uid[:8])
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] [Entity:{entity_name}] {message}")
        
        # Zapisz do memories
        self.remember('last_log', {
            'message': message,
            'level': level,
            'timestamp': timestamp
        })

    def remember(self, key: str, value: Any):
        """Zapisuje informację w pamięci bytu"""
        if not isinstance(self.memories, list):
            self.memories = []
        
        # Znajdź istniejący wpis lub dodaj nowy
        for memory in self.memories:
            if isinstance(memory, dict) and memory.get('key') == key:
                memory['value'] = value
                memory['updated_at'] = datetime.now().isoformat()
                return
        
        # Dodaj nowy wpis
        self.memories.append({
            'key': key,
            'value': value,
            'created_at': datetime.now().isoformat()
        })

    def recall(self, key: str) -> Any:
        """Odzyskuje informację z pamięci bytu"""
        if not isinstance(self.memories, list):
            return None
        
        for memory in self.memories:
            if isinstance(memory, dict) and memory.get('key') == key:
                return memory.get('value')
        return None
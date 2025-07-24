
import json
import uuid
from datetime import datetime
from app.beings.base import Being, Relationship
from app.beings.being_factory import BeingFactory
from app.beings.function_router import FunctionRouter
from app.beings.function_being import FunctionBeing
from app.beings.class_being import ClassBeing
from app.beings.data_being import DataBeing
from app.beings.scenario_being import ScenarioBeing
from app.beings.task_being import TaskBeing
from app.beings.component_being import ComponentBeing
from app.beings.message_being import MessageBeing




class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)
    
__all__ = [
    'Being',
    'BeingFactory',
    'Relationship',
    'DateTimeEncoder',
    'FunctionRouter',
    'FunctionBeing',
    'ClassBeing',
    'DataBeing',
    'ScenarioBeing',
    'TaskBeing',
    'ComponentBeing',
    'MessageBeing',
]
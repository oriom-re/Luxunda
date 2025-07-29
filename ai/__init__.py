# app_v2/ai/__init__.py
"""
AI module for LuxOS - Brain, OpenAI integration, and function calling
"""

from .ai_brain import AIBrain
from .openai_integration import OpenAIIntegration, MockOpenAI
from .hybrid_ai_system import HybridAISystem

try:
    from .openai_function_caller import OpenAIFunctionCaller
    OPENAI_FUNCTION_CALLER_AVAILABLE = True
except ImportError:
    OPENAI_FUNCTION_CALLER_AVAILABLE = False
    OpenAIFunctionCaller = None

__all__ = [
    'AIBrain',
    'OpenAIIntegration', 
    'MockOpenAI',
    'HybridAISystem'
]

if OPENAI_FUNCTION_CALLER_AVAILABLE:
    __all__.append('OpenAIFunctionCaller')

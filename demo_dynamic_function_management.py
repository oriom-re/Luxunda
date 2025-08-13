
#!/usr/bin/env python3
"""
🔧 Demo: Dynamic Function Management System
Pokazuje jak Master Function Being może dodawać sobie nowe funkcje jako atrybuty
i wykonywać je przez OpenAI + Kernel.
"""

import asyncio
from datetime import datetime
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.postgre_db import Postgre_db

async def main():
    print("🔧 DEMO: Dynamic Function Management System")
    print("=" * 60)

    # Inicjalizacja bazy danych
    await Postgre_db.initialize()

    # 1. Utwórz Soul dla Master Function Being
    master_genotype = {
        "genesis": {
            "name": "dynamic_function_master",
            "type": "master_function_soul",
            "version": "1.0.0",
            "description": "Master Being that can add and manage dynamic functions"
        },
        "attributes": {
            "name": {"py_type": "str", "default": "Dynamic Function Master"}
        },
        "module_source": '''
def init(being_context=None):
    """Initialize dynamic function master"""
    print(f"🔧 Dynamic Function Master initialized: {being_context.get('alias', 'unknown')}")
    return {
        "ready": True, 
        "suggested_persistence": True,
        "capabilities": ["add_functions", "execute_functions", "manage_functions"]
    }

def execute(request=None, being_context=None, **kwargs):
    """Main execution handler"""
    if isinstance(request, dict) and 'action' in request:
        action = request['action']
        
        if action == 'suggest_new_function':
            return suggest_new_function(request, being_context)
        elif action == 'analyze_capabilities':
            return analyze_current_capabilities(being_context)
    
    return {
        "status": "ready",
        "message": "Dynamic Function Master is ready to manage functions",
        "capabilities": ["add_functions", "execute_functions", "manage_functions"]
    }

def suggest_new_function(request, being_context):
    """Suggests adding a new function based on context"""
    domain = request.get('domain', 'general')
    
    suggestions = {
        'math': {
            'name': 'advanced_calculation',
            'description': 'Performs advanced mathematical calculations',
            'parameters': {
                'type': 'object',
                'properties': {
                    'operation': {'type': 'string', 'description': 'Type of calculation'},
                    'values': {'type': 'array', 'description': 'Values to calculate'}
                },
                'required': ['operation', 'values']
            }
        },
        'text': {
            'name': 'text_analysis',
            'description': 'Analyzes text for sentiment, keywords, etc.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'text': {'type': 'string', 'description': 'Text to analyze'},
                    'analysis_type': {'type': 'string', 'description': 'Type of analysis'}
                },
                'required': ['text']
            }
        }
    }
    
    suggestion = suggestions.get(domain, suggestions['math'])
    
    return {
        "suggested_function": suggestion,
        "domain": domain,
        "ready_to_add": True
    }

def analyze_current_capabilities(being_context):
    """Analyzes current function capabilities"""
    dynamic_functions = being_context.get('data', {}).get('_dynamic_functions', {})
    managed_functions = being_context.get('data', {}).get('_managed_functions', [])
    
    return {
        "total_functions": len(managed_functions),
        "dynamic_functions": len(dynamic_functions),
        "function_domains": list(set([
            f.get('definition', {}).get('domain', 'general') 
            for f in dynamic_functions.values()
        ])),
        "recommendations": ["Consider adding text processing functions", "Math functions could be enhanced"]
    }
'''
    }

    print("1. Creating Dynamic Function Master Soul...")
    master_soul = await Soul.create(master_genotype, "dynamic_function_master_soul")
    print(f"✅ Created Soul: {master_soul.alias}")

    # 2. Utwórz Master Function Being
    print("\n2. Creating Master Function Being...")
    master_being = await Being.create(
        master_soul,
        alias="function_master",
        attributes={"domain": "dynamic_functions"}
    )
    print(f"✅ Created Master Being: {master_being.alias}")
    print(f"   Is Function Master: {master_being.is_function_master()}")

    # 3. Master Being dodaje sobie nowe funkcje dynamicznie
    print("\n3. Master Being adds dynamic functions...")
    
    # Dodaj funkcję matematyczną
    math_function = {
        "description": "Calculates complex mathematical expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Mathematical expression"},
                "precision": {"type": "integer", "description": "Decimal precision"}
            },
            "required": ["expression"]
        },
        "domain": "mathematics"
    }
    
    result1 = await master_being.add_dynamic_function("calculate_expression", math_function, "self_enhancement")
    print(f"   Math function added: {result1.get('success', False)}")
    
    # Dodaj funkcję analizy tekstu
    text_function = {
        "description": "Analyzes text sentiment and extracts keywords",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyze"},
                "extract_keywords": {"type": "boolean", "description": "Whether to extract keywords"}
            },
            "required": ["text"]
        },
        "domain": "nlp"
    }
    
    result2 = await master_being.add_dynamic_function("analyze_text", text_function, "user_request")
    print(f"   Text function added: {result2.get('success', False)}")

    # 4. Sprawdź informacje o funkcjach
    print("\n4. Function Mastery Info:")
    mastery_info = master_being.get_function_mastery_info()
    print(f"   Total managed functions: {mastery_info['function_count']}")
    print(f"   Dynamic functions: {mastery_info['dynamic_functions']['count']}")
    print(f"   Dynamic function names: {mastery_info['dynamic_functions']['functions']}")

    # 5. Wykonaj dynamiczne funkcje przez OpenAI simulation
    print("\n5. Executing dynamic functions...")
    
    # Wykonaj funkcję matematyczną
    math_result = await master_being.execute_soul_function(
        "calculate_expression",
        expression="2^10 + sqrt(144)",
        precision=2
    )
    print(f"   Math execution: {math_result.get('success', False)}")
    if math_result.get('success'):
        print(f"   Result: {math_result['data']['result']}")

    # Wykonaj funkcję analizy tekstu
    text_result = await master_being.execute_soul_function(
        "analyze_text",
        text="This is a wonderful day for AI development!",
        extract_keywords=True
    )
    print(f"   Text analysis: {text_result.get('success', False)}")
    if text_result.get('success'):
        print(f"   Result: {text_result['data']['result']}")

    # 6. Master Being proponuje nową funkcję
    print("\n6. Master Being suggests new function...")
    suggestion_result = await master_being.execute_soul_function(
        "execute",
        request={"action": "suggest_new_function", "domain": "text"}
    )
    
    if suggestion_result.get('success'):
        suggestion = suggestion_result['data']['suggested_function']
        print(f"   Suggested function: {suggestion['name']}")
        print(f"   Description: {suggestion['description']}")
        
        # Automatycznie dodaj zasugerowaną funkcję
        result3 = await master_being.add_dynamic_function(
            suggestion['name'], 
            suggestion, 
            "self_suggestion"
        )
        print(f"   Auto-added suggested function: {result3.get('success', False)}")

    # 7. Finalna analiza możliwości
    print("\n7. Final capability analysis:")
    analysis_result = await master_being.execute_soul_function(
        "execute",
        request={"action": "analyze_capabilities"}
    )
    
    if analysis_result.get('success'):
        analysis = analysis_result['data']
        print(f"   Total functions: {analysis['total_functions']}")
        print(f"   Dynamic functions: {analysis['dynamic_functions']}")
        print(f"   Function domains: {analysis['function_domains']}")
        print(f"   Recommendations: {analysis['recommendations']}")

    # 8. Pokaż pełne statystyki
    print("\n8. Complete statistics:")
    final_mastery = master_being.get_function_mastery_info()
    print(f"   Final function count: {final_mastery['function_count']}")
    print(f"   Dynamic functions executed: {final_mastery['dynamic_functions']['total_executions']}")
    print(f"   Enabled functions: {final_mastery['dynamic_functions']['enabled_count']}")

if __name__ == "__main__":
    asyncio.run(main())

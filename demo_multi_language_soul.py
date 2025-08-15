
#!/usr/bin/env python3
"""
Demo wielojęzycznych Soul - JavaScript i Python w jednej Soul
"""

import asyncio
from luxdb.models.soul import Soul

async def demo_javascript_soul():
    """Demo Soul z kodem JavaScript"""
    print("🚀 Demo JavaScript Soul")
    
    # Soul z kodem JavaScript
    js_genotype = {
        "genesis": {
            "name": "javascript_calculator",
            "type": "calculator",
            "version": "1.0.0",
            "language": "javascript"
        },
        "attributes": {
            "last_result": {"py_type": "float", "default": 0.0}
        },
        "module_source": """
function calculate(a, b, operation) {
    switch(operation) {
        case 'add':
            return a + b;
        case 'subtract':
            return a - b;
        case 'multiply':
            return a * b;
        case 'divide':
            return b !== 0 ? a / b : 'Division by zero';
        default:
            return 'Unknown operation';
    }
}

function init(context) {
    console.log('JavaScript calculator initialized');
    return { success: true, message: 'JS Calculator ready' };
}

const factorial = (n) => {
    return n <= 1 ? 1 : n * factorial(n - 1);
}
"""
    }
    
    # Utwórz Soul
    js_soul = await Soul.create(js_genotype, alias="js_calculator")
    print(f"✅ Created JavaScript Soul: {js_soul.alias}")
    print(f"   Language: {js_soul.get_language()}")
    print(f"   Functions: {js_soul.list_functions()}")
    
    # Test wykonania bezpośrednio przez Soul
    if js_soul.can_execute_directly():
        result = await js_soul.execute_directly("calculate", 10, 5, "add")
        print(f"📊 JavaScript calculation result: {result}")
    
    return js_soul

async def demo_multi_language_soul():
    """Demo Soul z kodem wielojęzycznym"""
    print("\n🌍 Demo Multi-Language Soul")
    
    # Soul z kodem Python i JavaScript
    multi_genotype = {
        "genesis": {
            "name": "hybrid_processor",
            "type": "data_processor",
            "version": "1.0.0",
            "language": "multi"
        },
        "attributes": {
            "processed_count": {"py_type": "int", "default": 0}
        },
        "module_source": """
```python
import json
import datetime

def process_data(data):
    \"\"\"Process data using Python\"\"\"
    if isinstance(data, dict):
        data['processed_at'] = datetime.datetime.now().isoformat()
        data['processed_by'] = 'python'
    return data

def validate_json(json_string):
    \"\"\"Validate JSON using Python\"\"\"
    try:
        json.loads(json_string)
        return True
    except:
        return False

def init(context):
    return {"success": True, "python_ready": True}
```

```javascript
function formatData(data, format) {
    // Format data using JavaScript
    if (format === 'uppercase') {
        return JSON.stringify(data).toUpperCase();
    } else if (format === 'pretty') {
        return JSON.stringify(data, null, 2);
    }
    return JSON.stringify(data);
}

function calculateStats(numbers) {
    // Calculate statistics using JavaScript
    const sum = numbers.reduce((a, b) => a + b, 0);
    const avg = sum / numbers.length;
    const min = Math.min(...numbers);
    const max = Math.max(...numbers);
    
    return { sum, avg, min, max, count: numbers.length };
}
```
"""
    }
    
    # Utwórz Soul
    multi_soul = await Soul.create(multi_genotype, alias="hybrid_processor")
    print(f"✅ Created Multi-Language Soul: {multi_soul.alias}")
    print(f"   Language: {multi_soul.get_language()}")
    print(f"   Functions: {multi_soul.list_functions()}")
    
    # Test funkcji Python
    test_data = {"name": "test", "value": 123}
    result1 = await multi_soul.execute_directly("process_data", test_data)
    print(f"🐍 Python processing result: {result1}")
    
    # Test funkcji JavaScript
    numbers = [1, 2, 3, 4, 5]
    result2 = await multi_soul.execute_directly("calculateStats", numbers)
    print(f"🟨 JavaScript stats result: {result2}")
    
    return multi_soul

async def demo_language_compatibility():
    """Demo kompatybilności języków"""
    print("\n🔄 Demo Language Compatibility")
    
    # Utwórz różne Soul
    python_soul = await Soul.create({
        "genesis": {"name": "py_worker", "language": "python"},
        "module_source": "def work(): return 'Python working'"
    }, "py_worker")
    
    js_soul = await Soul.create({
        "genesis": {"name": "js_worker", "language": "javascript"},
        "module_source": "function work() { return 'JavaScript working'; }"
    }, "js_worker")
    
    # Test kompatybilności
    print(f"Python Soul can execute Python: {python_soul.is_executable_in_language('python')}")
    print(f"Python Soul can execute JavaScript: {python_soul.is_executable_in_language('javascript')}")
    print(f"JS Soul can execute JavaScript: {js_soul.is_executable_in_language('javascript')}")
    print(f"JS Soul can execute Python: {js_soul.is_executable_in_language('python')}")

async def main():
    """Main demo function"""
    print("🧬 Multi-Language Soul Execution Demo")
    print("=" * 50)
    
    try:
        # Demo JavaScript Soul
        js_soul = await demo_javascript_soul()
        
        # Demo Multi-Language Soul  
        multi_soul = await demo_multi_language_soul()
        
        # Demo kompatybilności
        await demo_language_compatibility()
        
        print("\n✅ All demos completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

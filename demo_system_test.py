
#!/usr/bin/env python3
"""
🌟 LuxOS v1.0.0 - System Demonstration
======================================

Demonstracja kluczowych funkcji systemu LuxOS:
- Soul/Being creation and management
- Function execution
- Hash-based security
- Multi-language support
- Being ownership management
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from luxdb.core.luxdb import LuxDB
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.being_ownership_manager import being_ownership_manager

class LuxOSDemo:
    """Comprehensive LuxOS system demonstration"""
    
    def __init__(self):
        self.db = None
        self.demo_results = []
        
    async def initialize(self):
        """Initialize LuxOS system"""
        print("🌟 LuxOS v1.0.0 System Demonstration")
        print("=" * 50)
        
        # Initialize database
        self.db = LuxDB(use_existing_pool=True)
        await self.db.initialize()
        
        health = await self.db.health_check()
        print(f"📊 Database Status: {health['status']}")
        print(f"💾 Souls: {health['souls_count']}, Beings: {health['beings_count']}")
        print()
        
    async def demo_1_basic_soul_creation(self):
        """Demo 1: Basic Soul creation with Python code"""
        print("🧬 Demo 1: Soul Creation with Python Module")
        print("-" * 40)
        
        # Create a simple calculator Soul
        calculator_genotype = {
            "genesis": {
                "name": "calculator",
                "type": "utility",
                "version": "1.0.0",
                "description": "Simple calculator with basic operations",
                "language": "python"
            },
            "module_source": """
def add(a, b):
    \"\"\"Add two numbers\"\"\"
    return a + b

def multiply(a, b):
    \"\"\"Multiply two numbers\"\"\"
    return a * b

def calculate_compound_interest(principal, rate, time):
    \"\"\"Calculate compound interest\"\"\"
    return principal * (1 + rate) ** time

def execute(request=None, **kwargs):
    \"\"\"Main execution function\"\"\"
    if not request:
        return {"result": "Calculator ready", "operations": ["add", "multiply", "calculate_compound_interest"]}
    
    action = request.get("action", "info")
    
    if action == "add":
        a = request.get("a", 0)
        b = request.get("b", 0)
        return {"result": add(a, b), "operation": f"{a} + {b}"}
    
    elif action == "multiply":
        a = request.get("a", 1)
        b = request.get("b", 1)
        return {"result": multiply(a, b), "operation": f"{a} * {b}"}
    
    elif action == "compound_interest":
        principal = request.get("principal", 1000)
        rate = request.get("rate", 0.05)
        time = request.get("time", 1)
        result = calculate_compound_interest(principal, rate, time)
        return {
            "result": result,
            "calculation": f"${principal} at {rate*100}% for {time} years = ${result:.2f}"
        }
    
    return {"error": "Unknown action", "available_actions": ["add", "multiply", "compound_interest"]}
"""
        }
        
        # Create Soul
        calculator_soul = await Soul.create(calculator_genotype, "calculator")
        print(f"✅ Created Calculator Soul: {calculator_soul.soul_hash[:16]}...")
        
        # Test direct Soul execution (no Being needed for simple calculations)
        result1 = await calculator_soul.execute_directly("add", a=15, b=25)
        print(f"🧮 Direct execution add(15, 25): {result1['data']['result']}")
        
        # Test execute function with request
        result2 = await calculator_soul.execute_directly("execute", request={"action": "multiply", "a": 12, "b": 8})
        print(f"🧮 Execute function multiply(12, 8): {result2['data']['result']['result']}")
        
        self.demo_results.append({
            "demo": "soul_creation",
            "soul_hash": calculator_soul.soul_hash,
            "functions_count": calculator_soul.get_functions_count(),
            "results": [result1, result2]
        })
        
        print()
        return calculator_soul
        
    async def demo_2_being_with_data(self):
        """Demo 2: Being creation with persistent data"""
        print("🤖 Demo 2: Being Creation with Persistent Data")
        print("-" * 40)
        
        # Create a Bank Account Soul that manages financial data
        bank_account_genotype = {
            "genesis": {
                "name": "bank_account",
                "type": "financial",
                "version": "1.0.0",
                "description": "Bank account management system",
                "language": "python"
            },
            "attributes": {
                "account_number": {"py_type": "str", "description": "Unique account number"},
                "balance": {"py_type": "float", "default": 0.0, "description": "Current balance"},
                "currency": {"py_type": "str", "default": "USD", "description": "Account currency"},
                "transactions": {"py_type": "list", "default": [], "description": "Transaction history"},
                "account_type": {"py_type": "str", "default": "checking", "description": "Type of account"}
            },
            "module_source": """
from datetime import datetime

def init(being_context=None):
    \"\"\"Initialize bank account\"\"\"
    if not being_context:
        return {"success": False, "error": "No being context provided"}
    
    account_data = being_context.get('data', {})
    account_number = account_data.get('account_number')
    
    if not account_number:
        # Generate account number if not provided
        import random
        account_number = f"ACC{random.randint(100000, 999999)}"
    
    return {
        "success": True,
        "message": f"Bank account {account_number} initialized",
        "data": {
            "account_number": account_number,
            "balance": account_data.get('balance', 1000.0),  # Starting balance
            "currency": account_data.get('currency', 'USD'),
            "transactions": [],
            "created_at": datetime.now().isoformat(),
            "suggested_persistence": True  # This Being should be persistent
        }
    }

def deposit(amount, description="Deposit", being_context=None):
    \"\"\"Deposit money to account\"\"\"
    if amount <= 0:
        return {"success": False, "error": "Amount must be positive"}
    
    current_balance = being_context.get('data', {}).get('balance', 0)
    new_balance = current_balance + amount
    
    transaction = {
        "type": "deposit",
        "amount": amount,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "balance_after": new_balance
    }
    
    # Update data in being_context (will be saved automatically)
    being_context['data']['balance'] = new_balance
    if 'transactions' not in being_context['data']:
        being_context['data']['transactions'] = []
    being_context['data']['transactions'].append(transaction)
    
    return {
        "success": True,
        "transaction": transaction,
        "new_balance": new_balance
    }

def withdraw(amount, description="Withdrawal", being_context=None):
    \"\"\"Withdraw money from account\"\"\"
    current_balance = being_context.get('data', {}).get('balance', 0)
    
    if amount <= 0:
        return {"success": False, "error": "Amount must be positive"}
    
    if amount > current_balance:
        return {"success": False, "error": "Insufficient funds"}
    
    new_balance = current_balance - amount
    
    transaction = {
        "type": "withdrawal", 
        "amount": amount,
        "description": description,
        "timestamp": datetime.now().isoformat(),
        "balance_after": new_balance
    }
    
    # Update data
    being_context['data']['balance'] = new_balance
    being_context['data']['transactions'].append(transaction)
    
    return {
        "success": True,
        "transaction": transaction,
        "new_balance": new_balance
    }

def get_balance(being_context=None):
    \"\"\"Get current balance\"\"\"
    return {
        "balance": being_context.get('data', {}).get('balance', 0),
        "currency": being_context.get('data', {}).get('currency', 'USD'),
        "account_number": being_context.get('data', {}).get('account_number')
    }

def execute(request=None, being_context=None, **kwargs):
    \"\"\"Main execution function for bank operations\"\"\"
    if not request:
        return {
            "status": "ready",
            "account_info": get_balance(being_context),
            "available_operations": ["deposit", "withdraw", "get_balance", "get_statement"]
        }
    
    action = request.get("action")
    
    if action == "deposit":
        return deposit(request.get("amount", 0), request.get("description", "Deposit"), being_context)
    elif action == "withdraw":
        return withdraw(request.get("amount", 0), request.get("description", "Withdrawal"), being_context)
    elif action == "get_balance":
        return get_balance(being_context)
    elif action == "get_statement":
        transactions = being_context.get('data', {}).get('transactions', [])
        return {
            "account_info": get_balance(being_context),
            "transaction_count": len(transactions),
            "recent_transactions": transactions[-5:]  # Last 5 transactions
        }
    
    return {"error": "Unknown action", "available_actions": ["deposit", "withdraw", "get_balance", "get_statement"]}
"""
        }
        
        # Create Bank Account Soul
        bank_soul = await Soul.create(bank_account_genotype, "bank_account")
        print(f"✅ Created Bank Account Soul: {bank_soul.soul_hash[:16]}...")
        
        # Create Bank Account Being with initial data
        initial_data = {
            "account_number": "ACC123456",
            "balance": 1500.0,
            "currency": "USD",
            "account_type": "premium_checking"
        }
        
        bank_being = await Being.create(bank_soul, attributes=initial_data, alias="john_doe_account")
        print(f"✅ Created Bank Account Being: {bank_being.alias} ({bank_being.ulid[:8]}...)")
        
        # Test banking operations
        print("\n💰 Testing Banking Operations:")
        
        # Deposit
        deposit_result = await bank_being.execute_soul_function("execute", 
                                                               request={"action": "deposit", "amount": 500, "description": "Salary deposit"})
        print(f"   💳 Deposit $500: New balance ${deposit_result['data']['result']['new_balance']}")
        
        # Withdraw
        withdraw_result = await bank_being.execute_soul_function("execute",
                                                                request={"action": "withdraw", "amount": 200, "description": "ATM withdrawal"})
        print(f"   💸 Withdraw $200: New balance ${withdraw_result['data']['result']['new_balance']}")
        
        # Get statement
        statement_result = await bank_being.execute_soul_function("execute",
                                                                 request={"action": "get_statement"})
        statement = statement_result['data']['result']
        print(f"   📊 Account Statement: ${statement['account_info']['balance']} ({statement['transaction_count']} transactions)")
        
        # Register as resource master (Being Ownership Management)
        ownership_result = await being_ownership_manager.register_being_as_resource_master(
            bank_being.ulid, f"bank_account_{bank_being.alias}", "financial_account"
        )
        print(f"   🏛️ Ownership registered: {ownership_result['success']}")
        
        self.demo_results.append({
            "demo": "being_with_data",
            "being_ulid": bank_being.ulid,
            "soul_hash": bank_soul.soul_hash,
            "final_balance": statement['account_info']['balance'],
            "transaction_count": statement['transaction_count']
        })
        
        print()
        return bank_being
        
    async def demo_3_multi_language_soul(self):
        """Demo 3: Multi-language Soul with JavaScript"""
        print("🌐 Demo 3: Multi-Language Soul (Python + JavaScript)")
        print("-" * 40)
        
        # Multi-language Soul with both Python and JavaScript code
        multi_lang_genotype = {
            "genesis": {
                "name": "text_processor",
                "type": "nlp",
                "version": "1.0.0",
                "description": "Text processing utilities in multiple languages",
                "language": "multi"
            },
            "module_source": """
```python
import re
from collections import Counter

def analyze_text_python(text):
    \"\"\"Analyze text using Python\"\"\"
    words = re.findall(r'\w+', text.lower())
    word_count = len(words)
    unique_words = len(set(words))
    most_common = Counter(words).most_common(3)
    
    return {
        "language": "python",
        "word_count": word_count,
        "unique_words": unique_words,
        "most_common_words": most_common,
        "readability_score": unique_words / word_count if word_count > 0 else 0
    }

def execute(request=None, **kwargs):
    \"\"\"Execute text processing request\"\"\"
    if not request:
        return {"status": "ready", "available_functions": ["analyze_text"]}
    
    action = request.get("action")
    text = request.get("text", "")
    
    if action == "analyze_text":
        return analyze_text_python(text)
    
    return {"error": "Unknown action"}
```

```javascript
function processTextJavaScript(text) {
    // JavaScript text processing
    const words = text.toLowerCase().match(/\w+/g) || [];
    const wordCount = words.length;
    const uniqueWords = new Set(words).size;
    
    // Count word frequencies
    const wordFreq = {};
    words.forEach(word => {
        wordFreq[word] = (wordFreq[word] || 0) + 1;
    });
    
    // Get top 3 most common words
    const sortedWords = Object.entries(wordFreq)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 3);
    
    return {
        language: "javascript",
        wordCount: wordCount,
        uniqueWords: uniqueWords,
        mostCommonWords: sortedWords,
        averageWordLength: words.reduce((sum, word) => sum + word.length, 0) / wordCount || 0
    };
}

function execute(request) {
    if (!request) {
        return {status: "ready", language: "javascript"};
    }
    
    const action = request.action;
    const text = request.text || "";
    
    if (action === "process_text") {
        return processTextJavaScript(text);
    }
    
    return {error: "Unknown action"};
}
```
"""
        }
        
        # Create Multi-language Soul
        text_soul = await Soul.create(multi_lang_genotype, "text_processor")
        print(f"✅ Created Multi-Language Soul: {text_soul.soul_hash[:16]}...")
        print(f"   📊 Detected Functions: {text_soul.list_functions()}")
        
        # Test text analysis
        sample_text = "This is a sample text for analysis. This text contains several words, and some words repeat to test frequency analysis."
        
        # Execute Python function
        python_result = await text_soul.execute_directly("execute", 
                                                        request={"action": "analyze_text", "text": sample_text})
        print(f"   🐍 Python Analysis: {python_result['data']['result']['word_count']} words, {python_result['data']['result']['unique_words']} unique")
        
        self.demo_results.append({
            "demo": "multi_language_soul",
            "soul_hash": text_soul.soul_hash,
            "languages": ["python", "javascript"],
            "analysis_result": python_result['data']['result']
        })
        
        print()
        return text_soul
        
    async def demo_4_hash_security(self):
        """Demo 4: Hash-based security and immutability"""
        print("🔒 Demo 4: Hash-Based Security & Immutability")
        print("-" * 40)
        
        # Create two identical Souls - should have same hash
        genotype1 = {
            "genesis": {"name": "test", "version": "1.0.0"},
            "module_source": "def test(): return 'hello'"
        }
        
        genotype2 = {
            "genesis": {"name": "test", "version": "1.0.0"},
            "module_source": "def test(): return 'hello'"
        }
        
        soul1 = await Soul.create(genotype1, "test_soul_1")
        soul2 = await Soul.create(genotype2, "test_soul_2")
        
        print(f"   🧬 Soul 1 Hash: {soul1.soul_hash[:16]}...")
        print(f"   🧬 Soul 2 Hash: {soul2.soul_hash[:16]}...")
        print(f"   🔐 Hashes Match: {soul1.soul_hash == soul2.soul_hash}")
        print(f"   📊 Same Soul Returned: {soul1 is soul2}")
        
        # Create slightly different Soul - should have different hash
        genotype3 = {
            "genesis": {"name": "test", "version": "1.0.0"},
            "module_source": "def test(): return 'world'"  # Different return value
        }
        
        soul3 = await Soul.create(genotype3, "test_soul_3")
        print(f"   🧬 Soul 3 Hash: {soul3.soul_hash[:16]}... (different code)")
        print(f"   🔐 Hash Different: {soul1.soul_hash != soul3.soul_hash}")
        
        # Demonstrate evolution
        evolved_soul = await Soul.create_evolved_version(soul1, {
            "genesis.version": "1.1.0",
            "module_source": "def test(): return 'hello world'"
        })
        
        print(f"   🧬 Evolved Soul Hash: {evolved_soul.soul_hash[:16]}...")
        print(f"   📈 Evolution Chain: {soul1.soul_hash[:8]}... -> {evolved_soul.soul_hash[:8]}...")
        
        self.demo_results.append({
            "demo": "hash_security",
            "original_hash": soul1.soul_hash,
            "evolved_hash": evolved_soul.soul_hash,
            "evolution_verified": evolved_soul.get_parent_hash() == soul1.soul_hash
        })
        
        print()
        
    async def demo_5_ownership_management(self):
        """Demo 5: Being Ownership Management"""
        print("🏛️ Demo 5: Being Ownership & Resource Management")
        print("-" * 40)
        
        # Create a simple data processor Soul
        processor_genotype = {
            "genesis": {
                "name": "data_processor",
                "type": "utility",
                "version": "1.0.0"
            },
            "module_source": """
def process_data(data, being_context=None):
    \"\"\"Process some data\"\"\"
    return {"processed": len(data), "data_type": type(data).__name__}

def execute(request=None, being_context=None, **kwargs):
    if not request:
        return {"status": "ready"}
    return process_data(request.get("data", []), being_context)
"""
        }
        
        processor_soul = await Soul.create(processor_genotype, "data_processor")
        
        # Create master Being
        master_being = await Being.create(processor_soul, alias="data_master")
        print(f"   🎯 Created Master Being: {master_being.alias}")
        
        # Register as resource master
        resource_id = "shared_data_pool"
        ownership_result = await being_ownership_manager.register_being_as_resource_master(
            master_being.ulid, resource_id, "data_processing"
        )
        print(f"   ✅ Resource Registration: {ownership_result['success']}")
        
        # Create worker Being
        worker_being = await Being.create(processor_soul, alias="data_worker")
        print(f"   👷 Created Worker Being: {worker_being.alias}")
        
        # Worker requests access
        access_result = await being_ownership_manager.request_resource_access(
            worker_being.ulid, resource_id, "read", 30
        )
        print(f"   🔑 Access Request: {access_result.get('success', False)}")
        
        if access_result.get('success'):
            print(f"       Session ID: {access_result['session_id'][:16]}...")
            
            # Simulate some work
            work_result = await worker_being.execute_soul_function("execute", 
                                                                  request={"data": [1, 2, 3, 4, 5]})
            print(f"   🔧 Work Result: Processed {work_result['data']['result']['processed']} items")
            
            # Release access
            release_result = await being_ownership_manager.release_resource_access(
                worker_being.ulid, resource_id
            )
            print(f"   🔓 Access Released: {release_result['success']}")
        
        # System status
        status = being_ownership_manager.get_system_status()
        print(f"   📊 System Status: {status['total_resources']} resources, {status['active_sessions_count']} active sessions")
        
        self.demo_results.append({
            "demo": "ownership_management",
            "master_being": master_being.ulid,
            "worker_being": worker_being.ulid,
            "resource_id": resource_id,
            "system_status": status
        })
        
        print()
        
    async def demo_6_system_performance(self):
        """Demo 6: System Performance & Statistics"""
        print("📈 Demo 6: System Performance & Statistics")
        print("-" * 40)
        
        # Get current system state
        all_souls = await Soul.get_all()
        all_beings = await Being.get_all()
        
        # Calculate statistics
        total_souls = len(all_souls)
        total_beings = len(all_beings)
        
        # Function counts
        total_functions = sum(soul.get_functions_count() for soul in all_souls)
        
        # Language distribution
        language_dist = {}
        for soul in all_souls:
            lang = soul.get_language()
            language_dist[lang] = language_dist.get(lang, 0) + 1
        
        # Hash diversity (first 4 chars distribution)
        hash_prefixes = {}
        for soul in all_souls:
            prefix = soul.soul_hash[:4]
            hash_prefixes[prefix] = hash_prefixes.get(prefix, 0) + 1
        
        print(f"   📊 Total Souls: {total_souls}")
        print(f"   🤖 Total Beings: {total_beings}")
        print(f"   ⚙️ Total Functions: {total_functions}")
        print(f"   🌐 Languages: {dict(language_dist)}")
        print(f"   🔐 Hash Diversity: {len(hash_prefixes)} unique prefixes")
        
        # Database health
        health = await self.db.health_check()
        print(f"   💾 DB Status: {health['status']}")
        print(f"   🔗 Pool Size: {health.get('pool_size', 'unknown')}")
        
        self.demo_results.append({
            "demo": "system_performance",
            "total_souls": total_souls,
            "total_beings": total_beings,
            "total_functions": total_functions,
            "language_distribution": language_dist,
            "hash_diversity": len(hash_prefixes),
            "database_health": health
        })
        
        print()
        
    async def generate_demo_report(self):
        """Generate comprehensive demo report"""
        print("📋 Demo Summary Report")
        print("=" * 50)
        
        for i, result in enumerate(self.demo_results, 1):
            print(f"Demo {i}: {result['demo'].replace('_', ' ').title()}")
            if 'soul_hash' in result:
                print(f"   Hash: {result['soul_hash'][:16]}...")
            if 'being_ulid' in result:
                print(f"   Being: {result['being_ulid'][:8]}...")
            print()
        
        # Save detailed report
        report_data = {
            "demo_timestamp": datetime.now().isoformat(),
            "luxos_version": "1.0.0",
            "demo_results": self.demo_results,
            "system_summary": {
                "total_demos": len(self.demo_results),
                "successful_demos": len([r for r in self.demo_results if not r.get('error')]),
                "database_connected": True
            }
        }
        
        with open("demo_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print("✅ Demo completed successfully!")
        print("📄 Detailed report saved to: demo_report.json")
        print()
        
        return report_data

async def main():
    """Run complete LuxOS demonstration"""
    demo = LuxOSDemo()
    
    try:
        # Initialize system
        await demo.initialize()
        
        # Run all demonstrations
        await demo.demo_1_basic_soul_creation()
        await demo.demo_2_being_with_data()
        await demo.demo_3_multi_language_soul()
        await demo.demo_4_hash_security()
        await demo.demo_5_ownership_management()
        await demo.demo_6_system_performance()
        
        # Generate report
        await demo.generate_demo_report()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if demo.db:
            await demo.db.close()

if __name__ == "__main__":
    asyncio.run(main())

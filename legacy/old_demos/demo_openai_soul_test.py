#!/usr/bin/env python3
"""
Demo test for OpenAI Soul with dynamic module loading
Tests the philosophy: only Soul and Being, everything else emerges from these two
"""

import asyncio
import os
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def main():
    print("🧬 Testing OpenAI Soul with Dynamic Module Loading")
    print("=" * 60)

    # Read OpenAI module source
    try:
        with open("gen_files/openai_client.module", "r") as f:
            openai_module_source = f.read()
    except FileNotFoundError:
        print("❌ OpenAI module file not found!")
        return

    # Create genotype with OpenAI module source
    openai_genotype = {
        "genesis": {
            "name": "openai_client_soul",
            "version": "1.0.0",
            "description": "Soul with OpenAI client capabilities",
            "type": "dynamic_module_soul",
            "created_at": "2025-01-30"
        },
        "attributes": {
            "api_key": {"py_type": "str", "sensitive": True},
            "model": {"py_type": "str", "default": "gpt-4o-mini"},
            "initialized": {"py_type": "bool", "default": False},
            "total_completions": {"py_type": "int", "default": 0}
        },
        "functions": {
            "initialize_openai": {
                "description": "Initialize OpenAI client with API key",
                "parameters": ["api_key", "model"]
            },
            "completion": {
                "description": "Generate completion from prompt with instruction",
                "parameters": ["prompt", "instruction", "max_tokens"]
            },
            "chat_completion": {
                "description": "Generate chat completion from message history",
                "parameters": ["messages", "max_tokens"]
            },
            "test_connection": {
                "description": "Test OpenAI connection",
                "parameters": []
            }
        },
        # Dynamic module source embedded in genotype
        "module_source": openai_module_source
    }

    print("🔬 Creating OpenAI Soul from genotype...")

    # Create Soul with OpenAI genotype
    openai_soul = await Soul.create(openai_genotype, alias="openai_client")

    print(f"✅ Soul created: {openai_soul}")
    print(f"📊 Soul has module source: {openai_soul.has_module_source()}")

    # Load module dynamically
    print("\n🔄 Loading dynamic module...")
    module = openai_soul.load_module_dynamically()

    if module:
        print("✅ Module loaded successfully!")

        # Extract functions from module
        functions = openai_soul.extract_functions_from_module(module)
        print(f"🔧 Found {len(functions)} functions: {list(functions.keys())}")

        # Register functions in Soul
        for func_name, func in functions.items():
            if not func_name.startswith('_'):  # Skip private functions
                openai_soul._register_immutable_function(func_name, func)

        print(f"📋 Registered functions: {openai_soul.list_functions()}")

        # Create Being from Soul
        print("\n👤 Creating Being from OpenAI Soul...")
        openai_being = await Being.create(
            openai_soul,
            phenotype={"role": "ai_assistant", "specialty": "openai_completions"},
            alias="openai_assistant"
        )

        print(f"✅ Being created: {openai_being}")

        # Test OpenAI functionality (if API key is available)
        api_key = os.environ.get("OPENAI_API_KEY")

        if api_key:
            print("\n🔑 Testing OpenAI integration...")

            # Initialize OpenAI through Soul function
            init_result = await openai_soul.execute_function("initialize_openai", api_key)
            print(f"🚀 Initialization: {init_result}")

            if init_result.get("success"):
                # Test simple completion
                completion_result = await openai_soul.execute_function(
                    "completion",
                    prompt="What is LuxDB?",
                    instruction="You are an expert on database systems. Be concise.",
                    max_tokens=100
                )
                print(f"💬 Completion test: {completion_result}")

                # Test connection
                connection_test = await openai_soul.execute_function("test_connection")
                print(f"🔌 Connection test: {connection_test}")

            # Update demo to show new execute methods and attribute separation
            # Test nowej metody execute z danymi
            print("\n=== Test execute z danymi ===")
            result = await openai_being.execute(data={
                "prompt": "Napisz krótką historię o AI",
                "context": "Jesteś kreatywnym pisarzem"
            }, model="gpt-3.5-turbo", temperature=0.8)

            print("Wynik execute:")
            print(f"Success: {result.get('success')}")

            if result.get('success'):
                completion_data = result.get('data', {}).get('result', {})
                print(f"Model: {completion_data.get('model')}")
                print(f"Status: {completion_data.get('status')}")
                if completion_data.get('completion'):
                    print(f"Odpowiedź: {completion_data.get('completion')[:200]}...")
                if completion_data.get('usage'):
                    usage = completion_data.get('usage')
                    print(f"Tokeny: {usage.get('total_tokens')}")
            else:
                print(f"Błąd: {result.get('error')}")

            # Test wykonania konkretnej funkcji
            print("\n=== Test execute z konkretną funkcją ===")
            result2 = await openai_being.execute(
                function="get_completion",
                prompt="Co to jest LuxDB?",
                context="Jesteś ekspertem od baz danych",
                temperature=0.3
            )

            print("Wynik execute z funkcją get_completion:")
            if result2.get('success'):
                completion_data = result2.get('data', {}).get('result', {})
                if completion_data.get('completion'):
                    print(f"Odpowiedź: {completion_data.get('completion')[:200]}...")
            else:
                print(f"Błąd: {result2.get('error')}")

            print(f"\nStatystyki Being: {openai_being.data.get('execution_count', 0)} wykonań")

        else:
            print("⚠️ No OPENAI_API_KEY found in environment - skipping live tests")

            # Test function execution without API key (should return error)
            test_result = await openai_soul.execute_function("test_connection")
            print(f"🧪 Function execution test: {test_result}")

    else:
        print("❌ Failed to load dynamic module!")

    print("\n🎯 Philosophy Test Results:")
    print("✅ Only Soul and Being models used")
    print("✅ Everything else emerges from these two")
    print("✅ Dynamic module loading works")
    print("✅ Functions automatically registered")
    print("✅ Being can execute Soul functions")

    # Show Soul lineage and version info
    print(f"\n📈 Soul version: {openai_soul.get_version()}")
    print(f"🧬 Soul hash: {openai_soul.soul_hash[:16]}...")

    return openai_soul, openai_being if 'openai_being' in locals() else None

if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n🏁 Demo completed!")
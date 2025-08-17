
#!/usr/bin/env python3
"""
🧬 LuxOS v1.0.0 - Kompletny system Soul-only
Kamień milowy: Usunięcie Being, Soul jako kompletny model
"""

import asyncio
import argparse
from typing import Dict, Any

# Import only existing modules
from luxdb.core import LuxDB, SimpleKernel
from luxdb.core.postgre_db import Postgre_db
from luxdb.core.access_control import access_controller
from luxdb.models.soul import Soul


class LuxOSSystem:
    """Główna klasa systemu LuxOS z architekturą Soul-only"""
    
    def __init__(self):
        self.db = None
        self.kernel = None
        self.souls_registry = {}
        
    async def initialize(self):
        """Inicjalizacja systemu"""
        print("🚀 LuxOS v1.0.0 - Soul-only Architecture")
        print("=" * 50)
        
        # Inicjalizuj bazę danych
        self.db = Postgre_db()
        await self.db.initialize()
        
        # Inicjalizuj kernel
        self.kernel = SimpleKernel()
        await self.kernel.initialize()
        
        # Inicjalizuj kontrolę dostępu
        access_controller.initialize()
        
        print("✅ System LuxOS initialized successfully")
        
    async def create_demo_soul(self):
        """Tworzy demonstracyjną Soul"""
        demo_genotype = {
            "genesis": {
                "name": "demo_soul",
                "type": "demonstration",
                "version": "1.0.0",
                "description": "Demonstracyjna Soul w architekturze Soul-only"
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "counter": {"py_type": "int", "default": 0},
                "active": {"py_type": "bool", "default": True}
            },
            "module_source": '''
def init(instance_context=None):
    """Inicjalizacja instancji Soul"""
    print(f"🎯 Initializing instance {instance_context.get('ulid', 'unknown')}")
    return {"initialized": True, "timestamp": instance_context.get("creation_time")}

def process_data(text="Hello World", instance_context=None):
    """Przetwarza dane tekstowe"""
    if instance_context:
        counter = instance_context["data"].get("counter", 0) + 1
        instance_context["data"]["counter"] = counter
        result = f"PROCESSED({counter}): {text}"
    else:
        result = f"PROCESSED: {text}"
    
    return {"result": result, "processed_at": "now"}

def get_status(instance_context=None):
    """Zwraca status instancji"""
    if instance_context:
        return {
            "ulid": instance_context["ulid"],
            "data": instance_context["data"],
            "active": instance_context["data"].get("active", True)
        }
    return {"status": "no_instance_context"}
'''
        }
        
        # Utwórz Soul
        soul = await Soul.create(demo_genotype, alias="demo_soul")
        self.souls_registry["demo"] = soul
        
        print(f"🧬 Created demo Soul: {soul.soul_hash[:8]}")
        
        return soul
        
    async def test_soul_instances(self, soul: Soul):
        """Testuje tworzenie i zarządzanie instancjami Soul"""
        print("\n🧪 Testing Soul instances...")
        
        # Test 1: Tworzenie instancji przez init().set()
        print("1. Creating instance via init().set()")
        result1 = await soul.init(
            data={"name": "Test Instance 1", "counter": 0}
        ).set()
        
        if result1.get("success"):
            ulid1 = result1["data"]["ulid"]
            print(f"   ✅ Created instance: {ulid1[:8]}")
        else:
            print(f"   ❌ Failed: {result1.get('error')}")
            return
        
        # Test 2: Tworzenie przez get_or_create  
        print("2. Creating instance via get_or_create")
        result2 = await soul.get_or_create(
            data={"name": "Test Instance 2", "counter": 5}
        )
        
        if result2.get("success"):
            ulid2 = result2["data"]["ulid"] 
            print(f"   ✅ Created instance: {ulid2[:8]}")
        else:
            print(f"   ❌ Failed: {result2.get('error')}")
            return
            
        # Test 3: Wykonywanie funkcji na instancjach
        print("3. Executing functions on instances")
        
        # Wykonaj process_data na pierwszej instancji
        exec_result1 = await soul.execute_function(
            "process_data", 
            ulid1,
            "Hello from Instance 1"
        )
        
        if exec_result1.get("success"):
            print(f"   ✅ Function result: {exec_result1['data']['result']}")
        else:
            print(f"   ❌ Execution failed: {exec_result1.get('error')}")
        
        # Test 4: Sprawdzanie statusu
        print("4. Checking instance status")
        status_result = await soul.execute_function("get_status", ulid1)
        
        if status_result.get("success"):
            status = status_result["data"]["result"]
            print(f"   ✅ Instance status: counter={status['data']['counter']}")
        else:
            print(f"   ❌ Status check failed: {status_result.get('error')}")
        
        # Test 5: Lista instancji
        print("5. Listing all instances")
        instances = soul.list_instances()
        print(f"   ✅ Total instances: {len(instances)}")
        for i, instance in enumerate(instances, 1):
            print(f"      {i}. {instance['ulid'][:8]} - {instance['data']['name']}")
        
        # Test 6: Wykonywanie na wszystkich instancjach
        print("6. Executing function on all instances")
        all_results = await soul.execute_on_all_instances("get_status")
        
        if all_results.get("success"):
            executed = all_results["data"]["instances_executed"]
            print(f"   ✅ Executed on {executed} instances")
        else:
            print(f"   ❌ Batch execution failed")

    async def run_web_interface(self):
        """Uruchamia interfejs webowy"""
        try:
            from luxdb.web_lux_interface import create_app
            
            app = create_app()
            
            print("🌐 Starting LuxOS Web Interface...")
            print("   URL: http://0.0.0.0:5000")
            print("   Soul-only architecture active")
            
            import uvicorn
            await uvicorn.run(
                app,
                host="0.0.0.0", 
                port=5000,
                log_level="info"
            )
            
        except ImportError:
            print("❌ Web interface dependencies not available")
        except Exception as e:
            print(f"❌ Failed to start web interface: {e}")

    async def run_demo(self):
        """Uruchamia demonstrację Soul-only"""
        await self.initialize()
        
        # Utwórz demonstracyjną Soul
        demo_soul = await self.create_demo_soul()
        
        # Testuj instancje
        await self.test_soul_instances(demo_soul)
        
        # Pokaż statystyki
        print(f"\n📊 Final Statistics:")
        print(f"   Soul hash: {demo_soul.soul_hash}")
        print(f"   Instances: {demo_soul.get_instance_count()}")
        print(f"   Functions: {demo_soul.get_functions_count()}")
        print(f"   Available functions: {', '.join(demo_soul.list_functions())}")
        
        print(f"\n🎉 LuxOS v1.0.0 Soul-only demonstration completed!")


async def main():
    """Główna funkcja systemu"""
    parser = argparse.ArgumentParser(description="LuxOS v1.0.0 - Soul-only Architecture")
    parser.add_argument("--mode", choices=["demo", "web"], default="demo",
                       help="Run mode: demo or web interface")
    parser.add_argument("--kernel", choices=["simple"], default="simple", 
                       help="Kernel type to use")
    
    args = parser.parse_args()
    
    system = LuxOSSystem()
    
    if args.mode == "web":
        await system.run_web_interface()
    else:
        await system.run_demo()


if __name__ == "__main__":
    print("🧬 LuxOS v1.0.0 - Soul-only Architecture")
    print("Kamień milowy: Being usunięte, Soul kompletne!")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 LuxOS shutdown completed")
    except Exception as e:
        print(f"\n💥 LuxOS error: {e}")

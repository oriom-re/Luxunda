
"""
LuxDB Server/Client Demo
=======================

Shows how to use LuxDB as both server and client.
"""

import asyncio
import json
from luxdb.server.server import LuxDBServer
from luxdb.server.client import LuxDBClient
from luxdb.ai_generator import AIGenotypGenerator


async def demo_server_client():
    """Demonstrate server/client functionality"""
    
    print("🚀 LuxDB Server/Client Demo")
    print("=" * 50)
    
    # Start server in background (in real usage, this would be separate process)
    print("1. Starting LuxDB Server...")
    server = LuxDBServer(
        port=5001,  # Use different port for demo
        db_host="localhost",
        db_user="your_user",
        db_password="your_password",
        db_name="luxdb_demo"
    )
    
    # Simulate server startup
    await asyncio.sleep(1)
    print("✅ Server started on port 5001")
    
    # Create client connection
    print("\n2. Connecting with LuxDB Client...")
    client = LuxDBClient(
        server_url="http://localhost:5001",
        namespace_id="demo_project"
    )
    
    async with client:
        # Create namespace
        print("\n3. Creating namespace 'demo_project'...")
        try:
            result = await client.create_namespace()
            print(f"✅ Namespace created: {result}")
        except Exception as e:
            print(f"ℹ️  Namespace might already exist: {e}")
        
        # Generate genotype with AI
        print("\n4. Generating genotype with AI assistant...")
        ai_generator = AIGenotypGenerator()
        suggestions = ai_generator.suggest_genotype(
            "I need to store user profiles with names, emails and preferences"
        )
        
        user_genotype = suggestions[0].genotype
        print(f"✅ Generated genotype: {user_genotype['genesis']['name']}")
        
        # Create soul
        print("\n5. Creating soul from genotype...")
        soul_result = await client.create_soul(
            genotype=user_genotype,
            alias="user_profile_v1"
        )
        soul_hash = soul_result["soul"]["soul_hash"]
        print(f"✅ Soul created: {soul_hash[:16]}...")
        
        # Create beings
        print("\n6. Creating beings (instances)...")
        users_data = [
            {
                "name": "Jan Kowalski", 
                "email": "jan@example.com", 
                "age": 30,
                "preferences": {"theme": "dark", "lang": "pl"},
                "active": True
            },
            {
                "name": "Anna Nowak",
                "email": "anna@example.com", 
                "age": 25,
                "preferences": {"theme": "light", "lang": "en"},
                "active": True
            }
        ]
        
        beings_created = []
        for i, user_data in enumerate(users_data):
            being_result = await client.create_being(
                soul_hash=soul_hash,
                data=user_data,
                alias=f"user_{i+1}"
            )
            beings_created.append(being_result["being"])
            print(f"✅ Being created: {user_data['name']}")
        
        # List all data
        print("\n7. Listing all data in namespace...")
        souls = await client.list_souls()
        beings = await client.list_beings()
        
        print(f"📊 Souls: {len(souls)}")
        print(f"📊 Beings: {len(beings)}")
        
        # Export schema
        print("\n8. Exporting schema...")
        schema_filename = "demo_project_schema.json"
        await client.save_schema_to_file(schema_filename)
        print(f"✅ Schema exported to {schema_filename}")
        
        # Show namespace info
        print("\n9. Namespace information...")
        info = await client.get_namespace_info()
        print(f"📋 Namespace: {info['namespace_id']}")
        print(f"📋 Created: {info['created_at']}")
        print(f"📋 Health: {info['health']['status']}")
        
        print("\n🎉 Demo completed successfully!")
        
        # Generate variations
        print("\n10. Generating genotype variations...")
        variations = ai_generator.generate_genotype_variations(user_genotype)
        for i, variation in enumerate(variations):
            print(f"   Variation {i+1}: {variation['genesis']['description']}")


async def demo_multi_namespace():
    """Demo with multiple namespaces"""
    
    print("\n" + "=" * 50)
    print("🌐 Multi-Namespace Demo")
    print("=" * 50)
    
    # Create multiple namespace clients
    namespaces = ["ecommerce", "blog", "analytics"]
    
    for namespace in namespaces:
        print(f"\n📁 Working with namespace: {namespace}")
        
        client = LuxDBClient(
            server_url="http://localhost:5001",
            namespace_id=namespace
        )
        
        async with client:
            # Setup namespace
            await client.setup_namespace()
            
            # Generate appropriate genotype
            ai_generator = AIGenotypGenerator()
            
            if namespace == "ecommerce":
                description = "product catalog with prices and inventory"
            elif namespace == "blog":
                description = "blog articles with content and metadata"
            else:  # analytics
                description = "analytics events with timestamps and user data"
            
            suggestions = ai_generator.suggest_genotype(description)
            genotype = suggestions[0].genotype
            
            # Create soul
            soul_result = await client.create_soul(
                genotype=genotype,
                alias=f"{namespace}_entity"
            )
            
            print(f"✅ Created soul for {namespace}: {genotype['genesis']['name']}")
    
    print("\n✅ Multi-namespace demo completed!")


async def demo_schema_migration():
    """Demo schema export/import for migration"""
    
    print("\n" + "=" * 50)
    print("📦 Schema Migration Demo")
    print("=" * 50)
    
    source_client = LuxDBClient(
        server_url="http://localhost:5001",
        namespace_id="demo_project"
    )
    
    target_client = LuxDBClient(
        server_url="http://localhost:5001",
        namespace_id="demo_project_backup"
    )
    
    async with source_client, target_client:
        # Export from source
        print("📤 Exporting schema from source namespace...")
        schema = await source_client.export_schema()
        
        # Create target namespace
        print("📁 Creating target namespace...")
        await target_client.create_namespace("demo_project_backup")
        
        # Import to target
        print("📥 Importing schema to target namespace...")
        import_result = await target_client.import_schema(schema)
        
        print(f"✅ Migration completed:")
        print(f"   Souls: {import_result['souls_imported']}")
        print(f"   Beings: {import_result['beings_imported']}")
        print(f"   Relationships: {import_result['relationships_imported']}")


if __name__ == "__main__":
    async def main():
        await demo_server_client()
        await demo_multi_namespace()
        await demo_schema_migration()
    
    asyncio.run(main())

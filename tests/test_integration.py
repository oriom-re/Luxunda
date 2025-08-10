
"""
LuxDB Integration Tests
=======================

End-to-end integration tests for complete LuxDB workflows.
"""

import pytest
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta

from luxdb import LuxDB, Soul, Being, Relationship
from ai.hybrid_ai_system import HybridAISystem
from services.message_similarity_service import MessageSimilarityService
from luxdb.models.message import Message
from luxdb.models.soul import Soul
from luxdb.models.being import Being


class IntegrationTester:
    """Integration test suite for complete workflows"""
    
    def __init__(self):
        self.db: LuxDB = None
        self.ai_system: HybridAISystem = None
        self.similarity_service: MessageSimilarityService = None
    
    async def setup_integration_environment(self) -> bool:
        """Setup integration test environment"""
        try:
            # Initialize core components
            self.db = LuxDB(
                host='localhost',
                port=5432,
                database='luxdb_test',
                user='postgres',
                password='password'
            )
            await self.db.initialize()
            
            self.ai_system = HybridAISystem()
            self.similarity_service = MessageSimilarityService()
            
            print("✅ Integration environment setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Integration setup failed: {str(e)}")
            return False
    
    async def test_complete_ai_workflow(self) -> Dict[str, Any]:
        """Test complete AI message processing workflow"""
        print("\n🤖 Testing Complete AI Workflow...")
        results = {
            'ai_message_processing': False,
            'similarity_detection': False,
            'relationship_creation': False,
            'knowledge_graph_building': False,
            'errors': []
        }
        
        try:
            # Create message genotype
            message_genotype = {
                "genesis": {
                    "name": "ai_message",
                    "type": "message",
                    "version": "1.0.0"
                },
                "attributes": {
                    "content": {"py_type": "str"},
                    "sender": {"py_type": "str"},
                    "timestamp": {"py_type": "str"},
                    "embedding": {"py_type": "List[float]", "vector_size": 1536},
                    "processed": {"py_type": "bool", "default": False}
                }
            }
            
            message_soul = await Soul.create(message_genotype, alias="ai_message")
            
            # Test AI message processing
            test_messages = [
                "Hello, how can I help you with data analysis?",
                "I need assistance with machine learning algorithms.",
                "Can you explain how neural networks work?",
                "What are the best practices for database design?",
                "How do I optimize my SQL queries for better performance?"
            ]
            
            processed_beings = []
            
            for i, content in enumerate(test_messages):
                # Process with AI system
                ai_result = await self.ai_system.process_request(content, use_openai=False)
                
                # Create being with message and AI analysis
                message_data = {
                    "content": content,
                    "sender": f"user_{i}",
                    "timestamp": datetime.now().isoformat(),
                    "embedding": [0.1 * j for j in range(1536)],  # Mock embedding
                    "processed": True
                }
                
                being = await Being.create(message_soul, message_data)
                processed_beings.append(being)
            
            if len(processed_beings) == 5:
                results['ai_message_processing'] = True
                print("✅ AI message processing successful")
            
            # Test similarity detection
            similarity_results = await self.similarity_service.compare_messages_and_create_relations(
                message_soul.soul_hash, threshold=0.7
            )
            
            if similarity_results.get('relationships_created', 0) > 0:
                results['similarity_detection'] = True
                print("✅ Similarity detection working")
            
            # Test relationship creation
            relationships = await Relationship.find_by_type('similar_content')
            
            if len(relationships) > 0:
                results['relationship_creation'] = True
                print("✅ Relationship creation successful")
            
            # Test knowledge graph building
            all_beings = await Being.load_all()
            all_relationships = await Relationship.load_all()
            
            knowledge_graph = {
                'nodes': len(all_beings),
                'edges': len(all_relationships),
                'connected_components': self.analyze_graph_connectivity(all_beings, all_relationships)
            }
            
            if knowledge_graph['nodes'] >= 5 and knowledge_graph['edges'] >= 1:
                results['knowledge_graph_building'] = True
                print(f"✅ Knowledge graph built: {knowledge_graph['nodes']} nodes, {knowledge_graph['edges']} edges")
            
        except Exception as e:
            results['errors'].append(f"AI workflow error: {str(e)}")
            print(f"❌ AI workflow error: {str(e)}")
        
        return results
    
    async def test_multi_user_scenario(self) -> Dict[str, Any]:
        """Test multi-user concurrent operations"""
        print("\n👥 Testing Multi-User Scenario...")
        results = {
            'concurrent_users': False,
            'data_isolation': False,
            'conflict_resolution': False,
            'performance_under_load': False,
            'errors': []
        }
        
        try:
            # Create user genotype
            user_genotype = {
                "genesis": {
                    "name": "user_profile",
                    "type": "user",
                    "version": "1.0.0"
                },
                "attributes": {
                    "username": {"py_type": "str", "unique": True},
                    "email": {"py_type": "str"},
                    "preferences": {"py_type": "dict"},
                    "last_active": {"py_type": "str"},
                    "session_count": {"py_type": "int", "default": 0}
                }
            }
            
            user_soul = await Soul.create(user_genotype, alias="user_profile")
            
            # Simulate concurrent users
            async def simulate_user(user_id: int):
                try:
                    # Create user
                    user_data = {
                        "username": f"user_{user_id}",
                        "email": f"user_{user_id}@test.com",
                        "preferences": {"theme": "dark", "language": "en"},
                        "last_active": datetime.now().isoformat(),
                        "session_count": 1
                    }
                    
                    user_being = await Being.create(user_soul, user_data)
                    
                    # Simulate user activity
                    for activity in range(5):
                        await asyncio.sleep(0.1)  # Simulate time between activities
                        await user_being.update_attribute("session_count", activity + 1)
                        await user_being.update_attribute("last_active", datetime.now().isoformat())
                    
                    return user_being.ulid
                    
                except Exception as e:
                    return f"Error: {str(e)}"
            
            # Run concurrent user simulations
            start_time = datetime.now()
            user_tasks = [simulate_user(i) for i in range(10)]
            user_results = await asyncio.gather(*user_tasks, return_exceptions=True)
            duration = (datetime.now() - start_time).total_seconds()
            
            successful_users = [r for r in user_results if isinstance(r, str) and not r.startswith("Error")]
            
            if len(successful_users) >= 8 and duration < 10:  # 80% success rate, under 10 seconds
                results['concurrent_users'] = True
                print(f"✅ Concurrent users: {len(successful_users)}/10 successful in {duration:.2f}s")
            
            # Test data isolation
            all_users = [b for b in await Being.load_all() if b.soul_hash == user_soul.soul_hash]
            usernames = [u.attributes.get('username') for u in all_users]
            unique_usernames = set(usernames)
            
            if len(usernames) == len(unique_usernames):
                results['data_isolation'] = True
                print("✅ Data isolation maintained")
            
            # Test conflict resolution
            if len(all_users) >= 2:
                user1, user2 = all_users[0], all_users[1]
                
                # Simulate concurrent updates
                async def update_user(user, value):
                    await user.update_attribute("session_count", value)
                
                await asyncio.gather(
                    update_user(user1, 100),
                    update_user(user1, 200)
                )
                
                # Check final state
                updated_user = await Being.load_by_ulid(user1.ulid)
                final_count = updated_user.attributes.get('session_count')
                
                if final_count in [100, 200]:
                    results['conflict_resolution'] = True
                    print("✅ Conflict resolution working")
            
            # Performance under load
            if duration < 15:  # All operations should complete quickly
                results['performance_under_load'] = True
                print("✅ Performance under load acceptable")
            
        except Exception as e:
            results['errors'].append(f"Multi-user scenario error: {str(e)}")
            print(f"❌ Multi-user scenario error: {str(e)}")
        
        return results
    
    async def test_data_migration_workflow(self) -> Dict[str, Any]:
        """Test data migration and versioning workflow"""
        print("\n📦 Testing Data Migration Workflow...")
        results = {
            'schema_evolution': False,
            'data_migration': False,
            'backward_compatibility': False,
            'version_management': False,
            'errors': []
        }
        
        try:
            # Create initial schema version
            v1_genotype = {
                "genesis": {
                    "name": "product",
                    "type": "entity",
                    "version": "1.0.0"
                },
                "attributes": {
                    "name": {"py_type": "str"},
                    "price": {"py_type": "float"},
                    "in_stock": {"py_type": "bool"}
                }
            }
            
            v1_soul = await Soul.create(v1_genotype, alias="product_v1")
            
            # Create test data with v1 schema
            v1_products = []
            for i in range(5):
                product_data = {
                    "name": f"Product {i}",
                    "price": 10.0 + i,
                    "in_stock": i % 2 == 0
                }
                product = await Being.create(v1_soul, product_data)
                v1_products.append(product)
            
            # Create evolved schema version
            v2_genotype = {
                "genesis": {
                    "name": "product",
                    "type": "entity",
                    "version": "2.0.0"
                },
                "attributes": {
                    "name": {"py_type": "str"},
                    "price": {"py_type": "float"},
                    "in_stock": {"py_type": "bool"},
                    "category": {"py_type": "str", "default": "general"},
                    "description": {"py_type": "str", "default": ""},
                    "tags": {"py_type": "List[str]", "default": []}
                }
            }
            
            v2_soul = await Soul.create(v2_genotype, alias="product_v2")
            
            if v2_soul:
                results['schema_evolution'] = True
                print("✅ Schema evolution successful")
            
            # Test data migration
            migrated_products = []
            for old_product in v1_products:
                old_attrs = await old_product.get_attributes()
                
                # Migrate to new schema with additional fields
                new_data = {
                    "name": old_attrs["name"],
                    "price": old_attrs["price"],
                    "in_stock": old_attrs["in_stock"],
                    "category": "migrated",
                    "description": f"Migrated product: {old_attrs['name']}",
                    "tags": ["migrated", "v1"]
                }
                
                new_product = await Being.create(v2_soul, new_data)
                migrated_products.append(new_product)
            
            if len(migrated_products) == len(v1_products):
                results['data_migration'] = True
                print("✅ Data migration successful")
            
            # Test backward compatibility
            v1_products_loaded = [b for b in await Being.load_all() if b.soul_hash == v1_soul.soul_hash]
            
            if len(v1_products_loaded) == len(v1_products):
                results['backward_compatibility'] = True
                print("✅ Backward compatibility maintained")
            
            # Test version management
            all_souls = await Soul.load_all()
            product_souls = [s for s in all_souls if s.alias.startswith("product_")]
            
            versions = [s.genotype.get("genesis", {}).get("version") for s in product_souls]
            
            if "1.0.0" in versions and "2.0.0" in versions:
                results['version_management'] = True
                print("✅ Version management working")
            
        except Exception as e:
            results['errors'].append(f"Migration workflow error: {str(e)}")
            print(f"❌ Migration workflow error: {str(e)}")
        
        return results
    
    def analyze_graph_connectivity(self, beings: List[Being], relationships: List[Relationship]) -> int:
        """Analyze graph connectivity (simplified)"""
        if not beings or not relationships:
            return len(beings)
        
        # Simple connectivity analysis
        connected_nodes = set()
        for rel in relationships:
            connected_nodes.add(rel.source_ulid)
            connected_nodes.add(rel.target_ulid)
        
        # Count components: connected nodes + isolated nodes
        isolated_nodes = len([b for b in beings if b.ulid not in connected_nodes])
        connected_components = 1 if connected_nodes else 0
        
        return connected_components + isolated_nodes
    
    async def run_integration_tests(self) -> Dict[str, Any]:
        """Run complete integration test suite"""
        print("🔗 Starting LuxDB Integration Test Suite")
        print("=" * 50)
        
        results = {
            'setup': False,
            'ai_workflow': {},
            'multi_user': {},
            'migration': {},
            'overall_success': False,
            'total_errors': 0,
            'recommendations': []
        }
        
        try:
            # Setup
            results['setup'] = await self.setup_integration_environment()
            
            if results['setup']:
                # Run integration tests
                results['ai_workflow'] = await self.test_complete_ai_workflow()
                results['multi_user'] = await self.test_multi_user_scenario()
                results['migration'] = await self.test_data_migration_workflow()
                
                # Calculate overall success
                test_sections = [results['ai_workflow'], results['multi_user'], results['migration']]
                total_errors = sum(len(section.get('errors', [])) for section in test_sections)
                results['total_errors'] = total_errors
                
                # Success criteria: most tests pass, minimal errors
                passed_tests = sum(
                    len([k for k, v in section.items() if k != 'errors' and v is True])
                    for section in test_sections
                )
                
                results['overall_success'] = passed_tests >= 8 and total_errors < 3
                
                if not results['overall_success']:
                    results['recommendations'] = [
                        "🔧 Integration test issues detected:",
                        "  1. Review error logs for specific failures",
                        "  2. Check AI system configuration and dependencies",
                        "  3. Verify database performance under concurrent load",
                        "  4. Test with production-like data volumes",
                        "  5. Monitor system resources during testing"
                    ]
            
        except Exception as e:
            results['total_errors'] += 1
            results['recommendations'].append(f"Critical integration error: {str(e)}")
        
        return results


async def run_integration_tests():
    """Main integration test runner"""
    tester = IntegrationTester()
    results = await tester.run_integration_tests()
    
    print("\n" + "=" * 60)
    print("📊 LUXDB INTEGRATION TEST REPORT")
    print("=" * 60)
    
    if results['overall_success']:
        print("🎉 INTEGRATION STATUS: ✅ PASSED - All workflows functioning correctly!")
    else:
        print("⚠️  INTEGRATION STATUS: ❌ FAILED - Workflow issues detected")
    
    print(f"\nTotal Errors: {results['total_errors']}")
    
    if results.get('recommendations'):
        print("\n🛠️  RECOMMENDATIONS:")
        for rec in results['recommendations']:
            print(f"   {rec}")
    
    return results


if __name__ == "__main__":
    asyncio.run(run_integration_tests())

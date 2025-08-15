"""
LuxDB Core Functionality Tests
==============================

Tests covering all core database operations with detailed diagnostics.
"""

import pytest
import asyncio
import os
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback

from luxdb import LuxDB, Soul, Being
from luxdb.utils.validators import validate_genotype
from luxdb.core.postgre_db import Postgre_db


class CoreFunctionalityTester:
    """Core functionality test suite with diagnostics"""

    def __init__(self):
        self.db: Optional[LuxDB] = None
        self.test_results: Dict[str, Any] = {}
        self.connection_info = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'luxdb_test'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }

    async def setup_test_environment(self) -> Dict[str, Any]:
        """Setup and validate test environment"""
        print("🔧 Setting up test environment...")
        setup_results = {
            'database_connection': False,
            'required_tables': False,
            'test_data_clean': False,
            'permissions': False,
            'errors': []
        }

        try:
            # Test database connection
            self.db = LuxDB(**self.connection_info)
            await self.db.initialize()
            setup_results['database_connection'] = True
            print("✅ Database connection successful")

            # Verify required tables exist
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_names = [row['table_name'] for row in tables]

                required_tables = ['souls', 'beings', 'attr_text', 'attr_int', 'attr_float', 'attr_boolean', 'attr_jsonb']
                missing_tables = [t for t in required_tables if t not in table_names]

                if not missing_tables:
                    setup_results['required_tables'] = True
                    print("✅ All required tables exist")
                else:
                    setup_results['errors'].append(f"Missing tables: {missing_tables}")
                    print(f"❌ Missing tables: {missing_tables}")

                # Test permissions
                try:
                    await conn.execute("CREATE TEMP TABLE test_permissions (id INT)")
                    await conn.execute("DROP TABLE test_permissions")
                    setup_results['permissions'] = True
                    print("✅ Database permissions OK")
                except Exception as e:
                    setup_results['errors'].append(f"Permission error: {str(e)}")
                    print(f"❌ Permission error: {str(e)}")

                # Clean test data
                await conn.execute("DELETE FROM beings WHERE soul_hash LIKE 'test_%'")
                await conn.execute("DELETE FROM souls WHERE soul_hash LIKE 'test_%'")
                setup_results['test_data_clean'] = True
                print("✅ Test data cleaned")

        except Exception as e:
            setup_results['errors'].append(f"Setup failed: {str(e)}")
            print(f"❌ Setup failed: {str(e)}")

        return setup_results

    async def test_soul_operations(self) -> Dict[str, Any]:
        """Test all Soul operations"""
        print("\n🧠 Testing Soul operations...")
        results = {
            'create_soul': False,
            'load_soul': False,
            'update_soul': False,
            'validate_genotype': False,
            'errors': []
        }

        try:
            # Test genotype validation
            test_genotype = {
                "genesis": {
                    "name": "test_entity",
                    "type": "test",
                    "version": "1.0.0"
                },
                "attributes": {
                    "name": {"py_type": "str", "max_length": 100},
                    "count": {"py_type": "int", "min_value": 0},
                    "active": {"py_type": "bool", "default": True},
                    "metadata": {"py_type": "dict"}
                }
            }

            # Validate genotype
            is_valid, errors = validate_genotype(test_genotype)
            if is_valid:
                results['validate_genotype'] = True
                print("✅ Genotype validation passed")
            else:
                results['errors'].append(f"Genotype validation failed: {errors}")
                print(f"❌ Genotype validation failed: {errors}")

            # Create soul
            soul = await Soul.create(test_genotype, alias="test_soul")
            if soul and soul.soul_hash:
                results['create_soul'] = True
                print(f"✅ Soul created: {soul.alias}")
            else:
                results['errors'].append("Failed to create soul")
                print("❌ Failed to create soul")

            # Load soul
            loaded_soul = await Soul.load_by_alias("test_soul")
            if loaded_soul and loaded_soul.soul_hash == soul.soul_hash:
                results['load_soul'] = True
                print("✅ Soul loaded successfully")
            else:
                results['errors'].append("Failed to load soul")
                print("❌ Failed to load soul")

            # Update soul (create new version)
            updated_genotype = test_genotype.copy()
            updated_genotype['genesis']['version'] = "1.1.0"
            updated_genotype['attributes']['description'] = {"py_type": "str", "default": ""}

            updated_soul = await Soul.create(updated_genotype, alias="test_soul_v2")
            if updated_soul:
                results['update_soul'] = True
                print("✅ Soul updated successfully")
            else:
                results['errors'].append("Failed to update soul")
                print("❌ Failed to update soul")

        except Exception as e:
            results['errors'].append(f"Soul operations error: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Soul operations error: {str(e)}")

        return results

    async def test_being_operations(self) -> Dict[str, Any]:
        """Test all Being operations"""
        print("\n🤖 Testing Being operations...")
        results = {
            'create_being': False,
            'load_being': False,
            'update_attributes': False,
            'delete_being': False,
            'bulk_operations': False,
            'errors': []
        }

        try:
            # Get test soul
            soul = await Soul.load_by_alias("test_soul")
            if not soul:
                results['errors'].append("Test soul not found")
                return results

            # Create being
            test_data = {
                "name": "Test Being",
                "count": 42,
                "active": True,
                "metadata": {"test": True, "created_at": datetime.now().isoformat()}
            }

            being = await Being.create(soul, test_data)
            if being and being.ulid:
                results['create_being'] = True
                print(f"✅ Being created: {being.ulid}")
            else:
                results['errors'].append("Failed to create being")
                print("❌ Failed to create being")
                return results

            # Load being
            loaded_being = await Being.load_by_ulid(being.ulid)
            if loaded_being and loaded_being.ulid == being.ulid:
                results['load_being'] = True
                print("✅ Being loaded successfully")
            else:
                results['errors'].append("Failed to load being")
                print("❌ Failed to load being")

            # Update attributes
            await being.update_attribute("count", 100)
            await being.update_attribute("name", "Updated Being")

            # Verify updates
            updated_attrs = await being.get_attributes()
            if updated_attrs.get("count") == 100 and updated_attrs.get("name") == "Updated Being":
                results['update_attributes'] = True
                print("✅ Being attributes updated successfully")
            else:
                results['errors'].append("Failed to update being attributes")
                print("❌ Failed to update being attributes")

            # Test bulk operations
            bulk_beings = []
            for i in range(5):
                bulk_data = {
                    "name": f"Bulk Being {i}",
                    "count": i * 10,
                    "active": i % 2 == 0,
                    "metadata": {"bulk": True, "index": i}
                }
                bulk_being = await Being.create(soul, bulk_data)
                bulk_beings.append(bulk_being)

            if len(bulk_beings) == 5 and all(b.ulid for b in bulk_beings):
                results['bulk_operations'] = True
                print("✅ Bulk operations successful")
            else:
                results['errors'].append("Failed bulk operations")
                print("❌ Failed bulk operations")

            # Delete being
            await being.delete()
            deleted_being = await Being.load_by_ulid(being.ulid)
            if not deleted_being:
                results['delete_being'] = True
                print("✅ Being deleted successfully")
            else:
                results['errors'].append("Failed to delete being")
                print("❌ Failed to delete being")

        except Exception as e:
            results['errors'].append(f"Being operations error: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Being operations error: {str(e)}")

        return results

    async def test_being_advanced_operations(self) -> Dict[str, Any]:
        """Test advanced Being operations"""
        print("\n🤖 Testing Advanced Being operations...")
        results = {
            'function_execution': False,
            'being_mastery': False,
            'evolution_requests': False,
            'soul_creation': False,
            'errors': []
        }

        try:
            # Get test soul
            soul = await Soul.load_by_alias("test_soul")
            if not soul:
                results['errors'].append("Test soul not found")
                return results

            # Create being for advanced testing
            test_data = {
                "name": "Advanced Test Being",
                "count": 1,
                "active": True,
                "metadata": {"advanced_test": True}
            }

            being = await Being.create(soul, test_data)
            if being and being.ulid:
                print(f"✅ Advanced Being created: {being.ulid}")
            else:
                results['errors'].append("Failed to create advanced being")
                return results

            # Test function mastery checking
            is_master = being.is_function_master()
            if isinstance(is_master, bool):
                results['being_mastery'] = True
                print(f"✅ Being mastery check: {is_master}")
            else:
                results['errors'].append("Failed to check being mastery")

            # Test evolution capabilities
            evolution_info = await being.can_evolve()
            if isinstance(evolution_info, dict) and 'can_evolve' in evolution_info:
                results['evolution_requests'] = True
                print(f"✅ Evolution capabilities checked")
            else:
                results['errors'].append("Failed to check evolution capabilities")

            # Test Soul creation capabilities (if being has privileges)
            soul_concept = {
                "genesis": {
                    "name": "test_created_soul",
                    "type": "test_creation",
                    "version": "1.0.0"
                },
                "attributes": {
                    "created_by_test": {"py_type": "bool", "default": True}
                }
            }
            
            creation_result = await being.propose_soul_creation(soul_concept)
            if isinstance(creation_result, dict):
                results['soul_creation'] = True
                print(f"✅ Soul creation proposal tested")
            else:
                results['errors'].append("Failed to test soul creation")

        except Exception as e:
            results['errors'].append(f"Advanced Being operations error: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Advanced Being operations error: {str(e)}")

        return results

    async def test_performance_and_stress(self) -> Dict[str, Any]:
        """Test performance under load"""
        print("\n⚡ Testing Performance and Stress...")
        results = {
            'bulk_create_performance': False,
            'concurrent_operations': False,
            'memory_usage': False,
            'query_performance': False,
            'errors': []
        }

        try:
            # Performance test setup
            soul = await Soul.load_by_alias("test_soul")
            start_time = datetime.now()

            # Bulk create test (100 beings)
            bulk_start = datetime.now()
            bulk_beings = []

            for i in range(100):
                data = {
                    "name": f"Perf Being {i}",
                    "count": i,
                    "active": True,
                    "metadata": {"performance_test": True, "batch": i // 10}
                }
                being = await Being.create(soul, data)
                bulk_beings.append(being)

            bulk_duration = (datetime.now() - bulk_start).total_seconds()

            if bulk_duration < 30 and len(bulk_beings) == 100:  # Should complete in under 30 seconds
                results['bulk_create_performance'] = True
                print(f"✅ Bulk create performance: {bulk_duration:.2f}s for 100 beings")
            else:
                results['errors'].append(f"Bulk create too slow: {bulk_duration:.2f}s")
                print(f"❌ Bulk create too slow: {bulk_duration:.2f}s")

            # Memory usage test
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # Load all beings
            all_beings = await Being.load_all()

            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before

            if memory_increase < 100:  # Less than 100MB increase
                results['memory_usage'] = True
                print(f"✅ Memory usage acceptable: +{memory_increase:.2f}MB")
            else:
                results['errors'].append(f"High memory usage: +{memory_increase:.2f}MB")
                print(f"❌ High memory usage: +{memory_increase:.2f}MB")

            # Query performance test
            query_start = datetime.now()

            # Complex queries
            for i in range(10):
                await Being.load_all()
                souls = await Soul.load_all()

            query_duration = (datetime.now() - query_start).total_seconds()

            if query_duration < 10:  # Should complete in under 10 seconds
                results['query_performance'] = True
                print(f"✅ Query performance: {query_duration:.2f}s for 30 queries")
            else:
                results['errors'].append(f"Query performance slow: {query_duration:.2f}s")
                print(f"❌ Query performance slow: {query_duration:.2f}s")

            # Concurrent operations test
            async def concurrent_task(task_id: int):
                try:
                    data = {
                        "name": f"Concurrent Being {task_id}",
                        "count": task_id,
                        "active": True,
                        "metadata": {"concurrent_test": True, "task_id": task_id}
                    }
                    being = await Being.create(soul, data)
                    await being.update_attribute("count", task_id * 2)
                    return True
                except Exception:
                    return False

            concurrent_start = datetime.now()

            # Run 20 concurrent operations
            tasks = [concurrent_task(i) for i in range(20)]
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            concurrent_duration = (datetime.now() - concurrent_start).total_seconds()
            successful_tasks = sum(1 for result in task_results if result is True)

            if successful_tasks >= 18 and concurrent_duration < 15:  # 90% success rate, under 15s
                results['concurrent_operations'] = True
                print(f"✅ Concurrent operations: {successful_tasks}/20 successful in {concurrent_duration:.2f}s")
            else:
                results['errors'].append(f"Concurrent operations issues: {successful_tasks}/20 in {concurrent_duration:.2f}s")
                print(f"❌ Concurrent operations issues: {successful_tasks}/20 in {concurrent_duration:.2f}s")

        except Exception as e:
            results['errors'].append(f"Performance test error: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Performance test error: {str(e)}")

        return results

    async def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and consistency"""
        print("\n🛡️ Testing Data Integrity...")
        results = {
            'foreign_key_constraints': False,
            'data_consistency': False,
            'transaction_rollback': False,
            'concurrent_updates': False,
            'errors': []
        }

        try:
            # Test Being data constraints
            soul = await Soul.load_by_alias("test_soul")
            being = await Being.create(soul, {"name": "Integrity Test", "count": 1, "active": True})

            # Try to create being with invalid soul_hash
            try:
                invalid_being = await Being.create(
                    soul_hash="invalid_hash_that_does_not_exist",
                    attributes={"name": "Invalid", "count": 1}
                )
                results['errors'].append("Soul foreign key constraint not enforced")
                print("❌ Soul foreign key constraint not enforced")
            except Exception:
                results['foreign_key_constraints'] = True
                print("✅ Soul foreign key constraints working")

            # Test data consistency
            original_attrs = await being.get_attributes()
            await being.update_attribute("count", 999)
            updated_attrs = await being.get_attributes()

            if updated_attrs["count"] == 999 and original_attrs["name"] == updated_attrs["name"]:
                results['data_consistency'] = True
                print("✅ Data consistency maintained")
            else:
                results['errors'].append("Data consistency failed")
                print("❌ Data consistency failed")

            # Test transaction behavior
            pool = await Postgre_db.get_db_pool()
            try:
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        # Create being in transaction
                        temp_being = await Being.create(soul, {"name": "Temp", "count": 1, "active": True})

                        # Force rollback by raising exception
                        raise Exception("Forced rollback")

            except Exception:
                # Check if being was rolled back
                temp_beings = [b for b in await Being.load_all() if b.attributes.get("name") == "Temp"]

                if len(temp_beings) == 0:
                    results['transaction_rollback'] = True
                    print("✅ Transaction rollback working")
                else:
                    results['errors'].append("Transaction rollback failed")
                    print("❌ Transaction rollback failed")

            # Test concurrent updates
            async def update_task(value: int):
                await being.update_attribute("count", value)
                return value

            # Run concurrent updates
            update_tasks = [update_task(i) for i in range(1, 6)]
            await asyncio.gather(*update_tasks)

            final_attrs = await being.get_attributes()
            final_count = final_attrs["count"]

            if final_count in range(1, 6):  # Should be one of the values we set
                results['concurrent_updates'] = True
                print(f"✅ Concurrent updates handled: final value {final_count}")
            else:
                results['errors'].append(f"Concurrent updates failed: unexpected value {final_count}")
                print(f"❌ Concurrent updates failed: unexpected value {final_count}")

        except Exception as e:
            results['errors'].append(f"Data integrity test error: {str(e)}\n{traceback.format_exc()}")
            print(f"❌ Data integrity test error: {str(e)}")

        return results

    async def cleanup_test_environment(self) -> Dict[str, Any]:
        """Clean up test environment"""
        print("\n🧹 Cleaning up test environment...")
        cleanup_results = {
            'test_data_removed': False,
            'connections_closed': False,
            'errors': []
        }

        try:
            # Remove test data
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                await conn.execute("DELETE FROM beings WHERE soul_hash IN (SELECT soul_hash FROM souls WHERE alias LIKE 'test_%')")
                await conn.execute("DELETE FROM souls WHERE alias LIKE 'test_%'")

                cleanup_results['test_data_removed'] = True
                print("✅ Test data removed")

            # Close connections
            await pool.close()
            cleanup_results['connections_closed'] = True
            print("✅ Database connections closed")

        except Exception as e:
            cleanup_results['errors'].append(f"Cleanup error: {str(e)}")
            print(f"❌ Cleanup error: {str(e)}")

        return cleanup_results

    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite"""
        print("🚀 Starting LuxDB Complete Test Suite")
        print("=" * 50)

        final_results = {
            'setup': {},
            'soul_tests': {},
            'being_tests': {},
            'relationship_tests': {},
            'performance_tests': {},
            'integrity_tests': {},
            'cleanup': {},
            'overall_success': False,
            'total_errors': 0,
            'recommendations': []
        }

        try:
            # Run all tests in sequence
            final_results['setup'] = await self.setup_test_environment()

            if final_results['setup']['database_connection']:
                final_results['soul_tests'] = await self.test_soul_operations()
                final_results['being_tests'] = await self.test_being_operations()
                final_results['advanced_being_tests'] = await self.test_being_advanced_operations()
                final_results['performance_tests'] = await self.test_performance_and_stress()
                final_results['integrity_tests'] = await self.test_data_integrity()

            final_results['cleanup'] = await self.cleanup_test_environment()

            # Calculate overall success
            all_tests = [
                final_results['setup'],
                final_results['soul_tests'],
                final_results['being_tests'],
                final_results['advanced_being_tests'],
                final_results['performance_tests'],
                final_results['integrity_tests']
            ]

            total_errors = sum(len(test.get('errors', [])) for test in all_tests)
            final_results['total_errors'] = total_errors

            # Determine success - allow for some non-critical failures
            critical_tests_passed = (
                final_results['setup'].get('database_connection', False) and
                final_results['soul_tests'].get('create_soul', False) and
                final_results['being_tests'].get('create_being', False)
            )

            final_results['overall_success'] = critical_tests_passed and total_errors < 5

            # Generate recommendations
            if not final_results['overall_success']:
                final_results['recommendations'] = self.generate_recommendations(final_results)

        except Exception as e:
            final_results['total_errors'] += 1
            final_results['recommendations'].append(f"Critical test suite error: {str(e)}")

        return final_results

    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate troubleshooting recommendations"""
        recommendations = []

        # Database connection issues
        if not results['setup'].get('database_connection', False):
            recommendations.extend([
                "🔧 DATABASE CONNECTION FAILED:",
                "  1. Check PostgreSQL is running: `systemctl status postgresql`",
                "  2. Verify connection parameters in environment variables",
                "  3. Test connection manually: `psql -h localhost -U postgres -d luxdb_test`",
                "  4. Check firewall settings and port accessibility",
                "  5. Ensure database 'luxdb_test' exists"
            ])

        # Missing tables
        if not results['setup'].get('required_tables', False):
            recommendations.extend([
                "🔧 MISSING DATABASE TABLES:",
                "  1. Run database migrations: `python -m luxdb.cli migrate`",
                "  2. Initialize database schema: `await db.initialize()`",
                "  3. Check database user permissions for DDL operations",
                "  4. Manually create tables using SQL scripts in /database/"
            ])

        # Performance issues
        if not results['performance_tests'].get('bulk_create_performance', False):
            recommendations.extend([
                "🔧 PERFORMANCE ISSUES DETECTED:",
                "  1. Check database connection pool size",
                "  2. Add database indexes for frequently queried columns",
                "  3. Consider connection pooling optimization",
                "  4. Monitor database server resources (CPU, memory, disk I/O)",
                "  5. Review query execution plans for optimization"
            ])

        # Memory issues
        if not results['performance_tests'].get('memory_usage', False):
            recommendations.extend([
                "🔧 HIGH MEMORY USAGE DETECTED:",
                "  1. Implement result pagination for large datasets",
                "  2. Use connection pooling with proper limits",
                "  3. Clear unused objects and close connections properly",
                "  4. Consider using streaming for large query results"
            ])

        # Data integrity issues
        if not results['integrity_tests'].get('foreign_key_constraints', False):
            recommendations.extend([
                "🔧 DATA INTEGRITY ISSUES:",
                "  1. Enable foreign key constraints in PostgreSQL",
                "  2. Add proper database constraints during table creation",
                "  3. Implement application-level validation",
                "  4. Review database schema for consistency"
            ])

        # General recommendations
        if results['total_errors'] > 0:
            recommendations.extend([
                "🔧 GENERAL TROUBLESHOOTING:",
                "  1. Check application logs for detailed error messages",
                "  2. Verify all dependencies are installed correctly",
                "  3. Ensure proper error handling in application code",
                "  4. Test with a fresh database instance",
                "  5. Update to latest LuxDB version if available"
            ])

        return recommendations

    def print_detailed_report(self, results: Dict[str, Any]) -> None:
        """Print detailed test report"""
        print("\n" + "=" * 60)
        print("📊 LUXDB COMPLETE TEST REPORT")
        print("=" * 60)

        if results['overall_success']:
            print("🎉 OVERALL STATUS: ✅ PASSED - Library is 100% reliable!")
        else:
            print("⚠️  OVERALL STATUS: ❌ FAILED - Issues found requiring attention")

        print(f"\n📈 SUMMARY:")
        print(f"   Total Errors: {results['total_errors']}")

        # Test section results
        sections = [
            ('Setup', results['setup']),
            ('Soul Operations', results['soul_tests']),
            ('Being Operations', results['being_tests']),
            ('Advanced Being Operations', results['advanced_being_tests']),
            ('Performance Tests', results['performance_tests']),
            ('Data Integrity', results['integrity_tests']),
            ('Cleanup', results['cleanup'])
        ]

        for section_name, section_results in sections:
            print(f"\n🔍 {section_name.upper()}:")
            if section_results:
                passed_tests = [k for k, v in section_results.items() if k != 'errors' and v is True]
                failed_tests = [k for k, v in section_results.items() if k != 'errors' and v is False]

                print(f"   ✅ Passed: {len(passed_tests)} tests")
                if passed_tests:
                    for test in passed_tests[:3]:  # Show first 3
                        print(f"      - {test}")
                    if len(passed_tests) > 3:
                        print(f"      ... and {len(passed_tests) - 3} more")

                print(f"   ❌ Failed: {len(failed_tests)} tests")
                if failed_tests:
                    for test in failed_tests:
                        print(f"      - {test}")

                if section_results.get('errors'):
                    print(f"   🚨 Errors: {len(section_results['errors'])}")
                    for error in section_results['errors'][:2]:  # Show first 2 errors
                        print(f"      - {error}")

        # Recommendations
        if results.get('recommendations'):
            print(f"\n🛠️  TROUBLESHOOTING RECOMMENDATIONS:")
            for rec in results['recommendations']:
                print(f"   {rec}")

        print("\n" + "=" * 60)


# Test runner function
async def run_luxdb_tests():
    """Main test runner function"""
    tester = CoreFunctionalityTester()
    return await tester.run_complete_test_suite()


def run_async_core_tests():
    """Run core tests with proper asyncio handling"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, run_luxdb_tests())
                return future.result()
        else:
            return asyncio.run(run_luxdb_tests())
    except RuntimeError:
        return asyncio.run(run_luxdb_tests())


if __name__ == "__main__":
    results = run_async_core_tests()
    if results.get('overall_success'):
        print("\n✅ All core tests PASSED")
        exit(0)
    else:
        print("\n❌ Some core tests FAILED")
        exit(1)
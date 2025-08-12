"""
Complete Soul & Being System Tests
==================================

Tests for the complete LuxDB Soul and Being system integration.
"""

import asyncio
import traceback
from datetime import datetime
from typing import Dict, Any

try:
    from luxdb.models.soul import Soul
    from luxdb.models.being import Being
    from luxdb.core.postgre_db import Postgre_db
except ImportError as e:
    print(f"❌ Import error in complete system tests: {e}")
    Soul = None
    Being = None
    Postgre_db = None


async def test_basic_soul_creation():
    """Test basic Soul creation"""
    print("\n🧬 Testing basic Soul creation...")

    if not Soul:
        print("❌ Soul class not available")
        return False

    try:
        genotype = {
            "genesis": {
                "name": "test_basic_soul",
                "type": "basic_test",
                "version": "1.0.0"
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "count": {"py_type": "int", "default": 0}
            }
        }

        soul = await Soul.create(genotype, alias="test_basic_soul")

        if soul and soul.soul_hash:
            print(f"✅ Basic Soul created successfully: {soul.alias}")
            return True
        else:
            print("❌ Basic Soul creation failed")
            return False

    except Exception as e:
        print(f"❌ Basic Soul creation error: {e}")
        return False


async def test_basic_being_creation():
    """Test basic Being creation"""
    print("\n🤖 Testing basic Being creation...")

    if not Soul or not Being:
        print("❌ Soul or Being class not available")
        return False

    try:
        # Create a soul first
        genotype = {
            "genesis": {
                "name": "test_being_soul",
                "type": "being_test",
                "version": "1.0.0"
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "active": {"py_type": "bool", "default": True}
            }
        }

        soul = await Soul.create(genotype, alias="test_being_soul")
        if not soul:
            print("❌ Could not create soul for Being test")
            return False

        # Create being
        being_data = {
            "name": "Test Being",
            "active": True
        }

        being = await Being.create(soul=soul, attributes=being_data, alias="test_basic_being")

        if being and being.ulid:
            print(f"✅ Basic Being created successfully: {being.alias}")
            return True
        else:
            print("❌ Basic Being creation failed")
            return False

    except Exception as e:
        print(f"❌ Basic Being creation error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def test_database_connection():
    """Test database connection"""
    print("\n🔌 Testing database connection...")

    if not Postgre_db:
        print("❌ Database class not available")
        return False

    try:
        pool = await Postgre_db.get_db_pool()
        if pool:
            print("✅ Database connection successful")

            # Test basic query
            async with pool.acquire() as conn:
                result = await conn.fetch("SELECT 1 as test")
                if result and result[0]['test'] == 1:
                    print("✅ Database query successful")
                    return True
                else:
                    print("❌ Database query failed")
                    return False
        else:
            print("❌ Database connection failed")
            return False

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


async def run_complete_system_tests():
    """Run all complete system tests"""
    print("🚀 Running Complete Soul & Being System Tests")
    print("=" * 60)

    results = {
        'database_connection': False,
        'basic_soul_creation': False,
        'basic_being_creation': False,
        'overall_success': False,
        'total_tests': 3,
        'passed_tests': 0,
        'errors': []
    }

    # Run tests
    test_functions = [
        ('Database Connection', test_database_connection),
        ('Basic Soul Creation', test_basic_soul_creation),
        ('Basic Being Creation', test_basic_being_creation)
    ]

    for test_name, test_func in test_functions:
        try:
            result = await test_func()
            if result:
                results['passed_tests'] += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                results['errors'].append(f"{test_name} failed")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results['errors'].append(f"{test_name} error: {str(e)}")

    # Update specific results
    results['database_connection'] = results['passed_tests'] > 0
    results['basic_soul_creation'] = results['passed_tests'] > 1
    results['basic_being_creation'] = results['passed_tests'] > 2

    # Overall success
    results['overall_success'] = results['passed_tests'] == results['total_tests']

    # Cleanup
    await cleanup_test_data()

    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPLETE SYSTEM TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['total_tests'] - results['passed_tests']}")

    if results['overall_success']:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
        if results['errors']:
            print("Errors:")
            for error in results['errors']:
                print(f"  - {error}")

    return results


async def cleanup_test_data():
    """Cleanup test data"""
    print("\n🧹 Cleaning up test data...")

    if not Postgre_db:
        return

    try:
        pool = await Postgre_db.get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                # Clean up test beings
                await conn.execute("DELETE FROM beings WHERE alias LIKE 'test_%'")
                # Clean up test souls
                await conn.execute("DELETE FROM souls WHERE alias LIKE 'test_%'")

                print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")


if __name__ == "__main__":
    asyncio.run(run_complete_system_tests())
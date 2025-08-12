#!/usr/bin/env python3
"""
LuxDB Test Runner
================

Comprehensive test runner for LuxDB system.
"""

import asyncio
import argparse
import sys
import traceback
from typing import Dict, Any
from datetime import datetime

# Import test modules
def safe_import_test_modules():
    """Safely import test modules with fallbacks"""
    modules = {}

    try:
        from tests.test_core_functionality import run_luxdb_tests
        modules['core'] = run_luxdb_tests
        print("✅ Core functionality tests imported")
    except ImportError as e:
        print(f"⚠️ Core tests not available: {e}")
        modules['core'] = None

    try:
        from tests.test_integration_soul_being_functions import run_integration_tests
        modules['integration'] = run_integration_tests
        print("✅ Integration tests imported")
    except ImportError as e:
        print(f"⚠️ Integration tests not available: {e}")
        modules['integration'] = None

    try:
        from tests.test_complete_soul_being_system import run_complete_system_tests
        modules['complete'] = run_complete_system_tests
        print("✅ Complete system tests imported")
    except ImportError as e:
        print(f"⚠️ Complete system tests not available: {e}")
        modules['complete'] = None

    return modules

# Get available test modules
TEST_MODULES = safe_import_test_modules()


async def run_initialization_tests():
    """Run initialization and basic functionality tests"""
    print("🔧 Running initialization tests...")

    results = {
        'database_connection': False,
        'basic_operations': False,
        'overall_success': False,
        'errors': []
    }

    try:
        # Test database connection
        from database.postgre_db import Postgre_db

        try:
            pool = await Postgre_db.get_db_pool()
            if pool:
                results['database_connection'] = True
                print("✅ Database connection successful")

                # Test basic table operations
                async with pool.acquire() as conn:
                    # Check if tables exist
                    tables = await conn.fetch("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name IN ('souls', 'beings')
                    """)

                    table_names = [row['table_name'] for row in tables]
                    print(f"Found tables: {table_names}")

                    if len(table_names) >= 2:
                        results['basic_operations'] = True
                        print("✅ Basic database tables exist")
                    else:
                        results['errors'].append(f"Missing required database tables. Found: {table_names}")

            else:
                results['errors'].append("Database connection failed - no pool")

        except Exception as db_e:
            results['errors'].append(f"Database error: {str(db_e)}")
            print(f"❌ Database error: {str(db_e)}")

    except ImportError as import_e:
        results['errors'].append(f"Import error: {str(import_e)}")
        print(f"❌ Import error: {str(import_e)}")
    except Exception as e:
        results['errors'].append(f"Initialization test error: {str(e)}")
        print(f"❌ Initialization test error: {str(e)}")

    results['overall_success'] = (results['database_connection'] and
                                 results['basic_operations'] and
                                 len(results['errors']) == 0)

    if results['overall_success']:
        print("🎉 Initialization tests PASSED")
    else:
        print(f"❌ Initialization tests FAILED. Errors: {results['errors']}")

    return results


async def main(args=None):
    """Main test runner function"""
    if not args:
        parser = argparse.ArgumentParser(description='LuxDB Test Runner')
        parser.add_argument('--core-only', action='store_true', help='Run only core functionality tests')
        parser.add_argument('--integration-only', action='store_true', help='Run only integration tests')
        parser.add_argument('--complete-system', action='store_true', help='Run complete system tests')
        parser.add_argument('--init-only', action='store_true', help='Run only initialization tests')
        parser.add_argument('--evolution-only', action='store_true', help='Run only evolution system tests')
        args = parser.parse_args()

    print("🚀 LuxDB Test Runner Starting...")
    print("=" * 50)

    results = {}

    if args.core_only:
        print("🧠 Running core functionality tests only...")
        if TEST_MODULES.get('core'):
            try:
                core_results = await TEST_MODULES['core']()
                results['core'] = core_results
                if core_results.get('overall_success'):
                    print("\n✅ Core tests PASSED")
                    return 0
                else:
                    print("\n❌ Core tests FAILED")
                    return 1
            except Exception as e:
                print(f"❌ Core tests error: {e}")
                return 1
        else:
            print("❌ Core tests not available")
            return 1

    elif args.integration_only:
        print("🔗 Running integration tests only...")
        if TEST_MODULES.get('integration'):
            try:
                passed, failed = await TEST_MODULES['integration']()
                results['integration'] = {'passed': passed, 'failed': failed}
                if failed == 0:
                    print("\n✅ Integration tests PASSED")
                    return 0
                else:
                    print("\n❌ Integration tests FAILED")
                    return 1
            except Exception as e:
                print(f"❌ Integration tests error: {e}")
                return 1
        else:
            print("❌ Integration tests not available")
            return 1

    elif args.complete_system:
        print("🧬 Running complete system tests...")
        if TEST_MODULES.get('complete'):
            try:
                complete_results = await TEST_MODULES['complete']()
                results['complete_system'] = complete_results
                if complete_results.get('overall_success'):
                    print("\n✅ Complete system tests PASSED")
                    return 0
                else:
                    print("\n❌ Complete system tests FAILED")
                    return 1
            except Exception as e:
                print(f"❌ Complete system tests error: {e}")
                return 1
        else:
            print("❌ Complete system tests not available")
            return 1
    elif args.init_only:
        print("🔧 Running initialization tests only...")
        init_results = await run_initialization_tests()
        results['initialization'] = init_results
        if init_results.get('overall_success'):
            print("\n✅ Initialization tests PASSED")
            return 0
        else:
            print("\n❌ Initialization tests FAILED")
            return 1

    elif args.evolution_only:
        print("Running evolution system tests only...")
        try:
            from tests.test_being_evolution_system import run_being_evolution_tests
            evolution_results = await run_being_evolution_tests()
            results['evolution'] = evolution_results
            if evolution_results.get('overall_success'):
                print("\n✅ Evolution system tests PASSED")
                return 0
            else:
                print("\n❌ Evolution system tests FAILED")
                return 1
        except ImportError:
            print("❌ Evolution system tests not available")
            return 1
        except Exception as e:
            print(f"❌ Evolution system tests error: {e}")
            return 1


    else:
        # Run all available test suites
        print("📋 Running all available test suites...")

        # Initialization tests
        print("\n" + "="*50)
        init_results = await run_initialization_tests()
        results['initialization'] = init_results

        # Core functionality tests
        if TEST_MODULES.get('core'):
            print("\n" + "="*50)
            print("🧠 Running core functionality tests...")
            try:
                core_results = await TEST_MODULES['core']()
                results['core'] = core_results
            except Exception as e:
                print(f"❌ Core tests error: {e}")
                results['core'] = {'overall_success': False, 'errors': [str(e)]}
        else:
            print("\n" + "="*50)
            print("⚠️ Core tests not available")
            results['core'] = {'overall_success': False, 'errors': ["Not available"]}


        # Integration tests
        if TEST_MODULES.get('integration'):
            print("\n" + "="*50)
            print("🔗 Running integration tests...")
            try:
                passed, failed = await TEST_MODULES['integration']()
                results['integration'] = {'passed': passed, 'failed': failed}
            except Exception as e:
                print(f"❌ Integration tests error: {e}")
                results['integration'] = {'passed': 0, 'failed': float('inf'), 'errors': [str(e)]}
        else:
            print("\n" + "="*50)
            print("⚠️ Integration tests not available")
            results['integration'] = {'passed': 0, 'failed': float('inf'), 'errors': ["Not available"]}


        # Complete system tests
        if TEST_MODULES.get('complete'):
            print("\n" + "="*50)
            print("🧬 Running complete system tests...")
            try:
                complete_results = await TEST_MODULES['complete']()
                results['complete_system'] = complete_results
            except Exception as e:
                print(f"❌ Complete system tests error: {e}")
                results['complete_system'] = {'overall_success': False, 'errors': [str(e)]}
        else:
            print("\n" + "="*50)
            print("⚠️ Complete system tests not available")
            results['complete_system'] = {'overall_success': False, 'errors': ["Not available"]}


        # Overall result check
        overall_success = (
            results.get('initialization', {}).get('overall_success', False) and
            results.get('core', {}).get('overall_success', False) and
            results.get('integration', {}).get('failed', float('inf')) == 0 and
            results.get('complete_system', {}).get('overall_success', False)
        )

        if overall_success:
            print("\n✅ All available tests PASSED")
            return 0
        else:
            print("\n❌ Some tests FAILED")
            return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n🚨 Critical error during test execution: {e}")
        traceback.print_exc()
        sys.exit(1)
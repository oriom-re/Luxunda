#!/usr/bin/env python3
"""
LuxDB Test Runner Script
========================

Simple script to run all LuxDB tests and get certification report.

Usage:
    python run_tests.py
    python run_tests.py --core-only
    python run_tests.py --integration-only
    python run_tests.py --save-report
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add tests directory to path
tests_dir = Path(__file__).parent / "tests"
sys.path.insert(0, str(tests_dir))

from tests.test_runner import main as run_all_tests
from tests.test_core_functionality import run_luxdb_tests
from tests.test_integration import run_integration_tests


async def main():
    parser = argparse.ArgumentParser(description="LuxDB Test Runner")
    parser.add_argument("--core-only", action="store_true", help="Run only core functionality tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--init-only", action="store_true", help="Run only initialization tests")
    parser.add_argument("--evolution-only", action="store_true", help="Run only evolution system tests")
    parser.add_argument("--save-report", action="store_true", help="Save detailed report to file")
    parser.add_argument("--quick", action="store_true", help="Run quick test subset")

    args = parser.parse_args()

    print("🚀 LuxDB Test Suite")
    print("=" * 50)

    if args.core_only:
        print("Running core functionality tests only...")
        results = await run_luxdb_tests()

        if results.get('overall_success'):
            print("\n✅ Core tests PASSED")
            return 0
        else:
            print("\n❌ Core tests FAILED")
            return 1

    elif args.integration_only:
        print("Running integration tests only...")
        results = await run_integration_tests()

        if results.get('overall_success'):
            print("\n✅ Integration tests PASSED")
            return 0
        else:
            print("\n❌ Integration tests FAILED")
            return 1

    elif args.init_only:
        print("Running initialization tests only...")
        from tests.test_system_initialization import run_initialization_tests
        results = await run_initialization_tests()

        if results.get('overall_success'):
            print("\n✅ Initialization tests PASSED")
            return 0
        else:
            print("\n❌ Initialization tests FAILED")
            return 1
    
    elif args.evolution_only:
        print("Running evolution system tests only...")
        from tests.test_being_evolution_system import run_being_evolution_tests
        results = await run_being_evolution_tests()

        if results.get('overall_success'):
            print("\n✅ Evolution system tests PASSED")
            return 0
        else:
            print("\n❌ Evolution system tests FAILED")
            return 1

    else:
        # Run complete test suite
        return await run_all_tests()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n🚨 Critical error: {e}")
        sys.exit(1)
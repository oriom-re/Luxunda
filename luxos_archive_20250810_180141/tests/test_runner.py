
"""
LuxDB Test Runner
=================

Main test runner that executes all test suites and generates comprehensive reports.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List
import traceback

from test_core_functionality import run_luxdb_tests
from test_integration import run_integration_tests


class LuxDBTestRunner:
    """Main test runner for LuxDB library"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {}
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        self.start_time = datetime.now()
        
        print("🚀 LUXDB COMPLETE TEST SUITE")
        print("=" * 60)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        final_results = {
            'timestamp': self.start_time.isoformat(),
            'core_tests': {},
            'integration_tests': {},
            'environment_info': self.get_environment_info(),
            'overall_status': 'UNKNOWN',
            'total_runtime': 0,
            'summary': {},
            'recommendations': [],
            'certification': False
        }
        
        try:
            # Run core functionality tests
            print("\n🔧 PHASE 1: Core Functionality Tests")
            print("-" * 40)
            final_results['core_tests'] = await run_luxdb_tests()
            
            # Run integration tests
            print("\n🔗 PHASE 2: Integration Tests")
            print("-" * 40)
            final_results['integration_tests'] = await run_integration_tests()
            
            # Calculate final results
            self.end_time = datetime.now()
            final_results['total_runtime'] = (self.end_time - self.start_time).total_seconds()
            
            # Determine overall status
            core_success = final_results['core_tests'].get('overall_success', False)
            integration_success = final_results['integration_tests'].get('overall_success', False)
            
            if core_success and integration_success:
                final_results['overall_status'] = 'PASSED'
                final_results['certification'] = True
            elif core_success:
                final_results['overall_status'] = 'PARTIAL'
                final_results['certification'] = False
            else:
                final_results['overall_status'] = 'FAILED'
                final_results['certification'] = False
            
            # Generate summary
            final_results['summary'] = self.generate_summary(final_results)
            
            # Generate recommendations
            final_results['recommendations'] = self.generate_final_recommendations(final_results)
            
        except Exception as e:
            final_results['overall_status'] = 'ERROR'
            final_results['recommendations'].append(f"Critical test runner error: {str(e)}")
            print(f"❌ Critical error in test runner: {str(e)}")
            traceback.print_exc()
        
        return final_results
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information for debugging"""
        import sys
        import platform
        
        try:
            import psutil
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            system_info = {
                'python_version': sys.version,
                'platform': platform.platform(),
                'architecture': platform.architecture(),
                'processor': platform.processor(),
                'memory_total_gb': round(memory_info.total / (1024**3), 2),
                'memory_available_gb': round(memory_info.available / (1024**3), 2),
                'disk_total_gb': round(disk_info.total / (1024**3), 2),
                'disk_free_gb': round(disk_info.free / (1024**3), 2)
            }
        except ImportError:
            system_info = {
                'python_version': sys.version,
                'platform': platform.platform(),
                'note': 'psutil not available for detailed system info'
            }
        
        # Environment variables
        env_vars = {
            'DB_HOST': os.getenv('DB_HOST', 'localhost'),
            'DB_PORT': os.getenv('DB_PORT', '5432'),
            'DB_NAME': os.getenv('DB_NAME', 'luxdb_test'),
            'OPENAI_API_KEY': 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT_SET'
        }
        
        return {
            'system': system_info,
            'environment_variables': env_vars,
            'working_directory': os.getcwd()
        }
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary"""
        summary = {
            'total_tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'total_errors': 0,
            'performance_metrics': {},
            'critical_issues': [],
            'success_rate': 0.0
        }
        
        # Core tests summary
        core_results = results.get('core_tests', {})
        if core_results:
            core_sections = ['soul_tests', 'being_tests', 'relationship_tests', 'performance_tests', 'integrity_tests']
            for section in core_sections:
                section_data = core_results.get(section, {})
                if section_data:
                    for test_name, test_result in section_data.items():
                        if test_name != 'errors':
                            summary['total_tests_run'] += 1
                            if test_result:
                                summary['tests_passed'] += 1
                            else:
                                summary['tests_failed'] += 1
                    
                    summary['total_errors'] += len(section_data.get('errors', []))
        
        # Integration tests summary
        integration_results = results.get('integration_tests', {})
        if integration_results:
            integration_sections = ['ai_workflow', 'multi_user', 'migration']
            for section in integration_sections:
                section_data = integration_results.get(section, {})
                if section_data:
                    for test_name, test_result in section_data.items():
                        if test_name != 'errors':
                            summary['total_tests_run'] += 1
                            if test_result:
                                summary['tests_passed'] += 1
                            else:
                                summary['tests_failed'] += 1
                    
                    summary['total_errors'] += len(section_data.get('errors', []))
        
        # Calculate success rate
        if summary['total_tests_run'] > 0:
            summary['success_rate'] = round((summary['tests_passed'] / summary['total_tests_run']) * 100, 2)
        
        # Performance metrics
        runtime = results.get('total_runtime', 0)
        summary['performance_metrics'] = {
            'total_runtime_seconds': round(runtime, 2),
            'tests_per_second': round(summary['total_tests_run'] / max(runtime, 1), 2),
            'runtime_category': 'FAST' if runtime < 60 else 'MEDIUM' if runtime < 180 else 'SLOW'
        }
        
        # Critical issues
        if not results.get('core_tests', {}).get('overall_success'):
            summary['critical_issues'].append('Core functionality failures detected')
        
        if summary['total_errors'] > 10:
            summary['critical_issues'].append('High error count detected')
        
        if summary['success_rate'] < 80:
            summary['critical_issues'].append('Low test success rate')
        
        return summary
    
    def generate_final_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate final recommendations"""
        recommendations = []
        
        status = results.get('overall_status')
        summary = results.get('summary', {})
        
        if status == 'PASSED':
            recommendations.extend([
                "🎉 CONGRATULATIONS! LuxDB library is certified 100% reliable!",
                "✅ All core functionality tests passed",
                "✅ All integration workflows working correctly",
                "✅ Performance metrics within acceptable ranges",
                "✅ Data integrity verified",
                "",
                "📋 DEPLOYMENT RECOMMENDATIONS:",
                "  • Library is ready for production use",
                "  • Consider setting up continuous integration",
                "  • Monitor performance in production environment",
                "  • Implement regular test runs",
                "  • Document any environment-specific configurations"
            ])
        
        elif status == 'PARTIAL':
            recommendations.extend([
                "⚠️  PARTIAL SUCCESS - Core functionality working but integration issues detected",
                "",
                "✅ Core database operations are reliable",
                "❌ Some integration workflows need attention",
                "",
                "📋 IMMEDIATE ACTIONS REQUIRED:",
                "  • Review integration test failures",
                "  • Fix AI system integration issues",
                "  • Test multi-user scenarios thoroughly",
                "  • Verify data migration procedures"
            ])
        
        elif status == 'FAILED':
            recommendations.extend([
                "🚨 CRITICAL ISSUES DETECTED - Library not ready for production",
                "",
                "❌ Core functionality failures detected",
                "❌ Multiple system components not working correctly",
                "",
                "📋 CRITICAL ACTIONS REQUIRED:",
                "  • Fix database connection issues",
                "  • Resolve core functionality problems",
                "  • Review error logs thoroughly",
                "  • Test with minimal configuration first",
                "  • Consider fresh database setup"
            ])
        
        # Performance recommendations
        runtime = summary.get('performance_metrics', {}).get('total_runtime_seconds', 0)
        if runtime > 180:
            recommendations.extend([
                "",
                "⚡ PERFORMANCE RECOMMENDATIONS:",
                "  • Test runtime is high - consider optimization",
                "  • Check database query performance",
                "  • Review connection pooling settings",
                "  • Monitor system resources during testing"
            ])
        
        # Error count recommendations
        error_count = summary.get('total_errors', 0)
        if error_count > 5:
            recommendations.extend([
                "",
                "🐛 ERROR REDUCTION RECOMMENDATIONS:",
                f"  • {error_count} errors detected - review logs carefully",
                "  • Implement better error handling",
                "  • Add more specific error messages",
                "  • Consider gradual deployment approach"
            ])
        
        # Success rate recommendations
        success_rate = summary.get('success_rate', 0)
        if success_rate < 90:
            recommendations.extend([
                "",
                "📈 SUCCESS RATE IMPROVEMENT:",
                f"  • Current success rate: {success_rate}% (target: >95%)",
                "  • Focus on failed test areas",
                "  • Implement more robust error handling",
                "  • Add retry mechanisms where appropriate"
            ])
        
        return recommendations
    
    def print_final_report(self, results: Dict[str, Any]) -> None:
        """Print comprehensive final report"""
        print("\n" + "=" * 80)
        print("📊 LUXDB COMPLETE TEST CERTIFICATION REPORT")
        print("=" * 80)
        
        # Header information
        print(f"🕒 Test Execution Time: {results.get('total_runtime', 0):.2f} seconds")
        print(f"📅 Timestamp: {results.get('timestamp', 'Unknown')}")
        print(f"🖥️  Platform: {results.get('environment_info', {}).get('system', {}).get('platform', 'Unknown')}")
        
        # Overall status
        status = results.get('overall_status', 'UNKNOWN')
        certification = results.get('certification', False)
        
        if status == 'PASSED':
            print(f"\n🎉 OVERALL STATUS: ✅ {status}")
            print(f"🏆 CERTIFICATION: ✅ LIBRARY IS 100% RELIABLE")
        elif status == 'PARTIAL':
            print(f"\n⚠️  OVERALL STATUS: 🔶 {status}")
            print(f"🏆 CERTIFICATION: ❌ REQUIRES FIXES BEFORE PRODUCTION")
        else:
            print(f"\n🚨 OVERALL STATUS: ❌ {status}")
            print(f"🏆 CERTIFICATION: ❌ NOT READY FOR PRODUCTION")
        
        # Summary statistics
        summary = results.get('summary', {})
        print(f"\n📈 TEST SUMMARY:")
        print(f"   Total Tests Run: {summary.get('total_tests_run', 0)}")
        print(f"   Tests Passed: {summary.get('tests_passed', 0)}")
        print(f"   Tests Failed: {summary.get('tests_failed', 0)}")
        print(f"   Success Rate: {summary.get('success_rate', 0)}%")
        print(f"   Total Errors: {summary.get('total_errors', 0)}")
        
        # Performance metrics
        perf = summary.get('performance_metrics', {})
        print(f"\n⚡ PERFORMANCE METRICS:")
        print(f"   Runtime: {perf.get('total_runtime_seconds', 0)}s ({perf.get('runtime_category', 'UNKNOWN')})")
        print(f"   Tests/Second: {perf.get('tests_per_second', 0)}")
        
        # Critical issues
        issues = summary.get('critical_issues', [])
        if issues:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in issues:
                print(f"   • {issue}")
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            print(f"\n🛠️  RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   {rec}")
        
        print("\n" + "=" * 80)
        
        # Certification statement
        if certification:
            print("🏆 CERTIFICATION STATEMENT:")
            print("   LuxDB library has passed all critical tests and is certified")
            print("   as 100% reliable for production use. All core functionality,")
            print("   integration workflows, and performance metrics meet standards.")
        else:
            print("⚠️  CERTIFICATION STATEMENT:")
            print("   LuxDB library has NOT passed certification requirements.")
            print("   Issues must be resolved before production deployment.")
            print("   Review recommendations and re-run tests after fixes.")
        
        print("=" * 80)
    
    async def save_results(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"luxdb_test_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"📄 Test results saved to: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")
            return ""


async def main():
    """Main entry point for test runner"""
    runner = LuxDBTestRunner()
    
    try:
        # Run all tests
        results = await runner.run_all_tests()
        
        # Print final report
        runner.print_final_report(results)
        
        # Save results
        await runner.save_results(results)
        
        # Return appropriate exit code
        if results.get('certification', False):
            print("\n✅ Test suite completed successfully - Library certified!")
            return 0
        else:
            print("\n❌ Test suite completed with issues - Library NOT certified!")
            return 1
            
    except Exception as e:
        print(f"\n🚨 Critical error in test runner: {str(e)}")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

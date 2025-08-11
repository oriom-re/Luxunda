
"""
LuxDB Complete Test Suite Runner
===============================

Kompletny runner wszystkich testów jednostkowych i integracyjnych.
"""

import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Import wszystkich modułów testowych
from test_soul_operations import run_soul_tests
from test_being_operations import run_being_tests
from test_system_initialization import run_initialization_tests
from test_core_functionality import run_luxdb_tests
from test_integration import run_integration_tests
from test_integration_soul_being_functions import run_integration_tests as run_soul_being_function_tests


class CompleteTestSuite:
    """Kompletny pakiet testów LuxDB"""
    
    def __init__(self):
        self.start_time = None
        self.results = {}
        self.total_passed = 0
        self.total_failed = 0
    
    async def run_all_tests(self) -> Dict[str, any]:
        """Uruchom wszystkie testy"""
        self.start_time = datetime.now()
        
        print("🌟 LUXDB COMPLETE TEST CERTIFICATION SUITE")
        print("=" * 70)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Kolejność testów - od najbardziej podstawowych do złożonych
        test_suites = [
            ("🔧 System Initialization", run_initialization_tests),
            ("🧠 Soul Operations", run_soul_tests),
            ("🤖 Being Operations", run_being_tests),
            ("🔄 Soul+Being+Functions Integration", run_soul_being_function_tests),
            ("⚙️  Core Functionality", run_luxdb_tests),
            ("🔗 Integration Tests", run_integration_tests)
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n{suite_name}")
            print("-" * 50)
            
            try:
                suite_start = time.time()
                
                if test_func == run_luxdb_tests or test_func == run_integration_tests:
                    # Te funkcje zwracają dict z wynikami
                    result = await test_func()
                    if isinstance(result, dict):
                        passed = result.get('total_tests_passed', 0) 
                        failed = result.get('total_tests_failed', 0)
                        if passed == 0 and failed == 0:
                            # Fallback - policz z success rate
                            success_rate = result.get('summary', {}).get('success_rate', 0)
                            total_tests = result.get('summary', {}).get('total_tests_run', 0)
                            passed = int(total_tests * success_rate / 100)
                            failed = total_tests - passed
                    else:
                        passed, failed = 0, 1
                else:
                    # Te funkcje zwracają tuple (passed, failed)
                    passed, failed = await test_func()
                
                suite_time = time.time() - suite_start
                
                self.results[suite_name] = {
                    'passed': passed,
                    'failed': failed,
                    'duration': suite_time,
                    'success': failed == 0
                }
                
                self.total_passed += passed
                self.total_failed += failed
                
                status = "✅ PASSED" if failed == 0 else "❌ FAILED"
                print(f"Result: {status} ({passed} passed, {failed} failed, {suite_time:.2f}s)")
                
            except Exception as e:
                print(f"❌ Suite failed with error: {e}")
                self.results[suite_name] = {
                    'passed': 0,
                    'failed': 1,
                    'duration': 0,
                    'success': False,
                    'error': str(e)
                }
                self.total_failed += 1
        
        return self.generate_final_report()
    
    def generate_final_report(self) -> Dict[str, any]:
        """Generuj końcowy raport"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        total_tests = self.total_passed + self.total_failed
        success_rate = (self.total_passed / max(total_tests, 1)) * 100
        
        # Determine certification level
        if self.total_failed == 0 and self.total_passed > 0:
            certification = "🏆 100% RELIABLE - PRODUCTION READY"
            status = "CERTIFIED"
        elif success_rate >= 90:
            certification = "⚠️  PARTIAL SUCCESS - MINOR ISSUES"
            status = "CONDITIONAL"
        else:
            certification = "🚨 CRITICAL ISSUES - NOT READY"
            status = "FAILED"
        
        report = {
            'status': status,
            'certification': certification,
            'total_tests': total_tests,
            'total_passed': self.total_passed,
            'total_failed': self.total_failed,
            'success_rate': round(success_rate, 2),
            'total_duration': round(total_duration, 2),
            'suites': self.results,
            'recommendations': self.generate_recommendations()
        }
        
        self.print_final_report(report)
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generuj rekomendacje na podstawie wyników"""
        recommendations = []
        
        if self.total_failed == 0:
            recommendations.extend([
                "🎉 GRATULACJE! System LuxDB przeszedł wszystkie testy!",
                "✅ System jest gotowy do użycia produkcyjnego",
                "✅ Wszystkie komponenty działają poprawnie",
                "📋 Zalecenia:",
                "  • Uruchamiaj testy regularnie podczas rozwoju",
                "  • Monitoruj wydajność w środowisku produkcyjnym",
                "  • Dokumentuj zmiany w API dla użytkowników"
            ])
        elif self.total_failed <= 3:
            recommendations.extend([
                "⚠️  System ma niewielkie problemy do rozwiązania",
                "📋 Natychmiastowe działania:",
                "  • Przejrzyj błędne testy i ich przyczyny",
                "  • Napraw krytyczne problemy przed wdrożeniem",
                "  • Uruchom testy ponownie po poprawkach"
            ])
        else:
            recommendations.extend([
                "🚨 System wymaga znaczących poprawek",
                "📋 Krytyczne działania:",
                "  • Zatrzymaj wdrożenie do produkcji",
                "  • Przeanalizuj wszystkie błędy testów",
                "  • Napraw podstawowe problemy systemu",
                "  • Przeprowadź pełną walidację po poprawkach"
            ])
        
        # Rekomendacje specyficzne dla suite'ów
        for suite_name, result in self.results.items():
            if not result['success']:
                if "Initialization" in suite_name:
                    recommendations.append("  • Sprawdź konfigurację bazy danych i zmienne środowiskowe")
                elif "Soul" in suite_name:
                    recommendations.append("  • Zweryfikuj walidację genotypów i operacje Soul")
                elif "Being" in suite_name:
                    recommendations.append("  • Przejrzyj operacje CRUD na bytach")
                elif "Core" in suite_name:
                    recommendations.append("  • Sprawdź podstawową funkcjonalność systemu")
                elif "Integration" in suite_name:
                    recommendations.append("  • Zweryfikuj integrację między komponentami")
        
        return recommendations
    
    def print_final_report(self, report: Dict[str, any]):
        """Wydrukuj końcowy raport"""
        print("\n" + "=" * 70)
        print("📊 LUXDB COMPLETE CERTIFICATION REPORT")
        print("=" * 70)
        
        print(f"\n🏆 CERTIFICATION STATUS: {report['certification']}")
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Tests: {report['total_tests']}")
        print(f"   Passed: {report['total_passed']} ✅")
        print(f"   Failed: {report['total_failed']} ❌")
        print(f"   Success Rate: {report['success_rate']}%")
        print(f"   Duration: {report['total_duration']}s")
        
        print(f"\n📋 SUITE BREAKDOWN:")
        for suite_name, result in report['suites'].items():
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {suite_name}: {result['passed']}/{result['passed'] + result['failed']} ({result['duration']:.2f}s)")
        
        print(f"\n🛠️  RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"   {rec}")
        
        if report['status'] == "CERTIFIED":
            print(f"\n🎊 SYSTEM CERTIFICATION COMPLETE!")
            print(f"   LuxDB is certified as 100% reliable and ready for production use.")
        else:
            print(f"\n⚠️  CERTIFICATION INCOMPLETE")
            print(f"   Please address the issues above before production deployment.")
        
        print("=" * 70)


async def main():
    """Główna funkcja uruchamiająca testy"""
    suite = CompleteTestSuite()
    
    try:
        results = await suite.run_all_tests()
        
        # Return appropriate exit code
        if results['status'] == 'CERTIFIED':
            print("\n✅ All tests passed - System certified!")
            return 0
        elif results['status'] == 'CONDITIONAL':
            print("\n⚠️  Tests completed with minor issues - Review required")
            return 1
        else:
            print("\n❌ Tests failed - System not ready for production")
            return 2
            
    except Exception as e:
        print(f"\n🚨 Critical error in test suite: {e}")
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

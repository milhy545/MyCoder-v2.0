#!/usr/bin/env python3
"""
Comprehensive Stress Test Runner for Enhanced MyCoder v2.0

This script orchestrates all stress tests and provides detailed reporting:
- Concurrency stress tests
- Memory pressure tests
- Q9550 thermal stress tests
- Network failure scenarios
- System limit boundaries
- Edge case handling
- Performance benchmarking

Usage:
    python tests/stress/run_stress_tests.py --all
    python tests/stress/run_stress_tests.py --quick
    python tests/stress/run_stress_tests.py --thermal  # Requires Q9550
    python tests/stress/run_stress_tests.py --suite concurrency
    python tests/stress/run_stress_tests.py --report-only
"""

import subprocess
import argparse
import time
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class StressTestResult:
    """Individual stress test result"""

    test_name: str
    suite: str
    status: str  # passed, failed, skipped, error
    duration: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class StressTestSuite:
    """Stress test suite configuration"""

    name: str
    description: str
    test_files: List[str]
    test_classes: List[str]
    requirements: List[str] = None
    timeout_minutes: int = 30


class StressTestRunner:
    """Comprehensive stress test runner"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.results: List[StressTestResult] = []
        self.start_time = time.time()

        # Define test suites
        self.suites = {
            "concurrency": StressTestSuite(
                name="Concurrency Stress",
                description="High load concurrent request handling",
                test_files=["tests/stress/test_mycoder_stress.py"],
                test_classes=["TestConcurrencyStress"],
                timeout_minutes=15,
            ),
            "memory": StressTestSuite(
                name="Memory Pressure",
                description="Memory usage and leak prevention",
                test_files=["tests/stress/test_mycoder_stress.py"],
                test_classes=["TestMemoryStress"],
                timeout_minutes=20,
            ),
            "thermal": StressTestSuite(
                name="Thermal Management",
                description="Q9550 thermal limit handling",
                test_files=["tests/stress/test_mycoder_stress.py"],
                test_classes=["TestThermalStress"],
                requirements=["Q9550 thermal system"],
                timeout_minutes=25,
            ),
            "network": StressTestSuite(
                name="Network Stress",
                description="Network failure and timeout scenarios",
                test_files=["tests/stress/test_mycoder_stress.py"],
                test_classes=["TestNetworkStress"],
                timeout_minutes=20,
            ),
            "edges": StressTestSuite(
                name="Edge Cases",
                description="Malformed inputs and boundary conditions",
                test_files=["tests/stress/test_mycoder_stress.py"],
                test_classes=["TestEdgeCaseStress"],
                timeout_minutes=15,
            ),
            "limits": StressTestSuite(
                name="System Limits",
                description="Configuration and system boundaries",
                test_files=["tests/stress/test_system_limits.py"],
                test_classes=[
                    "TestConfigurationLimits",
                    "TestProviderSwitchingLimits",
                    "TestSessionManagementLimits",
                    "TestToolRegistryLimits",
                    "TestSystemRestartStress",
                ],
                timeout_minutes=25,
            ),
        }

    def check_requirements(self) -> Dict[str, bool]:
        """Check system requirements for stress tests"""
        requirements = {}

        # Check Q9550 thermal system
        thermal_script = Path(
            "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh"
        )
        requirements["Q9550 thermal system"] = thermal_script.exists()

        # Check Python packages
        try:
            import pytest

            requirements["pytest"] = True
        except ImportError:
            requirements["pytest"] = False

        # Check system resources
        import psutil

        requirements["memory_gb"] = psutil.virtual_memory().total / (1024**3)
        requirements["cpu_cores"] = psutil.cpu_count()
        requirements["disk_gb"] = psutil.disk_usage("/").free / (1024**3)

        return requirements

    def run_test_suite(
        self, suite_name: str, verbose: bool = True
    ) -> List[StressTestResult]:
        """Run a specific stress test suite"""
        if suite_name not in self.suites:
            raise ValueError(f"Unknown test suite: {suite_name}")

        suite = self.suites[suite_name]
        results = []

        if verbose:
            print(f"\n{'='*60}")
            print(f"🔥 RUNNING STRESS SUITE: {suite.name}")
            print(f"📝 Description: {suite.description}")
            print(f"⏱️  Timeout: {suite.timeout_minutes} minutes")
            print(f"{'='*60}")

        # Check requirements
        if suite.requirements:
            requirements = self.check_requirements()
            missing_reqs = []

            for req in suite.requirements:
                if req not in requirements or not requirements[req]:
                    missing_reqs.append(req)

            if missing_reqs:
                result = StressTestResult(
                    test_name=suite.name,
                    suite=suite_name,
                    status="skipped",
                    duration=0.0,
                    details={"missing_requirements": missing_reqs},
                    error_message=f"Missing requirements: {', '.join(missing_reqs)}",
                )
                results.append(result)

                if verbose:
                    print(
                        f"⏭️  SKIPPED: Missing requirements: {', '.join(missing_reqs)}"
                    )

                return results

        # Run tests for each class
        for test_class in suite.test_classes:
            for test_file in suite.test_files:
                test_path = f"{test_file}::{test_class}"

                if verbose:
                    print(f"\n🧪 Running {test_class} from {test_file}...")

                start_time = time.time()

                try:
                    # Build pytest command
                    cmd = [
                        sys.executable,
                        "-m",
                        "pytest",
                        test_path,
                        "-v",
                        "-s",
                        "--tb=short",
                        f"--timeout={suite.timeout_minutes * 60}",
                        "--maxfail=3",  # Stop after 3 failures
                    ]

                    # Run test
                    result = subprocess.run(
                        cmd,
                        cwd=self.project_root,
                        capture_output=True,
                        text=True,
                        timeout=suite.timeout_minutes * 60
                        + 60,  # Extra minute for cleanup
                    )

                    duration = time.time() - start_time

                    # Parse results
                    if result.returncode == 0:
                        status = "passed"
                        error_message = None
                    elif "SKIPPED" in result.stdout or "skipped" in result.stdout:
                        status = "skipped"
                        error_message = "Test conditions not met"
                    else:
                        status = "failed"
                        error_message = self._extract_error_summary(
                            result.stdout, result.stderr
                        )

                    test_result = StressTestResult(
                        test_name=test_class,
                        suite=suite_name,
                        status=status,
                        duration=duration,
                        details={
                            "stdout_lines": len(result.stdout.split("\n")),
                            "stderr_lines": len(result.stderr.split("\n")),
                            "return_code": result.returncode,
                        },
                        error_message=error_message,
                    )

                    results.append(test_result)

                    # Print result
                    status_emoji = {
                        "passed": "✅",
                        "failed": "❌",
                        "skipped": "⏭️",
                        "error": "🚨",
                    }[status]
                    if verbose:
                        print(
                            f"{status_emoji} {test_class}: {status.upper()} ({duration:.1f}s)"
                        )
                        if error_message and status == "failed":
                            print(f"   Error: {error_message[:100]}...")

                except subprocess.TimeoutExpired:
                    duration = time.time() - start_time
                    test_result = StressTestResult(
                        test_name=test_class,
                        suite=suite_name,
                        status="error",
                        duration=duration,
                        details={"error_type": "timeout"},
                        error_message=f"Test timed out after {suite.timeout_minutes} minutes",
                    )
                    results.append(test_result)

                    if verbose:
                        print(f"⏱️ {test_class}: TIMEOUT ({duration:.1f}s)")

                except Exception as e:
                    duration = time.time() - start_time
                    test_result = StressTestResult(
                        test_name=test_class,
                        suite=suite_name,
                        status="error",
                        duration=duration,
                        details={
                            "error_type": "exception",
                            "exception_type": type(e).__name__,
                        },
                        error_message=str(e),
                    )
                    results.append(test_result)

                    if verbose:
                        print(f"🚨 {test_class}: ERROR - {type(e).__name__}")

        return results

    def _extract_error_summary(self, stdout: str, stderr: str) -> str:
        """Extract concise error summary from test output"""
        # Look for common error patterns
        error_indicators = [
            "FAILED",
            "AssertionError",
            "TimeoutError",
            "ConnectionError",
            "Exception:",
            "Error:",
        ]

        lines = (stdout + "\n" + stderr).split("\n")

        for line in lines:
            for indicator in error_indicators:
                if indicator in line:
                    return line.strip()

        # Fallback to last non-empty line
        non_empty_lines = [line_text for line_text in lines if line_text.strip()]
        if non_empty_lines:
            return non_empty_lines[-1].strip()

        return "Unknown error"

    def run_all_suites(
        self, exclude_thermal: bool = False, quick_mode: bool = False
    ) -> List[StressTestResult]:
        """Run all stress test suites"""
        all_results = []

        print(f"\n🚀 STARTING COMPREHENSIVE STRESS TEST SUITE")
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Show system info
        requirements = self.check_requirements()
        print(f"\n💻 System Information:")
        print(f"   Memory: {requirements['memory_gb']:.1f} GB")
        print(f"   CPU Cores: {requirements['cpu_cores']}")
        print(f"   Free Disk: {requirements['disk_gb']:.1f} GB")
        print(
            f"   Q9550 Thermal: {'✅' if requirements.get('Q9550 thermal system') else '❌'}"
        )

        # Determine suites to run
        suites_to_run = list(self.suites.keys())

        if exclude_thermal:
            suites_to_run = [s for s in suites_to_run if s != "thermal"]

        if quick_mode:
            # Run only fast suites in quick mode
            suites_to_run = ["concurrency", "edges", "limits"]
            print(f"\n⚡ QUICK MODE: Running {len(suites_to_run)} fast suites")

        print(f"\n📋 Planned test suites: {', '.join(suites_to_run)}")

        # Run each suite
        for suite_name in suites_to_run:
            suite_results = self.run_test_suite(suite_name, verbose=True)
            all_results.extend(suite_results)
            self.results.extend(suite_results)

            # Brief summary after each suite
            suite_passed = sum(1 for r in suite_results if r.status == "passed")
            suite_failed = sum(1 for r in suite_results if r.status == "failed")
            suite_skipped = sum(1 for r in suite_results if r.status == "skipped")
            suite_errors = sum(1 for r in suite_results if r.status == "error")

            print(f"\n📊 {suite_name.upper()} SUITE SUMMARY:")
            print(f"   ✅ Passed: {suite_passed}")
            if suite_failed:
                print(f"   ❌ Failed: {suite_failed}")
            if suite_skipped:
                print(f"   ⏭️  Skipped: {suite_skipped}")
            if suite_errors:
                print(f"   🚨 Errors: {suite_errors}")

        return all_results

    def generate_report(self, results: List[StressTestResult] = None) -> str:
        """Generate comprehensive stress test report"""
        if results is None:
            results = self.results

        total_time = time.time() - self.start_time

        # Calculate statistics
        total_tests = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        errors = sum(1 for r in results if r.status == "error")

        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0

        # Group by suite
        by_suite = {}
        for result in results:
            if result.suite not in by_suite:
                by_suite[result.suite] = []
            by_suite[result.suite].append(result)

        # Generate report
        report = []
        report.append("=" * 80)
        report.append("🔥 ENHANCED MYCODER V2.0 STRESS TEST REPORT")
        report.append("=" * 80)
        report.append(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"⏱️  Total Duration: {total_time:.1f}s ({total_time/60:.1f}m)")
        report.append("")

        # Overall summary
        report.append("📊 OVERALL RESULTS")
        report.append("-" * 40)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"✅ Passed: {passed}")
        if failed:
            report.append(f"❌ Failed: {failed}")
        if skipped:
            report.append(f"⏭️  Skipped: {skipped}")
        if errors:
            report.append(f"🚨 Errors: {errors}")
        report.append(f"📈 Success Rate: {success_rate:.1f}%")
        report.append("")

        # Suite breakdown
        report.append("🧪 SUITE BREAKDOWN")
        report.append("-" * 40)

        for suite_name, suite_results in by_suite.items():
            suite_info = self.suites.get(
                suite_name,
                type("Suite", (), {"name": suite_name, "description": "Unknown"})(),
            )

            suite_passed = sum(1 for r in suite_results if r.status == "passed")
            suite_total = len(suite_results)
            suite_rate = (suite_passed / suite_total * 100) if suite_total > 0 else 0
            suite_duration = sum(r.duration for r in suite_results)

            report.append(f"\n{suite_info.name}:")
            report.append(f"  Description: {suite_info.description}")
            report.append(
                f"  Results: {suite_passed}/{suite_total} passed ({suite_rate:.1f}%)"
            )
            report.append(f"  Duration: {suite_duration:.1f}s")

            # List failed tests
            failed_tests = [r for r in suite_results if r.status == "failed"]
            if failed_tests:
                report.append("  ❌ Failed tests:")
                for test in failed_tests:
                    report.append(f"    - {test.test_name}: {test.error_message}")

            # List error tests
            error_tests = [r for r in suite_results if r.status == "error"]
            if error_tests:
                report.append("  🚨 Error tests:")
                for test in error_tests:
                    report.append(f"    - {test.test_name}: {test.error_message}")

        # Performance insights
        report.append("\n⚡ PERFORMANCE INSIGHTS")
        report.append("-" * 40)

        if results:
            avg_duration = sum(r.duration for r in results) / len(results)
            longest_test = max(results, key=lambda r: r.duration)
            fastest_test = min(results, key=lambda r: r.duration)

            report.append(f"Average test duration: {avg_duration:.2f}s")
            report.append(
                f"Longest test: {longest_test.test_name} ({longest_test.duration:.1f}s)"
            )
            report.append(
                f"Fastest test: {fastest_test.test_name} ({fastest_test.duration:.2f}s)"
            )

        # System stress assessment
        report.append("\n🔬 STRESS TEST ASSESSMENT")
        report.append("-" * 40)

        if success_rate >= 90:
            report.append("✅ EXCELLENT: System handles stress very well")
        elif success_rate >= 75:
            report.append("✅ GOOD: System handles most stress scenarios")
        elif success_rate >= 50:
            report.append("⚠️  FAIR: System has some stress limitations")
        else:
            report.append("❌ POOR: System struggles under stress")

        # Recommendations
        report.append("\n💡 RECOMMENDATIONS")
        report.append("-" * 40)

        if failed > 0:
            report.append("🔧 Address failed test scenarios for better resilience")
        if errors > 0:
            report.append("🚨 Investigate error conditions to prevent crashes")
        if any(r.status == "skipped" and "thermal" in r.suite for r in results):
            report.append(
                "🌡️  Consider Q9550 thermal system testing for complete coverage"
            )
        if success_rate < 85:
            report.append("📈 Consider optimizations for better stress handling")

        report.append("")
        report.append("=" * 80)

        return "\n".join(report)

    def save_report(self, report: str, filename: str = None) -> Path:
        """Save report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_report_{timestamp}.txt"

        report_path = self.project_root / "tests" / "reports" / filename
        report_path.parent.mkdir(exist_ok=True)

        report_path.write_text(report)
        return report_path

    def export_json(self, filename: str = None) -> Path:
        """Export results as JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_results_{timestamp}.json"

        json_path = self.project_root / "tests" / "reports" / filename
        json_path.parent.mkdir(exist_ok=True)

        # Convert results to JSON-serializable format
        json_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_duration": time.time() - self.start_time,
                "system_info": self.check_requirements(),
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "suite": r.suite,
                    "status": r.status,
                    "duration": r.duration,
                    "details": r.details,
                    "error_message": r.error_message,
                }
                for r in self.results
            ],
        }

        with open(json_path, "w") as f:
            json.dump(json_data, f, indent=2)

        return json_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced MyCoder v2.0 Stress Test Runner"
    )

    parser.add_argument("--all", action="store_true", help="Run all stress test suites")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick stress tests only"
    )
    parser.add_argument("--suite", "-s", type=str, help="Run specific test suite")
    parser.add_argument(
        "--no-thermal",
        action="store_true",
        help="Exclude thermal tests (no Q9550 required)",
    )
    parser.add_argument(
        "--report-only", action="store_true", help="Generate report from last run"
    )
    parser.add_argument(
        "--export-json", action="store_true", help="Export results as JSON"
    )
    parser.add_argument("--save-report", type=str, help="Save report to specific file")

    args = parser.parse_args()

    runner = StressTestRunner()

    # Handle report-only mode
    if args.report_only:
        print("📄 Generating report from previous results...")
        if not runner.results:
            print("❌ No previous results found. Run tests first.")
            return 1

        report = runner.generate_report()
        print(report)

        if args.save_report:
            report_path = runner.save_report(report, args.save_report)
            print(f"\n💾 Report saved to: {report_path}")

        return 0

    # Run tests
    results = []

    if args.all:
        results = runner.run_all_suites(
            exclude_thermal=args.no_thermal, quick_mode=False
        )
    elif args.quick:
        results = runner.run_all_suites(exclude_thermal=True, quick_mode=True)
    elif args.suite:
        if args.suite not in runner.suites:
            print(f"❌ Unknown suite: {args.suite}")
            print(f"Available suites: {', '.join(runner.suites.keys())}")
            return 1
        results = runner.run_test_suite(args.suite)
    else:
        print("Please specify --all, --quick, or --suite <name>")
        print(f"Available suites: {', '.join(runner.suites.keys())}")
        return 1

    # Generate and display report
    print("\n" + "=" * 80)
    report = runner.generate_report(results)
    print(report)

    # Save outputs if requested
    if args.save_report:
        report_path = runner.save_report(report, args.save_report)
        print(f"\n💾 Report saved to: {report_path}")

    if args.export_json:
        json_path = runner.export_json()
        print(f"📊 Results exported to: {json_path}")

    # Return appropriate exit code
    total_tests = len(results)
    failed = sum(1 for r in results if r.status in ["failed", "error"])

    if failed == 0:
        print(f"\n🎉 ALL STRESS TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {failed}/{total_tests} stress tests had issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())

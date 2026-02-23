#!/usr/bin/env python3
"""
Příklad kódu vygenerovaného MyCoder v2.1.0
Log Analyzer - Analýza log souborů s pokročilými funkcemi
"""

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogAnalyzer:
    """
    Pokročilý analyzátor log souborů s podporou různých formátů.

    Features:
    - Automatická detekce log formátu
    - Analýza error a warning zpráv
    - Statistiky a trendy
    - Export do JSON
    - Performance optimalizace
    """

    def __init__(self, log_file: Union[str, Path]):
        """
        Initialize log analyzer.

        Args:
            log_file: Path to log file to analyze
        """
        self.log_file = Path(log_file)
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.stats: Dict = {}

        # Common log patterns
        self.patterns = {
            "timestamp": r"(\d{4}-\d{2}-\d{2}[\s|T]\d{2}:\d{2}:\d{2})",
            "error": r"(ERROR|Error|error)",
            "warning": r"(WARNING|Warning|warning|WARN|Warn)",
            "level": r"(DEBUG|INFO|WARNING|ERROR|CRITICAL)",
            "ip": r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})",
        }

    def analyze_log_file(self) -> Dict:
        """
        Hlavní funkce pro analýzu log souboru.

        Returns:
            Dict s výsledky analýzy

        Raises:
            FileNotFoundError: If log file doesn't exist
            IOError: If file can't be read
        """
        try:
            if not self.log_file.exists():
                raise FileNotFoundError(f"Log file not found: {self.log_file}")

            logger.info(f"Starting analysis of {self.log_file}")

            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            self._parse_lines(lines)
            self._calculate_statistics()

            result = {
                "file": str(self.log_file),
                "analyzed_at": datetime.now().isoformat(),
                "total_lines": len(lines),
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "top_errors": self._get_top_errors(5),
                "top_warnings": self._get_top_warnings(5),
                "statistics": self.stats,
                "error_details": self.errors[:10],  # First 10 errors
                "warning_details": self.warnings[:10],  # First 10 warnings
            }

            logger.info(
                f"Analysis complete: {len(self.errors)} errors, {len(self.warnings)} warnings"
            )
            return result

        except Exception as e:
            logger.error(f"Error analyzing log file: {e}")
            raise

    def _parse_lines(self, lines: List[str]) -> None:
        """Parse log lines and extract errors/warnings."""

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Extract timestamp
            timestamp_match = re.search(self.patterns["timestamp"], line)
            timestamp = timestamp_match.group(1) if timestamp_match else None

            # Check for errors
            if re.search(self.patterns["error"], line, re.IGNORECASE):
                self.errors.append(
                    {
                        "line_number": line_num,
                        "timestamp": timestamp,
                        "message": line,
                        "extracted_error": self._extract_error_message(line),
                    }
                )

            # Check for warnings
            elif re.search(self.patterns["warning"], line, re.IGNORECASE):
                self.warnings.append(
                    {
                        "line_number": line_num,
                        "timestamp": timestamp,
                        "message": line,
                        "extracted_warning": self._extract_warning_message(line),
                    }
                )

    def _extract_error_message(self, line: str) -> str:
        """Extract clean error message from log line."""
        # Remove timestamp and log level
        clean_line = re.sub(self.patterns["timestamp"], "", line)
        clean_line = re.sub(r"(ERROR|Error|error):\s*", "", clean_line).strip()
        return clean_line[:200]  # Limit length

    def _extract_warning_message(self, line: str) -> str:
        """Extract clean warning message from log line."""
        # Remove timestamp and log level
        clean_line = re.sub(self.patterns["timestamp"], "", line)
        clean_line = re.sub(
            r"(WARNING|Warning|warning|WARN|Warn):\s*", "", clean_line
        ).strip()
        return clean_line[:200]  # Limit length

    def _calculate_statistics(self) -> None:
        """Calculate detailed statistics."""

        # Error frequency by hour
        error_hours = defaultdict(int)
        warning_hours = defaultdict(int)

        for error in self.errors:
            if error["timestamp"]:
                try:
                    hour = datetime.fromisoformat(error["timestamp"]).hour
                    error_hours[hour] += 1
                except ValueError:
                    # Skip malformed timestamps.
                    continue

        for warning in self.warnings:
            if warning["timestamp"]:
                try:
                    hour = datetime.fromisoformat(warning["timestamp"]).hour
                    warning_hours[hour] += 1
                except ValueError:
                    # Skip malformed warnings.
                    continue

        self.stats = {
            "error_rate": len(self.errors)
            / max(len(self.errors) + len(self.warnings), 1),
            "warning_rate": len(self.warnings)
            / max(len(self.errors) + len(self.warnings), 1),
            "errors_by_hour": dict(error_hours),
            "warnings_by_hour": dict(warning_hours),
            "peak_error_hour": (
                max(error_hours.items(), key=lambda x: x[1])[0] if error_hours else None
            ),
            "peak_warning_hour": (
                max(warning_hours.items(), key=lambda x: x[1])[0]
                if warning_hours
                else None
            ),
        }

    def _get_top_errors(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get top N most frequent errors."""
        error_messages = [error["extracted_error"] for error in self.errors]
        return Counter(error_messages).most_common(top_n)

    def _get_top_warnings(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get top N most frequent warnings."""
        warning_messages = [warning["extracted_warning"] for warning in self.warnings]
        return Counter(warning_messages).most_common(top_n)

    def save_results_to_json(
        self, output_file: Union[str, Path], results: Dict
    ) -> None:
        """
        Save analysis results to JSON file.

        Args:
            output_file: Path where to save results
            results: Analysis results dictionary
        """
        try:
            output_path = Path(output_file)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to {output_path}")

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            raise


def main():
    """Example usage of LogAnalyzer."""

    # Create sample log file for demo
    sample_log = Path("sample.log")
    if not sample_log.exists():
        with open(sample_log, "w") as f:
            f.write(
                """2024-08-08 10:30:15 INFO Server started successfully
2024-08-08 10:30:20 WARNING High memory usage detected: 85%
2024-08-08 10:35:22 ERROR Database connection failed: Connection timeout
2024-08-08 10:35:23 ERROR Database connection failed: Connection timeout  
2024-08-08 10:40:11 WARNING SSL certificate expires in 7 days
2024-08-08 10:45:33 ERROR Failed to process request: Invalid JSON format
2024-08-08 10:50:15 INFO Request processed successfully
2024-08-08 10:55:42 ERROR Database connection failed: Connection timeout
2024-08-08 11:00:18 WARNING High CPU usage: 92%
2024-08-08 11:05:55 ERROR Authentication failed for user admin
"""
            )

    # Analyze the log
    analyzer = LogAnalyzer(sample_log)
    results = analyzer.analyze_log_file()

    # Save results
    analyzer.save_results_to_json("log_analysis_results.json", results)

    # Print summary
    print("🔍 LOG ANALYSIS RESULTS")
    print("=" * 40)
    print(f"📁 File: {results['file']}")
    print(f"📊 Total lines: {results['total_lines']}")
    print(f"❌ Errors: {results['errors']}")
    print(f"⚠️  Warnings: {results['warnings']}")
    print(f"📈 Error rate: {results['statistics']['error_rate']:.2%}")

    print("\n🔥 TOP 5 ERRORS:")
    for i, (error, count) in enumerate(results["top_errors"], 1):
        print(f"   {i}. {error[:50]}... ({count}x)")

    print("\n⚠️  TOP 5 WARNINGS:")
    for i, (warning, count) in enumerate(results["top_warnings"], 1):
        print(f"   {i}. {warning[:50]}... ({count}x)")


if __name__ == "__main__":
    main()

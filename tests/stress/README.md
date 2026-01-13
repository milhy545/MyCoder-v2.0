# MyCoder v2.1.0 Stress Testing Framework

This directory contains comprehensive stress tests designed to verify the robustness and reliability of Enhanced MyCoder v2.1.0 under extreme conditions.

## Overview

The stress testing framework evaluates system behavior under:
- **High Concurrent Load** - Multiple simultaneous requests
- **Memory Pressure** - Large files and memory-intensive operations
- **Thermal Stress** - Q9550 thermal management limits
- **Network Failures** - Timeouts, cascading failures, intermittent connectivity
- **Edge Cases** - Malformed inputs, boundary conditions
- **System Limits** - Configuration boundaries, resource exhaustion
- **Recovery Scenarios** - System restart, corruption recovery

## Test Structure

```
tests/stress/
├── test_mycoder_stress.py      # Core stress tests
├── test_system_limits.py       # System boundary tests
├── run_stress_tests.py         # Comprehensive test runner
├── README.md                   # This file
└── reports/                    # Generated test reports
```

## Quick Start

### Run All Stress Tests
```bash
python tests/stress/run_stress_tests.py --all
```

### Quick Stress Test (Fast suites only)
```bash
python tests/stress/run_stress_tests.py --quick
```

### Run Specific Test Suite
```bash
python tests/stress/run_stress_tests.py --suite concurrency
python tests/stress/run_stress_tests.py --suite memory
python tests/stress/run_stress_tests.py --suite thermal  # Requires Q9550
```

### Run Without Thermal Tests (No Q9550 required)
```bash
python tests/stress/run_stress_tests.py --all --no-thermal
```

## Test Suites

### 1. Concurrency Stress (`concurrency`)
**Duration:** ~5-15 minutes  
**Description:** Tests system behavior under high concurrent load

- **High Concurrent Requests** - 50 simultaneous requests
- **Session Overflow** - 200+ concurrent sessions  
- **Provider Cascade Failures** - Fallback chain under load

**Key Metrics:**
- Success rate ≥90% under 50 concurrent requests
- Session cleanup maintains ≤100 sessions
- Response time <1s average

### 2. Memory Pressure (`memory`)
**Duration:** ~10-20 minutes  
**Description:** Tests memory usage patterns and leak prevention

- **Large File Processing** - Multi-MB file handling
- **Memory Leak Prevention** - 500 operations without accumulation
- **Resource Exhaustion** - Boundary condition handling

**Key Metrics:**
- Handles files up to 10MB
- No memory leaks over 500 operations
- Graceful degradation at limits

### 3. Thermal Management (`thermal`) *[Requires Q9550]*
**Duration:** ~15-25 minutes  
**Description:** Tests Q9550 thermal management integration

- **Thermal Limit Stress** - Operations at temperature limits
- **Recovery Cycles** - Heat-up and cool-down handling
- **Thermal-Aware Operations** - Temperature-based throttling

**Requirements:**
- Q9550 system with thermal monitoring
- `/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh`

**Key Metrics:**
- Blocks operations above 82°C
- Recovers operations below 75°C
- Maintains system protection

### 4. Network Stress (`network`)
**Duration:** ~10-20 minutes  
**Description:** Tests network failure scenarios

- **Timeout Cascades** - Sequential provider timeouts
- **Intermittent Connectivity** - 30% random failure rate
- **Provider Health Oscillation** - Rapid health changes

**Key Metrics:**
- ≥60% success rate with intermittent network
- Graceful timeout handling <3s average
- Provider fallback functionality

### 5. Edge Cases (`edges`)
**Duration:** ~5-15 minutes  
**Description:** Tests boundary conditions and malformed inputs

- **Malformed Input Stress** - 15 different malformed input types
- **Resource Exhaustion** - File handle and memory limits
- **Unicode and Binary Data** - Special character handling

**Key Metrics:**
- Handles 80% of malformed inputs gracefully
- ≤3 unhandled exceptions
- No system crashes

### 6. System Limits (`limits`)
**Duration:** ~15-25 minutes  
**Description:** Tests configuration and system boundaries

- **Configuration Edge Cases** - Malformed config handling
- **Provider Switching Limits** - Rapid provider changes
- **Session Management Boundaries** - Session corruption scenarios
- **Tool Registry Overload** - High concurrent tool usage
- **System Recovery** - Restart and corruption recovery

**Key Metrics:**
- 80% malformed config handling
- 90% provider switch success rate
- Tool registry handles 100 concurrent operations

## System Requirements

### Minimum Requirements
- **Memory:** 4GB RAM available
- **CPU:** 2+ cores
- **Disk:** 2GB free space
- **Python:** 3.10-3.13 with pytest

### Optimal Requirements  
- **Memory:** 8GB+ RAM
- **CPU:** 4+ cores  
- **Disk:** 5GB+ free space
- **Network:** Stable connection for API tests

### Q9550 Thermal Requirements
- Q9550 processor with thermal monitoring
- PowerManagement thermal scripts installed
- Root access for thermal status checks

## Usage Examples

### Development Testing
```bash
# Quick verification during development
python tests/stress/run_stress_tests.py --quick

# Test specific area after changes
python tests/stress/run_stress_tests.py --suite concurrency
```

### CI/CD Integration
```bash
# Full stress test for releases
python tests/stress/run_stress_tests.py --all --no-thermal --export-json

# Generate reports for build artifacts
python tests/stress/run_stress_tests.py --all --save-report stress_report_v2.1.0.txt
```

### Q9550 System Testing
```bash
# Full thermal stress testing
python tests/stress/run_stress_tests.py --suite thermal

# Complete system validation
python tests/stress/run_stress_tests.py --all
```

### Debug and Analysis
```bash
# Run individual test files
pytest tests/stress/test_mycoder_stress.py::TestConcurrencyStress -v

# Run with detailed output
pytest tests/stress/test_system_limits.py -v -s --tb=long
```

## Interpreting Results

### Success Rate Guidelines
- **≥95%** - Excellent stress handling
- **90-94%** - Good resilience with minor issues
- **80-89%** - Acceptable but needs optimization
- **<80%** - Significant stress handling problems

### Common Failure Patterns

**High Memory Usage:**
```
AssertionError: Processing time exceeded limit
```
*Solution: Optimize file processing, implement streaming*

**Thermal Throttling:**
```
Operation blocked due to thermal limits (CPU: 85.0°C)
```
*Expected behavior: System protecting Q9550 from overheating*

**Provider Failures:**
```
All providers failed - Network timeout
```
*Solution: Check network connectivity, verify API keys*

**Session Overflow:**
```
Session count exceeded limit
```
*Expected behavior: Automatic session cleanup*

## Configuration

### Environment Variables
```bash
# API Keys for provider testing
export ANTHROPIC_API_KEY="your_key_here"
export GEMINI_API_KEY="your_key_here"

# Stress test configuration  
export STRESS_TEST_TIMEOUT=1800  # 30 minutes
export STRESS_TEST_CONCURRENCY=50
export STRESS_TEST_MEMORY_LIMIT=8GB
```

### Test Configuration Files
- `tests/stress/config/stress_test_config.json` - Custom stress parameters
- `tests/stress/config/thermal_limits.json` - Q9550 thermal thresholds

## Reporting

### Text Reports
Generated in `tests/reports/stress_test_report_YYYYMMDD_HHMMSS.txt`

Contains:
- Overall statistics
- Suite-by-suite breakdown
- Performance metrics
- Failure analysis
- Recommendations

### JSON Export  
Generated in `tests/reports/stress_test_results_YYYYMMDD_HHMMSS.json`

Contains:
- Machine-readable results
- Detailed timing data
- System information
- Error details

### Real-time Monitoring
```bash
# Watch stress test progress
tail -f tests/reports/stress_test_report_*.txt

# Monitor system resources during tests
htop
iotop
```

## Troubleshooting

### Common Issues

**"Q9550 thermal system not available"**
- Install PowerManagement thermal scripts
- Verify `/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh` exists
- Run with `--no-thermal` to skip thermal tests

**"pytest command not found"**
```bash
pip install pytest pytest-asyncio pytest-timeout
```

**"Tests timing out"**
- Increase timeout with `--timeout=3600` 
- Check system resources (CPU, memory, disk)
- Run quick tests first: `--quick`

**"Memory errors during large file tests"**
- Ensure 8GB+ RAM available
- Close other applications
- Run individual suites: `--suite edges`

**"Network tests failing"**
- Check internet connectivity  
- Verify API keys are valid
- Some network failures are expected (testing failure scenarios)

### Debug Mode
```bash
# Run with maximum verbosity
python tests/stress/run_stress_tests.py --suite concurrency --debug

# Individual test debugging
pytest tests/stress/test_mycoder_stress.py::TestConcurrencyStress::test_high_concurrent_requests -v -s --tb=long --pdb
```

## Contributing

### Adding New Stress Tests
1. Add test methods to existing test classes
2. Follow naming convention: `test_*_stress`
3. Use appropriate timeouts and resource limits
4. Include performance assertions
5. Add documentation

### Creating New Test Suites
1. Create new test class in appropriate file
2. Add suite definition to `run_stress_tests.py`
3. Update this README with suite description
4. Test on multiple system configurations

### Performance Benchmarks
- Document expected performance metrics
- Include system specification requirements
- Provide failure thresholds and success criteria
- Test on Q9550 reference system

## Integration

### Continuous Integration
```yaml
# GitHub Actions example
- name: Run Stress Tests
  run: |
    python tests/stress/run_stress_tests.py --quick --export-json
    
- name: Upload Results
  uses: actions/upload-artifact@v2
  with:
    name: stress-test-results
    path: tests/reports/
```

### Docker Integration
```dockerfile
# Add to Dockerfile
RUN pip install pytest pytest-asyncio pytest-timeout
COPY tests/ /app/tests/
RUN python tests/stress/run_stress_tests.py --quick --no-thermal
```

## Maintenance

### Regular Tasks
- Run full stress tests before releases
- Update performance baselines quarterly  
- Review and update thermal thresholds
- Validate on new system configurations

### Monitoring
- Track success rate trends over time
- Monitor performance regression
- Update failure thresholds based on improvements
- Document system-specific behavior

---

## Quick Reference

| Command | Description | Duration |
|---------|-------------|----------|
| `--all` | All stress tests | 60-90 min |
| `--quick` | Fast tests only | 15-30 min |
| `--suite concurrency` | Concurrent load tests | 5-15 min |
| `--suite memory` | Memory pressure tests | 10-20 min |
| `--suite thermal` | Q9550 thermal tests | 15-25 min |
| `--suite network` | Network failure tests | 10-20 min |
| `--suite edges` | Edge case tests | 5-15 min |
| `--suite limits` | System boundary tests | 15-25 min |

For questions or issues, see project documentation or create an issue on GitHub.

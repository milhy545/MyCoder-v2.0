from mycoder.cli_interactive import ExecutionMonitor


def test_monitor_initialization():
    """ExecutionMonitor should initialize with empty logs and configured capacity."""
    monitor = ExecutionMonitor()
    assert monitor.logs == []
    assert monitor.max_logs == 15


def test_add_log():
    """Adding a log should append the new entry with correct action/resource."""
    monitor = ExecutionMonitor()
    monitor.add_log("INIT_PROVIDER", "claude")
    assert len(monitor.logs) == 1
    timestamp, action, resource = monitor.logs[0]
    assert action == "INIT_PROVIDER"
    assert resource == "claude"
    assert isinstance(timestamp, str) and len(timestamp) > 0


def test_log_trimming():
    """Logs should be trimmed to the most recent max_logs entries."""
    monitor = ExecutionMonitor()
    for idx in range(20):
        monitor.add_log(f"A{idx}", f"resource-{idx}")
    assert len(monitor.logs) == 15
    assert monitor.logs[0][1] == "A5"
    assert monitor.logs[-1][1] == "A19"


def test_metrics_structure():
    """System metrics must include CPU, RAM, and thermal keys."""
    monitor = ExecutionMonitor()
    metrics = monitor.get_system_metrics()
    assert {"cpu", "ram", "thermal"}.issubset(metrics.keys())

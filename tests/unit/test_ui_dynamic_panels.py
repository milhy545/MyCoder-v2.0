from rich.console import Console
from rich.panel import Panel

from mycoder.ui_dynamic_panels import DynamicExecutionMonitor


def test_render_standard():
    monitor = DynamicExecutionMonitor()
    console = Console(width=120, height=40)
    panel = monitor.render(console)
    assert isinstance(panel, Panel)


def test_render_progress():
    monitor = DynamicExecutionMonitor()
    console = Console(width=120, height=40)
    monitor.set_operation("Testing", 50)
    monitor.update_provider_health("ollama_local", "healthy")
    panel = monitor.render(console)
    assert isinstance(panel, Panel)


def test_render_thermal_alert():
    monitor = DynamicExecutionMonitor()
    console = Console(width=120, height=40)
    monitor.set_thermal_warning(True)
    panel = monitor.render(console)
    assert isinstance(panel, Panel)
    assert "THERMAL" in str(panel.title)

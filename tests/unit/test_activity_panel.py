from rich.console import Console
from rich.panel import Panel

from mycoder.ui_activity_panel import Activity, ActivityPanel, ActivityType


def test_activity_panel_tracks_files():
    panel = ActivityPanel(max_activities=3)
    panel.add_activity(
        Activity(type=ActivityType.FILE_CREATE, description="Create", target="a.txt")
    )
    panel.add_activity(
        Activity(type=ActivityType.FILE_EDIT, description="Edit", target="b.py")
    )
    assert "a.txt" in panel.files_created
    assert "b.py" in panel.files_modified


def test_activity_panel_trims_activities():
    panel = ActivityPanel(max_activities=2)
    panel.add_activity(Activity(type=ActivityType.API_CALL, description="One"))
    panel.add_activity(Activity(type=ActivityType.API_CALL, description="Two"))
    panel.add_activity(Activity(type=ActivityType.API_CALL, description="Three"))
    assert len(panel.activities) == 2
    assert panel.activities[0].description == "Two"
    assert panel.activities[1].description == "Three"


def test_activity_panel_render():
    panel = ActivityPanel()
    panel.set_operation("Testing", 40)
    panel.set_thinking("Partial output")
    console = Console(width=120, height=40)
    rendered = panel.render(console)
    assert isinstance(rendered, Panel)

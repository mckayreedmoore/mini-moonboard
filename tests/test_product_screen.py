"""Small known intersections verify the diagnostic cannot silently call a pass."""
from types import SimpleNamespace

import cadquery as cq
import pytest
from product_frame_screen import screen

from mini_moonboard.box_frame import Connection
from mini_moonboard.product_connections import selected_connection


def test_known_overlap_and_separated_bodies():
    a = SimpleNamespace(name="a", shape=cq.Solid.makeBox(2, 2, 2))
    b = SimpleNamespace(name="b", shape=cq.Solid.makeBox(2, 2, 2, cq.Vector(1, 0, 0)))
    report = screen([a, b], [])
    assert report["qualified_for_design"] is False
    assert report["errors"] == []
    assert len(report["findings"]) == 1
    assert report["findings"][0]["category"] == "body_body"
    assert report["findings"][0]["volume_mm3"] == pytest.approx(4)
    b.shape = b.shape.translate((5, 0, 0))
    assert screen([a, b], [])["findings"] == []


def test_duplicate_inventory_is_rejected():
    a = SimpleNamespace(name="a", shape=cq.Solid.makeBox(1, 1, 1))
    with pytest.raises(ValueError, match="Duplicate"):
        screen([a, a], [])


def test_hardware_tools_and_intentional_thread_engagement():
    def part(name, z):
        return SimpleNamespace(name=name, shape=cq.Solid.makeBox(2, 2, 2, cq.Vector(-1, -1, z)))

    def screw(name, z):
        return selected_connection(Connection(name, cq.Vector(0, 0, z), cq.Vector(0, 0, 1),
                                               50.8, 4.3942, ("receiver",)))

    receiver, head_block, tool_block = part("receiver", 12), part("head_block", 1), part("tool_block", -20)
    first = screw("panel_1", 0)
    second = screw("panel_2", -10)
    report = screen([receiver, head_block, tool_block], [first, second])
    assert report["errors"] == []
    findings = report["findings"]
    for category, a, b in (
            ("hardware_body", "panel_1", "head_block"),
            ("shaft_body", "panel_1", "head_block"),
            ("tool_body", "panel_1", "tool_block"),
            ("hardware_hardware", "panel_1", "panel_2"),
            ("tool_hardware", "panel_1", "panel_2")):
        assert any(f["category"] == category and f["a"] == a and f["b"] == b for f in findings)
    assert not any(f["category"] == "shaft_body" and f["b"] == "receiver" for f in findings)


def test_intersection_errors_remain_visible(monkeypatch):
    a = SimpleNamespace(name="a", shape=cq.Solid.makeBox(2, 2, 2))
    b = SimpleNamespace(name="b", shape=cq.Solid.makeBox(2, 2, 2))

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic boolean failure")

    monkeypatch.setattr(cq.Shape, "intersect", fail)
    report = screen([a, b], [])
    assert report["findings"] == []
    assert len(report["errors"]) == 1
    assert "synthetic boolean failure" in report["errors"][0]["error"]
    assert report["qualified_for_design"] is False


def test_source_drift_prevents_report_publication(monkeypatch, tmp_path):
    import product_frame_screen as diagnostic

    from mini_moonboard import product_frame

    snapshots = iter(({"source": "before"}, {"source": "after"}))
    output = tmp_path/"report.json"
    monkeypatch.setattr("sys.argv", ["screen", "--output", str(output)])
    monkeypatch.setattr(diagnostic, "source_hashes", lambda paths: next(snapshots))
    monkeypatch.setattr(product_frame, "parts", lambda: ())
    monkeypatch.setattr(product_frame, "connections", lambda: ())
    with pytest.raises(RuntimeError, match="Source files changed"):
        diagnostic.main()
    assert not output.exists()

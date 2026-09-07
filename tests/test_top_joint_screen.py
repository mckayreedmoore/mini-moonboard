"""Full nominal collision/access screen for the separate top-joint revision."""
from product_frame_screen import screen

from mini_moonboard import top_joint_frame as frame


def test_revision_has_only_the_declared_installation_order_blockers():
    report = screen(frame.parts(), frame.connections())
    assert report["errors"] == []
    expected = {
        (f"analysis_edge_screw_{side}_{i}", f"leg_{side}_{ply}")
        for side in ("left", "right") for i in (4, 5) for ply in ("inner", "outer")}
    expected.update(
        (f"rib_{row}_{location}_{side}_front", f"main_{band}_{side}")
        for row in (1, 2, 3) for location in ("seam", "mid") for side in ("left", "right")
        for band in (("lower",) if row == 1 else ("upper",) if row == 3 else ("lower", "upper")))
    assert len(expected) == 24
    assert len(report["findings"]) == 24, report["findings"]
    assert {f["category"] for f in report["findings"]} == {"tool_body"}
    assert {(f["a"], f["b"]) for f in report["findings"]} == expected
    assert report["qualified_for_design"] is False

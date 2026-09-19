"""Keep the RS-2 sheet tied to raw CAD and frozen retained axes."""

from xml.etree import ElementTree

from scripts import draw_rs2_center_joint as drawing


def test_two_non_drilling_sheets_from_raw_cad(tmp_path, monkeypatch):
    monkeypatch.setattr(drawing, "OUT", tmp_path)
    result = drawing.generate()
    assert result["contact_x"] == -89.05
    assert result["header_z"] == (238.9, 277.0)
    assert result["retained_axes"] == {"hillman_panel": 66, "bolt_clearance": 12}
    assert result["top_y"] != result["stagger_y"]
    ns = {"s": "http://www.w3.org/2000/svg"}
    for name in ("shared", "stagger"):
        svg = ElementTree.parse(tmp_path / f"rs2-ab205-{name}.svg").getroot()
        contents = "".join(svg.itertext())
        assert "NON-DRILLING" in contents
        assert "no accepted holes" in contents
        assert "4 of 66 screw starts" in contents
        assert "0 of 12 frame bolts" in contents
        assert len(svg.findall(".//s:polyline", ns)) == 2  # top and underside angle legs
        assert all(f"S{index}" in contents for index in range(1, 5))
        assert ("T/U1" in contents) == (name == "shared")

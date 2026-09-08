"""Actual archived-mesh transformation proof; no CAD solids or solver."""
import json

import pytest

from fea import prove_panel_edge_release as proof


def test_actual_accepted_mesh_release_preserves_material_and_rim():
    result = proof.prove()
    assert result["added_node_count"] == 144
    assert result["volume_mm3"] == pytest.approx(289546572.28788966, rel=0, abs=.001)
    assert result["tolerance_mm"] == 1e-5
    for side in ("left", "right"):
        row = result["legs"][side]
        assert row["duplicated_node_count"] == 72
        assert row["released_panel_face_count"] == 34
        assert row["retained_rim_face_count"] == 148
        assert len(row["retained_common_edge_nodes"]) == 29
        assert row["released_panel_area_mm2"] == pytest.approx(9218.14883125195, rel=0, abs=1e-6)
        assert row["retained_rim_area_mm2"] == pytest.approx(81257.79116351595, rel=0, abs=1e-6)


def test_actual_mesh_rejects_changed_saved_leg_ownership():
    _, deck, _, _ = proof.authenticated_inputs()
    nodes, elements = proof.mesh(deck)
    leg = json.loads(proof.REPORT.read_text())["legs"]["left"]
    leg["element_count"] += 1
    with pytest.raises(ValueError, match="ownership differs"):
        proof.recover(nodes, elements, leg)

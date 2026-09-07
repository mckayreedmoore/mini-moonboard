"""Lightweight screen bookkeeping and geometric-ratio checks; no CAD or solver."""
import json

import pytest

from fea import bolted_screen as screen


def test_gross_section_ratios_do_not_claim_frame_strength():
    result = screen.section_comparison()
    ratios = result["new_over_old_ratios"]
    assert ratios["area_mm2"] == pytest.approx(7/3)
    assert ratios["I_out_of_plane_mm4"] == pytest.approx(7/3)
    assert ratios["I_in_plane_mm4"] == pytest.approx((7/3)**3)
    assert ratios["Z_in_plane_mm3"] == pytest.approx((7/3)**2)
    assert "not resistance" in result["interpretation"]


def test_each_weight_has_complete_screen_envelope():
    state = {"mass_kg": 200, "centre_xy_mm": [0, 0],
             "support_polygon_mm": [[-1000, -1000], [1000, -1000],
                                    [1000, 1000], [-1000, 1000]]}
    report = screen.candidate_report(state, [("edge_hold", (1100, 0, 2000), (0, 1, 0))])
    assert len(report["cases"]) == 96
    assert set(report["summaries"]) == {"150", "200", "250", "300"}
    assert all(summary["case_count"] == 24 for summary in report["summaries"].values())
    assert {case["mass_scale"] for case in report["cases"]} == {0.8, 1.0}
    assert {case["hold_standoff_mm"] for case in report["cases"]} == {0, 50, 100}


def test_source_drift_is_rejected(tmp_path):
    source = tmp_path/"source.py"
    source.write_text("original")
    manifest = tmp_path/"manifest.json"
    sources = {str(source): screen.digest(source)}
    manifest.write_text(json.dumps({"sources": sources}))
    assert screen.manifest_sources(manifest) == sources
    source.write_text("changed")
    with pytest.raises(ValueError, match="source closure"):
        screen.manifest_sources(manifest)

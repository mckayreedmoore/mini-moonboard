"""Known-solid controls for the full-breadth capacity correction, without a solve."""

import copy
import json

import cadquery as cq
import pytest

from scripts import eoere_v6_report as reducer
from scripts.eoere_v6_testing_review import (
    ORIGINAL,
    ROOT,
    SIDES,
    expand_side,
    sha,
    unchanged_maxima,
)


@pytest.fixture
def drilled_coupon():
    solid = cq.Solid.makeBox(100, 88.9, 50)
    bore = cq.Solid.makeCylinder(5, 88.9, cq.Vector(50, 0, 25), cq.Vector(0, 1, 0))
    solid = solid.cut(bore)
    u = [.001, 79.374]
    hole = {"axial_L_window_mm": [44, 56], "void_bounds_UV_mm": [[0, 88.9], [19, 31]]}
    regions = [
        {"local_grain_interval_mm": [2, 44], "retained_rectangles": [{"bounds_uv_mm": [u, [1, 49]]}]},
        {"local_grain_interval_mm": [44, 56], "retained_rectangles": [
            {"bounds_uv_mm": [u, [1, 19]]}, {"bounds_uv_mm": [u, [31, 49]]}]},
        {"local_grain_interval_mm": [56, 98], "retained_rectangles": [{"bounds_uv_mm": [u, [1, 49]]}]},
    ]
    row = {"member": "base_side_left", "minimum_full_depth_core_bounds_LUV_mm": [[2, 98], u, [1, 49]],
           "net_regions": regions, "curved_opening_projections": [hole]}
    profile = {"vertices_luv_mm": [[0, 0, 0], [100, 88.9, 50]]}
    return row, profile, solid


def test_full_breadth_is_credited_without_filling_the_known_bore(drilled_coupon):
    row, profile, solid = drilled_coupon
    original = copy.deepcopy(row)
    result = expand_side(row, profile, solid)
    assert row == original
    assert result["curved_opening_projections"] == original["curved_opening_projections"]
    # Analytical volume: 96 mm length x 48 mm depth, minus a 12 x 12 hole band.
    expected_volume = 88.898 * (96 * 48 - 12 * 12)
    probes = [p for r in result["net_regions"] for p in r["containment"]]
    assert sum(p["volume_mm3"] for p in probes) == pytest.approx(expected_volume)
    assert all(p["absent_material_mm3"] < .001 for p in probes)
    assert result["breadth_review"]["whole_interval_prisms_queried"] == 4


def test_extra_breadth_is_rejected_when_a_hidden_recess_removes_it(drilled_coupon):
    row, profile, solid = drilled_coupon
    recess = cq.Solid.makeBox(10, 5, 5, cq.Vector(10, 82, 10))
    with pytest.raises(ValueError, match="uncontained expanded ligament"):
        expand_side(row, profile, solid.cut(recess))


def test_even_a_bounding_hole_band_cannot_be_filled(drilled_coupon):
    row, profile, solid = drilled_coupon
    row["net_regions"][1]["retained_rectangles"][0]["bounds_uv_mm"][1][1] = 20
    with pytest.raises(ValueError, match="fills a projected hole"):
        expand_side(row, profile, solid)


def test_different_members_cannot_inherit_the_side_correction(drilled_coupon):
    row, profile, solid = drilled_coupon
    row["member"] = "base_header"
    with pytest.raises(ValueError, match="only the two side rails"):
        expand_side(row, profile, solid)


def test_current_bolt_and_plywood_summaries_keep_their_own_population_maxima():
    base = json.loads(ORIGINAL.read_bytes())
    result = unchanged_maxima(base)
    assert len(result["shafts_Cdelta_adjusted"]) == 3
    for metric, record in result["shafts_Cdelta_adjusted"].items():
        assert record == base["metric_maxima"]["shafts_Cdelta_adjusted"][metric]["all_96"]
    for group in ("plywood_nominal_38p1", "plywood_credited_36p5"):
        assert len(result[group]) == 3
        for metric, record in result[group].items():
            assert record == base["metric_maxima"][group][metric]["overall"]


def test_current_review_joins_all_corrected_intervals_to_the_same_six_fields():
    index = json.loads((ROOT / "docs/bolted-frame-development/development-revisions.json").read_bytes())
    binding = index["testing_review"]
    assert sha(binding["path"]) == binding["sha256"]
    review = json.loads((ROOT / binding["path"]).read_bytes())
    sources = review["source_bindings"]
    for reference in sources.values():
        assert sha(reference["path"]) == reference["sha256"]
    old = json.loads((ROOT / sources["original_core"]["path"]).read_bytes())
    current = json.loads((ROOT / sources["corrected_core"]["path"]).read_bytes())
    for path, digest in current["source_sha256"].items():
        assert sha(path) == digest
    for before, after in zip(old["rows"], current["rows"], strict=True):
        assert before["member"] == after["member"]
        if before["member"] not in SIDES:
            assert before == after
            continue
        assert before["source"] == after["source"]
        assert before["curved_opening_projections"] == after["curved_opening_projections"]
        for previous, corrected in zip(before["net_regions"], after["net_regions"], strict=True):
            assert previous["local_grain_interval_mm"] == corrected["local_grain_interval_mm"]
            assert previous["active_curved_faces"] == corrected["active_curved_faces"]
            assert corrected["all_contained"]
            for a, b in zip(previous["retained_rectangles"], corrected["retained_rectangles"], strict=True):
                assert a["bounds_uv_mm"][1] == b["bounds_uv_mm"][1]
    sections = json.loads((ROOT / sources["corrected_sections"]["path"]).read_bytes())
    for path, digest in sections["source_sha256"].items():
        assert sha(path) == digest
    maxima, exceedances = reducer.summarize_timber(sections)
    assert maxima == review["timber_reference_maxima"]
    assert exceedances == review["timber_member_metric_exceedances"]

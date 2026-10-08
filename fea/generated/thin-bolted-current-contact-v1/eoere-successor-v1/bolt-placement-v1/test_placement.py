"""Independent small geometry/table seams only; no candidate CAD or response."""

import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest

LEAF = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("eoere_placement", LEAF / "placement.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
PINS = json.loads((LEAF / "input.json").read_bytes())["source_sha256"]
SHOP, END = p.load_pure_methods(PINS)
DIMENSIONS = {"arm_A": 88.9, "arm_B": 88.9, "width": 88.9, "thickness": 6.35,
              "transverse_hole_pitch": 50.8, "axial_hole_row_pitch": 41.275}


def station():
    return {"duty_id": "toy", "beam": "rail", "post": "post", "origin_xyz_mm": [0, 0, 0],
            "u_xyz": [1, 0, 0], "v_xyz": [0, 0, -1], "w_xyz": [0, 1, 0]}


def rail_profile(oblique=False):
    vertices = [[(40 + .5 * y if oblique else 0) if end == 0 else 200, y, z]
                for end in (0, 1) for y in (-69.85, 69.85) for z in (0, 38.1)]
    facets, _ = SHOP.hull(vertices)
    return {"member": "rail", "facets": facets, "basis": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]}


def test_all_eight_centres_keep_near_holes_unoccupied():
    holes = p.factory_holes(station(), DIMENSIONS, 65.0875, 0, SHOP)
    assert len(holes) == 8 and len({h["id"] for h in holes}) == 8
    assert sum(h["installed"] for h in holes) == 4
    assert sorted({h["along_heel_scenario_mm"] for h in holes}) == pytest.approx([23.8125, 65.0875])
    for flange in ("beam", "post"):
        far = [h for h in holes if h["flange"] == flange and h["installed"]]
        assert math.dist(*(h["wood_entry_xyz_mm"] for h in far)) == pytest.approx(50.8)


def test_eight_hole_sharp_clearance_and_missing_bend_scope():
    domain = p.sharp_angle_domain(DIMENSIONS, 10.)
    assert [domain["low_mm"], domain["high_mm"]] == pytest.approx([52.625, 83.9])
    assert domain["low_inclusive"] is domain["high_inclusive"] is False
    assert "actual bend" in domain["scope"]


def test_square_end_and_raw_full_thickness_known_answer():
    hole = p.factory_holes(station(), DIMENSIONS, 65.0875, 0, SHOP)[2]
    out = p.hole_screen(hole, rail_profile(), 9.525, SHOP, END)
    assert out["raw_shaft_interval_from_entry_mm"] == pytest.approx([0, 38.1])
    assert [e["distance_mm"] for e in out["end_rays"]] == pytest.approx([65.0875, 134.9125])
    assert sorted(e["distance_mm"] for e in out["edge_rays"]) == pytest.approx([44.45, 95.25])
    assert out["end_rays"][0]["softwood_toward_end_factor_only"]["end_factor_only"] == pytest.approx(41 / 42)
    assert out["strength_pass"] is False and out["complete_geometry_factor"] is None


def test_oblique_owner_keeps_end_factor_unavailable():
    hole = p.factory_holes(station(), DIMENSIONS, 65.0875, 0, SHOP)[2]
    out = p.hole_screen(hole, rail_profile(oblique=True), 9.525, SHOP, END)
    end = out["end_rays"][0]
    assert end["square_to_ray"] is False
    assert end["softwood_toward_end_factor_only"] is None
    assert end["distance_mm"] == pytest.approx(65.0875 - (40 + .5 * -25.4))


def test_far_offset_and_depth_halfspace_intersections():
    out = p.flange_intervals(station(), "beam", rail_profile(), DIMENSIONS, [52.625, 83.9], 9.525, SHOP)
    assert out["far_offset_interval_mm"] == pytest.approx([66.675, 83.9])
    assert out["far_offset_interval_endpoints_inclusive"] == [True, False]
    assert out["depth_shift_interval_for_both_possible_loaded_edges_mm"] == pytest.approx([-6.35, 6.35])
    hole = p.factory_holes(station(), DIMENSIONS, 65.0875, 18, SHOP)[3]
    edge = p.hole_screen(hole, rail_profile(), 9.525, SHOP, END)
    assert min(e["distance_mm"] for e in edge["edge_rays"]) == pytest.approx(26.45)
    assert 4 * 9.525 - 26.45 == pytest.approx(11.65)


def test_incompatible_halfspaces_return_empty():
    facets = rail_profile()["facets"]
    shifts = [[0, 100, 0], [0, -100, 0]]
    assert p.affine_interval([0, 0, 19.05], [1, 0, 0], facets, shifts, [0, 200], SHOP) is None


def test_rows_follow_force_direction_not_grain_only():
    rules = p.active_pair_rules(9.525, 50.8)
    parallel, perpendicular = rules["parallel_load"], rules["perpendicular_load"]
    assert parallel["row_locations"] == 2 and parallel["bolts_per_location_from_this_pair"] == 1
    assert parallel["two_or_more_fastener_rows_in_isolated_pair"] == 0
    assert parallel["between_rows_min_mm"] == pytest.approx(14.2875)
    assert perpendicular["rows"] == 1 and perpendicular["bolts_in_row"] == 2
    assert perpendicular["in_row_min_mm"] == pytest.approx(28.575)
    assert perpendicular["between_rows_spacing_applicable"] is False
    assert perpendicular["in_row_spacing_factor_only"] is None
    assert parallel["edge_min_mm_if_ell_classified"] is None
    assert p.active_pair_rules(9.525, 50.8, ell_over_d=4)["parallel_load"]["edge_min_mm_if_ell_classified"] == pytest.approx(14.2875)
    assert p.active_pair_rules(9.525, 50.8, ell_over_d=7)["parallel_load"]["edge_min_mm_if_ell_classified"] == pytest.approx(25.4)
    assert p.active_pair_rules(9.525, 50.8, attached_spacing_mm=57.15)["perpendicular_load"]["in_row_spacing_factor_only"] == pytest.approx(8 / 9)


@pytest.mark.parametrize("distance,factor", [(33.3375, .5), (32., None), (66.675, 1.)])
def test_frozen_classified_end_minimum_is_not_strength_pass(distance, factor):
    out = END(distance, 9.525, "softwood_parallel_tension")
    assert out["end_factor_only"] == factor
    assert out["complete_geometry_factor"] is None


def test_proper_rotation_translation_preserves_own_ray_distances():
    a = .41
    rot = lambda v: [math.cos(a) * v[0] - math.sin(a) * v[1],
                     math.sin(a) * v[0] + math.cos(a) * v[1], v[2]]
    transform = lambda v: SHOP.add(rot(v), [17, -21, 83])
    st = station()
    reference = p.hole_screen(p.factory_holes(st, DIMENSIONS, 65.0875, 0, SHOP)[2], rail_profile(), 9.525, SHOP, END)
    for key in ("u_xyz", "v_xyz", "w_xyz"):
        st[key] = rot(st[key])
    st["origin_xyz_mm"] = transform(st["origin_xyz_mm"])
    vertices = [transform([x, y, z]) for x in (0, 200) for y in (-69.85, 69.85) for z in (0, 38.1)]
    profile = {"facets": SHOP.hull(vertices)[0], "basis": [rot(v) for v in rail_profile()["basis"]]}
    actual = p.hole_screen(p.factory_holes(st, DIMENSIONS, 65.0875, 0, SHOP)[2], profile, 9.525, SHOP, END)
    for key in ("end_rays", "edge_rays"):
        assert [e["distance_mm"] for e in actual[key]] == pytest.approx([e["distance_mm"] for e in reference[key]])


def test_reflection_and_nonfinite_offset_rejected():
    st = station()
    st["w_xyz"] = [0, -1, 0]
    with pytest.raises(ValueError, match="improper"):
        p.factory_holes(st, DIMENSIONS, 65.0875, 0, SHOP)
    with pytest.raises(ValueError, match="finite"):
        p.factory_holes(station(), DIMENSIONS, math.nan, 0, SHOP)


def test_source_byte_change_rejected_before_profile_use(tmp_path):
    path = tmp_path / "source.json"
    path.write_text("source")
    digest = p.sha(path)
    path.write_text("changed")
    with pytest.raises(ValueError, match="source bytes"):
        p.verify_pins({str(path): digest})


def test_raw_profile_forgery_is_rejected():
    source = {"vertices_world_mm": [[x, y, z] for x in (0, 200) for y in (-69.85, 69.85) for z in (0, 38.1)]}
    vertices = source["vertices_world_mm"]
    native = {"path": "toy", "sha256": "toy", "volume_mm3": 200 * 139.7 * 38.1}
    cached = {**native, "grain_axis_xyz": [1, 0, 0], "bounds_xyz_mm": [[0, 200], [-69.85, 69.85], [0, 38.1]]}
    record = {"member": "rail", "basis_grain_u_v_xyz": rail_profile()["basis"], "datum_xyz_mm": [0, 0, 0],
              "raw_profile_vertices_luv_mm": vertices, "raw_source_translation_xyz_mm": [0, 0, 0], "raw_native_body": native}
    assert p.profile_geometry(record, cached, source, SHOP)["convex_volume_mm3"] == pytest.approx(native["volume_mm3"])
    record = copy.deepcopy(record)
    record["raw_profile_vertices_luv_mm"][0][0] = 1
    with pytest.raises(ValueError, match="profile vertex"):
        p.profile_geometry(record, cached, source, SHOP)


def test_actual_source_geometry_only_census_and_conditional_limits():
    result = p.evaluate()
    assert result["counts"] == {"main_angles": 16, "factory_holes_retained": 128,
                                "active_flange_attachments": 64, "unused_factory_holes": 64,
                                "source_raw_members": 11}
    assert result["cadquery_imported"] is False
    assert result["summary"]["square_end_short_of_toward_end_full_factor_attachments"] == 32
    assert len(result["summary"]["affected_flange_pairs"]) == 16
    assert result["summary"]["conditional_square_end_factor_only"] == pytest.approx(41 / 42, abs=1e-8)
    assert result["summary"]["minimum_active_raw_edge_mm"] == pytest.approx(44.45, abs=1e-6)
    assert all(v is False for v in result["release"].values())
    assert all(r["complete_geometry_factor"] is None for r in result["far_and_depth_constraints"])
    rows = result["parallel_grain_member_row_inventory"]
    assert len(rows) == 11 and all(len(r["rows"]) == 2 for r in rows)
    assert min(group["fastener_count"] for r in rows for group in r["rows"]) == 2
    assert sum(group["fastener_count"] for r in rows for group in r["rows"]) == 64


def test_compact_receipt_preserves_hole_ray_identity_and_scope():
    hole = p.factory_holes(station(), DIMENSIONS, 65.0875, 0, SHOP)[2]
    source = p.hole_screen(hole, rail_profile(), 9.525, SHOP, END)
    original = copy.deepcopy(source)
    receipt = p.compact_receipt({"all_factory_hole_scenarios": [source]})
    row = receipt["all_factory_hole_scenarios"][0]
    assert source == original and row["id"] == source["id"]
    for key in ("end_rays", "edge_rays"):
        for a, b in zip(row[key], source[key], strict=True):
            assert a["distance_mm"] == b["distance_mm"]
            assert a["direction_sign"] == b["direction_sign"]
            assert a["square_to_ray"] == b["square_to_ray"]
            assert a["owning_raw_facet_vertex_indices"] == [f["raw_facet_vertex_indices"] for f in b["owning_facets"]]
    assert row["end_rays"][0]["softwood_toward_end_factor_only"] == pytest.approx(41 / 42)
    assert receipt["all_hole_claim_limits"]["complete_geometry_factor"] is None
    assert receipt["all_hole_claim_limits"]["strength_pass"] is False

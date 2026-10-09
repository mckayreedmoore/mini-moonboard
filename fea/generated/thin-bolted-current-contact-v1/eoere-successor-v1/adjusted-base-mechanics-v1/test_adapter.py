"""Real rejected-source regression plus source-only corrected synthetic fixture."""
import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("adjusted_base_adapter_under_test", OWN.with_name("adapter.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def sources():
    old = json.loads((a.ROOT / a.OLD_INPUT).read_bytes())
    v6 = json.loads((a.ROOT / a.BASE / "2026-adjustments-v6/base/geometry.json").read_bytes())
    assert a.sha(a.ROOT / a.OLD_INPUT) == a.OLD_INPUT_SHA
    return old, v6


def corrected_fixture():
    """Synthetic source rows, never represented as the corrected CAD payload."""
    old, v6 = sources()
    current = copy.deepcopy(v6)
    current["axes"] = [copy.deepcopy(r["source_axis"]) for r in old["shafts"]]
    current["affected_duties"] = sorted(a.DUTIES)
    moved = []
    for axis in current["axes"]:
        if any(r["duty_id"] in a.DUTIES for r in axis["attachments"]):
            moved.append(axis["id"])
            axis["point_xyz_mm"] = [x+y for x, y in zip(axis["point_xyz_mm"], a.SHIFT, strict=True)]
            for row in axis["attachments"]:
                row["point"] = [x+y for x, y in zip(row["point"], a.SHIFT, strict=True)]
                line = [x/math.sqrt(sum(v*v for v in row["direction"])) for x in row["direction"]]
                if next(x for x in line if abs(x) > 1e-8) < 0:
                    line = [-x for x in line]
                d = sum(x*y for x, y in zip(a.SHIFT, line, strict=True))
                row["interval_mm"] = [x+d for x in row["interval_mm"]]
    current["moved_bolt_axes"] = moved
    current["screw_axes"] = [copy.deepcopy(r["source_screw_descriptor"]) for r in old["hillman_rows"]]
    current["moved_panel_screw_axes"] = []
    for row in current["screw_axes"]:
        if row["receiver"] in a.MOVED_RAW:
            row["origin_xyz_mm"] = [x+y for x, y in zip(row["origin_xyz_mm"], a.SHIFT, strict=True)]
            current["moved_panel_screw_axes"].append(row["axis_id"])
    owner_sources = {r["id"]: copy.deepcopy(r["source"]) for r in old["finished_body_observations"]}
    changed = a.MOVED_RAW | a.EXTENDED | {"base_header", "base_rail_top"} | a.EXPECTED_PANELS
    for name in changed:
        owner_sources[name]["sha256"] = "synthetic-current-source"
        owner_sources[name].pop("center_of_mass_xyz_mm", None)
    parts = [{**owner_sources[n], "kind": "panel" if n in a.EXPECTED_PANELS else "timber"} for n in sorted(changed)]
    parts += [{"id": "eoere_"+d, "kind": "bracket"} for d in sorted(a.DUTIES)]
    parts += [{"id": axis+"_"+role, "kind": "bolt"} for axis in moved
              for role in ("shaft", "head", "nut", "head_washer", "nut_washer")]
    parts += [{"id": "fastener_"+name, "kind": "screw"} for name in current["moved_panel_screw_axes"]]
    current["changed_finished_solids"] = parts
    return old, current, owner_sources


def test_real_v6_shared_header_attachment_pose_is_rejected():
    old, v6 = sources()
    with pytest.raises(ValueError, match="incoherent shared-axis attachment pose: eoere_clip_split_header_center_right"):
        a.close_ports(old, v6)


def test_signed_negative_X_interval_bug_is_independently_rejected():
    old, current, _ = corrected_fixture()
    count = 0
    for axis in current["axes"]:
        if axis["id"] not in current["moved_bolt_axes"]:
            continue
        for row in axis["attachments"]:
            if row["direction"][0] < -0.999:
                row["interval_mm"] = [x+78.4 for x in row["interval_mm"]]
                count += 1
    assert count == 12
    with pytest.raises(ValueError, match="canonical-positive interval differs"):
        a.close_ports(old, current)


def test_all_source_descriptors_preserve_identity_and_require_changed_own_geometry():
    old, current, solids = corrected_fixture()
    before = a.canonical(old)
    result = a.descriptors(old, current, solids)
    assert a.canonical(old) == before
    assert len(result["physical_owner_gravity_descriptors"]) == 150
    assert len(result["shaft_descriptors"]) == 100
    assert len(result["fitting_ports"]) == 88
    assert sum(len(r["holes"]) for r in result["all_factory_holes"]) == 176
    assert len(result["hillman_rows"]) == 66
    assert len(result["moved_shaft_ids"]) == 22
    assert len(result["moved_screw_ids"]) == 10
    assert len(result["auxiliary_metal_gravity_descriptors"]) == 274
    old_access = json.loads((a.ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/access-takeoff-v4.json").read_bytes())
    shares = [r for r in result["auxiliary_metal_gravity_descriptors"] if r["id"].startswith("fastener_round_kicker_right_center_1/")]
    assert len(shares) == 2
    for share in shares:
        source_id = share["id"].split("/")[0]
        source = next(r for r in old_access["takeoff"]["conditional_metal_gravity_rows"] if r["id"] == source_id and r["owner"] == share["owner"])
        assert share["mass_kg"] == source["mass_kg"]
        assert share["center_xyz_mm"][0] == source["centroid_xyz_mm"][0]-39.2
    features = a.indexed(result["current_panel_machining_descriptors"]["features"], "identity")
    for name in result["moved_screw_ids"]:
        assert features[name]["start_xyz_mm"] == next(r for r in current["screw_axes"] if r["axis_id"] == name)["origin_xyz_mm"]
    beams = a.indexed(result["gross_raw_timber_rows"], "name")
    old_beams = a.indexed(old["timber_rows"], "name")
    for name in a.EXTENDED:
        assert abs(beams[name]["start"][0] - (old_beams[name]["start"][0]-39.2)) < 1e-8
        assert math.dist(beams[name]["end"], old_beams[name]["end"]) < 1e-8
    for name in a.MOVED_RAW:
        assert math.dist(beams[name]["start"], [x+y for x, y in zip(old_beams[name]["start"], a.SHIFT, strict=True)]) < 1e-8
    floor = a.indexed(result["floor_descriptors"], "host")
    assert sum(len(r["normal_reference_points_xyz_mm"]) for r in floor.values()) == 32
    assert [name for name, row in floor.items() if row["centroid_XY_enabled"]] == a.RESTRAINED
    assert floor["base_post_center_right"]["normal_reference_points_xyz_mm"][0][0] == old["floor_footprints"]["base_post_center_right"][0][0]-39.2
    assert floor["base_post_center_right"]["own_floor_face_confirmation_required"]
    assert all(floor[n]["normal_reference_points_xyz_mm"] == old["floor_footprints"][n] for n in a.RESTRAINED)
    assert set(result["pending_COM_owner_ids"]) == set(result["changed_finished_owner_ids"])
    assert result["panel_refresh"]["fresh_aperture_K_mass_and_screw_port_panels"] == sorted(a.EXPECTED_PANELS)
    assert not result["panel_refresh"]["affected_old_coefficient_blocks_reusable_as_unchanged"]


@pytest.mark.parametrize("mutate,match", [
    (lambda r: r["axes"][0]["attachments"].pop(), "attachments missing"),
    (lambda r: r["axes"][0]["attachments"][0]["point"].__setitem__(0, 999.), "off its own moved shaft"),
    (lambda r: r["axes"][0]["attachments"][0]["interval_mm"].__setitem__(0, float("nan")), "finite ordered"),
    (lambda r: r["axes"][0].__setitem__("nominal_under_head_length_mm", 999.), "recipe/receiver changed"),
])
def test_incoherent_ports_recipes_and_dropped_shared_attachments_stop(mutate, match):
    old, current, _ = corrected_fixture()
    mutate(current)
    with pytest.raises(ValueError, match=match):
        a.close_ports(old, current)


@pytest.mark.parametrize("approved,extra", [(False, False), (True, True)])
def test_unapproved_or_extra_on_manifest_rejected_before_geometry_read(tmp_path, approved, extra):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"schema": "eoere_adjusted_base_mechanics_frozen_sources/v1",
                               "parent_model_review_approved": approved, "optional_2026_extra": extra,
                               "geometry": {"path": "does-not-exist", "sha256": "none"}}))
    with pytest.raises(ValueError, match="approved frozen adjusted base"):
        a.preflight(path, a.sha(path))

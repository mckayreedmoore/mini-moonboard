"""Conditional BG045 end-grain lateral scenarios; not joint acceptance."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import sys

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
ACCEL = HERE.parent
GEOMETRY = ACCEL / "bolt-groups/bolt-groups.json"
REVIEWED = ACCEL / "nds-screen/produce.py"
REFERENCE = ACCEL / "nds-screen/single-bolt-scenarios.json"
EXPECTED_GEOMETRY = "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def produce():
    assert digest(GEOMETRY) == EXPECTED_GEOMETRY
    geometry = json.loads(GEOMETRY.read_text())
    reference = json.loads(REFERENCE.read_text())
    helper = ROOT / reference["sources"]["helper"]["path"]
    assert digest(helper) == reference["sources"]["helper"]["sha256"]
    for path, expected in geometry["source_sha256_observed"].items():
        assert digest(ROOT / path) == expected
    calc = runpy.run_path(str(REVIEWED))["calculate"]
    axes = [a for a in geometry["candidate_axes"] if a["group_id"] == "BG045"]
    assert len(axes) == 2
    main = "knee_outer_left_inner_frame_block"
    side = "base_header"
    lengths = []
    for a in axes:
        intervals = a["geometric_receiver_order_proposal"]["receiver_intervals_from_underhead_mm"]
        lm, ls = (intervals[m][1] - intervals[m][0] for m in (main, side))
        assert math.isclose(lm, 139, abs_tol=1e-8)
        assert math.isclose(ls, 38.1, abs_tol=1e-8)
        assert math.isclose(a["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8)
        grains = {r["receiver_member_id"]: r for r in geometry["candidate_axis_receiver_grain_angles"]
                  if r["axis_id"] == a["axis_id"]}
        assert math.isclose(grains[main]["axis_to_grain_angle_deg_unsigned"], 0, abs_tol=1e-8)
        assert math.isclose(grains[side]["axis_to_grain_angle_deg_unsigned"], 90, abs_tol=1e-8)
        lengths.append({"axis_id": a["axis_id"], "main_mm": lm, "side_mm": ls})
    rows = []
    for direction, side_fe in (("global X: parallel to header grain", 5600),
                               ("global Y: perpendicular to header grain", 4450)):
        # Main-member end-grain branch: main bearing is perpendicular-grain
        # regardless of the transverse X/Y lateral direction; Ceg applied once.
        r = calc(.25, lengths[0]["main_mm"] / 25.4,
                 lengths[0]["side_mm"] / 25.4, 4450, side_fe, 90)
        independent_iv = .25**2 / 4 * math.sqrt(2 * 4450 * 45000 / (3 * (1 + 4450 / side_fe)))
        assert math.isclose(r["reference_values_lbf"]["IV"], independent_iv, rel_tol=1e-12)
        z = r["reference_lateral_lbf"] * 4.4482216152605
        rows.append({"direction": direction, "main_Fe_psi": 4450,
                     "side_Fe_psi": side_fe, "yield_mode_result": r,
                     "unadjusted_single_bolt_reference_N": z,
                     "Ceg_only_reference_N": .67 * z, "Ceg": .67})
    return {"candidate": geometry["candidate"], "revision": geometry["geometry_revision_id"],
            "group_id": "BG045", "mechanical_acceptance": False,
            "native_solve_run": False, "accepted_case_demands": None,
            "role_scenario": {"main": main, "side": side,
                "status": "conditional roles for eligible NDS main-member end-grain branch; not inferred from head orientation"},
            "lengths": lengths, "rows": rows,
            "assumptions": ["Full-body 1/4 inch smooth shank in both modeled bearing lengths",
                "Bolt bending yield 45000 psi; explicit wood Fe 4450/5600 psi", "Zero gap",
                "Main receiver has proposed grain parallel to bolt axis; side has proposed grain perpendicular",
                "NDS 2024 12.3.3.4 perpendicular main bearing and 12.5.2.2 Ceg=.67 applicable"],
            "exclusions": ["No actual signed BG045 wrench or load sharing",
                "No group multiplication, Cg, Cdelta or other service adjustments",
                "No axial washer/bolt/nut qualification, splitting or net-section resistance",
                "No delivered shank/stock observations or complete BG003-to-header transfer"],
            "source_hashes": {str(p.relative_to(ROOT)): digest(p) for p in
                (GEOMETRY, REVIEWED, REFERENCE, helper)},
            "NDS_source": reference["sources"]["NDS_2024_chapter_12"]}


if __name__ == "__main__":
    content = json.dumps(produce(), indent=2) + "\n"
    target = HERE / "conditional-screen.json"
    if sys.argv[1:] == ["--write"]:
        target.write_text(content)
    elif sys.argv[1:] == ["--verify"]:
        assert target.read_text() == content
    else:
        raise SystemExit("Use --write or --verify")
    print("BG045 conditional source/role checks and independent mode IV check passed")

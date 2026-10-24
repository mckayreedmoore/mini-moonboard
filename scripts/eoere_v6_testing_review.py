"""Apply the method audit to the current six fields without solving the frame.

Prove the full side-rail breadth using cached solids, retain every projected
hole, and reuse the issued continuous timber worksheet. The original review
and all issued producers remain immutable. Outputs require a fresh directory.
"""

from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
import math
import platform
from pathlib import Path
from unittest.mock import patch

import cadquery as cq
import numpy as np

from scripts import eoere_v6_analysis as analysis
from scripts import eoere_v6_checks as checks
from scripts import eoere_v6_report as reducer
from scripts.eoere_paired_frame_basis import ROOT, read, ref, sha
from scripts.thin_bolted_timber_section_properties import rigid_matrix

OWN = Path(__file__).resolve()
ORIGINAL = ROOT / "docs/bolted-frame-development/owner-frame-v6/engineering-review.json"
OLD_CORE = checks.OUT / "timber-net-geometry-v1.json"
OLD_SECTIONS = checks.OUT / "timber-sections-v1.json"
AUDIT = analysis.WORK / "owner-assumptions-audit-v1/exceedance-method-review-v1/final-result.json"
AUDIT_SHA = "1458f6c2aa76148eb6ddd0c8d84c277f6508aa48e92483888e6ca3b364951c2d"
SIDES = {"base_side_left", "base_side_right"}
TOLERANCE = 0.001


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write_new(path, data):
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def verify(reference):
    require(sha(reference["path"]) == reference["sha256"], f"changed source: {reference['path']}")


def overlap(a, b):
    return min(a[1], b[1]) - max(a[0], b[0]) > 1e-8


def expand_side(row, profile, local_solid):
    """Restore only withheld breadth; reject missing material or filled holes."""
    require(row["member"] in SIDES, "only the two side rails may change")
    result = copy.deepcopy(row)
    vertices = np.asarray(profile["vertices_luv_mm"], dtype=float)
    require(np.isfinite(vertices).all(), "non-finite profile")
    breadth = [float(vertices[:, 1].min()) + TOLERANCE,
               float(vertices[:, 1].max()) - TOLERANCE]
    previous = row["minimum_full_depth_core_bounds_LUV_mm"][1]
    require(math.isclose(breadth[1] - breadth[0], 88.898, abs_tol=1e-6),
            "expected the current nominal 88.9 mm side rail")
    require(math.isclose((breadth[1] - breadth[0]) - (previous[1] - previous[0]),
                         9.525, abs_tol=1e-6), "expected the audited 9.525 mm withheld breadth")
    require(breadth[0] <= previous[0] and previous[1] <= breadth[1], "core must only expand")
    result["minimum_full_depth_core_bounds_LUV_mm"][1] = breadth
    count = 0
    for region in result["net_regions"]:
        lo, hi = region["local_grain_interval_mm"]
        require(hi > lo, "empty grain interval")
        probes = []
        for rectangle in region["retained_rectangles"]:
            u, v = rectangle["bounds_uv_mm"]
            require(np.allclose(u, previous, rtol=0, atol=1e-8),
                    "a partial-breadth ligament requires its own method")
            rectangle["bounds_uv_mm"][0] = list(breadth)
            for hole in result["curved_opening_projections"]:
                if overlap([lo, hi], hole["axial_L_window_mm"]):
                    require(not all(overlap(a, b) for a, b in
                                    zip(rectangle["bounds_uv_mm"], hole["void_bounds_UV_mm"], strict=True)),
                            "expanded core fills a projected hole")
            prism = cq.Solid.makeBox(hi - lo, breadth[1] - breadth[0], v[1] - v[0],
                                    cq.Vector(lo, breadth[0], v[0]))
            volume = prism.Volume()
            missing = max(0., volume - prism.intersect(local_solid).Volume())
            contained = missing <= max(TOLERANCE, volume * 1e-8)
            require(contained, f"uncontained expanded ligament: {row['member']} {lo}..{hi}")
            probes.append({"volume_mm3": volume, "absent_material_mm3": missing,
                           "contained": contained})
            count += 1
        region["containment"] = probes
        region["all_contained"] = True
    result["all_contained"] = True
    result["breadth_review"] = {
        "previous_bounds_U_mm": previous, "current_bounds_U_mm": breadth,
        "restored_breadth_mm": 9.525, "whole_interval_prisms_queried": count,
        "projected_holes_unchanged": True, "grain_intervals_unchanged": True,
        "cached_solid_unchanged": True,
    }
    return result


def corrected_cores(out):
    pins = {}
    core = read(OLD_CORE, pins)
    geometry, fields, active = checks.load()
    pins.update(active)
    require(core["geometry"] == ref(analysis.GEOMETRY), "current core geometry mismatch")
    require(core["member_count"] == 20 and core["all_nominal_core_prisms_contained"],
            "expected twenty previously contained current sawn cores")
    require({r["member"] for r in core["rows"]} ==
            {m["name"] for m in fields[0][3]["source_inputs"]["timber_rows"]
             if not m["name"].startswith("eoere_cleat_")}, "current sawn inventory mismatch")
    changed = []
    for i, row in enumerate(core["rows"]):
        if row["member"] not in SIDES:
            continue
        profile = geometry["profiles"][row["member"]]
        require(row["source"] == profile["finished"], "current side solid mismatch")
        verify(row["source"])
        frame = np.asarray(row["basis"])
        datum = np.asarray(row["datum_xyz_mm"])
        transform = rigid_matrix([[*r, float(t)] for r, t in
                                  zip(frame, -frame @ datum, strict=True)] + [[0, 0, 0, 1]])
        solid = cq.Shape.importBrep(str(ROOT / row["source"]["path"])).transformShape(transform)
        core["rows"][i] = expand_side(row, profile, solid)
        changed.append(row["member"])
    require(set(changed) == SIDES, "both side rails required")
    for path in (OWN, ORIGINAL, OLD_CORE, AUDIT, Path("scripts/thin_bolted_timber_section_properties.py")):
        pins[ref(path)["path"]] = sha(path)
    core["source_sha256"].update(pins)
    core["breadth_review_producer"] = ref(OWN)
    core["limits"].append(
        "The two side rails credit their full contained 88.898 mm nominal breadth; "
        "all projected bores, simultaneous deductions and grain intervals are unchanged. "
        "Containment does not qualify drilled-joint stresses or physical material.")
    for path, digest in core["source_sha256"].items():
        require(sha(path) == digest, f"core source changed: {path}")
    write_new(out / "timber-net-geometry-v1.json", core)
    return core


def member_maxima(sections):
    members = {row["member"] for case in sections["cases"] for row in case["members"]}
    return {name: {metric: max(
        ({"index": row[metric], "case_id": case["case_id"]}
         for case in sections["cases"] for row in case["members"] if row["member"] == name),
        key=lambda item: item["index"])
        for metric in reducer.TIMBER_METRICS} for name in sorted(members)}


def unchanged_maxima(base):
    # Shaft summaries distinguish the full 96-shaft population from its two
    # subpopulations; the plywood summaries use one overall group maximum.
    return {group: {metric: data["all_96" if group == "shafts_Cdelta_adjusted" else "overall"]
                    for metric, data in base["metric_maxima"][group].items()}
            for group in ("shafts_Cdelta_adjusted", "plywood_nominal_38p1", "plywood_credited_36p5")}


def build_summary(out, core, base):
    sections = json.loads((out / "timber-sections-v1.json").read_bytes())
    old_sections = json.loads(OLD_SECTIONS.read_bytes())
    for source, digest in sections["source_sha256"].items():
        require(sha(source) == digest, f"section source changed: {source}")
    maxima, exceedances = reducer.summarize_timber(sections)
    old, current = member_maxima(old_sections), member_maxima(sections)
    require(old.keys() == current.keys(), "member inventory changed")
    for name in old.keys() - SIDES:
        require(old[name] == current[name], f"unrelated member result changed: {name}")
    comparisons = [{"member": name, "original": old[name], "current": current[name]}
                   for name in sorted(SIDES | {"base_header", "base_rail_top"})]
    return {
        "schema": "eoere_current96_testing_method_review/v1",
        "geometry_revision": base["geometry_revision"], "physical_geometry": base["physical_geometry"],
        "analysis_geometry": base["analysis_geometry"], "base_review": ref(ORIGINAL),
        "case_ids": base["case_ids"], "case_count": 6, "load_contract": base["load_contract"],
        "inventory": {key: base["inventory"][key] for key in (
            "current_bolts", "sawn_timber_members", "physical_plywood_leaves", "panel_screws_deferred")},
        "source_bindings": {"producer": ref(OWN), "original_core": ref(OLD_CORE),
                            "original_sections": ref(OLD_SECTIONS), "prior_method_audit": ref(AUDIT),
                            "corrected_core": ref(out / "timber-net-geometry-v1.json"),
                            "corrected_sections": ref(out / "timber-sections-v1.json"),
                            "worksheet_intake": ref(out / "sections.current96-intake.json")},
        "side_core_changes": [{"member": row["member"], **row["breadth_review"]}
                              for row in core["rows"] if row["member"] in SIDES],
        "timber_reference_maxima": maxima, "member_comparisons": comparisons,
        "timber_member_metric_exceedances": exceedances,
        "unchanged_reference_maxima": unchanged_maxima(base),
        "geometry_eligibility": {key: base["geometry_eligibility"][key] for key in (
            "all_geometry_eligible", "eligible_axis_count_by_case", "no_pass_when_geometry_ineligible")},
        "testing_disposition": {
            "side_core_breadth_correction_applied": True,
            "current_six_case_all_interval_timber_references_recomputed": True,
            "original_bolt_and_cleat_references_retained": True,
            "all_force_couples_and_hole_deductions_retained": True,
            "midface_probe_or_force_only_row_used_as_pass": False,
            "reduced_bolt_interaction_replaced_by_elastic_index": False,
            "geometry_ineligibility_waived": False,
            "physical_failure_inferred_from_reference_exceedance": False,
            "new_frame_or_native_solve": False, "cad_rebuilt": False,
            "physical_geometry_or_loads_changed": False,
        },
        "qualification": base["qualification"],
        "limitations": [
            ("All six fields already include the complete modeled assembly, six panels and 66 screw springs. "
            "Generic 1000 N/mm axial/lateral Hillman spring stiffness is an unqualified assumption; "
            "panel presence does not establish physical load sharing or complete screw strength."),
            ("The rectangular torsion mathematics was independently checked in the prior audit. "
            "Common twist, area-proportional direct shear and intact ligament bridges at short loaded "
            "bore zones remain an engineering construction, not a verified three-dimensional joint stress bound."),
            ("Separate shear and torsion peak addition remains a conservative worksheet construction. "
            "Selected compatible midface probes cannot replace an all-point bound."),
            ("Reduced bolt interaction and elastic axial/bending/shear are distinct references; "
            "neither clears wood bearing, loaded edges or complete-joint behavior."),
            ("Plywood rows retain both leaves, through-thickness pressure and full force/first moment. "
            "The force-only lower comparison cannot clear the balanced row comparison. "
            "The NDS-style row/APA input combination remains an engineering extension."),
            ("Perfect plywood bonding, uniform 139.7 mm trapezoid beam approximation, gross timber "
            "response, first-order kinematics, stated restraints and the unverified no-slip floor "
            "hypothesis retain their original applicability limits. No actual adhesive or floor is qualified."),
            ("The eight upper axes remain geometry-ineligible in all six cases. Correcting side-core "
            "breadth does not change their edges, pair spacing, bolt forces or joint eligibility."),
        ],
        "tools": {"python": platform.python_version(), **{name: importlib.metadata.version(name)
                  for name in ("cadquery", "numpy", "scipy")}},
        "release": False,
    }


def run(out):
    require(out.is_relative_to(analysis.BASE), "output must remain in the current ignored analysis packet")
    require(sha(AUDIT) == AUDIT_SHA, "prior audit binding changed")
    index = json.loads((ROOT / "docs/bolted-frame-development/development-revisions.json").read_bytes())
    require(index["engineering_review"] == ref(ORIGINAL), "original current review binding changed")
    base = json.loads(ORIGINAL.read_bytes())
    require(base["physical_geometry"] == index["geometry"]["receipt"], "current geometry mismatch")
    # Reuse the issued reducer's source, replay, geometry and metric admission checks.
    reducer.HASH_CACHE.clear()
    replayed = reducer.build_report(out / "original-review-replay.json")
    require(replayed["metric_maxima"] == base["metric_maxima"], "original reference replay differs")
    out.mkdir(parents=True, exist_ok=False)
    (out / "producer-snapshot.py").write_bytes(OWN.read_bytes())
    core = corrected_cores(out)
    with patch.object(checks, "OUT", out):
        checks.worksheet("sections")
    summary = build_summary(out, core, base)
    write_new(out / "testing-review.json", summary)
    print(json.dumps({"result": ref(out / "testing-review.json"),
                      "timber_exceedance_count": len(summary["timber_member_metric_exceedances"]),
                      "members": summary["member_comparisons"]}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.out.resolve())


if __name__ == "__main__":
    main()

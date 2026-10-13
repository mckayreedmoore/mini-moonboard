"""Finished-wood support of the 112 current nominal washer seats.

Reads cached finished solids and authenticated current fields. Thin annular
containment proves modeled material occupancy only, not contact or strength.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from scripts import eoere_current_components as component
from scripts import eoere_current_response as current
from scripts.summarize_eoere_current_response import SEQUENCE, canonical_sha

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
INPUTS = {
    "path": str((current.DOC / "selected-hardware-v1/current-response-v1/joint-closure-v1/inputs-v2.json").relative_to(current.ROOT)),
    "sha256": "4e41f60fbfb76e95a51f0ca8c358855f3b60e41547a1e6ba720bf40782a4ea2d",
}
PROBE = {
    "path": str((current.DOC / "bounded-strength-v1/resistance-followup-v1/analyze.py").relative_to(current.ROOT)),
    "sha256": "5cddc0db7a3976d232e84b9789eccff0e7b0b99ca11bcf24bb0ef3dc28bfa5a7",
}
PARENT = {
    "path": str((current.DOC / "bounded-strength-v1/analyze.py").relative_to(current.ROOT)),
    "sha256": "8bffd53e9e730e63db2f041a10626edb002cba7034af118d6dc9bdf3fed69ae3",
}


def intake():
    inputs = current.read(INPUTS)
    forces, components = current.read(inputs["current_response"]), current.read(inputs["current_components"])
    manifest = current.manifest()
    current.require(forces["case_sequence"] == components["case_sequence"] == SEQUENCE
                    and [r["case_id"] for r in forces["cases"]] == [r["case_id"] for r in components["cases"]] == SEQUENCE
                    and len({r["state_id"] for r in forces["cases"]}) == 6
                    and forces["geometry_revision"] == components["geometry_revision"] == "eoere-raised-kicker-screws-v1"
                    and forces["hardware_revision"] == components["hardware_revision"] == "eoere-selected-purchase-hardware-v1"
                    and forces["extra_grid"] is False and components["extra_grid"] is False
                    and forces["all_six_saved_field_admissions_pass"] is True
                    and forces["geometry"] == components["geometry"] == manifest["geometry"]
                    and forces["hardware_model"] == components["hardware_model"] == manifest["hardware_model"]
                    and forces["release"] == components["release"] == manifest["release"]
                    and components["current_response"] == inputs["current_response"], "exact current six-case evidence required")
    maps, refs = [], [INPUTS, PROBE, PARENT, current.ref(OWN), inputs["current_response"], inputs["current_components"],
                      *inputs["case_components"]]
    for report in [forces, components]:
        union = report["source_union"]
        sources = current.read(union["record"])
        current.require(len(sources) == union["count"] and canonical_sha(sources) == union["canonical_sha256"], "parent source union differs")
        maps.append(sources)
        refs.append(union["record"])
    pins = current.join(*maps, {r["path"]: r["sha256"] for r in refs})
    current.verify(pins)
    cases = []
    for binding, summary, raw_ref in zip(forces["cases"], components["cases"], inputs["case_components"], strict=True):
        field, data = current.read(binding["field"]), current.read(raw_ref)
        current.require(field["case_id"] == data["case_id"] == summary["case_id"] == binding["case_id"]
                        and field["state_id"] == data["state_id"] == summary["state_id"] == binding["state_id"]
                        and data["field"] == summary["field"] == binding["field"]
                        and data["admission"] == summary["admission"] == binding["admission"]
                        and data["raw_field_canonical_sha256"] == canonical_sha(field), "own current field/component join required")
        cases.append((binding, field, data))
    return cases, pins


def seat_geometry(row, end):
    current.require(row["receiver_kind"] == "wood" and 0 <= row["grain_axis_abs_cos_to_pressure_normal"] < 1e-8
                    and row["host"] == end["second"] and row["capture_id"] == end["id"]
                    and row["axis_id"] == end["axis_id"], "own perpendicular-grain wood seat required")
    profiles = [row["nominal_own_hardware_geometry"], *row["USS_catalog_corners_min_thickness"]]
    current.require(all(math.isfinite(p["OD_mm"]) and math.isfinite(p["ID_mm"]) and math.isfinite(p["source_support_opening_diameter_mm"])
                        and 0 < p["ID_mm"] < p["OD_mm"] and 0 < p["source_support_opening_diameter_mm"] < p["OD_mm"]
                        for p in profiles), "finite positive own profile annuli required")
    outer = max(p["OD_mm"] for p in profiles)
    inner = min(max(p["ID_mm"], p["source_support_opening_diameter_mm"]) for p in profiles)
    current.require(math.isfinite(outer) and math.isfinite(inner) and 0 < inner < outer, "positive bounding annulus required")
    point, inward = np.asarray(end["host_support_point_xyz_mm"]), -np.asarray(end["end"]["direction_on_shaft_xyz"])
    delta = point-np.asarray(end["point_xyz_mm"])
    current.require(np.isfinite(point).all() and abs(np.linalg.norm(inward)-1.) < 1e-10
                    and float(delta @ inward) > 0 and np.linalg.norm(np.cross(delta, inward)) < 1e-6
                    and np.linalg.norm(point-row["own_support_point_xyz_mm"]) < 1e-6, "concentric inward seat datum required")
    return {"capture_id": row["capture_id"], "axis_id": row["axis_id"], "host": row["host"],
            "point_xyz_mm": point.tolist(), "inward_xyz": inward.tolist(),
            "bounding_OD_mm": outer, "bounding_inner_diameter_mm": inner,
            "least_profile_ring_area_mm2": min(math.pi/4*(p["OD_mm"]**2-max(p["ID_mm"], p["source_support_opening_diameter_mm"])**2) for p in profiles)}


def run():
    cases, pins = intake()
    first = cases[0][1]
    timber_names = {r["name"] for r in first["source_inputs"]["timber_rows"]}
    observations = {r["id"]: r for r in first["source_inputs"]["finished_body_observations"] if r["id"] in timber_names}
    current.require(len(timber_names) == len(observations) == 22 and len(first["source_inputs"]["shafts"]) == 100
                    and all(f["source_inputs"]["timber_rows"] == first["source_inputs"]["timber_rows"]
                    and f["source_inputs"]["finished_body_observations"] == first["source_inputs"]["finished_body_observations"]
                    and f["source_inputs"]["shafts"] == first["source_inputs"]["shafts"] for _, f, _ in cases), "same current 22 solids and shafts required")
    sources = [r["source"] for r in observations.values()]
    pins = current.join(pins, {r["path"]: r["sha256"] for r in sources})
    current.verify(pins)
    method = component.load(PROBE, "current_washer_annulus")
    known = method.known_answers()
    import cadquery as cq

    shapes, geometry, bindings = {}, {}, []
    for binding, field, data in cases:
        ends = {e["id"]: e for e in field["shaft_end_capture_actions"]}
        all_rows = data["findings"]["washers"]["all200_own_end_diagnostics"]
        rows = [r for r in all_rows if r["receiver_kind"] == "wood"]
        current.require(len(all_rows) == len(ends) == 200 and len(rows) == len({r["capture_id"] for r in rows}) == 112,
                        "112 own wood seats and 200 captures required")
        comparisons = []
        for row in rows:
            seat = seat_geometry(row, ends[row["capture_id"]])
            key, host = seat["capture_id"], seat["host"]
            if key not in geometry:
                observation = observations[host]
                if host not in shapes:
                    shape = cq.Shape.importBrep(str(current.ROOT/observation["source"]["path"]))
                    current.require(shape.isValid() and len(shape.Solids()) == 1 and abs(shape.Volume()-observation["volume_mm3"]) < .01,
                                    "current cached wood solid differs")
                    shapes[host] = shape
                probe = method.annular_probe(shapes[host], seat["point_xyz_mm"], seat["inward_xyz"], seat["bounding_OD_mm"], seat["bounding_inner_diameter_mm"])
                geometry[key] = {**seat, "solid_source": observation["source"], "thin_annulus": probe}
            current.require(all(geometry[key][k] == v for k, v in seat.items()), "same own seat geometry across six states required")
            force = row["N_n"]
            current.require(math.isfinite(force) and force >= 0 and abs(force-ends[key]["compression_n"]) < 1e-7,
                            "nonnegative own axial capture force required")
            comparisons.append({"capture_id": key, "own_model_axial_n": force,
                                "least_profile_area_uniform_mean_mpa": force/seat["least_profile_ring_area_mm2"],
                                "physical_pressure_couple_or_combined_resistance": None})
        bindings.append({**binding, "wood_seat_comparisons": comparisons})
    current.verify(pins)
    current.require(current.sha(OWN) == LOADED_SHA, "loaded producer changed")
    return {"schema": "eoere_current_finished_wood_washer_seats/v1", "producer": current.ref(OWN), "inputs": INPUTS,
            "source_sha256": pins, "all_sources_unchanged": True, "known_answer_checks": known,
            "case_sequence": SEQUENCE, "cases": bindings, "wood_seats": list(geometry.values()),
            "all112_bounding_thin_annuli_inside_modeled_finished_wood": all(r["thin_annulus"]["full_modeled_support"] for r in geometry.values()),
            "geometry_revision": "eoere-raised-kicker-screws-v1", "hardware_revision": "eoere-selected-purchase-hardware-v1", "extra_grid": False,
            "native_solve_CAD_rebuild_or_remedy_performed": False, "actual_fit_or_contact_observed": False,
            "release": current.manifest()["release"],
            "complete_hardware_or_wood_resistance": None, "structural_acceptance": False,
            "limits": ["Concentric ideal nominal/catalog annuli are queried 0.1 mm inward into exact cached finished solids; no received-part flatness, washer footprint or actual contact is observed.",
                       "Volume containment tolerance is the reused 1e-4 mm3 numerical gate, not a physical gap/pressure criterion.",
                       "Uniform mean stress is a geometric diagnostic. Eccentric pressure, local crushing/fracture, washer/spacer bending and complete joint interaction require separate resistance."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with current.load("bridge").reserve(args.out) as output:
        output.write(run())
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()

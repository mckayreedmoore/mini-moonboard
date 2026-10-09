"""Exact OFF extended-cleat intake; cached-solid queries remain parent gated.

Reuse the frozen adjusted-base metadata and cached-solid exporter. This wrapper
changes only the two cleat source bindings and declared gross blank profiles.
It constructs no frame, stiffness, load cases, response or physical acceptance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[6]
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
EXPORT = OWN.parent.parent / "current-source-export-v1/export.py"
EXPORT_SHA = "718fc48186bbb37ef297a599d371a0a8def020864c90426c8e5492dcd404fb2f"
if hashlib.sha256(EXPORT.read_bytes()).hexdigest() != EXPORT_SHA:
    raise ValueError("preserve the frozen cached-solid exporter")
spec = importlib.util.spec_from_file_location("frozen_cached_export_for_extended_cleats", EXPORT)
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
a, require = e.a, e.require
DOC = "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/"
GEOMETRY = {"path": DOC + "occupied-extended-cleats-v1.json",
            "sha256": "01ba30abe20c2efec136374b8d9a74a098a19929be3cc784b5ebcf7608e62a2d"}
PARENT = {"path": DOC + "occupied-adjusted-base-v3.json",
          "sha256": "5e0f05ea39347edcd89e088ab0cd478976b9a7ae9dabcc78c1b92e24d1f01aa7"}
CLEATS = {"eoere_cleat_left", "eoere_cleat_right"}


def checked_manifest(path, expected_sha):
    path = Path(path).resolve()
    require(a.sha(path) == expected_sha, "exact frozen parent manifest SHA required")
    manifest = json.loads(path.read_bytes())
    require(manifest.get("schema") == "eoere_extended_cleat_mechanics_frozen_sources/v1"
            and manifest.get("parent_model_review_approved") is True
            and manifest.get("optional_2026_extra") is False
            and manifest.get("geometry") == GEOMETRY
            and manifest.get("revision") == "eoere-base-side-edge-cleats-v1",
            "approved exact extended-cleat OFF manifest required")
    require(manifest.get("readiness") == {"cached_descriptor_source_intake": True,
            "actual_extraction_needs_separate_reviewed_method_and_serial_slot": True,
            "candidate_assembly_or_solve": False, "independent_current_field_admission": False}
            and manifest.get("release") and all(v is False for v in manifest["release"].values()),
            "cached-descriptor-only parent authority boundary required")
    ref = {"path": path.relative_to(ROOT).as_posix(), "sha256": expected_sha}
    parent = manifest["parent_base_manifest"]
    require(set(parent) == {"path", "sha256"}
            and not Path(parent["path"]).is_absolute()
            and (ROOT / parent["path"]).resolve().is_relative_to(ROOT),
            "exact repository parent-base manifest reference required")
    return manifest, ref


def close_extension(current, parent):
    """Close the extension against complete records, not a display summary."""
    require(current.get("schema") == "eoere_cleat_top_extension_geometry/v1"
            and current.get("candidate") == parent.get("candidate")
            == "compact-floor-flush-eoere-bolted-development"
            and current.get("revision") == "eoere-base-side-edge-cleats-v1"
            and current["parent_geometry"]["base"] == PARENT
            and current.get("only_two_cleat_bodies_changed") is True
            and all(v is False for v in current["release"].values()),
            "exact two-cleat geometry and release boundary required")
    require(current["axes"] == parent["axes"]
            and len(a.indexed(current["axes"], "id")) == 100
            and a.canonical(current["axes"]) == current["base_100_axis_records_canonical_sha256"],
            "all100 shaft records must equal exact OFF parent")
    require(current["screw_axes"] == parent["screw_axes"]
            and len(a.indexed(current["screw_axes"], "axis_id")) == 66
            and a.canonical(current["screw_axes"]) == current["base_66_screw_records_canonical_sha256"],
            "all66 screw records must equal exact OFF parent")
    require(current["counts"]["base"] == parent["counts"], "OFF owner census differs from parent")
    require(len(current["changed_finished_solids"]) == 2
            and set(a.indexed(current["changed_finished_solids"], "id")) == CLEATS,
            "only two finished cleat source replacements permitted")


def extend_descriptors(preflight, current, ex, m):
    """Separate full rectangular gross blanks from sloping finished solids."""
    result = copy.deepcopy(preflight)
    polygon = current["new_cleat_YZ_polygon_mm"]
    require(len(polygon) == 4 and all(len(p) == 2 and all(math.isfinite(v) for v in p) for p in polygon),
            "finite four-corner finished cleat polygon required")
    length = current["maximum_blank_length_mm"]
    require(math.isfinite(length) and length > 289.7
            and abs(max(p[1] for p in polygon)-min(p[1] for p in polygon)-length) < 1e-8,
            "finished polygon and maximum gross blank length differ")
    replacements = a.indexed(current["changed_finished_solids"], "id")
    profiles = a.indexed(result["gross_raw_timber_rows"], "name")
    owners = a.indexed(result["physical_owner_gravity_descriptors"], "id")
    for name in sorted(CLEATS):
        source, owner = replacements[name], owners[name]
        require(abs(source["parent_volume_mm3"]-owner["source"]["volume_mm3"]) < .01
                and source["valid_single_solid"] is True and source["volume_mm3"] > 0,
                "finished cleat replacement does not close to parent source")
        profile = copy.deepcopy(profiles[name]["raw_profile_source"])
        require(profile["basis_grain_u_v_xyz"] == [[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]]
                and profile["grain_inspected"] is False
                and profile["raw_stock_scenario_dimensions_mm"] == [38.1, 139.7, 289.7],
                "preserved declared cleat grain/gross-stock basis required")
        require(source["bounds_xyz_mm"][0] == [profile["datum_xyz_mm"][0], profile["datum_xyz_mm"][0]+38.1]
                and source["bounds_xyz_mm"][1] == [min(p[0] for p in polygon), max(p[0] for p in polygon)]
                and source["bounds_xyz_mm"][2] == [min(p[1] for p in polygon), max(p[1] for p in polygon)],
                "finished cleat source bounds and profile differ")
        profile["raw_profile_vertices_luv_mm"] = [[z, x, y] for z in (0., length) for x in (0., 38.1) for y in (0., 139.7)]
        profile["raw_stock_scenario_dimensions_mm"] = [38.1, 139.7, length]
        profile["current_analysis_transform"] = "full rectangular gross blank extends to current maximum height; finished sloping cut remains separate"
        profile["finished_YZ_polygon_mm"] = copy.deepcopy(polygon)
        profile["current_geometry_source"] = copy.deepcopy(GEOMETRY)
        profiles[name] = ex.gross_row(profile, m)
        owner.update(source=copy.deepcopy(source), center_xyz_mm=copy.deepcopy(source["center_of_mass_xyz_mm"]),
                     mass_kg=source["volume_mm3"]*result["parameters"]["wood_density_kg_m3"]*1e-9,
                     own_COM_query_required=False)
    result["gross_raw_timber_rows"] = [profiles[r["name"]] for r in result["gross_raw_timber_rows"]]
    for shaft in result["shaft_descriptors"]:
        for wall in shaft["wood_walls"]:
            if wall["receiver"] in CLEATS:
                wall.update(current_full_wall_query_required=True, intervals_mm=None)
        shaft["current_external_seat_join_required"] = any(w["current_full_wall_query_required"] for w in shaft["wood_walls"])
    result["required_own_wall_queries"] = [{"axis_id": s["axis_id"], "receiver": w["receiver"]}
                                            for s in result["shaft_descriptors"] for w in s["wood_walls"]
                                            if w["current_full_wall_query_required"]]
    require(sum(w["receiver"] in CLEATS for w in result["required_own_wall_queries"]) == 8,
            "eight current cleat wall queries required")
    bindings = {(b["angle_id"], ex.port_id(b["flange"], b["transverse"])): b
                for axis in current["axes"] for b in axis["attachments"]}
    for port in result["fitting_ports"]:
        binding = bindings[(port["angle_id"], port["model_port_id"])]
        port.update(source_flange=binding["flange"], source_transverse=binding["transverse"])
    result.update(schema="eoere_extended_cleat_mechanics_source_preflight/v1", geometry=copy.deepcopy(GEOMETRY),
                  parent_base_geometry=copy.deepcopy(PARENT), extension_finished_owner_ids=sorted(CLEATS))
    result["changed_finished_owner_ids"] = sorted(set(result["changed_finished_owner_ids"]) | CLEATS)
    result["pending_COM_owner_ids"] = sorted(r["id"] for r in result["physical_owner_gravity_descriptors"] if r.get("own_COM_query_required"))
    return result


def prepare(manifest_path, expected_sha):
    manifest, manifest_ref = checked_manifest(manifest_path, expected_sha)
    ref = manifest["parent_base_manifest"]
    p = a.preflight(ROOT / ref["path"], ref["sha256"])
    require(p["geometry"] == PARENT, "exact reviewed v3 parent-base intake required")
    pins = dict(p["source_sha256"])
    a.join(pins, {manifest_ref["path"]: expected_sha, str(OWN.relative_to(ROOT)): LOADED_SHA,
                  str(EXPORT.relative_to(ROOT)): EXPORT_SHA})
    parent_manifest = a.read_ref(ref, pins)
    require(parent_manifest.get("readiness") == manifest["readiness"]
            and parent_manifest.get("release") == manifest["release"],
            "parent-base intake authority boundary differs")
    review_dependencies = []
    for reviewed in (manifest, parent_manifest):
        require(reviewed.get("parent_geometry_review_evidence"), "parent geometry review evidence required")
        for evidence_ref in reviewed["parent_geometry_review_evidence"].values():
            # These frozen review receipts are authority evidence, not invoked
            # producers. Their historical viewer-runtime pins stay historical.
            evidence = a.read_ref(evidence_ref, pins)
            review_dependencies.append((evidence_ref, evidence.get("source_sha256", {})))
    current = a.read_ref(GEOMETRY, pins)
    parent = a.read_ref(PARENT, pins)
    close_extension(current, parent)
    a.join(pins, current["source_sha256"])
    proposal = a.read_ref(current["proposal"], pins)
    a.join(pins, proposal["source_sha256"])
    a.verify(pins)
    ex, m = a.generic()
    p = extend_descriptors(p, current, ex, m)
    old = a.read_ref({"path": a.OLD_INPUT, "sha256": a.OLD_INPUT_SHA}, pins)
    baseline = a.read_ref(old["geometry"]["report"], pins)
    sources = {r["id"]: copy.deepcopy(r["source"]) for r in p["physical_owner_gravity_descriptors"] if r["kind"] in {"timber", "panel"}}
    require(len(sources) == 28, "22 current timbers and six current panels required")
    a.join(pins, {s["path"]: s["sha256"] for s in sources.values()})
    review_checks = []
    for evidence_ref, historical in review_dependencies:
        overlap = {path: digest for path, digest in historical.items() if path in pins}
        require(all(pins[path] == digest for path, digest in overlap.items()),
                "historical review computational overlap differs from current source closure")
        review_checks.append({"evidence": evidence_ref, "current_computational_overlap_pins_verified": len(overlap),
                              "current_computational_overlap_canonical_sha256": a.canonical(overlap),
                              "historical_viewer_hashes_not_used_as_current_runtime": {path: digest for path, digest in historical.items()
                                                                                       if path.startswith("site/") and path not in pins}})
    p.update(source_sha256=pins, manifest=manifest_ref, parent_base_manifest=copy.deepcopy(ref))
    p["geometry_review_evidence"] = {"current": copy.deepcopy(manifest["parent_geometry_review_evidence"]),
                                      "parent_base": copy.deepcopy(parent_manifest["parent_geometry_review_evidence"]),
                                      "dependency_checks": review_checks,
                                      "historical_review_execution_dependencies_used_as_current_inputs": False}
    p["unresolved"].append("Both extended cleat finished-source observations, eight own bore walls, complete current seats and opposed-face atlas remain current-source obligations")
    report = {"axes": current["axes"], "scenario": baseline["scenario"],
              "finished_solids": [sources[n] for n in sorted(sources) if n not in old["panel_ids"]]}
    panels = [sources[n] for n in old["panel_ids"]]
    a.verify(pins)
    return p, old, report, panels, pins


def source_plan(manifest_path, expected_sha):
    prepared = prepare(manifest_path, expected_sha)
    with patch.object(e, "prepare", lambda *_: prepared):
        result = e.source_plan(manifest_path, expected_sha)
    result.update(schema="eoere_extended_cleat_cached_source_export_plan/v1",
                  manifest=prepared[0]["manifest"], parent_base_geometry=copy.deepcopy(PARENT),
                  geometry_review_evidence=prepared[0]["geometry_review_evidence"],
                  gross_profile_basis="two current maximum-length rectangular blanks; declared +Z grain; finished sloping sources separate")
    result["serial_slot_API"]["approved_manifest_sha256"] = expected_sha
    return result


def export_native(manifest_path, expected_sha, slot_path, slot_sha):
    require(os.environ.get("EOERE_PARENT_SERIALIZED_EXTRACTION") == "1",
            "parent serialized extraction marker required before current source intake")
    prepared = prepare(manifest_path, expected_sha)
    serial = e.slot(slot_path, slot_sha, GEOMETRY["sha256"])
    require(serial["record_at_start"].get("approved_manifest_sha256") == expected_sha,
            "parent serial slot must bind the exact frozen intake manifest SHA")
    with patch.object(e, "prepare", lambda *_: prepared):
        result = e.export_native(manifest_path, expected_sha, slot_path, slot_sha)
    p = prepared[0]
    result.update(schema="eoere_extended_cleat_cached_source_export/v1", manifest=p["manifest"],
                  parent_base_geometry=copy.deepcopy(PARENT), parent_base_manifest=p["parent_base_manifest"],
                  extension_finished_owner_ids=sorted(CLEATS))
    for key in ("parameters", "material_scenario", "support", "case_provider", "panel_refresh", "geometry_review_evidence"):
        result[key] = copy.deepcopy(p[key])
    a.verify(prepared[4])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--slot", type=Path)
    parser.add_argument("--slot-sha256")
    args = parser.parse_args()
    require(not args.out.exists(), "preserve prior descriptor output before any source/native intake")
    start = time.monotonic()
    result = export_native(args.manifest, args.manifest_sha256, args.slot, args.slot_sha256) if args.extract else source_plan(args.manifest, args.manifest_sha256)
    result["execution"] = {"command": list(sys.orig_argv), "elapsed_seconds": time.monotonic()-start}
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.out), "schema": result["schema"]}))


if __name__ == "__main__":
    main()

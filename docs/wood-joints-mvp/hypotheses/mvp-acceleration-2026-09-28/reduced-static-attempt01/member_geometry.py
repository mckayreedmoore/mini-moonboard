"""Read source-pinned WJ24 STEP geometry into gross member descriptors.

No CAD reconstruction, attachment mapping, meshing, material values, or solve.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).with_name("member-geometry.json")
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PINS = {
    "adapter_pins": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-adapter-attempt01/source-pins.json", "b5fde1e393092e4fcd2403245db6608ae7916c4f12ed5f7da4e6049024deb53c"),
    "manifest": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json", "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11"),
    "bundle": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json", "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420"),
    "timber_frames": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json", "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409"),
    "block_frames": ("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-block-material-frame-map-attempt02/material-frame-map.json", "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480"),
}
TOL = 1e-8


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_json(name: str):
    rel, expected = PINS[name]
    path = ROOT / rel
    if digest(path) != expected:
        raise ValueError(f"pinned input changed: {rel}")
    return json.loads(path.read_text()), rel, expected


def verify_map_pins(data, label: str) -> int:
    pins = data.get("source_pins")
    if not isinstance(pins, dict):
        raise ValueError(f"{label}: missing source_pins")
    for rel, record in pins.items():
        if digest(ROOT / rel) != record["sha256"]:
            raise ValueError(f"{label}: source pin changed: {rel}")
    return len(pins)


def dot(a, b):
    return sum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def norm(v):
    return math.sqrt(dot(v, v))


def unit(v):
    n = norm(v)
    if not math.isfinite(n) or n == 0:
        raise ValueError("invalid material-frame vector")
    return [float(x) / n for x in v]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def check_frame(axes):
    if set(axes) != {"X", "T", "N"}:
        raise ValueError("expected source X/T/N frame")
    vectors = {key: unit(axes[key]) for key in axes}
    if any(abs(norm(axes[k])-1) > TOL for k in axes):
        raise ValueError("non-unit source frame")
    if any(abs(dot(vectors[a], vectors[b])) > TOL for a, b in (("X", "T"), ("T", "N"), ("N", "X"))):
        raise ValueError("non-orthogonal source frame")
    if dot(cross(vectors["X"], vectors["T"]), vectors["N"]) < 1-TOL:
        raise ValueError("left-handed source frame")


def frame_record(source, kind):
    if kind == "timber":
        axes = source["source_frame"]["axes_global_xyz"]
        grain = unit(source["conditional_grain_assignment"]["proposed_global_xyz"])
        components = source["source_frame"]["grain_components_in_source_frame"]
        rebuilt = [sum(components[k]*axes[k][i] for k in ("X", "T", "N")) for i in range(3)]
        if max(abs(a-b) for a, b in zip(grain, rebuilt, strict=True)) > TOL:
            raise ValueError(f"{source['member_id']}: grain/source frame mismatch")
        identifier = source["member_id"]
        scenario_ids = []
        transverse = source["transverse_ring_axes"]["status"]
    else:
        axes = source["source_frame_axes_global_xyz"]
        grain = unit(source["conditional_grain_assignment"]["grain_direction_global_xyz"])
        identifier = source["part_id"]
        scenarios = source["transverse_assignment_cases"]
        scenario_ids = [row["scenario_id"] for row in scenarios]
        for row in scenarios:
            material = row["material_axes_global_xyz"]
            if (abs(dot(material["L"], grain)-1) > TOL
                    or abs(dot(material["R"], material["T"])) > TOL
                    or dot(cross(material["L"], material["R"]), material["T"]) < 1-TOL):
                raise ValueError(f"{identifier}: conditional material frame mismatch")
        transverse = "R/T unresolved; two conditional assignments retained in pinned map"
    check_frame(axes)
    # Source section axes preserve rotated timber cross sections. A global
    # Cartesian envelope can triple the apparent area of the inclined rails.
    # These remain geometric axes, not a selected material R/T assignment.
    source_axes = [(f"source_{key}", axes[key]) for key in ("X", "T", "N")]
    u_name, u0 = min(source_axes, key=lambda row: abs(dot(row[1], grain)))
    u = unit([u0[i] - dot(u0, grain)*grain[i] for i in range(3)])
    v = unit(cross(grain, u))
    return identifier, grain, u, v, u_name, scenario_ids, transverse


def bounds(shape):
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def validate_step(shape, row, tolerances):
    solids = shape.Solids()
    if len(solids) != 1 or not solids[0].isValid():
        raise ValueError(f"{row['member_id']}: expected one valid STEP solid")
    solid = solids[0]
    summary = row["step_roundtrip_summary"]
    if abs(solid.Volume()-summary["volume_mm3"]) > tolerances["volume_mm3"]:
        raise ValueError(f"{row['member_id']}: STEP volume differs from bundle")
    if max(abs(a-b) for a, b in zip(bounds(solid), summary["bounds_xyz_mm"], strict=True)) > tolerances["bounds_mm"]:
        raise ValueError(f"{row['member_id']}: STEP bounds differ from bundle")
    return solid


def member_geometry(shape, binding, frame, map_path, map_sha):
    import cadquery as cq
    name, grain, u, v, u_name, scenario_ids, transverse = frame
    candidates = [(u_name, u), ("global_X", [1., 0., 0.]),
                  ("global_Y", [0., 1., 0.]), ("global_Z", [0., 0., 1.])]
    envelopes = []
    for label, candidate in candidates:
        if abs(dot(candidate, grain)) > .99:
            continue
        projected = unit([candidate[i]-dot(candidate, grain)*grain[i] for i in range(3)])
        box = cq.Plane(origin=(0, 0, 0), xDir=projected, normal=grain).toLocalCoords(shape).BoundingBox()
        envelopes.append((box.xlen*box.ylen, label, projected, box))
    _, u_name, u, b = min(envelopes, key=lambda row: row[0])
    v = unit(cross(grain, u))
    width, depth, length = b.xlen, b.ylen, b.zlen
    if min(width, depth, length) <= 0:
        raise ValueError(f"{name}: degenerate oriented bounding box")
    start = [u[i]*(b.xmin+b.xmax)/2 + v[i]*(b.ymin+b.ymax)/2 + grain[i]*b.zmin for i in range(3)]
    end = [start[i]+grain[i]*length for i in range(3)]
    actual, envelope = float(shape.Volume()), float(width*depth*length)
    face_types = Counter(face.geomType() for face in shape.Faces())
    exceptions = []
    if envelope-actual > max(1e-6, envelope*1e-12):
        exceptions.append({"omitted_envelope_volume_mm3": envelope-actual,
                           "actual_to_rectangular_volume_ratio": actual/envelope,
                           "cylindrical_face_count": face_types.get("CYLINDER", 0)})
    return {
        "name": name, "member_id": name, "member_kind": binding["member_kind"],
        "step_path": binding["path"], "step_sha256": binding["file_sha256"],
        "material_frame_map": map_path, "material_frame_map_sha256": map_sha,
        "grain_global_xyz": [round(x, 9) for x in grain],
        "section_u_global_xyz": [round(x, 9) for x in u],
        "section_v_global_xyz": [round(x, 9) for x in v], "section_u_source_axis": u_name,
        "conditional_transverse_scenarios": scenario_ids,
        "transverse_status": transverse + "; section_u is a geometric envelope axis, not a selected R/T assignment",
        "start": [round(x, 9) for x in start], "end": [round(x, 9) for x in end],
        "axis": [round(x, 9) for x in grain], "section_u": [round(x, 9) for x in u],
        "section_v": [round(x, 9) for x in v],
        "width_mm": width, "depth_mm": depth, "length_mm": length,
        "actual_volume_mm3": actual, "rectangular_envelope_volume_mm3": envelope,
        "actual_to_rectangular_volume_ratio": actual/envelope,
        "cylindrical_face_count": face_types.get("CYLINDER", 0),
        "gross_geometry_exceptions": exceptions,
    }


def build():
    adapter, adapter_path, adapter_sha = pinned_json("adapter_pins")
    manifest, manifest_path, manifest_sha = pinned_json("manifest")
    bundle, bundle_path, bundle_sha = pinned_json("bundle")
    timber_map, timber_path, timber_sha = pinned_json("timber_frames")
    block_map, block_path, block_sha = pinned_json("block_frames")
    nested_pin_count = verify_map_pins(timber_map, "timber map") + verify_map_pins(block_map, "block map")
    if any(x.get("candidate") != CANDIDATE or x.get("geometry_revision_id") != REVISION
           for x in (manifest, bundle, timber_map, block_map)):
        raise ValueError("candidate or reviewed revision mismatch")
    adapter_inputs = {r["id"]: r for r in adapter["pinned_inputs"]}
    if adapter_inputs["attempt04_manifest"]["sha256"] != manifest_sha or adapter_inputs["member_bundle_descriptor"]["sha256"] != bundle_sha:
        raise ValueError("adapter source pins disagree with current manifest/bundle")

    bindings = {r["member_id"]: r for r in manifest["finished_member_step_bindings"]}
    bundle_rows = {r["member_id"]: r for r in bundle["members"]}
    timber = {r["member_id"]: r for r in timber_map["members"]}
    blocks = {r["part_id"]: r for r in block_map["members"]}
    kinds = {kind: {key for key, row in bindings.items() if row["member_kind"] == kind}
             for kind in ("timber", "candidate_block", "plywood_panel")}
    if (set(bindings) != set(bundle_rows) or len(bindings) != 50
            or set(timber) != kinds["timber"] or set(blocks) != kinds["candidate_block"]
            or tuple(map(len, (kinds["timber"], kinds["candidate_block"], kinds["plywood_panel"]))) != (20, 24, 6)):
        raise ValueError("50-body identity or 20/24 material-frame coverage mismatch")

    import cadquery as cq
    root = ROOT
    bundle_root = (root / bundle_path).parent.parent
    records, panels, step_hashes = [], [], {}
    for name, binding in sorted(bindings.items()):
        source = bundle_rows[name]
        expected_path = (bundle_root / source["step_file"]).relative_to(root).as_posix()
        if (binding["path"] != expected_path or binding["file_sha256"] != source["step_sha256"]
                or binding["shape_summary_sha256"] != source["shape_summary_sha256"]):
            raise ValueError(f"{name}: manifest and STEP bundle mismatch")
        step = root / binding["path"]
        if digest(step) != binding["file_sha256"] or step.stat().st_size != binding["size_bytes"]:
            raise ValueError(f"{name}: STEP hash/size mismatch")
        step_hashes[binding["path"]] = binding["file_sha256"]
        solid = validate_step(cq.importers.importStep(str(step)).val(), source, bundle["roundtrip_tolerances"])
        if binding["member_kind"] == "plywood_panel":
            box = bounds(solid)
            box_volume = (box[1]-box[0])*(box[3]-box[2])*(box[5]-box[4])
            panels.append({"panel_id": name, "step_path": binding["path"], "step_sha256": binding["file_sha256"],
                           "global_bounds_xyz_mm": box, "exact_volume_mm3": solid.Volume(),
                           "global_aabb_volume_mm3": box_volume, "actual_to_global_aabb_ratio": solid.Volume()/box_volume,
                           "layup_axes_properties": "unassigned", "shell_midsurface": "not generated"})
        else:
            source_map = timber if binding["member_kind"] == "timber" else blocks
            map_path, map_sha = ((timber_path, timber_sha) if binding["member_kind"] == "timber" else (block_path, block_sha))
            record = member_geometry(solid, binding, frame_record(source_map[name], binding["member_kind"]), map_path, map_sha)
            if binding["member_kind"] == "timber":
                expected = sorted(source_map[name]["conditional_grain_assignment"]["actual_source_section_mm"])
                measured = sorted([record["width_mm"], record["depth_mm"]])
                error = max(abs(a-b) for a, b in zip(expected, measured, strict=True))
                record["source_section_check"] = {"source_dimensions_mm": expected,
                                                  "envelope_dimensions_mm": measured,
                                                  "maximum_difference_mm": error,
                                                  "matches_within_0_00001_mm": error < 1e-5}
                if error >= 1e-5:
                    record["gross_geometry_exceptions"].append({"source_section_dimension_mismatch_mm": error})
            records.append(record)

    if len(records) != 44 or len(panels) != 6:
        raise ValueError("expected 44 gross member records and six panel descriptors")
    payload = {
        "schema": "wood_joint_reduced_static_member_geometry/v1", "candidate": CANDIDATE,
        "geometry_revision_id": REVISION, "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "inputs": {"adapter_source_pins": {"path": adapter_path, "sha256": adapter_sha},
                   "manifest": {"path": manifest_path, "sha256": manifest_sha},
                   "step_bundle": {"path": bundle_path, "sha256": bundle_sha},
                   "timber_material_map": {"path": timber_path, "sha256": timber_sha},
                   "block_material_map": {"path": block_path, "sha256": block_sha},
                   "verified_nested_material_map_pins": nested_pin_count,
                   "member_step_file_sha256": dict(sorted(step_hashes.items()))},
        "geometry_method": "Project exact STEP BReps into the pinned conditional grain frame and use each oriented bounding prism as a gross rectangular record.",
        "members": records, "panels": panels,
        "limits": ["Bounding-prism volume ratios identify omitted exact-solid volume; no engineering threshold is applied.",
                   "Every connection point must be checked against its exact STEP solid before meshing; the bounding envelope can extend outside the real body.",
                   "Panel layups/axes/properties, materials, connections, stiffness, mass transfer, loads, supports, mesh and demands remain unassigned."],
        "native_solve_executed": False, "candidate_accepted": False, "readiness": {"geometry_input_only": True, "full_frame_model_ready": False},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    payload["content_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        data = build()
        if args.write:
            with OUT.open("w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
        elif json.loads(OUT.read_text()) != data:
            raise ValueError("member-geometry.json differs from source replay")
        print(json.dumps({"content_sha256": data["content_sha256"], "members": len(data["members"]),
                          "panels": len(data["panels"]), "native_solve_executed": False}, sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"member geometry failed closed: {exc}\n")


if __name__ == "__main__":
    main()

"""Measure nominal concentric retained-washer support on saved receiver STEP solids."""

import argparse
import hashlib
import json
import math
import re
import shutil
from pathlib import Path

import cadquery as cq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = HERE / "retained-washer-attempt01/checks.json"
REGISTER = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json"
)
FEATURES = HERE.parent / "current-finished-feature-register-2026-10-01/axis-features.json"
PROPOSAL = HERE / "top-corner-correction/proposal.json"

PINNED = {
    REPORT: "55ad4689489bc965cde1d182a68c5171723a835180966f2b0e9fed2229faa2e1",
    REGISTER: "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1",
    FEATURES: "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    PROPOSAL: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
}
SIDE_OVERRIDES = {
    "base_side_left": (
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/base_side_left.step",
        "bf1b7398f4c177831d9792f7efcbe07ba8145ab1045bcef1611c2e44b19b3713",
    ),
    "base_side_right": (
        "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/base_side_right.step",
        "6b79617b36f44fc6750b334556779a01191802f8b67b2a3e46c69a6c42bc9601",
    ),
}
DEPTHS_MM = (0.01, 0.05, 0.1)
FACE_TOLERANCE_MM = 1e-5
NORMAL_TOLERANCE = 1e-8
FRACTION_TOLERANCE = 1e-6


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def checked_source_inputs():
    for path, expected in PINNED.items():
        require(path.is_file() and sha(path) == expected, f"pinned source changed: {path}")
    report = read_json(REPORT)
    register = read_json(REGISTER)["axis_register"]
    feature_doc = read_json(FEATURES)
    proposal = read_json(PROPOSAL)
    proposal_steps = proposal["proposal_step_sha256"]
    overrides = {}
    for member, (relative, expected) in SIDE_OVERRIDES.items():
        require(proposal_steps.get(relative) == expected,
                f"top-corner proposal binding changed: {relative}")
        path = ROOT / relative
        require(path.is_file() and sha(path) == expected,
                f"corrected side STEP changed: {relative}")
        overrides[member] = {"path": relative, "sha256": expected}
    features = {
        row["axis_id"]: row
        for row in feature_doc["source_axis_groups"]["retained_frame_bolt_axes"]["axes"]
    }
    require(report["schema"] == "retained_washer_current_dimensional_reference/v1",
            "unexpected dimensional report schema")
    require(len(report["unique_seats"]) == 24 and len(report["states"]) == 144,
            "dimensional report coverage changed")
    require(set(register) == set(features) and len(register) == 12,
            "retained axis feature coverage changed")
    input_pins = report["source_sha256"]
    for path, expected in (
        (REGISTER, PINNED[REGISTER]),
        (FEATURES, PINNED[FEATURES]),
    ):
        require(input_pins.get(str(path.resolve())) == expected,
                f"dimensional report does not bind source: {path}")
    step_paths = set()
    for source, expected in input_pins.items():
        path = Path(source)
        require(path.is_file() and sha(path) == expected,
                f"dimensional report source conflict: {source}")
        if path.suffix.lower() == ".step":
            step_paths.add(path.resolve())
    require(len(step_paths) == 8, "expected eight hash-bound finished receiver STEP files")

    pins = dict(input_pins)
    pins.update({
        str(REPORT.resolve()): sha(REPORT),
        str(REGISTER.resolve()): sha(REGISTER),
        str(FEATURES.resolve()): sha(FEATURES),
        str(PROPOSAL.resolve()): sha(PROPOSAL),
        **{str((ROOT / row["path"]).resolve()): row["sha256"]
           for row in overrides.values()},
        str(Path(__file__).resolve()): sha(Path(__file__).resolve()),
    })
    return report, register, features, overrides, pins


def vector(values, label):
    require(len(values) == 3 and all(math.isfinite(float(x)) for x in values),
            f"invalid vector: {label}")
    return cq.Vector(*(float(x) for x in values))


def import_receiver(receiver, feature_membership, overrides, cache, pins):
    source_binding = receiver["finished_step"]
    feature_binding = feature_membership["current_finished_step_binding"]
    for key in ("path", "file_sha256", "face_count", "shape_summary_sha256",
                "size_bytes", "solid_count", "manifest_roundtrip_valid", "valid"):
        require(source_binding.get(key) == feature_binding.get(key),
                f"receiver STEP feature binding differs: {receiver['member']}/{key}")
    override = overrides.get(receiver["member"])
    relative = Path(override["path"] if override else source_binding["path"])
    require(not relative.is_absolute(), "finished receiver path must be repository relative")
    path = ROOT / relative
    digest = override["sha256"] if override else source_binding["file_sha256"]
    require(path.is_file() and sha(path) == digest,
            f"finished receiver STEP changed: {receiver['member']}")
    pins[str(path.resolve())] = digest
    cache_key = path.resolve()
    if cache_key not in cache:
        imported = cq.importers.importStep(str(path)).val()
        solids = imported.Solids()
        require(len(solids) == 1 and solids[0].isValid(),
                f"invalid or non-single finished solid: {receiver['member']}")
        solid = solids[0]
        if not override:
            require(len(solid.Faces()) == source_binding["face_count"],
                    f"finished STEP face count changed: {receiver['member']}")
        cache[cache_key] = solid
    return cache[cache_key], {
        "path": relative.as_posix(),
        "sha256": digest,
        "face_count": len(cache[cache_key].Faces()),
        "corrected_top_corner_override": bool(override),
    }


def seat_source(axis_id, role, member, register, feature):
    axis_entry = register[axis_id]
    geometry = feature["source_axis_fields"]
    datum = vector(geometry["datum_global_xyz_mm"], f"{axis_id} datum")
    axis = vector(geometry["direction_global_xyz"], f"{axis_id} direction")
    require(abs(axis.Length - 1.0) <= 1e-8, f"nonunit source axis: {axis_id}")
    intervals = []
    memberships = {row["receiver_member_id"]: row for row in feature["receiver_memberships"]}
    for row in axis_entry["finished_receivers"]:
        interval = row["interval_from_axis_datum_mm"]
        require(len(interval) == 2, f"invalid receiver interval: {axis_id}")
        lower, upper = map(float, interval)
        require(math.isfinite(lower) and math.isfinite(upper) and 0 <= lower < upper,
                f"invalid receiver interval: {axis_id}")
        require(row["member"] in memberships,
                f"receiver membership missing: {axis_id}/{row['member']}")
        membership = memberships[row["member"]]
        require(membership["binding_status"] == "bound_to_current_finished_stock_frame"
                and membership["match_status"] == "matched_bore_patch",
                f"receiver feature not bound: {axis_id}/{row['member']}")
        require(len(membership["matched_feature_ids"]) == 1
                and membership["matched_feature_ids"][0] == row["feature_id"],
                f"receiver bore feature differs: {axis_id}/{row['member']}")
        intervals.append((lower, upper, row, membership))
    intervals.sort(key=lambda item: item[0])
    require(len(intervals) == 2, f"expected two exterior receiver intervals: {axis_id}")
    require(intervals[0][1] <= intervals[1][0] + FACE_TOLERANCE_MM,
            f"receiver intervals overlap: {axis_id}")
    selected = intervals[0] if role == "head" else intervals[-1]
    station = selected[0] if role == "head" else selected[1]
    inward = axis if role == "head" else -axis
    require(selected[2]["member"] == member,
            f"reported {role} receiver conflicts with signed interval: {axis_id}")
    point = datum + axis * station
    return {
        "member": member,
        "interval": [selected[0], selected[1]],
        "station": station,
        "datum": datum,
        "axis": axis,
        "point": point,
        "inward": inward,
        "receiver": selected[2],
        "membership": selected[3],
    }


def verify_exterior_face(body, seat, axis_id, role):
    datum, axis, point, inward = (
        seat["datum"], seat["axis"], seat["point"], seat["inward"]
    )
    lower, upper = seat["interval"]
    projections = [(cq.Vector(*vertex.toTuple()) - datum).dot(axis)
                   for vertex in body.Vertices()]
    require(projections and all(math.isfinite(value) for value in projections),
            f"receiver has no finite projected vertices: {axis_id}/{role}")
    projected_lower, projected_upper = min(projections), max(projections)
    # A bore's local receiver interval can omit stock outside a recess at
    # the opposite face. Only the selected exterior face must be the global
    # extreme; the complete local interval must lie inside the stock bounds.
    require(projected_lower <= lower + FACE_TOLERANCE_MM
            and projected_upper >= upper - FACE_TOLERANCE_MM,
            f"source interval lies outside receiver bounds: {axis_id}/{role}")
    exterior_extent = projected_lower if role == "head" else projected_upper
    require(abs(exterior_extent - seat["station"]) <= FACE_TOLERANCE_MM,
            f"washer station is not the exterior receiver bound: {axis_id}/{role}")

    outward = -inward
    faces = []
    for index, face in enumerate(body.Faces()):
        if face.geomType() != "PLANE":
            continue
        plane = face._geomAdaptor().Pln()
        location = cq.Vector(*plane.Location().Coord())
        geometric_normal = cq.Vector(*plane.Axis().Direction().Coord()).normalized()
        offset = abs((point - location).dot(geometric_normal))
        normal = face.normalAt().normalized()
        alignment = normal.dot(outward)
        if offset <= FACE_TOLERANCE_MM and alignment >= 1.0 - NORMAL_TOLERANCE:
            faces.append({"face_index": index, "plane_offset_mm": offset,
                          "outward_normal_alignment": alignment,
                          "face_area_mm2": face.Area()})
    require(faces, f"source station lacks outward exterior planar face: {axis_id}/{role}")
    return {
        "interval_projected_from_axis_datum_mm": [lower, upper],
        "step_projected_vertex_bounds_mm": [projected_lower, projected_upper],
        "face_center_global_xyz_mm": list(point.toTuple()),
        "inward_global_xyz": list(inward.toTuple()),
        "matching_outward_planar_faces": faces,
    }


def measure_depth(body, point, inward, od, ident, depth):
    outer = cq.Solid.makeCylinder(od / 2.0, depth, point, inward)
    inner = cq.Solid.makeCylinder(ident / 2.0, depth, point, inward)
    annulus = outer.cut(inner)
    require(outer.isValid() and inner.isValid() and annulus.isValid(),
            "invalid nominal washer annulus probe")
    nominal_volume = math.pi * (od**2 - ident**2) / 4.0 * depth
    require(abs(annulus.Volume() - nominal_volume) <= max(1e-6, nominal_volume * 1e-8),
            "annulus probe volume differs from nominal dimensions")
    overlap = annulus.intersect(body)
    solids = overlap.Solids()
    require(all(solid.isValid() for solid in solids), "invalid washer/receiver intersection solid")
    supported_volume = float(overlap.Volume())
    supported_area = supported_volume / depth
    fraction = supported_area / (math.pi * (od**2 - ident**2) / 4.0)
    require(math.isfinite(fraction)
            and -FRACTION_TOLERANCE <= fraction <= 1.0 + FRACTION_TOLERANCE,
            "intersection support fraction outside nominal annulus")
    return {
        "probe_depth_mm": depth,
        "intersection_volume_mm3": supported_volume,
        "mean_supported_area_over_probe_depth_mm2": supported_area,
        "nominal_concentric_supported_fraction": fraction,
    }


def build_report(report, register, features, overrides, pins):
    seat_rows = {(row["axis_id"], row["role"]): row for row in report["unique_seats"]}
    require(len(seat_rows) == 24, "duplicate or missing reported washer seats")
    state_rows = {}
    for row in report["states"]:
        key = (row["axis_id"], row["role"])
        state_rows.setdefault(key, []).append(row)
    require(set(state_rows) == set(seat_rows)
            and all(len(rows) == 6 for rows in state_rows.values()),
            "washer force-state mapping changed")

    shapes, seats, step_pins = {}, [], {}
    for seat_id in sorted(seat_rows):
        axis_id, role = seat_id
        dimensional = seat_rows[seat_id]
        feature = features[axis_id]
        require(dimensional["seat_id"] == f"{axis_id}/{role}", "washer seat ID mismatch")
        source = seat_source(axis_id, role, dimensional["member"], register, feature)
        body, support_step = import_receiver(
            source["receiver"], source["membership"], overrides, shapes, pins
        )
        face = verify_exterior_face(body, source, axis_id, role)

        od = float(dimensional["minimum_od_mm"])
        ident = float(dimensional["maximum_id_mm"])
        require(math.isfinite(od) and math.isfinite(ident) and 0 < ident < od,
                f"invalid report-bound washer annulus: {axis_id}/{role}")
        depth_results = [measure_depth(body, source["point"], source["inward"],
                                       od, ident, depth) for depth in DEPTHS_MM]
        source_step = source["receiver"]["finished_step"]
        path = (ROOT / support_step["path"]).resolve()
        step_pins[str(path)] = support_step["sha256"]
        state_outputs = []
        for state in state_rows[seat_id]:
            tie = float(state["simultaneous_signed_tie_n"])
            require(math.isfinite(tie) and tie >= 0,
                    f"invalid simultaneous tie: {axis_id}/{role}/{state['case_id']}")
            pressure = []
            for result in depth_results:
                area = result["mean_supported_area_over_probe_depth_mm2"]
                pressure.append({
                    "probe_depth_mm": result["probe_depth_mm"],
                    "conditional_uniform_pressure_scenario_mpa": tie / area if area > 0 else None,
                })
            state_outputs.append({
                "case_id": state["case_id"],
                "simultaneous_signed_tie_n": tie,
                "conditional_uniform_pressure_scenario_by_depth": pressure,
                "pressure_is_uniform_over_supported_area_scenario_only": True,
                "metal_transfer_or_washer_resistance_assigned": False,
            })
        seats.append({
            "seat_id": dimensional["seat_id"],
            "axis_id": axis_id,
            "role": role,
            "member": dimensional["member"],
            "washer_part": dimensional["washer_part"],
            "nominal_concentric_annulus_mm": {
                "minimum_od": od,
                "maximum_id": ident,
                "area": math.pi * (od**2 - ident**2) / 4.0,
            },
            "source_interval_face_binding": face,
            "datum_reference_step": {
                "path": source_step["path"], "sha256": source_step["file_sha256"]
            },
            "support_geometry_step": support_step,
            "depth_results": depth_results,
            "force_states": state_outputs,
            "delivered_geometry_observed": False,
            "tilted_or_displaced_support_evaluated": False,
        })
    require(len(seats) == 24 and len(step_pins) == 8 and len(shapes) == 8,
            "incomplete saved receiver washer-seat coverage")
    pins.update(step_pins)
    for path, digest in pins.items():
        require(Path(path).is_file() and sha(Path(path)) == digest,
                f"source changed during geometry calculation: {path}")

    return {
        "schema": "retained_washer_saved_step_support/v1",
        "status": "NOMINAL_SAVED_GEOMETRY_ONLY",
        "source_sha256": pins,
        "producer_sha256": {
            "retained_washer_support.py": sha(Path(__file__).resolve()),
        },
        "producer_snapshots": {
            "retained_washer_support.py.snapshot": sha(Path(__file__).resolve()),
        },
        "counts": {"axes": 12, "seats": len(seats), "finished_step_solids": len(shapes),
                   "force_states": sum(len(row["force_states"]) for row in seats)},
        "method": {
            "depths_mm": DEPTHS_MM,
            "face_station": "source datum plus axis times earliest receiver lower or latest receiver upper interval endpoint",
            "face_gate": "local bore interval inside signed STEP vertex bounds; selected exterior bound and outward planar face at source station",
            "supported_area": "washer-annulus intersection volume divided by inward probe depth; depth-averaged over probe",
            "placement": "nominal concentric with source bolt axis",
            "pressure": "tie divided by depth-averaged supported area; uniform-pressure scenario only",
        },
        "seats": seats,
        "claim_limits": {
            "saved_step_geometry_only": True,
            "delivered_observation": False,
            "actual_inspection": False,
            "displaced_or_tilted_support": False,
            "wood_bearing_acceptance": False,
            "washer_metal_transfer_or_resistance": False,
            "complete_joint_acceptance": False,
            "geometry_changed": False,
            "physical_release": False,
        },
    }


def main(output):
    output = output.resolve()
    require(output.parent == HERE and re.fullmatch(r"retained-washer-support-attempt\d{2}", output.name),
            "output must be a fresh retained-washer-support-attemptNN directory here")
    require(not output.exists(), "support output directory already exists")
    report, register, features, overrides, pins = checked_source_inputs()
    result = build_report(report, register, features, overrides, pins)

    output.mkdir()
    (output / ".gitignore").write_text("*\n", encoding="utf-8")
    snapshots = {
        "retained_washer_support.py.snapshot": Path(__file__).resolve(),
    }
    for name, source in snapshots.items():
        shutil.copyfile(source, output / name)
    result_path = output / "support.json"
    result_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({"output": str(result_path), "sha256": sha(result_path),
                      "seats": len(result["seats"]), "source_pins": len(result["source_sha256"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args().output)

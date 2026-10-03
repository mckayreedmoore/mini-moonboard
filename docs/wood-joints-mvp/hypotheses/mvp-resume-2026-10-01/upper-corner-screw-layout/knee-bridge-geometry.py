"""Export the frozen, unadopted four-bolt knee bridge when the parent calls run.

Importing this module performs no CAD, geometry arithmetic, or file writes.
Only the two pinned original spine STEP files are imported. The parent owns
serialized execution, mass/BOM reconciliation, and subsequent integration.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import platform
import sys
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-geometry"
PROPOSAL = HERE / "rawlocal/knee-spine-reinforcement/attempt01/checks.json"
PROPOSAL_RECEIPT = PROPOSAL.with_name("receipt.json")
ORIGINAL = HERE / "rawlocal/knee-spine-net-sections/attempt02/checks.json"
HELPER = HERE / "longitudinal-bore-geometry.py"
STEP_DIR = (
    HERE.parent.parent
    / "evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members"
)
BLOCKS = ("knee_outer_left_spine", "knee_outer_right_spine")
PINS = {
    PROPOSAL: "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778",
    PROPOSAL_RECEIPT: "991f6742f6aae386552338b1fea79f02766bd0def09bfa8fabea27560ba13819",
    ORIGINAL: "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
    HELPER: "faab8b5e5ff13dc4252329ed2f8917d9e2054f05e823a4e5fdbeb11da46accc4",
}
CAD_VERSIONS = {"cadquery": "2.8.0", "cadquery-ocp": "7.9.3.1.1"}
# Fixed numerical comparisons and tessellation settings; no retry or tuning.
COORD_TOL_MM = 1e-6
VOLUME_TOL_MM3 = 0.001
STL_SETTINGS = {"tolerance": 0.1, "angularTolerance": 0.1, "opt": {"ascii": False}}
FLAGS = {
    "proposal_adopted": False,
    "current_geometry_changed": False,
    "current_axes_changed": False,
    "viewer_changed": False,
    "authority_changed": False,
    "full_scene_rebuilt": False,
    "frame_or_native_run": False,
    "loads_or_stiffness_changed": False,
    "physics_recomputed": False,
    "gravity_delta_in_global_model": False,
    "mass_or_BOM_reconciled": False,
    "delivered_hardware_fit_established": False,
    "hardware_capacity_qualified": False,
    "installation_preload_credited": False,
    "local_compatibility_solved": False,
    "complete_joint_acceptance": False,
    "fabrication_authorized": False,
    "physical_release": False,
    "software_tests_or_agent_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return Path(path).relative_to(ROOT).as_posix()


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"STOP: frozen input changed: {path}")


def world_point(geometry, local):
    rows = geometry["grain_frame_rows_xyz"]
    return [
        geometry["start_xyz_mm"][j]
        + math.fsum(local[i] * rows[i][j] for i in range(3))
        for j in range(3)
    ]


def analytic_properties(helper, geometry):
    """Reuse the pinned disjoint-cylinder helper, without its coupon or main."""
    simple = {
        "grain_length_mm": geometry["grain_length_mm"],
        "width_depth_mm": geometry["width_depth_mm"],
        "bores": [
            {k: bore[k] for k in (
                "axis_id", "radius_mm", "station_mm",
                "transverse_center_mm", "removed_interval_axis",
            )}
            for bore in geometry["bores"]
        ],
    }
    length = simple["grain_length_mm"]
    width, depth = simple["width_depth_mm"]
    volume, first = helper.volume_first(simple, 0, length)
    corners = [
        world_point(geometry, point)
        for point in product((0.0, length), (-width / 2, width / 2), (-depth / 2, depth / 2))
    ]
    return {
        "volume_mm3": volume,
        "centroid_xyz_mm": world_point(geometry, [v / volume for v in first]),
        "bounds_xyz_mm": [[min(p[j] for p in corners), max(p[j] for p in corners)] for j in range(3)],
    }


def one_solid(shape, label):
    require(shape.isValid(), f"STOP: {label}: invalid CAD shape")
    solids = shape.Solids()
    require(len(solids) == 1, f"STOP: {label}: expected exactly one solid")
    require(solids[0].isValid(), f"STOP: {label}: invalid CAD solid")
    return solids[0]


def inspect(shape, expected, label):
    bounds = shape.BoundingBox()
    observed = {
        "volume_mm3": float(shape.Volume()),
        "centroid_xyz_mm": list(shape.Center().toTuple()),
        "bounds_xyz_mm": [[bounds.xmin, bounds.xmax], [bounds.ymin, bounds.ymax], [bounds.zmin, bounds.zmax]],
    }
    errors = {
        "volume_error_mm3": abs(observed["volume_mm3"] - expected["volume_mm3"]),
        "centroid_max_error_mm": max(abs(a - b) for a, b in zip(observed["centroid_xyz_mm"], expected["centroid_xyz_mm"])),
        "bounds_max_error_mm": max(abs(a - b) for actual, wanted in zip(observed["bounds_xyz_mm"], expected["bounds_xyz_mm"]) for a, b in zip(actual, wanted)),
    }
    require(
        all(math.isfinite(v) for v in [observed["volume_mm3"], *observed["centroid_xyz_mm"], *(v for pair in observed["bounds_xyz_mm"] for v in pair)]),
        f"STOP: {label}: nonfinite CAD properties",
    )
    require(observed["volume_mm3"] > 0, f"STOP: {label}: nonpositive CAD volume")
    require(errors["volume_error_mm3"] <= VOLUME_TOL_MM3, f"STOP: {label}: analytic volume mismatch")
    require(errors["centroid_max_error_mm"] <= COORD_TOL_MM, f"STOP: {label}: analytic centroid mismatch")
    require(errors["bounds_max_error_mm"] <= COORD_TOL_MM, f"STOP: {label}: stock bounds mismatch")
    return {"valid": True, "solid_count": 1, "observed": observed, "analytic": expected, **errors}


def run(output):
    """Create one fresh proposal packet; only the parent executes this API."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), f"STOP: fresh immediate child of {RAW} required")
    require(RAW.resolve() == RAW, "STOP: output root must not redirect through a symlink")
    pins = dict(PINS)
    producer = Path(__file__).resolve()
    producer_bytes = producer.read_bytes()
    pins[producer] = hashlib.sha256(producer_bytes).hexdigest()
    authenticate(pins)
    proposal, receipt, original = [json.loads(path.read_text()) for path in (PROPOSAL, PROPOSAL_RECEIPT, ORIGINAL)]
    require(receipt["output_sha256"]["checks.json"] == pins[PROPOSAL], "STOP: proposal receipt binding differs")
    require(not proposal["proposal_adopted"] and not proposal["current_geometry_changed"], "STOP: expected unadopted proposal")
    require(set(proposal["geometry_proposals"]) == set(original["geometry"]) == set(BLOCKS), "STOP: two-spine coverage differs")
    require(proposal["source_sha256"][key(ORIGINAL)] == receipt["source_sha256"][key(ORIGINAL)] == pins[ORIGINAL], "STOP: original geometry binding differs")
    require(proposal["source_sha256"][key(HELPER)] == receipt["source_sha256"][key(HELPER)] == pins[HELPER], "STOP: geometry helper binding differs")

    inputs = {}
    axes = []
    for body in BLOCKS:
        old = original["geometry"][body]
        record = proposal["geometry_proposals"][body]
        new = record["hypothetical_geometry"]
        expected_axes = [
            {"axis_id": f"{body}/proposed_v_bridge_{i}", "radius_mm": 3.75,
             "removed_interval_axis": 1, "station_mm": station, "transverse_center_mm": 0.0}
            for i, station in enumerate((100.0, 250.0), 1)
        ]
        require(record["new_axes"] == expected_axes, f"STOP: {body}: frozen new axes differ")
        require(len(old["bores"]) == 4 and all(b["removed_interval_axis"] == 2 and b["radius_mm"] == 3.75 for b in old["bores"]), f"STOP: {body}: four original u-bores required")
        require(new["bores"] == old["bores"] + expected_axes, f"STOP: {body}: original bores not preserved")
        for field in ("block", "grain_frame_rows_xyz", "grain_length_mm", "start_xyz_mm", "width_depth_mm"):
            require(new[field] == old[field], f"STOP: {body}: stock or placement changed: {field}")
        require(new["grain_frame_rows_xyz"] == [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], f"STOP: {body}: unsupported grain frame")
        require(abs(new["grain_length_mm"] - 276.3) <= COORD_TOL_MM and all(abs(a - b) <= COORD_TOL_MM for a, b in zip(new["width_depth_mm"], (38.1, 139.7))), f"STOP: {body}: stock dimensions differ")
        binding = old["finished_step_binding"]
        step = ROOT / binding["path"]
        require(step == STEP_DIR / (body + ".step"), f"STOP: {body}: original STEP path differs")
        require(binding["valid"] and binding["solid_count"] == 1 and step.stat().st_size == binding["size_bytes"], f"STOP: {body}: delivered STEP binding differs")
        pins[step] = binding["file_sha256"]
        require(all(d["source_sha256"][key(step)] == pins[step] for d in (proposal, receipt, original)), f"STOP: {body}: conflicting STEP pins")
        inputs[body] = {"original_geometry": old, "proposal_geometry": new, "new_axes": expected_axes, "washer_lands": record["washer_lands"]}
        depth = new["width_depth_mm"][1]
        for bore in expected_axes:
            seats = []
            for sign in (-1, 1):
                local = [bore["station_mm"], 0.0, sign * depth / 2]
                center = world_point(new, local)
                lands = [land for land in record["washer_lands"] if land["axis_id"] == bore["axis_id"] and land["end_v_sign"] == sign]
                require(len(lands) == 1 and all(abs(a - b) <= COORD_TOL_MM for a, b in zip(center, lands[0]["seat_center_xyz_mm"])), f"STOP: {bore['axis_id']}: end-seat binding differs")
                seats.append({"end_v_sign": sign, "center_local_guv_mm": local, "center_xyz_mm": center,
                              "outward_unit_xyz": [sign * v for v in new["grain_frame_rows_xyz"][2]]})
            axes.append({
                "axis_id": bore["axis_id"], "body": body, "proposal_only": True,
                "axis_origin_global_xyz_mm": seats[0]["center_xyz_mm"],
                "axis_unit_global_xyz": new["grain_frame_rows_xyz"][2],
                "axis_parameter_interval_mm": [0.0, depth],
                "center_local_guv_mm": [bore["station_mm"], 0.0, 0.0],
                "center_global_xyz_mm": world_point(new, [bore["station_mm"], 0.0, 0.0]),
                "bore_envelope_diameter_mm": 7.5, "end_seats": seats,
                "nominal_shaft_record": {"diameter_mm": 6.35, "wood_span_mm": depth,
                                         "geometry_exported": False, "delivered_profile_verified": False},
            })
    authenticate(pins)
    versions = {name: importlib.metadata.version(name) for name in CAD_VERSIONS}
    require(versions == CAD_VERSIONS, f"STOP: pinned CAD versions differ: {versions}")

    RAW.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(producer_bytes)
    (output / "geometry-helper.py.snapshot").write_bytes(HELPER.read_bytes())
    dump(output / "inputs.json", {"source_sha256": {key(p): v for p, v in pins.items()}, "bodies": inputs, **FLAGS})
    stage = "import pinned CAD and geometry definitions"
    try:
        sys.dont_write_bytecode = True
        import cadquery as cq

        spec = importlib.util.spec_from_file_location("knee_bridge_geometry_helper", HELPER)
        require(spec is not None and spec.loader is not None, "STOP: geometry helper unavailable")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        require(helper.GEOMETRY_TOL_MM == COORD_TOL_MM and helper.VOLUME_TOL_MM3 == VOLUME_TOL_MM3, "STOP: geometry comparison tolerances differ")
        bodies = {}
        for body in BLOCKS:
            stage = body + ": import original STEP"
            old, new = inputs[body]["original_geometry"], inputs[body]["proposal_geometry"]
            values = cq.importers.importStep(str(ROOT / old["finished_step_binding"]["path"])).vals()
            require(len(values) == 1, f"STOP: {body}: expected one imported object")
            source = one_solid(values[0], body + " original")
            source_check = inspect(source, analytic_properties(helper, old), body + " original")
            proposed = source
            body_axes = [axis for axis in axes if axis["body"] == body]
            for axis in body_axes:
                stage = axis["axis_id"] + ": cut full v-cylinder"
                cylinder = cq.Solid.makeCylinder(
                    axis["bore_envelope_diameter_mm"] / 2,
                    axis["axis_parameter_interval_mm"][1],
                    pnt=tuple(axis["axis_origin_global_xyz_mm"]),
                    dir=tuple(axis["axis_unit_global_xyz"]),
                )
                proposed = one_solid(proposed.cut(cylinder), axis["axis_id"])
            proposed_check = inspect(proposed, analytic_properties(helper, new), body + " proposal")
            removed_expected = math.fsum(math.pi * (axis["bore_envelope_diameter_mm"] / 2) ** 2 * axis["axis_parameter_interval_mm"][1] for axis in body_axes)
            removed_observed = source_check["observed"]["volume_mm3"] - proposed_check["observed"]["volume_mm3"]
            require(abs(removed_observed - removed_expected) <= VOLUME_TOL_MM3, f"STOP: {body}: exact cylinder removal mismatch")
            bounds_error = max(abs(a - b) for before, after in zip(source_check["observed"]["bounds_xyz_mm"], proposed_check["observed"]["bounds_xyz_mm"]) for a, b in zip(before, after))
            require(bounds_error <= COORD_TOL_MM, f"STOP: {body}: source bounds changed")
            stage = body + ": export proposal STEP and STL"
            step_name, stl_name = body + ".proposal.step", body + ".proposal.stl"
            cq.exporters.export(proposed, str(output / step_name), exportType="STEP", unit="MM")
            cq.exporters.export(proposed, str(output / stl_name), exportType="STL", **STL_SETTINGS)
            for name in (step_name, stl_name):
                require((output / name).is_file() and (output / name).stat().st_size > 0, f"STOP: missing or empty export: {name}")
            bodies[body] = {
                "source_step_binding": old["finished_step_binding"],
                "source": source_check, "proposal": proposed_check,
                "preserved_u_bore_count": 4, "added_v_bore_count": 2,
                "removed_volume_mm3": removed_observed, "analytic_removed_volume_mm3": removed_expected,
                "removed_volume_error_mm3": abs(removed_observed - removed_expected),
                "source_bounds_max_change_mm": bounds_error,
                "exports": {name: {"sha256": sha(output / name), "size_bytes": (output / name).stat().st_size} for name in (step_name, stl_name)},
            }
        stage = "authenticate sources and proposal deliveries after export"
        authenticate(pins)
        require(sha(output / "producer.py.snapshot") == pins[producer] and sha(output / "geometry-helper.py.snapshot") == pins[HELPER], "STOP: definition snapshot differs")
        manifest = {
            "schema": "knee-bridge-proposal-geometry/v1", "status": "PROPOSAL_GEOMETRY_EXPORTED",
            "producer_sha256": pins[producer], "source_sha256": {key(p): v for p, v in pins.items()},
            "source_authentication_before_after": True, "CAD_run_executed": True,
            "cad_versions": versions, "python_version": platform.python_version(), "units": "mm",
            "comparison_tolerances": {"coordinate_mm": COORD_TOL_MM, "volume_mm3": VOLUME_TOL_MM3},
            "STL_settings": STL_SETTINGS, "export_roundtrip_checked": False,
            "bodies": bodies, "added_stock_bolt_axes": axes,
            "current_authority_counts": proposal["current_authority_counts"],
            "hypothetical_counts_if_later_adopted": proposal["hypothetical_counts_if_later_adopted"],
            "scope": "Two modified proposal timber solids and four axis/end-seat records. Bore envelopes are not drill instructions. Parent owns mass/BOM reconciliation and global integration; no prior physics is rerun or adopted.",
            **FLAGS,
        }
        dump(output / "manifest.json", manifest)
        files = [".gitignore", "producer.py.snapshot", "geometry-helper.py.snapshot", "inputs.json", "manifest.json", *[name for body in bodies.values() for name in body["exports"]]]
        output_pins = {name: sha(output / name) for name in files}
        for body in bodies.values():
            for name, delivery in body["exports"].items():
                require(output_pins[name] == delivery["sha256"], f"STOP: proposal delivery changed: {name}")
        dump(output / "receipt.json", {
            "schema": "knee-bridge-proposal-geometry-receipt/v1", "status": manifest["status"],
            "source_sha256": manifest["source_sha256"], "output_sha256": output_pins,
            "source_authentication_before_after": True, "CAD_run_executed": True,
            "cad_versions": versions, "python_version": platform.python_version(), **FLAGS,
        })
        authenticate(pins)
        for name, expected in output_pins.items():
            require(sha(output / name) == expected, f"STOP: receipt-bound output changed: {name}")
        return manifest
    except Exception as error:
        dump(output / "STOP.json", {"status": "STOP", "stage": stage, "error": str(error), **FLAGS})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.output)
    print(json.dumps({"status": result["status"], "output": str(args.output.resolve()), "receipt_sha256": sha(args.output / "receipt.json"), **FLAGS}, sort_keys=True))

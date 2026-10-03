"""Run only the 120 saved effective-STEP washer land probes; parent execution.

Import is inert. ``build(output)`` authenticates the completed query plan and
starts one CadQuery child with a fixed 120-second timeout. It imports each of
the four STEP solids once and reuses the existing annular slab support method.
No scene, frame, mechanics, native solve, test or review is run.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-land-completion"
SOURCE = HERE / "rawlocal/washer-end-source-completion/attempt02"
SOURCE_RECEIPT_SHA = "d974544f39a670bde1d9a493754224b199fe10f5126fc266f9914101d5fcbe00"
PLAN_SHA = "a5bf7a49515766ed02b46af817e1795ef18e8ab259acdde83dee5185d5cd9c92"
SOURCE_PRODUCER_SHA = "dbf242d54ae501c0bf8d4241447837dcf08e7e4d2d108703f43a2fc0e1c078c9"
METHOD = ROOT / "docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01/check_support.py"
METHOD_PINS = {
    METHOD: "9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57",
    ROOT / "mini_moonboard/wood_joint_geometry.py": "e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e",
    ROOT / "mini_moonboard/wood_joint_frame.py": "77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545",
    ROOT / "mini_moonboard/connection_geometry.py": "f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4",
    ROOT / "uv.lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
    ROOT / "pyproject.toml": "84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452",
}
UPPER_SUPPORT_SHA = "4463f581490842095224afefd0b355428f82668f039b2e6035dfe4ec879c96c1"
REMAINING_SUPPORT_SHA = "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3"
TIMEOUT_SECONDS = 120
FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
         "physical_release": False, "fabrication_release": False,
         "physical_geometry_inspected": False, "loaded_shift_or_tilt_qualified": False,
         "actual_washer_capacity_n": None, "actual_washer_stress_mpa": None}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, document):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n")


def display(path):
    try:
        return Path(path).relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source bytes changed: " + str(path))


def add_pin(pins, path, digest):
    path = Path(path).resolve()
    require(path not in pins or pins[path] == digest, "conflicting source digest: " + str(path))
    pins[path] = digest


def input_plan():
    pins = {**METHOD_PINS, Path(__file__).resolve(): sha(__file__)}
    add_pin(pins, SOURCE / "receipt.json", SOURCE_RECEIPT_SHA)
    authenticate(pins)
    receipt = read(SOURCE / "receipt.json")
    require(receipt["schema"] == "washer_end_source_completion_receipt/v1"
            and receipt["sources_authenticated_before_and_after"] is True
            and receipt["complete_joint_acceptance"] is False and receipt["physical_release"] is False
            and receipt["output_sha256"]["land-query-plan.json"] == PLAN_SHA
            and receipt["output_sha256"]["producer.py.snapshot"] == SOURCE_PRODUCER_SHA,
            "completed source query plan or claim boundary differs")
    for name, digest in receipt["output_sha256"].items():
        require(Path(name).name == name and not (SOURCE / name).is_symlink(),
                "source artifact is not a plain file in its frozen packet")
        add_pin(pins, SOURCE / name, digest)
    for name, digest in receipt["source_sha256"].items():
        add_pin(pins, ROOT / name, digest)
    authenticate(pins)
    plan = read(SOURCE / "land-query-plan.json")
    counts = plan["counts"]
    require(plan["schema"] == "washer_land_query_plan/v1" and plan["geometry_queries_run"] == 0
            and counts["new_physical_land_queries"] == 20
            and counts["new_annulus_intersection_requests"] == 120
            and len(plan["known_partial_land"]) == 1 and len(plan["reused_corrected_retail_lands"]) == 4,
            "saved 20/120 plus one-known/four-reused partition differs")
    requests = plan["new_land_queries"]
    require(len(requests) == len({tuple(row["physical_land_key"]) for row in requests}) == 20,
            "duplicate or missing physical land requests")
    steps = {}
    for row in requests:
        require(row["disposition"] == "PARENT_CURRENT_STEP_ANNULUS_QUERY_REQUIRED"
                and row["annulus_inner_outer_radii_mm"] == [4.1529, 9.2329]
                and row["depths_mm"] == [0.01, 0.05, 0.1]
                and {(p["direction"], p["offset_from_seat_mm"]) for p in row["intersection_requests"]}
                    == {(direction, sign * depth) for direction, sign in (("inward", 1), ("outward", -1))
                        for depth in row["depths_mm"]}
                and len(row["intersection_requests"]) == 6,
                "query annulus, depths or signed direction differs")
        binding = row["effective_step"]
        member = row["physical_land_key"][2]
        require(member not in steps or steps[member] == binding, "one member has two effective STEP bindings")
        steps[member] = binding
        require(pins.get((ROOT / binding["path"]).resolve()) == binding["sha256"],
                "effective STEP is not authenticated by source receipt")
        require(row["original_support_source_sha256"] in {UPPER_SUPPORT_SHA, REMAINING_SUPPORT_SHA},
                "fresh request lacks its original support tolerance source")
    require(set(steps) == {"base_side_left", "base_side_right", "top_outer_left_cleat", "top_outer_right_cleat"},
            "four cached effective members differ")
    return plan, pins


def load_method():
    require(sha(METHOD) == METHOD_PINS[METHOD], "support method changed before child import")
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("washer_land_saved_method", METHOD)
    require(spec is not None and spec.loader is not None, "saved method loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.cq.__version__ == "2.8.0" and module.OCP.__version__ == "7.9.3.1"
            and tuple(module.DEPTHS_MM) == (0.01, 0.05, 0.1)
            and module.PLANE_TOLERANCE_MM == 1e-5 and module.NORMAL_TOLERANCE == 1e-8,
            "saved CadQuery/OCP runtime or datum tolerance differs")
    return module


def worker(input_path, output_path):
    """Internal parent-launched child; import/cache/probes share the hard timeout."""
    started = time.monotonic()
    plan = read(input_path)
    helper = load_method()
    cache, body_readbacks, probes, seats = {}, [], [], []
    progress = output_path.with_name("probe-progress.jsonl")
    with progress.open("x") as stream:
        for request in plan["new_land_queries"]:
            key = request["physical_land_key"]
            member, binding = key[2], request["effective_step"]
            if member not in cache:
                step = ROOT / binding["path"]
                require(sha(step) == binding["sha256"], "STEP changed before cached import")
                imported = helper.cq.importers.importStep(str(step))
                require(len(imported.vals()) == 1, "STEP has multiple top-level shapes: " + member)
                body = imported.val()
                require(body.isValid() and len(body.Solids()) == 1 and body.Volume() > 0,
                        "STEP does not contain one valid positive-volume solid: " + member)
                cache[member] = body
                box = body.BoundingBox()
                body_readbacks.append({"member": member, "effective_step": binding,
                                       "valid": True, "solid_count": 1,
                                       "volume_mm3": body.Volume(), "surface_area_mm2": body.Area(),
                                       "face_count": len(body.Faces()),
                                       "bounds_xyz_mm": [box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax]})
            body = cache[member]
            point = helper.cq.Vector(*request["current_nominal_seat_point_xyz_mm"])
            normal = helper.cq.Vector(*request["current_inward_normal_xyz"])
            require(math.isclose(normal.Length, 1, rel_tol=0, abs_tol=1e-8), "query normal is not unit length")
            try:
                planes = helper.matching_seat_planes(body, point, normal)
                datum_error = None
            except ValueError as error:
                planes, datum_error = [], str(error)
            inner, outer = request["annulus_inner_outer_radii_mm"]
            area = math.pi * (outer ** 2 - inner ** 2)
            hardware = helper.hardware_for(2 * outer, 2 * inner)
            tolerance = 1e-8 if request["original_support_source_sha256"] == UPPER_SUPPORT_SHA else 1e-7
            own_probes = []
            for proposed in request["intersection_requests"]:
                sign = 1 if proposed["direction"] == "inward" else -1
                depth = abs(proposed["offset_from_seat_mm"])
                row = {"physical_land_key": key, "effective_step": binding,
                       "direction": proposed["direction"], "signed_probe_extent_mm": sign * depth,
                       "nominal_seat_point_xyz_mm": request["current_nominal_seat_point_xyz_mm"],
                       "annulus_inner_outer_radii_mm": [inner, outer], "analytic_annulus_area_mm2": area,
                       "probe_geometry": "annular slab from nominal seat to signed extent",
                       "inward_supported_mean_area_mm2": None, "outward_overlap_mean_area_mm2": None,
                       "derived_overlap_volume_mm3": None,
                       "support_or_overlap_fraction": None, "error": None, "status": "NULL_QUERY_ERROR"}
                try:
                    seat = helper.WasherSeat(member, point, normal.multiply(sign))
                    report = helper.washer_support_report(seat, body, hardware, probe_depth_mm=depth)
                    fraction = float(report.support_fraction)
                    require(math.isfinite(fraction) and -tolerance <= fraction <= 1 + tolerance,
                            "annular probe returned nonfinite or out-of-range fraction")
                    row.update({"status": "FINITE_SAVED_ANNULAR_PROBE",
                                "support_or_overlap_fraction": fraction,
                                "inward_supported_mean_area_mm2": area * fraction if sign == 1 else None,
                                "outward_overlap_mean_area_mm2": area * fraction if sign == -1 else None,
                                "derived_overlap_volume_mm3": area * fraction * depth,
                                "unsupported_mean_area_mm2": float(report.unsupported_area_mm2) if sign == 1 else None})
                except (ValueError, TypeError, RuntimeError, ArithmeticError) as error:
                    row["error"] = type(error).__name__ + ": " + str(error)
                probes.append(row)
                own_probes.append(row)
                stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
                stream.flush()
            valid = all(row["status"] == "FINITE_SAVED_ANNULAR_PROBE" for row in own_probes)
            inward = [row["support_or_overlap_fraction"] for row in own_probes if row["direction"] == "inward"]
            outward = [row["support_or_overlap_fraction"] for row in own_probes if row["direction"] == "outward"]
            full = valid and min(inward) >= 1 - tolerance
            clear = valid and max(outward) <= tolerance
            supported = bool(planes) and full and clear
            seats.append({"physical_land_key": key,
                          "status": "FULL_NOMINAL_CONCENTRIC_ANNULUS_SUPPORTED" if supported
                              else "NOMINAL_LAND_UNRESOLVED_OR_INCOMPATIBLE",
                          "effective_step": binding,
                          "current_nominal_datum_binding": request["current_nominal_datum_binding"],
                          "point_xyz_mm": request["current_nominal_seat_point_xyz_mm"],
                          "inward_normal_xyz": request["current_inward_normal_xyz"],
                          "matching_planar_faces": planes, "datum_error": datum_error,
                          "all_six_probes_numeric": valid, "minimum_inward_support_fraction": min(inward) if valid else None,
                          "maximum_outward_overlap_fraction": max(outward) if valid else None,
                          "inward_full": full, "outward_clear": clear,
                          "support_fraction_tolerance": tolerance,
                          "nominal_annulus_support_established": supported, **FLAGS})
    write(output_path, {"schema": "washer_land_geometry_worker/v1", "seats": seats,
                        "probe_records": len(probes), "STEP_imports": len(cache),
                        "finite_probe_records": sum(row["status"] == "FINITE_SAVED_ANNULAR_PROBE" for row in probes),
                        "body_readbacks": body_readbacks, "elapsed_seconds": time.monotonic() - started,
                        "runtime": {"python": sys.version, "cadquery": helper.cq.__version__, "ocp": helper.OCP.__version__},
                        **FLAGS})


def build(output):
    """Parent-owned 120-second child geometry run; retains partial/failed output."""
    output = Path(output).absolute()
    require(output.resolve() == output and output.parent == RAW and not output.exists(),
            "use a fresh unaliased immediate child of rawlocal/washer-land-completion")
    plan, pins = input_plan()
    authenticate(pins)
    before = {display(path): digest for path, digest in sorted(pins.items())}
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "worker-input.json", plan)
    child_result = output / "worker-result.json"
    command = [str(ROOT / ".venv/bin/python"), "-B", str(Path(__file__).resolve()),
               "--worker-input", str(output / "worker-input.json"), "--worker-output", str(child_result)]
    timed_out, returncode, failure = False, None, None
    started = time.monotonic()
    with (output / "worker.stdout.log").open("x") as stdout, (output / "worker.stderr.log").open("x") as stderr:
        try:
            process = subprocess.run(command, cwd=ROOT, timeout=TIMEOUT_SECONDS, check=False,
                                     stdout=stdout, stderr=stderr,
                                     env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            timed_out, failure = True, "Geometry child exceeded its fixed 120-second timeout and was terminated."
        except OSError as error:
            failure = str(error)
    elapsed = time.monotonic() - started
    geometry = None
    if child_result.exists():
        try:
            geometry = read(child_result)
        except json.JSONDecodeError as error:
            failure = "Incomplete child result retained: " + str(error)
    progress = output / "probe-progress.jsonl"
    completed, progress_errors = [], []
    if progress.exists():
        for index, line in enumerate(progress.read_text().splitlines()):
            try:
                completed.append(json.loads(line))
            except json.JSONDecodeError as error:
                progress_errors.append({"line_index": index, "error": str(error)})
    all_finite = (geometry is not None and returncode == 0 and not timed_out
                  and not progress_errors
                  and len(completed) == geometry["probe_records"] == geometry["finite_probe_records"] == 120
                  and len(geometry["seats"]) == 20 and geometry["STEP_imports"] == 4)
    full_seats = sum(row["nominal_annulus_support_established"] for row in geometry["seats"]) if geometry else 0
    if all_finite:
        status = "COMPLETE_120_NOMINAL_LAND_PROBES" if full_seats == 20 else "COMPLETE_120_PROBES_WITH_OPEN_NOMINAL_LANDS"
    else:
        status = "STOP_GEOMETRY_TIMEOUT" if timed_out else "PARTIAL_OR_STOPPED_NOMINAL_LAND_PROBES"
    try:
        authenticate(pins)
        after = {display(path): sha(path) for path in sorted(pins)}
        unchanged = before == after
    except ValueError as error:
        after = {display(path): sha(path) for path in sorted(pins) if path.exists()}
        unchanged, status, failure = False, "STOP_SOURCE_BYTES_CHANGED", str(error)
    result = {"schema": "washer_land_completion/v1", "status": status,
              "source_query_receipt_sha256": SOURCE_RECEIPT_SHA, "source_query_plan_sha256": PLAN_SHA,
              "counts": {"required_physical_lands": 20, "required_probes": 120,
                         "returned_probe_records": len(completed),
                         "finite_probe_records": sum(row["status"] == "FINITE_SAVED_ANNULAR_PROBE" for row in completed),
                         "full_current_nominal_lands": full_seats if unchanged and all_finite else None,
                         "known_central_partial_land_reused": 1, "corrected_retail_current_lands_reused": 4},
              "known_partial_land": plan["known_partial_land"],
              "reused_corrected_retail_lands": plan["reused_corrected_retail_lands"],
              "geometry": geometry, "child_command": command, "child_exit_code": returncode,
              "child_timeout_seconds": TIMEOUT_SECONDS, "child_timed_out": timed_out,
              "child_elapsed_seconds": elapsed, "failure": failure,
              "progress_read_errors": progress_errors,
              "source_before_sha256": before, "source_after_sha256": after,
              "sources_authenticated_before_and_after": unchanged,
              "original_aggregate_applicability_rewritten": False,
              "limits": ["Annular slab mean area is not a zero-thickness section, a loaded contact mask or washer stress.",
                         "Only the 20 current nominal seats are queried; central failure and four retail lands are reused.",
                         "Inward support and outward overlap are separate observations; outward wood receives no support credit.",
                         "No frame, scene, mechanical law, bolt/washer capacity or release flag is changed."], **FLAGS}
    write(output / "washer-land-completion.json", result)
    outputs = {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()}
    write(output / "receipt.json", {"schema": "washer_land_completion_receipt/v1", "status": status,
                                    "source_sha256": before, "source_before_sha256": before,
                                    "source_after_sha256": after,
                                    "sources_authenticated_before_and_after": unchanged,
                                    "output_sha256": outputs, "counts": result["counts"], **FLAGS})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-input", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_input is not None:
        require(args.worker_output is not None and args.output is None, "internal child arguments differ")
        worker(args.worker_input, args.worker_output)
    else:
        require(args.output is not None and args.worker_output is None, "provide one fresh --output path")
        result = build(args.output)
        print(json.dumps({"status": result["status"], "counts": result["counts"]}, indent=2))
        raise SystemExit(0 if result["status"].startswith("COMPLETE_") else 1)

"""Bind eight actual top-side washer rings to 48 frozen own-end demands.

Import is inert. Parent-only ``build(output)`` runs 48 actual-profile slab
probes through the unchanged land worker, then computes mean references.
No plate, bolt, frame, native or new constitutive model is executed.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import math
import os
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-land-reference-completion"
LAND = HERE / "washer-land-completion.py"
LAND_SHA = "e6e42f901d08042c1c3ef1045af9b3f3cf0aea65bb1bcf8b051978bdc18ba0aa"
SOURCE = HERE / "rawlocal/washer-land-completion/attempt01"
RECEIPT_SHA = "7d541cef4b05b03a6d501243759dd1ea435eeb42be4ce2d71eda27cd9ea78679"
CORNER = HERE / "rawlocal/knee-bridge-corner-replay/attempt01/checks.json"
CORNER_SHA = "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976"
PROFILE = HERE / "upper-right-washer-flexure.py"
PROFILE_SHA = "782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac"
EDGE = HERE / "upper-right-washer-edge.py"
EDGE_SHA = "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61"
SAVED_PLATE = HERE / "rawlocal/upper-right-washer-flexure/attempt01/checks.json"
SAVED_PLATE_SHA = "a6ac3fb5587ed24926e5fbc3353f69db19fb7fe8a60eb2dee40fa911b2f2544a"
MATERIAL = ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json"
MATERIAL_SHA = "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a"
CASES = {"a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"}
FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
         "physical_release": False, "fabrication_release": False,
         "actual_washer_capacity_n": None, "actual_washer_stress_mpa": None,
         "actual_washer_yield_mpa": None, "actual_hardware_inspected": False,
         "global_frame_feedback": False, "loaded_shift_or_tilt_qualified": False,
         "plate_or_native_or_frame_solve_run": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def load_land():
    # Reuse its inert standard-library controller helpers and unchanged CAD worker.
    import hashlib
    require(hashlib.sha256(LAND.read_bytes()).hexdigest() == LAND_SHA, "frozen land worker changed")
    spec = importlib.util.spec_from_file_location("actual_side_saved_land", LAND)
    require(spec is not None and spec.loader is not None, "land worker loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def literal_family(node):
    """Read only the pinned numeric/dictionary profile expression; never eval."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float)):
        return node.value
    if isinstance(node, ast.Dict):
        return {literal_family(k): literal_family(v) for k, v in zip(node.keys, node.values, strict=True)}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        return literal_family(node.left) / literal_family(node.right)
    raise ValueError("STOP: pinned profile is no longer a literal numeric dictionary")


def side_profile():
    tree = ast.parse(PROFILE.read_text())
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "FAMILIES" for target in node.targets))
    profile = literal_family(assignment.value)["side"]
    require(profile == {"inner_radius_mm": 4.953, "outer_radius_mm": 11.0236,
                        "head_radius_mm": 6.0, "thickness_mm": 1.6256},
            "existing 5/16 side family dimensions differ")
    return profile


def inputs(api):
    pins = {**api.METHOD_PINS, LAND: LAND_SHA, Path(__file__).resolve(): api.sha(__file__),
            PROFILE: PROFILE_SHA, EDGE: EDGE_SHA, SAVED_PLATE: SAVED_PLATE_SHA,
            CORNER: CORNER_SHA, MATERIAL: MATERIAL_SHA,
            SOURCE / "receipt.json": RECEIPT_SHA}
    api.authenticate(pins)
    receipt = api.read(SOURCE / "receipt.json")
    require(receipt["schema"] == "washer_land_completion_receipt/v1"
            and receipt["sources_authenticated_before_and_after"] is True
            and receipt["status"] == "COMPLETE_120_PROBES_WITH_OPEN_NOMINAL_LANDS"
            and receipt["counts"]["finite_probe_records"] == 120
            and receipt["output_sha256"]["producer.py.snapshot"] == LAND_SHA
            and receipt["complete_joint_acceptance"] is False and receipt["physical_release"] is False,
            "completed generic land packet or boundaries differ")
    for name, digest in receipt["source_sha256"].items():
        api.add_pin(pins, ROOT / name, digest)
    for name, digest in receipt["output_sha256"].items():
        require(Path(name).name == name and not (SOURCE / name).is_symlink(), "source packet artifact alias")
        api.add_pin(pins, SOURCE / name, digest)
    api.authenticate(pins)
    old = api.read(SOURCE / "washer-land-completion.json")
    raw_plan = api.read(SOURCE / "worker-input.json")
    generic = {tuple(row["physical_land_key"]): row for row in old["geometry"]["seats"]
               if not row["nominal_annulus_support_established"]}
    requests = {tuple(row["physical_land_key"]): row for row in raw_plan["new_land_queries"]}
    profile = side_profile()
    saved_plate = api.read(SAVED_PLATE)
    require(saved_plate["schema"] == "upper_right_free_edge_mindlin_washer_flexure/v1"
            and saved_plate["model"]["families"]["side"] == profile
            and saved_plate["model"]["degree"] == 4
            and saved_plate["counts"]["completed_end_states"] == 48
            and sum(row["family"] == "side" for row in saved_plate["states"]) == 24,
            "saved degree-four side-family method reference differs")
    area = math.pi * (profile["outer_radius_mm"] ** 2 - profile["inner_radius_mm"] ** 2)
    material = api.read(MATERIAL)["conditional_DF_L_No2_base_row"]
    require(material["base_properties"]["Fc_perpendicular"] == 625, "conditional wood base reference differs")
    wood_reference = 625 * 0.006894757293168361
    corner = api.read(CORNER)
    require(corner["status"] == "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES"
            and corner["failure"] is None
            and all(pins.get((ROOT / name).resolve()) == digest
                    for name, digest in corner["fresh_load_sources"].items()),
            "fresh simultaneous corner response identity differs")
    rows, masks = [], {}
    for state_index, state in enumerate(corner["states"]):
        if state["level"] != "top":
            continue
        require(state["case_id"] in CASES and state["side"] in {"left", "right"}, "top case/side differs")
        host = "base_side_" + state["side"]
        packet = state["hosts"][host]
        geometry = packet["geometry"]
        require(geometry["diameter_mm"] == 7.9375 and geometry["bore_mm"] == 9.0
                and geometry["washer_ID_max_mm"] == 2 * profile["inner_radius_mm"]
                and geometry["washer_OD_min_mm"] == 2 * profile["outer_radius_mm"]
                and geometry["flat_radius_mm"] == profile["head_radius_mm"],
                "actual top-side source does not match the existing 5/16 family")
        bolts = {b["axis_id"]: b for b in packet["state"]["bolts"]}
        for seat_index, seat in enumerate(packet["wood_seat_recovery"]):
            require(seat["end"] in {"host_head", "cleat_nut"}, "top-side physical role differs")
            role = "head" if seat["end"] == "host_head" else "nut"
            receiver = host if role == "head" else state["cleat"]
            key = (seat["axis_id"], role, receiver)
            require(key in generic and key in requests and "/side_" in key[0],
                    "actual top-side end is outside the eight generic obligations")
            bolt = bolts[key[0]]
            axis = [float(x) for x in bolt["bolt_axis_head_to_nut_xyz"]]
            inward = [(1 if role == "head" else -1) * x for x in axis]
            wrench = [float(x) for x in seat["recovered_force_and_own_pressure_moment_at_seat_n_nmm"]]
            tension = float(bolt["compatible_T_n"])
            require(len(wrench) == 6 and all(math.isfinite(x) for x in wrench)
                    and tension >= 0 and math.isclose(tension, seat["T_n"], rel_tol=0, abs_tol=1e-7)
                    and max(abs(wrench[i] - tension * inward[i]) for i in range(3)) <= 1e-6
                    and abs(sum(wrench[i + 3] * axis[i] for i in range(3))) <= 1e-6,
                    "fresh own-seat signed force/moment convention differs")
            point = seat["nominal_outer_wood_seat_xyz_mm"]
            request = requests[key]
            require(max(abs(a - b) for a, b in zip(point, request["current_nominal_seat_point_xyz_mm"], strict=True)) <= 1e-7
                    and max(abs(a - b) for a, b in zip(inward, request["current_inward_normal_xyz"], strict=True)) <= 1e-8,
                    "actual-profile query would change current datum or normal")
            actual_inner = max(geometry["bore_mm"] / 2, profile["inner_radius_mm"])
            require(actual_inner == profile["inner_radius_mm"], "actual 5/16 washer has an inner unsupported strip")
            contract = {**request, "annulus_inner_outer_radii_mm": [actual_inner, profile["outer_radius_mm"]],
                        "actual_side_profile": profile, "bolt_diameter_mm": 7.9375, "bore_diameter_mm": 9.0,
                        "generic_result_retained": {k: generic[key][k] for k in (
                            "minimum_inward_support_fraction", "maximum_outward_overlap_fraction",
                            "support_fraction_tolerance")},
                        "generic_ring_not_actual_washer": True,
                        "wood_mask_inner_is_max_bore_and_washer_inner": True}
            if key in masks:
                require(masks[key]["annulus_inner_outer_radii_mm"] == contract["annulus_inner_outer_radii_mm"],
                        "actual profile changes with load case")
            else:
                masks[key] = contract
            contact = bolt["end_contacts"][0 if role == "head" else 1]
            magnitude = math.hypot(*wrench[3:])
            require(math.isclose(magnitude, abs(contact["moment_nmm"]), rel_tol=1e-8, abs_tol=1e-6),
                    "own-seat recovered moment disagrees with saved contact")
            rows.append({"case_id": state["case_id"], "axis_id": key[0], "end_role": role,
                         "receiver_member": receiver, "join_key": [state["case_id"], *key],
                         "physical_land_key": list(key), "T_n": tension,
                         "force_on_receiver_xyz_n": wrench[:3], "own_end_M_signed_xyz_nmm": wrench[3:],
                         "own_end_M_magnitude_nmm": magnitude,
                         "own_end_eccentricity_mm": magnitude / tension if tension > 0 else None,
                         "own_seat_xyz_mm": point, "normal_into_receiver_xyz": inward,
                         "source": api.display(CORNER), "source_sha256": CORNER_SHA,
                         "source_pointer": f"/states/{state_index}/hosts/{host}/wood_seat_recovery/{seat_index}",
                         "actual_side_profile": profile, "actual_annulus_area_mm2": area,
                         "ideal_actual_annulus_mean_pressure_mpa": tension / area,
                         "conditional_Fc_perp_reference_mpa": wood_reference,
                         "saved_rigid_contact": contact,
                         "nominal_support_status": "ACTUAL_PROFILE_QUERY_PENDING",
                         "bound_supported_mean_pressure_mpa": None, "wood_mean_reference_index": None,
                         "existing_plate_method_status": "ACTUAL_PROFILE_SUPPORT_PENDING", **FLAGS})
    require(len(rows) == len({tuple(row["join_key"]) for row in rows}) == 48
            and len(masks) == len(generic) == 8 and set(masks) == set(generic)
            and {row["case_id"] for row in rows} == CASES,
            "eight current top-side rings / 48 own-end states census differs")
    return rows, {"schema": "actual_top_side_annulus_plan/v1", "new_land_queries": list(masks.values()),
                  "physical_lands": 8, "inward_probes": 24, "outward_probes": 24,
                  "generic_120_probe_packet_unchanged": True, **FLAGS}, pins


def build(output):
    """Parent-owned actual-ring geometry and fixed-demand algebra only."""
    output = Path(output).absolute()
    require(output.resolve() == output and output.parent == RAW and not output.exists(),
            "use a fresh child of rawlocal/washer-land-reference-completion")
    api = load_land()
    rows, plan, pins = inputs(api)
    api.authenticate(pins)
    before = {api.display(path): digest for path, digest in sorted(pins.items())}
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    api.write(output / "actual-profile-plan.json", plan)
    child_result = output / "worker-result.json"
    command = [str(ROOT / ".venv/bin/python"), "-B", str(Path(__file__).resolve()),
               "--worker-input", str(output / "actual-profile-plan.json"), "--worker-output", str(child_result)]
    started = time.monotonic()
    returncode, timed_out, failure = None, False, None
    with (output / "worker.stdout.log").open("x") as stdout, (output / "worker.stderr.log").open("x") as stderr:
        try:
            process = subprocess.run(command, cwd=ROOT, check=False, timeout=api.TIMEOUT_SECONDS,
                                     stdout=stdout, stderr=stderr,
                                     env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            returncode = process.returncode
        except subprocess.TimeoutExpired:
            timed_out, failure = True, "Actual-profile geometry child exceeded 120 seconds; partial output retained."
        except OSError as error:
            failure = str(error)
    elapsed = time.monotonic() - started
    geometry = None
    if child_result.exists():
        try:
            geometry = api.read(child_result)
        except json.JSONDecodeError as error:
            failure = str(error)
    support = {tuple(row["physical_land_key"]): row for row in geometry["seats"]} if geometry else {}
    complete = (returncode == 0 and not timed_out and geometry is not None
                and geometry["schema"] == "washer_land_geometry_worker/v1"
                and geometry["probe_records"] == geometry["finite_probe_records"] == 48
                and len(geometry["seats"]) == 8 and geometry["STEP_imports"] == 4
                and set(support) == {tuple(r["physical_land_key"]) for r in rows})
    try:
        api.authenticate(pins)
        after = {api.display(path): api.sha(path) for path in sorted(pins)}
        unchanged = before == after
    except (ValueError, OSError) as error:
        after = {api.display(path): api.sha(path) for path in sorted(pins) if path.exists()}
        unchanged, complete, failure = False, False, "Source authentication failed: " + str(error)
    for row in rows:
        land = support.get(tuple(row["physical_land_key"]))
        qualified = complete and land is not None and land["nominal_annulus_support_established"] is True
        row["nominal_support_status"] = "BOUND_FULL_ACTUAL_SIDE_ANNULUS" if qualified else "ACTUAL_PROFILE_SUPPORT_UNRESOLVED"
        if qualified:
            row["bound_supported_mean_pressure_mpa"] = row["ideal_actual_annulus_mean_pressure_mpa"]
            row["wood_mean_reference_index"] = row["bound_supported_mean_pressure_mpa"] / row["conditional_Fc_perp_reference_mpa"]
            row["existing_plate_method_status"] = "MATCHED_EXISTING_SIDE_FAMILY_NOT_EXECUTED"
    full_lands = sum(row["nominal_annulus_support_established"] for row in support.values()) if complete else None
    peaks = {}
    for column in ("T_n", "own_end_M_magnitude_nmm", "own_end_eccentricity_mm", "wood_mean_reference_index"):
        available = [row for row in rows if row[column] is not None]
        witness = max(available, key=lambda row: row[column]) if available else None
        peaks[column] = None if witness is None else {"join_key": witness["join_key"], "value": witness[column],
                                                     "same_state_T_n": witness["T_n"],
                                                     "same_state_M_nmm": witness["own_end_M_magnitude_nmm"]}
    status = "COMPLETE_MATCHED_TOP_SIDE_NOMINAL_REFERENCES" if complete and full_lands == 8 else "ACTUAL_TOP_SIDE_SUPPORT_REMAINS_OPEN"
    if not unchanged:
        status = "STOP_SOURCE_BYTES_CHANGED"
    result = {"schema": "washer_land_reference_completion/v1", "status": status,
              "counts": {"fresh_own_end_states": 48, "actual_side_profile_land_contracts": 8,
                         "planned_actual_ring_probes": 48,
                         "returned_actual_ring_probes": geometry["probe_records"] if geometry else None,
                         "finite_actual_ring_probes": geometry["finite_probe_records"] if geometry else None,
                         "full_actual_profile_lands": full_lands},
              "same_state_peak_witnesses": peaks, "source_generic_land_receipt_sha256": RECEIPT_SHA,
              "generic_ring_clipping_not_actual_washer_deficit": True,
              "matching_existing_plate_method": {"helper": api.display(EDGE), "helper_sha256": EDGE_SHA,
                  "profile_source": api.display(PROFILE), "profile_source_sha256": PROFILE_SHA,
                  "family_key": "side", "profile": rows[0]["actual_side_profile"],
                  "helper_family_slot": "make_model uses FAMILIES['rail']; supply the declared side profile there without changing its dimensions.",
                  "conditional_material_hypotheses": {"E_mpa": 200000, "nu": 0.3, "Fy_comparator_mpa": 250,
                                                       "Kwood_mpa_per_mm": 20, "Khead_mpa_per_mm": 10000},
                  "saved_matching_family_reference": {"path": api.display(SAVED_PLATE), "sha256": SAVED_PLATE_SHA,
                                                       "degree": 4, "side_end_states": 24,
                                                       "old_independent_pair_loads": True,
                                                       "fresh_simultaneous_loads_covered": False},
                  "fresh_side_fine_stress_reference_available": False,
                  "capacity_or_stress_assigned": False},
              "geometry": geometry, "child_command": command, "child_exit_code": returncode,
              "child_elapsed_seconds": elapsed, "child_timeout_seconds": api.TIMEOUT_SECONDS,
              "child_timed_out": timed_out, "failure": failure,
              "source_before_sha256": before, "source_after_sha256": after,
              "sources_authenticated_before_and_after": unchanged,
              "limits": ["Only nominal support and fixed fresh own-end loads are compared; no force redistribution is computed.",
                         "Mean wood pressure is not peak contact pressure or a full timber/joint strength check.",
                         "The saved 5/16 degree-four method uses old loads; the fine helper is only a matched-family candidate, with no transferred stress/capacity result.",
                         "Actual washer thickness, steel yield, head/nut bearing profiles, loaded movement and compatibility remain unqualified.",
                         "Quarter-inch retail and ordinary N10 packets remain separate; all authority and release HOLD boundaries remain."], **FLAGS}
    api.write(output / "washer-land-reference-completion.json", result)
    with (output / "own-end-references.jsonl").open("x") as stream:
        for row in sorted(rows, key=lambda item: tuple(item["join_key"])):
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
    artifacts = {path.name: api.sha(path) for path in sorted(output.iterdir()) if path.is_file()}
    api.write(output / "receipt.json", {"schema": "washer_land_reference_completion_receipt/v1", "status": status,
                                       "source_sha256": before, "source_before_sha256": before,
                                       "source_after_sha256": after, "sources_authenticated_before_and_after": unchanged,
                                       "output_sha256": artifacts, "counts": result["counts"], **FLAGS})
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker-input", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--worker-output", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker_input is not None:
        require(args.worker_output is not None and args.output is None, "internal child arguments differ")
        load_land().worker(args.worker_input, args.worker_output)
    else:
        require(args.output is not None and args.worker_output is None, "provide a fresh --output path")
        result = build(args.output)
        print(json.dumps({"status": result["status"], "counts": result["counts"]}, indent=2))
        raise SystemExit(0 if result["status"].startswith("COMPLETE_") else 1)

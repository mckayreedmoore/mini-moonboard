"""Invert saved receiver beam comparisons without changing the working model.

Preparation authenticates sources and inventories saved identities only.
The parent owns build(), which calculates fixed-force necessary geometry
bounds. No result qualifies a translated connection or adopts a repair.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
ROOT = next(p for p in HERE.parents if (p / "current-candidate.json").is_file())
BEAM = UPPER / "rawlocal/beam-connection-shear-completion/attempt01"
DETAIL = UPPER / "rawlocal/bolt-detailing-completion/attempt02"
RAW = HERE / "rawlocal/receiver-revision-bounds"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
SCENARIOS = ("cd1", "cd1_25")
ALLOWED_LIMITS = {
    "ASSOCIATED_AXIAL_WASHER_OR_TIE_ACTION_SEPARATE",
    "OBLIQUE_LOAD_TRANSVERSE_COMPONENT_ONLY",
}
JOINS = {
    f"base_post_outer_{side} :: {first} | {second}": (first, second)
    for side in ("left", "right")
    for first, second in (
        (f"knee_outer_{side}_post_1", f"knee_outer_{side}_post_2"),
        (f"rail_front_bolt_{side}_1", f"rail_front_bolt_{side}_2"),
    )
}
EXPECTED_EXCEEDANCES = {
    ("left", "knee", "a12-rear"),
    ("left", "knee", "a12-forward"),
    ("left", "knee", "a12-left"),
    ("right", "knee", "k12-right"),
    ("right", "knee", "k12-rear"),
    ("left", "floor", "a12-left"),
    ("left", "floor", "a12-forward"),
    ("right", "floor", "k12-right"),
}
PINS = {
    BEAM / "receipt.json": "7b88e4ba5c9a64a6552880877970ebc4f7371080f126cedc9e40b46f0a5ede60",
    BEAM / "report.json": "f718352feed4a903a27da803831f21b78f335c7cfb60aad493725bd102c556b8",
    BEAM / "group-case-states.jsonl": "551a24999d6400e1c17c19cdf16a746da75ce2f75b6c3fb90595c6ca9a3882fb",
    BEAM / "body-case-closure.json": "f290f1ca671c4b7fabc2543214c0411ab91355ef0fc5491f0fb377cd3e12510d",
    UPPER / "beam-connection-shear-completion.md": "cf21bd3416e2d2d2f3cb5f91dee691a1afbcccff28263fd71469ba7870aa5144",
    DETAIL / "receipt.json": "28c00cefe1d95f86d75b837304a958ff5242690f88017e685a959ba7c1b15a59",
    DETAIL / "host-states.jsonl": "07f086dff6a9691d06370888e43adf4bcd8c016b40c73c9dd5e614be6948a998",
    DETAIL / "geometry-bindings.json": "c883691261a365125cedde76add0a3bf0406bd1c3c0b5fbfc1dc4b0aa25fa8ed",
    DETAIL / "pair-spacing.jsonl": "18919732c50de3b9ceba95cb39b196be141aec3814b4254f1202f6c81a6da049",
    UPPER / "rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf":
        "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
    UPPER.parent.parent / "upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf":
        "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
}
FLAGS = {
    key: False for key in (
        "splitting_resistance_established", "complete_joint_acceptance",
        "repair_accepted", "geometry_changed", "axis_positions_changed",
        "material_or_load_changed", "frame_solve", "native_launch", "CAD_rebuilt",
        "global_feedback", "partner_transfer_qualified", "N03_accepted",
        "physical_release", "fabrication_release", "proposal_adopted",
        "formal_criteria_updated", "tests_run", "review_run",
    )
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def rows(path: Path) -> list[dict]:
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def input_pins() -> dict[Path, str]:
    pins = dict(PINS)
    for receipt_path in (BEAM / "receipt.json", DETAIL / "receipt.json"):
        require(sha(receipt_path) == PINS[receipt_path], "receipt identity differs")
        receipt = read(receipt_path)
        additions = [(ROOT / name, h) for name, h in receipt["source_sha256"].items()]
        additions += [(receipt_path.parent / name, h)
                      for name, h in receipt["output_sha256"].items()]
        for path, digest in additions:
            require(path not in pins or pins[path] == digest, "conflicting source identity")
            pins[path] = digest
    return pins


def authenticate(pins: dict[Path, str]) -> dict[str, str]:
    for path, digest in pins.items():
        require(sha(path) == digest, "source identity differs: " + str(path.relative_to(ROOT)))
    return {str(path.relative_to(ROOT)): digest for path, digest in pins.items()}


def available(entry: dict) -> bool:
    return (entry["unloaded_edge_is_actual_unique_transfer"] is True
            and set(entry["limits"]) <= ALLOWED_LIMITS)


def selected_states() -> list[dict]:
    selected = [r for r in rows(BEAM / "group-case-states.jsonl") if r["join_id"] in JOINS]
    require(len(selected) == 24, "four joins times six cases not recovered")
    require({(r["join_id"], r["case_id"]) for r in selected}
            == {(j, c) for j in JOINS for c in CASES}, "case or join identity differs")
    observed = set()
    for row in selected:
        require(tuple(row["axis_ids"]) == JOINS[row["join_id"]], "physical pair differs")
        for entry in row["primary_component_comparisons"]:
            if available(entry) and any(entry["scenarios"][s]["comparison_exceeds_one"]
                                        for s in SCENARIOS):
                side = row["body"].removeprefix("base_post_outer_")
                family = "knee" if row["axis_ids"][0].startswith("knee") else "floor"
                observed.add((side, family, row["case_id"]))
                require(all(entry["scenarios"][s]["comparison_exceeds_one"]
                            for s in SCENARIOS), "duration exceedance membership changed")
    require(observed == EXPECTED_EXCEEDANCES, "eight actual-edge witnesses differ")
    return selected


def dot(a: list, b: list) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def inverse(entry: dict, scenario: str) -> dict:
    source = entry["scenarios"][scenario]
    b, d, de, fv, v = (entry["b_mm"], entry["d_mm"], entry["de_mm"],
                       source["Fv_mpa"], source["V_abs_n"])
    require(all(math.isfinite(x) and x > 0 for x in (b, d, de, fv)), "invalid inverse basis")
    require(math.isfinite(v) and v >= 0, "invalid saved shear")
    require(entry["branch"] == "near" and entry["equation"] == "3.4-6",
            "bounded scope lost the near-end equation")
    original_vr = (2 / 3) * fv * b * de * (de / d) ** 2
    require(math.isclose(original_vr, source["Vr_prime_n"], rel_tol=1e-9, abs_tol=1e-8),
            "saved capacity does not reproduce")
    require(math.isclose(v / original_vr, source["index"], rel_tol=1e-9, abs_tol=1e-9),
            "saved index does not reproduce")
    required = math.cbrt(3 * v * d * d / (2 * fv * b))
    inverse_vr = (2 / 3) * fv * b * required * (required / d) ** 2
    require(math.isclose(inverse_vr, v, rel_tol=1e-9, abs_tol=1e-8), "inverse does not close")
    side = entry["loaded_physical_depth_edge_sign"]
    require(side in (-1, 1), "actual edge sign missing")
    return {
        "scenario": scenario, "source": source, "required_de_mm": required,
        "existing_de_mm": de, "de_relation": "de(t) = existing_de - loaded_edge_sign * t",
        "loaded_edge_sign": side, "t_lower_bound_mm": required - de if side == -1 else None,
        "t_upper_bound_mm": de - required if side == 1 else None,
        "inverse_capacity_n": inverse_vr, "required_de_exceeds_depth": required > d,
        "fixed_force_only": True, "accepted_repair": False,
    }


def receiver_constraints(states: list[dict], details: dict, bindings: dict) -> dict:
    geometry = states[0]["geometry"]
    direction = geometry["depth_axis_global_xyz"]
    require(math.isclose(dot(direction, direction), 1, abs_tol=1e-8), "depth axis not unit")
    require(geometry["geometry_guard"] is None and geometry["NDS_rectangle_component_established"],
            "receiver rectangular geometry not established")
    require(geometry["branch"] == "near", "near-end branch changed")
    for state in states:
        require(state["geometry"] == geometry, "same-pair geometry changes by case")
    limits, unchanged_ends, unknown_edges, partner_references = [], [], [], []
    for axis, center, edge in zip(states[0]["axis_ids"], geometry["bore_centers_xyz_mm"],
                                  geometry["center_to_physical_edges_mm"], strict=True):
        binding = bindings[states[0]["body"], axis]
        require(binding["effective_STEP"] == binding["current_STEP"], "receiver geometry revised")
        radius = binding["bore_radius_mm"]
        limits.append({"kind": "BORE_ENVELOPE_WITHIN_RECEIVER_DEPTH_FACES", "axis_id": axis,
                       "lower_mm": radius - edge["-1"], "upper_mm": edge["1"] - radius,
                       "existing_center_xyz_mm": center, "bore_radius_mm": radius})
    for state in states:
        body, case = state["body"], state["case_id"]
        for axis in state["axis_ids"]:
            source = details[body, axis, case]
            detail = source["detail"]
            for name, edge in detail["reference_edge_comparisons"].items():
                ray = detail["reference_rays"][name]
                scalar = dot(ray["ray_unit_xyz"], direction)
                require(math.isclose(abs(scalar), 1, abs_tol=1e-7), "edge ray is not depth-aligned")
                require(ray["reference_basis"] == "EXACT_CONSTANT_PRISM_REFERENCE",
                        "receiver edge lost its constant-prism reference")
                side = 1 if scalar > 0 else -1
                value = edge["minimum_mm"]
                item = {"case_id": case, "axis_id": axis, "ray": name, "physical_edge_sign": side,
                        "source_comparison": edge, "source_ray_distance_mm": ray["distance_mm"]}
                if value is None:
                    unknown_edges.append(item)
                    continue
                require(math.isfinite(value) and value >= 0, "invalid saved edge requirement")
                rhs = ray["distance_mm"] - value
                item.update(kind="SAVED_EDGE_HYPOTHESIS", lower_mm=-rhs if side == -1 else None,
                            upper_mm=rhs if side == 1 else None, N03_accepted=False)
                limits.append(item)
            for name, end in detail["reference_end_comparisons"].items():
                ray = detail["reference_rays"][name]
                require(abs(dot(ray["ray_unit_xyz"], direction)) < 1e-7,
                        "receiver grain-end distance is not invariant under this translation")
                normals = ray["exterior_normals_xyz"]
                require(normals and all(abs(dot(n, direction)) < 1e-7 for n in normals),
                        "receiver end face is not translation-parallel")
                unchanged_ends.append({"case_id": case, "axis_id": axis, "ray": name,
                                       "source_comparison": end, "distance_unchanged": True,
                                       "N03_accepted": False})
            partners = {p["partner"] for p in state["loading"]["global_lateral_planes"]
                        if p["axis_id"] == axis}
            require(len(partners) == 1, "physical axis partner ambiguous")
            partner = next(iter(partners))
            other = details[partner, axis, case]["detail"]
            other_binding = bindings[partner, axis]
            partner_references.append({
                "case_id": case, "axis_id": axis, "partner": partner,
                "geometry_binding": other_binding,
                "proposal_geometry_differs_from_reviewed":
                    other_binding["effective_STEP"] != other_binding["current_STEP"],
                "source_end_comparisons": other["reference_end_comparisons"],
                "source_edge_comparisons": other["reference_edge_comparisons"],
                "translated_end_or_edge_reference_not_established": True,
                "floor_partner_end_distances_change": partner.startswith("base_floor_"),
                "partner_transfer_qualified": False,
            })
    lower = max(q["lower_mm"] for q in limits if q["lower_mm"] is not None)
    upper = min(q["upper_mm"] for q in limits if q["upper_mm"] is not None)
    return {"global_translation_direction": direction, "constraints": limits,
            "receiver_depth_and_saved_edge_window_mm": [lower, upper],
            "unchanged_receiver_grain_end_comparisons": unchanged_ends,
            "unassigned_edge_requirements": unknown_edges, "partner_references": partner_references,
            "complete_detailing_qualified": False}


def calculate(selected: list[dict]) -> dict:
    details = {(r["body"], r["axis_id"], r["case_id"]): r
               for r in rows(DETAIL / "host-states.jsonl")}
    bindings = {(r["body"], r["axis_id"]): r for r in read(DETAIL / "geometry-bindings.json")}
    spacing = rows(DETAIL / "pair-spacing.jsonl")
    joins = []
    for join in JOINS:
        states = [r for r in selected if r["join_id"] == join]
        constraints = receiver_constraints(states, details, bindings)
        comparisons, guarded = [], []
        for state in states:
            for entry in state["primary_component_comparisons"]:
                if not available(entry):
                    guarded.append({"case_id": state["case_id"], "source_component": entry,
                                    "inverse_assigned": False})
                    continue
                for scenario in SCENARIOS:
                    comparisons.append({"case_id": state["case_id"], "source_component": entry,
                                        **inverse(entry, scenario)})
        envelopes = []
        for scenario in SCENARIOS:
            candidates = [q for q in comparisons if q["scenario"] == scenario]
            lo, hi = constraints["receiver_depth_and_saved_edge_window_mm"]
            lo = max([lo] + [q["t_lower_bound_mm"] for q in candidates
                             if q["t_lower_bound_mm"] is not None])
            hi = min([hi] + [q["t_upper_bound_mm"] for q in candidates
                             if q["t_upper_bound_mm"] is not None])
            nonempty = lo <= hi
            shift = min(max(0.0, lo), hi) if nonempty else None
            centers = None if shift is None else [
                [x + shift * v for x, v in zip(p, constraints["global_translation_direction"], strict=True)]
                for p in states[0]["geometry"]["bore_centers_xyz_mm"]]
            envelopes.append({"scenario": scenario, "conditional_translation_window_mm": [lo, hi],
                              "window_nonempty": nonempty, "nearest_zero_translation_mm": shift,
                              "hypothetical_receiver_centers_xyz_mm": centers,
                              "pair_spacing_unchanged_by_common_translation": True,
                              "receiver_only_fixed_force_edge_hypothesis": True,
                              "whole_joint_feasibility_established": False, "repair_accepted": False})
        axes = set(states[0]["axis_ids"])
        own_spacing = [q for q in spacing if q["body"] == states[0]["body"]
                       and {q["first_axis_id"], q["second_axis_id"]} == axes]
        require({q["case_id"] for q in own_spacing} == set(CASES), "pair spacing cases missing")
        joins.append({"join_id": join, "source_geometry": states[0]["geometry"],
                      "source_spacing": own_spacing, "source_spacing_acceptance_not_transferred": True,
                      "comparisons": comparisons, "guarded_components": guarded,
                      "constraints": constraints, "envelopes": envelopes})
    return {"joins": joins, "fixed_force_only": True, **FLAGS}


def run(output: Path | str, *, numerical: bool) -> dict:
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "output must be a fresh immediate child")
    output.mkdir(parents=True)
    producer = Path(__file__)
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    sources = {}
    try:
        pins = input_pins()
        sources = authenticate(pins)
        selected = selected_states()
        ast.parse(producer.read_text())
        report = {"schema": "receiver-fixed-force-revision-bounds/v1",
                  "status": "COMPLETED_NECESSARY_BOUNDS" if numerical else "PREPARED_NOT_NUMERICALLY_RUN",
                  "numerical_arithmetic_run": numerical, "source_state_count": len(selected),
                  "target_exceedance_count": len(EXPECTED_EXCEEDANCES), "case_ids": CASES,
                  "reviewed_bolt_axes": 104, "panel_kicker_screws": 66,
                  "source_sha256": sources, "producer_sha256": sha(producer), **FLAGS}
        if numerical:
            write(output / "bounds.json", calculate(selected))
            with (output / "source-states.jsonl").open("w") as stream:
                for state in selected:
                    stream.write(json.dumps(state, sort_keys=True, allow_nan=False) + "\n")
        else:
            report["join_case_inventory"] = [(r["join_id"], r["case_id"]) for r in selected]
        authenticate(pins)
        report["sources_authenticated_before_and_after"] = True
        write(output / "checks.json", report)
    except Exception as error:
        write(output / "STOP.json", {"status": "STOP", "reason": str(error), **FLAGS})
        raise
    finally:
        outputs = {p.name: sha(p) for p in output.iterdir() if p.is_file() and p.name != "receipt.json"}
        write(output / "receipt.json", {"source_sha256": sources, "output_sha256": outputs,
                                       "producer_sha256": sha(producer), **FLAGS})
    return report


def prepare(output: Path | str) -> dict:
    return run(output, numerical=False)


def build(output: Path | str) -> dict:
    return run(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    result = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": result["status"], "numerical_arithmetic_run": result["numerical_arithmetic_run"]}))

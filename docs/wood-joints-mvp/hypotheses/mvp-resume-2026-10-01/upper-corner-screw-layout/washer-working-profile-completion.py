"""Freeze working washer profiles and current-source joins without mechanics.

The eight wider top-rail seats enter the existing scalar axial-column law,
the shaft contact annuli and the plate profile through one declared contract.
Import, --check and --prepare do not import numerical or geometry libraries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
ASSEMBLY = HERE.parent / "assembly-package"
RAW = HERE / "rawlocal/washer-working-profile-completion"
RETAIL = HERE / "rawlocal/retail-washer-suite/attempt01-fine"
MEANS = HERE / "rawlocal/joint-frame-action-reconciliation/mean-reference-attempt01"
BOLTS = HERE / "rawlocal/joint-frame-bolt-reference/attempt03"
ORDER = ASSEMBLY / "rawlocal/working-order/attempt03/working-order.json"
AXES = ASSEMBLY / "rawlocal/hardware-axes.csv"
ROWS = HERE / "operators-attempt02/row-identities.json"
TOP_GEOMETRY = HERE.parent / "top-corner-contact-geometry.json"
PINS = {
    RETAIL / "source-pins.json": "8eaeee303516584b7d031365cb83446c287735e9fa801120c0ec58dca1e67f79",
    MEANS / "receipt.json": "67e98ce04e58aab46659207295d8d200ace179b59809852b1fb8e549f6e6f890",
    BOLTS / "receipt.json": "730144d3762ff0238528dee23eca2e0ac52c61845d48a847ec47f099f4418885",
    ORDER: "6becf19a9b06f625b4292cc8cd60f908fd3bff8d865430e60abcec155af4e9be",
    AXES: "2fb010f1b55757e614d90940bfa2a8400df6ee41ab0f950ffa56d30157150b01",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    TOP_GEOMETRY: "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    ROOT / "fea/wood_joint_reduced_properties.py": "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1",
}
PROFILES = {
    "quarter": {"part": "K.L. Jack 25NWUS", "inner_radius_mm": 4.1529,
                "outer_radius_mm": 9.2329, "head_radius_mm": 5.0, "thickness_mm": 1.2954},
    "top_rail_wide": {"part": "Hillman 885522 / Lowe's 755754", "inner_radius_mm": 4.1529,
                      "outer_radius_mm": 12.7, "head_radius_mm": 5.0, "thickness_mm": 2.5},
    "top_side_working": {"part": "Bolt Depot 2995", "inner_radius_mm": 4.953,
                         "outer_radius_mm": 11.0236, "head_radius_mm": 6.0, "thickness_mm": 1.6256},
    "retained_15023": {"part": "Bolt Depot 15023", "inner_radius_mm": 5.7531,
                       "outer_radius_mm": 12.6111, "head_radius_mm": 6.9977, "thickness_mm": 1.6256},
    "retained_15025": {"part": "Bolt Depot 15025", "inner_radius_mm": 7.3279,
                       "outer_radius_mm": 17.3736, "head_radius_mm": 9.3472, "thickness_mm": 2.1844},
}
HYPOTHESES = {"E_mpa": 200000.0, "nu": 0.3, "Fy_mpa": 250.0,
              "Kwood_mpa_per_mm": 20.0, "Khead_mpa_per_mm": 10000.0,
              "preload_n": 0.0, "first_order": True, "concentric_nominal_seats": True}
FLAGS = {"complete_joint_acceptance": False, "physical_release": False,
         "fabrication_release": False, "actual_hardware_inspected": False,
         "washer_metal_comparisons_complete": False, "scalar_own_end_moments_complete": False,
         "mechanics_or_CAD_executed": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def key(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def artifact(root, name, *, absolute=False):
    require(isinstance(name, str) and name and "\x00" not in name, "invalid artifact name")
    path = Path(name)
    require(".." not in path.parts and (absolute or not path.is_absolute()), "unsafe artifact path")
    target = path.resolve() if path.is_absolute() else (root / path).resolve()
    require(path.is_absolute() or target.is_relative_to(root), "artifact escapes declared root")
    return target


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "invalid SHA256")
    require(path not in pins or pins[path] == digest, "conflicting source hash: " + key(path))
    pins[path] = digest


def packet(pins, directory, receipt_name):
    """Authenticate every direct source/output binding, including retained fields."""
    receipt_path = directory / receipt_name
    receipt = read(receipt_path)
    for name, digest in receipt["source_sha256"].items():
        bind(pins, artifact(ROOT, name, absolute=True), digest)
    for name, digest in receipt["output_sha256"].items():
        prefix = key(directory) + "/"
        path = artifact(ROOT, name) if name.startswith(prefix) else artifact(directory, name)
        bind(pins, path, digest)
    return receipt


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "source hash changed: " + key(path))


def annulus_area(profile, *, pressing=False):
    outer = profile["head_radius_mm"] if pressing else profile["outer_radius_mm"]
    return math.pi * (outer**2 - profile["inner_radius_mm"]**2)


def profile_for_axis(contract, axis_id, source_diameter_mm, *, mode="source"):
    """Shared inert API: choose one declared profile without changing a shaft."""
    require(contract["schema"] == "washer_working_profile_contract/v1", "profile schema differs")
    require(mode in {"source", "working"}, "profile mode must be source or working")
    row = contract["axes"][axis_id]
    require(math.isfinite(source_diameter_mm) and source_diameter_mm > 0, "invalid source diameter")
    match = math.isclose(source_diameter_mm, row["working_shaft_diameter_mm"], abs_tol=1e-6, rel_tol=0)
    profile_id = row["profile_id"]
    if not match:
        require(row["family_id"] == "candidate_top_side_5_16_4"
                and math.isclose(source_diameter_mm, 6.35, abs_tol=1e-6, rel_tol=0),
                "undeclared shaft/profile mismatch")
        if mode == "source":
            profile_id = "quarter"
    profile = deepcopy(contract["profiles"][profile_id])
    partial = axis_id == "center_principal_right_2"
    return {"profile_id": profile_id, "plate_profile": {k: profile[k] for k in
            ("inner_radius_mm", "outer_radius_mm", "head_radius_mm", "thickness_mm")},
            "part": profile["part"], "working_profile_id": row["profile_id"],
            "source_diameter_mm": source_diameter_mm, "working_diameter_matches_source": match,
            "working_profile_requires_explicit_diameter_branch": not match and mode == "working",
            "shaft_contact": {"washer_ID_max_mm": 2 * profile["inner_radius_mm"],
                              "washer_OD_min_mm": 10.0 if partial else 2 * profile["outer_radius_mm"],
                              "flat_radius_mm": profile["head_radius_mm"]},
            "partial_supported_ring_route": partial,
            "restricted_shaft_contact_does_not_shrink_actual_plate": partial,
            "hypotheses": deepcopy(contract["hypotheses"])}


def column_stiffness(basis, area, washer_thickness_mm, seat_spacing_mm):
    """Existing reduced-properties axial law using its recorded material inputs."""
    depth = math.sqrt(4 * area / math.pi)
    steel_length = seat_spacing_mm + 2 * washer_thickness_mm
    steel_area = math.pi * basis["steel_diameter_mm"]**2 / 4
    e1, e2 = basis["wood_seat_effective_E_axis_mpa_baseline"]
    compliance = steel_length / (basis["steel_E_mpa_baseline"] * steel_area)
    compliance += depth / (e1 * area) + depth / (e2 * area)
    return {"stiffness_n_per_mm": 1 / compliance, "compliance_mm_per_n": compliance,
            "washer_annular_bearing_area_mm2": area, "wood_column_depth_mm": depth,
            "steel_extension_length_mm": steel_length, "washer_thicknesses_mm": [washer_thickness_mm] * 2,
            "steel_area_mm2": steel_area,
            "wood_seat_effective_E_axis_mpa": [e1, e2], "steel_E_mpa": basis["steel_E_mpa_baseline"]}


def joint_updates(contract, rows, geometry):
    """Four original axial rows, eight seats; geometry/directions stay source-bound."""
    result = []
    for cleat_index, cleat in enumerate(geometry["cleats"]):
        for row_index, source in enumerate(cleat["rows"]):
            axis = source.get("axis_id")
            if source["kind"] != "bolt_tension" or axis not in contract["top_rail_axes"]:
                continue
            original = [r for r in rows if r["row_id"] == axis + "/outer-seat-axial-tie"]
            require(len(original) == 1, "top rail axial port is not unique")
            old = original[0]
            basis = source["axial_law"]["stiffness_basis"]
            od, inside, old_t = source["nominal_washer_OD_ID_thickness_mm"]
            old_area = math.pi * (od**2 - inside**2) / 4
            spacing = basis["steel_extension_length_mm"] - 2 * old_t
            reconstructed = column_stiffness(basis, old_area, old_t, spacing)
            require(math.isclose(reconstructed["stiffness_n_per_mm"], old["law"]["stiffness_N_per_mm"],
                                 abs_tol=1e-9, rel_tol=0)
                    and source["stiffness_n_per_mm"] == old["law"]["stiffness_N_per_mm"]
                    and old["ownership"]["role"] == "physical_bolt_outer_seat_tension"
                    and old["law"]["intended_law"] == "tension_only", "old column law does not reproduce port")
            profile = contract["profiles"]["top_rail_wide"]
            new = column_stiffness(basis, annulus_area(profile), profile["thickness_mm"], spacing)
            result.append({"axis_id": axis, "original_row": old["row"], "row_id": old["row_id"],
                           "old_stiffness_n_per_mm": old["law"]["stiffness_N_per_mm"],
                           "new_stiffness_n_per_mm": new["stiffness_n_per_mm"],
                           "old_column_law": reconstructed, "new_column_law": new,
                           "old_profile_OD_ID_thickness_mm": [od, inside, old_t],
                           "new_profile_OD_ID_thickness_mm": [25.4, 8.3058, 2.5],
                           "source_ownership": old["ownership"], "outer_seat_points_mm": old["outer_seat_points_mm"],
                           "source_column_law_record": {"path": key(TOP_GEOMETRY), "sha256": PINS[TOP_GEOMETRY],
                               "pointer": f"/cleats/{cleat_index}/rows/{row_index}/axial_law/stiffness_basis"},
                           "source_original_rows": {"path": key(ROWS), "sha256": PINS[ROWS]},
                           "local_shaft_plate_K20_is_separate_from_column_E_law": True})
    require(len(result) == 4 and {r["original_row"] for r in result} == {1850, 1851, 1886, 1887},
            "wider profile changes unexpected ports")
    return {"schema": "washer_working_profile_joint_update/v1", "status": "PREPARED_NUMERICAL_PROFILE_UPDATE",
            "changes": sorted(result, key=lambda r: r["original_row"]), "physical_seats": 8,
            "only_scalar_axial_stiffness_changes": True, "D_W_or_physical_counts_changed": False,
            "preload_n": 0.0, "global_solve_required_for_new_force_basis": True, **FLAGS}


def head_certificate(tension, moment, radius):
    require(all(math.isfinite(x) for x in (tension, moment, radius))
            and tension >= 0 and moment >= 0 and radius > 0, "invalid own-end load")
    if tension == 0:
        status = "ANALYTIC_ZERO_DEMAND" if moment == 0 else "HEAD_COMPRESSION_LOAD_PATH_LIMIT"
        eccentricity = None
    else:
        eccentricity = moment / tension
        status = "ELIGIBLE_POSITIVE_T_FINE_REFERENCE" if eccentricity <= radius else "HEAD_COMPRESSION_LOAD_PATH_LIMIT"
    return {"status": status, "eccentricity_mm": eccentricity, "pressing_outer_radius_mm": radius,
            "necessary_condition_only": True, "small_loads_rounded_to_zero": False}


def to_frame_update(update, original_to_port_map):
    """Convert original row identities using the caller's authenticated lump map."""
    require(update["schema"] == "washer_working_profile_joint_update/v1"
            and len(update["changes"]) == 4
            and {r["original_row"] for r in update["changes"]} == {1850, 1851, 1886, 1887},
            "unexpected profile update inventory")
    rows = []
    for change in update["changes"]:
        original = change["original_row"]
        require(original in original_to_port_map and type(original_to_port_map[original]) is int
                and original_to_port_map[original] >= 0, "profile axial row omitted by port map")
        rows.append({"port_row": original_to_port_map[original], "old_k": change["old_stiffness_n_per_mm"],
                     "new_k": change["new_stiffness_n_per_mm"], "original_row": original,
                     "row_id": change["row_id"], "source_column_law_record": change["source_column_law_record"]})
    require(len({r["port_row"] for r in rows}) == 4, "profile ports were merged or duplicated")
    return {"schema": "joint_frame_scalar_seat_update/v1", "rows": rows,
            "original_row_mapping_must_be_source_bound_by_caller": True,
            "physical_seats": 8, "only_scalar_axial_stiffness_changes": True,
            "D_W_or_physical_counts_changed": False, "preload_n": 0.0}


def current_preflight(contract, scalars, ends, inventory):
    """Join saved fields without inventing moments or executing plate/shaft helpers."""
    source = {(r["state_tag"], r["axis_id"]): r for r in scalars}
    accepted = {r["state_tag"] for r in inventory if r["accepted_force_field_exists"]}
    excluded = {r["state_tag"] for r in inventory if not r["accepted_force_field_exists"]}
    require(len(accepted) == 12 and len(excluded) == 2 and len(source) == 1200, "current state inventory differs")
    records = []
    for index, end in enumerate(ends):
        axis, tag = end["axis_id"], end["state_tag"]
        require(tag in accepted, "unavailable field supplied as an own-end source")
        scalar = source.get((tag, axis))
        diameter = scalar["source_diameter_mm"] if scalar else contract["axes"][axis]["working_shaft_diameter_mm"]
        profile = profile_for_axis(contract, axis, diameter)
        moment = end["own_end_wood_moment_xyz_nmm"]
        require((moment is None) is end["own_end_moment_unknown_not_zero"], "null moment was altered")
        magnitude = math.hypot(*moment) if moment is not None else None
        support = end["support"]
        support_valid = support["modeled_support_applicability"] and not end["shop_source_profile_mismatch"]
        support_override = None
        if axis in contract["top_rail_axes"]:
            role = "host" if end["receiver"] == "base_rail_top" else "cleat"
            support_override = contract["top_rail_nominal_support"][axis + "/" + role]
            canonical_seat = contract["top_rail_outer_seat_points_mm"][axis][0 if role == "host" else 1]
            require(contract["top_rail_finished_steps"][end["receiver"]]
                    == {"path": support["reviewed104_finished_step"],
                        "sha256": support["reviewed104_finished_step_sha256"]}
                    and math.dist(canonical_seat, support_override["seat_xyz_mm"]) <= 1e-5,
                    "wider nominal seat does not match current receiver datum")
            support_valid = True
        certificate = head_certificate(end["signed_end_compression_n"], magnitude,
                                       profile["plate_profile"]["head_radius_mm"]) if magnitude is not None else None
        status = "PENDING_CURRENT_SCALAR_SHAFT_END_SOURCE" if magnitude is None else (
            "PENDING_SUPPORTED_MASK_OR_PROFILE_BINDING" if not support_valid else
            "PREPARED_CURRENT_END_PLATE_INPUT" if certificate["status"] != "HEAD_COMPRESSION_LOAD_PATH_LIMIT"
            else certificate["status"])
        records.append({"state_tag": tag, "case_id": end["case_id"], "gap_scale": end["gap_scale"],
                        "axis_id": axis, "end_role": end["end_role"], "receiver_member": end["receiver"],
                        "status": status, "T_n": end["signed_end_compression_n"],
                        "own_end_M_signed_xyz_nmm": moment, "own_end_M_magnitude_nmm": magnitude,
                        "profile_binding": profile, "head_compression_certificate": certificate,
                        "source_state_record": end["source_state_record"],
                        "source_end_record": {"path": key(MEANS / "washer-own-end-means.jsonl"),
                                              "record_index": index},
                        "saved_nominal_support": support, "wider_profile_support_override": support_override,
                        "support_matches_declared_profile": bool(support_valid),
                        "washer_metal_stress_mpa": None, "washer_metal_resistance_index": None,
                        "old_result_transferred_to_current_forces": False})
    require(len(records) == len({(r["state_tag"], r["axis_id"], r["end_role"]) for r in records}) == 2496
            and sum(r["own_end_M_signed_xyz_nmm"] is None for r in records) == 2400,
            "current end source census differs")
    return records, {"accepted_end_states": len(records), "unavailable_end_states": 208 * len(excluded),
                     "required_end_states": 104 * 2 * len(inventory), "current_scalar_moments_pending": 2400,
                     "current_continuous_moments_available": 96, "status_counts": dict(Counter(r["status"] for r in records))}


def build_contract(pins):
    order = read(ORDER)
    with AXES.open(newline="") as stream:
        axes = [r for r in csv.DictReader(stream) if r["fastener_type"] == "structural through-bolt"]
    require(len(axes) == 104 and sum(int(r["separate_washers"]) for r in axes) == 208, "working axis census differs")
    family_profiles = {"candidate_top_rail_quarter_8in_4": "top_rail_wide",
                       "candidate_top_side_5_16_4": "top_side_working", "retained_rail_front_4": "retained_15023",
                       "retained_rail_rear_4": "retained_15023", "retained_lumber_leg_4": "retained_15025"}
    mapping = {r["axis_id"]: {"family_id": r["family_id"], "profile_id": family_profiles.get(r["family_id"], "quarter"),
                               "working_shaft_diameter_mm": float(r["diameter_mm"])} for r in axes}
    counts = Counter()
    counts.update({profile: 2 * sum(r["profile_id"] == profile for r in mapping.values()) for profile in PROFILES})
    require(dict(counts) == {"quarter": 168, "top_rail_wide": 8, "top_side_working": 8,
                             "retained_15023": 16, "retained_15025": 8}, "profile quantities differ")
    require({r["item"]: r["quantity_required"] for r in order["washer_order_lines"]}
            == {"25NWUS": 168, "885522": 8, "2995": 8, "15023": 16, "15025": 8}, "working order profiles differ")
    retail = read(RETAIL / "checks.json")
    require(retail["status"] == "FINITE_RETAIL_WASHER_SUITE_HYPOTHESIS"
            and retail["setup_failure"] is None and retail["envelope_covers_all_48"] is True
            and retail["model"]["family"] == {k: PROFILES["top_rail_wide"][k] for k in
                ("head_radius_mm", "inner_radius_mm", "outer_radius_mm", "thickness_mm")}, "wider suite is not complete")
    suite_records = []
    for entry in retail["ends"]:
        value = read(artifact(RETAIL, entry["checks"]))
        require(value["failure"] is None and value["status"] == "FINITE_RETAIL_WASHER_HYPOTHESIS"
                and value["state"]["elastic_Fy_250MPa_hypothesis_exceeded"] is False,
                "wider suite has a failed or exceeded end")
        suite_records.append(value)
    require(len(suite_records) == 48, "wider suite end inventory differs")
    top_axes = sorted(axis for axis, row in mapping.items() if row["profile_id"] == "top_rail_wide")
    require(len(top_axes) == 4 and {x["source"]["axis_id"] for x in suite_records} == set(top_axes), "wider roles differ")
    finished_steps = {"base_rail_top": ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_rail_top.step",
                      **{f"top_outer_{side}_cleat": HERE.parent / f"top-corner-correction/top_outer_{side}_cleat.step"
                         for side in ("left", "right")}}
    require(all(path in pins for path in finished_steps.values()), "wider suite omits a finished receiver")
    return {"schema": "washer_working_profile_contract/v1", "status": "FROZEN_NUMERICAL_PROFILE_CONTRACT",
            "profiles": deepcopy(PROFILES), "hypotheses": deepcopy(HYPOTHESES), "axes": mapping,
            "counts": {"structural_axes": 104, "physical_washers": 208, "profile_quantities": dict(counts)},
            "top_rail_axes": top_axes, "top_rail_nominal_support": retail["nominal_support_inventory"],
            "top_rail_finished_steps": {body: {"path": key(path), "sha256": pins[path]}
                                        for body, path in finished_steps.items()},
            "historical_wider_suite": {"result": {"path": key(RETAIL / "checks.json"), "sha256": pins[RETAIL / "checks.json"]},
                "receipt": {"path": key(RETAIL / "source-pins.json"), "sha256": PINS[RETAIL / "source-pins.json"]},
                "completed_end_states": 48, "Fy250_exceedances": 0,
                "maximum_Fy250_index": max(x["state"]["elastic_proxy_over_assumed_Fy"] for x in suite_records),
                "force_basis_transferred": False},
            "other_profile_widening_solution_adopted": False,
            "profile_stiffness_laws": {"scalar_frame_axial": "original orthotropic two wood-column plus steel-stretch series law",
                                       "isolated_shaft_contact": "K20 wood and K10000 head rigid-annulus series contacts",
                                       "washer_plate": "existing isotropic Mindlin plate and unilateral normal springs"},
            "limits": ["Working dimensions/materials/pressing circles are conditional hypotheses, not measured product properties.",
                       "Wider top-rail profile changes four axial spring values and eight contact/plate profiles; no timber datum changes.",
                       "Historical all48 success is retained on its original forces; current plate comparisons remain pending.",
                       "Four top-side source-quarter-inch/shop5/16 mismatches remain explicit; source and working branches are distinct.",
                       "Saved nominal support does not qualify loaded shifts/tilts or complete hardware/joint resistance."], **FLAGS}


def prepare(output=None):
    pins = dict(PINS)
    bind(pins, Path(__file__).resolve(), sha(Path(__file__).resolve()))
    documentation = Path(__file__).with_suffix(".md")
    bind(pins, documentation, sha(documentation))
    for directory, receipt_name in ((RETAIL, "source-pins.json"), (MEANS, "receipt.json"), (BOLTS, "receipt.json")):
        packet(pins, directory, receipt_name)
    authenticate(pins)
    contract = build_contract(pins)
    update = joint_updates(contract, read(ROWS), read(TOP_GEOMETRY))
    contract["top_rail_outer_seat_points_mm"] = {r["axis_id"]: r["outer_seat_points_mm"] for r in update["changes"]}
    scalar = [json.loads(line) for line in (BOLTS / "scalar-bolts.jsonl").read_text().splitlines()]
    ends = [json.loads(line) for line in (MEANS / "washer-own-end-means.jsonl").read_text().splitlines()]
    action_receipt = HERE / "rawlocal/joint-frame-action-reconciliation/attempt03/receipt.json"
    require(pins.get(action_receipt) == "370dafc75a90967cc45e9888bdbd5610fa2df6930a5821d4cd52d01bae70904e",
            "current source action binding differs")
    inventory = read(action_receipt)["required_state_inventory"]
    records, counts = current_preflight(contract, scalar, ends, inventory)
    authenticate(pins)
    summary = {"schema": "washer_working_profile_preflight/v1", "status": "PREPARED_CURRENT_PROFILE_JOINS_NOT_METAL_COMPARISONS",
               "source_action_receipt": {"path": key(action_receipt), "sha256": pins[action_receipt]},
               "required_state_inventory": inventory, "counts": counts, **FLAGS}
    if output is not None:
        output = Path(output).resolve()
        require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate child of washer-working-profile-completion")
        require(all(not p.is_relative_to(output) for p in pins), "output contains a consumed source")
        output.mkdir(parents=True)
        (output / ".gitignore").write_text("*\n")
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        (output / "documentation.md.snapshot").write_bytes(documentation.read_bytes())
        for name, document in (("profile-contract.json", contract), ("joint-update.json", update), ("summary.json", summary)):
            (output / name).write_text(json.dumps(document, indent=2, allow_nan=False) + "\n")
        (output / "current-end-preflight.jsonl").write_text("".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in records))
        authenticate(pins)
        receipt = {"schema": "washer_working_profile_preparation_receipt/v1", "status": summary["status"],
                   "source_sha256": {key(p): h for p, h in sorted(pins.items())},
                   "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
                   "sources_authenticated_before_and_after": True, "counts": counts, **FLAGS}
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return {"summary": summary, "joint_update": update, "contract": contract, "source_bindings": len(pins)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="write a fresh source-only profile/port/end packet")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    require(args.prepare == (args.output is not None), "--prepare and --output must be supplied together")
    result = prepare(args.output)
    print(json.dumps({"status": result["summary"]["status"], "counts": result["summary"]["counts"],
                      "source_bindings": result["source_bindings"]}, sort_keys=True))


if __name__ == "__main__":
    main()

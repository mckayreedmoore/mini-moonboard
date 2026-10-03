"""Complete the finite washer reference worksheet from pinned fresh inputs.

Import is inert.  The parent owns the single serialized ``build(output)``
call; that call runs only the existing fine retail washer edge model for the
48 fresh top-rail end states.  Other rows are source joins and finite algebra.
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-reference-completion"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]

EXPORT = HERE / "rawlocal/knee-bridge-response/attempt02"
SUMMARY, EXPORT_RECEIPT, DEMANDS = (EXPORT / name for name in
                                    ("summary.json", "receipt.json", "global-demands.jsonl"))
ASSESSMENT = HERE / "rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"
RESPONSE = FRAME.with_name("response.npz")
REGISTER = HERE / "rawlocal/working-joint-register/attempt03/register.json"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
CORNER = HERE / "rawlocal/knee-bridge-corner-replay/attempt01/checks.json"
CORNER_RECEIPT = CORNER.with_name("receipt.json")
CORNER_TIMBER = HERE / "rawlocal/corner-timber-sections/attempt02/checks.json"
SHAFT_DIR = HERE / "rawlocal/knee-bridge-continuous-shafts/attempt02"
SHAFT_SUITE, SHAFT_RECEIPT = SHAFT_DIR / "suite.json", SHAFT_DIR / "receipt.json"
CENTRAL = HERE / "rawlocal/central-seat-transfer/preparation-attempt01/contract.json"
OLD_RETAIL = HERE / "rawlocal/retail-washer-suite/attempt01-fine/checks.json"
RETAIL_CSV = HERE / "bolted-replay-results/remaining-attempt02/washer-reference-states.csv"
EDGE = HERE / "upper-right-washer-edge.py"
FLEXURE = HERE / "upper-right-washer-flexure.py"
MATERIALS = ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json"
UPPER_SUPPORT = ROOT / "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/seats.json"
REMAINING_SUPPORT = Path("/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json")
RETAINED_SUPPORT = HERE.parent / "retained-washer-support-attempt02/support.json"
LOWER_SUPPORT = HERE / "rawlocal/lower-service-washers/attempt01/result.json"
LEFT_KNEE_SUPPORT = (ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
                     / "current-corner-washer-wood-support-attempt01/support-screen.json")
LEFT_KNEE_PINS = LEFT_KNEE_SUPPORT.with_name("source-pins.json")
KNEE_GEOMETRY = HERE / "rawlocal/knee-bridge-geometry/attempt01/manifest.json"
KNEE_GEOMETRY_INPUTS = KNEE_GEOMETRY.with_name("inputs.json")
WORKING = HERE / "rawlocal/knee-bridge-working-package/attempt02/manifest.json"

PINS = {
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    FRAME: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    SUMMARY: "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    EXPORT_RECEIPT: "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    DEMANDS: "f0d9bb8a8a25775a2571692183860b209708111b089f16538f7eab5d9adbe4c3",
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    INTEGRATION: "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    CORNER: "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976",
    CORNER_RECEIPT: "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    CORNER_TIMBER: "8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813",
    SHAFT_SUITE: "ec3b5bbc6d2c80c38bfcbe5877a4ea9ca6ac89f926f5f22fa799bfb9c76a701f",
    SHAFT_RECEIPT: "5496190db02ec1ed8fca6ced59f7538526503ab6735f946e651394ab225d1ffa",
    CENTRAL: "e430c138f0e1fb4eacda278fa535d3e14400fcff3514f4a81d3a5f7fc3ac6646",
    OLD_RETAIL: "3e2dee327dbd81d8584955de3c4918c9acc695b0386fa46abd568ba767c64f74",
    RETAIL_CSV: "43da5dab2bc0ed8761959767aecec466a645a3832509c7162e494cc4da17f35b",
    EDGE: "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61",
    FLEXURE: "782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    UPPER_SUPPORT: "4463f581490842095224afefd0b355428f82668f039b2e6035dfe4ec879c96c1",
    REMAINING_SUPPORT: "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3",
    RETAINED_SUPPORT: "72ecad11051f7a72695f83561bb12503bfd79a44d3c3f6eeac2de476e3bc3448",
    LOWER_SUPPORT: "cea8ed7447fd3b73a50833bd3cbe67310917e7d37e02b1d1fcb59489997997db",
    LEFT_KNEE_SUPPORT: "0fa052decc7f56d34368a09d3e25b15a2d32d97445d14fddb57d97e7487fd304",
    LEFT_KNEE_PINS: "b4c01bf277ca36a134f2be0a7fdd54e8e720a473b7ac12f05bc75fabd67363c9",
    KNEE_GEOMETRY: "254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147",
    KNEE_GEOMETRY_INPUTS: "25c3a49825d898815e4311c95ea0f16be1bcf415d9983d496feb0371d157d965",
    WORKING: "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
}

GENERIC_INNER_MM, GENERIC_OUTER_MM = 8.3058 / 2, 18.4658 / 2
GENERIC_AREA_MM2 = math.pi * (GENERIC_OUTER_MM**2 - GENERIC_INNER_MM**2)
RAIL_FAMILY = {"inner_radius_mm": 4.1529, "outer_radius_mm": 12.7,
               "head_radius_mm": 5.0, "thickness_mm": 2.5}
FC_PERP_MPA = 625 * 0.006894757293168361
FC_PARALLEL_MPA = 1350 * 0.006894757293168361
PROPOSAL_FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
                  "physical_release": False, "fabrication_release": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def display(path):
    path = Path(path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def bind(pins, path, digest):
    path, digest = Path(path).resolve(), str(digest)
    require(path not in pins or pins[path] == digest, "conflicting pin: " + display(path))
    pins[path] = digest


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, "source changed: " + display(path))


def load_module(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "pinned washer method unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def dot(a, b):
    return math.fsum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def normalized_supports(pins, axis_map):
    remaining, upper, retained, lower, left = map(read, (
        REMAINING_SUPPORT, UPPER_SUPPORT, RETAINED_SUPPORT, LOWER_SUPPORT, LEFT_KNEE_SUPPORT))
    geometry_manifest = read(KNEE_GEOMETRY)
    inputs = read(KNEE_GEOMETRY_INPUTS)
    working = read(WORKING)

    require(geometry_manifest["schema"] == "knee-bridge-proposal-geometry/v1"
            and geometry_manifest["status"] == "PROPOSAL_GEOMETRY_EXPORTED"
            and set(geometry_manifest["bodies"]) == {"knee_outer_left_spine", "knee_outer_right_spine"}
            and left["source_pins_sha256"] == PINS[LEFT_KNEE_PINS],
            "pinned proposal geometry or left-knee support source identity differs")

    effective = {row["body"]: row["effective_proposal_step"]
                 for row in working["geometry"]["effective_members"]}
    for body, row in geometry_manifest["bodies"].items():
        name = body + ".proposal.step"
        proposal = row["exports"][name]
        current = effective.get(body)
        require(current is not None and current["path"].endswith("/" + name)
                and current["sha256"] == proposal["sha256"],
                "proposal STEP differs between pinned geometry receipts: " + body)
        original = inputs["bodies"][body]["original_geometry"]["finished_step_binding"]
        require(row["source_step_binding"]["path"] == original["path"]
                and row["source_step_binding"]["file_sha256"] == original["file_sha256"],
                "proposal geometry source STEP binding differs: " + body)
    support = {}

    def add(axis, member, role, source, source_digest, area, fraction, step_path, step_digest,
            evidence, seat_point=None, axis_dir=None):
        key = (axis, member)
        row = {"axis_id": axis, "member": member, "role": role, "source": display(source),
               "source_sha256": source_digest, "saved_supported_area_mm2": area,
               "saved_support_fraction": fraction, "support_evidence": evidence,
               "support_step_path": str(step_path) if step_path else None,
               "support_step_sha256": step_digest, "seat_point_xyz_mm": seat_point,
               "axis_direction_global_xyz": axis_dir}
        if key in support:
            prior = support[key]
            require(prior["role"] == role and math.isclose(float(prior["saved_supported_area_mm2"] or 0),
                    float(area or 0), abs_tol=1e-7), "overlapping seat inventories disagree: " + str(key))
            prior["corroborating_sources"].append(row)
            return
        row["corroborating_sources"] = []
        support[key] = row

    def path_pin_map(document):
        return {member: (binding["path"], binding["sha256"])
                for member, binding in document.get("finished_step_pins", {}).items()}

    remaining_steps = path_pin_map(remaining)
    for row in remaining["seats"]:
        area_case = next(x for x in row["nominal"] if x["scenario"] == "plain_minimum_area")
        measures = area_case["inward_measurements"]
        fraction = min(float(x["support_fraction"]) for x in measures)
        area = min(float(x["supported_area_mm2"]) for x in measures)
        step_path, step_digest = remaining_steps.get(row["member"], (None, None))
        add(row["axis_id"], row["member"], row["role"], REMAINING_SUPPORT, PINS[REMAINING_SUPPORT],
            area, fraction, step_path, step_digest,
            {"inventory": "remaining-seat plain_minimum_area", "screen_pass": row.get("geometry_screen_pass"),
             "scenario_supported": area_case.get("supported"), "source_status": remaining.get("status")},
            row.get("point_xyz_mm"), row.get("axis_global_xyz"))

    for row in upper["geometry_seats"]:
        case = row["scenario_support"]["catalog_minimum_area"]
        member_source = row["member_source_geometry"]
        ideal = GENERIC_AREA_MM2
        fraction = float(case["minimum_inward_support_fraction"])
        step = member_source.get("finished_step")
        add(row["axis_id"], row["owner_member_id"], row["seat_role"], UPPER_SUPPORT,
            PINS[UPPER_SUPPORT], ideal * fraction, fraction, step,
            member_source.get("finished_step_sha256"),
            {"inventory": "upper-block catalog_minimum_area", "support_status": case["support_status"],
             "helper_status": case["helper_status"], "depths_mm": case["depths_mm"]},
            row.get("seat_point_xyz_mm"), row.get("seat_inward_normal_global_xyz"))

    for row in retained["seats"]:
        annulus = row["nominal_concentric_annulus_mm"]
        fractions = [float(x["nominal_concentric_supported_fraction"]) for x in row["depth_results"]]
        fraction = min(fractions)
        step = row["support_geometry_step"]
        add(row["axis_id"], row["member"], row["role"], RETAINED_SUPPORT,
            PINS[RETAINED_SUPPORT], float(annulus["area"]) * fraction, fraction,
            step["path"], step["sha256"],
            {"inventory": "retained saved STEP annulus", "washer_part": row["washer_part"],
             "probe_depths_mm": [x["probe_depth_mm"] for x in row["depth_results"]]},
            None, None)
        support[(row["axis_id"], row["member"])]["ideal_annulus_area_mm2"] = float(annulus["area"])

    lower_rows = { (row["axis_id"], row["member"]): row for row in lower["endpoints"] }
    for key, row in lower_rows.items():
        binding = row["current_finished_step_binding"]
        add(row["axis_id"], row["member"], row["role"], LOWER_SUPPORT,
            PINS[LOWER_SUPPORT], GENERIC_AREA_MM2 if row["full_nominal_annulus_supported"] else 0.0,
            1.0 if row["full_nominal_annulus_supported"] else 0.0,
            binding["path"], binding["file_sha256"],
            {"inventory": "lower service washer result", "full_nominal_annulus_supported": row["full_nominal_annulus_supported"],
             "support_pointer": row["support_pointer"], "material_reference_pointer": row["material_reference_pointer"]},
            row.get("point_xyz_mm"), row.get("axis_global_xyz"))

    for row in left["seats"]:
        case = next(x for x in row["catalog_annulus_support_cases"]
                    if x["dimensional_case"] == "minimum_area_dimensional_envelope")
        add(row["axis_id"], row["receiver_member_id"], row["seat_role"].replace("_washer_seat", ""),
            LEFT_KNEE_SUPPORT, PINS[LEFT_KNEE_SUPPORT],
            float(case["wood_face_intersection_area_mm2"]), float(case["supported_fraction"]),
            row["receiver_step_path"], row["receiver_step_sha256"],
            {"inventory": "left knee dimensional-envelope support screen",
             "dimensional_case": case["dimensional_case"],
             "full_dimensional_envelope_annulus_supported_in_cad": row["full_dimensional_envelope_annulus_supported_in_cad"]},
            row["seat_center_global_xyz_mm"], row["expected_outward_wood_normal_global"])

    # The lower-service result independently refines eight of the remaining-seat rows.
    for key in lower_rows:
        require(key in support, "lower-service duplicate missing from remaining-seat inventory")
        expected = next(r for r in remaining["seats"] if (r["axis_id"], r["member"]) == key)
        area = min(float(x["supported_area_mm2"]) for x in
                   next(x for x in expected["nominal"] if x["scenario"] == "plain_minimum_area")["inward_measurements"])
        require(math.isclose(area, support[key]["saved_supported_area_mm2"], abs_tol=1e-7),
                "lower/remaining saved support areas differ")

    require(len(support) == 208, "saved exterior seat union differs from 104 global axes")
    geom = inputs["bodies"]
    for key, row in support.items():
        saved_path, saved_sha = row["support_step_path"], row["support_step_sha256"]
        current = effective.get(row["member"])
        applicability, reason, analytic_clearance = None, "effective_STEP_binding_unproved", None
        if current:
            bind(pins, ROOT / current["path"], current["sha256"])
        if current and saved_path and saved_sha and current["path"] == saved_path and current["sha256"] == saved_sha:
            applicability, reason = True, "saved_support_matches_effective_STEP"
        elif row["member"] in geom and row["member"].endswith("_spine") and current:
            source_body = geom[row["member"]]
            original = source_body["original_geometry"]
            new_axes = source_body["new_axes"]
            support_axis = row["axis_direction_global_xyz"]
            if support_axis is None:
                support_axis = axis_map[row["axis_id"]]["outer_tie"]["direction_global_xyz"]
                row["axis_direction_source"] = display(REGISTER)
                row["axis_direction_source_sha256"] = PINS[REGISTER]
            point = row["seat_point_xyz_mm"]
            bounds = next((x["source_bounds_xyz_mm"] for x in working["geometry"]["effective_members"]
                           if x["body"] == row["member"]), None)
            original_binding = original.get("finished_step_binding", {})
            proposal_step = current
            width_mm = float(original["width_depth_mm"][0])
            depth_mm = 0.1
            bore_radius = max(float(x["radius_mm"]) for x in new_axes)
            clearance = width_mm / 2 - bore_radius - depth_mm
            outer_x_face = (bounds is not None and point is not None and support_axis is not None
                            and abs(abs(float(support_axis[0])) - 1.0) <= 1e-8
                            and abs(float(support_axis[1])) <= 1e-8 and abs(float(support_axis[2])) <= 1e-8
                            and min(abs(float(point[0]) - float(bounds[0])),
                                    abs(float(point[0]) - float(bounds[1]))) <= 0.002)
            proposal_is_bound = (proposal_step["path"].endswith(row["member"] + ".proposal.step")
                                 and sha(ROOT / proposal_step["path"]) == proposal_step["sha256"])
            original_is_bound = (saved_path == original_binding.get("path")
                                 and saved_sha == original_binding.get("file_sha256"))
            axes_are_transverse = len(new_axes) == 2 and all(
                int(x["removed_interval_axis"]) == 1 and math.isclose(float(x["radius_mm"]), 3.75, abs_tol=1e-9)
                for x in new_axes)
            if (outer_x_face and proposal_is_bound and original_is_bound and axes_are_transverse
                    and math.isclose(width_mm, 38.1, abs_tol=1e-6) and clearance > 0
                    and float(row["saved_support_fraction"] or 0) >= 1 - 1e-8):
                applicability, reason, analytic_clearance = True, "pinned_proposal_outer_X_land_clearance", clearance
        if row["support_evidence"].get("scenario_supported") is False:
            applicability, reason = False, "saved_minimum_area_scenario_not_supported"
        row["modeled_support_applicability"] = applicability
        row["support_applicability_basis"] = reason
        row["added_spine_bore_clearance_mm"] = analytic_clearance
        if saved_path and saved_sha:
            step = Path(saved_path)
            bind(pins, ROOT / step if not step.is_absolute() else step, saved_sha)
    return support, effective, inputs, working, remaining, upper, retained, lower, left


def csv_reference_map(pins, axis_map):
    with RETAIL_CSV.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 1104 and len({(r["case_id"], r["axis_id"], r["member"]) for r in rows}) == 1104,
            "historical area/reference worksheet census differs")
    area_by_axis, material = {}, {}
    for row in rows:
        # Deliberately consume no old force, pressure, or applicability values.
        area = row["ideal_full_annulus_area_mm2"].strip()
        if area:
            area_by_axis.setdefault(row["axis_id"], set()).add(float(area))
        ref = row["wood_reference_mpa"].strip()
        route = row["wood_reference_route"].strip()
        if ref:
            material.setdefault((row["axis_id"], row["member"]), set()).add((route, float(ref)))
    require(all(len(values) == 1 for values in area_by_axis.values()), "historical annulus areas vary by case")
    require(all(len(values) == 1 for values in material.values()), "historical material references vary by case")
    result = {axis: next(iter(values)) for axis, values in area_by_axis.items()}
    refs = {key: next(iter(values)) for key, values in material.items()}
    # The older worksheet omitted the top and upper-service axes. Recover only
    # normal-to-grain or parallel-to-grain base references from the current
    # pinned material orientation; an oblique or missing orientation stays null.
    bind(pins, MATERIALS, PINS[MATERIALS])
    members = {row["member_id"]: row for row in read(MATERIALS)["members"]}
    for axis_id, identity in axis_map.items():
        direction = identity["outer_tie"]["direction_global_xyz"]
        for member in identity["receivers"]:
            key = (axis_id, member)
            if key in refs:
                continue
            grain = members.get(member, {}).get("source_proposed_longitudinal_grain_global_xyz")
            if grain is None or dot(grain, grain) <= 0:
                refs[key] = ("GRAIN_REFERENCE_UNAVAILABLE", None)
                continue
            cosine = abs(dot(direction, grain)) / math.sqrt(dot(direction, direction) * dot(grain, grain))
            if cosine <= 1e-8:
                refs[key] = ("PERPENDICULAR_BASE_REFERENCE", FC_PERP_MPA)
            elif abs(cosine - 1.0) <= 1e-8:
                refs[key] = ("PARALLEL_BASE_REFERENCE", FC_PARALLEL_MPA)
            else:
                refs[key] = ("OBLIQUE_GRAIN_REFERENCE_UNAVAILABLE", None)
    return result, refs


def geometry_and_fresh_inputs(pins):
    summary, export_receipt = read(SUMMARY), read(EXPORT_RECEIPT)
    frame, assessment, register, integration = map(read, (FRAME, ASSESSMENT, REGISTER, INTEGRATION))
    require(summary["schema"] == "knee-bridge-fresh-global-force-census/v1"
            and summary["status"] == "FRESH_GLOBAL_DEMANDS_EXPORTED"
            and summary["source_comparison_sha256"] == PINS[FRAME]
            and summary["census"]["global_structural_bolt_states"] == 624
            and summary["census"]["proposal_bolts"] == 108
            and summary["census"]["new_internal_allocations_separate"] == 24,
            "fresh 104-axis export scope differs")
    require(export_receipt["source_sha256"] == summary["source_sha256"]
            and export_receipt["output_sha256"]["summary.json"] == PINS[SUMMARY]
            and export_receipt["output_sha256"]["global-demands.jsonl"] == PINS[DEMANDS],
            "fresh force-export receipt differs")
    for path, expected in ((ASSESSMENT, PINS[ASSESSMENT]), (FRAME, PINS[FRAME]),
                           (RESPONSE, PINS[RESPONSE]), (REGISTER, PINS[REGISTER]),
                           (INTEGRATION, PINS[INTEGRATION])):
        relative = path.relative_to(ROOT).as_posix()
        require(summary["source_sha256"].get(relative) == expected,
                "fresh force export consumed a different source: " + relative)
    require(frame["schema"] == "coupled_two_receiver_frame_clearance/v1"
            and frame["response_sha256"] == PINS[RESPONSE]
            and frame["source_climber_weight_lb"] == 250
            and frame["climber_load_scale"] == frame["horizontal_load_scale"] == 1.0,
            "fresh frame response identity differs")
    require(assessment["operator_ready"] is True and assessment["case_ids"] == CASES,
            "fresh gravity assessment incomplete")
    require(register["case_ids"] == CASES and len(register["axes"]) == 104,
            "current 104-axis register differs")
    for name, digest in export_receipt["output_sha256"].items():
        if name in {"summary.json", "global-demands.jsonl", "producer.py.snapshot", ".gitignore"}:
            bind(pins, EXPORT / name, digest)
    demands = [json.loads(line) for line in DEMANDS.read_text().splitlines()]
    bolts = [r for r in demands if r["kind"] == "structural_bolt"]
    keyed = {(r["case_id"], r["axis_id"]): r for r in bolts}
    require(len(bolts) == 624 and len(keyed) == 624
            and set(keyed) == {(case, axis["axis_id"]) for case in CASES for axis in register["axes"]},
            "fresh signed global force row ownership differs")
    axis_map = {row["axis_id"]: row for row in register["axes"]}
    allocation_index = integration["proposed_internal_allocations"]
    require(allocation_index["file"] == "proposed-internal-allocations.jsonl"
            and allocation_index["record_count"] == 24 and allocation_index["end_count"] == 48,
            "separate internal bridge allocation descriptor differs")
    allocation_path = INTEGRATION.parent / allocation_index["file"]
    bind(pins, allocation_path, allocation_index["sha256"])
    require(sha(allocation_path) == allocation_index["sha256"],
            "separate internal bridge allocation bytes differ")
    allocations = [json.loads(line) for line in allocation_path.read_text().splitlines()]
    internal_axes = {row["canonical_axis_id"] for row in integration["proposed_internal_bolt_axes"]}
    require(len(internal_axes) == 4
            and len(allocations) == allocation_index["record_count"]
            and {(row["case_id"], row["canonical_axis_id"]) for row in allocations}
                == {(case, axis) for case in CASES for axis in internal_axes}
            and all(row["axis_id"] == row["canonical_axis_id"] and len(row["ends"]) == 2
                    for row in allocations)
            and sum(len(row["ends"]) for row in allocations) == allocation_index["end_count"],
            "separate internal bridge allocation census differs")
    integration = {**integration, "consumed_internal_allocation_rows": allocations}
    return summary, frame, assessment, register, integration, demands, keyed, axis_map


def make_support_rows(pins, support, axis_map, keyed, area_by_axis, material_refs):
    corner_ids = {axis for axis in axis_map if axis.startswith(("top_outer/", "bottom_outer/"))}
    retail_ids = {axis for axis in corner_ids if axis.startswith("top_outer/") and "/rail_" in axis}
    continuous_ids = {f"knee_outer_{side}_side_{number}"
                      for side in ("left", "right") for number in (1, 2)}
    require(len(corner_ids) == 16 and len(retail_ids) == 4 and len(continuous_ids) == 4,
            "corner or continuous axis partition differs")
    global_ids = set(axis_map)
    selected = global_ids - corner_ids
    ordinary_ids = selected - continuous_ids
    require(len(selected) == 88 and len(ordinary_ids) == 84,
            "88-bolt outside-corner partition differs")
    rows = []
    for axis in sorted(ordinary_ids):
        identity = axis_map[axis]
        source_members = set(keyed[(CASES[0], axis)]["receivers"])
        ends = [value for (candidate, _member), value in support.items() if candidate == axis]
        require(len(ends) == 2 and {r["member"] for r in ends} == source_members,
                "physical exterior end/support join differs: " + axis)
        for case in CASES:
            force = keyed[(case, axis)]
            require(set(force["receivers"]) == source_members, "fresh receiver ownership changed: " + axis)
            for saved in sorted(ends, key=lambda r: (r["role"], r["member"])):
                member = saved["member"]
                area = area_by_axis.get(axis, saved.get("ideal_annulus_area_mm2", GENERIC_AREA_MM2))
                if axis in area_by_axis:
                    require(math.isclose(area, GENERIC_AREA_MM2, abs_tol=1e-7, rel_tol=0),
                            "saved historical ideal washer annulus differs from this washer family")
                route, reference = material_refs.get((axis, member), ("REFERENCE_UNAVAILABLE", None))
                require(area > 0, "ideal washer area missing: " + axis)
                tension = float(force["signed_axial_n"])
                pressure = max(tension, 0.0) / area
                app = saved["modeled_support_applicability"]
                supported_area = saved["saved_supported_area_mm2"] if app is True else None
                supported_pressure = max(tension, 0.0) / supported_area if supported_area else None
                ref_ratio = pressure / reference if reference and reference > 0 else None
                supported_ratio = supported_pressure / reference if supported_pressure is not None and reference else None
                tie = identity["outer_tie"]
                require(tie["role"] == "physical_bolt_outer_seat_tension"
                        and tie["row_id"].startswith(axis + "/"),
                        "fresh signed tension is not owned by the registered outer tie: " + axis)
                row = {
                    "scope": "outside_corner_axial_reference", "case_id": case, "axis_id": axis,
                    "end_role": saved["role"], "receiver_member": member,
                    "fresh_force_source": "knee-bridge-response/attempt02/global-demands.jsonl",
                    "fresh_source_row_id": tie["row_id"],
                    "fresh_force_source_sha256": PINS[DEMANDS],
                    "fresh_signed_T_n": tension, "fresh_interface_lateral_max_n": force["peak_interface_lateral_n"],
                    "own_end_M_magnitude_nmm": None, "own_end_M_signed_xyz_nmm": None,
                    "local_end_moment_status": "UNKNOWN_NOT_SET_TO_ZERO",
                    "ideal_annulus_area_mm2": area, "ideal_annulus_mean_pressure_mpa": pressure,
                    "wood_reference_route": route, "wood_reference_mpa": reference,
                    "ideal_mean_over_wood_reference": ref_ratio,
                    "saved_supported_area_mm2": saved["saved_supported_area_mm2"],
                    "modeled_support_applicability": app,
                    "support_applicability_basis": saved["support_applicability_basis"],
                    "applicable_supported_area_mm2": supported_area,
                    "supported_mean_pressure_mpa": supported_pressure,
                    "supported_mean_over_wood_reference": supported_ratio,
                    "support_source": saved["source"], "support_source_sha256": saved["source_sha256"],
                    "support_step_path": saved["support_step_path"],
                    "support_step_sha256": saved["support_step_sha256"],
                    "added_spine_bore_clearance_mm": saved["added_spine_bore_clearance_mm"],
                    "metal_simultaneous_TM_status": "NOT_COMPUTABLE_LOCAL_MOMENT_UNKNOWN",
                    "metal_actual_stress_mpa": None, "metal_yield_mpa": None,
                    "metal_capacity_n": None, "central_ring_trial_q0_mpa": None,
                    "central_ring_trial_qmax_mpa": None, "central_trial_yield_floor_mpa": None,
                    "central_trial_Fc_perp_ratio": None,
                }
                rows.append(row)
    return rows, corner_ids, retail_ids, continuous_ids


def central_trials(contract, keyed, axis_map):
    axis_id, body = contract["axis_id"], contract["body"]
    require(axis_id == "center_principal_right_2" and body == "base_principal_center_right",
            "central supported-seat identity differs")
    source_axis = axis_map[axis_id]
    tie = source_axis["outer_tie"]
    seat = [float(x) for x in contract["seat_point_global_xyz_mm"]]
    patch = contract["credited_transfer_patch"]
    area, second = float(patch["area_mm2"]), float(patch["second_moment_yy_zz_mm4"])
    require(patch["full_washer_annulus_credited"] is False
            and patch["unsupported_crescent_credited"] is False
            and math.isclose(area, 24.358092307328498, abs_tol=1e-12)
            and math.isclose(second, 257.2615141448928, abs_tol=1e-10),
            "central ring patch changed")
    results = {}
    for case in CASES:
        force_row = keyed[(case, axis_id)]
        force = [-float(force_row["signed_axial_n"]) * float(x)
                 for x in tie["direction_global_xyz"]]
        lever = [float(a) - float(b) for a, b in zip(tie["point_mm"], seat, strict=True)]
        moment = cross(lever, force)
        require(max(abs(force[1]), abs(force[2]), abs(moment[0])) <= 1e-9,
                "central normal-only trial cannot carry fresh transverse wrench")
        q0 = force[0] / area
        qy, qz = -moment[2] / second, moment[1] / second
        excursion = 5.0 * math.hypot(qy, qz)
        qmin, qmax = q0 - excursion, q0 + excursion
        require(qmin >= 0, "central affine compression trial is not admissible")
        results[case] = {
            "axis_id": axis_id, "receiver_member": body, "end_role": "nut",
            "fresh_force_source": "knee-bridge-response/attempt02/global-demands.jsonl",
            "fresh_source_row_id": tie["row_id"], "fresh_force_source_sha256": PINS[DEMANDS],
            "case_id": case, "fresh_signed_T_n": float(force_row["signed_axial_n"]),
            "derived_force_on_saved_seat_xyz_n": force, "derived_moment_about_saved_seat_xyz_nmm": moment,
            "derived_moment_status": "LINE_OF_ACTION_FROM_FRESH_TIE_AND_SAVED_SEAT",
            "line_of_action_point_global_xyz_mm": tie["point_mm"],
            "saved_seat_point_global_xyz_mm": seat, "credited_patch_area_mm2": area,
            "credited_patch_second_moment_mm4": second,
            "trial_pressure_q0_qy_qz_mpa_or_mpa_per_mm": [q0, qy, qz],
            "trial_pressure_min_max_mpa": [qmin, qmax],
            "wood_mean_over_conditional_Fc_perp": q0 / FC_PERP_MPA,
            "required_hypothetical_washer_yield_mpa": qmax,
            "actual_washer_yield_mpa": None, "actual_washer_capacity_n": None,
            "limits": ["Centered normal branch only; this is not a recovered complete local nut wrench.",
                       "No crescent or full washer annulus is credited; no actual yield or capacity is assigned."],
        }
    return results


def retail_sources(pins, corner, old_suite, corner_timber, support, effective, material_refs, keyed, axis_map):
    require(old_suite["schema"] == "retail_washer_48_end_suite/v1"
            and old_suite["model"]["family"] == RAIL_FAMILY
            and old_suite["model"]["resolution"] == {
                "inside_elements": 4, "outside_elements": 12, "fourier_order": 8,
                "angles": 128, "unknowns": 1142}
            and old_suite["model"]["E_mpa_hypothesis"] == 200000.0
            and old_suite["model"]["nu_hypothesis"] == 0.3
            and old_suite["model"]["Kwood_mpa_per_mm_hypothesis"] == 20.0
            and old_suite["model"]["Khead_mpa_per_mm_hypothesis"] == 10000.0
            and old_suite["model"]["Fy_mpa_hypothesis"] == 250.0,
            "fixed fine retail washer reference settings differ")
    corner_sources = corner["fresh_load_sources"]
    require(corner["schema"] == "knee_bridge_original_corner_first_order_replay/v1"
            and corner["status"] == "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES"
            and corner["failure"] is None and corner["case_ids"] == CASES
            and corner_sources[display(ASSESSMENT)] == PINS[ASSESSMENT]
            and corner_sources[display(FRAME)] == PINS[FRAME]
            and corner_sources[display(RESPONSE)] == PINS[RESPONSE],
            "fresh top-corner transfer identity differs")
    model_input = load_module(FLEXURE, "washer_completion_flexure")
    edge = load_module(EDGE, "washer_completion_edge")
    model_input.FAMILIES = {**model_input.FAMILIES, "rail": dict(RAIL_FAMILY)}
    settings = old_suite["model"]
    source_rows, support_refs = [], {}
    for state in corner["states"]:
        if state["level"] != "top":
            continue
        host = state["hosts"]["base_rail_top"]
        for bolt in host["state"]["bolts"]:
            axis = bolt["axis_id"]
            require(axis.startswith("top_outer/") and any(key[0] == axis for key in support),
                    "fresh retail rail axis lacks saved support reference")
            require(len(bolt["end_contacts"]) == 2 and len(bolt["end_moment_vectors_in_transverse_basis_nmm"]) == 2,
                    "fresh retail own-end contact census differs")
            seats_by_role = {r["end"]: r for r in host["wood_seat_recovery"] if r["axis_id"] == axis}
            for index, (role, seat_role) in enumerate((("host", "host_head"), ("cleat", "cleat_nut"))):
                contact = bolt["end_contacts"][index]
                moment_vector = [float(x) for x in bolt["end_moment_vectors_in_transverse_basis_nmm"][index]]
                magnitude = float(contact["moment_nmm"])
                require(math.isclose(math.hypot(*moment_vector), magnitude, abs_tol=1e-7, rel_tol=0),
                        "retail signed own-end moment and magnitude differ")
                seat = seats_by_role.get(seat_role)
                require(seat is not None and len(seat["nominal_outer_wood_seat_xyz_mm"]) == 3,
                        "physical top-retail seat datum missing")
                key = (axis, role)
                saved = old_suite["nominal_support_inventory"].get(axis + "/" + role)
                require(saved is not None, "old retail nominal support record missing")
                receiver = saved["receiver"]
                current = effective.get(receiver)
                binding = saved.get("finished_step_binding")
                if role == "cleat":
                    side = "left" if "_left_" in receiver else "right"
                    require(saved["saved_geometry"] == corner_timber["geometry"][side]
                            and saved["geometry_source_sha256"] == PINS[CORNER_TIMBER],
                            "top cleat saved geometry differs from pinned corrected section")
                    step_path = next(path for path in corner_timber["source_sha256"]
                                     if path.endswith(f"top_outer_{side}_cleat.step"))
                    step_sha = corner_timber["source_sha256"][step_path]
                    bind(pins, ROOT / step_path, step_sha)
                else:
                    require(binding is not None, "top rail host support lacks exact STEP binding")
                    step_path = binding["path"]
                    step_sha = binding.get("sha256", binding.get("file_sha256"))
                support_applies = bool(current and current["path"] == step_path and current["sha256"] == step_sha)
                saved_seat = saved["seat_xyz_mm"]
                fresh_seat = seat["nominal_outer_wood_seat_xyz_mm"]
                require(len(saved_seat) == len(fresh_seat) == 3
                        and all(math.isclose(float(a), float(b), abs_tol=0.002, rel_tol=0)
                                for a, b in zip(saved_seat, fresh_seat, strict=True)),
                        "saved retail land datum differs from fresh physical end")
                support_row = support_refs.get(key)
                if support_row is None:
                    support_row = {"axis_id": axis, "retail_role": role, "receiver": receiver,
                                   "saved_area_mm2": float(saved["nominal_supported_annulus_area_mm2"]),
                                   "support_applicability": True if support_applies else None,
                                   "support_basis": "exact_effective_STEP" if support_applies else "saved_retail_geometry_only",
                                   "support_source_sha256": PINS[OLD_RETAIL],
                                   "support_step_path": step_path, "support_step_sha256": step_sha}
                    support_refs[key] = support_row
                else:
                    require(support_row["receiver"] == receiver
                            and support_row["support_applicability"] is (True if support_applies else None),
                            "retail support binding differs between six fresh states")
                tension = float(bolt["compatible_T_n"])
                material = material_refs.get((axis, receiver))
                wood_route, wood_reference = material if material is not None else ("REFERENCE_UNAVAILABLE", None)
                global_tie = axis_map[axis]["outer_tie"]
                require(global_tie["role"] == "physical_bolt_outer_seat_tension",
                        "top retail axis lacks registered global outer tie")
                global_force = keyed[(state["case_id"], axis)]
                source = {
                    "state_id": f"{state['case_id']}/{axis}/{role}", "case_id": state["case_id"],
                    "side": state["side"], "axis_id": axis, "end_role": role,
                    "axial_tie_row_id": global_tie["row_id"],
                    "compatible_T_source_row_id": (f"{state['case_id']}/{axis}/hosts/base_rail_top/"
                                                   f"state/bolts[axis={axis}]/compatible_T_n"),
                    "global_outer_tie_T_n": float(global_force["signed_axial_n"]),
                    "global_outer_tie_source_sha256": PINS[DEMANDS], "family": "rail",
                    "T_n": tension, "M_magnitude_nmm": magnitude,
                    "eccentricity_M_over_T_mm": magnitude / tension if tension > 0 else None,
                    "source_signed_M_vector_in_pair_basis_nmm": moment_vector,
                    "source_signed_slope_vector_in_pair_basis_rad": bolt["end_slope_vectors_rad"][index],
                    "source_moment_on_beam_xyz_nmm": contact["moment_on_beam_xyz_nmm"],
                    "source_signed_pressure_frame_columns_xyz": seat["signed_pressure_frame_columns_xyz"],
                    "source_bolt_axis_head_to_nut_xyz": bolt["bolt_axis_head_to_nut_xyz"],
                    "nominal_outer_wood_seat_xyz_mm": seat["nominal_outer_wood_seat_xyz_mm"],
                    "saved_rigid_contact": contact,
                }
                source_rows.append({"source": source, "support": support_row,
                                    "ideal_area_mm2": math.pi * (RAIL_FAMILY["outer_radius_mm"]**2
                                                                  - RAIL_FAMILY["inner_radius_mm"]**2),
                                    "wood_reference_route": wood_route,
                                    "wood_reference_mpa": wood_reference})
    require(len(source_rows) == 48 and len({r["source"]["state_id"] for r in source_rows}) == 48,
            "fresh retail own-end census differs")
    # Pin exact helper/method source bytes; no old producer loader is called.
    bind(pins, EDGE, PINS[EDGE])
    bind(pins, FLEXURE, PINS[FLEXURE])
    return edge, model_input, source_rows, support_refs, settings


def continuous_rows(pins, suite, receipt, support):
    require(suite["schema"] == "knee_bridge_continuous_shaft_fresh_suite/v1"
            and suite["status"] == "COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS"
            and suite["all24_nominal_completed"] is True
            and suite["fresh_source_comparison_sha256"] == PINS[FRAME]
            and suite["fresh_source_response_sha256"] == PINS[RESPONSE],
            "fresh continuous-shaft end references incomplete")
    require(receipt["output_sha256"]["suite.json"] == PINS[SHAFT_SUITE]
            and receipt["source_sha256"] == suite["source_sha256"],
            "continuous-shaft receipt differs")
    geometry_doc = read(HERE / "rawlocal/knee-compatible/prepare-attempt02/input-contract.json")
    bind(pins, HERE / "rawlocal/knee-compatible/prepare-attempt02/input-contract.json",
         "f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f")
    records = []
    for state in suite["states"]:
        require(state["reused_same_fresh_input_state"] is True
                and state["reused_historical_state"] is False
                and state["same_fresh_input_receipt_sha256"] == receipt["reuse"]["source_receipt_sha256"],
                "continuous result is not the exact same-fresh-input reuse")
        result_path = ROOT / state["result_path"]
        bind(pins, result_path, state["result_sha256"])
        result = read(result_path)
        require(result["case_id"] == state["case_id"] and result["axis_id"] == state["axis_id"]
                and result["fresh_source_comparison_sha256"] == PINS[FRAME]
                and result["fresh_source_response_sha256"] == PINS[RESPONSE],
                "continuous result state/source identity differs")
        tie_n = float(result["normal_transfer"]["single_physical_tie_n"])
        require(math.isclose(tie_n, float(state["physical_axial_tie_n"]), abs_tol=1e-9, rel_tol=1e-12),
                "continuous suite and result signed tie values differ")
        geometry = geometry_doc["geometry"][state["axis_id"]]
        contacts = result["outer_seat_fields"]
        require(len(contacts) == 2 and {x["end"] for x in contacts} == {"head", "nut"},
                "continuous physical outer-seat census differs")
        for end in contacts:
            role = end["end"]
            receiver = end["receiver"]
            seat = [float(x) for x in geometry["head_seat_point_mm" if role == "head" else "nut_seat_point_mm"]]
            traction = end["point_tractions"]["wood_contact"]
            moment = [0.0, 0.0, 0.0]
            for point, force in zip(traction["reference_points_mm"], traction["point_forces_xyz_n"], strict=True):
                term = cross([float(a) - b for a, b in zip(point, seat, strict=True)], force)
                moment = [a + b for a, b in zip(moment, term, strict=True)]
            magnitude = float(end["series_contact"]["moment_nmm"])
            require(math.isclose(math.sqrt(dot(moment, moment)), magnitude, abs_tol=1e-6, rel_tol=1e-8),
                    "signed continuous own-seat moment does not match retained series magnitude")
            trans = result["fresh_boundary"]["transverse_basis_xyz"]
            moment_pair = [dot(row, moment) for row in trans]
            require(math.isclose(math.hypot(*moment_pair), magnitude, abs_tol=1e-6, rel_tol=1e-8),
                    "continuous local signed moment basis differs")
            saved = support.get((state["axis_id"], receiver))
            require(saved is not None, "continuous outer receiver lacks saved support row")
            app = saved["modeled_support_applicability"]
            area = GENERIC_AREA_MM2
            records.append({
                "scope": "continuous_shaft_outer_end_TM_source", "case_id": state["case_id"],
                "axis_id": state["axis_id"], "end_role": role, "receiver_member": receiver,
                "fresh_force_source": state["result_path"],
                "fresh_source_row_id": state["case_id"] + "/" + state["axis_id"] + "/normal_transfer/single_physical_tie_n",
                "fresh_force_source_sha256": state["result_sha256"],
                "fresh_signed_T_n": tie_n,
                "fresh_interface_lateral_max_n": None,
                "own_end_M_magnitude_nmm": magnitude, "own_end_M_signed_xyz_nmm": moment,
                "own_end_M_signed_transverse_pair_nmm": moment_pair,
                "local_end_moment_status": "SIGNED_OWN_WOOD_CONTACT_TRACTION_RECOVERY",
                "ideal_annulus_area_mm2": area,
                "ideal_annulus_mean_pressure_mpa": max(tie_n, 0.0) / area,
                "wood_reference_route": "PERPENDICULAR_BASE_REFERENCE", "wood_reference_mpa": FC_PERP_MPA,
                "ideal_mean_over_wood_reference": max(tie_n, 0.0) / area / FC_PERP_MPA,
                "saved_supported_area_mm2": saved["saved_supported_area_mm2"],
                "modeled_support_applicability": app,
                "support_applicability_basis": saved["support_applicability_basis"],
                "applicable_supported_area_mm2": saved["saved_supported_area_mm2"] if app is True else None,
                "supported_mean_pressure_mpa": (max(tie_n, 0.0)
                    / saved["saved_supported_area_mm2"] if app is True and saved["saved_supported_area_mm2"] else None),
                "supported_mean_over_wood_reference": (max(tie_n, 0.0)
                    / saved["saved_supported_area_mm2"] / FC_PERP_MPA
                    if app is True and saved["saved_supported_area_mm2"] else None),
                "support_source": saved["source"], "support_source_sha256": saved["source_sha256"],
                "support_step_path": saved["support_step_path"], "support_step_sha256": saved["support_step_sha256"],
                "added_spine_bore_clearance_mm": saved["added_spine_bore_clearance_mm"],
                "metal_simultaneous_TM_status": "FRESH_SIGNED_TM_PAIR_SOURCE_ONLY_NO_WASHER_CAPACITY_METHOD",
                "metal_actual_stress_mpa": None, "metal_yield_mpa": None, "metal_capacity_n": None,
                "central_ring_trial_q0_mpa": None, "central_ring_trial_qmax_mpa": None,
                "central_trial_yield_floor_mpa": None, "central_trial_Fc_perp_ratio": None,
            })
    require(len(records) == 48 and len({(r["case_id"], r["axis_id"], r["end_role"]) for r in records}) == 48,
            "fresh continuous outer-end T/M row census differs")
    return records


def retail_solve_rows(edge, module, source_rows):
    model = edge.make_model(module, "fine")
    results, rows, failures = [], [], []
    for item in source_rows:
        source, support_row = item["source"], item["support"]
        debug = {}
        try:
            edge.STATE_ID = source["state_id"]
            state, _fields = edge.solve_state(model, source, debug)
            peak = state["sampled_stress_peak_witness"]
            balances = state["contact_balances"]
            wood_balance = next(x for x in balances if x["contact"] == "wood")
            source.update({"source_current_corner_checks_sha256": PINS[CORNER],
                           "support_id": source["axis_id"] + "/" + source["end_role"]})
            row = {
                "scope": "fresh_top_retail_plate_contact", "case_id": source["case_id"],
                "axis_id": source["axis_id"], "end_role": source["end_role"],
                "receiver_member": support_row["receiver"],
                "fresh_force_source": "knee-bridge-corner-replay/attempt01/checks.json",
                "fresh_source_row_id": source["compatible_T_source_row_id"],
                "fresh_force_source_sha256": PINS[CORNER], "fresh_signed_T_n": source["T_n"],
                "global_outer_tie_T_n": source["global_outer_tie_T_n"],
                "global_outer_tie_row_id": source["axial_tie_row_id"],
                "global_outer_tie_source_sha256": source["global_outer_tie_source_sha256"],
                "fresh_interface_lateral_max_n": None,
                "own_end_M_magnitude_nmm": source["M_magnitude_nmm"],
                "own_end_M_signed_xyz_nmm": source["source_moment_on_beam_xyz_nmm"],
                "own_end_M_signed_transverse_pair_nmm": source["source_signed_M_vector_in_pair_basis_nmm"],
                "local_end_moment_status": "FRESH_SIGNED_OWN_END_VECTOR_MAGNITUDE_DRIVEN_BY_EXISTING_CIRCULAR_MODEL",
                "ideal_annulus_area_mm2": item["ideal_area_mm2"],
                "ideal_annulus_mean_pressure_mpa": source["T_n"] / item["ideal_area_mm2"],
                "wood_reference_route": item["wood_reference_route"], "wood_reference_mpa": item["wood_reference_mpa"],
                "ideal_mean_over_wood_reference": (source["T_n"] / item["ideal_area_mm2"] / item["wood_reference_mpa"]
                    if item["wood_reference_mpa"] else None),
                "saved_supported_area_mm2": support_row["saved_area_mm2"],
                "modeled_support_applicability": support_row["support_applicability"],
                "support_applicability_basis": support_row["support_basis"],
                "applicable_supported_area_mm2": support_row["saved_area_mm2"] if support_row["support_applicability"] is True else None,
                "supported_mean_pressure_mpa": (source["T_n"] / support_row["saved_area_mm2"]
                    if support_row["support_applicability"] is True else None),
                "supported_mean_over_wood_reference": (source["T_n"] / support_row["saved_area_mm2"] / item["wood_reference_mpa"]
                    if support_row["support_applicability"] is True and item["wood_reference_mpa"] else None),
                "support_source": "retail-washer-suite/attempt01-fine/checks.json",
                "support_source_sha256": PINS[OLD_RETAIL],
                "support_step_path": support_row["support_step_path"],
                "support_step_sha256": support_row["support_step_sha256"],
                "added_spine_bore_clearance_mm": None,
                "metal_simultaneous_TM_status": "FINITE_EXISTING_FINE_PLATE_CONTACT_HYPOTHESIS",
                "metal_actual_stress_mpa": None, "metal_yield_mpa": None, "retail_Fy_hypothesis_mpa": 250.0,
                "metal_capacity_n": None, "central_ring_trial_q0_mpa": None,
                "central_ring_trial_qmax_mpa": None, "central_trial_yield_floor_mpa": None,
                "central_trial_Fc_perp_ratio": None,
                "retail_model_wood_mean_full_area_pressure_mpa": wood_balance["mean_full_area_pressure_mpa"],
                "retail_model_wood_peak_pressure_mpa": wood_balance["pressure_peak_mpa"],
                "retail_model_metal_sampled_stress_proxy_mpa": peak["sampled_through_thickness_maximum_proxy_mpa"],
                "retail_model_stress_proxy_over_hypothetical_Fy": peak["sampled_through_thickness_maximum_proxy_mpa"] / 250.0,
                "retail_model_stress_witness": peak,
                "retail_model_gradient_max_n": state["scaled_gradient_maximum_n"],
                "retail_model_wood_contact_balance": wood_balance,
                "solver_status": "FINITE_RETAIL_WASHER_HYPOTHESIS",
            }
            results.append({"state_id": source["state_id"], "status": row["solver_status"],
                            "source": source, "witness": peak,
                            "metrics": {k: row[k] for k in ("retail_model_wood_mean_full_area_pressure_mpa",
                                "retail_model_wood_peak_pressure_mpa", "retail_model_metal_sampled_stress_proxy_mpa",
                                "retail_model_stress_proxy_over_hypothetical_Fy", "retail_model_gradient_max_n")}})
        except (ValueError, RuntimeError, OSError, ArithmeticError) as error:
            failure = {"state_id": source["state_id"], "error": str(error),
                       "last_accepted_state": debug, "physical_incompatibility_proved": False,
                       "retry_performed": False}
            failures.append(failure)
            row = {
                "scope": "fresh_top_retail_plate_contact", "case_id": source["case_id"],
                "axis_id": source["axis_id"], "end_role": source["end_role"],
                "receiver_member": support_row["receiver"],
                "fresh_force_source": "knee-bridge-corner-replay/attempt01/checks.json",
                "fresh_source_row_id": source["compatible_T_source_row_id"],
                "fresh_force_source_sha256": PINS[CORNER], "fresh_signed_T_n": source["T_n"],
                "global_outer_tie_T_n": source["global_outer_tie_T_n"],
                "global_outer_tie_row_id": source["axial_tie_row_id"],
                "global_outer_tie_source_sha256": source["global_outer_tie_source_sha256"],
                "fresh_interface_lateral_max_n": None,
                "own_end_M_magnitude_nmm": source["M_magnitude_nmm"],
                "own_end_M_signed_xyz_nmm": source["source_moment_on_beam_xyz_nmm"],
                "own_end_M_signed_transverse_pair_nmm": source["source_signed_M_vector_in_pair_basis_nmm"],
                "local_end_moment_status": "FRESH_SIGNED_OWN_END_VECTOR_MAGNITUDE_DRIVEN_BY_EXISTING_CIRCULAR_MODEL",
                "ideal_annulus_area_mm2": item["ideal_area_mm2"],
                "ideal_annulus_mean_pressure_mpa": source["T_n"] / item["ideal_area_mm2"],
                "wood_reference_route": item["wood_reference_route"], "wood_reference_mpa": item["wood_reference_mpa"],
                "ideal_mean_over_wood_reference": (source["T_n"] / item["ideal_area_mm2"] / item["wood_reference_mpa"]
                    if item["wood_reference_mpa"] else None),
                "saved_supported_area_mm2": support_row["saved_area_mm2"],
                "modeled_support_applicability": support_row["support_applicability"],
                "support_applicability_basis": support_row["support_basis"],
                "applicable_supported_area_mm2": support_row["saved_area_mm2"] if support_row["support_applicability"] is True else None,
                "supported_mean_pressure_mpa": None, "supported_mean_over_wood_reference": None,
                "support_source": "retail-washer-suite/attempt01-fine/checks.json",
                "support_source_sha256": PINS[OLD_RETAIL],
                "support_step_path": support_row["support_step_path"],
                "support_step_sha256": support_row["support_step_sha256"],
                "added_spine_bore_clearance_mm": None,
                "metal_simultaneous_TM_status": "NUMERICAL_STOP_NO_CAPACITY_RESULT",
                "metal_actual_stress_mpa": None, "metal_yield_mpa": None, "retail_Fy_hypothesis_mpa": 250.0,
                "metal_capacity_n": None, "central_ring_trial_q0_mpa": None,
                "central_ring_trial_qmax_mpa": None, "central_trial_yield_floor_mpa": None,
                "central_trial_Fc_perp_ratio": None, "solver_status": "STOP",
                "solver_failure": failure,
            }
        rows.append(row)
    return rows, results, failures, model


CSV_COLUMNS = [
    "scope", "case_id", "axis_id", "end_role", "receiver_member", "fresh_force_source",
    "fresh_source_row_id", "fresh_force_source_sha256", "fresh_signed_T_n", "fresh_interface_lateral_max_n",
    "global_outer_tie_T_n", "global_outer_tie_row_id", "global_outer_tie_source_sha256",
    "own_end_M_magnitude_nmm", "own_end_M_signed_xyz_nmm", "own_end_M_signed_transverse_pair_nmm",
    "local_end_moment_status", "ideal_annulus_area_mm2", "ideal_annulus_mean_pressure_mpa",
    "wood_reference_route", "wood_reference_mpa", "ideal_mean_over_wood_reference",
    "saved_supported_area_mm2", "modeled_support_applicability", "support_applicability_basis",
    "applicable_supported_area_mm2", "supported_mean_pressure_mpa", "supported_mean_over_wood_reference",
    "support_source", "support_source_sha256", "support_step_path", "support_step_sha256",
    "added_spine_bore_clearance_mm", "metal_simultaneous_TM_status", "metal_actual_stress_mpa",
    "metal_yield_mpa", "retail_Fy_hypothesis_mpa", "metal_capacity_n", "central_ring_trial_q0_mpa", "central_ring_trial_qmax_mpa",
    "central_trial_yield_floor_mpa", "central_trial_Fc_perp_ratio", "retail_model_wood_mean_full_area_pressure_mpa",
    "retail_model_wood_peak_pressure_mpa", "retail_model_metal_sampled_stress_proxy_mpa",
    "retail_model_stress_proxy_over_hypothetical_Fy", "retail_model_stress_witness",
    "retail_model_gradient_max_n", "retail_model_wood_contact_balance", "solver_status", "solver_failure",
]


def csv_value(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return value


def json_value(value):
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(x) for x in value]
    if hasattr(value, "item"):
        return json_value(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def build(output):
    """Build the finite worksheet; never run earlier producers or other solvers."""
    output = Path(output).resolve()
    require(RAW.resolve() == RAW and output.parent == RAW.resolve() and not output.exists(),
            "use a fresh immediate child of rawlocal/washer-reference-completion")
    pins = {Path(path).resolve(): digest for path, digest in PINS.items()}
    bind(pins, Path(__file__).resolve(), sha(__file__))
    authenticate(pins)

    _summary, _frame, _assessment, _register, integration, _demands, keyed, axis_map = geometry_and_fresh_inputs(pins)
    support, effective, *_support_context = normalized_supports(pins, axis_map)
    area_by_axis, material_refs = csv_reference_map(pins, axis_map)
    require(math.isclose(FC_PERP_MPA, float(read(MATERIALS)["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"])
                         * 0.006894757293168361, rel_tol=0, abs_tol=1e-12),
            "DF-L No. 2 perpendicular material reference differs")
    old_suite, corner = read(OLD_RETAIL), read(CORNER)
    corner_timber = read(CORNER_TIMBER)
    shaft_suite, shaft_receipt = read(SHAFT_SUITE), read(SHAFT_RECEIPT)
    contract = read(CENTRAL)
    require(CORNER_RECEIPT.exists(), "fresh corner replay receipt missing")
    corner_receipt = read(CORNER_RECEIPT)
    require(corner_receipt["output_sha256"]["checks.json"] == PINS[CORNER],
            "corner replay output receipt differs")
    require(shaft_receipt["output_sha256"]["suite.json"] == PINS[SHAFT_SUITE],
            "fresh continuous suite result hash differs")
    require(contract["schema"] == "central_seat_static_transfer_preparation/v1"
            and contract["status"] == "CONDITIONAL_STATIC_ROUTE_COUPON_PENDING",
            "central ring method contract differs")
    # Authenticate the central effective receiver directly; old six trial loads are never read.
    central_step = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_principal_center_right.step"
    bind(pins, central_step, contract["source_sha256"][display(central_step)])
    generic_rows, corner_ids, retail_ids, _continuous_ids = make_support_rows(
        pins, support, axis_map, keyed, area_by_axis, material_refs)
    # Central trials are six annotations on an existing generic physical end.
    trials = central_trials(contract, keyed, axis_map)
    central_rows = [r for r in generic_rows if r["axis_id"] == contract["axis_id"]
                    and r["receiver_member"] == contract["body"]]
    require(len(central_rows) == 6, "central supported nut rows are not a six-state subset")
    for row in central_rows:
        trial = trials[row["case_id"]]
        row.update({"local_end_moment_status": "UNKNOWN_NOT_SET_TO_ZERO; CENTRAL_TRIAL_IS_NOT_RECOVERED_LOCAL_WRENCH",
            "central_ring_trial_q0_mpa": trial["trial_pressure_q0_qy_qz_mpa_or_mpa_per_mm"][0],
            "central_ring_trial_qmax_mpa": trial["trial_pressure_min_max_mpa"][1],
            "central_trial_yield_floor_mpa": trial["required_hypothetical_washer_yield_mpa"],
            "central_trial_Fc_perp_ratio": trial["wood_mean_over_conditional_Fc_perp"],
            "metal_simultaneous_TM_status": "CENTRAL_CONDITIONAL_STATIC_RING_TRIAL_ONLY"})

    edge, flexure, retail_input_rows, _retail_support_refs, retail_settings = retail_sources(
        pins, corner, old_suite, corner_timber, support, effective, material_refs, keyed, axis_map)
    shaft_rows = continuous_rows(pins, shaft_suite, shaft_receipt, support)
    # Every dynamic geometry/result pin is now known. Authenticate and record actual
    # observed bytes before the only new solver work begins.
    authenticate(pins)
    before = {display(path): sha(path) for path in sorted(pins)}
    expected_before = {display(path): digest for path, digest in sorted(pins.items())}
    require(before == expected_before, "observed source bytes differ from authenticated pins")
    retail_rows, retail_results, retail_failures, retail_model = retail_solve_rows(edge, flexure, retail_input_rows)
    all_rows = generic_rows + shaft_rows + retail_rows
    require(len(generic_rows) == 1008 and len(shaft_rows) == 48 and len(retail_rows) == 48
            and len(all_rows) == 1104
            and len({(r["case_id"], r["axis_id"], r["end_role"]) for r in all_rows}) == 1104,
            "finite endpoint/case state census differs")
    require(len(trials) == 6 and len(central_rows) == 6,
            "central six are not annotations on existing outside-corner rows")

    # Keep all source bytes stable across the calculations, including the 48 solver calls.
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    with (output / "washer-reference-states.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            writer.writerow({key: csv_value(row.get(key)) for key in CSV_COLUMNS})

    unsupported = [{"case_id": r["case_id"], "axis_id": r["axis_id"], "end_role": r["end_role"],
                    "receiver_member": r["receiver_member"], "basis": r["support_applicability_basis"]}
                   for r in all_rows if r["modeled_support_applicability"] is not True]
    unknown_moments = [{"case_id": r["case_id"], "axis_id": r["axis_id"], "end_role": r["end_role"],
                        "receiver_member": r["receiver_member"]}
                       for r in all_rows if r["own_end_M_magnitude_nmm"] is None]
    omitted_corners = sorted(corner_ids - retail_ids)
    internal_allocations = integration["consumed_internal_allocation_rows"]
    internal_axes = sorted({row["canonical_axis_id"] for row in internal_allocations})
    unknown_step_state_ids = [f"{case}/{axis}/{role}"
                              for axis in omitted_corners for case in CASES for role in ("head", "nut")]
    support_counts = {
        "saved_support_rows_before_lower_corroboration": 216,
        "unique_global_physical_exterior_seats": len(support),
        "exact_effective_or_pinned_proposal_geometry_applicable": sum(
            row["modeled_support_applicability"] is True for row in support.values()),
        "unknown_or_not_applicable_seat_rows": sum(
            row["modeled_support_applicability"] is not True for row in support.values()),
    }
    completed = [r for r in retail_rows if r.get("solver_status") == "FINITE_RETAIL_WASHER_HYPOTHESIS"]
    witnesses = {
        "maximum_ideal_annulus_mean_pressure": max(all_rows, key=lambda r: r["ideal_annulus_mean_pressure_mpa"]),
        "maximum_ideal_mean_over_material_reference": max(
            (r for r in all_rows if r["ideal_mean_over_wood_reference"] is not None),
            key=lambda r: r["ideal_mean_over_wood_reference"]),
        "maximum_supported_mean_pressure": max(
            (r for r in all_rows if r["supported_mean_pressure_mpa"] is not None),
            key=lambda r: r["supported_mean_pressure_mpa"], default=None),
        "maximum_fresh_retail_metal_stress_proxy": max(
            completed, key=lambda r: r["retail_model_metal_sampled_stress_proxy_mpa"], default=None),
        "maximum_fresh_retail_wood_mean_pressure": max(
            completed, key=lambda r: r["retail_model_wood_mean_full_area_pressure_mpa"], default=None),
        "maximum_central_ring_trial_required_yield": max(trials.values(),
            key=lambda r: r["required_hypothetical_washer_yield_mpa"]),
    }
    after = {display(path): sha(path) for path in sorted(pins)}
    require(after == before, "consumed source bytes changed during completion")
    source_map = {display(path): digest for path, digest in sorted(pins.items())}
    result = {
        "schema": "washer_reference_completion/v1",
        "status": "FINITE_PARTIAL_REFERENCE_WITH_NUMERICAL_STOPS" if retail_failures
                  else "FINITE_PARTIAL_WASHER_REFERENCE_ONLY",
        "source_sha256": source_map,
        "source_before_sha256": before, "source_after_sha256": after,
        "source_pins_unchanged": True,
        "runtime": {"python": sys.version.split()[0], "numpy": edge.np.__version__,
                    "scipy": edge.scipy.__version__, "platform": platform.platform()},
        "counts": {
            "global_export_axes": 104, "proposal_inventory_bolts": 108,
            "global_export_states": 624, "outside_corner_bolts": 88,
            "outside_corner_physical_ends": 176, "generic_endpoint_states": len(generic_rows) + len(shaft_rows),
            "continuous_shaft_axes": 4, "continuous_outer_end_TM_states": len(shaft_rows),
            "ordinary_global_axial_only_axes": 84, "ordinary_axial_only_end_states": len(generic_rows),
            "top_outer_retail_axes": len(retail_ids), "fresh_retail_end_states": len(retail_rows),
            "fresh_retail_solver_completed": len(completed), "fresh_retail_solver_stops": len(retail_failures),
            "central_ring_trial_states": len(trials), "central_ring_trials_already_in_generic_rows": len(central_rows),
            "distinct_output_end_state_rows": len(all_rows),
        },
        "support_join": support_counts,
        "model": {
            "generic_washer_annulus_inner_outer_radius_mm": [GENERIC_INNER_MM, GENERIC_OUTER_MM],
            "generic_ideal_area_mm2": GENERIC_AREA_MM2,
            "generic_wood_mean_definition": "max(signed_T_n, 0)/area; supported mean is numeric only when saved support matches the effective STEP or the pinned outer-X spine-land clearance proof.",
            "retail_family": RAIL_FAMILY, "retail_fixed_model": retail_settings,
            "retail_edge_resolution": retail_model["settings"],
            "retail_solver_calls_allowed": ["make_model", "solve_state"],
            "retail_coupon_or_retries": False,
            "retail_Fy_comparator_mpa": 250.0,
            "wood_reference_mpa": {"DF-L_No2_Fc_perpendicular": FC_PERP_MPA,
                                   "DF-L_No2_Fc_parallel": FC_PARALLEL_MPA},
            "old_csv_use": "Area and wood-reference labels only; its force, pressure and applicability columns are ignored.",
        },
        "central_ring_trials": list(trials.values()),
        "fresh_retail_states": retail_results,
        "numerical_stops": retail_failures,
        "unknown_local_moment_states": unknown_moments,
        "support_applicability_unknown_or_failed_states": unsupported,
        "excluded_corner_axes": omitted_corners,
        "excluded_corner_endpoint_case_rows": len(unknown_step_state_ids),
        "separate_internal_bridge_allocations": {
            "axis_ids": internal_axes, "tie_case_allocations": len(internal_allocations),
            "washer_endpoint_case_rows_included": 0,
            "reason": "Separate static allocations have no global bolt rows and no bound washer support/local end moments in this worksheet.",
        },
        "peak_witnesses": witnesses,
        "limits": [
            "Fresh global export contains 104 structural axes; four additional proposed bridge axes remain separate allocations.",
            "The 1,104 output rows are 1,056 exterior end/case references plus 48 top-retail T/M solves. Central six trials annotate existing generic rows.",
            "Unknown own-end moments remain null; no zero-moment metal bound or capacity is assigned.",
            "Continuous shaft records retain signed own-end moment vectors but have no additional washer plate solve.",
            "Retail stress values are sampled elastic proxies under the saved circular hypothesis and 250 MPa comparator; actual product stress, yield and capacity are null.",
            "Support rows apply only to their saved geometry or the explicit pinned proposal-land argument; no delivered wood, hardware or seat is inspected.",
            "The central patch is a conditional centered static ring trial, not a complete local nut wrench or actual product qualification.",
            "The other outer-corner washers and eight internal bridge exterior ends remain outside this finite comparison.",
        ],
        "actual_washer_stress_mpa": None, "actual_washer_yield_mpa": None,
        "actual_washer_capacity_n": None, "actual_supported_pressure_mpa": None,
        **PROPOSAL_FLAGS,
    }
    (output / "washer-reference-completion.json").write_text(
        json.dumps(json_value(result), sort_keys=True, indent=2, allow_nan=False) + "\n")
    (output / "source-pins.json").write_text(
        json.dumps({"source_sha256": source_map, "source_before_sha256": before,
                    "source_after_sha256": after, "source_pins_unchanged": True},
                   sort_keys=True, indent=2, allow_nan=False) + "\n")
    outputs = {str(path.relative_to(output)): sha(path) for path in sorted(output.rglob("*")) if path.is_file()}
    receipt = {"schema": "washer_reference_completion_receipt/v1", "source_sha256": source_map,
               "source_before_sha256": before, "source_after_sha256": after,
               "source_pins_unchanged": True, "output_sha256": outputs, **PROPOSAL_FLAGS}
    (output / "receipt.json").write_text(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), sort_keys=True, indent=2, allow_nan=False))

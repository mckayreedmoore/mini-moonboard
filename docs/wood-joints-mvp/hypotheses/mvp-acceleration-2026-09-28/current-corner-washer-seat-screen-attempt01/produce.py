#!/usr/bin/env python3
"""Reproduce the six current left outer-corner modeled washer-seat metrics."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent / "seat-screen.json"
AXIS_IDS = (
    "knee_outer_left_post_1",
    "knee_outer_left_post_2",
    "knee_outer_left_side_1",
    "knee_outer_left_side_2",
    "knee_outer_left_inner_header_1",
    "knee_outer_left_inner_header_2",
)
MODEL_PATH = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    "/reduced-static-attempt01/model-inputs.json"
)
TOPOLOGY_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-mass-topology-map-attempt03/source-topology-map.json"
)
CENTROIDS_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-mass-centroids-attempt01/mass-centroids.json"
)
REGISTER_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json"
)
MEMBER_GEOMETRY_PATH = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    "/reduced-static-attempt01/member-geometry.json"
)
REDUCED_PROPERTIES_PATH = "fea/wood_joint_reduced_properties.py"
BEARING_HELPER_PATH = "mini_moonboard/bolted_timber_checks.py"
BEARING_METHOD_PATH = "mini_moonboard/wood_joint_bolt_resistance.py"
BEARING_BASIS_PATH = "docs/wood-joints-mvp/bolt-resistance-basis.md"
WASHER_METHOD_DIR = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-washer-bending-method-attempt01-2026-09-28"
)
WASHER_METHOD_README = f"{WASHER_METHOD_DIR}/README.md"
WASHER_METHOD_ASSESSMENT = f"{WASHER_METHOD_DIR}/method-assessment.json"

# Source method basis: 2024 NDS Supplement Table 4A, DF-L No. 2 Fc-perp.
FC_PERP_PSI = 625.0
PSI_TO_MPA = 0.006894757293168361
N_PER_LBF = 4.4482216152605
INTERVAL_TOLERANCE_MM = 1.0e-5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def pin_sources(model: dict[str, Any], topology: dict[str, Any]) -> dict[str, str]:
    observed: dict[str, str] = {}
    # Check the reduced-property producer's direct transitive source pins.
    for relative, expected in model["source_sha256"].items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise ValueError(f"reduced model source hash changed: {relative}")
        observed[relative] = actual
    for relative, expected in topology["source_sha256"].items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise ValueError(f"topology source hash changed: {relative}")
        observed[relative] = actual
    # Additional method/register inputs used by this screen.
    for relative in (
        MODEL_PATH,
        TOPOLOGY_PATH,
        CENTROIDS_PATH,
        REGISTER_PATH,
        MEMBER_GEOMETRY_PATH,
        REDUCED_PROPERTIES_PATH,
        BEARING_HELPER_PATH,
        BEARING_METHOD_PATH,
        BEARING_BASIS_PATH,
        WASHER_METHOD_README,
        WASHER_METHOD_ASSESSMENT,
    ):
        observed[relative] = sha256(ROOT / relative)
    return dict(sorted(observed.items()))


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def unit(a: list[float]) -> list[float]:
    length = norm(a)
    if length <= 0.0:
        raise ValueError("zero-length vector")
    return [x / length for x in a]


def add(a: list[float], b: list[float]) -> list[float]:
    return [x + y for x, y in zip(a, b, strict=True)]


def scale(a: list[float], factor: float) -> list[float]:
    return [factor * x for x in a]


def grain_relation(axis: list[float], grain: list[float]) -> tuple[float, str]:
    cosine = abs(dot(unit(axis), unit(grain)))
    if cosine >= 1.0 - 1.0e-8:
        return cosine, "parallel_to_proposed_grain"
    if cosine <= 1.0e-8:
        return cosine, "perpendicular_to_proposed_grain"
    return cosine, "oblique_to_proposed_grain"


def effective_full_annulus_area_mm2(
    washer_projected_area_mm2: float,
    *,
    wood_bore_radius_mm: float,
    washer_opening_radius_mm: float | None,
) -> tuple[float | None, str]:
    """Return area only when opening/bore clipping can be excluded exactly."""
    if washer_opening_radius_mm is None:
        return None, "washer inner-opening radius is not carried by the reduced geometry record"
    if wood_bore_radius_mm > washer_opening_radius_mm + 1.0e-8:
        loss = math.pi * (wood_bore_radius_mm**2 - washer_opening_radius_mm**2)
        if loss >= washer_projected_area_mm2:
            return 0.0, "wood bore consumes the complete modeled annulus"
        return washer_projected_area_mm2 - loss, "wood bore clips modeled washer annulus"
    return washer_projected_area_mm2, "modeled washer opening clears the wood bore"


def build() -> dict[str, Any]:
    model = read_json(MODEL_PATH)
    topology = read_json(TOPOLOGY_PATH)
    centroids = read_json(CENTROIDS_PATH)
    register = read_json(REGISTER_PATH)
    member_geometry = read_json(MEMBER_GEOMETRY_PATH)
    if model.get("revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("unexpected current candidate geometry revision")
    if topology.get("revision_id") != model["revision_id"]:
        raise ValueError("topology and reduced inputs have different revisions")

    member_rows = {
        row["member_id"]: row for row in member_geometry["members"]
    }
    centroid_rows = {row["name"]: row for row in centroids["rows"]}
    register_rows = {
        row["axis_id"]: row for row in register["candidate_axis_rows"]
    }
    connection_rows = {
        row["axis_id"]: row
        for row in model["connections"]
        if row.get("kind") == "candidate_bolt"
    }
    if not set(AXIS_IDS).issubset(connection_rows):
        raise ValueError("one or more requested current corner axes are absent")

    fc_perp_mpa = FC_PERP_PSI * PSI_TO_MPA
    axes: list[dict[str, Any]] = []
    closure_residuals: list[float] = []
    for axis_id in AXIS_IDS:
        connection = connection_rows[axis_id]
        geometry = connection["source_record"]["geometry"]
        axis = unit([float(x) for x in geometry["axis_head_to_nut_global"]])
        center = [float(x) for x in geometry["shaft_center_global_xyz_mm"]]
        length = float(geometry["modeled_underhead_to_tip_mm"])
        underhead = [x - 0.5 * length * a for x, a in zip(center, axis, strict=True)]
        spans: list[dict[str, Any]] = []
        for receiver in geometry["wood_receiver_intervals"]:
            intervals = receiver[
                "current_shaft_intersection_solid_intervals_from_underhead_mm"
            ]
            if len(intervals) != 1:
                raise ValueError(f"{axis_id}: expected one saved receiver interval")
            lo, hi = map(float, intervals[0])
            spans.append(
                {"receiver_id": receiver["receiver_id"], "lo_mm": lo, "hi_mm": hi}
            )
        spans.sort(key=lambda row: (row["lo_mm"], row["hi_mm"], row["receiver_id"]))
        if not spans or any(
            abs(b["lo_mm"] - a["hi_mm"]) > INTERVAL_TOLERANCE_MM
            for a, b in zip(spans, spans[1:])
        ):
            raise ValueError(f"{axis_id}: saved receiver stack is not contiguous")
        if len(spans) not in (2, 3):
            raise ValueError(f"{axis_id}: unexpected receiver count")

        head = centroid_rows[f"{axis_id}/head_washer"]
        nut = centroid_rows[f"{axis_id}/nut_washer"]
        head_center = [float(x) for x in head["mass_center_global_xyz_mm"]]
        nut_center = [float(x) for x in nut["mass_center_global_xyz_mm"]]
        head_station = dot([x - y for x, y in zip(head_center, underhead, strict=True)], axis)
        nut_station = dot([x - y for x, y in zip(nut_center, underhead, strict=True)], axis)
        thickness = 2.0 * abs(head_station)
        nut_thickness = 2.0 * abs(spans[-1]["hi_mm"] - nut_station)
        if thickness <= 0.0 or abs(thickness - nut_thickness) > 1.0e-5:
            raise ValueError(f"{axis_id}: two modeled washer thicknesses do not reconcile")
        head_area = float(head["volume_mm3"]) / thickness
        nut_area = float(nut["volume_mm3"]) / thickness
        if abs(head_area - nut_area) > max(1.0e-5, head_area * 1.0e-6):
            raise ValueError(f"{axis_id}: head/nut washer annular areas differ")
        area = 0.5 * (head_area + nut_area)
        pressure_per_n_mpa = 1.0 / area
        seats = []
        outer_spans = (spans[0], spans[-1])
        for side, span in zip(("head_washer_seat", "nut_washer_seat"), outer_spans, strict=True):
            member_id = span["receiver_id"]
            member = member_rows[member_id]
            point = add(underhead, scale(axis, span["lo_mm"] if side == "head_washer_seat" else span["hi_mm"]))
            grain_cosine, relation = grain_relation(axis, member["grain_global_xyz"])
            bore_radii = [
                float(row["unique_bore_radius_mm"])
                for row in connection["receiver_clearance_geometry"]
                if row.get("receiver_id") == member_id
                and row.get("unique_bore_radius_mm") is not None
            ]
            bore_radius = bore_radii[0] if len(bore_radii) == 1 else None
            eff_area, eff_basis = effective_full_annulus_area_mm2(
                area,
                wood_bore_radius_mm=bore_radius if bore_radius is not None else 0.0,
                washer_opening_radius_mm=None,
            )
            # Only the preserved DF-L No. 2 frame-member scenario and transverse
            # loading bind the cited Fc-perp reference. Candidate-block strength
            # is not inferred from an elastic modulus or its grain direction.
            frame_dfl2_reference_eligible = (
                member_id in {"base_post_outer_left", "base_header"}
                and member.get("member_kind") == "timber"
                and relation == "perpendicular_to_proposed_grain"
            )
            wood_reference_n = area * fc_perp_mpa if frame_dfl2_reference_eligible else None
            one_n_closure = pressure_per_n_mpa * area
            closure_residuals.append(abs(one_n_closure - 1.0))
            seats.append(
                {
                    "seat_role": side,
                    "outer_receiver_member_id": member_id,
                    "member_kind": member["member_kind"],
                    "proposed_grain_global_xyz": member["grain_global_xyz"],
                    "bolt_axis_abs_dot_proposed_grain": grain_cosine,
                    "load_grain_relation": relation,
                    "seat_point_xyz_mm": point,
                    "source_receiver_interval_mm_from_underhead": [
                        span["lo_mm"], span["hi_mm"]
                    ],
                    "modeled_finished_wood_bore_radius_mm": bore_radius,
                    "conditional_full_annulus_effective_wood_area_mm2": eff_area,
                    "effective_area_status": (
                        "conditional_full_supported_annulus_only"
                        if eff_area is None
                        else "computed_from_opening_and_bore_geometry"
                    ),
                    "effective_area_missing": eff_basis,
                    "average_pressure_per_tie_N_MPa": pressure_per_n_mpa,
                    "ideal_dfl2_fc_perp_reference_N": wood_reference_n,
                    "ideal_dfl2_fc_perp_reference_status": (
                        "conditional_unadjusted_reference_if_DF_L_No2_full_support_and_transverse_loading"
                        if frame_dfl2_reference_eligible
                        else (
                            "Fc_perp_not_applicable_parallel_to_proposed_grain"
                            if relation == "parallel_to_proposed_grain"
                            else "candidate_block_bearing_strength_not_sourced"
                        )
                    ),
                }
            )
        record = register_rows[axis_id]
        axes.append(
            {
                "axis_id": axis_id,
                "modeled_axis_head_to_nut_global_xyz": axis,
                "modeled_receiver_count": len(spans),
                "one_physical_outer_seat_tie": True,
                "no_middle_member_axial_washer_seat": len(spans) == 3,
                "modeled_washer_thickness_mm": thickness,
                "modeled_head_washer_volume_mm3": float(head["volume_mm3"]),
                "modeled_nut_washer_volume_mm3": float(nut["volume_mm3"]),
                "modeled_outer_washer_annular_area_mm2": area,
                "washer_area_basis": (
                    "pinned modeled CAD component volume divided by per-axis measured thickness; "
                    "matches fea/wood_joint_reduced_properties.py"
                ),
                "one_N_full_annulus_average_pressure_MPa": pressure_per_n_mpa,
                "one_N_full_annulus_average_pressure_kPa": pressure_per_n_mpa * 1000.0,
                "one_N_full_annulus_average_pressure_psi": pressure_per_n_mpa / PSI_TO_MPA,
                "washer_product_status": "not_selected_or_delivered",
                "conditional_washer_lead_ids_in_axis_register": record.get(
                    "conditional_washer_lead_ids", []
                ),
                "selected_product": record.get("selected_product"),
                "fit_status": record.get("fit_status"),
                "outer_seats": seats,
                "limits": [
                    "T is a unit tie action only; no actual bolt demand is supplied.",
                    "Full-area pressure is a uniform-average scenario, not a contact-pressure solution.",
                    "No washer opening radius or exact finished support polygon is in the reduced seat record.",
                    "Washer steel bending/spreading and actual head/nut footprint remain unresolved.",
                ],
            }
        )

    expected_receivers = {
        "knee_outer_left_post_1": 2,
        "knee_outer_left_post_2": 2,
        "knee_outer_left_side_1": 3,
        "knee_outer_left_side_2": 3,
        "knee_outer_left_inner_header_1": 2,
        "knee_outer_left_inner_header_2": 2,
    }
    for row in axes:
        if row["modeled_receiver_count"] != expected_receivers[row["axis_id"]]:
            raise ValueError(f"{row['axis_id']}: changed current receiver stack")
        if len(row["outer_seats"]) != 2:
            raise ValueError(f"{row['axis_id']}: require exactly two outer seats")

    source_hashes = pin_sources(model, topology)
    return {
        "schema": "current_corner_washer_seat_screen/v1",
        "record_id": "current-corner-washer-seat-screen-attempt01",
        "candidate": model["candidate"],
        "geometry_revision_id": model["revision_id"],
        "status": "bounded_conditional_modeled_seat_geometry_only",
        "mechanical_acceptance": False,
        "native_solve_run": False,
        "cad_regenerated_or_modified": False,
        "mesh_created_or_modified": False,
        "axes": axes,
        "reference_basis": {
            "wood_fc_perp_psi": FC_PERP_PSI,
            "wood_fc_perp_mpa": fc_perp_mpa,
            "source": "2024 NDS Supplement Table 4A, DF-L No. 2; repository wood_washer_annulus_reference_lbf helper and bolt-resistance-basis.md",
            "reference_scope": "unadjusted wood compression-perpendicular-to-grain only, uniform pressure on a fully supported annulus, sound wood, no preload or bearing-area increase",
            "eligible_current_seat_members": ["base_post_outer_left", "base_header"],
            "reference_force_N_per_eligible_full_annulus_seat": (
                axes[0]["modeled_outer_washer_annular_area_mm2"] * fc_perp_mpa
            ),
            "not_a_design_resistance_or_complete_joint_capacity": True,
        },
        "scope_and_missing_inputs": [
            "No accepted signed physical-bolt tie tension at these six axes; upstream frame wrenches are not local washer actions.",
            "No selected/delivered washer dimensions, opening, thickness tolerance, flatness, or product/lot conformance.",
            "No exact finished timber support polygon including all nearby cuts/holes, seat gaps, flatness, or contact stiffness.",
            "The full annular area is conditional until the washer opening is shown to clear the modeled 3.75 mm bore radius and the full washer footprint bears on sound wood.",
            "Candidate block Fc-perp/Fc-parallel and grade are not sourced; BG045 inner-frame-block seats load parallel to the proposed grain, so Fc-perp is inapplicable there.",
            "Washer plate bending/load spreading remains unresolved; no resistance is inferred from dimensions, modeled area, hardness, or bolt proof load.",
            "For each three-member BG003 physical bolt, only one axial tie connects the two outer washer seats; the middle receiver gets no independent axial washer-seat tie.",
        ],
        "closure_check": {
            "unit_tie_action_N": 1.0,
            "equation": "p_avg = T / A_annulus; p_avg * A_annulus = T at each outer seat, conditional on uniform full-annulus pressure",
            "max_force_recovery_residual_N": max(closure_residuals),
        },
        "source_sha256": source_hashes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    data = build()
    encoded = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.write:
        OUT.write_text(encoded, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0
    if not OUT.exists() or OUT.read_text(encoding="utf-8") != encoded:
        raise SystemExit("seat-screen.json differs; regenerate with --write")
    print(
        "verified six axes; modeled area %.9f mm^2; thickness %.6f mm; "
        "max unit-seat closure residual %.3g N"
        % (
            data["axes"][0]["modeled_outer_washer_annular_area_mm2"],
            data["axes"][0]["modeled_washer_thickness_mm"],
            data["closure_check"]["max_force_recovery_residual_N"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

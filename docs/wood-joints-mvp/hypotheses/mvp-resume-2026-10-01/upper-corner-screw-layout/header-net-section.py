"""Compare six frozen header paired-bore sections under nominal MVP hypotheses.

Parent executes build(output) once. Reuse the frozen corner scalar calculator;
retain the complete source before/after cuts and actual header rectangles.
No mechanics solve, geometry change or joint qualification is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import platform
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/header-net-section"
CONTRACT = HERE / "rawlocal/header-local-transfer/attempt01"
TRACTION = HERE / "rawlocal/header-traction-map/attempt01"
HELPER = HERE / "corner-net-section.py"
TORSION = HERE.parent / "member_stability.py"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
DUTIES = {
    "center_post_cleat_left",
    "center_post_cleat_right",
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
}
PINS = {
    CONTRACT
    / "inputs.json": "cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b",
    CONTRACT
    / "model.json": "eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52",
    CONTRACT
    / "header-sections.csv": "f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953",
    CONTRACT
    / "receipt.json": "3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8",
    TRACTION
    / "result.json": "39d63b41dc495659b02cb4ff4fb638a19a491bc09e6ea3fd76a70314db08a837",
    TRACTION
    / "receipt.json": "1d454a949640a9b43d6ae3e3cf56ca20705e12ff6ae06f9bb51c1749623d96fd",
    HELPER: "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    TORSION: "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
}
FLAGS = {
    "formal_qualification": False,
    "native_readiness": False,
    "mechanics_executed": False,
    "compatibility_solved": False,
    "new_resistance_established": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
}
FORCE_TOL = 1e-7
MOMENT_TOL = 1e-5
GEOMETRY_TOL = 1e-6


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")


def load_helper():
    """Import only after authenticating the finalized scalar calculator."""
    authenticate({HELPER: PINS[HELPER], TORSION: PINS[TORSION]})
    spec = importlib.util.spec_from_file_location("frozen_corner_net_section", HELPER)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.TORSION_SOURCE == TORSION, "rectangle dependency differs")
    return module


def wrench(actions, datum):
    """Signed force and moment accounting, with every saved free couple."""
    value = np.zeros(6)
    for action in actions:
        force = np.asarray(action["force_n"], dtype=float)
        value[:3] += force
        value[3:] += np.cross(np.asarray(action["point_mm"]) - datum, force)
        value[3:] += action["free_moment_nmm"]
    return value


def check_residual(delta, label):
    require(np.isfinite(delta).all(), f"nonfinite {label}")
    require(
        max(abs(delta[:3])) < FORCE_TOL and max(abs(delta[3:])) < MOMENT_TOL,
        f"{label} loses full signed wrench: {delta.tolist()}",
    )


def section_geometry(model, section, helper):
    """Subtract saved full-depth bore chords from the actual header envelope."""
    body = model["bodies"]["base_header"]
    features = body["finished_surface_record"]["features"]
    bounds = np.asarray([f["bounds_global_xyz_mm"] for f in features]).reshape(-1, 3, 2)
    envelope = np.column_stack(
        (bounds[:, :, 0].min(axis=0), bounds[:, :, 1].max(axis=0))
    )
    datum = np.asarray(section["properties"]["centroid_global_xyz_mm"])
    holes = []
    for feature in features:
        if feature["surface_kind"] != "CYLINDER":
            continue
        cylinder = feature["cylinder"]
        center = np.asarray(cylinder["axis_origin_global_xyz_mm"])
        radius = cylinder["radius_mm"]
        dx = datum[0] - center[0]
        if abs(dx) >= radius - GEOMETRY_TOL:
            continue
        require(
            abs(dx) < GEOMETRY_TOL, "paired-bore cut is not at the saved bore center"
        )
        require(
            cylinder["material_side_geometry"] == "bore_like"
            and np.max(abs(np.abs(cylinder["axis_unit_global_xyz"]) - [0, 0, 1]))
            < 1e-8,
            "header passage is not a transverse circular bore",
        )
        bore_bounds = np.asarray(feature["bounds_global_xyz_mm"]).reshape(3, 2)
        require(
            np.max(abs(bore_bounds[2] - envelope[2])) < GEOMETRY_TOL,
            "bore is not full depth",
        )
        chord = math.sqrt(radius**2 - dx**2)
        holes.append(
            {
                "feature_id": feature["feature_id"],
                "axis_origin_xyz_mm": center.tolist(),
                "radius_mm": radius,
                "removed_y_interval_mm": [center[1] - chord, center[1] + chord],
            }
        )
    holes.sort(key=lambda h: h["removed_y_interval_mm"][0])
    require(len(holes) == 2, "exactly two existing bores required at each header duty")
    cursor = envelope[1, 0]
    regions = []
    for hole in holes:
        lo, hi = hole["removed_y_interval_mm"]
        require(
            cursor < lo < hi < envelope[1, 1],
            "paired bores overlap or leave the header",
        )
        regions.append(
            {
                "bounds_uv_mm": [
                    [cursor - datum[1], lo - datum[1]],
                    (envelope[2] - datum[2]).tolist(),
                ]
            }
        )
        cursor = hi
    regions.append(
        {
            "bounds_uv_mm": [
                [cursor - datum[1], envelope[1, 1] - datum[1]],
                (envelope[2] - datum[2]).tolist(),
            ]
        }
    )
    props = helper.area_properties(regions)
    saved = section["properties"]
    require(
        saved["component_count"] == 3 and saved["disconnected_ligaments"],
        "three ligaments required",
    )
    require(
        abs(props["area_mm2"] - saved["area_mm2"]) < FORCE_TOL, "saved net area differs"
    )
    require(
        max(abs(np.asarray(props["centroid_uv_mm"]))) < GEOMETRY_TOL,
        "saved net centroid differs",
    )
    # The saved CAD section's u coordinate runs along Z, and v along Y.
    covariance = saved["area_covariance_integrals_mm4"]
    require(
        np.allclose(
            props["central_integral_u2_uv_v2_matrix_mm4"],
            [[covariance["vv"], 0], [0, covariance["uu"]]],
            rtol=1e-10,
            atol=1e-4,
        ),
        "saved net inertia differs",
    )
    components = sorted(
        saved["components"], key=lambda c: c["centroid_global_xyz_mm"][1]
    )
    for region, component in zip(props["regions"], components, strict=True):
        center = np.r_[datum[0], datum[1:] + region["centroid_uv_mm"]]
        require(
            component["wire_count"] == 1
            and abs(region["area_mm2"] - component["area_mm2"]) < FORCE_TOL
            and np.max(abs(center - component["centroid_global_xyz_mm"]))
            < GEOMETRY_TOL,
            "retained rectangle differs from saved component",
        )
    pairs = {}
    for connection in model["header_connections"]:
        point = np.asarray(connection["source_point_xyz_mm"])
        if abs(point[0] - datum[0]) < GEOMETRY_TOL:
            duty = next(
                m for m in connection["receiver_member_ids"] if m != "base_header"
            )
            require(
                any(
                    np.max(abs(point[:2] - np.asarray(h["axis_origin_xyz_mm"])[:2]))
                    < GEOMETRY_TOL
                    for h in holes
                ),
                "header axis does not match actual bore",
            )
            pairs.setdefault(duty, []).append(connection["axis_id"])
    require(
        len(pairs) == 1 and len(next(iter(pairs.values()))) == 2,
        "header duty/section join differs",
    )
    duty = next(iter(pairs))
    return {
        "duty": duty,
        "axis_ids": sorted(pairs[duty]),
        "plane_id": section["plane_id"],
        "station_mm": section["station_mm"],
        "datum_xyz_mm": datum.tolist(),
        "envelope_bounds_xyz_mm": envelope.tolist(),
        "bores": holes,
        "regions": regions,
    }


def peaks(cuts):
    normal, shear = [], []
    for cut in cuts:
        identity = {
            k: cut[k] for k in ("duty", "case_id", "plane_id", "station_mm", "trace")
        }
        for region in cut["regions"]:
            own = {**identity, "region_id": region["region_id"]}
            shear.append(
                {
                    **own,
                    "ratio": region["same_state_shear_bound_over_Fv"],
                    "transverse_bound_mpa": region[
                        "nominal_transverse_shear_bound_mpa"
                    ],
                    "torsional_peak_mpa": region["nominal_torsional_peak_shear_mpa"],
                }
            )
            normal.extend(
                {**own, **corner} for corner in region["longitudinal_corners"]
            )
    return {
        "normal_comparisons": {
            key: max(normal, key=lambda item: item["comparisons"][key])
            for key in normal[0]["comparisons"]
        },
        "same_state_shear_bound_over_Fv": max(shear, key=lambda item: item["ratio"]),
        "comparison_counts_above_one": {
            **{
                key: sum(bool(item["comparisons"][key] > 1) for item in normal)
                for key in normal[0]["comparisons"]
            },
            "same_state_shear_bound_over_Fv": sum(bool(item["ratio"] > 1) for item in shear),
        },
    }


def build(output: str | Path) -> dict:
    """Parent API: one fresh output child, one coupon, all 72 section traces."""
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "use a fresh child of rawlocal/header-net-section",
    )
    producer = Path(__file__).resolve()
    pins = {**PINS, producer: sha(producer)}
    authenticate(pins)
    model, inputs = read(CONTRACT / "model.json"), read(CONTRACT / "inputs.json")
    prepared, mapped = read(CONTRACT / "receipt.json"), read(TRACTION / "result.json")
    map_receipt = read(TRACTION / "receipt.json")
    require(
        prepared["status"] == "PREPARED_HEADER_INPUT_CONTRACT_FOR_METHOD_SELECTION",
        "header input contract is not prepared",
    )
    for name in ("inputs.json", "model.json", "header-sections.csv"):
        require(
            prepared["output_sha256"][name] == pins[CONTRACT / name],
            "contract receipt differs",
        )
    require(
        map_receipt["output_sha256"]["result.json"] == pins[TRACTION / "result.json"]
        and mapped["boundary_mapping_executed"],
        "completed traction map receipt differs",
    )
    require(
        tuple(c["case_id"] for c in inputs["cases"]) == CASES
        and {c["case_id"] for c in mapped["cases"]} == set(CASES),
        "six-case census differs",
    )
    material = inputs["existing_header_evidence"]["conditional_material"]["base_header"]
    refs = material["CF_only_reference_mpa"]
    require(
        set(refs) == {"Ft_parallel", "Fc_parallel", "Fb", "Fv_parallel"},
        "header references differ",
    )
    body = model["bodies"]["base_header"]
    geometry = body["member_geometry"]["geometry"]
    frame = np.asarray([geometry["axis"], geometry["section_u"], geometry["section_v"]])
    require(
        np.max(abs(frame - np.eye(3))) < 1e-8
        and np.max(
            abs(
                np.asarray(body["grain_override"]["material_axes_global_xyz"]["L"])
                - frame[0]
            )
        )
        < 1e-8,
        "header longitudinal grain/frame differs",
    )
    helper = load_helper()
    coupon = helper.rectangular_known_answer(refs)
    sections = [
        s
        for s in model["saved_header_sections"]
        if s["properties"]["disconnected_ligaments"]
    ]
    require(len(sections) == 6, "six existing disconnected header sections required")
    layouts = [section_geometry(model, s, helper) for s in sections]
    require(
        {s["duty"] for s in layouts} == DUTIES, "six header duty assignments differ"
    )
    with (CONTRACT / "header-sections.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 1260, "complete saved header section census differs")
    keyed = {(r["case_id"], r["plane_id"], r["trace"]): r for r in rows}
    require(len(keyed) == len(rows), "duplicate saved section trace")
    cuts, source_balances = [], []
    mapped_cases = {c["case_id"]: c for c in mapped["cases"]}
    for case in inputs["cases"]:
        actions = case["complete_header_actions"]
        require(
            len(actions) == 394 and {i["block"] for i in case["interfaces"]} == DUTIES,
            "complete simultaneous header action/duty census differs",
        )
        physical = mapped_cases[case["case_id"]]
        require(
            physical["source_action_count"] == 394,
            "traction source action census differs",
        )
        map_delta = np.asarray(physical["mapping_residual_xyz_n_nmm"])
        check_residual(map_delta, "saved supported boundary map")
        source_balances.append(
            {
                "case_id": case["case_id"],
                "source_action_count": len(actions),
                "datum_xyz_mm": physical["datum_xyz_mm"],
                "source_body_residual_xyz_n_nmm": wrench(
                    actions, np.asarray(physical["datum_xyz_mm"])
                ).tolist(),
                "saved_supported_map_residual_xyz_n_nmm": map_delta.tolist(),
            }
        )
        for layout in layouts:
            datum = np.asarray(layout["datum_xyz_mm"])
            for trace in ("before", "after"):
                row = keyed[(case["case_id"], layout["plane_id"], trace)]
                q = np.asarray(json.loads(row["centroid_N_VY_VZ_T_M_Y_M_Z"]))
                included = [
                    a
                    for a in actions
                    if a["point_mm"][0] < datum[0] - GEOMETRY_TOL
                    or (
                        trace == "after"
                        and abs(a["point_mm"][0] - datum[0]) <= GEOMETRY_TOL
                    )
                ]
                delta = -wrench(included, datum) - q
                check_residual(delta, "all-action source section restoration")
                nominal = helper.nominal_section(q, layout["regions"], refs)
                roles = sorted({a["role"] for a in included})
                cuts.append(
                    {
                        **{k: v for k, v in layout.items() if k != "regions"},
                        "case_id": case["case_id"],
                        "trace": trace,
                        "source_actions_on_negative_half": len(included),
                        "source_restoration_residual_n_nmm": delta.tolist(),
                        "source_signed_cut_by_role_n_nmm": {
                            role: (
                                -wrench(
                                    [a for a in included if a["role"] == role], datum
                                )
                            ).tolist()
                            for role in roles
                        },
                        **nominal,
                    }
                )
    require(
        len(cuts) == 72 and sum(len(c["regions"]) for c in cuts) == 216,
        "finite comparison census differs",
    )
    saved_witness = mapped["source_A1_rear_133_35mm_witness"]
    witness = [
        c
        for c in cuts
        if c["case_id"] == saved_witness["case_id"]
        and c["plane_id"] == saved_witness["plane_id"]
    ]
    require(len(witness) == 2, "full A1 paired-bore witness missing")
    for cut in witness:
        original = next(
            r
            for r in saved_witness["source_signed_simultaneous_traces"]
            if r["trace"] == cut["trace"]
        )
        check_residual(
            np.asarray(cut["source_signed_cut_n_nmm"])
            - original["signed_N_VY_VZ_T_MY_MZ"],
            "preserved A1 torque witness",
        )
    residuals = {
        key: np.asarray([c[key] for c in cuts])
        for key in (
            "source_restoration_residual_n_nmm",
            "reconstructed_minus_source_n_nmm",
        )
    }
    counts = {
        "cases": 6,
        "duties": 6,
        "header_actions_per_case": 394,
        "paired_bore_sections": 6,
        "signed_section_traces": 72,
        "regional_comparisons": 216,
        "longitudinal_corner_comparisons": 864,
    }
    result = {
        "schema": "header-net-section-nominal-mvp/v1",
        "status": "COMPLETE_HEADER_NOMINAL_SECTION_COMPARISONS",
        "counts": counts,
        "source_sha256": {str(p.relative_to(ROOT)): s for p, s in sorted(pins.items())},
        "source_force_state_scope": inputs["source_force_state_scope"],
        "source_frame": "Original 100 mm lever, 250 lb times two and signed 300 N cases; saved frame forces unchanged.",
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "working_hypotheses": [
            *helper.ASSUMPTIONS[:4],
            "Retain the header's existing nominal-2x6 DF-L No.2 CF-only normal/shear references; no new adjustment or capacity.",
            "Use the saved full point-action before/after cuts as nominal demands. Interior annular-pressure cuts and local concentrations are not reconstructed.",
            "Header longitudinal grain is X. Retain the saved rotated R/T axes; the equal longitudinal shear modulus hypothesis permits calculations in geometric Y/Z axes.",
        ],
        "grain_override": body["grain_override"],
        "grain_u_v_frame_rows_xyz": frame.tolist(),
        "existing_reference_mpa": refs,
        "material_scenario": material,
        "rectangular_known_answer": coupon,
        "source_body_and_supported_map_accounting": source_balances,
        "cuts": cuts,
        "peaks": peaks(cuts),
        "duty_peaks": {
            duty: peaks([c for c in cuts if c["duty"] == duty])
            for duty in sorted(DUTIES)
        },
        "max_independent_accounting_residuals": {
            key: {
                "force_n": float(np.max(abs(values[:, :3]))),
                "moment_nmm": float(np.max(abs(values[:, 3:]))),
            }
            for key, values in residuals.items()
        },
        "A1_rear_full_torque_witness": witness,
        "balancing_free_couples_added": 0,
        "unavailable_design_resistances": inputs["unavailable_design_resistances"],
        "scope": "Finite nominal section/reference comparison under declared end-bridge and sharing assumptions. Completion records arithmetic, not a pass, full joint qualification or release. Existing counterpart claim gates remain unchanged.",
        **FLAGS,
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "schema": "header-net-section-receipt/v1",
            "status": result["status"],
            "counts": counts,
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
            "runtime": result["runtime"],
            **FLAGS,
        },
    )
    return {
        "status": result["status"],
        "output": str(output),
        "counts": counts,
        "checks_sha256": sha(output / "checks.json"),
        "receipt_sha256": sha(output / "receipt.json"),
        "peaks": result["peaks"],
        "max_independent_accounting_residuals": result[
            "max_independent_accounting_residuals"
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(
        json.dumps(build(parser.parse_args().output), sort_keys=True, allow_nan=False)
    )

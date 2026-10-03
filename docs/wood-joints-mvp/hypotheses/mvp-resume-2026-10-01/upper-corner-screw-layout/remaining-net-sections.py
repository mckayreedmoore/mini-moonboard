"""Finite nominal opening-section references for twelve frozen low-load blocks.

Parent executes this saved-data calculator. It performs no frame, native or CAD
run and supplies no notch, splitting, endbridge or complete-joint qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
MEMBER = BASE / "member-screen-attempt02/four-screw-layout01"
FEATURES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
REGISTER = HERE / "rawlocal/joint-register/attempt01/register.json"
RAW = HERE / "rawlocal/remaining-net-sections"
BLOCKS = (
    "bottom_center_left_cleat",
    "bottom_center_right_cleat",
    "top_center_left_cleat",
    "top_center_right_cleat",
    "left_service_inner_lower_cleat",
    "left_service_inner_upper_cleat",
    "left_service_outer_lower_cleat",
    "left_service_outer_upper_cleat",
    "wj04_lower_full_stock_cleat",
    "wj04_upper_g7_crosscut_full_stock_cleat",
    "wj06_outer_lower_right_cleat",
    "wj06_outer_upper_right_cleat",
)
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
TOL = 1e-6
PINS = {
    MEMBER
    / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBER
    / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER
    / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    REGISTER: "79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca",
    HERE
    / "operators-attempt02/model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    HERE
    / "operators-attempt02/row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    HERE
    / "operators-attempt02/model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    HERE
    / "frame-250-attempt02/comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE
    / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    HERE
    / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE
    / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    BASE
    / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    BASE
    / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    BASE.parent
    / "hardware-material-specification-2026-09-30/material-inputs.json": "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
}
ASSUMPTIONS = (
    "A common longitudinal strain plane spans the retained regions; continuous grain-end bridges maintain that plane.",
    "Regional transverse forces share in proportion to retained area, preserving their centroid-offset moments.",
    "Equal longitudinal shear moduli across regions and transverse directions, common regional twist and nominal free warping give regional torque in proportion to rectangular J.",
    "The same-state regional shear bound adds the parabolic transverse magnitude and rectangular Saint-Venant torsional peak; unchanged Fv applies to both longitudinal shear components.",
    "The per-member DF-L No.2 CF-only references and their recorded factor scenario are retained. No strength enhancement or separate torsional allowable is added.",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def arithmetic_module(filename, name):
    """Import definitions only; the frozen producer's run/main is not called."""
    sys.dont_write_bytecode = True
    path = HERE / filename
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "nominal helper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def geometry(body, member, surface):
    """Interpret the saved six bounding planes and four full cylinder patches."""
    g = member["geometry"]
    rows = np.array([g[k] for k in ("axis", "section_u", "section_v")])
    require(np.max(abs(rows @ rows.T - np.eye(3))) < 1e-8, "invalid grain frame")
    require(abs(np.linalg.det(rows) - 1) < 1e-8, "grain frame is not right handed")
    start = np.array(g["start"])
    width, depth = g["width_mm"], g["depth_mm"]
    length = float(np.dot(np.array(g["end"]) - start, rows[0]))
    require(abs(width - 88.9) < TOL and abs(depth - 88.9) < TOL, "section changed")
    expected_length = (
        86.9 if body == "wj04_upper_g7_crosscut_full_stock_cleat" else 119.7
    )
    require(abs(length - expected_length) < TOL, "grain length changed")
    require(
        not member["replaced_original_bore_features"]
        and member["recess_source"] is None,
        "changed opening geometry",
    )
    binding = surface["step_binding"]
    require(
        binding["file_sha256"] == member["current_finished_step_sha256"],
        "finished STEP identity differs",
    )
    step = ROOT / member["current_finished_step"]
    require(sha(step) == binding["file_sha256"], "finished STEP bytes differ")
    bores, sides = [], set()
    intervals = {b["id"]: b for b in member["bore_or_passage_intervals"]}
    features = surface["features"]
    require(len(features) == 10, "expected six planes and four cylinders")
    for feature in features:
        kind = feature["surface_kind"]
        if kind == "PLANE":
            plane = feature["plane"]
            normal = np.array(plane["normal_global_xyz"])
            local = rows @ normal
            axis = int(np.argmax(abs(local)))
            require(
                abs(abs(local[axis]) - 1) < 1e-7
                and np.max(abs(np.delete(local, axis))) < 1e-7,
                "nonrectangular plane",
            )
            coordinate = (
                plane["signed_plane_station_global_mm"] - normal @ start
            ) / local[axis]
            bounds = (
                [0, length]
                if axis == 0
                else [-[width, depth][axis - 1] / 2, [width, depth][axis - 1] / 2]
            )
            side = int(np.argmin(abs(np.array(bounds) - coordinate)))
            require(abs(bounds[side] - coordinate) < TOL, "bounding plane differs")
            require((axis, side) not in sides, "duplicate bounding plane")
            sides.add((axis, side))
            continue
        require(kind == "CYLINDER", "unsupported finished surface")
        cylinder = feature["cylinder"]
        require(
            cylinder["material_side_geometry"] == "bore_like", "cylinder is not a bore"
        )
        point = rows @ (np.array(cylinder["axis_origin_global_xyz_mm"]) - start)
        direction = rows @ np.array(cylinder["axis_unit_global_xyz"])
        axis = int(np.argmax(abs(direction)))
        require(
            axis in (1, 2)
            and abs(abs(direction[axis]) - 1) < 1e-7
            and np.max(abs(np.delete(direction, axis))) < 1e-7,
            "nontransverse cylinder",
        )
        radius = cylinder["radius_mm"]
        require(abs(radius - 3.75) < TOL, "bore radius differs")
        ends = sorted(
            point[axis]
            + direction[axis] * np.array(cylinder["axis_parameter_interval_mm"])
        )
        span = [width, depth][axis - 1]
        require(
            max(abs(np.array(ends) - [-span / 2, span / 2])) < TOL,
            "cylinder does not pass through finished stock",
        )
        u = feature["trim"]["surface_parameter_bounds"]["u"]
        require(abs(u[1] - u[0] - 2 * math.pi) < TOL, "partial cylinder patch")
        require(
            abs(feature["area_mm2"] - 2 * math.pi * radius * span) < 0.001,
            "cylinder area differs",
        )
        saved = intervals[feature["feature_id"]]
        station = (saved["lo"] + saved["hi"]) / 2
        require(abs(station - point[0]) < TOL, "saved bore station differs")
        removed_axis = 3 - axis
        require(
            radius < station < length - radius
            and abs(point[removed_axis]) + radius
            < [width, depth][removed_axis - 1] / 2,
            "bore meets an end or edge",
        )
        bores.append(
            {
                "axis_id": feature["feature_id"],
                "station_mm": station,
                "transverse_center_mm": float(point[removed_axis]),
                "removed_interval_axis": removed_axis,
                "radius_mm": radius,
                "full_cylinder_axis_local": direction.tolist(),
                "saved_axis_parameter_interval_mm": cylinder[
                    "axis_parameter_interval_mm"
                ],
            }
        )
    require(
        len(sides) == 6 and len(bores) == 4 and len(intervals) == 4,
        "finished feature count differs",
    )
    for first, second in combinations(bores, 2):
        distance = abs(first["station_mm"] - second["station_mm"])
        if first["removed_interval_axis"] == second["removed_interval_axis"]:
            distance = math.hypot(
                distance, first["transverse_center_mm"] - second["transverse_center_mm"]
            )
        require(
            distance > first["radius_mm"] + second["radius_mm"] + TOL,
            "overlapping bore cylinders",
        )
    removed = sum(
        math.pi * b["radius_mm"] ** 2 * ([width, depth][2 - b["removed_interval_axis"]])
        for b in bores
    )
    finished = width * depth * length - removed
    actual = g["geometry_diagnostics"]["actual_step_volume_mm3"]
    require(
        abs(finished - actual) < 0.001, "analytic net solid differs from saved volume"
    )
    return {
        "block": body,
        "grain_length_mm": length,
        "width_depth_mm": [width, depth],
        "bores": bores,
        "analytic_finished_volume_mm3": finished,
        "saved_finished_volume_mm3": actual,
        "finished_step_path": str(step.relative_to(ROOT)),
        "finished_step_sha256": binding["file_sha256"],
    }


def cut_summary(case, body, index, section, nominal):
    regions = nominal["regions"]
    corners = [c for r in regions for c in r["longitudinal_corners"]]
    return {
        "case": case,
        "block": body,
        "saved_trace_index": index,
        "station_mm": section["station_mm"],
        "limit": "before" if index % 2 == 0 else "after",
        "net_area_mm2": section["net_area_mm2"],
        "region_count": section["material_region_count"],
        "normal_reference_sum": max(
            c["comparisons"]["axial_plus_bending_reference_sum"] for c in corners
        ),
        "total_tension_over_Ft": max(
            c["comparisons"]["total_tension_over_Ft"] for c in corners
        ),
        "total_compression_over_Fc": max(
            c["comparisons"]["total_compression_over_Fc"] for c in corners
        ),
        "absolute_bending_over_Fb": max(
            c["comparisons"]["absolute_bending_over_Fb"] for c in corners
        ),
        "same_state_shear_bound_over_Fv": max(
            r["same_state_shear_bound_over_Fv"] for r in regions
        ),
        "transverse_shear_over_Fv": max(
            r["nominal_transverse_shear_bound_mpa"] for r in regions
        )
        / nominal["references"]["Fv_parallel"],
        "torsional_shear_over_Fv": max(
            r["nominal_torsional_peak_shear_mpa"] for r in regions
        )
        / nominal["references"]["Fv_parallel"],
        "source_signed_cut_n_nmm": nominal["source_signed_cut_n_nmm"],
        "regional_recovery_error_n_nmm": nominal["reconstructed_minus_source_n_nmm"],
    }


def run(output):
    output = output.resolve()
    require(
        output.is_relative_to(RAW.resolve()), "output must be in owned rawlocal child"
    )
    require(not output.exists(), "preserve existing output child")
    for path, expected in PINS.items():
        require(sha(path) == expected, f"source pin differs: {path}")
    results, geometries, surfaces, register = (
        read(MEMBER / "member-results.json"),
        read(MEMBER / "geometry.json"),
        read(FEATURES),
        read(REGISTER),
    )
    require(
        tuple(c["case_id"] for c in results["cases"]) == CASES,
        "six-case source differs",
    )
    surface_by_id = {r["member_id"]: r for r in surfaces["records"]}
    register_by_id = {r["block_id"]: r for r in register["blocks"]}
    for path, digest in PINS.items():
        relative = str(path.relative_to(ROOT))
        if "/operators-attempt02/" in relative or "/frame-250-attempt02/" in relative:
            require(
                results["source_sha256"].get(relative) == digest
                and register["source_sha256"].get(relative) == digest,
                "member/register frame binding differs",
            )
    helper = arithmetic_module("corner-net-section.py", "remaining_nominal_sections")
    section_at = arithmetic_module(
        "corner-timber-sections.py", "remaining_geometry_sections"
    ).section
    body_geometry, sections, summaries, peak_details = {}, {}, [], {}
    accounting = {
        "max_opposed_half_force_error_n": 0.0,
        "max_opposed_half_moment_error_nmm": 0.0,
        "max_regional_force_recovery_error_n": 0.0,
        "max_regional_moment_recovery_error_nmm": 0.0,
    }
    with np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays:
        for body in BLOCKS:
            record = geometries["members"][body]
            require(
                register_by_id[body]["physical_axis_count"] == 4,
                "registered block axes differ",
            )
            geom = geometry(body, record, surface_by_id[body])
            body_geometry[body] = geom
            own_sections = [
                (i, section_at(geom, float(s)))
                for i, s in enumerate(record["stations_mm"])
            ]
            own_sections = [
                (i, s) for i, s in own_sections if s["bore_or_tangency_ids"]
            ]
            require(own_sections, "no recorded opening sections")
            require(
                {b["axis_id"] for b in geom["bores"]}
                == {
                    identity
                    for _, s in own_sections
                    for identity in s["bore_or_tangency_ids"]
                },
                "not all bores covered",
            )
            sections[body] = [{"saved_station_index": i, **s} for i, s in own_sections]
            for case in results["cases"]:
                source = next(m for m in case["members"] if m["member"] == body)
                binding = source["conditional_material"]
                require(
                    binding["design_resistance_established"] is False,
                    "conditional reference boundary differs",
                )
                refs = binding["CF_only_reference_mpa"]
                prefix = source["array_prefix"]
                negative, positive = (
                    arrays[prefix + suffix]
                    for suffix in (
                        "__internal_negative_grain_u_v",
                        "__internal_positive_grain_u_v",
                    )
                )
                require(
                    negative.shape
                    == positive.shape
                    == (2 * len(record["stations_mm"]), 6),
                    "saved trace shape differs",
                )
                residual = np.max(abs(negative + positive), axis=0)
                accounting["max_opposed_half_force_error_n"] = max(
                    accounting["max_opposed_half_force_error_n"],
                    float(max(residual[:3])),
                )
                accounting["max_opposed_half_moment_error_nmm"] = max(
                    accounting["max_opposed_half_moment_error_nmm"],
                    float(max(residual[3:])),
                )
                require(
                    max(residual[:3]) <= 0.1 and max(residual[3:]) <= 2,
                    "existing whole-member closure bounds exceeded",
                )
                for station_index, section in own_sections:
                    for index in (2 * station_index, 2 * station_index + 1):
                        nominal = helper.nominal_section(
                            negative[index], section["regions"], refs
                        )
                        nominal["references"] = refs
                        summary = cut_summary(
                            case["case_id"], body, index, section, nominal
                        )
                        summaries.append(summary)
                        recovery = np.array(nominal["reconstructed_minus_source_n_nmm"])
                        accounting["max_regional_force_recovery_error_n"] = max(
                            accounting["max_regional_force_recovery_error_n"],
                            float(max(abs(recovery[:3]))),
                        )
                        accounting["max_regional_moment_recovery_error_nmm"] = max(
                            accounting["max_regional_moment_recovery_error_nmm"],
                            float(max(abs(recovery[3:]))),
                        )
                        for metric in (
                            "normal_reference_sum",
                            "same_state_shear_bound_over_Fv",
                        ):
                            key = body + "/" + metric
                            if (
                                key not in peak_details
                                or summary[metric]
                                > peak_details[key]["summary"][metric]
                            ):
                                peak_details[key] = {
                                    "summary": summary,
                                    "conditional_material": binding,
                                    "nominal_section": nominal,
                                }
    per_block = []
    for body in BLOCKS:
        rows = [r for r in summaries if r["block"] == body]
        metrics = (
            "normal_reference_sum",
            "same_state_shear_bound_over_Fv",
            "transverse_shear_over_Fv",
            "torsional_shear_over_Fv",
        )
        per_block.append(
            {
                "block": body,
                "evaluated_trace_count": len(rows),
                "recorded_opening_station_count": len(sections[body]),
                "minimum_evaluated_net_area_mm2": min(r["net_area_mm2"] for r in rows),
                "maximum_region_count": max(r["region_count"] for r in rows),
                "peaks": {key: max(rows, key=lambda r: r[key]) for key in metrics},
            }
        )
    report = {
        "schema": "remaining-12-block-nominal-net-section-references-v1",
        "status": "FINITE_NOMINAL_REFERENCE_COMPARISON_COMPLETE",
        "source_hold_lever_mm": 100,
        "case_ids": list(CASES),
        "block_ids": list(BLOCKS),
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in PINS.items()
        },
        "producer_sha256": sha(Path(__file__).resolve()),
        "assumptions": list(ASSUMPTIONS),
        "scope": "Only recorded bore/tangency cuts of twelve assigned low-load blocks; no full-prism rerun, new action allocation, wall concentration, notch/splitting capacity, or continuous-station maximum certification.",
        "cut_convention": "Use the complete saved negative-grain-half internal [N,Vu,Vv,T,Mu,Mv], N positive in tension. Opposed positive-half traces are retained as a closure comparison, not separately inverted tension/compression states.",
        "complete_joint_acceptance": False,
        "formal_qualification": False,
        "physical_release": False,
        "geometry": body_geometry,
        "opening_sections": sections,
        "accounting": accounting,
        "evaluated_trace_count": len(summaries),
        "all_evaluated_nominal_reference_indices_below_one": all(
            r["normal_reference_sum"] <= 1 and r["same_state_shear_bound_over_Fv"] <= 1
            for r in summaries
        ),
        "per_block": per_block,
        "cut_summaries": summaries,
        "peak_details": peak_details,
    }
    output.mkdir(parents=True)
    (RAW / ".gitignore").write_text("*\n")
    dump(output / "checks.json", report)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "checks_sha256": sha(output / "checks.json"),
                "evaluated_trace_count": len(summaries),
                "all_evaluated_nominal_reference_indices_below_one": report[
                    "all_evaluated_nominal_reference_indices_below_one"
                ],
                "accounting": accounting,
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)


if __name__ == "__main__":
    main()

"""Prepare finite nominal opening-section comparisons for two knee spines.

Parent executes build(output) or the CLI. Importing this producer performs no
section arithmetic or coupon. The saved six original 100 mm, 250 lb x 2 + 300 N
states, their signed cuts and existing CF-only references remain unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
MEMBER = BASE / "member-screen-attempt02/four-screw-layout01"
FEATURES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
MATERIAL = (
    BASE.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
)
INPUTS = HERE / "operators-attempt02/model-inputs.json"
FRAME = HERE / "frame-250-attempt02/comparison.json"
HELPER = HERE / "corner-net-section.py"
SECTION_HELPER = HERE / "corner-timber-sections.py"
TORSION = BASE / "member_stability.py"
RAW = HERE / "rawlocal/knee-spine-net-sections"
STEP_DIR = (
    BASE.parent
    / "evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members"
)
BLOCKS = ("knee_outer_left_spine", "knee_outer_right_spine")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    MEMBER
    / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBER
    / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER
    / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    HELPER: "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    SECTION_HELPER: "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    TORSION: "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    FRAME: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE
    / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    STEP_DIR
    / "knee_outer_left_spine.step": "081a3930dd1334e317fc0116a24d80b4b70e9cb3f36b928cda403f66194bb5c0",
    STEP_DIR
    / "knee_outer_right_spine.step": "f70ade3760f1615cc31f687bc4cf4c334d27db3b8b41e35e615e15b92c4e1faa",
}
TOL = 1e-6
REFERENCE_METRICS = (
    "normal_reference_sum",
    "total_tension_over_Ft",
    "total_compression_over_Fc",
    "absolute_bending_over_Fb",
    "same_state_shear_bound_over_Fv",
)
FLAGS = {
    "complete_member_acceptance": False,
    "complete_joint_acceptance": False,
    "formal_qualification": False,
    "new_resistance_established": False,
    "local_compatibility_solved": False,
    "native_launch": False,
    "CAD_rebuilt": False,
    "reviewed_geometry_changed": False,
    "tests_run": False,
    "review_run": False,
    "physical_release": False,
}


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


def load_helper(path, name):
    """Load authenticated definitions without calling either producer's main."""
    sys.dont_write_bytecode = True
    require(sha(path) == PINS[path], f"helper differs: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def geometry(body, member, surface):
    """Bind saved rectangular planes and full-width bores to delivered STEP bytes."""

    def supported(condition, detail):
        require(condition, f"UNSUPPORTED_GEOMETRY: {body}: {detail}")

    g = member["geometry"]
    rows = np.asarray([g[k] for k in ("axis", "section_u", "section_v")])
    supported(
        rows.shape == (3, 3)
        and np.isfinite(rows).all()
        and np.max(abs(rows @ rows.T - np.eye(3))) < 1e-8
        and abs(np.linalg.det(rows) - 1) < 1e-8,
        "saved grain/u/v frame is not orthonormal and right handed",
    )
    start = np.asarray(g["start"])
    delta = np.asarray(g["end"]) - start
    length = float(delta @ rows[0])
    width, depth = g["width_mm"], g["depth_mm"]
    supported(
        abs(length - 276.3) < TOL
        and abs(width - 38.1) < TOL
        and abs(depth - 139.7) < TOL
        and np.max(abs(rows[1:] @ delta)) < TOL,
        "expected 38.1 x 139.7 x 276.3 mm rectangular stock",
    )
    supported(
        member["member_kind"] == "timber"
        and g["source_descriptor"]["member_kind"] == "candidate_block"
        and not member["replaced_original_bore_features"]
        and member["recess_source"] is None,
        "changed member kind, replaced bores or recess",
    )
    step = STEP_DIR / (body + ".step")
    binding = surface["step_binding"]
    require(
        member["current_finished_step"]
        == binding["path"]
        == str(step.relative_to(ROOT))
        and member["current_finished_step_sha256"]
        == binding["file_sha256"]
        == PINS[step],
        f"finished STEP binding differs: {body}",
    )
    require(sha(step) == PINS[step], f"delivered STEP bytes differ: {body}")
    supported(
        binding["solid_count"] == 1 and binding["face_count"] == 10,
        "expected saved single solid with ten faces",
    )
    features = surface["features"]
    intervals = {b["id"]: b for b in member["bore_or_passage_intervals"]}
    supported(
        len(features) == len({f["feature_id"] for f in features}) == 10
        and len(intervals) == len(member["bore_or_passage_intervals"]) == 4,
        "expected six distinct planes and four distinct bore intervals",
    )
    bores, planes = [], {}
    for feature in features:
        identity, kind = feature["feature_id"], feature["surface_kind"]
        if kind == "PLANE":
            plane = feature["plane"]
            normal = np.asarray(plane["normal_global_xyz"])
            local = rows @ normal
            axis = int(np.argmax(abs(local)))
            supported(
                abs(abs(local[axis]) - 1) < 1e-7
                and np.max(abs(np.delete(local, axis))) < 1e-7,
                f"{identity}: oblique bounding plane",
            )
            station = (
                plane["signed_plane_station_global_mm"] - normal @ start
            ) / local[axis]
            bounds = (
                [0, length]
                if axis == 0
                else [-[width, depth][axis - 1] / 2, [width, depth][axis - 1] / 2]
            )
            side = int(np.argmin(abs(np.asarray(bounds) - station)))
            supported(
                abs(bounds[side] - station) < TOL and (axis, side) not in planes,
                f"{identity}: changed or duplicate bounding plane",
            )
            planes[axis, side] = feature
            continue
        supported(kind == "CYLINDER", f"{identity}: unsupported surface kind {kind}")
        cylinder = feature["cylinder"]
        point = rows @ (np.asarray(cylinder["axis_origin_global_xyz_mm"]) - start)
        direction = rows @ np.asarray(cylinder["axis_unit_global_xyz"])
        supported(
            cylinder["material_side_geometry"] == "bore_like"
            and abs(abs(direction[1]) - 1) < 1e-7
            and np.max(abs(direction[[0, 2]])) < 1e-7,
            f"{identity}: expected transverse full-width u-axis bore",
        )
        radius = cylinder["radius_mm"]
        ends = np.sort(
            point[1] + direction[1] * np.asarray(cylinder["axis_parameter_interval_mm"])
        )
        angular = feature["trim"]["surface_parameter_bounds"]["u"]
        supported(
            abs(radius - 3.75) < TOL
            and np.max(abs(ends - [-width / 2, width / 2])) < TOL
            and abs(angular[1] - angular[0] - 2 * math.pi) < TOL
            and abs(feature["area_mm2"] - 2 * math.pi * radius * width) < 0.001,
            f"{identity}: changed radius, blind/partial cylinder or trimmed area",
        )
        supported(identity in intervals, f"{identity}: missing saved bore interval")
        saved = intervals[identity]
        supported(
            abs(saved["radius_mm"] - radius) < TOL
            and max(
                abs(saved["lo"] - (point[0] - radius)),
                abs(saved["hi"] - (point[0] + radius)),
            )
            < TOL,
            f"{identity}: saved grain interval differs from cylinder",
        )
        supported(
            radius < point[0] < length - radius and abs(point[2]) + radius < depth / 2,
            f"{identity}: bore intersects grain end or depth edge",
        )
        bores.append(
            {
                "axis_id": identity,
                "station_mm": float(point[0]),
                "transverse_center_mm": float(point[2]),
                "removed_interval_axis": 2,
                "radius_mm": radius,
                "saved_grain_interval_mm": [saved["lo"], saved["hi"]],
                "axis_origin_global_xyz_mm": cylinder["axis_origin_global_xyz_mm"],
                "axis_unit_global_xyz": cylinder["axis_unit_global_xyz"],
                "saved_axis_parameter_interval_mm": cylinder[
                    "axis_parameter_interval_mm"
                ],
            }
        )
    supported(len(planes) == 6 and len(bores) == 4, "bounding plane/bore count differs")
    supported({b["axis_id"] for b in bores} == set(intervals), "bore identities differ")
    for first, second in combinations(bores, 2):
        supported(
            abs(first["station_mm"] - second["station_mm"])
            > first["radius_mm"] + second["radius_mm"] + TOL,
            f"{first['axis_id']} / {second['axis_id']}: overlapping grain opening bands",
        )
    bore_face_area = math.fsum(math.pi * b["radius_mm"] ** 2 for b in bores)
    for (axis, _side), feature in planes.items():
        expected = (width * depth, length * depth - bore_face_area, length * width)[
            axis
        ]
        supported(
            abs(feature["area_mm2"] - expected) < 0.001,
            f"{feature['feature_id']}: plane trim area differs",
        )
    volume = width * depth * length - width * bore_face_area
    actual = g["geometry_diagnostics"]["actual_step_volume_mm3"]
    supported(
        abs(volume - actual) < 0.001,
        "analytic finished volume differs from saved STEP volume",
    )
    return {
        "block": body,
        "grain_frame_rows_xyz": rows.tolist(),
        "start_xyz_mm": start.tolist(),
        "grain_length_mm": length,
        "width_depth_mm": [width, depth],
        "bores": bores,
        "analytic_finished_volume_mm3": volume,
        "saved_finished_volume_mm3": actual,
        "finished_step_binding": binding,
        "geometry_method": "Saved six planes minus four disjoint full-width cylinders; delivered STEP bytes authenticated without CAD import.",
    }


def source_contract(results, source_inputs, frame):
    """Keep this producer on the original simultaneous force and load identity."""
    require(
        tuple(c["case_id"] for c in results["cases"]) == CASES,
        "six-case source differs",
    )
    require(
        tuple(c["case_id"] for c in source_inputs["cases"]) == CASES,
        "load case order differs",
    )
    require(
        frame["source_climber_weight_lb"]
        == frame["comparison_climber_weight_lb"]
        == 250
        and frame["climber_load_scale"] == 1
        and frame["horizontal_force_scaled_with_climber"] is True
        and results["same_state_dead_load_factor"] == frame["dead_load_factor"],
        "original 250 lb simultaneous force identity differs",
    )
    for path in (INPUTS, FRAME, MATERIAL, HERE / "frame-250-attempt02/response.npz"):
        require(
            results["source_sha256"].get(str(path.relative_to(ROOT))) == PINS[path],
            f"member source binding differs: {path}",
        )
    for path in (MEMBER / "geometry.json", MEMBER / "action-section-arrays.npz"):
        require(
            results["output_sha256"].get(path.name) == PINS[path],
            f"member output binding differs: {path}",
        )
    horizontal = ([0, 300], [0, -300], [-300, 0], [300, 0], [0, 300], [0, 300])
    for case, expected in zip(source_inputs["cases"], horizontal, strict=True):
        load = case["source_applied_load"]
        inputs = load["case_inputs"]
        require(
            inputs["pounds"] == 250
            and inputs["dynamic_factor"] == 2
            and inputs["horizontal_force_global_xy_n"] == expected,
            f"load inputs differ: {case['case_id']}",
        )
        lever = (
            np.asarray(load["force_application_point_global_xyz_mm"])
            - load["patch_center_global_xyz_mm"]
        )
        require(
            abs(np.linalg.norm(lever) - 100) < TOL,
            f"original 100 mm lever differs: {case['case_id']}",
        )


def references(body, binding, material, helper):
    """Authenticate the saved nominal-2x6 CF scenario; add no adjustment factor."""
    scenario = material["standard_section_scenarios"]["nominal_2x6"]
    require(
        body in scenario["member_ids"]
        and binding["CF"] == scenario["CF"]
        and binding["design_resistance_established"] is False,
        f"conditional CF scenario differs: {body}",
    )
    refs = binding["CF_only_reference_mpa"]
    base = material["conditional_DF_L_No2_base_row"]["base_properties"]
    for key in ("Ft_parallel", "Fb", "Fc_parallel", "Fv_parallel"):
        require(
            abs(refs[key] - base[key] * scenario["CF"].get(key, 1) * helper.PSI_MPA)
            < 1e-12,
            f"saved CF-only reference differs: {body}/{key}",
        )
    return refs


def cut_summary(identity, nominal):
    corners = [
        (r["region_id"], c)
        for r in nominal["regions"]
        for c in r["longitudinal_corners"]
    ]
    witnesses = {}
    for metric, comparison in zip(
        REFERENCE_METRICS[:4],
        (
            "axial_plus_bending_reference_sum",
            "total_tension_over_Ft",
            "total_compression_over_Fc",
            "absolute_bending_over_Fb",
        ),
        strict=True,
    ):
        region_id, corner = max(corners, key=lambda r: r[1]["comparisons"][comparison])
        witnesses[metric] = {
            "region_id": region_id,
            "uv_mm": corner["uv_mm"],
            "ratio": corner["comparisons"][comparison],
        }
    for metric, field in (
        ("same_state_shear_bound_over_Fv", "same_state_shear_bound_over_Fv"),
        ("transverse_shear_over_Fv", "nominal_transverse_shear_bound_mpa"),
        ("torsional_shear_over_Fv", "nominal_torsional_peak_shear_mpa"),
    ):
        region = max(nominal["regions"], key=lambda r: r[field])
        ratio = (
            region[field]
            if metric == field
            else region[field] / nominal["references"]["Fv_parallel"]
        )
        witnesses[metric] = {
            "region_id": region["region_id"],
            "ratio": ratio,
            "transverse_bound_mpa": region["nominal_transverse_shear_bound_mpa"],
            "torsional_peak_mpa": region["nominal_torsional_peak_shear_mpa"],
        }
    return {
        **identity,
        **{metric: witness["ratio"] for metric, witness in witnesses.items()},
        "witnesses": witnesses,
        "source_signed_cut_n_nmm": nominal["source_signed_cut_n_nmm"],
        "signed_cut_at_net_centroid_n_nmm": nominal["signed_cut_at_net_centroid_n_nmm"],
        "regional_recovery_error_n_nmm": nominal["reconstructed_minus_source_n_nmm"],
    }


def build(output: Path):
    """Parent-only finite arithmetic, with one existing rectangle coupon."""
    output = output.resolve()
    require(
        output.is_relative_to(RAW.resolve())
        and output != RAW.resolve()
        and not output.exists(),
        "fresh owned rawlocal output child required",
    )
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    authenticate(pins)
    results, geometries, surfaces, material = (
        read(MEMBER / "member-results.json"),
        read(MEMBER / "geometry.json"),
        read(FEATURES),
        read(MATERIAL),
    )
    source_contract(results, read(INPUTS), read(FRAME))
    helper = load_helper(HELPER, "knee_spine_nominal_sections")
    section_at = load_helper(SECTION_HELPER, "knee_spine_opening_geometry").section
    require(helper.TORSION_SOURCE == TORSION, "torsion dependency differs")
    body_geometry, sections, bindings = {}, {}, {}
    for body in BLOCKS:
        matches = [r for r in surfaces["records"] if r["member_id"] == body]
        require(len(matches) == 1, f"finished surface record is not unique: {body}")
        record = geometries["members"][body]
        geom = geometry(body, record, matches[0])
        stations = np.asarray(record["stations_mm"])
        require(
            stations.ndim == 1
            and np.isfinite(stations).all()
            and np.all(np.diff(stations) > 0)
            and abs(stations[0]) < TOL
            and abs(stations[-1] - geom["grain_length_mm"]) < TOL,
            f"saved station order/span differs: {body}",
        )
        body_geometry[body] = geom
        sections[body] = []
        for index, station in enumerate(stations):
            section = section_at(geom, float(station))
            if section["bore_or_tangency_ids"]:
                require(
                    section["material_region_count"] in (1, 2),
                    f"UNSUPPORTED_GEOMETRY: {body}: saved station {station} has {section['material_region_count']} regions",
                )
                sections[body].append({"saved_station_index": index, **section})
        require(
            sections[body]
            and {b["axis_id"] for b in geom["bores"]}
            == {
                identity
                for s in sections[body]
                for identity in s["bore_or_tangency_ids"]
            },
            f"not all four openings covered: {body}",
        )
    cuts, summaries = [], []
    opposed_max, recovery_max = np.zeros(6), np.zeros(6)
    coupon = None
    with np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays:
        for case in results["cases"]:
            for body in BLOCKS:
                matches = [m for m in case["members"] if m["member"] == body]
                require(
                    len(matches) == 1,
                    f"member result is not unique: {case['case_id']}/{body}",
                )
                source = matches[0]
                binding = source["conditional_material"]
                refs = references(body, binding, material, helper)
                require(
                    body not in bindings or binding == bindings[body],
                    f"material scenario changes by case: {body}",
                )
                bindings[body] = binding
                if coupon is None:
                    coupon = helper.rectangular_known_answer(refs)
                prefix = case["case_id"] + "__" + body
                require(
                    source["array_prefix"] == prefix
                    and case["source_force_key"]
                    == case["case_id"] + "_gap_raw_force_n",
                    "saved cut/source force identity differs",
                )
                negative, positive = (
                    arrays[prefix + suffix]
                    for suffix in (
                        "__internal_negative_grain_u_v",
                        "__internal_positive_grain_u_v",
                    )
                )
                shape = (2 * len(geometries["members"][body]["stations_mm"]), 6)
                require(
                    negative.shape == positive.shape == shape
                    and np.isfinite(negative).all()
                    and np.isfinite(positive).all(),
                    f"saved signed cut schema differs: {prefix}",
                )
                residual = np.max(abs(negative + positive), axis=0)
                require(
                    max(residual[:3]) <= 0.1 and max(residual[3:]) <= 2,
                    f"existing whole-member closure bounds exceeded: {prefix}",
                )
                opposed_max = np.maximum(opposed_max, residual)
                for section in sections[body]:
                    station_index = section["saved_station_index"]
                    for index in (2 * station_index, 2 * station_index + 1):
                        nominal = helper.nominal_section(
                            negative[index], section["regions"], refs
                        )
                        nominal["references"] = refs
                        require(
                            abs(
                                nominal["net_section_integrals"]["area_mm2"]
                                - section["net_area_mm2"]
                            )
                            < 1e-7,
                            "analytic retained net area differs",
                        )
                        identity = {
                            "case": case["case_id"],
                            "block": body,
                            "saved_station_index": station_index,
                            "saved_trace_index": index,
                            "station_mm": section["station_mm"],
                            "limit": "before" if index % 2 == 0 else "after",
                            "net_area_mm2": section["net_area_mm2"],
                            "region_count": section["material_region_count"],
                            "bore_or_tangency_ids": section["bore_or_tangency_ids"],
                        }
                        summaries.append(cut_summary(identity, nominal))
                        cuts.append(
                            {
                                **identity,
                                "opposed_positive_half_cut_n_nmm": positive[
                                    index
                                ].tolist(),
                                "opposed_half_sum_n_nmm": (
                                    negative[index] + positive[index]
                                ).tolist(),
                                **nominal,
                            }
                        )
                        recovery_max = np.maximum(
                            recovery_max,
                            np.abs(nominal["reconstructed_minus_source_n_nmm"]),
                        )
    per_block = []
    for body in BLOCKS:
        rows = [r for r in summaries if r["block"] == body]
        expected_count = len(CASES) * len(sections[body]) * 2
        require(len(rows) == expected_count, f"finite trace coverage differs: {body}")
        per_block.append(
            {
                "block": body,
                "recorded_opening_station_count": len(sections[body]),
                "evaluated_trace_count": len(rows),
                "minimum_evaluated_net_area_mm2": min(r["net_area_mm2"] for r in rows),
                "maximum_region_count": max(r["region_count"] for r in rows),
                "conditional_material": bindings[body],
                "peaks": {
                    metric: max(rows, key=lambda r: r[metric])
                    for metric in (
                        *REFERENCE_METRICS,
                        "transverse_shear_over_Fv",
                        "torsional_shear_over_Fv",
                    )
                },
            }
        )
    report = {
        "schema": "knee-spine-two-body-nominal-opening-section-references-v1",
        "status": "FINITE_NOMINAL_REFERENCE_COMPARISON_COMPLETE",
        "saved_data_arithmetic_executed": True,
        **FLAGS,
        "block_ids": list(BLOCKS),
        "case_ids": list(CASES),
        "source_hold_lever_mm": 100,
        "source_climber_weight_lb": 250,
        "source_dynamic_factor": 2,
        "source_horizontal_force_magnitude_n": 300,
        "same_state_dead_load_factor": results["same_state_dead_load_factor"],
        "source_force_state_scope": results["source_force_state_scope"],
        "source_frame_assumptions": results["source_frame_assumptions"],
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in PINS.items()
        },
        "producer_sha256": pins[Path(__file__).resolve()],
        "assumptions": [
            *helper.ASSUMPTIONS[:-1],
            "Existing per-spine DF-L No.2 nominal-2x6 CF-only references and their saved factor scenario are retained; no new adjustment, strength enhancement or torsion allowable is supplied.",
        ],
        "reference_scope": "The saved nominal-2x6 DF-L No.2 CF-only material bindings and factor scenario are retained. No new duration, flatwise, stability, regional size or torsional strength factor is applied.",
        "scope": "Only saved bore/tangency cuts of the two outer knee spines. No new station, frame response, local bore-wall traction distribution, notch/splitting/endbridge capacity or continuous-station maximum is established.",
        "cut_convention": geometries["cut_trace_order"],
        "opposed_half_scope": "The complete negative-grain-half cut supplies the stress comparison; its saved opposed positive-half trace supplies equilibrium accounting, not a reversed tension/compression state.",
        "independent_peaks_summed": False,
        "geometry": body_geometry,
        "opening_sections": sections,
        "rectangle_known_answer": coupon,
        "accounting": {
            "max_opposed_half_component_error_n_nmm": opposed_max.tolist(),
            "max_regional_component_recovery_error_n_nmm": recovery_max.tolist(),
            "balancing_free_couples_added": 0,
        },
        "evaluated_trace_count": len(summaries),
        "all_evaluated_nominal_reference_indices_below_one": all(
            r[metric] <= 1 for r in summaries for metric in REFERENCE_METRICS
        ),
        "per_block": per_block,
        "cut_summaries": summaries,
        "cuts": cuts,
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    dump(output / "checks.json", report)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    receipt = {
        "schema": "knee-spine-nominal-opening-section-execution-receipt-v1",
        "status": "PARENT_ARITHMETIC_COMPLETE",
        "output": str(output.relative_to(ROOT)),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "source_and_producer_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in pins.items()
        },
        "sources_authenticated_before_and_after": True,
        "rectangle_known_answer_count": 1,
        "evaluated_trace_count": len(summaries),
        "all_evaluated_nominal_reference_indices_below_one": report[
            "all_evaluated_nominal_reference_indices_below_one"
        ],
        "output_sha256": {
            name: sha(output / name) for name in ("checks.json", "producer.py.snapshot")
        },
        **FLAGS,
    }
    dump(output / "receipt.json", receipt)
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "checks_sha256": sha(output / "checks.json"),
                "receipt_sha256": sha(output / "receipt.json"),
                "evaluated_trace_count": len(summaries),
                "all_evaluated_nominal_reference_indices_below_one": report[
                    "all_evaluated_nominal_reference_indices_below_one"
                ],
            },
            indent=2,
        )
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)


if __name__ == "__main__":
    main()

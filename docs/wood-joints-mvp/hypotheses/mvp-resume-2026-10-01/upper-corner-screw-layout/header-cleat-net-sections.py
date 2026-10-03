"""Finite nominal retained-wood comparisons for six frozen header cleat bodies.

Parent executes build(output). Full strips enclosing longitudinal circular
holes are omitted deliberately; actual transverse slots are retained. This
reuses the frozen rectangle calculator without a frame, native or CAD run.
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
CONTRACT = HERE / "rawlocal/header-local-transfer/attempt01"
FEATURES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
RAW = HERE / "rawlocal/header-cleat-net-sections"
MATERIAL = (
    BASE.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
)
BLOCKS = (
    "center_post_cleat_left",
    "center_post_cleat_right",
    "center_principal_cleat_left",
    "center_principal_cleat_right",
    "knee_outer_left_inner_frame_block",
    "knee_outer_right_inner_frame_block",
)
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    MEMBER
    / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBER
    / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER
    / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    CONTRACT
    / "inputs.json": "cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b",
    CONTRACT
    / "model.json": "eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52",
    CONTRACT
    / "receipt.json": "3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8",
    HERE
    / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE
    / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE
    / "remaining-net-sections.py": "acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129",
    BASE
    / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    HERE
    / "frame-250-attempt02/comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE
    / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
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
TOL = 1e-6
METRICS = (
    "normal_reference_sum",
    "total_tension_over_Ft",
    "total_compression_over_Fc",
    "absolute_bending_over_Fb",
    "same_state_shear_bound_over_Fv",
    "transverse_shear_over_Fv",
    "torsional_shear_over_Fv",
)


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


def load_helper(filename, name):
    """Load authenticated definitions only; no producer run/main is called."""
    sys.dont_write_bytecode = True
    path = HERE / filename
    require(sha(path) == PINS[path], f"helper differs: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def opening_geometry(body, record, surface, grain, pins):
    """Authenticate six finished planes and four nonintersecting full bores."""
    g = record["geometry"]
    frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
    require(
        np.max(abs(frame - [[0, 0, 1], [1, 0, 0], [0, 1, 0]])) < 1e-8,
        "grain frame differs",
    )
    require(
        np.max(abs(np.array(grain["material_axes_global_xyz"]["L"]) - frame[0])) < 1e-8,
        "material grain differs",
    )
    start = np.array(g["start"])
    width, depth = g["width_mm"], g["depth_mm"]
    length = float(np.dot(np.array(g["end"]) - start, frame[0]))
    expected = (
        (88.9, 88.9, 128.9)
        if "center_post" in body
        else (83.9, 139.7, 134.7)
        if "center_principal" in body
        else (88.9, 133.35, 139.0)
    )
    require(
        max(abs(np.array([width, depth, length]) - expected)) < TOL,
        "finished envelope differs",
    )
    require(
        not record["replaced_original_bore_features"]
        and record["recess_source"] is None,
        "changed openings",
    )
    step = ROOT / record["current_finished_step"]
    digest = surface["step_binding"]["file_sha256"]
    require(
        digest == record["current_finished_step_sha256"] and sha(step) == digest,
        "STEP binding differs",
    )
    pins[step] = digest
    features = surface["features"]
    require(len(features) == 10, "six planes and four cylinders required")
    saved = {b["id"]: b for b in record["bore_or_passage_intervals"]}
    planes, transverse, longitudinal = set(), [], []
    for feature in features:
        if feature["surface_kind"] == "PLANE":
            plane = feature["plane"]
            normal = np.array(plane["normal_global_xyz"])
            local = frame @ normal
            axis = int(np.argmax(abs(local)))
            require(
                abs(abs(local[axis]) - 1) < TOL
                and max(abs(np.delete(local, axis))) < TOL,
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
            require(
                abs(bounds[side] - coordinate) < TOL and (axis, side) not in planes,
                "finished bounding plane differs",
            )
            planes.add((axis, side))
            continue
        require(feature["surface_kind"] == "CYLINDER", "unsupported finished surface")
        cylinder = feature["cylinder"]
        require(
            cylinder["material_side_geometry"] == "bore_like",
            "cylinder is not an opening",
        )
        point = frame @ (np.array(cylinder["axis_origin_global_xyz_mm"]) - start)
        direction = frame @ np.array(cylinder["axis_unit_global_xyz"])
        axis = int(np.argmax(abs(direction)))
        require(
            axis in (0, 1)
            and abs(abs(direction[axis]) - 1) < TOL
            and max(abs(np.delete(direction, axis))) < TOL,
            "unsupported bore direction",
        )
        radius = cylinder["radius_mm"]
        require(
            abs(radius - (3.75 if "knee_outer" in body else 3.65)) < TOL,
            "bore diameter differs",
        )
        span = length if axis == 0 else width
        bounds = [0, length] if axis == 0 else [-width / 2, width / 2]
        ends = sorted(
            point[axis]
            + direction[axis] * np.array(cylinder["axis_parameter_interval_mm"])
        )
        require(
            max(abs(np.array(ends) - bounds)) < TOL, "partial cylinder is unsupported"
        )
        u = feature["trim"]["surface_parameter_bounds"]["u"]
        require(
            abs(u[1] - u[0] - 2 * math.pi) < TOL
            and abs(feature["area_mm2"] - 2 * math.pi * radius * span) < 0.001,
            "trimmed cylinder differs",
        )
        identity = feature["feature_id"]
        require(identity in saved, "bore interval missing")
        interval = saved[identity]
        item = {
            "axis_id": identity,
            "radius_mm": radius,
            "axis_unit_grain_u_v": direction.tolist(),
            "axis_parameter_interval_mm": cylinder["axis_parameter_interval_mm"],
            "source_center_grain_u_v_mm": point.tolist(),
        }
        if axis == 0:
            require(
                abs(interval["lo"]) < TOL and abs(interval["hi"] - length) < TOL,
                "longitudinal interval differs",
            )
            require(
                abs(point[1]) + radius < width / 2
                and abs(point[2]) + radius < depth / 2,
                "longitudinal hole meets an edge",
            )
            item["disk_center_uv_mm"] = point[1:].tolist()
            item["full_v_strip_mm"] = [
                float(point[2] - radius),
                float(point[2] + radius),
            ]
            longitudinal.append(item)
        else:
            require(
                abs(interval["lo"] - (point[0] - radius)) < TOL
                and abs(interval["hi"] - (point[0] + radius)) < TOL,
                "transverse interval differs",
            )
            require(
                radius < point[0] < length - radius
                and abs(point[2]) + radius < depth / 2,
                "transverse bore meets an edge",
            )
            item.update(
                station_mm=float(point[0]),
                transverse_center_mm=float(point[2]),
                removed_interval_axis=2,
            )
            transverse.append(item)
    require(
        len(planes) == 6
        and len(transverse) == len(longitudinal) == 2
        and len(saved) == 4,
        "opening census differs",
    )
    require(
        abs(transverse[0]["station_mm"] - transverse[1]["station_mm"])
        > sum(b["radius_mm"] for b in transverse) + TOL,
        "transverse cylinders overlap",
    )
    for first, second in combinations(longitudinal, 2):
        require(
            abs(first["disk_center_uv_mm"][1] - second["disk_center_uv_mm"][1])
            > first["radius_mm"] + second["radius_mm"] + TOL,
            "longitudinal strips overlap",
        )
    for t in transverse:
        for l in longitudinal:
            require(
                abs(t["transverse_center_mm"] - l["disk_center_uv_mm"][1])
                > t["radius_mm"] + l["radius_mm"] + TOL,
                "disk/transverse slot overlap requires another geometry method",
            )
    removed = math.pi * (
        width * sum(b["radius_mm"] ** 2 for b in transverse)
        + length * sum(b["radius_mm"] ** 2 for b in longitudinal)
    )
    volume = width * depth * length - removed
    actual = g["geometry_diagnostics"]["actual_step_volume_mm3"]
    require(
        abs(volume - actual) < 0.001, "analytic openings differ from saved solid volume"
    )
    return {
        "block": body,
        "grain_frame_rows_xyz": frame.tolist(),
        "grain_length_mm": length,
        "width_depth_mm": [width, depth],
        "bores": transverse,
        "longitudinal_holes": longitudinal,
        "analytic_finished_volume_mm3": volume,
        "saved_finished_volume_mm3": actual,
        "finished_step_path": str(step.relative_to(ROOT)),
        "finished_step_sha256": digest,
    }


def subset_section(geom, station, timber):
    """Keep rectangles wholly inside the physical rectangle-minus-slots/disks."""
    physical_slots = timber.section(geom, station)
    strips = [b["full_v_strip_mm"] for b in geom["longitudinal_holes"]]
    regions = [
        {"bounds_uv_mm": [r["bounds_uv_mm"][0], v]}
        for r in physical_slots["regions"]
        for v in timber.retained(r["bounds_uv_mm"][1], strips)
    ]
    subset_area = sum(
        (u[1] - u[0]) * (v[1] - v[0]) for u, v in (r["bounds_uv_mm"] for r in regions)
    )
    actual_area = physical_slots["net_area_mm2"] - math.pi * sum(
        b["radius_mm"] ** 2 for b in geom["longitudinal_holes"]
    )
    for region in regions:
        bounds = np.array(region["bounds_uv_mm"])
        for hole in geom["longitudinal_holes"]:
            center = np.array(hole["disk_center_uv_mm"])
            nearest = np.maximum(bounds[:, 0], np.minimum(center, bounds[:, 1]))
            require(
                np.linalg.norm(nearest - center) >= hole["radius_mm"] - TOL,
                "subset enters a circular opening",
            )
    require(0 < subset_area <= actual_area + TOL, "invalid retained material area")
    return {
        "station_mm": station,
        "net_area_mm2": subset_area,
        "material_region_count": len(regions),
        "regions": regions,
        "actual_opening_area_mm2": actual_area,
        "physical_transverse_slot_regions": physical_slots["regions"],
        "actual_longitudinal_disk_ids": [
            b["axis_id"] for b in geom["longitudinal_holes"]
        ],
        "transverse_bore_or_tangency_ids": physical_slots["bore_or_tangency_ids"],
        "omitted_sound_wood_area_mm2": actual_area - subset_area,
        "omitted_sound_wood_fraction_of_actual_net_area": (actual_area - subset_area)
        / actual_area,
        "region_scope": "Artificial retained rectangles; physical ligaments need not be disconnected. No local-stress-bound claim.",
    }


def action_cut(actions, geometry, station, before):
    """Independently retain every same-half force, arm and free couple."""
    frame = np.array([geometry[k] for k in ("axis", "section_u", "section_v")])
    datum = np.array(geometry["start"]) + station * frame[0]
    value = np.zeros(6)
    for action in actions:
        delta = action["station_mm"] - station
        if delta > TOL or (before and abs(delta) <= TOL):
            continue
        force = np.array(action["force_n"])
        value[:3] -= force
        value[3:] -= (
            np.cross(np.array(action["point_mm"]) - datum, force)
            + action["free_moment_nmm"]
        )
    return np.r_[frame @ value[:3], frame @ value[3:]]


def build(output: str | Path) -> dict:
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW.resolve())
        and output != RAW.resolve()
        and not output.exists(),
        "fresh owned raw output child required",
    )
    producer = Path(__file__).resolve()
    pins = {**PINS, producer: sha(producer)}
    authenticate(pins)
    results, geometries, surfaces = (
        read(MEMBER / "member-results.json"),
        read(MEMBER / "geometry.json"),
        read(FEATURES),
    )
    model, inputs, receipt = (
        read(CONTRACT / "model.json"),
        read(CONTRACT / "inputs.json"),
        read(CONTRACT / "receipt.json"),
    )
    require(
        receipt["status"] == "PREPARED_HEADER_INPUT_CONTRACT_FOR_METHOD_SELECTION",
        "input contract status differs",
    )
    for name in ("model.json", "inputs.json"):
        require(
            receipt["output_sha256"][name] == pins[CONTRACT / name],
            "contract receipt differs",
        )
    require(
        tuple(c["case_id"] for c in results["cases"])
        == tuple(c["case_id"] for c in inputs["cases"])
        == CASES,
        "case census differs",
    )
    for path in (
        HERE / "frame-250-attempt02/comparison.json",
        HERE / "frame-250-attempt02/response.npz",
        FEATURES,
    ):
        require(
            results["source_sha256"][str(path.relative_to(ROOT))] == pins[path],
            "member/source binding differs",
        )
    helper = load_helper("corner-net-section.py", "header_cleat_nominal_rectangles")
    timber = load_helper("corner-timber-sections.py", "header_cleat_opening_geometry")
    summaries_helper = load_helper(
        "remaining-net-sections.py", "header_cleat_cut_summaries"
    )
    require(
        helper.TORSION_SOURCE == BASE / "member_stability.py",
        "torsion dependency differs",
    )
    base_properties = read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"]
    for body in BLOCKS:
        material = inputs["existing_header_evidence"]["conditional_material"][body]
        for key, value in material["CF_only_reference_mpa"].items():
            expected = (
                base_properties[key] * material["CF"].get(key, 1) * helper.PSI_MPA
            )
            require(
                abs(value - expected) < 1e-12,
                "per-member existing CF-only reference differs",
            )
    coupon = helper.rectangular_known_answer(
        inputs["existing_header_evidence"]["conditional_material"][BLOCKS[0]][
            "CF_only_reference_mpa"
        ]
    )
    surface_by_id = {r["member_id"]: r for r in surfaces["records"]}
    body_geometry, sections, summaries, cuts = {}, {}, [], []
    saved_area_crosschecks = []
    accounting = {
        k: 0.0
        for k in (
            "max_action_cut_force_difference_n",
            "max_action_cut_moment_difference_nmm",
            "max_opposed_half_force_error_n",
            "max_opposed_half_moment_error_nmm",
            "max_regional_force_recovery_error_n",
            "max_regional_moment_recovery_error_nmm",
        )
    }
    with np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays:
        for body in BLOCKS:
            record = geometries["members"][body]
            frozen = model["bodies"][body]
            require(
                frozen["member_geometry"] == record
                and frozen["finished_surface_record"] == surface_by_id[body],
                "frozen body geometry differs",
            )
            geom = opening_geometry(
                body, record, surface_by_id[body], frozen["grain_override"], pins
            )
            body_geometry[body] = geom
            own_sections = [
                subset_section(geom, float(s), timber) for s in record["stations_mm"]
            ]
            sections[body] = own_sections
            for saved_section in geometries["saved_matching_finished_sections"]:
                if saved_section["member"] != body:
                    continue
                section = min(
                    own_sections,
                    key=lambda s: abs(s["station_mm"] - saved_section["station_mm"]),
                )
                require(
                    abs(section["station_mm"] - saved_section["station_mm"]) < TOL
                    and saved_section["source_step_sha256"]
                    == geom["finished_step_sha256"],
                    "saved exact section binding differs",
                )
                difference = (
                    section["actual_opening_area_mm2"]
                    - saved_section["properties"]["area_mm2"]
                )
                require(
                    abs(difference) < 0.001,
                    "analytic circle/slot area differs from saved exact section",
                )
                saved_area_crosschecks.append(
                    {
                        "block": body,
                        "plane_id": saved_section["plane_id"],
                        "station_mm": section["station_mm"],
                        "actual_opening_area_mm2": section["actual_opening_area_mm2"],
                        "saved_exact_area_mm2": saved_section["properties"]["area_mm2"],
                        "analytic_minus_saved_area_mm2": difference,
                    }
                )
            for case, contract_case in zip(
                results["cases"], inputs["cases"], strict=True
            ):
                source = next(m for m in case["members"] if m["member"] == body)
                binding = source["conditional_material"]
                require(
                    binding
                    == inputs["existing_header_evidence"]["conditional_material"][body]
                    and binding["design_resistance_established"] is False,
                    "conditional material differs",
                )
                refs = binding["CF_only_reference_mpa"]
                interface = next(
                    i for i in contract_case["interfaces"] if i["block"] == body
                )
                actions = interface["complete_block_actions"]
                require(
                    len(actions) == source["point_action_count"] == 40
                    and [a["source_id"] for a in actions] == record["point_action_ids"],
                    "complete action census differs",
                )
                prefix = source["array_prefix"]
                require(
                    np.max(
                        abs(
                            arrays[prefix + "__point_force_free_couple_xyz"]
                            - np.array(
                                [a["force_n"] + a["free_moment_nmm"] for a in actions]
                            )
                        )
                    )
                    < 1e-10,
                    "signed source actions differ",
                )
                require(
                    np.max(
                        abs(
                            arrays[body + "__point_xyz_mm"]
                            - np.array([a["point_mm"] for a in actions])
                        )
                    )
                    < TOL
                    and np.max(
                        abs(
                            arrays[body + "__point_stations_mm"]
                            - np.array([a["station_mm"] for a in actions])
                        )
                    )
                    < TOL,
                    "point/partition datum differs",
                )
                negative, positive = (
                    arrays[prefix + suffix]
                    for suffix in (
                        "__internal_negative_grain_u_v",
                        "__internal_positive_grain_u_v",
                    )
                )
                require(
                    negative.shape == positive.shape == (2 * len(own_sections), 6)
                    and np.isfinite(negative).all()
                    and np.isfinite(positive).all(),
                    "saved trace shape/value differs",
                )
                residual = np.max(abs(negative + positive), axis=0)
                require(
                    max(residual[:3]) <= 0.1 and max(residual[3:]) <= 2,
                    "source whole-member closure exceeded",
                )
                for key, value in zip(
                    (
                        "max_opposed_half_force_error_n",
                        "max_opposed_half_moment_error_nmm",
                    ),
                    (max(residual[:3]), max(residual[3:])),
                    strict=True,
                ):
                    accounting[key] = max(accounting[key], float(value))
                for station_index, section in enumerate(own_sections):
                    for index in (2 * station_index, 2 * station_index + 1):
                        delta = (
                            action_cut(
                                actions,
                                record["geometry"],
                                section["station_mm"],
                                index % 2 == 0,
                            )
                            - negative[index]
                        )
                        require(
                            max(abs(delta[:3])) < 1e-7 and max(abs(delta[3:])) < 1e-5,
                            "full signed action cut differs",
                        )
                        accounting["max_action_cut_force_difference_n"] = max(
                            accounting["max_action_cut_force_difference_n"],
                            float(max(abs(delta[:3]))),
                        )
                        accounting["max_action_cut_moment_difference_nmm"] = max(
                            accounting["max_action_cut_moment_difference_nmm"],
                            float(max(abs(delta[3:]))),
                        )
                        nominal = helper.nominal_section(
                            negative[index], section["regions"], refs
                        )
                        nominal["references"] = refs
                        summary = summaries_helper.cut_summary(
                            case["case_id"], body, index, section, nominal
                        )
                        summary.update(
                            actual_opening_area_mm2=section["actual_opening_area_mm2"],
                            omitted_sound_wood_area_mm2=section[
                                "omitted_sound_wood_area_mm2"
                            ],
                            omitted_sound_wood_fraction_of_actual_net_area=section[
                                "omitted_sound_wood_fraction_of_actual_net_area"
                            ],
                        )
                        summaries.append(summary)
                        cuts.append(
                            {
                                "summary": summary,
                                "full_signed_action_cut_difference_n_nmm": delta.tolist(),
                                "nominal_section": nominal,
                            }
                        )
                        recovery = np.array(nominal["reconstructed_minus_source_n_nmm"])
                        accounting["max_regional_force_recovery_error_n"] = max(
                            accounting["max_regional_force_recovery_error_n"],
                            float(max(abs(recovery[:3]))),
                        )
                        accounting["max_regional_moment_recovery_error_nmm"] = max(
                            accounting["max_regional_moment_recovery_error_nmm"],
                            float(max(abs(recovery[3:]))),
                        )
    per_block = []
    for body in BLOCKS:
        own = [s for s in summaries if s["block"] == body]
        per_block.append(
            {
                "block": body,
                "evaluated_trace_count": len(own),
                "recorded_station_count": len(sections[body]),
                "minimum_actual_opening_area_mm2": min(
                    s["actual_opening_area_mm2"] for s in own
                ),
                "minimum_retained_subset_area_mm2": min(s["net_area_mm2"] for s in own),
                "maximum_omitted_sound_wood_fraction": max(
                    s["omitted_sound_wood_fraction_of_actual_net_area"] for s in own
                ),
                "peaks": {key: max(own, key=lambda s: s[key]) for key in METRICS},
                "per_case": [
                    {
                        "case_id": case,
                        "trace_count": len(
                            rows := [s for s in own if s["case"] == case]
                        ),
                        "peaks": {
                            key: max(rows, key=lambda s: s[key]) for key in METRICS
                        },
                    }
                    for case in CASES
                ],
            }
        )
    require(
        len(per_block) == 6
        and sum(len(b["per_case"]) for b in per_block) == 36
        and len(cuts) == 1968
        and len(saved_area_crosschecks) == 9,
        "finite body/case/trace census differs",
    )
    report = {
        "schema": "header-cleat-nominal-retained-subset-v1",
        "status": "COMPLETE_HEADER_CLEAT_NOMINAL_SUBSET_COMPARISONS",
        **FLAGS,
        "source_hold_lever_mm": 100,
        "case_ids": list(CASES),
        "block_ids": list(BLOCKS),
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in pins.items()
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "working_hypotheses": [
            "Full v strips spanning the finished u width enclose the two longitudinal circular holes. The additional sound wood in these strips is omitted from all nominal resistance comparisons.",
            *summaries_helper.ASSUMPTIONS,
        ],
        "limits": [
            "Only saved finite stations and before/after action traces; no continuous-station maximum claim.",
            "The retained rectangles are an artificial material subset, not the physical topology. Common strain, area force sharing and common twist remain declared assumptions.",
            "Omitting sound wood does not establish a local stress bound or exact perforated-section torsion; notch, splitting, endbridge, perpendicular-tension and group resistances remain unassigned.",
            "Original same-state point actions and free couples are preserved, without a new physical annular pressure-map cut reconstruction or frame feedback.",
            "Per-member existing normal-duration CF-only hypotheses remain unchanged; the separate parent duration/dead-load checks are not adopted here.",
        ],
        "cut_convention": "Full saved negative-grain-half internal [N,Vu,Vv,T,Mu,Mv], N positive in tension; positive-half traces check closure and are not inverted as separate load states.",
        "conditional_material_by_block": {
            body: inputs["existing_header_evidence"]["conditional_material"][body]
            for body in BLOCKS
        },
        "source_force_state_scope": inputs["source_force_state_scope"],
        "rectangular_known_answer": coupon,
        "geometry": body_geometry,
        "opening_sections": sections,
        "saved_exact_section_area_crosschecks": saved_area_crosschecks,
        "accounting": accounting,
        "evaluated_trace_count": len(cuts),
        "body_case_count": 36,
        "all_evaluated_nominal_subset_reference_indices_below_one": all(
            s["normal_reference_sum"] <= 1 and s["same_state_shear_bound_over_Fv"] <= 1
            for s in summaries
        ),
        "global_peaks": {key: max(summaries, key=lambda s: s[key]) for key in METRICS},
        "per_block": per_block,
        "cuts": cuts,
    }
    authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    dump(output / "checks.json", report)
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    dump(
        output / "receipt.json",
        {
            "status": report["status"],
            **FLAGS,
            "source_sha256": report["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
        },
    )
    return {
        "status": report["status"],
        "output": str(output.relative_to(ROOT)),
        "checks_sha256": sha(output / "checks.json"),
        "receipt_sha256": sha(output / "receipt.json"),
        "body_case_count": 36,
        "evaluated_trace_count": len(cuts),
        "all_evaluated_nominal_subset_reference_indices_below_one": report[
            "all_evaluated_nominal_subset_reference_indices_below_one"
        ],
        "global_peaks": report["global_peaks"],
        "accounting": accounting,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2, sort_keys=True))

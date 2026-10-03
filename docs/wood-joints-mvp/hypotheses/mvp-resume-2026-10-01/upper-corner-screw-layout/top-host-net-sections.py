"""Finite nominal top-host bore sections, using complete frozen member actions.

Parent executes build(output). No frame, native or CAD solve is performed.
The current corrected side bores replace the original cylinders; the rail
bores are unchanged. Common strain, area sharing and twist remain hypotheses.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
MEMBER = BASE / "member-screen-attempt02/four-screw-layout01"
FEATURES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
PROPOSAL = BASE / "top-corner-correction/proposal.json"
MODEL = HERE / "operators-attempt02/model.json"
MATERIAL = (
    BASE.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
)
RAW = HERE / "rawlocal/top-host-net-sections"
SECTION_SOURCE = RAW / "attempt02"
SECTION_PINS = {
    SECTION_SOURCE
    / "checks.json": "7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9",
    SECTION_SOURCE
    / "receipt.json": "486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29",
    SECTION_SOURCE
    / "producer.py.snapshot": "c8c6e3c23bfe5e7d6999160546bc8f6ad106c178219307aa1d984367fcd80364",
}
HOSTS = ("base_rail_top", "base_side_left", "base_side_right")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    MEMBER
    / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBER
    / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER
    / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    FEATURES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    PROPOSAL: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
    HERE
    / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE
    / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE
    / "remaining-net-sections.py": "acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129",
    BASE
    / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    BASE
    / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    HERE
    / "frame-250-attempt02/comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    HERE
    / "frame-250-attempt02/response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    BASE.parent
    / "upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf": "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
}
FLAGS = dict.fromkeys(
    (
        "formal_qualification",
        "native_readiness",
        "mechanics_executed",
        "compatibility_solved",
        "new_resistance_established",
        "complete_joint_acceptance",
        "physical_release",
    ),
    False,
)
METRICS = (
    "normal_reference_sum",
    "total_tension_over_Ft",
    "total_compression_over_Fc",
    "absolute_bending_over_Fb",
    "same_state_shear_bound_over_Fv",
    "transverse_shear_over_Fv",
    "torsional_shear_over_Fv",
)
GEOM_TOL = 1e-5
PARTITION_TOL = 1e-6
SCENARIOS = {"original_CD1": 1.0, "conditional_peak_CD1_25": 1.25}


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
    for path, digest in pins.items():
        require(sha(path) == digest, f"STOP: frozen source differs: {path}")


def helper(filename, name):
    """Authenticated definitions only; do not call any helper producer."""
    sys.dont_write_bytecode = True
    path = HERE / filename
    require(sha(path) == PINS[path], f"STOP: helper differs: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(
        spec is not None and spec.loader is not None, f"STOP: import missing: {path}"
    )
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def outer_rectangle_function():
    """Reuse only the frozen planar-profile definitions, without frame imports."""
    path = BASE / "member_screen.py"
    tree = ast.parse(path.read_text())
    definitions = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name in {"basis", "rectangle_at"}
    ]
    require(
        {n.name for n in definitions} == {"basis", "rectangle_at"}
        and len(definitions) == 2,
        "STOP: outer-profile definitions differ",
    )
    namespace = {"np": np, "TOL": GEOM_TOL}
    exec(  # noqa: S102 - Named pure functions from hash-authenticated local source.
        compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec"),
        namespace,
    )
    return namespace["rectangle_at"]


def host_geometry(body, record, surface, model, proposal, pins):
    g = record["geometry"]
    frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
    require(
        np.max(abs(frame @ frame.T - np.eye(3))) < 1e-8
        and np.linalg.det(frame) > 0.999999,
        f"STOP: invalid frame: {body}",
    )
    grain = model["material_binding"]["orientation_overrides"][body]
    axes = grain["material_axes_global_xyz"]
    require(
        np.max(abs(frame - np.array([axes[k] for k in ("L", "R", "T")]))) < 1e-7,
        f"STOP: material frame differs: {body}",
    )
    require(record["recess_source"] is None, f"STOP: unsupported recess: {body}")
    original = surface["step_binding"]
    require(
        original["file_sha256"] == record["original_finished_step_sha256"],
        f"STOP: original STEP differs: {body}",
    )
    pins[ROOT / original["path"]] = original["file_sha256"]
    current_step = ROOT / record["current_finished_step"]
    pins[current_step] = record["current_finished_step_sha256"]
    side = body != "base_rail_top"
    if side:
        require(
            proposal["proposal_step_sha256"][str(current_step.relative_to(ROOT))]
            == pins[current_step],
            f"STOP: corrected STEP binding differs: {body}",
        )
        require(
            set(record["replaced_original_bore_features"])
            == {body + "/facet002", body + "/facet004"},
            f"STOP: replaced features differ: {body}",
        )
    else:
        require(
            not record["replaced_original_bore_features"]
            and pins[current_step] == original["file_sha256"],
            "STOP: rail openings changed",
        )
    bores = []
    for prop in proposal["proposals"]:
        own_side = (
            "base_side_left"
            if prop["block"] == "top_outer_left_cleat"
            else "base_side_right"
        )
        for axis in prop["axes"]:
            if ("/side_" in axis["axis_id"]) != side or (side and body != own_side):
                continue
            identity = axis["axis_id"]
            matched = []
            for feature in surface["features"]:
                if feature["surface_kind"] != "CYLINDER" or (
                    side
                    and feature["feature_id"]
                    not in record["replaced_original_bore_features"]
                ):
                    continue
                cylinder = feature["cylinder"]
                direction = np.array(cylinder["axis_unit_global_xyz"])
                delta = (
                    np.array(axis["old_axis_point_mm"])
                    - cylinder["axis_origin_global_xyz_mm"]
                )
                if (
                    np.linalg.norm(delta - np.dot(delta, direction) * direction)
                    < GEOM_TOL
                ):
                    matched.append(feature)
            require(
                len(matched) == 1,
                f"STOP: bore line not uniquely supported: {body}/{identity}",
            )
            feature = matched[0]
            cylinder = feature["cylinder"]
            direction = np.array(cylinder["axis_unit_global_xyz"])
            local_direction = frame @ direction
            require(
                max(abs(local_direction[[0, 2]])) < GEOM_TOL
                and abs(abs(local_direction[1]) - 1) < GEOM_TOL,
                f"STOP: nonaligned full-width bore: {identity}",
            )
            require(
                cylinder["material_side_geometry"] == "bore_like"
                and abs(cylinder["radius_mm"] - 3.75) < GEOM_TOL,
                f"STOP: original bore interpretation differs: {identity}",
            )
            old_point = frame @ (
                np.array(cylinder["axis_origin_global_xyz_mm"]) - g["start"]
            )
            old_ends = sorted(
                old_point[1]
                + local_direction[1] * np.array(cylinder["axis_parameter_interval_mm"])
            )
            require(
                max(abs(np.array(old_ends) - [-g["width_mm"] / 2, g["width_mm"] / 2]))
                < GEOM_TOL,
                f"STOP: partial cylinder unsupported: {identity}",
            )
            angular = feature["trim"]["surface_parameter_bounds"]["u"]
            require(
                abs(angular[1] - angular[0] - 2 * math.pi) < GEOM_TOL
                and abs(feature["area_mm2"] - 2 * math.pi * 3.75 * g["width_mm"])
                < 0.001,
                f"STOP: cylinder trim differs: {identity}",
            )
            radius = axis["proposed_CAD_bore_envelope_mm"] / 2
            require(
                abs(radius - (4.5 if side else 3.75)) < GEOM_TOL,
                f"STOP: reviewed bore diameter differs: {identity}",
            )
            opening_id = identity + "/corrected_bore" if side else feature["feature_id"]
            interval = next(
                (
                    b
                    for b in record["bore_or_passage_intervals"]
                    if b["id"] == opening_id
                ),
                None,
            )
            require(interval is not None, f"STOP: saved interval absent: {opening_id}")
            center = frame @ (np.array(axis["proposed_axis_point_mm"]) - g["start"])
            station = (interval["lo"] + interval["hi"]) / 2
            require(
                abs(center[0] - station) < GEOM_TOL
                and abs(interval["radius_mm"] - radius) < GEOM_TOL
                and abs(interval["hi"] - interval["lo"] - 2 * radius) < GEOM_TOL,
                f"STOP: bore station/radius binding differs: {identity}",
            )
            if side:
                replacement = next(
                    v
                    for v in proposal["side_host_bore_replacements"]
                    if v["host"] == body
                )
                bore_index = int(identity.rsplit("_", 1)[1]) - 1
                require(
                    abs(
                        replacement["new_bore_void_volumes_mm3"][bore_index]
                        - math.pi * radius**2 * g["width_mm"]
                    )
                    < 0.001
                    and abs(
                        replacement["old_bore_void_volumes_replaced_mm3"][bore_index]
                        - math.pi * 3.75**2 * g["width_mm"]
                    )
                    < 0.001,
                    f"STOP: full-width replacement volume differs: {identity}",
                )
            else:
                require(
                    axis["old_axis_point_mm"] == axis["proposed_axis_point_mm"],
                    f"STOP: rail line moved: {identity}",
                )
            bores.append(
                {
                    "axis_id": identity,
                    "opening_id": opening_id,
                    "original_feature_id": feature["feature_id"],
                    "station_mm": station,
                    "projected_proposal_station_mm": float(center[0]),
                    "radius_mm": radius,
                    "transverse_center_mm": float(center[2]),
                    "removed_interval_axis": 2,
                    "axis_unit_global_xyz": direction.tolist(),
                    "saved_interval_mm": [interval["lo"], interval["hi"]],
                    "full_width_void_volume_mm3": math.pi * radius**2 * g["width_mm"],
                }
            )
    require(
        len(bores) == (2 if side else 4),
        f"STOP: structural bore census differs: {body}",
    )
    return {
        "body": body,
        "grain_frame_rows_xyz": frame.tolist(),
        "material_orientation": grain,
        "width_depth_mm": [g["width_mm"], g["depth_mm"]],
        "bores": bores,
        "finished_step_path": str(current_step.relative_to(ROOT)),
        "finished_step_sha256": pins[current_step],
        "original_surface_step_sha256": original["file_sha256"],
        "scope": "Saved outer planes minus unchanged rail or proposal-bound full-width corrected side cylinders. No CAD replay; replaced side cylinders are excluded.",
    }


def selected_sections(body, record, geom, rectangle_at, section_at):
    sections = []
    opening_ids = {b["opening_id"] for b in geom["bores"]}
    for index, station in enumerate(record["stations_mm"]):
        active = [
            b
            for b in geom["bores"]
            if b["saved_interval_mm"][0] - PARTITION_TOL
            <= station
            <= b["saved_interval_mm"][1] + PARTITION_TOL
        ]
        if not active:
            continue
        unsupported = [
            b["id"]
            for b in record["bore_or_passage_intervals"]
            if b["id"] not in opening_ids
            and b["lo"] - GEOM_TOL <= station <= b["hi"] + GEOM_TOL
        ]
        require(
            not unsupported,
            f"STOP: unsupported overlapping opening: {body}, station {station}, features {unsupported}",
        )
        rectangle = rectangle_at(
            station, record["geometry"], record["profile_planes"], []
        )
        require(
            rectangle["status"] == "BORE_FREE_FULL_RECTANGLE",
            f"STOP: unsupported outer profile: {body}, station {station}, {rectangle}",
        )
        lo, hi = np.array(rectangle["bounds_uv_mm"])
        center = (lo + hi) / 2
        shifted = {
            "width_depth_mm": (hi - lo).tolist(),
            "bores": [
                {**b, "transverse_center_mm": b["transverse_center_mm"] - center[1]}
                for b in geom["bores"]
            ],
        }
        section = section_at(shifted, float(station))
        for region in section["regions"]:
            region["bounds_uv_mm"] = (
                np.array(region["bounds_uv_mm"]) + center[:, None]
            ).tolist()
            region["centroid_uv_mm"] = (
                np.array(region["centroid_uv_mm"]) + center
            ).tolist()
        require(
            set(section["bore_or_tangency_ids"]) == {b["axis_id"] for b in active},
            f"STOP: selected bore coverage differs: {body}, station {station}",
        )
        require(
            section["net_area_mm2"] > 0
            and all(
                abs(b["transverse_center_mm"] - center[1]) + b["radius_mm"]
                < (hi[1] - lo[1]) / 2
                for b in active
            ),
            f"STOP: bore meets outer edge: {body}, station {station}",
        )
        sections.append(
            {**section, "saved_station_index": index, "outer_profile": rectangle}
        )
    for bore in geom["bores"]:
        for required in [*bore["saved_interval_mm"], bore["station_mm"]]:
            require(
                any(abs(s["station_mm"] - required) < PARTITION_TOL for s in sections),
                f"STOP: saved center/tangency station absent: {body}/{bore['axis_id']}, {required}",
            )
    require(
        len(sections) == (12 if body == "base_rail_top" else 13),
        f"STOP: finite station census differs: {body}",
    )
    return sections


def global_cut(values, points, stations, geometry, station, before):
    """All signed global point forces, moment arms and free couples, once."""
    delta = stations - station
    positive_half = (delta > PARTITION_TOL) | (before & (abs(delta) <= PARTITION_TOL))
    own = ~positive_half
    datum = np.array(geometry["start"]) + station * np.array(geometry["axis"])
    force = -np.sum(values[own, :3], axis=0)
    moment = -np.sum(
        np.cross(points[own] - datum, values[own, :3]) + values[own, 3:], axis=0
    )
    return np.r_[force, moment], datum


def peaks(rows):
    return {metric: max(rows, key=lambda r: r[metric]) for metric in METRICS}


def build(output: str | Path) -> dict:
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW.resolve())
        and output != RAW.resolve()
        and not output.exists(),
        "STOP: fresh owned raw output child required",
    )
    producer = Path(__file__).resolve()
    pins = {**PINS, producer: sha(producer)}
    authenticate(pins)
    results, geometry, surfaces, model, proposal = (
        read(path)
        for path in (
            MEMBER / "member-results.json",
            MEMBER / "geometry.json",
            FEATURES,
            MODEL,
            PROPOSAL,
        )
    )
    require(
        tuple(c["case_id"] for c in results["cases"]) == CASES,
        "STOP: six-case census differs",
    )
    require(
        model["proposed_corner_axes"] == proposal["proposals"]
        and sum(len(p["axes"]) for p in proposal["proposals"]) == 8,
        "STOP: current eight-axis proposal differs",
    )
    for path in (
        MODEL,
        FEATURES,
        HERE / "frame-250-attempt02/comparison.json",
        HERE / "frame-250-attempt02/response.npz",
    ):
        require(
            results["source_sha256"][str(path.relative_to(ROOT))] == pins[path],
            f"STOP: member source binding differs: {path}",
        )
    nominal_helper = helper("corner-net-section.py", "top_host_nominal_sections")
    section_at = helper(
        "corner-timber-sections.py", "top_host_rectangle_openings"
    ).section
    summarize = helper(
        "remaining-net-sections.py", "top_host_cut_summaries"
    ).cut_summary
    rectangle_at = outer_rectangle_function()
    surface_by_id = {s["member_id"]: s for s in surfaces["records"]}
    body_geometry, sections, material = {}, {}, {}
    base = read(MATERIAL)["conditional_DF_L_No2_base_row"]["base_properties"]
    for body in HOSTS:
        record = geometry["members"][body]
        body_geometry[body] = host_geometry(
            body, record, surface_by_id[body], model, proposal, pins
        )
        sections[body] = selected_sections(
            body, record, body_geometry[body], rectangle_at, section_at
        )
        binding = next(
            m for m in results["cases"][0]["members"] if m["member"] == body
        )["conditional_material"]
        require(
            binding["CF"] == {"Fb": 1.3, "Ft_parallel": 1.3, "Fc_parallel": 1.1}
            and binding["design_resistance_established"] is False,
            f"STOP: existing member material differs: {body}",
        )
        for key, value in binding["CF_only_reference_mpa"].items():
            require(
                abs(
                    value
                    - base[key] * binding["CF"].get(key, 1) * nominal_helper.PSI_MPA
                )
                < 1e-12,
                f"STOP: CF-only reference differs: {body}/{key}",
            )
        material[body] = binding
    authenticate(pins)
    coupon = nominal_helper.rectangular_known_answer(
        material[HOSTS[0]]["CF_only_reference_mpa"]
    )
    crosschecks = []
    for saved in geometry["saved_matching_finished_sections"]:
        if saved["member"] != "base_rail_top":
            continue
        matches = [
            s
            for s in sections["base_rail_top"]
            if abs(s["station_mm"] - saved["station_mm"]) < PARTITION_TOL
        ]
        if not matches:
            continue
        require(
            len(matches) == 1
            and saved["source_step_sha256"]
            == body_geometry["base_rail_top"]["finished_step_sha256"],
            "STOP: saved exact rail section binding differs",
        )
        analytic = nominal_helper.area_properties(matches[0]["regions"])
        area_error = analytic["area_mm2"] - saved["properties"]["area_mm2"]
        rail_geometry = geometry["members"]["base_rail_top"]["geometry"]
        rail_frame = np.array(body_geometry["base_rail_top"]["grain_frame_rows_xyz"])
        cut_datum = (
            np.array(rail_geometry["start"]) + saved["station_mm"] * rail_frame[0]
        )
        saved_center_at_cut = rail_frame @ (
            np.array(saved["properties"]["centroid_global_xyz_mm"]) - cut_datum
        )
        center_error = np.array(analytic["centroid_uv_mm"]) - saved_center_at_cut[1:]
        require(
            abs(area_error) < 0.001
            and max(abs(center_error)) < GEOM_TOL
            and abs(saved_center_at_cut[0]) < GEOM_TOL,
            f"STOP: saved exact rail area/centroid differs: {saved['plane_id']}",
        )
        crosschecks.append(
            {
                "plane_id": saved["plane_id"],
                "station_mm": saved["station_mm"],
                "area_difference_mm2": area_error,
                "saved_centroid_at_beam_cut_grain_u_v_mm": saved_center_at_cut.tolist(),
                "source_section_relative_uv_mm_not_used_as_beam_datum": saved[
                    "properties"
                ]["centroid_relative_uv_mm"],
                "centroid_difference_uv_mm": center_error.tolist(),
            }
        )
    require(len(crosschecks) == 2, "STOP: two saved rail center sections required")
    cuts, summaries = [], []
    accounting = dict.fromkeys(
        (
            "max_action_cut_force_difference_n",
            "max_action_cut_moment_difference_nmm",
            "max_opposed_half_force_error_n",
            "max_opposed_half_moment_error_nmm",
            "max_regional_force_recovery_error_n",
            "max_regional_moment_recovery_error_nmm",
        ),
        0.0,
    )
    with np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays:
        for body in HOSTS:
            record = geometry["members"][body]
            frame = np.array(body_geometry[body]["grain_frame_rows_xyz"])
            points, stations = (
                arrays[body + "__point_xyz_mm"],
                arrays[body + "__point_stations_mm"],
            )
            count = len(record["point_action_ids"])
            require(
                points.shape == (count, 3)
                and stations.shape == (count,)
                and np.isfinite(points).all()
                and np.isfinite(stations).all(),
                f"STOP: point geometry census/value differs: {body}",
            )
            for case in results["cases"]:
                source = next(m for m in case["members"] if m["member"] == body)
                require(
                    source["conditional_material"] == material[body]
                    and source["point_action_count"] == count,
                    f"STOP: per-case material/action census differs: {body}/{case['case_id']}",
                )
                prefix = source["array_prefix"]
                values = arrays[prefix + "__point_force_free_couple_xyz"]
                negative, positive = (
                    arrays[prefix + suffix]
                    for suffix in (
                        "__internal_negative_grain_u_v",
                        "__internal_positive_grain_u_v",
                    )
                )
                require(
                    values.shape == (count, 6)
                    and negative.shape
                    == positive.shape
                    == (2 * len(record["stations_mm"]), 6)
                    and all(np.isfinite(a).all() for a in (values, negative, positive)),
                    f"STOP: signed array shape/value differs: {body}/{case['case_id']}",
                )
                residual = np.max(abs(negative + positive), axis=0)
                require(
                    max(residual[:3]) <= 0.1 and max(residual[3:]) <= 2,
                    f"STOP: source whole-member balance exceeded: {body}/{case['case_id']}",
                )
                accounting["max_opposed_half_force_error_n"] = max(
                    accounting["max_opposed_half_force_error_n"],
                    float(max(residual[:3])),
                )
                accounting["max_opposed_half_moment_error_nmm"] = max(
                    accounting["max_opposed_half_moment_error_nmm"],
                    float(max(residual[3:])),
                )
                for section in sections[body]:
                    for index in (
                        2 * section["saved_station_index"],
                        2 * section["saved_station_index"] + 1,
                    ):
                        global_value, datum = global_cut(
                            values,
                            points,
                            stations,
                            record["geometry"],
                            section["station_mm"],
                            index % 2 == 0,
                        )
                        local_value = np.r_[
                            frame @ global_value[:3], frame @ global_value[3:]
                        ]
                        difference = local_value - negative[index]
                        require(
                            max(abs(difference[:3])) < 1e-7
                            and max(abs(difference[3:])) < 1e-5,
                            f"STOP: full GLOBAL action reconstruction differs: {body}/{case['case_id']}/trace {index}: {difference.tolist()}",
                        )
                        accounting["max_action_cut_force_difference_n"] = max(
                            accounting["max_action_cut_force_difference_n"],
                            float(max(abs(difference[:3]))),
                        )
                        accounting["max_action_cut_moment_difference_nmm"] = max(
                            accounting["max_action_cut_moment_difference_nmm"],
                            float(max(abs(difference[3:]))),
                        )
                        duration_results = {}
                        for scenario, duration in SCENARIOS.items():
                            refs = {
                                key: duration * value
                                for key, value in material[body][
                                    "CF_only_reference_mpa"
                                ].items()
                            }
                            nominal = nominal_helper.nominal_section(
                                local_value, section["regions"], refs
                            )
                            nominal["references"] = refs
                            summary = summarize(
                                case["case_id"], body, index, section, nominal
                            )
                            summary["duration_scenario"] = scenario
                            summary["CD"] = duration
                            summaries.append(summary)
                            duration_results[scenario] = {
                                "summary": summary,
                                "nominal_section": nominal,
                            }
                            recovery = np.array(
                                nominal["reconstructed_minus_source_n_nmm"]
                            )
                            accounting["max_regional_force_recovery_error_n"] = max(
                                accounting["max_regional_force_recovery_error_n"],
                                float(max(abs(recovery[:3]))),
                            )
                            accounting["max_regional_moment_recovery_error_nmm"] = max(
                                accounting["max_regional_moment_recovery_error_nmm"],
                                float(max(abs(recovery[3:]))),
                            )
                        cuts.append(
                            {
                                "case": case["case_id"],
                                "body": body,
                                "saved_trace_index": index,
                                "cut_datum_global_xyz_mm": datum.tolist(),
                                "full_signed_cut_global_n_nmm": global_value.tolist(),
                                "full_signed_cut_grain_u_v_n_nmm": local_value.tolist(),
                                "reconstructed_minus_saved_grain_u_v_n_nmm": difference.tolist(),
                                "duration_results": duration_results,
                            }
                        )
    require(
        sum(len(s) for s in sections.values()) == 38
        and len(cuts) == 456
        and len(summaries) == 912,
        "STOP: finite section/trace/scenario census differs",
    )
    comparison = {}
    for scenario, duration in SCENARIOS.items():
        rows = [r for r in summaries if r["duration_scenario"] == scenario]
        comparison[scenario] = {
            "CD": duration,
            "global_peaks": peaks(rows),
            "all_evaluated_nominal_reference_indices_below_one": all(
                r[metric] <= 1 for r in rows for metric in METRICS
            ),
            "per_host": [
                {
                    "body": body,
                    "section_count": len(sections[body]),
                    "trace_count": len(own := [r for r in rows if r["block"] == body]),
                    "peaks": peaks(own),
                    "per_case": [
                        {
                            "case": case,
                            "peaks": peaks([r for r in own if r["case"] == case]),
                        }
                        for case in CASES
                    ],
                }
                for body in HOSTS
            ],
        }
    report = {
        "schema": "top-host-full-action-nominal-net-sections-v1",
        "status": "COMPLETE_FINITE_TOP_HOST_NOMINAL_COMPARISONS",
        **FLAGS,
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in pins.items()
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "source_hold_lever_mm": 100,
        "source_force_state_scope": results["source_force_state_scope"],
        "host_ids": list(HOSTS),
        "case_ids": list(CASES),
        "physical_bore_count": 8,
        "recorded_section_count": 38,
        "evaluated_trace_count": 456,
        "duration_comparison_count": 912,
        "cut_convention": "Complete negative-half GLOBAL internal force/couple at start+s*grain, restored from all signed point forces, arms and free couples, then rotated into the actual grain/u/v frame. N positive in tension. Positive halves check closure; before/after are saved limits, not new cases.",
        "working_hypotheses": [
            *nominal_helper.ASSUMPTIONS[:4],
            "All three hosts retain their saved member-specific CF values Fb=Ft=1.3, Fc=1.1. Original CD=1 is shown alongside hypothetical CD=1.25 for cumulative peak exposure no longer than seven days under pinned NDS Chapter 2. This does not change forces, stiffness, geometry, or duration assumptions of other components.",
            "Outer profiles come from saved finite planes. Unchanged rail full-width bores and corrected side cylinder lines/diameters/void volumes define nominal disconnected rectangles, without a new CAD section.",
        ],
        "limits": [
            "Finite saved bore/center/tangency stations only; no continuous maximum, local bore stress concentration, splitting, notch, perpendicular-grain or group capacity.",
            "Common strain, area sharing, equal shear moduli, end bridges and common twist are explicit working assumptions, not solved joint compatibility or exact perforated-body torsion. Fv comparisons supply no invented torsion allowable.",
            "Corrected side hosts have no matching saved exact CAD section; old side sections remain non-applicable. Only two unchanged rail center sections supply saved area/centroid crosschecks.",
            "The frozen six-case 250 lb dynamic response retains its original 100 mm hold lever and nonunique motion/stability boundary. These signed forces do not establish unique motions or frame stability.",
            "No annular washer traction redistribution, contact update, clamp preload, hardware correction, timber inspection or physical/release acceptance is supplied. All existing HOLD and 47-criterion authority boundaries remain unchanged.",
        ],
        "conditional_material_by_host": material,
        "geometry": body_geometry,
        "opening_sections": sections,
        "saved_exact_rail_section_crosschecks": crosschecks,
        "rectangular_known_answer": coupon,
        "accounting": accounting,
        "duration_comparison": comparison,
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
        "recorded_section_count": 38,
        "evaluated_trace_count": 456,
        "duration_comparison_count": 912,
        "duration_comparison": {
            key: {k: v for k, v in value.items() if k != "per_host"}
            for key, value in comparison.items()
        },
        "accounting": accounting,
    }


def region_faces(region, references, cut, frame):
    """Evaluate four signed midpoint vectors using the saved rectangle method.

    tau_u=Phi_v and tau_v=-Phi_u for positive grain-axis torque. At each
    midpoint one parabolic transverse component vanishes, while the other
    retains 1.5*V/A. Opposing torsion signs are retained, without stacking
    unrelated component peaks or claiming an interior maximum.
    """
    area = region["area_mm2"]
    vu, vv, torque = (region["wrench_at_regional_centroid_n_nmm"][i] for i in (1, 2, 3))
    cu, cv = region["rectangle_torsion"]["face_shear_coefficients_u_v_per_mm3"]
    center = np.array(region["centroid_uv_mm"])
    bounds = np.array(region["bounds_uv_mm"])
    su, sv = 1.5 * vu / area, 1.5 * vv / area
    faces = []
    for axis, label in ((0, "u"), (1, "v")):
        for edge, side in ((0, -1), (1, 1)):
            point = center.copy()
            point[axis] = bounds[axis, edge]
            transverse = np.array([0.0, sv] if axis == 0 else [su, 0.0])
            torsional = np.array(
                [0.0, side * torque * cv] if axis == 0 else [-side * torque * cu, 0.0]
            )
            vector = transverse + torsional
            magnitude = float(np.linalg.norm(vector))
            faces.append(
                {
                    "face": label + ("+" if side > 0 else "-"),
                    "point_uv_at_original_cut_datum_mm": point.tolist(),
                    "point_global_xyz_mm": (
                        np.array(cut["cut_datum_global_xyz_mm"]) + frame[1:].T @ point
                    ).tolist(),
                    "signed_transverse_shear_u_v_mpa": transverse.tolist(),
                    "signed_torsion_shear_u_v_mpa": torsional.tolist(),
                    "signed_combined_shear_u_v_mpa": vector.tolist(),
                    "signed_combined_shear_global_xyz_mpa": (
                        frame[1:].T @ vector
                    ).tolist(),
                    "combined_shear_magnitude_mpa": magnitude,
                    "combined_shear_over_Fv": magnitude / references["Fv_parallel"],
                }
            )
    component_bound = (
        math.hypot(abs(su) + abs(torque * cu), abs(sv) + abs(torque * cv))
        / references["Fv_parallel"]
    )
    original_bound = region["same_state_shear_bound_over_Fv"]
    return {
        "region_id": region["region_id"],
        "bounds_uv_mm": region["bounds_uv_mm"],
        "area_mm2": area,
        "source_regional_wrench_at_centroid_n_nmm": region[
            "wrench_at_regional_centroid_n_nmm"
        ],
        "source_rectangle_torsion": region["rectangle_torsion"],
        "source_scalar_component_sum_bound_over_Fv": original_bound,
        "rectangle_component_vector_bound_over_Fv": component_bound,
        "sufficient_all_section_bound_over_Fv": min(original_bound, component_bound),
        "face_peak": max(faces, key=lambda f: f["combined_shear_over_Fv"]),
        "faces": faces,
    }


def build_faces(output: str | Path) -> dict:
    """Parent postprocesses frozen attempt02 regional actions; no new solve."""
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW.resolve())
        and output != RAW.resolve()
        and not output.exists(),
        "STOP: fresh owned raw output child required",
    )
    producer = Path(__file__).resolve()
    pins = {**PINS, **SECTION_PINS, producer: sha(producer)}
    authenticate(pins)
    source, receipt = (
        read(SECTION_SOURCE / "checks.json"),
        read(SECTION_SOURCE / "receipt.json"),
    )
    require(
        source["status"]
        == receipt["status"]
        == "COMPLETE_FINITE_TOP_HOST_NOMINAL_COMPARISONS"
        and source["source_sha256"] == receipt["source_sha256"],
        "STOP: section source/receipt differs",
    )
    require(
        receipt["output_sha256"]
        == {
            name: SECTION_PINS[SECTION_SOURCE / name]
            for name in ("checks.json", "producer.py.snapshot")
        },
        "STOP: section output receipt differs",
    )
    old_producer = str(producer.relative_to(ROOT))
    require(
        source["source_sha256"][old_producer]
        == SECTION_PINS[SECTION_SOURCE / "producer.py.snapshot"],
        "STOP: executed section producer binding differs",
    )
    for relative, digest in source["source_sha256"].items():
        if relative == old_producer:
            continue  # Authenticate the frozen executed snapshot, not changed live code.
        path = ROOT / relative
        require(
            path not in pins or pins[path] == digest,
            f"STOP: conflicting source pin: {relative}",
        )
        pins[path] = digest
    authenticate(pins)
    require(
        tuple(source["case_ids"]) == CASES
        and tuple(source["host_ids"]) == HOSTS
        and source["recorded_section_count"] == 38
        and source["evaluated_trace_count"] == len(source["cuts"]) == 456
        and source["duration_comparison_count"] == 912,
        "STOP: finite source census differs",
    )
    require(
        all(source[key] is False for key in FLAGS), "STOP: section claim flags differ"
    )
    nominal_helper = helper("corner-net-section.py", "top_host_face_coefficients")
    cuts, rows = [], []
    for cut in source["cuts"]:
        frame = np.array(source["geometry"][cut["body"]]["grain_frame_rows_xyz"])
        duration_results = {}
        for scenario, result in cut["duration_results"].items():
            require(
                scenario in SCENARIOS
                and result["summary"]["duration_scenario"] == scenario,
                "STOP: duration scenario differs",
            )
            nominal = result["nominal_section"]
            regional = []
            for region in nominal["regions"]:
                require(
                    nominal_helper.rectangle_torsion(*region["width_depth_mm"])
                    == region["rectangle_torsion"],
                    "STOP: saved rectangle coefficients differ",
                )
                regional.append(region_faces(region, nominal["references"], cut, frame))
            deciding = max(
                regional, key=lambda r: r["face_peak"]["combined_shear_over_Fv"]
            )
            upper = max(r["sufficient_all_section_bound_over_Fv"] for r in regional)
            face_ratio = deciding["face_peak"]["combined_shear_over_Fv"]
            disposition = (
                "FACE_EXCEEDS_DECLARED_REFERENCE"
                if face_ratio > 1
                else "SUFFICIENT_RECTANGLE_BOUND_BELOW_REFERENCE"
                if upper <= 1
                else "FACES_BELOW_REFERENCE_INTERIOR_UNRESOLVED"
            )
            row = {
                "body": cut["body"],
                "case": cut["case"],
                "saved_trace_index": cut["saved_trace_index"],
                "station_mm": result["summary"]["station_mm"],
                "limit": result["summary"]["limit"],
                "duration_scenario": scenario,
                "CD": SCENARIOS[scenario],
                "compatible_face_peak_over_Fv": face_ratio,
                "sufficient_all_section_bound_over_Fv": upper,
                "source_scalar_component_sum_bound_over_Fv": result["summary"][
                    "same_state_shear_bound_over_Fv"
                ],
                "deciding_region_id": deciding["region_id"],
                "deciding_face": deciding["face_peak"],
                "full_signed_source_cut_global_n_nmm": cut[
                    "full_signed_cut_global_n_nmm"
                ],
                "full_signed_source_cut_grain_u_v_n_nmm": cut[
                    "full_signed_cut_grain_u_v_n_nmm"
                ],
                "disposition": disposition,
            }
            rows.append(row)
            duration_results[scenario] = {"summary": row, "regions": regional}
        cuts.append(
            {
                "body": cut["body"],
                "case": cut["case"],
                "saved_trace_index": cut["saved_trace_index"],
                "duration_results": duration_results,
            }
        )
    require(
        len(cuts) == 456 and len(rows) == 912, "STOP: face comparison census differs"
    )
    comparison = {}
    for scenario, duration in SCENARIOS.items():
        own = [r for r in rows if r["duration_scenario"] == scenario]
        comparison[scenario] = {
            "CD": duration,
            "compatible_face_peak": max(
                own, key=lambda r: r["compatible_face_peak_over_Fv"]
            ),
            "sufficient_all_section_bound_peak": max(
                own, key=lambda r: r["sufficient_all_section_bound_over_Fv"]
            ),
            "face_exceeding_trace_count": sum(
                r["compatible_face_peak_over_Fv"] > 1 for r in own
            ),
            "faces_below_reference_interior_unresolved_trace_count": sum(
                r["disposition"] == "FACES_BELOW_REFERENCE_INTERIOR_UNRESOLVED"
                for r in own
            ),
            "all_section_sufficient_bound_below_reference": all(
                r["sufficient_all_section_bound_over_Fv"] <= 1 for r in own
            ),
            "per_host": [
                {
                    "body": body,
                    "compatible_face_peak": max(
                        own_host := [r for r in own if r["body"] == body],
                        key=lambda r: r["compatible_face_peak_over_Fv"],
                    ),
                    "per_case": [
                        {
                            "case": case,
                            "compatible_face_peak": max(
                                [r for r in own_host if r["case"] == case],
                                key=lambda r: r["compatible_face_peak_over_Fv"],
                            ),
                        }
                        for case in CASES
                    ],
                }
                for body in HOSTS
            ],
        }
    report = {
        "schema": "top-host-saved-regional-signed-face-shear-v1",
        "status": "COMPLETE_FINITE_TOP_HOST_COMPATIBLE_FACE_COMPARISONS",
        **FLAGS,
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in pins.items()
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "source_force_state_scope": source["source_force_state_scope"],
        "source_hold_lever_mm": source["source_hold_lever_mm"],
        "recorded_section_count": 38,
        "evaluated_trace_count": 456,
        "duration_comparison_count": 912,
        "working_hypotheses": [
            *source["working_hypotheses"],
            "Reuse the existing member_stability shear_check midpoint method on each saved retained rectangle: parabolic tau_u=1.5*Vu/A*(1-4*u_relative^2/width^2), tau_v=1.5*Vv/A*(1-4*v_relative^2/depth^2). No off-axis transverse component is imposed on a free face.",
            "Saved equal-modulus rectangle torsion coefficients give signed tau_v=side_u*T*cv on u-face midpoints and tau_u=-side_v*T*cu on v-face midpoints. Both opposing faces are evaluated, so additions/cancellations occur at the same face/state/region.",
        ],
        "limits": [
            *source["limits"],
            "Face midpoint values provide a lower bound on the maximum of this declared nominal field. A face exceedance is a demonstrated exceedance of this working reference, not a physical test or a qualified wood failure.",
            "Faces below one do not prove all-section sufficiency when both retained scalar and directional component bounds exceed one; those interiors remain unresolved. No interior sampling, exact perforated-body field, orthotropic reinterpretation or new capacity is supplied.",
            "Attempt02 component bounds, normal comparisons, regional load sharing and CD hypotheses remain unchanged and preserved in the pinned source and this report.",
        ],
        "preserved_attempt02_duration_comparison": source["duration_comparison"],
        "duration_comparison": comparison,
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
        "duration_comparison": {
            key: {k: v for k, v in value.items() if k != "per_host"}
            for key, value in comparison.items()
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--faces",
        action="store_true",
        help="Postprocess frozen attempt02 regional shear on four compatible face midpoints.",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            (build_faces if args.faces else build)(args.output),
            indent=2,
            sort_keys=True,
        )
    )

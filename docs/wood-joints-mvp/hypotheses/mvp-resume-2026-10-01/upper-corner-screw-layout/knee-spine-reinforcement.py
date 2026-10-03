"""Prepare a four-stack knee-spine bridge proposal from frozen signed cuts.

Only the parent calls build(output). This prescribed-load static construction
does not adopt geometry, solve compatibility, or establish joint acceptance.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import platform
import sys
from itertools import combinations, product
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-spine-reinforcement"
SOURCE = HERE / "rawlocal/remaining-block-transverse/attempt01"
GEOMETRY = HERE / "rawlocal/knee-spine-net-sections/attempt02/checks.json"
NORMAL = (
    HERE
    / "rawlocal/corner-split-closure/finite-pressure-attempt01/producer.py.snapshot"
)
VOID = SOURCE / "producer.py.snapshot"
SECTION = HERE / "corner-timber-sections.py"
BLOCKS = ("knee_outer_left_spine", "knee_outer_right_spine")
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
CENTERS = ((100.0, 0.0), (250.0, 0.0))
BORE_RADIUS = 3.75  # Proposal envelope, not a drill instruction.
MARGIN = 1.25
TOL = 1e-7
PINS = {
    SOURCE
    / "checks.json": "f3118804d3a03df66d274d783ca93248757ac3d629de4a874d23e85da9a61f19",
    SOURCE
    / "receipt.json": "dce3437a105cdd269aec9ff98ac831c00d6e64e34a807c42254030ca4fffb519",
    SOURCE
    / "cuts.jsonl.gz": "86757d2db86751aa5cba5343df0065ac3d38cc7d69eeab71f02c55eedc72d4cc",
    VOID: "b7636729f666633feed74eb274968dc92b5d06620b4806ae697c79160869c9c8",
    GEOMETRY: "6b6c8df94f1ccab859ee980dd1835ba19286718f44e8a36ce6b9d0014064fc85",
    NORMAL: "e090270a3bea195800ed3b04b806fe4ea0c5e221ae57faf01f602c8dba769d5e",
    SECTION: "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE
    / "washer-product-basis.md": "af76a17eea64c63ad740694ebfde66cbf6d634dc70ad8bfb8b92648b0c0a4b53",
    HERE
    / "retail-washer.md": "c2845b8b395934a882b1636f6d5c1ae5441fd38cacf4fc5d6e11e6ed6fa65c62",
    HERE.parent
    / "assembly-package/hardware-engagement.md": "1790255824f49069883e5f9ab7a78ac55c42a1df57fdd8f3159cad029e8d1e4c",
}
HARDWARE = {
    "bolt_lead": "Lawson FA21103, conditional 1/4-20 x 8 in partial-thread Grade 5",
    "matched_metal_nut_lead": "K.L. Jack 25CNFH5Z, conditional SAE J995 Grade 5, 1/4-20 2B",
    "bolt_nominal_diameter_mm": 6.35,
    "bolt_nominal_under_head_length_mm": 203.2,
    "thread_pitch_mm": 1.27,
    "thread_tensile_stress_area_in2": 0.0318,
    "conditional_bolt_yield_ksi": 92.0,
    "conditional_nut_proof_ksi": 120.0,
    "washer_OD_ID_thickness_mm": [25.4, 8.3058, 2.5],
    "nut_height_envelope_mm": [5.3848, 5.7404],
    "washer_material_resistance": None,
    "delivered_dimensions_or_conformance_verified": False,
    "head_nut_bearing_profile_verified": False,
    "scene_fit_verified": False,
    "installation_tool_fit_verified": False,
}
FLAGS = {
    "proposal_adopted": False,
    "current_geometry_changed": False,
    "frame_or_native_run": False,
    "wood_stiffness_or_compatibility_solved": False,
    "installation_preload_credited": False,
    "modified_grain_nominal_check_complete": False,
    "old_grain_pass_transferred": False,
    "gravity_delta_in_global_model": False,
    "hardware_capacity_qualified": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "software_tests_or_agent_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return str(Path(path).relative_to(ROOT))


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"changed frozen input: {path}")


def imported(path, name):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    require(spec is not None, f"helper import unavailable: {path}")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def identity(cut):
    return {k: cut[k] for k in ("block", "case_id", "station_mm", "limit") if k in cut}


def constraints(cuts, length, width, centers):
    """Aggregate five necessary hull inequalities across all case cut planes."""
    half = width / 2
    coefficients = [
        [1.0, 1.0],
        [g / length for g, _ in centers],
        [(length - g) / length for g, _ in centers],
        [(u + half) / half for _, u in centers],
        [(half - u) / half for _, u in centers],
    ]
    names = (
        "normal",
        "grain_first_moment",
        "opposite_grain_first_moment",
        "positive_u_edge",
        "negative_u_edge",
    )
    result = [
        {"name": name, "coefficients": a, "rhs_n": -math.inf}
        for name, a in zip(names, coefficients, strict=True)
    ]
    for cut in cuts:
        q = cut["signed_internal_n_nmm"]
        require(
            len(q) == 6 and all(math.isfinite(v) for v in q),
            "invalid full source wrench",
        )
        n, p, r = q[0], -q[5], q[4]
        rhs = (
            n,
            p / length,
            (length * n - p) / length,
            (r + half * n) / half,
            (-r + half * n) / half,
        )
        for row, value in zip(result, rhs, strict=True):
            if value > row["rhs_n"]:
                row.update(
                    rhs_n=value,
                    witness={**identity(cut), "source_full_wrench_n_nmm": q},
                )
    require(
        all(math.isfinite(row["rhs_n"]) for row in result), "empty case cut inventory"
    )
    return [
        {"name": "bolt_1_nonnegative", "coefficients": [1.0, 0.0], "rhs_n": 0.0},
        {"name": "bolt_2_nonnegative", "coefficients": [0.0, 1.0], "rhs_n": 0.0},
        *result,
    ]


def lp(rows):
    """Minimize T1+T2 over a finite census of two-dimensional vertices."""
    vertices = []
    for first, second in combinations(rows, 2):
        a, b = first["coefficients"], second["coefficients"]
        det = a[0] * b[1] - a[1] * b[0]
        if abs(det) < 1e-14:
            continue
        c, d = first["rhs_n"], second["rhs_n"]
        point = [(c * b[1] - a[1] * d) / det, (a[0] * d - c * b[0]) / det]
        if min(point) < -TOL:
            continue
        point = [max(0.0, x) for x in point]
        if all(
            sum(a * t for a, t in zip(row["coefficients"], point, strict=True))
            >= row["rhs_n"] - TOL
            for row in rows
        ):
            vertices.append(
                {
                    "axial_ties_n": point,
                    "sum_n": sum(point),
                    "intersected_constraints": [first["name"], second["name"]],
                }
            )
    require(vertices, "no feasible nonnegative two-bolt hull vertex")
    best = min(vertices, key=lambda v: (v["sum_n"], *v["axial_ties_n"]))
    best["normalized_constraint_slacks_n"] = [
        sum(
            a * t
            for a, t in zip(row["coefficients"], best["axial_ties_n"], strict=True)
        )
        - row["rhs_n"]
        for row in rows
    ]
    return {
        **best,
        "feasible_vertices": vertices,
        "scope": "Minimum total hypothetical tie over the rectangular hull; necessary lower bound only.",
    }


def wood_wrench(q, ties, centers):
    gp = sum(g * t for (g, _), t in zip(centers, ties, strict=True))
    up = sum(u * t for (_, u), t in zip(centers, ties, strict=True))
    return [q[0] - sum(ties), *q[1:4], q[4] - up, q[5] + gp]


def separation(g1, r1, g2, r2):
    # Both perpendicular finite axes reach u=0 and the original bore's v center.
    return abs(g1 - g2) - r1 - r2


def geometry_proposal(source, void, section):
    length, (width, depth) = source["grain_length_mm"], source["width_depth_mm"]
    require(
        max(abs(length - 276.3), abs(width - 38.1), abs(depth - 139.7)) < 1e-6,
        "changed spine stock",
    )
    require(
        source["grain_frame_rows_xyz"]
        == [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        "changed local axes",
    )
    old = source["bores"]
    require(
        len(old) == 4
        and all(
            b["removed_interval_axis"] == 2 and abs(b["radius_mm"] - BORE_RADIUS) < 1e-6
            for b in old
        ),
        "changed original four u bores",
    )
    require(
        max(
            abs(a - b)
            for a, b in zip(
                sorted(b["station_mm"] for b in old),
                (31.75, 73.8, 191.61555301851, 226.08755295886),
                strict=True,
            )
        )
        < 1e-6,
        "changed original bore centers",
    )
    proposed, gaps, lands = [], [], []
    od, inside, _ = HARDWARE["washer_OD_ID_thickness_mm"]
    for index, (g, u) in enumerate(CENTERS, 1):
        axis_id = source["block"] + f"/proposed_v_bridge_{index}"
        require(
            min(g, length - g, width / 2 - abs(u)) > BORE_RADIUS,
            "new bore reaches a radial stock boundary",
        )
        proposed.append(
            {
                "axis_id": axis_id,
                "station_mm": g,
                "transverse_center_mm": u,
                "removed_interval_axis": 1,
                "radius_mm": BORE_RADIUS,
            }
        )
        for bore in old:
            gap = separation(g, BORE_RADIUS, bore["station_mm"], bore["radius_mm"])
            require(gap > 0, "new v bore intersects an original u bore")
            gaps.append(
                {
                    "new_axis": axis_id,
                    "original_axis": bore["axis_id"],
                    "cylinder_surface_gap_mm": gap,
                }
            )
        for sign in (-1, 1):
            v = sign * depth / 2
            edge = min(g, length - g, width / 2 - abs(u)) - od / 2
            absent = min(
                abs(v - b["transverse_center_mm"]) - b["radius_mm"] for b in old
            )
            other = min(
                math.hypot(g - h, u - z) - od / 2 - BORE_RADIUS
                for h, z in CENTERS
                if (h, z) != (g, u)
            )
            require(
                edge >= 0 and absent > 0 and other > 0 and inside / 2 >= BORE_RADIUS,
                "unsupported nominal washer annulus",
            )
            local = [g, u, v]
            xyz = [
                source["start_xyz_mm"][j]
                + sum(local[i] * source["grain_frame_rows_xyz"][i][j] for i in range(3))
                for j in range(3)
            ]
            lands.append(
                {
                    "axis_id": axis_id,
                    "end_v_sign": sign,
                    "seat_center_local_guv_mm": local,
                    "seat_center_xyz_mm": xyz,
                    "washer_outer_edge_margin_mm": edge,
                    "original_bore_gap_from_seat_plane_mm": absent,
                    "other_new_bore_gap_from_outer_disk_mm": other,
                    "supported_annulus_area_mm2": math.pi / 4 * (od**2 - inside**2),
                }
            )
    parallel_gap = math.dist(CENTERS[0], CENTERS[1]) - 2 * BORE_RADIUS
    require(parallel_gap > 0, "new bores intersect each other")
    geom = {
        k: source[k]
        for k in (
            "block",
            "grain_length_mm",
            "width_depth_mm",
            "grain_frame_rows_xyz",
            "start_xyz_mm",
        )
    }
    geom["bores"] = [*old, *proposed]
    # Reuse the exact original-cylinder/rectangle exclusion on this six-bore proposal.
    clear = min(
        min(b["station_mm"] - b["radius_mm"], length - b["station_mm"] - b["radius_mm"])
        for b in geom["bores"]
    )
    for v in (-depth / 2, 0.0, depth / 2):
        for bounds in (
            [[0.0, clear], [-width / 2, width / 2]],
            [[length - clear, length], [-width / 2, width / 2]],
        ):
            require(
                void.rectangle_supported(geom, 2, v, bounds),
                "end-band envelope enters a cylinder",
            )
    grain_geometry = [
        section.section(geom, g + offset)
        for g, _ in CENTERS
        for offset in (-BORE_RADIUS, 0.0, BORE_RADIUS)
    ]
    removed = len(proposed) * math.pi * BORE_RADIUS**2 * depth
    return {
        "hypothetical_geometry": geom,
        "new_axes": proposed,
        "perpendicular_bore_separations": gaps,
        "new_parallel_bore_surface_gap_mm": parallel_gap,
        "washer_lands": lands,
        "conservative_clear_grain_end_band_height_mm": clear,
        "modified_grain_opening_sections_geometry_only": grain_geometry,
        "removed_wood_volume_mm3": removed,
        "removed_wood_mass_at_original600_kg_m3_kg": removed * 600 / 1e9,
        "added_hardware_mass_kg": None,
        "modified_grain_nominal_check": "PENDING: evaluate full frozen grain W and source CF references at all six new center/tangency stations, including changed regional torque shares; no old grain pass transfers.",
        "gravity_delta": "PENDING GLOBAL ADOPTION: removed wood and four added hardware stacks are not fed into the frozen loads.",
        "end_pair_symmetry": "Equal concentric axial forces at opposite v seats give zero whole-body and grain-cut wrench; only declared static symmetry, not elastic compatibility.",
    }


def pressure_record(cut, ties, geom, normal, void):
    q = cut["signed_internal_n_nmm"]
    wood = wood_wrench(q, ties, CENTERS)
    result = normal.finite_band_pressure(wood, geom, 2)
    for patch in result.get("patches", []):
        require(
            void.rectangle_supported(geom, 2, cut["station_mm"], patch["bounds_pq_mm"]),
            "finite wood pressure patch enters an existing/proposed cylinder",
        )
    gp = sum(g * t for (g, _), t in zip(CENTERS, ties, strict=True))
    up = sum(u * t for (_, u), t in zip(CENTERS, ties, strict=True))
    bolt = [sum(ties), 0.0, 0.0, 0.0, up, -gp]
    error = max(abs(a + b - c) for a, b, c in zip(wood, bolt, q, strict=True))
    require(
        error < TOL and wood[1:4] == q[1:4],
        "bridge lost full-wrench recovery or tangential demand",
    )
    return {
        **identity(cut),
        "axis": 2,
        "source_signed_internal_n_nmm": q,
        "case_constant_axial_ties_n": ties,
        "bolt_normal_only_cut_n_nmm": bolt,
        "wood_full_cut_n_nmm": wood,
        "shear_shear_torque_retained_n_n_nmm": q[1:4],
        "maximum_full_wrench_recovery_error_n_nmm": error,
        "finite_wood_compression": result,
    }


def analytic_known_answers(normal, void):
    def case(q):
        return {"signed_internal_n_nmm": q}

    records = []
    for name, cuts, expected, expected_ties in [
        ("unloaded_no_preload", [case([0, 0, 0, 0, 0, 0])], 0.0, [0.0, 0.0]),
        ("centered_tension", [case([10, 7, -3, 11, 0, -50])], 10.0, [5.0, 5.0]),
        (
            "one_all_plane_allocation",
            [case([10, 7, -3, 11, 0, -20]), case([10, 7, -3, 11, 0, -80])],
            16.0,
            [8.0, 8.0],
        ),
        ("u_edge_couple", [case([0, 7, -3, 11, 10, 0])], 2.0, None),
    ]:
        result = lp(constraints(cuts, 10.0, 10.0, ((2.0, 0.0), (8.0, 0.0))))
        require(
            abs(result["sum_n"] - expected) < 1e-12, f"LP known answer differs: {name}"
        )
        if expected_ties is not None:
            require(
                max(
                    abs(a - b)
                    for a, b in zip(result["axial_ties_n"], expected_ties, strict=True)
                )
                < 1e-12,
                f"tie allocation known answer differs: {name}",
            )
        for cut in cuts:
            require(
                wood_wrench(
                    cut["signed_internal_n_nmm"],
                    result["axial_ties_n"],
                    ((2.0, 0.0), (8.0, 0.0)),
                )[1:4]
                == cut["signed_internal_n_nmm"][1:4],
                "known answer changed tangentials",
            )
        records.append(
            {
                "name": name,
                "expected_sum_n": expected,
                "expected_ties_n": expected_ties,
                "observed": result,
            }
        )
    coupon = {
        "grain_length_mm": 10.0,
        "width_depth_mm": [10.0, 10.0],
        "bores": [
            {
                "axis_id": "old_u",
                "station_mm": 5.0,
                "transverse_center_mm": 0.0,
                "removed_interval_axis": 2,
                "radius_mm": 1.0,
            },
            {
                "axis_id": "new_v",
                "station_mm": 2.0,
                "transverse_center_mm": 0.0,
                "removed_interval_axis": 1,
                "radius_mm": 1.0,
            },
        ],
    }
    require(
        separation(2, 1, 5, 1) == 1,
        "perpendicular-cylinder separation known answer differs",
    )
    for station, bounds, expected in [
        (0.0, [[0.0, 1.0], [-5.0, 5.0]], True),
        (0.0, [[1.5, 2.5], [-0.5, 0.5]], False),
        (0.0, [[4.5, 5.5], [-5.0, 5.0]], False),
        (3.0, [[4.5, 5.5], [-5.0, 5.0]], True),
    ]:
        require(
            void.rectangle_supported(coupon, 2, station, bounds) == expected,
            "cylinder/rectangle known answer differs",
        )
    return {
        "all_known_answers_satisfied": True,
        "two_variable_LP": records,
        "perpendicular_cylinder_gap_expected_mm": 1.0,
        "rectangle_exclusion_known_answer_count": 4,
        "frozen_normal_hull": normal.coupon(),
        "frozen_finite_end_bands": normal.band_coupon(),
    }


def axial_profile(depth):
    washer = HARDWARE["washer_OD_ID_thickness_mm"][2]
    nut_low, nut_high = HARDWARE["nut_height_envelope_mm"]
    nut_face = depth + 2 * washer
    return {
        "wood_interval_under_head_mm": [washer, washer + depth],
        "nut_bearing_face_under_head_mm": nut_face,
        "required_full_form_male_thread_window_mm": [nut_face, nut_face + nut_high],
        "nut_far_face_envelope_mm": [nut_face + nut_low, nut_face + nut_high],
        "three_pitch_nominal_tip_option_min_length_mm": nut_face
        + nut_high
        + 3 * HARDWARE["thread_pitch_mm"],
        "nominal_8in_tip_projection_past_farthest_nut_face_mm": HARDWARE[
            "bolt_nominal_under_head_length_mm"
        ]
        - nut_face
        - nut_high,
        "delivered_length_body_thread_fit": "UNPROVED: nominal 8 in and partial-thread labels do not prove thread at the required nut seat or a delivered profile.",
        "scene_tool_and_tip_clearance": "UNPROVED: no scene, CAD, drilling or installation access check is included.",
    }


def build(output):
    require(Path.cwd().resolve() == ROOT, "run from repository root")
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    pins = dict(PINS)
    producer = Path(__file__).resolve()
    pins[producer] = sha(producer)
    authenticate(pins)
    source, receipt, geometry = (
        read(SOURCE / "checks.json"),
        read(SOURCE / "receipt.json"),
        read(GEOMETRY),
    )
    require(
        source["status"] == "FINITE_REMAINING_BLOCK_ASSESSMENT_COMPLETE"
        and not source["affected_scope_stops"]
        and source["cut_count"] == 19536
        and source["evaluated_body_count"] == 20,
        "incomplete frozen remaining-twenty result",
    )
    require(
        tuple(source["case_ids"]) == tuple(geometry["case_ids"]) == CASES
        and set(geometry["geometry"]) == set(BLOCKS),
        "changed two-spine/six-case coverage",
    )
    for name in ("checks.json", "cuts.jsonl.gz", "producer.py.snapshot"):
        require(
            receipt["output_sha256"][name] == pins[SOURCE / name],
            "source output not bound by frozen receipt",
        )
    for document in (source, receipt, geometry):
        for relative, digest in document["source_sha256"].items():
            path = ROOT / relative
            require(
                path not in pins or pins[path] == digest,
                "conflicting inherited source pin",
            )
            pins[path] = digest
    authenticate(pins)
    normal, void, section = [
        imported(p, name)
        for p, name in (
            (NORMAL, "reinforcement_normal"),
            (VOID, "reinforcement_void"),
            (SECTION, "reinforcement_section"),
        )
    ]
    known = analytic_known_answers(normal, void)
    proposals = {
        body: geometry_proposal(geometry["geometry"][body], void, section)
        for body in BLOCKS
    }
    cuts = {(body, case): [] for body, case in product(BLOCKS, CASES)}
    seen, total_lines = set(), 0
    with gzip.open(SOURCE / "cuts.jsonl.gz", "rt") as stream:
        for line in stream:
            record = json.loads(line)
            total_lines += 1
            if record["block"] not in BLOCKS or record["axis"] != 2:
                continue
            own = (record["block"], record["case_id"])
            require(
                own in cuts and record["limit"] in ("before", "after"),
                "unexpected target cut identity",
            )
            stamp = (*own, record["station_mm"], record["limit"])
            require(stamp not in seen, "duplicate target cut")
            seen.add(stamp)
            require(
                abs(record["station_mm"])
                < proposals[own[0]]["hypothetical_geometry"]["width_depth_mm"][1] / 2,
                "cut outside bolt grip",
            )
            cuts[own].append(record)
    require(total_lines == source["cut_count"], "source cut archive coverage differs")
    for state in source["states"]:
        if state["block"] in BLOCKS and state["axis"] == 2:
            require(
                len(cuts[(state["block"], state["case_id"])]) == state["cut_count"],
                "target state coverage differs",
            )
    require(all(cuts.values()), "missing target body/case")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    fc = source["existing_Fc_perpendicular_reference_mpa"]
    require(
        abs(fc - 4.309223308230226) < 1e-12,
        "changed perpendicular compression reference",
    )
    area = math.pi / 4 * (25.4**2 - 8.3058**2)
    steel_area = HARDWARE["thread_tensile_stress_area_in2"] * 25.4**2
    ksi_mpa = 6.894757293168361
    states = []
    with gzip.open(output / "cuts.jsonl.gz", "wt") as stream:
        for (body, case), inventory in cuts.items():
            geom = proposals[body]["hypothetical_geometry"]
            rows = constraints(
                inventory, geom["grain_length_mm"], geom["width_depth_mm"][0], CENTERS
            )
            optimum = lp(rows)
            candidates = []
            for scale in (1.0, MARGIN):
                ties = [scale * t for t in optimum["axial_ties_n"]]
                peak, missing, exceeding, statuses = None, [], [], {}
                recovery = 0.0
                for cut in inventory:
                    record = pressure_record(cut, ties, geom, normal, void)
                    result = record["finite_wood_compression"]
                    statuses[result["status"]] = statuses.get(result["status"], 0) + 1
                    recovery = max(
                        recovery, record["maximum_full_wrench_recovery_error_n_nmm"]
                    )
                    if "pressure_peak_mpa" not in result:
                        missing.append(
                            {
                                **identity(cut),
                                "status": result["status"],
                                "wood_full_cut_n_nmm": record["wood_full_cut_n_nmm"],
                            }
                        )
                    else:
                        result["pressure_over_existing_Fc_perp_reference"] = (
                            result["pressure_peak_mpa"] / fc
                        )
                        if (
                            peak is None
                            or result["pressure_peak_mpa"]
                            > peak["finite_wood_compression"]["pressure_peak_mpa"]
                        ):
                            peak = record
                        if result["pressure_peak_mpa"] > fc:
                            exceeding.append(
                                {
                                    **identity(cut),
                                    "constructed_pressure_mpa": result[
                                        "pressure_peak_mpa"
                                    ],
                                }
                            )
                    stream.write(
                        json.dumps(
                            {"uniform_case_force_margin": scale, **record},
                            allow_nan=False,
                        )
                        + "\n"
                    )
                washers = [
                    {
                        "proposed_bolt_index": i,
                        "axial_tension_n": t,
                        "both_end_supported_annulus_area_mm2": area,
                        "each_end_mean_pressure_mpa": t / area,
                        "mean_over_Fc_perp_reference": t / area / fc,
                        "thread_nominal_axial_stress_mpa": t / steel_area,
                        "bolt_axial_over_conditional_yield_reference": t
                        / steel_area
                        / (HARDWARE["conditional_bolt_yield_ksi"] * ksi_mpa),
                        "nut_axial_over_conditional_proof_reference": t
                        / steel_area
                        / (HARDWARE["conditional_nut_proof_ksi"] * ksi_mpa),
                        "washer_metal_or_actual_thread_capacity_qualified": False,
                    }
                    for i, t in enumerate(ties, 1)
                ]
                found = not missing
                candidates.append(
                    {
                        "uniform_case_force_margin": scale,
                        "constant_axial_ties_n": ties,
                        "sum_ties_n": sum(ties),
                        "cut_count": len(inventory),
                        "finite_construction_status_counts": statuses,
                        "all_listed_cuts_have_finite_normal_witness": found,
                        "finite_normal_and_mean_reference_screen_satisfied": found
                        and not exceeding
                        and all(
                            w["mean_over_Fc_perp_reference"] <= 1
                            and w["bolt_axial_over_conditional_yield_reference"] <= 1
                            and w["nut_axial_over_conditional_proof_reference"] <= 1
                            for w in washers
                        ),
                        "missing_finite_witnesses": missing,
                        "constructed_pressures_above_reference": exceeding,
                        "maximum_finite_pressure_witness": peak,
                        "maximum_full_wrench_recovery_error_n_nmm": recovery,
                        "axial_stack_reference_comparisons": washers,
                    }
                )
            states.append(
                {
                    "block": body,
                    "case_id": case,
                    "aggregated_hull_constraints": rows,
                    "bare_hull_minimum": optimum,
                    "candidates": candidates,
                }
            )
    report = {
        "schema": "knee-spine-v-bridge-static-proposal/v1",
        "status": "FINITE_PROPOSAL_STATIC_ARITHMETIC_COMPLETE",
        **FLAGS,
        "source_sha256": {key(p): h for p, h in pins.items()},
        "source_force_state_scope": source["source_force_state_scope"],
        "source_frame_assumptions": geometry["source_frame_assumptions"],
        "source_gravity_multiplier": source["source_gravity_multiplier"],
        "source_load_identity": {
            k: geometry[k]
            for k in (
                "source_climber_weight_lb",
                "source_dynamic_factor",
                "source_horizontal_force_magnitude_n",
                "source_hold_lever_mm",
            )
        },
        "original_v_cut_count": len(seen),
        "body_case_count": len(states),
        "hardware_hypothesis": HARDWARE,
        "current_authority_counts": {
            "bolts": 104,
            "nuts": 104,
            "washers": 208,
            "Hillman_screws": 66,
        },
        "hypothetical_counts_if_later_adopted": {
            "bolts": 108,
            "nuts": 108,
            "washers": 216,
            "Hillman_screws": 66,
        },
        "geometry_proposals": proposals,
        "conditional_axial_profile": axial_profile(139.7),
        "known_answers": known,
        "existing_Fc_perpendicular_reference_mpa": fc,
        "states": states,
        "all_1_25_candidates_have_finite_normal_witnesses": all(
            s["candidates"][1]["all_listed_cuts_have_finite_normal_witness"]
            for s in states
        ),
        "all_1_25_candidates_meet_named_reference_screen": all(
            s["candidates"][1]["finite_normal_and_mean_reference_screen_satisfied"]
            for s in states
        ),
        "scope": "Prescribed original six-case v-cut normal equilibrium only. Constant passive tie demand per bolt/case; no preload, additional bolt shear/torque, wood stiffness, grain nominal pass, physical fit or global gravity adoption.",
    }
    authenticate(pins)
    dump(output / "checks.json", report)
    dump(
        output / "receipt.json",
        {
            "schema": "knee-spine-reinforcement-parent-receipt/v1",
            "python_version": platform.python_version(),
            "source_sha256": report["source_sha256"],
            "sources_authenticated_before_and_after": True,
            "output_sha256": {
                name: sha(output / name)
                for name in (
                    ".gitignore",
                    "checks.json",
                    "cuts.jsonl.gz",
                    "producer.py.snapshot",
                )
            },
            **FLAGS,
        },
    )
    return {
        "status": report["status"],
        "checks_sha256": sha(output / "checks.json"),
        "body_case_count": len(states),
        "original_v_cut_count": len(seen),
        "all_1_25_candidates_meet_named_reference_screen": report[
            "all_1_25_candidates_meet_named_reference_screen"
        ],
        "modified_grain_nominal_check_complete": False,
        "proposal_adopted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), allow_nan=False))

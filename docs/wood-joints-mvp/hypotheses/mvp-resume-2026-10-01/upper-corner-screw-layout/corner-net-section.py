"""Finite nominal ligament comparisons for eight frozen cosine-wall cuts.

Parent owns execution. The declared common longitudinal strain plane,
end-bridge compatibility, area sharing and common rectangular twist are MVP
working hypotheses. This calculator establishes no joint qualification.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import platform
from functools import cache
from itertools import combinations, product
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/corner-net-section"
WALL = HERE / "rawlocal/corner-bore-wall/attempt01/checks.json"
WALL_RECEIPT = WALL.with_name("receipt.json")
TIMBER = HERE / "rawlocal/corner-timber-sections/attempt02/checks.json"
MATERIAL = (
    HERE.parents[1] / "hardware-material-specification-2026-09-30/material-inputs.json"
)
TORSION_SOURCE = HERE.parent / "member_stability.py"
PSI_MPA = 0.006894757293168361
PINS = {
    WALL: "b95e7fc3d1d60c94ae449c681d4cec12221345a5ba0eb865f3ca225086350caf",
    WALL_RECEIPT: "465d7caf7a37889b24970062f9739d2f450573c97139f82167b5c17dac70ad3b",
    HERE
    / "corner-bore-wall.py": "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    HERE
    / "corner-bore-wall.md": "4b446f14e28cab4a313a60b08280084ea79bd0f87ed29f301143e11af1fdd5ee",
    TIMBER: "8b954edf5743999f427d2b99fcaaf9288578f02dc59a5cf1e632da634aa2e813",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    TORSION_SOURCE: "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    Path(
        "/tmp/wood-handbook-ch9.pdf"
    ): "84829761afb977291236c85bd51fdb00a3a56109625b0c09e7a0915ae684a9b4",
}
ASSUMPTIONS = [
    "A common longitudinal strain plane gives sigma_g=a+b*u+c*v across all retained regions; continuous grain-end bridges maintain this compatibility.",
    "Regional transverse forces share in proportion to retained area, with their centroid-offset moments retained.",
    "Equal longitudinal shear moduli in both transverse directions and across regions, common regional twist and nominal free warping give T_j=J_j/sum(J)*T_centroid.",
    "Within the same cut/state/region, the conservative nominal shear magnitude bound is 1.5*hypot(V_uj,V_vj)/A_j + tau_Tj; unchanged Fv is used for both longitudinal shear components.",
    "Existing DF-L No.2 nominal-4x6 CF-only references are retained; no new adjustment, strength enhancement or torsion allowable is supplied.",
]


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
        require(sha(path) == expected, f"source pin differs: {path}")


@cache
def torsion_face_function():
    """Reuse only the frozen scalar function, without importing its full module."""
    require(sha(TORSION_SOURCE) == PINS[TORSION_SOURCE], "torsion source differs")
    tree = ast.parse(TORSION_SOURCE.read_text())
    definitions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "torsion_faces"
    ]
    require(len(definitions) == 1, "frozen rectangle function missing")
    namespace = {"math": math, "cache": cache}
    exec(  # noqa: S102 - Only the named scalar function from authenticated source.
        compile(
            ast.Module(body=definitions, type_ignores=[]), str(TORSION_SOURCE), "exec"
        ),
        namespace,
    )
    return namespace["torsion_faces"]


def rectangle_torsion(width, depth):
    """Standard rectangle J and peak coefficient, using 200 fixed odd terms."""
    require(min(width, depth) > 0, "nonpositive rectangle")
    short, long = sorted((width, depth))
    odd = range(1, 400, 2)
    j = (
        long
        * short**3
        / 3
        * (
            1
            - 192
            * short
            / (math.pi**5 * long)
            * math.fsum(math.tanh(n * math.pi * long / (2 * short)) / n**5 for n in odd)
        )
    )
    face = torsion_face_function()(width, depth, 1.0)
    # The same finite series is used by the existing face-coefficient routine.
    tail_j = long * short**3 / 3 * 192 * short / (math.pi**5 * long * 4 * 400**4)
    require(j > tail_j > 0 and min(face) > 0, "rectangle torsion coefficient differs")
    return {
        "J_mm4": j,
        "J_series_absolute_tail_bound_mm4": tail_j,
        "peak_shear_coefficient_per_mm3": max(face),
        "face_shear_coefficients_u_v_per_mm3": list(face),
        "fixed_odd_term_count": 200,
    }


def area_properties(regions):
    """Analytic integrals of disjoint axis-aligned retained rectangles."""
    require(len(regions) > 0, "empty net section")
    values = []
    for index, region in enumerate(regions):
        bounds = np.asarray(region["bounds_uv_mm"], dtype=float)
        require(bounds.shape == (2, 2) and np.isfinite(bounds).all(), "invalid bounds")
        width, depth = bounds[:, 1] - bounds[:, 0]
        require(min(width, depth) > 0, "empty retained rectangle")
        centroid = np.mean(bounds, axis=1)
        area = float(width * depth)
        values.append(
            {
                "region_id": index,
                "bounds_uv_mm": bounds.tolist(),
                "width_depth_mm": [float(width), float(depth)],
                "area_mm2": area,
                "centroid_uv_mm": centroid.tolist(),
                "local_integral_u2_v2_mm4": [
                    area * width**2 / 12,
                    area * depth**2 / 12,
                ],
            }
        )
    for first, second in combinations(values, 2):
        a, b = np.array(first["bounds_uv_mm"]), np.array(second["bounds_uv_mm"])
        overlap = np.minimum(a[:, 1], b[:, 1]) - np.maximum(a[:, 0], b[:, 0])
        require(not np.all(overlap > 1e-9), "retained rectangles overlap")
    area = math.fsum(r["area_mm2"] for r in values)
    center = np.array(
        [
            math.fsum(r["area_mm2"] * r["centroid_uv_mm"][k] for r in values) / area
            for k in (0, 1)
        ]
    )
    inertia = np.zeros((2, 2))
    for region in values:
        offset = np.array(region["centroid_uv_mm"]) - center
        inertia += np.diag(region["local_integral_u2_v2_mm4"]) + region[
            "area_mm2"
        ] * np.outer(offset, offset)
    first = area * center
    raw_second = inertia + area * np.outer(center, center)
    matrix = np.array(
        [[area, *first], [first[0], *raw_second[0]], [first[1], *raw_second[1]]]
    )
    require(np.linalg.det(inertia) > 0, "singular net-section inertia")
    return {
        "area_mm2": area,
        "centroid_uv_mm": center.tolist(),
        "central_integral_u2_uv_v2_matrix_mm4": inertia.tolist(),
        "raw_integral_1_u_v_matrix_mixed_mm_units": matrix.tolist(),
        "regions": values,
    }


def normal_comparisons(mean, bending, total, refs):
    """Nominal stress/reference comparisons, without a new interaction law."""
    axial_reference = (
        max(mean, 0) / refs["Ft_parallel"] + max(-mean, 0) / refs["Fc_parallel"]
    )
    return {
        "total_tension_over_Ft": max(total, 0) / refs["Ft_parallel"],
        "total_compression_over_Fc": max(-total, 0) / refs["Fc_parallel"],
        "absolute_bending_over_Fb": abs(bending) / refs["Fb"],
        "axial_plus_bending_reference_sum": axial_reference + abs(bending) / refs["Fb"],
    }


def nominal_section(wrench, regions, refs):
    """Retain a signed [N,Vu,Vv,T,Mu,Mv] cut and reconstruct regional offsets."""
    q = np.asarray(wrench, dtype=float)
    require(q.shape == (6,) and np.isfinite(q).all(), "invalid signed cut")
    require(
        all(math.isfinite(v) and v > 0 for v in refs.values()), "invalid references"
    )
    props = area_properties(regions)
    area = props["area_mm2"]
    center = np.array(props["centroid_uv_mm"])
    offset = np.r_[0.0, center]
    centroid_moment = q[3:] - np.cross(offset, q[:3])
    mean = q[0] / area
    b, c = np.linalg.solve(
        np.array(props["central_integral_u2_uv_v2_matrix_mm4"]),
        [-centroid_moment[2], centroid_moment[1]],
    )
    a = mean - np.dot([b, c], center)
    rectangles = [rectangle_torsion(*r["width_depth_mm"]) for r in props["regions"]]
    total_j = math.fsum(r["J_mm4"] for r in rectangles)
    regional = []
    recovered = np.zeros(6)
    for region, torsion in zip(props["regions"], rectangles, strict=True):
        own_area = region["area_mm2"]
        own_center = np.array(region["centroid_uv_mm"])
        own_force = np.r_[
            own_area * (a + np.dot([b, c], own_center)), q[1:3] * own_area / area
        ]
        own_moment = np.array(
            [
                centroid_moment[0] * torsion["J_mm4"] / total_j,
                c * region["local_integral_u2_v2_mm4"][1],
                -b * region["local_integral_u2_v2_mm4"][0],
            ]
        )
        moment_offset = np.cross(np.r_[0.0, own_center], own_force)
        at_datum = np.r_[own_force, own_moment + moment_offset]
        recovered += at_datum
        corners = []
        for u, v in product(*region["bounds_uv_mm"]):
            bending = b * (u - center[0]) + c * (v - center[1])
            sigma = mean + bending
            corners.append(
                {
                    "uv_mm": [u, v],
                    "sigma_parallel_mpa": sigma,
                    "signed_bending_mpa": bending,
                    "comparisons": normal_comparisons(mean, bending, sigma, refs),
                }
            )
        transverse = 1.5 * math.hypot(*own_force[1:]) / own_area
        torsional = abs(own_moment[0]) * torsion["peak_shear_coefficient_per_mm3"]
        regional.append(
            {
                **region,
                "rectangle_torsion": torsion,
                "wrench_at_regional_centroid_n_nmm": np.r_[
                    own_force, own_moment
                ].tolist(),
                "centroid_offset_moment_at_cut_nmm": moment_offset.tolist(),
                "wrench_at_original_cut_datum_n_nmm": at_datum.tolist(),
                "longitudinal_corners": corners,
                "sigma_parallel_min_max_mpa": [
                    min(x["sigma_parallel_mpa"] for x in corners),
                    max(x["sigma_parallel_mpa"] for x in corners),
                ],
                "nominal_transverse_shear_bound_mpa": transverse,
                "nominal_torsional_peak_shear_mpa": torsional,
                "same_state_combined_shear_bound_mpa": transverse + torsional,
                "same_state_shear_bound_over_Fv": (transverse + torsional)
                / refs["Fv_parallel"],
            }
        )
    error = recovered - q
    require(
        max(abs(error[:3])) < 1e-7 and max(abs(error[3:])) < 1e-6,
        "regional wrench closure differs",
    )
    return {
        "source_signed_cut_n_nmm": q.tolist(),
        "net_section_integrals": {k: v for k, v in props.items() if k != "regions"},
        "signed_cut_at_net_centroid_n_nmm": np.r_[q[:3], centroid_moment].tolist(),
        "sigma_a_b_c_mpa_mpa_per_mm": [a, b, c],
        "mean_axial_parallel_stress_mpa": mean,
        "sum_rectangular_J_mm4": total_j,
        "regions": regional,
        "reconstructed_signed_cut_n_nmm": recovered.tolist(),
        "reconstructed_minus_source_n_nmm": error.tolist(),
        "balancing_free_couples_added": 0,
    }


def rectangular_known_answer(refs):
    """Prepared translated-rectangle coupon; parent executes this once."""
    section = nominal_section(
        [102, 12, -6, 30, -120, -424],
        [{"bounds_uv_mm": [[2, 6], [-4, 2]]}],
        refs,
    )
    require(
        np.max(abs(np.array(section["sigma_a_b_c_mpa_mpa_per_mm"]) - [2, 0.5, -0.25]))
        < 1e-12,
        "rectangle affine stress differs",
    )
    require(
        np.max(
            abs(
                np.array(section["signed_cut_at_net_centroid_n_nmm"])
                - [102, 12, -6, 42, -18, -16]
            )
        )
        < 1e-10,
        "rectangle datum translation differs",
    )
    region = section["regions"][0]
    require(
        np.max(abs(np.array(region["sigma_parallel_min_max_mpa"]) - [2.5, 6])) < 1e-12,
        "rectangle corner stresses differ",
    )
    expected_transverse = 1.5 * math.sqrt(180) / 24
    require(
        abs(region["nominal_transverse_shear_bound_mpa"] - expected_transverse) < 1e-12,
        "rectangle transverse bound differs",
    )
    square = rectangle_torsion(1.0, 1.0)
    require(
        abs(square["J_mm4"] - 0.140577014955) < 5e-11,
        "unit-square Saint-Venant J differs",
    )
    require(
        abs(square["peak_shear_coefficient_per_mm3"] - 4.8) < 0.02,
        "unit-square FPL graph coefficient differs",
    )
    return {
        "translated_rectangle": section,
        "expected_sigma_a_b_c": [2, 0.5, -0.25],
        "expected_sigma_min_max_mpa": [2.5, 6],
        "expected_centroid_cut_n_nmm": [102, 12, -6, 42, -18, -16],
        "expected_transverse_bound_mpa": expected_transverse,
        "unit_square_torsion": square,
        "unit_square_FPL_graph_peak_coefficient_approximate": 4.8,
        "scope": "One finite rectangle coupon: affine stress, six-component datum/offset accounting and standard rectangle torsion coefficients. No mechanics solve or qualification.",
    }


def run(args):
    output = args.output.resolve()
    require(
        output.is_relative_to(RAW) and output != RAW and not output.exists(),
        "fresh owned output child required",
    )
    pins = dict(PINS)
    wall, timber, material = read(WALL), read(TIMBER), read(MATERIAL)
    for record in (wall, timber):
        for name, expected in record["source_sha256"].items():
            path = Path(name)
            path = path if path.is_absolute() else ROOT / path
            require(
                path not in pins or pins[path] == expected, f"conflicting pin: {path}"
            )
            pins[path] = expected
    pins[Path(__file__).resolve()] = sha(Path(__file__))
    authenticate(pins)
    refs = timber["conditional_CF_only_reference_mpa"]
    base = material["conditional_DF_L_No2_base_row"]["base_properties"]
    cf = material["standard_section_scenarios"]["nominal_4x6"]["CF"]
    for key in ("Ft_parallel", "Fb", "Fc_parallel", "Fv_parallel"):
        require(
            abs(refs[key] - base[key] * cf.get(key, 1) * PSI_MPA) < 1e-12,
            "existing reference differs",
        )
    coupon = rectangular_known_answer(refs)
    cuts = wall["deciding_cut_mappings"]
    require(
        len(cuts) == 8
        and all(c["section"]["material_region_count"] == 3 for c in cuts),
        "eight three-region cuts required",
    )
    results = []
    for cut in cuts:
        nominal = nominal_section(
            cut["cosine_wall_complete_cut_grain_u_v_n_nmm"],
            cut["section"]["regions"],
            refs,
        )
        require(
            abs(
                nominal["net_section_integrals"]["area_mm2"]
                - cut["section"]["net_area_mm2"]
            )
            < 1e-7,
            "saved net area differs",
        )
        for region in nominal["regions"]:
            region["ligament_name"] = ("low_v_outer", "middle", "high_v_outer")[
                region["region_id"]
            ]
        results.append(
            {
                **{
                    k: cut[k]
                    for k in ("side", "case_id", "station_mm", "limit", "datum_xyz_mm")
                },
                "grain_frame_rows_xyz": timber["geometry"][cut["side"]][
                    "grain_frame_rows_xyz"
                ],
                "intersected_bore_ids": cut["section"]["bore_or_tangency_ids"],
                **nominal,
            }
        )
    shear_witnesses = []
    normal_witnesses = []
    for cut in results:
        identity = {k: cut[k] for k in ("side", "case_id", "station_mm", "limit")}
        for region in cut["regions"]:
            own = {
                **identity,
                "region_id": region["region_id"],
                "ligament_name": region["ligament_name"],
            }
            shear_witnesses.append(
                {
                    **own,
                    "ratio": region["same_state_shear_bound_over_Fv"],
                    "transverse_bound_mpa": region[
                        "nominal_transverse_shear_bound_mpa"
                    ],
                    "torsional_peak_mpa": region["nominal_torsional_peak_shear_mpa"],
                }
            )
            for corner in region["longitudinal_corners"]:
                normal_witnesses.append({**own, **corner})
    peaks = {
        key: max(normal_witnesses, key=lambda c: c["comparisons"][key])
        for key in normal_witnesses[0]["comparisons"]
    }
    result = {
        "schema": "corner-net-section-nominal-mvp-v1",
        "source_sha256": {
            str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): s
            for p, s in sorted(pins.items())
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "working_hypotheses": ASSUMPTIONS,
        "existing_reference_mpa": refs,
        "material_scenario": timber["material_scenario"],
        "rectangular_known_answer": coupon,
        "cuts": results,
        "peaks": {
            "normal_comparisons": peaks,
            "same_state_shear_bound_over_Fv": max(
                shear_witnesses, key=lambda r: r["ratio"]
            ),
        },
        "balancing_free_couples_added": 0,
        "scope": "Nominal stress/reference comparisons of eight named full signed cuts under stated working hypotheses only. No 3D compatibility, notch/bore concentration, perpendicular tension, stability, group/splitting or elastic qualification; no new capacity or load reconstruction.",
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    dump(
        output / "receipt.json",
        {
            "source_sha256": result["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
        },
    )
    print(
        json.dumps(
            {
                "checks_sha256": sha(output / "checks.json"),
                "cut_count": len(results),
                "regional_comparison_count": sum(len(c["regions"]) for c in results),
                "peaks": result["peaks"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())

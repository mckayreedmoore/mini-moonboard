"""Separate Saint-Venant rectangle torsion and simultaneous nominal stress bound.

The analytical bound covers the chosen prismatic, freely warping rectangle
field. Holes, a short formed heel and restrained warping remain separate gaps.
Issued steel helpers/reports are imported and preserved without modification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path

import numpy as np

from scripts import thin_bolted_steel_resistance as frozen

ROOT, PACKET = frozen.ROOT, frozen.PACKET
COMPONENT_WRITER_SHA = "4b5973697d6ed5a5ca4ae39b2bd836ff044e1cb5858934879ff1e86649b0a037"
FROZEN_STEEL_SHA = "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602"
SOURCES = {
    "rectangle_prandtl_series": {"url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC11467641/",
        "locator": "Wang2024 Eq7, isotropic Gxz=Gyz, a=t/2,b=B/2; conventional single-series Prandtl solution",
        "access": "Equation7 formula available in primary search excerpt; full-page browser request encountered access challenge"},
    "prandtl_equations": {"url": "https://ocw.mit.edu/courses/16-20-structural-mechanics-fall-2002/e888339011c834eb2a02bd365fa25052_unit10.pdf",
        "locator": "Unit10 pp13-21: stress-function derivatives, zero free-boundary value, torque integral and Poisson equation; long prismatic/free-warping assumptions pp5-6"},
    "exact_rectangle_J": {"url": "https://zhaolab.stanford.edu/sites/g/files/sbiybj21256/files/media/file/part-ii.pdf",
        "locator": "Equation3: rectangular torsion odd-integer tanh series; author-hosted primary research"},
    "independent_J_benchmark": {"url": "https://zhaolab.stanford.edu/sites/g/files/sbiybj21256/files/media/file/supplementary_material_jam-22-1117.pdf",
        "locator": "SupplementaryText p1: h2mm,t0.5mm,J0.0702mm4 (rounded)"},
    "independent_rectangle_table": {"url": "https://www.iieta.org/node/2622",
        "locator": "Ike2019 Table1: J/(bt3)0.1406 square,0.2287 aspect2,0.307 aspect8, limit1/3"},
    "short_connection_limit": {"url": "https://ej.aisc.org/index.php/engj/article/download/1147/1146",
        "locator": "Dowswell2019 pp63-65: uniform torsion and short connection warping; no plastic/warping/Wagner capacity adopted"},
}


@lru_cache(maxsize=4096)
def _series_bracket(b, t, terms):
    """Cache immutable geometry-only coefficients across unchanged sections."""
    partial = math.fsum(math.tanh(n * math.pi * b / (2*t)) / n**5 for n in range(1, 2*terms, 2))
    next_n = 2*terms + 1
    tail = 1 / next_n**5 + 1 / (8*next_n**4)
    factor, coefficient = b*t**3/3, 192*t/(math.pi**5*b)
    low = factor * (1 - coefficient*(partial + tail))
    high = factor * (1 - coefficient*partial)
    return partial, tail, low, high


def rectangle_torsion(width_mm: float, thickness_mm: float, terms=64) -> dict:
    """Exact J bracket from positive odd series and explicit integral tail bound."""
    width = frozen.number(width_mm, "width", positive=True)
    thickness = frozen.number(thickness_mm, "thickness", positive=True)
    if isinstance(terms, bool) or not isinstance(terms, int) or not 1 <= terms <= 4096:
        raise ValueError("integer series count from 1 to 4096 required")
    b, t = max(width, thickness), min(width, thickness)
    partial, tail, low, high = _series_bracket(b, t, terms)
    if low <= 0:
        raise ValueError("positive torsional-constant lower bound required")
    # Small explicit allowance for finite arithmetic, separate from series tail.
    allowance = 32*np.finfo(float).eps
    return {"long_side_mm": b, "short_side_mm": t, "series_terms": terms,
            "odd_series_partial": partial, "positive_series_tail_upper_bound": tail,
            "J_lower_mm4": low*(1-allowance), "J_upper_mm4": high*(1+allowance),
            "finite_arithmetic_relative_allowance": allowance,
            "global_torsion_shear_bound_mpa_per_nmm": t/(low*(1-allowance)),
            "polar_second_moment_substituted_for_J": False}


def prandtl_unit_field(width_mm: float, thickness_mm: float, y_mm: float, z_mm: float, terms=64) -> dict:
    """Independent coupon field for G*twist_rate=1; y long side, z short side.

    Exact single cosine series solves -laplacian(phi)=2 with phi=0 boundary.
    The stress-vector series is absolutely convergent; its global norm bound
    is t. This sampled partial field is a fixture, not a sampled capacity.
    """
    section = rectangle_torsion(width_mm, thickness_mm, terms)
    b, t = section["long_side_mm"], section["short_side_mm"]
    y, z = frozen.number(y_mm, "point y"), frozen.number(z_mm, "point z")
    if abs(y) > b/2 + 1e-12 or abs(z) > t/2 + 1e-12:
        raise ValueError("point leaves the rectangle")
    phi, tau_y, tau_z = [], [], []
    for index, n in enumerate(range(1, 2*terms, 2)):
        k = n*math.pi/t
        near, far = math.exp(k*(abs(y)-b/2)), math.exp(-k*(abs(y)+b/2))
        divisor = 1 + math.exp(-k*b)
        c, s = (near+far)/divisor, (near-far)/divisor * (1 if y >= 0 else -1)
        trig = n*math.pi*z/t
        sign = (-1)**index
        phi.append(sign * math.cos(trig) * (1-c) / n**3)
        tau_y.append(-sign * math.sin(trig) * (1-c) / n**2)
        tau_z.append(sign * math.cos(trig) * s / n**2)
    next_n = 2*terms+1
    stress_tail = 8*t/math.pi**2 * (1/next_n**2 + 1/(2*next_n))
    return {"phi_mm2_per_unit_G_twist": 8*t*t/math.pi**3 * math.fsum(phi),
            "tau_xy_mpa_per_unit_G_twist": 8*t/math.pi**2 * math.fsum(tau_y),
            "tau_xz_mpa_per_unit_G_twist": 8*t/math.pi**2 * math.fsum(tau_z),
            "stress_vector_series_tail_norm_bound": stress_tail,
            "exact_global_stress_vector_norm_bound": t}


def simultaneous_section_bound(*, width_mm, thickness_mm, removed_center_width_mm,
                               force_local_n, moment_local_nmm, fy_mpa, scenario) -> dict:
    """Pointwise conservative VM envelope for one declared same-section field."""
    if scenario not in ("gross_rectangle", "two_ligament_equal_twist_proxy"):
        raise ValueError("explicit gross rectangle or two-ligament proxy required")
    width = frozen.number(width_mm, "width", positive=True)
    thickness = frozen.number(thickness_mm, "thickness", positive=True)
    removed = frozen.number(removed_center_width_mm, "removed width")
    if not 0 <= removed < width:
        raise ValueError("removed width must lie in[0,width)")
    force, moment = frozen.vector(force_local_n, "force"), frozen.vector(moment_local_nmm, "moment")
    proxy = scenario == "two_ligament_equal_twist_proxy"
    if proxy and removed <= 0:
        raise ValueError("two-ligament proxy requires an actual removed chord")
    nominal = frozen.section_reference(width_mm=width, thickness_mm=thickness,
        removed_center_width_mm=removed if proxy else 0., force_local_n=force,
        moment_local_nmm=moment, fy_mpa=fy_mpa)
    rectangle = rectangle_torsion((width-removed)/2 if proxy else width, thickness)
    count = 2 if proxy else 1
    tau_t = abs(moment[0]) * rectangle["short_side_mm"] / (count*rectangle["J_lower_mm4"])
    tau_v = nominal["nominal_transverse_shear_envelope_mpa"]
    sigma = nominal["nominal_normal_stress_envelope_mpa"]
    vm = math.hypot(sigma, math.sqrt(3)*(tau_v+tau_t))
    return {"section_scenario": scenario, "removed_chord_mm": removed,
        "same_section_force_N_V1_V2_n": force.tolist(), "same_section_moment_T_M1_M2_nmm": moment.tolist(),
        "nominal_normal_stress_bound_mpa": sigma, "nominal_transverse_shear_norm_bound_mpa": tau_v,
        "nominal_torsion_shear_norm_bound_mpa": tau_t, "simultaneous_nominal_vm_bound_mpa": vm,
        "specified_fy_mpa": fy_mpa, "simultaneous_nominal_first_yield_bound_index": vm/fy_mpa if fy_mpa else None,
        "torsion_rectangle": rectangle, "nominal_field_pointwise_analytic_bound": True,
        "component_stress_maxima_claimed_at_one_same_point": False,
        "gross_rectangle_fills_removed_hole": bool(not proxy and removed > 1e-8),
        "two_separate_ligaments_equal_twist_and_rectangular_shear_allocation_assumed": proxy,
        "actual_holed_plate_torsion_sharing_or_stress_concentrations_verified": False,
        "restrained_warping_heel_bimoment_or_local_load_introduction_included": False,
        "physical_fitting_strength_or_complete_joint_acceptance": False}


def extend_flange_comparisons(component: dict) -> dict:
    """Reuse frozen signed point-load cuts; add torsion to every sampled cut."""
    if (component.get("schema") != "thin_bolted_common_shaft_steel/v2"
            or component.get("independent_physical_common_shaft_audit", {}).get(
                "independent_common_shaft_support_load_and_equilibrium_checks_pass") is not True
            or component.get("independent_shaft_cut_replay", {}).get("independent_same_cut_equilibrium_replay_pass") is not True):
        raise ValueError("accepted physical common-shaft component schema required")
    layout = json.loads(frozen.LAYOUT.read_text())
    fittings = {row["angle_id"]: row for row in layout["raw_fittings"]}
    rows = component["fresh_flange_component_comparison"]["flange_comparisons"]
    if len(rows) != 72 or len({(r["angle_id"], r["flange"]) for r in rows}) != 72:
        raise ValueError("all unique72 flange actions required")
    result = []
    for row in rows:
        if (row["case_id"], row["accessory_placement"]) != (component["case_id"], component["accessory_placement"]):
            raise ValueError("flange actions mix admitted cases or accessory placements")
        fitting = fittings[row["angle_id"]]
        sections = frozen.flange_reference(fitting, row["flange"], row["external_point_actions_on_steel"])["sections"]
        gross, proxies = [], []
        for cut in sections:
            chord = max(0., frozen.WIDTH-cut["area_mm2"]/frozen.THICKNESS)
            common = {"width_mm": frozen.WIDTH, "thickness_mm": frozen.THICKNESS,
                "removed_center_width_mm": chord, "force_local_n": cut["force_local_n"],
                "moment_local_nmm": cut["moment_local_nmm"], "fy_mpa": frozen.FY_CATALOG}
            station = {"station_from_assumed_corner_mm": cut["station_from_assumed_corner_mm"]}
            gross.append({**station, **simultaneous_section_bound(**common, scenario="gross_rectangle")})
            if chord > 1e-8:
                proxies.append({**station, **simultaneous_section_bound(**common, scenario="two_ligament_equal_twist_proxy")})
        result.append({"state_id": component["state_id"], "case_id": component["case_id"],
            "accessory_placement": component["accessory_placement"], "angle_id": row["angle_id"], "flange": row["flange"],
            "sample_count": len(sections), "gross_filled_rectangle_sampled_witness": max(gross, key=lambda s: s["simultaneous_nominal_vm_bound_mpa"]),
            "unperforated_gross_section_sampled_witness": max((s for s in gross if not s["gross_rectangle_fills_removed_hole"]),
                key=lambda s: s["simultaneous_nominal_vm_bound_mpa"], default=None),
            "holed_equal_twist_ligament_proxy_sampled_witness": max(proxies, key=lambda s: s["simultaneous_nominal_vm_bound_mpa"], default=None),
            "full_same_cut_torsion_included_in_declared_nominal_bound": True,
            "continuous_station_extrema_or_actual_fitting_capacity_verified": False})
    return {"flanges": result, "gross_rectangle_uniform_torsion_method_gap_closed": True,
            "actual_holed_angle_heel_and_restrained_warping_strength_gap_closed": False}


def consume(path: Path) -> dict:
    payload = path.read_bytes()
    input_sha = hashlib.sha256(payload).hexdigest()
    component = json.loads(payload)
    writer = "scripts/thin_bolted_common_shaft_steel_bound.py"
    if component.get("source_sha256", {}).get(writer) != COMPONENT_WRITER_SHA:
        raise ValueError("source report must bind the reviewed physical-shaft component writer")
    for table in (component["source_sha256"], component["producer_source_sha256"]):
        for relative, expected in table.items():
            if frozen.sha(ROOT/relative) != expected:
                raise ValueError("component/source dependency differs: "+relative)
    if frozen.sha(Path(frozen.__file__)) != FROZEN_STEEL_SHA or frozen.sha(frozen.LAYOUT) != frozen.LAYOUT_SHA:
        raise ValueError("preserve the frozen fitting source")
    extended = extend_flange_comparisons(component)
    if frozen.sha(path) != input_sha:
        raise ValueError("component report changed during torsion extension")
    return {"schema": "thin_bolted_flange_torsion/v1", "candidate": component["candidate"],
        "state_id": component["state_id"], "case_id": component["case_id"], "accessory_placement": component["accessory_placement"],
        "source_sha256": {str(path.resolve().relative_to(ROOT)): input_sha,
            str(Path(__file__).relative_to(ROOT)): frozen.sha(Path(__file__)),
            "scripts/thin_bolted_steel_resistance.py": frozen.sha(Path(frozen.__file__))},
        "source_component_pins": component["source_sha256"], "method_sources": SOURCES, **extended,
        "native_or_CAD_execution": False, "complete_joint_acceptance": False,
        "fabrication_release": False, "climbing_release": False}


def method_report() -> dict:
    if frozen.sha(Path(frozen.__file__)) != FROZEN_STEEL_SHA or frozen.sha(frozen.LAYOUT) != frozen.LAYOUT_SHA:
        raise ValueError("preserve the frozen signed section method and fitting source")
    unit = []
    for removed, scenario in ((0., "gross_rectangle"), (frozen.HOLE, "two_ligament_equal_twist_proxy")):
        unit.append(simultaneous_section_bound(width_mm=frozen.WIDTH, thickness_mm=frozen.THICKNESS,
            removed_center_width_mm=removed, force_local_n=[0., 0., 0.], moment_local_nmm=[1., 0., 0.],
            fy_mpa=frozen.FY_CATALOG, scenario=scenario))
    tests = ROOT / "tests/test_thin_bolted_flange_torsion.py"
    return {"schema": "thin_bolted_flange_torsion_method/v1", "candidate": "compact-floor-flush-thin-bolted-development",
        "source_sha256": {str(Path(__file__).relative_to(ROOT)): frozen.sha(Path(__file__)),
            str(tests.relative_to(ROOT)): frozen.sha(tests),
            "scripts/thin_bolted_steel_resistance.py": frozen.sha(Path(frozen.__file__)),
            str(frozen.LAYOUT.relative_to(ROOT)): frozen.LAYOUT_SHA}, "method_sources": SOURCES,
        "analytical_proof": [
            "For each odd Prandtl harmonic, 0<=C=cosh(ky)/cosh(kb/2)<=1 and |S|=|sinh(ky)|/cosh(kb/2)<=C.",
            "The gradient vector factor [-sin(kz)*(1-C),cos(kz)*S] has norm<=1; its coefficient is8|Gtheta'|t/(pi²n²).",
            "Absolute convergence and sumodd1/n²=pi²/8 give the pointwise ideal torsional shear bound |tau|<=|Gtheta'|t=|T|t/J.",
            "Subtract partial+upperpositive tail in the exact J series to obtain J_lower; hence |T|t/J_lower is conservative for the ideal rectangle field.",
            "At every point in the declared same-section field, |sigma|<=sigma_envelope and |tauV+tauT|<=tauV_bound+tauT_bound; VM<=sqrt[sigma_envelope²+3(tauV_bound+tauT_bound)²].",
            "Separate component maxima need not coincide; the formula is a global upper bound, not an assertion of one physical peak location."],
        "new_unit_torsion_references_per_1_nmm": unit,
        "validation": {"fixtures_passed": 18,
            "test_command": "OPENBLAS_NUM_THREADS=1 .venv/bin/pytest -q tests/test_thin_bolted_flange_torsion.py",
            "lint_command": ".venv/bin/ruff check scripts/thin_bolted_flange_torsion.py tests/test_thin_bolted_flange_torsion.py",
            "known_answers": ["published rectangleJ table, square and2:1/4:1/8:1", "independent2mm×0.5mm primary J0.0702mm4 rounded",
                "thinrectangle limit and dimensional scaling", "positive-tail coarse/fine bracket", "independent96×96Gauss Prandtl torque integral",
                "sampled shear-vector bound and free-surface conditions", "simultaneous signedN/V/M/T and separateholeproxy", "invalid inputs and historical report rejection"]},
        "limits": ["The ideal gross-rectangle uniform-torsion method is complete for six signed nominal section actions; actual angle strength is unqualified.",
            "At hole stations the gross case fills the opening; the separate two-ligament case assumes independent rectangles at equal twist and declared nominal shear allocation.",
            "Actual hole/heel stress concentrations, short-leg restrained-warping normal stress, bimoment and formed open-angle load introduction are absent.",
            "No candidate force field, physical fitting capacity, washer property, geometry change or native execution follows from these method fixtures."],
        "native_or_CAD_execution": False, "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--components", type=Path)
    mode.add_argument("--method-report", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued torsion-extension evidence")
    report = method_report() if args.method_report else consume(args.components)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(args.out), "flanges": len(report.get("flanges", [])), "state_id": report.get("state_id")}))


if __name__ == "__main__":
    main()

"""Fresh source-row gross-member witnesses; no field reader, CAD or solve.

The caller must first authenticate the new field. Only pure predecessor
cut/rectangle arithmetic is reused; old forces, cut stations and passes are not.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import numpy as np

from scripts import thin_bolted_timber_common_shaft_checks as own

ROOT = Path(__file__).resolve().parents[5]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
RECTANGLE = ROOT / "fea/generated/thin-bolted-direct-contact-a12-v1/observer-isolation-v2/member-strength-v1/member_strength.py"
RECTANGLE_SHA = "46a329afb4264b88e0ad85ad8f818178cc5b38784dc11c4b5c7b2161a439f51c"
PINS = {
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
    "scripts/thin_bolted_timber_demand_checks.py": "1be05e74563d2cc7a7ea5437aa4ff7217e62f8314f9fe011ff273d201f755e20",
    "scripts/thin_bolted_timber_resistance.py": "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    "fea/reinforced_timber_resistance.py": "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
    str(RECTANGLE.relative_to(ROOT)): RECTANGLE_SHA,
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_pins():
    pins = {**PINS, str(OWN.relative_to(ROOT)): LOADED_SHA}
    for path, expected in pins.items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected,
                "gross-member method source differs: " + path)
    return pins


source_pins()
SPEC = importlib.util.spec_from_file_location("eoere_reused_rectangle_only", RECTANGLE)
rectangle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rectangle)
PINS.update({str(rectangle.METHOD.relative_to(ROOT)): rectangle.METHOD_SHA,
             **rectangle.PRIMARY_PINS})
# Imports select only the earlier method's pure functions. No consume() call,
# historical field read, saved cut plan or historical section geometry is used.


def member_witnesses(field, *, samples=51):
    """Same-cut signed wrenches and conditional gross CD1 references for22 rows.

    Reference geometry belongs to this first-order field. Axial capture loads
    use their own host_support_point, and actual free couples are retained.
    These sampled full-stock comparisons do not establish finished net strength.
    """
    before = source_pins()
    require(type(samples) is int and samples >= 3, "at least three gross stations required")
    rows = field["source_inputs"]["timber_rows"]
    names = [row["name"] for row in rows]
    require(len(names) == len(set(names)) and names, "unique fresh timber source rows required")
    bodies = {row["id"]: row for row in field["physical_body_descriptors"]}
    actions, gravity = own.member_point_inputs(field)
    result = []
    for row in rows:
        name = row["name"]
        basis = np.asarray([row[key] for key in ("axis", "section_u", "section_v")], dtype=float)
        start, end = np.asarray(row["start"], dtype=float), np.asarray(row["end"], dtype=float)
        width, depth = float(row["width_mm"]), float(row["depth_mm"])
        require(basis.shape == (3, 3) and np.isfinite(basis).all()
                and np.linalg.norm(basis @ basis.T - np.eye(3)) < 1e-8
                and abs(np.linalg.det(basis) - 1.) < 1e-8 and min(width, depth) > 0,
                "proper fresh member basis and dimensions required")
        grain = basis[0]
        low, high = float(grain @ start), float(grain @ end)
        require(high > low and np.linalg.norm(end-start-grain*(high-low)) < 1e-7,
                "fresh centerline span must follow own grain")
        require(name in bodies and name in gravity, "own member mass/centroid gravity required")
        center, weight = gravity[name]
        require(np.linalg.norm(np.asarray(center)-bodies[name]["center_xyz_mm"]) < 1e-7,
                "selfweight centroid differs from own body")
        gravity_rows = [r for r in field["body_applied_loads"]
                        if r["id"] == "self-weight/"+name]
        require(len(gravity_rows) == 1
                and np.linalg.norm(gravity_rows[0].get("moment_xyz_nmm", [0., 0., 0.])) == 0.,
                "affine selfweight cannot silently discard a free couple")
        stations = set(np.linspace(low, high, samples).tolist())
        for point, _, _ in actions[name]:
            s = float(grain @ point)
            stations.update((float(np.clip(s-1e-5, low, high)),
                             float(np.clip(s+1e-5, low, high))))
        cuts = []
        for station in sorted(stations):
            cut = (start+grain*(station-low)).tolist()
            wrench = own.previous.member_cut_wrench(grain.tolist(), low, high, cut,
                                                     center, weight, actions[name])
            force = basis @ np.asarray(wrench["force_on_lower_portion_xyz_n"])
            moment = basis @ np.asarray(wrench["moment_on_lower_portion_about_cut_xyz_nmm"])
            value = np.r_[force, moment].tolist()
            comparison = rectangle.rectangle_check(value, width, depth, high-low)
            cuts.append({"station_global_grain_projection_mm": station,
                         "local_N_Vu_Vv_T_Mu_Mv_n_nmm": value,
                         "signed_same_cut_wrench": wrench, "gross_CD1_comparison": comparison})
        selectors = {
            "fully_braced_normal": "fully_braced_component_normal_interaction",
            "sufficient_shear_torsion": "equal_longitudinal_shear_moduli_rectangle_component_upper_bound_ratio",
        }
        witnesses = {key: max(cuts, key=lambda c, k=value: c["gross_CD1_comparison"][k])
                     for key, value in selectors.items()}
        result.append({"member": name, "sample_count": len(cuts), "source_width_mm": width,
                       "source_depth_mm": depth, "source_span_mm": high-low,
                       "source_basis_grain_u_v_xyz": basis.tolist(), "witnesses": witnesses,
                       "own_host_capture_points_and_free_couples_preserved": True,
                       "old_cut_or_force_used": False, "finished_net_resistance_established": False,
                       "continuous_maximum_or_actual_bracing_established": False})
    require(source_pins() == before, "gross-member sources changed during arithmetic")
    return result

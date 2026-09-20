"""Conditional PB01 cleat gross rectangular stress components from frozen sections.

These are isolated elastic stress components, not adjusted design checks.
"""

import hashlib
import json
import math
import tarfile

from scripts.simple_pb01_hybrid_local_actions import (
    ARCHIVE,
    REPORT_SHA256,
    extract,
    require,
)

WIDTH_MM = 139.7
DEPTH_MM = 57.15
LENGTH_MM = 300.0
LOAD_KEYS = (
    "axial_n_tension_positive",
    "shear_u_n",
    "shear_v_n",
    "moment_u_nmm",
    "moment_v_nmm",
    "torsion_nmm",
)


def finite_number(value, label):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        raise ValueError(f"Invalid {label}")
    return float(value)


def stress_components(section, width_mm, depth_mm):
    """Resolve isolated elastic components in N/mm² for one reported cut side."""
    width = finite_number(width_mm, "width_mm")
    depth = finite_number(depth_mm, "depth_mm")
    require(width > 0 and depth > 0, "Gross dimensions must be positive")
    station = finite_number(section["station_along_grain_mm"], "station_along_grain_mm")
    include = section["include_station_loads"]
    require(isinstance(include, bool), "Invalid include_station_loads")
    loads = {key: finite_number(section[key], key) for key in LOAD_KEYS}
    area = width * depth
    section_modulus_u = width * depth**2 / 6
    section_modulus_v = depth * width**2 / 6
    axial = loads["axial_n_tension_positive"] / area
    bending_u = loads["moment_u_nmm"] / section_modulus_u
    bending_v = loads["moment_v_nmm"] / section_modulus_v
    shear_u = 1.5 * loads["shear_u_n"] / area
    shear_v = 1.5 * loads["shear_v_n"] / area
    corner_bending = abs(bending_u) + abs(bending_v)
    return {
        "station_along_grain_mm": station,
        "include_station_loads": include,
        "axial_mpa": axial,
        "bending_u_mpa": bending_u,
        "bending_v_mpa": bending_v,
        "shear_u_peak_mpa": shear_u,
        "shear_v_peak_mpa": shear_v,
        "normal_tension_corner_mpa": max(0.0, axial + corner_bending),
        "normal_compression_corner_mpa": max(0.0, -axial + corner_bending),
        "transverse_shear_center_mpa": math.hypot(shear_u, shear_v),
        "torsion_nmm": loads["torsion_nmm"],
        "torsional_stress_mpa": None,
    }


def _maximum(rows, field, magnitude=abs):
    row = max(rows, key=lambda item: magnitude(item[field]))
    return {
        "value": magnitude(row[field]),
        "station_along_grain_mm": row["station_along_grain_mm"],
        "include_station_loads": row["include_station_loads"],
        "signed_component": row[field],
    }


def screen(path=ARCHIVE):
    """Authenticate the frozen hybrid report, then screen every cleat cut side."""
    evidence = extract(path)
    with tarfile.open(path, "r:gz") as bundle:
        member = bundle.extractfile("report.json")
        require(member is not None, "Missing report.json")
        raw = member.read()
    require(hashlib.sha256(raw).hexdigest() == REPORT_SHA256, "Report SHA-256 mismatch")
    report = json.loads(raw)
    demand = report["member_section_demands"]["base_cleat_pb01"]
    member = demand["member"]
    require(member["name"] == "base_cleat_pb01", "Wrong section member")
    require(member["qualified_for_design"] is False, "Changed design qualification")
    require(
        math.isclose(
            finite_number(member["gross_width_mm"], "gross_width_mm"),
            WIDTH_MM,
            abs_tol=1e-6,
        )
        and math.isclose(
            finite_number(member["gross_depth_mm"], "gross_depth_mm"),
            DEPTH_MM,
            abs_tol=1e-6,
        )
        and math.isclose(
            finite_number(member["width_mm"], "width_mm"), WIDTH_MM, abs_tol=1e-6
        )
        and math.isclose(
            finite_number(member["depth_mm"], "depth_mm"), DEPTH_MM, abs_tol=1e-6
        )
        and math.isclose(
            finite_number(member["area_mm2"], "area_mm2"),
            WIDTH_MM * DEPTH_MM,
            abs_tol=1e-6,
        )
        and math.isclose(
            finite_number(demand["length_mm"], "length_mm"), LENGTH_MM, abs_tol=1e-6
        ),
        "Cleat gross section differs from modeled rectangle",
    )
    require(member["retained_area_fraction"] == 1.0, "Unexpected section reduction")
    rows = [
        stress_components(section, WIDTH_MM, DEPTH_MM) for section in demand["sections"]
    ]
    require(len(rows) == 20, "Unexpected cleat section inventory")
    require(
        all(-1e-6 <= row["station_along_grain_mm"] <= LENGTH_MM + 1e-6 for row in rows),
        "Section outside modeled length",
    )
    area = WIDTH_MM * DEPTH_MM
    return {
        "case": evidence["case"],
        "candidate": evidence["candidate"],
        "scope": evidence["scope"],
        "archive_sha256": evidence["archive_sha256"],
        "report_sha256": evidence["report_sha256"],
        "member": "base_cleat_pb01",
        "geometry_mm": {
            "width_u": WIDTH_MM,
            "depth_v": DEPTH_MM,
            "length_along_grain": LENGTH_MM,
            "gross_area_mm2": area,
            "section_modulus_u_mm3": WIDTH_MM * DEPTH_MM**2 / 6,
            "section_modulus_v_mm3": DEPTH_MM * WIDTH_MM**2 / 6,
        },
        "method": "Gross elastic N/A axial, M_u/S_u and M_v/S_v bending, signed 3V_u/(2A) and 3V_v/(2A) rectangular peak shear; same-cut corner normal stress and center transverse shear magnitude; 1 N/mm² = 1 MPa",
        "sections": rows,
        "maxima": {
            "axial_tension_mpa": _maximum(rows, "axial_mpa", lambda x: max(x, 0.0)),
            "axial_compression_mpa": _maximum(
                rows, "axial_mpa", lambda x: max(-x, 0.0)
            ),
            "bending_u_abs_mpa": _maximum(rows, "bending_u_mpa"),
            "bending_v_abs_mpa": _maximum(rows, "bending_v_mpa"),
            "shear_u_peak_abs_mpa": _maximum(rows, "shear_u_peak_mpa"),
            "shear_v_peak_abs_mpa": _maximum(rows, "shear_v_peak_mpa"),
            "normal_tension_corner_mpa": _maximum(rows, "normal_tension_corner_mpa"),
            "normal_compression_corner_mpa": _maximum(
                rows, "normal_compression_corner_mpa"
            ),
            "transverse_shear_center_mpa": _maximum(
                rows, "transverse_shear_center_mpa"
            ),
            "torsion_abs_nmm": _maximum(rows, "torsion_nmm"),
        },
        "reference_design_values_mpa": None,
        "net_section_stress_mpa": None,
        "combined_stress_mpa": None,
        "capacity_n": None,
        "utilization": None,
        "complete_joint_pass": None,
        "limits": [
            "One authenticated a12-left hybrid diagnostic; 23 other stations are old ML24Z/SDS proxies, so these are not full V4 design demands.",
            "Gross unbored rectangle only: bolt bores and any net or critical section are not represented by the reported retained-area fraction of 1.0.",
            "Nonzero torsion is reported, but torsional stress and its interaction with bending, shear, and axial stress are not calculated.",
            "Isolated component peaks can occur at different cuts and cannot be added as independent maxima; same-cut elastic combinations exclude torsion and strength interaction.",
            "Same-cut corner normal stress combines axial and biaxial bending elastically; center transverse shear combines orthogonal shear components, but torsion and failure interaction are excluded.",
            "Delivered cleat species and grade, moisture, load duration, size, and other NDS adjustment applicability are unverified; no reference value, adjusted capacity, or utilization is adopted.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2, sort_keys=True))

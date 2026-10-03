"""Independent analytic geometry for the hypothetical nut and washer solids.

No CAD, mesh, solver, source stiffness or resistance is read or calculated.
The volume formula integrates a circle clipped by six hex half-spaces;
separate numerical quadrature checks it and supplies the axial centroid.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

from scipy.integrate import quad

HERE = Path(__file__).resolve().parent
PROFILE = HERE / "conditional-nut-profile.json"
PROFILE_SHA = "d30a5e94e7adbd4b617ea85af8790955738025dbae26af544efc96b29fecab34"


def circle_hex_area(radius: float, apothem: float) -> float:
    if not 0 < radius <= apothem / math.cos(math.pi / 6) + 1e-13:
        raise ValueError(
            "Only circles below the regular-hex vertex radius are supported"
        )
    if radius <= apothem:
        return math.pi * radius**2
    cap = radius**2 * math.acos(apothem / radius) - apothem * math.sqrt(
        radius**2 - apothem**2
    )
    return math.pi * radius**2 - 6 * cap


def area_primitive(radius: float, apothem: float) -> float:
    value = math.pi * radius**3 / 3
    if radius > apothem:
        s = math.sqrt(radius**2 - apothem**2)
        cap_primitive = (
            radius**3 * math.acos(apothem / radius)
            - 2 * apothem * radius * s
            + apothem**3 * math.log((radius + s) / apothem)
        ) / 3
        value -= 6 * cap_primitive
    return value


def calculate() -> dict:
    raw = PROFILE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PROFILE_SHA:
        raise ValueError("Parent hypothetical profile changed")
    p = json.loads(raw)
    height = p["nut_height"]
    apothem = p["silhouette"]["regular_hex_across_flats"] / 2
    clipped_radius = p["silhouette"]["coaxial_corner_clip_diameter"] / 2
    bore = p["bearing_side_inner_relief"]["smooth_through_bore_radius"]
    land_inner = p["bearing_side_inner_relief"]["land_inner_radius"]
    assert math.isclose(
        circle_hex_area(apothem, apothem), math.pi * apothem**2, rel_tol=1e-14
    )
    assert math.isclose(
        circle_hex_area(apothem / math.cos(math.pi / 6), apothem),
        2 * math.sqrt(3) * apothem**2,
        rel_tol=1e-14,
    )
    hole_volume = math.pi * (
        (land_inner**3 - bore**3) / 3 + bore**2 * (height - land_inner + bore)
    )
    result = {}
    for branch in ("H1", "H2"):
        land_outer = p["bearing_side_outer_relief"][branch + "_land_outer_radius"]
        transition = clipped_radius - land_outer
        assert 0 < transition < height and bore < land_inner < land_outer <= apothem
        outer_volume = area_primitive(clipped_radius, apothem) - area_primitive(
            land_outer, apothem
        )
        outer_volume += (height - transition) * circle_hex_area(clipped_radius, apothem)
        volume = outer_volume - hole_volume

        def section(depth: float, land_radius: float = land_outer) -> float:
            return (
                circle_hex_area(min(land_radius + depth, clipped_radius), apothem)
                - math.pi * max(bore, land_inner - depth) ** 2
            )

        breaks = sorted(
            {0.0, height, land_inner - bore, transition, max(0.0, apothem - land_outer)}
        )
        quadrature_volume = 0.0
        quadrature_first_moment = 0.0
        error_estimate = 0.0
        for lo, hi in itertools.pairwise(breaks):
            v, err = quad(section, lo, hi, epsabs=1e-10, epsrel=1e-12)
            moment, _ = quad(
                lambda depth: depth * section(depth), lo, hi, epsabs=1e-10, epsrel=1e-12
            )
            quadrature_volume += v
            quadrature_first_moment += moment
            error_estimate += err
        difference = abs(volume - quadrature_volume)
        if difference > 1e-8:
            raise ValueError("Closed-form volume disagrees with independent quadrature")
        result[branch] = {
            "volume_mm3": volume,
            "independent_quadrature_volume_mm3": quadrature_volume,
            "volume_difference_mm3": difference,
            "quadrature_error_estimate_mm3": error_estimate,
            "centroid_depth_from_bearing_plane_mm": quadrature_first_moment
            / quadrature_volume,
            "initial_annular_land_area_mm2": math.pi * (land_outer**2 - land_inner**2),
            "outward_load_face_area_mm2": circle_hex_area(clipped_radius, apothem)
            - math.pi * bore**2,
            "outer_relief_to_full_silhouette_depth_mm": transition,
        }
    washer_od, washer_id, washer_thickness = 18.653125, 7.9248, 1.5875
    return {
        "scope": "independent hypothetical hardware geometry only; no CAD/mesh/native/resistance",
        "profile_sha256": PROFILE_SHA,
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "nut_branches": result,
        "washer": {
            "OD_ID_thickness_mm": [washer_od, washer_id, washer_thickness],
            "volume_mm3": math.pi
            * (washer_od**2 - washer_id**2)
            * washer_thickness
            / 4,
            "annular_face_area_mm2": math.pi * (washer_od**2 - washer_id**2) / 4,
        },
        "geometry_limit": "Hypothetical clipped/relieved solids only; no product shape, support footprint, contact activity, material strength or candidate qualification",
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2, sort_keys=True, allow_nan=False))

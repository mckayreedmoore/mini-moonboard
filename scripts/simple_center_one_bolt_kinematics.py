"""Bound the PB-02 one-bolt/frictionless-face point-model mechanism."""

import json

import numpy as np

# Nominal centers of the four new serial interfaces in the revised combined
# center pose. Face spans only pick non-collinear illustrative contact points;
# the free twist result is independent of their exact distances.
INTERFACES = {
    "post_cleat": ((177.65, -150.0, 160.0), (1.0, 0.0, 0.0), 30.0, 40.0),
    "cleat_header": ((222.1, -130.0, 238.9), (0.0, 0.0, 1.0), 30.0, 30.0),
    "header_cleat": ((15.475, -145.3, 277.0), (0.0, 0.0, 1.0), 20.0, 30.0),
    "cleat_principal": ((50.95, -95.0, 307.5), (1.0, 0.0, 0.0), 20.0, 20.0),
}


def _row(direction, point):
    """Rigid relative translation/rotation at a point, about the bolt center."""
    return np.r_[direction, np.cross(point, direction)]


def _interface(center, normal, half_a, half_b):
    n = np.asarray(normal, dtype=float)
    seed = np.eye(3)[int(np.argmin(abs(n)))]
    tangent_a = np.cross(n, seed)
    tangent_a /= np.linalg.norm(tangent_a)
    tangent_b = np.cross(n, tangent_a)
    contact_points = [
        a * half_a * tangent_a + b * half_b * tangent_b
        for a in (-1.0, 1.0)
        for b in (-1.0, 1.0)
    ]
    lateral = [_row(tangent_a, np.zeros(3)), _row(tangent_b, np.zeros(3))]
    contacts = [_row(n, point) for point in contact_points]
    one_with_axial = np.asarray([*lateral, _row(n, np.zeros(3)), *contacts])
    one_without_axial = np.asarray([*lateral, *contacts])
    second_bolt = tangent_a * min(half_a, 20.0)
    two_with_one_axial = np.asarray(
        [
            *one_with_axial,
            _row(tangent_a, second_bolt),
            _row(tangent_b, second_bolt),
        ]
    )
    free_twist = np.r_[np.zeros(3), n]
    return {
        "bolt_center_xyz_mm": list(center),
        "face_normal_xyz": list(normal),
        "illustrative_contact_half_spans_mm": [half_a, half_b],
        "one_bolt_rank_with_axial": int(np.linalg.matrix_rank(one_with_axial)),
        "one_bolt_rank_without_axial": int(np.linalg.matrix_rank(one_without_axial)),
        "face_normal_twist_null_residual": float(
            np.linalg.norm(one_with_axial @ free_twist)
        ),
        "two_bolt_rank_with_one_axial": int(np.linalg.matrix_rank(two_with_one_axial)),
        "two_bolt_spacing_mm_illustrative": float(np.linalg.norm(second_bolt)),
    }


def screen():
    """Show model rank only, never a physical strength or contact verdict."""
    return {
        "model": "single point bolt with two lateral springs, optional no-preload axial spring, and four frictionless compression-only face samples",
        "interfaces": {
            name: _interface(*geometry) for name, geometry in INTERFACES.items()
        },
        "interpretation": "Each one-bolt point idealization has an unresisted relative face-normal twist even if all four contacts are closed. Ideal coaxial round-bolt/bore radial bearing alone cannot resist twist about that axis; friction or another independently justified restraint is not represented or credited.",
        "two_bolt_result_is_geometry_or_capacity_check": False,
        "physical_joint_failure_claimed": False,
        "rating_or_drilling_release": False,
    }


if __name__ == "__main__":
    print(json.dumps(screen(), indent=2))

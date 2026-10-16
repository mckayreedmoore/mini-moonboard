"""Known-answer checks for bore-domain quadrature; no assembly or solve."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(path for path in HERE.parents if (path / "current-candidate.json").is_file())
AUDIT = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/exceedance-remedy-screen/splitting-hotspot-audit01.json"
)
HELPER_PATH = HERE / "bore-domain-correction.py"
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("bore_domain_correction", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(helper)

from fea.floor_recess_mesh import CORNERS, EDGES, shape20
from fea.wood_joint_reduced_members import shape20_derivatives


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_nodes(low: np.ndarray, high: np.ndarray) -> np.ndarray:
    natural = np.vstack((CORNERS, EDGES)).astype(float)
    return (low + high) / 2.0 + natural * ((high - low) / 2.0)


def assert_outside(rule: dict, bore: dict) -> None:
    points = rule["physical_points_mm"]
    if not len(points):
        return
    axis = np.asarray(bore["axis"], dtype=float)
    origin = np.asarray(bore["origin"], dtype=float)
    relative = points - origin
    along = relative @ axis
    radial = np.linalg.norm(relative - along[:, None] * axis, axis=1)
    within = (along >= bore["interval_mm"][0]) & (along <= bore["interval_mm"][1])
    assert not np.any(within & (radial < bore["radius_mm"])), "quadrature inside exact bore"


def nearest_saved_cut_element(nodes_mm: np.ndarray, elements: np.ndarray, bore: dict) -> int:
    corners = nodes_mm[elements[:, :8]]
    low, high = corners.min(axis=1), corners.max(axis=1)
    origin = np.asarray(bore["origin"], dtype=float)
    direction = np.asarray(bore["axis"], dtype=float)
    shaft = int(np.argmax(np.abs(direction)))
    radial = [axis for axis in range(3) if axis != shaft]
    axial_ends = origin[shaft] + direction[shaft] * np.asarray(bore["interval_mm"])
    axial_overlap = np.maximum(
        0.0,
        np.minimum(high[:, shaft], np.max(axial_ends))
        - np.maximum(low[:, shaft], np.min(axial_ends)),
    )
    nearest = np.maximum(
        0.0,
        np.maximum(
            low[:, radial] - origin[radial], origin[radial] - high[:, radial]
        ),
    )
    farthest = np.maximum(
        np.abs(low[:, radial] - origin[radial]),
        np.abs(high[:, radial] - origin[radial]),
    )
    intersects = (
        (axial_overlap > 0.0)
        & (np.sum(nearest**2, axis=1) < bore["radius_mm"] ** 2)
        & (np.sum(farthest**2, axis=1) > bore["radius_mm"] ** 2)
    )
    choices = np.flatnonzero(intersects)
    assert len(choices), "saved mesh has no positive-volume cell cut by selected bore"
    centers = (low[choices] + high[choices]) / 2.0
    center_delta = centers[:, radial] - origin[radial]
    nearest_order = np.argmin(np.linalg.norm(center_delta, axis=1))
    return int(choices[nearest_order])


def known_answer() -> dict:
    low, high = np.full(3, -1.0), np.full(3, 1.0)
    nodes = cell_nodes(low, high)
    exact_volume = 8.0 - 0.5 * np.pi
    bore = {
        "origin": [0.0, 0.0, 0.0],
        "axis": [1.0, 0.0, 0.0],
        "interval_mm": [-1.0, 1.0],
        "radius_mm": 0.5,
    }
    box_geometry = {
        "actual_volume_mm3": exact_volume,
        "planes": [
            {"normal": [1.0, 0.0, 0.0], "offset": 1.0},
            {"normal": [-1.0, 0.0, 0.0], "offset": 1.0},
            {"normal": [0.0, 1.0, 0.0], "offset": 1.0},
            {"normal": [0.0, -1.0, 0.0], "offset": 1.0},
            {"normal": [0.0, 0.0, 1.0], "offset": 1.0},
            {"normal": [0.0, 0.0, -1.0], "offset": 1.0},
        ],
        "bores": [bore],
    }
    rebuilt = helper.positive_volume_c3d20_mesh(
        [-1.0, 1.0], [-1.0, 1.0], [-1.0, 1.0], box_geometry
    )
    assert rebuilt["elements"].shape == (1, 20)
    assert rebuilt["element_bore_indices"] == [0]
    assert rebuilt["positive_volume_cut_cell_count"] == 1
    assert abs(rebuilt["retained_volume_mm3"] - exact_volume) < 1e-12
    coarse = helper.c3d20_cylinder_cut_rule(nodes, bore, order=8)
    fine = helper.c3d20_cylinder_cut_rule(nodes, bore, order=16)
    assert abs(fine["report"]["exact_retained_volume_mm3"] - exact_volume) < 1e-12
    assert fine["report"]["relative_volume_error"] < 2e-7
    assert fine["report"]["moment_error_vs_2x_order"] < 2e-6
    assert abs(coarse["report"]["integrated_volume_mm3"] - exact_volume) < 1e-5
    assert_outside(coarse, bore)
    assert_outside(fine, bore)
    # An entirely void box must remain exactly empty under volume subtraction;
    # rounded analytic circle areas must not create positive-material slivers.
    empty_low=np.array([-0.8,-0.2,-0.2])
    empty_high=np.array([0.8,0.2,0.2])
    assert helper.exact_cylinder_retained_volume_mm3(empty_low,empty_high,bore)==0.0
    empty=helper.c3d20_cylinder_cut_rule(cell_nodes(empty_low,empty_high),bore,order=4)
    assert len(empty["natural_points"])==0
    # A finite Y-axis bore endpoint and a CAD-equivalent grid plane differ
    # here by one ulp. No positive-weight sample may enter the void at that
    # plane; radial partial cells still retain their real wood volume.
    endpoint_bore={"origin":[35.,-82.54999999999998,0.],"axis":[0.,1.,0.],
        "interval_mm":[38.099999999999994,127.],"radius_mm":3.65}
    endpoint_nodes=cell_nodes(np.array([31.35,-44.45,-3.65]),np.array([33.175,-26.67,-1.825]))
    endpoint_rule=helper.c3d20_cylinder_cut_rule(endpoint_nodes,endpoint_bore,order=8)
    assert_outside(endpoint_rule,endpoint_bore)
    assert endpoint_rule["report"]["maximum_axial_plane_roundoff_alignment_mm"]<1e-12
    assert endpoint_rule["report"]["relative_volume_error"]<1e-12
    void_low=np.array([33.175,-44.45,0.])
    void_high=np.array([35.,-26.67,1.825])
    assert helper.exact_cylinder_retained_volume_mm3(void_low,void_high,endpoint_bore)==0.0
    assert len(helper.c3d20_cylinder_cut_rule(cell_nodes(void_low,void_high),endpoint_bore,order=4)["natural_points"])==0

    # Symmetric retained geometry has zero first moments about the cell center.
    centroid_numerator = np.einsum(
        "i,ij->j", fine["weights_mm3"], fine["physical_points_mm"]
    )
    assert np.max(np.abs(centroid_numerator)) < 2e-8

    # A C3D20 field must reproduce an arbitrary affine displacement at all
    # retained integration points and its constant infinitesimal strain.
    gradient = np.array([[0.012, -0.003, 0.004], [0.006, -0.008, 0.002], [-0.005, 0.007, 0.011]])
    offset = np.array([0.2, -0.4, 0.8])
    displacement_nodes = nodes @ gradient.T + offset
    target_strain = 0.5 * (gradient + gradient.T)
    strain_integral = np.zeros((3, 3))
    patch_error = 0.0
    for point, natural, weight in zip(
        fine["physical_points_mm"], fine["natural_points"], fine["weights_mm3"], strict=True
    ):
        assert np.max(np.abs(shape20(natural) @ nodes - point)) < 1e-12
        derivatives = shape20_derivatives(natural)
        jacobian = nodes.T @ derivatives
        physical_gradient = displacement_nodes.T @ derivatives @ np.linalg.inv(jacobian)
        strain = 0.5 * (physical_gradient + physical_gradient.T)
        patch_error = max(patch_error, float(np.max(np.abs(strain - target_strain))))
        strain_integral += strain * weight
    assert patch_error < 2e-12
    assert np.max(np.abs(strain_integral - target_strain * exact_volume)) < 2e-7
    constitutive = np.diag([100.0, 80.0, 90.0, 20.0, 25.0, 30.0])
    stress = helper.c3d20_stress_at_rule(
        nodes, displacement_nodes, constitutive, fine
    )
    target_engineering_strain = np.array(
        [target_strain[0, 0], target_strain[1, 1], target_strain[2, 2],
         2.0 * target_strain[0, 1], 2.0 * target_strain[0, 2],
         2.0 * target_strain[1, 2]]
    )
    expected_stress = constitutive @ target_engineering_strain
    assert np.max(np.abs(stress - expected_stress)) < 2e-10
    return {
        "exact_retained_volume_mm3": exact_volume,
        "coarse_order8_relative_volume_error": coarse["report"]["relative_volume_error"],
        "fine_order16_relative_volume_error": fine["report"]["relative_volume_error"],
        "fine_order16_vs32_moment_error": fine["report"]["moment_error_vs_2x_order"],
        "affine_patch_max_strain_error": patch_error,
        "integration_points_order8_order16": [
            coarse["report"]["integration_point_count"],
            fine["report"]["integration_point_count"],
        ],
        "center_deleted_positive_cell_restored": True,
        "vectorized_truewood_stress_patch_error_mpa": float(
            np.max(np.abs(stress - expected_stress))
        ),
    }


def actual_hotspots() -> list[dict]:
    audit = json.loads(AUDIT.read_text())
    for relative, expected in audit["sources_sha256"].items():
        assert digest(ROOT / relative) == expected, relative
    pins = audit["sources_sha256"]
    geometry_rel = next(
        relative
        for relative in pins
        if relative.endswith("all-joint-splitting/rawlocal/splitting-capacity-completion/coupled-prepared01/geometry.json")
    )
    geometries = json.loads((ROOT / geometry_rel).read_text())
    records = []
    for side in ("left", "right"):
        source = next(record for record in audit["records"] if record["side"] == side)
        assert source["sample_inside_any_exact_void"] is (side == "left")
        if side == "left":
            assert abs(
                source["nearest_bore"]["radial_clearance_mm"] + 0.778184040450586
            ) < 1e-9
        geometry = geometries[f"center_post_cleat_{side}"]
        bore_id = source["nearest_bore"]["bore_id"]
        bore = next(item for item in geometry["bores"] if item["id"] == bore_id)
        with np.load(ROOT / source["operator_source"], allow_pickle=False) as operator:
            all_nodes = operator["nodes_mm"]
            all_elements = operator["elements"]
        old_point = np.asarray(source["local_point_g_u_v_mm"], dtype=float)
        origin = np.asarray(bore["origin"], dtype=float)
        axis = np.asarray(bore["axis"], dtype=float)
        delta = old_point - origin
        radial = np.linalg.norm(delta - (delta @ axis) * axis)
        if side == "left":
            assert radial < bore["radius_mm"]
        else:
            assert radial > bore["radius_mm"]

        cut_element = (
            source["element_zero_based"]
            if side == "left"
            else nearest_saved_cut_element(all_nodes, all_elements, bore)
        )
        cut_nodes = all_nodes[all_elements[cut_element]]
        cut_low, cut_high = cut_nodes.min(axis=0), cut_nodes.max(axis=0)
        cut_hits = helper.intersecting_bore_indices(
            cut_low, cut_high, geometry["bores"]
        )
        assert len(cut_hits) == 1 and geometry["bores"][cut_hits[0]]["id"] == bore_id
        rules = [helper.c3d20_cylinder_cut_rule(cut_nodes, bore, order=order) for order in (4, 8)]
        for rule in rules:
            assert_outside(rule, bore)
            assert rule["report"]["relative_volume_error"] < 2e-6
            assert rule["report"]["bore_active"]
        records.append(
            {
                "side": side,
                "source_state": source["state"],
                "element_zero_based": source["element_zero_based"],
                "cut_element_zero_based": cut_element,
                "exact_bore_id": bore_id,
                "previous_gauss_point_radial_clearance_mm": float(
                    radial - bore["radius_mm"]
                ),
                "corrected_cell_retained_volume_mm3": rules[-1]["report"][
                    "exact_retained_volume_mm3"
                ],
                "order4_order8": [
                    {
                        "integration_point_count": rule["report"][
                            "integration_point_count"
                        ],
                        "relative_volume_error": rule["report"][
                            "relative_volume_error"
                        ],
                        "moment_error_vs_2x_order": rule["report"][
                            "moment_error_vs_2x_order"
                        ],
                        "minimum_truewood_bore_clearance_mm": rule["report"][
                            "minimum_bore_clearance_mm"
                        ],
                    }
                    for rule in rules
                ],
                "historical_governing_sample_inside_exact_bore": side == "left",
                "cut_cell_rule_contains_only_truewood_quadrature": True,
                "stiffness_and_stress_rules_identical": True,
            }
        )
    return records


if __name__ == "__main__":
    print(
        json.dumps(
            {
                "status": "PASS_GEOMETRY_AND_AFFINE_PATCH_KNOWN_ANSWER",
                "new_assembly_or_solve": False,
                "centered_cylinder_known_answer": known_answer(),
                "saved_left_and_right_hotspots": actual_hotspots(),
                "strength_or_initiation_capacity_inferred": False,
            },
            indent=2,
            sort_keys=True,
        )
    )

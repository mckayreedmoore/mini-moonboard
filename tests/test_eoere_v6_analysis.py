"""Fast property and source-join checks for the v6 mechanics adapter.

These tests read the frozen inputs and BRep bytes but do not build CAD,
prepare a candidate, or solve a case.
"""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from scripts import eoere_v6_analysis as v6

ROOT = Path(__file__).resolve().parents[1]
ARCHIVED_V4_MATERIAL = (
    v6.WORK / "owner-bolt-moves-v4/analysis/material.json"
)
ARCHIVED_V4_MATERIAL_SHA256 = (
    "07c749f8f18ccbd121679b9e7768ce70f0dc0e474176bf570d5ad689503401ae"
)


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived_v4_properties():
    assert file_sha256(ARCHIVED_V4_MATERIAL) == ARCHIVED_V4_MATERIAL_SHA256
    return json.loads(ARCHIVED_V4_MATERIAL.read_text())["properties"]


def test_2032_mm_operator_reproduces_the_archived_v4_material():
    expected = archived_v4_properties()
    observed = v6.plywood_properties(width=203.2, thickness=19.05)

    assert observed.keys() == expected.keys()
    for name, value in expected.items():
        assert observed[name] == pytest.approx(value, rel=1e-12, abs=1e-10)


def rectangle_torsion(width, thickness):
    return width * thickness**3 * (
        1 / 3 - 0.21 * thickness / width
        * (1 - thickness**4 / (12 * width**4))
    )


def test_1397_mm_pair_properties_follow_section_width_scaling():
    old_width, width, thickness = 203.2, 139.7, 19.05
    old = v6.plywood_properties(width=old_width, thickness=thickness)
    current = v6.plywood_properties(width=width, thickness=thickness)
    ratio = width / old_width

    assert current["EA_N"] == pytest.approx(old["EA_N"] * ratio, rel=1e-12)
    assert current["EI_z_Nmm2"] == pytest.approx(
        old["EI_z_Nmm2"] * ratio, rel=1e-12
    )
    assert current["EI_y_Nmm2"] == pytest.approx(
        old["EI_y_Nmm2"] * ratio**3, rel=1e-12
    )
    assert current["GA_v_N"] == pytest.approx(old["GA_v_N"] * ratio, rel=1e-12)
    # GA_u is the declared large shear-stiffness surrogate, scaled by width;
    # it is not treated here as a published plywood property.
    assert current["GA_u_N"] == pytest.approx(old["GA_u_N"] * ratio, rel=1e-12)
    assert current["GJ_Nmm2"] == pytest.approx(
        old["GJ_Nmm2"]
        * rectangle_torsion(width, 2 * thickness)
        / rectangle_torsion(old_width, 2 * thickness),
        rel=1e-12,
    )
    assert current["shear_factor"] == old["shear_factor"]


@pytest.mark.parametrize(
    ("width", "thickness"),
    [
        (0.0, 19.05),
        (-1.0, 19.05),
        (139.7, 0.0),
        (139.7, -1.0),
        (19.05, 19.051),
        (math.nan, 19.05),
        (139.7, math.nan),
    ],
)
def test_nonpositive_or_incompatible_rectangle_dimensions_are_rejected(
    width, thickness
):
    with pytest.raises(ValueError, match="positive rectangle dimensions"):
        v6.plywood_properties(width=width, thickness=thickness)


def test_v6_physical_geometry_and_clearance_remain_receipt_bound():
    receipt_path = ROOT / v6.RECEIPT
    receipt = json.loads(receipt_path.read_text())
    geometry_ref = receipt["checked_geometry"]
    clearance_ref = receipt["checked_clearance"]

    assert str(v6.PHYSICAL.relative_to(ROOT)) == geometry_ref["path"]
    assert file_sha256(v6.PHYSICAL) == geometry_ref["sha256"]
    geometry = json.loads(v6.PHYSICAL.read_text())
    assert geometry["revision"] == "eoere-flat-cleats-principal-upper-pairs-v6"
    assert geometry["plywood_leaf_count"] == 4
    assert len(geometry["axes"]) == receipt["counts"]["bolt_stacks"] == 96
    assert len(geometry["screw_axes"]) == receipt["counts"]["Hillman_axes"] == 66
    assert len(geometry["fitting_poses"]) == receipt["counts"]["angles"] == 24

    clearance_path = ROOT / clearance_ref["path"]
    assert file_sha256(clearance_path) == clearance_ref["sha256"]
    clearance = json.loads(clearance_path.read_text())
    assert clearance["geometry"] == geometry_ref
    assert clearance["nominal_geometry_clear"] is True
    assert clearance["collisions"] == []
    assert clearance["missing_candidates"] == []


def test_v6_flat_cleat_proofs_join_to_unchanged_physical_profiles():
    receipt = json.loads((ROOT / v6.RECEIPT).read_text())
    geometry = json.loads(v6.PHYSICAL.read_text())
    proofs = receipt["principal_pair_revision"]["flat_cleat_proofs"]
    expected_names = {
        "eoere_cleat_left",
        "eoere_cleat_left_outer",
        "eoere_cleat_right",
        "eoere_cleat_right_outer",
    }

    assert {proof["member"] for proof in proofs} == expected_names
    for proof in proofs:
        name = proof["member"]
        profile = geometry["profiles"][name]
        finished = profile["finished"]
        assert finished == proof["finished"]
        assert proof["bolt_holes_per_leaf"] == 4
        assert proof["outline_edges_per_face"] == 4
        assert proof["straight_edges_only"] is True
        assert file_sha256(ROOT / finished["path"]) == finished["sha256"]

        bounds = finished["bounds_xyz_mm"]
        assert bounds[1] - bounds[0] == pytest.approx(19.05)
        assert bounds[3] - bounds[2] == pytest.approx(139.7)
        assert bounds[5] - bounds[4] == pytest.approx(361.1860828293809)
        local_outline = sorted(
            {(round(point[0], 8), round(point[2], 8))
             for point in profile["vertices_luv_mm"]}
        )
        expected_outline = sorted(
            {
                (0.0, 0.0),
                (0.0, 139.7),
                (194.69810594, 0.0),
                (361.18608283, 139.7),
            }
        )
        np.testing.assert_allclose(local_outline, expected_outline, rtol=0.0, atol=1e-8)

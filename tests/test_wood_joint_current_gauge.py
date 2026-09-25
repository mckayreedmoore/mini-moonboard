from __future__ import annotations

import math

from fea.wood_joint_current_gauge import build_current_gauge


def test_current_remote_gauge_is_source_bound_and_disjoint_from_patches() -> None:
    fragment, report = build_current_gauge()

    assert fragment.endswith(
        "*BOUNDARY\n"
        "33824,1,3,0.\n"
        "43470,2,3,0.\n"
        "33822,2,2,0.\n"
    )
    assert report["current_mesh"] == {
        "wood_bodies": 3,
        "physical_bolts": 4,
        "physical_metal_bodies": 16,
        "wood_interfaces": 3,
        "body_count": 19,
        "node_count": 116162,
        "element_count": 57643,
    }
    assert report["constraints"]["rigid_body_kinematic_matrix_rank"] == 6
    assert report["constraints"]["constrained_scalar_count"] == 6
    assert report["constraints"]["full_face_clamp"] is False
    assert report["gauge_selection"]["selected_contact_node_intersection"] == []
    assert report["gauge_selection"]["selected_load_node_intersection"] == []
    assert report["gauge_selection"]["contact_nset_node_union_count"] > 0
    assert report["gauge_selection"]["load_patch_node_count"] > 0
    assert math.isclose(
        report["source_local_frame"]["far_T_projected_global_mm"],
        2600.9241337697295,
        abs_tol=1e-6,
    )

    for node in report["gauge_selection"]["selected_nodes"]:
        assert node["owner"] == "base_principal_center_right"
        assert node["mesh_owner"] == "W02_BASE_PRINCIPAL_CENTER_RIGHT"
        assert node["nearest_contact_surface_node_distance_mm"] > 0
        assert node["nearest_load_patch_node_distance_mm"] > 0
        assert math.isclose(node["local_XTN_mm"][1], 2415.403793361191, abs_tol=1e-5)

    # The source-contract corner recipe does resolve, but those mesh nodes lie
    # in the emitted complete-face contact surfaces, so the revised edge triad
    # is an explicit, source-bound change rather than a silent substitution.
    literal = report["gauge_selection"]["literal_contract_corner_nodes"]
    assert {key: row["node_id"] for key, row in literal.items()} == {
        "A": 32537,
        "B": 32554,
        "C": 32538,
    }
    assert all(row["in_contact_surface_node_sets"] for row in literal.values())
    assert report["gauge_selection"]["revised_from_contract_corner_triad"] is True
    assert report["native_solve_run"] is False

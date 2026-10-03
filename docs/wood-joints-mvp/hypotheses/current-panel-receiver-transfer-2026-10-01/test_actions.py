from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "panel_receiver_actions_test", Path(__file__).with_name("actions.py")
)
assert SPEC is not None and SPEC.loader is not None
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)


def inventory_rows() -> dict:
    return {
        "schema": "wood_joint_current_panel_receiver_transfer_inventory/v1",
        "candidate": A.CANDIDATE,
        "geometry_revision_id": A.REVISION,
        "axes": [
            {
                "axis_id": f"axis-{index:02}",
                "panel_member": "panel",
                "receiver_member": "receiver",
                "origin_global_xyz_mm": [float(index), 0.0, 0.0],
                "axis_global_xyz": [1.0, 0.0, 0.0],
            }
            for index in range(66)
        ],
    }


def lateral_fixture() -> tuple[list[dict], dict, dict]:
    basis = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    springs = [
        {
            "source_row_id": "L2",
            "group": "L2",
            "element": 2,
            "name": "axis/panel-wood-interface",
            "dof": 2,
            "nodes": [10, 20],
            "connector_local_dof": 2,
            "intended_law": "bilateral",
            "stiffness_n_per_mm": 10.0,
            "physical_owner": {"force_basis": basis},
        },
        {
            "source_row_id": "L3",
            "group": "L3",
            "element": 3,
            "name": "axis/panel-wood-interface",
            "dof": 3,
            "nodes": [10, 20],
            "connector_local_dof": 3,
            "intended_law": "bilateral",
            "stiffness_n_per_mm": 10.0,
            "physical_owner": {"force_basis": basis},
        },
    ]
    components = {
        "L2": {
            "source_row_id": "L2",
            "source_group": "L2",
            "element": 2,
            "rf_action_reaction_passed": True,
            "rf_kdu_intervals_intersect": True,
            "force_on_first_local_N": -4.0,
            "force_rounding_radius_local_N": 0.1,
            "relative_displacement_mm": -0.4,
            "bilateral_kdu_N": -4.0,
        },
        "L3": {
            "source_row_id": "L3",
            "source_group": "L3",
            "element": 3,
            "rf_action_reaction_passed": True,
            "rf_kdu_intervals_intersect": True,
            "force_on_first_local_N": 2.0,
            "force_rounding_radius_local_N": 0.2,
            "relative_displacement_mm": 0.2,
            "bilateral_kdu_N": 2.0,
        },
    }
    row = {
        "source_row_ids": ["L2", "L3"],
        "force_on_first_xyz_n": [0.0, -4.0, 2.0],
        "force_rounding_radius_xyz_n": [0.0, 0.1, 0.2],
    }
    return springs, components, row


def withdrawal_fixture() -> tuple[dict, dict, dict]:
    binding = {
        "source_row_id": "W1",
        "group": "W1",
        "source_element": 4,
        "name": "axis/parametric-withdrawal",
        "source_projection_nodes": [10, 20],
        "source_projection_dof": 1,
        "stiffness_n_per_mm": 6.0,
        "force_law": "k * max(q_mm, 0)",
        "table_domain_mm": [-10.0, 10.0],
        "force_vs_elongation_table_N_mm": [[0.0, -10.0], [0.0, 0.0], [60.0, 10.0]],
        "physical_owner": {"scalar_normal": [0.0, -1.0, 0.0]},
    }
    component = {
        "source_row_id": "W1",
        "source_group": "W1",
        "element": 4,
        "intended_source_law": "tension_only",
        "native_endpoint_action_reaction_passed": True,
        "table_force_interval_intersects_native_rf": True,
        "inside_table_domain_including_rounding": True,
        "numerical_ground_rf_excluded_from_physical_balance": True,
        "native_endpoint_internal_force_N": 3.0,
        "native_endpoint_internal_radius_N": 0.1,
        "native_table_force_interval_N": [2.9, 3.1],
    }
    row = {
        "source_row_ids": ["W1"],
        "force_on_first_xyz_n": [0.0, -3.0, 0.0],
        "force_rounding_radius_xyz_n": [0.0, 0.1, 0.0],
    }
    return binding, {"W1": component}, row


def test_current_inventory_requires_66_unique_axes_and_preserves_the_join_identity():
    axes = A._axes(inventory_rows())
    assert len(axes) == 66
    assert axes["axis-00"]["panel_member"] == "panel"
    assert axes["axis-65"]["receiver_member"] == "receiver"

    malformed = inventory_rows()
    malformed["axes"][1]["axis_id"] = malformed["axes"][0]["axis_id"]
    with pytest.raises(A.SourceRefusal, match="duplicate axis ID"):
        A._axes(malformed)


def test_each_case_pins_shared_inventory_report_bytes_even_when_axis_identity_is_retained(
    tmp_path: Path,
):
    model_hashes = {}
    for relative in A.SHARED_INVENTORY_SOURCE_REPORTS:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        content = f"saved:{relative}".encode()
        path.write_bytes(content)
        model_hashes[relative] = hashlib.sha256(content).hexdigest()
    model = {"source_geometry_hashes": model_hashes}

    expected_paths = set(A.SHARED_INVENTORY_SOURCE_REPORTS)
    for case in A.CASES:
        pins = A._pin_shared_inventory_source_reports(tmp_path, case, model)
        assert {row["path"] for row in pins} == expected_paths
        assert all(row["size_bytes"] > 0 for row in pins)

    unchanged_inventory = inventory_rows()
    original_axis_ids = [
        row["axis_id"] for row in A._axes(unchanged_inventory).values()
    ]
    mutated_path = tmp_path / A.SHARED_INVENTORY_SOURCE_REPORTS[1]
    mutated_path.write_bytes(b"changed receiver screen bytes")
    assert unchanged_inventory["geometry_revision_id"] == A.REVISION
    assert [
        row["axis_id"] for row in A._axes(unchanged_inventory).values()
    ] == original_axis_ids

    for case in A.CASES:
        with pytest.raises(
            A.SourceRefusal,
            match="pinned source changed: .*receiver-screen-attempt04.json",
        ):
            A._pin_shared_inventory_source_reports(tmp_path, case, model)


def test_geometry_application_offset_retains_sign_and_rejects_transverse_mismatch():
    axis = {
        "axis_id": "axis",
        "origin_global_xyz_mm": [1.0, 2.0, 3.0],
        "axis_global_xyz": [1.0, 0.0, 0.0],
    }
    result = A._datums(axis, "withdrawal", [-8.0, 2.0, 3.0], [-1.0, 0.0, 0.0])
    assert result["signed_axial_offset_mm"] == -9.0
    assert result["native_direction_dot_inventory_axis"] == -1.0
    assert result["transverse_offset_mm"] == 0.0

    with pytest.raises(A.SourceRefusal, match="off the axis"):
        A._datums(axis, "lateral", [-8.0, 2.01, 3.0], [1.0, 0.0, 0.0])


def test_lateral_scalars_keep_signed_local_components_and_rf_radii():
    springs, components, row = lateral_fixture()
    output, force, radius = A._lateral_components("axis", springs, components, row)
    assert [item["source_row_id"] for item in output] == ["L2", "L3"]
    assert [item["signed_force_on_first_local_n"] for item in output] == [-4.0, 2.0]
    assert force == [0.0, -4.0, 2.0]
    assert radius == [0.0, 0.1, 0.2]


@pytest.mark.parametrize("mutation", ["wrong_sign", "failed_law_gate", "wrong_group"])
def test_lateral_mutations_refuse_false_force_or_component_joins(mutation):
    springs, components, row = lateral_fixture()
    if mutation == "wrong_sign":
        row["force_on_first_xyz_n"][1] = 4.0
    elif mutation == "failed_law_gate":
        components["L3"]["rf_kdu_intervals_intersect"] = False
    else:
        components["L2"]["source_group"] = "different"
    with pytest.raises(A.SourceRefusal):
        A._lateral_components("axis", springs, components, row)


def test_withdrawal_is_tension_only_and_projects_to_the_preserved_normal():
    binding, components, row = withdrawal_fixture()
    record, force, radius = A._withdrawal_component("axis", binding, components, row)
    assert record["source_law"] == "tension_only"
    assert record["source_stiffness_n_per_mm"] == 6.0
    assert force == [0.0, -3.0, 0.0]
    assert radius == [0.0, 0.1, 0.0]

    components["W1"]["native_endpoint_internal_force_N"] = -0.1
    with pytest.raises(A.SourceRefusal, match="negative"):
        A._withdrawal_component("axis", binding, components, row)


def test_role_endpoint_order_keeps_bilateral_and_withdrawal_signs_separate():
    springs, lateral, _ = lateral_fixture()
    lateral_row = {"first": "panel", "second": "receiver"}
    assert A._transfer_scalars(lateral_row, "panel", springs, lateral, A.LATERAL) == [
        ((10, 2), -4.0, 0.1),
        ((10, 3), 2.0, 0.2),
    ]
    assert A._transfer_scalars(
        lateral_row, "receiver", springs, lateral, A.LATERAL
    ) == [((20, 2), 4.0, 0.1), ((20, 3), -2.0, 0.2)]

    binding, withdrawal, _ = withdrawal_fixture()
    withdrawal_row = {"first": "receiver", "second": "panel"}
    assert A._transfer_scalars(
        withdrawal_row, "receiver", [binding], withdrawal, A.WITHDRAWAL
    ) == [((10, 1), 3.0, 0.1)]
    assert A._transfer_scalars(
        withdrawal_row, "panel", [binding], withdrawal, A.WITHDRAWAL
    ) == [((20, 1), -3.0, 0.1)]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("audit_pass", "pinned parent all-body audit gate changed"),
        ("audit_body_count", "pinned parent all-body audit gate changed"),
        ("audit_body_printed", "pinned source body audit gate changed for body-3"),
        ("audit_body_interval", "pinned source body audit gate changed for body-3"),
        (
            "unaffected_body_printed",
            "pinned source body audit gate changed for body-49",
        ),
        ("response_body_printed", "pinned source body audit gate changed for body-3"),
        ("response_body_interval", "pinned source body audit gate changed for body-3"),
        ("audit_global_printed", "pinned source global audit gate changed"),
        ("audit_global_interval", "pinned source global audit gate changed"),
        ("response_global_printed", "pinned source global audit gate changed"),
        ("response_global_interval", "pinned source global audit gate changed"),
        ("numerical_ground", "numerical spring ground"),
    ],
)
def test_source_audit_snapshot_refuses_failed_original_gate_or_numerical_ground(
    mutation, message
):
    names = [f"body-{index}" for index in range(50)]

    def balance_row(seed):
        force_scale = seed * 1e-6
        moment_scale = seed * 1e-4
        return {
            "reference_xyz_mm": [seed + 0.25, -seed - 0.5, seed + 0.75],
            "force_residual_xyz_n": [
                force_scale,
                -2.0 * force_scale,
                3.0 * force_scale,
            ],
            "moment_residual_xyz_nmm": [
                moment_scale,
                -2.0 * moment_scale,
                3.0 * moment_scale,
            ],
            "force_rounding_radius_xyz_n": [
                2.0 * force_scale,
                3.0 * force_scale,
                4.0 * force_scale,
            ],
            "moment_rounding_radius_xyz_nmm": [
                2.0 * moment_scale,
                3.0 * moment_scale,
                4.0 * moment_scale,
            ],
            "force_interval_distance_from_zero_n": [0.0, 0.0, 0.0],
            "moment_interval_distance_from_zero_nmm": [0.0, 0.0, 0.0],
            "printed_resultants_passed": True,
            "interval_resultants_passed": True,
            "criterion": "synthetic raw and interval balance snapshot",
        }

    model = {"physical_body_nodes": {name: [] for name in names}}
    increment = {
        "load_factor": 1.0,
        "time": 1.0,
        "physical_balance": {
            "body_equilibrium": {
                name: balance_row(100 + index) for index, name in enumerate(names)
            },
            "global_equilibrium": balance_row(888),
        },
    }
    audit_global = balance_row(777)
    audit = {
        "body_count": 50,
        "load_factor": 1.0,
        "time": 1.0,
        "passed": True,
        "numerical_grounds_counted": 0,
        "body_equilibrium": {
            name: balance_row(index + 1) for index, name in enumerate(names)
        },
        "global_equilibrium": audit_global,
    }
    result = A._audit_snapshot(model, increment, audit, {"body-3"})
    assert result["source_all_body_and_global_gates_passed"] is True
    assert result["affected_body_equilibrium"] == {"body-3": balance_row(4)}
    assert result["affected_body_equilibrium"]["body-3"]["force_residual_xyz_n"] == [
        4e-6,
        -8e-6,
        12e-6,
    ]
    assert result["affected_body_equilibrium"]["body-3"][
        "moment_rounding_radius_xyz_nmm"
    ] == pytest.approx([0.0008, 0.0012, 0.0016])
    assert result["global_equilibrium"] == audit_global
    assert result["global_equilibrium"]["moment_residual_xyz_nmm"] == pytest.approx(
        [
            0.0777,
            -0.1554,
            0.2331,
        ]
    )
    # Distinctive source radii must survive the audit snapshot as well.
    assert result["global_equilibrium"]["force_rounding_radius_xyz_n"] == pytest.approx(
        [0.001554, 0.002331, 0.003108]
    )

    if mutation == "audit_pass":
        audit["passed"] = False
    elif mutation == "audit_body_count":
        audit["body_count"] = 49
    elif mutation == "audit_body_printed":
        audit["body_equilibrium"]["body-3"]["printed_resultants_passed"] = False
    elif mutation == "audit_body_interval":
        audit["body_equilibrium"]["body-3"]["interval_resultants_passed"] = False
    elif mutation == "unaffected_body_printed":
        audit["body_equilibrium"]["body-49"]["printed_resultants_passed"] = False
    elif mutation == "response_body_printed":
        increment["physical_balance"]["body_equilibrium"]["body-3"][
            "printed_resultants_passed"
        ] = False
    elif mutation == "response_body_interval":
        increment["physical_balance"]["body_equilibrium"]["body-3"][
            "interval_resultants_passed"
        ] = False
    elif mutation == "audit_global_printed":
        audit["global_equilibrium"]["printed_resultants_passed"] = False
    elif mutation == "audit_global_interval":
        audit["global_equilibrium"]["interval_resultants_passed"] = False
    elif mutation == "response_global_printed":
        increment["physical_balance"]["global_equilibrium"][
            "printed_resultants_passed"
        ] = False
    elif mutation == "response_global_interval":
        increment["physical_balance"]["global_equilibrium"][
            "interval_resultants_passed"
        ] = False
    elif mutation == "numerical_ground":
        audit["numerical_grounds_counted"] = 1
    else:
        raise AssertionError(f"unknown audit mutation: {mutation}")

    with pytest.raises(A.SourceRefusal, match=message):
        A._audit_snapshot(model, increment, audit, {"body-3"})


def test_screw_record_combines_signed_lateral_and_withdrawal_endpoint_wrenches():
    point = [5.0, 0.0, 0.0]
    axis = {
        "axis_id": "axis-test",
        "panel_member": "panel",
        "receiver_member": "receiver",
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "axis_global_xyz": [1.0, 0.0, 0.0],
    }
    basis = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    springs, lateral_response, lateral_row = lateral_fixture()
    for spring in springs:
        spring["nodes"] = [10, 20]
        spring["physical_owner"] = {
            "first": "panel",
            "second": "receiver",
            "point": point,
            "force_basis": basis,
        }
    lateral_row.update(
        {
            "name": "axis/panel-wood-interface",
            "role": A.LATERAL,
            "first": "panel",
            "second": "receiver",
            "point": point,
            "force_on_second_xyz_n": [0.0, 4.0, -2.0],
            "force_precision_basis": "Native RF token half-last-place interval propagation",
            "source_inventory_rows": [
                {
                    "source_row_id": spring["source_row_id"],
                    "source_connection_name": spring["name"],
                    "intended_law": "bilateral",
                }
                for spring in springs
            ],
        }
    )

    binding, withdrawal_response, withdrawal_row = withdrawal_fixture()
    binding["source_projection_nodes"] = [20, 10]
    binding["physical_owner"] = {
        "first": "receiver",
        "second": "panel",
        "point": point,
        "scalar_normal": [1.0, 0.0, 0.0],
    }
    withdrawal_row.update(
        {
            "name": binding["name"],
            "role": A.WITHDRAWAL,
            "first": "receiver",
            "second": "panel",
            "point": point,
            "force_on_first_xyz_n": [3.0, 0.0, 0.0],
            "force_on_second_xyz_n": [-3.0, 0.0, 0.0],
            "force_rounding_radius_xyz_n": [0.1, 0.0, 0.0],
            "force_precision_basis": "Native RF token half-last-place interval propagation",
            "source_inventory_rows": [
                {
                    "source_row_id": binding["source_row_id"],
                    "source_connection_name": binding["name"],
                    "intended_law": "tension_only",
                }
            ],
        }
    )
    model = {
        "physical_body_nodes": {"panel": [10, 11], "receiver": [20, 21]},
        "nodes": {
            "10": point,
            "11": [5.0, 2.0, 0.0],
            "20": point,
            "21": [5.0, -2.0, 0.0],
        },
        "equations": [],
        "connection_ownership": {
            lateral_row["name"]: {
                "first": "panel",
                "second": "receiver",
                "role": A.LATERAL,
                "point": point,
            },
            withdrawal_row["name"]: {
                "first": "receiver",
                "second": "panel",
                "role": A.WITHDRAWAL,
                "point": point,
            },
        },
    }
    expansion = A.NODAL.MPCExpansion(
        model["equations"], A.NODAL.owner_map(model), model.get("fixed_nodes", ())
    )

    record, nodal, physical_projection = A._screw_record(
        axis,
        springs,
        binding,
        lateral_row,
        withdrawal_row,
        lateral_response,
        withdrawal_response,
        model,
        expansion,
        {"panel": [5.0, 1.0, 0.0], "receiver": [5.0, -1.0, 0.0]},
        load_factor=1.0,
        include_stencils=False,
    )

    assert [
        component["signed_force_on_first_local_n"]
        for component in record["lateral_scalar_components"]
    ] == [-4.0, 2.0]
    assert record["withdrawal_scalar_component"]["source_law"] == "tension_only"
    assert record["withdrawal_scalar_component"]["native_internal_force_n"] == 3.0
    assert [row["source_role"] for row in record["source_connections"]] == [
        A.LATERAL,
        A.WITHDRAWAL,
    ]
    assert all(
        row[endpoint]["mpc_transfer_status"]
        == "REPRODUCED_WITH_EXISTING_HELPER_COMPARISON"
        for row in record["source_connections"]
        for endpoint in ("panel_endpoint", "receiver_endpoint")
    )

    panel = record["same_state_panel_screw_wrench_at_panel_centroid"]
    assert panel["force_n"] == [-3.0, -4.0, 2.0]
    assert panel["moment_nmm"] == [-2.0, 0.0, -3.0]
    assert panel["force_rounding_radius_n"] == [0.1, 0.1, 0.2]
    assert panel["moment_rounding_radius_nmm"] == [0.2, 0.0, 0.1]

    receiver = record["same_state_receiver_screw_wrench_at_receiver_centroid"]
    assert receiver["force_n"] == [3.0, 4.0, -2.0]
    assert receiver["moment_nmm"] == [-2.0, 0.0, -3.0]
    assert receiver["force_rounding_radius_n"] == [0.1, 0.1, 0.2]
    assert receiver["moment_rounding_radius_nmm"] == [0.2, 0.0, 0.1]
    assert nodal["panel"][A.LATERAL][0]["force_n"] == [0.0, -4.0, 2.0]
    assert nodal["panel"][A.WITHDRAWAL][0]["force_n"] == [-3.0, 0.0, 0.0]
    assert nodal["receiver"][A.LATERAL][0]["force_n"] == [0.0, 4.0, -2.0]
    assert nodal["receiver"][A.WITHDRAWAL][0]["force_n"] == [3.0, 0.0, 0.0]
    assert physical_projection["panel"][A.LATERAL] == nodal["panel"][A.LATERAL]
    assert (
        physical_projection["receiver"][A.WITHDRAWAL] == nodal["receiver"][A.WITHDRAWAL]
    )


def test_physical_body_endpoint_projection_uses_signed_nonunit_weights_and_keeps_support_separate():
    model = {
        "physical_body_nodes": {"receiver": [1, 3]},
        "nodes": {
            "100": [10.0, 20.0, 30.0],
            "1": [11.0, 22.0, 30.0],
            "2": [0.0, 0.0, 0.0],
            "3": [9.0, 18.0, 30.0],
            "4": [0.0, 0.0, 0.0],
        },
        "equations": [
            [[100, 1, 1.0], [1, 1, -1.25], [3, 1, 0.25]],
            [[1, 1, 1.0], [2, 1, -1.0]],
            [[3, 1, 1.0], [4, 1, -1.0]],
        ],
        "fixed_nodes": [2, 4],
    }
    expansion = A.NODAL.MPCExpansion(
        model["equations"], A.NODAL.owner_map(model), model["fixed_nodes"]
    )
    row = {
        "first": "receiver",
        "second": "panel",
        "point": [10.0, 20.0, 30.0],
        "force_on_first_xyz_n": [3.0, 0.0, 0.0],
        "force_on_second_xyz_n": [-3.0, 0.0, 0.0],
        "force_rounding_radius_xyz_n": [0.2, 0.0, 0.0],
    }
    scalars = [((100, 1), 3.0, 0.2)]
    source_rows = [
        {"source_row_id": "SPR-test", "connector_local_dof": 1, "nodes": [100, 200]}
    ]

    result = A._nodal_action_observation(
        model, expansion, row, "receiver", scalars, source_rows, True
    )
    (
        free_cloud,
        point,
        free_wrench,
        fixed_cloud,
        fixed_wrench,
        complete,
        owner_cloud,
        owner_wrench,
        nonphysical,
        stencils,
    ) = result

    assert free_cloud == []
    assert free_wrench["force_n"] == [0.0, 0.0, 0.0]
    assert fixed_cloud == [
        {
            "node": 2,
            "point_mm": [0.0, 0.0, 0.0],
            "force_n": [3.75, 0.0, 0.0],
            "radius_n": [0.25, 0.0, 0.0],
        },
        {
            "node": 4,
            "point_mm": [0.0, 0.0, 0.0],
            "force_n": [-0.75, 0.0, 0.0],
            "radius_n": [0.05, 0.0, 0.0],
        },
    ]
    assert fixed_wrench["force_n"] == [3.0, 0.0, 0.0]
    assert fixed_wrench["moment_nmm"] == [0.0, -90.0, 60.0]
    assert fixed_wrench["force_radius_n"] == [0.3, 0.0, 0.0]
    assert fixed_wrench["moment_radius_nmm"] == [0.0, 9.0, 6.0]
    assert complete["force_n"] == point["force_n"]
    assert {entry["node"] for entry in owner_cloud} == {1, 3}
    assert owner_cloud == [
        {
            "node": 1,
            "point_mm": [11.0, 22.0, 30.0],
            "force_n": [3.75, 0.0, 0.0],
            "radius_n": [0.25, 0.0, 0.0],
        },
        {
            "node": 3,
            "point_mm": [9.0, 18.0, 30.0],
            "force_n": [-0.75, 0.0, 0.0],
            "radius_n": [0.05, 0.0, 0.0],
        },
    ]
    assert owner_wrench["force_n"] == point["force_n"]
    assert owner_wrench["moment_nmm"] == [0.0, 0.0, -9.0]
    assert owner_wrench["force_radius_n"] == [0.3, 0.0, 0.0]
    assert owner_wrench["moment_radius_nmm"] == [0.0, 0.0, 0.6]
    common_datum_wrench = A.NODAL.wrench(owner_cloud, [0.0, 0.0, 0.0])
    assert common_datum_wrench["force_n"] == [3.0, 0.0, 0.0]
    assert common_datum_wrench["moment_nmm"] == [0.0, 90.0, -69.0]
    assert common_datum_wrench["force_radius_n"] == [0.3, 0.0, 0.0]
    assert common_datum_wrench["moment_radius_nmm"] == [0.0, 9.0, 6.4]
    assert nonphysical == []
    assert stencils[0]["recursive_terminal_dof_weights"] == [
        {"node": 2, "dof": 1, "weight": 1.25, "fixed": True, "physical_owner": None},
        {"node": 4, "dof": 1, "weight": -0.25, "fixed": True, "physical_owner": None},
    ]
    assert stencils[0]["physical_owner_terminal_dof_weights"] == [
        {"node": 1, "dof": 1, "weight": 1.25},
        {"node": 3, "dof": 1, "weight": -0.25},
    ]
    assert stencils[0]["physical_owner_pivot_equations_traversed"] == [
        {
            "node": 1,
            "dof": 1,
            "physical_owner": "receiver",
            "terms": [[1, 1, 1.0], [2, 1, -1.0]],
        },
        {
            "node": 3,
            "dof": 1,
            "physical_owner": "receiver",
            "terms": [[3, 1, 1.0], [4, 1, -1.0]],
        },
    ]

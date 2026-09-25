"""Synthetic checks for explicit rigid-body constraint-rank diagnostics."""

import numpy as np
import pytest

from fea.wood_joint_patch_rigid_modes import (
    ActiveContactNormal,
    MpcKinematicConstraint,
    MpcPointTerm,
    RigidBodyDatum,
    ThreadConstraint,
    audit_rigid_modes,
)


def _body(body_id: str, origin=(0.0, 0.0, 0.0)) -> RigidBodyDatum:
    return RigidBodyDatum(body_id, origin)


def _contact(
    constraint_id="contact-1",
    *,
    body_a="a",
    body_b="b",
    point=(0.0, 0.0, 0.0),
    point_a=None,
    point_b=None,
    normal=(0.0, 0.0, 1.0),
):
    return ActiveContactNormal(
        constraint_id,
        pair_id="pair-1",
        interface_id="interface-1",
        body_a=body_a,
        body_b=body_b,
        point_a_xyz_mm=point if point_a is None else point_a,
        point_b_xyz_mm=point if point_b is None else point_b,
        normal_xyz_global=normal,
    )


def test_unrestrained_body_exposes_six_modes_and_gauge_is_separate():
    report = audit_rigid_modes(
        [_body("a")],
        [],
        [],
        assumed_active_set_id="explicitly-no-active-contacts",
        characteristic_length_mm=100.0,
        point_alignment_tolerance_mm=0.0,
        global_gauge_body_id="a",
    )

    assert report["assumed_active_set_id"] == "explicitly-no-active-contacts"
    assert report["active_contact_normal_assumptions"] == []
    assert report["physical_only"]["rank"] == 0
    assert report["physical_only"]["nullity"] == 6
    assert report["physical_only"]["nullspace_translation_participation_fraction"][
        "a"
    ] == pytest.approx(0.5)
    assert report["physical_only"]["nullspace_scaled_rotation_participation_fraction"][
        "a"
    ] == pytest.approx(0.5)
    assert report["with_global_gauge"]["rank"] == 6
    assert report["with_global_gauge"]["nullity"] == 0
    assert report["with_global_gauge"]["row_kinds"] == [
        "global_coordinate_gauge"
    ] * 6


def test_one_active_normal_leaves_global_modes_and_five_relative_modes():
    report = audit_rigid_modes(
        [_body("a"), _body("b")],
        [_contact()],
        [],
        assumed_active_set_id="one-normal-row-assumed-active",
        characteristic_length_mm=100.0,
        point_alignment_tolerance_mm=0.0,
        global_gauge_body_id="a",
    )

    assert report["physical_only"]["rank"] == 1
    assert report["physical_only"]["nullity"] == 11
    assert report["with_global_gauge"]["rank"] == 7
    assert report["with_global_gauge"]["nullity"] == 5
    participation = report["with_global_gauge"][
        "nullspace_body_participation_fraction"
    ]
    assert participation["a"] == pytest.approx(0.0)
    assert participation["b"] == pytest.approx(1.0)


def test_complete_wood_and_hardware_inventory_keeps_six_dofs_per_body():
    body_ids = [f"wood-{index}" for index in range(5)] + [
        f"metal-{index}" for index in range(32)
    ]
    report = audit_rigid_modes(
        [_body(body_id) for body_id in body_ids],
        [],
        [],
        assumed_active_set_id="all-37-body-inventory-no-physical-rows",
        characteristic_length_mm=100.0,
        point_alignment_tolerance_mm=0.0,
    )

    assert report["body_ids_in_coordinate_order"] == body_ids
    assert report["physical_only"]["matrix_shape"] == [0, 222]
    assert report["physical_only"]["nullity"] == 222
    assert len(report["physical_only"]["dof_order_scaled_coordinates"]) == 37
    assert report["physical_only"]["dof_order_scaled_coordinates"][5]["body_id"] == "metal-0"
    assert report["physical_only"]["dof_order_scaled_coordinates"][5]["components"] == [
        "ux_mm",
        "uy_mm",
        "uz_mm",
        "L_omega_x_mm",
        "L_omega_y_mm",
        "L_omega_z_mm",
    ]
    assert sum(
        report["physical_only"]["nullspace_translation_participation_fraction"].values()
    ) == pytest.approx(0.5)
    assert sum(
        report["physical_only"]["nullspace_scaled_rotation_participation_fraction"].values()
    ) == pytest.approx(0.5)


def test_contact_row_has_correct_scaled_rotation_levers():
    report = audit_rigid_modes(
        [_body("a"), _body("b", (1.0, 0.0, 0.0))],
        [_contact(point=(0.0, 2.0, 0.0))],
        [],
        assumed_active_set_id="offset-normal-contact",
        characteristic_length_mm=2.0,
        point_alignment_tolerance_mm=0.0,
    )

    row = np.asarray(report["physical_only"]["dimensionless_constraint_matrix"])[0]
    assert row == pytest.approx(
        (0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, -0.5, 0.0)
    )


def test_thread_row_uses_declared_direction_and_separate_engagement_points():
    thread = ThreadConstraint(
        constraint_id="bolt-a-axial",
        thread_id="bolt-a",
        body_a="a",
        body_b="b",
        point_a_xyz_mm=(0.0, 2.0, 0.0),
        point_b_xyz_mm=(0.0, 2.0, 1.0),
        direction_xyz_global=(0.0, 0.0, 1.0),
        declared_mode="engaged-axial-translation",
    )
    report = audit_rigid_modes(
        [_body("a"), _body("b", (1.0, 0.0, 1.0))],
        [],
        [thread],
        assumed_active_set_id="no-normal-contact-thread-only",
        characteristic_length_mm=2.0,
        point_alignment_tolerance_mm=0.0,
    )

    row = np.asarray(report["physical_only"]["dimensionless_constraint_matrix"])[0]
    assert row == pytest.approx(
        (0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, -1.0, -1.0, -0.5, 0.0)
    )
    assert report["physical_only"]["row_kinds"] == [
        "declared_thread_translation:engaged-axial-translation"
    ]


def test_mpc_row_retains_nut_master_element_shape_weights_and_is_objective():
    mpc = MpcKinematicConstraint(
        constraint_id="bolt-nut-axial-mpc",
        global_direction_xyz=(0.0, 0.0, 1.0),
        declared_mode="unapproved-perfect-axial-engagement-proxy",
        source_pair_id="bolt-1::root-to-nut-radial-contact",
        source_provenance={
            "projection_distance_mm": 0.0,
            "conditioning_indicator": "synthetic-only",
        },
        terms=(
            MpcPointTerm(
                "bolt",
                global_node_xyz_mm=(0.0, 0.0, 0.0),
                coefficient=1.0,
                source_node_id=10,
            ),
            MpcPointTerm(
                "nut",
                global_node_xyz_mm=(1.0, 0.0, -10.0),
                coefficient=-0.25,
                source_node_id=21,
                source_element_id=7,
                interpolation_weight=0.25,
            ),
            MpcPointTerm(
                "nut",
                global_node_xyz_mm=(-1.0, 0.0, -10.0),
                coefficient=-0.25,
                source_node_id=22,
                source_element_id=7,
                interpolation_weight=0.25,
            ),
            MpcPointTerm(
                "nut",
                global_node_xyz_mm=(0.0, 1.0, -10.0),
                coefficient=-0.25,
                source_node_id=23,
                source_element_id=7,
                interpolation_weight=0.25,
            ),
            MpcPointTerm(
                "nut",
                global_node_xyz_mm=(0.0, -1.0, -10.0),
                coefficient=-0.25,
                source_node_id=24,
                source_element_id=7,
                interpolation_weight=0.25,
            ),
            MpcPointTerm(
                "nut",
                global_node_xyz_mm=(0.0, 0.0, -10.0),
                coefficient=0.0,
                source_node_id=25,
                source_element_id=7,
                interpolation_weight=0.0,
            ),
        ),
    )
    report = audit_rigid_modes(
        [_body("bolt"), _body("nut", (0.0, 0.0, -10.0))],
        [],
        [],
        mpc_constraints=[mpc],
        assumed_active_set_id="explicit-mpc-proxy-rows",
        characteristic_length_mm=10.0,
        point_alignment_tolerance_mm=1e-10,
    )

    row = np.asarray(report["physical_only"]["dimensionless_constraint_matrix"])[0]
    assert row == pytest.approx(
        (0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.0, 0.0)
    )
    assert report["physical_only"]["row_kinds"] == [
        "declared_mpc_kinematic:unapproved-perfect-axial-engagement-proxy"
    ]
    assumptions = report["mpc_kinematic_assumptions"][0]
    assert assumptions["source_pair_id"] == "bolt-1::root-to-nut-radial-contact"
    assert assumptions["source_provenance"]["projection_distance_mm"] == 0.0
    assert assumptions["terms"][1]["source_element_id"] == 7
    assert assumptions["terms"][1]["interpolation_weight"] == 0.25
    assert assumptions["terms"][5]["interpolation_weight"] == 0.0
    assert max(
        report["global_rigid_motion_check_before_gauge"][
            "maximum_absolute_residual_mm_by_mode"
        ]
    ) < 1e-12


def test_mpc_rows_reject_unbalanced_or_nonobjective_point_terms():
    unbalanced = MpcKinematicConstraint(
        constraint_id="unbalanced-mpc",
        global_direction_xyz=(0.0, 0.0, 1.0),
        declared_mode="unbalanced",
        terms=(
            MpcPointTerm("a", (0.0, 0.0, 0.0), 1.0),
            MpcPointTerm("b", (0.0, 0.0, -1.0), -0.9),
        ),
    )
    with pytest.raises(ValueError, match="not translation-objective"):
        audit_rigid_modes(
            [_body("a"), _body("b")],
            [],
            [],
            mpc_constraints=[unbalanced],
            assumed_active_set_id="unbalanced-row",
            characteristic_length_mm=10.0,
            point_alignment_tolerance_mm=1e-8,
        )

    nonobjective = MpcKinematicConstraint(
        constraint_id="nonobjective-mpc",
        global_direction_xyz=(0.0, 0.0, 1.0),
        declared_mode="offset-points",
        terms=(
            MpcPointTerm("a", (0.0, 0.0, 0.0), 1.0),
            MpcPointTerm("b", (1.0, 0.0, -1.0), -1.0),
        ),
    )
    with pytest.raises(ValueError, match="nonobjective under global rotation"):
        audit_rigid_modes(
            [_body("a"), _body("b")],
            [],
            [],
            mpc_constraints=[nonobjective],
            assumed_active_set_id="nonobjective-row",
            characteristic_length_mm=10.0,
            point_alignment_tolerance_mm=1e-8,
        )


def test_mpc_mapping_uses_contact_adapter_global_keys_and_preserves_source_record():
    report = audit_rigid_modes(
        [_body("bolt"), _body("nut", (0.0, 0.0, -2.0))],
        [],
        [],
        mpc_constraints=[
            {
                "constraint_id": "adapter-row-1",
                "source_pair_id": "bolt-root-to-nut",
                "global_direction_xyz": (0.0, 0.0, 1.0),
                "declared_mode": "explicit-upper-bound-proxy",
                "source_provenance": {"master_element_id": 9, "projection_gap_mm": 0.0},
                "terms": [
                    {
                        "body_id": "bolt",
                        "global_node_xyz_mm": (0.0, 0.0, 0.0),
                        "coefficient": 1.0,
                        "source_node_id": 101,
                    },
                    {
                        "body_id": "nut",
                        "global_node_xyz_mm": (0.0, 0.0, -2.0),
                        "coefficient": -1.0,
                        "source_node_id": 202,
                        "source_element_id": 9,
                        "interpolation_weight": 1.0,
                    },
                ],
            }
        ],
        assumed_active_set_id="adapter-shape-weight-mpc-example",
        characteristic_length_mm=10.0,
        point_alignment_tolerance_mm=0.0,
    )

    assumptions = report["mpc_kinematic_assumptions"][0]
    assert assumptions["source_provenance"]["master_element_id"] == 9
    assert assumptions["terms"][1]["global_node_xyz_mm"] == (0.0, 0.0, -2.0)
    assert assumptions["terms"][1]["source_node_id"] == 202


def test_dependent_rows_are_reported_but_do_not_inflate_rank():
    report = audit_rigid_modes(
        [_body("a"), _body("b")],
        [_contact("contact-1"), _contact("contact-2")],
        [],
        assumed_active_set_id="two-coincident-normal-assumptions",
        characteristic_length_mm=10.0,
        point_alignment_tolerance_mm=0.0,
    )

    assert report["physical_only"]["matrix_shape"] == [2, 12]
    assert report["physical_only"]["row_ids"] == ["contact-1", "contact-2"]
    assert report["physical_only"]["rank"] == 1
    assert report["physical_only"]["nullity"] == 11


def test_mapping_inputs_are_preserved_as_explicit_active_set_rows():
    contact = {
        "constraint_id": "contact-row",
        "pair_id": "source-pair",
        "interface_id": "interface-1",
        "body_a": "a",
        "body_b": "b",
        "point_a_xyz_mm": [0.0, 0.0, 0.0],
        "point_b_xyz_mm": [0.0, 0.0, 0.0],
        "normal_xyz_global": [0.0, 0.0, 1.0],
    }
    report = audit_rigid_modes(
        [{"body_id": "a", "origin_xyz_mm": [0, 0, 0]}, _body("b")],
        [contact],
        [],
        assumed_active_set_id="caller-selected-row-set",
        characteristic_length_mm=1.0,
        point_alignment_tolerance_mm=0.0,
    )

    assumption = report["active_contact_normal_assumptions"][0]
    assert assumption["constraint_id"] == contact["constraint_id"]
    assert assumption["point_a_xyz_mm"] == (0.0, 0.0, 0.0)
    assert assumption["point_b_xyz_mm"] == (0.0, 0.0, 0.0)
    assert assumption["normal_xyz_global"] == (0.0, 0.0, 1.0)


@pytest.mark.parametrize(
    "contacts,threads,gauge,match",
    [
        ([_contact("same"), _contact("same")], [], None, "constraint ids"),
        ([_contact(body_b="missing")], [], None, "unknown body"),
        (
            [
                {
                    "constraint_id": "bad-normal",
                    "pair_id": "pair-1",
                    "interface_id": "interface-1",
                    "body_a": "a",
                    "body_b": "b",
                    "point_a_xyz_mm": (0.0, 0.0, 0.0),
                    "point_b_xyz_mm": (0.0, 0.0, 0.0),
                    "normal_xyz_global": (0.0, 0.0, 2.0),
                }
            ],
            [],
            None,
            "unit vector",
        ),
        ([], [], "missing", "gauge body"),
        ([], [], None, "at least one rigid body"),
    ],
)
def test_invalid_constraint_or_gauge_inputs_fail_closed(contacts, threads, gauge, match):
    bodies = [] if match == "at least one rigid body" else [_body("a"), _body("b")]
    with pytest.raises(ValueError, match=match):
        audit_rigid_modes(
            bodies,
            contacts,
            threads,
            assumed_active_set_id="explicit-test-set",
            characteristic_length_mm=100.0,
            point_alignment_tolerance_mm=0.0,
            global_gauge_body_id=gauge,
        )


def test_normal_and_thread_rows_annihilate_six_global_rigid_motions_before_gauge():
    thread = ThreadConstraint(
        constraint_id="thread-axial",
        thread_id="bolt-a",
        body_a="a",
        body_b="b",
        point_a_xyz_mm=(0.0, 2.0, 0.0),
        point_b_xyz_mm=(0.0, 2.0, 1.0),
        direction_xyz_global=(0.0, 0.0, 1.0),
        declared_mode="engaged-axial-translation",
    )
    report = audit_rigid_modes(
        [_body("a"), _body("b", (1.0, 0.0, 1.0))],
        [
            _contact(
                point_a=(0.0, 2.0, 0.0),
                point_b=(0.0, 2.0, 1.0),
            )
        ],
        [thread],
        assumed_active_set_id="explicit-objective-rows",
        characteristic_length_mm=100.0,
        point_alignment_tolerance_mm=0.0,
    )

    check = report["global_rigid_motion_check_before_gauge"]
    assert check["mode_ids"] == [
        "global_translation_x",
        "global_translation_y",
        "global_translation_z",
        "global_rotation_x",
        "global_rotation_y",
        "global_rotation_z",
    ]
    assert max(check["maximum_absolute_residual_mm_by_mode"]) < 1e-12


@pytest.mark.parametrize(
    "contact,thread,message",
    [
        (
            _contact(point_a=(0.0, 0.0, 0.0), point_b=(1.0, 0.0, 0.0)),
            None,
            "tangential point mismatch",
        ),
        (
            None,
            ThreadConstraint(
                constraint_id="off-axis-thread",
                thread_id="bolt-a",
                body_a="a",
                body_b="b",
                point_a_xyz_mm=(0.0, 0.0, 0.0),
                point_b_xyz_mm=(1.0, 0.0, 0.0),
                direction_xyz_global=(0.0, 0.0, 1.0),
                declared_mode="engaged-axial-translation",
            ),
            "off-axis endpoint mismatch",
        ),
    ],
)
def test_nonobjective_point_pairs_are_rejected(contact, thread, message):
    with pytest.raises(ValueError, match=message):
        audit_rigid_modes(
            [_body("a"), _body("b")],
            [] if contact is None else [contact],
            [] if thread is None else [thread],
            assumed_active_set_id="misaligned-points",
            characteristic_length_mm=10.0,
            point_alignment_tolerance_mm=1e-8,
        )

"""Focused synthetic tests for the streamed symmetric-matrix witness audit."""

from __future__ import annotations

import pytest

from fea import wood_joint_current_matrix_witness as witness


def _three_dof_laplacian():
    # K = [[1, -1, 0], [-1, 2, -1], [0, -1, 1]] in lower-triangle order.
    return [
        (1, 1, 1.0),
        (2, 1, -1.0),
        (2, 2, 2.0),
        (3, 2, -1.0),
        (3, 3, 1.0),
    ]


def test_symmetric_triangle_stream_finds_candidate_null_and_positive_strain_witness():
    result = witness.evaluate_symmetric_coordinate_matrix(
        _three_dof_laplacian(),
        3,
        {"translation": [1.0, 1.0, 1.0], "strain": [1.0, -1.0, 0.0]},
    )

    assert result["matrix_dimension"] == 3
    assert result["coordinate_record_count"] == 5
    assert result["diagonal_record_count"] == 3
    assert result["off_diagonal_record_count"] == 2
    assert result["implicit_symmetric_triangle"] == "lower"
    translation = result["probes"]["translation"]
    assert translation["kv_inf_norm"] == pytest.approx(0.0)
    assert translation["scaled_residual_inf"] == pytest.approx(0.0)
    assert translation["scaled_residual_definition"] == "||Kv||_inf / || |K| |v| ||_inf"
    assert translation["quadratic_form_vtkv"] == pytest.approx(0.0)
    strain = result["probes"]["strain"]
    assert strain["quadratic_form_vtkv"] == pytest.approx(5.0)
    assert strain["scaled_residual_inf"] > 0.0


def test_symmetric_triangle_stream_accepts_sorted_upper_triangle():
    result = witness.evaluate_symmetric_coordinate_matrix(
        [(1, 1, 1.0), (1, 2, -1.0), (2, 2, 1.0)],
        2,
        {"rigid": [1.0, 1.0]},
    )

    assert result["implicit_symmetric_triangle"] == "upper"
    assert result["probes"]["rigid"]["scaled_residual_inf"] == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("entries", "message"),
    [
        ([(1, 1, 1.0), (2, 1, -1.0), (1, 2, -1.0), (2, 2, 1.0)], "mix upper and lower"),
        (
            [(1, 1, 1.0), (2, 1, -1.0), (2, 1, -1.0), (2, 2, 1.0)],
            "duplicate coordinate",
        ),
        ([(2, 1, -1.0), (1, 1, 1.0), (2, 2, 1.0)], "not sorted"),
        ([(1, 1, float("nan")), (2, 1, -1.0), (2, 2, 1.0)], "not finite"),
        ([(1, 1, 1.0), (2, 1, -1.0)], "missing 1 diagonal"),
    ],
)
def test_matrix_stream_rejects_malformed_symmetric_coordinate_records(entries, message):
    with pytest.raises(ValueError, match=message):
        witness.evaluate_symmetric_coordinate_matrix(entries, 2, {"probe": [1.0, 0.0]})


def test_dof_reader_preserves_equation_order_and_rejects_duplicate_labels(tmp_path):
    path = tmp_path / "reference.dof"
    path.write_text("17.1\n17.2\n25.3\n")
    assert witness._read_dof(path) == [(17, 1), (17, 2), (25, 3)]

    path.write_text("17.1\n17.1\n")
    with pytest.raises(ValueError, match="duplicate node.direction"):
        witness._read_dof(path)


def test_target_vector_uses_exact_mesh_owners_and_zeros_other_nodes_and_controls():
    labels = [
        (1, 1),
        (1, 2),
        (1, 3),
        (2, 1),
        (2, 2),
        (2, 3),
        (3, 1),
        (3, 2),
        (3, 3),
        (99, 1),
        (99, 2),
        (99, 3),
    ]
    candidate, strain, scope = witness._build_probe_vectors(
        labels,
        {1: (0.0, 0.0, 0.0), 2: (2.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0)},
        {
            1: witness.TARGET_BODY_ID,
            2: witness.TARGET_BODY_ID,
            3: "W01_BASE_RAIL_BOTTOM_RIGHT",
        },
        [99],
    )

    assert candidate[:6] == pytest.approx(
        [
            0.0,
            witness.TARGET_DIRECTION[1],
            witness.TARGET_DIRECTION[2],
            0.0,
            witness.TARGET_DIRECTION[1],
            witness.TARGET_DIRECTION[2],
        ]
    )
    assert candidate[6:] == pytest.approx([0.0] * 6)
    assert strain[0] == pytest.approx(-1 / 2**0.5)
    assert strain[3] == pytest.approx(1 / 2**0.5)
    assert strain[[1, 2, 4, 5, 6, 7, 8, 9, 10, 11]] == pytest.approx([0.0] * 10)
    assert scope["target_mesh_node_count"] == 2
    assert scope["observed_nonmesh_control_node_ids"] == [99]
    assert scope["external_control_node_active_directions"] == {"99": [1, 2, 3]}
    assert (
        scope["active_dofs_by_mesh_owner"][witness.TARGET_BODY_ID]["equation_count"]
        == 6
    )
    assert scope["all_control_nodes_zero_in_candidate"] is True


def test_target_vector_rejects_missing_selected_body_dof():
    with pytest.raises(ValueError, match="all three active translation DOFs"):
        witness._build_probe_vectors(
            [(1, 1), (1, 2)],
            {1: (0.0, 0.0, 0.0)},
            {1: witness.TARGET_BODY_ID},
            [],
        )


def test_frequency_deck_requires_matrixstorage_perturbation_and_no_loads(tmp_path):
    path = tmp_path / "matrix.inp"
    path.write_text(
        "*STEP,PERTURBATION\n*FREQUENCY,SOLVER=MATRIXSTORAGE\n1,1\n*END STEP\n"
    )
    summary = witness._check_frequency_deck(path)
    assert summary["unloaded_frequency_reference_deck"] is True
    assert summary["contact_active_set_or_zero_pressure_state_proven"] is False

    path.write_text(
        "*STEP,PERTURBATION\n*CLOAD\n10,1,100\n*FREQUENCY,SOLVER=MATRIXSTORAGE\n"
        "1,1\n*END STEP\n"
    )
    with pytest.raises(ValueError, match="applied load cards"):
        witness._check_frequency_deck(path)


def test_frequency_deck_rejects_wrong_solver_or_nonperturbation(tmp_path):
    path = tmp_path / "matrix.inp"
    path.write_text("*STEP\n*FREQUENCY,SOLVER=SPOOLES\n1,1\n*END STEP\n")
    with pytest.raises(ValueError, match=r"PERTURBATION and \*FREQUENCY"):
        witness._check_frequency_deck(path)


def test_sti_chunk_reader_handles_chunk_boundaries(tmp_path):
    path = tmp_path / "reference.sti"
    path.write_text("1 1 1.0\n2 1 -1.0\n2 2 2.0\n3 2 -1.0\n3 3 1.0\n")

    result = witness.evaluate_symmetric_coordinate_chunks(
        witness._iter_sti_chunks(path, records_per_chunk=2),
        3,
        {"translation": [1.0, 1.0, 1.0]},
    )

    assert result["coordinate_record_count"] == 5
    assert result["implicit_symmetric_triangle"] == "lower"
    assert result["probes"]["translation"]["kv_inf_norm"] == pytest.approx(0.0)

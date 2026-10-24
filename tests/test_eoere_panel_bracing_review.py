"""Known-answer controls and explicit source-dependent panel-restraint audit."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from scripts.eoere_panel_bracing_review import annotated_inputs, compliance, controls

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "docs/bolted-frame-development/owner-frame-v6/panel-bracing-review.json"


def test_panel_stiffness_depends_on_both_fastener_and_panel_return_path():
    assert controls()["known_answer_controls_passed"]


def test_free_unloaded_coordinate_is_not_replaced_by_a_support():
    result, audit = compliance(csr_matrix([[20., 0.], [0., 0.]]), np.array([[1.], [0.]]))
    assert result[0, 0] == pytest.approx(.05)
    assert audit["zero_uncoupled_unloaded_coordinates_omitted"] == 1
    assert audit["added_stiffness_or_supports"] is False


def test_loading_a_free_coordinate_is_rejected():
    with pytest.raises(ValueError, match="loads a free coordinate"):
        compliance(csr_matrix([[20., 0.], [0., 0.]]), np.array([[0.], [1.]]))


def test_coupled_force_and_moment_work_reproduces_an_independent_dense_solution():
    stiffness = np.array([[120., 10., -20.], [10., 60., 5.], [-20., 5., 80.]])
    loads = np.array([[1., 0.], [-1., 2.], [0., -2.]])
    expected = loads.T @ np.linalg.solve(stiffness, loads)
    observed, audit = compliance(csr_matrix(stiffness), loads)
    np.testing.assert_allclose(observed, expected, rtol=1e-12, atol=1e-14)
    assert audit["maximum_normalized_reciprocity_error"] < 1e-12


def test_stiff_connector_refinement_preserves_the_small_real_support_stiffness():
    connector = 1e10
    stiffness = csr_matrix([[connector + 1, -connector], [-connector, connector + 3]])
    observed, audit = compliance(stiffness, np.array([[1.], [0.]]))
    expected = (connector + 3) / (4*connector + 3)
    assert observed[0, 0] == pytest.approx(expected, rel=1e-10)
    assert audit["maximum_relative_equilibrium_error"] < 1e-7


def test_only_authenticated_plywood_annotations_can_join_the_saved_timber_chart():
    data = {"timber_rows": [{"name": "eoere_cleat_left"}, {"name": "base_rail_top"}]}
    chart = {"timber": {
        "eoere_cleat_left": {"source": {"name": "eoere_cleat_left", "explicit_plywood_operator": {"EA_N": 100}}},
        "base_rail_top": {"source": {"name": "base_rail_top"}},
    }}
    joined = annotated_inputs(data, chart, {"EA_N": 100})
    assert "explicit_plywood_operator" not in data["timber_rows"][0]
    assert joined["timber_rows"][0]["explicit_plywood_operator"] == {"EA_N": 100}
    with pytest.raises(ValueError, match="source join differs"):
        annotated_inputs(data, chart, {"EA_N": 101})


def test_public_bracing_review_keeps_stiffness_separate_from_strength_and_later_geometry():
    result = json.loads(PUBLIC.read_bytes())
    assert result["geometry_revision"] == "eoere-flat-cleats-principal-upper-pairs-v6"
    assert result["later_revisions_receive_no_force_or_strength_transfer"] is True
    assert result["case_count"] == len(result["case_ids"]) == 6
    assert result["inventory"]["probe_comparisons"] == 72
    assert result["inventory"]["balanced_rhs_solves"] == 144
    assert result["strength_gain_factor"] is None
    for key in ("physical_strength_gain_established", "compression_crushing_or_buckling_gain_established",
                "current_exceedances_reduced_again_by_these_ratios", "matched_external_strength_multiplier_validated",
                "unbraced_climber_load_equilibrium_computed"):
        assert result["evaluation"][key] is False
    assert result["model_assumptions"]["physical_Hillman_law_qualified"] is False
    reference = result["source_bindings"]["method"]
    assert hashlib.sha256((ROOT / reference["path"]).read_bytes()).hexdigest() == reference["sha256"]
    assert result["numerical_checks"]["maximum_relative_equilibrium_error"] < 1e-7


def test_recovered_bracing_inputs_and_all_six_contact_comparisons_remain_bound():
    public = json.loads(PUBLIC.read_bytes())
    for source in public["source_bindings"].values():
        assert hashlib.sha256((ROOT / source["path"]).read_bytes()).hexdigest() == source["sha256"]
    raw = json.loads((ROOT / public["source_bindings"]["full_raw_result"]["path"]).read_bytes())
    for path, digest in raw["source_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
    assert {c["case_id"] for c in raw["cases"]} == set(public["case_ids"])
    for case in raw["cases"]:
        assert len(case["probes"]) == 12
        for name, screws, contacts in (("with_panels", 66, 914), ("without_panels", 0, 0)):
            audit = case["audits"][name]
            assert audit["screw_springs_retained"] == screws
            assert audit["panel_contacts_retained"] == contacts
            assert audit["added_stiffness_or_supports"] is False
            assert audit["maximum_relative_equilibrium_error"] < 1e-7
        for probe in case["probes"]:
            assert probe["modeled_stiffness_ratio"] == pytest.approx(
                probe["with_panels_stiffness"] / probe["without_panels_stiffness"], rel=1e-12)

import json
import math

from fea.wood_joint_axial_mpc_benchmark import (
    ARTIFACT_DIR,
    BOTTOM_NODES,
    TOP_AREA_WEIGHTS,
    TOP_NODES,
    analytical_oracle,
    prepare_artifacts,
    render_deck,
)


def _section(deck, keyword):
    lines = deck.splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip().upper() == keyword)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("*")),
        len(lines),
    )
    return [
        line.strip()
        for line in lines[start + 1 : end]
        if line.strip() and not line.lstrip().startswith("**")
    ]


def test_deck_has_one_area_weighted_mean_axial_equation_and_rigid_nut():
    deck = render_deck()
    assert deck.count("*EQUATION\n") == 1
    assert deck.count("*RIGID BODY,") == 1
    assert "*CONTACT" not in deck and "*TIE" not in deck and "*COUPLING" not in deck

    rows = _section(deck, "*EQUATION")
    assert rows[0] == "10"
    fields = [float(value) for row in rows[1:] for value in row.split(",")]
    terms = [tuple(fields[i : i + 3]) for i in range(0, len(fields), 3)]
    assert terms[0] == (14.0, 3.0, 0.25)  # largest bolt-face tributary weight
    assert terms[-1] == (900.0, 3.0, -1.0)  # loaded RP remains independent
    actual = {
        int(node): coefficient
        for node, dof, coefficient in terms
        if int(node) in TOP_NODES
    }
    assert actual == TOP_AREA_WEIGHTS
    assert math.isclose(sum(actual.values()), 1.0)

    assert "*RIGID BODY,NSET=NUT_NODES,REF NODE=900,ROT NODE=901" in deck
    assert "21,22,23,24,25,26,27,28" in _section(deck, "*NSET,NSET=NUT_NODES")
    assert all(
        len(row.split(",")) <= 16 for row in _section(deck, "*NSET,NSET=ALL_NODES")
    )
    assert "*STEP,INC=10" in deck and "NLGEOM" not in deck
    assert "900,1,2,0" in _section(deck, "*BOUNDARY")
    assert "901,1,3,0" in _section(deck, "*BOUNDARY")


def test_analytic_oracle_balances_force_moment_and_affine_bar_response():
    oracle = analytical_oracle()
    assert math.isclose(oracle["axial_extension_mm"], 0.005, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(oracle["axial_strain"], 5e-5, rel_tol=0, abs_tol=1e-15)
    assert oracle["stress_mpa_voigt_11_22_33_12_13_23"] == [
        0.0,
        0.0,
        10.0,
        0.0,
        0.0,
        0.0,
    ]
    assert oracle["lateral_strain_x_y"] == -1.5e-5
    assert math.isclose(sum(oracle["bottom_reaction_by_node_n_u3"].values()), -1000.0)
    assert oracle["force_residual_n"] == [0.0, 0.0, 0.0]
    assert oracle["moment_residual_nmm"] == [0.0, 0.0, 0.0]
    assert oracle["load_moment_about_global_origin_nmm"] == [5000.0, -5000.0, 0.0]
    assert oracle["support_moment_about_global_origin_nmm"] == [-5000.0, 5000.0, 0.0]
    assert oracle["weighted_bolt_face_mean_u3_mm"] == oracle["reference_node_u3_mm"]
    assert math.isclose(
        sum(abs(v) for v in oracle["bottom_reaction_by_node_n_u3"].values()), 1000.0
    )
    assert set(oracle["bottom_reaction_by_node_n_u3"]) == {
        str(node) for node in BOTTOM_NODES
    }


def test_preparation_writes_unsolved_deck_and_oracle_manifest(tmp_path):
    deck_path, manifest_path = prepare_artifacts(tmp_path)
    assert deck_path.name == "axial-mean-mpc.inp"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["status"] == "PREPARED_NOT_SOLVED"
    assert (
        manifest["solver"]["execution_status"]
        == "not_run; parent owns frozen native execution"
    )
    assert manifest["axial_endpoint"]["explicit_equation_count"] == 1
    assert manifest["oracle"]["axial_extension_mm"] == 0.005
    assert manifest["claim_boundary"]
    assert ARTIFACT_DIR.name == "ccx_wood_joint_axial_mpc_benchmark"

import hashlib
from copy import deepcopy

import pytest

from fea.floor_contact import floor_faces
from fea.full_frame_mortar import audit, build_deck, mesh_digest, verify_deck


def affine_fixture_weights(elements, nodes):
    # Unit-test integration seam only: each fixture element is an affine
    # 10x10x10 right tetrahedron, V=1000/6. Production uses Gmsh on curved tets.
    assert {n for ids in elements.values() for n in ids} == nodes.keys()
    weights = dict.fromkeys(nodes, 0.)
    for ids in elements.values():
        for i, n in enumerate(ids):
            weights[n] += (1000/6)*(-1/20 if i < 4 else 1/5)
    return weights


@pytest.fixture(autouse=True)
def analytical_integration_seam(monkeypatch):
    monkeypatch.setattr("fea.full_frame_mortar.integrated_weights", affine_fixture_weights)


def fixture(formulation="mortar"):
    # Three small disconnected tetrahedra supply algebraic audit fixtures;
    # they are not a physical frame or a solver validation.
    nodes, elements, owners = {}, {}, {}
    for e, (name, x, y) in enumerate((("LEFT", -20., 1200.), ("RIGHT", 20., 1200.), ("KICKER", 0., 0.)), 1):
        corners = [(x, y, 0.), (x+10, y, 0.), (x, y+10, 0.), (x, y, 10.)]
        points = corners+[tuple((corners[a][i]+corners[b][i])/2 for i in range(3))
                          for a, b in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
        ids = list(range(10*(e-1)+1, 10*e+1))
        nodes.update(zip(ids, points, strict=True))
        elements[e] = tuple(ids)
        owners.update(dict.fromkeys(ids, name))
    groups = floor_faces(nodes, elements)
    top = [4, 8, 14, 18, 24]
    text, ground, bottom = build_deck(nodes, elements, groups, top, formulation)
    record = {"wood_nodes": nodes, "nodal_volume_mm3": affine_fixture_weights(elements, nodes),
              "load_nodes": top, "ground_nodes": ground, "bottom_nodes": bottom,
              "formulation": formulation, "mu": .5, "normal_penalty_n_mm3": 10000.,
              "tangent_penalty_n_mm3": 100., "increment": .25,
              "deck_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "wood_mesh_sha256": mesh_digest(nodes, elements)}
    rows = {}
    for endpoint in (1., 2.):
        u = dict.fromkeys(nodes, (.1, .2, -.001))
        rows[("displacements", "WOODN", endpoint)] = u
        for name, xyz in ground.items():
            rows[("displacements", "GROUND_"+name, endpoint)] = {
                n: (0., 0., 0.) if n in bottom[name] else (.2, .3, -.001) for n in xyz}
            rf = {n: [0., 0., 0.] if n in bottom[name] else [123., 456., 789.] for n in xyz}
            x0, x1 = min(p[0] for p in xyz.values()), max(p[0] for p in xyz.values())
            y0, y1 = min(p[1] for p in xyz.values()), max(p[1] for p in xyz.values())
            for n, p in nodes.items():
                if owners[n] != name:
                    continue
                force = record["nodal_volume_mm3"][n]*6e-10*9806.65
                if endpoint == 2. and n in top:
                    force += 240.
                tx, ty = (p[0]+u[n][0]-x0)/(x1-x0), (p[1]+u[n][1]-y0)/(y1-y0)
                for tag, fraction in zip(bottom[name], ((1-tx)*(1-ty), tx*(1-ty), tx*ty, (1-tx)*ty), strict=True):
                    rf[tag][2] += force*fraction
            rows[("forces", "GROUND_"+name, endpoint)] = rf
    return text, record, rows


def output(rows):
    return "\n".join(f"{kind} for set {name} and time {t}\n"+
                     "\n".join(f"{n} "+" ".join(map(str, xyz)) for n, xyz in values.items())+"\n"
                     for (kind, name, t), values in rows.items())


def test_formulations_have_identical_physics_except_contact_and_supported_output():
    penalty, p, _ = fixture("penalty")
    mortar, m, _ = fixture("mortar")
    diagnostic = "*CONTACT PRINT\nCDIS,CSTR\n"+"".join(
        f"*CONTACT PRINT,SLAVE=SLAVE_{name},MASTER=MASTER_{name}\nCF,CFN,CFS\n" for name in p["ground_nodes"])
    assert penalty.replace(diagnostic, "").replace("TYPE=SURFACE TO SURFACE", "TYPE=MORTAR") == mortar
    assert sum(map(len, m["bottom_nodes"].values())) == 12
    assert all(m["ground_nodes"][name][n][2] == -100. for name, ids in m["bottom_nodes"].items() for n in ids)
    model, gravity, load = mortar.split("*STEP,NLGEOM,INC=200\n")
    assert model.split("*BOUNDARY\n")[1] == "BOTTOM_LEFT,1,3,0\nBOTTOM_RIGHT,1,3,0\nBOTTOM_KICKER,1,3,0\n"
    assert "*BOUNDARY" not in gravity+load and "*CLOAD" not in gravity
    assert mortar.count("TIMBER,GRAV,9806.65,0,0,-1") == 2
    assert mortar.count("*STATIC\n0.25,1,1e-6,0.25") == 2
    assert "*CONTACT PRINT" not in mortar


def test_deformed_equilibrium_ignores_free_contact_rf_and_requires_complete_steps():
    text, record, rows = fixture()
    result = audit(text, output(rows), record)
    assert [s["load_n"] for s in result] == [0., 1200.]
    assert all(max(map(abs, s["moment_residual_nmm"])) < 1e-8 for s in result)
    assert all(s["patches"]["LEFT"]["maximum_ground_displacement_mm"] > .3 for s in result)
    # Nonzero free master RF was deliberately excluded from external balance.
    assert rows[("forces", "GROUND_LEFT", 2.)][max(record["ground_nodes"]["LEFT"])] == [123., 456., 789.]


def test_exact_consistent_weights_include_negative_corners():
    text, record, rows = fixture()
    weights = record["nodal_volume_mm3"]
    assert sum(weights.values()) == pytest.approx(500.)
    assert sum(v < 0 for v in weights.values()) == 12
    assert weights[1] == pytest.approx(-1000/120)
    assert weights[5] == pytest.approx(1000/30)
    assert len(audit(text, output(rows), record)) == 2


@pytest.mark.parametrize("preserve_total", [False, True])
def test_finite_stale_or_redistributed_gravity_weights_rejected(preserve_total):
    text, record, _ = fixture()
    weights = record["nodal_volume_mm3"]
    original_total = sum(weights.values())
    weights[1] += 1.
    if preserve_total:
        weights[2] -= 1.
        assert sum(weights.values()) == pytest.approx(original_total)
    # Reject before reading results: neither a new total nor cancellation in
    # the total can disguise weights belonging to different mesh integration.
    with pytest.raises(ValueError, match="weights differ from verified mesh"):
        audit(text, "", record)


def test_initial_horizontal_cone_is_not_a_deformed_master_acceptance_gate():
    text, record, rows = fixture()
    # Equal/opposite collinear forces retain global balance but exceed each
    # initial-horizontal friction estimate. The local law is not validated.
    for name, force in (("LEFT", 5.), ("RIGHT", -5.)):
        n = record["bottom_nodes"][name][0]
        rows[("forces", "GROUND_"+name, 1.)][n][0] = force
        for n, p in record["ground_nodes"][name].items():
            if n not in record["bottom_nodes"][name]:
                rows[("displacements", "GROUND_"+name, 1.)][n] = (.2, .3, p[0]*.001)
    result = audit(text, output(rows), record)
    assert not result[0]["patches"]["LEFT"]["approximate_horizontal_friction_diagnostic_pass"]
    assert "neither a necessary" in result[0]["patches"]["LEFT"]["friction_qualification"]


@pytest.mark.parametrize("kind,name", [("displacements", "WOODN"), ("displacements", "GROUND_LEFT"),
                                       ("forces", "GROUND_RIGHT"), ("forces", "GROUND_KICKER")])
def test_missing_endpoint_output_is_rejected(kind, name):
    text, record, rows = fixture()
    del rows[(kind, name, 2.)]
    with pytest.raises(ValueError, match="Incomplete"):
        audit(text, output(rows), record)


@pytest.mark.parametrize("mutation", ["force", "moment", "support_motion", "nan_output", "undeformed_wood"])
def test_balance_and_fixed_support_fail_closed(mutation):
    text, record, rows = fixture()
    n = record["bottom_nodes"]["LEFT"][0]
    reactions = rows[("forces", "GROUND_LEFT", 2.)]
    if mutation == "force":
        reactions[n][2] += 1.
    elif mutation == "moment":
        reactions[n][2] += 1.
        reactions[record["bottom_nodes"]["LEFT"][1]][2] -= 1.
    elif mutation == "support_motion":
        rows[("displacements", "GROUND_LEFT", 2.)][n] = (.01, 0., 0.)
    elif mutation == "nan_output":
        reactions[n][0] = float("nan")
    else:
        rows[("displacements", "WOODN", 2.)] = dict.fromkeys(record["wood_nodes"], (0., 0., 0.))
    with pytest.raises(ValueError):
        audit(text, output(rows), record)


@pytest.mark.parametrize("mutation", ["weights", "empty_load", "duplicate_load", "support", "ground", "mu", "mesh"])
def test_invalid_or_mismatched_record_context_fails(mutation):
    text, record, rows = fixture()
    if mutation == "weights":
        record["nodal_volume_mm3"][1] = float("nan")
    elif mutation == "empty_load":
        record["load_nodes"] = []
    elif mutation == "duplicate_load":
        record["load_nodes"][1] = record["load_nodes"][0]
    elif mutation == "support":
        record["bottom_nodes"]["LEFT"][0] = max(record["ground_nodes"]["LEFT"])
    elif mutation == "ground":
        record["ground_nodes"]["LEFT"][record["bottom_nodes"]["LEFT"][0]] = (0., 0., -100.)
    elif mutation == "mu":
        record["mu"] = float("nan")
    else:
        record["wood_mesh_sha256"] = "changed"
    with pytest.raises(ValueError):
        audit(text, output(rows), record)


@pytest.mark.parametrize("change", ["wood_spc", "cload", "gravity", "contact", "spring"])
def test_updated_digest_cannot_hide_changed_physics(change):
    text, record, _ = fixture()
    if change == "wood_spc":
        text = text.replace("*STEP,NLGEOM", "*BOUNDARY,OP=MOD\nWOODN,1,3,0\n*STEP,NLGEOM", 1)
    elif change == "cload":
        text = text.replace("4,3,-240.0", "4,3,-120.0")
    elif change == "gravity":
        text = text.replace("TIMBER,GRAV,9806.65,0,0,-1", "TIMBER,GRAV,980.665,0,0,-1", 1)
    elif change == "contact":
        text = text.replace("0.5,100.0", "0.9,100.0")
    else:
        text += "*SPRING\n1,1\n100.\n"
    record["deck_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    with pytest.raises(ValueError, match="Deck differs"):
        verify_deck(text, record)


def test_builder_rejects_incomplete_floor_faces_and_unused_mesh_nodes():
    _, record, _ = fixture()
    nodes, elements, groups, _, _ = verify_deck(fixture()[0], record)
    missing = deepcopy(groups)
    missing["LEFT"] = []
    with pytest.raises(ValueError, match="floor faces"):
        build_deck(nodes, elements, missing, record["load_nodes"], "mortar")
    nodes[1000] = (0., 0., 0.)
    with pytest.raises(ValueError, match="coverage"):
        build_deck(nodes, elements, groups, record["load_nodes"], "mortar")

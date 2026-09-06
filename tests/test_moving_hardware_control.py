import copy
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

from fea import moving_hardware_control as control
from fea.floor_contact import FACES


def fixture(*, catalog=False):
    xyz, elements, bodies = {}, {}, {}
    origin = [1255.3, 971.0333737790937, 1134.3443559823804]
    names = ["leg_right_inner", "leg_right_outer"] + [f"leg_stitch_right_{i}_{role}"
        for i in (1, 2, 3) for role in ("bolt_nut", "washer_inner", "washer_outer")]
    for name in names:
        body_nodes, body_elements, surfaces = [], [], {}
        role = next((k for k, v in control.BODY_NAMES.items() if v == name), None)
        washer_radius = control.CATALOG_WASHER_RADIUS if catalog else control.RADIUS
        specs = [(label, spec) for label, spec in control.surface_specs(washer_radius).items() if spec[0] == role]
        for label, spec in specs or [("unused", (None, "Plane", (0, 0, 0, 1, 1, 1), 1))]:
            _, kind, bounds, area = spec
            surface_radius = washer_radius if role == "WASHER" else control.RADIUS
            if kind == "Cylinder":
                corners = [(0, surface_radius, 0), (1, surface_radius, 0), (0, surface_radius*math.cos(.2), surface_radius*math.sin(.2)), (0, 0, 0)]
            else:
                corners = [(0, 6, 0), (0, 7, 0), (0, 6, 1), (1, 6, 0)]
            points = corners + [tuple((corners[i][a]+corners[j][a])/2 for a in range(3))
                                for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))]
            if kind == "Cylinder":
                for i in (4, 5, 6):
                    x, y, z = points[i]
                    radius = math.hypot(y, z)
                    points[i] = (x, y*surface_radius/radius, z*surface_radius/radius)
            ids = list(range(len(xyz)+1, len(xyz)+11))
            xyz.update({n: tuple(v+origin[a] for a, v in enumerate(p)) for n, p in zip(ids, points)})
            e = len(elements)+1
            elements[e] = ids
            body_nodes += ids
            body_elements.append(e)
            surfaces[label] = {"cad_type": kind, "cad_bounds_mm": [v+origin[i % 3] for i, v in enumerate(bounds)],
                "cad_area_mm2": area, "faces": [[e, 1]], "nodes": [ids[i] for i in FACES[0]]}
        bodies[name] = {"nodes": body_nodes, "elements": body_elements, "surfaces": surfaces,
                       "min_sampled_jacobian": 1, "min_integration_jacobian": 1, "mesh_volume_mm3": 1, "cad_volume_mm3": 1}
    lines = ["*NODE"] + [str(n)+","+",".join(map(repr, p)) for n, p in xyz.items()]
    lines += ["*ELEMENT,TYPE=C3D10"] + [str(e)+","+",".join(map(str, ids)) for e, ids in elements.items()]
    text = "\n".join(lines)+"\n"
    geometry = {"locked_threads": True, "parts": {n: {"bounds_mm": [0]*6} for n in names},
                "step_sha256": {n+".step": "unused" for n in names}, "stitches": [{"name": control.STATION,
                "start_mm": origin, "axis": [1., 0., 0.], "shank_diameter_mm": 9.525, "grip_mm": 38.1, "length_mm": 57.15}]}
    if catalog:
        geometry.update(catalog_washer_bore=True, geometry_variant="locked-thread-fw38-minimum-bore-11-body")
        geometry["stitches"][0]["washer_bore_diameter_mm"] = 10.9982
    record = {"locked_threads": True, "body_count": 11, "bodies": bodies, "mesh_sha256": control.digest(text.encode()),
              "status": "VERIFIED MESH ONLY; NO SOLVER", "geometry_sha256": control.digest(json.dumps(geometry).encode())}
    return text, record, geometry


def test_selects_two_owned_bodies_and_four_complete_surfaces():
    context = control.build_context(*fixture())
    assert set(context["bodies"]) == {"BOLT_NUT", "WASHER"}
    assert len(context["nodes"]) == 40 and len(context["elements"]) == 4
    assert len(context["surfaces"]) == 4
    assert context["angular_reference_mm_local"] == [1, 0, 0]
    assert all(len(surface["nodes"]) == 6 for surface in context["surfaces"].values())
    assert context["diagnostic_reference_scales"]["status"].startswith("FORMULAS ONLY")
    assert context["quiescent_diagnostic_gates"]["max_displacement_mm"] == 1e-6


def test_catalog_bore_preserves_core_and_prepares_only_stationary_case():
    context = control.build_context(*fixture(catalog=True))
    assert context["nominal_washer_shank_radial_clearance_mm"] == pytest.approx(.7366)
    assert context["surfaces"]["CORE_SHANK"]["cad_bounds_mm_local"][4] == control.RADIUS
    assert context["surfaces"]["WASHER_BORE"]["cad_bounds_mm_local"][4] == control.CATALOG_WASHER_RADIUS
    assert set(context["cases"]) == {"quiescent"}
    assert "*DYNAMIC,ALPHA=0" in control.deck(context, "quiescent")
    with pytest.raises(ValueError, match="explicitly prepared"):
        control.deck(context, "moving")


def test_direct_quiescent_changes_only_integration_and_preserves_quiet_gates():
    adaptive = control.build_context(*fixture(catalog=True))
    direct = control.build_context(*fixture(catalog=True), direct_quiescent=True)
    assert {k: v for k, v in direct.items() if k not in ("cases", "integration_intent")} == {
        k: v for k, v in adaptive.items() if k not in ("cases", "integration_intent")}
    assert set(direct["cases"]) == {"quiescent"}
    assert direct["integration_intent"]["expected_fixed_increment_count"] == 20
    settings = direct["cases"]["quiescent"]
    assert settings["total_time_s"] / settings["initial_dt_s"] == 20
    assert "min_dt_s" not in settings and "max_dt_s" not in settings
    output = control.deck(direct, "quiescent")
    assert "*STEP,NLGEOM,INC=20\n*DYNAMIC,DIRECT,ALPHA=0\n1e-07,2e-06\n*NODE PRINT" in output
    assert output == control.deck(json.loads(json.dumps(direct)), "quiescent")
    initial = output.split("*INITIAL CONDITIONS,TYPE=VELOCITY\n")[1].split("*STEP")[0]
    assert all(float(line.split(",")[2]) == 0 for line in initial.splitlines())
    assert not any(word in output for word in ("EXPLICIT", "*BOUNDARY", "*TIE", "*DLOAD", "*CLOAD"))
    with pytest.raises(ValueError, match="explicitly prepared"):
        control.deck(direct, "moving")


@pytest.mark.parametrize("flag", [None, 0, 1, "true", "false", {}])
def test_direct_option_requires_boolean(flag, tmp_path):
    with pytest.raises(ValueError, match="must be a boolean"):
        control.build_context(*fixture(catalog=True), direct_quiescent=flag)
    with pytest.raises(ValueError, match="must be a boolean"):
        control.prepare(tmp_path, tmp_path / "missing", direct_quiescent=flag)


def test_direct_rejects_legacy_geometry_and_malformed_cli():
    with pytest.raises(ValueError, match="requires catalog"):
        control.build_context(*fixture(), direct_quiescent=True)
    result = subprocess.run([sys.executable, "-m", "fea.moving_hardware_control", "missing", "missing",
                             "--direct-quiescent=false"], capture_output=True, text=True, check=False)
    assert result.returncode == 2 and "ignored explicit argument" in result.stderr


@pytest.mark.parametrize("fault", ["velocity", "dt", "geometry", "flag"])
def test_direct_deck_rejects_changed_intent(fault):
    context = control.build_context(*fixture(catalog=True), direct_quiescent=True)
    settings = context["cases"]["quiescent"]
    if fault == "velocity":
        settings["initial_velocity_mm_s"]["WASHER"][0] = 100
    elif fault == "dt":
        settings["initial_dt_s"] = 1e-8
    elif fault == "geometry":
        context["geometry_variant"] = "locked-thread-11-body"
    else:
        settings["direct_quiescent"] = "true"
    with pytest.raises(ValueError):
        control.deck(context, "quiescent")


@pytest.mark.parametrize("fault", ["flag", "tag", "diameter", "legacy_mesh"])
def test_catalog_selector_rejects_mismatched_geometry(fault):
    text, record, geometry = fixture(catalog=True)
    if fault == "flag":
        geometry["catalog_washer_bore"] = "true"
    elif fault == "tag":
        geometry["geometry_variant"] = "unknown"
    elif fault == "diameter":
        geometry["stitches"][0]["washer_bore_diameter_mm"] = 9.525
    else:
        text, record, _ = fixture()
    with pytest.raises(ValueError):
        control.build_context(text, record, geometry)


def test_surface_checks_midnodes_area_bounds_and_uniqueness():
    for fault in ("midnode", "area", "bounds", "duplicate", "off_cylinder"):
        text, record, geometry = fixture()
        body = record["bodies"][control.BODY_NAMES["WASHER"]]
        surface = body["surfaces"]["WASHER_BORE"]
        if fault == "midnode":
            surface["nodes"].pop()
        elif fault == "area":
            surface["cad_area_mm2"] *= 2
        elif fault == "bounds":
            surface["cad_bounds_mm"][0] += .01
        elif fault == "duplicate":
            body["surfaces"]["duplicate"] = copy.deepcopy(surface)
        else:
            nodes, elements = control.mesh(text)
            n = surface["nodes"][-1]
            nodes[n] = (nodes[n][0], nodes[n][1]+.01, nodes[n][2])
            with pytest.raises(ValueError, match="cylinder"):
                control.select_surface("WASHER_BORE", body, nodes, elements, geometry["stitches"][0]["start_mm"])
            continue
        with pytest.raises(ValueError):
            control.build_context(text, record, geometry)


@pytest.mark.parametrize("fault", ["variant", "count", "hash", "jacobian"])
def test_rejects_wrong_mesh_or_geometry(fault):
    text, record, geometry = fixture()
    if fault == "variant":
        geometry["locked_threads"] = False
    elif fault == "count":
        record["body_count"] = 14
    elif fault == "hash":
        text += "** changed\n"
    else:
        record["bodies"][control.BODY_NAMES["WASHER"]]["min_integration_jacobian"] = -1
    with pytest.raises(ValueError):
        control.build_context(text, record, geometry)


def test_decks_have_only_unforced_implicit_frictionless_contacts():
    context = control.build_context(*fixture())
    for case in ("quiescent", "moving"):
        deck = control.deck(context, case)
        assert deck == control.deck(json.loads(json.dumps(context)), case)
        assert "*DYNAMIC,ALPHA=0\n1e-08,2e-06,1e-11,1e-07" in deck
        assert deck.count("*CONTACT PAIR,") == 2
        assert "WASHER_HEAD,CORE_HEAD" in deck and "WASHER_BORE,CORE_SHANK" in deck
        assert "210000.,0.3\n*DENSITY\n7.85e-9" in deck
        assert "*CONTACT PRINT,FREQUENCY=1,TOTALS=YES\nCDIS,CSTR,CELS,CNUM" in deck
        assert deck.count("\nCF\n") == 2 and "CFN" not in deck and "CFS" not in deck
        assert not any(word in deck for word in ("EXPLICIT", "*BOUNDARY", "*TIE", "TYPE=MORTAR", "*FRICTION\n", "*DLOAD", "*CLOAD", "ADJUST", "SMALLSLIDING"))
        initial = deck.split("*INITIAL CONDITIONS,TYPE=VELOCITY\n")[1].split("*STEP")[0]
        velocities = {(int(n), int(a)): float(v) for n, a, v in (line.split(",") for line in initial.splitlines())}
        assert len(velocities) == 3*len(context["nodes"])
        for role, body in context["bodies"].items():
            expected = context["cases"][case]["initial_velocity_mm_s"][role]
            assert all(velocities[n, a] == expected[a-1] for n in body["nodes"] for a in (1, 2, 3))


def test_preparation_freezes_inputs_and_only_two_decks(tmp_path):
    text, record, geometry = fixture()
    (tmp_path / "mesh.inp").write_text(text)
    (tmp_path / "mesh.json").write_text(json.dumps(record))
    (tmp_path / "geometry.json").write_text(json.dumps(geometry))
    directory = control.prepare(tmp_path, tmp_path / "geometry.json", tmp_path / "outputs")
    frozen = json.loads((directory / "freeze.json").read_text())
    for name, expected in frozen["files_sha256"].items():
        assert control.digest((directory / name).read_bytes()) == expected
    assert sorted(p.name for p in directory.glob("*.inp")) == ["moving.inp", "quiescent.inp"]
    assert not list(directory.glob("*.dat"))
    assert (directory / "frozen/mesh.inp").read_text() == text


def test_foreign_import_and_loaded_source_drift_rejected(monkeypatch):
    module = sys.modules["fea.floor_contact"]
    with monkeypatch.context() as patch:
        patch.setattr(module, "__file__", "/tmp/foreign-checkout/floor_contact.py")
        with pytest.raises(ValueError, match="outside this checkout"):
            control.source_snapshot()
    with monkeypatch.context() as patch:
        patch.setattr(module, "mesh", lambda text: ({}, {}))
        with pytest.raises(ValueError, match="Loaded code differs"):
            control.source_snapshot()


def test_source_mutation_during_preparation_rejected(tmp_path, monkeypatch):
    text, record, geometry = fixture()
    (tmp_path / "mesh.inp").write_text(text)
    (tmp_path / "mesh.json").write_text(json.dumps(record))
    (tmp_path / "geometry.json").write_text(json.dumps(geometry))
    snapshots = control.source_snapshot()
    calls = []
    def snapshot():
        calls.append(1)
        return snapshots if len(calls) == 1 else {**snapshots, "floor_contact.py": b"changed"}
    monkeypatch.setattr(control, "source_snapshot", snapshot)
    with pytest.raises(ValueError, match="Source changed during"):
        control.prepare(tmp_path, tmp_path / "geometry.json", tmp_path / "outputs")
    leftovers = list((tmp_path / "outputs").iterdir())
    assert len(leftovers) == 1
    assert (leftovers[0] / "context.json").exists()  # Retain failure evidence.
    assert not (leftovers[0] / "freeze.json").exists()
    from fea import moving_hardware_solve
    with pytest.raises(FileNotFoundError):
        moving_hardware_solve.prepare(leftovers[0], tmp_path / "solves")


def test_surface_cannot_drop_an_exterior_face_and_trim_its_node_list():
    text, record, geometry = fixture()
    xyz, elements = control.mesh(text)
    body = record["bodies"][control.BODY_NAMES["WASHER"]]
    surface = body["surfaces"]["WASHER_BORE"]
    original_element = surface["faces"][0][0]
    # Two independent TRI6-bearing cells test set completeness. Coincident
    # coordinates deliberately do not merge their distinct node ownership.
    first_node = max(xyz)+1
    mapping = dict(zip(elements[original_element], range(first_node, first_node+10)))
    new_element = max(elements)+1
    xyz.update({mapping[n]: xyz[n] for n in elements[original_element]})
    elements[new_element] = tuple(mapping[n] for n in elements[original_element])
    body["nodes"] += list(mapping.values())
    body["elements"].append(new_element)
    extra_nodes = [elements[new_element][i] for i in FACES[0]]
    surface["faces"].append([new_element, 1])
    surface["nodes"] += extra_nodes
    selected = control.select_surface("WASHER_BORE", body, xyz, elements, geometry["stitches"][0]["start_mm"])
    assert len(selected["faces"]) == 2
    surface["faces"].pop()
    surface["nodes"] = [n for n in surface["nodes"] if n not in extra_nodes]
    with pytest.raises(ValueError, match="omits matching exterior"):
        control.select_surface("WASHER_BORE", body, xyz, elements, geometry["stitches"][0]["start_mm"])


@pytest.mark.parametrize("direct", [False, True])
def test_optional_native_mass_stage_freezes_predeclared_scales(tmp_path, monkeypatch, direct):
    text, record, geometry = fixture(catalog=direct)
    (tmp_path / "mesh.inp").write_text(text)
    (tmp_path / "mesh.json").write_text(json.dumps(record))
    (tmp_path / "geometry.json").write_text(json.dumps(geometry))
    snapshot = control.source_snapshot()
    # Replace only numerical integration for this pure test; production snapshot
    # checks deliberately reject patched code, so retain its original snapshot here.
    monkeypatch.setattr(control, "source_snapshot", lambda: snapshot)
    def native_mass(elements, nodes, density):
        washer = record["bodies"][control.BODY_NAMES["WASHER"]]
        assert set(elements) == set(washer["elements"])
        assert set(nodes) == set(washer["nodes"])
        assert density == 7.85e-9
        assert all(v == float(format(v, ".12g")) for p in nodes.values() for v in p)
        return {1: ((), ((6e-6,),))}
    monkeypatch.setattr(control.dynamic_momentum, "calculix_221_mass", native_mass)
    directory = control.prepare(tmp_path, tmp_path / "geometry.json", tmp_path / "outputs",
                                integrate_reference=True, direct_quiescent=direct)
    scales = json.loads((directory / "context.json").read_text())["diagnostic_reference_scales"]
    assert scales["reference_mass_tonne"] == 6e-6
    assert scales["P_star_tonne_mm_s"] == pytest.approx(6e-6*math.sqrt(20000))
    assert scales["E_star_N_mm"] == pytest.approx(.06)
    assert scales["H_star_tonne_mm2_s"] == pytest.approx(57.15*6e-6*math.sqrt(20000))
    assert (directory / "frozen/dynamic_momentum.py").exists()
    if direct:
        context = json.loads((directory / "context.json").read_text())
        assert context["integration_intent"]["direct_quiescent"] is True
        assert context["cases"]["quiescent"]["maximum_increment_count"] == 20
        assert not (directory / "moving.inp").exists()
        inventory = json.loads((directory / "freeze.json").read_text())["files_sha256"]
        assert inventory["context.json"] == control.digest((directory / "context.json").read_bytes())
        assert inventory["quiescent.inp"] == control.digest((directory / "quiescent.inp").read_bytes())


def test_constant_only_source_change_after_import_is_rejected(monkeypatch):
    source = Path(control.__file__).resolve()
    original_read = Path.read_bytes
    original = original_read(source)
    changed = original.replace(b'"max_dt_s": 1e-7', b'"max_dt_s": 2e-7')
    assert changed != original
    # Simulate a concurrent editor without altering any real source file.
    monkeypatch.setattr(Path, "read_bytes", lambda path: changed if path.resolve() == source else original_read(path))
    with pytest.raises(ValueError, match="Source bytes changed after module import"):
        control.source_snapshot()


def test_in_memory_declared_configuration_mutation_is_rejected(monkeypatch):
    monkeypatch.setitem(control.CASE_SETTINGS, "total_time_s", 2e-5)
    with pytest.raises(ValueError, match="Declared configuration changed"):
        control.source_snapshot()


def test_native_node_reader_width_regression():
    context = control.build_context(*fixture())
    node = next(iter(context["nodes"]))
    context["nodes"][node] = (-3.751665644813329e-12, .12345678901234567, 57.15)
    line = next(line for line in control.deck(context, "quiescent").splitlines() if line.startswith(f"{node},"))
    assert all(len(value) <= 20 for value in line.split(",")[1:])


def test_quantized_context_matches_every_solver_coordinate_and_declared_bound():
    text, record, geometry = fixture()
    context = control.build_context(text, record, geometry)
    nodes = {}
    for line in control.deck(context, "quiescent").split("*NODE\n")[1].split("*ELEMENT")[0].splitlines():
        tag, *coordinates = line.split(",")
        assert len(coordinates) == 3 and all(len(v) <= 20 for v in coordinates)
        nodes[int(tag)] = tuple(map(float, coordinates))
    assert nodes == context["nodes"]
    original, _ = control.mesh(text)
    origin = context["origin_mm_global"]
    actual_error = max(abs(p[a]-(original[n][a]-origin[a])) for n, p in nodes.items() for a in range(3))
    report = context["coordinate_quantization"]
    assert report["max_abs_component_error_mm"] == actual_error
    assert actual_error <= report["maximum_allowed_error_mm"] == 5e-10
    assert report["format"] == ".12g"
    assert "frozen/mesh.inp" in report["original_coordinates"]


def test_coordinate_quantization_rejects_out_of_scope_roundoff():
    with pytest.raises(ValueError, match="quantization exceeds"):
        control.quantize_coordinates({1: (1234567890123.456, 0., 0.)})

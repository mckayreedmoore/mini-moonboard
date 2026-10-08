"""Only guards and loaded4strip/2flange recovery; no candidate preparation."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("guarded_assembly_interface.py")
SPEC = importlib.util.spec_from_file_location("eoere_guarded_assembly_fixtures", PATH)
method = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(method)


def element():
    return method.GuardedFourPortAssemblyElement(method.four.FourPortStripModel(),
                                                "toy-fitting", np.arange(24), 24)


def response(el):
    return el.response(np.arange(24)*1e-5, declared_route=method.ROUTE,
        loads=[{"id": "own-gravity", "body": "toy-fitting", "point_xyz_mm": [18., 3., 21.],
                "force_xyz_n": [0., 0., -12.]}])


@pytest.mark.parametrize("mutation", ["scenario", "matrix", "port", "source", "storage"])
def test_rejects_edited_cached_scenario_operator_map_sources_and_storage(mutation):
    el = element()
    if mutation == "scenario":
        el.model.inputs["elastic_modulus_mpa"] = 1.
    elif mutation == "matrix":
        el.model.K = el.model.K.copy()+np.eye(24)
    elif mutation == "port":
        el.model.port_manifest[0]["point_reference_xyz_mm"][0] += 1.
    elif mutation == "source":
        el.source_sha256["invented-source"] = "0"*64
    else:
        el.rotation_scale = 1.
    with pytest.raises(ValueError, match="changed after construction"):
        response(el)
    with pytest.raises(ValueError):
        el.descriptor()


@pytest.mark.parametrize("public", ["response", "project_loads", "point_port", "centroid_load_port",
                                    "rigid_modes", "elastic_block", "descriptor"])
def test_every_public_call_rechecks_actual_source_pins(public, monkeypatch):
    el = element()
    real = method.four.sha
    monkeypatch.setattr(method.four, "sha", lambda path: "0"*64 if Path(path) == method.BASE else real(path))
    calls = {"response": lambda: response(el), "project_loads": lambda: el.project_loads([], declared_route=method.ROUTE),
             "point_port": lambda: el.point_port("arm-x/far-minus", [1., 2., 3.]),
             "centroid_load_port": lambda: el.centroid_load_port([1., 2., 3.], declared_route=method.ROUTE),
             "rigid_modes": lambda: el.rigid_modes([0., 0., 0.]),
             "elastic_block": el.elastic_block, "descriptor": el.descriptor}
    with pytest.raises(ValueError, match="source changed"):
        calls[public]()


def test_loaded_four_strip_roots_two_flange_wrenches_and_each_strip_balance():
    el = element()
    result = response(el)
    assert len(result["strip_root_actions"]) == 4
    assert set(result["per_flange_applied_strip_root_wrench_about_heel_n_nmm"]) == {"arm-x", "arm-z"}
    assert np.max(abs(np.asarray(result["loaded_root_wrench_minus_source_body_wrench_n_nmm"]))) < 1e-8
    for root, tip in zip(result["strip_root_actions"], result["port_actions"], strict=True):
        wr = method.four.wrench_at(np.asarray(root["applied_to_strip_force_xyz_n"]),
            np.asarray(root["applied_to_strip_couple_at_root_xyz_nmm"]), root["point_xyz_mm"], el.model.origin)
        wt = method.four.wrench_at(np.asarray(tip["external_force_required_at_port_xyz_n"]),
            np.asarray(tip["external_couple_required_at_port_xyz_nmm"]), tip["point_xyz_mm"], el.model.origin)
        assert np.max(abs(wr+wt)) < 1e-8
    unloaded = el.model.response(np.arange(24)*1e-5*el.scale)
    old_roots = sum((method.four.wrench_at(np.asarray(row["applied_to_strip_force_xyz_n"]),
        np.asarray(row["applied_to_strip_moment_at_root_xyz_nmm"]), row["point_xyz_mm"], el.model.origin)
        for row in unloaded["strip_root_actions"]), np.zeros(6))
    assert np.max(abs(old_roots)) < 1e-8
    assert np.linalg.norm(np.asarray(result["load_projection"]["heel_wrench_n_nmm"])-old_roots) > 200.


def test_output_mutation_cannot_change_model_input_or_datums():
    el = element()
    output = response(el)
    output["port_actions"][0]["point_xyz_mm"][0] += 5.
    desc = el.descriptor()
    desc["own_fitting_scenario"]["elastic_modulus_mpa"] = 1.
    assert response(el)["port_actions"][0]["point_xyz_mm"][0] == 65.0875
    assert el.descriptor()["own_fitting_scenario"]["elastic_modulus_mpa"] == 200000.

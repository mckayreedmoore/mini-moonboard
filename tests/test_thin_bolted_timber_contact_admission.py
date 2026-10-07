"""New path/source mutations and small frozen serializer coupons only.

These checks reuse the issued reference geometry; no CAD, candidate mechanics,
global solve, or synthetic admission result is produced.
"""

import copy
import importlib.util
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from scripts import thin_bolted_timber_contact_admission as gate
from scripts import thin_bolted_timber_face_contact as method


@lru_cache(maxsize=1)
def issued_geometry():
    return (json.loads(gate.PROOF.read_bytes()),
            json.loads((gate.PACKET/"native-geometry-v4.json").read_bytes()),
            json.loads((gate.PACKET/"mixed-offset-rows-shallow-wires-v4.json").read_bytes()))


def geometry():
    return copy.deepcopy(issued_geometry())


def parameters():
    return {"timber_face_contact_basis": gate.BASIS,
            "timber_face_contact_geometry_sha256": gate.PROOF_SHA256,
            "timber_face_contact_bedding_n_mm3": 1.,
            "timber_face_contact_scenario_id": method.DEFAULT_SCENARIO_ID,
            "timber_face_contact_cell_mm": 25.,
            "timber_face_contact_producer_sha256": gate.METHOD_SHA256,
            "timber_face_contact_method_receipt_sha256": gate.METHOD_RECEIPT_SHA256}


def test_issued_finished_geometry_census_and_independent_compact_mapping():
    proof, cache, layout = geometry()
    assert gate.original.support.digest(gate.PROOF) == gate.PROOF_SHA256
    census = gate.verify_patch_inventory(proof, cache, layout)
    assert (census["retained_pair_count"], census["source_timber_count"], census["patch_count"],
            census["contact_cell_count"]) == (6, 8, 6, 272)
    assert census["current_projected_footprint_pressure_or_contact_capacity_established"] is False
    expected = gate.expected_contact_descriptors(proof, 1., method.DEFAULT_SCENARIO_ID)
    rows = method.describe_contacts(proof, 1., proof_sha256=gate.PROOF_SHA256)
    assert set(expected) == {row["id"] for row in rows}
    for row in rows:
        gate.original.verify_descriptor_fields(row, expected[row["id"]])
        assert "patch" not in row["source_descriptor"] and "cell" not in row["source_descriptor"]
    field = {"parameters": parameters(), "reference_interaction_descriptors": rows,
             "finite_interaction_actions": copy.deepcopy(rows)}
    gate.verify_contact_source_aliases(field, proof)


@pytest.mark.parametrize("mutation", ["missing_pair", "duplicate_pair", "wrong_host", "missing_patch",
    "duplicate_patch", "duplicate_cell", "area", "point", "occupancy", "source", "face_signature",
    "normal", "region_signature", "grid", "second_moment", "header_count", "retained_axis"])
def test_source_geometry_mutations_fail(mutation):
    proof, cache, layout = geometry()
    patch, cell = proof["patches"][0], proof["patches"][0]["cells"][0]
    if mutation == "missing_pair":
        proof["pairs"].pop()
    elif mutation == "duplicate_pair":
        proof["pairs"][-1] = copy.deepcopy(proof["pairs"][0])
    elif mutation == "wrong_host":
        patch["second"] = "base_header_left"
    elif mutation == "missing_patch":
        proof["patches"].pop()
    elif mutation == "duplicate_patch":
        other = copy.deepcopy(patch); other["id"] += "/duplicate"
        proof["patches"].append(other)
    elif mutation == "duplicate_cell":
        patch["cells"].append(copy.deepcopy(cell))
    elif mutation == "area":
        cell["area_mm2"] += 1.
    elif mutation == "point":
        cell["point_xyz_mm"][0] += .01
    elif mutation == "occupancy":
        cell["both_inward_material_probes_occupied"] = False
    elif mutation == "source":
        proof["sources"][0]["volume_mm3"] += 1.
    elif mutation == "face_signature":
        patch["source_first_face"]["signature"]["area_mm2"] += 1.
    elif mutation == "normal":
        patch["normal_from_second_to_first_xyz"] = [-v for v in patch["normal_from_second_to_first_xyz"]]
    elif mutation == "region_signature":
        patch["trimmed_region_signature_sha256"] = "0"*64
    elif mutation == "grid":
        patch["effective_cell_size_mm"] /= 2.
    elif mutation == "second_moment":
        patch["sampled_centroidal_second_moment_matrix_xyz_mm4"][1][1] += 1.
    elif mutation == "header_count":
        proof["counts"]["cells"] -= 1
    else:
        proof["pairs"][0]["retained_axis_ids"][0] = "foreign-axis"
    with pytest.raises(ValueError):
        gate.verify_patch_inventory(proof, cache, layout)


@pytest.mark.parametrize("mutation", ["basis", "proof", "producer", "receipt", "stiffness", "scenario", "grid"])
def test_contact_parameter_mutations_fail(mutation):
    proof, _, _ = geometry()
    field = {"parameters": parameters()}
    key = {"basis": "basis", "proof": "geometry_sha256", "producer": "producer_sha256",
           "receipt": "method_receipt_sha256", "stiffness": "bedding_n_mm3", "scenario": "scenario_id",
           "grid": "cell_mm"}[mutation]
    field["parameters"]["timber_face_contact_"+key] = {
        "stiffness": 0., "scenario": "", "grid": 50.}.get(mutation, "foreign")
    with pytest.raises(ValueError):
        gate.contact_parameters(field, proof)


@pytest.mark.parametrize("alias", ["geometry_proof_sha256", "cell_area_mm2", "source_first_face",
                                   "both_inward_material_probes_occupied"])
def test_compact_source_alias_mutation_fails(alias):
    proof, _, _ = geometry()
    rows = list(gate.expected_contact_descriptors(proof, 1., method.DEFAULT_SCENARIO_ID).values())
    field = {"parameters": parameters(), "reference_interaction_descriptors": copy.deepcopy(rows),
             "finite_interaction_actions": copy.deepcopy(rows)}
    field["finite_interaction_actions"][0]["source_descriptor"][alias] = "altered"
    with pytest.raises(ValueError, match="compact"):
        gate.verify_contact_source_aliases(field, proof)


@lru_cache(maxsize=1)
def current_coupon():
    """Two small existing mapped bodies, a new law, and all 32 floor corners.

    The synthetic body names are deliberately outside candidate proof pairs;
    only frozen serialization/current-law replay is tested here.
    """
    filename = Path(__file__).with_name("test_thin_bolted_finite_frame.py")
    spec = importlib.util.spec_from_file_location("timber_admission_coupon", filename)
    fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
    potential, _, _ = fixture.small_potential()
    for i in range(32):
        point = [float(i), 0., 0.]
        normal = fixture.descriptor(f"coupon/floor-{i}", "floor_normal", "timber", "floor", point,
                                    [0., 0., 1.], "floor", axial=25000., sign=-1.)
        tangent = fixture.descriptor(normal["id"]+"/finite-no-slip-xy", "floor_tangent_xy", "timber", "floor", point,
                                     [0., 0., 1.], "floor", lateral=25000.)
        tangent.update(floor_support_id=normal["id"], normal_contact_id=normal["id"])
        potential.interactions.extend((normal, tangent))
    direct = fixture.descriptor("coupon/direct-wood", "timber_face_contact", "timber", "shaft/test", [51., 22., 31.],
                                [0., 0., 1.], "shaft/test", axial=1000., sign=-1.)
    direct["source_descriptor"] = {"patch_id": "coupon", "cell_id": "coupon/direct-wood", "cell_area_mm2": 1000.}
    potential.interactions.append(direct)
    q = np.zeros(potential.ndof)
    for node in potential.map["mechanical_bodies"]["timber"]["node_dof_indices"]:
        q[np.asarray(node)[:3]] = [.03, -.02, -5.]
        q[np.asarray(node)[3:]] = [20., -30., 40.]
    result = potential.response(q, False, recover_actions=True)
    disabled = [key for key, value in result["floor_normal_reactions_n"].items() if value <= 1e-7]
    result = potential.response(q, False, recover_actions=True, disabled_floor_support_ids=disabled)
    field = {**potential.case, "response": {"disabled_floor_support_ids": disabled},
             **{key: result[key] for key in ("finite_kinematic_map", "reference_interaction_descriptors", "finite_interaction_actions")}}
    return field, q, {r["id"]: copy.deepcopy(r) for r in potential.interactions}


def test_new_current_pair_serializer_and_zero_rows_use_unchanged_physical_replay():
    field, q, expected = copy.deepcopy(current_coupon())
    result = gate.original.verify_current_actions(field, q, expected)
    assert result["counts"]["timber_face_contact"] == 1
    assert result["counts"]["floor_normal"] == result["counts"]["floor_tangent_xy"] == 32
    row = next(r for r in field["finite_interaction_actions"] if r["kind"] == "timber_face_contact")
    assert row["axial_scalar_force_n"] > 0.
    np.testing.assert_allclose(np.cross(np.array(row["point_on_first_xyz_mm"])-row["point_on_second_xyz_mm"],
        row["force_on_first_xyz_n"])+np.array(row["moment_on_second_at_current_point_xyz_nmm"]), 0., atol=1e-8)
    old_expected = {key: value for key, value in expected.items() if value["kind"] != "timber_face_contact"}
    with pytest.raises(ValueError, match="census"):
        gate.original.verify_current_actions(field, q, old_expected)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "host", "sign", "stiffness", "state", "couple", "force_dual"])
def test_additional_current_contact_mutations_fail(mutation):
    field, q, expected = copy.deepcopy(current_coupon())
    row = next(r for r in field["finite_interaction_actions"] if r["kind"] == "timber_face_contact")
    if mutation == "missing":
        field["finite_interaction_actions"].remove(row)
    elif mutation == "duplicate":
        field["finite_interaction_actions"].append(copy.deepcopy(row))
    elif mutation == "host":
        row["second"] = "timber"
    elif mutation == "sign":
        row["axial_sign"] = 1.
    elif mutation == "stiffness":
        row["axial_stiffness_n_mm"] *= 2.
    elif mutation == "state":
        row["state_id"] = "other"
    elif mutation == "couple":
        row["moment_on_second_at_current_point_xyz_nmm"][0] += 1.
    else:
        row["force_on_second_xyz_n"][0] += 1.
    with pytest.raises(ValueError):
        gate.original.verify_current_actions(field, q, expected)


def test_conflicting_source_graph_cannot_overwrite_frozen_dependency():
    assert gate.merge_pins({"one": "a"}, {"one": "a", "two": "b"}) == {"one": "a", "two": "b"}
    with pytest.raises(ValueError, match="conflicting"):
        gate.merge_pins({"one": "a"}, {"one": "b"})


def proof_field():
    proof, _, _ = geometry()
    receipt = json.loads(gate.METHOD_RECEIPT.read_bytes())
    explicit = {str(gate.PROOF.relative_to(gate.ROOT)): gate.PROOF_SHA256, gate.METHOD: gate.METHOD_SHA256,
                str(gate.METHOD_RECEIPT.relative_to(gate.ROOT)): gate.METHOD_RECEIPT_SHA256}
    return {"parameters": parameters(),
            "source_sha256": gate.merge_pins(explicit, proof["source_sha256"], receipt["source_sha256"])}


def test_actual_proof_and_method_source_graph_authenticates_without_mechanics():
    _, cache, layout = geometry()
    proof, census, bedding, scenario, pins = gate.read_proof(proof_field(), cache, layout)
    assert census["contact_cell_count"] == 272 and len(proof["patches"]) == 6
    assert bedding == 1. and scenario == method.DEFAULT_SCENARIO_ID
    assert pins[gate.METHOD] == gate.METHOD_SHA256


@pytest.mark.parametrize("mutation", ["missing", "wrong"])
def test_extended_field_must_bind_every_contact_proof_and_method_source(mutation):
    _, cache, layout = geometry()
    field = proof_field()
    if mutation == "missing":
        field["source_sha256"].pop(gate.METHOD)
    else:
        field["source_sha256"][gate.METHOD] = "0"*64
    with pytest.raises(ValueError, match="exact proof/method source"):
        gate.read_proof(field, cache, layout)


def test_changed_proof_payload_is_rejected_before_source_or_geometry_use(tmp_path, monkeypatch):
    proof = tmp_path/"proof.json"; proof.write_bytes(gate.PROOF.read_bytes()+b" ")
    monkeypatch.setattr(gate, "PROOF", proof)
    with pytest.raises(ValueError, match="proof changed"):
        gate.read_proof({}, {}, {})


def orchestration():
    return {"source_sha256": {gate.DRIVER: gate.DRIVER_SHA256},
            "execution": {"command": ["python", "-m", "scripts.run_thin_bolted_timber_contact_frame"]},
            "timber_contact_geometry_sha256": gate.PROOF_SHA256}


@pytest.mark.parametrize("mutation", ["driver", "command", "proof"])
def test_new_orchestration_source_module_and_proof_alias_are_required(mutation):
    field = orchestration()
    gate.verify_orchestration(field)
    if mutation == "driver":
        field["source_sha256"][gate.DRIVER] = "0"*64
    elif mutation == "command":
        field["execution"]["command"][2] = "scripts.run_thin_bolted_finite_frame"
    else:
        field["timber_contact_geometry_sha256"] = "0"*64
    with pytest.raises(ValueError):
        gate.verify_orchestration(field)


def test_compact_method_receipt_authenticates_inputs_without_admitting_forces():
    report = gate.method_report()
    assert report["descriptor_count"] == 272
    assert report["source_sha256"][gate.OWN] == gate.LOADED_PRODUCER_SHA256
    assert report["source_sha256"][gate.DRIVER] == gate.DRIVER_SHA256
    assert report["candidate_CAD_K_response_or_force_field_prepared_admitted_or_solved"] is False
    assert gate.SUCCESS not in report
    assert not any(report["release"].values())


def test_original_body_balance_counts_direct_wood_force_and_owned_couple_once():
    field, _, _ = copy.deepcopy(current_coupon())
    row = next(r for r in field["finite_interaction_actions"] if r["kind"] == "timber_face_contact")
    residuals, _, global_value = gate.original.current_balances([row["first"], row["second"]], [], [row], [])
    np.testing.assert_allclose(sum(residuals.values()), 0., atol=1e-8)
    np.testing.assert_array_equal(global_value, 0.)
    assert np.linalg.norm(residuals[row["first"]]) > 0.

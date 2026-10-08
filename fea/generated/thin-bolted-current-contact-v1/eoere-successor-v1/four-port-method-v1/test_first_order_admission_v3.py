"""Two toy shafts with reversed source/JSON order; no candidate preparation."""
import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

PATH = Path(__file__).with_name("first_order_admission_v3.py")
SPEC = importlib.util.spec_from_file_location("eoere_source_order_gate_fixtures", PATH)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)
TOY_SPEC = importlib.util.spec_from_file_location("eoere_order_genuine_toy", PATH.with_name("test_first_order_factory.py"))
toy = importlib.util.module_from_spec(TOY_SPEC)
TOY_SPEC.loader.exec_module(toy)
CHEAP_SPEC = importlib.util.spec_from_file_location("eoere_order_cheap_fixture", PATH.with_name("test_first_order_admission_v2.py"))
cheap = importlib.util.module_from_spec(CHEAP_SPEC)
CHEAP_SPEC.loader.exec_module(cheap)


def reversed_source_toy(tmp_path):
    data, panels, integrated = toy.toy()
    first = data["shafts"][0]
    first.update(body="z-shaft", axis_id="z-axis")
    for load in data["case"]["loads"]:
        if load["body"] == "toy-shaft":
            load["body"] = "z-shaft"
    second = copy.deepcopy(first)
    second.update(body="a-shaft", axis_id="a-axis")
    second["metal_roles"][0]["id"] = "second-toy-bolt"
    data["shafts"].append(second)
    role = second["metal_roles"][0]
    data["case"]["loads"].append({"id": "physical-bolt-metal/"+role["id"], "body": second["body"],
        "point_xyz_mm": role["center_of_mass_xyz_mm"], "force_xyz_n": [0., 0., -role["volume_mm3"]*7850e-9*gate.frame.GRAVITY]})
    p = gate.base.factory.prepare_synthetic(data, panels, integrated)
    pointer = gate.base.bundle.snapshot(p, arrays_path=tmp_path/"toy.npz", manifest_path=tmp_path/"toy.json",
        pins=gate.source_pins(), command=["pure-reversed-source-order-coupon"])
    snapshot = gate.base.bundle.read_snapshot(pointer)
    maps = gate.base.OwnedMaps(snapshot, data)
    q = np.random.default_rng(22).normal(size=p.assembly.ndof)*.02
    fresh = gate.base.replay_original(snapshot, q, ["wood-a"])
    response = {"converged": True, "q": q, "connector_local_force_n": fresh[3], "normal_contact_force_n": fresh[4],
        "nonbearing_no_slip_removed": [], "support_state_search_v1": {"accepted_enabled_centroid_xy_hosts": ["wood-a"]}}
    # Arbitrary-q component recovery only; no equilibrium/admission is asserted.
    field = gate.core.recover(p, response)
    field["source_inputs"] = data
    return field, snapshot, maps, q


def test_genuine_cut_recovery_source_order_differs_from_json_map_and_keeps_all_values(tmp_path):
    field, snapshot, maps, q = reversed_source_toy(tmp_path)
    assert list(maps.shafts) == ["a-shaft", "z-shaft"]
    assert [row["axis_id"] for row in field["common_shaft_section_cut_actions"]] == ["z-axis", "a-axis"]
    before = json.dumps(gate.core.serial(field), sort_keys=True)
    with pytest.raises(ValueError, match="source/guard"):
        gate.corrected.verify_fitting_and_alias_recovery(field, snapshot, maps, q)
    view = gate.source_ordered_maps(field, maps)
    assert list(view.shafts) == ["z-shaft", "a-shaft"]
    assert all(view.shafts[key] is maps.shafts[key] for key in maps.shafts)
    result = gate.verify_fitting_and_alias_recovery(field, snapshot, maps, q)
    assert result["own_signed_external_action_shaft_cut_recoveries_replayed"] == 2
    assert json.dumps(gate.core.serial(field), sort_keys=True) == before
    assert list(maps.shafts) == ["a-shaft", "z-shaft"]
    field["common_shaft_section_cut_actions"][0]["cuts"][-1]["local_N_V1_V2_T_M1_M2_n_nmm"][0] += 1.
    with pytest.raises(ValueError):
        gate.verify_fitting_and_alias_recovery(field, snapshot, maps, q)


@pytest.mark.parametrize("mutation", ["duplicate-body", "duplicate-axis", "missing", "foreign-body", "foreign-axis", "cut-axis", "cut-value"])
def test_owned_axis_and_source_order_controls_reject(tmp_path, mutation):
    field, snapshot, maps, q = reversed_source_toy(tmp_path)
    sources = field["source_inputs"]["shafts"]
    if mutation == "duplicate-body":
        sources[1]["body"] = sources[0]["body"]
    elif mutation == "duplicate-axis":
        sources[1]["axis_id"] = sources[0]["axis_id"]
    elif mutation == "missing":
        sources.pop()
    elif mutation == "foreign-body":
        sources[0]["body"] = "foreign"
    elif mutation == "foreign-axis":
        sources[0]["axis_id"] = "foreign"
    elif mutation == "cut-axis":
        field["common_shaft_section_cut_actions"][0]["axis_id"] = "foreign"
    else:
        field["common_shaft_section_cut_actions"][0]["cuts"][0]["local_N_V1_V2_T_M1_M2_n_nmm"][3] += 1.
    with pytest.raises(ValueError):
        gate.verify_fitting_and_alias_recovery(field, snapshot, maps, q)


def test_new_same_byte_consumer_contract_keeps_genuine_sources_and_rejects_old_order_provenance():
    field = cheap.minimal_pending()
    field["source_sha256"] = gate.source_pins()
    raw = json.dumps(field).encode()
    receipt = cheap.contract_receipt(field, raw)
    receipt.update(source_path=str(gate.OWN.relative_to(gate.frame.ROOT)), admission_source_sha256=gate.LOADED_SHA,
        source_sha256=gate.source_pins(), admission_recovery_order_correction=gate.order_provenance())
    parsed, pins = gate.require_admitted_payload(raw, receipt, admission_sha256=gate.LOADED_SHA)
    assert parsed == field and pins[str(gate.REUSED.relative_to(gate.frame.ROOT))] == gate.REUSED_SHA
    assert "usable_conditional_actions" not in parsed
    for key in ("reused_corrected_gate_sha256", "order_source_path", "cut_values_or_force_tolerances_changed"):
        bad = copy.deepcopy(receipt)
        bad["admission_recovery_order_correction"][key] = "foreign"
        with pytest.raises(ValueError):
            gate.require_admitted_payload(raw, bad, admission_sha256=gate.LOADED_SHA)
    assert Path(gate.corrected.__file__).resolve() == gate.REUSED
    assert Path(gate.base.__file__).resolve() == gate.corrected.ORIGINAL

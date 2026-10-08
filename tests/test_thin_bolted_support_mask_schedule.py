"""Scheduling-only reuse fixtures, with small unchanged fixed-branch mechanics."""

import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from scripts import thin_bolted_support_mask_schedule as schedule
from scripts import thin_bolted_support_state_search as core


def tiny_fixture():
    path = Path(__file__).with_name("test_thin_bolted_support_state_search.py")
    spec = importlib.util.spec_from_file_location("reused_support_search_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.cycling_fixture()


def failed_payload():
    return {"schema": "thin_bolted_common_shaft_frame/v1", "candidate": "synthetic-support-coupon",
        "revision": "fixture", "case_id": "fixture", "accessory_placement": "synthetic",
        "layout_report_sha256": "synthetic-layout", "geometry_cache_sha256": "synthetic-geometry",
        "counts": {"structural_bodies": 2, "dofs": 6}, "gravity": {"declared": True},
        "applied_force_xyz_n": [0., 0., 0.], "applied_moment_about_global_origin_xyz_nmm": [0., 0., 0.],
        "body_applied_loads": [], "body_identities": ["foot-A", "foot-B"],
        "finished_floor_footprints": [{"member": "foot-A"}, {"member": "foot-B"}],
        "parameters": {"floor_corner_contact_n_mm": 25000., "floor_no_slip_xy_penalty_n_mm": 100000.,
            "support_state_search_mask_budget": 2, "lean_case_wall_time_limit_seconds": 1770.},
        "source_sha256": core.source_pins(), "usable_conditional_actions": False,
        "failed_response_without_recovered_actions": True, "compatible_numerical_mvp_complete": False,
        "release": copy.deepcopy(schedule.frame.RELEASE),
        "response": core.compatible_contact_solve(*tiny_fixture(), mask_budget=2)}


def write_payload(tmp_path, report):
    report = copy.deepcopy(report)
    # Serialize the diagnostic vector; it is never put into the schedule.
    if isinstance(report["response"].get("diagnostic_last_q"), np.ndarray):
        report["response"]["diagnostic_last_q"] = report["response"]["diagnostic_last_q"].tolist()
    identity = {key: report[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    report["state_id"] = "thin-v4-" + schedule.canonical_sha256(identity)[:24]
    path = tmp_path / "previous-failed.json"
    path.write_text(json.dumps(report))
    return path, schedule.frame.sha(path), report


def test_authenticated_prior_masks_only_order_fresh_engine_and_find_hand_equilibrium(tmp_path):
    path, digest, previous = write_payload(tmp_path, failed_payload())
    prior = schedule.load_previous_schedule(path, digest)
    assert prior["previous_mask_ids"] == ["centroid-mask-11", "centroid-mask-00"]
    assert prior["previous_field_canonical_sha256"] == schedule.canonical_sha256(previous)
    assert prior["scheduling_only"] and not prior["old_q_or_forces_used"]
    assert "diagnostic_last_q" not in prior and "floor_normal_force_n_by_host" not in prior
    assert prior["source_sha256"][str(path)] == digest
    original_selector = core._next_mask
    events = []
    result = schedule.compatible_contact_solve(*tiny_fixture(), previous_schedule=prior,
                                             mask_budget=4, branch_observer=events.append)
    assert result["converged"]
    assert core._next_mask is original_selector
    diagnostic = result["support_state_search_v1"]
    assert [row["mask_id"] for row in diagnostic["tested_masks"]] == ["centroid-mask-11", "centroid-mask-01", "centroid-mask-10"]
    assert diagnostic["accepted_enabled_centroid_xy_hosts"] == ["foot-A"]
    assert not events[0]["initialization_from_previous_fresh_branch_only"]
    assert result["support_mask_schedule_v1"] == schedule.schedule_metadata(prior)
    assert "source_sha256" not in result["support_mask_schedule_v1"]


def test_selector_deprioritizes_then_reconsiders_prior_masks_and_never_repeats():
    prior = {"previous_host_order": ["A", "B", "C"],
             "previous_mask_ids": ["centroid-mask-111", "centroid-mask-011", "centroid-mask-001"]}
    original = core._next_mask
    with schedule.preferred_unvisited_masks(prior):
        visited = {7}
        number, _ = core._next_mask(7, 6, visited, 8)
        assert number == 5  # Prior demand6 and neighbor6 deferred; next one-host neighbor5.
        seen = [7]
        while number is not None:
            assert number not in visited
            seen.append(number); visited.add(number)
            number, _ = core._next_mask(number, 6, visited, 8)
        assert len(seen) == 8
        assert seen[1:6] == [5, 1, 0, 2, 3]
        assert seen[6:] == [6, 4]
    assert core._next_mask is original


def test_selector_restores_core_on_interruption():
    original = core._next_mask
    with (pytest.raises(RuntimeError, match="synthetic interruption"),
          schedule.preferred_unvisited_masks({"previous_host_order": ["A"], "previous_mask_ids": ["centroid-mask-1"]})):
        raise RuntimeError("synthetic interruption")
    assert core._next_mask is original


@pytest.mark.parametrize("mutation", ["success", "q", "mask", "source", "host", "state", "acceptance", "release"])
def test_prior_reader_rejects_changed_or_ineligible_payloads(tmp_path, mutation):
    report = failed_payload()
    if mutation == "success": report["response"]["converged"] = True
    if mutation == "q": report["response"]["q"] = [0.] * 6
    if mutation == "mask": report["response"]["support_state_search_v1"]["tested_masks"][1]["mask_id"] = "centroid-mask-11"
    if mutation == "source": report["source_sha256"]["scripts/thin_bolted_support_state_search.py"] = "0" * 64
    if mutation == "host": report["finished_floor_footprints"][0]["member"] = "other"
    if mutation == "acceptance": report["usable_conditional_actions"] = True
    if mutation == "release": report["release"]["candidate_accepted"] = True
    path, digest, _ = write_payload(tmp_path, report)
    if mutation == "state":
        data = json.loads(path.read_text()); data["state_id"] = "thin-v4-forged"
        path.write_text(json.dumps(data)); digest = schedule.frame.sha(path)
    with pytest.raises(ValueError): schedule.load_previous_schedule(path, digest)


def test_previous_raw_sha_and_later_bytes_cannot_change(tmp_path):
    path, digest, report = write_payload(tmp_path, failed_payload())
    with pytest.raises(ValueError, match="raw SHA"):
        schedule.load_previous_schedule(path, "0" * 64)
    prior = schedule.load_previous_schedule(path, digest)
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="previous failed payload changed"):
        schedule.validate_current_report(report, prior)


def test_physical_signature_allows_only_declared_numerical_provenance_changes(tmp_path):
    path, digest, report = write_payload(tmp_path, failed_payload())
    prior = schedule.load_previous_schedule(path, digest)
    current = copy.deepcopy(report)
    current["parameters"].update(support_state_search_mask_budget=64,
        support_priority_driver_sha256="new-driver", support_priority_schedule_sha256="new-selector",
        support_mask_schedule_previous_field_sha256=digest, lean_case_wall_time_limit_seconds=1770.)
    schedule.validate_current_report(current, prior)
    for key, change in (("parameters", {**current["parameters"], "floor_corner_contact_n_mm": 25001.}),
                        ("body_applied_loads", [{"body": "foot-A", "force_xyz_n": [1., 0., 0.]}]),
                        ("geometry_cache_sha256", "other-geometry")):
        mutated = copy.deepcopy(current); mutated[key] = change
        with pytest.raises(ValueError, match="unchanged complete physical inputs"):
            schedule.validate_current_report(mutated, prior)


def test_fresh_host_mismatch_and_external_q_are_rejected(tmp_path):
    path, digest, _ = write_payload(tmp_path, failed_payload())
    prior = schedule.load_previous_schedule(path, digest)
    inputs = list(tiny_fixture())
    inputs[3][0]["first"] = "other"
    with pytest.raises(ValueError):
        schedule.compatible_contact_solve(*inputs, previous_schedule=prior, mask_budget=4)
    with pytest.raises(ValueError, match="external q"):
        schedule.compatible_contact_solve(*tiny_fixture(), previous_schedule=prior,
                                         mask_budget=4, warm_q=np.zeros(6))

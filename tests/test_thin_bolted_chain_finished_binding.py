"""Real finished-state identity coupons; no candidate q, forces or body proof."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts import run_thin_bolted_finished_floor as finished
from scripts import run_thin_bolted_support_identity_scope_frame as scoped
from scripts import thin_bolted_joint_post_admission as reducer


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def identity_only_report():
    """Synthetic labels exercise the real binder, without physical action data."""
    report = {
        "case_id": "a12-rear",
        "accessory_placement": "retained-original-top-hold",
        "parameters": {"beam_size_mm": 150.},
        "geometry_cache_sha256": finished.frame.GEOMETRY_CACHE_SHA,
        "source_sha256": {},
        "limits": [],
        "response": {"converged": False, "termination": "identity-only synthetic coupon"},
        "usable_conditional_actions": False,
        "release": dict(finished.frame.RELEASE),
    }
    report["state_id"] = reducer.references.state_identity(report)
    current = {key: report[key] for key in reducer.IDENTITIES}
    for table in (
        "common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions",
        "common_shaft_section_cut_actions", "member_element_actions",
    ):
        report[table] = [{**current, "identity_only_fixture": True,
                          "cuts": [{**current, "identity_only_fixture": True}]}]
    nested = {**current, "identity_only_fixture": True}
    report["contact_actions"] = [{**current, "nested_current_identity": {"rows": [nested]}}]
    # A genuine object alias proves the real binder's visited-object guard.
    report["flange_contact_actions"] = report["contact_actions"][:]
    return report


def history_metadata():
    return {
        "previous_state_id": "thin-v4-historical-leaf",
        "cohorts": [
            {"state_id": "thin-v4-historical-core", "case_id": "a12-rear",
             "accessory_placement": "retained-original-top-hold",
             "policy": "original-core", "local_mask_ids": ["centroid-mask-11111111"]},
            {"state_id": "thin-v4-historical-leaf", "case_id": "a12-rear",
             "accessory_placement": "retained-original-top-hold",
             "policy": "chain", "local_mask_ids": ["centroid-mask-11111111", "centroid-mask-01111111"]},
        ],
        "scheduling_only": True,
        "old_q_or_forces_used": False,
    }


def all_current_labels(value):
    if isinstance(value, dict):
        if "state_id" in value:
            yield value
        for nested in value.values():
            yield from all_current_labels(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from all_current_labels(nested)


def test_real_frozen_binder_reproduces_historical_cohort_collision():
    report = identity_only_report()
    report["response"]["support_mask_chain_schedule_v1"] = history_metadata()
    with pytest.raises(ValueError, match="mixed action identity before finished-support binding"):
        finished.bind_finished_state(report, [], {}, "a" * 64)


def test_real_frozen_binder_relabels_every_nested_current_identity():
    report = identity_only_report()
    old_id = report["state_id"]
    current_case = report["case_id"]
    current_accessory = report["accessory_placement"]
    bound = finished.bind_finished_state(report, [], {}, "a" * 64)
    assert bound is report
    assert bound["state_id"] != old_id
    assert bound["state_id"] == reducer.references.state_identity(bound)
    labels = list(all_current_labels(bound))
    assert len(labels) >= 12
    assert all(row["state_id"] == bound["state_id"] for row in labels)
    assert all(row["case_id"] == current_case and row["accessory_placement"] == current_accessory for row in labels)
    assert bound["contact_actions"][0] is bound["flange_contact_actions"][0]
    assert "q" not in bound["response"]
    assert all("force" not in key and "moment" not in key for row in labels for key in row)
    reducer.timber.verify_alias_state_labels(bound)


@pytest.mark.parametrize("key", reducer.IDENTITIES)
def test_reducer_checks_current_alias_identity_without_visiting_history(key):
    report = identity_only_report()
    report["response"]["support_mask_chain_schedule_v1"] = history_metadata()
    previous = encoded(report["response"]["support_mask_chain_schedule_v1"])
    reducer.timber.verify_alias_state_labels(report)
    assert encoded(report["response"]["support_mask_chain_schedule_v1"]) == previous
    broken = copy.deepcopy(report)
    broken["common_shaft_section_cut_actions"][0]["cuts"][0][key] = "foreign-current-identity"
    with pytest.raises(ValueError, match="alias mixes or omits admitted state/load identity"):
        reducer.timber.verify_alias_state_labels(broken)


def expected_identity(report):
    identity = {key: report[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    return "thin-v4-" + hashlib.sha256(encoded(identity)).hexdigest()[:24]


def scoped_report():
    report = identity_only_report()
    report["parameters"].update({
        "support_mask_schedule_identity_scope_driver_sha256": scoped.LOADED_DRIVER_SHA256,
        # This is an identity-only synthetic receipt digest, not admission.
        "support_mask_schedule_identity_scope_method_receipt_sha256": "6" * 64,
    })
    report["source_sha256"][scoped.OWN] = scoped.LOADED_DRIVER_SHA256
    report["support_identity_scope_execution"] = {"identity_only_fixture": True}
    report["response"][scoped.HISTORY_KEY] = history_metadata()
    return report


def bind_real_scope(report):
    # No binder injection: this calls the actual captured finished binder.
    assert scoped.ORIGINAL_FINISHED_BINDING is finished.bind_finished_state
    return scoped.bind_scoped_finished_state(
        report, [], {}, finished.frame.sha(Path(finished.__file__)))


def test_scope_uses_real_binder_and_preserves_identical_history_and_current_aliases():
    report = scoped_report()
    original_current = report["state_id"]
    original_history = report["response"][scoped.HISTORY_KEY]
    original_history_bytes = encoded(original_history)
    bound = bind_real_scope(report)
    assert bound is report
    assert bound["state_id"] != original_current
    assert bound["state_id"] == expected_identity(bound)
    assert bound["response"][scoped.HISTORY_KEY] is original_history
    assert encoded(original_history) == original_history_bytes
    execution = bound["support_identity_scope_execution"]
    digest = hashlib.sha256(original_history_bytes).hexdigest()
    assert execution["historical_metadata_path"] == "response.support_mask_chain_schedule_v1"
    assert execution["historical_metadata_before_canonical_sha256"] == digest
    assert execution["historical_metadata_after_canonical_sha256"] == digest
    assert execution["historical_metadata_restored_unchanged"] is True
    assert execution["current_action_identities_verified"] is True
    current_only = copy.deepcopy(bound)
    current_only["response"].pop(scoped.HISTORY_KEY)
    identity = tuple(bound[key] for key in reducer.IDENTITIES)
    assert all(tuple(row[key] for key in reducer.IDENTITIES) == identity for row in all_current_labels(current_only))
    assert bound["contact_actions"][0] is bound["flange_contact_actions"][0]
    reducer.timber.verify_alias_state_labels(bound)
    assert "q" not in bound["response"]
    assert bound["response"]["converged"] is False
    assert bound["usable_conditional_actions"] is False
    assert not any(bound["release"].values())


@pytest.mark.parametrize("key", reducer.IDENTITIES)
def test_wrong_deep_current_identity_rejects_with_real_binder_and_restores_history(key):
    report = scoped_report()
    history = report["response"][scoped.HISTORY_KEY]
    before = encoded(history)
    report["contact_actions"][0]["nested_current_identity"]["rows"][0][key] = "foreign-current-identity"
    with pytest.raises(ValueError, match="mixed (action|current) identity"):
        bind_real_scope(report)
    assert report["response"][scoped.HISTORY_KEY] is history
    assert encoded(history) == before
    assert "current_action_identities_verified" not in report["support_identity_scope_execution"]
    assert "q" not in report["response"]


def test_history_exemption_is_only_the_exact_response_subtree():
    report = scoped_report()
    history = report["response"][scoped.HISTORY_KEY]
    before = encoded(history)
    report["unscoped_history_alias"] = history
    with pytest.raises(ValueError, match="mixed action identity"):
        bind_real_scope(report)
    assert report["response"][scoped.HISTORY_KEY] is history
    assert encoded(history) == before


@pytest.mark.parametrize("parameter", [
    "support_mask_schedule_identity_scope_driver_sha256",
    "support_mask_schedule_identity_scope_method_receipt_sha256",
])
def test_new_source_and_method_parameter_pins_change_the_finished_state(parameter):
    first = scoped_report()
    second = copy.deepcopy(first)
    second["parameters"][parameter] = "9" * 64
    before = encoded(first["response"][scoped.HISTORY_KEY])
    left, right = bind_real_scope(first), bind_real_scope(second)
    assert left["state_id"] == expected_identity(left)
    assert right["state_id"] == expected_identity(right)
    assert left["state_id"] != right["state_id"]
    assert encoded(left["response"][scoped.HISTORY_KEY]) == before
    assert encoded(right["response"][scoped.HISTORY_KEY]) == before
    assert "q" not in left["response"] and "q" not in right["response"]


def test_invalid_history_digest_does_not_remove_the_original_subtree():
    report = scoped_report()
    history = report["response"][scoped.HISTORY_KEY]
    # This malformed in-memory history is not an authenticated ancestor.
    history["invalid_fixture_value"] = float("nan")
    with pytest.raises(ValueError, match="Out of range float values"):
        bind_real_scope(report)
    assert report["response"][scoped.HISTORY_KEY] is history
    assert "current_action_identities_verified" not in report["support_identity_scope_execution"]

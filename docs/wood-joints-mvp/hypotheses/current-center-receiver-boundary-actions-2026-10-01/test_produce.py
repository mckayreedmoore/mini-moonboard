"""Focused refusal tests for the center boundary source guards."""

from __future__ import annotations

import hashlib

import produce
import pytest
from boundary import CANDIDATE, FACTORS, REVISION


def _case_fixture():
    case = "a1-rear"
    files = {
        "model": {"sha256": "model-sha"},
        "deck": {"sha256": "deck-sha"},
        "native_data": {"sha256": "dat-sha"},
        "response": {"sha256": "response-sha"},
    }
    model = {"candidate": CANDIDATE, "geometry_revision_id": REVISION, "case_id": case}
    response = {
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "case_id": case,
        "qualified_for_design": False,
        "mechanical_acceptance": False,
        "joint_demand_accepted": False,
        "floor_capacity_established": False,
        "friction_qualified": False,
        "source_input_model_json_sha256": files["model"]["sha256"],
        "source_input_deck_sha256": files["deck"]["sha256"],
        "native_data_sha256": files["native_data"]["sha256"],
        "increments": [
            {"load_factor": factor, **{gate: True for gate in produce.GATES}}
            for factor in FACTORS
        ],
    }
    audit = {
        "status": "PASS_PARENT_ALL_BODY_RESPONSE_SUMS",
        "source_model_sha256": files["model"]["sha256"],
        "source_response_sha256": files["response"]["sha256"],
        "physical_tolerances_N_Nmm": [0.1, 2.0],
        "increments": [{"load_factor": factor} for factor in FACTORS],
    }
    terminal = {
        "conditional_case_forces_usable": True,
        "case_id": case,
        "response_sha256": files["response"]["sha256"],
    }
    return case, files, model, response, audit, terminal


def _assert_case_rejected(args, message):
    with pytest.raises(ValueError, match=message):
        produce.checked_case(*args)


def test_checked_pin_accepts_matching_bytes_and_size(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "source.bin"
    data = b"pinned synthetic source"
    source.write_bytes(data)

    result = produce.checked_pin(
        root,
        {
            "path": "source.bin",
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        },
    )

    assert result == {
        "path": "source.bin",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }


@pytest.mark.parametrize("failure", ("outside_path", "hash", "size"))
def test_checked_pin_refuses_changed_source_binding(tmp_path, failure):
    root = tmp_path / "repo"
    root.mkdir()
    source = root / "source.bin"
    data = b"pinned synthetic source"
    source.write_bytes(data)
    pin = {
        "path": "source.bin",
        "sha256": hashlib.sha256(data).hexdigest(),
        "size_bytes": len(data),
    }

    if failure == "outside_path":
        outside = tmp_path / "outside.bin"
        outside.write_bytes(data)
        pin["path"] = "../outside.bin"
        message = "source path outside repository"
    elif failure == "hash":
        pin["sha256"] = "0" * 64
        message = "source hash changed"
    else:
        pin["size_bytes"] += 1
        message = "source size changed"

    with pytest.raises(ValueError, match=message):
        produce.checked_pin(root, pin)


def test_checked_case_accepts_a_compact_frozen_record():
    args = _case_fixture()

    assert produce.checked_case(*args) is None


@pytest.mark.parametrize(
    ("target", "key", "value"),
    (
        ("model", "candidate", "other-candidate"),
        ("response", "geometry_revision_id", "other-revision"),
        ("response", "case_id", "a12-rear"),
    ),
)
def test_checked_case_refuses_wrong_candidate_revision_or_case(target, key, value):
    args = list(_case_fixture())
    args[2 if target == "model" else 3][key] = value

    _assert_case_rejected(args, "source case/candidate/revision differs")


def test_checked_case_refuses_a_case_argument_that_disagrees_with_sources():
    args = list(_case_fixture())
    args[0] = "a12-rear"

    _assert_case_rejected(args, "source case/candidate/revision differs")


@pytest.mark.parametrize(
    ("target", "key"),
    (
        ("response", "source_input_model_json_sha256"),
        ("response", "source_input_deck_sha256"),
        ("response", "native_data_sha256"),
        ("audit", "source_model_sha256"),
        ("audit", "source_response_sha256"),
        ("terminal", "response_sha256"),
    ),
)
def test_checked_case_refuses_broken_provenance_links(target, key):
    args = list(_case_fixture())
    index = {"response": 3, "audit": 4, "terminal": 5}[target]
    args[index][key] = "different-source-sha"

    message = {
        "response": "response input hash differs",
        "audit": "source all-body audit differs",
        "terminal": "terminal case/response differs",
    }[target]
    _assert_case_rejected(args, message)


@pytest.mark.parametrize("flag", produce.FALSE_FLAGS)
def test_checked_case_refuses_source_qualification_or_release_flags(flag):
    args = list(_case_fixture())
    args[3][flag] = True

    _assert_case_rejected(args, "source qualification boundary changed")


@pytest.mark.parametrize("target", ("response", "audit"))
def test_checked_case_refuses_reordered_seven_state_history(target):
    args = list(_case_fixture())
    increments = args[3 if target == "response" else 4]["increments"]
    increments[0], increments[1] = increments[1], increments[0]

    _assert_case_rejected(args, "source state coverage differs")


@pytest.mark.parametrize("target", ("response", "audit"))
def test_checked_case_refuses_a_mismatched_state_factor(target):
    args = list(_case_fixture())
    index = 3 if target == "response" else 4
    args[index]["increments"][3]["load_factor"] = 0.4

    _assert_case_rejected(args, "source state coverage differs")


@pytest.mark.parametrize("gate", produce.GATES)
def test_checked_case_refuses_a_failed_response_increment_gate(gate):
    args = list(_case_fixture())
    args[3]["increments"][-1][gate] = False

    _assert_case_rejected(args, "source increment gate failed")


@pytest.mark.parametrize(
    "terminal_key",
    ("conditional_case_forces_usable", "response_usable_for_conditional_joint_checks"),
)
def test_checked_case_refuses_an_unusable_terminal_record(terminal_key):
    args = list(_case_fixture())
    args[5].pop("conditional_case_forces_usable", None)
    args[5][terminal_key] = False

    _assert_case_rejected(args, "terminal conditional response unusable")


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("status", "FAIL"),
        ("physical_tolerances_N_Nmm", [1.0, 2.0]),
    ),
)
def test_checked_case_refuses_an_incompatible_all_body_audit(key, value):
    args = list(_case_fixture())
    args[4][key] = value

    _assert_case_rejected(args, "source all-body audit differs")


def _authority_fixture():
    ids = [f"legacy-{index:02}" for index in range(40)]
    ids.extend(f"candidate-{index:02}" for index in range(7))
    criteria = {
        "candidate": CANDIDATE,
        "legacy_criteria": [
            {"legacy_id": key, "status": "pending"} for key in ids[:40]
        ],
        "additional_candidate_obligations": [
            {"id": key, "status": "pending"} for key in ids[40:]
        ],
        "release_flags": {"climbing_release": False, "complete_joint_accepted": False},
    }
    lane = {
        "candidate": CANDIDATE,
        "current_development_revision": {"revision_id": REVISION},
        "release_flags": {"fabrication_release": False, "climbing_release": False},
    }
    return criteria, lane, ids


def test_checked_authority_accepts_only_a_complete_pending_inventory():
    criteria, lane, ids = _authority_fixture()

    result = produce.checked_authority(criteria, lane)

    assert result["criterion_count"] == 47
    assert result["pending_criterion_ids"] == sorted(ids)
    assert result["all_pending"] is True


@pytest.mark.parametrize(
    "failure",
    ("missing_id", "duplicate_id", "nonpending", "criteria_release", "lane_release"),
)
def test_checked_authority_refuses_incomplete_or_released_authority(failure):
    criteria, lane, ids = _authority_fixture()
    if failure == "missing_id":
        criteria["additional_candidate_obligations"].pop()
    elif failure == "duplicate_id":
        criteria["additional_candidate_obligations"][0]["id"] = ids[0]
    elif failure == "nonpending":
        criteria["legacy_criteria"][0]["status"] = "accepted"
    elif failure == "criteria_release":
        criteria["release_flags"]["climbing_release"] = True
    else:
        lane["release_flags"]["fabrication_release"] = True

    with pytest.raises(ValueError):
        produce.checked_authority(criteria, lane)

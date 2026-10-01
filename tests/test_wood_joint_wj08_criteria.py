"""Tests for the WJ-08 evidence boundary; synthetic passes are test-only."""

from __future__ import annotations

import copy
import json
import math
import shutil
from pathlib import Path

import pytest

from scripts.wood_joint_wj08_criteria import (
    ACCEPTANCE_CONTRACT_SCHEMA,
    DEMAND_MANIFEST_SCHEMA,
    EVIDENCE_SCHEMA,
    EXPECTATIONS_SCHEMA,
    CANDIDATE_PATH,
    COVERAGE_PATH,
    CRITERIA_PATH,
    DUTY_REGISTRY_PATH,
    FRAME_MANIFEST_PATH,
    LOAD_CASES_PATH,
    METHOD_MAP_PATH,
    ROOT,
    SOURCE_INVENTORY_PATH,
    TOPOLOGY_PATH,
    CRITERIA_OVERLAY_PATH,
    RECONCILIATION_PATH,
    RECONCILIATION_REVIEW_PATH,
    RECONCILIATION_SCRIPT_PATH,
    RECONCILIATION_README_PATH,
    aggregate_documents,
    build_current_expectations,
    sha256_file,
)


def _binding_map(expectations):
    return {row["binding_id"]: row for row in expectations["source_bindings"]}


def _source_hashes(expectations, binding_ids, extra_paths=()):
    bindings = _binding_map(expectations)
    result = {
        bindings[binding_id]["path"]: bindings[binding_id]["sha256"]
        for binding_id in binding_ids
    }
    for path in extra_paths:
        result[str(path)] = sha256_file(Path(path))
    return result


def _make_fixture(tmp_path, *, static_ids=()):
    source_root = tmp_path / "synthetic-repo"
    for rel in (
        CRITERIA_PATH,
        COVERAGE_PATH,
        METHOD_MAP_PATH,
        CANDIDATE_PATH,
        SOURCE_INVENTORY_PATH,
        DUTY_REGISTRY_PATH,
        FRAME_MANIFEST_PATH,
        LOAD_CASES_PATH,
        TOPOLOGY_PATH,
        CRITERIA_OVERLAY_PATH,
        RECONCILIATION_PATH,
        RECONCILIATION_REVIEW_PATH,
        RECONCILIATION_SCRIPT_PATH,
        RECONCILIATION_README_PATH,
    ):
        destination = source_root / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, destination)
    criteria, coverage, candidate, frame_manifest, expectations, _ = build_current_expectations(source_root)
    expectations = copy.deepcopy(expectations)
    static_ids = set(static_ids)
    inventory = _binding_map(expectations)["source_inventory"]
    topology = _binding_map(expectations)["attachment_topology"]
    cases = _binding_map(expectations)["load_case_contract"]
    frame = _binding_map(expectations)["full_frame_manifest"]
    demand_path = source_root / "synthetic/demand-manifest.json"
    demand_path.parent.mkdir(parents=True, exist_ok=True)
    wrench = {
        "force_xyz": [3.0, -2.0, 1.0],
        "moment_xyz": [8.0, -5.0, 4.0],
        "datum_xyz": [0.0, 0.0, 0.0],
        "units": {"force": "N", "moment": "N*mm", "length": "mm"},
    }
    demand_path.write_text(json.dumps({
        "schema": DEMAND_MANIFEST_SCHEMA,
        "candidate": expectations["candidate"],
        "revision_id": expectations["revision_id"],
        "fresh_current_demands": True,
        "synthetic_fixture_only": True,
        "cases": [{"case_id": "a12-rear", "wrench": wrench}],
    }))
    demand_hash = sha256_file(demand_path)
    acceptance_path = source_root / "synthetic/acceptance-contracts.json"
    contracts = []

    records = []
    for index, row in enumerate(expectations["criteria"]):
        criterion_id = row["criterion_id"]
        is_static = criterion_id in static_ids
        scope_id = f"{criterion_id}:static-geometry" if is_static else f"{criterion_id}:station-interface-case"
        if is_static:
            member_binding = frame
            cell = {
                "scope_id": scope_id,
                "station_id": None,
                "interface_id": None,
                "case_id": None,
                "entity_ids": [{"kind": "member_id", "id": "base_floor_left"}],
                "static_scope_reason": "The criterion subcheck is a source-bound identity/geometry check with no load demand.",
                "authoritative_ids": [
                    {
                        "binding_id": member_binding["binding_id"],
                        "kind": "member_id",
                        "value": "base_floor_left",
                        "json_pointer": "/physical_members/0/member_id",
                    }
                ],
            }
        else:
            cell = {
                "scope_id": scope_id,
                "station_id": "clip_single_top_left_1",
                "interface_id": "pair:base_floor_left|base_post_outer_left",
                "case_id": "a12-rear",
                "demand_source": {
                    "binding_id": "synthetic_demand",
                    "json_pointer": "/cases/0",
                },
                "entity_ids": [],
                "authoritative_ids": [
                    {
                        "binding_id": inventory["binding_id"],
                        "kind": "station_id",
                        "value": "clip_single_top_left_1",
                        "json_pointer": "/legacy_duties/0/legacy_station_id",
                    },
                    {
                        "binding_id": topology["binding_id"],
                        "kind": "interface_id",
                        "value": "pair:base_floor_left|base_post_outer_left",
                        "json_pointer": "/contact_pair_catalog/0/pair_id",
                    },
                    {
                        "binding_id": cases["binding_id"],
                        "kind": "case_id",
                        "value": "a12-rear",
                        "json_pointer": "/cases/0/case_id",
                    },
                ],
            }
        cell["acceptance_contract_source"] = {
            "binding_id": "synthetic_acceptance",
            "json_pointer": f"/contracts/{index}",
        }
        contracts.append({
            "candidate": expectations["candidate"],
            "revision_id": expectations["revision_id"],
            "criterion_id": criterion_id,
            "scope_id": scope_id,
            "method_id": "synthetic-boundary-example",
            "version": "test-1",
            "scope": "synthetic only; no engineering method or capacity asserted",
            "comparison": "<=",
            "limit": 1.0,
            "unit": "ratio",
        })
        row["applicability"] = "applicable"
        row.pop("reason", None)
        row["scope_cells"] = [cell]
        row["covers_obligation_ids"] = []
        record = {
            "criterion_id": criterion_id,
            "scope_id": scope_id,
            "candidate": expectations["candidate"],
            "revision_id": expectations["revision_id"],
            "coverage": {
                key: cell[key]
                for key in ("station_id", "interface_id", "case_id", "entity_ids", "static_scope_reason")
                if key in cell
            },
            "method": {
                "method_id": "synthetic-boundary-example",
                "version": "test-1",
                "scope": "synthetic only; no engineering method or capacity asserted",
                "source_path": "synthetic/acceptance-contracts.json",
                "source_sha256": "",
            },
            "status": "passed_under_recorded_assumptions",
            "result": 0.5,
            "limit": 1.0,
            "comparison": "<=",
            "result_unit": "ratio",
            "limit_unit": "ratio",
            "governing_mode": "synthetic mode",
            "governing_case_id": None if is_static else "a12-rear",
            "simultaneous_demand": None if is_static else {
                "case_id": "a12-rear",
                "source_binding_id": "synthetic_demand",
                "source_path": "synthetic/demand-manifest.json",
                "source_sha256": demand_hash,
                "source_json_pointer": "/cases/0",
                "wrench": wrench,
            },
            "known_limits": ["Synthetic test fixture only; not engineering evidence."],
            "source_hashes": _source_hashes(
                expectations,
                {
                    "criteria_register",
                    "coverage_plan",
                    "candidate_authority",
                    "full_frame_manifest",
                    "source_inventory" if not is_static else "full_frame_manifest",
                    "attachment_topology" if not is_static else "full_frame_manifest",
                    "load_case_contract" if not is_static else "full_frame_manifest",
                },
            ),
        }
        records.append(record)
    acceptance_path.parent.mkdir(parents=True, exist_ok=True)
    acceptance_path.write_text(json.dumps({
        "schema": ACCEPTANCE_CONTRACT_SCHEMA,
        "synthetic_fixture_only": True,
        "contracts": contracts,
    }, indent=2) + "\n")
    acceptance_hash = sha256_file(acceptance_path)
    demand_binding = {
        "binding_id": "synthetic_demand",
        "path": "synthetic/demand-manifest.json",
        "sha256": demand_hash,
        "role": "independent_demand_manifest",
    }
    acceptance_binding = {
        "binding_id": "synthetic_acceptance",
        "path": "synthetic/acceptance-contracts.json",
        "sha256": acceptance_hash,
        "role": "independent_acceptance_manifest",
    }
    expectations["source_bindings"].extend([acceptance_binding, demand_binding])
    for record in records:
        record["method"]["source_sha256"] = acceptance_hash
        record["source_hashes"][acceptance_binding["path"]] = acceptance_hash
        for binding_id in (
            "criteria_source_overlay",
            "method_map_reconciliation",
            "method_map_reconciliation_review",
        ):
            binding = _binding_map(expectations)[binding_id]
            record["source_hashes"][binding["path"]] = binding["sha256"]
        if record["simultaneous_demand"] is not None:
            record["source_hashes"][demand_binding["path"]] = demand_hash
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "candidate": expectations["candidate"],
        "revision_id": expectations["revision_id"],
        "producer": {"name": "pytest synthetic fixture", "version": "test-only"},
        "synthetic_fixture": True,
        "synthetic_fixture_ack": "TEST_ONLY_NOT_ENGINEERING_EVIDENCE",
        "records": records,
    }
    fixture = (criteria, coverage, candidate, frame_manifest, expectations, source_root, evidence)
    _authorize_synthetic_overlay(fixture)
    return fixture


def _aggregate(fixture):
    criteria, coverage, candidate, frame_manifest, expectations, source_root, evidence = fixture
    return aggregate_documents(
        criteria,
        coverage,
        candidate,
        frame_manifest,
        expectations,
        evidence,
        source_root=source_root,
        expectation_sha256="synthetic-expectation-digest",
    )


def _rewrite_bound_document(fixture, binding_id, document):
    expectations = fixture[4]
    source_root = fixture[5]
    binding = _binding_map(expectations)[binding_id]
    path = source_root / binding["path"]
    path.write_text(json.dumps(document, indent=2) + "\n")
    new_hash = sha256_file(path)
    binding["sha256"] = new_hash
    for record in fixture[-1]["records"]:
        if binding["path"] in record.get("source_hashes", {}):
            record["source_hashes"][binding["path"]] = new_hash


def _authorize_synthetic_overlay(fixture):
    """Create an isolated test-only copy of the coordinator-reviewed state."""
    expectations = fixture[4]
    source_root = fixture[5]
    bindings = _binding_map(expectations)
    review = {
        "schema": "wood_joint_parent_review/v1",
        "synthetic_fixture_only": True,
        "reviewer": "/root",
        "artifact": "current-criteria-method-map-reconciliation-attempt02",
        "status": "PASS_SOURCE_PROVENANCE_RECONCILIATION_ONLY",
        "reviewed_hashes": {
            "reconcile.py": sha256_file(source_root / bindings["method_map_reconciliation_script"]["path"]),
            "README.md": sha256_file(source_root / bindings["method_map_reconciliation_readme"]["path"]),
            "source-reconciliation.json": sha256_file(source_root / bindings["method_map_reconciliation"]["path"]),
        },
        "independent_checks": {
            "all_reproducer_checks_pass": True,
            "frozen_coverage_unchanged": True,
            "old_method_map_digest_matches_embedded_pin": True,
            "current_method_map_matches_reviewed_working_tree_bytes": True,
            "changed_rows_match_reviewed_scope": True,
            "all_47_criterion_ids_preserved": True,
            "no_criterion_dispositions_established": True,
        },
        "review_scope": "Synthetic test fixture only; provenance mechanics test data, not an actual coordinator review.",
    }
    _rewrite_bound_document(fixture, "method_map_reconciliation_review", review)
    overlay_binding = bindings["criteria_source_overlay"]
    overlay_path = source_root / overlay_binding["path"]
    overlay = json.loads(overlay_path.read_text())
    overlay["coordinator_review"].update({
        "sha256": bindings["method_map_reconciliation_review"]["sha256"],
        "reviewer": review["reviewer"],
        "status": review["status"],
    })
    _rewrite_bound_document(fixture, "criteria_source_overlay", overlay)


def test_synthetic_positive_fixture_aggregates_47_only_as_test_evidence(tmp_path):
    result = _aggregate(_make_fixture(tmp_path))

    assert result["criterion_count"] == 47
    assert result["disposition_counts"]["conditional_pass"] == 47
    assert result["evidence_synthetic_fixture_only"] is True
    assert result["engineering_mvp_complete"] is False
    assert result["source_overlay_validation"]["accepted"] is True
    assert result["source_overlay_validation"]["status"] == "accepted_provenance_only"
    assert result["source_overlay_validation"]["coordinator_review_status"] == "PASS_SOURCE_PROVENANCE_RECONCILIATION_ONLY"
    assert result["release_flags"] == {
        "engineering_mvp_complete": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "climbing_released": False,
    }


def test_static_geometry_scope_can_pass_without_load_case(tmp_path):
    fixture = _make_fixture(tmp_path, static_ids={"all_machining_represented"})
    result = _aggregate(fixture)
    row = next(item for item in result["criteria"] if item["criterion_id"] == "all_machining_represented")

    assert row["status"] == "conditional_pass"
    assert row["reasons"] == []


@pytest.mark.parametrize(
    "mutation,reason_fragment",
    [
        ("nan", "finite"),
        ("stale_hash", "stale"),
        ("missing_row", "missing evidence"),
        ("duplicate_row", "duplicate"),
        ("missing_demand", "simultaneous-demand"),
        ("wrong_revision", "revision"),
        ("producer_coverage", "producer evidence cannot supply independent coverage"),
    ],
)
def test_invalid_or_incomplete_evidence_never_passes(tmp_path, mutation, reason_fragment):
    fixture = _make_fixture(tmp_path)
    evidence = fixture[-1]
    first = evidence["records"][0]
    if mutation == "nan":
        first["result"] = math.nan
    elif mutation == "stale_hash":
        first["source_hashes"]["docs/wood-joints-mvp/criteria.json"] = "0" * 64
    elif mutation == "missing_row":
        evidence["records"].pop(0)
    elif mutation == "duplicate_row":
        evidence["records"].append(copy.deepcopy(first))
    elif mutation == "missing_demand":
        first["simultaneous_demand"] = None
    elif mutation == "wrong_revision":
        first["revision_id"] = "stale-revision"
    elif mutation == "producer_coverage":
        first["expected_coverage"] = {"case_ids": []}
    result = _aggregate(fixture)
    row = next(item for item in result["criteria"] if item["criterion_id"] == first["criterion_id"])

    assert row["status"] == "pending"
    assert row["reasons"]
    assert any(reason_fragment in reason.lower() for reason in row["reasons"])


@pytest.mark.parametrize(
    "mutation,reason_fragment",
    [
        ("method", "producer method_id differs"),
        ("limit", "producer limit differs"),
    ],
)
def test_producer_cannot_self_author_method_or_acceptance_limit(tmp_path, mutation, reason_fragment):
    fixture = _make_fixture(tmp_path)
    record = fixture[-1]["records"][0]
    if mutation == "method":
        record["method"]["method_id"] = "producer-selected-permissive-method"
    else:
        record["limit"] = 1_000_000.0
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "pending"
    assert any(reason_fragment in reason for reason in result["criteria"][0]["reasons"])


def test_producer_cannot_rebind_demand_path_or_hash(tmp_path):
    fixture = _make_fixture(tmp_path)
    source_root = fixture[5]
    record = fixture[-1]["records"][0]
    rogue_path = source_root / "synthetic/rogue-demand-manifest.json"
    expected_demand = record["simultaneous_demand"]
    rogue_manifest = {
        "schema": DEMAND_MANIFEST_SCHEMA,
        "candidate": fixture[4]["candidate"],
        "revision_id": fixture[4]["revision_id"],
        "fresh_current_demands": True,
        "synthetic_fixture_only": True,
        "cases": [{"case_id": expected_demand["case_id"], "wrench": expected_demand["wrench"]}],
    }
    rogue_path.write_text(json.dumps(rogue_manifest))
    rogue_hash = sha256_file(rogue_path)
    record["simultaneous_demand"]["source_path"] = "synthetic/rogue-demand-manifest.json"
    record["simultaneous_demand"]["source_sha256"] = rogue_hash
    record["source_hashes"]["synthetic/rogue-demand-manifest.json"] = rogue_hash
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "pending"
    assert any("differs from the independent demand binding" in reason for reason in result["criteria"][0]["reasons"])


def test_empty_independent_scope_does_not_borrow_producer_coverage(tmp_path):
    fixture = _make_fixture(tmp_path)
    fixture[4]["criteria"][0]["scope_cells"] = []
    fixture[-1]["records"][0]["expected_coverage"] = fixture[-1]["records"][0]["coverage"]
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "pending"
    assert any("empty independent scope" in reason for reason in result["criteria"][0]["reasons"])


def test_empty_evidence_record_never_passes(tmp_path):
    fixture = _make_fixture(tmp_path)
    fixture[-1]["records"] = [{}]
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "pending"
    assert any("no criterion_id" in reason for reason in result["criteria"][0]["reasons"])


def test_valid_failure_stays_failed_even_if_other_scopes_are_missing(tmp_path):
    fixture = _make_fixture(tmp_path)
    record = fixture[-1]["records"][0]
    record["result"] = 1.2
    record["status"] = "failed"
    fixture[-1]["records"].pop(1)
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "failed"


def test_not_applicable_requires_a_sourced_replacement_obligation(tmp_path):
    fixture = _make_fixture(tmp_path)
    expectations = fixture[4]
    first = expectations["criteria"][0]
    replacement = expectations["criteria"][1]
    obligation = "legacy_duty:clip_single_top_left_1"
    first.update({
        "applicability": "not_applicable",
        "scope_cells": [],
        "not_applicable_reason": "This source-specific subcheck is replaced by its named retained load-path criterion.",
        "replacement_criterion_ids": [replacement["criterion_id"]],
        "preserved_obligation_ids": [obligation],
        "preserved_obligation_sources": [{
            "obligation_id": obligation,
            "binding_id": "source_inventory",
            "json_pointer": "/legacy_duties/*/legacy_station_id",
            "value": "clip_single_top_left_1",
        }],
    })
    replacement["covers_obligation_ids"] = [obligation]
    na = {
        "criterion_id": first["criterion_id"],
        "candidate": expectations["candidate"],
        "revision_id": expectations["revision_id"],
        "status": "not_applicable_with_reason",
        "not_applicable_reason": first["not_applicable_reason"],
        "preserved_obligation_ids": [obligation],
        "source_hashes": _source_hashes(expectations, {
            "criteria_register", "coverage_plan", "candidate_authority", "full_frame_manifest", "source_inventory",
            "criteria_source_overlay", "method_map_reconciliation", "method_map_reconciliation_review"
        }),
    }
    fixture[-1]["records"][0] = na
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "not_applicable_with_reason"

    replacement["covers_obligation_ids"] = []
    blocked = _aggregate(fixture)
    assert blocked["criteria"][0]["status"] == "pending"
    assert any("drop" in reason for reason in blocked["criteria"][0]["reasons"])


def test_default_current_inventory_is_all_pending():
    criteria, coverage, candidate, frame_manifest, expectations, evidence = build_current_expectations(ROOT)
    result = aggregate_documents(
        criteria,
        coverage,
        candidate,
        frame_manifest,
        expectations,
        evidence,
        source_root=ROOT,
    )

    assert expectations["schema"] == EXPECTATIONS_SCHEMA
    assert result["criterion_count"] == 47
    assert result["disposition_counts"] == {
        "conditional_pass": 0,
        "failed": 0,
        "not_applicable_with_reason": 0,
        "pending": 47,
    }
    assert result["engineering_mvp_complete"] is False
    assert all(row["status"] == "pending" for row in result["criteria"])
    if result["source_overlay_validation"]["accepted"]:
        assert all(
            not any("stale against its method map" in reason for reason in row["reasons"])
            for row in result["criteria"]
        )
    else:
        assert result["source_overlay_validation"]["coordinator_review_status"] == "PENDING_COORDINATOR_REVIEW"
        assert all(any("coordinator review status" in reason for reason in row["reasons"]) for row in result["criteria"])
    assert any("no reviewed wj-07/wj-08" in reason.lower() for reason in result["criteria"][0]["reasons"])


def test_current_overlay_is_versioned_to_exact_working_tree_map_bytes():
    _, coverage, _, _, expectations, _ = build_current_expectations(ROOT)
    bindings = _binding_map(expectations)
    overlay = json.loads((ROOT / bindings["criteria_source_overlay"]["path"]).read_text())

    assert bindings["criteria_source_overlay"]["path"].endswith("current-criteria-overlay-attempt02/source-overlay.json")
    assert bindings["method_map"]["sha256"] == "2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7"
    assert overlay["method_map"]["current_sha256"] == bindings["method_map"]["sha256"]
    assert coverage["source_criteria"]["method_map_sha256"] == "1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80"


def test_synthetic_current_overlay_accepts_exact_reviewed_working_tree_bytes(tmp_path):
    result = _aggregate(_make_fixture(tmp_path))

    assert result["source_overlay_validation"]["accepted"] is True
    assert result["source_overlay_validation"]["current_method_map_sha256"] == "2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7"
    assert result["source_overlay_validation"]["historical_method_map_sha256"] == "1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80"


def test_method_map_bytes_that_differ_from_reviewed_pin_are_rejected(tmp_path):
    fixture = _make_fixture(tmp_path)
    expectations = fixture[4]
    source_root = fixture[5]
    binding = _binding_map(expectations)["method_map"]
    map_path = source_root / binding["path"]
    map_path.write_bytes(map_path.read_bytes() + b"\n")
    binding["sha256"] = sha256_file(map_path)
    for record in fixture[-1]["records"]:
        if binding["path"] in record.get("source_hashes", {}):
            record["source_hashes"][binding["path"]] = binding["sha256"]

    result = _aggregate(fixture)

    assert result["source_overlay_validation"]["accepted"] is False
    assert result["criteria"][0]["status"] == "pending"
    assert any("immutable reviewed working-tree pin" in reason for reason in result["criteria"][0]["reasons"])


def test_changed_frozen_coverage_bytes_are_rejected_even_with_updated_binding(tmp_path):
    fixture = _make_fixture(tmp_path)
    expectations = fixture[4]
    source_root = fixture[5]
    binding = _binding_map(expectations)["coverage_plan"]
    coverage_path = source_root / binding["path"]
    coverage_path.write_bytes(coverage_path.read_bytes() + b"\n")
    binding["sha256"] = sha256_file(coverage_path)
    for record in fixture[-1]["records"]:
        if binding["path"] in record.get("source_hashes", {}):
            record["source_hashes"][binding["path"]] = binding["sha256"]

    result = _aggregate(fixture)

    assert result["source_overlay_validation"]["accepted"] is False
    assert result["criteria"][0]["status"] == "pending"
    assert any("immutable reviewed pin" in reason for reason in result["criteria"][0]["reasons"])


def test_frozen_coverage_source_is_still_byte_identical_to_pinned_digest():
    assert sha256_file(ROOT / COVERAGE_PATH) == "c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c"


@pytest.mark.parametrize(
    "mutation,reason_fragment",
    [
        ("current_map_hash", "source overlay current method-map hash"),
        ("coverage_digest", "source overlay frozen coverage digest"),
        ("reconciliation_hash", "source overlay reconciliation hash"),
        ("review_status", "source overlay reviewer status"),
    ],
)
def test_invalid_source_overlay_never_suppresses_stale_pin_failure(tmp_path, mutation, reason_fragment):
    fixture = _make_fixture(tmp_path)
    expectation = fixture[4]
    overlay_binding = _binding_map(expectation)["criteria_source_overlay"]
    overlay_path = fixture[5] / overlay_binding["path"]
    overlay = json.loads(overlay_path.read_text())
    if mutation == "current_map_hash":
        overlay["method_map"]["current_sha256"] = overlay["method_map"]["historical_sha256"]
    elif mutation == "coverage_digest":
        overlay["frozen_coverage"]["sha256"] = "0" * 64
    elif mutation == "reconciliation_hash":
        overlay["reconciliation"]["sha256"] = "0" * 64
    elif mutation == "review_status":
        overlay["coordinator_review"]["status"] = "PENDING_COORDINATOR_REVIEW"
    _rewrite_bound_document(fixture, "criteria_source_overlay", overlay)

    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "pending"
    assert result["source_overlay_validation"]["accepted"] is False
    assert any("stale against its method map" in reason for reason in result["criteria"][0]["reasons"])
    assert any(reason_fragment in reason for reason in result["criteria"][0]["reasons"])


def test_missing_source_overlay_binding_keeps_frozen_pin_pending(tmp_path):
    fixture = _make_fixture(tmp_path)
    fixture[4]["source_bindings"] = [
        row for row in fixture[4]["source_bindings"]
        if row["binding_id"] != "criteria_source_overlay"
    ]
    result = _aggregate(fixture)

    assert result["criteria"][0]["status"] == "pending"
    assert result["source_overlay_validation"]["accepted"] is False
    assert any("stale against its method map" in reason for reason in result["criteria"][0]["reasons"])
    assert any("requires independent criteria_source_overlay" in reason for reason in result["criteria"][0]["reasons"])

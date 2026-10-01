from __future__ import annotations

import copy
import math

import pytest

from scripts import build_current_timber_cut_yield_scenario_attempt02 as hardened


def _sources() -> dict:
    sources, _ = hardened._load_pinned_sources()
    return sources


def test_both_source_revision_identifiers_are_checked() -> None:
    sources = _sources()
    schedule = copy.deepcopy(sources["block_schedule"])
    revision = copy.deepcopy(sources["revision"])

    schedule["geometry_revision_id"] = "other-revision"
    with pytest.raises(ValueError, match="schedule geometry_revision_id"):
        hardened.validate_revision_identity(schedule, revision)

    schedule["geometry_revision_id"] = hardened.REVISION_ID
    revision["revision_id"] = "other-revision"
    with pytest.raises(ValueError, match="revision source revision_id"):
        hardened.validate_revision_identity(schedule, revision)


def test_attempt01_and_attempt02_verification_require_every_expected_field() -> None:
    sources = _sources()
    v1_packet = hardened.ROOT / hardened.ATTEMPT01_PACKET_REL
    v1_report = sources["attempt01_report"]
    v1_report_bytes = (v1_packet / hardened.ATTEMPT01_REPORT_NAME).read_bytes()
    v1_verification = sources["attempt01_verification"]
    hardened.validate_attempt01_verification(
        v1_report, v1_report_bytes, v1_verification
    )

    for field, replacement in (
        ("schema", "contradictory-schema"),
        ("source_pins_status", "FAIL"),
        ("source_count", 0),
        ("source_pins", []),
        ("scenario_inputs_sha256", "0" * 64),
        ("report_sha256", "0" * 64),
        ("scenario_count", 0),
        ("blank_count", 0),
        ("physical_or_purchase_claims", True),
    ):
        mutated = copy.deepcopy(v1_verification)
        mutated[field] = replacement
        with pytest.raises(ValueError, match="complete expected record"):
            hardened.validate_attempt01_verification(
                v1_report, v1_report_bytes, mutated
            )

    report = hardened.build_report()
    report_bytes = hardened._json_bytes(report)
    v2_verification = hardened.expected_verification(report, report_bytes)
    hardened.validate_verification(report, report_bytes, v2_verification)
    mutated_v2 = copy.deepcopy(v2_verification)
    mutated_v2["physical_or_purchase_claims"] = True
    with pytest.raises(ValueError, match="complete expected record"):
        hardened.validate_verification(report, report_bytes, mutated_v2)


@pytest.mark.parametrize("bad_value", [math.nan, math.inf, -math.inf])
def test_nonfinite_scenario_stock_kerf_and_trim_inputs_fail(bad_value: float) -> None:
    sources = _sources()
    scenario_inputs = copy.deepcopy(sources["attempt01_scenario_inputs"])

    scenario_inputs["stock_length_options"][0]["published_lengths_ft"][0] = bad_value
    with pytest.raises(ValueError, match="finite"):
        hardened.validate_numeric_inputs(sources["block_schedule"], scenario_inputs)

    scenario_inputs = copy.deepcopy(sources["attempt01_scenario_inputs"])
    scenario_inputs["cut_loss_scenarios"][0]["kerf_mm"] = bad_value
    with pytest.raises(ValueError, match="finite"):
        hardened.validate_numeric_inputs(sources["block_schedule"], scenario_inputs)

    scenario_inputs = copy.deepcopy(sources["attempt01_scenario_inputs"])
    scenario_inputs["cut_loss_scenarios"][0]["end_trim_per_arithmetic_bin_mm"] = (
        bad_value
    )
    with pytest.raises(ValueError, match="finite"):
        hardened.validate_numeric_inputs(sources["block_schedule"], scenario_inputs)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("proposed_blank_stock_length_mm", math.nan),
        ("proposed_blank_cross_section_mm", [88.9, math.inf]),
    ],
)
def test_nonfinite_source_blank_length_and_section_fail(
    field: str, bad_value: object
) -> None:
    sources = _sources()
    schedule = copy.deepcopy(sources["block_schedule"])
    schedule["candidate_block_records"][0][field] = bad_value
    with pytest.raises(ValueError, match="finite"):
        hardened.validate_numeric_inputs(schedule, sources["attempt01_scenario_inputs"])


@pytest.mark.parametrize(
    "stock,kerf,trim",
    [
        (math.nan, 3.2, 0.0),
        (100.0, math.inf, 0.0),
        (100.0, 3.2, -math.inf),
    ],
)
def test_nonfinite_packer_inputs_fail_before_arithmetic(
    stock: float, kerf: float, trim: float
) -> None:
    blanks = [
        {
            "part_id": "test_blank",
            "proposed_blank_length_mm": 40.0,
            "proposed_blank_cross_section_mm": [88.9, 88.9],
        }
    ]
    with pytest.raises(ValueError, match="finite"):
        hardened.checked_pack_arithmetic_group(blanks, stock, kerf, trim)


@pytest.mark.parametrize(
    "length,section",
    [
        (math.nan, [88.9, 88.9]),
        (40.0, [88.9, math.inf]),
    ],
)
def test_nonfinite_packer_blank_length_or_section_fails(
    length: float, section: list[float]
) -> None:
    blanks = [
        {
            "part_id": "test_blank",
            "proposed_blank_length_mm": length,
            "proposed_blank_cross_section_mm": section,
        }
    ]
    with pytest.raises(ValueError, match="finite"):
        hardened.checked_pack_arithmetic_group(blanks, 100.0, 3.2, 0.0)


def test_attempt04_manifest_requires_24_unique_block_ids() -> None:
    sources = _sources()
    schedule_rows = sources["block_schedule"]["candidate_block_records"]
    manifest_rows = sources["manifest"]["candidate_blocks"]
    hardened.validate_manifest_block_ids(schedule_rows, manifest_rows)

    duplicate = copy.deepcopy(manifest_rows)
    duplicate[-1]["part_id"] = duplicate[0]["part_id"]
    with pytest.raises(ValueError, match="exactly 24 unique block IDs"):
        hardened.validate_manifest_block_ids(schedule_rows, duplicate)

    extra_duplicate = copy.deepcopy(manifest_rows)
    extra_duplicate.append(copy.deepcopy(extra_duplicate[0]))
    with pytest.raises(ValueError, match="exactly 24 unique block IDs"):
        hardened.validate_manifest_block_ids(schedule_rows, extra_duplicate)


def test_attempt02_reproduces_all_30_arithmetic_scenarios_and_claim_limits() -> None:
    report = hardened.build_report()
    v1 = _sources()["attempt01_report"]

    assert report["scenario_result_count"] == 30
    assert report["scenarios"] == v1["scenarios"]
    assert report["inventory_reconciliation"] == v1["inventory_reconciliation"]
    assert report["packing_policy"] == v1["packing_policy"]
    assert report["claim_boundary"] == v1["claim_boundary"]
    assert report["validation_closure"] == {
        "source_yield_and_revision_source_ids_checked": True,
        "complete_attempt01_verification_compared": True,
        "finite_numeric_inputs_required": True,
        "attempt04_manifest_exactly_24_unique_ids_required": True,
    }


def test_stored_attempt02_verification_and_report_pass_packet_check() -> None:
    verification = hardened.verify_packet()
    assert verification["source_count"] == 14
    assert verification["scenario_count"] == 30
    assert verification["blank_count"] == 24

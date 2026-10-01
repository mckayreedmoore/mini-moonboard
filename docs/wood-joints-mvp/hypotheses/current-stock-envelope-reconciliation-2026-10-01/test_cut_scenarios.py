"""Behavior checks for joining current stock geometry and cut arithmetic."""

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location(
    "stock_cut_scenarios", HERE / "cut_scenarios.py"
)
cuts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cuts)


@pytest.fixture
def sources():
    inventory = {"parts": []}
    manifest = {
        "candidate": cuts.CANDIDATE,
        "geometry_revision_id": cuts.REVISION,
        "candidate_blocks": [],
        "physical_members": [],
    }
    proposals = {
        "candidate": cuts.CANDIDATE,
        "geometry_revision_id": cuts.REVISION,
        "candidate_block_records": [],
    }
    for i in range(20):
        name = f"frame-{i:02}"
        inventory["parts"].append(
            {
                "part_id": name,
                "kind": "timber",
                "source_blank_dimensions_mm": [2500.0, 139.7, 38.1],
                "actual_source_section_mm": [38.1, 139.7],
            }
        )
        manifest["physical_members"].append(
            {
                "member_id": name,
                "composition_roles": ["source_inventory_member"]
                + (["current_rebuilt_host"] if i >= 4 else []),
                "current_finished_step_binding": {
                    "path": f"solids/{name}.step",
                    "file_sha256": "f" * 64,
                },
            }
        )
    for i in range(24):
        name = f"block-{i:02}"
        manifest["candidate_blocks"].append({"part_id": name})
        manifest["physical_members"].append(
            {
                "member_id": name,
                "composition_roles": ["candidate_block"],
                "current_finished_step_binding": {
                    "path": f"solids/{name}.step",
                    "file_sha256": "f" * 64,
                },
            }
        )
        proposals["candidate_block_records"].append(
            {
                "part_id": name,
                "proposed_stock_class": "4x6" if i < 4 else "4x4",
                "proposed_blank_stock_length_mm": 139.0 if i < 4 else 119.7,
                "proposed_blank_cross_section_mm": (
                    [83.9, 139.7] if i < 2 else [88.9, 133.35]
                )
                if i < 4
                else [88.9, 88.9],
            }
        )
    return inventory, manifest, proposals


def envelope_for(expected):
    rows = []
    for name, source in sorted(expected.items()):
        binding = source["current_finished_step_binding"]
        prepared = source["prepared_section_mm"]
        length = source["stock_blank_length_mm"]
        original_bounds = [[0, length]] + [
            [0, dimension] for dimension in source["original_stock_section_mm"]
        ]
        prepared_bounds = (
            [[0, length]] + [[0, dimension] for dimension in prepared]
            if prepared
            else None
        )
        rows.append(
            {
                "member_id": name,
                "member_kind": "frame_timber"
                if source["member_kind"] == "timber"
                else "candidate_block",
                "stock_class": source["stock_class"],
                "stock_blank_length_mm": source["stock_blank_length_mm"],
                "original_stock_section_mm": source["original_stock_section_mm"],
                "prepared_section_mm": prepared,
                "frame_status": source["frame_status"],
                "current_finished_step_path": binding["path"],
                "current_finished_step_sha256": binding["file_sha256"],
                "containment_status": "CONTAINED",
                "original_stock_containment": {
                    "status": "CONTAINED",
                    "proposed_stock_bounds_g_q_r_mm": original_bounds,
                },
                "prepared_section_containment": {
                    "status": "CONTAINED",
                    "proposed_stock_bounds_g_q_r_mm": prepared_bounds,
                }
                if prepared
                else None,
            }
        )
    return {
        "candidate": cuts.CANDIDATE,
        "geometry_revision_id": cuts.REVISION,
        "records": rows,
    }


def test_source_blank_lengths_and_original_sections_survive_finished_span(sources):
    _, manifest, _ = sources
    manifest["physical_members"][0]["finished_grain_span_mm"] = 2450.0
    expected = cuts.expected_records(*sources)
    report = envelope_for(expected)
    schedule, blanks, excluded = cuts.reconcile(report, expected)
    assert len(schedule) == len(blanks) == 44
    assert not excluded
    assert (
        next(row for row in schedule if row["member_id"] == "frame-00")[
            "stock_blank_length_mm"
        ]
        == 2500.0
    )
    assert sum(row["prepared_section_mm"] is not None for row in schedule) == 4
    assert {blank.section for blank in blanks if blank.rip_to_section} == {"4x6"}
    assert {blank.rip_to_section for blank in blanks if blank.rip_to_section} == {
        (83.9, 139.7),
        (88.9, 133.35),
    }


@pytest.mark.parametrize("document", [1, 2])
@pytest.mark.parametrize(
    "field,value",
    [("candidate", "historical"), ("geometry_revision_id", "other-model")],
)
def test_wrong_model_identity_is_rejected(sources, document, field, value):
    sources[document][field] = value
    with pytest.raises(cuts.ReconciliationError, match="wrong"):
        cuts.expected_records(*sources)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-block",
        "duplicate-frame",
        "wrong-block-id",
        "missing-current",
        "wrong-section",
        "lost-rip",
        "oversize-rip",
        "nonpositive-length",
        "role-drift",
    ],
)
def test_changed_piece_basis_fails_closed(sources, mutation):
    inventory, manifest, proposals = sources
    if mutation == "missing-block":
        manifest["candidate_blocks"].pop()
    elif mutation == "duplicate-frame":
        inventory["parts"].append(copy.deepcopy(inventory["parts"][0]))
    elif mutation == "wrong-block-id":
        proposals["candidate_block_records"][0]["part_id"] = "historical-block"
    elif mutation == "missing-current":
        manifest["physical_members"].pop()
    elif mutation == "wrong-section":
        inventory["parts"][0]["actual_source_section_mm"] = [38.1, 140]
    elif mutation == "lost-rip":
        proposals["candidate_block_records"][0]["proposed_blank_cross_section_mm"] = [
            88.9,
            139.7,
        ]
    elif mutation == "oversize-rip":
        proposals["candidate_block_records"][0]["proposed_blank_cross_section_mm"] = [
            89,
            139.7,
        ]
    elif mutation == "nonpositive-length":
        inventory["parts"][0]["source_blank_dimensions_mm"][0] = 0
    elif mutation == "role-drift":
        manifest["physical_members"][0]["composition_roles"].append(
            "current_rebuilt_host"
        )
    with pytest.raises(cuts.ReconciliationError):
        cuts.expected_records(*sources)


@pytest.mark.parametrize(
    "mutation",
    [
        "length",
        "section",
        "prepared",
        "step",
        "role",
        "kind",
        "missing",
        "duplicate",
        "unknown-status",
        "detail-disagrees",
        "missing-rip-proof",
    ],
)
def test_mismatched_envelope_cannot_enter_nesting(sources, mutation):
    expected = cuts.expected_records(*sources)
    report = envelope_for(expected)
    row = report["records"][0]
    if mutation == "length":
        row["stock_blank_length_mm"] -= 1
    elif mutation == "section":
        row["original_stock_section_mm"] = [80, 139.7]
    elif mutation == "prepared":
        row["prepared_section_mm"] = [83, 139.7]
    elif mutation == "step":
        row["current_finished_step_sha256"] = "0" * 64
    elif mutation == "role":
        report["records"][-1]["frame_status"] = "source_only"
    elif mutation == "kind":
        row["member_kind"] = "frame_timber"
    elif mutation == "missing":
        report["records"].pop()
    elif mutation == "duplicate":
        report["records"].append(copy.deepcopy(row))
    elif mutation == "unknown-status":
        row["containment_status"] = "PASS"
    elif mutation == "detail-disagrees":
        row["prepared_section_containment"]["status"] = "INCOMPATIBLE"
    elif mutation == "missing-rip-proof":
        row["prepared_section_containment"] = None
    with pytest.raises(cuts.ReconciliationError):
        cuts.reconcile(report, expected)


@pytest.mark.parametrize("status", ["INCOMPATIBLE", "AMBIGUOUS"])
def test_unproved_piece_is_excluded_and_prevents_full_coverage_claim(sources, status):
    expected = cuts.expected_records(*sources)
    report = envelope_for(expected)
    row = report["records"][0]
    row["containment_status"] = status
    row["prepared_section_containment"]["status"] = status
    schedule, blanks, excluded = cuts.reconcile(report, expected)
    assert len(schedule) == 44 and len(blanks) == 43
    assert excluded == [{"member_id": row["member_id"], "containment_status": status}]
    assert all(
        not case["all_current_44_lengths_arithmetically_placed"]
        for case in cuts.scenarios(blanks, excluded)
    )


def test_individually_fitting_prepared_box_must_be_inside_the_original_box(sources):
    expected = cuts.expected_records(*sources)
    report = envelope_for(expected)
    report["records"][0]["prepared_section_containment"][
        "proposed_stock_bounds_g_q_r_mm"
    ][1] = [0, 139.7]
    with pytest.raises(
        cuts.ReconciliationError, match="prepared box does not lie inside"
    ):
        cuts.reconcile(report, expected)


def test_scenarios_keep_unfitted_ids_kerfs_rips_and_board_length_balance(sources):
    expected = cuts.expected_records(*sources)
    _, blanks, excluded = cuts.reconcile(envelope_for(expected), expected)
    scenarios = cuts.scenarios(blanks, excluded)
    assert len(scenarios) == 15
    for case in scenarios:
        packing = case["packing"]
        placed = {row["item_id"] for row in packing["placements"]}
        unfitted = set(packing["infeasible_item_ids"])
        assert not placed & unfitted and placed | unfitted == set(expected)
        if case["nominal_stock_length_options_ft"] == [8]:
            assert unfitted == {f"frame-{i:02}" for i in range(20)}
            assert not case["all_current_44_lengths_arithmetically_placed"]
        else:
            assert not unfitted and case["all_current_44_lengths_arithmetically_placed"]
        for board in packing["boards"]:
            assert board["remainder_section"] == board["section"]
            assert board["separation_kerf_mm"] == pytest.approx(
                len(board["item_ids"]) * 3.2
            )
            assert board["stock_length_mm"] == pytest.approx(
                sum(
                    board[key]
                    for key in (
                        "blank_length_mm",
                        "separation_kerf_mm",
                        "start_trim_mm",
                        "end_trim_mm",
                        "remainder_mm",
                    )
                )
            )
        ripped = [row for row in packing["placements"] if row["rip_to_section"]]
        assert len(ripped) == 4 and {row["section"] for row in ripped} == {"4x6"}


def test_exact_8ft_boundary_requires_last_blank_kerf():
    blanks = [
        cuts.Blank("exact-with-kerf", 2435.2, "2x6"),
        cuts.Blank("one-tenth-too-long", 2435.3, "2x6"),
    ]
    case = cuts.scenarios(blanks, [])[0]
    assert case["packing"]["infeasible_item_ids"] == ("one-tenth-too-long",)
    assert [row["item_id"] for row in case["packing"]["placements"]] == [
        "exact-with-kerf"
    ]


def test_pinned_file_requires_exact_content_and_declared_digest(tmp_path, monkeypatch):
    path = tmp_path / "source.json"
    path.write_bytes(b'{"value":1}\n')
    monkeypatch.setattr(
        cuts, "PINNED", {"source.json": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    assert cuts.read_pinned(tmp_path, "source.json") == {"value": 1}
    path.write_bytes(b'{"value":2}\n')
    with pytest.raises(cuts.ReconciliationError, match="changed input"):
        cuts.read_pinned(tmp_path, "source.json")
    with pytest.raises(cuts.ReconciliationError, match="not frozen"):
        cuts.read_pinned(tmp_path, "unfrozen.json")


def test_report_binds_actual_step_bytes_and_helpers(tmp_path, monkeypatch, sources):
    inventory, manifest, proposals = sources
    for member in manifest["physical_members"]:
        binding = member["current_finished_step_binding"]
        path = tmp_path / binding["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(member["member_id"].encode())
        binding["file_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    expected = cuts.expected_records(*sources)
    documents = {
        cuts.INVENTORY: inventory,
        cuts.MANIFEST: manifest,
        cuts.PROPOSALS: proposals,
        cuts.ENVELOPES: envelope_for(expected),
    }
    pins = {}
    for relative, document in documents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(cuts.canonical(document))
        pins[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in (cuts.ENVELOPE_PRODUCER, cuts.NESTING_PRODUCER):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"test producer identity\n")
        pins[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(cuts, "PINNED", pins)
    report = cuts.build_report(tmp_path)
    assert report["counts"]["geometry_eligible_records"] == 44
    assert report["status"] == "SOURCE_BOUND_PROPOSED_STOCK_CUT_ARITHMETIC"
    assert report["claim_boundary"]["physical_work_released"] is False
    assert cuts.canonical(report) == cuts.canonical(json.loads(cuts.canonical(report)))
    (
        tmp_path
        / manifest["physical_members"][0]["current_finished_step_binding"]["path"]
    ).write_bytes(b"changed")
    with pytest.raises(cuts.ReconciliationError, match="changed current STEP"):
        cuts.build_report(tmp_path)
    (tmp_path / cuts.NESTING_PRODUCER).write_bytes(b"changed producer")
    with pytest.raises(cuts.ReconciliationError, match="changed producer"):
        cuts.build_report(tmp_path)


def test_cli_frozen_output_is_not_overwritten_and_verification_is_exact(
    tmp_path, monkeypatch
):
    output = tmp_path / "cut-scenarios.json"
    report = {"status": "fixture", "counts": {"proposed_records": 44}}
    monkeypatch.setattr(cuts, "OUTPUT", output)
    monkeypatch.setattr(cuts, "build_report", lambda: report)
    cuts.main(["--write"])
    cuts.main(["--verify"])
    frozen = output.read_bytes()
    with pytest.raises(cuts.ReconciliationError, match="refusing to overwrite"):
        cuts.main(["--write"])
    assert output.read_bytes() == frozen
    output.write_bytes(json.dumps(report).encode())
    with pytest.raises(cuts.ReconciliationError, match="canonical pinned replay"):
        cuts.main(["--verify"])

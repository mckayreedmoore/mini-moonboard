"""Exact release-schema seam and provenance controls; synthetic builder sentinel."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_distinct_release_contract_fix", OWN.with_name("descriptor.py"))
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


def test_authentic_pinned_proposal_and_current_keep_distinct_all_false_contracts():
    frozen = fix.verified_v2().frozen_module()
    inp = json.loads((OWN.parent.parent / "inputs.json").read_bytes())
    actual = {}
    for key in ("current", "layout"):
        ref = inp["sources"][key]
        source = frozen.exact_ref(ref)
        actual[key] = json.loads(source.read_bytes())["release"]
    assert actual["layout"] == fix.PROPOSAL_RELEASE
    assert actual["current"] == frozen.RELEASE
    assert set(actual["layout"]) != set(actual["current"])


def bundle_before_census():
    frozen = fix.corrected_frozen_module(fix.verified_v2())
    parent = {"path": "parent.json", "sha256": "parent"}
    current_ref = {"path": "current.json", "sha256": "current"}
    layout_ref = {"path": "layout.json", "sha256": "layout"}
    sources = {"current": current_ref, "native": {}, "current_geometry": parent, "layout": layout_ref,
        "source_verification_adapter": fix.source_ref(fix.V2), "layout_release_contract_adapter": fix.source_ref(fix.OWN)}
    current = {"schema": "eoere_extended_cleat_cached_source_export/v1", "release": dict(frozen.RELEASE), "geometry": parent,
        "shafts": [], "hillman_rows": [], "physical_owner_gravity_rows": [], "finished_body_observations": []}
    layout = {"schema": "eoere_lower_cleat_z180_geometry_patch/v1", "revision": "eoere-lower-cleat-z180-proposal-v1",
        "parent_geometry": parent, "optional_2026_extra": False, "release": dict(fix.PROPOSAL_RELEASE), "saved_response_transferred": False}
    records = {"current": current, "layout": layout, "native": {}, "current_geometry": {"axes": []},
        "viewer_verification": {"passed": True, "parent_review_consumed_native_digest_joined": True,
            "original_outputs": {"layout.json": {"sha256": "layout"}}},
        "native_review": {"schema": "eoere_four_finished_receiver_candidate01_independent_correctness_saved_result_review/v1",
            "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SAVED_RESULT_SCOPE", "findings": []},
        "manifest": {"schema": "eoere_z180_analytical_mechanics_frozen_sources/v1", "geometry": layout_ref,
            "parent_geometry": parent, "parent_descriptors": current_ref, "release": {"own_release": False},
            "readiness": {"candidate_operator_assembly_or_solve": False, "independent_field_admission": False,
                "source_only_analytic_descriptor_preparation": True}}}
    return frozen, {"input": {"sources": sources, "helper": {"path": "frozen", "sha256": "frozen"}}, "records": records}


def test_actual_builder_path_accepts_distinct_proposal_contract_before_census_sentinel():
    frozen, bundle = bundle_before_census()
    before = copy.deepcopy(bundle)
    with pytest.raises(ValueError, match="protected100/66/150/28 census differs"):
        frozen.build_descriptor(bundle)
    assert bundle == before
    # The unchanged original deterministically rejects that same contract.
    original = fix.verified_v2().frozen_module()
    with pytest.raises(ValueError, match="exact unadopted OFF proposal required"):
        original.build_descriptor(bundle)


@pytest.mark.parametrize("failure", ["wrong_current_keys", "true_release", "missing_key", "extra_key"])
def test_wrong_or_adopted_proposal_release_rejected_before_geometry_arithmetic(failure):
    frozen, bundle = bundle_before_census()
    release = bundle["records"]["layout"]["release"]
    if failure == "wrong_current_keys":
        bundle["records"]["layout"]["release"] = dict(frozen.RELEASE)
    elif failure == "true_release":
        release["geometry_adopted"] = True
    elif failure == "missing_key":
        release.pop("geometry_adopted")
    else:
        release["foreign_release"] = False
    with pytest.raises(ValueError, match="exact unadopted OFF proposal required"):
        frozen.build_descriptor(bundle)


def test_helper_correction_provenance_is_exact_and_records_are_not_relabelled():
    _, bundle = bundle_before_census()
    record = fix.source_correction_record(bundle["input"])
    assert record["authentic_proposal_release_keys"] == fix.PROPOSAL_RELEASE
    assert record["records_relabelled_or_release_granted"] is False
    bundle["input"]["sources"]["layout_release_contract_adapter"]["sha256"] = "foreign"
    with pytest.raises(ValueError, match="exact input/helper correction provenance join required"):
        fix.source_correction_record(bundle["input"])


def test_original_source_hash_checked_before_ast_parse(tmp_path):
    v2 = fix.verified_v2()
    source = tmp_path / "changed.py"
    source.write_text("changed")
    v2.FROZEN = source
    with patch.object(fix, "release_contract_tree", side_effect=AssertionError("AST parser reached")), \
            pytest.raises(ValueError, match="source bytes differ"):
        fix.corrected_frozen_module(v2)


@pytest.mark.parametrize("raw", ["pass", 'layout["release"] == RELEASE\nlayout["release"] == RELEASE'])
def test_ast_seam_requires_exactly_one_matching_comparison(raw):
    with pytest.raises(ValueError, match="exact single frozen proposal release comparison required"):
        fix.release_contract_tree(raw, "owned-fixture")


@pytest.mark.parametrize("kind", ["file", "dangling_link"])
def test_actual_v3_wrapper_preserves_output_reservation_before_input_work(tmp_path, kind):
    v2 = fix.verified_v2()
    frozen = fix.corrected_frozen_module(v2)
    frozen.OWN = tmp_path / "packet/descriptor.py"
    out = frozen.OWN.parent / "runs-v1/existing.json"
    out.parent.mkdir(parents=True)
    if kind == "file":
        out.write_text("preserved")
    else:
        out.symlink_to(out.with_name("missing.json"))
    with patch.object(fix, "verified_v2", return_value=v2), patch.object(fix, "corrected_frozen_module", return_value=frozen), \
            patch.object(frozen, "load_inputs", side_effect=AssertionError("source intake reached")), pytest.raises(FileExistsError):
        fix.write_descriptor(tmp_path / "inputs.json", "wrong", out)
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()

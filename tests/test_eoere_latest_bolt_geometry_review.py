"""Tests for the latest-analysis routing adapter without reading an analysis bank."""

import hashlib
import inspect
import json
from pathlib import Path
from types import SimpleNamespace

from scripts import eoere_current_bolt_geometry_review as frozen_reader
from scripts import eoere_latest_bolt_geometry_review as latest
from scripts import eoere_v8_analysis


def test_analysis_name_selects_its_own_readiness_schema():
    assert latest.readiness_schema("v8") == "eoere_v8_existing_response_method_readiness/v1"
    assert latest.readiness_schema("v9") == "eoere_v9_existing_response_method_readiness/v1"


def test_v9_adapter_changes_only_the_frozen_readiness_schema_literal():
    frozen = inspect.getsource(frozen_reader._checked_readiness)
    adapted = latest.adapted_readiness_checker_source("v9")
    old = '"eoere_v8_existing_response_method_readiness/v1"'
    new = '"eoere_v9_existing_response_method_readiness/v1"'

    assert frozen.count(old) == 1
    assert adapted == frozen.replace(old, new, 1)


def test_v8_binding_reuses_frozen_functions_with_latest_wrapper_globals():
    namespace = latest.make_reader_namespace("v8", eoere_v8_analysis)

    assert namespace["analysis"] is eoere_v8_analysis
    assert namespace["OWN"] == latest.OWN
    assert namespace["READINESS"] == eoere_v8_analysis.BASE / "adapter-readiness.json"
    assert namespace["OUT"] == eoere_v8_analysis.BASE / "bolt-geometry-review-latest-v1"
    assert namespace["review"].__globals__ is namespace
    assert namespace["review"].__code__ is frozen_reader.review.__code__
    assert namespace["_admitted_fields"].__code__ is frozen_reader._admitted_fields.__code__
    assert namespace["_checked_readiness"] is not frozen_reader._checked_readiness


def test_method_blueprint_pins_the_frozen_reader_and_selected_module():
    blueprint = latest.method_blueprint("v8", eoere_v8_analysis)

    assert blueprint["selected_analysis_module"] == "v8"
    assert blueprint["analysis_module"]["path"] == str(eoere_v8_analysis.OWN.relative_to(latest.ROOT))
    assert blueprint["frozen_geometry_reader"]["path"] == str(latest.FROZEN_READER.relative_to(latest.ROOT))
    assert blueprint["frozen_geometry_reader_sha256"] == latest.FROZEN_READER_SHA256
    assert blueprint["latest_wrapper"]["path"] == str(latest.OWN.relative_to(latest.ROOT))


def test_v9_metadata_does_not_describe_its_fields_as_v8():
    v9_analysis = SimpleNamespace(
        OWN=Path(__file__).resolve(),
        REVISION="eoere-v9-test-analysis",
        PHYSICAL_REVISION="eoere-v9-test-geometry",
    )
    result = {
        "qualification_limits": [
            "The admitted six fields are evaluated with their own v8 forces and geometry; no earlier frame metric or response is carried into this report."
        ],
        "source_bindings": {},
    }

    latest.bind_report_metadata(result, "v9", v9_analysis)

    assert "own v9 forces and geometry" in result["qualification_limits"][0]
    assert "own v8 forces and geometry" not in result["qualification_limits"][0]
    assert result["method_blueprint"]["analysis_revision"] == v9_analysis.REVISION


def test_raw_publication_binds_lineage_before_full_report_hash(tmp_path):
    v9_analysis = SimpleNamespace(
        OWN=Path(__file__).resolve(),
        REVISION="eoere-v9-test-analysis",
        PHYSICAL_REVISION="eoere-v9-test-geometry",
        BASE=tmp_path,
    )
    namespace = latest.make_reader_namespace("v9", v9_analysis)

    def local_ref(path):
        path = Path(path)
        return {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "0" * 64,
        }

    namespace["ref"] = local_ref
    raw_path = tmp_path / "full-review.json"
    result = {
        "schema": "eoere_current_bolt_geometry_review/v1",
        "analysis_revision": v9_analysis.REVISION,
        "cases": [],
        "qualification_limits": [
            "The admitted six fields are evaluated with their own v8 forces and geometry; no earlier frame metric or response is carried into this report."
        ],
        "source_bindings": {},
        "source_sha256": {},
        "profile_face_confirmations": {},
    }

    namespace["_write_new"](raw_path, result)
    raw = json.loads(raw_path.read_text())
    digest_before_summary = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    summary = namespace["public_summary"](raw, raw_path)

    assert raw["method_blueprint"]["analysis_revision"] == v9_analysis.REVISION
    assert raw["method_blueprint"]["frozen_geometry_reader_sha256"] == latest.FROZEN_READER_SHA256
    assert raw["source_bindings"]["analysis_module"] == latest.ref(v9_analysis.OWN)
    assert "own v9 forces and geometry" in raw["qualification_limits"][0]
    assert summary["full_review"]["sha256"] == digest_before_summary
    assert summary["method_blueprint"] == raw["method_blueprint"]

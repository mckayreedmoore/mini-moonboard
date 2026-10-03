import hashlib
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "center_producer_test", Path(__file__).with_name("produce.py")
)
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def authority_fixture():
    candidate, revision = "candidate", "reviewed-revision"
    geometry = {"revision_id": revision}
    sources = {}
    for kind, (path, sha) in zip(
        ("scene", "report", "snapshot"), P.REVIEWED_GEOMETRY_BINDINGS, strict=True
    ):
        geometry[kind + "_path"] = path
        geometry[kind + "_sha256"] = sha
        sources[path] = {"sha256": sha}
    coverage = {
        "candidate": candidate,
        "current_geometry_pin": geometry,
        "criteria": [
            {"criterion_id": identity, "status": "pending"}
            for identity in (
                "actual_kicker_cutouts",
                "center_kicker_receiver_paths",
                "complete_load_path_coverage",
            )
        ],
    }
    return (
        coverage,
        {"candidate": candidate, "engineering_mvp_complete": False},
        candidate,
        revision,
        sources,
    )


def test_current_authority_is_bound_to_reviewed_candidate_and_all_obligations():
    inputs = authority_fixture()
    assert P.current_obligations(*inputs) == inputs[0]["criteria"]


@pytest.mark.parametrize(
    "mutation",
    [
        "coverage_candidate",
        "criteria_candidate",
        "revision",
        "scene_hash",
        "report_path",
        "other_bound_path_and_hash",
        "snapshot_missing",
        "duplicate_id",
        "missing_id",
        "resolved",
        "complete",
    ],
)
def test_current_authority_mismatches_are_refused(mutation):
    coverage, criteria, candidate, revision, sources = deepcopy(authority_fixture())
    if mutation == "coverage_candidate":
        coverage["candidate"] = "other"
    elif mutation == "criteria_candidate":
        criteria["candidate"] = "other"
    elif mutation == "revision":
        coverage["current_geometry_pin"]["revision_id"] = "other"
    elif mutation == "scene_hash":
        coverage["current_geometry_pin"]["scene_sha256"] = "other"
    elif mutation == "report_path":
        coverage["current_geometry_pin"]["report_path"] = "unbound.json"
    elif mutation == "other_bound_path_and_hash":
        pin = coverage["current_geometry_pin"]
        pin["report_path"] = pin["scene_path"]
        pin["report_sha256"] = pin["scene_sha256"]
    elif mutation == "snapshot_missing":
        coverage["current_geometry_pin"].pop("snapshot_path")
    elif mutation == "duplicate_id":
        coverage["criteria"][1] = deepcopy(coverage["criteria"][0])
    elif mutation == "missing_id":
        coverage["criteria"].pop()
    elif mutation == "resolved":
        coverage["criteria"][0]["status"] = "resolved"
    else:
        criteria["engineering_mvp_complete"] = True
    with pytest.raises(ValueError):
        P.current_obligations(coverage, criteria, candidate, revision, sources)


def test_known_prose_delta_is_visible_and_other_changes_stop(tmp_path, monkeypatch):
    old, current = b"old prose", b"current prose"
    monkeypatch.setattr(P, "STALE_PATH", "prose.md")
    monkeypatch.setattr(P, "STALE_EXPECTED", hashlib.sha256(old).hexdigest())
    monkeypatch.setattr(P, "STALE_CURRENT", hashlib.sha256(current).hexdigest())
    (tmp_path / "prose.md").write_bytes(current)
    pins = {}
    assert P.register_pin(tmp_path, pins, "prose.md", P.STALE_EXPECTED, "old-pins.json")
    assert pins["prose.md"]["upstream_bindings"] == [
        {
            "manifest_path": "old-pins.json",
            "expected_sha256": P.STALE_EXPECTED,
            "status": "STALE_PROSE_INPUT",
        }
    ]
    (tmp_path / "geometry.json").write_bytes(current)
    with pytest.raises(ValueError, match="source pin changed"):
        P.register_pin(tmp_path, pins, "geometry.json", P.STALE_EXPECTED)
    (tmp_path / "prose.md").write_bytes(b"another prose edit")
    with pytest.raises(ValueError, match="source pin changed"):
        P.register_pin(tmp_path, pins, "prose.md", P.STALE_EXPECTED)


def test_path_escape_and_changed_source_during_read_are_refused(tmp_path):
    with pytest.raises(ValueError, match="escapes root"):
        P.register_pin(tmp_path, {}, "../outside.json")
    (tmp_path / "source.json").write_text("one")
    pins = {}
    P.register_pin(tmp_path, pins, "source.json")
    (tmp_path / "source.json").write_text("two")
    with pytest.raises(ValueError, match="during read"):
        P.register_pin(tmp_path, pins, "source.json")


@pytest.mark.parametrize("raw", ['{"x":1,"x":2}', '{"x":NaN}'])
def test_ambiguous_json_is_refused(tmp_path, raw):
    path = tmp_path / "input.json"
    path.write_text(raw)
    with pytest.raises(ValueError):
        P.read_json(path)


def test_cli_source_refusal_writes_no_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(P, "HERE", tmp_path)

    def refused():
        raise ValueError("missing frozen input")

    monkeypatch.setattr(P, "build_report", refused)
    assert P.main(["--write"]) == 2
    assert "missing frozen input" in capsys.readouterr().err
    assert list(tmp_path.iterdir()) == []


def test_exact_metadata_verify_detects_changed_bytes(tmp_path, monkeypatch):
    report, pins = {"status": "diagnostic"}, {"sources": []}
    monkeypatch.setattr(P, "HERE", tmp_path)
    monkeypatch.setattr(P, "build_report", lambda: (report, pins))
    assert P.main(["--write"]) == 0
    assert P.main(["--verify"]) == 0
    (tmp_path / "backing-duty.json").write_text(json.dumps(report))
    assert P.main(["--verify"]) == 2

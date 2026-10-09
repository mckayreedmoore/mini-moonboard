"""Inert correction controls; authentic review metadata shape, no field run."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_component_release_correction", OWN.with_name("consume.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a = m.original()
ROOT = a.ROOT
TESTS = m.FROZEN.with_name("test_consume.py")
TEST_SHA = "1024873b79c965172ddd7d4324063863c4d41561570f30c24d9cd895b6bd7d44"
REVIEW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-inputs-v1/independent-review-v2/correctness/receipt.json"
REVIEW_SHA = "acecce87e8b737374f75b896a7875fcdf287649923b641d431edb8a301e49a38"


@pytest.fixture
def tiny(tmp_path, monkeypatch):
    assert hashlib.sha256(TESTS.read_bytes()).hexdigest() == TEST_SHA
    spec = importlib.util.spec_from_file_location("z180_original_inert_fixture", TESTS)
    controls = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(controls)
    monkeypatch.setattr(controls, "m", a)
    t = controls.tiny.__wrapped__(tmp_path, monkeypatch)
    own = tmp_path / "review-fix-v2/consume.py"
    own.parent.mkdir()
    own.write_bytes(m.OWN.read_bytes())
    monkeypatch.setattr(m, "OWN", own)
    raw = REVIEW.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == REVIEW_SHA
    authentic = json.loads(raw)
    # A new inert fixture uses the genuine schema/success/release shape only.
    # The genuine receipt itself and its descriptor reference remain untouched.
    t.review = {k: copy.deepcopy(authentic[k]) for k in
        ("schema", "success", "independent_z180_descriptor_source_checks_pass", "release")}
    t.controls = controls
    def freeze_review():
        t.review["descriptor"] = t.config["sources"]["descriptor"]
        ref = controls.write(tmp_path, "review.json", t.review)
        t.config["sources"]["descriptor_review"] = ref
        t.config_ref = controls.write(tmp_path, "config.json", t.config)
    t.freeze_review = freeze_review
    freeze_review()
    return t


def call(t):
    return m.consume(t.root / "config.json", t.config_ref["sha256"])


def test_authentic_geometry_release_shape_passes_inert_boundary_without_rewriting(tiny):
    before = (tiny.root / "review.json").read_bytes()
    old_authenticate, old_release = a.authenticate, dict(a.RELEASE)
    with pytest.raises(ValueError, match="exact own descriptor review"):
        old_authenticate(tiny.root / "config.json", tiny.config_ref["sha256"])
    result = call(tiny)
    assert tiny.events == ["gate_definitions", "inert_gate_callback", "metadata", "corrected_source_scope",
                           "source_join", "source_scope_restored", "inert_reducer_callback"]
    assert (tiny.root / "review.json").read_bytes() == before
    assert result["release"] == old_release and a.RELEASE == old_release and a.authenticate is old_authenticate
    assert result["source_sha256"]["review-fix-v2/consume.py"] == m.LOADED_SHA
    assert result["source_sha256"]["consume.py"] == m.FROZEN_SHA


@pytest.mark.parametrize("mutation", ["field_style", "missing", "true", "unknown"])
def test_wrong_descriptor_review_release_contract_stops_before_gate_or_reducer(tiny, mutation):
    if mutation == "field_style":
        tiny.review["release"] = dict(a.RELEASE)
    elif mutation == "missing":
        del tiny.review["release"]["physical_contact"]
    elif mutation == "true":
        tiny.review["release"]["physical_contact"] = True
    else:
        tiny.review["release"]["unknown"] = False
    tiny.freeze_review()
    original_authenticate = a.authenticate
    with pytest.raises(ValueError, match="exact own descriptor review"):
        call(tiny)
    assert tiny.events == [] and a.authenticate is original_authenticate


@pytest.mark.parametrize("mutation", ["missing", "true", "unknown", "geometry_style"])
def test_original_mechanics_field_release_semantics_remain_exact(tiny, mutation):
    if mutation == "missing":
        del tiny.field["release"]["capacity_established"]
    elif mutation == "true":
        tiny.field["release"]["capacity_established"] = True
    elif mutation == "unknown":
        tiny.field["release"]["unknown"] = False
    else:
        tiny.field["release"] = dict(m.DESCRIPTOR_RELEASE)
    tiny.freeze()
    tiny.freeze_review()
    before = dict(a.RELEASE)
    with pytest.raises(ValueError, match="own unreleased Z180"):
        call(tiny)
    assert tiny.events == [] and a.RELEASE == before


@pytest.mark.parametrize("when", ["before", "during"])
def test_closure_checks_and_authenticate_restore_on_failure(tiny, when):
    if when == "before":
        (tiny.root / "proof.bin").write_bytes(b"changed")
    else:
        tiny.during_gate = lambda: (tiny.root / "proof.bin").write_bytes(b"changed")
    original_authenticate = a.authenticate
    with pytest.raises(ValueError, match="source closure changed"):
        call(tiny)
    assert a.authenticate is original_authenticate and "inert_reducer_callback" not in tiny.events


def test_nested_correction_fails_and_restores(tiny):
    original_authenticate = a.authenticate
    with m.corrected_context(), pytest.raises(ValueError, match="unnested"), m.corrected_context():
        pytest.fail("nested correction entered")
    assert a.authenticate is original_authenticate


def test_compilation_checks_exact_original_source_bytes(tiny, monkeypatch):
    changed = tiny.root / "changed.py"
    changed.write_bytes(m.FROZEN.read_bytes() + b"\n")
    monkeypatch.setattr(m, "FROZEN", changed)
    with pytest.raises(ValueError, match="exact original compiler bytes changed"):
        m.corrected_authenticate(a)


def test_wrapper_source_drift_rejects_before_gate(tiny):
    m.OWN.write_bytes(m.OWN.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="exact original/corrected consumer bytes changed"):
        call(tiny)
    assert tiny.events == []


def test_corrected_cli_keeps_fresh_reservation_and_failed_attempt(tmp_path):
    out = tmp_path / "attempt.json"
    command = [sys.executable, "-B", str(OWN.with_name("consume.py")), "--config", str(tmp_path / "absent.json"),
               "--config-sha256", "0"*64, "--out", str(out)]
    first = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode != 0 and json.loads(out.read_bytes())["status"] == "FAILED"
    before = out.read_bytes()
    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert second.returncode != 0 and "FileExistsError" in second.stderr and out.read_bytes() == before

"""Focused inert saved-shape controls, reusing frozen synthetic fixtures."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("z180_summary_shape_v4", HERE/"summarize.py")
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)
OWN_RAW = c.OWN.read_bytes()
FROZEN_TEST = HERE.parent/"test_summarize.py"


@pytest.fixture
def inert(tmp_path, monkeypatch):
    raw = FROZEN_TEST.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "53fb7a6a9be0678116f877de6b7659a8b9356406765b9ca9035b32059d1dcb7d"
    frozen = ModuleType("frozen_z180_summary_inert_fixtures_53fb7a6a")
    frozen.__file__ = str(FROZEN_TEST)
    exec(compile(raw, str(FROZEN_TEST), "exec"), frozen.__dict__)  # noqa: S102 -- authenticated frozen inert fixtures
    a = c.original()
    frozen.a = a
    f = frozen.fixture.__wrapped__(tmp_path, monkeypatch)
    own_ref = f.save("shape-adapter.py", OWN_RAW)
    monkeypatch.setattr(c, "OWN", tmp_path/own_ref["path"])
    for i, binding in enumerate(f.manifest["cases"]):
        process = json.loads((f.root/binding["component"]["process"]["path"]).read_bytes())
        for key in ("source_pins_before", "source_pins_after"):
            snapshot = json.loads((f.root/process[key]["path"]).read_bytes())
            snapshot["schema"] = c.SNAPSHOT_SCHEMA
            if key == "source_pins_before" and i:
                snapshot.pop("inventory_only_historical_receipts")
            ref = f.save(process[key]["path"], snapshot)
            process[key] = {**ref, "bytes": (f.root/ref["path"]).stat().st_size}
        binding["component"]["process"] = f.save(binding["component"]["process"]["path"], process)
    f.ref = f.save("manifest.json", f.manifest)
    f.a, f.own_ref = a, own_ref
    return f


def mutate_snapshot(f, role, mutate, *, case=0):
    binding = f.manifest["cases"][case]
    ref = binding["component"]["process"]
    process = json.loads((f.root/ref["path"]).read_bytes())
    snapshot = json.loads((f.root/process[role]["path"]).read_bytes())
    mutate(snapshot)
    own_ref = f.save(process[role]["path"], snapshot)
    process[role] = {**own_ref, "bytes": (f.root/own_ref["path"]).stat().st_size}
    binding["component"]["process"] = f.save(ref["path"], process)
    f.ref = f.save("manifest.json", f.manifest)


def test_actual_schema_and_optional_history_preserve_selectors_and_caveat(inert):
    result = inert.a.build(inert.manifest, inert.ref)
    assert [row["case_id"] for row in result["cases"]] == list(inert.a.CASES)
    first = result["cases"][0]
    assert first["outer_snapshot_caveats"]["inventory_only_historical_receipts"] == ["inventory-only"]
    assert len(first["outer_snapshot_caveats"]["result_pins_missing_before_snapshot"]) == 1
    assert first["outer_snapshot_caveats"]["complete_outer_pre_snapshot_claimed"] is False
    assert all(row["outer_snapshot_caveats"]["inventory_only_historical_receipts"] == [] for row in result["cases"][1:])
    assert result["source_sha256"][inert.own_ref["path"]] == c.LOADED_SHA
    selectors = inert.a.definitions(inert.a.SELECTORS, inert.a.SELECTED, {})
    for binding, row in zip(inert.manifest["cases"], result["cases"], strict=True):
        component = json.loads((inert.root/binding["component"]["result"]["path"]).read_bytes())
        field = json.loads((inert.root/binding["field"]["path"]).read_bytes())
        assert row["coarse"] == selectors.coarse_findings({"component_reductions": component["findings"]["coarse"], "limits": field["limits"]})
        assert row["rich"] == selectors.rich_findings({"findings": component["findings"]["rich"]})
    assert result["verified_source_union"]["before_after_exact"] is True
    assert result["complete_joint_resistance"] is None and not any(result["release"].values())


@pytest.mark.parametrize("role", ["source_pins_before", "source_pins_after"])
@pytest.mark.parametrize("schema", [*c.OLD_SCHEMAS, "foreign/v1"])
def test_old_invented_or_foreign_schema_rejected_without_relabel(inert, role, schema):
    mutate_snapshot(inert, role, lambda snapshot: snapshot.update(schema=schema))
    with pytest.raises(ValueError, match="exact component source snapshot"):
        inert.a.build(inert.manifest, inert.ref)


def test_missing_history_observation_is_empty_without_erasing_coverage(inert):
    mutate_snapshot(inert, "source_pins_before", lambda snapshot: snapshot.pop("inventory_only_historical_receipts"))
    first = inert.a.build(inert.manifest, inert.ref)["cases"][0]["outer_snapshot_caveats"]
    assert first["inventory_only_historical_receipts"] == []
    assert len(first["result_pins_missing_before_snapshot"]) == 1
    assert first["complete_outer_pre_snapshot_claimed"] is False


def test_unchanged_coverage_mismatch_guard_rejects(inert):
    mutate_snapshot(inert, "source_pins_after", lambda snapshot: snapshot.update(result_pins_missing_before_snapshot=[]))
    with pytest.raises(ValueError, match="missing-before coverage caveat differs"):
        inert.a.build(inert.manifest, inert.ref)


def test_exact_raw_snapshot_hash_still_required(inert):
    ref = inert.manifest["cases"][0]["component"]["process"]
    process = json.loads((inert.root/ref["path"]).read_bytes())
    snapshot_path = inert.root/process["source_pins_before"]["path"]
    raw = snapshot_path.read_bytes()
    snapshot_path.write_bytes(b"["+raw[1:])  # Same size: exercise SHA, not the earlier size guard.
    with pytest.raises(ValueError, match="exact source bytes differ"):
        inert.a.build(inert.manifest, inert.ref)


def test_production_build_requires_own_adapter_manifest_pin(inert, monkeypatch):
    monkeypatch.setattr(c, "original", lambda: inert.a)
    a = c.output_original()
    with pytest.raises(ValueError, match="exact v4 adapter manifest pin required"):
        a.build(inert.manifest, inert.ref)
    inert.manifest["source_sha256"][inert.own_ref["path"]] = c.LOADED_SHA
    inert.ref = inert.save("manifest.json", inert.manifest)
    assert len(a.build(inert.manifest, inert.ref)["cases"]) == 6


def test_adapter_source_drift_rejected_before_ast(inert, monkeypatch):
    c.OWN.write_bytes(OWN_RAW+b"# drift\n")
    monkeypatch.setattr(c.ast, "parse", lambda *_args, **_kwargs: pytest.fail("AST reached after adapter drift"))
    with pytest.raises(ValueError, match="v4 adapter source changed"):
        c.original()


def test_exact_v3_output_guard_reused_without_copy():
    assert c._writer.write_to_file.__code__.co_filename == str(c.V3)
    assert hashlib.sha256(c.V3.read_bytes()).hexdigest() == c.V3_SHA
    a = c.original()
    assert a.SELECTORS["sha256"] == "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735"
    assert a.build.__code__.co_filename == str(c.OWN)

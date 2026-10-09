"""Inert output-path race controls; no actual candidate descriptor trial."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_canonical_output_fix", OWN.with_name("descriptor.py"))
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)


@contextmanager
def inert_writer(tmp_path, *, fail=False):
    v4 = fix.corrected_v4()
    v3 = v4.corrected_v3()
    frozen = v3.corrected_frozen_module(v3.verified_v2())
    frozen.OWN = tmp_path / "packet/descriptor.py"
    frozen.ROOT = tmp_path
    loaded = {"source_sha256": {}, "root": tmp_path}
    def intake(*_args, **_kwargs):
        if fail:
            raise ValueError("owned inert source failure")
        return loaded
    result = {"geometry_delta_proof": {"counts": {}}, "release": frozen.RELEASE,
        "force_execution_readiness_claimed": False}
    with ExitStack() as stack:
        stack.enter_context(patch.object(v4, "corrected_v3", return_value=v3))
        stack.enter_context(patch.object(v3, "corrected_frozen_module", return_value=frozen))
        stack.enter_context(patch.object(frozen, "load_inputs", side_effect=intake))
        stack.enter_context(patch.object(frozen, "build_descriptor", return_value=result))
        yield v4, frozen


def test_canonical_parent_bound_before_delegation_mkdir_and_exclusive_open(tmp_path):
    with inert_writer(tmp_path) as (v4, _):
        parent = tmp_path / "packet/runs-v1/intended"
        parent.mkdir(parents=True)
        outside = tmp_path / "outside"
        outside.mkdir()
        alias = tmp_path / "packet/runs-v1/parent-alias"
        alias.symlink_to(parent, target_is_directory=True)
        def retarget():
            alias.unlink()
            alias.symlink_to(outside, target_is_directory=True)
            return v4
        with patch.object(fix, "OWN", tmp_path / "packet/review-fix-v5/descriptor.py"), \
                patch.object(fix, "corrected_v4", side_effect=retarget):
            result = fix.write_descriptor(tmp_path / "inputs.json", "inert", alias / "descriptor.json")
        assert Path(result["path"]) == Path("packet/runs-v1/intended/descriptor.json")
        assert json.loads((parent / "descriptor.json").read_bytes())["source_pins_before_after_unchanged"] is True
        assert not (outside / "descriptor.json").exists()


def test_parent_alias_retarget_still_retains_failure_in_bound_owned_parent(tmp_path):
    with inert_writer(tmp_path, fail=True) as (v4, _):
        parent = tmp_path / "packet/runs-v1/intended"
        parent.mkdir(parents=True)
        outside = tmp_path / "outside"
        outside.mkdir()
        protected = outside / "descriptor.json"
        protected.write_text("preserved outside")
        alias = tmp_path / "packet/runs-v1/parent-alias"
        alias.symlink_to(parent, target_is_directory=True)
        def retarget():
            alias.unlink()
            alias.symlink_to(outside, target_is_directory=True)
            return v4
        with patch.object(fix, "OWN", tmp_path / "packet/review-fix-v5/descriptor.py"), \
                patch.object(fix, "corrected_v4", side_effect=retarget), pytest.raises(ValueError, match="owned inert source failure"):
            fix.write_descriptor(tmp_path / "inputs.json", "inert", alias / "descriptor.json")
        assert json.loads((parent / "descriptor.json").read_bytes())["status"] == "FAILED"
        assert protected.read_text() == "preserved outside"


def test_initial_outside_parent_alias_rejected_before_source_or_output_work(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    alias = tmp_path / "packet/runs-v1/parent-alias"
    alias.parent.mkdir(parents=True)
    alias.symlink_to(outside, target_is_directory=True)
    with patch.object(fix, "OWN", tmp_path / "packet/review-fix-v5/descriptor.py"), \
            patch.object(fix, "corrected_v4", side_effect=AssertionError("source intake reached")), \
            pytest.raises(ValueError, match="belongs under this packet"):
        fix.write_descriptor(tmp_path / "inputs.json", "inert", alias / "descriptor.json")
    assert not list(outside.iterdir())


@pytest.mark.parametrize("kind", ["existing_file", "dangling_link", "late_file", "late_dangling_link"])
def test_existing_and_late_leaf_refused_before_intake(tmp_path, kind):
    with inert_writer(tmp_path) as (v4, frozen):
        out = tmp_path / "packet/runs-v1/descriptor.json"
        out.parent.mkdir(parents=True)
        def create_leaf():
            if "dangling" in kind:
                out.symlink_to(out.with_name("missing.json"))
            else:
                out.write_text("preserved")
            return v4
        if not kind.startswith("late"):
            create_leaf()
        with patch.object(fix, "OWN", tmp_path / "packet/review-fix-v5/descriptor.py"), \
                patch.object(fix, "corrected_v4", side_effect=create_leaf if kind.startswith("late") else lambda: v4), \
                patch.object(frozen, "load_inputs", side_effect=AssertionError("source intake reached")), pytest.raises(FileExistsError):
            fix.write_descriptor(tmp_path / "inputs.json", "inert", out)
        assert out.is_symlink() if "dangling" in kind else out.read_text() == "preserved"


def test_started_receipt_precedes_failure_and_failed_attempt_stays_reserved(tmp_path):
    with inert_writer(tmp_path) as (v4, frozen):
        out = tmp_path / "packet/runs-v1/new/descriptor.json"
        def intake(*_args, **_kwargs):
            assert json.loads(out.read_bytes())["status"] == "STARTED"
            raise ValueError("owned inert source failure")
        with patch.object(fix, "OWN", tmp_path / "packet/review-fix-v5/descriptor.py"), \
                patch.object(fix, "corrected_v4", return_value=v4), patch.object(frozen, "load_inputs", side_effect=intake):
            with pytest.raises(ValueError, match="owned inert source failure"):
                fix.write_descriptor(tmp_path / "inputs.json", "inert", out)
            assert json.loads(out.read_bytes())["status"] == "FAILED"
            with pytest.raises(FileExistsError):
                fix.write_descriptor(tmp_path / "inputs.json", "inert", out)


def test_reserved_inode_replacement_rejected_without_touching_replacement(tmp_path):
    with inert_writer(tmp_path) as (v4, frozen):
        out = tmp_path / "packet/runs-v1/descriptor.json"
        moved = out.with_name("reserved-inode.json")
        def intake(*_args, **_kwargs):
            out.rename(moved)
            out.write_text("replacement preserved")
            raise ValueError("owned failure after leaf replacement")
        with patch.object(fix, "OWN", tmp_path / "packet/review-fix-v5/descriptor.py"), \
                patch.object(fix, "corrected_v4", return_value=v4), patch.object(frozen, "load_inputs", side_effect=intake), \
                pytest.raises(ValueError, match="reserved output identity changed"):
            fix.write_descriptor(tmp_path / "inputs.json", "inert", out)
        assert out.read_text() == "replacement preserved"
        assert json.loads(moved.read_bytes())["status"] == "STARTED"


def test_new_input_output_provenance_requires_exact_adapter_bytes():
    v4 = fix.corrected_v4()
    v3 = v4.corrected_v3()
    inp = json.loads((OWN.parent.parent / "review-fix-v4/inputs.json").read_bytes())
    ref = v3.source_ref(fix.OWN)
    inp["sources"]["canonical_output_adapter"] = ref
    assert v3.source_correction_record(inp)["canonical_output_adapter"] == ref
    inp["sources"]["canonical_output_adapter"]["sha256"] = "foreign"
    with pytest.raises(ValueError, match="exact canonical-output correction provenance required"):
        v3.source_correction_record(inp)


def test_frozen_v4_authenticated_before_compilation(tmp_path):
    changed = tmp_path / "changed.py"
    changed.write_text("raise AssertionError('untrusted source executed')")
    with patch.object(fix, "V4", changed), pytest.raises(ValueError, match="source bytes differ|adapter bytes differ"):
        fix.verified_v4()


def test_all_original_sources_and_result_attempts_preserved():
    packet = OWN.parent.parent
    expected = {"descriptor.py": "691f46fd47b2e952e3b8911d61ddf855d9806c20190f77a1d6e0f57ad022a9ac",
        "review-fix-v2/descriptor.py": "8ab67c15c544ba1cf1f0209020fb87614072c665a8eaa39dc667a23db5b2823a",
        "review-fix-v3/descriptor.py": "b9540ab1612033194c8ae7ac230ab21082813cd63cf824cc77b58cba9bfa6b1b",
        "review-fix-v4/descriptor.py": fix.V4_SHA256,
        "runs-v1/attempt01/descriptor.json": "cbd631119812264c03eb1b41e6b696421b55b20426de42ef84f03d90f7c4cb71",
        "runs-v1/attempt02/descriptor.json": "fd56af74e5133fb96229708ae2372beb96ece2ec778c052e6ee78a4aeaf0c054",
        "runs-v1/attempt03/descriptor.json": "e7a1a56f7c61119445c85f554d534abc5c43f77fede27a7fab42ad252bb275f0",
        "result.json": "3b8c2b7849573104a10ca1b0cf827bd9b0055c6edf3ee2ac91feaab88e3357d4"}
    for path, digest in expected.items():
        assert hashlib.sha256((packet / path).read_bytes()).hexdigest() == digest

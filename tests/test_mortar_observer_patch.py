"""Hermetic tests against the exact two official upstream source files."""
import base64
import hashlib
import io
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from fea.mortar_observer.patch import SOURCE_SHA256, patched_sources, replacements

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sources():
    fixture = ROOT / "fea/mortar_observer/upstream-two-files.tar.gz.base64"
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(fixture.read_bytes())), mode="r:gz") as archive:
        return {name: archive.extractfile(name).read() for name in SOURCE_SHA256}


def test_exact_sources_and_insertions_only(sources):
    assert {k: hashlib.sha256(v).hexdigest() for k, v in sources.items()} == SOURCE_SHA256
    outputs = patched_sources(sources)
    for name, edits in replacements().items():
        restored = outputs[name].decode()
        for anchor, addition, position in reversed(edits):
            combined = addition + anchor if position == "before" else anchor + addition
            assert restored.count(combined) == 1
            restored = restored.replace(combined, anchor, 1)
        assert restored.encode() == sources[name]


@pytest.mark.parametrize("name", SOURCE_SHA256)
def test_wrong_source_rejected(sources, name):
    with pytest.raises(ValueError, match="source hash"):
        patched_sources(sources | {name: sources[name] + b"\n"})


def test_reapplication_rejected(sources):
    with pytest.raises(ValueError, match="source hash"):
        patched_sources(patched_sources(sources))


def test_observer_chronology(sources):
    outputs = patched_sources(sources)
    stress = outputs["stressmortar.c"].decode()
    ordered = ["INVENTORY", "PRE_RAW", "DDTIL", "generate cstressini2,cstresstil",
               "LAW", "if( ncf_n<0.0)", "POST_RAW_AFTER_ACTIVE_LOOP",
               "SUMMARY_PRE_OVERRIDE", "if(*iit>ndiverg)", "SUMMARY_POST_OVERRIDE"]
    positions = [stress.index(token) for token in ordered]
    assert positions == sorted(positions)
    caller = outputs["nonlingeo.c"].decode()
    ordered = ["++mortar_observer_call_id", 'kind\\\":\\\"BEGIN', "stressmortar(bhat",
               'kind\\\":\\\"RETURN', "PRE_CHECK", "checkconvergence(co", "POST_CHECK"]
    positions = [caller.index(token) for token in ordered]
    assert positions == sorted(positions)
    assert caller.count("++mortar_observer_call_id") == 1
    assert "%.17g" in stress and "ITGFORMAT" in stress


def test_cli_preserves_input_and_refuses_existing_destination(sources, tmp_path):
    original = tmp_path / "original"
    original.mkdir()
    for name, data in sources.items():
        (original / name).write_bytes(data)
    destination = tmp_path / "patched"
    command = [sys.executable, str(ROOT / "fea/mortar_observer/patch.py"), str(original), str(destination)]
    assert subprocess.run(command, capture_output=True, check=False).returncode == 0
    assert subprocess.run(command, capture_output=True, check=False).returncode != 0
    assert {name: (original / name).read_bytes() for name in sources} == sources
    assert {name: (destination / name).read_bytes() for name in sources} == patched_sources(sources)
    for name in sources:
        (original / name).write_bytes(b"wrong")
    nonexistent = tmp_path / "never-created"
    assert subprocess.run(command[:-1] + [str(nonexistent)], capture_output=True, check=False).returncode != 0
    assert not nonexistent.exists()

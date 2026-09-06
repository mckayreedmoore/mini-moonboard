"""Hermetic insertion/manifest tests; no solver compilation or execution."""
import base64
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

from fea.mortar_observer import kinematic_patch as v2
from fea.mortar_observer import patch as v1

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sources():
    fixture = ROOT/"fea/mortar_observer/upstream-two-files.tar.gz.base64"
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode(fixture.read_bytes())), mode="r:gz") as archive:
        return {name: archive.extractfile(name).read() for name in v1.SOURCE_SHA256}


def test_only_two_additive_blocks_on_top_of_unchanged_v1(sources):
    original = dict(sources)
    old, new = v1.patched_sources(sources), v2.patched_sources(sources)
    assert sources == original
    assert new["nonlingeo.c"] == old["nonlingeo.c"]
    for name, edits in v2.replacements().items():
        restored = new[name].decode()
        for anchor, addition, position in reversed(edits):
            assert position == "before"
            assert restored.count(addition+anchor) == 1
            restored = restored.replace(addition+anchor, anchor, 1)
        assert restored.encode() == old[name]


@pytest.mark.parametrize("name", v1.SOURCE_SHA256)
def test_wrong_original_and_reapplication_rejected(sources, name):
    with pytest.raises(ValueError, match="source hash"):
        v2.patched_sources(sources | {name: sources[name]+b"\n"})
    with pytest.raises(ValueError, match="source hash"):
        v2.patched_sources(v1.patched_sources(sources))
    with pytest.raises(ValueError, match="source hash"):
        v2.patched_sources(v2.patched_sources(sources))


def test_exact_kinematic_force_observation_phases_and_sparse_coverage(sources):
    source = v2.patched_sources(sources)["stressmortar.c"].decode()
    ordered = ["/* overwrite b with untransformed delta u*/", "KIN_INVENTORY", "KIN_NODE", "KIN_DD",
               "KIN_BD", "KIN_GAP", "/* calculate hatu=D u^S+ B u^M", "INVENTORY", "PRE_RAW", "LAW",
               "POST_RAW_AFTER_ACTIVE_LOOP", "cfs[mt*(i+1)-3+l]+=Dd[j]", "cfs[mt*(i+1)-3+l]+=Bd[j]",
               "CFS_INVENTORY", "CFS_NODE", "CFS_OUTSIDE", "CFS_END", "resultsforc(nk,f_cs,rc", "SUMMARY_PRE_OVERRIDE"]
    # The generic V1 INVENTORY substring also appears in KIN_INVENTORY.
    cursor = 0
    for token in ordered:
        if token == "INVENTORY":
            token = 'kind\\\":\\\"INVENTORY'
        cursor = source.index(token, cursor)+len(token)
    for block in (v2.kinematics(), v2.forces()):
        assert v2.COUPLED in block
        assert 'for(on=1;on<=*nk;on++)' in block
        assert "%.17g" in block
        assert "NNEW" not in block and "SFREE" not in block
    assert "cfs[mt*on-3]!=0.0 || cfs[mt*on-2]!=0.0 || cfs[mt*on-1]!=0.0" in v2.forces()
    assert "islavnodeinv[irowd[oe]-1]-1" in v2.kinematics()
    assert "islavnodeinv[irowb[oe]-1]-1" in v2.kinematics()


def test_generated_blocks_are_c_syntax_and_format_correct():
    compiler = shutil.which("gcc")
    if compiler is None:
        pytest.skip("GCC unavailable for syntax-only generated-fragment check")
    prefix = ('#include <stdio.h>\n#define ITGFORMAT "d"\ntypedef int ITG;\n'
              'long mortar_observer_call_id;\nvoid observe(ITG *nk,ITG *ntie,ITG mt, '
              'ITG *jqd,ITG *jqb,ITG *irowd,ITG *irowb,ITG *islavnodeinv, '
              'ITG *nslavnode,ITG *islavnode,char *tieset,double *Dd,double *Bd, '
              'double *b2,double *vold,double *vini,double *gap,double *cfs){\n')
    checked = subprocess.run([compiler, "-x", "c", "-fsyntax-only", "-Wformat", "-Werror=format", "-"],
                             input=prefix+v2.kinematics()+v2.forces()+"}\n", text=True, capture_output=True, check=False)
    assert checked.returncode == 0, checked.stderr


def test_standalone_cli_and_both_generator_hashes(sources, tmp_path):
    source_dir, copied = tmp_path/"source", tmp_path/"scripts"
    source_dir.mkdir()
    copied.mkdir()
    for name, data in sources.items():
        (source_dir/name).write_bytes(data)
    for module in (v1, v2):
        path = Path(module.__file__)
        (copied/path.name).write_bytes(path.read_bytes())
    destination = tmp_path/"new-v2"
    command = [sys.executable, str(copied/"kinematic_patch.py"), str(source_dir), str(destination)]
    assert subprocess.run(command, cwd=tmp_path, capture_output=True, check=False).returncode == 0
    assert {p.name for p in destination.iterdir()} == {*sources, "patch_manifest.json"}
    manifest = json.loads((destination/"patch_manifest.json").read_text())
    sha = lambda raw: hashlib.sha256(raw).hexdigest()
    assert manifest["source_sha256"] == v1.SOURCE_SHA256
    assert manifest["v1_patched_sha256"] == {name: sha(raw) for name, raw in v1.patched_sources(sources).items()}
    assert manifest["patched_sha256"] == {name: sha(raw) for name, raw in v2.patched_sources(sources).items()}
    assert manifest["v1_patch_generator_sha256"] == sha(Path(v1.__file__).read_bytes())
    assert manifest["patch_generator_sha256"] == manifest["v2_patch_generator_sha256"] == sha(Path(v2.__file__).read_bytes())
    assert {name: (source_dir/name).read_bytes() for name in sources} == sources
    assert subprocess.run(command, cwd=tmp_path, capture_output=True, check=False).returncode != 0

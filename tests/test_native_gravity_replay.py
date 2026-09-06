import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from fea.native_gravity_replay import (
    GRAVITY,
    IMAGE,
    corrected_residual,
    freeze_sources,
    isolated_environment,
    save,
    verify_origins,
)


def test_gravity_delta_sign_deformed_position_and_ramp():
    original = {"time":.5,"force_residual_n":[0,0,1],"moment_residual_nmm":[3,-2,0],
                "global_gate_pass":False}
    result = corrected_residual({1:(1,2,0)},{1:(1,1,0)},{1:2/GRAVITY},original)
    assert result["delta_gravity_force_n"] == pytest.approx((0,0,-1))
    assert result["delta_gravity_moment_nmm"] == pytest.approx((-3,2,0))
    assert result["candidate_force_residual_n"] == pytest.approx((0,0,0))
    assert result["candidate_moment_residual_nmm"] == pytest.approx((0,0,0))
    assert result["candidate_global_gate_pass"]
    assert not original["global_gate_pass"]
    assert result["original"] == original
    with pytest.raises(ValueError,match="Incomplete"):
        corrected_residual({1:(1,2,0)},{},{1:1},original)
    with pytest.raises(ValueError,match="Nonfinite"):
        corrected_residual({1:(1,2,0)},{1:(0,0,0)},{1:math.nan},original)
    with pytest.raises(ValueError,match="Published gate"):
        corrected_residual({1:(1,2,0)},{1:(0,0,0)},{1:1},{**original,"global_gate_pass":True})


def test_straight_and_curved_native_gravity_in_immutable_gmsh():
    if not shutil.which("docker") or subprocess.run(["docker","image","inspect",IMAGE],
                                                    capture_output=True,timeout=10,check=False).returncode:
        pytest.skip("Immutable local Gmsh image required")
    code = '''
from fea.native_gravity_replay import native_volume_weights
from fea.floor_contact import integrated_weights
xyz = [(0,0,0),(1,0,0),(0,1,0),(0,0,1),(.5,0,0),(.5,.5,0),(0,.5,0),(0,0,.5),(.5,0,.5),(0,.5,.5)]
nodes = dict(enumerate(xyz,1))
elements = {1:tuple(nodes)}
native = native_volume_weights(nodes,elements)
exact = integrated_weights(elements,nodes)
assert max(abs(native[n]-exact[n]) for n in nodes) < 1e-12
nodes[5] = (.5,-.04,.02)
nodes[9] = (.52,.01,.55)
native = native_volume_weights(nodes,elements)
exact = integrated_weights(elements,nodes)
assert max(abs(native[n]-exact[n]) for n in nodes) > 1e-6
'''
    result = subprocess.run(["docker","run","--rm","--network=none","--read-only","--memory=2g","--cpus=2",
                             "--tmpfs","/tmp:size=128m","-e","PYTHONDONTWRITEBYTECODE=1",
                             "-v",f"{Path.cwd()}:/sources:ro","-w","/sources",IMAGE,
                             "timeout","--kill-after=5s","45s","python3","-c",code],
                            capture_output=True,text=True,timeout=60,check=False)
    assert result.returncode == 0, result.stdout+result.stderr


def test_actual_competing_regular_fea_package_cannot_override_frozen_sources(tmp_path,monkeypatch):
    hashes = freeze_sources(tmp_path)
    save(tmp_path/"launch.json",{"sources_sha256":hashes})
    competing = tmp_path/"competing/fea"
    competing.mkdir(parents=True)
    (competing/"__init__.py").write_text("raise RuntimeError('competing package executed')\n")
    monkeypatch.setenv("PYTHONPATH",str(competing.parent))
    command = [sys.executable,"-m","fea.native_gravity_replay","--verify-origins",str(tmp_path)]
    package = tmp_path/"sources/fea/__init__.py"
    # Reproduce the original namespace-package launch with inherited PYTHONPATH.
    package.rename(package.with_suffix(".disabled"))
    original = subprocess.run(command,cwd=tmp_path/"sources",env=dict(os.environ),
                              capture_output=True,text=True,timeout=10,check=False)
    assert original.returncode and "competing package executed" in original.stderr
    package.with_suffix(".disabled").rename(package)
    assert "PYTHONPATH" not in isolated_environment()
    fixed = subprocess.run(command,cwd=tmp_path/"sources",env=isolated_environment(),
                           capture_output=True,text=True,timeout=10,check=False)
    assert fixed.returncode == 0, fixed.stderr
    assert "loaded_sha256" in fixed.stdout
    with pytest.raises(ValueError,match="source identity"):
        verify_origins(tmp_path)  # Current repository imports are not frozen imports.

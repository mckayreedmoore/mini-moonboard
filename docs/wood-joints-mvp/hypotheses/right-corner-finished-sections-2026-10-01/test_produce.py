from __future__ import annotations

import hashlib
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "right_finished_sections_producer_test", Path(__file__).with_name("produce.py")
)
assert SPEC is not None and SPEC.loader is not None
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def test_source_pin_refuses_changed_bytes_sizes_and_paths_outside_root(tmp_path):
    path = tmp_path / "source.json"
    raw = b'{"saved": true}\n'
    path.write_bytes(raw)
    record = {
        "path": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }
    assert P.verify_pin(tmp_path, record) == record
    with pytest.raises(ValueError, match="pinned size changed"):
        P.verify_pin(tmp_path, {**record, "size_bytes": len(raw) + 1})
    path.write_bytes(b'{"saved": false}\n')
    with pytest.raises(ValueError, match="pinned source changed"):
        P.verify_pin(tmp_path, record)
    with pytest.raises(ValueError, match="pin escapes root"):
        P.verify_pin(tmp_path, {**record, "path": "../outside.json"})


def test_source_pin_merge_preserves_one_exact_binding_and_refuses_conflicts():
    record = {"path": "source", "sha256": "a" * 64, "size_bytes": 2}
    assert P.merge_pins([record], [{**record, "roles": ["input"]}]) == [record]
    with pytest.raises(ValueError, match="conflicting source pin"):
        P.merge_pins([record], [{**record, "sha256": "b" * 64}])


def test_source_only_cli_refuses_missing_frozen_closure_without_geometry(tmp_path):
    folder = (
        tmp_path
        / "docs/wood-joints-mvp/hypotheses/right-corner-finished-sections-2026-10-01"
    )
    folder.mkdir(parents=True)
    target = folder / "produce.py"
    shutil.copyfile(Path(P.__file__), target)
    result = subprocess.run(
        [sys.executable, str(target), "--plan-only"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert result.stdout == ""
    assert "right finished-section source join refused" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (folder / "sections.json").exists()


def test_deterministic_json_refuses_nonfinite_values():
    assert P.canonical({"b": 2, "a": 1}) == P.canonical({"a": 1, "b": 2})
    with pytest.raises(ValueError):
        P.canonical({"force": float("nan")})


def test_refused_geometric_query_retains_the_exact_plane_without_fabricated_properties():
    plane = {
        "plane_id": "terminal",
        "member_id": "member",
        "plane_origin_global_xyz_mm": [1.0, 2.0, 3.0],
        "grain_axis_global_xyz": [1.0, 0.0, 0.0],
        "section_u_global_xyz": [0.0, 1.0, 0.0],
        "section_v_global_xyz": [0.0, 0.0, 1.0],
        "source_identities": [{"identity_key": "load:member:node:7"}],
    }

    class RefusingKernel:
        class SectionGeometryError(ValueError):
            pass

        @classmethod
        def section_properties(cls, shape, origin, grain, u, v, **kwargs):
            assert origin == plane["plane_origin_global_xyz_mm"]
            raise cls.SectionGeometryError("no positive-area section")

    result = P.query_section(RefusingKernel, object(), plane)
    assert result["plane_origin_global_xyz_mm"] == plane["plane_origin_global_xyz_mm"]
    assert result["source_identities"] == plane["source_identities"]
    assert result["properties"] is None
    assert result["status"] == "REFUSED_FINISHED_SECTION_QUERY"
    assert result["kernel_refusal_reason"] == "no positive-area section"

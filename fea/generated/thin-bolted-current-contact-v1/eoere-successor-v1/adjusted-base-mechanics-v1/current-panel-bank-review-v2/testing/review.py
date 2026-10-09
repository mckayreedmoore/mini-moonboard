"""Independent cheap panel-source review; no actual BREP, real bank, q or solve.

Run from any directory with the repository's shared Python environment. The
published tests run in separate processes so their import-absence assertions
retain their intended scope. All extra operators use the existing tiny fixture.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parents[2]
BANK = BASE / "current-panel-bank-v1"
FIX = BANK / "review-fix-v2"
PINS = {
    BANK / "panel_operators.py": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
    BANK / "test_panel_operators.py": "dd48189121a3aef78c60a5eb5677f789ac45a91c7fc42ebb7822442a0986c0c1",
    BANK / "method-receipt.json": "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2",
    FIX / "cli.py": "6502e109fad6365ed30a31029a24fccdc0ae44826add029fc540f3d42c9f740e",
    FIX / "test_cli.py": "f3881893d012428903af353be4ea9c4070edd8d8e16198366293848109c3f934",
    FIX / "check_source_seam.py": "e9c3359e8b3ece581014e59027ee742144455f784635edefc65803df94e5ab74",
    FIX / "method-receipt.json": "4904adf8dde8bf87c46cfc189c791cd65c6cc91a1cb3329daa28eb738320509a",
    BASE / "extended-cleat-intake-v1/export.py": "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb",
    BASE / "parent-authority-v1/extended-cleat-manifest.json": "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_pins():
    for path, expected in PINS.items():
        assert sha(path) == expected, str(path)


def load(path, label):
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def subprocess_check(arguments, cwd=ROOT):
    result = subprocess.run([sys.executable, *arguments], cwd=cwd, text=True,
                            capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr + result.stdout
    return {"command": [sys.executable, *arguments], "exit_code": result.returncode,
            "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def forbidden(*args, **kwargs):
    raise AssertionError("actual BREP, real panel bank or q forbidden in this review")


def synthetic_checks():
    import cadquery as cq
    import numpy as np

    with patch.object(cq.Shape, "importBrep", side_effect=forbidden) as importer:
        fixture = load(BANK / "test_panel_operators.py", "independent_panel_test_fixtures")
        m = fixture.m
        sources = fixture.sources.__wrapped__()
        plan, prior, current, moved, data = fixture.current_data(sources)
        pins = {"fixture": "1" * 64}
        loader_rejections = []
        mutations = {
            "missing_observation": lambda d: d["finished_body_observations"].pop(),
            "duplicate_observation": lambda d: d["finished_body_observations"].append(copy.deepcopy(d["finished_body_observations"][0])),
            "wrong_observed_source_path": lambda d: d["finished_body_observations"][0]["source"].update(path="wrong.brep"),
            "wrong_observed_source_sha": lambda d: d["finished_body_observations"][0]["source"].update(sha256="e" * 64),
            "negative_volume": lambda d: d["finished_body_observations"][0].update(volume_mm3=-1.),
            "infinite_volume": lambda d: d["finished_body_observations"][0].update(volume_mm3=float("inf")),
            "short_COM": lambda d: d["finished_body_observations"][0].update(center_xyz_mm=[0., 0.]),
            "infinite_COM": lambda d: d["finished_body_observations"][0].update(center_xyz_mm=[0., float("inf"), 0.]),
            "wrong_geometry": lambda d: d["geometry"].update(sha256="0" * 64),
            "contradictory_pin": lambda d: d["source_sha256"].update(fixture="0" * 64),
            "wrong_aperture": lambda d: d["current_panel_machining_descriptors"]["features"][0].update(diameter_mm=6.),
            "wrong_screw": lambda d: d["hillman_rows"][0]["source_screw_descriptor"].update(receiver="wrong"),
            "duplicate_panel_owner": lambda d: d["panel_ids"].__setitem__(0, d["panel_ids"][1]),
        }
        with patch.object(m, "read_sources", return_value=(plan, prior, current, moved, pins)), \
             patch.object(m.raised, "verify", return_value=None), \
             patch.object(m.raised, "prepare_panel_operators", side_effect=forbidden) as loader:
            assert m.load_projection_inputs(data)["finished_stock"]
            for name, mutate in mutations.items():
                altered = copy.deepcopy(data)
                mutate(altered)
                try:
                    m.prepare_panel_operators(altered)
                except ValueError:
                    loader_rejections.append(name)
                except AssertionError as exc:
                    raise AssertionError("real loader reached for malformed input: " + name) from exc
                else:
                    raise AssertionError("malformed production input accepted: " + name)
            assert loader.call_count == 0

        # Every owner gets a distinct rotation and translation. Existing tests
        # use identity charts, so this checks current local-XY routing separately.
        panels = fixture.toy_bank(prior)
        old_K = {name: panel["K"].copy() for name, panel in panels.items()}
        old_moments = {}
        for name, panel in panels.items():
            xy, area = m.mass.mass_only_quadrature(panel)
            old_moments[name] = area @ xy
        world_prior, world_current = copy.deepcopy(prior), copy.deepcopy(current)
        rotations, translations = {}, {}
        for index, name in enumerate(m.plate.PANELS):
            ax, ay, az = .11 * (index + 1), -.19 * (index + 1), .23 * (index + 1)
            rx = np.array([[1., 0., 0.], [0., math.cos(ax), -math.sin(ax)], [0., math.sin(ax), math.cos(ax)]])
            ry = np.array([[math.cos(ay), 0., math.sin(ay)], [0., 1., 0.], [-math.sin(ay), 0., math.cos(ay)]])
            rz = np.array([[math.cos(az), -math.sin(az), 0.], [math.sin(az), math.cos(az), 0.], [0., 0., 1.]])
            rotations[name], translations[name] = rz @ ry @ rx, np.array([110. + 30. * index, -53. * index, 170. + 41. * index])
        for metadata in (world_prior, world_current):
            for row in metadata["panel_machining"]["features"]:
                r, t = rotations[row["panel"]], translations[row["panel"]]
                row["start_xyz_mm"] = (r @ row["start_xyz_mm"] + t).tolist()
                row["direction_xyz"] = (r @ row["direction_xyz"]).tolist()
            for row in metadata["screw_axes"]:
                r, t = rotations[row["panel"]], translations[row["panel"]]
                row["origin_xyz_mm"] = (r @ row["origin_xyz_mm"] + t).tolist()
                row["direction_xyz"] = (r @ row["direction_xyz"]).tolist()
        for name, panel in panels.items():
            r, t = rotations[name], translations[name]
            panel["geometry"].update(origin=t, axes=r, inward=-r[:, 2])
            panel["holes"] = [{**h, "xy_mm": m.plate.local_xy(h["start_xyz_mm"], panel["geometry"]).tolist()}
                              for h in world_prior["panel_machining"]["features"] if h["panel"] == name]
        rows = m.refresh_bank(panels, world_current, moved)
        worst_direct_relative, worst_wrench_error, worst_mass_moment_error = 0., 0., 0.
        checked_screws = 0
        reference = np.array([13., -27., 41.])
        force = np.array([3., -2., 4.])
        for name, panel in panels.items():
            direct = m.raised.direct_reference_matrix(panel)
            relative = float(np.max(abs(panel["K"] - direct))) / max(1., float(np.max(abs(direct))))
            worst_direct_relative = max(worst_direct_relative, relative)
            assert relative < 2e-10
            if name not in m.CHANGED:
                assert np.array_equal(panel["K"], old_K[name])
            rigid = m.mass.rigid_modes(panel, reference=reference)
            for index, screw in enumerate(panel["screws"]):
                local_rows = np.vstack([panel[key][index] for key in ("screw_u", "screw_v", "screw_w")])
                wrench = rigid.T @ local_rows.T @ (panel["geometry"]["axes"].T @ force)
                expected = np.r_[force, np.cross(np.asarray(screw["origin_xyz_mm"]) - reference, force)]
                worst_wrench_error = max(worst_wrench_error, float(np.max(abs(wrench - expected))))
                assert np.allclose(wrench, expected, atol=2e-10, rtol=0.)
                checked_screws += 1
            xy, area = m.mass.mass_only_quadrature(panel)
            count = sum(s["axis_id"] in moved for s in panel["screws"])
            expected = np.array([count * 39.2 * np.pi * 2.5 ** 2, 0.])
            error = float(np.max(abs(area @ xy - old_moments[name] - expected)))
            worst_mass_moment_error = max(worst_mass_moment_error, error)
            assert error < 1e-8
            assert not any(k.startswith("contact_") or k in {"q", "support_bounds"} for k in panel)
        assert importer.call_count == 0
        return {"tiny_chart_DOFs": 48, "distinct_rotated_translated_owner_charts": 6,
                "screw_virtual_work_checks": checked_screws, "exact_unchanged_K_blocks": 3,
                "delta_direct_max_relative_error": worst_direct_relative,
                "virtual_work_max_wrench_component_error": worst_wrench_error,
                "net_mass_first_moment_max_component_error_mm3": worst_mass_moment_error,
                "malformed_inputs_rejected_before_real_bank_loader": loader_rejections,
                "real_bank_loader_calls": 0, "guarded_BREP_import_calls": 0}


CLI_HARNESS = r"""
import importlib.util,json,pathlib,sys,types
from unittest.mock import patch
s=importlib.util.spec_from_file_location('independent_panel_cli',sys.argv[1])
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
mode=sys.argv[2]
if mode=='real_source_metadata':
 import cadquery as cq
 original=m.load_bank
 def forbidden(*args,**kwargs):raise AssertionError('BREP/real K forbidden')
 def load():
  bank=original()
  bank.raised.prepare_panel_operators=forbidden
  bank.raised.saved.reuse_panel_operators=forbidden
  return bank
 m.load_bank=load
 with patch.object(cq.Shape,'importBrep',side_effect=forbidden) as guard:
  m.main(['--out',sys.argv[3]])
  assert guard.call_count==0
elif mode=='bank_digest_failure':
 m.BANK=pathlib.Path(sys.argv[4])
 m.main(['--out',sys.argv[3]])
else:
 def load():
  if mode=='interrupt':raise KeyboardInterrupt('stub interruption')
  if mode=='system_exit':raise SystemExit('stub exit')
  return types.SimpleNamespace(read_sources=lambda: ({},None,{},[],{}),
   input_record=lambda *args:{'value':float('nan') if mode=='serialization_failure' else True},
   raised=types.SimpleNamespace(RELEASE={'fabrication_released':False}))
 m.load_bank=load
 original=pathlib.Path.read_bytes
 def changed(path):return b'changed-source' if path==m.OWN else original(path)
 if mode=='own_source_changed':
  with patch.object(pathlib.Path,'read_bytes',changed):m.main(['--out',sys.argv[3]])
 else:m.main(['--out',sys.argv[3]])
"""


def extra_cli_checks():
    with tempfile.TemporaryDirectory(prefix="panel-testing-review-") as scratch:
        directory = Path(scratch)
        out = directory / "source-plan.json"
        result = subprocess.run([sys.executable, "-c", CLI_HARNESS, str(FIX / "cli.py"),
                                 "real_source_metadata", str(out)], cwd=directory,
                                text=True, capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr
        plan = json.loads(out.read_text())
        assert plan["production_bank_prepared"] is False
        assert plan["metadata_only_no_K_q_or_contact_construction"] is True
        assert not any(plan["release"].values())
        assert plan["source_inputs"]["optional_2026_extra"] is False
        assert len(plan["source_inputs"]["finished_panel_solids"]) == 6
        assert len(plan["source_inputs"]["screw_axis_ids"]) == 66
        assert plan["source_sha256"][str((FIX / "cli.py").relative_to(ROOT))] == PINS[FIX / "cli.py"]
        failed_modes = {}
        scratch_bank = directory / "different-bank.py"
        scratch_bank.write_text("raise AssertionError('must not import')\n")
        for mode, expected_type in (("serialization_failure", "ValueError"), ("interrupt", "KeyboardInterrupt"),
                                    ("system_exit", "SystemExit"), ("bank_digest_failure", "ValueError"),
                                    ("own_source_changed", "ValueError")):
            output = directory / (mode + ".json")
            result = subprocess.run([sys.executable, "-c", CLI_HARNESS, str(FIX / "cli.py"),
                                     mode, str(output), str(scratch_bank)], cwd=directory,
                                    text=True, capture_output=True, timeout=15)
            assert result.returncode != 0
            report = json.loads(output.read_text())
            assert report["status"] == "FAILED_RESERVED_OUTPUT_RETAINED"
            assert report["production_bank_prepared"] is False
            assert report["exception_type"] == expected_type
            assert report["source_sha256"][str((FIX / "cli.py").relative_to(ROOT))] == PINS[FIX / "cli.py"]
            failed_modes[mode] = {"exception_type": expected_type, "reserved_failure_JSON_retained": True}
        return {"real_metadata_CLI_with_external_CWD_passed": True,
                "real_metadata_source_pin_count": len(plan["source_sha256"]),
                "BREP_and_real_bank_loader_guarded": True, "failure_paths": failed_modes}


def main():
    verify_pins()
    tests = [subprocess_check(["-m", "pytest", str(BANK / "test_panel_operators.py"), "-q"]),
             subprocess_check(["-m", "pytest", str(FIX / "test_cli.py"), "-q"])]
    seam_run = subprocess_check([str(FIX / "check_source_seam.py")])
    seam = json.loads(seam_run["stdout"])
    synthetic, cli = synthetic_checks(), extra_cli_checks()
    verify_pins()
    report = {
        "schema": "eoere_current_off_panel_independent_testing_review/v2",
        "status": "SOURCE_STUB_AND_SYNTHETIC_TESTING_REVIEW_PASSED_PRODUCTION_DEFERRED",
        "confirmed_substantial_findings": [],
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
        "source_hashes_unchanged_before_after": True,
        "published_tests_in_isolated_processes": tests,
        "exact_current_source_seam": seam,
        "independent_synthetic_checks": synthetic,
        "independent_CLI_checks": cli,
        "coverage_and_limits": [
            "18 original checks and seven corrected CLI checks reproduced in separate processes.",
            "Original metadata-only admission, own-source observation/pin/aperture/screw rejection, synthetic delta/direct stiffness, exact unchanged K, screw work and mass first moments are exercised.",
            "Additional six rotated/translated 48-DOF charts check local-XY routing and all 66 global screw virtual-work wrenches.",
            "Malformed current observations reject before the real bank loader; finite COM is an input requirement, not an independently verified geometric COM.",
            "Actual CLI source-only metadata succeeds from an external directory; additional serialization, interruption, exit and source-hash failures retain valid failure JSON.",
            "Source seam check matches own six panel sources, 66 screw descriptors and 340 apertures against current frozen exporter bdfa95b4; original stale receipt remains frozen.",
            "Library cadquery was imported under a guarded Shape.importBrep. No actual BREP import, actual panel/frame K, historical q load, native solve or browser work occurred.",
            "The direct K comparisons reuse frozen numerical primitives; they check delta routing within that method and do not independently qualify the plate model or actual panel resistance.",
            "The source-admission proof is metadata/projection evidence. It is not independent authentication of runtime panel K/mass/screw arrays or a current structural field.",
            "Real current observed volume/COM extraction, parent-owned frozen inputs/readiness, real three-panel bank construction, fresh contacts/loads/response and independent admission remain deferred.",
        ],
        "production_bank_prepared": False,
        "actual_BREP_import_or_real_K_q_native_solve": False,
        "release": {name: False for name in ("candidate_accepted", "capacity_established", "complete_joint_acceptance",
                                             "fabrication_released", "structural_released", "climbing_released")},
        "tool_versions": {"python": sys.version.split()[0], **{name: importlib.metadata.version(name)
                           for name in ("numpy", "scipy", "pytest", "cadquery")}},
        "retention": "Keep this compact review code/receipt active with the source-method packet; all temporary CLI outputs were removed with their private temporary directory. No archive/prune operation occurred.",
    }
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output),
                      "bytes": output.stat().st_size, "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()

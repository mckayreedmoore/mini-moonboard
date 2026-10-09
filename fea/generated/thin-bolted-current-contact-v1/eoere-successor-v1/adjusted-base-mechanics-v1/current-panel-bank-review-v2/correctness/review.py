"""Independent cheap correctness probes; no real BREP, saved K, q or solver.

Run from the repository with `uv run python PATH_TO_THIS_FILE`.
The original test fixtures provide the synthetic 48-DOF charts; the numerical
operators remain the frozen production primitives.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

import cadquery as cq
import numpy as np

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parents[2]
BANK = BASE / "current-panel-bank-v1"
TARGETS = {
    BANK / "panel_operators.py": "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b",
    BANK / "test_panel_operators.py": "dd48189121a3aef78c60a5eb5677f789ac45a91c7fc42ebb7822442a0986c0c1",
    BANK / "method-receipt.json": "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2",
    BANK / "review-fix-v2/cli.py": "6502e109fad6365ed30a31029a24fccdc0ae44826add029fc540f3d42c9f740e",
    BANK / "review-fix-v2/test_cli.py": "f3881893d012428903af353be4ea9c4070edd8d8e16198366293848109c3f934",
    BANK / "review-fix-v2/check_source_seam.py": "e9c3359e8b3ece581014e59027ee742144455f784635edefc65803df94e5ab74",
    BANK / "review-fix-v2/method-receipt.json": "4904adf8dde8bf87c46cfc189c791cd65c6cc91a1cb3329daa28eb738320509a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_targets():
    for path, digest in TARGETS.items():
        assert sha(path) == digest, str(path)


def load(path, label):
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(call, expected=ValueError):
    try:
        call()
    except expected:
        return
    raise AssertionError("expected rejection: " + expected.__name__)


def rotated_chart_probe(t):
    m = t.m
    original = t.sources.__wrapped__()
    prior, base, extension, _ = [copy.deepcopy(value) for value in original]
    transforms = {}
    for index, name in enumerate(m.plate.PANELS):
        angle = math.radians(11 + index * 13)
        c, s = math.cos(angle), math.sin(angle)
        transforms[name] = (np.array([170. + 31*index, -83. + 19*index, 271. - 23*index]),
                            np.array([[1., 0., 0.], [0., c, -s], [0., s, c]]))
    for metadata in (prior,):
        for feature in metadata["panel_machining"]["features"]:
            origin, axes = transforms[feature["panel"]]
            feature["start_xyz_mm"] = (origin + axes @ feature["start_xyz_mm"]).tolist()
            feature["direction_xyz"] = (axes @ feature["direction_xyz"]).tolist()
    for metadata in (prior, base):
        for screw in metadata["screw_axes"]:
            origin, axes = transforms[screw["panel"]]
            screw["origin_xyz_mm"] = (origin + axes @ screw["origin_xyz_mm"]).tolist()
            screw["direction_xyz"] = (axes @ screw["direction_xyz"]).tolist()
    extension["screw_axes"] = copy.deepcopy(base["screw_axes"])
    old = {"hillman_rows": [{"source_screw_descriptor": copy.deepcopy(s)} for s in prior["screw_axes"]]}
    current, moved = m.compose_panel_metadata(prior, base, extension, old)
    panels = t.toy_bank(original[0])
    before_K, before_moment, before_area = {}, {}, {}
    for name, panel in panels.items():
        origin, axes = transforms[name]
        panel["geometry"].update(origin=origin, axes=axes, inward=-axes[:, 2])
        panel["holes"] = [{**row, "xy_mm": m.plate.local_xy(row["start_xyz_mm"], panel["geometry"]).tolist()}
                          for row in prior["panel_machining"]["features"] if row["panel"] == name]
        panel["K"] = m.raised.direct_reference_matrix(panel)
        before_K[name] = panel["K"].copy()
        xy, area = m.mass.mass_only_quadrature(panel)
        before_moment[name], before_area[name] = area @ xy, float(area.sum())
    rows = m.refresh_bank(panels, current, moved)
    maximum_direct_relative_error = 0.
    maximum_rigid_work_error = 0.
    maximum_first_moment_error = 0.
    reference = np.array([-17., 29., 53.])
    force = np.array([3., -2., 4.])
    for name, panel in panels.items():
        assert panel["K"].shape == (48, 48)
        if name in m.CHANGED:
            direct = m.raised.direct_reference_matrix(panel)
            error = float(abs(direct - panel["K"]).max()) / max(1., float(abs(direct).max()))
            maximum_direct_relative_error = max(maximum_direct_relative_error, error)
            assert error < 2e-10
            assert not np.array_equal(panel["K"], before_K[name])
        else:
            assert np.array_equal(panel["K"], before_K[name])
        assert not any(k.startswith("contact_") or k in {"q", "support_bounds"} for k in panel)
        rigid = m.mass.rigid_modes(panel, reference)
        for index, screw in enumerate(panel["screws"]):
            rows_local = np.vstack([panel[k][index] for k in ("screw_u", "screw_v", "screw_w")])
            wrench = rigid.T @ rows_local.T @ (panel["geometry"]["axes"].T @ force)
            expected = np.r_[force, np.cross(np.asarray(screw["origin_xyz_mm"]) - reference, force)]
            error = float(abs(wrench - expected).max())
            maximum_rigid_work_error = max(maximum_rigid_work_error, error)
            assert error < 1e-9
        xy, area = m.mass.mass_only_quadrature(panel)
        count = sum(s["axis_id"] in moved for s in panel["screws"])
        expected_delta = np.array([count * 39.2 * np.pi * 2.5**2, 0.])
        error = float(abs(area @ xy - before_moment[name] - expected_delta).max())
        maximum_first_moment_error = max(maximum_first_moment_error, error)
        assert error < 1e-7
        assert abs(float(area.sum()) - before_area[name]) < 1e-8
        assert abs(panel["mass_row"].sum() - 1.) < 1e-12
    assert sum(row["hole_count"] for row in rows) == 340
    assert sum(row["screw_count"] for row in rows) == 66
    return {"synthetic_chart_DOF_each": 48, "synthetic_charts": 6,
            "changed_K_direct_comparisons": 3, "unchanged_K_exact_comparisons": 3,
            "global_screw_wrench_comparisons": 66,
            "maximum_delta_vs_direct_relative_error": maximum_direct_relative_error,
            "maximum_rigid_work_wrench_error_N_Nmm": maximum_rigid_work_error,
            "maximum_net_mass_first_moment_error_mm3": maximum_first_moment_error,
            "old_contact_q_and_support_bounds_removed": True}


def admission_probe(t):
    m = t.m
    plan, prior, current, moved, data = t.current_data(t.sources.__wrapped__())
    pins = {"fixture": "1"*64}
    invalid_routes = []
    with patch.object(m, "read_sources", return_value=(plan, prior, current, moved, pins)), \
         patch.object(m.raised, "verify", return_value=None), \
         patch.object(m.raised, "prepare_panel_operators", side_effect=AssertionError("real K forbidden")):
        for kind in ("missing_observation", "duplicate_observation", "old_geometry", "optional_grid", "source", "volume", "COM", "pin"):
            bad = copy.deepcopy(data)
            if kind == "missing_observation":
                bad["finished_body_observations"].pop()
            elif kind == "duplicate_observation":
                bad["finished_body_observations"].append(copy.deepcopy(bad["finished_body_observations"][0]))
            elif kind == "old_geometry":
                bad["geometry"] = copy.deepcopy(m.BASE_GEOMETRY)
            elif kind == "optional_grid":
                bad["panel_operator_source_inputs"]["optional_2026_extra"] = True
            elif kind == "source":
                bad["finished_body_observations"][0]["source"]["sha256"] = "e"*64
            elif kind == "volume":
                bad["finished_body_observations"][0]["volume_mm3"] += 1.
            elif kind == "COM":
                bad["finished_body_observations"][0]["center_xyz_mm"][0] = float("nan")
            else:
                bad["source_sha256"]["fixture"] = "2"*64
            reject(lambda: m.prepare_panel_operators(bad))
            invalid_routes.append(kind)
    with patch.object(m, "read_sources", return_value=(plan, prior, current, moved, pins)), \
         patch.object(m.raised, "verify", return_value=None), \
         patch.object(m.raised, "prepare_panel_operators", side_effect=lambda: (t.toy_bank(prior), pins, {})):
        panels, projection, returned_pins, proof = m.load_panel_dependencies(data)
        assert len(panels) == len(projection["finished_stock"]) == 6 and returned_pins == pins
        assert m.verify_panel_source_inputs(data, proof)["passed"]
        assert not any(proof["release"].values())
        assert proof["fresh_contact_extractor_required"] and not proof["global_K_or_response_constructed"]
        bad = copy.deepcopy(data)
        bad["finished_body_observations"][0]["center_xyz_mm"][0] += 1.
        reject(lambda: m.verify_panel_source_inputs(bad, proof))
    return {"invalid_routes_rejected_before_loader": invalid_routes,
            "synthetic_dependency_API_and_projection_proof_checked": True,
            "changed_COM_rejected_against_preparation_proof": True,
            "readiness_scope": "Parent-owned extraction, independent source review and run readiness remain external preconditions; panel API checks source/observations only."}


def cli_exception_probe():
    cli = load(BANK / "review-fix-v2/cli.py", "correctness_reserved_panel_cli")
    results = {}
    with tempfile.TemporaryDirectory(prefix="panel-correctness-") as temporary:
        root = Path(temporary)
        for kind in ("KeyboardInterrupt", "serialization_error"):
            out = root / (kind + ".json")
            if kind == "KeyboardInterrupt":
                loader = patch.object(cli, "load_bank", side_effect=KeyboardInterrupt("stub interrupt"))
                expected = KeyboardInterrupt
            else:
                stub = SimpleNamespace(read_sources=lambda: ({}, None, {}, [], {}),
                    input_record=lambda *_: {"invalid": float("nan")},
                    raised=SimpleNamespace(RELEASE={"fabrication_released": False}))
                loader = patch.object(cli, "load_bank", return_value=stub)
                expected = ValueError
            with loader:
                reject(lambda: cli.main(["--out", str(out)]), expected)
            failure = json.loads(out.read_text())
            assert failure["status"] == "FAILED_RESERVED_OUTPUT_RETAINED"
            assert failure["production_bank_prepared"] is False
            assert failure["exception_type"] == expected.__name__
            assert failure["source_sha256"] == {str(cli.OWN.relative_to(cli.ROOT)): cli.LOADED_SHA}
            with patch.object(cli, "load_bank", side_effect=AssertionError("retry must not load sources")):
                reject(lambda: cli.main(["--out", str(out)]), FileExistsError)
            assert json.loads(out.read_text()) == failure
            results[kind] = "explicit failure retained; retry rejected before sources"
    return results


def check():
    verify_targets()
    with patch.object(cq.Shape, "importBrep", side_effect=AssertionError("BREP forbidden")) as brep_guard, \
         patch.object(np, "load", side_effect=AssertionError("saved operator/response array loading forbidden")) as array_guard:
        t = load(BANK / "test_panel_operators.py", "independent_panel_correctness_fixtures")
        m = t.m
        with patch.object(m.raised, "prepare_panel_operators", side_effect=AssertionError("real bank forbidden")), \
             patch.object(m.raised.saved, "reuse_panel_operators", side_effect=AssertionError("saved bank forbidden")):
            plan, prior, current, moved, pins = m.read_sources()
            receipt = json.loads((BANK / "method-receipt.json").read_text())
            assert receipt["source_inputs"] == m.input_record(plan, current, moved)
            assert receipt["source_pin_count"] == len(pins) == 840
            assert receipt["source_pin_union_canonical_sha256"] == m.canonical(pins)
            source_result = {"exact_current_source_inputs_match_original_receipt": True,
                             "source_pin_count": len(pins), "source_pin_union_canonical_sha256": m.canonical(pins)}
            charts = rotated_chart_probe(t)
        admission = admission_probe(t)
        exceptions = cli_exception_probe()
        assert brep_guard.call_count == array_guard.call_count == 0
    verify_targets()
    return {"schema": "independent_current_panel_correctness_review/v2", "passed": True,
            "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in TARGETS.items()},
            "review_program_sha256": sha(OWN), "source_checks": source_result,
            "rotated_chart_checks": charts, "admission_checks": admission, "CLI_exception_checks": exceptions,
            "guarded_BREP_import_calls": 0, "guarded_saved_array_load_calls": 0,
            "actual_current_panel_frame_K_q_native_browser_executed": False,
            "substantial_confirmed_findings": [],
            "limits": ["All numerical checks use six synthetic 48-DOF charts and frozen primitives.",
                       "No real current bank or current COM observations were evaluated.",
                       "Reviewed method does not establish resistance, structural acceptance or release."]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True, allow_nan=False))

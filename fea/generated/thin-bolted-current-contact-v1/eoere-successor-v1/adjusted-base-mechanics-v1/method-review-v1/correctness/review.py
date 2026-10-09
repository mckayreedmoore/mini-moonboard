"""Independent source and synthetic checks for current descriptor methods."""

from __future__ import annotations

import hashlib
import importlib.abc
import importlib.util
import json
import math
import sys
import tempfile
import traceback
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path.cwd()
OUT = Path(__file__).resolve().parent
RAW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1"
PINS = {}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path, expected=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    actual = sha(path)
    need(expected is None or actual == expected, "frozen source mismatch: " + str(path))
    key = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    need(key not in PINS or PINS[key] == actual, "conflicting pin: " + key)
    PINS[key] = actual
    return path


def read(path, expected=None):
    return json.loads(pin(path, expected).read_bytes())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def index(rows, key):
    result = {row[key]: row for row in rows}
    need(len(result) == len(rows), "duplicate owner")
    return result


class BlockCAD(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "cadquery" or fullname.startswith("cadquery.") or fullname == "OCP" or fullname.startswith("OCP."):
            raise RuntimeError("BLOCKED_GENUINE_CAD_IMPORT:" + fullname)


need("cadquery" not in sys.modules, "review must start without CAD loaded")
sys.meta_path.insert(0, BlockCAD())
export = pin(RAW / "extended-cleat-intake-v1/export.py", "bdfa95b4da8dfcb3d183dcaf59574afdb2f42e938f8e535680739fa0637696bb")
export_receipt = read(RAW / "extended-cleat-intake-v1/verification.json", "e5b8451c7b6d23822b8909378f2df98e6132e16384900ac20b5c3522b5193544")
panel_path = pin(RAW / "current-panel-bank-v1/panel_operators.py", "014f867eac1e9286dee188024544b5853e5cda2aa1cd11037d7aee5a2b29966b")
panel_receipt = read(RAW / "current-panel-bank-v1/method-receipt.json", "72f1d047ddf567fd2053911157be02288c1357477ee3ca429223bb85f9acc0e2")
for receipt in (export_receipt, panel_receipt):
    for path, digest in receipt["source_sha256"].items():
        pin(path, digest)
manifest_path = pin(RAW / "parent-authority-v1/extended-cleat-manifest.json", "458a7f0220e5776fdb53b876b9815715bf278c5b22eea7699824a9919dd6bfe6")
manifest = read(manifest_path)
base_manifest = read(RAW / "parent-authority-v1/adjusted-base-manifest.json", "27220ec69ebe96e0c637d02d74aea1a7732f68d111b9918c973fa8ee954b48c2")
for record in (manifest, base_manifest):
    need(record["parent_model_review_approved"] and record["optional_2026_extra"] is False, "manifest scope")
    need(record["readiness"]["candidate_assembly_or_solve"] is False and record["readiness"]["independent_current_field_admission"] is False, "readiness overclaim")
    need(all(value is False for value in record["release"].values()), "manifest release overclaim")

x = load(export, "independent_current_metadata_export")
p, old, report, panels, export_pins = x.prepare(manifest_path, sha(manifest_path))
for path, digest in export_pins.items():
    pin(path, digest)
need(len(export_pins) == 1076 and x.a.canonical(export_pins) == export_receipt["source_closure"]["canonical_sha256"], "export closure receipt")
parent = x.a.preflight(ROOT / manifest["parent_base_manifest"]["path"], manifest["parent_base_manifest"]["sha256"])
profiles = index(p["gross_raw_timber_rows"], "name")
parent_profiles = index(parent["gross_raw_timber_rows"], "name")
owners = index(p["physical_owner_gravity_descriptors"], "id")
sources = index(report["finished_solids"] + panels, "id")
need(len(profiles) == 22 and len(owners) == 150 and len(sources) == 28, "current owner census")
need({name for name in profiles if profiles[name] != parent_profiles[name]} == x.CLEATS, "gross replacement boundary")
for name in x.CLEATS:
    row, source, owner = profiles[name], sources[name], owners[name]
    need(row["axis"] == [0., 0., 1.] and abs(row["width_mm"]-38.1) < 1e-8 and row["depth_mm"] == 139.7, "cleat stock axes")
    need(abs(row["end"][2]-row["start"][2]-361.1860828293809) < 1e-8, "cleat gross length")
    need(owner["center_xyz_mm"] == source["center_of_mass_xyz_mm"] and owner["own_COM_query_required"] is False, "cleat own source COM")
    need(abs(owner["mass_kg"] - source["volume_mm3"] * p["parameters"]["wood_density_kg_m3"] * 1e-9) < 1e-12, "cleat finished volume mass")
    need(source["raw_polygon_volume_mm3"] < row["width_mm"]*row["depth_mm"]*361.1860828293809, "finished/gross separation")
    need(row["finished_cut_stiffness_or_resistance_qualified"] is False, "finished resistance overclaim")
need(p["hillman_rows"] == parent["hillman_rows"] and p["floor_descriptors"] == parent["floor_descriptors"], "extension changed protected datums")
need(len(p["shaft_descriptors"]) == 100 and len(p["fitting_ports"]) == 88 and len(p["hillman_rows"]) == 66, "protected census")
need(len(p["required_own_wall_queries"]) == 60 and sum(row["receiver"] in x.CLEATS for row in p["required_own_wall_queries"]) == 8, "fresh bore wall obligations")
need(len(p["auxiliary_metal_gravity_descriptors"]) == 274 and sum(len(row["metal_roles"]) for row in p["shaft_descriptors"]) == 500, "gravity role census")
need(p["case_provider"]["fresh_cases_ready"] is False and p["historical_q_forces_or_passes_transferred"] is False, "old response transfer")
need(p["candidate_CAD_K_factorization_q_force_or_native_run_performed"] is False, "source-plan execution claim")
need(len(p["floor_descriptors"]) == 8 and sum(len(row["normal_reference_points_xyz_mm"]) for row in p["floor_descriptors"]) == 32, "floor census")

blocked_import_trace = []
try:
    load(panel_path, "independent_panel_import_boundary")
except RuntimeError as error:
    need(str(error) == "BLOCKED_GENUINE_CAD_IMPORT:cadquery", "unexpected module import failure")
    blocked_import_trace = [{"path": str(Path(frame.filename).relative_to(ROOT)), "line": frame.lineno, "call": frame.name}
        for frame in traceback.extract_tb(error.__traceback__) if Path(frame.filename).is_absolute() and Path(frame.filename).is_relative_to(ROOT)]
else:
    raise ValueError("expected import-boundary observation did not reproduce")
need("cadquery" not in sys.modules, "blocked diagnostic imported CAD")
# Suppress only the unused package initializer. Genuine selected_hardware source
# remains loaded normally; all math and target functions remain the actual code.
package = types.ModuleType("mini_moonboard")
package.__path__ = [str(ROOT / "mini_moonboard")]
sys.modules["mini_moonboard"] = package
for path in ("mini_moonboard/__init__.py", "mini_moonboard/model.py", "mini_moonboard/selected_hardware.py", "fea/current_response_materials.py"):
    pin(path)
m = load(panel_path, "independent_current_panel_metadata")
plan, prior_panel, current, moved, panel_pins = m.read_sources()
for path, digest in panel_pins.items():
    pin(path, digest)
need(len(panel_pins) == 840 and m.canonical(panel_pins) == panel_receipt["source_pin_union_canonical_sha256"], "panel closure receipt")
need(m.input_record(plan, current, moved) == panel_receipt["source_inputs"], "panel source input receipt")
need(current["panel_machining"] == p["current_panel_machining_descriptors"], "export/panel aperture seam")
need(current["screw_axes"] == [row["source_screw_descriptor"] for row in p["hillman_rows"]], "export/panel66 screw seam")
need(index(current["finished_panel_solids"], "id") == index([m.source_binding(row) for row in panels], "id"), "export/panel6 source seam")
need(len(moved) == 10 and len(current["panel_machining"]["features"]) == 340, "current aperture census")
need(set(m.CHANGED) == {"main_lower_right", "main_upper_right", "kicker_right"}, "changed panel owners")

fresh_output_observations = []
with tempfile.TemporaryDirectory(prefix="current-source-fresh-output-review-") as directory:
    temporary = Path(directory)
    path = temporary / "dangling-export.json"
    path.symlink_to(temporary / "missing-target.json")
    calls = []
    with patch.object(sys, "argv", ["export.py", "--manifest", "unused", "--manifest-sha256", "unused", "--extract", "--out", str(path)]), patch.object(x, "export_native", lambda *_: (calls.append("native_export_callback_reached") or {})):
        try:
            x.main()
        except FileExistsError:
            pass
        else:
            raise ValueError("expected final exclusive-write rejection")
    need(calls == ["native_export_callback_reached"] and path.is_symlink() and not path.resolve().exists(), "dangling output gate reproduction")
    fresh_output_observations.append({"target": "extended-cleat-intake-v1/export.py:243", "existing_dangling_symlink": True, "callbacks": calls, "final_exclusive_write_rejected": True, "symlink_target_created": False})
    calls = []
    with patch.object(m, "read_sources", lambda: (calls.append("source_plan_callback_reached") or (plan, prior_panel, current, moved, panel_pins))):
        try:
            m.main(["--out", str(path)])
        except FileExistsError:
            pass
        else:
            raise ValueError("expected final panel exclusive-write rejection")
    need(calls == ["source_plan_callback_reached"], "panel dangling output gate reproduction")
    fresh_output_observations.append({"target": "current-panel-bank-v1/panel_operators.py:251", "callbacks": calls, "final_exclusive_write_rejected": True})

seam = panel_receipt["intake_seam"]
need(seam["method_path"] == str(export.relative_to(ROOT)), "seam method path")
need(seam["method_sha256"] != sha(export), "stale seam pin not reproduced")
need(seam["manifest_sha256"] == sha(manifest_path), "seam manifest mismatch")
for path, digest in PINS.items():
    need(sha(ROOT / path) == digest, "source changed during review: " + path)
need("cadquery" not in sys.modules and not any(name == "OCP" or name.startswith("OCP.") for name in sys.modules), "restricted checks imported CAD")
pin(__file__)
findings = [
    {"severity": "medium", "file": str(export.relative_to(ROOT)), "line": 243,
     "title": "Reject dangling output symlinks before native extraction",
     "impact": "Path.exists follows the final symlink. A dangling existing output passes the fresh-output gate and reaches export_native; exclusive open rejects only after extraction. It preserves bytes but can waste the parent-controlled native extraction slot and fails the stated pre-intake rejection boundary. The panel source CLI has the same early-gate gap at line251.",
     "fix": "Reject lexical final-path existence with lstat/is_symlink before source/native work, or exclusively reserve the output before work; retain exclusive final writes. Add a dangling-link synthetic callback rejection check."},
    {"severity": "medium", "file": str((RAW / "current-panel-bank-v1/method-receipt.json").relative_to(ROOT)), "line": 47,
     "title": "Rebind the panel seam evidence to the reviewed exporter bytes",
     "impact": "The seam receipt names exporter7b85a771... while its method path now contains bdfa95b4.... The current metadata composition independently matches, but this frozen receipt does not authenticate the exporter submitted for review.",
     "fix": "Preserve the frozen receipt and source snapshot; issue a source-bound supplement rerunning only the metadata seam against the exact reviewed exporter, manifest and panel-module hashes. No CAD or production panel K is needed."},
]
receipt = {
    "schema": "independent_extended_intake_current_panel_method_correctness_review/v1",
    "status": "TWO_CONFIRMED_CORRECTNESS_FINDINGS",
    "substantial_findings": findings,
    "checks": {
        "export_source_pin_count": len(export_pins), "panel_source_pin_count": len(panel_pins),
        "source_closures_before_after_unchanged": True,
        "metadata_owner_census": {"finished_timber_and_panels": 28, "gross_timber": 22, "physical_owners": 150, "shafts": 100, "fitting_ports": 88, "screws": 66, "apertures": 340},
        "two_extended_gross_blanks_361p186mm_and_finished_mass_COM_separate": True,
        "fresh_wall_queries_required": 60, "fresh_cleat_wall_queries_required": 8,
        "floor_hosts_and_normal_points": [8, 32], "nominal_shaft_metal_roles": 500, "auxiliary_gravity_shares": 274,
        "current_panel_export_source_screw_aperture_seam_matches": True,
        "panel_source_inputs_reproduce_receipt_exactly": True,
        "fresh_output_symlink_reproduction": fresh_output_observations,
        "stale_panel_seam_recorded_sha256": seam["method_sha256"], "current_exporter_sha256": sha(export),
        "blocked_CAD_import_diagnostic_trace": blocked_import_trace,
        "isolated_intake_tests": {"passed": 25, "failed": 0, "pytest_cache_disabled": True},
        "panel_tests_with_unused_package_initializer_suppressed_and_CAD_import_blocker": {"passed": 18, "failed": 0, "cadquery_imported": False},
        "initial_combined_test_observation": {"passed": 41, "failed": 2, "failure_lines": ["test_extended_intake.py:57", "test_extended_intake.py:180"], "reason": "Collecting panel tests imports cadquery through the unused mini_moonboard package initializer. The failures are assertions of module absence, not BRep queries or mathematical failures.", "genuine_cadquery_module_imported_in_that_prior_process": True, "BRep_or_production_operator_execution": False},
    },
    "nonfinding_observations": ["The CAD module import makes combined collection incompatible with the intake module-absence assertions. Isolated frozen intake claims remain true; the panel receipt claims no actual BRep imports, which this observation does not contradict."],
    "limits": [
        "Source metadata and synthetic callbacks only; no production exporter was called.",
        "No BRep/current-panelK/frameK/global/native solve, browser, case construction or force admission executed.",
        "The initial permitted combined tests transitively imported the cadquery module; all subsequent review execution blocks genuine cadquery/OCP imports.",
        "Synthetic panel tests retain the actual target/array helper functions while suppressing the unused mini_moonboard package initializer; no installed dependency or target source changed.",
        "Current-force bridge and physical/joint acceptance remain separate parent-owned duties.",
        "Only this review.py and receipt.json are retained in the exclusive reviewer folder; no shared source, docs, staging or commit changes.",
    ],
    "mechanics_acceptance": False, "physical_release": False,
    "command": [".venv/bin/python", "-B", str(Path(__file__).relative_to(ROOT))],
    "source_sha256": PINS,
}
with (OUT / "receipt.json").open("x") as stream:
    json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
    stream.write("\n")
print(json.dumps({"status": receipt["status"], "receipt_sha256": sha(OUT / "receipt.json"), "source_pin_count": len(PINS)}))

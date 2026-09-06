"""Freeze the first posed moving event; preparation only, never launch a solver."""
import argparse
import copy
import gzip
import hashlib
import io
import json
import math
import sys
import tarfile
import tempfile
import types
from pathlib import Path

from fea import hardware_mass_cache as mass
from fea import moving_hardware_control as control
from fea import moving_hardware_pose as pose
from fea import quiescent_hardware_audit as quiet

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "fea/results/posed_hardware_control/posed-quiet.tar.gz"
ARCHIVE_SHA = "0149053d26aa67e1c5f2d22de7e9b1e058d24f7188ef02324fe3cc6508bb86ea"
DOCUMENT = ROOT / "docs/moving-hardware-control.md"
SECTION = "## Moving comparison protocol — selected, not launched"
EVALUATOR_FILES = ("fea/moving_hardware_balance.py", "fea/moving_hardware_replay.py", "fea/floor_contact_results.py",
                   "tests/test_moving_hardware_balance.py", "tests/test_moving_hardware_replay.py",
                   "fea/moving_hardware_audit.py", "tests/test_moving_hardware_audit.py",
                   "fea/moving_hardware_solve.py", "tests/test_moving_hardware_solve.py")
PROTOCOL = {
    "formal_operator": "native_four_point", "physical_operator_scope": "Separate Gauss8 diagnostic",
    "native_mass_rtol": 5e-6, "native_ke_rtol": 5e-6, "native_ke_floor_over_E_star": 1e-8,
    "body_linear_residual_over_P_star": 1e-3, "body_angular_residual_over_H_star": 1e-3,
    "assembly_linear_drift_over_P_star": 1e-4, "assembly_angular_drift_over_H_star": 1e-4,
    "total_energy_residual_over_E_star": .01,
    "min_endpoint_pair_impulse_over_P_star": 1e-3, "min_endpoint_core_ke_over_E_star": 1e-4,
    "refinement_linear_and_pair_impulse_over_P_star": .01,
    "refinement_angular_and_pair_impulse_over_H_star": .01, "refinement_energy_over_E_star": .01,
    "solver_timeout_seconds": 1800, "outer_timeout_seconds": 1820,
    "refinement": {"initial_dt_s": 5e-8, "total_time_s": 2e-5, "increments": 400,
                   "solver_timeout_seconds": 3600, "outer_timeout_seconds": 3620,
                   "authorization": "Not prepared; requires complete coarse pass and separate explicit selection"},
    "integration": "Trapezoidal signed force/moment vectors at every accepted state, including justified t=0 zeros",
    "initial_force_basis": "Exact separated pose; archived quiet CNUM=0 and zero CF; unchanged velocity-independent linear frictionless law",
    "initial_force_source": "CalculiX2.21 gencontelem_f2f.f:551-560 and springforc_f2f.f:186-200; suppression is in contact generation",
    "positions": "X+U; Hc=H0-c cross P and Mc=M0-c cross F about fixed posed initial washer centre",
    "body_signs": "Washer deltaP-sumJ and deltaH-sumK; independently reconstructed core deltaP+sumJ and deltaH+sumK",
    "energy": "sum(ELKE+ELSE)+CELS-initial_energy; no external work",
    "scope": "Every accepted state; refinement at every matching coarse-grid time; endpoint transfer gates; no structural allowables",
    "incomplete_or_insufficient_transfer": "Inconclusive, not qualification; no automatic rerun, extension or refinement",
}
_SOURCE_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_CONFIG = json.dumps((ARCHIVE_SHA, SECTION, PROTOCOL, EVALUATOR_FILES), sort_keys=True)


def sources():
    own = Path(__file__).read_bytes()
    if control.digest(own) != _SOURCE_HASH or json.dumps((ARCHIVE_SHA, SECTION, PROTOCOL, EVALUATOR_FILES), sort_keys=True) != _CONFIG:
        raise ValueError("Moving event source/configuration changed after import")
    for code in compile(own, str(Path(__file__).resolve()), "exec").co_consts:
        if isinstance(code, types.CodeType) and code.co_name.isidentifier():
            loaded = getattr(sys.modules[__name__], code.co_name, None)
            if not isinstance(loaded, types.FunctionType) or loaded.__code__ != code:
                raise ValueError("Loaded moving event function differs from source")
    for module in (control, pose, quiet, mass, quiet.retained, control.dynamic_momentum):
        if Path(module.__file__).resolve() != ROOT / "fea" / (module.__name__.split(".")[-1] + ".py"):
            raise ValueError("Imported moving event source outside this checkout")
    return {**control.source_snapshot(), **pose.source_snapshot(), **quiet.sources(), **mass.sources(),
            "moving_hardware_event.py": own,
            "test_moving_hardware_event.py": (ROOT / "tests/test_moving_hardware_event.py").read_bytes(),
            **{Path(name).name: (ROOT / name).read_bytes() for name in EVALUATOR_FILES}}


def archived_files(data):
    if control.digest(data) != ARCHIVE_SHA:
        raise ValueError("Passed posed quiet archive identity differs")
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        entries = archive.getmembers()
        if any(not item.isfile() for item in entries) or len({item.name for item in entries}) != len(entries):
            raise ValueError("Unexpected archive member inventory")
        files = {item.name: archive.extractfile(item).read() for item in entries}
    inventory = json.loads(files["members.json"])
    if set(inventory) != set(files) - {"members.json"} or any(control.digest(files[n]) != h for n, h in inventory.items()):
        raise ValueError("Posed quiet archive member hash differs")
    return files


def build_context(files, protocol_text):
    """Replay quiet/proof/mass evidence before changing only the selected event."""
    inputs = {n: files["solve/" + quiet.retained.input_path(n).as_posix()] for n in quiet.INPUTS}
    replayed = quiet.audit(inputs)
    recorded = json.loads(files["audit/report.json"])
    recorded.pop("source_sha256")
    if recorded != json.loads(json.dumps(replayed)) or replayed["status"] != "COMPLETE QUIESCENT OUTPUT GATES PASSED":
        raise ValueError("Archived posed quiet audit does not replay as a complete pass")
    if len(replayed["states"]) != 20 or any(s["CNUM"] != 0 or any(
            p["area_mm2"] != 0 or any(p["force_N"] + p["origin_moment_N_mm"]) for p in s["pairs"].values())
            for s in replayed["states"]):
        raise ValueError("Initial zero-contact evidence differs")
    data = files["prepared/context.json"]
    if data != inputs["context.json"] or files["prepared/quiescent.inp"] != inputs["control.inp"]:
        raise ValueError("Passed quiet preparation identity differs")
    original = json.loads(data)
    if control.deck(original, "quiescent").encode() != inputs["control.inp"]:
        raise ValueError("Passed quiet deck/context differs")
    centred = json.loads(files["prepared/frozen/centred/context.json"])
    proof = json.loads(files["prepared/frozen/pose/report.json"])
    bounds = pose.mesh_clearance(centred)
    if (proof["quadratic_mesh"] != json.loads(json.dumps(bounds)) or not bounds["strictly_separated_selected_surfaces"]
            or original["nodes"] != json.loads(json.dumps(pose.posed_nodes(centred)[0]))):
        raise ValueError("Positive exact-pose proof does not replay")
    cache = json.loads(gzip.decompress(files["mass/blocks.json.gz"]))
    cache_report = json.loads(files["mass/report.json"])
    if (files["mass/context.json"] != data or files["mass/quiescent.inp"] != inputs["control.inp"]
            or control.digest(files["mass/blocks.json.gz"]) != cache_report["blocks_sha256"]):
        raise ValueError("Archived posed mass identity differs")
    masses = mass.validate_cache(cache, data)
    if masses != cache_report["body_mass_tonne"]:
        raise ValueError("Archived posed mass totals differ")
    reference = original["diagnostic_reference_scales"]
    if not math.isclose(reference["reference_mass_tonne"], masses["native_four_point"]["WASHER"], rel_tol=1e-12, abs_tol=0):
        raise ValueError("Unchanged reference mass differs from archived posed operator")
    for state in replayed["states"]:
        for body, expected in masses["native_four_point"].items():
            if abs(state["bodies"][body]["observed_mass_tonne"] / expected - 1) > 5e-6:
                raise ValueError("Archived native body mass comparison differs")
    context = copy.deepcopy(original)
    context["cases"] = {"moving": {**control.DIRECT_MOVING_SETTINGS,
        "initial_velocity_mm_s": {"BOLT_NUT": [0., 0., 0.], "WASHER": [-100., 100., 0.]}}}
    context["integration_intent"] = {"direct_moving": True, "mode": "Fixed-increment coarse moving comparison",
        "expected_fixed_increment_count": 200, "scope": "Preparation only; explicit launch and complete moving audit required"}
    context["moving_protocol"] = copy.deepcopy(PROTOCOL)
    context["moving_protocol"]["document_section"] = protocol_text
    context["moving_protocol"]["document_section_sha256"] = control.digest(protocol_text.encode())
    context["passed_quiet_evidence"] = {"archive_sha256": ARCHIVE_SHA, "audit_status": replayed["status"],
        "context_sha256": control.digest(data), "posed_mass_blocks_sha256": cache_report["blocks_sha256"],
        "reference_scope": "Unchanged exact serialized coordinates/density; archived posed reference retained, not a moving comparison"}
    context["status"] = "PREPARED MOVING EVENT ONLY; NO SOLVER OR MOVING OUTPUT QUALIFICATION"
    context["scope"] = "Two free bodies; first coarse moving numerical comparison only; no strength qualification"
    context["time_step_basis"] = "Predeclared coarse DIRECT 1e-7 s through 2e-5 s; nested-grid diagnostic, not an established stability/accuracy limit"
    context["next_comparison"] = "No refinement preparation until complete coarse pass and separate explicit selection"
    return context


def prepare(parent=ROOT / "fea/generated/moving-hardware-events", *, archive=ARCHIVE, document=DOCUMENT):
    before = sources()
    archive, document = Path(archive), Path(document)
    archive_bytes, document_bytes = archive.read_bytes(), document.read_bytes()
    text = document_bytes.decode()
    if text.count(SECTION) != 1:
        raise ValueError("Unique selected moving protocol section required")
    protocol_text = SECTION + text.split(SECTION, 1)[1]
    context = build_context(archived_files(archive_bytes), protocol_text)
    inputs = {"posed-quiet.tar.gz": archive_bytes, "moving-hardware-control.md": document_bytes}
    context["input_sha256"] = {n: control.digest(b) for n, b in inputs.items()}
    context["source_sha256"] = {n: control.digest(b) for n, b in before.items()}
    context["audit_source_sha256"] = {Path(n).name: context["source_sha256"][Path(n).name] for n in EVALUATOR_FILES}
    deck = control.deck(context, "moving").encode()
    mass.deck_mesh(deck.decode(), context)
    context["deck_sha256"] = {"moving": control.digest(deck)}
    if sources() != before or archive.read_bytes() != archive_bytes or document.read_bytes() != document_bytes:
        raise ValueError("Moving event input/source drift before publication")
    parent = Path(parent)
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="moving-event-", dir=parent))
    frozen = directory / "frozen"
    frozen.mkdir()
    for name, data in {**inputs, **before}.items():
        (frozen / name).write_bytes(data)
    (directory / "moving.inp").write_bytes(deck)
    (directory / "context.json").write_text(json.dumps(context, indent=2, allow_nan=False) + "\n")
    if sources() != before or archive.read_bytes() != archive_bytes or document.read_bytes() != document_bytes:
        raise ValueError("Moving event input/source drift; no launchable freeze")
    (directory / "freeze.json").write_text(json.dumps({"status": context["status"], "files_sha256": {
        p.relative_to(directory).as_posix(): control.digest(p.read_bytes()) for p in directory.rglob("*") if p.is_file()}}, indent=2) + "\n")
    return directory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "fea/generated/moving-hardware-events")
    args = parser.parse_args()
    print(prepare(args.output))

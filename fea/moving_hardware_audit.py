"""Complete coarse moving-run audit; no launcher, solver, or refinement acceptance."""
import argparse
import gzip
import hashlib
import json
import math
import sys
import tempfile
import types
from collections.abc import Mapping
from pathlib import Path

from fea import floor_contact_results
from fea import moving_hardware_balance as balance
from fea import moving_hardware_event as event
from fea import moving_hardware_replay as replay
from fea import moving_hardware_solve as launcher
from fea import quiescent_hardware_audit as quiet

LIMITS = "Complete coarse numerical audit only. Refinement, moving-contact qualification, joint resistance and board safety remain unqualified."
MAX_DAT_BYTES = 1_500_000_000
BUILD_SHA256 = "04b8da67a5edf12c763e03c9a4c3da241375c8d7a37c07eec06e2b31a4622988"
_PATHS = tuple(Path(__file__).resolve().with_name(n) for n in
               ("moving_hardware_audit.py", "moving_hardware_balance.py", "moving_hardware_replay.py", "floor_contact_results.py", "moving_hardware_solve.py"))
_HASHES = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in _PATHS}
_CONFIG = json.dumps((LIMITS, MAX_DAT_BYTES, BUILD_SHA256, balance.GATES, launcher.IMAGE, launcher.BINARY), sort_keys=True)


class FileInputs(Mapping):
    """Stream-hashed inventory; unrequested FRD/log payloads never enter memory."""

    def __init__(self, root):
        self.root = Path(root)
        quiet.require((self.root / "result/control.dat").stat().st_size <= MAX_DAT_BYTES, "DAT exceeds predeclared audit size cap")
        self.hashes = self.scan()

    def scan(self):
        result = {}
        for path in self.root.rglob("*"):
            quiet.require(not path.is_symlink(), "Symlink in audit input inventory")
            if path.is_file():
                with path.open("rb") as stream:
                    result[path.relative_to(self.root).as_posix()] = hashlib.file_digest(stream, "sha256").hexdigest()
        return result

    def __iter__(self):
        return iter(self.hashes)

    def __len__(self):
        return len(self.hashes)

    def __getitem__(self, name):
        expected = self.hashes[name]
        path = self.root / name
        if name == "result/control.dat":
            quiet.require(path.stat().st_size <= MAX_DAT_BYTES, "DAT exceeds predeclared audit size cap")
        value = path.read_bytes()
        quiet.require(event.control.digest(value) == expected, "Input changed since inventory scan")
        return value


def input_hash(files, name):
    return files.hashes[name] if isinstance(files, FileInputs) else event.control.digest(files[name])


def sources():
    quiet.require(json.dumps((LIMITS, MAX_DAT_BYTES, BUILD_SHA256, balance.GATES, launcher.IMAGE, launcher.BINARY), sort_keys=True) == _CONFIG, "Moving audit configuration changed after import")
    for path, module in zip(_PATHS, (sys.modules[__name__], balance, replay, floor_contact_results, launcher), strict=True):
        quiet.require(Path(module.__file__).resolve() == path, "Moving evaluator imported outside checkout")
        data = path.read_bytes()
        quiet.require(event.control.digest(data) == _HASHES[path.name], "Moving evaluator source changed after import")
        for code in compile(data, str(path), "exec").co_consts:
            if isinstance(code, types.CodeType) and code.co_name.isidentifier():
                loaded = getattr(module, code.co_name, None)
                if isinstance(loaded, type):
                    for method in code.co_consts:
                        if isinstance(method, types.CodeType):
                            function = getattr(loaded, method.co_name, None)
                            quiet.require(isinstance(function, types.FunctionType) and function.__code__ == method, "Loaded audit input reader differs from source")
                else:
                    quiet.require(isinstance(loaded, types.FunctionType) and loaded.__code__ == code, "Loaded moving evaluator differs from source")
    quiet.require(balance.cross is floor_contact_results.cross, "Moving evaluator vector binding differs")
    result = event.sources()
    quiet.require(set(_HASHES) <= set(result), "Event omitted moving evaluator sources")
    return result


def common_inputs(files):
    return {n: files["frozen/" + n if n == "context.json" else n if n in ("freeze.json", "launch.json") else "result/" + n]
            for n in quiet.INPUTS}


def identities(files, loaded):
    def record(name):
        return json.loads(files[name])
    def hashes(prefix, inventory):
        for name, expected in inventory.items():
            quiet.require(not Path(name).is_absolute() and ".." not in Path(name).parts, "Unsafe frozen member name")
            quiet.require(input_hash(files, prefix + name) == expected, "Frozen/output inventory hash differs: " + prefix + name)
    freeze, launch, outcome = [record(n) for n in ("freeze.json", "launch.json", "result/exit.json")]
    hashes("frozen/", freeze["inputs_sha256"])
    hashes("result/", outcome["output_sha256"])
    quiet.require({n[7:] for n in files if n.startswith("frozen/")} == set(freeze["inputs_sha256"]), "Frozen inventory is incomplete or has extra files")
    quiet.require({n[7:] for n in files if n.startswith("result/")} == set(outcome["output_sha256"]) | {"exit.json"}, "Native output inventory is incomplete or has extra files")
    context = quiet.identities(common_inputs(files), case="moving")
    quiet.require(files["frozen/control.inp"] == files["result/control.inp"], "Executed moving deck differs")
    prepared = record("frozen/prepared-freeze.json")["files_sha256"]
    quiet.require(prepared["context.json"] == event.control.digest(files["frozen/context.json"])
                  and prepared["moving.inp"] == event.control.digest(files["frozen/control.inp"]), "Prepared moving context/deck differs")
    protocol = context["moving_protocol"]
    quiet.require(all(protocol.get(k) == v for k, v in event.PROTOCOL.items())
                  and all(protocol.get(k) == v for k, v in balance.GATES.items()), "Frozen moving numerical gates/protocol differ")
    quiet.require(context["passed_quiet_evidence"]["archive_sha256"] == event.ARCHIVE_SHA
                  and context["passed_quiet_evidence"]["audit_status"] == "COMPLETE QUIESCENT OUTPUT GATES PASSED", "Passed quiet prerequisite differs")
    quiet.require(context["angular_reference_mm_local"] == [1.001, .7356, 0.], "Fixed posed angular reference differs")
    required_evaluators = {Path(n).name for n in event.EVALUATOR_FILES}
    quiet.require(set(context["audit_source_sha256"]) == required_evaluators, "Prepared evaluator inventory differs")
    for name, data in loaded.items():
        quiet.require(context["source_sha256"].get(name) == event.control.digest(data)
                      and prepared.get("frozen/" + name) == event.control.digest(data)
                      and files["frozen/evaluators/" + name + ".snapshot"] == data, "Current loaded evaluator/source differs from selected event: " + name)
    quiet.require(all(context["audit_source_sha256"][n] == event.control.digest(loaded[n]) for n in required_evaluators), "Audit evaluator identity differs")
    approval = record("frozen/moving-preflight.json")
    quiet.require(approval["case"] == "moving" and approval["inputs_sha256"] == {
        n: h for n, h in freeze["inputs_sha256"].items() if n != "moving-preflight.json"}, "Preflight approved inventory differs")
    quiet.require(approval["evaluator_sha256"] == {
        "evaluators/" + n + ".snapshot": event.control.digest(b) for n, b in loaded.items()}, "Preflight evaluator inventory differs")
    expected = {"moving_hardware_solve.py", "control.inp", "context.json", "build_manifest.json", "prepared-freeze.json", "moving-preflight.json"}
    expected |= set(approval["evaluator_sha256"])
    expected |= {"mass/"+n for n in ("context.json", "prepared-freeze.json", "moving.inp", "report.json", "blocks.json.gz", "hardware_mass_cache.py.snapshot", "dynamic_momentum.py.snapshot")}
    quiet.require(set(freeze["inputs_sha256"]) == expected, "Unexpected coarse frozen inventory")
    for key, name in (("context_sha256", "context.json"), ("deck_sha256", "control.inp"),
                      ("prepared_freeze_sha256", "prepared-freeze.json"),
                      ("mass_report_sha256", "mass/report.json"), ("mass_blocks_sha256", "mass/blocks.json.gz")):
        quiet.require(approval[key] == input_hash(files, "frozen/" + name), "Preflight approval identity differs: " + key)
    quiet.require(approval["passed_quiet_archive_sha256"] == event.ARCHIVE_SHA, "Preflight quiet proof differs")
    quiet.require(files["frozen/moving_hardware_solve.py"] == loaded["moving_hardware_solve.py"]
                  and input_hash(files, "frozen/build_manifest.json") == BUILD_SHA256
                  and freeze["image"] == launcher.IMAGE, "Frozen launcher/build/image differs")
    command = launch["command"]
    quiet.require(freeze["solver_timeout_seconds"] == 1800 and launch["outer_timeout_seconds"] == 1820
                  and command == launcher.command(Path(command[5]).parent.parent, solver_timeout_seconds=1800, case="moving"), "Selected coarse runtime bounds/command differ")
    probe = json.loads(record("result/container-probe.json")["stdout"])[0]
    quiet.require(probe["Name"] == "/" + command[3] and files["result/container.id"].decode().strip() == outcome["owned_container_id"]
                  and outcome["container_stopped_successfully_before_cleanup"] is True, "Owned coarse container differs")
    return context


def mass_cache(files, context):
    report = json.loads(files["frozen/mass/report.json"])
    data = files["frozen/context.json"]
    quiet.require(files["frozen/mass/context.json"] == data
                  and files["frozen/mass/moving.inp"] == files["frozen/control.inp"]
                  and files["frozen/mass/prepared-freeze.json"] == files["frozen/prepared-freeze.json"], "Selected moving mass-cache inputs differ")
    quiet.require(report["case"] == "moving" and report["context_sha256"] == event.control.digest(data)
                  and report["deck_sha256"] == event.control.digest(files["frozen/control.inp"])
                  and report["prepared_freeze_sha256"] == event.control.digest(files["frozen/prepared-freeze.json"])
                  and report["blocks_sha256"] == event.control.digest(files["frozen/mass/blocks.json.gz"]), "Selected mass-cache identity differs")
    for name, digest in report["source_sha256"].items():
        quiet.require(event.control.digest(files["frozen/mass/" + name + ".snapshot"]) == digest, "Mass-cache source snapshot differs")
    quiet.require(report["source_sha256"] == {n: event.control.digest(b) for n, b in event.mass.sources().items()}, "Selected mass-cache source differs from current evaluator")
    cache = json.loads(gzip.decompress(files["frozen/mass/blocks.json.gz"]))
    totals = event.mass.validate_cache(cache, data)
    quiet.require(totals == report["body_mass_tonne"] and cache["gmsh_version"] == report["gmsh_version"], "Mass-cache totals/version differ")
    reference = context["diagnostic_reference_scales"]
    m = totals["native_four_point"]["WASHER"]
    quiet.require(all(math.isclose(reference[k], value, rel_tol=1e-12, abs_tol=0) for k, value in
        (("reference_mass_tonne", m), ("P_star_tonne_mm_s", m*math.sqrt(20000)), ("E_star_N_mm", m*10000), ("H_star_tonne_mm2_s", 57.15*m*math.sqrt(20000)))), "Moving reference scales differ from selected native mass")
    return cache


def audit(files):
    before = sources()
    if not isinstance(files, FileInputs):
        quiet.require(len(files["result/control.dat"]) <= MAX_DAT_BYTES, "DAT exceeds predeclared audit size cap")
    input_hashes = {n: input_hash(files, n) for n in files}
    context = identities(files, before)
    cache = mass_cache(files, context)
    states = replay.reconstruct(files["frozen/context.json"], files["frozen/control.inp"], cache,
                                files["result/control.dat"].decode(), files["result/control.sta"].decode())
    assessed = balance.assess(states, context["diagnostic_reference_scales"], context["angular_reference_mm_local"])
    status = {"NUMERICAL BALANCE GATES FAILED": "COARSE MOVING AUDIT FAILED",
              "NUMERICAL BALANCE INCONCLUSIVE": "COARSE MOVING AUDIT INCONCLUSIVE",
              "NUMERICAL BALANCE GATES PASSED": "COMPLETE COARSE MOVING GATES PASSED; REFINEMENT REQUIRED"}[assessed["status"]]
    final_hashes = files.scan() if isinstance(files, FileInputs) else {n: input_hash(files, n) for n in files}
    quiet.require(input_hashes == final_hashes, "Moving audit input changed during reconstruction")
    quiet.require(sources() == before, "Moving audit source changed during reconstruction")
    return {"status": status, "limits": LIMITS, "balance": assessed,
            "prerequisite_scope": "Hash-bound recorded host preflight approval; this audit does not rerun CAD or the pinned quiet proof",
            "physical_Gauss8": [{"time_s": s["time_s"], "bodies": {n: b["physical_Gauss8"] for n, b in s["bodies"].items()}} for s in states],
            "initial_state_source": states[0]["source"], "accepted_states": len(states)-1,
            "refinement_qualified": False, "input_sha256": input_hashes}


def write_audit(directory, parent):
    before = sources()
    files = FileInputs(directory)
    report = audit(files)
    quiet.require(sources() == before and files.scan() == files.hashes, "Moving audit source/input drift before publication")
    Path(parent).mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix="moving-audit-", dir=parent))
    for name, data in before.items():
        (destination / (name + ".snapshot")).write_bytes(data)
    report["source_sha256"] = {n: event.control.digest(b) for n, b in before.items()}
    (destination / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("fea/generated/moving-hardware-audits"))
    args = parser.parse_args()
    print(write_audit(args.directory, args.output))

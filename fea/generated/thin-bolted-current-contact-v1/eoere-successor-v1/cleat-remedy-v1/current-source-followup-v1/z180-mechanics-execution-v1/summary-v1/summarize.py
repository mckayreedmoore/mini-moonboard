"""Deferred saved-JSON summary of six own unadopted Z180 cases.

Only frozen witness selectors are compiled. No gate, consumer, reducer, field
producer, CAD, operator or solver is imported or called. Parent supplies the
future exact six-case manifest; this module supplies no candidate roster.
"""
import argparse
import ast
import hashlib
import json
import math
import os
import stat
from pathlib import Path
from types import SimpleNamespace

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
PROP = BASE + "cleat-remedy-v1/current-source-followup-v1/"
E = PROP + "z180-mechanics-execution-v1/"
CASES = ("a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear")
SELECTORS = {"path": BASE+"adjusted-base-mechanics-v1/current-component-results-v1/summarize.py",
             "sha256": "0547b984f150bb9bbd4dbe25b50825a12c047de70bcb1d86a267abd58a935735"}
CLOSURE_GUARD = {"path": PROP+"z180-mechanics-inputs-v1/review-fix-v2/descriptor.py",
                 "sha256": "8ab67c15c544ba1cf1f0209020fb87614072c665a8eaa39dc667a23db5b2823a"}
GATE = {"path": E+"review-fix-v2/bridge.py", "sha256": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55"}
CONSUMER = {"path": E+"component-consumer-v1/review-fix-v2/consume.py", "sha256": "791e39cbdfbf80e6a207ca568898c0347e7f400ac428efa84dc65906a8a8cf92"}
GEOMETRY = {
    "report": {"path": PROP+"viewer-revision-v1/runs-v1/export01/layout.json", "sha256": "4886a4bccaee43b93b23e521710b7d8b84dcb7b5ba627ef722694ceb79b7f319"},
    "source_manifest": {"path": E+"parent-sources-v1.json", "sha256": "60167af5e6dc11207bf17df0b62a9c3177d4ec3109531d6e7d3068023eee91c2"},
    "cached_source_export": {"path": PROP+"z180-mechanics-inputs-v1/runs-v1/attempt04/descriptor.json", "sha256": "deccc585f3cc38cc315bf5618cb7ab7007b948e90cec8a4144c04a89cd2275df"},
}
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)
INPUT_SCHEMA = "eoere_exact_unadopted_z180_six_case_summary_inputs/v1"
SCHEMA = "eoere_exact_unadopted_z180_six_case_summary/v1"
SELECTED = ("require", "sha", "canonical", "pick", "maximum", "coarse_findings", "rich_findings")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def decode(raw):
    def pairs(rows):
        value = {}
        for key, item in rows:
            require(key not in value, "duplicate JSON key: "+key)
            value[key] = item
        return value
    def finite(value):
        number = float(value)
        require(math.isfinite(number), "finite JSON numbers required")
        return number
    return json.loads(raw, object_pairs_hook=pairs, parse_float=finite,
                      parse_constant=lambda value: require(False, "nonfinite JSON: "+value))


def merge(pins, extra):
    for path, digest in extra.items():
        require(isinstance(path, str) and isinstance(digest, str) and len(digest) == 64
                and all(c in "0123456789abcdef" for c in digest), "exact source pin required")
        require(path not in pins or pins[path] == digest, "conflicting source pin: "+path)
        pins[path] = digest


def checked(ref, pins):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact path/SHA reference required")
    path = Path(ref["path"])
    require(not path.is_absolute() and ".." not in path.parts and (ROOT/path).resolve().is_relative_to(ROOT), "repository source path required")
    merge(pins, {str(path): ref["sha256"]})
    raw = (ROOT/path).read_bytes()
    require(sha(raw) == ref["sha256"], "exact source bytes differ: "+str(path))
    return raw


def definitions(ref, names, pins, *, assignments=()):
    # Parse these exact authenticated bytes, never a second unverified read.
    raw = checked(ref, pins)
    tree = ast.parse(raw)
    chosen = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names
              or isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
              and node.targets[0].id in assignments]
    require(len(chosen) == len(names)+len(assignments)
            and {n.name for n in chosen if isinstance(n, ast.FunctionDef)} == set(names), "exact checked definitions required")
    namespace = {"hashlib": hashlib, "json": json, "math": math, "Path": Path}
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(ROOT/ref["path"]), "exec"), namespace)  # noqa: S102 -- exact frozen pure definitions only
    return SimpleNamespace(**{name: namespace[name] for name in (*names, *assignments)})


def verify(pins):
    # Reuse the reviewed two-exception absolute provenance guard unchanged.
    guard_pins = {}
    guard = definitions(CLOSURE_GUARD, ("verify_pins",), guard_pins, assignments=("INHERITED_ABSOLUTE_PINS",))
    merge(pins, guard_pins)
    def exact_ref(ref, root):
        require(root == ROOT, "foreign source root")
        checked(ref, {})
    facade = SimpleNamespace(require=require, sha=lambda path: sha(path.read_bytes()), exact_ref=exact_ref)
    guard.verify_pins(facade, pins, ROOT)


def same_ref(value, expected):
    require(isinstance(value, dict) and set(value) in ({"path", "sha256"}, {"path", "sha256", "bytes"})
            and {k: value[k] for k in ("path", "sha256")} == expected, "recorded reference differs")
    if "bytes" in value:
        require(value["bytes"] == (ROOT/expected["path"]).stat().st_size, "recorded byte size differs")


def command_check(command, config, result):
    require(isinstance(command, list) and len(command) > 2
            and Path(command[2]) == ROOT/CONSUMER["path"], "exact corrected consumer command required")
    for flag, expected in (("--config", str(ROOT/config["path"])), ("--config-sha256", config["sha256"]),
                           ("--mode", "both"), ("--samples", "41"), ("--out", str(ROOT/result["path"]))):
        require(command.count(flag) == 1 and command[command.index(flag)+1] == expected, "exact recorded command binding required: "+flag)


def case_records(binding, pins):
    require(set(binding) == {"case_id", "field", "admission", "component"}, "exact per-case reference set required")
    refs = binding["component"]
    require(set(refs) == {"config", "result", "process", "stdout", "stderr"}, "exact combined result/config/process/log set required")
    raw = checked(binding["field"], pins)
    field = decode(raw)
    admission = decode(checked(binding["admission"], pins))
    saved = {key: decode(checked(refs[key], pins)) for key in ("config", "result", "process")}
    for key in ("stdout", "stderr"):
        checked(refs[key], pins)
    config, result, process = (saved[k] for k in ("config", "result", "process"))
    identity = {key: field[key] for key in ("state_id", "case_id", "accessory_placement")}
    require(identity["case_id"] == binding["case_id"] and isinstance(identity["state_id"], str)
            and identity["state_id"].startswith("eoere-z180-fixed-floor-"), "own Z180 case/state required")
    require(all(row.get(key) == value for row in (admission, result) for key, value in identity.items()), "same-state own identity differs")
    require(field["schema"] == "eoere_z180_fixed_floor_candidate/v1"
            and admission["schema"] == "eoere_z180_fixed_floor_independent_field_admission/v1"
            and admission.get("unadopted_z180_equilibrium_and_recovery_pass") is True
            and result["schema"] == "eoere_unadopted_z180_same_state_component_references/v1", "own Z180 schemas/admission required")
    require(all(row["release"] == RELEASE for row in (field, admission, result, config))
            and result["unadopted_proposal"] is True and result["complete_joint_resistance"] is None
            and result["mode"] == "both", "unadopted/null resistance/all-false same-state result required")
    require(admission["input_raw_sha256"] == binding["field"]["sha256"]
            and admission["input_canonical_sha256"] == canonical(field)
            and admission["admission_source_sha256"] == GATE["sha256"]
            and admission["source_path"] == GATE["path"], "exact raw field/admission/gate binding required")
    require(field["source_inputs"]["geometry"] == GEOMETRY
            and field["current_execution"]["geometry"] == GEOMETRY["report"]
            and field["current_execution"]["loaded_driver_path"] == GATE["path"]
            and field["current_execution"]["loaded_driver_sha256"] == GATE["sha256"], "exact own source geometry/producer required")
    for key in ("q_canonical_sha256", "gradient_canonical_sha256"):
        require(admission[key] == field["response"][key], "own q/gradient receipt identity differs")
    require(admission["source_case_selection"] == field["source_case_selection"]
            and field["source_case_selection"]["case_id"] == identity["case_id"]
            and admission["original_operator_fingerprint_sha256"] == field["original_operator_fingerprint_sha256"], "source selection/operator differs")
    require(config["schema"] == "eoere_z180_component_consumer_inputs/v1"
            and config["ready_for_saved_field_consumption"] is True
            and (config["state_id"], config["case_id"]) == (identity["state_id"], identity["case_id"])
            and config["field"] == result["field"] == binding["field"]
            and config["admission"] == result["admission"] == binding["admission"]
            and config["sources"] == result["sources"], "exact combined consumer config/pair required")
    for key, expected in (("geometry", GEOMETRY["report"]), ("manifest", GEOMETRY["source_manifest"]),
                          ("descriptor", GEOMETRY["cached_source_export"]), ("gate", GATE)):
        require(config["sources"][key] == expected, "exact Z180 component source required: "+key)
    require(result["source_inputs_canonical_sha256"] == canonical(field["source_inputs"])
            and result["source_sha256"].get(CONSUMER["path"]) == CONSUMER["sha256"]
            and result["source_sha256"].get(GATE["path"]) == GATE["sha256"], "exact consumer/source-input provenance required")
    require(process["schema"] == "eoere_z180_component_process_receipt/v1" and process["exit_code"] == 0
            and process["cwd"] == str(ROOT) and process["env"]["OPENBLAS_NUM_THREADS"] == process["env"]["OMP_NUM_THREADS"] == "1", "successful serialized process required")
    command_check(process["command"], refs["config"], refs["result"])
    for key, expected in {"field": binding["field"], "admission": binding["admission"], "consumer": CONSUMER,
                          **{key: refs[key] for key in ("config", "result", "stdout", "stderr")}}.items():
        same_ref(process[key], expected)
    require(all(not process[key] for key in ("source_drift_before", "source_drift_after", "result_source_drift")), "component process source drift recorded")
    snapshots = {}
    for key, schema in (("source_pins_before", "eoere_z180_component_source_snapshot_before/v1"),
                        ("source_pins_after", "eoere_z180_component_source_snapshot_after/v1")):
        ref = {k: process[key][k] for k in ("path", "sha256")}
        same_ref(process[key], ref)
        snapshots[key] = decode(checked(ref, pins))
        require(snapshots[key]["schema"] == schema, "exact component source snapshot required")
    before, after = snapshots["source_pins_before"], snapshots["source_pins_after"]
    require(not before["drift"] and not after["before_after_drift"] and not after["result_source_drift"], "snapshot source drift recorded")
    require(process["result_pin_count"] == after["result_source_pin_count"] == len(result["source_sha256"]), "saved result source census differs")
    require(all(after["observed_after"].get(path) == digest for path, digest in result["source_sha256"].items()), "after snapshot omits returned source")
    require(all(before["observed_before"][path] == digest for path, digest in result["source_sha256"].items() if path in before["observed_before"]), "available before snapshot differs")
    require(set(after["result_pins_missing_before_snapshot"]) == set(result["source_sha256"])-set(before["observed_before"]), "missing-before coverage caveat differs")
    for row in (field, admission, result):
        merge(pins, row["source_sha256"])
    merge(pins, field["source_inputs"]["source_sha256"])
    for ref in config["sources"].values():
        checked(ref, pins)
    # Outer snapshots can be incomplete for the first newly-returned provenance.
    # Preserve that caveat; the summary independently verifies the full union.
    return identity, field, admission, result, process, snapshots


def build(manifest, manifest_ref):
    require(set(manifest) == {"schema", "geometry", "source_sha256", "cases", "release"}
            and manifest["schema"] == INPUT_SCHEMA and manifest["geometry"] == GEOMETRY
            and manifest["release"] == RELEASE and tuple(row["case_id"] for row in manifest["cases"]) == CASES, "six exact ordered unadopted case bindings required")
    own_path = str(OWN.relative_to(ROOT))
    require(manifest["source_sha256"].get(own_path) == LOADED_SHA == sha(OWN.read_bytes()), "exact summary source required")
    pins = dict(manifest["source_sha256"])
    merge(pins, {manifest_ref["path"]: manifest_ref["sha256"]})
    require(decode(checked(manifest_ref, pins)) == manifest, "exact summary manifest bytes required")
    for ref in (GATE, CONSUMER, *GEOMETRY.values()):
        checked(ref, pins)
    selectors = definitions(SELECTORS, SELECTED, pins)
    records = [case_records(row, pins) for row in manifest["cases"]]
    require(len({row[0]["state_id"] for row in records}) == len({row[0]["case_id"] for row in records}) == 6, "six unique own states/cases required")
    verify(pins)
    before = canonical(pins)
    rows = []
    for binding, (identity, field, admission, result, process, snapshots) in zip(manifest["cases"], records, strict=True):
        coarse = selectors.coarse_findings({"component_reductions": result["findings"]["coarse"], "limits": field["limits"]})
        rich = selectors.rich_findings({"findings": result["findings"]["rich"]})
        seats = result["nominal_seat_geometry"]
        require(seats["nominal_wood_seats"] == 112 and len(seats["new_own_nominal_seats"]) == 16
                and seats["unaffected_proof_count"] == len(seats["unaffected_capture_ids"]) == 96
                and len(set(seats["unaffected_capture_ids"])) == 96
                and seats["old_actions_or_strength_transferred"] is False, "own16/unchanged96 nominal evidence join required")
        renewed = {row["capture_id"] for row in seats["new_own_nominal_seats"]}
        require(len(renewed) == 16 and not renewed.intersection(seats["unaffected_capture_ids"]), "distinct own16/inherited96 seat identities required")
        require(result["findings"]["coarse"]["six_panel_reductions"]["sample_count_per_axis"] == 41, "original41 spatial samples required")
        rows.append({**identity, "field": binding["field"], "admission": binding["admission"], "component_bindings": binding["component"],
            "coarse": coarse, "rich": rich, "nominal_seat_geometry": seats,
            "coarse_selector_limits_provenance": {"source": binding["field"], "pointer": "/limits", "original_reducer_contract_limits_not_relabelled": True},
            "admission_diagnostics": {key: admission[key] for key in ("declared_law_checks", "loaded_recovery_checks", "motion_diagnostics",
                "normal_force_n_by_host", "horizontal_force_xyz_n_by_host", "reaction_ratio_required_not_measured_friction", "support_contract")},
            "outer_process_source_coverage": {key: process[key] for key in ("missing_before", "source_pins_before", "source_pins_after",
                "source_drift_before", "source_drift_after", "result_source_drift", "union_pin_count", "result_pin_count")},
            "outer_snapshot_caveats": {"result_pins_missing_before_snapshot": snapshots["source_pins_after"]["result_pins_missing_before_snapshot"],
                "inventory_only_historical_receipts": snapshots["source_pins_before"]["inventory_only_historical_receipts"],
                "observed_before_count": len(snapshots["source_pins_before"]["observed_before"]),
                "observed_after_count": len(snapshots["source_pins_after"]["observed_after"]),
                "complete_outer_pre_snapshot_claimed": not snapshots["source_pins_after"]["result_pins_missing_before_snapshot"]},
            "process_elapsed_seconds": process["elapsed_seconds"]})
    verify(pins)
    require(canonical(pins) == before, "source union changed during selection")
    return {"schema": SCHEMA, "source_manifest": manifest_ref, "source_sha256": dict(sorted(pins.items())),
        "verified_source_union": {"count": len(pins), "canonical_sha256": before, "before_after_exact": True},
        "geometry": GEOMETRY, "cases": rows, "selectors_source": SELECTORS,
        "complete_joint_resistance": None, "unadopted_proposal": True, "spacer_or_4p5in_adopted": False, "release": RELEASE,
        "limits": ["Per-case saved witnesses only. Maxima select complete saved witnesses; no cross-case force or scalar steel scenario combination.",
                   "Original112-seat classifier retained with separate16 own/96 inherited nominal evidence; pressure, stiffness and strength stay unknown.",
                   "Own end/net-section/finished ligament, group/splitting, tool/fit, physical floor and complete-joint resistance remain unresolved; no panel remedy or physical release follows."],
        "execution": {"saved_JSON_and_source_bytes_only": True, "gate_consumer_reducer_CAD_operator_K_q_native_or_solve_called": False}}


def bind_output(out):
    # Same canonical-parent/original-leaf rule as frozen descriptor v5. Reject
    # traversal before abspath can normalize it; keep leaf unresolved for 'x'.
    out = Path(out)
    require(".." not in out.parts, "output parent traversal rejected")
    canonical_parent = Path(os.path.abspath(out)).parent.resolve()
    owned_runs = OWN.parent/"runs-v1"
    require(not owned_runs.is_symlink() and owned_runs.resolve().is_relative_to(OWN.parent)
            and canonical_parent.is_relative_to(owned_runs.resolve()), "summary belongs under own runs-v1")
    return canonical_parent/out.name


def write_to_file(manifest_ref, out):
    bound = bind_output(out)
    bound.parent.mkdir(parents=True, exist_ok=True)
    attempt = {"schema": "eoere_z180_summary_attempt/v1", "status": "STARTED", "release": RELEASE}
    with bound.open("x+") as stream:
        opened = os.fstat(stream.fileno())
        parent = bound.parent.stat()
        def write(record):
            live, directory = bound.lstat(), bound.parent.stat()
            require(stat.S_ISREG(live.st_mode) and (live.st_dev, live.st_ino) == (opened.st_dev, opened.st_ino)
                    and (directory.st_dev, directory.st_ino) == (parent.st_dev, parent.st_ino), "reserved summary inode/parent changed")
            stream.seek(0)
            json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        write(attempt)
        try:
            manifest = decode(checked(manifest_ref, {}))
            result = build(manifest, manifest_ref)
            write(result)
            return result
        except BaseException as error:
            attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
            write(attempt)
            raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = write_to_file({"path": args.manifest, "sha256": args.manifest_sha256}, args.out)
    print(json.dumps({"schema": result["schema"], "cases": len(result["cases"]), "output": str(args.out)}))


if __name__ == "__main__":
    main()

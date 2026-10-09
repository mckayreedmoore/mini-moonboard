"""Deferred Z180 component boundary; exact admission precedes frozen reducers.

No production config is supplied. Parent binds the final gate, descriptors and
one admitted pair. All numerical equations remain in the frozen C/F methods.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from threading import RLock
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[8]
BASE = OWN.parents[4]
MECH = BASE / "adjusted-base-mechanics-v1"
GATE_PATH = OWN.parent.parent / "review-fix-v2/bridge.py"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
FROZEN = {
    "coarse": {"path": str((MECH / "current-component-bridge-v1/consumer-v1/consume.py").relative_to(ROOT)),
               "sha256": "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9"},
    "rich": {"path": str((MECH / "current-component-bridge-v1/followups-v1/followups.py").relative_to(ROOT)),
             "sha256": "a27bacf7260905f69c2a69bae60c0f2cf4ed1f4efd229100e3c8fb846b892798"},
    "compiler": {"path": str((MECH / "current-force-bridge-v1/review-fix-v2/bridge.py").relative_to(ROOT)),
                 "sha256": "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"},
}
FIELD_SCHEMA = "eoere_z180_fixed_floor_candidate/v1"
ADMISSION_SCHEMA = "eoere_z180_fixed_floor_independent_field_admission/v1"
SUCCESS = "unadopted_z180_equilibrium_and_recovery_pass"
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)
SOURCE_KEYS = {"gate", "descriptor", "descriptor_review", "geometry", "manifest", "parent_descriptors", "finished_receivers"}
HOSTS = {"eoere_cleat_left", "eoere_cleat_right", "base_post_outer_left", "base_post_outer_right"}
LOCK = RLock()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def decode(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
                      parse_constant=lambda value: require(False, "nonfinite JSON value: " + value))


def merge(pins, extra):
    for path, sha in extra.items():
        require(path not in pins or pins[path] == sha, "conflicting source pin: " + path)
        pins[path] = sha


def checked(ref, pins):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "exact path/SHA reference required")
    path = Path(ref["path"])
    require(not path.is_absolute() and ".." not in path.parts and (ROOT / path).resolve().is_relative_to(ROOT),
            "repository-relative source reference required")
    require(isinstance(ref["sha256"], str) and len(ref["sha256"]) == 64
            and all(c in "0123456789abcdef" for c in ref["sha256"]), "full lowercase SHA256 required")
    raw = (ROOT / path).read_bytes()
    require(digest(raw) == ref["sha256"], "exact source bytes differ: " + str(path))
    merge(pins, {str(path): ref["sha256"]})
    return raw


def verify(pins):
    for path, sha in pins.items():
        require(digest((ROOT / path).read_bytes()) == sha, "source closure changed: " + path)


def load(ref, pins, label):
    checked(ref, pins)
    spec = importlib.util.spec_from_file_location(label, ROOT / ref["path"])
    module = importlib.util.module_from_spec(spec)
    sys.modules[label] = module
    spec.loader.exec_module(module)
    checked(ref, pins)
    return module


def authenticate(config_path, expected_config_sha256):
    """Only gate definitions load here; no component reducer is reachable."""
    require(digest(OWN.read_bytes()) == LOADED_SHA, "consumer source changed")
    path = Path(config_path).resolve()
    require(path.is_relative_to(ROOT), "repository config required")
    pins = {str(OWN.relative_to(ROOT)): LOADED_SHA}
    config_ref = {"path": str(path.relative_to(ROOT)), "sha256": expected_config_sha256}
    config = decode(checked(config_ref, pins))
    require(set(config) == {"schema", "sources", "field", "admission", "state_id", "case_id",
                            "ready_for_saved_field_consumption", "release"}
            and config["schema"] == "eoere_z180_component_consumer_inputs/v1"
            and config["ready_for_saved_field_consumption"] is True and config["release"] == RELEASE,
            "exact parent frozen saved-field config required")
    refs = config["sources"]
    require(set(refs) == SOURCE_KEYS and (ROOT / refs["gate"]["path"]).resolve() == GATE_PATH,
            "exact corrected Z180 gate/source reference set required")
    records = {key: decode(checked(ref, pins)) for key, ref in refs.items() if key != "gate"}
    exported, parent, review = (records[k] for k in ("descriptor", "parent_descriptors", "descriptor_review"))
    require(exported["schema"] == "eoere_z180_geometry_delta_descriptors/v1"
            and exported["geometry"] == refs["geometry"] and exported["manifest"] == refs["manifest"]
            and exported["parent_descriptors"] == refs["parent_descriptors"]
            and records["manifest"]["saved_finished_receiver_evidence"] == refs["finished_receivers"],
            "own full descriptor and partial-layout provenance required")
    require(review["schema"] == "eoere_z180_geometry_descriptors_independent_review/v1"
            and review["success"] == "independent_z180_descriptor_source_checks_pass"
            and review.get("independent_z180_descriptor_source_checks_pass") is True
            and review["descriptor"] == refs["descriptor"] and review["release"] == RELEASE,
            "exact own descriptor review required")
    merge(pins, parent["source_sha256"])
    merge(pins, exported["source_sha256"])
    for ref in (refs[k] for k in ("geometry", "manifest", "parent_descriptors", "finished_receivers")):
        require(exported["source_sha256"].get(ref["path"]) == ref["sha256"], "descriptor source reference outside closure")
    require(all(exported["source_sha256"].get(p) == sha for p, sha in parent["source_sha256"].items()),
            "inherited exact source closure omitted")
    raw = checked(config["field"], pins)
    receipt = decode(checked(config["admission"], pins))
    field = decode(raw)
    require(field["schema"] == FIELD_SCHEMA and field["release"] == RELEASE
            and (field["state_id"], field["case_id"]) == (config["state_id"], config["case_id"])
            and isinstance(config["state_id"], str) and config["state_id"]
            and isinstance(config["case_id"], str) and config["case_id"], "own unreleased Z180 state/case required")
    require(field["source_inputs"]["geometry"] == {"report": refs["geometry"], "source_manifest": refs["manifest"],
            "cached_source_export": refs["descriptor"]} and field["current_execution"]["geometry"] == refs["geometry"],
            "exact Z180 field geometry references required; no old scene alias")
    require(receipt["schema"] == ADMISSION_SCHEMA and receipt.get(SUCCESS) is True, "own Z180 admission required")
    merge(pins, field["source_inputs"]["source_sha256"])
    verify(pins)
    gate = load(refs["gate"], pins, "z180_component_exact_gate")
    admitted, gate_pins = gate.require_admitted_payload(raw, receipt, admission_sha256=refs["gate"]["sha256"])
    require(canonical(admitted) == canonical(field), "gate changed the raw field payload")
    merge(pins, gate_pins)
    verify(pins)
    return config, records, admitted, pins, gate


def source_contract(config, records, field, pins, gate, c):
    """Exact corrected source join; derive100 axes from full descriptors."""
    a = gate.original()
    with gate.corrected_context(a):
        bound = a.require_sources(field["source_inputs"])
    require(bound["cached_source_export"] == records["descriptor"]
            and a.GEOMETRY == config["sources"]["geometry"]
            and a.SOURCE_MANIFEST == config["sources"]["manifest"]
            and a.PARENT_DESCRIPTOR == config["sources"]["parent_descriptors"], "corrected gate/source config mismatch")
    exported = records["descriptor"]
    for key, exported_key in c.DESCRIPTOR_KEYS.items():
        require(field["source_inputs"][key] == exported[exported_key], "own descriptor join differs: " + key)
    axes = {s["axis_id"]: s["source_axis"] for s in exported["shafts"]}
    require(len(axes) == len(exported["shafts"]) == 100
            and all(key == axis["id"] for key, axis in axes.items()), "100 unique own descriptor axes required")
    proposed = {a["id"]: a for a in records["geometry"]["proposed_axes"]}
    require(len(proposed) == len(records["geometry"]["proposed_axes"]) == 4
            and all(axes.get(key) == axis for key, axis in proposed.items()), "partial layout must join four own axes")
    parent_axes = {s["axis_id"]: s["source_axis"] for s in records["parent_descriptors"]["shafts"]}
    require(len(parent_axes) == len(records["parent_descriptors"]["shafts"]) == 100
            and set(parent_axes) == set(axes) and all(axes[k] == v for k, v in parent_axes.items() if k not in proposed),
            "exact96 unaffected parent axes required")
    verify(pins)
    return axes


def nominal_seats(exported, parent, finished, old_contract, old_details, refs):
    """Select96 unchanged proofs plus16 own nominal observations, never pressure."""
    timber = {r["name"] for r in exported["raw_gross_timber_rows"]}
    def seats(data):
        pairs = [(s["axis_id"] + "/" + end["end"] + "-capture", (s, end))
                 for s in data["shafts"] for end in s["ends"] if end["host"] in timber]
        result = dict(pairs)
        require(len(result) == len(pairs), "duplicate wood seat identity")
        return result
    own, prior = seats(exported), seats(parent)
    require(len(own) == len(prior) == 112 and set(own) == set(prior), "112 own wood seat identities required")
    historical = {r["capture_id"]: r for r in old_details["washer_seat_rows"]}
    require(len(historical) == len(old_details["washer_seat_rows"]) == 112
            and set(historical) == set(own) and old_contract["nominal_wood_seats"] == 112,
            "authenticated original112 nominal proofs required")
    observations = {r["id"]: r["source"] for r in exported["finished_body_observations"]}
    old_sources = {r["id"]: r["source"] for r in parent["finished_body_observations"]}
    unaffected = [key for key, (_, end) in own.items() if end["host"] not in HOSTS]
    require(len(unaffected) == 96, "exact96 unaffected wood seats required")
    for key in unaffected:
        shaft, end = own[key]
        require((shaft, end) == prior[key] and observations[end["host"]] == old_sources[end["host"]]
                and historical[key]["full_modeled_support"] is True, "unaffected seat/source provenance differs")
    scenarios = [r for r in finished["scenarios"] if r["scenario"] == "proposed_Z180_modeled"]
    if len(scenarios) != 1 or len(scenarios[0].get("annular_queries", [])) != 16:
        return {"nominal_wood_seats": None, "scope": "Missing complete16 own nominal Z180 annular observations.",
                "unaffected_proof_count": 96, "physical_pressure_or_strength": None}
    scenario = scenarios[0]
    rows = {(r["axis_id"], r["receiver"], r["end"]): r for r in scenario["annular_queries"]}
    require(len(rows) == 16, "duplicate changed-host annular observation")
    renewed = []
    for key, (shaft, end) in own.items():
        host = end["host"]
        if host not in HOSTS:
            continue
        row = rows[(shaft["axis_id"], host, end["end"])]
        body = scenario["finished_bodies"][host]
        require({k: observations[host][k] for k in ("path", "sha256")} == {k: body[k] for k in ("path", "sha256")},
                "new nominal annulus finished source differs")
        point = [p + d * end["support_s_mm"] for p, d in zip(shaft["point"], shaft["basis"][0], strict=True)]
        hardware = shaft["source_axis"]["hardware_scenario"]
        require(math.dist(point, row["support_point_xyz_mm"]) <= 1e-6
                and math.dist([-v for v in end["direction_on_shaft_xyz"]], row["inward_xyz"]) <= 1e-6
                and abs(row["nominal_washer_OD_mm"] - hardware["washer_od_mm"]) <= 1e-6
                and abs(row["nominal_washer_ID_mm"] - hardware["washer_id_mm"]) <= 1e-6
                and abs(row["observed_backing_fraction"] - 1.) <= 1e-8
                and row["single_own_host_targets"] == 1 and row["inward_skin_mm"] == .05
                and row["physical_contact_or_strength_qualified"] is False, "own new nominal annulus provenance differs")
        renewed.append({"capture_id": key, "finished_source": {k: body[k] for k in ("path", "sha256")},
                        "observation": copy.deepcopy(row)})
    require(len(renewed) == 16 and len(rows) == len(renewed), "exact16 new own seat joins required")
    return {"nominal_wood_seats": 112, "new_own_nominal_seats": renewed,
            "unaffected_capture_ids": sorted(unaffected), "unaffected_proof_count": 96,
            "new_evidence": refs["finished_receivers"], "parent_nominal_basis": old_contract,
            "scope": "Nominal geometry only; pressure, stiffness, delivered support and complete resistance unknown.",
            "old_actions_or_strength_transferred": False}


def washer_composition(field, axes, parent_geometry, refs):
    """Explicit full-descriptor/partial-layout/v3-cut/own-fitting composition."""
    cuts = parent_geometry.get("service_cuts", [])
    descriptors = field["fitting_operator_descriptors"]
    poses = {r["id"] for r in field["source_inputs"]["fitting_poses"]}
    require(len(descriptors) == len({r["body"] for r in descriptors}) == 22
            and {r["body"] for r in descriptors} == poses, "22 own fitting scenario identities required")
    keys = {"leg_mm": "arm_length_mm", "width_mm": "width_mm", "thickness_mm": "thickness_mm",
            "factory_hole_mm": "factory_hole_diameter_mm"}
    scenarios = [{k: d["own_fitting_scenario"][v] for k, v in keys.items()} for d in descriptors]
    if (len(cuts) != 27 or len({(r["service"], r["kind"], r["receiver"]) for r in cuts}) != 27
            or not all(s == {"leg_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "factory_hole_mm": 10.}
                       for s in scenarios)):
        return None
    return {"schema": "eoere_z180_washer_geometry_composition/v1", "axes": copy.deepcopy(list(axes.values())),
            "service_cuts": copy.deepcopy(cuts), "scenario": scenarios[0],
            "source_composition": {"axes": {"full_descriptors": refs["descriptor"], "partial_layout": refs["geometry"],
                                             "retained_parent_descriptors": refs["parent_descriptors"]},
                "service_cuts": refs["parent_geometry"], "fitting_dimensions": {
                    "basis": "all22 own admitted fitting operator scenarios",
                    "own_operator_descriptors_canonical_sha256": canonical(descriptors)}},
            "partial_layout_contains_full_axes_or_service_cuts": False}


def prepare_contract(config, records, field, pins, c, plan):
    """Authenticate original nominal evidence only for the96 unchanged seats."""
    def read(key):
        ref = plan.ARTIFACTS[key]
        return decode(checked(ref, pins))
    old_geometry, audit, details, extension, v3 = [read(k) for k in
        ("geometry", "seat_audit", "seat_details", "extension_review", "parent_geometry")]
    parent = records["parent_descriptors"]
    require(config["sources"]["parent_descriptors"] == plan.ARTIFACTS["descriptors"]
            and records["manifest"]["parent_geometry"] == plan.ARTIFACTS["geometry"], "exact preserved parent proof scope required")
    old_seats = plan.nominal_seat_carry(parent, old_geometry, audit, details, extension)
    for evidence, key in ((details, "complete_source_sha256"), (extension, "source_sha256")):
        require(all(pins[p] == sha for p, sha in evidence[key].items() if p in pins and not p.startswith("site/")),
                "historical computational source overlap differs")
    seats = nominal_seats(records["descriptor"], parent, records["finished_receivers"], old_seats, details, config["sources"])
    refs = {"geometry": config["sources"]["geometry"], "manifest": config["sources"]["manifest"],
            "descriptors": config["sources"]["descriptor"], "parent_geometry": plan.ARTIFACTS["parent_geometry"]}
    facade = SimpleNamespace(BASE=plan.BASE, METHODS=plan.METHODS, ARTIFACTS=refs,
                             merge=plan.merge, checked_bytes=plan.checked_bytes)
    verify(pins)
    return facade, {"nominal_seat_geometry": seats}, v3


def reduce_admitted(config, records, field, pins, gate, *, mode, samples):
    """Only source-identity hooks change; original equations remain untouched."""
    c = load(FROZEN["coarse"], pins, "z180_component_frozen_coarse")
    axes = source_contract(config, records, field, pins, gate, c)
    plan = c._load_plan()
    merge(pins, {str(c.PLAN.relative_to(ROOT)): c.PLAN_SHA})
    facade, contract, v3 = prepare_contract(config, records, field, pins, c, plan)
    findings = {}
    with c.BOUNDARY_LOCK, patch.object(c, "FIELD_SCHEMA", FIELD_SCHEMA):
        if mode in ("coarse", "both"):
            findings["coarse"] = c._reduce(field, axes, facade, pins, samples)
        if mode in ("rich", "both"):
            f = load(FROZEN["rich"], pins, "z180_component_frozen_rich")
            compiler = load(FROZEN["compiler"], pins, "z180_component_guarded_compiler_only")
            composition = washer_composition(field, axes, v3, {**config["sources"], "parent_geometry": facade.ARTIFACTS["parent_geometry"]})
            original_methods = f._methods
            def methods(*args):
                result = original_methods(*args)
                if composition is None:
                    result.washer["calculate"] = lambda *_args, **_kwargs: {
                        "complete_washer_resistance": None, "diagnostics": None,
                        "preserved_first_tmp_sha256": {}, "first_tmp_bytes_currently_match": {}, "known_answer_checks": {},
                        "limits": ["Full washer composition unavailable: need all27 source-bound v3 cuts and22 own fitting dimensional scenarios."]}
                return result
            with patch.object(c, "_load_gate", lambda _plan: SimpleNamespace(checked_ast=compiler.checked_ast)), \
                    patch.object(f, "GATE_SHA", config["sources"]["gate"]["sha256"]), \
                    patch.object(f, "washer_geometry", lambda *_args: composition), patch.object(f, "_methods", methods):
                findings["rich"] = f._reduce(field, ROOT / config["field"]["path"], c, facade, pins, contract)
            findings["rich"]["missing_current_inputs"]["finished_sections"] = (
                "Own finished critical ligaments, connected paths and section witnesses; "
                "the separate four-receiver finished-section step remains pending.")
            if composition is None:
                findings["rich"]["missing_current_inputs"]["washer_composition"] = "All27 source-bound v3 cuts and22 own fitting dimensional scenarios required; no full washer reduction performed."
    return findings, contract


def consume(config_path, expected_config_sha256, *, mode="both", samples=41):
    require(mode in ("coarse", "rich", "both") and type(samples) is int and samples >= 3, "valid mode/spatial sample count required")
    with LOCK:
        config, records, field, pins, gate = authenticate(config_path, expected_config_sha256)
        before = canonical(field)
        findings, contract = reduce_admitted(config, records, field, pins, gate, mode=mode, samples=samples)
        require(canonical(field) == before, "reducer changed the admitted field")
        verify(pins)
    return {"schema": "eoere_unadopted_z180_same_state_component_references/v1",
            **{k: field[k] for k in ("state_id", "case_id", "accessory_placement")},
            "field_schema": field["schema"], "field": config["field"], "admission": config["admission"],
            "sources": config["sources"], "source_sha256": dict(sorted(pins.items())), "mode": mode,
            "source_inputs_canonical_sha256": canonical(field["source_inputs"]), "findings": findings,
            "nominal_seat_geometry": contract["nominal_seat_geometry"], "complete_joint_resistance": None,
            "unadopted_proposal": True, "release": dict(RELEASE),
            "execution": {"frozen_equations_tolerances_and_generic9mm_head_unchanged": True,
                "own_admission_precedes_reducer_loading": True, "historical_field_or_geometry_alias_used": False,
                "CAD_BREP_panel_preparation_K_q_native_solve_or_browser": False}}


def consume_to_file(config_path, expected_config_sha256, out, **kwargs):
    """Own one new inode before any config, input, gate or reducer read."""
    attempt = {"schema": "eoere_z180_component_attempt/v1", "status": "STARTED", "release": dict(RELEASE),
               "command": list(sys.orig_argv), "config": str(config_path), "expected_config_sha256": expected_config_sha256}
    with Path(out).open("x+") as stream:
        def write(record):
            stream.seek(0)
            stream.write(json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
            stream.truncate()
            stream.flush()
            os.fsync(stream.fileno())
        write(attempt)
        try:
            result = consume(config_path, expected_config_sha256, **kwargs)
            result["execution"].update(command=list(sys.orig_argv), cwd=str(Path.cwd()), python=sys.version,
                                       exclusive_output_reserved_before_intake=True, failed_attempts_retained=True)
            write(result)
        except BaseException as error:
            attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
            write(attempt)
            raise
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--config-sha256", required=True)
    parser.add_argument("--mode", choices=("coarse", "rich", "both"), default="both")
    parser.add_argument("--samples", type=int, default=41)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = consume_to_file(args.config, args.config_sha256, args.out, mode=args.mode, samples=args.samples)
    print(json.dumps({"output": str(args.out), "state_id": result["state_id"], "sha256": digest(args.out.read_bytes())}))


if __name__ == "__main__":
    main()

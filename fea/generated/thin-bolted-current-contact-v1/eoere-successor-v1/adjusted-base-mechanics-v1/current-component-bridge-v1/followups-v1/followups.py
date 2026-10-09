"""Current admitted fixed-action steel, timber/bolt and washer references.

Only source identity/intake boundaries change. Frozen equations and tolerances
are reused. Reserve output before intake; failed attempts remain reviewable.
No CAD, operator preparation, frame assembly or global/native solve is called.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import itertools
import json
import os
import platform
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/"
CONSUMER = OWN.parent.parent / "consumer-v1/consume.py"
CONSUMER_SHA = "f11175782c7b29abbdfbcbf5fbad63f919596bc6a613b4c7a5b65acc1027bad9"
GATE_SHA = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
RELEASE = dict.fromkeys(("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                         "fabrication_released", "structural_released", "climbing_released"), False)
SOURCES = {
    "group": (BASE + "bolt-group-method-v1/method.py", "70321b1690269644c6bee6e5d37806f5fcfc31f9677a2a0eae3fb50939b83f69"),
    "steel": (BASE + "joint-mvp-v1/steel-reuse-v1/calculate.py", "6acf9421d8fcbcafd1334edfa3a5a9e3bbb80ccea8594d9094d47cba4c4d7b18"),
    "core": (BASE + "joint-mvp-v1/steel-reuse-v1/core.py", "477ca831860a163e4baefcab3a93fd82002528f4735fe66ec98aec0d382797f1"),
    "net": (BASE + "steel-net-sections-v1/net_normal.py", "304f96e6c0df4e18c3a00f2c5c8a7d2206d3c6f024c4bf6ab1beb171924d78b0"),
    "steel_tests": (BASE + "joint-mvp-v1/steel-reuse-v1/test_core.py", "5ae1573a706117a96dc2ddc3afc5e3c6bffbac4be502f354726cfe40186241e0"),
    "steel_material": (BASE + "steel-net-sections-v1/material-source.json", "37808016a6ff7e6d9d0b95f51e5acd43f9ec2e0d48713d2c084850301a7f8072"),
    "timber": (BASE + "joint-mvp-v1/timber-reuse-v1/calculate_v2.py", "41385d35d8faf785ae14f88f8bb54ed69dbed56e271ff7524f1dc6b071f6310d"),
    "timber_template": (BASE + "joint-mvp-v1/timber-reuse-v1/input-v2.json", "849e779f57b281aaa6c38dbb3b2944e4c550e654494a3cb9f6a8c213bc19a57a"),
    "catalog": (BASE + "catalog-hardware-strength-v1/catalog-inputs.json", "b40aa4681143e0d5ca84c986cfad982549c58dc6127e2d58d7455ab7411efe6d"),
    "catalog_math": (BASE + "catalog-hardware-strength-v1/calculate.py", "2add5973386746fc7df8d1a72956d0b10e101f73234ee072a7c300cdc4968350"),
    "roots": (BASE + "catalog-hardware-strength-v1/thread-root-design-v1/result.json", "e741022ce8265079a745b2e8acbfc77f11b9c80d82a20bd9177f61465056b247"),
    "fyb": (BASE + "catalog-hardware-strength-v1/f606-tensile-yield-spec-v1/receipt-v2.json", "3378a3a4de466f5deaabf17e15a0621bef65daeaf5f01856ace509a41cb25fe6"),
    "first": (BASE + "joint-mvp-v1/first_joint.py", "9a3decbff84ba24ab5ecb9d34489a3427d83144a0813e9dcf6a5b500904a279e"),
    "washer": (BASE + "joint-mvp-v1/washer-reuse-v1/calculate.py", "96bb2ede4b65202bd9c74631cb39568aad3055294d931e1d352b9d3a8b4741e5"),
    "washer_math": ("scripts/thin_bolted_steel_resistance.py", "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602"),
}
STEEL_SCENARIOS = (
    {"id": "t6_r6", "thickness_mm": 6., "inside_radius_scenario_mm": 6., "yield_factor": 1.67, "rupture_factor": 2.},
    {"id": "t6p35_r6p35", "thickness_mm": 6.35, "inside_radius_scenario_mm": 6.35, "yield_factor": 1.67, "rupture_factor": 2.},
)
TIMBER_METHODS = ("mini_moonboard/bolted_timber_checks.py", "fea/dowel_yield.py",
                  "mini_moonboard/bolted_steel_wood_yield.py", "mini_moonboard/bolted_wood_wood_yield.py",
                  "scripts/thin_bolted_timber_resistance.py")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return digest(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def name(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def checked(path, expected):
    raw = Path(path).read_bytes()
    require(digest(raw) == expected, "exact source/artifact bytes required: " + str(path))
    return raw


def _consumer():
    checked(OWN, LOADED_SHA)
    checked(CONSUMER, CONSUMER_SHA)
    spec = importlib.util.spec_from_file_location("eoere_current_frozen_consumer_for_followups", CONSUMER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    checked(CONSUMER, CONSUMER_SHA)
    return module


def washer_geometry(field, geometry, parent, refs):
    """Explicit composition, never an alias of the extension-only report."""
    axes = geometry["axes"]
    require(len(axes) == len({a["id"] for a in axes}) == 100, "100 current axes required")
    require({s["axis_id"]: s["source_axis"] for s in field["source_inputs"]["shafts"]}
            == {a["id"]: a for a in axes}, "own current axes differ")
    require(parent["axes"] == axes and geometry["parent_geometry"]["base"] == refs["parent_geometry"],
            "current axes and exact v3 parent reference required")
    cuts = parent["service_cuts"]
    require(len(cuts) == 27 and len({(r["service"], r["kind"], r["receiver"]) for r in cuts}) == 27,
            "all 27 v3 service cuts required")
    descriptors = field["fitting_operator_descriptors"]
    poses = {p["id"] for p in field["source_inputs"]["fitting_poses"]}
    require(len(descriptors) == len({d["body"] for d in descriptors}) == 22
            and {d["body"] for d in descriptors} == poses, "all22 own fitting scenarios required")
    keys = {"leg_mm": "arm_length_mm", "width_mm": "width_mm", "thickness_mm": "thickness_mm",
            "factory_hole_mm": "factory_hole_diameter_mm"}
    scenarios = [{k: d["own_fitting_scenario"][v] for k, v in keys.items()} for d in descriptors]
    require(all(s == scenarios[0] for s in scenarios)
            and scenarios[0] == {"leg_mm": 88.9, "width_mm": 88.9, "thickness_mm": 6.35, "factory_hole_mm": 10.},
            "one exact own current fitting dimensional scenario required")
    return {"schema": "eoere_current_washer_geometry_composition/v1", "axes": copy.deepcopy(axes),
            "service_cuts": copy.deepcopy(cuts), "scenario": scenarios[0],
            "source_composition": {"axes": refs["geometry"], "service_cuts": refs["parent_geometry"],
                "fitting_dimensions": {"basis": "all22 own admitted fitting operator scenarios",
                    "field_source_inputs_canonical_sha256": canonical(field["source_inputs"]),
                    "own_operator_descriptors_canonical_sha256": canonical(descriptors)}},
            "extension_report_contains_service_cuts_or_fitting_scenario": False}


def _materials(c, plan, pins):
    """Static purchase/material evidence only; historical field maps stay historical."""
    def read(key):
        relative, sha = SOURCES[key]
        plan.merge(pins, {relative: sha})
        return json.loads(c.checked(ROOT / relative, sha))
    template, facts, roots, fyb, steel = [read(k) for k in ("timber_template", "catalog", "roots", "fyb", "steel_material")]
    require(fyb["conditional_NDS_input"]["Fyb_psi"] == template["Fyb_purchase_design_psi"] == 92000.
            and template["generic_steel_Fe_psi"] == 87000., "unchanged conditional material scalars required")
    require((steel["primary_guide"]["minimum_yield_mpa"], steel["primary_guide"]["minimum_tensile_mpa"]) == (235, 370),
            "unchanged conditional base-metal reference required")
    guide = steel["primary_guide"]
    plan.merge(pins, {guide["local_path"]: guide["sha256"], **roots["direct_source_sha256"], **fyb["direct_source_sha256"],
                     **{p: template["source_sha256"][p] for p in TIMBER_METHODS}})
    seller = steel["seller_grade_context"]
    plan.merge(pins, {seller["path"]: seller["sha256"]})
    historical = []
    for ref in roots["referenced_source_maps"]:
        raw = c.checked(ROOT / ref["path"], ref["raw_sha256"])
        rows = json.loads(raw)[ref["key"]]
        require(canonical(rows) == ref["canonical_sha256"], "historical root evidence source-map identity differs")
        overlap = {p: sha for p, sha in rows.items() if p in pins
                   and p.endswith((".py", ".pdf"))}
        require(all(pins[p] == sha for p, sha in overlap.items()), "historical computational source overlap differs")
        plan.merge(pins, {ref["path"]: ref["raw_sha256"]})
        historical.append({**ref, "computational_overlap_verified": len(overlap),
                           "historical_field_or_viewer_map_imported_as_current": False})
    c.verify(pins)
    return template, facts, roots, {"root_evidence_maps": historical,
        "material_receipts_are_purchase_scenarios": True, "delivered_hardware_inspected": False}


def _methods(c, plan, pins):
    """Lazy exact source reuse, called only after the current admission/metadata gate."""
    import numpy as np
    from scipy.spatial import ConvexHull

    group = c.load(ROOT / SOURCES["group"][0], SOURCES["group"][1], "eoere_current_followup_group")
    gate = c._load_gate(plan)
    plan.merge(pins, dict(SOURCES.values()))
    c.verify(pins)

    def pure(key, functions, namespace=None):
        relative, sha = SOURCES[key] if key in SOURCES else (key, pins[key])
        # The original helper's second read is authenticated immediately at AST parse.
        with c.BOUNDARY_LOCK, patch.object(group, "ast", gate.checked_ast(sha)):
            return group.pinned_functions(relative, functions, pins, namespace)

    def constants(key, wanted):
        relative, sha = SOURCES[key]
        ast = gate.checked_ast(sha)
        tree = ast.parse(c.checked(ROOT / relative, sha), filename=str(ROOT / relative))
        nodes = [n for n in tree.body if isinstance(n, ast.Assign) and len(n.targets) == 1
                 and isinstance(n.targets[0], ast.Name) and n.targets[0].id in wanted]
        require({n.targets[0].id for n in nodes} == wanted, "exact frozen constant census required")
        scope = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(ROOT / relative), "exec"), scope)  # noqa: S102
        return {k: scope[k] for k in wanted}

    core = c.load(ROOT / SOURCES["core"][0], SOURCES["core"][1], "eoere_current_followup_steel_core")
    net = c.load(ROOT / SOURCES["net"][0], SOURCES["net"][1], "eoere_current_followup_net")
    steel = pure("steel", ["own_loads", "reduce_angle", "summary"], {"np": np, "core": core})
    timber = c.load(ROOT / SOURCES["timber"][0], SOURCES["timber"][1], "eoere_current_followup_timber")
    dfl = pure(TIMBER_METHODS[0], ["dfl_dowel_bearing_psi"])
    solver = pure(TIMBER_METHODS[1], ["single_shear"])
    ns = {"single_shear": solver["single_shear"], "dfl_dowel_bearing_psi": dfl["dfl_dowel_bearing_psi"]}
    ws = pure(TIMBER_METHODS[2], ["wood_steel_single_shear_reference"], ns)
    ww = pure(TIMBER_METHODS[3], ["_finite_number", "dowel_bending_yield_moment_lb_in", "wood_wood_single_shear_reference"],
              dict(ns, _MODES=timber.MODES))
    resolved = pure(TIMBER_METHODS[4], ["vector", "unit", "dot", "cross", "resolved_action"])["resolved_action"]
    bolt = pure("first", ["bolt_components"], {"np": np})["bolt_components"]
    circles = SimpleNamespace(**pure("catalog_math", ["scalar", "vec6", "circle_vm"], {"np": np}))
    plate = pure("washer_math", ["number", "annulus_pressure", "_plate_basis", "_plate_particular", "washer_axisymmetric_bending"],
                 {"np": np, "pairwise": itertools.pairwise, **constants("washer_math", {"MIT_PLATE"})})
    # These unchanged constants are read from the exact original AST, not equations copied here.
    wanted = {"PSI", "FC_PERP", "FY_MARKER", "TOL", "FIRST_SHA"}
    washer_ns = dict(np=np, ConvexHull=ConvexHull, itertools=itertools, Counter=Counter, hashlib=hashlib,
        json=json, ROOT=ROOT, Path=Path, platform=platform, **constants("washer", wanted),
        annulus_pressure=plate["annulus_pressure"], washer_axisymmetric_bending=plate["washer_axisymmetric_bending"])
    washer = pure("washer", ["require", "sha", "canonical", "verify", "number", "unit", "raw_vertices",
        "raw_disk_land", "wood_land", "steel_land", "scenario_metrics", "known_checks", "calculate"], washer_ns)
    steel_known = pure("steel_tests", ["known_answers"], {"np": np, "core": core})["known_answers"]
    return SimpleNamespace(pure=pure, steel=steel, core=core, net=net, timber=timber, group=group,
        ws=ws, ww=ww, resolved=resolved, bolt=bolt, circles=circles, washer=washer, steel_known=steel_known)


def _reduce(field, field_path, c, plan, pins, contract):
    template, facts, roots, material = _materials(c, plan, pins)
    methods = _methods(c, plan, pins)
    descriptors = field["fitting_operator_descriptors"]
    geometry = json.loads(plan.checked_bytes(plan.ARTIFACTS["geometry"]))
    parent = json.loads(plan.checked_bytes(plan.ARTIFACTS["parent_geometry"]))
    composition = washer_geometry(field, geometry, parent, plan.ARTIFACTS)
    steel = []
    for scenario in STEEL_SCENARIOS:
        angles = [methods.steel["reduce_angle"](field, d, methods.net, scenario) for d in descriptors]
        require(len(angles) == 22 and sum(len(a["bands"]) for a in angles) == 88
                and sum(a["integrity"]["point_loads_retained"] for a in angles) == 616,
                "all22 steel owner/four-band/616-point census required")
        steel.append({"comparison": dict(scenario), "summary": methods.steel["summary"](angles), "angles": angles,
            "fixed_actions_scalar_scenario_only": True, "product_strength_established": False})
    manifest = {"files": {"field": name(field_path)},
                **{k: copy.deepcopy(template[k]) for k in ("Fyb_purchase_design_psi", "generic_steel_Fe_psi", "steel_Fe_primary_basis")},
                "calculation_scope": "Own current admitted state only; individual compatible two-member references; mixed stacks, groups, splitting, finished sections and complete joints remain unknown."}

    def current_intake(_):
        return manifest, field, facts, roots, None, pins, methods.group, methods.ws, methods.ww, methods.resolved

    with c.BOUNDARY_LOCK, patch.object(methods.timber, "intake", current_intake):
        timber = methods.timber.produce(OWN)
    unsupported = [r["axis_id"] for r in timber["shaft_components"] if r["component"] is None]
    require(len(unsupported) == 8, "eight own mixed-stack unknowns required")
    timber["same_field_reused_gross_member_witnesses"] = []
    timber["gross_member_witness_reuse_limit"] = "Coarse current witnesses are produced separately; this adapter has no assessment join. No historical witness used."
    bolts = methods.bolt({s["axis_id"]: s for s in field["source_inputs"]["shafts"]}, field, facts, roots, methods.circles)
    require(len(bolts) == len({r["axis_id"] for r in bolts}) == 100, "100 distinct current shaft references required")
    washer = methods.washer["calculate"](field, composition, facts, pins,
        {"raw_field_sha256": pins[name(field_path)], "fresh_gate_sha256": GATE_SHA,
         "current_geometry_composition_canonical_sha256": canonical(composition)})
    # The original /tmp checks are explicitly historical diagnostics, never current authentication.
    washer["historical_first_tmp_diagnostics"] = {k: washer.pop(k) for k in ("preserved_first_tmp_sha256", "first_tmp_bytes_currently_match")}
    washer["limits"][-1] = "Every diagnostic belongs to this own current admitted state. No historical force or geometry pass transfers."
    washer["geometry_composition"] = composition
    washer["reviewed_nominal_seat_geometry"] = copy.deepcopy(contract["nominal_seat_geometry"])
    return {"rich_steel": steel, "timber": timber,
            "shaft": {"all100": bolts, "first_yield_reference_exceedances": [r["axis_id"] for r in bolts
                        if r["governing"]["specified_material_first_yield_index"] > 1], "complete_bolt_resistance": None},
            "washers": washer, "static_material_evidence": material,
            "known_answers": {"steel": methods.steel_known(methods.net), "washers": washer["known_answer_checks"]},
            "missing_current_inputs": {"mixed_stacks": unsupported,
                "finished_sections": "Current finished critical ligaments/connected paths and section witnesses for all15 changed sources.",
                "groups_and_splitting": "Signed nonuniform multi-fastener/group fracture and splitting method with current local paths.",
                "restraint_and_complete_joints": "Current local restraint and complete interaction of independent couples, axial/bearing/washer/flange paths.",
                "washers": "Actual pressure/prying couples, local contact bound, nut footprint and product strength; source geometry carry proves nominal support only."}}


def consume(field_path, receipt_path, *, expected_field_sha256, expected_receipt_sha256, admission_sha256=GATE_SHA):
    c = _consumer()
    field, pins, plan = c.authenticate(field_path, receipt_path, expected_field_sha256, expected_receipt_sha256, admission_sha256)
    before = canonical(field)
    contract, _ = c._current_contract(field, plan)
    plan.merge(pins, contract["source_sha256"])
    plan.merge(pins, {name(OWN): LOADED_SHA})
    c.verify(pins)
    findings = _reduce(field, field_path, c, plan, pins, contract)
    require(canonical(field) == before, "followup methods changed the admitted field")
    c.verify(pins)
    return {"schema": "eoere_current_same_state_followup_component_references/v1",
        **{k: field[k] for k in ("state_id", "case_id", "accessory_placement")}, "field_schema": field["schema"],
        "raw_field_sha256": expected_field_sha256, "field_admission_receipt_sha256": expected_receipt_sha256,
        "fresh_gate_sha256": admission_sha256, "current_geometry": plan.ARTIFACTS["geometry"],
        "current_source_manifest": plan.ARTIFACTS["manifest"], "current_saved_descriptors": plan.ARTIFACTS["descriptors"],
        "source_inputs_canonical_sha256": canonical(field["source_inputs"]), "source_sha256": dict(sorted(pins.items())),
        "findings": findings, "complete_joint_resistance": None, "release": dict(RELEASE),
        "execution": {"CAD_query_or_rebuild": False, "operator_K_or_preparation": False,
            "frame_K_q_native_or_browser": False, "frozen_equations_and_tolerances_unchanged": True,
            "historical_force_or_geometry_intake_called": False, "scoped_intake_restored": True}}


def write_record(stream, value):
    stream.seek(0)
    stream.write(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    stream.truncate()
    stream.flush()
    os.fsync(stream.fileno())


def consume_to_file(field_path, receipt_path, out, **kwargs):
    attempt = {"schema": "eoere_current_followup_attempt/v1", "status": "STARTED", "output": str(out),
               "command": list(sys.orig_argv), "expected_source_sha256": {name(OWN): LOADED_SHA},
               "expected_inputs": {"field": {"path": str(field_path), "sha256": kwargs.get("expected_field_sha256")},
                   "receipt": {"path": str(receipt_path), "sha256": kwargs.get("expected_receipt_sha256")},
                   "gate_sha256": kwargs.get("admission_sha256", GATE_SHA)}, "release": dict(RELEASE)}
    with Path(out).open("x") as stream:
        write_record(stream, attempt)
        try:
            result = consume(field_path, receipt_path, **kwargs)
            result["execution"].update(command=list(sys.orig_argv), cwd=str(Path.cwd()), python=sys.version)
            result["output_reservation"] = {"method": "exclusive-create-before-intake", "failed_attempts_retained": True}
            write_record(stream, result)
        except BaseException as error:
            attempt.update(status="FAILED", exception={"type": type(error).__name__, "message": str(error)})
            write_record(stream, attempt)
            raise
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--field-sha256", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--gate-sha256", default=GATE_SHA)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = consume_to_file(args.field, args.receipt, args.out, expected_field_sha256=args.field_sha256,
        expected_receipt_sha256=args.receipt_sha256, admission_sha256=args.gate_sha256)
    print(json.dumps({"output": str(args.out), "state_id": result["state_id"], "case_id": result["case_id"]}))


if __name__ == "__main__":
    main()

"""Current raised-screw / selected-hardware conditional first-order response.

Reuse the frozen cached-solid, panel, contact, solve and saved-field audit APIs.
Only source intake, the eight spacer roles and their axial capture stations,
panel apertures/ports, and provenance change. No native FEA or design remedy.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
DOC = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1"
MANIFEST = DOC / "selected-hardware-v1/current-response-v1/inputs.json"
RAW = ROOT / "fea/generated/selected-hardware-followup-v1/current-response-v1"
INPUT_SCHEMA = "eoere_selected_hardware_first_order_inputs/v1"
EXPORT_SCHEMA = "eoere_selected_hardware_cached_sources/v1"
REVIEW_SCHEMA = "eoere_selected_hardware_inputs_review/v1"
REVIEW_SUCCESS = "current_selected_hardware_source_checks_pass"
METHOD_SCHEMA = "eoere_selected_hardware_fixed_floor_method/v1"
FIELD_SCHEMA = "eoere_selected_hardware_fixed_floor_candidate/v1"
SUCCESS = "current_selected_hardware_equilibrium_and_recovery_pass"
_modules = {}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ref(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "repository source required")
    digest = sha(path)
    require(path != OWN or digest == LOADED_SHA, "loaded response adapter changed")
    return {"path": str(path.relative_to(ROOT)), "sha256": digest}


def read(source):
    path = ROOT / source["path"]
    require(sha(path) == source["sha256"], "source changed: " + source["path"])
    return json.loads(path.read_bytes())


def manifest():
    data = json.loads(MANIFEST.read_bytes())
    require(data["schema"] == "eoere_selected_hardware_current_response_sources/v1"
            and data["optional_extra_grid"] is False and not any(data["release"].values()),
            "current OFF manifest with all releases false required")
    return data


def load(key):
    source = manifest()["references"][key]
    require(sha(ROOT / source["path"]) == source["sha256"], "frozen method changed")
    if key not in _modules:
        spec = importlib.util.spec_from_file_location("eoere_selected_response_" + key, ROOT / source["path"])
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _modules[key] = module
    return _modules[key]


def join(*maps):
    result = {}
    for pins in maps:
        for name, digest in pins.items():
            require(name not in result or result[name] == digest, "source pin conflict: " + name)
            result[name] = digest
    return result


def verify(pins):
    require(sha(OWN) == LOADED_SHA, "loaded response adapter changed")
    for name, digest in pins.items():
        require(sha(ROOT / name) == digest, "source drift: " + name)
    return pins


def selected_sources(old, channels, geometry):
    sources = {r["id"]: copy.deepcopy(r["source"]) for r in old["finished_body_observations"]}
    before = {name: row["sha256"] for name, row in sources.items()}
    for row in channels["changed_finished_solids"]:
        require(row.get("variant") in {"base", "common", "extra"}, "explicit channel variant required")
        if row["id"] in sources and row["variant"] in {"base", "common"}:
            sources[row["id"]] = copy.deepcopy(row)
    for row in geometry["changed_finished_solids"]:
        if row["id"] in sources:
            sources[row["id"]] = copy.deepcopy(row)
    require({name for name, row in sources.items() if row["sha256"] != before[name]}
            == {"base_principal_center_right", "kicker_left", "kicker_right"},
            "OFF geometry must change only one principal and two kicker panels")
    return sources


def current_metadata():
    config = manifest()
    references = config["references"]
    old = read(references["prior_export"])
    geometry, channels, hardware, prior = (read(references[k]) for k in
                                            ("geometry", "channels", "hardware", "prior_geometry"))
    require(geometry["axes"] == channels["axes"] == prior["axes"], "all100 bolt axes must stay fixed")
    require(hardware["parents"]["base"] == references["geometry"]
            and hardware["wood_screw_revision"] == geometry["revision"], "hardware/wood binding differs")
    pins = join(old["source_sha256"], geometry["source_sha256"], channels["source_sha256"],
                {r["path"]: r["sha256"] for r in references.values()},
                {r["path"]: r["sha256"] for r in (ref(OWN), ref(MANIFEST))})
    source_map = read(hardware["source_map"])
    pins = join(pins, source_map, {hardware["source_map"]["path"]: hardware["source_map"]["sha256"]})
    sources = selected_sources(old, channels, geometry)
    for row in sources.values():
        bounds = row.get("bounds_xyz_mm")
        if bounds and len(bounds) == 6:
            row["bounds_xyz_mm"] = [bounds[i:i+2] for i in (0, 2, 4)]
    pins = join(pins, {r["path"]: r["sha256"] for r in sources.values()})
    screws = {r["axis_id"]: r for r in geometry["screw_axes"]}
    before = {r["axis_id"]: r for r in prior["screw_axes"]}
    moves = {name: [b-a for a, b in zip(before[name]["origin_xyz_mm"], row["origin_xyz_mm"], strict=True)]
             for name, row in screws.items() if row != before[name]}
    require(moves == {"round_kicker_left_rim_2": [0., 0., 20.],
                      "round_kicker_right_rim_2": [0., 0., 20.]}, "exact two reviewed screw moves required")
    current = copy.deepcopy(old)
    for row in current["hillman_rows"]:
        identity = row["id"]
        row["source_screw_descriptor"] = copy.deepcopy(screws[identity])
        if identity in moves:
            row["point_xyz_mm"] = [a+b for a, b in zip(row["point_xyz_mm"], moves[identity], strict=True)]
    for row in current["current_panel_machining_descriptors"]["features"]:
        if row["identity"] in moves:
            row["start_xyz_mm"] = copy.deepcopy(screws[row["identity"]]["origin_xyz_mm"])
    for row in current["auxiliary_metal_gravity_descriptors"]:
        moved = [name for name in moves if row["id"].startswith("fastener_"+name+"/")]
        if moved:
            row["center_xyz_mm"] = [a+b for a, b in zip(row["center_xyz_mm"], moves[moved[0]], strict=True)]
    selected = {r["axis_id"]: r for r in hardware["selected_stacks"]}
    require(len(selected) == 100 and sum(r["nut_side_spacer_mm"] > 0 for r in selected.values()) == 8,
            "100 selected stacks and eight spacers required")
    axes = copy.deepcopy(geometry["axes"])
    for axis in axes:
        choice = selected[axis["id"]]
        require(choice["selected_diameter_mm"] == axis["diameter_mm"], "bolt diameter changed")
        axis["nominal_under_head_length_mm"] = choice["selected_underhead_length_mm"]
        axis["tip_projection_beyond_nut_mm"] += choice["selected_tip_delta_mm"] - choice["nut_side_spacer_mm"]
        axis["nut_side_spacer_mm"] = choice["nut_side_spacer_mm"]
    verify(pins)
    return current, sources, axes, selected, pins


def spacer_roles(axis, method, volumes, original):
    rows = original(axis, method, volumes)
    length = axis.get("nut_side_spacer_mm", 0.)
    if length:
        direction = method.unit(axis["direction_xyz"])
        nut = next(r for r in rows if r["kind"] == "nut")
        nut["center_of_mass_xyz_mm"] = method.add(nut["center_of_mass_xyz_mm"], method.scale(direction, length))
        station = axis["grip_mm"] + axis["after_plate_mm"] + axis["hardware_scenario"]["washer_thickness_mm"] + length/2
        volume = math.pi/4*(19.05**2-10.31875**2)*length
        rows.append({"id": axis["id"]+"/spacer", "kind": "spacer", "volume_mm3": volume,
                     "mass_kg": volume*7850e-9,
                     "center_of_mass_xyz_mm": method.add(axis["point_xyz_mm"], method.scale(direction, station)),
                     "basis": "source-bound nominal selected annulus; separate own-shaft gravity role"})
    return rows


def spacer_ends(axis, surfaces, method, original):
    ends = original(axis, surfaces, method)
    ends[1]["pressure_face_s_mm"] += axis.get("nut_side_spacer_mm", 0.)
    ends[1]["own_spacer_length_mm"] = axis.get("nut_side_spacer_mm", 0.)
    return ends


def export_sources(slot_path, slot_sha):
    old, sources, axes, _, pins = current_metadata()
    exporter = load("cached_exporter")
    ex, method = exporter.a.generic()
    prior_inputs = read(manifest()["references"]["prior_inputs"])
    report = {"axes": axes, "scenario": read({"path": ex.REPORT, "sha256": ex.REPORT_SHA})["scenario"],
              "finished_solids": [sources[r["name"]] for r in old["raw_gross_timber_rows"]]}
    panels = [sources[name] for name in prior_inputs["panel_ids"]]
    prepared = {**old, "geometry": manifest()["references"]["geometry"],
                "gross_raw_timber_rows": old["raw_gross_timber_rows"],
                "floor_descriptors": old["floor_observations"]}
    role_original, ends_original = ex.role_rows, ex.end_seats
    with patch.object(exporter, "prepare", lambda *_: (prepared, prior_inputs, report, panels, pins)), \
            patch.object(ex, "role_rows", lambda a, m, v: spacer_roles(a, m, v, role_original)), \
            patch.object(ex, "end_seats", lambda a, s, m: spacer_ends(a, s, m, ends_original)), \
            patch.object(exporter.a, "generic", lambda: (ex, method)):
        result = exporter.export_native(MANIFEST, sha(MANIFEST), slot_path, slot_sha)
    for key in ("parameters", "material_scenario", "support", "case_provider", "panel_refresh"):
        result[key] = copy.deepcopy(old[key])
    result["panel_refresh"].update(fresh_aperture_K_mass_and_screw_port_panels=
        ["kicker_left", "kicker_right", "main_lower_right", "main_upper_right"],
        unchanged_panel_K_candidates=["main_lower_left", "main_upper_left"])
    result["case_provider"] = {"method": "unchanged scripts.thin_bolted_frame_mechanics.load_cases",
                               "shaft_metal_role_count": 508, "original_six_live_cases_retained": True}
    for row in result["physical_owner_gravity_rows"]:
        if row["kind"] == "shaft":
            row["gravity_route"] = "separate own nominal metal-role loads, including each selected spacer; no duplicate selfweight"
    result.update(schema=EXPORT_SCHEMA, manifest=ref(MANIFEST), hardware_model=manifest()["references"]["hardware"],
                  geometry_review_evidence={"source_manifest": ref(MANIFEST), "all_axes_retained": True},
                  release=copy.deepcopy(manifest()["release"]),
                  remaining=["Current independent source review, fresh six fields and own saved-field audits"])
    return result


def panel_sources():
    pb = load("panel_bank")
    plan, prior, current, moved, pins = pb.read_sources()
    metadata, sources, _, _, current_pins = current_metadata()
    current["panel_machining"] = metadata["current_panel_machining_descriptors"]
    current["screw_axes"] = [r["source_screw_descriptor"] for r in metadata["hillman_rows"]]
    current["finished_panel_solids"] = [pb.source_binding(sources[n]) for n in pb.plate.PANELS]
    moved = sorted(set(moved) | {"round_kicker_left_rim_2", "round_kicker_right_rim_2"})
    return plan, prior, current, moved, join(pins, current_pins)


@contextmanager
def panel_context():
    pb = load("panel_bank")
    values = panel_sources()
    with patch.object(pb, "read_sources", lambda: values), \
            patch.object(pb, "GEOMETRY", manifest()["references"]["geometry"]), \
            patch.object(pb, "CHANGED", {"main_lower_right", "main_upper_right", "kicker_left", "kicker_right"}), \
            patch.object(pb, "SCHEMA", "eoere_selected_hardware_panel_sources/v1"):
        yield pb


def source_inputs():
    with panel_context() as pb:
        return pb.source_inputs()


def verify_panel_source_inputs(data, proof=None):
    with panel_context() as pb:
        return pb.verify_panel_source_inputs(data, proof)


def load_panel_dependencies(data):
    with panel_context() as pb:
        panels, integrated, pins, proof = pb.load_panel_dependencies(data)
        proof["schema"] = "eoere_selected_hardware_panel_preparation/v1"
        proof["limits"] = ["Twelve current apertures in four panels refreshed from the frozen raised bank.",
                           "Generic Hillman stiffness prior; no product resistance or complete joint acceptance."]
        return panels, integrated, pins, proof


def compile_validator(factory, compiler):
    """Extend only the role census; retain every numerical/source check."""
    source = Path(factory.__file__)
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == factory.LOADED_SHA,
            "exact loaded factory compiler bytes changed")
    tree = ast.parse(raw)
    node = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "validate_rows"))
    changes = 0
    for part in ast.walk(node):
        if isinstance(part, ast.Constant) and part.value == 500:
            part.value = 508
            changes += 1
        if isinstance(part, ast.Compare) and isinstance(part.left, ast.Call) and ast.unparse(part.left) == "len(row['metal_roles'])":
            require(len(part.ops) == 1 and isinstance(part.ops[0], ast.Eq) and part.comparators[0].value == 5,
                    "exact original role-census hook required")
            part.ops, part.comparators = [ast.In()], [ast.Tuple(elts=[ast.Constant(5), ast.Constant(6)], ctx=ast.Load())]
            changes += 1
    require(changes == 2, "two original role-census hooks required")
    namespace = {**vars(factory), "SCHEMA": INPUT_SCHEMA}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(compiler), "exec"), namespace)  # noqa: S102
    original = namespace["validate_rows"]

    def validate(data, **kwargs):
        if not kwargs.get("synthetic", False):
            selected = {r["axis_id"]: r for r in read(manifest()["references"]["hardware"])["selected_stacks"]}
            validate_metal_roles(data["shafts"], selected)
        return original(data, **kwargs)
    return validate


def validate_metal_roles(shafts, selected):
    require(len(shafts) == len(selected) == 100 and {r["axis_id"] for r in shafts} == set(selected),
            "exact100 selected shaft identities required")
    for shaft in shafts:
        expected = {"head", "shaft", "nut", "head_washer", "nut_washer"}
        if selected[shaft["axis_id"]]["nut_side_spacer_mm"]:
            expected.add("spacer")
        require({r["kind"] for r in shaft["metal_roles"]} == expected
                and len(shaft["metal_roles"]) == len(expected), "exact selected per-shaft role census differs")


def require_current_sources(data):
    require(data["schema"] == INPUT_SCHEMA and data["optional_2026_extra"] is False
            and data["release"] == manifest()["release"], "distinct current inputs required")
    refs = data["geometry"]
    require(set(refs) == {"report", "source_manifest", "cached_source_export"}
            and refs["report"] == manifest()["references"]["geometry"] and refs["source_manifest"] == ref(MANIFEST),
            "exact current geometry and source manifest required")
    exported = read(refs["cached_source_export"])
    require(exported["schema"] == EXPORT_SCHEMA and exported["hardware_model"] == manifest()["references"]["hardware"]
            and exported["geometry"] == refs["report"] and exported["manifest"] == refs["source_manifest"]
            and exported["source_pins_before_after_unchanged"] is True
            and exported["native_cached_solid_queries_performed"] is True
            and exported["fresh_contact_domains_not_copied_from_old_field"] is True
            and exported["native_nominal_flat_reference_flange_masks_created"] == 88
            and exported["candidate_CAD_rebuild_mesh_K_assembly_factorization_q_forces_load_cases_or_native_solve_performed"] is False
            and exported["release"] == manifest()["release"],
            "current own selected-hardware export required")
    joins = {"timber_rows": "raw_gross_timber_rows", "base_bodies": None,
             "fitting_port_bindings": "fitting_ports"}
    for key in ("physical_owner_gravity_rows", "fitting_poses", "all_factory_holes", "shafts",
                "finished_receiver_wall_queries", "finished_body_observations", "direct_contacts", "hillman_rows",
                "current_panel_machining_descriptors", "flange_domains", "flange_shared_face_patches",
                "timber_and_panel_shared_face_patches", "shared_pair_query_census", "parameters"):
        joins[key] = key
    for key, other in joins.items():
        expected = exported[other] if other else [r for r in exported["physical_owner_gravity_rows"] if r["kind"] != "shaft"]
        require(data[key] == expected, "current source join differs: " + key)
    require(data["scenario"] == exported["material_scenario"]
            == read(manifest()["references"]["prior_export"])["material_scenario"],
            "material/stiffness assumptions changed")
    require(data["panel_ids"] == sorted(r["id"] for r in exported["physical_owner_gravity_rows"] if r["kind"] == "panel")
            and data["factory_holes"] == [{**hole, "angle_id": angle["angle_id"],
                "used": hole["installed_bolt_axis_id"] is not None}
                for angle in exported["all_factory_holes"] for hole in angle["holes"]],
            "complete own panels/factory holes differ")
    require(data["floor_footprints"] == {r["host"]: r["observed_normal_reference_points_xyz_mm"]
                                         for r in exported["floor_observations"]}, "floor geometry changed")
    require(all(data["source_sha256"].get(p) == h for p, h in exported["source_sha256"].items()),
            "cached-source closure incomplete")
    require(all(data["source_sha256"].get(r["path"]) == r["sha256"] for r in refs.values()),
            "current source reference is outside source closure")
    verify(data["source_sha256"])
    return exported


@contextmanager
def response_context():
    fixed = load("bridge")
    b = fixed.frozen()
    with fixed.corrected_context(b), ExitStack() as stack:
        original_pins = b.source_pins
        def pins(extra=None, *, method=None):
            return original_pins(join(extra or {}, {r["path"]: r["sha256"] for r in (ref(OWN), ref(MANIFEST))}), method=method)
        values = {"OWN": OWN, "LOADED_SHA": LOADED_SHA, "GEOMETRY": manifest()["references"]["geometry"],
                  "SOURCE_MANIFEST": ref(MANIFEST), "PANEL_BANK": ref(OWN), "INPUT_SCHEMA": INPUT_SCHEMA,
                  "REVIEW_SCHEMA": REVIEW_SCHEMA, "REVIEW_SUCCESS": REVIEW_SUCCESS, "METHOD_SCHEMA": METHOD_SCHEMA,
                  "FIELD_SCHEMA": FIELD_SCHEMA, "STATE_PREFIX": "eoere-selected-hardware-fixed-floor-",
                  "ADMISSION_SCHEMA": "eoere_selected_hardware_field_admission/v1", "SUCCESS": SUCCESS,
                  "source_pins": pins, "require_current_sources": require_current_sources}
        for name, value in values.items():
            stack.enter_context(patch.object(b, name, value))
        stack.enter_context(patch.object(b.factory, "validate_rows", compile_validator(b.factory, OWN)))
        yield b, fixed


def build_inputs(export_path):
    with response_context() as (b, _):
        original_load = b.load
        def current_load(path, digest, name):
            module = original_load(path, digest, name)
            if Path(path).name != "cases.py":
                return module
            def derive(evidence, geometry, **kwargs):
                verify(kwargs["source_sha256"])
                roles = [r for r in geometry["bolt_gravity_components"] if r["owner"].startswith("shaft/")]
                require(len(roles) == 508 and len({r["id"] for r in roles}) == 508, "508 unique current metal roles required")
                cases, gravity = module.frame.load_cases(evidence, geometry)
                cases = [r for r in cases if r["primary_load_basis"]]
                for case in cases:
                    for row in case["loads"]:
                        if row["id"].startswith("bolt-weight/") and row["body"].startswith("shaft/"):
                            row["id"] = "physical-bolt-metal/" + row["id"].removeprefix("bolt-weight/")
                return cases, gravity
            return SimpleNamespace(derive_fresh_cases=derive)
        with patch.object(b, "load", current_load):
            result = b.build_inputs(ref(export_path), ref(MANIFEST), ref(OWN))
        return result


def write(path, data):
    path = output_path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(data, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def output_path(path):
    path = Path(os.path.abspath(path))
    require(path.parent.resolve().is_relative_to(RAW.resolve()), "fresh ignored response output required")
    return path


def preflight_pins(args, source_pins, extra=None, *, method=None):
    """Carry the separately verified raw input pointer into the review join."""
    pins = dict(extra or {})
    if args.inputs is not None and args.inputs_sha256 is not None:
        path = args.inputs.resolve()
        require(path.is_relative_to(ROOT) and sha(path) == args.inputs_sha256,
                "preflight raw input bytes differ")
        pins = join(pins, {str(path.relative_to(ROOT)): args.inputs_sha256})
    return source_pins(pins, method=method)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--mode" in argv and argv[argv.index("--mode")+1] in ("export", "inputs"):
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--mode", choices=("export", "inputs"), required=True)
        parser.add_argument("--out", type=Path, required=True)
        parser.add_argument("--source-export", type=Path)
        parser.add_argument("--slot", type=Path)
        parser.add_argument("--slot-sha256")
        args = parser.parse_args(argv)
        args.out = output_path(args.out)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        fixed = load("bridge")
        with fixed.reserve(args.out) as output:
            result = (export_sources(args.slot, args.slot_sha256) if args.mode == "export"
                      else build_inputs(args.source_export))
            output.write(result)
        print(json.dumps({"output": str(args.out), "sha256": sha(args.out)}))
        return 0
    with response_context() as (b, fixed):
        args = b.parse_args(argv)
        require(args.out.resolve().is_relative_to(RAW), "ignored current-response output required")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with fixed.reserve(args.out) as output:
            if args.mode == "run":
                return fixed.run_reserved(args, output, b)
            if args.mode == "admit":
                result = b.audit(args.field)
            else:
                context = {**vars(b), "source_pins": lambda extra=None, **kw:
                           preflight_pins(args, b.source_pins, extra, **kw)}
                preflight = b.compile_function(fixed.FROZEN, "preflight", context, replacements={
                    "eoere_extended_cleat_cached_source_export/v1": EXPORT_SCHEMA},
                    expected_counts={"eoere_extended_cleat_cached_source_export/v1": 1})
                result = preflight(args)
            output.write(b.core.serial(result))
            print(json.dumps({"output": str(args.out), "sha256": sha(args.out)}))
            return 0


if __name__ == "__main__":
    raise SystemExit(main())

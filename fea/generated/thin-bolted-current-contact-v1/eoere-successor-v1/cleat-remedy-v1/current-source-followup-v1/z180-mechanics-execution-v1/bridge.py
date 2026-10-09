"""Deferred unadopted Z180 source/input/execution adapter; no import-time work.

The frozen491653 bridge owns preparation, fixed-support solve and saved-field
admission arithmetic. This adapter owns proposal source identities/joins and a
proved unchanged-panel reuse view. No descriptor/input trial is implied by its
source preflight. Parent owns independent readiness and serialized execution.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = OWN.parents[7]
BASE = OWN.parents[3]
PRODUCTION = BASE / "adjusted-base-mechanics-v1/current-force-bridge-v1/review-fix-v2/bridge.py"
PRODUCTION_SHA = "4916532168ba05268e164b28bb634743013b4aa7e062b7f9d345ecfafb954643"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
GEOMETRY = {"path": str((OWN.parent.parent / "viewer-revision-v1/runs-v1/export01/layout.json").relative_to(ROOT)),
            "sha256": "4886a4bccaee43b93b23e521710b7d8b84dcb7b5ba627ef722694ceb79b7f319"}
SOURCE_MANIFEST = {"path": str(OWN.with_name("parent-sources-v1.json").relative_to(ROOT)),
                   "sha256": "60167af5e6dc11207bf17df0b62a9c3177d4ec3109531d6e7d3068023eee91c2"}
PARENT_DESCRIPTOR = {"path": str((BASE / "adjusted-base-mechanics-v1/current-source-observations-v1/attempt01.json").relative_to(ROOT)),
                     "sha256": "0f7e95f0dabfb5f0b5d63f8ef7d78e3c52c07672b4f482a89a89496eec703de7"}
PARENT_INPUT = {"path": str((BASE / "adjusted-base-mechanics-v1/current-inputs-v1/attempt01/inputs.json").relative_to(ROOT)),
                "sha256": "f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa"}
INPUT_SCHEMA = "eoere_z180_first_order_mechanics_inputs/v1"
DESCRIPTOR_SCHEMA = "eoere_z180_geometry_delta_descriptors/v1"
REVIEW_SCHEMA = "eoere_z180_mechanics_inputs_independent_review/v1"
REVIEW_SUCCESS = "independent_z180_source_input_checks_pass"
METHOD_SCHEMA = "eoere_z180_fixed_floor_method_inputs/v1"
FIELD_SCHEMA = "eoere_z180_fixed_floor_candidate/v1"
ADMISSION_SCHEMA = "eoere_z180_fixed_floor_independent_field_admission/v1"
SUCCESS = "unadopted_z180_equilibrium_and_recovery_pass"
STATE_PREFIX = "eoere-z180-fixed-floor-"
RELEASE = {key: False for key in ("candidate_accepted", "complete_joint_acceptance", "capacity_established",
                                "fabrication_released", "structural_released", "climbing_released")}
ROW_JOINS = {
    "timber_rows": "raw_gross_timber_rows", "physical_owner_gravity_rows": "physical_owner_gravity_rows",
    "fitting_poses": "fitting_poses", "fitting_port_bindings": "fitting_ports", "all_factory_holes": "all_factory_holes",
    **{name: name for name in ("shafts", "finished_receiver_wall_queries", "finished_body_observations", "direct_contacts",
       "hillman_rows", "current_panel_machining_descriptors", "flange_domains", "flange_shared_face_patches",
       "timber_and_panel_shared_face_patches", "shared_pair_query_census")},
}
_production = None


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_ref(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"} and not Path(ref["path"]).is_absolute(),
            "exact repository-relative proposal source reference required")
    path = (ROOT / ref["path"]).resolve()
    require(path.is_relative_to(ROOT) and sha(path) == ref["sha256"], "proposal source bytes differ")
    return json.loads(path.read_bytes())


def production():
    global _production
    require(sha(PRODUCTION) == PRODUCTION_SHA and sha(OWN) == LOADED_SHA, "frozen production/proposal bridge changed")
    if _production is None:
        spec = importlib.util.spec_from_file_location("eoere_z180_frozen_corrected_production", PRODUCTION)
        _production = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _production
        spec.loader.exec_module(_production)
    return _production


def manifest():
    value = read_ref(SOURCE_MANIFEST)
    require(value["schema"] == "eoere_z180_analytical_mechanics_frozen_sources/v1"
            and value["geometry"] == GEOMETRY and value["parent_descriptors"] == PARENT_DESCRIPTOR
            and value["parent_source_delta_preparation_authorized"] is True
            and value["optional_2026_extra"] is False and not any(value["release"].values())
            and value["readiness"]["candidate_operator_assembly_or_solve"] is False,
            "exact source-only unadopted parent authority required")
    return value


def source_pins(w, b, extra=None, *, method=None):
    additions = dict(extra or {})
    for path, digest in {str(OWN.relative_to(ROOT)): LOADED_SHA,
                         GEOMETRY["path"]: GEOMETRY["sha256"], SOURCE_MANIFEST["path"]: SOURCE_MANIFEST["sha256"]}.items():
        require(path not in additions or additions[path] == digest, "proposal source pin conflict")
        additions[path] = digest
    return w.runtime_source_pins(b, additions, method=method)


def validate_descriptor(exported):
    """Consume authentic analytic descriptors; never assert fresh native queries."""
    authority = manifest()
    require(exported.get("schema") == DESCRIPTOR_SCHEMA and exported.get("geometry") == GEOMETRY
            and exported.get("manifest") == SOURCE_MANIFEST and exported.get("parent_descriptors") == PARENT_DESCRIPTOR
            and exported.get("parent_geometry") == authority["parent_geometry"]
            and exported.get("status") == "SOURCE_ONLY_UNADOPTED_Z180_DESCRIPTORS_PENDING_INDEPENDENT_REVIEW"
            and exported.get("source_pins_before_after_unchanged") is True
            and exported.get("native_CAD_BREP_import_K_panel_preparation_response_or_solve_performed") is False
            and exported.get("current_4in_hardware_retained_spacer_proposal_excluded") is True
            and exported.get("historical_q_forces_operators_or_acceptance_transferred") is False
            and exported.get("force_execution_readiness_claimed") is False
            and exported.get("complete_joint_resistance", "missing") is None
            and exported.get("release") and not any(exported["release"].values()),
            "distinct complete source-only unadopted Z180 descriptor required")
    require(not any(key in exported for key in ("q", "response", "old_field", "native_cached_solid_queries_performed")),
            "response or relabeled native-current descriptor prohibited")
    for ref in (GEOMETRY, SOURCE_MANIFEST, PARENT_DESCRIPTOR, authority["saved_finished_receiver_evidence"]):
        require(exported["source_sha256"].get(ref["path"]) == ref["sha256"], "proposal descriptor reference outside source closure")
    parent = read_ref(PARENT_DESCRIPTOR)
    require(all(exported["source_sha256"].get(path) == digest for path, digest in parent["source_sha256"].items()),
            "proposal descriptor omits inherited exact sources")
    for key in ("parameters", "material_scenario", "support", "raw_gross_timber_rows", "fitting_poses", "fitting_ports",
                "all_factory_holes", "hillman_rows", "current_panel_machining_descriptors"):
        require(exported[key] == parent[key], "protected source primitive differs: " + key)
    counts = exported["geometry_delta_proof"]["counts"]
    require(all(counts.get(key) == value for key, value in {
        "finished_owners_changed": 4, "shaft_axes_changed": 4, "hardware_role_locations_changed": 20,
        "wall_occurrences_moved": 8, "wall_occurrences_rebound_same_axis": 8,
        "contact_patches_rebuilt": 2, "contact_cells_rebuilt": 12, "physical_owners": 150, "shafts": 100, "Hillman_screws": 66}.items()),
        "complete declared four-axis/eight-hole/two-patch proposal proof required")
    require((len(exported["shafts"]), len(exported["physical_owner_gravity_rows"]), len(exported["hillman_rows"]),
             len(exported["finished_body_observations"]), len(exported["finished_receiver_wall_queries"])) == (100, 150, 66, 28, 120),
            "proposal source census differs")
    proposed = {row["id"]: row for row in read_ref(GEOMETRY)["proposed_axes"]}
    old_shafts = {row["axis_id"]: row for row in parent["shafts"]}
    require(set(proposed) == set(authority["declared_changes"]["axis_ids"]), "exact four proposal source axes required")
    for shaft in exported["shafts"]:
        axis_id = shaft["axis_id"]
        old = old_shafts[axis_id]
        if axis_id not in proposed:
            require(shaft == old, "unmoved physical shaft descriptor changed")
            continue
        require(shaft["source_axis"] == proposed[axis_id] and shaft["point"] == proposed[axis_id]["point_xyz_mm"]
                and proposed[axis_id]["nominal_under_head_length_mm"] == 101.6 and len(shaft["metal_roles"]) == 5,
                "own four-axis patch must retain nominal4in hardware")
        for role, prior in zip(shaft["metal_roles"], old["metal_roles"], strict=True):
            require({key: value for key, value in role.items() if key not in {"basis", "center_of_mass_xyz_mm"}}
                    == {key: value for key, value in prior.items() if key not in {"basis", "center_of_mass_xyz_mm"}}
                    and role["center_of_mass_xyz_mm"] == [prior["center_of_mass_xyz_mm"][0], prior["center_of_mass_xyz_mm"][1],
                                                         prior["center_of_mass_xyz_mm"][2]-20.],
                    "same nominal metal role with only Z180 translation required; no spacer")
    return parent


def require_sources(data):
    require(data.get("schema") == INPUT_SCHEMA and data.get("optional_2026_extra") is False
            and data.get("historical_q") is None and data.get("old_field") is None,
            "distinct own Z180 OFF inputs without predecessor response required")
    refs = data["geometry"]
    require(set(refs) == {"report", "source_manifest", "cached_source_export"}
            and refs["report"] == GEOMETRY and refs["source_manifest"] == SOURCE_MANIFEST,
            "exact proposal layout/parent manifest/own descriptor references required")
    exported = read_ref(refs["cached_source_export"])
    validate_descriptor(exported)
    require(data["release"] == RELEASE, "proposal inputs must retain exact release policy")
    for ref in refs.values():
        require(data["source_sha256"].get(ref["path"]) == ref["sha256"], "input reference outside own source closure")
    require(all(data["source_sha256"].get(path) == digest for path, digest in exported["source_sha256"].items()),
            "input descriptor source closure incomplete")
    for own_key, source_key in ROW_JOINS.items():
        require(data[own_key] == exported[source_key], "own proposal descriptor join differs: " + own_key)
    require(data["base_bodies"] == [row for row in exported["physical_owner_gravity_rows"] if row["kind"] != "shaft"]
            and data["floor_footprints"] == {row["host"]: row["observed_normal_reference_points_xyz_mm"] for row in exported["floor_observations"]}
            and data["parameters"] == exported["parameters"] and data["scenario"] == exported["material_scenario"],
            "own proposal base/floor/material join differs")
    require(data["panel_ids"] == sorted(row["id"] for row in exported["physical_owner_gravity_rows"] if row["kind"] == "panel")
            and data["factory_holes"] == [{**hole, "angle_id": angle["angle_id"], "used": hole["installed_bolt_axis_id"] is not None}
                for angle in exported["all_factory_holes"] for hole in angle["holes"]], "own panel/factory-hole join differs")
    return {"report": read_ref(GEOMETRY), "source_manifest": manifest(), "cached_source_export": exported}


def panel_view(data, source_inputs):
    """Only a proved panel reuse view names the old bank's actual geometry."""
    authority = manifest()
    require(data["geometry"]["report"] == GEOMETRY and source_inputs["geometry"] == authority["parent_geometry"]
            and data["panel_operator_source_inputs"] == source_inputs, "original panel-source geometry identity must remain explicit")
    parent = read_ref(PARENT_DESCRIPTOR)
    ids = set(data["panel_ids"])
    original_rows = {row["id"]: row for row in parent["finished_body_observations"] if row["id"] in ids}
    own_rows = {row["id"]: row for row in data["finished_body_observations"] if row["id"] in ids}
    require(len(ids) == len(own_rows) == len(original_rows) == 6 and own_rows == original_rows,
            "six unchanged own finished panel sources/volume/COM observations required")
    require(data["current_panel_machining_descriptors"] == parent["current_panel_machining_descriptors"]
            and len(data["current_panel_machining_descriptors"]["features"]) == 340
            and data["hillman_rows"] == parent["hillman_rows"] and len(data["hillman_rows"]) == 66,
            "unchanged own340 apertures and66 screw ports required")
    require([row for row in data["physical_owner_gravity_rows"] if row["kind"] == "panel"]
            == [row for row in parent["physical_owner_gravity_rows"] if row["kind"] == "panel"], "own panel gravity/COM differs")
    view = {**data, "geometry": {**data["geometry"], "report": authority["parent_geometry"]}}
    proof = {"proposal_geometry": GEOMETRY, "panel_source_geometry": authority["parent_geometry"],
             "parent_descriptor": PARENT_DESCRIPTOR, "unchanged_six_source_volume_COM_rows": original_rows,
             "apertures": 340, "screw_ports": 66, "historical_q_actions_or_contacts_reused": False}
    return view, proof


class PanelProxy:
    def __init__(self, bank, bridge=None):
        self.bank, self.bridge, self.method = bank, bridge, None

    def authenticate(self, data):
        require(self.bridge is not None and self.method is not None, "own raw source review required before panel callback")
        b, method = self.bridge, self.method
        raw = read_ref(method["input"])
        expected, selection = b.driver.select_case(raw, data["case"]["case_id"])
        require(data == expected, "panel callback source view differs from reviewed own input")
        pins = b.source_pins({**raw["source_sha256"], method["input"]["path"]: method["input"]["sha256"]})
        b.authenticate_review(method["input_review"], data, pins, raw_data=raw, selection=selection)

    def source_inputs(self):
        return self.bank.source_inputs()  # Original bank identity is never relabeled.

    def verify_panel_source_inputs(self, data, proof=None):
        if proof is not None:
            self.authenticate(data)
        view, reuse = panel_view(data, self.source_inputs())
        original_proof = None
        if proof is not None:
            require(proof["schema"] == "eoere_z180_unchanged_panel_reuse_preparation/v1" and proof["reuse"] == reuse,
                    "own proposal panel reuse proof differs")
            original_proof = proof["original_panel_preparation"]
        return self.bank.verify_panel_source_inputs(view, original_proof)

    def load_panel_dependencies(self, data):
        self.authenticate(data)
        view, reuse = panel_view(data, self.source_inputs())
        panels, integrated, pins, proof = self.bank.load_panel_dependencies(view)
        return panels, integrated, pins, {"schema": "eoere_z180_unchanged_panel_reuse_preparation/v1", "reuse": reuse,
                                        "original_panel_preparation": proof, "source_sha256": pins}


def read_method(b, path, digest):
    record = b.z180_original_read_method(path, digest)
    require(record.get("parent_execution_bridge_readiness_pass") is True
            and record.get("unchanged_panel_reuse_independently_reviewed") is True,
            "own parent-reviewed proposal execution/panel reuse readiness required")
    raw = read_ref(record["input"])
    require_sources(raw)
    require(record.get("source_export") == raw["geometry"]["cached_source_export"], "method source-export binding differs")
    source_review = record.get("descriptor_review")
    require(source_review is not None, "own independent proposal descriptor review required")
    reviewed = read_ref(source_review)
    require(reviewed.get("schema") == "eoere_z180_geometry_descriptors_independent_review/v1"
            and reviewed.get("success") == "independent_z180_descriptor_source_checks_pass"
            and reviewed.get("descriptor") == record["source_export"] and not any(reviewed["release"].values())
            and record["source_sha256"].get(source_review["path"]) == source_review["sha256"],
            "method lacks exact independent proposal descriptor review")
    pins = b.source_pins({**raw["source_sha256"], record["input"]["path"]: record["input"]["sha256"]})
    b.authenticate_review(record["input_review"], raw, pins)  # Before any bank callback, including saved admission.
    return record


def methods(b, record):
    centroidal = b.driver.load(b.driver.CENTROIDAL, b.driver.CENTROIDAL_SHA, "eoere_z180_genuine_centroidal")
    ref = record["panel_bank"]
    require(ref == manifest()["unchanged_panel_method"], "exact unchanged original panel method required")
    bank = b.load(ROOT / ref["path"], ref["sha256"], "eoere_z180_original_panel_bank")
    bank.method = record
    return centroidal, bank


@contextmanager
def context(w, b):
    with w.corrected_context(b), ExitStack() as stack:
        original_load, original_method = b.load, b.read_method
        def load(path, digest, name):
            module = original_load(path, digest, name)
            return PanelProxy(module, b) if Path(path).resolve() == ROOT / b.PANEL_BANK["path"] else module
        hooks = {"OWN": OWN, "LOADED_SHA": LOADED_SHA, "GEOMETRY": GEOMETRY, "SOURCE_MANIFEST": SOURCE_MANIFEST,
                 "INPUT_SCHEMA": INPUT_SCHEMA, "REVIEW_SCHEMA": REVIEW_SCHEMA, "REVIEW_SUCCESS": REVIEW_SUCCESS,
                 "METHOD_SCHEMA": METHOD_SCHEMA, "FIELD_SCHEMA": FIELD_SCHEMA, "STATE_PREFIX": STATE_PREFIX,
                 "ADMISSION_SCHEMA": ADMISSION_SCHEMA, "SUCCESS": SUCCESS, "read_ref": read_ref,
                 "require_current_sources": require_sources, "load": load, "z180_original_read_method": original_method,
                 "read_method": lambda path, digest: read_method(b, path, digest),
                 "methods": lambda record: methods(b, record),
                 "source_pins": lambda extra=None, *, method=None: source_pins(w, b, extra, method=method)}
        for name, value in hooks.items():
            stack.enter_context(patch.object(b, name, value, create=name == "z180_original_read_method"))
        yield b


def applied_wrench(loads):
    force = [math.fsum(row["force_xyz_n"][i] for row in loads) for i in range(3)]
    moment = [math.fsum(row["point_xyz_mm"][(i+1)%3]*row["force_xyz_n"][(i+2)%3]
                        - row["point_xyz_mm"][(i+2)%3]*row["force_xyz_n"][(i+1)%3]
                        + row.get("moment_xyz_nmm", [0., 0., 0.])[i] for row in loads) for i in range(3)]
    return force + moment


def input_reuse_checks(data):
    original = read_ref(PARENT_INPUT)
    require(data["floor_footprints"] == original["floor_footprints"], "proposal floor points/support hull changed")
    before = {row["case_id"]: applied_wrench(row["loads"]) for row in original["cases"]}
    after = {row["case_id"]: applied_wrench(row["loads"]) for row in data["cases"]}
    require(before.keys() == after.keys(), "source case roster changed")
    errors = {key: [abs(a-b) for a, b in zip(before[key], after[key], strict=True)] for key in before}
    require(all(max(row[:3]) <= 1e-9 and max(row[3:]) <= 1e-6 for row in errors.values()), "fresh source applied wrench changed")
    return {"source": PARENT_INPUT, "case_wrenches_xyz_n_xyz_nmm": after, "absolute_errors": errors,
            "force_tolerance_n": 1e-9, "moment_tolerance_nmm": 1e-6, "same_floor_points": True,
            "scope": "applied source wrench and nominal support geometry only; no elastic reaction/q/action or floor capacity transfer"}


def build_inputs(b, export_ref, manifest_ref, bank_ref):
    require(manifest_ref == SOURCE_MANIFEST and bank_ref == manifest()["unchanged_panel_method"], "own manifest/panel source bindings required")
    validate_descriptor(read_ref(export_ref))  # Reject old/delta-incomplete input before any panel callback.
    data = b.build_inputs(export_ref, manifest_ref, bank_ref)
    data["applied_source_wrench_reuse"] = input_reuse_checks(data)
    data["source_sha256"] = b.source_pins({**data["source_sha256"], PARENT_INPUT["path"]: PARENT_INPUT["sha256"]})
    return data


def preflight(args, b):
    provided, missing = {}, []
    for name in ("source_export", "inputs", "input_review", "method_input", "source_manifest", "panel_bank"):
        path, digest = getattr(args, name), getattr(args, name + "_sha256")
        if path is None or digest is None:
            missing.append(name)
        else:
            require(path.resolve().is_relative_to(ROOT) and sha(path) == digest, "provided proposal source bytes differ")
            provided[name] = {"path": str(path.resolve().relative_to(ROOT)), "sha256": digest}
    if "source_export" in provided:
        validate_descriptor(read_ref(provided["source_export"]))
    if "source_manifest" in provided:
        require(provided["source_manifest"] == SOURCE_MANIFEST, "supplied proposal manifest differs")
    if "panel_bank" in provided:
        require(provided["panel_bank"] == manifest()["unchanged_panel_method"], "supplied unchanged panel source differs")
    if "inputs" in provided:
        with b.factory_boundary():
            data, pins = b.read_inputs(args.inputs, args.inputs_sha256)
        if "input_review" in provided:
            b.authenticate_review(provided["input_review"], data, pins)
        if "source_export" in provided:
            require(data["geometry"]["cached_source_export"] == provided["source_export"], "supplied proposal descriptor/input mismatch")
    if "method_input" in provided:
        method = b.read_method(args.method_input, args.method_input_sha256)
        expected = {"inputs": method["input"], "input_review": method["input_review"], "source_export": method["source_export"],
                    "source_manifest": method["source_manifest"], "panel_bank": method["panel_bank"]}
        require(all(ref == expected[key] for key, ref in provided.items() if key in expected), "supplied reference differs from own method binding")
    return {"schema": "eoere_z180_execution_source_preflight/v1", "status": "SOURCE_ADAPTER_ONLY_PRODUCTION_UNPERFORMED",
        "provided": provided, "missing": missing, "geometry": GEOMETRY, "source_manifest": SOURCE_MANIFEST,
        "source_sha256": b.source_pins({ref["path"]: ref["sha256"] for ref in provided.values()}),
        "schemas": {"descriptor": DESCRIPTOR_SCHEMA, "inputs": INPUT_SCHEMA, "review": REVIEW_SCHEMA, "method": METHOD_SCHEMA,
                    "field": FIELD_SCHEMA, "admission": ADMISSION_SCHEMA}, "support": b.law.contract(),
        "generalized_residual_tolerance_n_inclusive": 1e-5, "production_readiness_claimed": False,
        "candidate_descriptor_or_input_construction_panel_K_frame_K_q_actions_solve_or_native_work_performed": False,
        "complete_joint_resistance": None, "unadopted_proposal": True, "release": dict(b.core.RELEASE)}


def proposal_output(output):
    def write(value):
        value = {**value, "unadopted_proposal": True, "proposal_geometry": GEOMETRY,
                 "complete_joint_resistance": None, "nut_spacer_proposal_included": False}
        output.write(value)
    return SimpleNamespace(path=output.path, owned=output.owned, write=write)


def run_case(args):
    w = production()
    with w.reserve(args.out) as output:
        b = w.frozen()
        with context(w, b):
            return w.run_reserved(args, proposal_output(output), b)


def audit(path):
    w = production()
    b = w.frozen()
    with context(w, b):
        return b.audit(path)


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    w = production()
    b = w.frozen()
    with context(w, b):
        return b.require_admitted_payload(field_bytes, receipt, admission_sha256=admission_sha256)


def main(argv=None):
    # Reserve through the genuine wrapper before its frozen numerical imports.
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    early = argparse.ArgumentParser(add_help=False)
    early.add_argument("--out", type=Path, required=True)
    out, _ = early.parse_known_args(argv)
    w = production()
    with w.reserve(out.out) as output:
        b = w.frozen()
        with context(w, b):
            args = b.parse_args(argv)
            if args.mode == "run":
                return w.run_reserved(args, proposal_output(output), b)
            if args.mode == "admit":
                require(args.field is not None, "own proposal field required")
                result = b.audit(args.field)
            elif args.mode == "build-inputs":
                def ref(name):
                    path, digest = getattr(args, name), getattr(args, name + "_sha256")
                    require(path is not None and digest is not None, "exact own " + name + " reference required")
                    return {"path": b.bundle.artifact_path(path.resolve()), "sha256": digest}
                result = build_inputs(b, ref("source_export"), ref("source_manifest"), ref("panel_bank"))
            else:
                result = preflight(args, b)
            proposal_output(output).write(b.core.serial(result))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

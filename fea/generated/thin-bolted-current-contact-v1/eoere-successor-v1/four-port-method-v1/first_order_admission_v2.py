"""Narrow corrected admission around immutable e61 saved-operator mechanics.

Two checked AST clauses requiring an absent historical producer flag are
removed. Own surface aliases additionally require exact source metadata and
table membership. No field/receipt is projected or relabeled; no original
module global, __file__, physical law or numerical algorithm is changed.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
from pathlib import Path

OWN = Path(__file__).resolve()
ORIGINAL = OWN.with_name("first_order_admission.py")
ORIGINAL_SHA = "e61ee415f0a8cd83f3ea4b0606064bceb128413eed4e66f1192955b1610ff66b"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
if hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() != ORIGINAL_SHA:
    raise ValueError("preserve frozen e61 admission")
SPEC = importlib.util.spec_from_file_location("eoere_genuine_e61_admission_reuse", ORIGINAL)
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
SCHEMA, SUCCESS = base.SCHEMA, base.SUCCESS
frame, core = base.frame, base.core
require = base.require
GUARD_AST = ast.dump(ast.parse('field.get("usable_conditional_actions") is True', mode="eval").body)
CORRECTED_FUNCTIONS = ("audit_first_order_state", "require_admitted_payload")
IDENTITY_KEYS = {"state_id", "case_id", "accessory_placement"}
PAIR_VALUES = {"force_on_first_xyz_n", "force_on_second_xyz_n", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"}


def source_pins(extra=None):
    pins = base.source_pins(extra)
    require(frame.sha(ORIGINAL) == ORIGINAL_SHA and frame.sha(OWN) == LOADED_SHA,
            "loaded corrected or reused admission bytes changed")
    path = str(OWN.relative_to(frame.ROOT))
    require(path not in pins or pins[path] == LOADED_SHA, "corrected admission source join conflict")
    pins[path] = LOADED_SHA
    return base.verify_pins(pins)


def verify_alias_source_metadata(field, snapshot, maps):
    """Exact own surface joins; force equality alone cannot qualify grouping."""
    screws = {row["axis_id"]: row for row in field["panel_screw_actions"]}
    source_screws = [row for row in snapshot.groups if row["kind"] == "panel_screw"]
    require(len(screws) == len(field["panel_screw_actions"]) == len(source_screws)
            and set(screws) == {row["id"] for row in source_screws}, "own Hillman recovery metadata census differs")
    for source in source_screws:
        saved = screws[source["id"]]
        metadata = {"axis_id": source["id"], "point_xyz_mm": source["point_xyz_mm"], "first": source["first"],
            "second": source["second"], "panel": source["first"], "receiver": source["second"],
            "moment_at_point_model_xyz_nmm": [0., 0., 0.], "physical_bolt_end_prying_moment_resolved": False,
            "physical_stiffness_bounded": False}
        values = {"force_on_first_xyz_n", "force_on_receiver_xyz_n", "local_force_n", "withdrawal_n", "lateral_n"}
        require(set(saved)-IDENTITY_KEYS == set(metadata)|values
                and {key: saved[key] for key in metadata} == core.serial(metadata), "own Hillman source/recovery labels differ")
    for table, sources in (("common_shaft_bearing_actions", [row for row in snapshot.groups if row["kind"] == "common_shaft_bearing"]),
                           ("shaft_end_capture_actions", [row for row in snapshot.contacts if row["kind"] == "shaft_end_capture"])):
        saved = {row["id"]: row for row in field[table]}
        require(len(saved) == len(field[table]) == len(sources) and set(saved) == {row["id"] for row in sources},
                "raw own bearing/capture metadata census differs")
        for row in sources:
            metadata = {key: row[key] for key in ("id", "axis_id", "kind", "first", "second", "point_xyz_mm")}
            if row["kind"] == "common_shaft_bearing":
                metadata.update(surface_index=row["surface_index"], surface_material=row["surface"]["kind"],
                    host=row["surface"]["host"], flange=row["surface"].get("flange"), surface_interval_mm=row["surface"]["interval_mm"],
                    quad_index=row["quad_index"], axis_station_mm=row["axis_station_mm"], weight_length_mm=row["weight_length_mm"],
                    foundation_spring_n_mm=row["kl"], own_bore_radial_gap_mm=row["clearance"])
                numeric = PAIR_VALUES
            else:
                metadata.update(host_support_point_xyz_mm=row["host_support_point_xyz_mm"], end=row["end"],
                    physical_pressure_or_prying_resolved=False, unilateral_axial_centre_capture_without_rotational_clamp=True)
                numeric = PAIR_VALUES|{"compression_n"}
            alias = saved[row["id"]]
            require(set(alias)-IDENTITY_KEYS == set(metadata)|numeric
                    and {key: alias[key] for key in metadata} == core.serial(metadata),
                    "raw own bearing/capture source labels differ, including zero-force rows")
    expected = {(row["axis_id"], i): (row, surface) for row in maps.shafts.values()
                for i, surface in enumerate(row["surfaces"])}
    seen = set()
    for table, kind in (("common_shaft_wood_bearing_actions", "wood"), ("common_shaft_steel_port_actions", "steel")):
        for alias in field[table]:
            key = (alias["axis_id"], alias["surface_index"])
            require(key in expected and key not in seen, "alias source surface duplicated or foreign")
            seen.add(key)
            _, surface = expected[key]
            expected_keys = {"axis_id", "host", "surface_index", "surface_interval_mm", "point_xyz_mm", "force_on_host_xyz_n",
                             "moment_on_host_at_point_xyz_nmm", "own_bearing_points", "own_end_captures",
                             "force_on_opposed_flange_or_other_host_not_inferred"}
            expected_keys |= {"member", "grain_axis_xyz"} if kind == "wood" else {
                "angle_id", "flange", "receiver", "force_on_steel_xyz_n", "moment_on_steel_at_point_xyz_nmm"}
            require(surface["kind"] == kind and alias["host"] == surface["host"]
                    and alias["surface_interval_mm"] == surface["interval_mm"]
                    and alias["force_on_opposed_flange_or_other_host_not_inferred"] is True
                    and set(alias)-IDENTITY_KEYS == expected_keys,
                    "alias table/kind/host/interval/own-only source join differs")
            if kind == "wood":
                require(alias["member"] == surface["host"] and alias["grain_axis_xyz"] == surface["grain_axis_xyz"],
                        "wood alias member/grain source join differs")
            else:
                require(alias["angle_id"] == surface["host"] and alias["flange"] == surface["flange"]
                        and alias["receiver"] == surface["receiver"], "steel alias angle/flange/receiver source join differs")
    require(seen == set(expected), "own surface metadata census has missing source paths")


def verify_fitting_and_alias_recovery(field, snapshot, maps, q):
    verify_alias_source_metadata(field, snapshot, maps)
    screws = {row["axis_id"]: row for row in field["panel_screw_actions"]}
    for source in snapshot.groups:
        if source["kind"] == "panel_screw":
            local, _, _ = frame.spring_constitutive(source["B"]@q, source["ka"], source["kl"], source["clearance"], source["tension_only"])
            saved = screws[source["id"]]
            base.close(saved["local_force_n"], local, 1e-8)
            base.close(saved["withdrawal_n"], local[0], 1e-8)
            base.close(saved["lateral_n"], base.np.linalg.norm(local[1:]), 1e-8)
            base.close(saved["force_on_receiver_xyz_n"], base.array(source["basis"]).T@local, 1e-8)
    return base.verify_fitting_and_alias_recovery(field, snapshot, maps, q)


def corrected_function(name, context):
    """Compile exactly one frozen function with exactly one absent-flag clause removed."""
    require(name in CORRECTED_FUNCTIONS and frame.sha(ORIGINAL) == ORIGINAL_SHA,
            "only the two authenticated compatibility corrections are allowed")
    tree = ast.parse(ORIGINAL.read_bytes(), filename=str(ORIGINAL))
    node = copy.deepcopy(next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == name))

    class RemoveAbsentFlag(ast.NodeTransformer):
        count = 0

        def visit_BoolOp(self, node):
            self.generic_visit(node)
            values = [value for value in node.values if ast.dump(value) != GUARD_AST]
            if len(values) != len(node.values):
                require(isinstance(node.op, ast.And) and len(values) >= 2, "exact AND guard correction required")
                self.count += len(node.values)-len(values)
                node.values = values
            return node

    transform = RemoveAbsentFlag()
    corrected = transform.visit(node)
    require(transform.count == 1, "frozen absent-flag guard location/count differs")
    module = ast.fix_missing_locations(ast.Module(body=[corrected], type_ignores=[]))
    exec(compile(module, str(OWN), "exec"), context)  # noqa: S102
    return context[name]


# A private function context binds the actual new contract path and source SHA.
# Original functions/mathematics and the genuine original module remain intact.
CONTEXT = {**vars(base), "OWN": OWN, "LOADED_SHA": LOADED_SHA, "source_pins": source_pins,
           "verify_fitting_and_alias_recovery": verify_fitting_and_alias_recovery}
CORRECTED_AUDIT = corrected_function("audit_first_order_state", CONTEXT)
CORRECTED_CONSUMER = corrected_function("require_admitted_payload", CONTEXT)


def audit_first_order_state(path_or_bytes):
    before = source_pins()
    receipt = CORRECTED_AUDIT(path_or_bytes)
    require(source_pins() == before, "corrected/reused admission sources changed during audit")
    # These describe the actual executed method, not a relabeling of an old PASS.
    receipt["admission_compatibility_correction"] = {
        "reused_source_path": str(ORIGINAL.relative_to(frame.ROOT)), "reused_source_sha256": ORIGINAL_SHA,
        "removed_absent_historical_flag_guards": list(CORRECTED_FUNCTIONS),
        "exact_own_alias_metadata_and_table_membership_verified": True,
        "physical_laws_or_algorithms_changed": False, "field_bytes_or_action_aliases_modified": False}
    return receipt


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    correction = receipt.get("admission_compatibility_correction", {})
    require(correction == {
        "reused_source_path": str(ORIGINAL.relative_to(frame.ROOT)), "reused_source_sha256": ORIGINAL_SHA,
        "removed_absent_historical_flag_guards": list(CORRECTED_FUNCTIONS),
        "exact_own_alias_metadata_and_table_membership_verified": True,
        "physical_laws_or_algorithms_changed": False, "field_bytes_or_action_aliases_modified": False},
        "actual corrected admission provenance required")
    return CORRECTED_CONSUMER(field_bytes, receipt, admission_sha256=admission_sha256)

"""Admit the narrow linear timber-face extension of frozen common shafts.

Only saved JSON, source hashes and linear point kinematics are inspected.
The existing common-shaft audit owns unchanged loads, centroid floor support
and all132 body balances. No K/CAD/response or capacity is evaluated here.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft_export_audit as common_export
from scripts import thin_bolted_panel_load_diagnostics as panel_sources
from scripts import thin_bolted_timber_common_shaft_checks as spans
from scripts import thin_bolted_timber_contact_admission as proof_method

common = common_export.frozen
support, arithmetic = common.support, common.arithmetic
ROOT, PACKET = common.ROOT, common.PACKET
OWN = str(Path(__file__).resolve().relative_to(ROOT))
LOADED_PRODUCER_SHA256 = support.digest(Path(__file__))
SCHEMA = "thin_bolted_independent_linear_timber_admission/v1"
SUCCESS = "independent_linear_timber_face_source_map_law_and_equilibrium_checks_pass"
MAP_SCHEMA = "thin_bolted_linear_timber_coordinates/v1"
BASIS = "source-bound-linear-finished-paired-wood-compression-v1"
METHOD = "scripts/thin_bolted_linear_timber_faces.py"
METHOD_SHA256 = "6283d85ec2bfacd6d72f0713c662e273201935e09445a6455b86a841de587208"
DRIVER = "scripts/run_thin_bolted_linear_timber_frame.py"
DRIVER_SHA256 = "4d1e1d86c70186f4cd2a1dfcc1da7714cbd761660c54de6a11f26a0738f37669"
METHOD_RECEIPT = PACKET/"linear-timber-face-method-v4.json"
METHOD_RECEIPT_SHA256 = "fd1cba29d11f2a69e0248a18fa6c7cbf97c23abd5177524c60a30dc8f6bdb11c"
IDENTITIES = ("state_id", "case_id", "accessory_placement")
PINS = {
    "scripts/thin_bolted_common_shaft_export_audit.py": "26feb3bb369490729c6f8e48365d816cbda458b2fdeea89a97b8286842d1be58",
    "scripts/thin_bolted_common_shaft_audit.py": common_export.FROZEN_AUDIT_SHA,
    "scripts/thin_bolted_finished_support_audit.py": common.SUPPORT_AUDIT_SHA,
    "scripts/thin_bolted_equilibrium_audit.py": support.ARITHMETIC_SHA,
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
    "scripts/thin_bolted_timber_demand_checks.py": spans.PREVIOUS_SHA,
    "scripts/thin_bolted_timber_resistance.py": "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    "scripts/thin_bolted_timber_contact_admission.py": "75011f4cfa042a46d8e45eb5716ae01df2edff3418b1439553afb04b14b14632",
    "scripts/thin_bolted_finite_state_audit.py": proof_method.ORIGINAL_GATE_SHA256,
    "scripts/thin_bolted_panel_coupled.py": panel_sources.COUPLED_SHA,
    "scripts/thin_bolted_panel_load_diagnostics.py": "ff5e0e7b3944e64379181a6b3a1c442b921c197b87d25da3bd20a2d69ec63ebd",
    str(spans.SPAN_SOURCE.relative_to(ROOT)): spans.SPAN_SOURCE_SHA,
    str(panel_sources.OPERATORS.relative_to(ROOT)): panel_sources.OPERATORS_SHA,
    str(panel_sources.coupled.DATUMS.relative_to(ROOT)): panel_sources.coupled.DATUMS_SHA,
    str(METHOD_RECEIPT.relative_to(ROOT)): METHOD_RECEIPT_SHA256,
}
require = proof_method.original.require
canonical_sha = proof_method.original.canonical_sha
merge_pins = proof_method.merge_pins


def verify_pins(pins):
    for path, expected in pins.items():
        require(isinstance(expected, str) and len(expected) == 64 and support.digest(ROOT/path) == expected,
                "linear timber admission source changed: "+path)


def source_pins():
    pins = merge_pins(PINS, {OWN: LOADED_PRODUCER_SHA256})
    verify_pins(pins)
    return pins


def expected_timber_map(cache, beam_size_mm, ndof, geometry):
    """Recreate only frozen beam coordinates, never a stiffness matrix."""
    size = support.finite_scalar(beam_size_mm)
    require(size > 0. and isinstance(ndof, int) and not isinstance(ndof, bool) and ndof > 0,
            "positive beam size and complete integer coordinate dimension required")
    order = [row["member"] for row in cache["raw_parts"]]
    require(len(order) == len(set(order)) == 20 and set(order) == set(geometry), "all20 frozen timber members/order required")
    rows, offset = [], 0
    for name in order:
        start = arithmetic.vector(geometry[name]["start_xyz_mm"])
        end = arithmetic.vector(geometry[name]["end_xyz_mm"])
        axis = arithmetic.vector(geometry[name]["basis_grain_u_v_xyz"][0])
        length = float(np.linalg.norm(end-start))
        require(length > 0. and abs(np.linalg.norm(axis)-1.) < 1e-8
                and np.linalg.norm(end-start-axis*length) < 1e-5, "frozen timber centerline/grain differs")
        stations = np.linspace(0., length, max(1, int(np.ceil(length/size)))+1)
        index = np.arange(offset, offset+6*len(stations)).reshape(-1, 6)
        offset += index.size
        rows.append({"member": name, "node_dof_indices": index.tolist(), "reference_start_xyz_mm": start.tolist(),
            "reference_axis_xyz": axis.tolist(), "reference_stations_mm": stations.tolist(),
            "node_reference_centers_xyz_mm": (start+stations[:, None]*axis).tolist(),
            "storage_basis_columns_xyz": np.eye(3).tolist()})
    require(offset <= ndof, "complete coordinates omit a timber node")
    return {"schema": MAP_SCHEMA, "ndof": ndof, "rotation_scale": 1000., "members": rows,
            "action_datums": "reference world points; first-order rigid arms"}


def verify_timber_map(field, cache, geometry):
    mapping = field["linear_timber_coordinate_map"]
    require(mapping["ndof"] == field["counts"]["dofs"], "linear map/full field coordinate dimensions differ")
    expected = expected_timber_map(cache, field["parameters"]["beam_size_mm"], mapping["ndof"], geometry)
    # The array comparison admits only serialized floating-point rounding,
    # while order, indices and the dimension remain exact.
    require(mapping.get("schema") == MAP_SCHEMA and mapping.get("rotation_scale") == 1000.
            and mapping.get("action_datums") == expected["action_datums"]
            and len(mapping["members"]) == 20, "complete linear timber coordinate schema required")
    for row, source in zip(mapping["members"], expected["members"], strict=True):
        require(row["member"] == source["member"] and row["node_dof_indices"] == source["node_dof_indices"]
                and row["storage_basis_columns_xyz"] == source["storage_basis_columns_xyz"],
                "linear timber member order/node indices/world storage basis differ")
        for key in ("reference_start_xyz_mm", "reference_axis_xyz", "reference_stations_mm", "node_reference_centers_xyz_mm"):
            proof_method.original.close(row[key], source[key], 1e-8, "linear timber reference coordinate differs: "+key)
    q = proof_method.original.array(field["response"]["q"], (mapping["ndof"],))
    return expected, q


def point_displacement(mapping, member, point, q):
    """Original world-storage linear interpolation and exact reference arm."""
    row = next(r for r in mapping["members"] if r["member"] == member)
    start, axis, point = [arithmetic.vector(v) for v in (row["reference_start_xyz_mm"], row["reference_axis_xyz"], point)]
    stations = np.asarray(row["reference_stations_mm"])
    station = float((point-start) @ axis)
    segment = int(np.clip(np.searchsorted(stations, station)-1, 0, len(stations)-2))
    a, b = stations[segment:segment+2]
    t = float(np.clip((station-a)/(b-a), 0., 1.))
    center = start+axis*(a+t*(b-a))
    index = np.asarray(row["node_dof_indices"])
    nodal = (1.-t)*q[index[segment]]+t*q[index[segment+1]]
    return nodal[:3]+np.cross(nodal[3:]/1000., point-center)


def panel_contact_sources():
    """Read only saved contact datums, owners and areas; never load K."""
    datums = json.loads(panel_sources.coupled.DATUMS.read_bytes())
    result = {}
    with np.load(panel_sources.OPERATORS, allow_pickle=False) as saved:
        for panel, datum in datums.items():
            points, area = saved[panel+"/contact_points_xyz_mm"], saved[panel+"/contact_area"]
            owners = datum["contact_receivers"]
            require(len(points) == len(area) == len(owners), "saved panel contact source census differs")
            normal = np.asarray(datum["local_axes_columns_xyz"])[:, 2]
            for i, (point, weight, owner) in enumerate(zip(points, area, owners, strict=True)):
                result[panel+f"/compression-{i}"] = {"first": panel, "second": owner,
                    "point_xyz_mm": point.tolist(), "direction_xyz": normal.tolist(), "area_mm2": float(weight)}
    require(len(result) == 530, "initial panel contact70 source requires530 cells")
    return result


def verify_action_census(field, panels):
    """Reject extra paths, omissions and zero-row loss before body closure."""
    require(field["parameters"]["panel_intervals"] == 8
            and field["parameters"]["foundation_port_cell_mm"] == 70., "source-bound interval8/contact70 required")
    contacts = proof_method.original.unique(field["contact_actions"])
    require(len(contacts) == 1090 and Counter(r["kind"] for r in contacts.values())
            == {"flange_contact": 288, "panel_contact": 530, "timber_face_contact": 272},
            "complete1090 known contact paths required; foreign/omitted contacts rejected")
    rows = {k: r for k, r in contacts.items() if r["kind"] == "panel_contact"}
    require(set(rows) == set(panels), "complete530 source-bound panel contact IDs required")
    for identity, source in panels.items():
        row = rows[identity]
        require((row["first"], row["second"]) == (source["first"], source["second"]), "panel contact owner differs")
        proof_method.original.close(row["point_xyz_mm"], source["point_xyz_mm"], 1e-7, "panel contact reference datum differs")
        compression = support.finite_scalar(row["compression_n"])
        require(compression >= 0., "panel contact compression must be nonnegative")
        proof_method.original.close(row["force_on_first_xyz_n"], compression*np.asarray(source["direction_xyz"]),
                                    1e-6, "panel contact force differs from source normal")
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"):
            if key in row:
                proof_method.original.close(row[key], [0., 0., 0.], 1e-8, "panel point law supplies no free couple")
    tables = (("panel_screw_actions", 66, lambda r: r["axis_id"]),
              ("common_shaft_bearing_actions", 308, lambda r: r["id"]),
              ("shaft_end_capture_actions", 140, lambda r: r["id"]),
              ("common_shaft_wood_bearing_actions", 82, lambda r: (r["axis_id"], r["surface_index"])),
              ("common_shaft_steel_port_actions", 72, lambda r: (r["axis_id"], r["angle_id"], r["flange"])),
              ("common_shaft_section_cut_actions", 70, lambda r: r["axis_id"]))
    for name, count, key in tables:
        require(len(field[name]) == len({key(r) for r in field[name]}) == count, "complete unique action/aggregate census differs: "+name)
        proof_method.original.identities(field, [labeled for row in field[name] for labeled in (row, *row.get("cuts", []))])
    floor = proof_method.original.unique(field["floor_actions"])
    require(sum(r["kind"] == "floor_normal" for r in floor.values()) == 32, "all32 floor normal rows required")
    require(len(field["body_identities"]) == len(set(field["body_identities"])) == 132
            and sum(name.startswith("shaft/") for name in field["body_identities"]) == 70, "all132 bodies/70 shaft bodies required")
    expected_counts = {"normal_contacts": 1262, "timber_members": 20, "finite_fittings": 36, "flexible_panels": 6,
        "physical_bolt_axes": 70, "physical_shaft_bodies": 70, "structural_bodies": 132, "panel_screw_axes": 66,
        "finished_wood_bearing_spans": 82, "steel_bore_spans": 72, "radial_bearing_quadrature_ports": 308,
        "own_axial_end_captures": 140, "independent_lumped_frame_bolt_ports": 0,
        "paired_timber_interfaces": 6, "paired_timber_compression_cells": 272}
    require(all(field["counts"].get(key) == value for key, value in expected_counts.items()), "producer census differs from complete actions")
    return {"normal_contact_count": 1262, "contact_action_count": 1090, "panel_contact_count": 530,
            "unchanged_panel_contact_q_law_independently_replayed": False}


def verify_face_actions(field, proof, mapping, q):
    params = field["parameters"]
    require(field.get("linear_timber_face_method") == BASIS and params.get("linear_timber_face_contact_basis") == BASIS,
            "distinct source-bound linear face method required")
    bedding = support.finite_scalar(params["linear_timber_face_contact_bedding_n_mm3"])
    scenario = params["linear_timber_face_contact_scenario_id"]
    require(bedding > 0. and isinstance(scenario, str) and scenario.strip()
            and params["linear_timber_face_contact_geometry_sha256"] == proof_method.PROOF_SHA256
            and params["linear_timber_face_contact_cell_mm"] == proof["method"]["cell_size_mm"],
            "linear face proof/bedding/scenario/grid differs")
    expected = proof_method.expected_contact_descriptors(proof, bedding, scenario)
    rows = [r for r in field["contact_actions"] if r["kind"] == "timber_face_contact"]
    indexed = proof_method.original.unique(rows)
    alias = proof_method.original.unique(field["timber_face_contact_actions"])
    require(len(expected) == len(indexed) == 272 and set(indexed) == set(expected)
            and canonical_sha(indexed) == canonical_sha(alias), "all272 exact face rows/aliases, including zero, required")
    proof_method.original.identities(field, rows)
    for identity, descriptor in expected.items():
        row = indexed[identity]
        point, normal = descriptor["reference_first_point_xyz_mm"], arithmetic.vector(descriptor["reference_director_xyz"])
        require((row["first"], row["second"]) == (descriptor["first"], descriptor["second"])
                and canonical_sha(row["source_descriptor"]) == canonical_sha(descriptor["source_descriptor"])
                and row.get("action_wrench_uses_reference_point_first_order") is True
                and row.get("physical_pressure_or_current_overlap_resolved") is False,
                "linear face host/source aliases differ")
        closure = -float(normal @ (point_displacement(mapping, row["first"], point, q)
                                  -point_displacement(mapping, row["second"], point, q)))
        stiffness = descriptor["axial_stiffness_n_mm"]
        compression = stiffness*max(closure, 0.)
        force = compression*normal
        for key, target in (("point_xyz_mm", point), ("direction_xyz", normal), ("force_on_first_xyz_n", force),
                            ("force_on_second_xyz_n", -force)):
            proof_method.original.close(row[key], target, 1e-6 if "force" in key else 1e-8,
                                        "linear face datum/normal/force dual differs: "+key)
        require(abs(support.finite_scalar(row["relative_closure_mm"])-closure) <= 1e-8
                and abs(support.finite_scalar(row["compression_n"])-compression) <= 1e-6
                and support.finite_scalar(row["penalty_stiffness_n_mm"]) == stiffness
                and support.finite_scalar(row["cell_area_mm2"]) == descriptor["source_descriptor"]["cell_area_mm2"],
                "linear face closure/area/stiffness/compression differs from original q law")
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"):
            proof_method.original.close(row[key], [0., 0., 0.], 1e-8, "linear face point law supplies no free couple")
        if "host_support_point_xyz_mm" in row:
            proof_method.original.close(row["host_support_point_xyz_mm"], point, 1e-8, "linear face paired datum differs")
    return {"face_cell_count": 272, "retained_pair_count": 6, "all_source_cells_and_zero_rows_retained": True,
            "original_linear_q_contact_laws_replayed": True, "current_overlap_pressure_or_capacity_established": False}


def audit_linear_timber_state(path_or_dict):
    """Admit one source-bound face extension and reuse unchanged132-body checks."""
    pins = source_pins()
    require("UNISSUED" not in (METHOD_SHA256, DRIVER_SHA256), "linear face producer/driver must be frozen before admission")
    path = None if isinstance(path_or_dict, (bytes, dict)) else Path(path_or_dict)
    payload = path.read_bytes() if path else path_or_dict if isinstance(path_or_dict, bytes) else None
    field = json.loads(payload) if payload is not None else path_or_dict
    field_before = canonical_sha(field)
    require(field.get("schema") == "thin_bolted_common_shaft_frame/v1" and field.get("release")
            and not any(field["release"].values()), "unreleased common-shaft field required")
    identity = {key: field[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field["state_id"] == "thin-v4-"+canonical_sha(identity)[:24], "linear state identity differs")
    require(field["source_sha256"].get(METHOD) == METHOD_SHA256
            and field["parameters"].get("linear_timber_face_contact_producer_sha256") == METHOD_SHA256
            and field["source_sha256"].get(DRIVER) == DRIVER_SHA256
            and field["parameters"].get("linear_timber_frame_driver_sha256") == DRIVER_SHA256,
            "linear field does not bind frozen face producer/driver")
    command = field.get("common_shaft_execution", {}).get("command")
    require(isinstance(command, list) and len(command) >= 3 and all(isinstance(part, str) for part in command)
            and command[1:3] == ["-m", "scripts.run_thin_bolted_linear_timber_frame"],
            "new linear timber execution module required")
    _, cache, _, layout, _, _, base_pins = common.read_sources()
    proof_bytes = proof_method.PROOF.read_bytes()
    require(hashlib.sha256(proof_bytes).hexdigest() == proof_method.PROOF_SHA256, "finished paired-face proof changed")
    proof = json.loads(proof_bytes)
    pins = merge_pins(pins, base_pins, proof["source_sha256"],
                     {str(proof_method.PROOF.relative_to(ROOT)): proof_method.PROOF_SHA256,
                      METHOD: METHOD_SHA256, DRIVER: DRIVER_SHA256}, field["source_sha256"])
    verify_pins(pins)
    require(all(field["source_sha256"].get(path) == PINS[path] for path in
                (str(panel_sources.OPERATORS.relative_to(ROOT)), str(panel_sources.coupled.DATUMS.relative_to(ROOT)))),
            "linear state omits authenticated panel contact discretization sources")
    require(all(field["source_sha256"].get(k) == v for k, v in proof["source_sha256"].items())
            and field["source_sha256"].get(str(proof_method.PROOF.relative_to(ROOT))) == proof_method.PROOF_SHA256,
            "linear state omits authenticated face geometry sources")
    inventory = proof_method.verify_patch_inventory(proof, cache, layout)
    mapping, q = verify_timber_map(field, cache, spans.read_member_span_geometry())
    faces = verify_face_actions(field, proof, mapping, q)
    census = verify_action_census(field, panel_contact_sources())
    require(not field.get("attachment_actions") and not field.get("retained_bolt_actions"), "old bolt proxies cannot survive")
    # The full frozen audit includes every contact_actions row in body closure.
    original = common_export.audit_common_shaft_state(field)
    require(original[common_export.ACCEPTANCE_KEY] is True, "unchanged common132-body/support/load audit failed")
    pins = merge_pins(pins, original["source_sha256"])
    verify_pins(pins)
    require(canonical_sha(field) == field_before, "linear parsed field changed during admission")
    if path:
        require(support.digest(path) == hashlib.sha256(payload).hexdigest(), "linear field changed during admission")
    return {"schema": SCHEMA, SUCCESS: True, **{k: field[k] for k in IDENTITIES},
        "field_sha256": hashlib.sha256(payload).hexdigest() if payload is not None else None,
        "field_canonical_sha256": canonical_sha(field), "source_sha256": pins,
        "linear_timber_map_checks_pass": True, "linear_timber_face_checks": faces, "timber_contact_geometry": inventory,
        "complete_action_census": census,
        "independent_common_shaft_audit": original, "native_CAD_K_or_response_execution": False,
        "small_motion_applicability_physical_bounds_complete_capacity_or_release_established": False,
        "release": {k: False for k in field["release"]}}

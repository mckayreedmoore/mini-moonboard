"""Independent saved-operator admission of one conditional eoere A12 field.

No assembly, solve or CAD reader is called. The genuine original constitutive
kernel replays captured numeric operators, with separately checked owned point
maps, load work, force recovery and physical-body closure. Distributed panel
RHS values are captured/source-authenticated, not independently regenerated.
This receipt establishes numerical consistency, never physical demand bounds,
resistance, finite contact applicability or a release.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.sparse import csr_matrix, hstack

from scripts import thin_bolted_panel_mechanics as panel

OWN = Path(__file__).resolve()
BUNDLE = OWN.with_name("operator_bundle.py")
DRIVER = OWN.with_name("run_first_order_v2.py")
BUNDLE_SHA = "534356acc914bd9fb81f24e67311fe40123d70754224a6466fe0da1d7f1426a9"
DRIVER_SHA = "750dd24733c101c98c06d135e9c5c88a5b33a610d09e79736ee4500171685f32"
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
if hashlib.sha256(BUNDLE.read_bytes()).hexdigest() != BUNDLE_SHA:
    raise ValueError("preserve reviewed operator exporter")
SPEC = importlib.util.spec_from_file_location("eoere_independent_saved_operators", BUNDLE)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)
core, frame, factory = bundle.core, bundle.frame, bundle.core.factory
require, canonical = factory.require, factory.canonical
SCHEMA = "eoere_first_order_independent_field_admission/v1"
SUCCESS = "independent_eoere_original_law_gradient_work_and_equilibrium_checks_pass"
FIELD_SCHEMA = "eoere_first_order_common_shaft_four_port_candidate/v2"
TABLES = ("panel_screw_actions", "contact_actions", "floor_actions", "common_shaft_bearing_actions",
          "shaft_end_capture_actions", "common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions",
          "four_port_fitting_actions", "common_shaft_section_cut_actions", "member_section_action_samples",
          "panel_generalized_coefficients")


def array(value, shape=None):
    result = np.asarray(value, dtype=float)
    require(np.isfinite(result).all() and (shape is None or result.shape == shape), "finite array shape differs")
    return result


def close(actual, expected, tolerance=1e-8, message="saved value differs from independent replay"):
    a, b = array(actual), array(expected)
    require(a.shape == b.shape and np.max(abs(a-b), initial=0.) <= tolerance, message)


def verify_pins(pins):
    require(isinstance(pins, dict) and pins, "nonempty immutable source closure required")
    for path, digest in pins.items():
        require(isinstance(path, str) and isinstance(digest, str) and len(digest) == 64
                and frame.sha(frame.ROOT/path) == digest, "source/artifact bytes changed: "+str(path))
    return dict(pins)


def source_pins(extra=None):
    pins = bundle.source_pins(extra)
    for path, digest in ((BUNDLE, BUNDLE_SHA), (DRIVER, DRIVER_SHA), (OWN, LOADED_SHA)):
        require(frame.sha(path) == digest, "loaded admission/export/driver bytes changed")
        name = str(path.relative_to(frame.ROOT))
        require(name not in pins or pins[name] == digest, "admission source join conflict")
        pins[name] = digest
    return verify_pins(pins)


def identities(field):
    expected = {key: field[key] for key in ("state_id", "case_id", "accessory_placement")}

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in expected:
                    require(item == expected[key], "foreign or null current action identity")
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(field)
    return expected


def parse_command(command):
    require(isinstance(command, list) and all(isinstance(v, str) for v in command)
            and len(command) >= 2 and Path(command[1]).resolve() == DRIVER, "true new outer Python driver required")
    parser = argparse.ArgumentParser(exit_on_error=False, add_help=False)
    for key in ("inputs", "inputs-sha256", "input-review", "input-review-sha256", "out"):
        parser.add_argument("--"+key, required=True)
    parser.add_argument("--mask-budget", type=int, default=64)
    parser.add_argument("--max-iterations", type=int, default=300)
    parser.add_argument("--wall-seconds", type=float, default=1770.)
    parser.add_argument("--run", action="store_true")
    try:
        args, remainder = parser.parse_known_args(command[2:])
    except (argparse.ArgumentError, SystemExit) as error:
        raise ValueError("actual command is invalid") from error
    require(not remainder and args.run and 1 <= args.mask_budget <= 256 and 1 <= args.max_iterations <= 300
            and 0. < args.wall_seconds <= 1800., "one bounded original fresh search command required")
    return args


def verify_execution(field, snapshot):
    outer, inner = field["operator_bundle_execution"], field["execution"]
    command = outer["command"]
    args = parse_command(command)
    require(outer["loaded_driver_path"] == bundle.artifact_path(DRIVER) and outer["loaded_driver_sha256"] == DRIVER_SHA
            and outer["loaded_operator_export_path"] == bundle.artifact_path(BUNDLE)
            and outer["loaded_operator_export_sha256"] == BUNDLE_SHA
            and outer["frozen_inner_driver_path"] == bundle.artifact_path(bundle.CORE)
            and outer["frozen_inner_driver_sha256"] == bundle.CORE_SHA
            and outer["nested_first_order_execution_is_reused_internal_call"] is True
            and outer["one_preparation_one_fresh_search"] is True and outer["historical_q_or_forces_used"] is False,
            "outer loaded source/reused-call contract differs")
    require(inner["command"] == command == snapshot.manifest["execution_command"]
            and inner["role"] == "reused_frozen_first_order_core_execution"
            and inner["loaded_driver_sha256"] == bundle.CORE_SHA and inner["loaded_factory_sha256"] == factory.LOADED_SHA
            and inner["one_preparation"] is True and inner["one_case"] is True
            and inner["automatic_retry"] is False and inner["historical_q_used"] is False
            and inner["wall_seconds"] == args.wall_seconds, "internal execution must remain truthful")
    data, input_pins = factory.read_inputs(frame.ROOT/args.inputs, args.inputs_sha256)
    review = {"path": bundle.artifact_path(frame.ROOT/args.input_review), "sha256": args.input_review_sha256}
    pins, checked = factory.authenticate_source_review(review, data, source_pins(field["source_sha256"]))
    require(field["source_input_review"] == checked and canonical(field["source_inputs"]) == canonical(data),
            "field must use the exact reviewed immutable inputs")
    require(all(field["source_sha256"].get(path) == digest for path, digest in {**input_pins, **pins}.items()
                if path != str(OWN.relative_to(frame.ROOT))), "producer input/source closure incomplete")
    expected_paths = {"arrays": Path(args.out).with_suffix(Path(args.out).suffix+".operators.npz"),
                      "manifest": Path(args.out).with_suffix(Path(args.out).suffix+".operators.json")}
    require(all(field["operator_bundle"][key]["path"] == bundle.artifact_path(frame.ROOT/path)
                for key, path in expected_paths.items()), "command output and operator artifact paths differ")
    require(snapshot.case["case_id"] == field["case_id"] == "a12-rear"
            and snapshot.case["accessory_placement"] == field["accessory_placement"] == "retained-original-top-hold"
            and snapshot.case["loads"] == data["case"]["loads"] == field["body_applied_loads"], "one original A12 load case required")
    expected_state = "eoere-a12-"+canonical({"source_sha256": field["source_sha256"], "inputs": data,
        "case": snapshot.case, "counts": field["counts"], "mask_budget": args.mask_budget,
        "max_iterations": args.max_iterations})[:24]
    require(field["state_id"] == expected_state, "fresh state identity does not bind new sources, inputs and search")
    return data, args


class OwnedMaps:
    """Rebuild only geometric point/rigid maps, never material K or an assembly."""

    def __init__(self, snapshot, data):
        self.n = snapshot.assembly.ndof
        chart = snapshot.coordinate_map
        require(chart["schema"] == "eoere_first_order_owned_coordinate_map/v1"
                and chart["final_ndof"] == self.n and chart["rotation_scale"] == 1000.
                and not chart["unused_legacy_two_port_fitting_indices"]
                and chart["shaft_axial_spin_is_free_numerical_gauge_without_torque_reaction"] is True,
                "owned coordinate chart contract differs")
        self.members, self.shafts, self.fittings, self.panels = {}, {}, {}, {}
        used = []
        source_wood = {row["name"]: row for row in data["timber_rows"]}
        source_shafts = {row["body"]: row for row in data["shafts"]}
        require(set(chart["timber"]) == set(source_wood) and set(chart["shafts"]) == set(source_shafts)
                and set(chart["panels"]) == set(data["panel_ids"]), "owned chart owner census differs")
        for name, row in chart["timber"].items():
            source = source_wood[name]
            require(row["source"] == source, "timber map source owner differs")
            length = float(np.linalg.norm(array(source["end"])-source["start"]))
            count = max(1, int(np.ceil(length/data["scenario"]["beam_size_mm"])))
            close(row["stations"], np.linspace(0., length, count+1), 1e-10)
            close(row["start"], source["start"], 0.)
            close(row["axis"], source["axis"], 0.)
            index = self.index(row["index"], (count+1, 6))
            used.extend(index.ravel())
            self.members[name] = {**row, "index": index, "start": array(row["start"]),
                                  "axis": array(row["axis"]), "stations": array(row["stations"])}
        for name, row in chart["panels"].items():
            basis = panel.SheetBasis(row["width_mm"], row["height_mm"], row["intervals"])
            require(basis.order == row["basis_order_per_direction"] and basis.knots.tolist() == row["knots_normalized"],
                    "genuine unchanged panel spline basis differs")
            geometry = {key: array(value) if key in {"origin", "axes", "inward"} else value
                        for key, value in row["geometry"].items()}
            index = self.index(row["indices"], (3*basis.size,))
            used.extend(index)
            self.panels[name] = {"basis": basis, "geometry": geometry, "thickness": row["thickness_mm"], "indices": index}
        poses = {row["id"]: row for row in data["fitting_poses"]}
        require(set(chart["four_port_fittings"]) == set(poses)
                and chart["four_port_fittings"] == {row["body"]: row for row in snapshot.manifest["fitting_descriptors"]},
                "owned fitting descriptor census differs")
        for name, row in chart["four_port_fittings"].items():
            pose = poses[name]
            model, _ = factory.guarded.model_from_reference_pose(pose["origin_xyz_mm"], pose["u_xyz"], pose["v_xyz"], pose["w_xyz"])
            index = self.index(row["dof_indices"], (24,))
            require(row["ndof"] == chart["fitting_embedding_ndof_by_owner"][name] <= self.n, "pre-shaft fitting embedding differs")
            element = factory.guarded.GuardedFourPortAssemblyElement(model, name, index, row["ndof"])
            require(element.descriptor() == row, "fitting source/operator/immutable snapshot cannot be reproduced")
            self.fittings[name] = element
            used.extend(index)
        for name, row in chart["shafts"].items():
            source = source_shafts[name]
            require(all(row[key] == source[key] for key in ("axis_id", "point", "basis", "diameter_mm", "surfaces", "ends")),
                    "shaft map own source differs")
            stations = array(row["stations"])
            index = self.index(row["index"], (len(stations), 6), gauge=True)
            require(np.all(np.diff(stations) > 0.) and index[0, 3] == -1 and np.sum(index == -1) == 1
                    and np.array_equal(index[index >= 0], np.arange(row["offset"], row["offset"]+row["ndof"])),
                    "shaft stations and one unloaded axial-spin gauge differ")
            used.extend(index[index >= 0])
            self.shafts[name] = {**row, "index": index, "stations": stations, "point": array(row["point"]), "basis": array(row["basis"])}
        require(len(used) == self.n and set(used) == set(range(self.n)), "physical coordinate ownership duplicated or dropped")

    def index(self, value, shape, *, gauge=False):
        result = np.asarray(value)
        require(result.shape == shape and result.dtype.kind in "iu"
                and np.all((result >= (-1 if gauge else 0)) & (result < self.n)), "owned global DOF index differs")
        return result

    def embed(self, block, index):
        block, index = np.asarray(block), np.asarray(index)
        i, j = np.nonzero(abs(block) > 1e-14)
        return csr_matrix((block[i, j], (i, index[j])), shape=(block.shape[0], self.n))

    def port(self, body, point, flange=None):
        point = array(point, (3,))
        if body == "floor":
            return csr_matrix((3, self.n))
        if body in self.fittings:
            el = self.fittings[body]
            result = el.centroid_load_port(point, declared_route=factory.guarded.ROUTE) if flange is None else el.point_port(flange, point)
            return hstack([result, csr_matrix((3, self.n-result.shape[1]))], format="csr")
        if body in self.panels:
            row = self.panels[body]
            return self.embed(panel.point_matrix(row, point), row["indices"])
        require(body in self.members or body in self.shafts, "foreign point-port owner")
        shaft = body in self.shafts
        row = self.shafts[body] if shaft else self.members[body]
        start, axis = (row["point"], row["basis"][0]) if shaft else (row["start"], row["axis"])
        station = float((point-start)@axis)
        i = int(np.clip(np.searchsorted(row["stations"], station)-1, 0, len(row["stations"])-2))
        a, b = row["stations"][i:i+2]
        t = float(np.clip((station-a)/(b-a), 0., 1.))
        block = frame.point_matrix(point, start+axis*(a+t*(b-a)))
        if shaft:
            basis = row["basis"]
            block = block @ np.block([[basis.T, np.zeros((3, 3))], [np.zeros((3, 3)), basis.T]])
        block, index = np.hstack(((1-t)*block, t*block)), row["index"][i:i+2].ravel()
        return self.embed(block[:, index >= 0], index[index >= 0])

    def rigid_modes(self):
        result = np.zeros((self.n, 6))
        for row in self.members.values():
            for index, s in zip(row["index"], row["stations"], strict=True):
                result[index[:3]] = frame.point_matrix(row["start"]+s*row["axis"], frame.REFERENCE, 1.)
                result[index[3:], 3:] = np.eye(3)*1000.
        for row in self.shafts.values():
            for index, s in zip(row["index"], row["stations"], strict=True):
                local = np.vstack((row["basis"]@frame.point_matrix(row["point"]+s*row["basis"][0], frame.REFERENCE, 1.),
                                   np.hstack((np.zeros((3, 3)), row["basis"]*1000.))))
                local[3] = 0.
                result[index[index >= 0]] = local[index >= 0]
        for element in self.fittings.values():
            result[element.indices] = element.rigid_modes(frame.REFERENCE)
        for row in self.panels.values():
            basis, geometry = row["basis"], row["geometry"]
            greville = np.array([np.mean(basis.knots[i+1:i+4]) for i in range(basis.order)])
            x, y = np.meshgrid(greville*basis.width, greville*basis.height, indexing="ij")
            points = geometry["origin"]+np.c_[x.ravel(), y.ravel()]@geometry["axes"][:, :2].T
            fields = [((np.broadcast_to(np.eye(3)[i], points.shape) if i < 3 else
                        np.cross(np.eye(3)[i-3], points-frame.REFERENCE))@geometry["axes"]).T.ravel() for i in range(6)]
            result[row["indices"]] = np.array(fields).T
        return result


def verify_ports(snapshot, maps, data):
    """Check source-owned row identity and work-dual geometry of every port."""
    direct = {row["id"]: row for row in data["direct_contacts"]}
    hillman = {row["id"]: row for row in data["hillman_rows"]}
    source_shafts = {row["body"]: row for row in data["shafts"]}
    floor = data["floor_footprints"]
    expected_ids = set(direct)|set(hillman)
    for host in floor:
        expected_ids.update(host+f"/floor-{i}" for i in range(4))
        expected_ids.update(host+f"/no-slip-{i}" for i in (0, 1))
    for source in source_shafts.values():
        expected_ids.update(source["axis_id"]+f"/bearing-{i}-{j}" for i in range(len(source["surfaces"])) for j in (0, 1))
        expected_ids.update(source["axis_id"]+"/"+end["end"]+"-capture" for end in source["ends"])
    all_rows = [*snapshot.groups, *snapshot.contacts, *snapshot.tangents]
    require(len(all_rows) == len(expected_ids) and {row["id"] for row in all_rows} == expected_ids,
            "complete interaction union has dropped or duplicate source paths")
    for row in all_rows:
        kind, point = row["kind"], row["point_xyz_mm"]
        if kind in {"panel_screw", "common_shaft_bearing"}:
            require(kind == "panel_screw" and row["id"] in hillman or kind == "common_shaft_bearing" and row["first"] in source_shafts,
                    "foreign vector spring source")
            if kind == "panel_screw":
                require(all(row[key] == value for key, value in hillman[row["id"]].items()), "Hillman source descriptor differs")
            else:
                source = source_shafts[row["first"]]
                surface = source["surfaces"][row["surface_index"]]
                require(row["surface"] == surface and row["second"] == surface["host"] and row["basis"] == source["basis"],
                        "bearing source ownership differs")
                a, b = surface["interval_mm"]
                s = .5*(a+b)+.5*(b-a)*(-1./np.sqrt(3.) if row["quad_index"] == 0 else 1./np.sqrt(3.))
                close(point, array(source["point"])+array(source["basis"])[0]*s, 1e-10)
                parameters = data["scenario"]["common_shaft_parameters"]
                density = parameters.get("wood_foundation_n_mm2", 1000./38.1) if surface["kind"] == "wood" else parameters.get("plate_foundation_n_mm2", 10000./5.55625)
                close([row["ka"], row["kl"], row["clearance"]], [0., density*.5*(b-a), .5*(surface["bore_diameter_mm"]-source["diameter_mm"])], 1e-10)
                require(row["tension_only"] is False, "bearing spring must retain bilateral axial-off radial law")
            flange = row.get("surface", {}).get("flange")
            expected = csr_matrix(array(row["basis"], (3, 3)))@(maps.port(row["first"], point)-maps.port(row["second"], point, flange))
        elif kind == "floor_tangent":
            require(row["first"] in floor and row["id"] in {row["first"]+f"/no-slip-{i}" for i in (0, 1)}
                    and row["stiffness"] == 100000., "original centroid XY path differs")
            direction = np.eye(3)[int(row["id"][-1])]
            close(point, np.mean(floor[row["first"]], axis=0), 0.)
            close(row["direction_xyz"], direction, 0.)
            expected = csr_matrix(direction[None])@maps.port(row["first"], point)
        else:
            require(kind in {"floor_normal", "shaft_end_capture", "timber_face_contact", "flange_contact", "panel_contact"},
                    "unknown scalar physical law")
            if kind == "floor_normal":
                host = row["first"]
                require(host in floor and row["second"] == "floor" and row["stiffness"] == 25000., "original floor normal law differs")
                close(point, floor[host][int(row["id"].split("/floor-")[-1])], 0.)
                close(row["direction_xyz"], [0., 0., 1.], 0.)
            elif kind == "shaft_end_capture":
                source = source_shafts[row["first"]]
                end = next(value for value in source["ends"] if value["end"] == row["end"]["end"])
                require(row["end"] == end and row["second"] == end["host"]
                        and row["stiffness"] == data["scenario"]["common_shaft_parameters"].get("end_capture_n_mm", 1000.),
                        "own end capture source differs")
                close(point, array(source["point"])+array(source["basis"])[0]*end["pressure_face_s_mm"], 1e-10)
                close(row["host_support_point_xyz_mm"], array(source["point"])+array(source["basis"])[0]*end["support_s_mm"], 1e-10)
                close(row["direction_xyz"], end["direction_on_shaft_xyz"], 0.)
            else:
                require(row["id"] in direct and all(row[key] == value for key, value in direct[row["id"]].items()),
                        "reviewed own contact area/point/director law differs")
            second_point = row.get("host_support_point_xyz_mm", point)
            first_port = row.get("first_port_id")
            second_port = row.get("second_port_id", row.get("end", {}).get("flange"))
            expected = -csr_matrix(array(row["direction_xyz"], (3,))[None])@(maps.port(row["first"], point, first_port)-maps.port(row["second"], second_point, second_port))
        difference = (row["B"]-expected).tocsr()
        require(np.max(abs(difference.data), initial=0.) <= 1e-12, "source-owned interaction B geometry differs")
    close(snapshot.rigid_modes, maps.rigid_modes(), 1e-9, "captured six rigid work modes differ from owned source maps")
    return {"owned_point_ports_independently_replayed": len(all_rows), "full_owned_dof_count": maps.n,
            "unchanged_original_reference_floor_rows": 6*len(floor), "new_finite_contact_law_adopted": False}


def verify_load_work(snapshot, maps, data):
    case = snapshot.case
    total = sum((frame.wrench(row["force_xyz_n"], row["point_xyz_mm"], frame.REFERENCE) for row in case["loads"]), np.zeros(6))
    close(snapshot.rigid_modes.T@snapshot.applied, total, 1e-5, "complete applied RHS rigid work differs from physical point-load wrench")
    nonpanel = np.zeros(maps.n)
    # Reuse the genuine affine timber selfweight quadrature and point projection
    # on a geometry-only map object: empty panels prevents panel K/load rebuild.
    fake = SimpleNamespace(ndof=maps.n, panels={}, members=maps.members, port=maps.port)
    nonpanel_case = {**case, "loads": [row for row in case["loads"] if row["body"] not in maps.panels]}
    # coupled_load_vector only consults integrated through load_cases even when
    # panels is empty; use its already pinned pure evidence input, not CAD.
    integrated = json.loads(frame.EVIDENCE.read_bytes())
    nonpanel[:] = frame.coupled_load_vector(fake, nonpanel_case, integrated)
    panel_indices = np.concatenate([row["indices"] for row in maps.panels.values()]) if maps.panels else np.array([], dtype=int)
    indices = np.setdiff1d(np.arange(maps.n), panel_indices)
    close(snapshot.applied[indices], nonpanel[indices], 1e-9, "nonpanel source load projection differs from captured RHS")
    origin_wrench = sum((frame.wrench(row["force_xyz_n"], row["point_xyz_mm"]) for row in case["loads"]), np.zeros(6))
    close(np.r_[case["applied_force_xyz_n"], case["applied_moment_about_global_origin_xyz_nmm"]], origin_wrench, 1e-5)
    return {"complete_six_component_applied_load_work_replayed": True,
            "nonpanel_affine_selfweight_and_point_load_projections_replayed": True,
            "distributed_panel_rhs_independently_regenerated": False,
            "distributed_panel_rhs_is_exact_source_authenticated_capture": True,
            "physical_load_count": len(data["case"]["loads"]), "applied_wrench_about_reference_n_nmm": total.tolist()}


def replay_original(snapshot, q, enabled):
    """Saved same-q original physical energy/gradient/forces; no numerical step."""
    q = array(q, (snapshot.assembly.ndof,))
    return core.search._fresh_fields(snapshot.assembly.K, snapshot.applied, snapshot.groups,
                                     snapshot.contacts, snapshot.tangents, set(enabled), q)


def verify_search(response, hosts, q, normal_by_host, budget):
    diag = response["support_state_search_v1"]
    require(diag["schema"] == "thin_bolted_support_state_search/v1" and diag["method"] == core.search.METHOD
            and diag["host_order"] == hosts and diag["total_possible_masks"] == 1 << len(hosts)
            and diag["floor_activation_threshold_n"] == 1e-7 and diag["mask_budget"] == budget
            and diag["old_field_initialization_used"] is False and diag["physical_laws_changed"] is False
            and diag["no_fixed_point_proven"] is False
            and diag["near_threshold_diagnostic_is_a_normal_force_error_bound"] is False
            and diag["body_global_and_export_admission_required"] is True,
            "unchanged fresh whole-foot search contract required")
    rows, visited = diag["tested_masks"], set()
    require(isinstance(rows, list) and 1 <= len(rows) <= budget, "bounded nonempty search rows required")
    current, reason = (1 << len(hosts))-1, "original all-host initial mask"
    for i, row in enumerate(rows):
        enabled = core.search._enabled(hosts, current)
        disabled = sorted(set(hosts)-set(enabled))
        require(row["pattern_index"] == i and row["mask_id"] == core.search._mask_id(hosts, current)
                and row["selection_reason"] == reason and row["enabled_centroid_xy_hosts"] == enabled
                and row["disabled_centroid_xy_hosts"] == disabled and current not in visited
                and row["initialization_from_previous_fresh_branch_only"] is (i > 0 and rows[i-1]["fresh_original_gradient_inf_n"] is not None),
                "recorded search choices or fresh initialization differ")
        visited.add(current)
        fixed = row["fixed_branch_converged"] is True
        demanded = None
        if row["fresh_original_gradient_inf_n"] is not None:
            require(np.isfinite(row["fresh_original_gradient_inf_n"]) and row["fresh_original_gradient_inf_n"] >= 0.,
                    "finite nonnegative fresh branch residual required")
            normals = row["floor_normal_force_n_by_host"]
            require(set(normals) == set(hosts) and np.all(array(list(normals.values())) >= 0.), "own floor resultants required")
            demanded = sum(1 << j for j, host in enumerate(hosts) if normals[host] > 1e-7)
            require(row["demanded_enabled_centroid_xy_hosts"] == core.search._enabled(hosts, demanded)
                    and row["disabled_xy_force_exactly_zero"] is True
                    and row["disabled_xy_force_n_by_host"] == {host: [0., 0.] for host in disabled}, "branch floor mask law differs")
        require(type(row["fixed_branch_converged"]) is bool and type(row["self_consistent"]) is bool
                and row["self_consistent"] is (fixed and current == demanded)
                and (not fixed or 0. <= row["fresh_original_gradient_inf_n"] < 1e-5), "branch convergence/consistency claim differs")
        if i < len(rows)-1:
            require(not row["self_consistent"], "search continued after accepted branch")
            current, reason = core.search._next_mask(current, demanded if fixed else None, visited, 1 << len(hosts))
    final = rows[-1]
    enabled = sorted(host for host in hosts if normal_by_host[host] > 1e-7)
    require(final["self_consistent"] is True and diag["accepted_pattern_index"] == len(rows)-1
            and diag["accepted_enabled_centroid_xy_hosts"] == final["enabled_centroid_xy_hosts"] == enabled
            and diag["accepted_disabled_centroid_xy_hosts"] == response["nonbearing_no_slip_removed"] == sorted(set(hosts)-set(enabled))
            and diag["final_q_canonical_sha256"] == canonical(q.tolist()) and diag["final_mask_id"] == final["mask_id"]
            and final["fresh_original_gradient_inf_n"] == response["gradient_inf_n"]
            and diag["all_masks_visited"] is (len(visited) == 1 << len(hosts))
            and diag["complete_enumeration"] is (len(visited) == 1 << len(hosts) and all(row["fixed_branch_converged"] for row in rows)),
            "final q and original whole-foot mask must be the fresh final fixed point")
    close([final["floor_normal_force_n_by_host"][host] for host in hosts], [normal_by_host[host] for host in hosts], 1e-8)
    return {"final_q_canonical_sha256": canonical(q.tolist()), "final_mask_id": final["mask_id"],
            "accepted_pattern_index": len(rows)-1, "tested_mask_count": len(rows),
            "bearing_hosts": enabled, "floor_activation_threshold_n": 1e-7}


def verify_actions(field, snapshot, q, fresh):
    """Recover every physical pair from original forces and check 150-body closure."""
    gradient, energy, _, forces, normals, displacement = fresh
    response = field["response"]
    close(response["connector_local_force_n"], forces, 1e-8)
    close(response["normal_contact_force_n"], normals, 1e-8)
    close(response["normal_contact_displacement_mm"], displacement, 1e-10)
    close(response["gradient_n"], gradient, 0., "full signed original gradient differs at saved q")
    require(response["gradient_canonical_sha256"] == canonical(gradient.tolist())
            and response["q_canonical_sha256"] == canonical(q.tolist()), "q/gradient canonical identity differs")
    close(response["potential_energy_nmm"], energy, 1e-7)
    require(float(np.max(abs(gradient))) == response["gradient_inf_n"] <= 1e-5, "original full generalized equilibrium failed")
    group_rows = [row for table in ("panel_screw_actions", "common_shaft_bearing_actions") for row in field[table]]
    scalar_rows = [row for table in ("contact_actions", "shaft_end_capture_actions", "floor_actions") for row in field[table]]
    groups = {row.get("id", row.get("axis_id")): row for row in group_rows}
    scalar = {row["id"]: row for row in scalar_rows}
    require(len(group_rows) == len(groups) == len(snapshot.groups) and set(groups) == {row["id"] for row in snapshot.groups}
            and len(scalar_rows) == len(scalar) == len(snapshot.contacts)+len(snapshot.tangents)
            and set(scalar) == {row["id"] for row in [*snapshot.contacts, *snapshot.tangents]}
            and not field["attachment_actions"] and not field["retained_bolt_actions"], "physical action census has duplicates, omissions or legacy fittings")
    balance = {row["id"]: np.zeros(6) for row in snapshot.assembly.geo["bodies"]}
    for load in snapshot.case["loads"]:
        balance[load["body"]] += frame.wrench(load["force_xyz_n"], load["point_xyz_mm"], frame.REFERENCE)
    floor_wrench = np.zeros(6)

    def action(source, saved, force):
        require(saved["first"] == source["first"] and saved["second"] == source.get("second", "floor"), "action ownership differs")
        close(saved["point_xyz_mm"], source["point_xyz_mm"], 0.)
        close(saved["force_on_first_xyz_n"], force, 1e-8)
        if "force_on_second_xyz_n" in saved:
            close(saved["force_on_second_xyz_n"], -force, 1e-8)
        for key in ("moment_at_point_model_xyz_nmm", "moment_on_first_at_point_xyz_nmm", "moment_on_second_at_point_xyz_nmm"):
            if key in saved:
                close(saved[key], np.zeros(3), 0., "point spring acquired an artificial free couple")
        balance[source["first"]] += frame.wrench(force, source["point_xyz_mm"], frame.REFERENCE)
        if source.get("second", "floor") == "floor":
            floor_wrench[:] += frame.wrench(force, source["point_xyz_mm"])
        else:
            point = source.get("host_support_point_xyz_mm", source["point_xyz_mm"])
            if "host_support_point_xyz_mm" in source:
                close(saved["host_support_point_xyz_mm"], point, 0.)
            balance[source["second"]] -= frame.wrench(force, point, frame.REFERENCE)
    for source, local in zip(snapshot.groups, forces, strict=True):
        action(source, groups[source["id"]], -array(source["basis"]).T@local)
    normal_by_host = dict.fromkeys(sorted({row["first"] for row in snapshot.contacts if row["kind"] == "floor_normal"}), 0.)
    for source, normal in zip(snapshot.contacts, normals, strict=True):
        saved = scalar[source["id"]]
        close(saved["compression_n"], normal, 1e-8)
        action(source, saved, normal*array(source["direction_xyz"]))
        if source["kind"] == "floor_normal":
            normal_by_host[source["first"]] += float(normal)
    enabled = {host for host, value in normal_by_host.items() if value > 1e-7}
    for source in snapshot.tangents:
        saved = scalar[source["id"]]
        d = float((source["B"]@q)[0])
        on = source["first"] in enabled
        require(saved["interaction_enabled"] is on, "centroid enabled flag differs from whole-foot bearing")
        close(saved["tangent_displacement_mm"], d, 1e-10)
        if not on:
            close(saved["force_on_first_xyz_n"], np.zeros(3), 0., "disabled centroid shear must be exactly zero")
            close(saved["force_on_second_xyz_n"], np.zeros(3), 0.)
            require(saved["energy_nmm"] == 0., "disabled centroid energy must be exactly zero")
        action(source, saved, (-source["stiffness"]*d if on else 0.)*array(source["direction_xyz"]))
    rows = field["body_equilibrium_residuals"]
    require(len(rows) == len(balance) and {row["body"] for row in rows} == set(balance), "full physical-body residual census differs")
    for row in rows:
        close(row["force_xyz_n"], balance[row["body"]][:3], 1e-8)
        close(row["moment_about_reference_xyz_nmm"], balance[row["body"]][3:], 1e-5)
    force_error = max(np.linalg.norm(value[:3]) for value in balance.values())
    moment_error = max(np.linalg.norm(value[3:]) for value in balance.values())
    global_residual = floor_wrench+np.r_[snapshot.case["applied_force_xyz_n"], snapshot.case["applied_moment_about_global_origin_xyz_nmm"]]
    close(field["global_equilibrium_residual_force_n"], global_residual[:3], 1e-8)
    close(field["global_equilibrium_residual_moment_nmm"], global_residual[3:], 1e-5)
    require(force_error < 1e-4 and moment_error < .1 and np.linalg.norm(global_residual[:3]) < 1e-4
            and np.linalg.norm(global_residual[3:]) < .1, "independent physical body/global wrench closure failed")
    return normal_by_host, {"physical_body_count": len(balance), "maximum_body_force_norm_n": float(force_error),
        "maximum_body_moment_about_reference_norm_nmm": float(moment_error), "global_residual_n_nmm": global_residual.tolist(),
        "full_signed_gradient_canonical_sha256": canonical(gradient.tolist()), "gradient_inf_n": float(np.max(abs(gradient))),
        "original_potential_energy_nmm": energy, "floor_force_and_original_whole_foot_mask_replayed": True}


def compare_tree(actual, expected):
    """Exact metadata and finite numerical recovery, with bounded roundoff only."""
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), "loaded fitting recovery metadata differs")
        for key in expected:
            compare_tree(actual[key], expected[key])
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), "loaded fitting recovery shape differs")
        for a, b in zip(actual, expected, strict=True):
            compare_tree(a, b)
    elif isinstance(expected, float):
        close(actual, expected, 1e-7)
    else:
        require(actual == expected, "loaded fitting recovery source/guard flag differs")


def verify_fitting_and_alias_recovery(field, snapshot, maps, q):
    saved = {row["body"]: row for row in field["four_port_fitting_actions"]}
    require(len(saved) == len(field["four_port_fitting_actions"]) == len(maps.fittings), "loaded fitting action census differs")
    constant = 0.
    for body, element in maps.fittings.items():
        expected = element.response(q[element.indices], loads=[row for row in snapshot.case["loads"] if row["body"] == body],
                                    declared_route=factory.guarded.ROUTE)
        compare_tree(saved[body], expected)
        require(expected["root_recovery_uses_loaded_heel"] is True and expected["frozen_unloaded_model_response_used_for_gravity"] is False,
                "own gravity must recover at its loaded internal heel")
        constant += expected["load_projection"]["potential_constant_nmm"]
    bearings, captures = field["common_shaft_bearing_actions"], field["shaft_end_capture_actions"]
    aliases = [*field["common_shaft_wood_bearing_actions"], *field["common_shaft_steel_port_actions"]]
    require(len(aliases) == sum(len(row["surfaces"]) for row in maps.shafts.values()), "own wood/steel alias census differs")
    seen = set()
    for alias in aliases:
        key = (alias["axis_id"], alias["surface_index"])
        require(key not in seen, "own surface aggregate duplicated")
        seen.add(key)
        shaft = next(row for row in maps.shafts.values() if row["axis_id"] == alias["axis_id"])
        surface = shaft["surfaces"][alias["surface_index"]]
        reference = array(surface["entry_xyz_mm"]) if surface["kind"] == "steel" else shaft["point"]+shaft["basis"][0]*np.mean(surface["interval_mm"])
        own = [row for row in bearings if row["axis_id"] == alias["axis_id"] and row["surface_index"] == alias["surface_index"]]
        ends = [row for row in captures if row["axis_id"] == alias["axis_id"] and row["second"] == surface["host"]]
        require(alias["host"] == surface["host"] and alias["own_bearing_points"] == [row["id"] for row in own]
                and alias["own_end_captures"] == [row["id"] for row in ends], "own surface action references differ")
        force, moment = np.zeros(3), np.zeros(3)
        for row in [*own, *ends]:
            value = array(row["force_on_second_xyz_n"])
            force += value
            moment += np.cross(array(row.get("host_support_point_xyz_mm", row["point_xyz_mm"]))-reference, value)
        close(alias["point_xyz_mm"], reference, 1e-10)
        close(alias["force_on_host_xyz_n"], force, 1e-8)
        close(alias["moment_on_host_at_point_xyz_nmm"], moment, 1e-6)
        if surface["kind"] == "steel":
            close(alias["force_on_steel_xyz_n"], force, 1e-8)
            close(alias["moment_on_steel_at_point_xyz_nmm"], moment, 1e-6)
    shaft_sources = {row["body"]: row for row in field.get("source_inputs", {}).get("shafts", [])}
    cut_count = 0
    if shaft_sources:
        # Genuine signed section-cut recovery uses only verified external pair
        # forces/own point gravity, not another material operator or K build.
        view = SimpleNamespace(shafts={name: {**shaft_sources[name], **row} for name, row in maps.shafts.items()},
            parameters={"shaft_diameter_scale": field["source_inputs"]["scenario"]["common_shaft_parameters"].get("diameter_scale", 1.)})
        expected_cuts = factory.common.CommonShaftSystem.section_cut_actions(view, snapshot.case, bearings, captures)
        compare_tree(field["common_shaft_section_cut_actions"], expected_cuts)
        cut_count = len(expected_cuts)
    return {"loaded_root_recoveries_replayed": len(saved), "own_surface_aggregate_recoveries_replayed": len(aliases),
            "own_signed_external_action_shaft_cut_recoveries_replayed": cut_count,
            "fitting_gravity_condensation_potential_constant_nmm": constant,
            "captured_global_potential_omits_this_q_independent_constant": True}


def motion_diagnostics(snapshot, maps, q):
    translations, rotations = [], []
    for body, row in maps.members.items():
        nodal = q[row["index"]]
        translations.append({"body": body, "maximum_node_translation_norm_mm": float(np.max(np.linalg.norm(nodal[:, :3], axis=1)))})
        rotations.append({"body": body, "maximum_node_rotation_norm_rad": float(np.max(np.linalg.norm(nodal[:, 3:]/1000., axis=1)))})
    points = [(row[side], row.get("host_support_point_xyz_mm", row["point_xyz_mm"]) if side == "second" else row["point_xyz_mm"],
               row.get(side+"_port_id", row.get("surface", {}).get("flange", row.get("end", {}).get("flange")) if side == "second" else None))
              for row in [*snapshot.groups, *snapshot.contacts] for side in ("first", "second") if row.get(side) != "floor"]
    values = [float(np.linalg.norm(maps.port(body, point, flange)@q)) for body, point, flange in points]
    relative = []

    def rotation(body, point, port_id):
        if body in maps.fittings:
            element = maps.fittings[body]
            row = next(value for value in element.model.port_manifest if value["id"] == port_id)
            return q[element.indices[6*row["port_index"]+3:6*row["port_index"]+6]]/1000.
        member = maps.members[body]
        s = float((array(point)-member["start"])@member["axis"])
        i = int(np.clip(np.searchsorted(member["stations"], s)-1, 0, len(member["stations"])-2))
        a, b = member["stations"][i:i+2]
        t = float(np.clip((s-a)/(b-a), 0., 1.))
        return ((1-t)*q[member["index"][i, 3:]]+t*q[member["index"][i+1, 3:]])/1000.

    for row in snapshot.contacts:
        if (row["first"] in maps.members or row["first"] in maps.fittings) and (row["second"] in maps.members or row["second"] in maps.fittings):
            first = rotation(row["first"], row["point_xyz_mm"], row.get("first_port_id"))
            second = rotation(row["second"], row["point_xyz_mm"], row.get("second_port_id"))
            relative.append(float(np.linalg.norm(first-second)))
    return {"timber_node_translation_rows": translations, "timber_node_rotation_rows": rotations,
            "maximum_owned_interaction_point_linear_displacement_norm_mm": max(values, default=0.),
            "maximum_relative_timber_or_fitting_strip_rotation_norm_rad": max(relative, default=0.),
            "first_order_applicability_established": False, "adopted_small_motion_threshold": None,
            "finite_contact_pressure_or_physical_demand_bounds_established": False}


def verify_physical_bodies(snapshot, data):
    expected = list(data["base_bodies"])
    for row in data["shafts"]:
        mass = sum(role["volume_mm3"]*7850e-9 for role in row["metal_roles"])
        center = sum((array(role["center_of_mass_xyz_mm"])*role["volume_mm3"]*7850e-9 for role in row["metal_roles"]), np.zeros(3))/mass
        expected.append({"id": row["body"], "kind": "shaft_assembly", "mass_kg": mass, "center_xyz_mm": center.tolist()})
    require(snapshot.assembly.geo["bodies"] == expected, "actual 150 physical-owner masses/datums differ from source rows")


def audit_first_order_state(path_or_bytes):
    raw = path_or_bytes if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_bytes()
    field = json.loads(raw)
    require(field.get("schema") == FIELD_SCHEMA and field.get("disposition") == "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION"
            and field.get("independent_admission_required") is True and field.get("release") == core.RELEASE
            and field.get("usable_conditional_actions") is True,
            "one pending conditional v2 field with every release false required")
    identity = identities(field)
    response = field["response"]
    require(response.get("converged") is True and "q" in response and "diagnostic_last_q" not in response
            and response.get("physical_residual_uses_unmodified_laws") is True
            and response.get("generalized_residual_tolerance_n") == 1e-5
            and response.get("wall_time_limit_reached", False) is False,
            "failed/unaccepted coefficients cannot enter field admission")
    before = source_pins(field["source_sha256"])
    snapshot = bundle.read_snapshot(field["operator_bundle"])
    require(all(field["source_sha256"].get(path) == digest for path, digest in snapshot.manifest["source_sha256"].items())
            and all(field["source_sha256"].get(row["path"]) == row["sha256"] for row in field["operator_bundle"].values())
            and field["original_operator_fingerprint_sha256"] == snapshot.manifest["original_operator_fingerprint_sha256"]
            and field["physical_body_descriptors"] == snapshot.manifest["body_descriptors"]
            and field["fitting_operator_descriptors"] == snapshot.manifest["fitting_descriptors"]
            and field["reference_interaction_descriptors"] == [core.descriptor(row) for row in [*snapshot.groups, *snapshot.contacts, *snapshot.tangents]],
            "field must retain exact captured source/operators/descriptors")
    data, args = verify_execution(field, snapshot)
    counts = factory.validate_rows(data)
    require(all(field["counts"][key] == value for key, value in counts.items())
            and field["counts"]["dofs"] == snapshot.assembly.ndof
            and field["counts"]["bearings"] == sum(row["kind"] == "common_shaft_bearing" for row in snapshot.groups)
            and field["counts"]["contacts"] == len(snapshot.contacts)
            and field["counts"]["end_captures"] == 200 and field["counts"]["floor_normals"] == 32
            and field["counts"]["floor_xy_components"] == 16, "actual 150-owner/operator census differs")
    require(len(field["physical_body_descriptors"]) == 150 and set(field["body_identities"]) == {row["id"] for row in field["physical_body_descriptors"]},
            "all 150 actual physical owners required")
    maps = OwnedMaps(snapshot, data)
    verify_physical_bodies(snapshot, data)
    port_checks = verify_ports(snapshot, maps, data)
    load_checks = verify_load_work(snapshot, maps, data)
    q = array(response["q"], (snapshot.assembly.ndof,))
    enabled = response["support_state_search_v1"]["accepted_enabled_centroid_xy_hosts"]
    fresh = replay_original(snapshot, q, enabled)
    normals, law_checks = verify_actions(field, snapshot, q, fresh)
    search_checks = verify_search(response, sorted(data["floor_footprints"]), q, normals, args.mask_budget)
    recovery_checks = verify_fitting_and_alias_recovery(field, snapshot, maps, q)
    for body, row in field["panel_generalized_coefficients"].items():
        chart = snapshot.coordinate_map["panels"][body]
        require({key: row[key] for key in chart} == chart and row["global_dof_start"] == chart["indices"][0], "panel response chart differs")
        close(row["coefficients"], q[chart["indices"]], 0.)
    require(set(field["panel_generalized_coefficients"]) == set(maps.panels), "six panel coefficient exports required")
    diagnostics = motion_diagnostics(snapshot, maps, q)
    require(source_pins(field["source_sha256"]) == before, "immutable field sources changed during admission")
    return {"schema": SCHEMA, SUCCESS: True, **identity, "input_raw_sha256": hashlib.sha256(raw).hexdigest(),
            "input_canonical_sha256": canonical(field), "source_sha256": before, "source_path": str(OWN.relative_to(frame.ROOT)),
            "admission_source_sha256": LOADED_SHA, "operator_bundle": field["operator_bundle"],
            "original_operator_fingerprint_sha256": field["original_operator_fingerprint_sha256"],
            "support_search_checks": search_checks, "original_law_checks": law_checks, "owned_port_checks": port_checks,
            "applied_load_checks": load_checks, "loaded_recovery_checks": recovery_checks, "motion_diagnostics": diagnostics,
            "table_canonical_sha256": {key: canonical(field[key]) for key in TABLES}, "release": core.RELEASE,
            "physical_demand_bounds_established": False, "first_order_physical_applicability_established": False}


def require_admitted_payload(field_bytes, receipt, *, admission_sha256):
    """Cheap unchanged-byte consumer; never replay operators or relabel receipts."""
    require(isinstance(field_bytes, bytes) and admission_sha256 == LOADED_SHA == frame.sha(OWN), "actual issued gate SHA required")
    field = json.loads(field_bytes)
    require(receipt.get("schema") == SCHEMA and receipt.get(SUCCESS) is True
            and receipt.get("source_path") == str(OWN.relative_to(frame.ROOT))
            and receipt.get("admission_source_sha256") == admission_sha256
            and receipt.get("input_raw_sha256") == hashlib.sha256(field_bytes).hexdigest()
            and receipt.get("input_canonical_sha256") == canonical(field)
            and receipt.get("release") == field.get("release") == core.RELEASE
            and field.get("schema") == FIELD_SCHEMA and field["response"].get("converged") is True
            and field.get("disposition") == "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION"
            and field.get("usable_conditional_actions") is True,
            "actual independent receipt and exact unchanged pending field required")
    require(all(receipt.get(key) == value for key, value in identities(field).items())
            and receipt["support_search_checks"]["final_q_canonical_sha256"] == canonical(field["response"]["q"])
            and receipt["original_law_checks"]["full_signed_gradient_canonical_sha256"] == canonical(field["response"]["gradient_n"])
            and receipt["operator_bundle"] == field["operator_bundle"]
            and receipt["original_operator_fingerprint_sha256"] == field["original_operator_fingerprint_sha256"]
            and receipt["table_canonical_sha256"] == {key: canonical(field[key]) for key in TABLES},
            "state/q/gradient/operator/action receipt binding differs")
    pins = source_pins(receipt["source_sha256"])
    require(all(pins.get(path) == digest for path, digest in field["source_sha256"].items()), "consumer source closure incomplete")
    return field, pins

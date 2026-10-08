"""Pure, source-bound B104 local mechanical profile inputs; no CAD or solve."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import sys
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PACKET = Path("docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison")
CONTACT = Path("docs/wood-joints-mvp/hypotheses/washer-finite-sector-contact-native-2026-10-01-attempt02")
FROZEN = {
    str(PACKET / "mixed-offset-rows-shallow-wires-v4.json"): "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c",
    str(PACKET / "native-geometry-v4.json"): "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
    str(PACKET / "steel-resistance-methods-v4.json"): "d00ff10eb875c0d093f6c0e811a7b1e2ef850f6d3ec846b6b910eb2c4cdabf19",
    str(PACKET / "timber-bolt-resistance-v4.json"): "5e78ac49a2db2050caf7ee7d2002d0ebf4f9a92496e857a0e2d652629bd0d848",
    str(PACKET / "timber-demand-a12-rear-finished-floor-v4.json"): "fb1a8f0b18de475d48db4a5aad59d681e8be4df90fe028c93612ed613066509b",
    str(PACKET / "access-takeoff-v4.json"): "0c5a09879c9b191c39b96ce670d71ad110661bff7dfeab68133f711b32de476c",
    str(CONTACT / "freeze.json"): "87894949d0f9aa45ca479fa290fb2ae8c354884d290b9ac0e13e2a902522c8aa",
}
PATCHES = {
    "outer_base_left_single": {"axes": ["019", "020"], "timber": ["base_header", "base_side_left"],
                               "fittings": ["B104ZN_clip_angle_base_left_reference"], "body_count": 11},
    "center_left_shared": {"axes": ["011", "012", "013"], "timber": ["base_header", "base_principal_center_left", "base_post_center_left"],
                           "fittings": ["B104ZN_clip_split_base_center_left_reference", "B104ZN_clip_split_header_center_left_reference"], "body_count": 17},
}
TOL = 1e-8


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def scale(a, s):
    return [x * s for x in a]


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def finite_tree(value):
    if isinstance(value, float):
        require(math.isfinite(value), "nonfinite profile input")
    elif isinstance(value, dict):
        for item in value.values():
            finite_tree(item)
    elif isinstance(value, list):
        for item in value:
            finite_tree(item)


def assert_close(a, b, label):
    require(abs(a-b) <= TOL * max(1., abs(a), abs(b)), label)


def verify_pins(pins):
    for relative, expected in pins.items():
        require(sha(ROOT / relative) == expected, "source mismatch: " + relative)


def frame(axis, fitting):
    z = axis["direction"]
    x = fitting["w_xyz"]
    y = cross(z, x)
    for vector in (x, y, z):
        assert_close(dot(vector, vector), 1., "axis frame norm")
    assert_close(dot(x, y), 0., "axis frame orthogonality")
    assert_close(dot(cross(x, y), z), 1., "axis frame handedness")
    offset = axis["hardware_scenario"]["washer_thickness_mm"] + axis["before_plate_mm"]
    origin = add(axis["point"], scale(z, -offset))
    return {"origin_underhead_xyz_mm": origin, "x_xyz": x, "y_xyz": y, "z_head_to_nut_xyz": z,
            "local_to_global_rotation_rows": [[x[i], y[i], z[i]] for i in range(3)],
            "coordinate_rule": "world=underhead_origin+x*local_x+y*local_y+z*local_z",
            "hex_azimuth": "regular-hex vertex on local+x; response convention, not inspected product clocking"}


def plane(transform, station, outward):
    z = transform["z_head_to_nut_xyz"]
    return {"local_z_mm": station, "origin_xyz_mm": add(transform["origin_underhead_xyz_mm"], scale(z, station)),
            "washer_outward_normal_xyz": scale(z, outward)}


def source_body(parts, identity):
    source = parts[identity]
    return {k: source[k] for k in ("id", "kind", "path", "sha256", "solid_count")}


def build_stack(axis, fittings, seats, windows, supports, dimensions, parts):
    identifier = axis["id"]
    h = axis["hardware_scenario"]
    require(axis["diameter_mm"] == 12.7 and h["threads_per_inch"] == 13, "wrong selected dimensional family")
    require(all((identifier, r) in seats for r in ("head_washer", "nut_washer")), "missing own seat")
    require(len(axis["receivers"]) == 1, "selected stack receiver changed")
    first = fittings[axis["attachments"][0]["angle_id"]]
    transform = frame(axis, first)
    washer, before, after = h["washer_thickness_mm"], axis["before_plate_mm"], axis["after_plate_mm"]
    near = washer + before
    far = near + axis["grip_mm"]
    nut_washer_start = far + after
    nut_start = nut_washer_start + washer
    length = axis["nominal_under_head_length_mm"]
    standard = dimensions["cap_screw_standard"]
    head_height = 25.4 * standard["half_inch_head_height_in"][1]
    head_ac = 25.4 * standard["half_inch_AC_in"][1]
    head_af = head_ac * math.sqrt(3.) / 2.
    face_height = 25.4 * standard["washer_face_height_in"][0]
    face_diameter = 25.4 * standard["half_inch_AF_in"][1] * standard["washer_face_diameter_factor_of_max_AF"][0]
    nut_height = 25.4 * dimensions["nut"]["height_in"][1]
    nut_af = 25.4 * dimensions["nut"]["AF_in"][1]
    nut_end = nut_start + nut_height
    assert_close(near, windows[identifier]["all_bearing_members"][0]["underhead_bearing_intervals_mm"][0][0], "saved bearing start replay")
    assert_close(length-nut_start-h["nut_height_mm"], axis["tip_projection_beyond_nut_mm"], "frozen tip replay")
    require(nut_end < length, "response nut extends beyond preserved nominal tip")
    actual_support = supports[(identifier, axis["receivers"][0])]
    expected_intervals = windows[identifier]["all_bearing_members"][0]["underhead_bearing_intervals_mm"]
    require(expected_intervals == [[a+near, b+near] for a, b in actual_support["finished_full_wall_intervals_from_axis_point_mm"]], "saved finished wall replay")
    roles = {
        "bolt": {"body_id": identifier+"_response_bolt", "recipe": "union head hex upper body, circular washer face, and continuous coaxial shaft segments; no separate overlapping collision head",
                 "head_hex_z_mm": [-head_height, -face_height], "head_AC_mm": head_ac, "derived_head_AF_mm": head_af,
                 "circular_washer_face_z_mm": [-face_height, 0.], "washer_face_diameter_mm": face_diameter,
                 "head_fillet_radius_mm": None, "head_chamfer_geometry": None,
                 "face_scope": "flat circular gaged-diameter response idealization, not authenticated pressure footprint; sharp joins not product stress geometry"},
        "head_washer": {"body_id": identifier+"_response_head_washer", "shape": "annular cylinder", "z_mm": [0., washer],
                        "OD_mm": h["washer_od_mm"], "ID_mm": h["washer_id_mm"]},
        "nut_washer": {"body_id": identifier+"_response_nut_washer", "shape": "annular cylinder", "z_mm": [nut_washer_start, nut_start],
                       "OD_mm": h["washer_od_mm"], "ID_mm": h["washer_id_mm"]},
        "nut": {"body_id": identifier+"_response_nut", "shape": "regular hex prism minus nominal-major exclusion cylinder", "z_mm": [nut_start, nut_end],
                "AF_mm": nut_af, "derived_AC_mm": 2.*nut_af/math.sqrt(3.), "exclusion_bore_mm": axis["diameter_mm"],
                "exclusion_bore_scope": "12.7mm nominal major-diameter void retained from frozen geometry; not delivered bore, internal minor diameter or active thread geometry",
                "face_scope": "flat hollow-hex response face, intersected with washer annulus; actual chamfer and pressure footprint unresolved"},
    }
    segments = []
    switches = {"frozen_fullD_cylinder_reference": None, "entire_0p8D_cylinder_sensitivity": 0.,
                "Lb_0p8D_root_sensitivity": windows[identifier]["standard_Lbmin_mm"],
                "Lg_0p8D_root_sensitivity": windows[identifier]["standard_Lgmax_mm"],
                "far_wood_face_0p8D_root_sensitivity": far}
    for name, switch in switches.items():
        sections = []
        if switch is None:
            sections.append({"z_mm": [0., length], "diameter_mm": 12.7})
        else:
            if switch > 0:
                sections.append({"z_mm": [0., switch], "diameter_mm": 12.7})
            sections.append({"z_mm": [switch, length], "diameter_mm": .8*12.7})
        nut_sections = [r for r in sections if r["z_mm"][0] < nut_end and r["z_mm"][1] > nut_start]
        segments.append({"id": name, "shaft_segments": sections,
                         "nut_span_radial_exclusion_gaps_mm": [(12.7-r["diameter_mm"])/2 for r in nut_sections],
                         "physical_profile_or_thread_occupancy_bound": False})
    contacts = []
    washer_planes = []
    for role, receiving_station, pressure_station, outward in (("head_washer", washer, 0., 1.), ("nut_washer", nut_washer_start, nut_start, -1.)):
        seat = seats[(identifier, role)]
        plate_station = receiving_station
        attached = [a for a in axis["attachments"] if abs(dot(add(a["entry_xyz_mm"], scale(axis["point"], -1.)), axis["direction"])-(0. if role=="head_washer" else axis["grip_mm"])) < TOL]
        receiving_body = attached[0]["angle_id"] if seat["support_material"] == "steel" else axis["receivers"][0]
        require(len(attached) == (1 if seat["support_material"]=="steel" else 0), "ambiguous washer receiver ownership")
        pressure_role = "bolt" if role == "head_washer" else "nut"
        pressure = plane(transform, pressure_station, -outward)
        receiving = plane(transform, plate_station, outward)
        washer_planes.append({"role": role, "body_id": roles[role]["body_id"], "receiving_body": receiving_body,
                              "pressure_body": roles[pressure_role]["body_id"], "receiving_plane": receiving, "pressure_plane": pressure,
                              "receiving_support_opening_mm": seat["planned_support_opening_mm"],
                              "source_backed_fraction": seat["annulus_outside_intentional_opening_backed_fraction"],
                              "pressure_to_receiving_arm_local_mm": [0., 0., receiving_station-pressure_station],
                              "moment_translation": "M_receiving=M_pressure+(r_pressure-r_receiving) cross F; transform full wrench with declared frame",
                              "unilateral_pressure_moment_recovery_required": True})
        for side, partner, p in (("receiving", receiving_body, receiving), ("pressure", roles[pressure_role]["body_id"], pressure)):
            contacts.append({"id": identifier+"/"+role+"/"+side, "bodies": [roles[role]["body_id"], partner],
                             "kind": "finite_face_compression_only_frictionless", "washer_plane_reference": role+"/"+side+"_plane",
                             "initial_normal_gap_mm": 0., "zero_gap_is_not_active_pressure": True,
                             "domain": "intersection of actual two owned faces; retain washer and receiving openings; no disk fill"})
    bore_contacts = [{"body": axis["receivers"][0], "z_mm": expected_intervals, "bore_diameter_mm": axis["bore_diameter_mm"]}]
    for attachment in axis["attachments"]:
        s = dot(add(attachment["entry_xyz_mm"], scale(axis["point"], -1.)), axis["direction"])+near
        interval = [washer, near] if abs(s-near) < TOL else [far, far+after]
        bore_contacts.append({"body": attachment["angle_id"], "flange": attachment["flange"], "z_mm": [interval], "bore_diameter_mm": axis["bore_diameter_mm"]})
    frozen_axis = {k: axis[k] for k in ("id", "point", "direction", "grip_mm", "diameter_mm", "bore_diameter_mm", "receivers", "before_plate_mm", "after_plate_mm", "hardware_scenario", "nominal_under_head_length_mm", "tip_projection_beyond_nut_mm", "nominal_thread_window_qualified")}
    frozen_axis["attachments"] = [{k: a[k] for k in ("angle_id", "duty_id", "flange", "receiver", "entry_xyz_mm", "axis_xyz")} for a in axis["attachments"]]
    frozen_axis["complete_original_axis_canonical_sha256"] = canonical(axis)
    window = windows[identifier]
    window_compact = {k: window[k] for k in ("standard_Lgmax_mm", "standard_Lbmin_mm", "NDS_diameter_window_scenario")}
    window_compact["complete_original_row_canonical_sha256"] = canonical(window)
    window_compact["source_bearing_intervals"] = [{k: r[k] for k in ("member", "material", "underhead_bearing_intervals_mm", "minimum_thread_bearing_from_Lgmax_mm", "maximum_possible_thread_bearing_from_Lbmin_mm")} for r in window["all_bearing_members"]]
    return {"axis_id": identifier, "frozen_occupancy": frozen_axis, "local_frame": transform,
            "wood_faces_underhead_z_mm": [near, far], "mechanical_roles": roles,
            "shaft_profiles": segments, "washer_planes": washer_planes, "axial_contact_pairs": contacts,
            "shaft_receiver_contact_domains": bore_contacts,
            "shaft_washer_bore_contact_domains": [{"body": roles[r]["body_id"], "z_mm": [roles[r]["z_mm"]], "bore_diameter_mm": roles[r]["ID_mm"]} for r in ("head_washer", "nut_washer")],
            "radial_gap_rule": "(owned bore diameter - local shaft segment diameter)/2; open clearance before engagement, frictionless normal bearing",
            "nominal_fullD_radial_bore_gap_mm": (axis["bore_diameter_mm"]-12.7)/2,
            "frozen_standard_thread_window": window_compact,
            "response_nominal_tip_beyond_nut_mm": length-nut_end,
            "comparison_shortest_length_tip_beyond_same_response_nut_mm": length + 25.4*dimensions["bolt_3in" if length==76.2 else "bolt_5in"]["length_tolerance_in"][0]-nut_end,
            "collision_metadata_sources": [source_body(parts, identifier+"_"+role) for role in ("shaft", "head", "head_washer", "nut_washer", "nut")],
            "engagement": {"id": identifier+"/response_nut_to_shaft", "bodies": [roles["bolt"]["body_id"], roles["nut"]["body_id"]],
                           "origin_local_mm": [0., 0., .5*(nut_start+nut_end)], "strict_axial_span_local_mm": [nut_start, nut_end],
                           "type": "objective internal projected-motion sensitivity", "constrained_relative_coordinates": ["ux", "uy", "uz", "rx", "ry"],
                           "free_relative_coordinate": "rz", "external_torsional_clamp": False, "axial_spin_torque_transferred": False,
                           "recipe": "independent rank-six rigid-motion fits to owned shaft and hollow-nut patches at the common origin; equate three translations and two transverse rotations; use the adjoint for wrench recovery",
                           "scope": "infinite translational/tilt engagement sensitivity across exclusion gap; no actual helix/flank/thread stiffness, stripping strength, spin-to-axial pitch law, preload or friction"}}


def validate_report(report):
    finite_tree(report)
    require(report["complete_contact_model"] is False and report["native_ready"] is False, "contact-incomplete input relabelled ready")
    require(report["counts"] == {"local_patches": 2, "physical_shafts": 5, "own_washer_bodies": 10, "own_washer_planes": 20, "shaft_profiles_per_axis": 5}, "profile census changed")
    stacks = {r["axis_id"]: r for r in report["stacks"]}
    for patch in report["patches"]:
        roles = [stacks[a]["mechanical_roles"][r]["body_id"] for a in patch["axis_ids"] for r in ("bolt", "head_washer", "nut_washer", "nut")]
        require(len(set(roles+patch["timber_ids"]+patch["fitting_ids"])) == patch["expected_mechanical_body_count"], "mechanical body ownership changed")
    for stack in stacks.values():
        require(stack["engagement"]["free_relative_coordinate"] == "rz" and not stack["engagement"]["external_torsional_clamp"], "torsional restraint invented")
        for row in stack["washer_planes"]:
            t = abs(row["receiving_plane"]["local_z_mm"]-row["pressure_plane"]["local_z_mm"])
            assert_close(t, stack["frozen_occupancy"]["hardware_scenario"]["washer_thickness_mm"], "own washer planes collapsed")
        for profile in stack["shaft_profiles"]:
            sections = profile["shaft_segments"]
            assert_close(sections[0]["z_mm"][0], 0., "shaft start changed")
            assert_close(sections[-1]["z_mm"][1], stack["frozen_occupancy"]["nominal_under_head_length_mm"], "shaft nominal tip changed")
            for a, b in pairwise(sections):
                assert_close(a["z_mm"][1], b["z_mm"][0], "shaft discontinuity")
            require(all(r["z_mm"][1] > r["z_mm"][0] and r["diameter_mm"] > 0 for r in sections), "nonpositive shaft segment")
        f = stack["local_frame"]
        # Six global rigid motions give zero relative projected engagement.
        o = add(f["origin_underhead_xyz_mm"], scale(f["z_head_to_nut_xyz"], stack["engagement"]["origin_local_mm"][2]))
        for basis in ([1., 0., 0.], [0., 1., 0.], [0., 0., 1.]):
            for translation, rotation in ((basis, [0., 0., 0.]), ([0., 0., 0.], basis)):
                centers = (add(o, [.6, -1.2, 2.3]), add(o, [-.9, 2.1, -3.2]))
                recovered = []
                for center in centers:
                    at_center = add(translation, cross(rotation, center))
                    recovered.append(add(at_center, cross(rotation, add(o, scale(center, -1.)))))
                for a, b in zip(*recovered, strict=True):
                    assert_close(a, b, "engagement constrains global rigid motion")
        for transverse in (f["x_xyz"], f["y_xyz"]):
            assert_close(dot(transverse, f["z_head_to_nut_xyz"]), 0., "relative shaft-axis spin constrained by engagement")
        # Check origin translation and local/world virtual work for a nontrivial wrench.
        force = [2., -3., 5.]
        moment = [7., 11., -13.]
        displacement = [.01, -.02, .03]
        rotation = [.004, -.005, .006]
        matrix = f["local_to_global_rotation_rows"]
        def rotate(v, matrix=matrix):
            return [dot(r, v) for r in matrix]
        assert_close(dot(force, displacement)+dot(moment, rotation), dot(rotate(force), rotate(displacement))+dot(rotate(moment), rotate(rotation)), "local/global virtual work mismatch")
        for row in stack["washer_planes"]:
            arm = row["pressure_to_receiving_arm_local_mm"]
            translated = add(moment, scale(cross(arm, force), -1.))
            # u_pressure=u_receiving + theta cross (r_pressure-r_receiving).
            u_pressure = add(displacement, cross(rotation, scale(arm, -1.)))
            assert_close(dot(force, u_pressure)+dot(moment, rotation), dot(force, displacement)+dot(translated, rotation), "moment datum virtual work mismatch")


def build():
    verify_pins(FROZEN)
    reports = {Path(k).name: json.loads((ROOT/k).read_text()) for k in FROZEN if Path(k).name != "freeze.json"}
    layout, native = reports["mixed-offset-rows-shallow-wires-v4.json"], reports["native-geometry-v4.json"]
    source_pins = dict(FROZEN)
    binding_entries = len(FROZEN)
    for report in reports.values():
        for path, expected in report.get("source_sha256", {}).items():
            require(path not in source_pins or source_pins[path] == expected, "inconsistent original source binding")
            source_pins[path] = expected
            binding_entries += 1
    own_files = [Path(__file__).resolve(), HERE/"primary-dimensions.json"]
    reuse = ["scripts/wood_joint_wj04_mechanics_hardware.py", "fea/wood_joint_current_nut_coupling.py", "fea/wood_joint_patch_rigid_modes.py",
             "fea/wood_joint_patch_contact_contract.py", "fea/wood_joint_patch_materials.py", "uv.lock"]
    for path in own_files + [ROOT/p for p in reuse]:
        source_pins[str(path.relative_to(ROOT))] = sha(path)
    parent = json.loads((ROOT/CONTACT/"parent-result.json").read_text())
    require(parent["input_freeze_sha256"] == FROZEN[str(CONTACT/"freeze.json")] and parent["status"] == "PASS_FINITE_CONTACT_RESULTANT_METHOD_FIXTURE", "annular method identity changed")
    for path, expected in {**parent["raw_outputs_sha256"], **parent["review_sha256"], "parent-output-receipt.json": parent["parent_output_receipt_sha256"], "execution.json": parent["execution_sha256"], "frozen-output-audit.json": parent["audit_sha256"]}.items():
        source_pins[str(CONTACT/path)] = expected
    source_pins[str(CONTACT/"parent-result.json")] = sha(ROOT/CONTACT/"parent-result.json")
    primary = json.loads((HERE/"primary-dimensions.json").read_text())
    parts = {r["id"]: r for r in native["parts"]}
    fittings = {r["angle_id"]: r for r in layout["raw_fittings"]}
    axes = {r["id"]: r for r in layout["installed_axes"]}
    seats = {(r["axis_id"], r["role"]): r for r in layout["washer_seats"]}
    window_rows = reports["timber-demand-a12-rear-finished-floor-v4.json"]["product_standard_thread_windows"]["current70nominal_length_scenarios"]
    windows = {r["axis_id"]: r for r in window_rows}
    full_ref = reports["timber-bolt-resistance-v4.json"]["reproducible_detail_artifact"]
    source_pins[full_ref["path"]] = full_ref["sha256"]
    detail = json.loads((ROOT/full_ref["path"]).read_text())
    supports = {(r["axis_id"], r["member"]): r for r in detail["finished_geometry_queries"]["receiver_boundary_geometry"]}
    selected_ids = sorted({"thin_factory_bolt_"+a for patch in PATCHES.values() for a in patch["axes"]})
    selected_parts = {a+"_"+r for a in selected_ids for r in ("shaft", "head", "head_washer", "nut_washer", "nut")}
    selected_parts.update(n for patch in PATCHES.values() for n in patch["timber"]+patch["fittings"])
    for identity in selected_parts:
        source_pins[parts[identity]["path"]] = parts[identity]["sha256"]
    verify_pins(source_pins)
    stacks = [build_stack(axes[a], fittings, seats, windows, supports, primary, parts) for a in selected_ids]
    patches = []
    for name, config in PATCHES.items():
        flange_planes = []
        for identity in config["fittings"]:
            f = fittings[identity]
            for flange, member, normal, length, hole_centers in (("beam", f["beam"], f["v_xyz"], 104.775, [36.5125, 84.1375]), ("post", f["post"], f["u_xyz"], 88.9, [20.6375, 68.2625])):
                flange_planes.append({"id": identity+"/"+flange+"/backing", "bodies": [identity, member], "origin_xyz_mm": f["origin_xyz_mm"],
                                      "normal_from_wood_into_steel_xyz": normal, "nominal_length_mm": length, "width_mm": 41.275,
                                      "hole_centers_from_ideal_corner_mm": hole_centers, "hole_diameter_mm": 14.2875,
                                      "domain": "cached steel backing face intersected with finished receiving wood; all holes and finished voids retained",
                                      "initial_nominal_normal_gap_mm": 0., "unilateral_frictionless": True, "face_atlas_meshed_or_contact_pressure_verified": False})
        patches.append({"id": name, "axis_ids": ["thin_factory_bolt_"+a for a in config["axes"]], "timber_ids": config["timber"],
                        "fitting_ids": config["fittings"], "expected_mechanical_body_count": config["body_count"],
                        "cached_timber_and_fitting_sources": [source_body(parts, n) for n in config["timber"]+config["fittings"]],
                        "fitting_local_frames": [{k: fittings[n][k] for k in ("angle_id", "origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")} for n in config["fittings"]],
                        "fitting_backing_planes": flange_planes,
                        "unresolved_own_timber_interfaces": [{"bodies": ["base_header", n], "status": "TOUCHING_FACE_ATLAS_AND_FINISHED_CONTACT_AREA_UNAUTHENTICATED; no bilateral tie or silent omission"} for n in config["timber"] if n != "base_header"],
                        "neighbor_ports_and_loaded_free_modes": "separate timber/kinematic worker contract required; no fixed-neighbor restraint assigned"})
    direct_pins = {k: source_pins[k] for k in FROZEN}
    for path in own_files + [ROOT/p for p in reuse] + [ROOT/full_ref["path"], ROOT/CONTACT/"parent-result.json"]:
        relative = str(path.relative_to(ROOT))
        direct_pins[relative] = source_pins[relative]
    result = {"schema": "thin_b104_local_mechanical_hardware_inputs/v1", "status": "SOURCE_BOUND_RESPONSE_ONLY_HARDWARE_INPUTS_CONTACT_INCOMPLETE_NO_CAD_OR_SOLVE",
              "candidate": layout["candidate"], "revision": layout["revision"], "source_sha256": dict(sorted(direct_pins.items())),
              "source_proof": {"original_report_binding_entries": binding_entries, "all_pin_paths_verified_before_and_after": len(source_pins), "pin_union_canonical_sha256": canonical(source_pins),
                               "layout_canonical_sha256": canonical(layout), "native_manifest_canonical_sha256": canonical(native), "selected_cache_parts_verified": len(selected_parts),
                               "full_union_recipe": "direct reports' source_sha256 maps, selected cached parts, bound full detail, reusable helpers, own files and annular parent result output/review maps; verify_pins before and after",
                               "saved_thread_rows_only": "old nominal dimensional scenarios reused as input metadata; no old field demand or candidate acceptance transferred"},
              "method": {"python_version": platform.python_version(), "third_party_python_imports": [], "command_argv": sys.orig_argv,
                         "reproduction_command": ".venv/bin/python fea/generated/thin-bolted-b104-local-hardware-inputs/prepare.py",
                         "CAD_import_or_query": False, "native_or_global_solve": False,
                         "later_geometry_primitives": "WJ04 _hex_prism/_annular_cylinder are parameterized primitives only; do not invoke its WJ16 full adapter or constants"},
              "primary_dimension_observations": primary,
              "counts": {"local_patches": 2, "physical_shafts": 5, "own_washer_bodies": 10, "own_washer_planes": 20, "shaft_profiles_per_axis": 5},
              "patches": patches, "stacks": stacks,
              "material_scenario": {"steel_E_mpa": 200000., "steel_nu": .3, "scope": "existing elastic response assumption for all metal; no washer/bolt/nut yield strength assigned",
                                    "timber": "existing orthotropic material helper with source grain and explicit R/T roll still required; no stock calibration"},
              "contact_method_reuse": {"result_path": str(CONTACT/"parent-result.json"), "status": parent["status"], "run_id": parent["run_id"],
                                       "scope": parent["scope"], "no_repeat_native": True, "curved_bore_or_product_contact_law_validated": False},
              "remaining_inputs": ["Actual selected-product shank/root, thread transition/runout, coating and functional engagement remain unverified; nominal length is not shank.",
                                   "Actual head fillet/chamfer, nut minor bore/face/chamfer and active pressure footprints are missing; supplied shapes are named response idealizations.",
                                   "Minimum USS washer dimensions are comparison-product observations only; actual chosen washer properties and numeric yield remain unknown.",
                                   "Finished touching timber face atlases/area, neighboring ports, active contact branches, mechanical meshes and rank/penalty convergence contract remain unresolved.",
                                   "Actual B104 formed heel radius/minimum dimensions remain required for product heel stress claims; sharp-corner peaks cannot become yield ratios."],
              "complete_contact_model": False, "native_ready": False, "actual_product_profile_qualified": False,
              "strength_or_joint_acceptance": False, "geometry_changed": False, "fabrication_release": False, "climbing_release": False}
    # Store common recipes once; each body keeps its own identity and placement.
    templates = {}
    for role in ("bolt", "head_washer", "nut_washer", "nut"):
        variable = {"body_id", "z_mm"}
        reference = {k: v for k, v in stacks[0]["mechanical_roles"][role].items() if k not in variable}
        for stack in stacks:
            body = stack["mechanical_roles"][role]
            require(reference == {k: v for k, v in body.items() if k not in variable}, "shared dimensional recipe differs")
            stack["mechanical_roles"][role] = {k: v for k, v in body.items() if k in variable} | {"template": role}
        templates[role] = reference
    result["hardware_geometry_templates"] = templates
    result["common_interface_contract"] = {
        "axial_contacts": "finite owned face intersection, compression only, frictionless; normal gap0 is touch, not pressure. Retain every washer/receiver hole; no disk fill, gap adjustment or ties.",
        "washer_moment_rule": "M_receiving=M_pressure+(r_pressure-r_receiving) cross F; local-to-world rotate full wrench at each own declared plane, then translate origin. Distributed pressure/moment recovery required.",
        "engagement": stacks[0]["engagement"]["recipe"], "engagement_scope": stacks[0]["engagement"]["scope"],
        "shaft_profiles": "existing fullD reference and explicit0.8D sensitivities; Lb/Lg are standard metadata, not actual thread-start switches or delivered profile bounds",
        "radial_gap_rule": stacks[0]["radial_gap_rule"],
    }
    for stack in stacks:
        stack["collision_metadata_source_ids"] = [r["id"] for r in stack.pop("collision_metadata_sources")]
        stack.pop("radial_gap_rule")
        for row in stack["washer_planes"]:
            row.pop("moment_translation")
            row.pop("unilateral_pressure_moment_recovery_required")
        for row in stack["axial_contact_pairs"]:
            for key in ("kind", "zero_gap_is_not_active_pressure", "domain"):
                row.pop(key)
        for key in ("recipe", "scope", "type"):
            stack["engagement"].pop(key)
    validate_report(result)
    verify_pins(source_pins)
    return result


def self_checks(report):
    validate_report(report)
    for mutation in ("nonfinite", "body_count", "collapsed_washer", "torsional_clamp", "shaft_tip", "ready_relabel"):
        bad = copy.deepcopy(report)
        if mutation == "nonfinite":
            bad["stacks"][0]["response_nominal_tip_beyond_nut_mm"] = float("nan")
        elif mutation == "body_count":
            bad["patches"][0]["expected_mechanical_body_count"] += 1
        elif mutation == "collapsed_washer":
            row = bad["stacks"][0]["washer_planes"][0]
            row["receiving_plane"]["local_z_mm"] = row["pressure_plane"]["local_z_mm"]
        elif mutation == "torsional_clamp":
            bad["stacks"][0]["engagement"]["external_torsional_clamp"] = True
        elif mutation == "shaft_tip":
            bad["stacks"][0]["shaft_profiles"][0]["shaft_segments"][-1]["z_mm"][1] += 1.
        else:
            bad["complete_contact_model"] = True
        try:
            validate_report(bad)
        except ValueError:
            continue
        raise ValueError("forged profile accepted: " + mutation)
    forged = dict(report["source_sha256"])
    forged[str(PACKET/"mixed-offset-rows-shallow-wires-v4.json")] = "0"*64
    try:
        verify_pins(forged)
    except ValueError:
        return 7
    raise ValueError("forged source pin accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE/"inputs.json")
    args = parser.parse_args()
    require(not args.out.exists(), "refuse to overwrite existing exclusive input artifact")
    report = build()
    report["checks"] = {"profile_math_and_saved_span_replay": "PASS", "forged_profile_and_source_rejections": self_checks(report),
                        "six_rigid_motions_and_same_datum_wrench_work": "PASS", "check_scope": "pure input contracts only; no mesh/contact response is inferred"}
    args.out.write_text(json.dumps(report, separators=(",", ":"), allow_nan=False)+"\n")
    print(json.dumps({"output": str(args.out.relative_to(ROOT)) if args.out.is_relative_to(ROOT) else str(args.out), "sha256": sha(args.out), "bytes": args.out.stat().st_size,
                      "counts": report["counts"], "source_paths": len(report["source_sha256"]), "checks": report["checks"]}, indent=2))


if __name__ == "__main__":
    main()

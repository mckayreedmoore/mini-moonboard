"""Independent current-point admission for the thin finite numerical scenario.

Only source JSON/NPZ, basis values, and mapped positions/directors are read.
No CAD, stiffness, constitutive tangent, equilibrium solve, or old demand is
selected. Admission is conditional export consistency, never strength release.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from itertools import pairwise
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft as common_method
from scripts import thin_bolted_common_shaft_audit as common
from scripts import thin_bolted_equilibrium_audit as arithmetic
from scripts import thin_bolted_finished_support_audit as support
from scripts import thin_bolted_finite_frame as finite
from scripts import thin_bolted_finite_panel_adapter as panel_finite
from scripts import thin_bolted_panel_coupled as panel_datums
from scripts import thin_bolted_panel_load_diagnostics as panel_loads
from scripts import thin_bolted_panel_mechanics as panel_method
from scripts import thin_bolted_timber_common_shaft_checks as member_geometry

ROOT, PACKET = arithmetic.ROOT, arithmetic.PACKET
FINITE_SHA = "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588"
FLOOR_SHA = "0852ced82484414621106314531e883f713f5943358541539e8750af243c2e1f"
SCHEMA = "thin_bolted_finite_frame_response/v1"
SUCCESS = "independent_finite_current_support_load_and_equilibrium_checks_pass"
REFERENCE = np.array([0., 750., 1100.])
POINT_TOL = 1e-5
FORCE_TOL = 1e-6
MOMENT_ALIAS_TOL = .001
SOURCE_PINS = {
    "scripts/thin_bolted_common_shaft_audit.py": "a236900e59a3d5984598df56d4243408ce12801d4ab6fcc7f765f6a420de01ba",
    "scripts/thin_bolted_timber_common_shaft_checks.py": "c27d8d0209f2b0a032c490314fe05cee8fbc949f608dabbf813676c044b90cc7",
    "scripts/thin_bolted_finished_support_audit.py": "0a37e67ed20e3fd1eed8b8b4d0d12889df6fd9a6fb33d6f8f68a0c6768f5ada0",
    "scripts/thin_bolted_timber_resistance.py": "74d992cfbe4947587a8c6f0e65f7a8b47e0cd1c79f07721620c7137208919c2d",
    "scripts/thin_bolted_timber_demand_checks.py": "1be05e74563d2cc7a7ea5437aa4ff7217e62f8314f9fe011ff273d201f755e20",
    "scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0",
    "scripts/thin_bolted_panel_load_diagnostics.py": "ff5e0e7b3944e64379181a6b3a1c442b921c197b87d25da3bd20a2d69ec63ebd",
    str(member_geometry.SPAN_SOURCE.relative_to(ROOT)): member_geometry.SPAN_SOURCE_SHA,
    str(panel_datums.ASSESSMENT.relative_to(ROOT)): panel_datums.ASSESSMENT_SHA,
    str(panel_datums.DATUMS.relative_to(ROOT)): panel_datums.DATUMS_SHA,
    str(panel_loads.OPERATORS.relative_to(ROOT)): panel_loads.OPERATORS_SHA,
}
PHYSICAL_EXPORT_PINS = {
    "scripts/run_thin_bolted_finite_frame.py": "5cf423d80e57b6f4386eb6c7aae39961ba083a7b4a457c7d37694cb80101361e",
    "scripts/thin_bolted_finite_newton.py": "039282fa1c06d90b5e899c1c69c2920c003b42db1a8600e390a7a2d9aca75afe",
    str((PACKET / "finite-frame-method-v4.json").relative_to(ROOT)): "790b1925f042cc3f48fae596f5f8097ec64f8dc9605a00d9e200b4cd7bf28e9f",
    str((PACKET / "floor-corner-stick-method-coupons-v4.json").relative_to(ROOT)): "e7569ddc3ea2addb6171b3a3bcccadaa1b004b8c14da94b0eb61320b3982355e",
}
LOADED_PRODUCER_SHA256 = support.digest(Path(__file__))


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def require(test, message):
    if not test:
        raise ValueError(message)


def array(value, shape=None):
    result = np.asarray(value, dtype=float)
    require(np.isfinite(result).all() and (shape is None or result.shape == shape), "finite audit array of declared shape required")
    return result


def close(actual, expected, tolerance, message):
    a, b = array(actual), array(expected)
    require(a.shape == b.shape and np.max(abs(a - b), initial=0.) <= tolerance, message)


def unique(rows, key="id"):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), "duplicate finite export identity")
    return result


def identities(field, rows):
    identity = tuple(field[k] for k in ("state_id", "case_id", "accessory_placement"))
    require(all(tuple(row.get(k) for k in ("state_id", "case_id", "accessory_placement")) == identity for row in rows),
            "finite export mixes state, case, or accessory identity")


def source_receipt(field):
    require(FINITE_SHA != "UNISSUED", "finite composition must be issued before field admission")
    contact, cache, unit, layout, takeoff, integrated, pins = common.read_sources()
    pins.update(SOURCE_PINS)
    physical = finite.source_pins()
    physical.update(PHYSICAL_EXPORT_PINS)
    require(physical["scripts/thin_bolted_finite_frame.py"] == FINITE_SHA, "frozen finite producer differs")
    require(physical["scripts/thin_bolted_floor_contact.py"] == FLOOR_SHA, "frozen corner support differs")
    pins.update(physical)
    for path, expected in pins.items():
        require(support.digest(ROOT / path) == expected, "finite audit source differs: " + path)
    # Audit-only geometry extraction producers need not be part of a solve.
    required = {k: v for k, v in pins.items() if k not in SOURCE_PINS or not k.startswith("scripts/")}
    state_pins = field.get("source_sha256", {})
    require(all(state_pins.get(k) == v for k, v in required.items()), "finite state omits an authenticated physical/geometry/load source")
    for path, expected in state_pins.items():
        require(support.digest(ROOT / path) == expected, "finite field bound source changed: " + path)
    return contact, cache, unit, layout, takeoff, integrated, pins


def verify_header(field):
    require(field.get("schema") == SCHEMA, "new finite-current outer schema required")
    require(field.get("candidate") == "compact-floor-flush-thin-bolted-development", "foreign finite candidate")
    require(field.get("geometry_cache_sha256") == arithmetic.PINS["native-geometry-v4.json"]
            and field.get("layout_report_sha256") == arithmetic.PINS["mixed-offset-rows-shallow-wires-v4.json"], "finite source geometry differs")
    identity = {k: field[k] for k in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    require(field["state_id"] == "thin-finite-v4-" + canonical_sha(identity)[:24], "finite identity does not bind scenario parameters")
    response = field["response"]
    require(response.get("converged") is True and field.get("usable_conditional_actions") is True,
            "failed finite solve supplies no admitted current actions")
    q = array(response["q"])
    gradient = array(response["gradient_n"], q.shape)
    tolerance = support.finite_scalar(response["generalized_residual_tolerance_n"])
    require(q.ndim == 1 and 0. < tolerance <= 1e-5, "original finite residual tolerance required")
    norm = float(abs(gradient).max(initial=0.))
    require(norm <= tolerance and abs(norm - support.finite_scalar(response["gradient_inf_n"])) <= 1e-10,
            "full original finite gradient fails declared convergence")
    require(field.get("release") and not any(field["release"].values()), "finite numerical admission cannot release fabrication or climbing")
    return q


def verify_floor_proofs(field, contact, cache):
    require(field["parameters"].get("floor_support_basis") == "finished-corner-local-rough-elastic-stick-v1"
            and field["parameters"].get("floor_normal_activation_threshold_n") == 1e-7,
            "source-bound own-corner sticking scenario required")
    require(field["parameters"].get("floor_contact_geometry_sha256") == support.CONTACT_SHA,
            "authenticated finished support geometry pin required")
    proofs = unique(field["finished_floor_footprints"], "member")
    require(set(proofs) == support.FLOOR_HOSTS, "all eight actual finished support polygons required")
    timbers = {r["id"]: r for r in cache["parts"] if r["kind"] == "timber"}
    for host, proof in proofs.items():
        source = timbers[host]
        require(proof["source_brep_path"] == source["path"] and proof["source_brep_sha256"] == source["sha256"],
                "finished support BREP identity differs")
        require(len(proof["polygons_xyz_mm"]) == 1, "one actual horizontal polygon per current foot required")
        polygon = support.rectangle_polygon(proof["polygons_xyz_mm"][0])
        expected = support.rectangle_polygon(contact["finished_floor_footprints"][host], ordered=False)
        distances = np.linalg.norm(polygon[:, None] - expected[None], axis=2) <= POINT_TOL
        require(np.all(distances.sum(axis=0) == 1) and np.all(distances.sum(axis=1) == 1), "finished support polygon differs")
        area = np.prod(np.ptp(polygon[:, :2], axis=0))
        require(abs(area - support.finite_scalar(proof["bearing_area_mm2"])) <= POINT_TOL, "finished support area differs")


def verify_maps(field, q, layout, shafts, integrated):
    mapping = field["finite_kinematic_map"]
    require(mapping["ndof"] == len(q), "finite map and q dimensions differ")
    mechanical, panels = mapping["mechanical_bodies"], mapping["panels"]
    spans = member_geometry.read_member_span_geometry()
    fittings = {r["angle_id"]: r for r in layout["raw_fittings"]}
    shaft_by_id = {r["body"]: r for r in shafts}
    require(set(mechanical) == set(spans) | set(fittings) | set(shaft_by_id) and len(mechanical) == 126,
            "complete 20 timber, 36 fitting, 70 shaft maps required")
    all_indices = []
    for name, row in mechanical.items():
        centers = array(row["node_reference_centers_xyz_mm"])
        indices = np.asarray(row["node_dof_indices"])
        require(centers.ndim == 2 and centers.shape[1] == 3 and indices.shape == (len(centers), 6)
                and np.issubdtype(indices.dtype, np.integer), "six full finite DOFs per mechanical node required")
        all_indices.extend(indices.ravel().tolist())
        basis = array(row["storage_basis_columns_xyz"], (3, 3))
        if name in fittings:
            require(row["kind"] == "fitting" and row["flange_node_map"] == {"beam": 0, "post": 1}, "fitting flange node identity differs")
            require(row.get("gravity_port") == "mean of two exact flange rigid-arm ports", "fitting gravity mean-port derivative basis differs")
            holes = {r["flange"]: r["entry_xyz_mm"] for r in fittings[name]["holes"]}
            close(centers, [holes["beam"], holes["post"]], POINT_TOL, "fitting reference port differs")
            close(basis, np.eye(3), 1e-10, "fitting storage basis differs")
            continue
        stations = array(row["reference_stations_mm"])
        require(stations.shape == (len(centers),) and len(stations) >= 2 and np.all(np.diff(stations) > 1e-7),
                "complete ordered finite member stations required")
        if name in spans:
            saved = spans[name]
            start = array(saved["start_xyz_mm"])
            axis = array(saved["basis_grain_u_v_xyz"][0])
            bounds = [0., float(np.linalg.norm(array(saved["end_xyz_mm"]) - start))]
            require(row["kind"] == "timber", "timber map kind differs")
            close(basis, np.eye(3), 1e-10, "timber storage basis differs")
        else:
            shaft = shaft_by_id[name]
            start, axis, bounds = shaft["point"], shaft["basis"][0], shaft["shaft_interval_mm"]
            require(row["kind"] == "shaft", "shaft map kind differs")
            close(basis, np.asarray(shaft["basis"]).T, 1e-8, "shaft storage basis differs")
            events = {s for surface in shaft["surfaces"] for s in (*surface["interval_mm"], np.mean(surface["interval_mm"]))}
            events.update(s for end in shaft["ends"] for s in (end["support_s_mm"], end["pressure_face_s_mm"]))
            require(all(np.min(abs(stations - s)) <= POINT_TOL for s in events), "shaft map omits an actual bearing/capture mesh event")
        close(row["reference_start_xyz_mm"], start, POINT_TOL, "member map reference start differs")
        close(row["reference_axis_xyz"], axis, 1e-9, "member map reference axis differs")
        close(stations[[0, -1]], bounds, POINT_TOL, "member map omits or extends physical span")
        close(centers, np.asarray(start) + stations[:, None] * axis, POINT_TOL, "member node leaves authenticated reference centerline")
    geometry = {r["panel"]: r for r in json.loads(panel_datums.ASSESSMENT.read_text())["panel_geometry"]}
    datums = json.loads(panel_datums.DATUMS.read_text())
    require(set(panels) == set(panel_method.PANELS), "six finite panel maps required")
    prepared = {}
    for name, row in panels.items():
        source, datum = geometry[name], datums[name]
        close(row["origin_xyz_mm"], datum["origin_xyz_mm"], 1e-8, "panel origin differs")
        close(row["axes_columns_xyz"], datum["local_axes_columns_xyz"], 1e-10, "panel horizontal strength-axis embedding differs")
        close([row["basis_width_mm"], row["basis_height_mm"]], [source["width_mm"], source["height_mm"]], 1e-8, "panel outlines differ")
        require(row["basis_order"] == field["parameters"]["panel_intervals"] + 3, "panel basis discretization differs")
        basis = panel_method.SheetBasis(row["basis_width_mm"], row["basis_height_mm"], row["basis_order"] - 3)
        close(row["basis_knots_normalized"], basis.knots, 1e-15, "panel knots differ")
        indices = np.asarray(row["global_dof_indices"])
        require(indices.shape == (3 * basis.size,) and np.issubdtype(indices.dtype, np.integer), "complete panel coefficient indices required")
        all_indices.extend(indices.tolist())
        require(abs(row["thickness_mm"] - panel_method.CAT) < 1e-9 and row["twist_scale"] == 1., "recorded CAT plywood constitutive scenario required")
        geo = {"name": name, "origin": array(row["origin_xyz_mm"]), "axes": array(row["axes_columns_xyz"]),
               "inward": -array(row["axes_columns_xyz"])[:, 2], "front_height": source["front_height_mm"]}
        holes = [{**r, "xy_mm": panel_method.local_xy(r["start_xyz_mm"], geo).tolist()}
                 for r in integrated["panel_machining"]["features"] if r["panel"] == name]
        panel = {"geometry": geo, "basis": basis, "holes": holes, "thickness": row["thickness_mm"], "twist_scale": row["twist_scale"]}
        panel_loads.mass_only_quadrature(panel)
        close(row["mass_coefficient_row"], panel["mass_row"], 1e-12, "finite panel mass coefficient measure differs")
        close(row["mass_reference_xy_mm"], panel["mass_weights"] @ panel["mass_xy"], 1e-8, "finite panel mass centroid differs")
        prepared[name] = panel
    require(len(all_indices) == len(q) and set(all_indices) == set(range(len(q))), "finite full DOF map duplicates, omits, or constrains a coordinate")
    return prepared, datums


def descriptor_expected(field, contact, layout, shafts, panels, datums):
    """Build each physical path from issued geometry; no linear B/K is built."""
    params, result = field["parameters"], {}
    values = [params[key] for key in ("wood_radial_foundation_n_mm2", "plate_radial_foundation_n_mm2",
        "end_capture_stiffness_n_mm", "Hillman_axial_lateral_stiffness_n_mm", "flange_corner_contact_n_mm",
        "panel_foundation_n_mm3", "floor_corner_contact_n_mm", "floor_xy_penalty_n_mm_per_corner")]
    require(np.isfinite(values).all() and min(values) > 0., "all declared physical path stiffness scenarios must be positive and finite")

    def add(identity, kind, first, second, p1, n, owner, ka=0., kl=0., gap=0., sign=1., p2=None,
            first_flange=None, second_flange=None, ring=False, extra=None):
        p2 = p1 if p2 is None else p2
        value = {"id": identity, "kind": kind, "first": first, "second": second,
            "reference_first_point_xyz_mm": np.asarray(p1).tolist(), "reference_second_point_xyz_mm": np.asarray(p2).tolist(),
            "reference_director_xyz": np.asarray(n).tolist(), "director_owner": owner,
            "first_port_kind": "projected_ring" if ring else "point", "axial_sign": sign,
            "reference_axial_projection_mm": float(sign * (np.asarray(n) @ (np.asarray(p1) - p2))),
            "axial_stiffness_n_mm": float(ka), "lateral_stiffness_n_mm": float(kl), "radial_gap_mm": float(gap),
            "axial_tension_only": True}
        value.update(first_flange=first_flange, second_flange=second_flange, director_flange=second_flange)
        if extra:
            value.update(extra)
        require(identity not in result, "duplicate source finite path")
        result[identity] = value

    for shaft in shafts:
        p, g = shaft["point"], shaft["basis"][0]
        for i, surface in enumerate(shaft["surfaces"]):
            a, b = surface["interval_mm"]
            foundation = params["wood_radial_foundation_n_mm2"] if surface["kind"] == "wood" else params["plate_radial_foundation_n_mm2"]
            for quad, xi in enumerate((-1 / np.sqrt(3), 1 / np.sqrt(3))):
                point = p + g * (.5 * (a + b) + .5 * (b - a) * xi)
                add(shaft["axis_id"] + f"/bearing-{i}-{quad}", "common_shaft_bearing", shaft["body"], surface["host"], point, g,
                    surface["host"], kl=foundation * .5 * (b - a), gap=.5 * (shaft["bore_diameter_mm"] - shaft["diameter_mm"]),
                    second_flange=surface.get("flange"), extra={"source_descriptor": {
                        "axis_id": shaft["axis_id"], "surface": surface, "surface_index": i, "quad_index": quad,
                        "axis_station_mm": float(.5 * (a + b) + .5 * (b - a) * xi), "weight_length_mm": float(.5 * (b - a))}})
        for end in shaft["ends"]:
            add(shaft["axis_id"] + "/" + end["end"] + "-capture", "shaft_end_capture", shaft["body"], end["host"],
                p + g * end["pressure_face_s_mm"], end["direction_on_shaft_xyz"], end["host"],
                ka=params["end_capture_stiffness_n_mm"], sign=-1., p2=p + g * end["support_s_mm"], second_flange=end.get("flange"),
                extra={"source_descriptor": {"axis_id": shaft["axis_id"], "end": end}})
    for fitting in layout["raw_fittings"]:
        o, u, v, w = [array(fitting[k]) for k in ("origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz")]
        for flange, host, along, normal, length in (("beam", fitting["beam"], u, v, 104.775),
                ("post", fitting["post"], v, u, 41.275 if fitting["angle_id"].startswith("B103ZN") else 88.9)):
            for corner, (station, width) in enumerate((s, width) for s in (5.55625, length) for width in (-20.6375, 20.6375)):
                add(fitting["angle_id"] + "/" + flange + f"/contact-{corner}", "flange_contact", fitting["angle_id"], host,
                    o + along * station + w * width, normal, host, ka=params["flange_corner_contact_n_mm"], sign=-1., first_flange=flange,
                    extra={"source_descriptor": {"angle_id": fitting["angle_id"], "flange": flange}})
    for screw in layout["screw_axes"]:
        inward = array(screw["direction_xyz"]); inward /= np.linalg.norm(inward)
        point = array(screw["origin_xyz_mm"]) + inward * panel_method.CAT / 2
        add(screw["axis_id"], "panel_screw", screw["panel"], screw["receiver"], point, -inward, screw["panel"],
            ka=params["Hillman_axial_lateral_stiffness_n_mm"], kl=params["Hillman_axial_lateral_stiffness_n_mm"], ring=True,
            extra={"source_descriptor": {"axis_id": screw["axis_id"]}})
    require(params["panel_intervals"] == 8 and params["foundation_port_cell_mm"] == 70., "initial admitted panel contact70/interval8 source required")
    with np.load(panel_loads.OPERATORS, allow_pickle=False) as operators:
        for name, panel in panels.items():
            xy, area = operators[name + "/contact_xy"], operators[name + "/contact_area"]
            owners = datums[name]["contact_receivers"]
            require(len(xy) == len(area) == len(owners), "saved panel contact source census differs")
            for i, (point, weight, owner) in enumerate(zip(xy, area, owners, strict=True)):
                geo = panel["geometry"]
                world = geo["origin"] + geo["axes"][:, :2] @ point - geo["axes"][:, 2] * panel_method.CAT / 2
                close(world, operators[name + "/contact_points_xyz_mm"][i], 1e-7, "saved panel contact datum differs")
                add(name + f"/compression-{i}", "panel_contact", name, owner, world, geo["axes"][:, 2], name,
                    ka=params["panel_foundation_n_mm3"] * weight, sign=-1.)
    for host, points in contact["finished_floor_footprints"].items():
        for i, point in enumerate(points):
            normal_id = host + f"/floor-{i}"
            add(normal_id, "floor_normal", host, "floor", point, [0., 0., 1.], "floor",
                ka=params["floor_corner_contact_n_mm"], sign=-1.)
            add(normal_id + "/finite-no-slip-xy", "floor_tangent_xy", host, "floor", point, [0., 0., 1.], "floor",
                kl=params["floor_xy_penalty_n_mm_per_corner"],
                extra={"floor_support_id": normal_id, "normal_contact_id": normal_id,
                    "source_component_ids": [normal_id + "/no-slip-0", normal_id + "/no-slip-1"]})
    require(params["floor_xy_penalty_n_mm_per_corner"] * 4 == params["floor_no_slip_xy_penalty_n_mm_per_foot"],
            "own corner and per-foot tangent penalties differ")
    return result


def field_hashes(field, payload=None):
    return {"field_sha256": hashlib.sha256(payload).hexdigest() if payload is not None else None,
            "field_hash_basis": "exact supplied JSON bytes" if payload is not None else "parsed dict; no original byte hash claimed",
            "field_canonical_sha256": canonical_sha(field)}


def verify_descriptor_fields(row, expected):
    for key, value in expected.items():
        if isinstance(value, dict):
            require(isinstance(row.get(key), dict), "finite source descriptor metadata absent")
            verify_descriptor_fields(row[key], value)
        elif isinstance(value, list) and value and isinstance(value[0], str):
            require(row.get(key) == value, "finite source component identity differs")
        elif isinstance(value, (list, tuple, np.ndarray)):
            close(row.get(key), value, POINT_TOL if "point" in key else 1e-9, "finite descriptor geometry differs: " + key)
        elif isinstance(value, (float, int)) and not isinstance(value, bool):
            require(abs(support.finite_scalar(row.get(key)) - value) <= 1e-8 * max(1., abs(value)), "finite descriptor law differs: " + key)
        else:
            require(row.get(key) == value, "finite descriptor identity differs: " + key)


def replay_constitutive(row, p1, p2, normal, enabled=True):
    """Direct derivative in physical space, independent of connector jets."""
    n, d = array(normal, (3,)), array(p1, (3,)) - array(p2, (3,))
    require(abs(np.linalg.norm(n) - 1.) < 1e-8, "unit current material director required")
    projection = float(n @ d)
    sign = row["axial_sign"]
    extension = sign * projection - row["reference_axial_projection_mm"]
    ka, kl, gap = row["axial_stiffness_n_mm"], row["lateral_stiffness_n_mm"], row["radial_gap_mm"]
    require(np.isfinite([ka, kl, gap, extension]).all() and min(ka, kl, gap) >= 0., "finite nonnegative current spring law required")
    if not enabled:
        ka = kl = 0.
    active_axial = extension if not row["axial_tension_only"] else max(extension, 0.)
    tension = ka * active_axial
    radial = d - projection * n
    radius = float(np.linalg.norm(radial))
    radial_force = kl * (1 - gap / radius) * radial if radius > gap else np.zeros(3)
    force = -sign * tension * n - radial_force
    derivative = sign * tension * d - projection * radial_force - d * float(n @ radial_force)
    moment = -np.cross(n, derivative)
    energy = .5 * ka * active_axial**2 + .5 * kl * max(radius - gap, 0.)**2
    return force, moment, extension, radius, tension, energy


def verify_current_actions(field, q, expected):
    descriptors = unique(field["reference_interaction_descriptors"])
    actions = unique(field["finite_interaction_actions"])
    require(set(descriptors) == set(expected) == set(actions), "finite current path census differs")
    identities(field, list(actions.values()))
    disabled = field["response"]["disabled_floor_support_ids"]
    require(len(set(disabled)) == len(disabled), "duplicate disabled floor corner")
    normal_ids = {k for k, r in expected.items() if r["kind"] == "floor_normal"}
    require(set(disabled) <= normal_ids and len(normal_ids) == 32, "disabled floor support must be one actual normal corner")
    normal_forces, maximum_pair_moment = {}, 0.
    mapping = field["finite_kinematic_map"]
    for key, source in expected.items():
        descriptor, row = descriptors[key], actions[key]
        verify_descriptor_fields(descriptor, source)
        verify_descriptor_fields(row, source)
        p1 = finite.current_pose_from_map(mapping, source["first"], source["reference_first_point_xyz_mm"], q,
                flange=source.get("first_flange"), projected_ring=source["first_port_kind"] == "projected_ring")["position_xyz_mm"]
        p2 = finite.current_pose_from_map(mapping, source["second"], source["reference_second_point_xyz_mm"], q,
                flange=source.get("second_flange"))["position_xyz_mm"]
        owner = source["director_owner"]
        director_point = source["reference_first_point_xyz_mm"] if owner == source["first"] else source["reference_second_point_xyz_mm"]
        n = finite.current_pose_from_map(mapping, owner, director_point, q, flange=source.get("director_flange"),
                projected_ring=owner == source["first"] and source["first_port_kind"] == "projected_ring",
                reference_director=source["reference_director_xyz"])["current_vector_xyz"]
        close(row["point_on_first_xyz_mm"], p1, POINT_TOL, "current first action port differs")
        close(row["point_on_second_xyz_mm"], p2, POINT_TOL, "current second action port differs")
        close(row["current_director_xyz"], n, 1e-8, "current director transport differs")
        enabled = not (source["kind"] == "floor_tangent_xy" and source["floor_support_id"] in disabled)
        require(row.get("interaction_enabled") is enabled, "same-state current interaction activation differs")
        force, moment, extension, radius, tension, energy = replay_constitutive(source, p1, p2, n, enabled)
        close(row["force_on_first_xyz_n"], force, FORCE_TOL, "current physical force differs from source spring law")
        close(row["force_on_second_xyz_n"], -force, FORCE_TOL, "current paired force dual differs")
        first_m = moment if owner == source["first"] else np.zeros(3)
        second_m = moment if owner == source["second"] else np.zeros(3)
        close(row["moment_on_first_at_current_point_xyz_nmm"], first_m, MOMENT_ALIAS_TOL, "current first free spatial couple differs")
        close(row["moment_on_second_at_current_point_xyz_nmm"], second_m, MOMENT_ALIAS_TOL, "current second free spatial couple differs")
        close(row["moment_on_director_owner_xyz_nmm"], moment, MOMENT_ALIAS_TOL, "material director couple differs")
        for fieldname, value in (("signed_axial_extension_mm", extension), ("radial_distance_mm", radius),
                ("axial_scalar_force_n", tension), ("energy_nmm", energy)):
            require(abs(support.finite_scalar(row[fieldname]) - value) <= max(FORCE_TOL, abs(value) * 1e-9), "current constitutive scalar differs")
        residual = np.cross(p1 - p2, force) + first_m + second_m
        close(row["pair_spatial_moment_residual_nmm"], residual, MOMENT_ALIAS_TOL, "current pair moment alias differs")
        require(np.linalg.norm(residual) <= MOMENT_ALIAS_TOL, "current internal pair fails spatial moment closure")
        maximum_pair_moment = max(maximum_pair_moment, float(np.linalg.norm(residual)))
        if source["kind"] == "floor_normal":
            normal_forces[key] = tension
    require(set(disabled) == {key for key, n in normal_forces.items() if n <= 1e-7}, "own current corner normal and XY activation disagree")
    if "floor_normal_reactions_n" in field["response"]:
        require(set(field["response"]["floor_normal_reactions_n"]) == normal_ids, "floor normal summary census differs")
        for key, value in normal_forces.items():
            require(abs(field["response"]["floor_normal_reactions_n"][key] - value) <= FORCE_TOL, "floor normal summary differs")
    return {"counts": dict(Counter(r["kind"] for r in actions.values())), "maximum_current_pair_moment_residual_nmm": maximum_pair_moment,
            "disabled_floor_support_ids": disabled, "own_corner_activation_authenticated": True}


def light_panel_adapter(panel, row, ndof):
    """Frozen position/J routines only; skip energy-group and stiffness setup."""
    adapter = panel_finite.FinitePanelAdapter.__new__(panel_finite.FinitePanelAdapter)
    adapter.panel, adapter.geometry, adapter.basis = panel, panel["geometry"], panel["basis"]
    adapter.local_size = 3 * panel["basis"].size
    adapter.indices, adapter.ndof = np.asarray(row["global_dof_indices"]), ndof
    adapter.origin, adapter.axes = panel["geometry"]["origin"], panel["geometry"]["axes"]
    adapter.source_sha256 = dict(panel_finite.BASE_PINS)
    adapter.measure = {"xy_mm": panel["mass_xy"], "mass_weights": panel["mass_weights"], "mass_row": panel["mass_row"]}
    return adapter


def expected_finite_loads(field, source_loads):
    """Expand the authenticated wood source into the saved discrete load model."""
    result = []
    mapping = field["finite_kinematic_map"]
    for load in source_loads:
        body = load["body"]
        row = mapping["mechanical_bodies"].get(body)
        if load["id"].startswith("self-weight/") and row and row["kind"] == "timber":
            axis, start, stations = array(row["reference_axis_xyz"]), array(row["reference_start_xyz_mm"]), array(row["reference_stations_mm"])
            low, high = stations[[0, -1]]
            center = array(load["point_xyz_mm"])
            center_s = float((center - start) @ axis)
            off = center - axis * center_s
            beta = 12 * (center_s - .5 * (low + high)) / (high - low)**2
            require(min(1 + beta * (low - .5 * (low + high)), 1 + beta * (high - .5 * (low + high))) >= -1e-10,
                    "negative affine source timber gravity measure")
            for i, (a, b) in enumerate(pairwise(stations)):
                for j, xi in enumerate((-1 / np.sqrt(3), 1 / np.sqrt(3))):
                    station = .5 * (a + b) + .5 * (b - a) * xi
                    fraction = .5 * (b - a) / (high - low) * (1 + beta * (station - .5 * (low + high)))
                    result.append({**load, "id": load["id"] + f"/span-{i}/gauss-{j}", "source_load_id": load["id"],
                        "point_xyz_mm": (off + axis * station).tolist(), "force_xyz_n": (array(load["force_xyz_n"]) * fraction).tolist()})
        else:
            result.append({**load, "source_load_id": load["id"]})
    return result


def verify_current_loads(field, q, source_loads, panels, integrated):
    mapping = field["finite_kinematic_map"]
    expected = unique(expected_finite_loads(field, source_loads))
    recorded = unique(field["finite_body_applied_loads"])
    require(set(recorded) == set(expected), "finite source load census differs; gravity may not be omitted or duplicated")
    identities(field, list(recorded.values()))
    for key, load in expected.items():
        row, body = recorded[key], load["body"]
        require(row["body"] == body, "current source load owner differs")
        if body not in panels:
            require(row.get("source_load_id") == load["source_load_id"], "finite mechanical source load identity differs")
        close(row["force_xyz_n"], load["force_xyz_n"], 1e-7, "current world load differs from frozen source")
        close(row["point_xyz_mm"], load["point_xyz_mm"], POINT_TOL, "original source load datum differs")
        close(row["free_spatial_moment_xyz_nmm"], [0., 0., 0.], 1e-10, "source point gravity has no free couple")
        uniform = body in panels and (key.startswith("self-weight/") or
                    (field["accessory_placement"] == "proportional-six-panel-sensitivity" and key.startswith("accessory/")))
        if uniform:
            panel, pmap = panels[body], mapping["panels"][body]
            geo, basis = panel["geometry"], panel["basis"]
            xy = panel["mass_weights"] @ panel["mass_xy"]
            reference = geo["origin"] + geo["axes"] @ np.r_[xy, 0.]
            local = q[np.asarray(pmap["global_dof_indices"])].reshape(3, basis.size)
            current = reference + geo["axes"] @ (local @ panel["mass_row"])
        else:
            reference = array(load["point_xyz_mm"])
            current = finite.current_pose_from_map(mapping, body, reference, q, allow_edge_extension=key.startswith("accessory/"))["position_xyz_mm"]
        close(row["reference_point_xyz_mm"], reference, POINT_TOL, "finite load reference port differs")
        close(row["current_point_xyz_mm"], current, POINT_TOL, "current source load point differs")
        if body in panels:
            close(row["source_reference_point_xyz_mm"], load["point_xyz_mm"], POINT_TOL, "panel source centroid metadata differs")
    corrections = unique(field["panel_generalized_load_corrections"])
    expected_ids = {name + "/" + kind for name in panels for kind in ("retained_rigid_RHS", "reference_port_alignment")}
    require(set(corrections) == expected_ids, "both generalized panel correction vectors required for all six panels")
    identities(field, list(corrections.values()))
    case = next(r for r in panel_method.load_cases(integrated) if r["id"] == ("permanent" if field["case_id"] == "gravity-only" else field["case_id"]))
    accessory = "original_top" if field["accessory_placement"] == "retained-original-top-hold" else "proportional"
    maximum_correction_wrench = 0.
    for name, panel in panels.items():
        pmap = mapping["panels"][name]
        adapter = light_panel_adapter(panel, pmap, len(q))
        owned = [r for r in source_loads if r["body"] == name]
        # Only frozen source load/basis/J routines run; no panel energy or K.
        loads = panel_finite.FinitePanelLoads(adapter, case, integrated, accessory, owned)
        rigid = adapter.current_rigid_modes(q, REFERENCE)
        for kind, force in (("retained_rigid_RHS", loads.retained_rigid_correction_n),
                            ("reference_port_alignment", loads.reference_port_alignment_correction_n)):
            row = corrections[name + "/" + kind]
            require(row["panel"] == name and row["kind"] == kind and row["global_coefficient_indices"] == pmap["global_dof_indices"],
                    "panel generalized correction ownership/index identity differs")
            close(row["local_generalized_force_n"], force, 1e-9, "panel generalized correction differs from retained source RHS")
            close(row["wrench_reference_xyz_mm"], REFERENCE, 1e-10, "panel generalized correction wrench reference differs")
            wrench = rigid.T @ force
            close(row["current_equivalent_rigid_wrench_n_nmm"], wrench, MOMENT_ALIAS_TOL, "current generalized correction wrench differs")
            require(row["physical_point_forces_or_pressure_representation"] is False, "generalized correction cannot invent a physical traction")
            maximum_correction_wrench = max(maximum_correction_wrench, float(np.linalg.norm(wrench)))
    roles = [r for r in recorded.values() if r["id"].startswith("physical-bolt-metal/")]
    require(len(roles) == 350 and all(r["body"].startswith("shaft/") for r in roles), "350 physical metal roles must belong once to their own 70 shafts")
    return {"source_load_count_before_timber_quadrature": len(source_loads), "exported_discrete_load_count": len(recorded),
            "own_shaft_metal_roles": 350, "generalized_panel_corrections": 12,
            "maximum_current_generalized_correction_wrench_norm": maximum_correction_wrench}


def current_balances(body_ids, loads, actions, corrections, reference=REFERENCE):
    residuals = {name: np.zeros(6) for name in body_ids}
    applied, floor = np.zeros(6), np.zeros(6)
    for row in loads:
        value = arithmetic.wrench(row["force_xyz_n"], row["current_point_xyz_mm"], reference, row["free_spatial_moment_xyz_nmm"])
        residuals[row["body"]] += value; applied += value
    for row in corrections:
        require(np.linalg.norm(array(row["wrench_reference_xyz_mm"]) - reference) < 1e-9, "generalized wrench reference differs")
        value = array(row["current_equivalent_rigid_wrench_n_nmm"], (6,))
        residuals[row["panel"]] += value; applied += value
    for row in actions:
        for side in ("first", "second"):
            value = arithmetic.wrench(row["force_on_" + side + "_xyz_n"], row["point_on_" + side + "_xyz_mm"], reference,
                                     row["moment_on_" + side + "_at_current_point_xyz_nmm"])
            if row[side] != "floor":
                residuals[row[side]] += value
                if row["second"] == "floor":
                    floor += value
    return residuals, applied, applied + floor


def verify_equilibrium(field, bodies):
    residuals, applied, global_value = current_balances(bodies, field["finite_body_applied_loads"],
            field["finite_interaction_actions"], field["panel_generalized_load_corrections"])
    force = max(np.linalg.norm(r[:3]) for r in [*residuals.values(), global_value])
    origin_global_moment = global_value[3:] + np.cross(REFERENCE, global_value[:3])
    moment = max(*[np.linalg.norm(r[3:]) for r in residuals.values()], np.linalg.norm(origin_global_moment))
    if "body_equilibrium_residuals" in field:
        stored = unique(field["body_equilibrium_residuals"], "body")
        require(set(stored) == set(residuals), "stored finite body residual census differs")
        for name, value in residuals.items():
            close(stored[name]["force_xyz_n"], value[:3], FORCE_TOL, "stored current body force residual differs")
            close(stored[name]["moment_about_reference_xyz_nmm"], value[3:], MOMENT_ALIAS_TOL, "stored current body moment residual differs")
    require(force <= 1e-4 and moment <= .1, "independent 132 body/global current wrench closure fails")
    return {"all_132_current_body_and_global_checks_pass": True, "body_count": len(residuals),
            "maximum_body_or_global_force_norm_n": float(force), "maximum_body_or_global_moment_norm_nmm": float(moment),
            "force_tolerance_n": 1e-4, "moment_tolerance_nmm": .1, "body_wrench_reference_xyz_mm": REFERENCE.tolist(),
            "physical_plus_generalized_applied_wrench_n_nmm": applied.tolist(), "global_current_residual_about_reference_n_nmm": global_value.tolist()}


def audit_finite_state(path_or_dict):
    """Admit a path, immutable bytes, or dict; raw and canonical hashes differ."""
    require(support.digest(Path(__file__)) == LOADED_PRODUCER_SHA256, "finite admission producer changed after loading")
    path = None if isinstance(path_or_dict, (dict, bytes)) else Path(path_or_dict)
    payload = path.read_bytes() if path else path_or_dict if isinstance(path_or_dict, bytes) else None
    field = json.loads(payload) if payload is not None else path_or_dict
    q = verify_header(field)
    contact, cache, unit, layout, takeoff, integrated, pins = source_receipt(field)
    verify_floor_proofs(field, contact, cache)
    bodies, loads, _ = common.expected_common_loads(field, cache, takeoff, integrated)
    common.verify_load_table(field["body_reference_applied_loads"], loads)
    recorded = field["body_identities"]
    names = [r["id"] if isinstance(r, dict) else r for r in recorded]
    require(len(names) == 132 and len(set(names)) == 132 and set(names) == set(bodies), "132 unique actual body identities required")
    shafts = common_method.shaft_inputs(layout, unit, cache)
    panels, datums = verify_maps(field, q, layout, shafts, integrated)
    expected = descriptor_expected(field, contact, layout, shafts, panels, datums)
    action_receipt = verify_current_actions(field, q, expected)
    load_receipt = verify_current_loads(field, q, loads, panels, integrated)
    equilibrium = verify_equilibrium(field, bodies)
    require(path is None or path.read_bytes() == payload, "finite source field changed during independent admission")
    for name, digest in pins.items():
        require(support.digest(ROOT / name) == digest, "finite audit source changed while checking: " + name)
    require(support.digest(Path(__file__)) == LOADED_PRODUCER_SHA256, "finite admission producer changed while checking")
    pins[str(Path(__file__).relative_to(ROOT))] = LOADED_PRODUCER_SHA256
    return {"schema": "thin_bolted_independent_finite_admission/v1", "state_id": field["state_id"], "case_id": field["case_id"],
            "accessory_placement": field["accessory_placement"], **field_hashes(field, payload), "source_sha256": pins, SUCCESS: True,
            "current_action_replay": action_receipt, "source_current_load_replay": load_receipt, "equilibrium": equilibrium,
            "native_CAD_K_or_response_solves_performed": False, "physical_stiffness_demand_bounds_or_strength_established": False,
            "full_original_generalized_gradient_is_reported_by_source_bound_producer_not_independently_resolved": True,
            "release": {k: False for k in field["release"]}}

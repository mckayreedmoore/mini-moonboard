"""Direct six-duty center cross-dowel viewer trial; no joint or drill release."""

import json

import cadquery as cq

from mini_moonboard.box_frame import Connection
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import center_posts_outward_owner_layout as posts
from scripts import owner_barrel_coordinates as coordinates
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger

N, T = coordinates.N, coordinates.T

SOURCE_ID = "owner-barrel-center-six-direct-layout-v1"
STATIONS = (
    "clip_split_header_center_left",
    "clip_split_header_center_right",
    "clip_split_base_center_left",
    "clip_split_base_center_right",
    "clip_horizontal_bottom_left_2",
    "clip_horizontal_bottom_right_1",
)
BARREL_LENGTH_MM = hardware.BARREL_LENGTH_MM
BARREL_OD_MM = hardware.BARREL_OD_MM
BOLT_LENGTH_MM = hardware.BOLT_LENGTH_MM
WASHER_THICKNESS_MM = hardware.WASHER_THICKNESS_SENSITIVITY_MM
AXIS_OFFSET_SENSITIVITY_MM = hardware.AXIS_OFFSET_SENSITIVITY_MM
THREAD_AXIS_OFFSET_MM = 8.001  # One assumed pose, not a Hillman specification.
BARREL_AXIS_DEPTH_MM = 19.05
BARREL_RECESS_MM = BARREL_AXIS_DEPTH_MM - THREAD_AXIS_OFFSET_MM
BORE_DIAMETER_MM = 7.5
WASHER_DIAMETER_MM = 25.4  # Diagnostic envelope, not controlled retail OD.
HEAD_DIAMETER_MM = 11.0
TOOL_DIAMETER_MM = 20.0
TOOL_LENGTH_MM = 40.0
VOLUME_TOL_MM3 = 1.0
REVISED_SOURCE_ID = "owner-barrel-center-principal-viewer-revision-v1"
REVISED_PRINCIPAL_ROWS_Y_MM = (-162.433333, -138.166667)
REVISED_PRINCIPAL_WASHER_OD_MM = 22.0  # Trial envelope, not a selected product.
REVISED_PRINCIPAL_BOLT_LENGTH_MM = 4.0 * 25.4  # Nominal full-thread candidate.


def _cylinder(point, axis, length, diameter):
    return cq.Solid.makeCylinder(
        diameter / 2, length, cq.Vector(*point), cq.Vector(*axis)
    )


def _add(point, axis, distance):
    return tuple(point[i] + axis[i] * distance for i in range(3))


def _yz(t, n):
    return (t * T[0] + n * N[0], t * T[1] + n * N[1])


def _local_bounds(shape):
    return coordinates.local_bounds(shape)


def _finite_hits(shape, obstacles):
    return {
        name: round(volume, 6)
        for name, other in obstacles.items()
        if (volume := protected._volume(shape, other)) > VOLUME_TOL_MM3
    }


def _wood():
    source = variant(KERF_RIGHT)
    wood = {part.name: part.shape for part in source.uncut_wood_parts()}
    if len(wood) != len(tuple(source.uncut_wood_parts())):
        raise ValueError("Kerf-right whole timber inventory changed")
    layout = posts.build_layout()
    if layout["post_bounds_x_mm"] != {
        "left": [-199.05, -160.95],
        "right": [160.95, 199.05],
    }:
        raise ValueError("Approved original-width X±180 post pose changed")
    for side in ("left", "right"):
        name = f"base_post_center_{side}"
        wood[name] = wood[name].translate(
            cq.Vector(layout["post_shift_x_mm"][side], 0, 0)
        )
        x0, x1 = layout["backer_bounds_x_mm"][side]
        wood[f"inner_kicker_backer_{side}"] = cq.Solid.makeBox(
            x1 - x0,
            posts.BACKER_FRONT_Y_MM - posts.BACKER_REAR_Y_MM,
            posts.BACKER_TOP_Z_MM,
            cq.Vector(x0, posts.BACKER_REAR_Y_MM, 0),
        )
    return source, wood, layout


def _station_spec(station, wood):
    side = "left" if station.endswith("left") or "_left_" in station else "right"
    sign = -1 if side == "left" else 1
    if station.startswith("clip_split_header_center_"):
        family = "post_header"
        receiver = f"base_post_center_{side}"
        header = "base_header"
        host = wood[receiver]
        hb = host.BoundingBox()
        bb = wood[header].BoundingBox()
        if abs(hb.zmax - bb.zmin) > 1e-5:
            raise ValueError(f"{station}: post/header butt changed")
        center_x = (hb.xmin + hb.xmax) / 2
        barrel_entry_x = hb.xmin if sign < 0 else hb.xmax
        barrel_axis = (float(-sign), 0.0, 0.0)
        seat_z, receiver_z = bb.zmax, 200.0
        rows = (-145.0, -95.0)
        specs = [
            {
                "bolt_seat": (center_x, y, seat_z),
                "bolt_axis": (0.0, 0.0, -1.0),
                "barrel_entry": (barrel_entry_x, y, receiver_z),
                "barrel_axis": barrel_axis,
                "header_length": bb.zlen,
                "receiver_length": hb.zmax - receiver_z,
                "barrel_host": receiver,
                "bolt_hosts": (header, receiver),
                "butt": (host, wood[header], (0.0, 0.0, 1.0)),
            }
            for y in rows
        ]
        y_margin = min(y - hb.ymin - WASHER_DIAMETER_MM / 2 for y in rows)
    elif station.startswith("clip_split_base_center_"):
        family = "principal_header"
        receiver = f"base_principal_center_{side}"
        header = "base_header"
        host = wood[receiver]
        hb = host.BoundingBox()
        bb = wood[header].BoundingBox()
        if abs(hb.zmin - bb.zmax) > 1e-5:
            raise ValueError(f"{station}: principal/header butt changed")
        center_x = (hb.xmin + hb.xmax) / 2
        barrel_entry_x = hb.xmax if sign < 0 else hb.xmin
        barrel_axis = (float(sign), 0.0, 0.0)
        seat_z, receiver_z = bb.zmin, 305.0
        rows = (-163.0, -137.6)
        specs = [
            {
                "bolt_seat": (center_x, y, seat_z),
                "bolt_axis": (0.0, 0.0, 1.0),
                "barrel_entry": (barrel_entry_x, y, receiver_z),
                "barrel_axis": barrel_axis,
                "header_length": bb.zlen,
                "receiver_length": receiver_z - hb.zmin,
                "barrel_host": receiver,
                "bolt_hosts": (header, receiver),
                "butt": (host, wood[header], (0.0, 0.0, -1.0)),
            }
            for y in rows
        ]
        y_margin = min(
            rows[0] - bb.ymin - WASHER_DIAMETER_MM / 2,
            posts.BACKER_REAR_Y_MM - rows[1] - WASHER_DIAMETER_MM / 2,
        )
    else:
        family = "bottom_center"
        receiver = f"base_rail_bottom_{side}"
        principal = f"base_principal_center_{side}"
        rb = wood[receiver].BoundingBox()
        pb = wood[principal].BoundingBox()
        butt_x = rb.xmax if sign < 0 else rb.xmin
        principal_butt_x = pb.xmin if sign < 0 else pb.xmax
        if abs(butt_x - principal_butt_x) > 1e-5:
            raise ValueError(f"{station}: rail/principal butt changed")
        rail_local = _local_bounds(wood[receiver])
        entry_t = rail_local["t"][0]
        thread_t = entry_t + BARREL_AXIS_DEPTH_MM
        receiver_x = butt_x + sign * 70.0
        principal_outer_x = pb.xmax if sign < 0 else pb.xmin
        specs = []
        for n in (250.0, 310.0):
            y, z = _yz(thread_t, n)
            ey, ez = _yz(entry_t, n)
            specs.append(
                {
                    "bolt_seat": (principal_outer_x, y, z),
                    "bolt_axis": (float(sign), 0.0, 0.0),
                    "barrel_entry": (receiver_x, ey, ez),
                    "barrel_axis": (0.0, *T),
                    "header_length": pb.xlen,
                    "receiver_length": 70.0,
                    "barrel_host": receiver,
                    "bolt_hosts": (principal, receiver),
                    "butt": (
                        wood[receiver],
                        wood[principal],
                        (-float(sign), 0.0, 0.0),
                    ),
                }
            )
        y_margin = None
    return family, specs, y_margin


def _hardware(
    station,
    index,
    spec,
    *,
    bolt_length_mm=BOLT_LENGTH_MM,
    washer_diameter_mm=WASHER_DIAMETER_MM,
):
    name = f"barrel_center_{station}_{index}"
    seat = spec["bolt_seat"]
    bolt_axis = spec["bolt_axis"]
    entry = spec["barrel_entry"]
    barrel_axis = spec["barrel_axis"]
    cross_depth = BARREL_RECESS_MM + BARREL_LENGTH_MM
    body_start = _add(entry, barrel_axis, BARREL_RECESS_MM)
    thread_center = _add(entry, barrel_axis, BARREL_AXIS_DEPTH_MM)
    seat_to_axis = spec["header_length"] + spec["receiver_length"]
    expected = _add(seat, bolt_axis, seat_to_axis)
    if max(abs(a - b) for a, b in zip(expected, thread_center, strict=True)) > 1e-5:
        raise ValueError(f"{name}: bolt and barrel axes do not meet")
    body = _cylinder(body_start, barrel_axis, BARREL_LENGTH_MM, BARREL_OD_MM)
    cross_bore = _cylinder(entry, barrel_axis, cross_depth, BARREL_OD_MM)
    bolt_start = _add(seat, bolt_axis, -WASHER_THICKNESS_MM)
    shaft = _cylinder(bolt_start, bolt_axis, bolt_length_mm, hardware.THREAD_MAJOR_MM)
    bolt_bore = _cylinder(
        seat, bolt_axis, bolt_length_mm - WASHER_THICKNESS_MM, BORE_DIAMETER_MM
    )
    washer = _cylinder(bolt_start, bolt_axis, WASHER_THICKNESS_MM, washer_diameter_mm)
    head_start = _add(bolt_start, bolt_axis, -4.0)
    head = _cylinder(head_start, bolt_axis, 4.0, HEAD_DIAMETER_MM)
    bolt_tool = _cylinder(
        seat, tuple(-v for v in bolt_axis), TOOL_LENGTH_MM, TOOL_DIAMETER_MM
    )
    barrel_tool = _cylinder(
        entry, tuple(-v for v in barrel_axis), TOOL_LENGTH_MM, TOOL_DIAMETER_MM
    )
    features = {
        f"{name}/bolt_bore_full_nominal": bolt_bore,
        f"{name}/bolt_shaft_full_nominal": shaft,
        f"{name}/barrel_cross_bore": cross_bore,
        f"{name}/barrel_body": body,
        f"{name}/washer": washer,
        f"{name}/head": head,
        f"{name}/bolt_tool": bolt_tool,
        f"{name}/barrel_tool": barrel_tool,
    }
    return (
        name,
        features,
        {
            "bolt_seat_xyz_mm": list(seat),
            "bolt_axis_xyz": list(bolt_axis),
            "barrel_entry_xyz_mm": list(entry),
            "barrel_axis_xyz": list(barrel_axis),
            "thread_axis_xyz_mm": list(thread_center),
            "thread_axis_offset_assumed_mm": THREAD_AXIS_OFFSET_MM,
            "bolt_seat_to_thread_axis_mm": round(seat_to_axis, 6),
            "nominal_tip_beyond_thread_axis_mm": round(
                bolt_length_mm - WASHER_THICKNESS_MM - seat_to_axis, 6
            ),
            "bolt_barrel_intersection_mm3": round(
                protected._volume(bolt_bore, cross_bore), 6
            ),
            "barrel_body_cross_bore_fraction": round(
                protected._volume(body, cross_bore) / body.Volume(), 7
            ),
            "complete_thread_engagement_verified": False,
        },
    )


def build(wood=None):
    """Return direct CAD solids and finite stop-gate evidence for six duties."""
    source, default_wood, _layout = _wood()
    wood = default_wood if wood is None else wood
    if not set(default_wood) <= set(wood):
        raise ValueError("Center viewer missing whole-timber or kicker backer solids")
    for side, target in (("left", -180.0), ("right", 180.0)):
        bounds = wood[f"base_post_center_{side}"].BoundingBox()
        if abs((bounds.xmin + bounds.xmax) / 2 - target) > 1e-5:
            raise ValueError("Center viewer input must use approved X±180 post pose")
    duties = ledger.selected_duties()
    source_connections = tuple(source.connections())
    panel = tuple(source.panel_connections())
    frame = tuple(row for row in source_connections if row.kind == "bolt")
    removed = tuple(
        row
        for row in source_connections
        if any(row.name.startswith(station + "_") for station in STATIONS)
    )
    if len(panel) != 66 or len(frame) != 12 or len(removed) != 36:
        raise ValueError("Six-duty fixed axis inventory changed")
    for station in STATIONS:
        side = "left" if "_left" in station else "right"
        if station.startswith("clip_split_header_center_"):
            expected = ("base_header", f"base_post_center_{side}")
        elif station.startswith("clip_split_base_center_"):
            expected = ("base_header", f"base_principal_center_{side}")
        else:
            expected = (
                f"base_rail_bottom_{side}",
                f"base_principal_center_{side}",
            )
        if duties[station]["timber"] != expected:
            raise ValueError(f"{station}: original direct center duty host map changed")
    protected_inventory = protected.inventory()
    if (
        protected_inventory["counts"]["panel_screws"] != 66
        or protected_inventory["counts"]["frame_bolts"] != 12
    ):
        raise ValueError("Finite fixed-axis protection changed")
    all_solids, station_reports = {}, {}
    for station in STATIONS:
        family, specs, y_margin = _station_spec(station, wood)
        first, second, inward = specs[0]["butt"]
        contact = (
            protected._volume(
                first.translate(cq.Vector(*(component * 0.1 for component in inward))),
                second,
            )
            / 0.1
        )
        bolt_reports = {}
        for index, spec in enumerate(specs, 1):
            name, solids, result = _hardware(station, index, spec)
            all_solids.update(solids)
            host_names = spec["bolt_hosts"]
            header_segment = _cylinder(
                spec["bolt_seat"],
                spec["bolt_axis"],
                spec["header_length"],
                BORE_DIAMETER_MM,
            )
            host_segment = _cylinder(
                _add(spec["bolt_seat"], spec["bolt_axis"], spec["header_length"]),
                spec["bolt_axis"],
                spec["receiver_length"],
                BORE_DIAMETER_MM,
            )
            barrel = solids[f"{name}/barrel_body"]
            barrel_bore = solids[f"{name}/barrel_cross_bore"]
            result["intended_wood_core_fraction"] = {
                host_names[0]: round(
                    protected._volume(header_segment, wood[host_names[0]])
                    / header_segment.Volume(),
                    7,
                ),
                host_names[1]: round(
                    protected._volume(host_segment, wood[host_names[1]])
                    / host_segment.Volume(),
                    7,
                ),
                spec["barrel_host"] + "/cross_bore": round(
                    protected._volume(barrel_bore, wood[spec["barrel_host"]])
                    / barrel_bore.Volume(),
                    7,
                ),
                spec["barrel_host"] + "/body": round(
                    protected._volume(barrel, wood[spec["barrel_host"]])
                    / barrel.Volume(),
                    7,
                ),
            }
            bolt_reports[name] = result
        reasons = []
        if y_margin is not None and y_margin < 1.0:
            reasons.append(
                "backer/washer tolerance"
                if family == "principal_header"
                else "washer edge tolerance"
            )
        station_reports[station] = {
            "family": family,
            "butt_contact_area_mm2": round(contact, 6),
            "bolts": bolt_reports,
            "nominal_washer_to_edge_or_backer_margin_mm": y_margin,
            "revise_reasons": reasons,
        }
    finite_hits = protected.hits(all_solids, protected_inventory)
    for station, row in station_reports.items():
        for name, bolt in row["bolts"].items():
            bolt["protected_hits_mm3"] = {
                feature.removeprefix(name + "/"): hits
                for feature, hits in finite_hits.items()
                if feature.startswith(name + "/") and hits
            }
            spec = _station_spec(station, wood)[1][int(name.rsplit("_", 1)[1]) - 1]
            unrelated = {
                member: shape
                for member, shape in wood.items()
                if member not in spec["bolt_hosts"]
            }
            bolt["unrelated_timber_hits_mm3"] = {
                feature.removeprefix(name + "/"): hit
                for feature, shape in all_solids.items()
                if feature.startswith(name + "/")
                and (hit := _finite_hits(shape, unrelated))
            }
            if any(
                value < 0.999 for value in bolt["intended_wood_core_fraction"].values()
            ):
                row["revise_reasons"].append("incomplete intended wood/bore path")
            if bolt["protected_hits_mm3"]:
                row["revise_reasons"].append("finite protected-service intersection")
            if bolt["unrelated_timber_hits_mm3"]:
                row["revise_reasons"].append("unrelated timber or backer intersection")
        row["revise_reasons"] = sorted(set(row["revise_reasons"]))
        row["revise_required"] = bool(row["revise_reasons"])
    return {
        "solids": all_solids,
        "report": {
            "source_id": SOURCE_ID,
            "stations": station_reports,
            "approved_post_centers_x_mm": [-180.0, 180.0],
            "inventory": {
                "candidate_barrels": 12,
                "candidate_bolts": 12,
                "replaced_legacy_sds": len(removed),
                "fixed_panel_kicker_axes": len(panel),
                "retained_frame_bolts": len(frame),
            },
            "protected_counts": protected_inventory["counts"],
            "provisional_hardware": {
                "barrel_length_mm": BARREL_LENGTH_MM,
                "barrel_od_mm": BARREL_OD_MM,
                "thread_major_mm": hardware.THREAD_MAJOR_MM,
                "thread_axis_offset_mm_assumed": THREAD_AXIS_OFFSET_MM,
                "axis_offset_sensitivity_mm_not_screened": AXIS_OFFSET_SENSITIVITY_MM,
                "bolt_under_head_length_mm": BOLT_LENGTH_MM,
                "washer_thickness_mm_sensitivity": WASHER_THICKNESS_MM,
                "retail_identity_only": "Hillman 880543; Lowe's 3012559; Home Depot 202242356 / 933902",
            },
            "backer_frame_attachment_qualified": False,
            "retained_pb02_return_chain": False,
            "legacy_brackets_installed": False,
            "purchased_hillman_fit_verified": False,
            "cross_dowel_resistance_verified": False,
            "delivered_hold_bolt_length_verified": False,
            "wiring_bend_and_assembly_access_verified": False,
            "native_solve": False,
            "drilling_released": False,
            "structural_released": False,
            "decision": "REVISE_VIEWER_ONLY",
        },
    }


def build_layout(wood):
    """Leibniz viewer adapter: full provisional poses, never a fit verdict."""
    built = build(wood)
    report = built["report"]
    solids = built["solids"]
    stations = {}
    for station in STATIONS:
        diagnostic = report["stations"][station]
        _, specs, _ = _station_spec(station, wood)
        bolts, barrels, stacks, drilling, access = {}, {}, {}, {}, {}
        for index, spec in enumerate(specs, 1):
            base = f"barrel_center_{station}_{index}"
            bolt_name = f"{base}_bolt"
            seat = spec["bolt_seat"]
            axis = spec["bolt_axis"]
            bolts[bolt_name] = Connection(
                bolt_name,
                cq.Vector(*_add(seat, axis, -WASHER_THICKNESS_MM)),
                cq.Vector(*axis),
                BOLT_LENGTH_MM,
                hardware.THREAD_MAJOR_MM,
                spec["bolt_hosts"],
                "bolt",
            )
            barrels[base] = solids[f"{base}/barrel_body"]
            stacks[bolt_name] = {
                "shaft": solids[f"{base}/bolt_shaft_full_nominal"],
                "washer": solids[f"{base}/washer"],
                "head": solids[f"{base}/head"],
            }
            drilling[f"{base}/bolt_bore"] = solids[f"{base}/bolt_bore_full_nominal"]
            drilling[f"{base}/barrel_cross_bore"] = solids[f"{base}/barrel_cross_bore"]
            access[f"{base}/bolt_tool"] = solids[f"{base}/bolt_tool"]
            access[f"{base}/barrel_tool"] = solids[f"{base}/barrel_tool"]
        revise = diagnostic["revise_required"]
        stations[station] = {
            "mode": "direct",
            "axis_offset_mm": THREAD_AXIS_OFFSET_MM,
            "disposition": "REVISE" if revise else "VIEWER_ONLY_UNVERIFIED",
            "bolts": bolts,
            "barrels": barrels,
            "stacks": stacks,
            "drilling_paths": drilling,
            "access_paths": access,
        }
    return {
        "stations": stations,
        "diagnostics": report,
    }


def build_revised_layout(wood):
    """Expose the two revised center-principal poses without changing the default.

    The 22 mm washer and 4 in full-thread bolt are nominal drawing envelopes;
    neither is an identified, measured, strength-qualified purchased part.
    """
    # Import here so the unchanged default producer does not depend on its probe.
    from scripts import owner_barrel_center_margin_probe as margin

    original = build_layout(wood)
    trial = margin.screen_pose(
        wood,
        protected.inventory(),
        REVISED_PRINCIPAL_WASHER_OD_MM,
        REVISED_PRINCIPAL_ROWS_Y_MM,
        bolt_length_mm=REVISED_PRINCIPAL_BOLT_LENGTH_MM,
    )
    stations = dict(original["stations"])
    diagnostics = dict(original["diagnostics"])
    station_reports = dict(diagnostics["stations"])
    for side in ("left", "right"):
        station = f"clip_split_base_center_{side}"
        family, original_specs, _ = _station_spec(station, wood)
        if family != "principal_header" or len(original_specs) != 2:
            raise ValueError(f"{station}: principal/header duty changed")
        bolts, barrels, stacks, drilling, access, bolt_reports = {}, {}, {}, {}, {}, {}
        for index, (source, y) in enumerate(
            zip(original_specs, REVISED_PRINCIPAL_ROWS_Y_MM, strict=True), 1
        ):
            spec = dict(source)
            spec["bolt_seat"] = (source["bolt_seat"][0], y, source["bolt_seat"][2])
            spec["barrel_entry"] = (
                source["barrel_entry"][0],
                y,
                source["barrel_entry"][2],
            )
            name, solids, datum = _hardware(
                station,
                index,
                spec,
                bolt_length_mm=REVISED_PRINCIPAL_BOLT_LENGTH_MM,
                washer_diameter_mm=REVISED_PRINCIPAL_WASHER_OD_MM,
            )
            if name not in trial["bolts"]:
                raise ValueError(f"{station}: probe/revision bolt identity changed")
            bolt_name = f"{name}_bolt"
            seat, axis = spec["bolt_seat"], spec["bolt_axis"]
            bolts[bolt_name] = Connection(
                bolt_name,
                cq.Vector(*_add(seat, axis, -WASHER_THICKNESS_MM)),
                cq.Vector(*axis),
                REVISED_PRINCIPAL_BOLT_LENGTH_MM,
                hardware.THREAD_MAJOR_MM,
                spec["bolt_hosts"],
                "bolt",
            )
            barrels[name] = solids[f"{name}/barrel_body"]
            stacks[bolt_name] = {
                "shaft": solids[f"{name}/bolt_shaft_full_nominal"],
                "washer": solids[f"{name}/washer"],
                "head": solids[f"{name}/head"],
            }
            drilling[f"{name}/bolt_bore"] = solids[f"{name}/bolt_bore_full_nominal"]
            drilling[f"{name}/barrel_cross_bore"] = solids[f"{name}/barrel_cross_bore"]
            access[f"{name}/bolt_tool"] = solids[f"{name}/bolt_tool"]
            access[f"{name}/barrel_tool"] = solids[f"{name}/barrel_tool"]
            bolt_reports[name] = {**datum, **trial["bolts"][name]}
        stations[station] = {
            "mode": "direct",
            "axis_offset_mm": THREAD_AXIS_OFFSET_MM,
            "disposition": "REVISE",
            "bolts": bolts,
            "barrels": barrels,
            "stacks": stacks,
            "drilling_paths": drilling,
            "access_paths": access,
        }
        station_reports[station] = {
            **station_reports[station],
            "bolts": bolt_reports,
            "nominal_washer_to_edge_or_backer_margin_mm": min(
                trial["reserves_mm"].values()
            ),
            "revise_reasons": [
                "nominal 22 mm washer and 4 in full-thread bolt not product-qualified",
                "complete barrel thread/wood/assembly resistance unverified",
            ],
            "revise_required": True,
        }
    for station in STATIONS:
        stations[station] = {**stations[station], "disposition": "REVISE"}
        if station not in (
            "clip_split_base_center_left",
            "clip_split_base_center_right",
        ):
            station_reports[station] = {
                **station_reports[station],
                "revise_reasons": [
                    *station_reports[station]["revise_reasons"],
                    "complete hardware/wood/assembly verification unverified",
                ],
                "revise_required": True,
            }
    diagnostics.update(
        {
            "source_id": REVISED_SOURCE_ID,
            "stations": station_reports,
            "principal_header_geometry_trial": trial,
            "principal_header_trial_washer_od_mm": REVISED_PRINCIPAL_WASHER_OD_MM,
            "principal_header_trial_bolt_length_mm": (REVISED_PRINCIPAL_BOLT_LENGTH_MM),
            "principal_header_trial_full_thread_assumed": True,
            "washer_product_selected": False,
            "bolt_product_selected": False,
            "provisional_hardware": {
                **diagnostics["provisional_hardware"],
                "bolt_under_head_length_mm": None,
                "washer_od_mm": None,
                "mixed_center_principal_trial_envelopes": True,
            },
            "decision": "REVISE_VIEWER_ONLY",
            "drilling_released": False,
            "structural_released": False,
        }
    )
    return {"stations": stations, "diagnostics": diagnostics}


if __name__ == "__main__":
    print(json.dumps(build()["report"], indent=2, sort_keys=True))

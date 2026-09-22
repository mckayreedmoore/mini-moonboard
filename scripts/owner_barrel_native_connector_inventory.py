"""Source-built connector inventory for the -85 mm owner barrel viewer pose.

This is a preparation input, not a native model, solve, joint rating, or release.
"""

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from scripts.center_posts_outward_owner_layout import build_layout as post_layout
from scripts.export_owner_barrel_scene import build_viewer_assembly
from scripts.simple_owner_duty_ledger import selected_duties

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "owner_barrel_native_connector_inventory/v1"
SOURCE_PATHS = (
    "scripts/owner_barrel_native_connector_inventory.py",
    "scripts/export_owner_barrel_scene.py",
    "scripts/owner_barrel_layout_assembly.py",
    "scripts/owner_barrel_rail_layout.py",
    "scripts/owner_barrel_center_layout.py",
    "scripts/owner_barrel_outer_top_layout.py",
    "scripts/owner_barrel_center_margin_probe.py",
    "scripts/center_posts_outward_owner_layout.py",
    "scripts/owner_barrel_coordinates.py",
    "scripts/simple_cross_dowel_continuation.py",
    "scripts/simple_owner_duty_ledger.py",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/compact_floor_flush_frame.py",
    "docs/floor-flush-construction/connection-axes.csv",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv",
    "docs/floor-flush-construction-kerf-right/stock-profiles.json",
)
BACKERS = ("inner_kicker_backer_left", "inner_kicker_backer_right")


def _digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _xyz(vector):
    values = tuple(float(value) for value in vector.toTuple())
    if len(values) != 3 or not all(math.isfinite(value) for value in values):
        raise ValueError("Connector geometry has an invalid point or direction")
    return list(values)


def _connection(row, *, receiver=None):
    direction = row.direction.normalized()
    if row.length <= 0 or row.diameter <= 0 or len(row.members) != 2:
        raise ValueError(f"{row.name}: invalid connection geometry")
    return {
        "name": row.name,
        "kind": row.kind,
        "members": list(row.members),
        "receiver": row.members[1] if receiver is None else receiver,
        "start_mm": _xyz(row.start),
        "direction_xyz": _xyz(direction),
        "length_mm": float(row.length),
        "diameter_mm": float(row.diameter),
    }


def _barrel_axis(shape):
    """Recover the two actual cylindrical end caps, not a drawn bore axis."""
    caps = [face for face in shape.Faces() if face.geomType() == "PLANE"]
    if len(caps) != 2 or not math.isclose(caps[0].Area(), caps[1].Area(), rel_tol=1e-6):
        raise ValueError("Barrel envelope is not a two-cap cylinder")
    ends = sorted(_xyz(face.Center()) for face in caps)
    delta = [b - a for a, b in zip(*ends, strict=True)]
    length = math.sqrt(sum(value * value for value in delta))
    if length <= 0:
        raise ValueError("Barrel envelope has no axis length")
    radius = math.sqrt(caps[0].Area() / math.pi)
    center = [(a + b) / 2 for a, b in zip(*ends, strict=True)]
    return center, [value / length for value in delta], length, 2 * radius


def _axis_distance(point, start, direction):
    offset = [a - b for a, b in zip(point, start, strict=True)]
    along = sum(a * b for a, b in zip(offset, direction, strict=True))
    return math.sqrt(
        sum((a - along * b) ** 2 for a, b in zip(offset, direction, strict=True))
    ), along


def _physical_hosts(barrel, bolt, wood):
    """Identify receiver and entry wood from this pose's finite solids."""
    members = bolt["members"]
    body_volume = barrel.Volume()
    barrel_overlap = {name: barrel.intersect(wood[name]).Volume() for name in members}
    receivers = [
        name for name, volume in barrel_overlap.items() if volume > 0.99 * body_volume
    ]
    if len(receivers) != 1 or any(
        volume > 1e-5 * body_volume
        for name, volume in barrel_overlap.items()
        if name != receivers[0]
    ):
        raise ValueError(f"{bolt['name']}: barrel receiving wood is ambiguous")

    start = cq.Vector(*bolt["start_mm"])
    direction = cq.Vector(*bolt["direction_xyz"])
    shaft = cq.Solid.makeCylinder(
        bolt["diameter_mm"] / 2, bolt["length_mm"], start, direction
    )
    entry_positions = {}
    for name in members:
        intersection = shaft.intersect(wood[name])
        if intersection.Volume() <= 1e-6:
            raise ValueError(f"{bolt['name']}: machine bolt misses {name}")
        entry_positions[name] = min(
            (vertex.Center() - start).dot(direction)
            for vertex in intersection.Vertices()
        )
    ordered = sorted(entry_positions, key=entry_positions.get)
    if (
        entry_positions[ordered[1]] - entry_positions[ordered[0]] <= 1e-3
        or ordered[0] == receivers[0]
    ):
        raise ValueError(f"{bolt['name']}: machine bolt entry wood is ambiguous")
    return ordered[0], receivers[0], barrel_overlap, entry_positions


def build_inventory(*, assembly=None, placement=None):
    """Bind one viewer pose to exact candidate axes; leave native laws unresolved."""
    if (assembly is None) != (placement is None):
        raise ValueError("Supply both source-built assembly and placement, or neither")
    if assembly is None:
        assembly, placement = build_viewer_assembly(), post_layout()
    duties = selected_duties()
    diagnostics = assembly["diagnostics"]["producer_diagnostics"]
    if (
        set(assembly["station_modes"]) != set(duties)
        or set(assembly["removed_legacy_stations"]) != set(duties)
        or set(assembly["station_modes"].values()) != {"direct"}
        or diagnostics["outer_top8"]["viewer_trial_outer_header_forward_y_mm"] != -85.0
        or diagnostics["outer_top8"]["viewer_trial_outer_header_recess_mm"] is None
        or not set(BACKERS).issubset(assembly["wood"])
    ):
        raise ValueError("Require the complete -85 mm barrel-only viewer pose")
    legacy_sds = {name for duty in duties.values() for name in duty["sds_axes"]}
    removed_sds = {row.name for row in assembly["removed_legacy_sds"]}
    panel = {row.name: row for row in assembly["panel_connections"]}
    frame = {row.name: row for row in assembly["frame_connections"]}
    bolt_source = assembly["bolts"]
    barrel_source = assembly["barrels"]
    if (
        len(legacy_sds) != 144
        or len(removed_sds) != 144
        or removed_sds != legacy_sds
        or len(panel) != 66
        or len(frame) != 12
        or len(bolt_source) != 48
        or len(barrel_source) != 48
        or set(assembly["bolt_station"]) != set(bolt_source)
        or set(assembly["barrel_station"]) != set(barrel_source)
    ):
        raise ValueError("Candidate fixed, legacy, bolt, or barrel inventory changed")
    # Check original source axes against the independent placement record.
    if set(placement["fixed_panel_axes"]) != set(panel):
        raise ValueError("Fixed panel screw identities changed")
    receivers = placement["panel_receiver_map"]
    landings = placement["center_kicker_screws"]
    if (
        set(receivers) != set(panel)
        or len(landings) != 4
        or set(landings)
        != {name for name, receiver in receivers.items() if receiver in BACKERS}
        or placement["backer_frame_attachment_qualified"] is not False
    ):
        raise ValueError("Backer screw landing or attachment status changed")
    fixed_screws = {}
    for name, row in panel.items():
        source_axis = placement["fixed_panel_axes"][name]
        record = _connection(row, receiver=receivers[name])
        if any(
            abs(a - b) > 1e-5 for a, b in zip(record["start_mm"], source_axis[0])
        ) or any(
            abs(a - b) > 1e-8 for a, b in zip(record["direction_xyz"], source_axis[1])
        ):
            raise ValueError(f"{name}: fixed screw axis differs from placement source")
        fixed_screws[name] = record
    backers = {}
    for backer in BACKERS:
        screws = sorted(name for name in landings if receivers[name] == backer)
        if len(screws) != 2 or backer not in assembly["wood"]:
            raise ValueError(f"{backer}: missing screw landings or timber")
        backers[backer] = {
            "screw_names": screws,
            "frame_attachment_status": "missing",
            "frame_attachment_connections": [],
        }

    bolts, barrels, stations = {}, {}, {}
    for station, duty in duties.items():
        bolt_names = sorted(
            name for name, owner in assembly["bolt_station"].items() if owner == station
        )
        barrel_names = sorted(
            name
            for name, owner in assembly["barrel_station"].items()
            if owner == station
        )
        if (
            len(bolt_names) != 2
            or len(barrel_names) != 2
            or {name.removesuffix("_bolt") for name in bolt_names} != set(barrel_names)
        ):
            raise ValueError(f"{station}: missing paired bolt or barrel")
        stations[station] = {
            "family": duty["family"],
            "side": duty["side"],
            "timber_members": list(duty["timber"]),
            "bolt_names": bolt_names,
            "barrel_names": barrel_names,
            "viewer_disposition": assembly["station_dispositions"][station],
        }
        for name in bolt_names:
            barrel_name = name.removesuffix("_bolt")
            bolt = _connection(bolt_source[name])
            if bolt["kind"] != "bolt" or set(bolt["members"]) != set(duty["timber"]):
                raise ValueError(f"{name}: structural member ownership changed")
            center, axis, length, diameter = _barrel_axis(barrel_source[barrel_name])
            distance, along = _axis_distance(
                center, bolt["start_mm"], bolt["direction_xyz"]
            )
            if distance > 1e-3:
                raise ValueError(f"{name}: viewer bolt and barrel axes do not meet")
            entry, receiver, overlap, entry_positions = _physical_hosts(
                barrel_source[barrel_name], bolt, assembly["wood"]
            )
            bolt.update(
                station=station,
                barrel_name=barrel_name,
                entry_member=entry,
                receiving_member=receiver,
                receiver=receiver,
                provisional_thread_axis_point_mm=center,
                provisional_axis_point_from_bolt_start_mm=along,
                modeled_shaft_reaches_provisional_axis=(
                    along <= bolt["length_mm"] + 1e-6
                ),
                modeled_shaft_shortfall_mm=max(0.0, along - bolt["length_mm"]),
                machine_entry_along_bolt_mm=entry_positions[entry],
                native_connector_law=None,
            )
            bolts[name] = bolt
            barrels[barrel_name] = {
                "station": station,
                "bolt_name": name,
                "receiving_member": receiver,
                "entry_member": entry,
                "provisional_thread_axis_point_mm": center,
                "body_axis_xyz_unoriented_provisional": axis,
                "body_length_mm_provisional": length,
                "body_diameter_mm_provisional": diameter,
                "body_wood_overlap_mm3": overlap,
                "wood_reaction_law": None,
            }

    retained = {name: _connection(row) for name, row in frame.items()}
    reach_shortfalls = {
        name: round(row["modeled_shaft_shortfall_mm"], 6)
        for name, row in bolts.items()
        if not row["modeled_shaft_reaches_provisional_axis"]
    }
    candidate_names = sorted(set(fixed_screws) | set(retained) | set(bolts))
    if (
        len(candidate_names) != 126
        or set(candidate_names) & legacy_sds
        or set(candidate_names) & set(duties)
    ):
        raise ValueError("Candidate inventory retains a legacy structural connector")
    source_sha256 = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in SOURCE_PATHS
    }
    inventory = {
        "schema": SCHEMA,
        "status": "preparation_inventory_only",
        "viewer_pose": {
            "outer_header_forward_y_mm": -85.0,
            "outer_header_recess_mm_provisional": diagnostics["outer_top8"][
                "viewer_trial_outer_header_recess_mm"
            ],
            "producer_source_ids": {
                family: row["source_id"] for family, row in diagnostics.items()
            },
        },
        "stations": stations,
        "bolts": bolts,
        "barrels": barrels,
        "modeled_shaft_reach_shortfalls_mm": reach_shortfalls,
        "fixed_panel_screws": fixed_screws,
        "retained_frame_bolts": retained,
        "candidate_connection_names": candidate_names,
        "excluded_legacy": {
            "angle_stations": sorted(duties),
            "sds_axes": sorted(legacy_sds),
        },
        "backers": backers,
        "backer_screw_landings": {
            name: {
                "receiver": receivers[name],
                "start_mm": fixed_screws[name]["start_mm"],
                "direction_xyz": fixed_screws[name]["direction_xyz"],
                "length_mm": fixed_screws[name]["length_mm"],
            }
            for name in sorted(landings)
        },
        "missing_native_inputs": {
            "backer_frame_attachment": "No connection to frame is defined for either backer",
            "bolt_reach_and_engagement": (
                "Viewer shaft lengths and provisional thread-axis points require "
                "per-bolt reach, tip-clearance, and delivered engagement checks"
            ),
            "contact_laws": [
                "actual butt-face compression-only cells and stiffness",
                "existing header/post bearing overlap and floor support reconciliation",
            ],
            "connector_laws": [
                "no-preload axial tension and lateral bearing/clearance for each bolt",
                "barrel-to-wood reaction and stiffness at each thread center",
                "backer attachment stiffness and retained-frame-bolt recheck",
            ],
        },
        "source_sha256": source_sha256,
        "native_ready": False,
        "native_solve": False,
        "capacities_claimed": False,
        "release_claimed": False,
    }
    inventory["inventory_fingerprint_sha256"] = _digest(inventory)
    return inventory

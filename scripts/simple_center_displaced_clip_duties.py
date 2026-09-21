"""Read-only PB-02 inventory of two displaced right-center legacy clips.

This reports old ownership and proxy actions, never a replacement load or fit.
"""

import csv
import json
from pathlib import Path

from mini_moonboard import compact_floor_flush_frame as frame
from scripts.simple_center_edge_reserve_probe import probe

ROOT = Path(__file__).resolve().parents[1]
AXES = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
ARCHIVE = ROOT / "docs/bolted-candidate-prototypes/center-reference-diagnostic.json"
STATIONS = {
    "clip_split_base_center_right": ("principal_header", "base_principal_center_right"),
    "clip_split_header_center_right": ("post_header", "base_post_center_right"),
}


def _xyz(vector):
    return [round(value, 6) for value in vector.toTuple()]


def _bounds(box):
    return [
        round(value, 6)
        for value in (box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax)
    ]


def _historical_z_separation(header, partner):
    """Infer face-normal sense only when old wood boxes abut in Z and overlap in XY."""
    tolerance = 1e-5
    if (
        min(header.xmax, partner.xmax) - max(header.xmin, partner.xmin) <= tolerance
        or min(header.ymax, partner.ymax) - max(header.ymin, partner.ymin) <= tolerance
    ):
        raise ValueError("Old header/partner boxes do not share an XY region")
    if abs(partner.zmin - header.zmax) <= tolerance and partner.zmax > header.zmax:
        return 1
    if abs(partner.zmax - header.zmin) <= tolerance and partner.zmin < header.zmin:
        return -1
    raise ValueError("Old header/partner Z face relationship is not established")


def _old_actions(stations):
    """Copy only signed old-clip proxy actions with matching station identity."""
    archive = json.loads(ARCHIVE.read_text())
    result = {}
    for case in archive["accepted_default_v2"]:
        if case["status"] != "accepted_proxy_reference" or not all(
            case["convergence"].get(key) is True
            for key in (
                "numerically_accepted",
                "contact_active_set_converged",
                "global_equilibrium_passed",
                "member_equilibrium_passed",
                "mpc_check_passed",
            )
        ):
            raise ValueError(f"Unaccepted archival case: {case['case']}")
        if (
            case["settings"]["diagnostic_scope"]["connector_proxy"]
            != "baseline ML24Z angles and SDS screws"
        ):
            raise ValueError("Archival connection topology changed")
        for name, (key, partner) in STATIONS.items():
            row = case["sides"]["right"]["interfaces"][key]
            if (
                row["clip"] != name
                or row["header"] != "base_header"
                or row["center_member"] != partner
                or any(
                    abs(a - b) > 1e-6
                    for a, b in zip(
                        row["origin_xyz_mm"], stations[name]["origin_xyz_mm"]
                    )
                )
            ):
                raise ValueError(
                    f"Archival station does not match current old pose: {case['case']}/{name}"
                )
            result.setdefault(name, []).append(
                {
                    "case": case["case"],
                    "source_report_sha256": case["source"]["report_sha256"],
                    "source_record_sha256": case["source"]["record_sha256"],
                    "force_on_old_partner_via_clip_xyz_n": row[
                        "on_center_member_components"
                    ]["via_clip"]["force_xyz_n"],
                    "moment_on_old_partner_via_clip_xyz_nmm": row[
                        "on_center_member_components"
                    ]["via_clip"]["moment_xyz_nmm"],
                }
            )
    return result


def inventory():
    """Reconcile live CAD, kerf-right axis schedule, and the latest pose."""
    pose = probe()
    if set(pose["removed_legacy_stations"]) != set(STATIONS):
        raise ValueError("Edge-reserve pose no longer displaces exactly these stations")
    live_stations = {
        name: (origin, u, v, beam, upright)
        for name, origin, u, v, beam, upright in frame.stations()
        if name in STATIONS
    }
    if set(live_stations) != set(STATIONS):
        raise ValueError("Missing live CAD station")
    connections = {c.name: c for c in frame.connections()}
    old_wood = {
        part.name: part.shape.BoundingBox()
        for part in frame.uncut_wood_parts()
        if part.name in {"base_header", *(partner for _, partner in STATIONS.values())}
    }
    with AXES.open(newline="") as handle:
        rows = {
            row["name"]: row
            for row in csv.DictReader(handle)
            if any(row["name"].startswith(name + "_") for name in STATIONS)
        }
    stations = {}
    for name, (_, expected_partner) in STATIONS.items():
        origin, u, v, beam, partner = live_stations[name]
        if (beam, partner) != ("base_header", expected_partner):
            raise ValueError(f"Old wood ownership changed: {name}")
        separation = _historical_z_separation(old_wood[beam], old_wood[partner])
        names = [
            f"{name}_{side}_{index}"
            for side in ("beam", "upright")
            for index in (1, 2, 3)
        ]
        if set(names) != {key for key in rows if key.startswith(name + "_")}:
            raise ValueError(f"Incomplete scheduled SDS inventory: {name}")
        screws = []
        for connection_name in names:
            c, row = connections[connection_name], rows[connection_name]
            owner = beam if "_beam_" in connection_name else partner
            start = _xyz(c.start)
            direction = _xyz(c.direction)
            scheduled_start = [float(row[f"start_{axis}_mm"]) for axis in "xyz"]
            scheduled_direction = [float(row[f"direction_{axis}"]) for axis in "xyz"]
            if (
                c.members != (name, owner)
                or row["first_member"] != name
                or row["second_member"] != owner
                or row["shop_opening_kind"] != "sds_wood"
                or any(abs(a - b) > 1e-5 for a, b in zip(start, scheduled_start))
                or any(
                    abs(a - b) > 1e-6 for a, b in zip(direction, scheduled_direction)
                )
            ):
                raise ValueError(
                    f"CAD/schedule ownership or axis mismatch: {connection_name}"
                )
            screws.append(
                {
                    "name": connection_name,
                    "wood_receiver": owner,
                    "start_xyz_mm": start,
                    "direction_xyz": direction,
                    "modeled_length_mm": float(row["modeled_length_mm"]),
                    "modeled_diameter_mm": float(row["modeled_diameter_mm"]),
                    "product": "Simpson SDS25112, separately purchased",
                }
            )
        stations[name] = {
            "old_clip": "purchased ML24Z",
            "old_header_host": beam,
            "old_partner": partner,
            "origin_xyz_mm": _xyz(origin),
            "clip_u_xyz": _xyz(u),
            "clip_v_xyz": _xyz(v),
            "old_header_bounds_mm": _bounds(old_wood[beam]),
            "old_partner_bounds_mm": _bounds(old_wood[partner]),
            "inferred_historical_separation_partner_away_from_header_xyz": [
                0,
                0,
                separation,
            ],
            "inferred_historical_separation_header_away_from_partner_xyz": [
                0,
                0,
                -separation,
            ],
            "old_fasteners": screws,
            "replacement_duties": [
                f"Connect {beam} to {partner} in both separation senses and in-plane actions",
                "Account for the old three header-side and three partner-side SDS paths",
                "Establish a verified path and signed actions for the changed wood geometry",
            ],
        }
    actions = _old_actions(stations)
    return {
        "scope": "PB-02 two displaced clips; inventory only; no replacement design or rating",
        "pose": {
            "post_bounds_mm": pose["post_bounds_mm"],
            "rear_cleat_bounds_mm": pose["cleat_bounds_mm"]["rear"],
            "post_bolt_x_mm": pose["post_bolt_x_mm"],
            "cleat_link_x_mm": pose["cleat_link_x_mm"],
            "legacy_clip_wood_hits_mm3": {
                k: v
                for k, v in pose["legacy_clip_wood_hits_mm3"].items()
                if k.split("/")[0] in STATIONS
            },
            "legacy_screw_wood_hits_mm3": {
                k: v
                for k, v in pose["legacy_clip_screw_wood_hits_mm3"].items()
                if k.split("/")[0].rsplit("_", 2)[0] in STATIONS
            },
        },
        "stations": stations,
        "archival_old_topology_actions": actions,
        "archival_case_coverage": "five accepted old-proxy cases; a12-forward missing; not a full old-duty envelope",
        "ambiguity": [
            "Historical separation senses are inferred from abutting old timber bounds, not verified new load directions or contact normals.",
            "Five accepted proxy cases omit a12-forward and do not form a full old-duty envelope.",
            "Source report/input digests are copied from the proxy packet, not independently authenticated by this extractor.",
            "The later link-edge side-cleat trial is outside this pose; recheck old station identity and displacement against that exact trial.",
            "Old proxy clip actions are not new bolt demand; the changed wood/connector topology has no established actions.",
            "Signed loaded directions, separation magnitudes, and replacement load sharing are unresolved.",
        ],
    }


if __name__ == "__main__":
    print(json.dumps(inventory(), indent=2, sort_keys=True))

"""Read-only relocation screen; keep the reviewed frame and all source bytes frozen.

Run from the repository root:
PYTHONPATH=. .venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/principal-midpoint-relocation.py
"""

import hashlib
import json
import sys
from pathlib import Path

import cadquery as cq

from mini_moonboard import no_shoes_frame, panel_grid_v2
from scripts import wood_joint_midpoint_clearance as method

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "occupied-aligned-wire-v1.json"
TARGET = "base_principal_center_right"
OUT = Path(
    "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/future-midpoint-clearance-v1/relocation-result.json"
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    receipt = json.loads(SOURCE.read_bytes())
    pins = {
        str(SOURCE.relative_to(Path.cwd())): digest(SOURCE),
        str(Path(__file__).resolve().relative_to(Path.cwd())): digest(__file__),
    }
    for name in (
        "scripts/wood_joint_midpoint_clearance.py",
        "mini_moonboard/panel_grid_v2.py",
    ):
        pins[name] = digest(name)
    for name, module in tuple(sys.modules.items()):
        if name.startswith("mini_moonboard.") and getattr(module, "__file__", None):
            path = Path(module.__file__).resolve()
            pins[str(path.relative_to(Path.cwd()))] = digest(path)
    wood = {}
    for row in (
        receipt["changed_finished_solids"] + receipt["unchanged_finished_solids"]
    ):
        assert digest(row["path"]) == row["sha256"], row["path"]
        pins[row["path"]] = row["sha256"]
        wood[row["id"]] = cq.Shape.importBrep(row["path"])
        assert wood[row["id"]].isValid() and len(wood[row["id"]].Solids()) == 1
    assert len(wood) == 22
    frame = no_shoes_frame.b
    normal = frame.normal().normalized()
    grid = panel_grid_v2.main_tnut_datums()
    f = grid["F1"][0] - frame.HALF
    midpoint = (grid["F1"][0] + grid["G1"][0]) / 2 - frame.HALF
    bounds = wood[TARGET].BoundingBox()
    width = bounds.xmax - bounds.xmin
    proposed_center = (f + midpoint) / 2
    shift = proposed_center - (bounds.xmin + bounds.xmax) / 2
    radius = method.FLANGE_DIAMETER_MM / 2
    clear_center_interval = [f + radius + width / 2, midpoint - radius - width / 2]
    assert clear_center_interval[0] < proposed_center < clear_center_interval[1]
    moved = dict(wood)
    moved[TARGET] = wood[TARGET].translate((shift, 0, 0))

    def hits(probe, solids):
        box = method._bbox(probe)
        return [
            {"member": name, "volume_mm3": round(volume, 6)}
            for name, shape in solids.items()
            if method._overlap(box, method._bbox(shape))
            and (volume := probe.intersect(shape).Volume())
            > method.VOLUME_TOLERANCE_MM3
        ]

    def probes(x, s):
        rear = frame.point(x - frame.HALF, s, 0)
        return {
            "flange": cq.Solid.makeCylinder(
                radius, method.FLANGE_THICKNESS_MM, rear, normal
            ),
            "rear_projection": cq.Solid.makeCylinder(
                method.PROJECTION_DIAMETER_MM / 2,
                method.PROJECTION_LENGTH_MM,
                rear,
                normal,
            ),
        }

    sites = [
        s
        for s in method.midpoint_sites()
        if s["family"] == "T-nut"
        and s["direction"] == "horizontal"
        and s["surface"] == "main"
    ]
    states = {}
    for label, solids in (("current", wood), ("principal_only_left_shift", moved)):
        blocked = []
        for site in sites:
            found = {
                kind: h
                for kind, probe in probes(site["x_mm"], site["s_mm"]).items()
                if (h := hits(probe, solids))
            }
            if found:
                blocked.append({"id": site["id"], "hits": found})
        states[label] = {
            "sites": len(sites),
            "blocked": blocked,
            "clear": len(sites) - len(blocked),
        }
        print(label, states[label]["clear"], "clear /", len(sites), flush=True)
    assert states["current"]["clear"] == 108
    assert states["principal_only_left_shift"]["clear"] == 120
    existing_hits = []
    for label, (x, s) in grid.items():
        for kind, probe in probes(x, s).items():
            if found := hits(probe, {TARGET: moved[TARGET]}):
                existing_hits.append({"id": label, "envelope": kind, "hits": found})
    assert not existing_hits
    led_hits = []
    for label, (x, s) in panel_grid_v2.main_led_datums().items():
        corridor = cq.Solid.makeCylinder(
            6.5, 50.8, frame.point(x - frame.HALF, s, 0), normal
        )
        if found := hits(corridor, {TARGET: moved[TARGET]}):
            led_hits.append({"id": label, "hits": found})
    assert not led_hits
    contacts = []
    for name, shape in wood.items():
        if name == TARGET:
            continue
        old_distance = wood[TARGET].distance(shape)
        new_distance = moved[TARGET].distance(shape)
        overlap = hits(moved[TARGET], {name: shape})
        if old_distance < 1e-5 or new_distance < 1e-5 or overlap:
            contacts.append(
                {
                    "member": name,
                    "before_distance_mm": old_distance,
                    "after_distance_mm": new_distance,
                    "overlap": overlap,
                }
            )
    duties = {
        a["duty_id"]
        for row in receipt["axes"]
        if TARGET in row["receivers"]
        for a in row["attachments"]
    }
    affected = [
        row
        for row in receipt["axes"]
        if any(a["duty_id"] in duties for a in row["attachments"])
    ]
    screws = [row for row in receipt["screw_axes"] if row["receiver"] == TARGET]
    new_bounds = moved[TARGET].BoundingBox()
    screw_actions = [
        {
            "id": row["axis_id"],
            "old_x_mm": row["origin_xyz_mm"][0],
            "proposed_x_mm": row["origin_xyz_mm"][0] + shift,
            "old_axis_outside_shifted_receiver": not new_bounds.xmin
            <= row["origin_xyz_mm"][0]
            <= new_bounds.xmax,
            "proposed_axis_side_edge_distance_mm": width / 2,
        }
        for row in screws
    ]
    assert len(affected) == 20 and len(screws) == 8
    assert all(row["old_axis_outside_shifted_receiver"] for row in screw_actions)
    result = {
        "source_revision": receipt["revision"],
        "status": "UNADOPTED_GEOMETRY_SCREEN",
        "source_sha256": pins,
        "cadquery_version": cq.__version__,
        "target": TARGET,
        "shift_xyz_mm": [shift, 0, 0],
        "old_center_x_mm": (bounds.xmin + bounds.xmax) / 2,
        "proposed_center_x_mm": proposed_center,
        "proposed_panel_x_mm": proposed_center + frame.HALF,
        "proposed_x_bounds_mm": [new_bounds.xmin, new_bounds.xmax],
        "F_column_x_mm": f,
        "FG_midpoint_x_mm": midpoint,
        "flange_clear_center_interval_mm_without_tolerance": clear_center_interval,
        "equal_nominal_flange_margin_mm": (midpoint - f - width) / 2 - radius,
        "envelopes": {
            "flange_diameter_mm": method.FLANGE_DIAMETER_MM,
            "flange_thickness_mm": method.FLANGE_THICKNESS_MM,
            "rear_projection_diameter_mm": method.PROJECTION_DIAMETER_MM,
            "rear_projection_length_mm": method.PROJECTION_LENGTH_MM,
        },
        "midpoint_states": states,
        "existing_132_hold_proxy_hits_on_moved_principal": existing_hits,
        "existing_132_LED_13mm_by_50_8mm_corridor_hits_on_moved_principal": led_hits,
        "timber_contact_changes": contacts,
        "affected_duties": sorted(duties),
        "affected_bolt_axes": [
            {
                "id": row["id"],
                "receivers": row["receivers"],
                "old_point_xyz_mm": row["point_xyz_mm"],
                "proposal_point_xyz_mm": [
                    row["point_xyz_mm"][0] + shift,
                    *row["point_xyz_mm"][1:],
                ],
            }
            for row in affected
        ],
        "panel_screw_actions": screw_actions,
        "services_to_recheck": [
            r for r in receipt["service_cuts"] if r["receiver"] == TARGET
        ],
        "limits": [
            "Only the principal is translated in memory; no coordinated successor is generated.",
            "Bracket bodies, hardware, wires, LED bodies, retention screws and tools are not screened.",
            "LED check covers nominal 13-mm by 50.8-mm rear corridors only, not feeding or wiring.",
            "Existing holds use the same flange and provisional rear-projection proxies, not selected bolts.",
            "Eight screw moves preserve count but require new panel bores and receiver/support checks.",
            "Three right split rails need inward end extensions to restore their 39.2-mm contact gaps.",
            "All five bracket duties need coordinated geometry, bore/washer edge, access and force rechecks.",
            "No native solve, viewer edit, structural acceptance or physical work.",
        ],
    }
    for path, expected in pins.items():
        assert digest(path) == expected, path
    result["source_bytes_unchanged"] = True
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print("Saved", OUT, digest(OUT), flush=True)


if __name__ == "__main__":
    main()

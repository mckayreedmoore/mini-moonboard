"""Isolated top-corner correction proposal; preserve the old lateral wrenches.

This is a fixed-demand sizing scenario, not a revised whole-frame solution.
No reviewed geometry, selected authority or old evidence is overwritten.
"""

import csv
import json
import math
from pathlib import Path

import cadquery as cq
import lateral_reference as lateral
import numpy as np
import top_corner_actions as accounting
import top_corner_local as local

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SURFACES = HERE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
ACTION_PATH = HERE / "top-corner-actions.json"
PINS = {
    **lateral.PINS,
    SURFACES: "33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb",
    ACTION_PATH: "dd6ce9ce278406dc63e73400f0b5822ad7c40e3c37398910a8461d9331d92623",
    local.SOURCE_CACHE
    / "chapter12-2024-awc-20260911.pdf": "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
}
X = np.array([1.0, 0.0, 0.0])
T = local.unit([0, 0.642787610, 0.766044443])
N = local.unit([0, -0.766044443, 0.642787610])
SIDE_D = 25.4 * 5 / 16
SIDE_BORE = 9.0
SIDE_PITCH = 139.7 / 2 - 2.0
NEW_T_CENTER = -25.4
sha, require, read = accounting.sha, accounting.require, accounting.read


def cylinder(point, direction, radius, length):
    return cq.Solid.makeCylinder(
        radius, length, cq.Vector(*point), cq.Vector(*direction)
    )


def overlap(a, b):
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if any(
        getattr(ba, k + "max") < getattr(bb, k + "min") - 1e-6
        or getattr(bb, k + "max") < getattr(ba, k + "min") - 1e-6
        for k in "xyz"
    ):
        return 0.0
    return float(a.intersect(b).Volume())


def bolt_reference(force, diameter_in, fyb):
    angles = [lateral.angle(force, N), lateral.angle(force, T)]
    parallel = 11200 * 0.5
    perpendicular = 6100 * 0.5**1.45 / math.sqrt(diameter_in)

    def bearing(theta):
        theta = math.radians(theta)
        return (
            parallel
            * perpendicular
            / (parallel * math.sin(theta) ** 2 + perpendicular * math.cos(theta) ** 2)
        )

    moment = fyb * diameter_in**3 / 6
    rd = 1 + 0.25 * max(angles) / 90
    result = lateral.single_shear(
        main_length_in=3.5,
        side_length_in=3.5,
        main_bearing_lb_in=bearing(angles[0]) * diameter_in,
        side_bearing_lb_in=bearing(angles[1]) * diameter_in,
        main_yield_moment_lb_in=moment,
        side_yield_moment_lb_in=moment,
        gap_in=0,
        reduction_terms={
            k: v * rd
            for k, v in {
                "Im": 4,
                "Is": 4,
                "II": 3.6,
                "IIIm": 3.2,
                "IIIs": 3.2,
                "IV": 3.2,
            }.items()
        },
    )
    return {
        "grain_angles_degrees": angles,
        "parallel_perpendicular_bearing_psi": [parallel, perpendicular],
        "reference_n": result["reference_lateral_lbf"] * lateral.N_PER_LBF,
        "governing_mode": result["governing_mode"],
    }


def side_geometry(point, descriptor, pitch, cleat):
    grain = local.unit(descriptor["axis"])
    start = np.array(descriptor["start"])
    length = np.linalg.norm(np.array(descriptor["end"]) - start)
    station = float(grain @ (point - start))
    transverse = T if cleat else N
    width = 139.7
    q = float(transverse @ (point - (start + grain * length / 2)))
    edges = [width / 2 + q, width / 2 - q]
    ends = [station, float(length - station)]
    required_parallel_edge = max(1.5 * SIDE_D, pitch / 2) if cleat else 1.5 * SIDE_D
    required_perpendicular_edge = 4 * SIDE_D
    require(min(ends) >= 7 * SIDE_D, "proposed side end below full comparator")
    require(
        min(edges) >= max(required_parallel_edge, required_perpendicular_edge),
        "proposed side edge below component comparator",
    )
    required_pitch = 5 * SIDE_D if cleat else 4 * SIDE_D
    require(pitch >= required_pitch, "proposed side spacing below comparator")
    return {
        "grain_end_distances_mm": ends,
        "transverse_edge_distances_mm": edges,
        "full_softwood_tension_end_comparator_mm": 7 * SIDE_D,
        "parallel_edge_comparator_mm": required_parallel_edge,
        "perpendicular_loaded_edge_comparator_mm": required_perpendicular_edge,
        "row_spacing_comparator_mm": required_pitch,
        "component_geometry_comparators_met": True,
        "scope": "Both pure-direction component scenarios; no oblique-group acceptance.",
    }


def build_proposal(block, geom, bolts, source_shapes, surface_rows):
    old_center = (np.array(geom["start"]) + np.array(geom["end"])) / 2
    center = old_center + NEW_T_CENTER * T
    length = float(np.linalg.norm(np.array(geom["end"]) - geom["start"]))
    blank = (
        cq.Workplane(cq.Plane(origin=tuple(center), xDir=tuple(X), normal=tuple(N)))
        .box(88.9, 139.7, length)
        .val()
    )
    finished = blank
    axes = []
    direction = X if block.endswith("left_cleat") else -X
    for bolt in bolts:
        axis = bolt["axis_id"]
        old = np.array(bolt["source_point_xyz_mm"])
        if "/side_" in axis:
            side_index = int(axis.rsplit("_", 1)[1]) - 1
            target_t = NEW_T_CENTER + (-1 if side_index == 0 else 1) * SIDE_PITCH / 2
            delta = target_t - float(T @ (old - old_center))
            new = old + delta * T
            bore = SIDE_BORE
            cutter = cylinder(new - direction * 300, direction, bore / 2, 600)
            geometry = {**geom, "depth_mm": 139.7}
            geometry["start"] = (np.array(geom["start"]) + NEW_T_CENTER * T).tolist()
            geometry["end"] = (np.array(geom["end"]) + NEW_T_CENTER * T).tolist()
            scenario = side_geometry(new, geometry, SIDE_PITCH, True)
        else:
            new, delta, bore, scenario = old, 0.0, 7.5, None
            cutter = cylinder(new - 300 * T, T, bore / 2, 600)
        finished = finished.cut(cutter)
        axes.append(
            {
                "axis_id": axis,
                "old_axis_point_mm": old.tolist(),
                "proposed_axis_point_mm": new.tolist(),
                "axis_translation_T_mm": delta,
                "nominal_bolt_diameter_mm": SIDE_D if scenario else 6.35,
                "proposed_CAD_bore_envelope_mm": bore,
                "cleat_geometry_comparators": scenario,
                "wood_grip_mm": 177.8,
                "old_wood_grip_mm": 177.8 if scenario else 127.0,
            }
        )
    require(finished.isValid() and len(finished.Solids()) == 1, "invalid new cleat")
    conflicts = []
    panel_clearances = {}
    for name, source in source_shapes.items():
        if name == block:
            continue
        volume = overlap(blank, source)
        if volume > 1e-4:
            conflicts.append({"member": name, "overlap_mm3": volume})
        if name.startswith("main_"):
            panel_clearances[name] = float(blank.distance(source))
    # Extend only the source 40.1 mm service-passage cylinders through the
    # cleat. No transfer of approved cable routing is inferred from this query.
    passage_hits = []
    for row in surface_rows:
        for f in row["features"]:
            if f["surface_kind"] != "CYLINDER":
                continue
            c = f["cylinder"]
            if not math.isclose(c["radius_mm"], 20.05, abs_tol=1e-5):
                continue
            axis = local.unit(c["axis_unit_global_xyz"])
            passage = cylinder(
                np.array(c["centroid_global_xyz_mm"]) - 300 * axis,
                axis,
                c["radius_mm"],
                600,
            )
            volume = overlap(blank, passage)
            if volume > 1e-4:
                passage_hits.append(
                    {"feature_id": f["feature_id"], "overlap_mm3": volume}
                )
    return {
        "block": block,
        "old_section_X_T_mm": [88.9, 88.9],
        "proposed_section_X_T_mm": [88.9, 139.7],
        "grain_length_mm": length,
        "center_translation_T_mm": NEW_T_CENTER,
        "rail_interface_face_translation_mm": 0.0,
        "side_bolt_pitch_mm": SIDE_PITCH,
        "axes": axes,
        "raw_blank_volume_mm3": blank.Volume(),
        "finished_proposal_volume_mm3": finished.Volume(),
        "other_finished_wood_overlap_records": conflicts,
        "extended_service_passage_overlap_records": passage_hits,
        "main_panel_clearances_mm": panel_clearances,
        "geometry_scope": "New blank only; old side-host bores must be replaced in a future receiver revision. No retrofit is qualified.",
    }, finished


def lateral_states(interface, proposal, case):
    old = interface["lateral_bolt_pair"]["individual_bolts"]
    schedule = {r["axis_id"]: r for r in proposal["axes"]}
    points = [np.array(schedule[r["axis_id"]]["proposed_axis_point_mm"]) for r in old]
    # Source axis points are shaft datums. Restore their original X plane;
    # translations here change only T, not the interface/shear-plane position.
    for i, r in enumerate(old):
        points[i][0] = r["point_mm"][0]
    datum = np.array(interface["datum_mm"])
    old_w = accounting.wrench(old, datum)
    free = sum((np.array(r["free_moment_nmm"]) for r in old), start=np.zeros(3))
    tangents = [float(T @ r["force_n"]) * T for r in old]
    rn = float(N @ old_w[:3])
    # f1_N + f2_N = R_N, with the complete pair moment about the old datum.
    baseline_m = free + sum(
        (np.cross(p - datum, f) for p, f in zip(points, tangents, strict=True)),
        start=np.zeros(3),
    )
    a = float(X @ np.cross(points[0] - datum, N))
    b = float(X @ np.cross(points[1] - datum, N))
    f2_n = float((old_w[3] - baseline_m[0] - a * rn) / (b - a))
    components = [rn - f2_n, f2_n]
    new = []
    records = []
    for i, r in enumerate(old):
        force = tangents[i] + components[i] * N
        new.append({**r, "point_mm": points[i].tolist(), "force_n": force.tolist()})
        record = {
            "case_id": case,
            "block": interface["block"],
            "axis_id": r["axis_id"],
            "old_lateral_n": r["force_resultant_n"],
            "proposed_lateral_n": float(np.linalg.norm(force)),
            "proposed_force_xyz_n": force.tolist(),
            "proposed_force_N_T_n": [float(N @ force), float(T @ force)],
            "bearing_parallel_perpendicular_psi": [
                11200 * 0.5,
                6100 * 0.5**1.45 / math.sqrt(5 / 16),
            ],
        }
        for fyb, key in [(45000, "45ksi"), (106000, "106ksi")]:
            ref = bolt_reference(force, 5 / 16, fyb)
            record["reference_" + key + "_n"] = ref["reference_n"]
            record["ratio_" + key] = record["proposed_lateral_n"] / ref["reference_n"]
        records.append(record)
    new_w = accounting.wrench(new, datum)
    residual = new_w - old_w
    require(np.max(abs(residual[:3])) < 1e-5, "changed pair resultant")
    require(np.max(abs(residual[3:])) < 1e-3, "changed pair moment")
    return records, {
        "case_id": case,
        "block": interface["block"],
        "datum_mm": datum.tolist(),
        "original_lateral_wrench_xyz_n_nmm": old_w.tolist(),
        "proposed_lateral_wrench_xyz_n_nmm": new_w.tolist(),
        "wrench_residual_xyz_n_nmm": residual.tolist(),
        "assumption": "Retain each original T force component; solve N components from total force and pair moment. Stiffness sharing is not recomputed.",
    }


def revised_side_host(host, source, bolts, proposals):
    """Replace the two old bore voids in an isolated proposal, then cut new ones."""
    shape = source
    fills = []
    for bolt in bolts:
        old = np.array(bolt["source_point_xyz_mm"])
        axis = local.unit(bolt["axis_xyz"])
        geometry = bolt["source_record"]["geometry"]
        underhead = old - axis * geometry["modeled_shaft_occupied_length_mm"] / 2
        interval = next(
            r for r in geometry["wood_receiver_intervals"] if r["receiver_id"] == host
        )
        spans = interval["current_shaft_intersection_solid_intervals_from_underhead_mm"]
        require(len(spans) == 1, "host bore has multiple bearing intervals")
        lo, hi = spans[0]
        radius = next(
            r for r in bolt["receiver_clearance_geometry"] if r["receiver_id"] == host
        )["unique_bore_radius_mm"]
        fill = cylinder(underhead + lo * axis, axis, radius, hi - lo)
        shape = shape.fuse(fill).clean()
        fills.append(math.pi * radius**2 * (hi - lo))
    require(
        abs(shape.Volume() - source.Volume() - sum(fills)) < 1e-3,
        "old bore replacement changed other host features",
    )
    removed = []
    for bolt in bolts:
        axis = local.unit(bolt["axis_xyz"])
        proposal = next(r for r in proposals if r["axis_id"] == bolt["axis_id"])
        point = np.array(proposal["proposed_axis_point_mm"])
        cutter = cylinder(point - 300 * axis, axis, SIDE_BORE / 2, 600)
        before = shape.Volume()
        shape = shape.cut(cutter).clean()
        removed.append(before - shape.Volume())
    expected = math.pi * (SIDE_BORE / 2) ** 2 * 88.9
    require(
        all(abs(v - expected) < 1e-3 for v in removed),
        "new bore intersects another host feature or leaves receiver",
    )
    require(shape.isValid() and len(shape.Solids()) == 1, "invalid proposed host")
    return shape, {
        "host": host,
        "old_bore_void_volumes_replaced_mm3": fills,
        "new_bore_void_volumes_mm3": removed,
        "finished_host_volume_mm3": shape.Volume(),
        "scope": "An alternative drilling layout for new stock; not filling or reworking a delivered timber. Other archived host features are retained.",
    }


def tool_approach_scenarios(proposals, shapes, inputs):
    """Sixteen straight cylindrical tool approaches against proposed wood/shafts."""
    rows = []
    own_ids = {r["axis_id"] for p in proposals for r in p["axes"]}
    source_shafts = {}
    for bolt in inputs["connections"]:
        if bolt["kind"] != "candidate_bolt" or bolt["axis_id"] in own_ids:
            continue
        g = bolt["source_record"]["geometry"]
        axis = local.unit(bolt["axis_xyz"])
        length = g["modeled_shaft_occupied_length_mm"]
        start = np.array(g["shaft_center_global_xyz_mm"]) - length * axis / 2
        source_shafts[bolt["axis_id"]] = cylinder(
            start, axis, g["modeled_shaft_diameter_mm"] / 2, length
        )
    for prop in proposals:
        block = prop["block"]
        # Recover the rail interface from the raw block datum, not its
        # finished center of mass, which is displaced slightly by the bores.
        source_center = next(
            r["reduced_geometry_descriptor"]
            for r in inputs["members"]
            if r["member_id"] == block
        )
        cleat_center = (
            np.array(source_center["start"]) + source_center["end"]
        ) / 2 + NEW_T_CENTER * T
        left = block.endswith("left_cleat")
        for r in prop["axes"]:
            point = np.array(r["proposed_axis_point_mm"])
            side = "/side_" in r["axis_id"]
            direction = (X if left else -X) if side else -T
            diameter = SIDE_D if side else 6.35
            washer = 2.6416 if side else 2.032
            nut = 6.7469 if side else 5.7404
            if side:
                contact_x = -1130.3 if left else 1127.125
                wood_entry = point.copy()
                wood_entry[0] = contact_x - direction[0] * 88.9
            else:
                rail_outer_t = 139.7 / 2 + 38.1
                wood_entry = (
                    point + (rail_outer_t - float(T @ (point - cleat_center))) * T
                )
            underhead = wood_entry - washer * direction
            tip = underhead + 203.2 * direction
            for end, origin, outward in [
                ("head", underhead, -direction),
                ("nut", wood_entry + (177.8 + washer + nut) * direction, direction),
            ]:
                tool = cylinder(origin, outward, 12.7, 50)
                wood_hits = {
                    name: volume
                    for name, shape in shapes.items()
                    if (volume := overlap(tool, shape)) > 1e-4
                }
                shaft_hits = {
                    name: volume
                    for name, shape in source_shafts.items()
                    if (volume := overlap(tool, shape)) > 1e-4
                }
                rows.append(
                    {
                        "axis_id": r["axis_id"],
                        "end": end,
                        "tool_origin_mm": origin.tolist(),
                        "outward_axis_xyz": outward.tolist(),
                        "tool_diameter_mm": 25.4,
                        "tool_length_mm": 50,
                        "proposed_wood_hits_mm3": wood_hits,
                        "other_candidate_shaft_hits_mm3": shaft_hits,
                        "proposed_bolt_tip_mm": tip.tolist(),
                        "proposed_bolt_underhead_mm": underhead.tolist(),
                        "nominal_bolt_diameter_mm": diameter,
                        "scope": "Straight approach enclosure only; no turning sweep, withdrawal, installed head/nut/washer or retained-frame/hold hardware check.",
                    }
                )
    require(
        len(rows) == 16 and len(source_shafts) == 84, "incomplete approach scenario"
    )
    for row in rows:
        if row["end"] != "head":
            continue
        source_shafts[row["axis_id"]] = cylinder(
            np.array(row["proposed_bolt_underhead_mm"]),
            -np.array(row["outward_axis_xyz"]),
            row["nominal_bolt_diameter_mm"] / 2,
            203.2,
        )
    require(len(source_shafts) == 92, "missing proposed shafts")
    for row in rows:
        tool = cylinder(
            np.array(row["tool_origin_mm"]),
            np.array(row["outward_axis_xyz"]),
            12.7,
            50,
        )
        row["other_candidate_shaft_hits_mm3"] = {
            name: volume
            for name, shape in source_shafts.items()
            if name != row["axis_id"] and (volume := overlap(tool, shape)) > 1e-4
        }
    return rows


def preview(path):
    """Side view in the cleat grain/T plane, same geometry on both corners."""
    scale = 3.0

    def px(n):
        return 100 + (n + 59.85) * scale

    def py(t):
        return 105 + (44.45 - t) * scale

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="780" height="620" viewBox="0 0 780 620">',
        '<rect width="780" height="620" fill="#fff"/>',
        '<g font-family="sans-serif" fill="#172b3a">',
        '<text x="36" y="34" font-size="21">Top outer corner: isolated correction proposal</text>',
        '<text x="36" y="62" font-size="14">Both corners mirrored. No drilling or fabrication release.</text>',
        f'<rect x="{px(-59.85)}" y="{py(44.45)}" width="{119.7 * scale}" height="{139.7 * scale}" fill="#e9f2fa" stroke="#245c85" stroke-width="2"/>',
        f'<rect x="{px(-59.85)}" y="{py(44.45)}" width="{119.7 * scale}" height="{88.9 * scale}" fill="none" stroke="#657a8b" stroke-dasharray="7 5"/>',
    ]
    for t in [-16.45, 16.55]:
        svg.append(
            f'<circle cx="{px(0)}" cy="{py(t)}" r="{3.75 * scale}" fill="none" stroke="#657a8b" stroke-dasharray="3 2"/>'
        )
    for t in [NEW_T_CENTER - SIDE_PITCH / 2, NEW_T_CENTER + SIDE_PITCH / 2]:
        svg.append(
            f'<circle cx="{px(0)}" cy="{py(t)}" r="{SIDE_BORE / 2 * scale}" fill="#fff" stroke="#245c85" stroke-width="2"/>'
        )
    svg.extend(
        [
            '<text x="500" y="126" font-size="16">Rail-touching face fixed</text>',
            '<text x="500" y="180" font-size="15">Solid 4×6 stock</text>',
            '<text x="500" y="204" font-size="15">88.9 × 139.7 mm section</text>',
            '<text x="500" y="242" font-size="15">119.7 mm grain length</text>',
            '<text x="500" y="280" font-size="15">5/16-inch side bolts</text>',
            '<text x="500" y="304" font-size="15">67.85 mm center spacing</text>',
            '<text x="500" y="342" font-size="15">9 mm CAD bore envelope</text>',
            '<text x="500" y="366" font-size="15">Not a bit instruction</text>',
            '<text x="500" y="414" font-size="15">Dashed: reviewed 4×4</text>',
            '<text x="500" y="438" font-size="15">Solid: proposed 4×6</text>',
            '<text x="100" y="560" font-size="15">Grain →. Face viewed along side-bolt axis X.</text>',
            '<text x="100" y="588" font-size="15">Four existing rail bolts need 177.8 mm grips; their axes stay fixed.</text>',
            "</g></svg>",
        ]
    )
    path.write_text("\n".join(svg) + "\n")


def main():
    for path, expected in PINS.items():
        require(sha(path) == expected, "changed correction input: " + str(path))
    actions = read(ACTION_PATH)
    require(
        actions["producer_sha256"] == sha(Path(accounting.__file__)),
        "changed action producer",
    )
    inputs = read(lateral.INPUTS)
    members = {r["member_id"]: r for r in inputs["members"]}
    sources = {}
    for name, record in members.items():
        binding = record["current_finished_step_binding"]
        path = ROOT / binding["path"]
        require(sha(path) == binding["file_sha256"], "changed finished STEP")
        PINS[path] = binding["file_sha256"]
        sources[name] = cq.importers.importStep(str(path)).val()
    surface_rows = read(SURFACES)["records"]
    proposals = []
    geometries = {}
    host_replacements = []
    for block, (_, host) in accounting.BLOCK_HOSTS.items():
        bolts = [
            r
            for r in inputs["connections"]
            if r["kind"] == "candidate_bolt" and block in r["receiver_member_ids"]
        ]
        require(len(bolts) == 4, "missing top-corner axes")
        prop, shape = build_proposal(
            block,
            members[block]["reduced_geometry_descriptor"],
            bolts,
            sources,
            surface_rows,
        )
        for axis in prop["axes"]:
            if "/side_" in axis["axis_id"]:
                axis["host_geometry_comparators"] = side_geometry(
                    np.array(axis["proposed_axis_point_mm"]),
                    members[host]["reduced_geometry_descriptor"],
                    SIDE_PITCH,
                    False,
                )
        proposals.append(prop)
        geometries[block] = shape
        side_bolts = [r for r in bolts if "/side_" in r["axis_id"]]
        host_shape, host_record = revised_side_host(
            host, sources[host], side_bolts, prop["axes"]
        )
        geometries[host] = host_shape
        host_replacements.append(host_record)
    tool_scenarios = tool_approach_scenarios(
        proposals, {**sources, **geometries}, inputs
    )
    states, wrenches = [], []
    for case in actions["cases"]:
        for interface in case["interfaces"]:
            if not interface["host"].startswith("base_side_"):
                continue
            prop = next(r for r in proposals if r["block"] == interface["block"])
            rows, w = lateral_states(interface, prop, case["case_id"])
            states.extend(rows)
            wrenches.append(w)
    require(len(states) == 24 and len(wrenches) == 12, "incomplete six-case correction")
    output = HERE / "top-corner-correction"
    output.mkdir(exist_ok=True)
    preview(output / "side-view.svg")
    steps = {}
    for name, shape in geometries.items():
        path = output / (name + ".step")
        cq.exporters.export(shape, str(path))
        steps[str(path.relative_to(ROOT))] = sha(path)
    with (output / "lateral-states.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(states[0]))
        writer.writeheader()
        writer.writerows(states)
    result = {
        "schema": "top_corner_correction_proposal/v1",
        "status": "ISOLATED_FIXED_DEMAND_PROPOSAL_NOT_SELECTED",
        "source_candidate": actions["candidate"],
        "source_revision": actions["revision_id"],
        "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
        "producer_sha256": sha(Path(__file__)),
        "producer_dependency_sha256": {
            str(Path(module.__file__).relative_to(ROOT)): sha(Path(module.__file__))
            for module in [lateral, accounting, local]
        },
        "source_member_count": len(sources),
        "proposals": proposals,
        "side_host_bore_replacements": host_replacements,
        "straight_tool_approach_scenarios": tool_scenarios,
        "preserved_lateral_wrenches": wrenches,
        "states": states,
        "peak_by_block_106ksi": [
            max(
                (r for r in states if r["block"] == block),
                key=lambda r: r["ratio_106ksi"],
            )
            for block in accounting.BLOCK_HOSTS
        ],
        "proposal_step_sha256": steps,
        "lateral_csv_sha256": sha(output / "lateral-states.csv"),
        "side_preview_sha256": sha(output / "side-view.svg"),
        "counts": {
            "candidate_axes": 92,
            "moved_axes": 4,
            "larger_side_bolts": 4,
            "longer_rail_grips": 4,
            "retained_frame_bolts": 12,
            "Hillman_screw_axes": 66,
        },
        "normal_contact_and_axial_tie_sharing_recomputed": False,
        "whole_frame_redistribution_recomputed": False,
        "complete_joint_acceptance": False,
        "reviewed_geometry_changed": False,
        "physical_release": False,
        "limits": [
            "106 ksi remains an unadopted Grade 5 bending-yield estimate; 45 ksi is a separate hypothesis, not the proposed product property.",
            "Both pure-direction geometry comparators are met; oblique/group interaction and splitting still require a supported method.",
            "Source whole-frame actions are held fixed; new stiffness, self-weight, contact and tie redistribution remain to be computed.",
            "Proposed side-host bores are replaced in isolated STEP copies; bolt shanks/threads, washer resistance and complete installed-tool/withdrawal compatibility remain unqualified.",
            "The exported two cleats and two side hosts are proposal artifacts. They are not machining instructions or replacements for the reviewed scene.",
        ],
    }
    (output / "proposal.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    for r in result["peak_by_block_106ksi"]:
        print(
            r["block"],
            r["case_id"],
            "45ksi",
            round(r["ratio_45ksi"], 4),
            "106ksi",
            round(r["ratio_106ksi"], 4),
        )
    for p in proposals:
        print(
            p["block"],
            "wood conflicts",
            len(p["other_finished_wood_overlap_records"]),
            "service conflicts",
            len(p["extended_service_passage_overlap_records"]),
            "panel minimum mm",
            round(min(p["main_panel_clearances_mm"].values()), 4),
        )


if __name__ == "__main__":
    main()

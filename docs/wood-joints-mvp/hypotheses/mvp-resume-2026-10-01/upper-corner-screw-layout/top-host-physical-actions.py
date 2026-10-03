"""Parent-owned top-rail cuts with saved compatible local pressure placement.

Replace only original top-cleat rows. Uniform pressure on source-clipped
4x4 face tiles is an explicit MVP placement hypothesis. Host bores reuse
the declared half-cosine wall measure; washers retain saved quadrature.
No frame, contact, native or CAD solve occurs here.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/top-host-physical-actions"
MEMBER = BASE / "member-screen-attempt02/four-screw-layout01"
SECTION = HERE / "rawlocal/top-host-net-sections/attempt02"
FIRST = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
FACE = BASE / "top-corner-contact-geometry.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
HOST = "base_rail_top"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
PINS = {
    SECTION
    / "checks.json": "7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9",
    SECTION
    / "receipt.json": "486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29",
    SECTION
    / "producer.py.snapshot": "c8c6e3c23bfe5e7d6999160546bc8f6ad106c178219307aa1d984367fcd80364",
    HERE
    / "top-host-net-sections.py": "bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8",
    FIRST: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
    MEMBER
    / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    MEMBER
    / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBER
    / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    FACE: "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    BASE
    / "top_corner_contact.py": "a077c8636f504a2d4a7437f0f68722411c16911dbddc2734a96e444bf2b4655a",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    HERE
    / "operators-attempt02/model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    HERE
    / "corner-bore-wall.py": "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    HERE
    / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE
    / "upper-right-rail-pair.py": "4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96",
    HERE
    / "upper-left-block.py": "7b07b3f575b7c7cac6dc69dfef83b02ec06c8bac5990ebf1a58f74e807498f6f",
    HERE
    / "cleat-traction.py": "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
}
GEOM_TOL = 1e-5
PARTITION_TOL = 1e-6
# Preserve the existing local rail method's interface accounting tolerances.
FORCE_TOL, MOMENT_TOL = 0.001, 0.2
DURATIONS = {"original_CD1": 1.0, "conditional_peak_CD1_25": 1.25}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, f"frozen source differs: {path}")


def module(name):
    path = HERE / name
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(
        "physical_top_" + name.replace("-", "_"), path
    )
    require(spec is not None and spec.loader is not None, f"helper missing: {name}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def compare_wrench(actual, expected, label, force_tol=FORCE_TOL, moment_tol=MOMENT_TOL):
    error = np.array(actual) - expected
    require(
        np.isfinite(error).all()
        and max(abs(error[:3])) <= force_tol
        and max(abs(error[3:])) <= moment_tol,
        f"{label}: {error.tolist()}",
    )
    return error


def point_wrench(point, force, datum):
    force = np.array(force)
    return np.r_[force, np.cross(np.array(point) - datum, force)]


def disk_strip(low, high, center_g, center_v, radius):
    """Area and first moments of a circle restricted only in grain coordinate."""
    a, b = max(-radius, low - center_g), min(radius, high - center_g)
    if b <= a:
        return np.zeros(3)

    def area_primitive(x):
        return x * math.sqrt(max(0.0, radius**2 - x**2)) + radius**2 * math.asin(
            x / radius
        )

    area = area_primitive(b) - area_primitive(a)
    first_relative = (
        -2 / 3 * (max(0.0, radius**2 - b**2) ** 1.5 - max(0.0, radius**2 - a**2) ** 1.5)
    )
    return np.array([area, area * center_g + first_relative, area * center_v])


def supported_tile_integrals(bounds, bores, cut=None):
    """Source mask rectangle minus the known circular mouth fragments.

    Any circle partially intersecting a v boundary is refused; this bounded
    recipe relies on each recorded rail hole lying wholly in its v grid row.
    """
    g, v = np.array(bounds)
    high = g[1] if cut is None else min(g[1], cut)
    if high <= g[0]:
        return np.zeros(3)
    area = (high - g[0]) * (v[1] - v[0])
    value = np.array([area, area * (g[0] + high) / 2, area * np.mean(v)])
    for bore in bores:
        center_v, radius = bore["transverse_center_mm"], bore["radius_mm"]
        if center_v + radius <= v[0] or center_v - radius >= v[1]:
            continue
        require(
            center_v - radius >= v[0] - GEOM_TOL
            and center_v + radius <= v[1] + GEOM_TOL,
            f"unsupported circle crossing face-tile v boundary: {bore['axis_id']}, {bounds}",
        )
        value -= disk_strip(g[0], high, bore["station_mm"], center_v, radius)
    require(value[0] >= -0.001, f"negative supported face area: {bounds}")
    return value


def face_tiles(block, record, geometry, frame, rail_record, first_cases, identities):
    """Reconstruct the authenticated clipped 4x4 masks without loading CAD."""
    face = next(f for f in record["faces"] if f["host"] == HOST)
    corners = (np.array(face["corners_mm"]) - geometry["start"]) @ frame.T
    require(np.ptp(corners[:, 1]) < GEOM_TOL, f"nonplanar rail face: {block}")
    low, high = np.min(corners[:, [0, 2]], axis=0), np.max(corners[:, [0, 2]], axis=0)
    require(
        max(abs(high - low - [88.9, 119.7])) < GEOM_TOL,
        f"face envelope differs: {block}",
    )
    require(
        low[0] >= -GEOM_TOL
        and high[0]
        <= np.dot(np.array(geometry["end"]) - geometry["start"], frame[0]) + GEOM_TOL
        and low[1] >= -geometry["depth_mm"] / 2 - GEOM_TOL
        and high[1] <= geometry["depth_mm"] / 2 + GEOM_TOL,
        f"face polygon outside retained host stock: {block}",
    )
    require(
        all(
            any(max(abs(corner[[0, 2]] - [g, v])) < GEOM_TOL for corner in corners)
            for g in (low[0], high[0])
            for v in (low[1], high[1])
        ),
        f"unsupported nonrectangular face polygon: {block}",
    )
    plane_u = float(np.mean(corners[:, 1]))
    require(
        abs(plane_u + geometry["width_mm"] / 2) < GEOM_TOL,
        f"face is not supported rail u boundary: {block}",
    )
    bores = [
        b
        for b in rail_record["bores"]
        if b["station_mm"] + b["radius_mm"] > low[0]
        and b["station_mm"] - b["radius_mm"] < high[0]
    ]
    require(len(bores) == 2, f"two rail mouth circles required: {block}")
    expected_ids = {b["opening_id"] for b in bores}
    member_record = read(MEMBER / "geometry.json")["members"][HOST]
    unexpected = [
        b["id"]
        for b in member_record["bore_or_passage_intervals"]
        if b["id"] not in expected_ids and b["hi"] > low[0] and b["lo"] < high[0]
    ]
    require(
        not unexpected, f"unsupported additional face opening: {block}: {unexpected}"
    )
    template = first_cases[0]["hosts"][HOST]["state"]["face_cells"]
    require(
        len(template) == 16
        and all(identities[f["row"]]["row_id"] == f["row_id"] for f in template),
        f"face row binding differs: {block}",
    )
    tiles = []
    for k, cell in enumerate(template):
        source_index = 18 + k
        source_cell = record["rows"][source_index]
        require(
            source_cell["kind"] == "contact"
            and source_cell["host"] == HOST
            and cell["row_id"] == f"{block}/contact-cell-{source_index}"
            and source_cell["point_mm"] == cell["point_xyz_mm"]
            and source_cell["area_mm2"] == cell["area_mm2"],
            f"face recipe/source/operator join differs: {cell['row_id']}",
        )
        i, j = divmod(k, 4)
        bounds = [
            [
                float(low[0] + i * (high[0] - low[0]) / 4),
                float(low[0] + (i + 1) * (high[0] - low[0]) / 4),
            ],
            [
                float(low[1] + j * (high[1] - low[1]) / 4),
                float(low[1] + (j + 1) * (high[1] - low[1]) / 4),
            ],
        ]
        integral = supported_tile_integrals(bounds, bores)
        require(integral[0] > 0, f"empty supported face tile: {cell['row_id']}")
        center = np.array(geometry["start"]) + frame.T @ [
            integral[1] / integral[0],
            plane_u,
            integral[2] / integral[0],
        ]
        require(
            abs(integral[0] - cell["area_mm2"]) < 0.001
            and max(abs(center - cell["point_xyz_mm"])) < GEOM_TOL,
            f"source-clipped face area/centroid mismatch: {cell['row_id']}, area {integral[0]}, source {cell['area_mm2']}, centroid {center.tolist()}",
        )
        tiles.append(
            {
                "row": cell["row"],
                "row_id": cell["row_id"],
                "grid_index": [i, j],
                "mask_bounds_grain_v_mm": bounds,
                "plane_u_mm": plane_u,
                "bores": bores,
                "source_area_mm2": cell["area_mm2"],
                "source_point_global_xyz_mm": cell["point_xyz_mm"],
                "source_force_direction_on_cleat_xyz": source_cell["direction_xyz"],
                "analytic_supported_area_mm2": float(integral[0]),
                "analytic_supported_centroid_global_xyz_mm": center.tolist(),
            }
        )
    require(
        abs(
            sum(t["analytic_supported_area_mm2"] for t in tiles)
            - face["exact_finished_area_mm2"]
        )
        < 0.001,
        f"finished face area mismatch: {block}",
    )
    return tiles


def face_negative(tiles, host, geometry, frame, station, datum):
    total, records = np.zeros(6), []
    saved = {f["row_id"]: f for f in host["state"]["face_cells"]}
    actions = {
        a["identity"]: a
        for a in host["physical_host_actions"]
        if a["kind"] == "face_cell"
    }
    for tile in tiles:
        cell, action = saved[tile["row_id"]], actions[tile["row_id"]]
        require(
            cell["area_mm2"] == tile["source_area_mm2"]
            and cell["point_xyz_mm"] == tile["source_point_global_xyz_mm"],
            f"per-case face geometry differs: {tile['row_id']}",
        )
        integral = supported_tile_integrals(
            tile["mask_bounds_grain_v_mm"], tile["bores"], station
        )
        fraction = float(integral[0] / tile["analytic_supported_area_mm2"])
        force = np.array(action["force_xyz_n"])
        require(
            action["point_xyz_mm"] == cell["point_xyz_mm"]
            and cell["compression_n"] >= 0
            and cell["pressure_mpa"] >= 0
            and abs(cell["pressure_mpa"] * cell["area_mm2"] - cell["compression_n"])
            < FORCE_TOL
            and max(
                abs(
                    force
                    + cell["compression_n"]
                    * np.array(tile["source_force_direction_on_cleat_xyz"])
                )
            )
            < FORCE_TOL,
            f"face force/pressure binding differs: {tile['row_id']}",
        )
        if integral[0] > 0:
            center = np.array(geometry["start"]) + frame.T @ [
                integral[1] / integral[0],
                tile["plane_u_mm"],
                integral[2] / integral[0],
            ]
            value = point_wrench(center, fraction * force, datum)
            total += value
        else:
            center, value = None, np.zeros(6)
        records.append(
            {
                "row_id": tile["row_id"],
                "uniform_pressure_mpa": float(
                    np.linalg.norm(force) / tile["analytic_supported_area_mm2"]
                ),
                "saved_cell_pressure_mpa": cell["pressure_mpa"],
                "negative_supported_area_fraction": fraction,
                "negative_supported_centroid_global_xyz_mm": None
                if center is None
                else center.tolist(),
                "negative_external_wrench_global_n_nmm": value.tolist(),
            }
        )
    return total, records


def bore_profiles(host, geom, wall):
    profiles = []
    actions = [
        a
        for a in host["physical_host_actions"]
        if a["kind"] == "bore_station_resultant"
    ]
    for bolt in host["state"]["bolts"]:
        own = [a for a in actions if a["identity"] == bolt["axis_id"]]
        fields = [f for f in bolt["bore_fields"] if f["receiver"] == "host"]
        require(
            len(own) == len(fields) == 24,
            f"host bore measure census differs: {bolt['axis_id']}",
        )
        bore = next(b for b in geom["bores"] if b["axis_id"] == bolt["axis_id"])
        axis = bolt["bolt_axis_head_to_nut_xyz"]
        for index, (action, field) in enumerate(zip(own, fields, strict=True)):
            expected_point = np.array(bolt["interface_point_xyz_mm"]) + (
                field["x_mm"] - host["geometry"]["host_length_mm"]
            ) * np.array(axis)
            require(
                max(abs(np.array(action["force_xyz_n"]) + field["force_on_beam_xyz_n"]))
                < 1e-8
                and max(abs(np.array(action["point_xyz_mm"]) - expected_point)) < 1e-8,
                f"host bore force binding differs: {bolt['axis_id']}/{index}",
            )
            certificate = wall.wall_support(
                action["point_xyz_mm"], axis, bore["radius_mm"], geom, bolt["axis_id"]
            )
            profile = wall.pressure_profile(
                action["point_xyz_mm"],
                action["force_xyz_n"],
                axis,
                bore["radius_mm"],
                field["quadrature_weight_mm"],
                identity=bolt["axis_id"],
                support=certificate,
            )
            profile["quadrature_index"] = index
            profile["source_axis_bearing_pressure_mpa"] = field["pressure_mpa"]
            profiles.append(profile)
    return profiles


def washer_actions(host, geom, frame):
    """Bind the saved finite measures to supported host washer footprints."""
    actions = [
        a
        for a in host["physical_host_actions"]
        if a["kind"] == "outer_wood_washer_quadrature"
    ]
    require(len(actions) == 512, "512 host washer measures required")
    width, depth = geom["width_depth_mm"]
    for bolt in host["state"]["bolts"]:
        own = [a for a in actions if a["identity"] == bolt["axis_id"]]
        require(
            len(own) == 256 and {a["quadrature_index"] for a in own} == set(range(256)),
            f"host washer measure census differs: {bolt['axis_id']}",
        )
        bore = next(b for b in geom["bores"] if b["axis_id"] == bolt["axis_id"])
        for action in own:
            local = frame @ (np.array(action["point_xyz_mm"]) - geom["start_xyz_mm"])
            radial = math.hypot(
                local[0] - bore["station_mm"],
                local[2] - bore["transverse_center_mm"],
            )
            require(
                action["end"] == "host_head"
                and abs(local[1] - width / 2) < GEOM_TOL
                and -GEOM_TOL <= local[0] <= geom["grain_length_mm"] + GEOM_TOL
                and abs(local[2]) <= depth / 2 + GEOM_TOL
                and host["geometry"]["washer_ID_max_mm"] / 2 - GEOM_TOL
                <= radial
                <= host["geometry"]["washer_OD_min_mm"] / 2 + GEOM_TOL
                and all(
                    math.hypot(
                        local[0] - other["station_mm"],
                        local[2] - other["transverse_center_mm"],
                    )
                    >= other["radius_mm"] - GEOM_TOL
                    for other in geom["bores"]
                ),
                f"unsupported saved host washer point: {bolt['axis_id']}/{action['quadrature_index']}",
            )
            require(
                action["pressure_mpa"] >= 0
                and action["quadrature_area_mm2"] > 0
                and max(
                    abs(
                        np.array(action["force_xyz_n"])
                        - action["pressure_mpa"]
                        * action["quadrature_area_mm2"]
                        * np.array(bolt["bolt_axis_head_to_nut_xyz"])
                    )
                )
                < FORCE_TOL,
                f"washer pressure/force binding differs: {bolt['axis_id']}/{action['quadrature_index']}",
            )
    return actions


def replacement_negative(
    host, profiles, washers, tiles, geometry, geom, frame, section, before, wall
):
    station = section["station_mm"]
    datum = np.array(geometry["start"]) + station * frame[0]
    values = {"washer_quadrature": np.zeros(6), "bore_wall": np.zeros(6)}
    for action in washers:
        delta = float(np.dot(np.array(action["point_xyz_mm"]) - datum, frame[0]))
        if delta > PARTITION_TOL or (before and abs(delta) <= PARTITION_TOL):
            continue
        values["washer_quadrature"] += point_wrench(
            action["point_xyz_mm"], action["force_xyz_n"], datum
        )
    for profile in profiles:
        arcs = wall.cut_pressure_arcs(profile, geom, section)
        full = np.sum([a["boundary_wrench_at_cut_n_nmm"] for a in arcs], axis=0)
        compare_wrench(
            full,
            wall.pressure_arc_wrench(profile, datum),
            "host radial full force/moment recovery",
            1e-7,
            1e-6,
        )
        for arc in arcs:
            if arc["grain_half"] == "negative":
                values["bore_wall"] += arc["boundary_wrench_at_cut_n_nmm"]
    values["supported_uniform_face"], face_records = face_negative(
        tiles, host, geometry, frame, station, datum
    )
    return (
        sum(values.values(), start=np.zeros(6)),
        {k: v.tolist() for k, v in values.items()},
        face_records,
    )


def build(output: str | Path) -> dict:
    output = Path(output).resolve()
    require(
        output.is_relative_to(RAW.resolve())
        and output != RAW.resolve()
        and not output.exists(),
        "fresh owned raw output child required",
    )
    producer = Path(__file__).resolve()
    pins = {**PINS, producer: sha(producer)}
    authenticate(pins)
    (
        source,
        old_receipt,
        first,
        face_geometry,
        member_results,
        member_geometry,
        identities,
    ) = (
        read(path)
        for path in (
            SECTION / "checks.json",
            SECTION / "receipt.json",
            FIRST,
            FACE,
            MEMBER / "member-results.json",
            MEMBER / "geometry.json",
            ROWS,
        )
    )
    require(
        old_receipt["output_sha256"]
        == {
            name: pins[SECTION / name]
            for name in ("checks.json", "producer.py.snapshot")
        },
        "section receipt differs",
    )
    require(
        face_geometry["producer_sha256"] == pins[BASE / "top_corner_contact.py"],
        "finite face recipe binding differs",
    )
    old_path = str((HERE / "top-host-net-sections.py").relative_to(ROOT))
    for relative, digest in source["source_sha256"].items():
        if relative == old_path:
            require(
                digest == pins[SECTION / "producer.py.snapshot"],
                "old section producer binding differs",
            )
            continue
        path = ROOT / relative
        require(
            path not in pins or pins[path] == digest,
            f"conflicting inherited source: {relative}",
        )
        pins[path] = digest
    for relative, digest in face_geometry["source_sha256"].items():
        path = ROOT / relative
        require(
            path not in pins or pins[path] == digest,
            f"conflicting face geometry source: {relative}",
        )
        pins[path] = digest
    authenticate(pins)
    previous, nominal, wall = (
        module("top-host-net-sections.py"),
        module("corner-net-section.py"),
        module("corner-bore-wall.py"),
    )
    require(
        (previous.GEOM_TOL, previous.PARTITION_TOL) == (GEOM_TOL, PARTITION_TOL),
        "source bookkeeping tolerances differ",
    )
    geometry = member_geometry["members"][HOST]["geometry"]
    rail_record = source["geometry"][HOST]
    frame = np.array(rail_record["grain_frame_rows_xyz"])
    geom = {
        **rail_record,
        "start_xyz_mm": geometry["start"],
        "grain_length_mm": float(
            np.dot(np.array(geometry["end"]) - geometry["start"], frame[0])
        ),
    }
    sections = source["opening_sections"][HOST]
    require(len(sections) == 12, "twelve saved rail stations required")
    require(
        tuple(c["case_id"] for c in member_results["cases"]) == CASES,
        "six original member cases differ",
    )
    row_map = {r["row"]: r for r in identities}
    by_side, tiles_by_side = {}, {}
    for side in ("left", "right"):
        states = [s for s in first["states"] if s["side"] == side]
        require(
            tuple(s["case_id"] for s in states) == CASES,
            f"six saved local cases differ: {side}",
        )
        by_side[side] = {s["case_id"]: s["hosts"][HOST] for s in states}
        block = "top_outer_" + side + "_cleat"
        face_record = next(c for c in face_geometry["cleats"] if c["block"] == block)
        tiles_by_side[side] = face_tiles(
            block, face_record, geometry, frame, rail_record, states, row_map
        )
    record = member_geometry["members"][HOST]
    cuts, summaries, groups = [], [], []
    accounting = {
        "maximum_group_replacement_force_error_n": 0.0,
        "maximum_group_replacement_moment_error_nmm": 0.0,
        "maximum_pressure_representation_force_error_n": 0.0,
        "maximum_pressure_representation_moment_error_nmm": 0.0,
        "maximum_regional_force_recovery_error_n": 0.0,
        "maximum_regional_moment_recovery_error_nmm": 0.0,
    }
    with np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays:
        points, stations, point_rows = (
            arrays[HOST + suffix]
            for suffix in ("__point_xyz_mm", "__point_stations_mm", "__point_rows")
        )
        for case in member_results["cases"]:
            case_id = case["case_id"]
            row = next(m for m in case["members"] if m["member"] == HOST)
            values = arrays[row["array_prefix"] + "__point_force_free_couple_xyz"]
            saved_negative = arrays[
                row["array_prefix"] + "__internal_negative_grain_u_v"
            ]
            removed, profiles_by_side, washers_by_side = {}, {}, {}
            for side in ("left", "right"):
                host, block = by_side[side][case_id], "top_outer_" + side + "_cleat"
                own = np.array(
                    [other == block for other in record["point_action_other_bodies"]]
                )
                require(
                    sum(own) == 22, f"original incident row census differs: {block}"
                )
                expected_rows = (
                    set(range(1800, 1804)) | set(range(1834, 1852))
                    if side == "left"
                    else set(range(1808, 1812)) | set(range(1870, 1888))
                )
                require(
                    {int(x) for x in point_rows[own]} == expected_rows
                    and all(
                        row_map[int(point_rows[i])]["row_id"]
                        == record["point_action_ids"][i]
                        and {
                            row_map[int(point_rows[i])]["ownership"]["first_body"],
                            row_map[int(point_rows[i])]["ownership"]["second_body"],
                        }
                        == {HOST, block}
                        for i in np.flatnonzero(own)
                    ),
                    f"removed source row IDs differ: {block}",
                )
                removed[side] = own
                original = np.sum(
                    np.column_stack(
                        [
                            values[own, :3],
                            np.cross(points[own] - geometry["start"], values[own, :3])
                            + values[own, 3:],
                        ]
                    ),
                    axis=0,
                )
                replacement = sum(
                    (
                        point_wrench(
                            a["point_xyz_mm"],
                            a["force_xyz_n"],
                            np.array(geometry["start"]),
                        )
                        for a in host["physical_host_actions"]
                    ),
                    start=np.zeros(6),
                )
                error = compare_wrench(
                    replacement,
                    original,
                    f"whole-host target replacement: {block}/{case_id}",
                )
                accounting["maximum_group_replacement_force_error_n"] = max(
                    accounting["maximum_group_replacement_force_error_n"],
                    float(max(abs(error[:3]))),
                )
                accounting["maximum_group_replacement_moment_error_nmm"] = max(
                    accounting["maximum_group_replacement_moment_error_nmm"],
                    float(max(abs(error[3:]))),
                )
                profiles_by_side[side] = bore_profiles(host, geom, wall)
                washers_by_side[side] = washer_actions(host, geom, frame)
                require(
                    len(host["physical_host_actions"]) == 576,
                    f"576 physical host actions required: {block}/{case_id}",
                )
                full_datum = np.array(geometry["start"])
                full_face, _ = face_negative(
                    tiles_by_side[side],
                    host,
                    geometry,
                    frame,
                    geom["grain_length_mm"] + 1,
                    full_datum,
                )
                full_by_kind = {
                    "supported_uniform_face": full_face,
                    "bore_wall": sum(
                        (
                            wall.pressure_arc_wrench(p, full_datum)
                            for p in profiles_by_side[side]
                        ),
                        start=np.zeros(6),
                    ),
                    "washer_quadrature": sum(
                        (
                            point_wrench(
                                a["point_xyz_mm"], a["force_xyz_n"], full_datum
                            )
                            for a in washers_by_side[side]
                        ),
                        start=np.zeros(6),
                    ),
                }
                represented = sum(full_by_kind.values(), start=np.zeros(6))
                representation_error = compare_wrench(
                    represented,
                    replacement,
                    f"supported full pressure placement recovery: {block}/{case_id}",
                )
                accounting["maximum_pressure_representation_force_error_n"] = max(
                    accounting["maximum_pressure_representation_force_error_n"],
                    float(max(abs(representation_error[:3]))),
                )
                accounting["maximum_pressure_representation_moment_error_nmm"] = max(
                    accounting["maximum_pressure_representation_moment_error_nmm"],
                    float(max(abs(representation_error[3:]))),
                )
                groups.append(
                    {
                        "case": case_id,
                        "side": side,
                        "removed_rows": sorted(expected_rows),
                        "removed_row_ids": [
                            record["point_action_ids"][i] for i in np.flatnonzero(own)
                        ],
                        "original_full_external_wrench_at_start_global_n_nmm": original.tolist(),
                        "current_full_external_wrench_at_start_global_n_nmm": replacement.tolist(),
                        "replacement_minus_original_global_n_nmm": error.tolist(),
                        "represented_full_pressure_wrench_at_start_global_n_nmm": represented.tolist(),
                        "pressure_representation_minus_saved_global_n_nmm": representation_error.tolist(),
                        "represented_full_external_by_kind_global_n_nmm": {
                            k: v.tolist() for k, v in full_by_kind.items()
                        },
                        "physical_host_actions": host["physical_host_actions"],
                        "host_bore_pressure_profiles": profiles_by_side[side],
                    }
                )
            for section in sections:
                for index in (
                    2 * section["saved_station_index"],
                    2 * section["saved_station_index"] + 1,
                ):
                    before = index % 2 == 0
                    original_cut, datum = previous.global_cut(
                        values,
                        points,
                        stations,
                        geometry,
                        section["station_mm"],
                        before,
                    )
                    original_local = np.r_[
                        frame @ original_cut[:3], frame @ original_cut[3:]
                    ]
                    compare_wrench(
                        original_local,
                        saved_negative[index],
                        "original full signed cut replay",
                        1e-7,
                        1e-5,
                    )
                    revised, replacement_records = original_cut.copy(), []
                    for side in ("left", "right"):
                        own = removed[side]
                        old_internal, _ = previous.global_cut(
                            values[own],
                            points[own],
                            stations[own],
                            geometry,
                            section["station_mm"],
                            before,
                        )
                        new_negative, by_kind, face_records = replacement_negative(
                            by_side[side][case_id],
                            profiles_by_side[side],
                            washers_by_side[side],
                            tiles_by_side[side],
                            geometry,
                            geom,
                            frame,
                            section,
                            before,
                            wall,
                        )
                        revised -= old_internal + new_negative
                        replacement_records.append(
                            {
                                "side": side,
                                "old_negative_external_wrench_global_n_nmm": (
                                    -old_internal
                                ).tolist(),
                                "current_negative_external_wrench_global_n_nmm": new_negative.tolist(),
                                "current_negative_external_by_kind_global_n_nmm": by_kind,
                                "finite_face_negative_records": face_records,
                            }
                        )
                    local = np.r_[frame @ revised[:3], frame @ revised[3:]]
                    duration_results = {}
                    for scenario, duration in DURATIONS.items():
                        refs = {
                            k: v * duration
                            for k, v in source["conditional_material_by_host"][HOST][
                                "CF_only_reference_mpa"
                            ].items()
                        }
                        result = nominal.nominal_section(
                            local, section["regions"], refs
                        )
                        result["references"] = refs
                        face_results = [
                            previous.region_faces(
                                r,
                                refs,
                                {"cut_datum_global_xyz_mm": datum.tolist()},
                                frame,
                            )
                            for r in result["regions"]
                        ]
                        deciding = max(
                            face_results,
                            key=lambda r: r["face_peak"]["combined_shear_over_Fv"],
                        )
                        normal = max(
                            c["comparisons"]["axial_plus_bending_reference_sum"]
                            for r in result["regions"]
                            for c in r["longitudinal_corners"]
                        )
                        summary = {
                            "case": case_id,
                            "station_mm": section["station_mm"],
                            "limit": "before" if before else "after",
                            "saved_trace_index": index,
                            "duration_scenario": scenario,
                            "CD": duration,
                            "normal_reference_sum": normal,
                            "compatible_face_peak_over_Fv": deciding["face_peak"][
                                "combined_shear_over_Fv"
                            ],
                            "scalar_shear_bound_over_Fv": max(
                                r["same_state_shear_bound_over_Fv"]
                                for r in result["regions"]
                            ),
                            "sufficient_rectangle_bound_over_Fv": max(
                                r["sufficient_all_section_bound_over_Fv"]
                                for r in face_results
                            ),
                            "deciding_region_id": deciding["region_id"],
                            "deciding_face": deciding["face_peak"],
                        }
                        summaries.append(summary)
                        duration_results[scenario] = {
                            "summary": summary,
                            "nominal_section": result,
                            "regional_faces": face_results,
                        }
                        recovery = result["reconstructed_minus_source_n_nmm"]
                        accounting["maximum_regional_force_recovery_error_n"] = max(
                            accounting["maximum_regional_force_recovery_error_n"],
                            max(abs(x) for x in recovery[:3]),
                        )
                        accounting["maximum_regional_moment_recovery_error_nmm"] = max(
                            accounting["maximum_regional_moment_recovery_error_nmm"],
                            max(abs(x) for x in recovery[3:]),
                        )
                    cuts.append(
                        {
                            "case": case_id,
                            "station_mm": section["station_mm"],
                            "saved_trace_index": index,
                            "cut_datum_global_xyz_mm": datum.tolist(),
                            "original_integrated_point_cut_global_n_nmm": original_cut.tolist(),
                            "current_pressure_cut_global_n_nmm": revised.tolist(),
                            "current_pressure_cut_grain_u_v_n_nmm": local.tolist(),
                            "replacement_negative_records": replacement_records,
                            "duration_results": duration_results,
                        }
                    )
    require(
        len(cuts) == 144 and len(summaries) == 288 and len(groups) == 12,
        "finite physical replacement census differs",
    )
    comparison = {}
    for scenario, duration in DURATIONS.items():
        own = [r for r in summaries if r["duration_scenario"] == scenario]
        comparison[scenario] = {
            "CD": duration,
            "global_peaks": {
                k: max(own, key=lambda r: r[k])
                for k in (
                    "normal_reference_sum",
                    "compatible_face_peak_over_Fv",
                    "scalar_shear_bound_over_Fv",
                    "sufficient_rectangle_bound_over_Fv",
                )
            },
            "face_exceeding_trace_count": sum(
                r["compatible_face_peak_over_Fv"] > 1 for r in own
            ),
            "all_sufficient_rectangle_bounds_below_one": all(
                r["sufficient_rectangle_bound_over_Fv"] <= 1 for r in own
            ),
            "per_case": [
                {
                    "case": case_id,
                    "face_peak": max(
                        [r for r in own if r["case"] == case_id],
                        key=lambda r: r["compatible_face_peak_over_Fv"],
                    ),
                }
                for case_id in CASES
            ],
        }
    report = {
        "schema": "top-rail-current-local-pressure-cuts-v1",
        "status": "COMPLETE_FINITE_TOP_RAIL_LOCAL_PRESSURE_COMPARISONS",
        **previous.FLAGS,
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in pins.items()
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "case_ids": list(CASES),
        "recorded_section_count": 12,
        "evaluated_trace_count": 144,
        "duration_comparison_count": 288,
        "source_force_state_scope": source["source_force_state_scope"],
        "source_hold_lever_mm": 100,
        "working_hypotheses": [
            "Uniform pressure on each source-supported clipped face tile is an owner-directed MVP placement hypothesis. The authenticated 4x4 CAD mask recipe is reconstructed analytically by subtracting only the known circular bore mouths; every saved clipped area and centroid must match. No pressure crosses a void.",
            "Host bore force vectors retain all original axial Gauss measures; angular half-cosine radial pressure is the same explicit nonunique shape already used by the frozen cleat wall helper.",
            "Host washer pressure uses the exact saved 512 weighted quadrature measures per interface. No new continuous pressure fit, added beam-end rocking couple or axial tie is superposed.",
            *source["working_hypotheses"],
        ],
        "limits": [
            "No new frame/contact/native/CAD response, geometry or material law. Current local host allocation preserves original interface wrenches without global displacement feedback.",
            "Washer half-cut placement is the frozen 8-radial/32-angular quadrature measure, not a continuously integrated annulus or a cut-error envelope; unsupported pressure interpolation is not invented.",
            "Finite 12 bore/tangency stations only. Nominal ligament sharing/common strain/twist, local concentration/splitting, free warping, actual timber/hardware and nonunique global pose boundaries remain unqualified.",
            "Original integrated-point sensitivities remain preserved in top-host-net-sections attempt02/03; these conditional pressure cuts do not rewrite authority or release criteria.",
        ],
        "face_tiles": tiles_by_side,
        "whole_interface_accounting": groups,
        "accounting": accounting,
        "duration_comparison": comparison,
        "cuts": cuts,
    }
    authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    dump(output / "checks.json", report)
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    dump(
        output / "receipt.json",
        {
            "status": report["status"],
            **previous.FLAGS,
            "source_sha256": report["source_sha256"],
            "output_sha256": {
                name: sha(output / name)
                for name in ("checks.json", "producer.py.snapshot")
            },
        },
    )
    return {
        "status": report["status"],
        "output": str(output.relative_to(ROOT)),
        "checks_sha256": sha(output / "checks.json"),
        "receipt_sha256": sha(output / "receipt.json"),
        "accounting": accounting,
        "duration_comparison": comparison,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2, sort_keys=True))

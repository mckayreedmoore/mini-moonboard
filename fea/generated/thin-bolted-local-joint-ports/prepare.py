"""Geometry-only local cut/datum and crossing-duty contract; no CAD/K/forces."""

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
OWN = Path(__file__).resolve()
OUT = OWN.with_name("input.json")
PATHS = {
    "layout": PACKET / "mixed-offset-rows-shallow-wires-v4.json",
    "cache": PACKET / "native-geometry-v4.json",
    "reference_geometry": PACKET / "compatible-frame-a12-rear-finished-floor-v4.json",
    "inventory": ROOT / "fea/generated/thin-bolted-v4-geometry/timber-bolt-resistance-v4-full.json",
    "timber_faces": PACKET / "timber-face-contact-geometry-v4.json",
}
EXPECTED = {
    "layout": "8174841bf64914570397ee6d960c5602f74097e2e412e5910502811bc5b9405c",
    "cache": "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
    "reference_geometry": "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d",
    "inventory": "e79e78a769b0e2423e4ef828c973974e38be4518cba94593dc225fe922ae6631",
    "timber_faces": "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    assert all(sha(PATHS[k]) == expected for k, expected in EXPECTED.items())
    source = {key: json.loads(path.read_text()) for key, path in PATHS.items()}
    layout, geometry = source["layout"], source["reference_geometry"]
    samples = {r["member"]: r for r in source["inventory"]["finished_geometry_queries"]["finished_member_sections"]}
    cache = {r["id"]: r for r in source["cache"]["parts"]}
    members = {}
    for name in ("base_header", "base_side_left", "base_principal_center_left", "base_post_center_left"):
        elements = [r for r in geometry["member_element_actions"] if r["member"] == name]
        frame = np.asarray(elements[0]["basis_grain_u_v_xyz"], dtype=float)
        assert np.linalg.norm(frame @ frame.T - np.eye(3)) < 1e-10 and np.linalg.det(frame) > .999999999
        members[name] = {"member": name, "grain_frame_rows_xyz": frame.tolist(),
            "reference_centerline_start_xyz_mm": elements[0]["start_xyz_mm"],
            "reference_centerline_end_xyz_mm": elements[-1]["end_xyz_mm"],
            "finished_brep_path": cache[name]["path"], "finished_brep_sha256": cache[name]["sha256"]}

    def remote(member, station, retained_side):
        row = next(r for r in samples[member]["sampled_sections"]
                   if abs(r["station_global_grain_projection_mm"] - station) < 1e-7)
        assert row["raw_full_cross_section_plane"] and abs(row["finished_area_mm2"] - row["raw_area_mm2"]) < 1e-4
        g = np.asarray(members[member]["grain_frame_rows_xyz"][0])
        start = np.asarray(members[member]["reference_centerline_start_xyz_mm"])
        datum = start + g * (station - start @ g)
        assert abs(datum @ g - station) < 1e-8
        return {"member": member, "station_global_grain_projection_mm": station,
            "datum_reference_xyz_mm": datum.tolist(), "retained_material_side": retained_side,
            "grain_frame_rows_xyz": members[member]["grain_frame_rows_xyz"],
            "finished_area_mm2": row["finished_area_mm2"], "raw_full_cross_section_plane": True,
            "saved_finished_area_equals_raw_area": True, "no_local_bolt_section_loss_at_saved_plane": True,
            "actual_section_centroid_inertia_or_continuous_pressure_qualified": False,
            "all_contact_duties_avoided": False, "Saint_Venant_or_boundary_stiffness_qualified": False}

    specs = [
        ("outerbase-left", ["base_header", "base_side_left"], [19, 20],
         ["B104ZN_clip_angle_base_left_reference"],
         [remote("base_header", -613.246875, "negative-grain"),
          remote("base_side_left", 225.417272, "negative-grain")]),
        ("sharedcenter-left", ["base_header", "base_principal_center_left", "base_post_center_left"], [11, 12, 13],
         ["B104ZN_clip_split_base_center_left_reference", "B104ZN_clip_split_header_center_left_reference"],
         [remote("base_header", -613.246875, "positive-grain"),
          remote("base_header", -3.571875, "negative-grain"),
          remote("base_principal_center_left", 236.3532073, "negative-grain"),
          remote("base_post_center_left", 85.31875, "positive-grain")]),
    ]
    patches = []
    for identifier, timbers, numbers, fittings, ports in specs:
        bounds = {}
        for member in timbers:
            g = np.asarray(members[member]["grain_frame_rows_xyz"][0])
            bounds[member] = [float(np.asarray(members[member]["reference_centerline_start_xyz_mm"]) @ g),
                              float(np.asarray(members[member]["reference_centerline_end_xyz_mm"]) @ g)]
        for p in ports:
            bounds[p["member"]][0 if p["retained_material_side"] == "positive-grain" else 1] = p["station_global_grain_projection_mm"]

        def inside(member, point, bounds=bounds):
            station = float(np.asarray(point) @ np.asarray(members[member]["grain_frame_rows_xyz"][0]))
            lo, hi = bounds[member]
            return station, lo <= station <= hi

        bolts, screws, contacts = [], [], {}
        for axis in layout["installed_axes"]:
            for member in set(axis["receivers"]) & set(timbers):
                station, included = inside(member, axis["point"])
                bolts.append({"axis_id": axis["id"], "member": member,
                    "reference_axis_point_xyz_mm": axis["point"], "reference_direction_xyz": axis["direction"],
                    "grain_station_mm": station, "axis_point_inside_retained_patch": included,
                    "selected_local_axis": axis["id"] in [f"thin_factory_bolt_{n:03}" for n in numbers],
                    "receiver_ids": axis["receivers"], "attached_fitting_ids": [a["angle_id"] for a in axis["attachments"]],
                    "duty_ids": [a["duty_id"] for a in axis["attachments"]],
                    "cross_boundary_occupancy_proved_from_point_only": False})
        for screw in layout["screw_axes"]:
            member = screw["receiver"]
            if member in timbers:
                station, included = inside(member, screw["origin_xyz_mm"])
                screws.append({**screw, "grain_station_mm": station,
                    "axis_origin_inside_retained_patch": included,
                    "complete_panel_joint_included": False})
        for c in geometry["contact_actions"]:
            member = c["second"]
            if member not in timbers:
                continue
            key = (member, c["kind"], c.get("angle_id", c["first"]))
            station, included = inside(member, c["point_xyz_mm"])
            record = contacts.setdefault(key, {"member": member, "kind": c["kind"], "other_body": key[2],
                "source_point_count": 0, "source_points_inside_retained_patch": 0,
                "source_grain_station_range_mm": [station, station], "reference_source_point_ids": []})
            record["source_point_count"] += 1
            record["source_points_inside_retained_patch"] += int(included)
            record["source_grain_station_range_mm"][0] = min(record["source_grain_station_range_mm"][0], station)
            record["source_grain_station_range_mm"][1] = max(record["source_grain_station_range_mm"][1], station)
            record["reference_source_point_ids"].append(c["id"])
        contact_rows = list(contacts.values())
        for c in contact_rows:
            c["source_sample_range_crosses_remote_cut"] = any(c["source_grain_station_range_mm"][0] < p["station_global_grain_projection_mm"] < c["source_grain_station_range_mm"][1]
                for p in ports if p["member"] == c["member"])
            c["sample_span_is_trimmed_continuous_contact_footprint"] = False
        patches.append({"id": identifier, "timber_body_order": timbers, "fitting_body_order": fittings,
            "selected_axis_ids": [f"thin_factory_bolt_{n:03}" for n in numbers], "remote_ports": ports,
            "retained_reference_centerline_grain_intervals_mm": bounds,
            "surrounding_shaft_duties": bolts, "surrounding_panel_screw_duties": screws,
            "surrounding_nominal_contact_duties": contact_rows,
            "authenticated_local_timber_timber_contact_pairs": [],
            "missing_direct_timber_contact_atlas": (["header-to-side at Z277"] if identifier == "outerbase-left"
                else ["header-to-principal at Z277", "header-to-centerpost at Z238.9"]),
            "neighbor_reactions_or_old_force_bounds_supplied": False})
    pins = {str(PATHS[key].relative_to(ROOT)): EXPECTED[key] for key in PATHS}
    pins[str(OWN.relative_to(ROOT))] = sha(OWN)
    return {"schema": "thin_bolted_local_remote_port_geometry_contract/v1", "source_sha256": pins,
        "candidate": layout["candidate"], "members": list(members.values()), "patches": patches,
        "geometry_source_selection": "Only centerline/basis/contact-point geometry selected from old62-body packet; no q, forces, couples, reactions or acceptance selected.",
        "work_contract": {"coordinate": "Each rigid body q=(u_world_mm,Ltheta_world_rad), positive explicit L; remote rows use grain frame.",
            "work_conjugate_load": "Remote f=(F_grain_N,M_grain_Nmm/L); f.T*q_remote equals physical force/couple work.",
            "mandatory_compatibility": "Retain six whole-patch free motions; every unit load annihilates them and each remaining internal free mode. Reject incompatible supplied loads.",
            "observable": "Cij=f_i.T*q_remote_j; Maxwell Cij=Cji only for the same reciprocal elastic operator and fixed admitted active branch, with gauges removed but no physical clamp.",
            "numeric_compliance_or_capacity": None},
        "limits": ["Reference cuts avoid saved bolt-section loss and selected flange corners; panel duties cross cuts and remain explicit neighbor ports.",
            "Nearest hardware-clear planes are not proven remote/Saint-Venant boundaries or section-stiffness bounds.",
            "Six-pair timberface proof supplies no direct header/timber contact within these local patches; bounds alone do not prove trimmed contact area.",
            "Rigid-patch rank/work is a method diagnostic; finite timber/steel/shaft flexibility and unilateral active-branch response remain separate.",
            "No CAD/BREP import/query, K/operator assembly, native/global solve or current/historical force consumption."],
        "release": {"structural_acceptance": False, "fabrication_release": False, "climbing_release": False}}


if __name__ == "__main__":
    if OUT.exists():
        raise SystemExit("Refusing to overwrite geometry contract")
    result = prepare()
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "sha256": sha(OUT), "source_sha256": sha(OWN)}))

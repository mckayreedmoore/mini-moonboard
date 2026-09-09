"""Prerequisite load-mapping diagnostic, NOT an NDS beam-column resistance check.

NDS2024 15.4.1 assumes eccentric end loading. Equilibrium equivalence below a
distributed bolt group does not establish that stability idealization. No
interaction ratio is returned, even when the clear-strip moment bounds hold.
"""
import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea import lumber_leg_resistance as source

LIMITS = (__doc__ + " Unverified K=1 nonsway translation and bearing-end anti-roll "
          "restraints remain assumptions, not physical details. Loaded-region "
          "moments are first-order nodal free-body demands, not hole/local stresses. "
          "Floor bevel, net section, torsion, joints and unanchored contact remain open.")


def decompose(points, forces, origin, along, across):
    """Split axial/lateral forces before taking moments; never add Pe twice."""
    if not points or set(points) != set(forces):
        raise ValueError("Require matching nonempty point and force ownership")
    if any(len(v) != 3 or not all(math.isfinite(x) for x in v)
           for v in [*points.values(), *forces.values(), origin, along, across]):
        raise ValueError("Require finite XYZ vectors")
    if abs(along[0]) > 1e-8 or abs(source.dot(along, along)-1) > 1e-8 or any(
            abs(v-w) > 1e-8 for v, w in zip(across, [0., along[2], -along[1]], strict=True)):
        raise ValueError("Require orthonormal leg axes in the YZ plane")
    def moment_of(values):
        terms = [source.cross([p[i]-origin[i] for i in range(3)], values[n]) for n, p in points.items()]
        return [math.fsum(m[i] for m in terms) for i in range(3)]
    axial_forces = {n: [source.dot(f, along)*v for v in along] for n, f in forces.items()}
    moment, axial_moment = moment_of(forces), moment_of(axial_forces)
    side = [a-b for a, b in zip(moment, axial_moment, strict=True)]
    signed_n = math.fsum(source.dot(f, along) for f in forces.values())
    # along x (r x N*along) / N recovers the transverse offset r.
    eccentricity = ([v/signed_n for v in source.cross(along, axial_moment)]
                    if abs(signed_n) > 1e-8 else None)
    return {"axial_n_tension_positive": signed_n,
        "total_moment_xyz_nmm": moment, "axial_moment_xyz_nmm": axial_moment,
        "side_load_moment_xyz_nmm": side,
        "eccentricity_xyz_mm": eccentricity,
        "side_bending_in_out_nmm": [side[0], source.dot(side, across)],
        "total_bending_in_out_nmm": [moment[0], source.dot(moment, across)]}


def envelope(points, forces, origin_at, along, stations):
    """Exact piecewise-linear nodal first-order envelope, both sides of jumps.

    Stations must include each applied node and the interval ends. Excludes
    floor reactions: callers restrict cuts to above the full floor bevel.
    """
    across = [0., along[2], -along[1]]
    node_stations = {n: source.dot(p, along) for n, p in points.items()}
    peak = [0., 0.]
    witness = [None, None]
    for station in sorted(set(stations)):
        origin = origin_at(station)
        threshold = source.dot(origin, along)
        for include_equal in (False, True):
            selected = {n: p for n, p in points.items()
                        if node_stations[n] > threshold + 1e-8 or
                        (include_equal and abs(node_stations[n]-threshold) < 1e-8)}
            if not selected:
                continue
            moments = [source.cross([p[i]-origin[i] for i in range(3)], forces[n])
                       for n, p in selected.items()]
            moment = [math.fsum(m[i] for m in moments) for i in range(3)]
            for axis, value in enumerate((moment[0], source.dot(moment, across))):
                if abs(value) > peak[axis]:
                    peak[axis] = abs(value)
                    witness[axis] = {"station_from_foot_mm": station,
                                     "include_station_loads": include_equal, "moment_nmm": value}
    return {"absolute_total_bending_in_out_nmm": peak, "witnesses": witness}


def screen(path):
    """Authenticate supported straight-leg evidence, then diagnose same-case legs."""
    path = Path(path)
    diagnostic_sources = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                          for name in ("fea/leg_beam_column_screen.py", "fea/lumber_leg_resistance.py")}
    evidence = source.screen(path)
    with tarfile.open(path) as archive:
        inputs = json.load(archive.extractfile("input.json"))
        native = json.load(archive.extractfile("report.json"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != evidence["archive_sha256"]:
        raise ValueError("Archive changed during diagnostic")
    if native.get("geometry") not in (None, "spread-100x50-top150"):
        raise ValueError("Unsupported straight-leg geometry")
    _, foot_v, along_v, across_v = source.model.geometry(evidence["stock"], evidence["extension_mm"])
    foot, along, across = foot_v.toTuple(), along_v.toTuple(), across_v.toTuple()
    metadata, mappings = {}, {}
    for side, sign in (("left", -1), ("right", 1)):
        mapping = {n: p for n, p in inputs["points"].items() if n.startswith(f"lumber_leg_bolt_{side}_")}
        active = {node for p in mapping.values() for node, w in
                  zip(p["gusset_nodes"], p["other_weights"], strict=True) if w != 0}
        floor = inputs["legs"][side]["floor_nodes"]
        station = lambda node: source.dot([inputs["nodes"][str(node)][i]-foot[i] for i in range(3)], along)
        low, high = min(map(station, floor)), max(map(station, active))
        metadata[side] = {"lowest_floor_station_mm": low, "highest_loaded_station_mm": high,
            "unsupported_span_candidate_mm": high-low, "K_both_axes_assumed": 1.,
            "restraints_physically_established": False,
            "centroid_x_mm": sign*(source.model.b.HALF+19.05)}
        mappings[side] = mapping
    rows = []
    for case in evidence["rows"]:
        for side, sections in case["sections"].items():
            mapping = mappings[side]
            points = {n: p["point_mm"] for n, p in mapping.items()}
            forces = {n: case["bolts"][n]["force_xyz_n"] for n in mapping}
            split = [decompose(points, forces, s["origin_xyz_mm"], along, across) for s in sections]
            nodal_points, contributions = {}, {}
            for name, p in mapping.items():
                for node, weight in zip(p["gusset_nodes"], p["other_weights"], strict=True):
                    if weight == 0:
                        continue
                    nodal_points[node] = inputs["nodes"][str(node)]
                    contributions.setdefault(node, []).append([weight*f for f in forces[name]])
            nodal_forces = {n: [math.fsum(f[i] for f in values) for i in range(3)]
                            for n, values in contributions.items()}
            errors = []
            for section, point_split in zip(sections, split, strict=True):
                node_split = decompose(nodal_points, nodal_forces, section["origin_xyz_mm"], along, across)
                errors.extend(abs(node_split[k][i]-point_split[k][i])
                              for k in ("total_moment_xyz_nmm", "axial_moment_xyz_nmm") for i in range(3))
                if abs(node_split["axial_n_tension_positive"]-point_split["axial_n_tension_positive"]) > 1e-6:
                    raise ValueError("MPC axial resultant equivalence failed")
            if max(errors) > .001:
                raise ValueError("MPC moment equivalence failed")
            low = sections[0]["station_from_foot_mm"]
            stations = [low]+[source.dot([p[i]-foot[i] for i in range(3)], along)
                              for p in nodal_points.values()]
            def origin_at(station, centroid_x=metadata[side]["centroid_x_mm"]):
                result = [foot[i]+station*along[i] for i in range(3)]
                result[0] = centroid_x
                return result
            full = envelope(nodal_points, nodal_forces, origin_at, along, stations)
            clear = [max(abs(s["total_bending_in_out_nmm"][i]) for s in split) for i in range(2)]
            side_envelope = [max(abs(s["side_bending_in_out_nmm"][i]) for s in split) for i in range(2)]
            axial = [source.dot(f, along) for f in forces.values()]
            rows.append({"stiffness": case["stiffness"], "case": case["case"], "side": side,
                "status": "unassessed_NDS_end_load_mapping", "interaction_ratio": None,
                "clear_endpoint_decomposition": split,
                "same_case_clear_side_moment_envelope_nmm": side_envelope,
                "clear_total_moment_envelope_nmm": clear, "through_loaded_region_envelope": full,
                "clear_envelope_misses_loaded_region_peak": any(a > b+.001 for a, b in
                    zip(full["absolute_total_bending_in_out_nmm"], clear, strict=True)),
                "opposing_bolt_axial_forces": min(axial) < 0 < max(axial),
                "maximum_below_group_moment_equivalence_error_nmm": max(errors)})
    if any(hashlib.sha256(Path(n).read_bytes()).hexdigest() != sha for n, sha in diagnostic_sources.items()):
        raise ValueError("Diagnostic source changed")
    return {"archive": str(path), "archive_sha256": evidence["archive_sha256"],
        "diagnostic_source_sha256": diagnostic_sources,
        "mapping_source": "NDS2024 15.4.1 and15.4.2 pp155–156: https://web-media.awc.org/wp-content/uploads/2021/12/17210150/AWC_NDS2024_20231129_AWCWebsite_Chapter15.pdf",
        "stock": evidence["stock"], "geometry": evidence["geometry"],
        "extension_mm": evidence["extension_mm"],
        "qualified_for_design": False, "combined_member_strength_evaluated": False,
        "limits": LIMITS, "span_candidates": metadata, "rows": rows,
        "summary": {"case_leg_count": len(rows),
            "opposing_axial_force_cases": sum(r["opposing_bolt_axial_forces"] for r in rows),
            "missed_loaded_region_peak_cases": sum(r["clear_envelope_misses_loaded_region_peak"] for r in rows)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(screen(parser.parse_args().archive), allow_nan=False, indent=2))

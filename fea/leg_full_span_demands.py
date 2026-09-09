"""First-order gross-section demands through the loaded region; NOT strength.

Each independent maximum retains its own simultaneous wrench and case. No
net-section, bevel, torsional shear, beam-column or restraint qualification.
"""
import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea import lumber_leg_resistance as source


def measures(row):
    normal = row["normal_stress_extrema_mpa_tension_positive"]
    return {"compression_n": max(0., -row["axial_n_tension_positive"]),
        "tension_n": max(0., row["axial_n_tension_positive"]),
        "shear_out_n": abs(row["shear_out_in_plane_n"][0]),
        "shear_in_n": abs(row["shear_out_in_plane_n"][1]),
        "bending_in_nmm": abs(row["bending_in_out_plane_nmm"][0]),
        "bending_out_nmm": abs(row["bending_in_out_plane_nmm"][1]),
        "torsion_nmm": abs(row["torsion_nmm"]),
        "normal_compression_mpa": max(0., -normal[0]),
        "normal_tension_mpa": max(0., normal[1]),
        "shear_out_mpa_excluding_torsion": row["shear_out_in_plane_max_mpa_excluding_torsion"][0],
        "shear_in_mpa_excluding_torsion": row["shear_out_in_plane_max_mpa_excluding_torsion"][1]}


def cut_peaks(points, forces, foot, along, centroid_x, low, properties):
    """Scan both sides of each load jump and the lowest full-width section.

    Between jumps N/V are constant and M is affine: endpoint sampling bounds
    these gross-section demand measures, including simultaneous biaxial stress.
    Node forces may have either sign, including negative quadratic weights.
    """
    if not points or points.keys() != forces.keys():
        raise ValueError("Require matching nonempty nodal load ownership")
    if (not math.isfinite(low) or low < 0 or not math.isfinite(centroid_x)
            or len(foot) != 3 or not all(math.isfinite(v) for v in foot)
            or len(along) != 3 or not all(math.isfinite(v) for v in along)
            or abs(along[0]) > 1e-8 or abs(source.dot(along, along)-1) > 1e-8):
        raise ValueError("Require finite geometry and unit YZ grain axis")
    across = [0., along[2], -along[1]]
    # Validate vectors through the shared demand kernel before filtering cuts.
    source.section_demand(points, forces, list(foot), along, across, properties)
    stations = {n: source.dot([p[i]-foot[i] for i in range(3)], along) for n, p in points.items()}
    if min(stations.values()) <= low:
        raise ValueError("Applied nodes must lie above the lowest full-width cut")
    peaks = {}
    for station in sorted({low, *stations.values()}):
        origin = [foot[i]+station*along[i] for i in range(3)]
        origin[0] = centroid_x
        for include in (False, True):
            chosen = {n: p for n, p in points.items() if stations[n] > station+1e-8
                      or (include and abs(stations[n]-station) <= 1e-8)}
            loads = {n: forces[n] for n in chosen}
            # Above all applied forces the free-body wrench is zero.
            demand = source.section_demand(chosen or {0: origin}, loads or {0: [0., 0., 0.]},
                                           origin, along, across, properties)
            witness = {"station_from_foot_mm": station, "include_station_loads": include,
                       "included_load_node_count": len(chosen), "simultaneous_section": demand}
            for key, value in measures(demand).items():
                if key not in peaks or value > peaks[key]["value"]:
                    peaks[key] = {"value": value, **witness}
    return peaks


def screen(path):
    path = Path(path)
    sources = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
        "fea/leg_full_span_demands.py", "fea/lumber_leg_resistance.py", "fea/leg_stock_screen.py")}
    evidence = source.screen(path)
    with tarfile.open(path) as archive:
        inputs = json.load(archive.extractfile("input.json"))
    if hashlib.sha256(path.read_bytes()).hexdigest() != evidence["archive_sha256"]:
        raise ValueError("Archive changed during demand recovery")
    _, foot_v, along_v, _ = source.model.geometry(evidence["stock"], evidence["extension_mm"])
    foot, along = foot_v.toTuple(), along_v.toTuple()
    summaries = {}
    count = 0
    for case in evidence["rows"]:
        key = case["stiffness"], case["case"]["climber_lb"]
        summary = summaries.setdefault(key, {"stiffness": key[0], "climber_lb": key[1], "peaks": {}})
        for side, sections in case["sections"].items():
            points, contributions = {}, {}
            for name, mapping in inputs["points"].items():
                if not name.startswith(f"lumber_leg_bolt_{side}_"):
                    continue
                force = case["bolts"][name]["force_xyz_n"]
                for node, weight in zip(mapping["gusset_nodes"], mapping["other_weights"], strict=True):
                    if weight == 0:
                        continue
                    points[node] = inputs["nodes"][str(node)]
                    contributions.setdefault(node, []).append([weight*f for f in force])
            forces = {n: [math.fsum(f[i] for f in terms) for i in range(3)] for n, terms in contributions.items()}
            # Independently verify complete nodal transfer below the group.
            low_section = sections[0]
            check = source.section_demand(points, forces, low_section["origin_xyz_mm"], along,
                [0., along[2], -along[1]], evidence["section_properties"])
            for field, tolerance in (("upper_load_force_xyz_n", 1e-6), ("upper_load_moment_xyz_nmm", .001)):
                if max(abs(a-b) for a, b in zip(check[field], low_section[field], strict=True)) > tolerance:
                    raise ValueError("Nodal transfer differs from archived connector wrench")
            peaks = cut_peaks(points, forces, foot, along, low_section["origin_xyz_mm"][0],
                              low_section["station_from_foot_mm"], evidence["section_properties"])
            count += 1
            for name, peak in peaks.items():
                if name not in summary["peaks"] or peak["value"] > summary["peaks"][name]["value"]:
                    summary["peaks"][name] = {**peak, "case": case["case"], "side": side}
    if any(hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha for name, sha in sources.items()):
        raise ValueError("Reporting source changed")
    return {"archive": str(path), "archive_sha256": evidence["archive_sha256"],
        "reporting_source_sha256": sources, "geometry": evidence["geometry"],
        "stock": evidence["stock"], "extension_mm": evidence["extension_mm"],
        "case_leg_count": count, "rows": list(summaries.values()),
        "qualified_for_design": False, "combined_strength_evaluated": False,
        "limits": __doc__+" Uses archived fixed-floor, isotropic, uncalibrated-connector "
            "loads without gravity. Gross prismatic sections only, above the entire floor bevel; "
            "nodal load spread is not physical bolt bearing. Independent maxima are not simultaneous "
            "with each other. No stiffness calibration, contact or buckling acceptance."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    print(json.dumps(screen(parser.parse_args().archive), indent=2, allow_nan=False))
